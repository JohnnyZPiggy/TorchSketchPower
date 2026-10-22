import pytest
import torch
from torchsketchpower import (
    construct_sketches,
    gaussian_test_matrix,
    sparse_sign_test_matrix,
    test_matrix,
)


def _gen(seed=0):
    return torch.Generator().manual_seed(seed)


def test_gaussian_shape_dtype_and_moments():
    x = gaussian_test_matrix(400, 50, generator=_gen(), dtype=torch.float32)
    assert x.shape == (400, 50) and x.dtype == torch.float32
    assert abs(float(x.mean())) < 0.05 and abs(float(x.std()) - 1) < 0.05


@pytest.mark.parametrize("rows,cols", [(40, 5), (5, 40), (6, 6), (3, 20), (20, 3)])
@pytest.mark.parametrize("sparsity", [1, 4, 8])
def test_sparse_sign_structure(rows, cols, sparsity):
    x = sparse_sign_test_matrix(rows, cols, sparsity=sparsity, generator=_gen(1))
    assert x.shape == (rows, cols)
    nnz = min(sparsity, min(rows, cols))
    lines = x if rows >= cols else x.T  # each line runs along the short side
    assert torch.equal((lines != 0).sum(dim=1), torch.full((lines.shape[0],), nnz))
    nz = x[x != 0].abs()
    torch.testing.assert_close(nz, torch.full_like(nz, nnz**-0.5))
    torch.testing.assert_close(lines.norm(dim=1), torch.ones(lines.shape[0], dtype=x.dtype))


def test_sparse_sign_has_both_signs():
    x = sparse_sign_test_matrix(200, 10, generator=_gen(2))
    assert (x > 0).any() and (x < 0).any()


@pytest.mark.parametrize("dist", ["gaussian", "sparsesign", "SparseSign"])
def test_seeded_reproducible(dist):
    a = test_matrix(30, 6, dist, generator=_gen(7))
    b = test_matrix(30, 6, dist, generator=_gen(7))
    assert torch.equal(a, b)


def test_validation():
    with pytest.raises(ValueError):
        test_matrix(5, 5, "rademacher")
    with pytest.raises(ValueError):
        gaussian_test_matrix(0, 3)
    with pytest.raises(ValueError):
        sparse_sign_test_matrix(5, 3, sparsity=0)
    with pytest.raises(ValueError):
        sparse_sign_test_matrix(5, 3, sparsity=True)
    with pytest.raises(ValueError):
        sparse_sign_test_matrix(5.0, 3)


def test_feeds_sketch_power_subspace():
    from torchsketchpower import sketch_power_subspace

    g = _gen(3)
    a = torch.randn(60, 40, generator=g, dtype=torch.float64)
    y = a @ sparse_sign_test_matrix(40, 6, generator=g)
    z = a @ gaussian_test_matrix(40, 12, generator=g)
    q = sketch_power_subspace(y, z, steps=1)
    torch.testing.assert_close(q.mH @ q, torch.eye(6, dtype=torch.float64), atol=1e-10, rtol=0)


@pytest.mark.parametrize("dist", ["gaussian", "sparsesign"])
@pytest.mark.parametrize("dtype", [torch.float32, torch.float64, torch.complex64, torch.complex128])
@pytest.mark.parametrize("m,n", [(30, 20), (20, 30), (25, 25)])
def test_construct_sketches_matches_direct_products(dist, dtype, m, n):
    g = _gen(11)
    a = torch.randn(m, n, generator=g, dtype=dtype)
    y, z = construct_sketches(a, 4, 9, distribution=dist, generator=_gen(5))
    assert y.shape == (m, 4) and z.shape == (m, 9)
    assert y.dtype == z.dtype == dtype and y.device == a.device
    # Direct algebraic oracle: replay the same draws.
    g2 = _gen(5)
    omega = test_matrix(n, 4, dist, generator=g2, dtype=dtype)
    phi = test_matrix(n, 9, dist, generator=g2, dtype=dtype)
    torch.testing.assert_close(y, a @ omega, rtol=0, atol=0)
    torch.testing.assert_close(z, a @ phi, rtol=0, atol=0)


def test_construct_sketches_omega_phi_are_distinct_draws():
    a = torch.eye(12, dtype=torch.float64)  # a @ x == x, so the sketches expose Omega and Phi
    y, z = construct_sketches(a, 3, 5, generator=_gen(1))
    assert not torch.equal(y, z[:, :3])
    again = construct_sketches(a, 3, 5, generator=_gen(1))
    assert torch.equal(y, again[0]) and torch.equal(z, again[1])
    other = construct_sketches(a, 3, 5, generator=_gen(2))
    assert not torch.equal(y, other[0])


def test_construct_sketches_noncontiguous_input():
    base = torch.randn(40, 30, generator=_gen(8), dtype=torch.float64)
    a = base.T  # (30, 40), non-contiguous view
    assert not a.is_contiguous()
    y, z = construct_sketches(a, 3, 7, generator=_gen(4))
    y2, z2 = construct_sketches(a.contiguous(), 3, 7, generator=_gen(4))
    torch.testing.assert_close(y, y2)
    torch.testing.assert_close(z, z2)


def test_construct_sketches_sparsity_kwarg():
    a = torch.eye(20, dtype=torch.float64)
    y, z = construct_sketches(a, 3, 6, distribution="sparsesign", sparsity=2, generator=_gen(6))
    # a is the identity, so each row of y/z is a row of Omega/Phi with exactly 2 nonzeros.
    assert torch.equal((y != 0).sum(dim=1), torch.full((20,), 2))
    assert torch.equal((z != 0).sum(dim=1), torch.full((20,), 2))


def test_construct_sketches_validation():
    a = torch.randn(10, 8, generator=_gen(), dtype=torch.float64)
    with pytest.raises(ValueError):
        construct_sketches(a, 5, 5)  # s must be < ell
    with pytest.raises(ValueError):
        construct_sketches(a, 0, 5)
    with pytest.raises(ValueError):
        construct_sketches(a, True, 5)
    with pytest.raises(ValueError):
        construct_sketches(a[0], 2, 5)
    with pytest.raises(ValueError):
        construct_sketches(a.unsqueeze(0), 2, 5)
    with pytest.raises(TypeError):
        construct_sketches(torch.ones(4, 4, dtype=torch.int64), 1, 2)
    with pytest.raises(ValueError):
        construct_sketches(a, 2, 5, distribution="rademacher")


@pytest.mark.parametrize("steps", [0, 1])
def test_construct_then_sketch_power_on_low_rank_a(steps):
    from torchsketchpower import sketch_power_subspace

    g = _gen(13)
    u = torch.randn(80, 5, generator=g, dtype=torch.float64)
    v = torch.randn(60, 5, generator=g, dtype=torch.float64)
    a = u @ v.T  # exact rank 5
    y, z = construct_sketches(a, 5, 12, generator=g)
    q = sketch_power_subspace(y, z, steps)
    # range(Y) = range(A) for exact rank 5 and s = 5, so Q captures A.
    resid = torch.linalg.matrix_norm(a - q @ (q.T @ a)) / torch.linalg.matrix_norm(a)
    assert float(resid) < 1e-10
