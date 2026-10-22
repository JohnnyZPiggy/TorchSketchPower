import warnings

import pytest
import torch
from torchsketchpower import RankDeficiencyError, RankDeficiencyWarning, sketch_power_subspace


def _oracle(y, z, steps):
    exact = y
    for _ in range(steps):
        exact = z @ (z.mH @ exact)
    q, _ = torch.linalg.qr(exact, mode="reduced")
    return q


def _proj_dist(a, b):
    return float(torch.linalg.matrix_norm(a @ a.mH - b @ b.mH))


@pytest.mark.parametrize("steps", [0, 1, 2])
@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_power_subspace(steps, dtype):
    g = torch.Generator().manual_seed(17)
    y = torch.randn(30, 4, generator=g, dtype=dtype)
    z = torch.randn(30, 8, generator=g, dtype=dtype)
    q = sketch_power_subspace(y, z, steps)
    torch.testing.assert_close(q.mH @ q, torch.eye(4, dtype=dtype), atol=2e-5 if dtype == torch.float32 else 1e-10, rtol=0)
    assert _proj_dist(q, _oracle(y, z, steps)) < (1e-3 if dtype == torch.float32 else 1e-8)


@pytest.mark.parametrize(
    "m,k,ell",
    [
        (30, 4, 4),   # k == ell
        (30, 4, 30),  # ell == m
        (10, 3, 15),  # ell > m (Z Z^H is still a valid m x m operator)
        (6, 6, 6),    # square, k == ell == m
    ],
)
def test_shape_edges(m, k, ell):
    g = torch.Generator().manual_seed(3)
    y = torch.randn(m, k, generator=g, dtype=torch.float64)
    z = torch.randn(m, ell, generator=g, dtype=torch.float64)
    with warnings.catch_warnings():
        warnings.simplefilter("error", RankDeficiencyWarning)
        q = sketch_power_subspace(y, z, 2)
    assert q.shape == (m, k)
    assert _proj_dist(q, _oracle(y, z, 2)) < 1e-8


@pytest.mark.parametrize("dtype", [torch.complex64, torch.complex128])
def test_complex(dtype):
    g = torch.Generator().manual_seed(5)
    y = torch.randn(40, 5, generator=g, dtype=dtype)
    z = torch.randn(40, 12, generator=g, dtype=dtype)
    q = sketch_power_subspace(y, z, 2)
    tol = 1e-4 if dtype == torch.complex64 else 1e-10
    torch.testing.assert_close(q.mH @ q, torch.eye(5, dtype=dtype), atol=tol, rtol=0)
    assert _proj_dist(q, _oracle(y, z, 2)) < tol * 10


def test_validation():
    torch.manual_seed(23)
    with pytest.raises(ValueError):
        sketch_power_subspace(torch.randn(10, 5), torch.randn(10, 3))  # k > ell
    with pytest.raises(ValueError):
        sketch_power_subspace(torch.randn(3, 5), torch.randn(3, 6))  # k > m
    with pytest.raises(ValueError):
        sketch_power_subspace(torch.randn(10, 2), torch.randn(10, 3), True)
    with pytest.raises(TypeError):
        sketch_power_subspace(torch.ones(10, 2, dtype=torch.int64), torch.ones(10, 3, dtype=torch.int64))


def _orthonormal(g, rows, cols):
    q, _ = torch.linalg.qr(torch.randn(rows, cols, generator=g, dtype=torch.float64))
    return q


def test_default_raises_when_z_rank_below_k():
    g = torch.Generator().manual_seed(11)
    y = torch.randn(12, 3, generator=g, dtype=torch.float64)
    z = torch.ones(12, 5, dtype=torch.float64)  # rank(Z) = 1 < k = 3
    with pytest.raises(RankDeficiencyError, match="rank 1 < k=3"):
        sketch_power_subspace(y, z, 1)


def test_warn_policy_z_rank_below_k():
    g = torch.Generator().manual_seed(11)
    y = torch.randn(12, 3, generator=g, dtype=torch.float64)
    z = torch.ones(12, 5, dtype=torch.float64)
    with pytest.warns(RankDeficiencyWarning, match="rank 1 < k=3"):
        q = sketch_power_subspace(y, z, 1, on_rank_deficient="warn")
    assert q.shape == (12, 3) and torch.isfinite(q).all()
    torch.testing.assert_close(q.mH @ q, torch.eye(3, dtype=torch.float64), atol=1e-10, rtol=0)
    # Only the well-defined direction span(Z) is guaranteed; the other two are arbitrary.
    u = z[:, :1] / torch.linalg.vector_norm(z[:, :1])
    assert float(torch.linalg.vector_norm(u - q @ (q.mH @ u))) < 1e-10


@pytest.mark.parametrize("policy", ["raise", "warn"])
def test_zero_cross_product(policy):
    # range(Z) is orthogonal to range(Y): Z^H Y = 0, so the powered range is {0}.
    m, k, ell = 8, 3, 4
    y = torch.zeros(m, k, dtype=torch.float64)
    y[5:, :] = torch.eye(k, dtype=torch.float64)
    z = torch.zeros(m, ell, dtype=torch.float64)
    z[:4, :] = torch.eye(4, dtype=torch.float64)
    if policy == "raise":
        with pytest.raises(RankDeficiencyError, match="rank 0 < k=3"):
            sketch_power_subspace(y, z, 1)
    else:
        with pytest.warns(RankDeficiencyWarning, match="rank 0 < k=3"):
            sketch_power_subspace(y, z, 1, on_rank_deficient="warn")


def _graded_z(delta):
    # y = u and z = u diag(1, 1, delta) v^T give z^H q with singular values (1, 1, delta).
    g = torch.Generator().manual_seed(29)
    u, v = _orthonormal(g, 20, 3), _orthonormal(g, 7, 3)
    z = (u * torch.tensor([1.0, 1.0, delta], dtype=torch.float64)) @ v.T
    return u.clone(), z


def test_near_rank_deficient_above_tolerance_is_accepted():
    y, z = _graded_z(1e-3)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        q = sketch_power_subspace(y, z, 1)
    assert _proj_dist(q, _oracle(y, z, 1)) < 1e-8


def test_near_rank_deficient_below_tolerance_is_rejected():
    y, z = _graded_z(1e-17)  # tolerance is about 7 * eps ~ 1.6e-15
    with pytest.raises(RankDeficiencyError, match="rank 2 < k=3"):
        sketch_power_subspace(y, z, 1)


@pytest.mark.parametrize("steps", [0, 1])
def test_rank_deficient_y_raises(steps):
    g = torch.Generator().manual_seed(13)
    col = torch.randn(10, 1, generator=g, dtype=torch.float64)
    y = torch.cat([col, 2 * col], dim=1)  # numerical rank 1 < k = 2
    z = torch.randn(10, 4, generator=g, dtype=torch.float64)
    with pytest.raises(RankDeficiencyError, match="y has numerical rank 1"):
        sketch_power_subspace(y, z, steps)


def test_subspace_rank_loss_at_later_step():
    # y has full rank, but Z^H y keeps only 2 directions of a 3-dimensional y.
    g = torch.Generator().manual_seed(31)
    u = _orthonormal(g, 10, 5)
    y = u[:, :3]
    z = u[:, :2] @ _orthonormal(g, 6, 2).T  # rank(Z) = 2 < k = 3
    with pytest.raises(RankDeficiencyError, match=r"z\.mH @ q at step 1"):
        sketch_power_subspace(y, z, 2)


def test_ignore_policy_is_silent():
    torch.manual_seed(19)
    z = torch.ones(12, 5, dtype=torch.float64)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        sketch_power_subspace(torch.randn(12, 3, dtype=torch.float64), z, 1, on_rank_deficient="ignore")


def test_invalid_policy():
    with pytest.raises(ValueError, match="on_rank_deficient"):
        sketch_power_subspace(torch.randn(10, 2), torch.randn(10, 3), 1, on_rank_deficient="silent")


def test_float32_stable_vs_float64():
    g = torch.Generator().manual_seed(7)
    m, n = 120, 80
    u, _ = torch.linalg.qr(torch.randn(m, n, generator=g, dtype=torch.float64))
    v, _ = torch.linalg.qr(torch.randn(n, n, generator=g, dtype=torch.float64))
    s = 10.0 ** (-torch.arange(n, dtype=torch.float64) / 20)
    a = (u * s) @ v.T
    y = a @ torch.randn(n, 6, generator=g, dtype=torch.float64)
    z = a @ torch.randn(n, 18, generator=g, dtype=torch.float64)
    q64 = sketch_power_subspace(y, z, 3)
    q32 = sketch_power_subspace(y.float(), z.float(), 3)
    assert _proj_dist(q32.double(), q64) < 1e-4
