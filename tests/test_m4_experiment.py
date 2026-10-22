"""Tests for the M4 experiment code (math, schema, runner). Not tests of experiment results."""
import copy
import json
import os
import subprocess
import sys

import pytest
import torch

_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "experiments", "m4_cpu")
sys.path.insert(0, _DIR)
import m4lib as lib  # noqa: E402
import run_m4  # noqa: E402

SMALL = ((24, 18), (18, 24), (28, 28))


def _cfg(**over):
    c = lib.build_grid(seeds=1, shapes=SMALL, scale="smoke")[0]
    c.update(over)
    return c


# ---- spectra, matrices and the exact-SVD baseline ------------------------------------


@pytest.mark.parametrize("kind", lib.SPECTRA)
def test_spectrum_properties(kind):
    sg = lib.make_spectrum(kind, 20)
    assert sg.shape == (20,) and sg.dtype == torch.float64
    assert float(sg[0]) == 1.0 and bool((sg[:-1] >= sg[1:]).all()) and bool((sg >= 0).all())
    if kind == "exact_low_rank":
        assert int((sg > 0).sum()) == lib.EXACT_LOW_RANK
    else:
        assert float(sg[-1]) > 0
    with pytest.raises(ValueError):
        lib.make_spectrum("nope", 5)


@pytest.mark.parametrize("kind", lib.SPECTRA)
@pytest.mark.parametrize("shape", [(30, 20), (20, 30), (24, 24)])
def test_make_matrix_has_prescribed_singular_values(kind, shape):
    a, sg = lib.make_matrix(*shape, kind, a_seed=3)
    assert a.shape == shape and a.dtype == torch.float64
    torch.testing.assert_close(torch.linalg.svdvals(a), sg, rtol=0, atol=1e-12)
    a2, _ = lib.make_matrix(*shape, kind, a_seed=3)
    a3, _ = lib.make_matrix(*shape, kind, a_seed=4)
    assert torch.equal(a, a2) and not torch.equal(a, a3)


@pytest.mark.parametrize("kind", ["geometric", "polynomial", "flat"])
@pytest.mark.parametrize("r", [1, 3, 6])
def test_optimal_errors_equal_direct_truncated_svd_error(kind, r):
    a, sg = lib.make_matrix(30, 22, kind, 5)
    u, s, vh = torch.linalg.svd(a, full_matrices=False)
    direct = a - (u[:, :r] * s[:r]) @ vh[:r]
    fro, spec = lib.optimal_errors(sg, r)
    assert fro == pytest.approx(float(torch.linalg.matrix_norm(direct)), rel=1e-10)
    assert spec == pytest.approx(float(torch.linalg.matrix_norm(direct, ord=2)), rel=1e-10)


def test_optimal_errors_edge_cases():
    sg = torch.tensor([3.0, 2.0, 1.0], dtype=torch.float64)
    assert lib.optimal_errors(sg, 3) == (0.0, 0.0)
    assert lib.optimal_errors(sg, 1)[0] == pytest.approx(5**0.5)


def test_eckart_young_lower_bound_holds_for_random_rank_r_matrices():
    a, sg = lib.make_matrix(30, 22, "polynomial", 1)
    g = torch.Generator().manual_seed(0)
    fro_opt, spec_opt = lib.optimal_errors(sg, 4)
    for _ in range(20):
        b = torch.randn(30, 4, generator=g, dtype=torch.float64) @ torch.randn(4, 22, generator=g, dtype=torch.float64)
        assert float(torch.linalg.matrix_norm(a - b)) >= fro_opt - 1e-12
        assert float(torch.linalg.matrix_norm(a - b, ord=2)) >= spec_opt - 1e-12


# ---- metrics ---------------------------------------------------------------------------


def _svd_approx(a, r):
    u, s, vh = torch.linalg.svd(a, full_matrices=False)
    return u[:, :r], s[:r], vh[:r]


def test_metrics_of_optimal_truncation_hit_the_baseline():
    a, sg = lib.make_matrix(30, 22, "geometric", 2)
    m = lib.metrics(a, sg, *_svd_approx(a, 4), 4, 1e-8)
    assert m["rel_fro_err"] == pytest.approx(m["fro_opt_rel"], rel=1e-9)
    assert m["rel_spec_err"] == pytest.approx(m["spec_opt_rel"], rel=1e-9)
    assert m["fro_ratio"] == pytest.approx(1.0, rel=1e-9) and m["spec_ratio"] == pytest.approx(1.0, rel=1e-9)
    assert abs(m["fro_excess_rel"]) < 1e-12 and m["ey_ok"] and m["finite"]
    assert m["orth_u"] < 1e-12 and m["orth_v"] < 1e-12 and m["ratio_null_reason"] is None


def test_metrics_exact_low_rank_denominator_is_null_not_inf():
    a, sg = lib.make_matrix(30, 22, "exact_low_rank", 2)
    m = lib.metrics(a, sg, *_svd_approx(a, lib.EXACT_LOW_RANK), lib.EXACT_LOW_RANK, 1e-8)
    assert m["fro_opt_rel"] == 0.0
    assert m["fro_ratio"] is None and m["spec_ratio"] is None
    assert m["ratio_null_reason"] == "baseline_below_noise_floor"
    assert m["rel_fro_err"] < 1e-12 and m["fro_excess_rel"] < 1e-12


def test_metrics_flags_eckart_young_violation_orthogonality_and_nonfinite():
    a, sg = lib.make_matrix(30, 22, "geometric", 2)
    u, s, vh = _svd_approx(a, 4)
    inflated = sg.clone()
    inflated[4:] *= 3  # a wrong, too-large baseline: the true optimum now "beats" it
    assert lib.metrics(a, inflated, u, s, vh, 4, 1e-8)["ey_ok"] is False
    assert lib.metrics(a, sg, u, s, vh, 4, 1e-8)["ey_ok"] is True
    assert lib.metrics(a, sg, u * 2, s, vh, 4, 1e-8)["orth_u"] > 1.0
    nan = lib.metrics(a, sg, u, s * float("nan"), vh, 4, 1e-8)
    assert nan["finite"] is False and nan["rel_fro_err"] is None
    assert nan["ratio_null_reason"] == "nonfinite_output"
    lib.validate_rows([dict(lib.run_sample(_cfg()), **nan)])


# ---- production API runs: success rows, failure rows, determinism -------------------------------


def test_run_sample_ok_row_matches_schema_and_math():
    row = lib.run_sample(_cfg())
    assert row["status"] == "ok" and row["error_type"] is None
    lib.validate_rows([row])
    assert row["finite"] and row["ey_ok"]
    assert row["rel_fro_err"] >= row["fro_opt_rel"] - 1e-12
    assert row["fro_excess_rel"] == pytest.approx(row["rel_fro_err"] - row["fro_opt_rel"])
    assert row["est_buffer_bytes"] > 0


def test_run_sample_is_deterministic():
    a, b = lib.run_sample(_cfg()), lib.run_sample(_cfg())
    assert a == b


def test_run_sample_records_expected_failure_as_a_row():
    cfg = next(c for c in lib.build_grid(1, SMALL, "smoke") if c["block"] == "D_exact_rank" and c["s"] == 12)
    row = lib.run_sample(cfg)
    assert row["status"] == "error" and row["error_type"] == "RankDeficiencyError"
    assert row["rel_fro_err"] is None and row["finite"] is None
    lib.validate_rows([row])


def test_run_sample_exact_rank_success_has_tiny_error():
    cfg = next(c for c in lib.build_grid(1, SMALL, "smoke") if c["block"] == "D_exact_rank" and c["s"] == 8)
    row = lib.run_sample(cfg)
    assert row["status"] == "ok" and row["rank_true"] == lib.EXACT_LOW_RANK
    assert row["rel_fro_err"] <= row["fro_opt_rel"] + 1e-9  # recovers up to the rank-r truncation


def test_run_sample_float32_probe_runs_and_is_finite():
    cfg = next(c for c in lib.build_grid(1, SMALL, "smoke") if c["dtype"] == "float32")
    row = lib.run_sample(cfg)
    assert row["status"] == "ok" and row["finite"] and row["ey_ok"]


def test_q_does_not_change_rng_consumption():
    # Paired q comparisons share Omega, Phi, Psi only if q leaves the generator state alone.
    from torchsketchpower import sketch_power_low_rank

    a, _ = lib.make_matrix(24, 18, "geometric", 1)
    states = []
    for q in (0, 1, 2):
        g = torch.Generator().manual_seed(9)
        sketch_power_low_rank(a, 6, 12, 24, 24, steps=q, generator=g)
        states.append(g.get_state())
    assert torch.equal(states[0], states[1]) and torch.equal(states[1], states[2])


def test_grid_seeds_are_paired_across_q_and_sizes_shift_streams():
    grid = {c["sample_id"]: c for c in lib.build_grid(2, SMALL, "smoke")}
    q0 = grid["geometric-24x18-s12-l24-d24-q0-float64-seed1"]
    q2 = grid["geometric-24x18-s12-l24-d24-q2-float64-seed1"]
    assert (q0["a_seed"], q0["sketch_seed"]) == (q2["a_seed"], q2["sketch_seed"])
    assert q0["a_seed"] != q0["sketch_seed"]


# ---- grid contract -----------------------------------------------------------------------------


def test_full_grid_is_bounded_unique_and_paired_seeds_ge_5():
    grid = lib.build_grid()
    assert len(grid) <= lib.MAX_SAMPLES
    ids = [c["sample_id"] for c in grid]
    assert len(ids) == len(set(ids))
    a_block = [c for c in grid if c["block"] == "A_q"]
    assert len({c["a_seed"] for c in a_block if c["spectrum"] == "geometric" and c["q"] == 0}) >= 5
    assert {c["q"] for c in a_block} == {0, 1, 2}
    for c in grid:
        assert c["r"] <= c["s"] <= min(c["m"], c["n"]) and c["s"] < c["ell"] and c["d"] >= c["s"]
    assert {c["dtype"] for c in grid} == {"float64", "float32"}


def test_timing_configs_are_valid():
    for c in lib.timing_configs():
        assert c["r"] <= c["s"] < c["ell"] and c["d"] >= c["s"] and "seed" not in c["sample_id"]


# ---- schema, IO, summary -------------------------------------------------------------------------


def _rows():
    return [lib.run_sample(c) for c in lib.build_grid(1, SMALL, "smoke")]


def test_csv_round_trip_preserves_rows(tmp_path):
    rows = _rows()
    p = tmp_path / "s.csv"
    lib.write_csv(str(p), rows)
    assert lib.read_csv(str(p)) == rows  # includes None, bool, int and exact float repr


def test_schema_rejects_bad_rows():
    row = _rows()[0]
    lib.validate_rows([row])
    missing = {k: v for k, v in row.items() if k != "q"}
    extra = dict(row, surprise=1)
    wrong = dict(row, m="80")
    null_required = dict(row, status=None)
    nonfinite = dict(row, rel_fro_err=float("nan"))
    boolint = dict(row, m=True)
    for bad in (missing, extra, wrong, null_required, nonfinite, boolint):
        with pytest.raises(ValueError):
            lib.validate_rows([bad])


def test_json_rows_are_serialisable_and_valid():
    rows = _rows()
    assert json.loads(json.dumps(rows)) == rows


def test_failures_are_not_dropped_from_summary():
    rows = _rows()
    fails = [r for r in rows if r["status"] != "ok"]
    assert fails
    s = lib.summarize(rows)
    assert sum(g["n"] for g in s) == len(rows) and sum(g["n_fail"] for g in s) == len(fails)
    assert "RankDeficiencyError" in lib.summary_markdown(rows)


def test_paired_q_table_counts():
    rows = [
        {"block": "A_q", "status": "ok", "spectrum": "x", "a_seed": 1, "q": q, "rel_fro_err": e}
        for q, e in ((0, 3.0), (1, 2.0), (2, 2.5))
    ]
    assert lib.paired_q_table(rows) == {"x": {"pairs": 1, "q1_lt_q0": 1, "q2_lt_q1": 0, "q2_lt_q0": 1}}


def test_estimate_buffer_bytes_formula():
    m, n, r, s, ell, d = 10, 8, 2, 3, 5, 4
    elems = (n * s + n * ell + d * m) + (m * s + m * ell + d * n) + 2 * ell * s + m * s + d * s + s * n + (m * r + r + r * n)
    assert lib.estimate_buffer_bytes(m, n, r, s, ell, d, 1, torch.float64) == elems * 8
    assert lib.estimate_buffer_bytes(m, n, r, s, ell, d, 1, torch.float32) == elems * 4


def test_sha256_file(tmp_path):
    p = tmp_path / "x"
    p.write_bytes(b"abc")
    assert lib.sha256_file(str(p)) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


# ---- runner: memory probe, child process, end-to-end smoke ---------------------------------------


def test_process_memory_returns_bytes_or_not_measured():
    method, peak, cur = run_m4.process_memory()
    if peak is None:
        assert method == "NOT MEASURED"
    else:
        assert peak > 10**6 and (cur is None or cur > 10**6)


def test_timing_child_runs_in_fresh_process():
    trows, mrow, fail = run_m4.run_timing_config(lib.timing_configs()[0], repeats=2)
    assert fail is None
    lib.validate_rows(trows, lib.TIMING_SCHEMA)
    lib.validate_rows([mrow], lib.MEMORY_SCHEMA)
    phases = [t["phase"] for t in trows]
    assert phases.count("cold") == 1 and phases.count("warm") == 2 and phases.count("svd_baseline_warm") == 2
    assert all(t["seconds"] > 0 for t in trows)


def test_timing_child_failure_is_recorded_not_raised():
    bad = dict(lib.timing_configs()[0], spectrum="no_such_spectrum")
    trows, mrow, fail = run_m4.run_timing_config(bad, repeats=1)
    assert trows == [] and mrow is None and fail["config_id"] == bad["sample_id"]


def test_runner_smoke_end_to_end_is_reproducible(tmp_path):
    outs = []
    for name in ("a", "b"):
        out = tmp_path / name
        run_m4.main(["--out", str(out), "--smoke"])
        outs.append(out)
    for fname in ("samples.csv", "samples.json", "summary.md"):  # deterministic content
        assert (outs[0] / fname).read_bytes() == (outs[1] / fname).read_bytes()
    man = json.loads((outs[0] / "manifest.json").read_text())
    assert man["device"] == "cpu" and man["grid"] == "smoke" and "GPU" in man["not_run"]
    for fname, info in man["files"].items():
        assert lib.sha256_file(str(outs[0] / fname)) == info["sha256"]
    lib.read_csv(str(outs[0] / "samples.csv"))
    lib.read_csv(str(outs[0] / "timings.csv"), lib.TIMING_SCHEMA)
    lib.read_csv(str(outs[0] / "memory.csv"), lib.MEMORY_SCHEMA)
