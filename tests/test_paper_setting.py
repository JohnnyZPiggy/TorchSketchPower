"""Paper setting: Y = A Omega, Z = A Phi from a rectangular A (Chang-Yang Eqs. 2.5-2.6).

Subspaces are compared through orthogonal projectors / principal angles, never
through entries or signs of Q.
"""
import pytest
import torch
from torchsketchpower import sketch_power_subspace

F64 = torch.float64


def _max_angle_sin(a, b):
    """Largest sine of principal angles between orthonormal bases a and b."""
    return float(torch.linalg.matrix_norm(a @ a.mH - b @ b.mH, ord=2))


def _dense_oracle(y, z, steps):
    exact = y
    for _ in range(steps):
        exact = z @ (z.mH @ exact)
    return torch.linalg.qr(exact, mode="reduced").Q


def _paper_recurrence(y, z, steps):
    """Eq. (2.6) as written: Yhat_0 = Y; X_j = qr(Z^T Yhat_{j-1}).Q; Yhat_j = Z X_j; one final QR."""
    yhat = y
    for _ in range(steps):
        x, _ = torch.linalg.qr(z.mH @ yhat, mode="reduced")
        yhat = z @ x
    return torch.linalg.qr(yhat, mode="reduced").Q


def _sketches(m, n, s, ell, spectrum, seed):
    g = torch.Generator().manual_seed(seed)
    u, _ = torch.linalg.qr(torch.randn(m, min(m, n), generator=g, dtype=F64))
    v, _ = torch.linalg.qr(torch.randn(n, min(m, n), generator=g, dtype=F64))
    a = (u * spectrum[: u.shape[1]]) @ v.mH
    omega = torch.randn(n, s, generator=g, dtype=F64)
    phi = torch.randn(n, ell, generator=g, dtype=F64)
    return a @ omega, a @ phi


@pytest.mark.parametrize("seed", [0, 1, 2])
@pytest.mark.parametrize("m,n", [(120, 80), (80, 120), (100, 100)])
@pytest.mark.parametrize("kind", ["flat", "poly", "exp"])
@pytest.mark.parametrize("steps", [0, 1, 2])
def test_kernel_matches_oracle_and_paper_recurrence(seed, m, n, kind, steps):
    idx = torch.arange(1, min(m, n) + 1, dtype=F64)
    spectrum = {"flat": torch.ones_like(idx), "poly": idx**-1.0, "exp": 10 ** (-0.05 * idx)}[kind]
    y, z = _sketches(m, n, s=6, ell=14, spectrum=spectrum, seed=seed)
    q = sketch_power_subspace(y, z, steps)
    assert q.shape == (m, 6)
    torch.testing.assert_close(q.mH @ q, torch.eye(6, dtype=F64), atol=1e-12, rtol=0)
    assert _max_angle_sin(q, _dense_oracle(y, z, steps)) < 1e-6
    assert _max_angle_sin(q, _paper_recurrence(y, z, steps)) < 1e-6


def test_zero_steps_returns_orth_y_without_using_z():
    y, z = _sketches(60, 40, 5, 12, torch.ones(40, dtype=F64), seed=4)
    q = sketch_power_subspace(y, z * float("nan"), 0)
    assert _max_angle_sin(q, torch.linalg.qr(y, mode="reduced").Q) < 1e-12


def test_sketches_with_orthogonal_range_are_rejected():
    # Full-rank Y and Z individually, yet Z^T Y = 0: the cross product has rank 0.
    from torchsketchpower import RankDeficiencyError

    g = torch.Generator().manual_seed(9)
    basis, _ = torch.linalg.qr(torch.randn(30, 10, generator=g, dtype=F64))
    y, z = basis[:, :3], basis[:, 3:10]
    assert torch.linalg.matrix_rank(y) == 3 and torch.linalg.matrix_rank(z) == 7
    with pytest.raises(RankDeficiencyError):
        sketch_power_subspace(y, z, 1)
