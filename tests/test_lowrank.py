import warnings

import pytest
import torch
from torchsketchpower import (
    IllConditionedWarning,
    RankDeficiencyError,
    construct_corange_sketch,
    construct_sketches,
    gaussian_test_matrix,
    reconstruct_from_corange,
    sketch_power_low_rank,
    sketch_power_subspace,
)

DTYPES = [torch.float32, torch.float64, torch.complex64, torch.complex128]
TOL = {torch.float32: 2e-3, torch.complex64: 2e-3, torch.float64: 1e-8, torch.complex128: 1e-8}


def _gen(seed=0):
    return torch.Generator().manual_seed(seed)


def _randn(*shape, dtype=torch.float64, seed=0):
    return torch.randn(*shape, generator=_gen(seed), dtype=dtype)


def _lowrank(m, n, rank, dtype, seed=0):
    return _randn(m, rank, dtype=dtype, seed=seed) @ _randn(rank, n, dtype=dtype, seed=seed + 1)


def _approx(res):
    u, sg, vh = res
    return (u * sg) @ vh


def _fro(x):
    return float(torch.linalg.matrix_norm(x))


# ---- composition oracle: new API == manual replay of M0/M1/M2 ----------------------


@pytest.mark.parametrize("dtype", DTYPES)
@pytest.mark.parametrize("steps", [0, 1, 2])
@pytest.mark.parametrize("dist,kw", [("gaussian", {}), ("sparsesign", {"sparsity": 3})])
def test_matches_manual_replay(dtype, steps, dist, kw):
    a = _lowrank(18, 12, 4, dtype) + 0.01 * _randn(18, 12, dtype=dtype, seed=5)
    s, ell, d, r = 4, 8, 9, 3
    got = sketch_power_low_rank(
        a, r, s, ell, d, steps=steps, distribution=dist, generator=_gen(7), **kw
    )
    g = _gen(7)
    y, z = construct_sketches(a, s, ell, distribution=dist, generator=g, **kw)
    q = sketch_power_subspace(y, z, steps=steps)
    psi, w = construct_corange_sketch(a, d, distribution=dist, generator=g, **kw)
    want = reconstruct_from_corange(q, psi, w, r)
    assert got[0].shape == (18, r) and got[1].shape == (r,) and got[2].shape == (r, 12)
    assert got[0].dtype == dtype and got[2].dtype == dtype
    torch.testing.assert_close(got[1], want[1])
    torch.testing.assert_close(_approx(got), _approx(want))


# ---- independent dense oracle --------------------------------------------------------


@pytest.mark.parametrize("dtype", [torch.float64, torch.complex128])
@pytest.mark.parametrize("steps", [0, 1, 2])
def test_independent_dense_oracle(dtype, steps):
    m, n, s, ell, d, r = 14, 10, 4, 7, 8, 2
    a = _lowrank(m, n, 4, dtype, seed=1) + 0.05 * _randn(m, n, dtype=dtype, seed=2)
    got = sketch_power_low_rank(a, r, s, ell, d, steps=steps, generator=_gen(3))
    # Rebuild the same random matrices, then use only dense / SVD reference algebra.
    g = _gen(3)
    omega = gaussian_test_matrix(n, s, generator=g, dtype=dtype)
    phi = gaussian_test_matrix(n, ell, generator=g, dtype=dtype)
    psi = gaussian_test_matrix(d, m, generator=g, dtype=dtype)
    y, z = a @ omega, a @ phi
    mm = z @ z.mH  # dense operator, test oracle only
    target = torch.linalg.matrix_power(mm, steps) @ y
    uq, sq, _ = torch.linalg.svd(target, full_matrices=False)
    assert float(sq[-1]) > 1e-8 * float(sq[0])  # powered range genuinely s-dimensional
    q_ref = uq
    c = psi @ q_ref
    uc, sc, vhc = torch.linalg.svd(c, full_matrices=False)
    b_ref = vhc.mH @ ((uc.mH @ (psi @ a)) / sc[:, None])
    ub, sb, vhb = torch.linalg.svd(q_ref @ b_ref, full_matrices=False)
    ref = (ub[:, :r] * sb[:r]) @ vhb[:r]
    cond = float(sc[0] / sc[-1])
    tol = 1e-9 * cond * float(sq[0] / sq[-1])
    torch.testing.assert_close(got[1], sb[:r], rtol=tol, atol=tol * float(sb[0]))
    torch.testing.assert_close(_approx(got), ref, rtol=0, atol=tol * float(sb[0]))
    # Sensible error: never worse than a loose multiple of the optimal rank-r error.
    u0, s0, vh0 = torch.linalg.svd(a, full_matrices=False)
    best = _fro(a - (u0[:, :r] * s0[:r]) @ vh0[:r])
    assert _fro(a - _approx(got)) >= best * (1 - 1e-12)  # Eckart-Young lower bound
    assert _fro(a - _approx(got)) <= 20 * best


# ---- exact low-rank recovery -----------------------------------------------------------


@pytest.mark.parametrize("dtype", DTYPES)
@pytest.mark.parametrize("steps", [0, 1, 2])
@pytest.mark.parametrize("m,n", [(20, 14), (9, 24), (12, 12)])
def test_exact_rank_s_recovery(dtype, steps, m, n):
    s, ell, d = 3, 6, 8
    a = _lowrank(m, n, s, dtype, seed=11)
    nrm = _fro(a)
    full = sketch_power_low_rank(a, s, s, ell, d, steps=steps, generator=_gen(1))
    assert _fro(a - _approx(full)) <= TOL[dtype] * nrm
    for r in (1, 2):
        got = sketch_power_low_rank(a, r, s, ell, d, steps=steps, generator=_gen(1))
        u0, s0, vh0 = torch.linalg.svd(a, full_matrices=False)
        opt = (u0[:, :r] * s0[:r]) @ vh0[:r]
        assert _fro(_approx(got) - opt) <= TOL[dtype] * nrm
        torch.testing.assert_close(got[1], s0[:r], rtol=TOL[dtype], atol=TOL[dtype] * float(s0[0]))


def test_rank_below_s_raises_by_default():
    a = _lowrank(16, 12, 2, torch.float64)
    with pytest.raises(RankDeficiencyError):
        sketch_power_low_rank(a, 2, 4, 8, 6, steps=1, generator=_gen())


def test_steps_zero_and_default_steps():
    a = _lowrank(12, 9, 3, torch.float64, seed=4)
    for kw in ({"steps": 0}, {}):
        got = sketch_power_low_rank(a, 3, 3, 6, 6, generator=_gen(2), **kw)
        assert _fro(a - _approx(got)) <= 1e-8 * _fro(a)


# ---- reproducibility ---------------------------------------------------------------------


def test_seed_reproducible_and_seed_sensitive():
    a = _randn(20, 15, seed=8)  # full rank: approximation depends on the draws
    r1 = sketch_power_low_rank(a, 2, 4, 8, 10, generator=_gen(1))
    r2 = sketch_power_low_rank(a, 2, 4, 8, 10, generator=_gen(1))
    r3 = sketch_power_low_rank(a, 2, 4, 8, 10, generator=_gen(2))
    assert torch.equal(_approx(r1), _approx(r2)) and torch.equal(r1[1], r2[1])
    assert not torch.allclose(_approx(r1), _approx(r3), rtol=1e-6, atol=1e-6)
    assert all(torch.isfinite(t).all() for t in r1)


def test_global_rng_path_runs():
    a = _lowrank(10, 8, 2, torch.float64)
    torch.manual_seed(0)
    x = sketch_power_low_rank(a, 2, 2, 4, 4)
    torch.manual_seed(0)
    y = sketch_power_low_rank(a, 2, 2, 4, 4)
    torch.testing.assert_close(_approx(x), _approx(y))


# ---- layouts and sparse-sign ------------------------------------------------------------------


def test_non_contiguous_input():
    a = _lowrank(9, 21, 3, torch.float64, seed=6).T  # (21, 9), non-contiguous
    assert not a.is_contiguous()
    got = sketch_power_low_rank(a, 3, 3, 6, 6, generator=_gen(3))
    ref = sketch_power_low_rank(a.contiguous(), 3, 3, 6, 6, generator=_gen(3))
    torch.testing.assert_close(_approx(got), _approx(ref))
    assert _fro(a - _approx(got)) <= 1e-8 * _fro(a)


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_sparsesign_exploratory_recovers_exact_low_rank(seed):
    # Fixed-nnz sparse sign (exploratory, not the paper's distribution); with
    # sparsity >= s each Omega row is dense +-1/sqrt(s), full rank for these seeds.
    a = _lowrank(24, 16, 3, torch.float64, seed=9)
    got = sketch_power_low_rank(
        a, 3, 3, 6, 8, distribution="sparsesign", sparsity=8, generator=_gen(seed)
    )
    assert _fro(a - _approx(got)) <= 1e-7 * _fro(a)


# ---- warnings and error propagation --------------------------------------------------------------


def test_conditioning_warning_is_not_masked():
    a = _lowrank(16, 10, 3, torch.float64)
    with pytest.warns(IllConditionedWarning):
        sketch_power_low_rank(a, 3, 3, 6, 6, generator=_gen(), max_condition=1.0)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        sketch_power_low_rank(a, 3, 3, 6, 8, generator=_gen(4))


def test_rank_deficient_psi_q_propagates():
    # m = s = d = 3, sparse-sign sparsity 1: Psi has one nonzero per column, so
    # Psi @ Q is rank deficient whenever two columns pick the same row.
    a = _randn(3, 6, seed=2)
    messages = []
    for seed in range(60):
        try:
            sketch_power_low_rank(
                a, 3, 3, 4, 3, distribution="sparsesign", sparsity=1, generator=_gen(seed)
            )
        except RankDeficiencyError as exc:
            messages.append(str(exc))
    assert any("psi @ q" in msg for msg in messages)


# ---- negative contract ----------------------------------------------------------------------------

_A = torch.zeros(10, 8)


@pytest.mark.parametrize(
    "a,args,kw,exc",
    [
        ([[1.0]], (1, 1, 2, 1), {}, ValueError),
        (torch.zeros(5), (1, 1, 2, 1), {}, ValueError),
        (torch.zeros(2, 3, 4), (1, 1, 2, 1), {}, ValueError),
        (torch.zeros(0, 8), (1, 1, 2, 1), {}, ValueError),
        (torch.zeros(10, 0), (1, 1, 2, 1), {}, ValueError),
        (torch.zeros(10, 8, dtype=torch.int64), (1, 1, 2, 1), {}, TypeError),
        (_A, (3, 2, 4, 2), {}, ValueError),  # r > s
        (_A, (1, 11, 12, 11), {}, ValueError),  # s > m
        (_A, (1, 3, 3, 3), {}, ValueError),  # ell <= s
        (_A, (1, 3, 2, 3), {}, ValueError),  # ell < s
        (_A, (1, 3, 6, 2), {}, ValueError),  # d < s
        (_A, (9, 9, 12, 9), {}, ValueError),  # r > n
        (_A, (0, 3, 6, 3), {}, ValueError),
        (_A, (1.0, 3, 6, 3), {}, ValueError),
        (_A, (True, 3, 6, 3), {}, ValueError),
        (_A, (1, 3, 6.0, 3), {}, ValueError),
        (_A, (1, 3, 6, None), {}, ValueError),
        (_A, (1, 3, 6, 3), {"steps": -1}, ValueError),
        (_A, (1, 3, 6, 3), {"steps": 1.0}, ValueError),
        (_A, (1, 3, 6, 3), {"steps": True}, ValueError),
        (_A, (1, 3, 6, 3), {"distribution": "rademacher"}, ValueError),
        (_A, (1, 3, 6, 3), {"distribution": None}, ValueError),
    ],
)
def test_contract_errors(a, args, kw, exc):
    with pytest.raises(exc):
        sketch_power_low_rank(a, *args, **kw)


def test_non_cpu_input_is_rejected():
    a = torch.empty(10, 8, device="meta")
    with pytest.raises(ValueError, match="CPU"):
        sketch_power_low_rank(a, 1, 3, 6, 3)


def test_zero_matrix_raises_rank_deficiency():
    with pytest.raises(RankDeficiencyError):
        sketch_power_low_rank(torch.zeros(10, 8), 1, 3, 6, 3, generator=_gen())


def test_does_not_mutate_input():
    a = _randn(12, 9, seed=3)
    before = a.clone()
    sketch_power_low_rank(a, 2, 3, 6, 5, generator=_gen())
    assert torch.equal(a, before)
