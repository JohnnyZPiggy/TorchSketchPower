"""In-memory rank-r reconstruction from a range basis Q and a corange sketch (Psi, W).

Given A (m, n), Q (m, s) with Q^H Q = I, Psi (d, m) and W = Psi @ A (d, n), solve
min_B ||(Psi Q) B - W||_F and return the rank-r truncated SVD of Q @ B. This is a
scoped in-memory step, not the complete paper algorithm and not one-pass streaming.
"""
import warnings

import torch

from .core import RankDeficiencyError


class IllConditionedWarning(RuntimeWarning):
    """Psi @ Q is numerically full column rank but poorly conditioned."""


def _check_inputs(q: torch.Tensor, psi: torch.Tensor, w: torch.Tensor) -> None:
    if not all(isinstance(t, torch.Tensor) for t in (q, psi, w)):
        raise TypeError("q, psi and w must be torch tensors")
    if q.ndim != 2 or psi.ndim != 2 or w.ndim != 2:
        raise ValueError("q, psi and w must be two-dimensional")
    if not (q.dtype == psi.dtype == w.dtype) or not (q.device == psi.device == w.device):
        raise ValueError("q, psi and w must share device and dtype")
    if not (q.is_floating_point() or q.is_complex()):
        raise TypeError("floating or complex tensors required")
    m, s = q.shape
    d = psi.shape[0]
    if psi.shape[1] != m or w.shape[0] != d:
        raise ValueError("expected q (m, s), psi (d, m), w (d, n)")
    if not (0 < s <= m):
        raise ValueError("expected 0 < s <= m")
    if d < s:
        raise ValueError("expected d >= s")


def solve_corange_coefficient(
    q: torch.Tensor,
    psi: torch.Tensor,
    w: torch.Tensor,
    *,
    max_condition: float = None,
) -> torch.Tensor:
    """Return B (s, n) minimizing ||(psi @ q) B - w||_F.

    Preconditions: q has orthonormal columns (checked, tolerance 50 * m * eps in the
    Frobenius norm of q^H q - I) and C = psi @ q has numerical full column rank
    (SVD tolerance max(shape) * eps * s_max). Rank deficiency raises
    ``RankDeficiencyError``. If cond(C) exceeds ``max_condition`` (default
    eps**-0.5) an ``IllConditionedWarning`` is emitted and B is still returned.
    The solve uses ``torch.linalg.lstsq`` with the SVD driver ``gelsd`` and forms
    no explicit inverse. B is the least-squares solution; C B = w is not expected
    unless the columns of w lie in range(C).
    """
    _check_inputs(q, psi, w)
    m, s = q.shape
    eps = torch.finfo(q.real.dtype).eps
    gram_err = torch.linalg.matrix_norm(q.mH @ q - torch.eye(s, dtype=q.dtype, device=q.device))
    if not float(gram_err) <= 50 * m * eps:
        raise ValueError("q must have orthonormal columns")
    c = psi @ q
    sv = torch.linalg.svdvals(c)
    smax, smin = float(sv[0]), float(sv[-1])
    if not smin > max(c.shape) * eps * smax:
        rank = int((sv > max(c.shape) * eps * smax).sum())
        raise RankDeficiencyError(
            f"psi @ q has numerical rank {rank} < s={s}; the coefficient is not unique"
        )
    limit = eps**-0.5 if max_condition is None else max_condition
    if smax / smin > limit:
        warnings.warn(
            f"psi @ q has condition number {smax / smin:.3g} > {limit:.3g}; "
            "the reconstruction may amplify sketch error",
            IllConditionedWarning,
            stacklevel=2,
        )
    return torch.linalg.lstsq(c, w, driver="gelsd").solution


def reconstruct_from_corange(
    q: torch.Tensor,
    psi: torch.Tensor,
    w: torch.Tensor,
    r: int,
    *,
    max_condition: float = None,
):
    """Return ``(u, sigma, vh)``: the rank-r truncated SVD of ``q @ B``.

    B = argmin ||(psi @ q) B - w||_F (see ``solve_corange_coefficient``). The thin
    SVD B = U_B S Vh is taken on the small (s, n) matrix only; u = q @ U_B[:, :r]
    is (m, r), sigma is (r,), vh is (r, n). Requires 1 <= r <= min(s, n). Singular
    vectors are unique only up to sign/phase (and rotation at repeated values).
    ``q @ B`` is never formed.
    """
    _check_inputs(q, psi, w)
    if type(r) is not int or not 1 <= r <= min(q.shape[1], w.shape[1]):
        raise ValueError("r must be an integer with 1 <= r <= min(s, n)")
    b = solve_corange_coefficient(q, psi, w, max_condition=max_condition)
    u_b, sigma, vh = torch.linalg.svd(b, full_matrices=False)
    return q @ u_b[:, :r], sigma[:r], vh[:r]
