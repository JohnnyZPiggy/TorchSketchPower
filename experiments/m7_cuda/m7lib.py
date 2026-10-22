"""M7 device-correctness oracles (O1 to O6 of docs/gpu-readiness.md), runnable on any supported device.

The same functions are exercised on the CPU (to validate the oracle logic itself) and, in a real
CUDA environment, on the GPU. A CPU run is never GPU evidence: every result row records the device it
ran on. Tolerances are pre-registered below from standard backward-error arguments, not fitted to
observed GPU results; every row also stores the observed error, the tolerance and their ratio
(``margin``) so reviewers can see how close a result is.

Standard library + torch only.
"""
import contextlib
import math
import os
import sys
import warnings

import torch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "m4_cpu"))
import m4lib  # noqa: E402  (spectrum definitions)
from torchsketchpower import (  # noqa: E402
    IllConditionedWarning,
    RankDeficiencyError,
    construct_corange_sketch,
    construct_sketches,
    reconstruct_from_corange,
    sketch_power_low_rank,
    sketch_power_subspace,
    solve_corange_coefficient,
)

PASS, FAIL, BLOCKED, NOT_RUN = "PASS", "FAIL", "BLOCKED", "NOT_RUN"
C_BWD = 50.0  # constant in the backward-error tolerances (pre-registered, see tolerance docstrings)
DTYPES = (torch.float32, torch.float64, torch.complex64, torch.complex128)
WIDE = {torch.float32: torch.float64, torch.float64: torch.float64,
        torch.complex64: torch.complex128, torch.complex128: torch.complex128}


def eps_of(dtype):
    return float(torch.finfo(torch.empty((), dtype=dtype).real.dtype).eps)


def fro(x):
    return float(torch.linalg.matrix_norm(x))


def _row(case, device, dtype, **kw):
    row = {"case": case, "device": str(device), "dtype": str(dtype).replace("torch.", ""), "status": NOT_RUN}
    row.update(kw)
    return row


# ---- problem construction (on the CPU, deterministic, then moved to the device) ------------------


def _randn(g, *shape, dtype):
    return torch.randn(*shape, generator=g, dtype=dtype)


def make_problem(m, n, s, d, dtype, cond, seed):
    """Orthonormal Q, designed C = Psi Q with singular values 1 .. 1/cond, A = Q B* + E, W = Psi A.

    Built in the wide dtype on the CPU and then cast, so C has the designed condition number up to
    the rounding of the cast (the tolerances use the condition number measured after the cast).
    """
    wide = WIDE[dtype]
    g = torch.Generator().manual_seed(seed)
    q = torch.linalg.qr(_randn(g, m, s, dtype=wide)).Q
    ub = torch.linalg.qr(_randn(g, s, s, dtype=wide)).Q
    vb = torch.linalg.qr(_randn(g, n, min(s, n), dtype=wide)).Q
    k = min(s, n)
    sb = 0.5 ** torch.arange(k, dtype=torch.float64)
    bstar = (ub[:, :k] * sb.to(wide)) @ vb.mH
    gm = _randn(g, m, n, dtype=wide)
    e = 0.1 * (gm - q @ (q.mH @ gm))
    a = q @ bstar + e
    uc = torch.linalg.qr(_randn(g, d, s, dtype=wide)).Q
    vc = torch.linalg.qr(_randn(g, s, s, dtype=wide)).Q
    sv = torch.logspace(0, -math.log10(cond), s, dtype=torch.float64).to(wide)
    c_design = (uc * sv) @ vc.mH
    psi0 = _randn(g, d, m, dtype=wide)
    psi = c_design @ q.mH + psi0 - psi0 @ q @ q.mH
    w = psi @ a
    return tuple(t.to(dtype) for t in (a, q, psi, w))


def make_matrix(m, n, spectrum, seed, dtype):
    wide = WIDE[dtype]
    k = min(m, n)
    g = torch.Generator().manual_seed(seed)
    u = torch.linalg.qr(_randn(g, m, k, dtype=wide)).Q
    v = torch.linalg.qr(_randn(g, n, k, dtype=wide)).Q
    sigma = m4lib.make_spectrum(spectrum, k).to(wide)
    return ((u * sigma) @ v.mH).to(dtype), m4lib.make_spectrum(spectrum, k)


# ---- device-residency spy ------------------------------------------------------------------------


@contextlib.contextmanager
def transfer_spy():
    """Count host transfers (`.cpu()`, `.numpy()`, `.tolist()`, `.to(cpu)`) made inside the block.

    Scalar reads (`.item()`, `float(t)`) are allowed and expected: the rank gates use them for
    control flow and thereby synchronize the device.
    """
    calls = []
    saved = {n: getattr(torch.Tensor, n) for n in ("cpu", "numpy", "tolist", "to")}

    def wrap(name):
        def f(self, *a, **k):
            calls.append(name)
            return saved[name](self, *a, **k)
        return f

    def to(self, *a, **k):
        target = k.get("device", a[0] if a else None)
        if isinstance(target, str):
            target = torch.device(target)
        if isinstance(target, torch.device) and target.type == "cpu" and self.device.type != "cpu":
            calls.append("to(cpu)")
        return saved["to"](self, *a, **k)

    try:
        for n in ("cpu", "numpy", "tolist"):
            setattr(torch.Tensor, n, wrap(n))
        torch.Tensor.to = to
        yield calls
    finally:
        for n, f in saved.items():
            setattr(torch.Tensor, n, f)


def _svd_pinv(c, w):
    u, sv, vh = torch.linalg.svd(c, full_matrices=False)
    return vh.mH @ ((u.mH @ w) / sv[:, None])


def _guard(fn, row):
    """Run fn(row); unsupported-operation errors become BLOCKED rows, anything else FAIL, never silent."""
    try:
        fn(row)
    except (NotImplementedError, RuntimeError) as exc:
        row.update(status=BLOCKED, reason=f"{type(exc).__name__}: {str(exc)[:200]}")
    except Exception as exc:  # noqa: BLE001
        row.update(status=FAIL, reason=f"{type(exc).__name__}: {str(exc)[:200]}")
    return row


# ---- O1 + O2 + O3: coefficient, normal equations, truncated SVD --------------------------------------


def coefficient_case(device, dtype, m, n, s, d, cond, seed, r=None):
    """Coefficient B and rank-r reconstruction against SVD-pseudoinverse oracles.

    Tolerances (pre-registered; kappa = cond(C) measured on the transferred C, rho = ||Cx-W|| /
    (||C||_2 ||x||) with x the reference solution, eps the unit roundoff of the input dtype):
      O1  ||B - B_ref||_F / ||B_ref||_F <= 50 eps (kappa + kappa^2 rho)      (least-squares forward error)
      O1' against the same SVD pseudoinverse computed on the device: <= 2 x the bound above
      O2  ||C^H (C B - W)||_F <= 50 eps ||C||_2 (||C||_2 ||B||_F + ||W||_F)  (normal-equation residual)
      O3  |sigma_i(B) - sigma_i(B_ref)| <= ||B - B_ref||_F + 50 eps sigma_1     (Weyl)
          ||B_r - B_ref,r||_F <= 50 (||B - B_ref||_F + eps ||B_ref||_F) (1 + sigma_1/gap)
    """
    r = r or max(1, s // 2)
    row = _row("coefficient", device, dtype, m=m, n=n, s=s, d=d, r=r, cond_designed=cond, seed=seed)
    eps = eps_of(dtype)

    def body(row):
        a, q, psi, w = (t.to(device) for t in make_problem(m, n, s, d, dtype, cond, seed))
        wide = WIDE[dtype]
        with warnings.catch_warnings(record=True) as caught, transfer_spy() as calls:
            warnings.simplefilter("always")
            b = solve_corange_coefficient(q, psi, w)
            u, sig, vh = reconstruct_from_corange(q, psi, w, r)
        row["warnings"] = sorted({x.category.__name__ for x in caught})
        row["host_transfers"] = list(calls)
        row["resident"] = all(t.device == q.device for t in (b, u, sig, vh)) and not calls
        c_dev = psi @ q
        c64, w64, q64 = (t.cpu().to(wide) for t in (c_dev, w, q))  # oracle path: transfers allowed here
        ref = _svd_pinv(c64, w64)
        ref_dev = _svd_pinv(c_dev, w)
        b64 = b.cpu().to(wide)
        sc = torch.linalg.svdvals(c64)
        kappa = float(sc[0] / sc[-1])
        resid = fro(c64 @ ref - w64)
        rho = resid / (float(sc[0]) * fro(ref))
        tol1 = C_BWD * eps * (kappa + kappa**2 * rho)
        err1 = fro(b64 - ref) / fro(ref)
        err1d = fro(b64 - ref_dev.cpu().to(wide)) / fro(ref)
        ne = fro(c64.mH @ (c64 @ b64 - w64))
        tol2 = C_BWD * eps * float(sc[0]) * (float(sc[0]) * fro(b64) + fro(w64))
        # O3: the truncated SVD of B
        sb = torch.linalg.svdvals(b64)
        sr = torch.linalg.svdvals(ref)
        errb = fro(b64 - ref)
        sv_err = float((sb[:r] - sr[:r]).abs().max())
        sv_tol = errb + C_BWD * eps * float(sr[0])
        ub, sbb, vhb = torch.linalg.svd(ref, full_matrices=False)
        ref_r = (ub[:, :r] * sbb[:r]) @ vhb[:r]
        got_r = (u.cpu().to(wide) * sig.cpu().to(wide)) @ vh.cpu().to(wide)
        # u, vh come from the device SVD of B; compare the rank-r matrices Q B_r (Q has orthonormal columns)
        gap = float(sr[r - 1] - sr[r]) if r < sr.numel() else float(sr[r - 1])
        mat_err = fro(ref_r - q64.mH @ got_r)
        mat_tol = C_BWD * (errb + eps * fro(ref)) * (1 + float(sr[0]) / max(gap, 1e-300))
        orth_u = fro(u.mH @ u - torch.eye(r, dtype=u.dtype, device=u.device))
        orth_v = fro(vh @ vh.mH - torch.eye(r, dtype=vh.dtype, device=vh.device))
        orth_tol = 1e3 * eps
        row.update(
            kappa=kappa, rho=rho, err_cpu64=err1, tol_o1=tol1, margin_o1=err1 / tol1, err_dev_pinv=err1d,
            ne_residual=ne, tol_o2=tol2, margin_o2=ne / tol2, sv_err=sv_err, sv_tol=sv_tol,
            matrix_err=mat_err, matrix_tol=mat_tol, margin_o3=mat_err / mat_tol,
            orth_u=orth_u, orth_v=orth_v, orth_tol=orth_tol,
        )
        ok = (err1 <= tol1 and err1d <= 2 * tol1 and ne <= tol2 and sv_err <= sv_tol
              and mat_err <= mat_tol and orth_u <= orth_tol and orth_v <= orth_tol and row["resident"]
              and bool(torch.isfinite(b).all()))
        row["status"] = PASS if ok else FAIL

    return _guard(body, row)


# ---- O4: end to end -------------------------------------------------------------------------------------


def end_to_end_mode_a(device, dtype, m, n, spectrum, seed, q_steps, r=3, s=6, ell=12, d=12):
    """Mode A: sketches drawn on the CPU and transferred, so the device and CPU see identical inputs.

    The reference is the production CPU pipeline run in the wide dtype on the same sketches. Tolerance:
    1e3 eps (1 + kappa_Y)(1 + kappa_C + kappa_C^2 rho)(1 + sigma_1/gap) on the relative Frobenius
    difference of the final rank-r matrices (pre-registered; kappa_Y = cond(Y), kappa_C = cond(Psi Q)).
    """
    row = _row("end_to_end_A", device, dtype, m=m, n=n, spectrum=spectrum, seed=seed, q=q_steps, r=r, s=s, ell=ell, d=d)
    eps = eps_of(dtype)

    def body(row):
        wide = WIDE[dtype]
        a_cpu, _ = make_matrix(m, n, spectrum, seed, dtype)
        g = torch.Generator().manual_seed(1000 + seed)
        y, z = construct_sketches(a_cpu, s, ell, generator=g)
        psi, w = construct_corange_sketch(a_cpu, d, generator=g)
        # reference on the CPU in the wide dtype
        y64, z64, psi64, w64 = (t.to(wide) for t in (y, z, psi, w))
        q64 = sketch_power_subspace(y64, z64, steps=q_steps)
        u64, s64, vh64 = reconstruct_from_corange(q64, psi64, w64, r)
        ref = (u64 * s64) @ vh64
        # device pipeline on the transferred sketches
        yd, zd, psid, wd = (t.to(device) for t in (y, z, psi, w))
        with warnings.catch_warnings(record=True) as caught, transfer_spy() as calls:
            warnings.simplefilter("always")
            qd = sketch_power_subspace(yd, zd, steps=q_steps)
            ud, sd, vhd = reconstruct_from_corange(qd, psid, wd, r)
        row["warnings"] = sorted({x.category.__name__ for x in caught})
        row["host_transfers"] = list(calls)
        row["resident"] = not calls and all(t.device == yd.device for t in (qd, ud, sd, vhd))
        got = ((ud * sd) @ vhd).cpu().to(wide)
        diff = fro(got - ref) / fro(ref)
        ky = float(torch.linalg.cond(y64))
        c64 = psi64 @ q64
        sc = torch.linalg.svdvals(c64)
        kc = float(sc[0] / sc[-1])
        x = _svd_pinv(c64, w64)
        rho = fro(c64 @ x - w64) / (float(sc[0]) * fro(x))
        sr = torch.linalg.svdvals(x)
        gap = float(sr[r - 1] - sr[r]) if r < sr.numel() else float(sr[r - 1])
        tol = 1e3 * eps * (1 + ky) * (1 + kc + kc**2 * rho) * (1 + float(sr[0]) / max(gap, 1e-300))
        row.update(rel_diff=diff, tol=tol, margin=diff / tol, kappa_y=ky, kappa_c=kc, rho=rho)
        row["status"] = PASS if (diff <= tol and row["resident"]) else FAIL

    return _guard(body, row)


def _identities(a, q, psi, r):
    """M5 identities I and II and the signed cross term on the device, in the wide dtype."""
    wide = WIDE[a.dtype]
    a, q, psi = a.to(wide), q.to(wide), psi.to(wide)
    w = psi @ a
    c = psi @ q
    b = _svd_pinv(c, w)
    bstar = q.mH @ a
    e = a - q @ bstar
    dd = b - bstar
    ub, sb, vhb = torch.linalg.svd(b, full_matrices=False)
    b_r = (ub[:, :r] * sb[:r]) @ vhb[:r]
    na2 = fro(a) ** 2
    full = fro(a - q @ b) ** 2 / na2
    trunc = fro(a - q @ b_r) ** 2 / na2
    e2, d2 = fro(e) ** 2 / na2, fro(dd) ** 2 / na2
    bmb2 = fro(bstar - b_r) ** 2 / na2
    tail = fro(b - b_r) ** 2 / na2
    cross = -2 * float((dd.conj() * (b - b_r)).sum().real) / na2
    s1 = max(1.0, full, e2 + d2)
    s2 = max(1.0, trunc, e2 + bmb2, d2, tail, abs(cross))
    return {"id1_rel": abs(full - (e2 + d2)) / s1, "id2_rel": abs(trunc - (e2 + bmb2)) / s2,
            "expansion_rel": abs(bmb2 - (d2 + tail + cross)) / s2, "cross": cross, "e2": e2, "d2": d2}


def end_to_end_mode_b(device, dtype, m, n, spectrum, seed, q_steps, r=3, s=6, ell=12, d=12):
    """Mode B: device-local random draws. Only invariants are tested (no CPU/GPU element comparison)."""
    row = _row("end_to_end_B", device, dtype, m=m, n=n, spectrum=spectrum, seed=seed, q=q_steps, r=r, s=s, ell=ell, d=d)
    eps = eps_of(dtype)

    def body(row):
        a_cpu, sigma = make_matrix(m, n, spectrum, seed, dtype)
        a = a_cpu.to(device)
        gen = torch.Generator(device=a.device if a.device.type == "cuda" else "cpu").manual_seed(5000 + seed)
        with warnings.catch_warnings(record=True) as caught, transfer_spy() as calls:
            warnings.simplefilter("always")
            u, sg, vh = sketch_power_low_rank(a, r, s, ell, d, steps=q_steps, generator=gen)
        row["warnings"] = sorted({x.category.__name__ for x in caught})
        row["host_transfers"] = list(calls)
        row["resident"] = not calls and all(t.device == a.device for t in (u, sg, vh))
        # replay the same draws on the device with the lower-level production functions (invariants need Q, Psi)
        g2 = torch.Generator(device=gen.device).manual_seed(5000 + seed)
        y, z = construct_sketches(a, s, ell, generator=g2)
        qd = sketch_power_subspace(y, z, steps=q_steps)
        psi, _ = construct_corange_sketch(a, d, generator=g2)
        ident = _identities(a, qd, psi, r)
        wide = WIDE[dtype]
        approx = ((u * sg) @ vh).to(wide)
        err = fro(a.to(wide) - approx)
        norm_a = fro(a.to(wide))
        tail = sigma[r:].double()
        opt = float(torch.sqrt((tail**2).sum())) if tail.numel() else 0.0
        tol_id = 1e3 * eps
        replay_u, replay_s, replay_vh = reconstruct_from_corange(qd, psi, psi @ a, r)
        replay_diff = fro(((replay_u * replay_s) @ replay_vh).to(wide) - approx) / norm_a
        row.update(ident, rel_fro=err / norm_a, rel_fro_opt=opt / float(torch.sqrt((sigma.double() ** 2).sum())),
                   replay_diff=replay_diff, tol_identity=tol_id,
                   orth_u=fro(u.mH @ u - torch.eye(r, dtype=u.dtype, device=u.device)))
        ok = (ident["id1_rel"] <= tol_id and ident["id2_rel"] <= tol_id and ident["expansion_rel"] <= tol_id
              and err / norm_a >= (opt / float(torch.sqrt((sigma.double() ** 2).sum()))) * (1 - tol_id)
              and replay_diff <= tol_id and row["orth_u"] <= tol_id and bool(torch.isfinite(u).all())
              and bool(torch.isfinite(sg).all()) and row["resident"])
        row["status"] = PASS if ok else FAIL

    return _guard(body, row)


# ---- O5: negative controls -------------------------------------------------------------------------------


def _expect(case, device, dtype, fn, exc=None, warn=None):
    row = _row(case, device, dtype, expected=(exc.__name__ if exc else f"warning {warn.__name__}"))
    with warnings.catch_warnings(record=True) as caught, transfer_spy() as calls:
        warnings.simplefilter("always")
        try:
            out = fn()
            raised = None
        except Exception as e:  # noqa: BLE001
            out, raised = None, e
    row["host_transfers"] = list(calls)
    row["observed"] = type(raised).__name__ if raised else "no exception"
    row["warnings"] = sorted({x.category.__name__ for x in caught})
    if exc is not None:
        wrong_subclass = exc is ValueError and isinstance(raised, RankDeficiencyError)
        row["status"] = PASS if (isinstance(raised, exc) and not wrong_subclass and not calls) else FAIL
    else:
        finite = out is not None and all(bool(torch.isfinite(t).all()) for t in (out if isinstance(out, tuple) else (out,)))
        row["status"] = PASS if (raised is None and warn.__name__ in row["warnings"] and finite and not calls) else FAIL
    if raised is not None:
        row["message"] = str(raised)[:160]
    return row


def negative_cases(device):
    out = []
    dev = torch.device(device)
    is_cuda = dev.type == "cuda"
    for dtype in (torch.float64, torch.float32, torch.complex128):
        eps = eps_of(dtype)
        a, q, psi, w = (t.to(dev) for t in make_problem(30, 20, 5, 9, dtype, 10.0, 1))
        g = lambda seed=0: torch.Generator(device=dev.type if dev.type == "cuda" else "cpu").manual_seed(seed)  # noqa: E731
        low = (torch.randn(30, 2, generator=torch.Generator().manual_seed(2), dtype=dtype)
               @ torch.randn(2, 20, generator=torch.Generator().manual_seed(3), dtype=dtype)).to(dev)
        out.append(_expect("rank(A) < s", dev, dtype, lambda: sketch_power_low_rank(low, 2, 5, 10, 8, generator=g()), RankDeficiencyError))
        # exactly rank-deficient C: two identical rows of Psi with d = s
        a2, q2, psi2, w2 = (t.to(dev) for t in make_problem(30, 20, 5, 5, dtype, 10.0, 4))
        psi2 = psi2.clone()
        psi2[1] = psi2[0]
        out.append(_expect("C exactly rank deficient (duplicate Psi row)", dev, dtype,
                           lambda: solve_corange_coefficient(q2, psi2, psi2 @ a2), RankDeficiencyError))
        # designed rank deficiency below the gate: sigma_min / sigma_max = 1e-3 * (shape factor) * eps
        bad_cond = 1.0 / (30 * eps * 1e-3)
        a3, q3, psi3, w3 = (t.to(dev) for t in make_problem(30, 20, 5, 9, dtype, bad_cond, 5))
        out.append(_expect("C numerically rank deficient (designed)", dev, dtype,
                           lambda: solve_corange_coefficient(q3, psi3, w3), RankDeficiencyError))
        # ill-conditioned but valid: above eps^(-1/2), below the rank gate
        warn_cond = 10.0 ** (math.log10(1 / math.sqrt(eps)) + 1.0)
        a4, q4, psi4, w4 = (t.to(dev) for t in make_problem(30, 20, 5, 9, dtype, warn_cond, 6))
        out.append(_expect("ill-conditioned full-rank C warns", dev, dtype,
                           lambda: solve_corange_coefficient(q4, psi4, w4), warn=IllConditionedWarning))
        out.append(_expect("non-orthonormal Q", dev, dtype, lambda: solve_corange_coefficient(q * 1.01, psi, w), ValueError))
        other = torch.float64 if dtype == torch.float32 else torch.float32
        if not dtype.is_complex:
            out.append(_expect("dtype mismatch", dev, dtype, lambda: solve_corange_coefficient(q, psi.to(other), w), ValueError))
        out.append(_expect("d < s", dev, dtype, lambda: sketch_power_low_rank(a, 2, 5, 10, 4, generator=g()), ValueError))
        out.append(_expect("invalid r", dev, dtype, lambda: sketch_power_low_rank(a, 6, 5, 10, 8, generator=g()), ValueError))
    meta = torch.empty(10, 8, dtype=torch.float64, device="meta")
    out.append(_expect("unsupported device type (meta)", dev, torch.float64, lambda: sketch_power_low_rank(meta, 1, 3, 6, 3), ValueError))
    if is_cuda:
        a = make_problem(30, 20, 5, 9, torch.float64, 10.0, 1)[0]
        out.append(_expect("CPU generator with CUDA input", dev, torch.float64,
                           lambda: sketch_power_low_rank(a.to(dev), 2, 5, 10, 8, generator=torch.Generator().manual_seed(0)), ValueError))
        out.append(_expect("sparsesign on CUDA (not validated)", dev, torch.float64,
                           lambda: sketch_power_low_rank(a.to(dev), 2, 5, 10, 8, distribution="sparsesign", generator=torch.Generator(device=dev.type).manual_seed(0)), ValueError))
        q_, psi_, w_ = (t for t in make_problem(30, 20, 5, 9, torch.float64, 10.0, 1)[1:])
        out.append(_expect("mixed CPU and CUDA tensors", dev, torch.float64,
                           lambda: solve_corange_coefficient(q_.to(dev), psi_, w_.to(dev)), ValueError))
        if torch.cuda.device_count() > 1:
            out.append(_expect("mixed CUDA indices", dev, torch.float64,
                               lambda: solve_corange_coefficient(q_.to("cuda:0"), psi_.to("cuda:1"), w_.to("cuda:0")), ValueError))
        else:
            out.append(_row("mixed CUDA indices", dev, torch.float64, status=NOT_RUN, reason="only one CUDA device"))
    else:
        for name in ("CPU generator with CUDA input", "sparsesign on CUDA (not validated)", "mixed CPU and CUDA tensors", "mixed CUDA indices"):
            out.append(_row(name, dev, torch.float64, status=NOT_RUN, reason="needs a CUDA device"))
    return out
