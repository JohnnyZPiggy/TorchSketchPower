"""Small-sketch power subspace iteration; not a complete one-pass SVD."""
import warnings

import torch


class RankDeficiencyWarning(RuntimeWarning):
    """The requested k-dimensional subspace is not uniquely defined."""


class RankDeficiencyError(ValueError):
    """The requested k-dimensional subspace is not uniquely defined."""


_POLICIES = ("raise", "warn", "ignore")


def _numerical_rank(a: torch.Tensor) -> int:
    # Same default tolerance as torch.linalg.matrix_rank: max(shape) * eps * s_max.
    s = torch.linalg.svdvals(a)
    tol = max(a.shape) * torch.finfo(s.dtype).eps * s.max()
    return int((s > tol).sum())


def sketch_power_subspace(
    y: torch.Tensor,
    z: torch.Tensor,
    steps: int = 1,
    on_rank_deficient: str = "raise",
) -> torch.Tensor:
    """Return an orthonormal basis of span((z @ z.mH) ** steps @ y).

    y: (m, k) target sketch; z: (m, ell) auxiliary sketch, with k <= ell and k <= m.
    The operator z @ z.mH is never formed. For steps=0, return qr(y).Q.

    Output contract. The result is the powered range only if y and, at every
    step, the (ell, k) cross-product z.mH @ q have numerical rank k (SVD
    tolerance max(shape) * eps * s_max, as in torch.linalg.matrix_rank).
    Otherwise the powered range has dimension < k and reduced QR completes
    the basis with arbitrary orthonormal columns that need not lie in
    range(z); finite, orthonormal output does not imply correctness.
    on_rank_deficient selects the behavior in that case:

    * "raise" (default): raise RankDeficiencyError.
    * "warn": emit RankDeficiencyWarning and return the basis; the trailing
      k - rank columns are arbitrary.
    * "ignore": skip the rank checks (no SVD, no host synchronization).

    The checks cost one small SVD per step and a host synchronization.
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
    if on_rank_deficient not in _POLICIES:
        raise ValueError(f"on_rank_deficient must be one of {_POLICIES}")

    def check_rank(a: torch.Tensor, what: str) -> None:
        if on_rank_deficient == "ignore":
            return
        r = _numerical_rank(a)
        if r < k:
            msg = f"{what} has numerical rank {r} < k={k}; the powered range is not k-dimensional"
            if on_rank_deficient == "raise":
                raise RankDeficiencyError(msg)
            warnings.warn(
                f"{msg}, so the trailing {k - r} output columns are arbitrary",
                RankDeficiencyWarning,
                stacklevel=3,
            )

    check_rank(y, "y")
    q, _ = torch.linalg.qr(y, mode="reduced")
    for step in range(steps):
        zq = z.mH @ q
        # If zq has rank k, middle spans a k-dimensional subspace of range(z.mH),
        # on which z is injective, so z @ middle also has rank k. If zq is
        # rank-deficient, that implication fails and the check below flags it.
        check_rank(zq, f"z.mH @ q at step {step + 1}")
        middle, _ = torch.linalg.qr(zq, mode="reduced")
        q, _ = torch.linalg.qr(z @ middle, mode="reduced")
    return q
