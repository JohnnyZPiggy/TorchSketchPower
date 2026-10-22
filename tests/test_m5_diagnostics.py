"""Tests for the M5 diagnostics code (identities, oracles, schema, runner). Not tests of results."""
import json
import os
import sys

import pytest
import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "experiments", "m5_cpu"))
import m5lib as lib  # noqa: E402
import run_m5  # noqa: E402
from torchsketchpower import IllConditionedWarning, RankDeficiencyError  # noqa: E402

M4_CSV = os.path.join(ROOT, "reports", "m4_cpu", "samples.csv")


def _problem(m=30, n=20, s=6, d=10, dtype=torch.float64, seed=0):
    g = torch.Generator().manual_seed(seed)
    a = torch.randn(m, n, generator=g, dtype=dtype)
    q = torch.linalg.qr(torch.randn(m, s, generator=g, dtype=dtype)).Q
    psi = torch.randn(d, m, generator=g, dtype=dtype)
    return a, q, psi


def _direct(a, q, psi, r):
    """Independent recomputation of the quantities with plain torch (no lib helpers)."""
    na2 = float(torch.linalg.matrix_norm(a)) ** 2
    c = psi @ q
    u, sv, vh = torch.linalg.svd(c, full_matrices=False)
    b = vh.mH @ ((u.mH @ (psi @ a)) / sv[:, None])
    ub, sb, vhb = torch.linalg.svd(b, full_matrices=False)
    b_r = (ub[:, :r] * sb[:r]) @ vhb[:r]
    full = float(torch.linalg.matrix_norm(a - q @ b)) ** 2 / na2
    trunc = float(torch.linalg.matrix_norm(a - q @ b_r)) ** 2 / na2
    return b, b_r, full, trunc, na2


# ---- exact identities ------------------------------------------------------------------


@pytest.mark.parametrize("dtype", [torch.float64, torch.complex128])
@pytest.mark.parametrize("r", [1, 3, 6])
@pytest.mark.parametrize("seed", [0, 1])
def test_identities_match_direct_residuals(dtype, r, seed):
    a, q, psi = _problem(dtype=dtype, seed=seed)
    out = lib.decompose(a, q, psi, r)
    b, b_r, full, trunc, na2 = _direct(a, q, psi, r)
    assert out["full_lhs"] == pytest.approx(full, rel=1e-10)
    assert out["trunc_lhs"] == pytest.approx(trunc, rel=1e-10)
    e = a - q @ (q.mH @ a)
    assert out["e2"] == pytest.approx(float(torch.linalg.matrix_norm(e)) ** 2 / na2, rel=1e-10)
    d = b - q.mH @ a
    assert out["d2"] == pytest.approx(float(torch.linalg.matrix_norm(d)) ** 2 / na2, rel=1e-10)
    # I: lhs = E^2 + D^2 ; II: lhs = E^2 + ||Bstar - B_r||^2
    assert full == pytest.approx(out["e2"] + out["d2"], abs=1e-12)
    assert trunc == pytest.approx(out["e2"] + out["bstar_minus_br2"], abs=1e-12)
    assert out["id1_ok"] and out["id2_ok"] and out["qe_orth"] < 1e-14


def test_signed_cross_term_expansion_and_squares_do_not_add():
    a, q, psi = _problem(seed=3)
    out = lib.decompose(a, q, psi, 2)
    assert abs(out["cross"]) > 1e-3  # a nonzero cross term in this instance
    naive = out["d2"] + out["tail_b2"]
    assert abs(out["bstar_minus_br2"] - naive) > 1e-3  # adding squares would be wrong
    assert out["bstar_minus_br2"] == pytest.approx(naive + out["cross"], abs=1e-12)
    assert out["expansion_resid"] < 1e-12


def test_hand_checkable_counterexample():
    # m=3, s=2, Q=[e1 e2], Psi=[[1,0,1],[0,1,1]] => C=I, B=W=Psi A, D=ones(2,2), E has only row 3.
    a = torch.tensor([[2.0, 0.0], [0.0, 1.0], [1.0, 1.0]], dtype=torch.float64)
    q = torch.eye(3, dtype=torch.float64)[:, :2]
    psi = torch.tensor([[1.0, 0.0, 1.0], [0.0, 1.0, 1.0]], dtype=torch.float64)
    out = lib.decompose(a, q, psi, 1)
    na2 = 7.0
    assert out["e2"] * na2 == pytest.approx(2.0)  # E = [0 0; 0 0; 1 1]
    assert out["d2"] * na2 == pytest.approx(4.0)  # D = ones
    b = torch.tensor([[3.0, 1.0], [1.0, 2.0]], dtype=torch.float64)  # symmetric
    lam, vec = torch.linalg.eigh(b)  # ascending: lam[0] is the discarded one
    d = torch.ones(2, 2, dtype=torch.float64)
    cross = -2 * float(lam[0]) * float(vec[:, 0] @ d @ vec[:, 0])  # <D, B-B_1> = lam0 * w^T D w
    assert out["cross"] * na2 == pytest.approx(cross, abs=1e-12)
    assert out["tail_b2"] * na2 == pytest.approx(float(lam[0]) ** 2)
    assert out["bstar_minus_br2"] * na2 == pytest.approx(4.0 + float(lam[0]) ** 2 + cross)
    assert out["trunc_lhs"] * na2 == pytest.approx(2.0 + 4.0 + float(lam[0]) ** 2 + cross)
    assert cross < 0


def test_complex_uses_hermitian_inner_product():
    a, q, psi = _problem(m=20, n=12, s=4, d=8, dtype=torch.complex128, seed=5)
    out = lib.decompose(a, q, psi, 2)
    b, b_r, _, _, na2 = _direct(a, q, psi, 2)
    d = b - q.mH @ a
    ref = -2 * float((d.conj() * (b - b_r)).sum().real) / na2  # Re tr(D^H (B - B_r))
    assert out["cross"] == pytest.approx(ref, abs=1e-12)
    wrong = -2 * float((d * (b - b_r)).sum().real) / na2  # transpose-without-conjugate inner product
    assert abs(wrong - ref) > 1e-6
    assert out["id1_ok"] and out["id2_ok"]


def test_counterfactual_ordering():
    a, q, psi = _problem(m=40, n=25, s=8, d=16, seed=2)
    out = lib.decompose(a, q, psi, 3)
    assert out["opt_r2"] <= out["ideal_r2"] + 1e-14  # Eckart-Young: optimum beats ideal-Q truncation
    assert out["ideal_r2"] == pytest.approx(out["e2"] + float(  # E^2 + tail of Bstar beyond r
        (torch.linalg.svdvals(q.mH @ a)[3:] ** 2).sum()) / (float(torch.linalg.matrix_norm(a)) ** 2), abs=1e-12)
    assert out["extra_vs_ideal2"] == pytest.approx(out["trunc_lhs"] - out["ideal_r2"])


# ---- coefficient oracles and null handling --------------------------------------------------------


def test_coefficient_oracles_and_stationarity():
    a, q, psi = _problem()
    out = lib.decompose(a, q, psi, 2)
    assert out["b_oracle_diff"] < 1e-12 and out["b_lstsq_diff"] < 1e-10
    assert out["d_formula_diff_rel"] < 1e-10  # D = C^+ Psi E
    assert out["stationarity_rel"] < 1e-10 and out["c_resid_rel"] > 1e-3
    cs = torch.linalg.svdvals(psi @ q)
    assert out["cond_c"] == pytest.approx(float(cs[0] / cs[-1])) and out["sigma_min_c"] == pytest.approx(float(cs[-1]))


def test_exact_low_rank_gives_null_ratios_not_inf():
    row = lib.run_case(next(c for c in lib.build_cases() if c["case"] == "tiny_exact"))
    assert row["status"] == "ok"
    assert row["e_ratio_s"] is None and row["d_formula_diff_rel"] is None
    assert "e_ratio_s" in row["null_reason"] and "D at noise floor" in row["null_reason"]
    assert row["id1_ok"] and row["id2_ok"]
    lib.validate_rows([row])


def test_consistent_system_has_null_stationarity():
    # A in range(Q): E = 0 so C B = W exactly and the normal-equation residual is at the noise floor.
    g = torch.Generator().manual_seed(0)
    q = torch.linalg.qr(torch.randn(20, 4, generator=g, dtype=torch.float64)).Q
    a = q @ torch.randn(4, 9, generator=g, dtype=torch.float64)
    psi = torch.randn(8, 20, generator=g, dtype=torch.float64)
    out = lib.decompose(a, q, psi, 2)
    assert out["stationarity_rel"] is None and "stationarity_rel" in out["null_reason"]


# ---- negative controls -------------------------------------------------------------------------------


def _case(name):
    return next(c for c in lib.build_cases() if c["case"] == name)


def test_rank_deficient_a_is_an_error_row():
    row = lib.run_case(_case("tiny_rank_def_a"))
    assert row["status"] == "error" and row["error_type"] == "RankDeficiencyError"
    assert row["e2"] is None and row["id1_ok"] is None
    lib.validate_rows([row])


def test_rank_deficient_c_is_an_error_row():
    row = lib.run_case(_case("tiny_dup_psi"))
    assert row["status"] == "error" and row["error_type"] == "RankDeficiencyError"
    assert "psi @ q" in row["error_message"]


def test_ill_conditioned_c_warns_and_is_recorded_not_masked():
    row = lib.run_case(_case("tiny_illcond"))
    assert row["status"] == "ok" and row["n_warnings"] >= 1
    assert "IllConditionedWarning" in row["warning_types"]
    assert row["cond_c"] == pytest.approx(1e9, rel=1e-2)
    assert row["id1_ok"] and row["id2_ok"]  # identities hold regardless of conditioning


def test_complex_tiny_case_runs():
    row = lib.run_case(_case("tiny_complex"))
    assert row["status"] == "ok" and row["dtype"] == "complex128" and row["id1_ok"] and row["id2_ok"]


# ---- reuse of M4: same seeds, same production decomposition ------------------------------------------------


@pytest.mark.skipif(not os.path.exists(M4_CSV), reason="committed M4 report not present")
def test_replay_reproduces_committed_m4_rows():
    m4 = lib.load_m4_rows(M4_CSV)
    cases = [c for c in lib.build_cases() if c["block"] == "P_baseline"]
    picks = [c for c in cases if c["sample_id"].endswith(("q0-float64-seed0", "q1-float64-seed3", "q2-float64-seed4"))]
    assert len(picks) == 9
    for c in picks:
        row = lib.run_case(c, m4)
        assert row["m4_rel_diff"] is not None and row["m4_rel_diff"] < lib.M4_TOL, c["sample_id"]
        assert row["api_rel_diff"] < 1e-12  # replay == sketch_power_low_rank


def test_all_baseline_ids_exist_in_m4_report():
    if not os.path.exists(M4_CSV):
        pytest.skip("committed M4 report not present")
    m4 = lib.load_m4_rows(M4_CSV)
    for c in lib.build_cases():
        if c["block"] == "P_baseline":
            assert c["sample_id"] in m4 and m4[c["sample_id"]]["status"] == "ok"


# ---- controlled Psi variation ------------------------------------------------------------------------------


def test_psi_variation_keeps_a_and_q_fixed():
    rows = [lib.run_case(c) for c in lib.build_cases() if c["block"] == "S_psi" and c["spectrum"] == "geometric"]
    assert len(rows) == 7 and all(r["status"] == "ok" for r in rows)
    assert len({r["e2"] for r in rows}) == 1  # E depends on A and Q only, bit for bit
    assert len({r["d2"] for r in rows}) > 3  # D changes with Psi


def test_prefix_psi_is_nested():
    cfg = {c["case"]: c for c in lib.build_cases()}
    a, _ = lib.m4lib.make_matrix(80, 60, "flat", cfg["flat-psi-prefix-d12"]["a_seed"])
    p12 = lib._psi_for(cfg["flat-psi-prefix-d12"], a, None, None)
    p48 = lib._psi_for(cfg["flat-psi-prefix-d48"], a, None, None)
    assert p12.shape == (12, 80) and p48.shape == (48, 80) and torch.equal(p48[:12], p12)


# ---- grid, schema, summary, runner -----------------------------------------------------------------------------


def test_grid_is_bounded_and_unique():
    cases = lib.build_cases()
    assert len(cases) <= lib.MAX_CASES and sum(c["block"] == "S_psi" for c in cases) <= 15
    ids = [c["sample_id"] for c in cases]
    assert len(ids) == len(set(ids))
    counts = {b: sum(c["block"] == b for c in cases) for b in {c["block"] for c in cases}}
    assert counts == {"P_baseline": 45, "S_psi": 14, "O_tiny": 6}
    for c in cases:
        assert c["r"] <= c["s"] and c["d"] >= c["s"]


def test_schema_and_csv_round_trip(tmp_path):
    rows = [lib.run_case(_case(n)) for n in ("tiny_noisy", "tiny_rank_def_a", "tiny_illcond")]
    p = tmp_path / "s.csv"
    lib.write_csv(str(p), rows)
    assert lib.read_csv(str(p)) == rows
    bad = dict(rows[0], block=None)
    extra = dict(rows[0], surprise=1)
    nonfinite = dict(rows[0], e2=float("nan"))
    for b in (bad, extra, nonfinite):
        with pytest.raises(ValueError):
            lib.validate_rows([b])


def test_summary_is_computed_from_rows_and_shows_failures():
    base = {k: None for k in lib.SCHEMA}
    def row(q, trunc, e2, cond):
        return dict(base, block="P_baseline", spectrum="s", q=q, status="ok", n_warnings=0, case=f"c{q}{trunc}",
                    opt_r2=0.1, ideal_r2=0.2, e2=e2, d2=0.3, tail_b2=0.4, cross=-0.1, trunc_lhs=trunc,
                    extra_vs_ideal2=trunc - 0.2, cond_c=cond)
    rows = [row(0, 1.0, 0.5, 2.0), row(0, 3.0, 0.7, 4.0), row(0, 2.0, 0.6, 3.0)]
    rows.append(dict(base, block="O_tiny", case="bad", status="error", error_type="RankDeficiencyError", n_warnings=0))
    table = lib.stage_table(rows)
    assert "| s | 0 | 3 |" in table and "2.000e+00" in table and "4.000e+00" in table  # median final, max cond
    assert "3/3" in table  # cross<0 count
    assert "RankDeficiencyError" in lib.failure_table(rows)


def test_runner_smoke_is_deterministic_and_hashed(tmp_path):
    outs = []
    for name in ("a", "b"):
        run_m5.main(["--out", str(tmp_path / name), "--smoke"])
        outs.append(tmp_path / name)
    for fname in ("samples.csv", "samples.json", "summary.md"):
        assert (outs[0] / fname).read_bytes() == (outs[1] / fname).read_bytes()
    man = json.loads((outs[0] / "manifest.json").read_text())
    assert man["device"] == "cpu" and man["grid"] == "smoke" and "GPU" in man["not_run"]
    for fname, info in man["files"].items():
        assert lib.sha256_file(str(outs[0] / fname)) == info["sha256"]
    rows = lib.read_csv(str(outs[0] / "samples.csv"))
    assert {r["block"] for r in rows} == {"P_baseline", "S_psi", "O_tiny"}
    assert any(r["status"] == "error" for r in rows)  # negative controls are kept
