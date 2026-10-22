"""Small-sketch power subspace iteration; not a complete one-pass SVD."""
import torch


def sketch_power_subspace(y: torch.Tensor, z: torch.Tensor, steps: int = 1) -> torch.Tensor:
    """Return an orthonormal basis after sketch-power iterations.

    y: (m, k) target sketch; z: (m, ell) auxiliary sketch, ell >= k.
    The operator z @ z.mH is never formed. For steps=0, return qr(y).Q.
    """
    if not isinstance(y, torch.Tensor) or not isinstance(z, torch.Tensor):
        raise TypeError("y and z must be torch tensors")
    if y.ndim != 2 or z.ndim != 2 or y.shape[0] != z.shape[0]:
        raise ValueError("y and z must be two-dimensional and share row dimension")
    if not (0 < y.shape[1] <= z.shape[1] <= y.shape[0]):
        raise ValueError("expected 0 < k <= ell <= m")
    if y.device != z.device or y.dtype != z.dtype:
        raise ValueError("y and z must share device and dtype")
    if not (y.is_floating_point() or y.is_complex()):
        raise TypeError("floating or complex tensors required")
    if type(steps) is not int or steps < 0:
        raise ValueError("steps must be a nonnegative integer")
    q, _ = torch.linalg.qr(y, mode="reduced")
    for _ in range(steps):
        middle, _ = torch.linalg.qr(z.mH @ q, mode="reduced")
        q, _ = torch.linalg.qr(z @ middle, mode="reduced")
    return q
