import warnings

import pytest
import torch
from torchsketchpower import RankDeficiencyWarning, sketch_power_subspace


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


def test_rank_deficient_z_warns():
    g = torch.Generator().manual_seed(11)
    y = torch.randn(12, 3, generator=g, dtype=torch.float64)
    z = torch.ones(12, 5, dtype=torch.float64)  # rank(Z) = 1 < k = 3
    with pytest.warns(RankDeficiencyWarning, match="rank 1 < k=3"):
        q = sketch_power_subspace(y, z, 1)
    assert torch.isfinite(q).all()
    # The well-defined part (span of Z) is still contained in the output.
    u = z[:, :1] / torch.linalg.vector_norm(z[:, :1])
    assert float(torch.linalg.vector_norm(u - q @ (q.mH @ u))) < 1e-10


def test_rank_deficient_y_warns_at_q0():
    torch.manual_seed(13)
    y = torch.ones(10, 2, dtype=torch.float64)
    z = torch.randn(10, 4, dtype=torch.float64)
    with pytest.warns(RankDeficiencyWarning):
        sketch_power_subspace(y, z, 0)


def test_check_rank_off_is_silent():
    torch.manual_seed(19)
    z = torch.ones(12, 5, dtype=torch.float64)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        sketch_power_subspace(torch.randn(12, 3, dtype=torch.float64), z, 1, check_rank=False)


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
