import pytest
import torch
from torchsketchpower import gaussian_test_matrix, sparse_sign_test_matrix, test_matrix


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
