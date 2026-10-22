"""Random test matrices (Gaussian, sparse sign) and in-memory sketch construction.

Everything here operates on a fully resident matrix. Nothing is streamed and
nothing is one-pass: ``construct_sketches`` is two ordinary matrix products.
"""
from typing import Optional

import torch

_DISTRIBUTIONS = ("gaussian", "sparsesign")


def gaussian_test_matrix(
    rows: int,
    cols: int,
    *,
    generator: Optional[torch.Generator] = None,
    dtype: torch.dtype = torch.float64,
    device: Optional[torch.device] = None,
) -> torch.Tensor:
    """Return a (rows, cols) matrix with i.i.d. standard normal entries.

    ``generator`` must live on ``device`` (a CPU generator with a CUDA device
    raises inside torch; non-CPU devices are NOT RUN here).
    """
    _check_dims(rows, cols)
    return torch.randn(rows, cols, generator=generator, dtype=dtype, device=device)


def sparse_sign_test_matrix(
    rows: int,
    cols: int,
    *,
    sparsity: int = 8,
    generator: Optional[torch.Generator] = None,
    dtype: torch.dtype = torch.float64,
    device: Optional[torch.device] = None,
) -> torch.Tensor:
    """Return a dense (rows, cols) sparse sign matrix.

    Sparsity is imposed along the shorter dimension: each row (if rows >= cols)
    or each column (otherwise) has exactly min(sparsity, short side) nonzeros
    at uniformly random positions, with values +-1/sqrt(nnz). Every such row or
    column therefore has unit Euclidean norm.

    This is a fixed-nnz distribution defined here; it is not shown to coincide
    with the paper's sparse Rademacher distribution or to be a JL embedding.
    Storage is dense (structured zeros), not ``torch.sparse``.
    """
    _check_dims(rows, cols)
    if type(sparsity) is not int or sparsity < 1:
        raise ValueError("sparsity must be a positive integer")
    long_side, short_side = max(rows, cols), min(rows, cols)
    nnz = min(sparsity, short_side)
    # Distinct positions per line: take the nnz smallest of i.i.d. uniform scores.
    scores = torch.rand(long_side, short_side, generator=generator, device=device)
    pos = scores.topk(nnz, dim=1, largest=False).indices
    signs = torch.randint(0, 2, (long_side, nnz), generator=generator, device=device)
    vals = (signs.to(dtype) * 2 - 1) / nnz**0.5
    out = torch.zeros(long_side, short_side, dtype=dtype, device=device)
    out.scatter_(1, pos, vals)
    return out if rows >= cols else out.T.contiguous()


def test_matrix(
    rows: int,
    cols: int,
    distribution: str = "gaussian",
    **kwargs,
) -> torch.Tensor:
    """Dispatch on distribution name: "gaussian" or "sparsesign"."""
    name = distribution.lower() if isinstance(distribution, str) else distribution
    if name == "gaussian":
        return gaussian_test_matrix(rows, cols, **kwargs)
    if name == "sparsesign":
        return sparse_sign_test_matrix(rows, cols, **kwargs)
    raise ValueError(f"distribution must be one of {_DISTRIBUTIONS}")


def construct_sketches(
    a: torch.Tensor,
    s: int,
    ell: int,
    *,
    distribution: str = "gaussian",
    generator: Optional[torch.Generator] = None,
    **kwargs,
):
    """Return ``(Y, Z) = (a @ Omega, a @ Phi)`` for a resident 2-D tensor ``a`` (m, n).

    Omega (n, s) and Phi (n, ell) are independent draws, taken in that order from
    ``generator`` (so a fixed seed fixes both and Omega != Phi). Requires
    0 < s < ell. Extra keyword arguments (e.g. ``sparsity``) go to the test matrix
    constructor; dtype and device follow ``a``. Y is (m, s), Z is (m, ell).

    In-memory only: this is two matrix products over a resident ``a``, not a
    one-pass or streaming construction, and it does not form W = Psi a.
    """
    if not isinstance(a, torch.Tensor) or a.ndim != 2:
        raise ValueError("a must be a two-dimensional torch tensor")
    if not (a.is_floating_point() or a.is_complex()):
        raise TypeError("floating or complex tensor required")
    for v in (s, ell):
        if type(v) is not int or v < 1:
            raise ValueError("s and ell must be positive integers")
    if not s < ell:
        raise ValueError("expected 0 < s < ell")
    n = a.shape[1]
    kwargs.update(generator=generator, dtype=a.dtype, device=a.device)
    omega = test_matrix(n, s, distribution, **kwargs)
    phi = test_matrix(n, ell, distribution, **kwargs)
    return a @ omega, a @ phi


def construct_corange_sketch(
    a: torch.Tensor,
    d: int,
    *,
    distribution: str = "gaussian",
    generator: Optional[torch.Generator] = None,
    **kwargs,
):
    """Return ``(Psi, W) = (Psi, Psi @ a)`` for a resident 2-D tensor ``a`` (m, n).

    Psi (d, m) is one draw from the chosen test matrix distribution; dtype and
    device follow ``a``. W is (d, n). Extra keyword arguments (e.g. ``sparsity``)
    go to the test matrix constructor. The "sparsesign" option is the fixed-nnz
    distribution of ``sparse_sign_test_matrix``, not shown equivalent to the paper's.

    In-memory only: one matrix product over a resident ``a``; not one-pass or streaming.
    """
    if not isinstance(a, torch.Tensor) or a.ndim != 2:
        raise ValueError("a must be a two-dimensional torch tensor")
    if not (a.is_floating_point() or a.is_complex()):
        raise TypeError("floating or complex tensor required")
    if type(d) is not int or d < 1:
        raise ValueError("d must be a positive integer")
    kwargs.update(generator=generator, dtype=a.dtype, device=a.device)
    psi = test_matrix(d, a.shape[0], distribution, **kwargs)
    return psi, psi @ a


# Not a test: stop pytest from collecting the dispatcher when imported into test modules.
test_matrix.__test__ = False


def _check_dims(rows: int, cols: int) -> None:
    for v in (rows, cols):
        if type(v) is not int or v < 1:
            raise ValueError("rows and cols must be positive integers")
