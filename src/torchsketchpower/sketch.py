"""Random test matrices (Gaussian, sparse sign) for building sketches."""
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
    """Return a (rows, cols) matrix with i.i.d. standard normal entries."""
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


# Not a test: stop pytest from collecting the dispatcher when imported into test modules.
test_matrix.__test__ = False


def _check_dims(rows: int, cols: int) -> None:
    for v in (rows, cols):
        if type(v) is not int or v < 1:
            raise ValueError("rows and cols must be positive integers")
