# TorchSketchPower

Experimental portable PyTorch sketch-power subspace kernel inspired by Chang and Yang (2026), DOI: 10.1137/25M1760143.

## Status

**EXPLORE / unmerged prototype.** The kernel computes an orthonormal basis for repeated auxiliary-sketch power operations; it is **not** yet the complete paper algorithm or a verified single-pass low-rank reconstruction.

```bash
python -m pip install -e '.[test]'
pytest -q
```

If `(Z Z^H)^q Y` (or `Y` itself) has numerical rank below `k`, the `k`-dimensional powered range does not exist and QR would fill the missing columns arbitrarily. By default `sketch_power_subspace` raises `RankDeficiencyError`; pass `on_rank_deficient="warn"` to get a `RankDeficiencyWarning` and a basis whose trailing columns are arbitrary, or `"ignore"` to skip the checks. A finite, orthonormal output alone does not imply a correct powered range.

`construct_sketches(A, s, ell)` forms `Y = A @ Omega`, `Z = A @ Phi` for a resident matrix with Gaussian or fixed-nnz sparse-sign test matrices. It is in-memory only: not streaming, not one-pass, no `W = Psi A`.

`construct_corange_sketch(A, d)` forms `Psi (d x m)` and `W = Psi @ A`; `reconstruct_from_corange(Q, Psi, W, r)` solves `min_B ||(Psi Q) B - W||_F` (`torch.linalg.lstsq`, SVD driver) and returns the rank-`r` truncated SVD `(U, sigma, Vh)` of `Q B`. In-memory and CPU only: not streaming, not one-pass, not the complete paper Algorithm 2.1. Rank-deficient `Psi Q` raises `RankDeficiencyError`; poor conditioning warns with `IllConditionedWarning`.

`sketch_power_low_rank(A, r, s, ell, d, steps=1)` composes the four steps above (sketches, `sketch_power_subspace`, corange sketch, reconstruction) into a rank-`r` `(U, sigma, Vh)`. It makes three products over a resident CPU matrix: not streaming, not one-pass, not a verified paper Algorithm 2.1. Non-CPU input raises; GPU: NOT RUN.

CPU evidence for each revision is recorded in the PR conversation (PR #2). GPU: NOT RUN.

See [research rationale](docs/research/spi-tensorization.md) and [Issue #1](https://github.com/JohnnyZPiggy/TorchSketchPower/issues/1).

Upstream MATLAB: https://github.com/Mitchell-Cxyk/SketchPowerIteration @ `752be34fbd26595f8d608a25e7dcdea586a6e0ca`. No root LICENSE found: no code copied.

SAE V3.3 framework: complete verbatim snapshot of `JohnnyZPiggy/SAE-Framework@65338eb1aa67971e110db982a07cf43161c23446` in [`.sae/`](.sae/). Its own template `.sae/examples/project/AGENTS.md` links `.sae/...` and resolves from the repository root, which is the layout used here.
