"""M4 CPU validation helpers: test matrices, exact-SVD baselines, metrics, grid, IO.

Standard library + torch only. Nothing here changes the production package; it
calls the public ``sketch_power_low_rank``. All numbers are produced by running
the code; nothing is tabulated by hand.
"""
import csv
import hashlib
import json
import math
import statistics
import warnings

import torch
from torchsketchpower import sketch_power_low_rank

TARGET_RANK = 6
SPECTRA = ("geometric", "polynomial", "flat", "exact_low_rank")
EXACT_LOW_RANK = 8  # rank of the exact_low_rank family
SPECTRUM_INDEX = {name: i for i, name in enumerate(SPECTRA)}
SHAPES = ((80, 60), (60, 80), (96, 96))
SEEDS = 5
MAX_SAMPLES = 120

# name -> (python type, nullable). CSV and JSON rows must match this exactly.
ROW_SCHEMA = {
    "sample_id": (str, False),
    "block": (str, False),
    "spectrum": (str, False),
    "m": (int, False),
    "n": (int, False),
    "rank_true": (int, False),
    "r": (int, False),
    "s": (int, False),
    "ell": (int, False),
    "d": (int, False),
    "q": (int, False),
    "dtype": (str, False),
    "a_seed": (int, False),
    "sketch_seed": (int, False),
    "status": (str, False),
    "error_type": (str, True),
    "error_message": (str, True),
    "n_warnings": (int, False),
    "warning_types": (str, True),
    "rel_fro_err": (float, True),
    "rel_spec_err": (float, True),
    "fro_opt_rel": (float, True),
    "spec_opt_rel": (float, True),
    "fro_excess_rel": (float, True),
    "fro_ratio": (float, True),
    "spec_ratio": (float, True),
    "ratio_null_reason": (str, True),
    "orth_u": (float, True),
    "orth_v": (float, True),
    "finite": (bool, True),
    "ey_ok": (bool, True),
    "est_buffer_bytes": (int, False),
}

TIMING_SCHEMA = {
    "config_id": (str, False),
    "phase": (str, False),  # cold | warm | svd_baseline_cold | svd_baseline_warm
    "repeat": (int, False),
    "seconds": (float, False),
}

MEMORY_SCHEMA = {
    "config_id": (str, False),
    "method": (str, False),
    "peak_before_call_bytes": (int, True),
    "peak_after_cold_call_bytes": (int, True),
    "peak_after_all_calls_bytes": (int, True),
    "current_after_all_calls_bytes": (int, True),
    "est_buffer_bytes": (int, False),
}


# ---- matrices and baselines ---------------------------------------------------------


def make_spectrum(kind: str, k: int) -> torch.Tensor:
    """Singular values (float64, nonincreasing, sigma_1 = 1) of length k."""
    i = torch.arange(1, k + 1, dtype=torch.float64)
    if kind == "geometric":
        return 0.7 ** (i - 1)
    if kind == "polynomial":
        return 1.0 / i
    if kind == "flat":
        return 1.0 - 0.1 * (i - 1) / max(k - 1, 1)
    if kind == "exact_low_rank":
        return torch.where(i <= EXACT_LOW_RANK, 0.7 ** (i - 1), torch.zeros_like(i))
    raise ValueError(f"unknown spectrum {kind!r}")


def make_matrix(m: int, n: int, kind: str, a_seed: int):
    """Return ``(A, sigma)``: A = U diag(sigma) Vh in float64, U, V from seeded QR."""
    k = min(m, n)
    g = torch.Generator().manual_seed(a_seed)
    u = torch.linalg.qr(torch.randn(m, k, generator=g, dtype=torch.float64)).Q
    v = torch.linalg.qr(torch.randn(n, k, generator=g, dtype=torch.float64)).Q
    sigma = make_spectrum(kind, k)
    return (u * sigma) @ v.mH, sigma


def optimal_errors(sigma: torch.Tensor, r: int):
    """Eckart-Young optimal rank-r errors ``(frobenius, spectral)`` from singular values."""
    tail = sigma[r:]
    fro = float(torch.sqrt((tail**2).sum())) if tail.numel() else 0.0
    spec = float(sigma[r]) if sigma.numel() > r else 0.0
    return fro, spec


def estimate_buffer_bytes(m, n, r, s, ell, d, steps, dtype) -> int:
    """Sum of element counts of the named buffers, times element size.

    ESTIMATE of tensor storage the pipeline allocates in total (Omega, Phi, Psi, Y, Z,
    W, one Z^H Q, QR factors, C = Psi Q, B, and the returned u, sigma, vh). It is not a
    measured peak and ignores LAPACK workspace and temporaries that are freed early.
    """
    elems = (
        n * s + n * ell + d * m  # test matrices
        + m * s + m * ell + d * n  # Y, Z, W
        + ell * s  # Z^H Q (and its Q factor, same shape)
        + ell * s
        + m * s  # Q
        + d * s  # C
        + s * n  # B
        + m * r + r + r * n  # u, sigma, vh
    )
    return int(elems * torch.empty((), dtype=dtype).element_size())


def _fro(x: torch.Tensor) -> float:
    return float(torch.linalg.matrix_norm(x))


def metrics(a64: torch.Tensor, sigma64: torch.Tensor, u, sigma, vh, r: int, ratio_floor: float):
    """Accuracy metrics of u @ diag(sigma) @ vh against a64 (all evaluated in float64)."""
    if not all(bool(torch.isfinite(t).all()) for t in (u, sigma, vh)):
        nulls = {k: None for k in ("rel_fro_err", "rel_spec_err", "fro_opt_rel", "spec_opt_rel",
                                   "fro_excess_rel", "fro_ratio", "spec_ratio", "orth_u", "orth_v", "ey_ok")}
        return dict(nulls, finite=False, ratio_null_reason="nonfinite_output")
    ahat = (u.double() * sigma.double()) @ vh.double()
    norm_f = _fro(a64)
    norm_2 = float(sigma64[0])
    err = a64 - ahat
    ef = _fro(err)
    e2 = float(torch.linalg.matrix_norm(err, ord=2))
    fro_opt, spec_opt = optimal_errors(sigma64, r)
    fro_opt_rel, spec_opt_rel = fro_opt / norm_f, spec_opt / norm_2
    out = {
        "rel_fro_err": ef / norm_f,
        "rel_spec_err": e2 / norm_2,
        "fro_opt_rel": fro_opt_rel,
        "spec_opt_rel": spec_opt_rel,
        "fro_excess_rel": ef / norm_f - fro_opt_rel,
        "orth_u": _fro(u.double().mH @ u.double() - torch.eye(r, dtype=torch.float64)),
        "orth_v": _fro(vh.double() @ vh.double().mH - torch.eye(r, dtype=torch.float64)),
        "finite": bool(all(torch.isfinite(t).all() for t in (u, sigma, vh))),
    }
    if fro_opt_rel > ratio_floor:
        out["fro_ratio"] = out["rel_fro_err"] / fro_opt_rel
        out["spec_ratio"] = out["rel_spec_err"] / spec_opt_rel if spec_opt_rel > ratio_floor else None
        out["ratio_null_reason"] = None if out["spec_ratio"] is not None else "spectral_baseline_below_floor"
    else:
        out["fro_ratio"] = out["spec_ratio"] = None
        out["ratio_null_reason"] = "baseline_below_noise_floor"
    # Eckart-Young lower bound, with a rounding allowance.
    allow = 1e-12 if ahat.dtype == torch.float64 and u.dtype == torch.float64 else 1e-6
    out["ey_ok"] = bool(
        out["rel_fro_err"] >= fro_opt_rel - allow and out["rel_spec_err"] >= spec_opt_rel - allow
    )
    return out


# ---- one sample -----------------------------------------------------------------------


def run_sample(cfg: dict) -> dict:
    """Run one configuration with the production API; failures become rows, never raise."""
    dtype = {"float64": torch.float64, "float32": torch.float32}[cfg["dtype"]]
    a64, sigma = make_matrix(cfg["m"], cfg["n"], cfg["spectrum"], cfg["a_seed"])
    a = a64.to(dtype)
    a_eff = a.double()  # the matrix the algorithm actually sees
    sigma_eff = torch.linalg.svdvals(a_eff)
    row = {k: None for k in ROW_SCHEMA}
    row.update({k: cfg[k] for k in (
        "sample_id", "block", "spectrum", "m", "n", "rank_true", "r", "s", "ell", "d", "q",
        "dtype", "a_seed", "sketch_seed")})
    row["est_buffer_bytes"] = estimate_buffer_bytes(
        cfg["m"], cfg["n"], cfg["r"], cfg["s"], cfg["ell"], cfg["d"], cfg["q"], dtype
    )
    gen = torch.Generator().manual_seed(cfg["sketch_seed"])
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            u, sg, vh = sketch_power_low_rank(
                a, cfg["r"], cfg["s"], cfg["ell"], cfg["d"],
                steps=cfg["q"], distribution="gaussian", generator=gen,
            )
            floor = 1e-8 if dtype == torch.float64 else 1e-4
            row.update(metrics(a_eff, sigma_eff, u, sg, vh, cfg["r"], floor))
            row["status"] = "ok"
        except Exception as exc:  # recorded, not filtered
            row.update(status="error", error_type=type(exc).__name__, error_message=str(exc)[:300])
    kinds = sorted({w.category.__name__ for w in caught})
    row["n_warnings"] = len(caught)
    row["warning_types"] = ";".join(kinds) if kinds else None
    return row


# ---- grid -------------------------------------------------------------------------------


def _cfg(block, spectrum, shape, s, ell, d, q, seed_idx, dtype="float64", shapes=SHAPES):
    m, n = shape
    a_seed = 10000 * SPECTRUM_INDEX[spectrum] + 100 * shapes.index(shape) + seed_idx
    return {
        "block": block, "spectrum": spectrum, "m": m, "n": n,
        "rank_true": EXACT_LOW_RANK if spectrum == "exact_low_rank" else min(m, n),
        "r": TARGET_RANK, "s": s, "ell": ell, "d": d, "q": q, "dtype": dtype,
        "a_seed": a_seed, "sketch_seed": 500000 + a_seed,
        "sample_id": f"{spectrum}-{m}x{n}-s{s}-l{ell}-d{d}-q{q}-{dtype}-seed{seed_idx}",
    }


def build_grid(seeds: int = SEEDS, shapes=SHAPES, scale: str = "full") -> list:
    """Predeclared bounded grid (deduplicated by sample_id). ``scale='full'`` => 110 samples."""
    big = (12, 24, 24)
    base = shapes[0]
    cfgs = []
    for sp in ("geometric", "polynomial", "flat"):  # A: q study, same A and same draws
        for q in (0, 1, 2):
            for i in range(seeds):
                cfgs.append(_cfg("A_q", sp, base, *big, q, i, shapes=shapes))
    for sp in ("geometric", "polynomial"):  # B: sketch sizes at q = 1
        for size in ((8, 12, 12), (8, 16, 16), (12, 16, 16), big):
            for i in range(seeds):
                cfgs.append(_cfg("B_sizes", sp, base, *size, 1, i, shapes=shapes))
    for shape in shapes[1:]:  # C: shapes at q = 1
        for i in range(seeds):
            cfgs.append(_cfg("C_shapes", "geometric", shape, *big, 1, i, shapes=shapes))
    for size in ((8, 16, 16), big):  # D: exact low rank 8 (s = 12 > rank is an expected failure)
        for i in range(seeds):
            cfgs.append(_cfg("D_exact_rank", "exact_low_rank", base, *size, 1, i, shapes=shapes))
    for q in (0, 1, 2):  # E: float32 sensitivity probe (own RNG stream, not matched)
        for i in range(seeds):
            cfgs.append(_cfg("E_float32", "geometric", base, *big, q, i, "float32", shapes=shapes))
    seen, out = set(), []
    for c in cfgs:
        if c["sample_id"] not in seen:
            seen.add(c["sample_id"])
            out.append(c)
    if scale == "full" and len(out) > MAX_SAMPLES:
        raise RuntimeError(f"grid has {len(out)} > {MAX_SAMPLES} samples")
    return out


def timing_configs():
    """Subset (seed 0, geometric) used for timing and process-isolated memory."""
    big = (12, 24, 24)
    base, wide, square = SHAPES
    items = [(base, *big, q) for q in (0, 1, 2)]
    items += [(base, *size, 1) for size in ((8, 12, 12), (8, 16, 16), (12, 16, 16))]
    items += [(wide, *big, 1), (square, *big, 1)]
    out = []
    for shape, s, ell, d, q in items:
        c = _cfg("T_timing", "geometric", shape, s, ell, d, q, 0)
        c["sample_id"] = c["sample_id"].replace("-seed0", "")
        out.append(c)
    return out


# ---- schema, IO, summary --------------------------------------------------------------------


def validate_rows(rows, schema=ROW_SCHEMA):
    """Raise ValueError unless every row has exactly the schema keys with correct types."""
    for i, row in enumerate(rows):
        if set(row) != set(schema):
            raise ValueError(f"row {i}: keys differ from schema: {set(row) ^ set(schema)}")
        for key, (typ, nullable) in schema.items():
            v = row[key]
            if v is None:
                if not nullable:
                    raise ValueError(f"row {i}: {key} must not be null")
                continue
            if typ is float:
                ok = isinstance(v, (int, float)) and not isinstance(v, bool)
                if ok and not math.isfinite(v):
                    raise ValueError(f"row {i}: {key} is not finite")
            elif typ is int:
                ok = isinstance(v, int) and not isinstance(v, bool)
            else:
                ok = isinstance(v, typ)
            if not ok:
                raise ValueError(f"row {i}: {key}={v!r} is not {typ.__name__}")
    return True


def write_csv(path, rows, schema=ROW_SCHEMA):
    validate_rows(rows, schema)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(schema), lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: ("" if row[k] is None else repr(row[k]) if isinstance(row[k], float) else row[k])
                        for k in schema})


def read_csv(path, schema=ROW_SCHEMA):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            row = {}
            for key, (typ, _) in schema.items():
                v = raw[key]
                if v == "":
                    row[key] = None
                elif typ is bool:
                    row[key] = v == "True"
                else:
                    row[key] = typ(v)
            rows.append(row)
    validate_rows(rows, schema)
    return rows


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _med(xs):
    return statistics.median(xs) if xs else None


def summarize(rows):
    """Group rows (spectrum, block, shape, sizes, q, dtype) -> median / min / max accuracy."""
    groups = {}
    for r in rows:
        key = (r["block"], r["spectrum"], r["m"], r["n"], r["s"], r["ell"], r["d"], r["q"], r["dtype"])
        groups.setdefault(key, []).append(r)
    out = []
    for key, rs in groups.items():
        ok = [x for x in rs if x["status"] == "ok"]
        fro = [x["rel_fro_err"] for x in ok]
        out.append({
            "key": key, "n": len(rs), "n_ok": len(ok), "n_fail": len(rs) - len(ok),
            "fail_types": sorted({x["error_type"] for x in rs if x["status"] != "ok"}),
            "fro_median": _med(fro), "fro_min": min(fro) if fro else None, "fro_max": max(fro) if fro else None,
            "opt_median": _med([x["fro_opt_rel"] for x in ok]),
            "ratio_median": _med([x["fro_ratio"] for x in ok if x["fro_ratio"] is not None]),
            "spec_median": _med([x["rel_spec_err"] for x in ok]),
            "spec_opt_median": _med([x["spec_opt_rel"] for x in ok]),
        })
    return out


def _f(v):
    return "n/a" if v is None else f"{v:.3e}"


def summary_markdown(rows) -> str:
    lines = ["| block | spectrum | m x n | s,ell,d | q | dtype | ok/n | fail types | median rel Fro | min..max | median opt Fro | median ratio | median rel spec | median opt spec |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for g in summarize(rows):
        b, sp, m, n, s, ell, d, q, dt = g["key"]
        lines.append(
            f"| {b} | {sp} | {m}x{n} | {s},{ell},{d} | {q} | {dt} | {g['n_ok']}/{g['n']} | "
            f"{','.join(g['fail_types']) or '-'} | {_f(g['fro_median'])} | "
            f"{_f(g['fro_min'])}..{_f(g['fro_max'])} | {_f(g['opt_median'])} | {_f(g['ratio_median'])} | "
            f"{_f(g['spec_median'])} | {_f(g['spec_opt_median'])} |"
        )
    return "\n".join(lines)


def timing_markdown(trows, mrows) -> str:
    """Per-config cold time, warm median/IQR, SVD baseline median, RSS high-water, buffer estimate."""
    def stats(vals):
        if not vals:
            return None, None
        med = statistics.median(vals)
        q = statistics.quantiles(vals, n=4) if len(vals) >= 2 else [vals[0], vals[0], vals[0]]
        return med, q[2] - q[0]

    mem = {m["config_id"]: m for m in mrows}
    lines = ["| config | cold (ms) | warm median (ms) | warm IQR (ms) | n warm | full-SVD warm median (ms) | peak WS before call (MB) | peak WS after all calls (MB) | est. buffers (KB, estimate) |",
             "|---|---|---|---|---|---|---|---|---|"]
    for cid in dict.fromkeys(t["config_id"] for t in trows):
        sel = [t for t in trows if t["config_id"] == cid]
        warm = [t["seconds"] for t in sel if t["phase"] == "warm"]
        cold = [t["seconds"] for t in sel if t["phase"] == "cold"]
        svd = [t["seconds"] for t in sel if t["phase"] == "svd_baseline_warm"]
        wm, wi = stats(warm)
        sm, _ = stats(svd)
        m = mem.get(cid)
        mb = lambda v: "n/a" if v is None else f"{v / 2**20:.1f}"  # noqa: E731
        lines.append(
            f"| {cid} | {cold[0] * 1e3:.2f} | {wm * 1e3:.3f} | {wi * 1e3:.3f} | {len(warm)} | {sm * 1e3:.3f} | "
            f"{mb(m and m['peak_before_call_bytes'])} | {mb(m and m['peak_after_all_calls_bytes'])} | "
            f"{'n/a' if m is None else f'{m['est_buffer_bytes'] / 1024:.1f}'} |"
        )
    return "\n".join(lines)


def paired_q_table(rows):
    """For block A_q: per (spectrum, seed) rel Fro error at q=0,1,2 and win counts (same A, same draws)."""
    by = {}
    for r in rows:
        if r["block"] == "A_q" and r["status"] == "ok":
            by.setdefault((r["spectrum"], r["a_seed"]), {})[r["q"]] = r["rel_fro_err"]
    table = {}
    for (sp, _), d in by.items():
        if set(d) == {0, 1, 2}:
            t = table.setdefault(sp, {"pairs": 0, "q1_lt_q0": 0, "q2_lt_q1": 0, "q2_lt_q0": 0})
            t["pairs"] += 1
            t["q1_lt_q0"] += d[1] < d[0]
            t["q2_lt_q1"] += d[2] < d[1]
            t["q2_lt_q0"] += d[2] < d[0]
    return table
