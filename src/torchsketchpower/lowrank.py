"""End-to-end in-memory sketch-power low-rank approximation (CPU only)."""
from typing import Optional

import torch

from .core import sketch_power_subspace
from .reconstruct import reconstruct_from_corange
from .sketch import _DISTRIBUTIONS, construct_corange_sketch, construct_sketches


def _is_int(v) -> bool:
    return type(v) is int


def sketch_power_low_rank(
    a: torch.Tensor,
    r: int,
    s: int,
    ell: int,
    d: int,
    *,
    steps: int = 1,
    distribution: str = "gaussian",
    generator: Optional[torch.Generator] = None,
    max_condition: Optional[float] = None,
    **kwargs,
):
    """Return ``(u, sigma, vh)``, a rank-``r`` approximation ``u @ diag(sigma) @ vh`` of ``a``.

    Pipeline, for a resident CPU tensor ``a`` (m, n), with 1 <= r <= min(s, n),
    s <= m, s < ell (ell may exceed m) and d >= s:

    1. ``Y = a @ Omega`` (m, s), ``Z = a @ Phi`` (m, ell)      [construct_sketches]
    2. ``Q = sketch_power_subspace(Y, Z, steps)``, default rank safety kept
    3. ``Psi`` (d, m), ``W = Psi @ a`` (d, n)                  [construct_corange_sketch]
    4. ``B = argmin ||Psi Q B - W||_F``; ``u, sigma, vh`` = rank-r truncated SVD of ``Q B``
       [reconstruct_from_corange]

    Omega, Phi and Psi are drawn sequentially from ``generator`` (a CPU generator, or
    the global RNG if None), so a fixed seed replays and the three draws differ; this
    is not a test of statistical independence. ``distribution`` is "gaussian" or
    the exploratory fixed-nnz "sparsesign" (not shown equivalent to the paper's);
    extra keyword arguments (e.g. ``sparsity``) go to the test matrix constructors.
    ``max_condition`` is forwarded to the coefficient solve.

    Rank safety is never masked: ``RankDeficiencyError`` is raised if Y, a cross
    product z^H q, or Psi Q is numerically rank deficient (e.g. rank(a) < s), and
    ``IllConditionedWarning`` is emitted for a poorly conditioned Psi Q.

    This is three matrix products over a fully resident ``a``: not one-pass, not
    streaming, and not a verified implementation of the paper's Algorithm 2.1.
    CPU only: non-CPU input raises ``ValueError`` (the least-squares driver is
    CPU-specific and other devices are NOT RUN).
    """
    if not isinstance(a, torch.Tensor) or a.ndim != 2:
        raise ValueError("a must be a two-dimensional torch tensor")
    if not (a.is_floating_point() or a.is_complex()):
        raise TypeError("floating or complex tensor required")
    if a.device.type != "cpu":
        raise ValueError(f"a must be on the CPU, got device {a.device}; other devices are not supported")
    m, n = a.shape
    if m < 1 or n < 1:
        raise ValueError("a must have nonempty dimensions")
    for name, v in (("r", r), ("s", s), ("ell", ell), ("d", d)):
        if not _is_int(v) or v < 1:
            raise ValueError(f"{name} must be a positive integer")
    if not _is_int(steps) or steps < 0:
        raise ValueError("steps must be a nonnegative integer")
    if not (r <= s <= m):
        raise ValueError("expected 1 <= r <= s <= m")
    if r > n:
        raise ValueError("expected r <= n")
    if not s < ell:
        raise ValueError("expected s < ell")
    if d < s:
        raise ValueError("expected d >= s")
    if not isinstance(distribution, str) or distribution.lower() not in _DISTRIBUTIONS:
        raise ValueError(f"distribution must be one of {_DISTRIBUTIONS}")
    if generator is not None and generator.device.type != "cpu":
        raise ValueError("generator must be a CPU generator")

    y, z = construct_sketches(a, s, ell, distribution=distribution, generator=generator, **kwargs)
    q = sketch_power_subspace(y, z, steps=steps)
    psi, w = construct_corange_sketch(a, d, distribution=distribution, generator=generator, **kwargs)
    return reconstruct_from_corange(q, psi, w, r, max_condition=max_condition)
