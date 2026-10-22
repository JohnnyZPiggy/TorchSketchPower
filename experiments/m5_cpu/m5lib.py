"""M5 CPU numerical diagnostics: where does the error of sketch_power_low_rank come from?

For A (m, n), orthonormal Q (m, s), Psi (d, m), C = Psi Q, W = Psi A, B = C^+ W,
Bstar = Q^H A, E = (I - Q Q^H) A, D = B - Bstar, B_r = rank-r truncation of B:

    I.   ||A - Q B||_F^2   = ||E||^2 + ||D||^2
    II.  ||A - Q B_r||_F^2 = ||E||^2 + ||Bstar - B_r||^2
         ||Bstar - B_r||^2 = ||D||^2 + ||B - B_r||^2 + cross,  cross = -2 Re <D, B - B_r>

Both identities hold for any B, B_r once Q^H Q = I (Q^H E = 0); D = C^+ Psi E additionally
needs C to have full column rank and B to be the least-squares solution. Everything is
computed from the production functions replayed with the M4 seeds; no production code
is changed. Standard library + torch only.
"""
import csv
import hashlib
import math
import os
import statistics
import sys
import warnings

import torch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "m4_cpu"))
import m4lib  # noqa: E402  (M4 data generation, seeds and CSV helpers are reused)
from torchsketchpower import (  # noqa: E402
    construct_corange_sketch,
    construct_sketches,
    sketch_power_low_rank,
    sketch_power_subspace,
    solve_corange_coefficient,
)

SHAPE = (80, 60)
R, S, ELL = 6, 12, 24
PSI_BASE_SEED = 900000
ID_TOL = 1e-10  # identities, in units of ||A||_F^2, float64/complex128
M4_TOL = 1e-9  # relative agreement with committed M4 rows
MAX_CASES = 70
FLOAT_FIELDS = (
    "norm_a_fro e2 d2 full_lhs full_rhs id1_resid trunc_lhs tail_b2 cross bstar_minus_br2 trunc_rhs "
    "id2_resid expansion_resid opt_r2 ideal_r2 extra_vs_ideal2 rel_fro_final rel_fro_ideal_r rel_fro_opt "
    "rel_spec_final rel_spec_ideal_r rel_spec_opt e_rel e_opt_s_rel e_ratio_s d_rel qe_orth cond_c "
    "sigma_min_c sigma_max_c c_resid_rel stationarity_rel b_oracle_diff b_lstsq_diff d_formula_diff_rel "
    "id1_rel id2_rel api_rel_diff m4_rel_fro_err m4_rel_diff"
).split()

SCHEMA = {
    "sample_id": (str, False), "block": (str, False), "case": (str, False), "spectrum": (str, False),
    "dtype": (str, False), "m": (int, False), "n": (int, False), "r": (int, False), "s": (int, False),
    "ell": (int, False), "d": (int, False), "q": (int, False), "a_seed": (int, True),
    "sketch_seed": (int, False), "psi_kind": (str, False), "psi_seed": (int, True),
    "status": (str, False), "error_type": (str, True), "error_message": (str, True),
    "n_warnings": (int, False), "warning_types": (str, True), "null_reason": (str, True),
    "id1_ok": (bool, True), "id2_ok": (bool, True),
}
SCHEMA.update({k: (float, True) for k in FLOAT_FIELDS})


# ---- linear-algebra helpers -------------------------------------------------------------


def fro(x):
    return float(torch.linalg.matrix_norm(x))


def inner_re(x, y):
    """Re <x, y> = Re tr(x^H y) = Re sum conj(x) * y."""
    return float((x.conj() * y).sum().real)


def truncate(b, r):
    u, s, vh = torch.linalg.svd(b, full_matrices=False)
    return (u[:, :r] * s[:r]) @ vh[:r], s


def svd_pinv_solve(c, w):
    """Independent oracle: B = V diag(1/s) U^H W from a thin SVD of C (C must be full column rank)."""
    u, s, vh = torch.linalg.svd(c, full_matrices=False)
    return vh.mH @ ((u.mH @ w) / s[:, None])


def decompose(a, q, psi, r):
    """All diagnostics for one (A, Q, Psi, r). Raises the production errors; collects nothing else."""
    w = psi @ a
    c = psi @ q
    b = solve_corange_coefficient(q, psi, w)  # production solve; may raise / warn
    bstar = q.mH @ a
    e = a - q @ bstar
    d = b - bstar
    b_r, _ = truncate(b, r)
    bs_r, _ = truncate(bstar, r)
    na = fro(a)
    na2 = na * na
    sa = torch.linalg.svdvals(a)
    tail = lambda sv, k: float((sv[k:] ** 2).sum())  # noqa: E731
    e2 = fro(e) ** 2 / na2
    d2 = fro(d) ** 2 / na2
    full_lhs = fro(a - q @ b) ** 2 / na2
    trunc_lhs = fro(a - q @ b_r) ** 2 / na2
    tail_b2 = fro(b - b_r) ** 2 / na2
    cross = -2 * inner_re(d, b - b_r) / na2
    bmb2 = fro(bstar - b_r) ** 2 / na2
    ideal_r2 = fro(a - q @ bs_r) ** 2 / na2
    opt_r2 = tail(sa, r) / na2
    cs = torch.linalg.svdvals(c)
    resid = c @ b - w
    sa1 = float(sa[0])
    out = {
        "norm_a_fro": na, "e2": e2, "d2": d2, "full_lhs": full_lhs, "full_rhs": e2 + d2,
        "id1_resid": abs(full_lhs - (e2 + d2)), "trunc_lhs": trunc_lhs, "tail_b2": tail_b2,
        "cross": cross, "bstar_minus_br2": bmb2, "trunc_rhs": e2 + bmb2,
        "id2_resid": abs(trunc_lhs - (e2 + bmb2)),
        "expansion_resid": abs(bmb2 - (d2 + tail_b2 + cross)),
        "opt_r2": opt_r2, "ideal_r2": ideal_r2, "extra_vs_ideal2": trunc_lhs - ideal_r2,
        "rel_fro_final": math.sqrt(trunc_lhs), "rel_fro_ideal_r": math.sqrt(ideal_r2),
        "rel_fro_opt": math.sqrt(opt_r2),
        "rel_spec_final": float(torch.linalg.matrix_norm(a - q @ b_r, ord=2)) / sa1,
        "rel_spec_ideal_r": float(torch.linalg.matrix_norm(a - q @ bs_r, ord=2)) / sa1,
        "rel_spec_opt": float(sa[r]) / sa1 if sa.numel() > r else 0.0,
        "e_rel": math.sqrt(e2), "e_opt_s_rel": math.sqrt(tail(sa, q.shape[1]) / na2),
        "d_rel": math.sqrt(d2), "qe_orth": fro(q.mH @ e) / na,
        "cond_c": float(cs[0] / cs[-1]), "sigma_min_c": float(cs[-1]), "sigma_max_c": float(cs[0]),
        "c_resid_rel": fro(resid) / fro(w),
        "b_oracle_diff": fro(b - svd_pinv_solve(c, w)) / fro(b),
        "b_lstsq_diff": fro(b - torch.linalg.lstsq(c, w, driver="gelsy").solution) / fro(b),
        "d_formula_diff_rel": fro(d - svd_pinv_solve(c, psi @ e)) / max(fro(d), 1e-300),
        "stationarity_rel": None,
    }
    rn = fro(resid)
    if rn > 1e-14 * fro(w):
        out["stationarity_rel"] = fro(c.mH @ resid) / (float(cs[0]) * rn)
    nulls = []
    if out["e_opt_s_rel"] > 1e-12:
        out["e_ratio_s"] = out["e_rel"] / out["e_opt_s_rel"]
    else:
        out["e_ratio_s"] = None
        nulls.append("e_ratio_s: optimal rank-s error below floor")
    if out["stationarity_rel"] is None:
        nulls.append("stationarity_rel: consistent system, residual at noise floor")
    out["null_reason"] = "; ".join(nulls) or None
    if out["d_rel"] < 1e-10:
        out["d_formula_diff_rel"] = None
        nulls.append("d_formula_diff_rel: D at noise floor")
        out["null_reason"] = "; ".join(nulls)
    # Absolute tolerance on terms of size <= 1; relative to the largest term when terms exceed 1
    # (an ill-conditioned C can make D huge, and rounding then scales with D).
    s1 = max(1.0, full_lhs, e2 + d2)
    s2 = max(1.0, trunc_lhs, e2 + bmb2, d2, tail_b2, abs(cross))
    out["id1_rel"] = out["id1_resid"] / s1
    out["id2_rel"] = max(out["id2_resid"], out["expansion_resid"]) / s2
    out["id1_ok"] = out["id1_resid"] <= ID_TOL * s1
    out["id2_ok"] = out["id2_resid"] <= ID_TOL * s2 and out["expansion_resid"] <= ID_TOL * s2
    return out


# ---- cases --------------------------------------------------------------------------------


def _m4cfg(spectrum, q, seed_idx):
    return m4lib._cfg("A_q", spectrum, SHAPE, S, ELL, ELL, q, seed_idx)


def _tiny(kind):
    """Deterministic tiny problems for oracle and negative-control rows."""
    g = torch.Generator().manual_seed({"tiny_exact": 1, "tiny_noisy": 2, "tiny_complex": 3,
                                       "tiny_rank_def_a": 4, "tiny_dup_psi": 5, "tiny_illcond": 6}[kind])
    cplx = kind == "tiny_complex"
    dt = torch.complex128 if cplx else torch.float64

    def rnd(*shape):
        return torch.randn(*shape, generator=g, dtype=dt)

    rank = {"tiny_exact": 4, "tiny_rank_def_a": 2}.get(kind, 3)
    a = rnd(12, rank) @ rnd(rank, 9)
    if kind in ("tiny_noisy", "tiny_complex", "tiny_dup_psi", "tiny_illcond"):
        a = a + 0.1 * rnd(12, 9)
    return a


def build_cases():
    cases = []
    for sp in ("geometric", "polynomial", "flat"):  # P: baseline paired, M4 ids
        for q in (0, 1, 2):
            for i in range(5):
                c = _m4cfg(sp, q, i)
                cases.append({**c, "block": "P_baseline", "case": c["sample_id"], "psi_kind": "sequential",
                              "psi_seed": None, "kind": "m4"})
    for sp in ("flat", "geometric"):  # S: A, Q fixed (q=1, seed 0); only Psi changes
        base = _m4cfg(sp, 1, 0)
        for d in (12, 16, 24, 48):
            cases.append({**base, "block": "S_psi", "case": f"{sp}-psi-prefix-d{d}", "d": d,
                          "sample_id": f"{sp}-S-prefix-d{d}", "psi_kind": "prefix48", "psi_seed": PSI_BASE_SEED, "kind": "m4"})
        for k in (1, 2, 3):
            cases.append({**base, "block": "S_psi", "case": f"{sp}-psi-seed{k}-d24", "d": 24,
                          "sample_id": f"{sp}-S-seed{k}-d24", "psi_kind": "seeded", "psi_seed": PSI_BASE_SEED + k, "kind": "m4"})
    tiny = {"tiny_exact": ("exact", 2, 4, 8, 8, "sequential"), "tiny_noisy": ("noisy", 2, 4, 8, 8, "sequential"),
            "tiny_complex": ("noisy", 2, 4, 8, 8, "sequential"), "tiny_rank_def_a": ("rank2", 2, 4, 8, 8, "sequential"),
            "tiny_dup_psi": ("noisy", 2, 4, 8, 4, "dup_rows"), "tiny_illcond": ("noisy", 2, 4, 8, 8, "ill_cond")}
    for kind, (sp, r, s, ell, d, pk) in tiny.items():
        cases.append({"block": "O_tiny", "case": kind, "sample_id": kind, "kind": "tiny", "spectrum": sp,
                      "dtype": "complex128" if kind == "tiny_complex" else "float64", "m": 12, "n": 9, "r": r,
                      "s": s, "ell": ell, "d": d, "q": 1, "a_seed": None, "sketch_seed": 700000 + len(cases),
                      "psi_kind": pk, "psi_seed": None})
    if len(cases) > MAX_CASES:
        raise RuntimeError(f"{len(cases)} > {MAX_CASES} cases")
    return cases


def _psi_for(cfg, a, q_basis, gen):
    """Psi for the case; 'sequential' continues the sketch generator exactly like the production API."""
    m, d = a.shape[0], cfg["d"]
    kind = cfg["psi_kind"]
    if kind == "sequential":
        return construct_corange_sketch(a, d, generator=gen)[0]
    if kind == "prefix48":
        g = torch.Generator().manual_seed(cfg["psi_seed"])
        return construct_corange_sketch(a, 48, generator=g)[0][:d]
    if kind == "seeded":
        g = torch.Generator().manual_seed(cfg["psi_seed"])
        return construct_corange_sketch(a, d, generator=g)[0]
    if kind == "dup_rows":  # C = Psi Q loses rank: two identical rows, d = s
        psi = construct_corange_sketch(a, d, generator=gen)[0].clone()
        psi[1] = psi[0]
        return psi
    if kind == "ill_cond":  # prescribe C = Psi Q with singular values 1 .. 1e-9, other directions untouched
        psi0 = construct_corange_sketch(a, d, generator=gen)[0]
        s = q_basis.shape[1]
        g = torch.Generator().manual_seed(11)
        uc = torch.linalg.qr(torch.randn(d, s, generator=g, dtype=a.dtype)).Q
        vc = torch.linalg.qr(torch.randn(s, s, generator=g, dtype=a.dtype)).Q
        c = (uc * torch.tensor([1.0, 1e-3, 1e-6, 1e-9], dtype=torch.float64)) @ vc.mH
        return c @ q_basis.mH + psi0 - psi0 @ q_basis @ q_basis.mH
    raise ValueError(kind)


def run_case(cfg, m4_rows=None):
    """Run one case; every failure becomes a row. Warnings from the whole run are recorded."""
    row = {k: None for k in SCHEMA}
    for k in ("sample_id", "block", "case", "spectrum", "dtype", "m", "n", "r", "s", "ell", "d", "q",
              "a_seed", "sketch_seed", "psi_kind", "psi_seed"):
        row[k] = cfg[k]
    if cfg["kind"] == "m4":
        a, _ = m4lib.make_matrix(cfg["m"], cfg["n"], cfg["spectrum"], cfg["a_seed"])
    else:
        a = _tiny(cfg["case"])
    gen = torch.Generator().manual_seed(cfg["sketch_seed"])
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            y, z = construct_sketches(a, cfg["s"], cfg["ell"], generator=gen)
            q_basis = sketch_power_subspace(y, z, steps=cfg["q"])
            psi = _psi_for(cfg, a, q_basis, gen)
            row.update(decompose(a, q_basis, psi, cfg["r"]))
            row["status"] = "ok"
            if cfg["psi_kind"] == "sequential":
                u, sg, vh = sketch_power_low_rank(a, cfg["r"], cfg["s"], cfg["ell"], cfg["d"], steps=cfg["q"],
                                                  generator=torch.Generator().manual_seed(cfg["sketch_seed"]))
                api = fro(a - (u * sg) @ vh) / fro(a)
                row["api_rel_diff"] = abs(api - row["rel_fro_final"]) / max(api, 1e-300)
            if m4_rows is not None and cfg["sample_id"] in m4_rows and m4_rows[cfg["sample_id"]]["status"] == "ok":
                ref = m4_rows[cfg["sample_id"]]["rel_fro_err"]
                row["m4_rel_fro_err"] = ref
                row["m4_rel_diff"] = abs(row["rel_fro_final"] - ref) / ref
        except Exception as exc:
            row.update(status="error", error_type=type(exc).__name__, error_message=str(exc)[:300])
    kinds = sorted({w.category.__name__ for w in caught})
    row["n_warnings"] = len(caught)
    row["warning_types"] = ";".join(kinds) if kinds else None
    return row


# ---- schema / IO (reuse M4 machinery) ---------------------------------------------------------


def validate_rows(rows):
    return m4lib.validate_rows(rows, SCHEMA)


def write_csv(path, rows):
    return m4lib.write_csv(path, rows, SCHEMA)


def read_csv(path):
    return m4lib.read_csv(path, SCHEMA)


def load_m4_rows(path):
    return {r["sample_id"]: r for r in m4lib.read_csv(path)}


# ---- summaries ----------------------------------------------------------------------------------


def _med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def _f(v):
    return "n/a" if v is None else f"{v:.3e}"


def _ok(rows, block):
    return [r for r in rows if r["block"] == block and r["status"] == "ok"]


def stage_table(rows):
    """Block P: normalized squared error terms, grouped by (spectrum, q); medians over seeds."""
    groups = {}
    for r in _ok(rows, "P_baseline"):
        groups.setdefault((r["spectrum"], r["q"]), []).append(r)
    head = ["| spectrum | q | n | opt r^2 | ideal-Q r^2 | E^2 | D^2 | tail(B)^2 | cross | final r^2 | final-ideal | cross<0 | median cond(C) | max cond(C) |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for (sp, q), rs in groups.items():
        g = lambda k: _med([x[k] for x in rs])  # noqa: E731
        head.append(
            f"| {sp} | {q} | {len(rs)} | {_f(g('opt_r2'))} | {_f(g('ideal_r2'))} | {_f(g('e2'))} | {_f(g('d2'))} | "
            f"{_f(g('tail_b2'))} | {_f(g('cross'))} | {_f(g('trunc_lhs'))} | {_f(g('extra_vs_ideal2'))} | "
            f"{sum(x['cross'] < 0 for x in rs)}/{len(rs)} | {_f(g('cond_c'))} | {_f(max(x['cond_c'] for x in rs))} |")
    return "\n".join(head)


def psi_table(rows):
    """Block S: A and Q fixed; each row differs only in Psi."""
    head = ["| spectrum | Psi variant | d | E^2 (fixed) | D^2 | cross | final r^2 | rel Fro final | cond(C) | sigma_min(C) |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for r in _ok(rows, "S_psi"):
        head.append(f"| {r['spectrum']} | {r['case'].split('-psi-')[1]} | {r['d']} | {_f(r['e2'])} | {_f(r['d2'])} | "
                    f"{_f(r['cross'])} | {_f(r['trunc_lhs'])} | {_f(r['rel_fro_final'])} | {_f(r['cond_c'])} | {_f(r['sigma_min_c'])} |")
    return "\n".join(head)


def check_table(rows):
    ok = [r for r in rows if r["status"] == "ok"]
    mx = lambda k: max((r[k] for r in ok if r[k] is not None), default=None)  # noqa: E731
    m4d = [r["m4_rel_diff"] for r in ok if r["m4_rel_diff"] is not None]
    lines = ["| check | value |", "|---|---|",
             f"| ok / failed rows | {len(ok)} / {len(rows) - len(ok)} |",
             f"| identity I residual, max (flag tol {ID_TOL:g} x max(1, largest term)) | {_f(mx('id1_resid'))} |",
             f"| identity II residual, max (absolute) | {_f(mx('id2_resid'))} |",
             f"| identity I / II residual relative to largest term, max | {_f(mx('id1_rel'))} / {_f(mx('id2_rel'))} |",
             f"| cross-term expansion residual, max | {_f(mx('expansion_resid'))} |",
             f"| identity flags false (I / II) | {sum(r['id1_ok'] is False for r in ok)} / {sum(r['id2_ok'] is False for r in ok)} |",
             f"| Q^H E / ||A||, max | {_f(mx('qe_orth'))} |",
             f"| B vs SVD-pseudoinverse oracle, max rel diff | {_f(mx('b_oracle_diff'))} |",
             f"| B vs lstsq gelsy, max rel diff | {_f(mx('b_lstsq_diff'))} |",
             f"| D vs C^+ Psi E, max rel diff | {_f(mx('d_formula_diff_rel'))} |",
             f"| stationarity C^H(CB-W) (rel), max | {_f(mx('stationarity_rel'))} |",
             f"| replay vs sketch_power_low_rank, max rel diff | {_f(mx('api_rel_diff'))} |",
             f"| rows compared with committed M4 | {len(m4d)} |",
             f"| replay vs M4 rel Fro error, max rel diff (tol {M4_TOL:g}) | {_f(max(m4d) if m4d else None)} |"]
    return "\n".join(lines)


def failure_table(rows):
    lines = ["| case | status | error | warnings |", "|---|---|---|---|"]
    for r in rows:
        if r["status"] != "ok" or r["n_warnings"]:
            lines.append(f"| {r['case']} | {r['status']} | {r['error_type'] or '-'} | {r['warning_types'] or '-'} |")
    return "\n".join(lines)


def oracle_table(rows):
    lines = ["| case | status | E^2 | D^2 | cross | final r^2 | cond(C) | id I | id II |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if r["block"] == "O_tiny":
            lines.append(f"| {r['case']} | {r['status']} | {_f(r['e2'])} | {_f(r['d2'])} | {_f(r['cross'])} | "
                         f"{_f(r['trunc_lhs'])} | {_f(r['cond_c'])} | {_f(r['id1_resid'])} | {_f(r['id2_resid'])} |")
    return "\n".join(lines)


def summary_markdown(rows):
    return "\n".join([
        "# M5 CPU numerical diagnostics - generated summary", "",
        "Generated by `experiments/m5_cpu/run_m5.py`; all numbers are computed from `samples.csv`. "
        "Squared quantities are relative to ||A||_F^2; medians are over 5 seeds in block P. "
        "These are observations on this grid only, not explanations or population statements.", "",
        f"Cases: {len(rows)} ({sum(r['status'] == 'ok' for r in rows)} ok, {sum(r['status'] != 'ok' for r in rows)} recorded failures).", "",
        "## Identity and oracle checks", "", check_table(rows), "",
        "## Block P: error terms by stage (80x60, r=6, s=12, ell=d=24; same A and draws across q)", "", stage_table(rows), "",
        "## Block S: A and Q fixed, only Psi changes (q=1, seed 0)", "", psi_table(rows), "",
        "## Block O: tiny oracle and negative-control cases", "", oracle_table(rows), "",
        "## Failures and warnings (none hidden)", "", failure_table(rows), ""])


sha256_file = m4lib.sha256_file
