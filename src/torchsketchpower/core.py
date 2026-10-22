"""Small-sketch power subspace iteration; not a complete one-pass SVD."""
import warnings

import torch


class RankDeficiencyWarning(RuntimeWarning):
    """The requested k-dimensional subspace is not uniquely defined."""


def _numerical_rank(a: torch.Tensor) -> int:
    # Same default tolerance as torch.linalg.matrix_rank: max(shape) * eps * s_max.
    s = torch.linalg.svdvals(a)
    tol = max(a.shape) * torch.finfo(s.dtype).eps * s.max()
    return int((s > tol).sum())


def sketch_power_subspace(
    y: torch.Tensor,
    z: torch.Tensor,
    steps: int = 1,
    check_rank: bool = True,
) -> torch.Tensor:
    """Return an orthonormal basis of span((z @ z.mH) ** steps @ y).

    y: (m, k) target sketch; z: (m, ell) auxiliary sketch, with k <= ell and k <= m.
    The operator z @ z.mH is never formed. For steps=0, return qr(y).Q.

    The result is only meaningful when (z @ z.mH) ** steps @ y has rank k.
    Otherwise QR fills the missing directions with arbitrary orthonormal
    columns. With check_rank=True (default), a RankDeficiencyWarning is raised
    in that case; this costs a small SVD per step and a host synchronization.
    """
    if not isinstance(y, torch.Tensor) or not isinstance(z, torch.Tensor):
        raise TypeError("y and z must be torch tensors")
    if y.ndim != 2 or z.ndim != 2 or y.shape[0] != z.shape[0]:
        raise ValueError("y and z must be two-dimensional and share row dimension")
    m, k = y.shape
    ell = z.shape[1]
    if not (0 < k <= m and k <= ell):
        raise ValueError("expected 0 < k <= m and k <= ell")
    if y.device != z.device or y.dtype != z.dtype:
        raise ValueError("y and z must share device and dtype")
    if not (y.is_floating_point() or y.is_complex()):
        raise TypeError("floating or complex tensors required")
    if type(steps) is not int or steps < 0:
        raise ValueError("steps must be a nonnegative integer")

    def warn_if_deficient(a: torch.Tensor, what: str) -> None:
        if check_rank:
            r = _numerical_rank(a)
            if r < k:
                warnings.warn(
                    f"{what} has numerical rank {r} < k={k}; the trailing "
                    f"{k - r} output columns are arbitrary",
                    RankDeficiencyWarning,
                    stacklevel=3,
                )

    warn_if_deficient(y, "y")
    q, _ = torch.linalg.qr(y, mode="reduced")
    for step in range(steps):
        zq = z.mH @ q
        # rank(z @ zq-basis) == rank(zq), so checking zq covers the whole step.
        warn_if_deficient(zq, f"z.mH @ q at step {step + 1}")
        middle, _ = torch.linalg.qr(zq, mode="reduced")
        q, _ = torch.linalg.qr(z @ middle, mode="reduced")
    return q
