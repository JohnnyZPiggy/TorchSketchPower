import pytest
import torch
from torchsketchpower import sketch_power_subspace

@pytest.mark.parametrize("steps", [0, 1, 2])
@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_power_subspace(steps, dtype):
    g = torch.Generator().manual_seed(17)
    y = torch.randn(30, 4, generator=g, dtype=dtype)
    z = torch.randn(30, 8, generator=g, dtype=dtype)
    q = sketch_power_subspace(y, z, steps)
    torch.testing.assert_close(q.mH @ q, torch.eye(4, dtype=dtype), atol=2e-5 if dtype == torch.float32 else 1e-10, rtol=0)
    operator = z @ z.mH
    exact = y
    for _ in range(steps):
        exact = operator @ exact
    oracle, _ = torch.linalg.qr(exact, mode="reduced")
    dist = torch.linalg.matrix_norm(q @ q.mH - oracle @ oracle.mH)
    assert float(dist) < (1e-3 if dtype == torch.float32 else 1e-8)

def test_validation():
    with pytest.raises(ValueError):
        sketch_power_subspace(torch.randn(10, 5), torch.randn(10, 3))
    with pytest.raises(TypeError):
        sketch_power_subspace(torch.ones(10, 2, dtype=torch.int64), torch.ones(10, 3, dtype=torch.int64))

def test_rank_deficient_outputs_finite():
    y = torch.randn(12, 3, dtype=torch.float64)
    z = torch.ones(12, 5, dtype=torch.float64)
    q = sketch_power_subspace(y, z, 1)
    assert torch.isfinite(q).all()
