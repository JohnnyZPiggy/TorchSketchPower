import warnings

import pytest
import torch
from torchsketchpower import (
    IllConditionedWarning,
    RankDeficiencyError,
    construct_corange_sketch,
    construct_sketches,
    reconstruct_from_corange,
    sketch_power_subspace,
    solve_corange_coefficient,
)

DTYPES = [torch.float32, torch.float64, torch.complex64, torch.complex128]
# (rtol/atol scale) generous for well-conditioned problems; float32 ~ 1e-3.
TOL = {torch.float32: 1e-3, torch.complex64: 1e-3, torch.float64: 1e-9, torch.complex128: 1e-9}


def _gen(seed=0):
    return torch.Generator().manual_seed(seed)


def _randn(*shape, dtype, seed=0):
    return torch.randn(*shape, generator=_gen(seed), dtype=dtype)


def _orth(m, s, dtype, seed=0):
    return torch.linalg.qr(_randn(m, s, dtype=dtype, seed=seed), mode="reduced").Q


def _problem(m, n, s, d, dtype, seed=0):
    a = _randn(m, n, dtype=dtype, seed=seed)
    q = _orth(m, s, dtype, seed + 1)
    psi = _randn(d, m, dtype=dtype, seed=seed + 2)
    return a, q, psi, psi @ a


# ---- construct_corange_sketch -------------------------------------------------


@pytest.mark.parametrize("dtype", DTYPES)
@pytest.mark.parametrize("m,n,d", [(12, 7, 5), (7, 12, 9), (6, 6, 6)])
def test_corange_sketch_shapes_and_oracle(dtype, m, n, d):
    a = _randn(m, n, dtype=dtype)
    psi, w = construct_corange_sketch(a, d, generator=_gen(3))
    assert psi.shape == (d, m) and w.shape == (d, n)
    assert psi.dtype == dtype and w.dtype == dtype
    torch.testing.assert_close(w, psi @ a)


@pytest.mark.parametrize("dist", ["gaussian", "sparsesign"])
def test_corange_sketch_seeded_replay(dist):
    a = _randn(10, 4, dtype=torch.float64)
    p1, w1 = construct_corange_sketch(a, 6, distribution=dist, generator=_gen(5))
    p2, w2 = construct_corange_sketch(a, 6, distribution=dist, generator=_gen(5))
    p3, _ = construct_corange_sketch(a, 6, distribution=dist, generator=_gen(6))
    assert torch.equal(p1, p2) and torch.equal(w1, w2)
    assert not torch.equal(p1, p3)


def test_corange_sketch_sparse_sign_nnz():
    a = _randn(30, 4, dtype=torch.float64)
    psi, _ = construct_corange_sketch(a, 10, distribution="sparsesign", sparsity=3, generator=_gen())
    # d < m: nnz imposed per column along the short side (rows), here min(3, 10) = 3.
    assert torch.equal((psi != 0).sum(dim=0), torch.full((30,), 3))


def test_corange_sketch_noncontiguous():
    a = _randn(8, 12, dtype=torch.float64).T
    assert not a.is_contiguous()
    psi, w = construct_corange_sketch(a, 4, generator=_gen())
    torch.testing.assert_close(w, psi @ a.contiguous())


@pytest.mark.parametrize(
    "a,d,exc",
    [
        (torch.zeros(3), 2, ValueError),
        (torch.zeros(2, 3, 4), 2, ValueError),
        ([[1.0]], 1, ValueError),
        (torch.zeros(3, 3, dtype=torch.int64), 2, TypeError),
        (torch.zeros(3, 3), 0, ValueError),
        (torch.zeros(3, 3), 2.0, ValueError),
        (torch.zeros(3, 3), True, ValueError),
    ],
)
def test_corange_sketch_validation(a, d, exc):
    with pytest.raises(exc):
        construct_corange_sketch(a, d)


def test_corange_sketch_unknown_distribution():
    with pytest.raises(ValueError):
        construct_corange_sketch(torch.zeros(3, 3), 2, distribution="rademacher")


# ---- coefficient solve ----------------------------------------------------------


def _pinv_oracle(c, w):
    u, sv, vh = torch.linalg.svd(c, full_matrices=False)
    return vh.mH @ ((u.mH @ w) / sv[:, None])


@pytest.mark.parametrize("dtype", DTYPES)
@pytest.mark.parametrize("m,n,s,d", [(20, 9, 4, 7), (9, 20, 5, 5), (15, 15, 6, 12)])
def test_coefficient_matches_pinv_oracle(dtype, m, n, s, d):
    _, q, psi, w = _problem(m, n, s, d, dtype)
    b = solve_corange_coefficient(q, psi, w)
    assert b.shape == (s, n) and b.dtype == dtype
    c = psi @ q
    cond = float(torch.linalg.cond(c))
    torch.testing.assert_close(
        b, _pinv_oracle(c, w), rtol=TOL[dtype] * cond, atol=TOL[dtype] * cond
    )


@pytest.mark.parametrize("dtype", DTYPES)
def test_coefficient_normal_equations_residual(dtype):
    # A is not in range(Q): C B != W in general, but C^H (C B - W) = 0 at the optimum.
    _, q, psi, w = _problem(18, 10, 4, 9, dtype)
    c = psi @ q
    b = solve_corange_coefficient(q, psi, w)
    resid = c @ b - w
    assert float(torch.linalg.matrix_norm(resid)) > 1e-3  # genuinely inconsistent
    scale = float(torch.linalg.matrix_norm(c)) * float(torch.linalg.matrix_norm(resid))
    assert float(torch.linalg.matrix_norm(c.mH @ resid)) <= 50 * TOL[dtype] * scale


@pytest.mark.parametrize("dtype", DTYPES)
@pytest.mark.parametrize("m,n,s,d", [(16, 9, 5, 5), (10, 14, 4, 8)])
def test_exact_consistency_recovers_h(dtype, m, n, s, d):
    q = _orth(m, s, dtype, 1)
    h = _randn(s, n, dtype=dtype, seed=2)
    psi = _randn(d, m, dtype=dtype, seed=3)
    a = q @ h
    cond = float(torch.linalg.cond(psi @ q))
    tol = TOL[dtype] * cond
    b = solve_corange_coefficient(q, psi, psi @ a)
    torch.testing.assert_close(b, h, rtol=tol, atol=tol)
    r = min(s, n) - 1
    u, sg, vh = reconstruct_from_corange(q, psi, psi @ a, r)
    uo, so, vho = torch.linalg.svd(a, full_matrices=False)
    approx = (u * sg) @ vh
    oracle = (uo[:, :r] * so[:r]) @ vho[:r]
    scl = float(so[0])
    torch.testing.assert_close(approx, oracle, rtol=0, atol=tol * scl)


# ---- error decomposition --------------------------------------------------------


@pytest.mark.parametrize("dtype", DTYPES)
@pytest.mark.parametrize("m,n,s,d", [(20, 9, 4, 7), (9, 20, 5, 5), (14, 14, 6, 10)])
def test_error_decomposition(dtype, m, n, s, d):
    a, q, psi, w = _problem(m, n, s, d, dtype)
    c = psi @ q
    cond = float(torch.linalg.cond(c))
    b = solve_corange_coefficient(q, psi, w)
    e = a - q @ (q.mH @ a)
    # Independent reference: pseudoinverse through a small SVD, not lstsq.
    b_ref = q.mH @ a + _pinv_oracle(c, psi @ e)
    lhs = float(torch.linalg.matrix_norm(a - q @ b)) ** 2
    rhs = (
        float(torch.linalg.matrix_norm(e)) ** 2
        + float(torch.linalg.matrix_norm(_pinv_oracle(c, psi @ e))) ** 2
    )
    assert lhs == pytest.approx(rhs, rel=TOL[dtype] * cond * 10)
    torch.testing.assert_close(b, b_ref, rtol=TOL[dtype] * cond, atol=TOL[dtype] * cond)


# ---- truncated SVD --------------------------------------------------------------


@pytest.mark.parametrize("dtype", DTYPES)
@pytest.mark.parametrize("m,n,s,d,r", [(20, 9, 4, 7, 2), (9, 20, 5, 5, 5), (12, 12, 6, 9, 1)])
def test_truncated_svd_matches_dense(dtype, m, n, s, d, r):
    _, q, psi, w = _problem(m, n, s, d, dtype)
    b = solve_corange_coefficient(q, psi, w)
    u, sg, vh = reconstruct_from_corange(q, psi, w, r)
    assert u.shape == (m, r) and sg.shape == (r,) and vh.shape == (r, n)
    assert u.dtype == dtype and vh.dtype == dtype
    assert sg.dtype == torch.empty(0, dtype=dtype).real.dtype
    tol = TOL[dtype]
    eye = torch.eye(r, dtype=dtype)
    torch.testing.assert_close(u.mH @ u, eye, rtol=0, atol=tol)
    torch.testing.assert_close(vh @ vh.mH, eye, rtol=0, atol=tol)
    uo, so, vho = torch.linalg.svd(q @ b, full_matrices=False)
    torch.testing.assert_close(sg, so[:r], rtol=tol, atol=tol * float(so[0]))
    # Compare subspace-insensitive objects: the rank-r matrix and the left projector.
    torch.testing.assert_close(
        (u * sg) @ vh, (uo[:, :r] * so[:r]) @ vho[:r], rtol=0, atol=tol * float(so[0])
    )
    gap = float(so[r - 1] - so[r]) if r < so.numel() else 1.0
    if gap > 1e-2:
        torch.testing.assert_close(u @ u.mH, uo[:, :r] @ uo[:, :r].mH, rtol=0, atol=tol * 50)


def test_complex_uses_hermitian_adjoint():
    # Plain .T would give a wrong answer for complex data; compare against dense SVD.
    dtype = torch.complex128
    _, q, psi, w = _problem(10, 6, 3, 6, dtype, seed=7)
    u, sg, vh = reconstruct_from_corange(q, psi, w, 3)
    b = solve_corange_coefficient(q, psi, w)
    torch.testing.assert_close((u * sg) @ vh, q @ b, rtol=1e-9, atol=1e-9)
    assert float(u.imag.abs().max()) > 1e-3


def test_full_rank_r_equals_q_times_b():
    _, q, psi, w = _problem(14, 8, 5, 7, torch.float64)
    u, sg, vh = reconstruct_from_corange(q, psi, w, 5)
    torch.testing.assert_close((u * sg) @ vh, q @ solve_corange_coefficient(q, psi, w))


# ---- composition with M0/M1 -------------------------------------------------------


def test_composition_with_construct_sketches_and_power_subspace():
    g = _gen(11)
    m, n, k, s, ell, d = 60, 40, 3, 6, 12, 14
    left = _randn(m, k, dtype=torch.float64, seed=20)
    right = _randn(k, n, dtype=torch.float64, seed=21)
    a = left @ right  # exact rank k
    y, z = construct_sketches(a, s, ell, generator=g)
    q = sketch_power_subspace(y, z, steps=1, on_rank_deficient="ignore")
    psi, w = construct_corange_sketch(a, d, generator=g)
    u, sg, vh = reconstruct_from_corange(q, psi, w, k)
    # a has rank 3 < s, so range(Y) = range(a) and the recovery is exact up to rounding.
    torch.testing.assert_close((u * sg) @ vh, a, rtol=1e-6, atol=1e-6 * float(torch.linalg.matrix_norm(a, 2)))


# ---- negatives ----------------------------------------------------------------------


def test_rank_deficient_c_raises():
    _, q, psi, w = _problem(12, 6, 4, 6, torch.float64)
    psi = psi.clone()
    psi[:, :] = psi[:1, :]  # all rows equal -> rank(C) = 1 < 4
    with pytest.raises(RankDeficiencyError):
        solve_corange_coefficient(q, psi, psi @ torch.ones(12, 6, dtype=torch.float64))
    with pytest.raises(RankDeficiencyError):
        reconstruct_from_corange(q, psi, w, 2)


def test_near_rank_deficient_c_warns_or_raises():
    m, s, d, n = 20, 4, 8, 5
    q = _orth(m, s, torch.float64, 1)
    psi = _randn(d, m, dtype=torch.float64, seed=2)
    # Force C = psi @ q to have singular values spanning 1 .. 1e-9 (rank-deficient only to eps^.5).
    c = _randn(d, s, dtype=torch.float64, seed=3)
    uc, _, vhc = torch.linalg.svd(c, full_matrices=False)
    sv = torch.tensor([1.0, 1e-2, 1e-5, 1e-9], dtype=torch.float64)
    c = (uc * sv) @ vhc
    psi = c @ q.mH + psi - psi @ q @ q.mH  # psi @ q == c, other directions unchanged
    w = _randn(d, n, dtype=torch.float64, seed=4)
    torch.testing.assert_close(psi @ q, c, rtol=1e-12, atol=1e-12)
    with pytest.warns(IllConditionedWarning):
        b = solve_corange_coefficient(q, psi, w)
    assert torch.isfinite(b).all()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        solve_corange_coefficient(q, psi, w, max_condition=1e12)  # explicit threshold, no warning


def test_well_conditioned_emits_no_warning():
    _, q, psi, w = _problem(20, 8, 4, 9, torch.float64)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        reconstruct_from_corange(q, psi, w, 2)


def test_d_less_than_s():
    _, q, psi, w = _problem(12, 6, 5, 4, torch.float64)
    with pytest.raises(ValueError, match="d >= s"):
        solve_corange_coefficient(q, psi, w)


@pytest.mark.parametrize(
    "q,psi,w",
    [
        (torch.zeros(10, 3), torch.zeros(5, 9), torch.zeros(5, 4)),  # psi cols != m
        (torch.zeros(10, 3), torch.zeros(5, 10), torch.zeros(6, 4)),  # w rows != d
        (torch.zeros(10), torch.zeros(5, 10), torch.zeros(5, 4)),  # ndim
        (torch.zeros(3, 10), torch.zeros(5, 3), torch.zeros(5, 4)),  # s > m
        (torch.zeros(10, 3), torch.zeros(5, 10, dtype=torch.float64), torch.zeros(5, 4)),  # dtype
        (torch.zeros(10, 3, dtype=torch.int64),) * 3,  # non-floating
    ],
)
def test_contract_errors(q, psi, w):
    with pytest.raises((ValueError, TypeError)):
        solve_corange_coefficient(q, psi, w)


def test_non_tensor_input():
    with pytest.raises(TypeError):
        solve_corange_coefficient([[1.0]], torch.zeros(1, 1), torch.zeros(1, 1))


def test_device_mismatch():
    q = torch.zeros(4, 2)
    psi = torch.zeros(3, 4)
    w = torch.zeros(3, 2, device="meta")
    with pytest.raises(ValueError):
        solve_corange_coefficient(q, psi, w)


@pytest.mark.parametrize("r", [0, -1, 5, 3.0, True, None])
def test_invalid_r(r):
    _, q, psi, w = _problem(12, 6, 4, 7, torch.float64)  # min(s, n) = 4
    with pytest.raises(ValueError):
        reconstruct_from_corange(q, psi, w, r)


def test_r_bounded_by_n():
    _, q, psi, w = _problem(12, 2, 4, 7, torch.float64)  # n = 2 < s
    reconstruct_from_corange(q, psi, w, 2)
    with pytest.raises(ValueError):
        reconstruct_from_corange(q, psi, w, 3)


def test_non_orthonormal_q_rejected():
    _, q, psi, w = _problem(12, 6, 4, 7, torch.float64)
    with pytest.raises(ValueError, match="orthonormal"):
        solve_corange_coefficient(q * 1.01, psi, w)
    q2 = q.clone()
    q2[:, 1] = q2[:, 0]
    with pytest.raises(ValueError, match="orthonormal"):
        solve_corange_coefficient(q2, psi, w)


def test_deterministic_replay_and_finite():
    outs = []
    for _ in range(2):
        a = _randn(15, 9, dtype=torch.float64, seed=9)
        q = _orth(15, 4, torch.float64, 10)
        psi, w = construct_corange_sketch(a, 8, generator=_gen(12))
        outs.append(reconstruct_from_corange(q, psi, w, 3))
    for x, y in zip(*outs):
        assert torch.equal(x, y) and torch.isfinite(x).all()


def test_noncontiguous_inputs():
    _, q, psi, w = _problem(12, 6, 4, 7, torch.float64)
    ref = reconstruct_from_corange(q, psi, w, 2)
    qn = torch.empty(4, 12, dtype=torch.float64).T.copy_(q)
    wn = torch.empty(6, 7, dtype=torch.float64).T.copy_(w)
    assert not qn.is_contiguous() and not wn.is_contiguous()
    got = reconstruct_from_corange(qn, psi, wn, 2)
    torch.testing.assert_close(got[1], ref[1])
    torch.testing.assert_close((got[0] * got[1]) @ got[2], (ref[0] * ref[1]) @ ref[2])
