"""M7: device policy, CPU behaviour guard, and the device-correctness oracles.

* CPU tests run everywhere: they check the device-policy helpers, that the CPU path still uses ``gelsd``,
  and that the oracle suite itself is sound (it passes on the CPU and fails on deliberately broken code).
* ``cuda`` tests run the same oracles on a real GPU. Without CUDA they are SKIPPED, which is not a pass:
  M7 GPU correctness is NOT RUN until they execute on a CUDA device (see experiments/m7_cuda/README.md).
"""
import json
import os
import sys
import warnings
from types import SimpleNamespace

import pytest
import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "experiments", "m7_cuda"))
import m7lib as lib  # noqa: E402
import run_m7_cuda  # noqa: E402
from torchsketchpower import RankDeficiencyError, sketch_power_low_rank, solve_corange_coefficient  # noqa: E402
from torchsketchpower import _device, reconstruct  # noqa: E402

cuda = pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available: GPU test NOT RUN")
CPU = torch.device("cpu")


# ---- device policy (pure, runs without a GPU) ---------------------------------------------------------------


@pytest.mark.parametrize("name,ok", [("cpu", True), ("cuda", True), ("cuda:1", True), ("meta", False), ("mps", False), ("xpu", False)])
def test_supported_device_types(name, ok):
    dev = torch.device(name)
    if ok:
        _device.require_supported_device(dev, "a")
    else:
        with pytest.raises(ValueError, match="CPU or CUDA"):
            _device.require_supported_device(dev, "a")


def test_lstsq_driver_by_device():
    assert _device.lstsq_driver(torch.device("cpu")) == "gelsd"
    assert _device.lstsq_driver(torch.device("cuda")) == "gels"
    assert _device.lstsq_driver(torch.device("cuda:1")) == "gels"


def test_same_device_rules():
    assert _device.same_device(torch.device("cpu"), torch.device("cpu"))
    assert _device.same_device(torch.device("cuda:0"), torch.device("cuda:0"))
    assert not _device.same_device(torch.device("cuda:0"), torch.device("cuda:1"))
    assert not _device.same_device(torch.device("cpu"), torch.device("cuda:0"))


def test_check_generator_and_distribution():
    _device.check_generator(None, torch.device("cuda:0"))
    _device.check_generator(SimpleNamespace(device=torch.device("cuda:0")), torch.device("cuda:0"))
    with pytest.raises(ValueError, match="must match"):
        _device.check_generator(SimpleNamespace(device=torch.device("cpu")), torch.device("cuda:0"))
    with pytest.raises(ValueError, match="must match"):
        _device.check_generator(SimpleNamespace(device=torch.device("cuda:1")), torch.device("cuda:0"))
    with pytest.raises(ValueError, match="must match"):
        _device.check_generator(SimpleNamespace(device=torch.device("cuda:0")), torch.device("cpu"))
    _device.check_distribution("gaussian", torch.device("cuda:0"))
    _device.check_distribution("SparseSign", torch.device("cpu"))  # CPU keeps the exploratory option
    with pytest.raises(ValueError, match="not validated on CUDA"):
        _device.check_distribution("sparsesign", torch.device("cuda:0"))


def test_low_rank_checks_generator_device_before_any_draw():
    a = torch.randn(20, 10, dtype=torch.float64, generator=torch.Generator().manual_seed(0))
    fake = SimpleNamespace(device=torch.device("cuda:0"))  # would explode if used for a draw
    with pytest.raises(ValueError, match="must match"):
        sketch_power_low_rank(a, 2, 4, 8, 6, generator=fake)


def test_low_rank_rejects_meta_with_cpu_or_cuda_message():
    with pytest.raises(ValueError, match="CPU or CUDA"):
        sketch_power_low_rank(torch.empty(10, 8, dtype=torch.float64, device="meta"), 1, 3, 6, 3)


def test_lower_level_solvers_reject_unsupported_device():
    m = lambda *s: torch.empty(*s, dtype=torch.float64, device="meta")  # noqa: E731
    with pytest.raises(ValueError, match="CPU or CUDA"):
        solve_corange_coefficient(m(10, 3), m(5, 10), m(5, 8))
    with pytest.raises(ValueError, match="CPU or CUDA"):
        reconstruct.reconstruct_from_corange(m(10, 3), m(5, 10), m(5, 8), 2)


# ---- CPU behaviour is unchanged ----------------------------------------------------------------------------------


def test_cpu_path_still_uses_gelsd(monkeypatch):
    seen = []
    real = torch.linalg.lstsq

    def spy(*a, **k):
        seen.append(k.get("driver"))
        return real(*a, **k)

    monkeypatch.setattr(torch.linalg, "lstsq", spy)
    _, q, psi, w = lib.make_problem(30, 20, 5, 9, torch.float64, 10.0, 1)
    solve_corange_coefficient(q, psi, w)
    sketch_power_low_rank(lib.make_matrix(30, 20, "geometric", 1, torch.float64)[0], 2, 5, 10, 8, generator=torch.Generator().manual_seed(0))
    assert seen == ["gelsd", "gelsd"]


def test_driver_plumbing_gels_matches_gelsd_on_full_rank_cpu(monkeypatch):
    # The CUDA branch passes driver="gels"; on the CPU the same driver is valid and must agree for a well-conditioned C.
    _, q, psi, w = lib.make_problem(30, 20, 5, 9, torch.float64, 10.0, 1)
    ref = solve_corange_coefficient(q, psi, w)
    seen = []
    real = torch.linalg.lstsq
    monkeypatch.setattr(reconstruct, "lstsq_driver", lambda dev: "gels")
    monkeypatch.setattr(torch.linalg, "lstsq", lambda *a, **k: (seen.append(k["driver"]), real(*a, **k))[1])
    got = solve_corange_coefficient(q, psi, w)
    assert seen == ["gels"]
    torch.testing.assert_close(got, ref, rtol=1e-10, atol=1e-10)


def test_rank_gate_still_runs_before_the_solve(monkeypatch):
    # With a driver that does not detect rank (gels), the explicit gate must still reject a rank-deficient C first.
    monkeypatch.setattr(reconstruct, "lstsq_driver", lambda dev: "gels")
    _, q, psi, w = lib.make_problem(30, 20, 5, 5, torch.float64, 10.0, 4)
    psi = psi.clone()
    psi[1] = psi[0]
    called = []
    monkeypatch.setattr(torch.linalg, "lstsq", lambda *a, **k: called.append(1))
    with pytest.raises(RankDeficiencyError):
        solve_corange_coefficient(q, psi, psi @ torch.randn(30, 20, dtype=torch.float64, generator=torch.Generator().manual_seed(0)))
    assert not called


# ---- the oracle suite is sound: passes on CPU, fails on broken code -----------------------------------------------------


@pytest.mark.parametrize("dtype", lib.DTYPES)
@pytest.mark.parametrize("m,n,s,d", [(40, 24, 6, 10), (30, 30, 6, 6), (24, 40, 6, 12)])
def test_coefficient_oracles_pass_on_cpu(dtype, m, n, s, d):
    cond = 1e2 if dtype in (torch.float32, torch.complex64) else 1e4
    row = lib.coefficient_case(CPU, dtype, m, n, s, d, cond, seed=7)
    assert row["status"] == lib.PASS, row
    assert row["margin_o1"] < 1 and row["margin_o2"] < 1 and row["margin_o3"] < 1
    assert row["resident"] and row["host_transfers"] == []


@pytest.mark.parametrize("dtype", lib.DTYPES)
@pytest.mark.parametrize("q_steps", [0, 1, 2])
def test_end_to_end_oracles_pass_on_cpu(dtype, q_steps):
    a = lib.end_to_end_mode_a(CPU, dtype, 40, 30, "geometric", 3, q_steps)
    b = lib.end_to_end_mode_b(CPU, dtype, 40, 30, "polynomial", 1, q_steps)
    assert a["status"] == lib.PASS, a
    assert b["status"] == lib.PASS, b
    assert b["id1_rel"] < 1e-10 or dtype in (torch.float32, torch.complex64)


def test_negative_matrix_on_cpu():
    rows = lib.negative_cases(CPU)
    bad = [r for r in rows if r["status"] not in (lib.PASS, lib.NOT_RUN)]
    assert not bad, bad
    assert {r["case"] for r in rows if r["status"] == lib.NOT_RUN} == {
        "CPU generator with CUDA input", "sparsesign on CUDA (not validated)", "mixed CPU and CUDA tensors", "mixed CUDA indices"}
    assert sum(r["status"] == lib.PASS for r in rows) >= 20


def test_oracle_detects_wrong_coefficient(monkeypatch):
    real = lib.solve_corange_coefficient
    monkeypatch.setattr(lib, "solve_corange_coefficient", lambda *a, **k: real(*a, **k) * (1 + 1e-3))
    assert lib.coefficient_case(CPU, torch.float64, 40, 24, 6, 10, 1e3, 11)["status"] == lib.FAIL


def test_oracle_detects_host_transfers(monkeypatch):
    real = lib.solve_corange_coefficient
    monkeypatch.setattr(lib, "solve_corange_coefficient", lambda *a, **k: real(*a, **k).cpu())
    row = lib.coefficient_case(CPU, torch.float64, 40, 24, 6, 10, 1e3, 11)
    assert row["status"] == lib.FAIL and "cpu" in row["host_transfers"]


def test_oracle_detects_swallowed_rank_error(monkeypatch):
    real = lib.solve_corange_coefficient

    def sloppy(q, p, w, **k):
        try:
            return real(q, p, w, **k)
        except RankDeficiencyError:
            return torch.zeros(q.shape[1], w.shape[1], dtype=w.dtype)

    monkeypatch.setattr(lib, "solve_corange_coefficient", sloppy)
    rows = lib.negative_cases(CPU)
    assert any(r["status"] == lib.FAIL and "rank deficient" in r["case"] for r in rows)


def test_oracle_detects_ignored_power_steps(monkeypatch):
    monkeypatch.setattr(lib, "sketch_power_subspace", lambda y, z, steps=1, **k: torch.linalg.qr(y)[0])
    assert lib.end_to_end_mode_b(CPU, torch.float64, 40, 30, "geometric", 0, 1)["status"] == lib.FAIL


def test_transfer_spy_restores_tensor_methods():
    before = {n: getattr(torch.Tensor, n) for n in ("cpu", "numpy", "tolist", "to")}
    with lib.transfer_spy() as calls:
        torch.ones(2).cpu()
        torch.ones(2).tolist()
    assert calls == ["cpu", "tolist"]
    assert all(getattr(torch.Tensor, n) is f for n, f in before.items())


def test_make_problem_designs_the_condition_number():
    for cond in (1.0, 1e3, 1e6):
        _, q, psi, _ = lib.make_problem(40, 20, 6, 10, torch.float64, cond, 3)
        sv = torch.linalg.svdvals(psi @ q)
        assert float(sv[0] / sv[-1]) == pytest.approx(cond, rel=1e-6)
        torch.testing.assert_close(q.mH @ q, torch.eye(6, dtype=torch.float64), atol=1e-12, rtol=0)


# ---- runner -----------------------------------------------------------------------------------------------------------------


def test_runner_cpu_dry_run_is_labelled_and_reproducible(tmp_path):
    reports = []
    for name in ("a", "b"):
        out = tmp_path / name
        assert run_m7_cuda.main(["--device", "cpu", "--quick", "--out", str(out), "--source-sha", "0" * 40]) == 0
        reports.append(json.loads((out / "results.json").read_text()))
    rep = reports[0]
    assert rep["status"] == "DRY_RUN_CPU" and rep["gpu_evidence"] is False and rep["device"] == "cpu"
    assert rep["counts"].get("FAIL", 0) == 0 and rep["counts"].get("BLOCKED", 0) == 0 and rep["counts"]["PASS"] > 20
    assert all(r["device"] == "cpu" for r in rep["rows"])
    assert "performance" in rep["not_run"] and "torch.compile" in rep["not_run"]
    assert reports[0]["rows"] == reports[1]["rows"]  # deterministic rows
    man = json.loads((tmp_path / "a" / "manifest.json").read_text())
    for name, info in man["files"].items():
        assert run_m7_cuda.sha256_file(str(tmp_path / "a" / name)) == info["sha256"]


@pytest.mark.skipif(torch.cuda.is_available(), reason="only meaningful without CUDA")
def test_runner_cuda_request_without_cuda_is_blocked_not_passed(tmp_path):
    code = run_m7_cuda.main(["--device", "cuda", "--out", str(tmp_path), "--source-sha", "0" * 40])
    rep = json.loads((tmp_path / "results.json").read_text())
    assert code == 2 and rep["status"] == "BLOCKED" and rep["gpu_evidence"] is False and rep["rows"] == []
    assert "no CUDA test was run" in rep["reason"]


def test_runner_time_limit_marks_not_run(tmp_path):
    run_m7_cuda.main(["--device", "cpu", "--quick", "--out", str(tmp_path), "--max-seconds", "-1"])
    rep = json.loads((tmp_path / "results.json").read_text())
    assert rep["counts"] == {"NOT_RUN": 1}


# ---- GPU-only: the same oracles on a real CUDA device (SKIPPED without CUDA) -------------------------------------------------


@cuda
@pytest.mark.parametrize("dtype", lib.DTYPES)
@pytest.mark.parametrize("m,n,s,d", [(40, 24, 6, 10), (30, 30, 6, 6), (24, 40, 6, 12)])
@pytest.mark.parametrize("cond", [1.0, 1e2, 1e3])
def test_cuda_coefficient_oracles(dtype, m, n, s, d, cond):
    row = lib.coefficient_case(torch.device("cuda"), dtype, m, n, s, d, cond, seed=11)
    assert row["status"] == lib.PASS, row


@cuda
@pytest.mark.parametrize("dtype", lib.DTYPES)
@pytest.mark.parametrize("q_steps", [0, 1])
def test_cuda_end_to_end_modes(dtype, q_steps):
    dev = torch.device("cuda")
    assert lib.end_to_end_mode_a(dev, dtype, 40, 30, "geometric", 3, q_steps)["status"] == lib.PASS
    for seed in range(5):
        assert lib.end_to_end_mode_b(dev, dtype, 40, 30, "polynomial", seed, q_steps)["status"] == lib.PASS


@cuda
def test_cuda_negative_matrix():
    rows = lib.negative_cases(torch.device("cuda"))
    bad = [r for r in rows if r["status"] not in (lib.PASS, lib.NOT_RUN)]
    assert not bad, bad


@cuda
def test_cuda_outputs_stay_on_the_device():
    a = lib.make_matrix(40, 30, "geometric", 1, torch.float64)[0].cuda()
    with lib.transfer_spy() as calls:
        u, sg, vh = sketch_power_low_rank(a, 3, 6, 12, 12, generator=torch.Generator(device="cuda").manual_seed(0))
    assert calls == [] and all(t.is_cuda for t in (u, sg, vh))
