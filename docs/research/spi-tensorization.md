# Sketch-power iteration: preliminary R1–R3 and Reuse Report

**Issue:** #1. **Mode:** EXPLORE. **Research decision:** SCOPED_HYPOTHESIS, not paper-equivalent RESEARCH_READY.

**Primary paper:** Chang and Yang, *Improving Sketching Algorithms for Low-Rank Matrix Approximation via Sketch-Power Iterations*, SIAM J. Matrix Anal. Appl. 47(3), 2026, DOI: 10.1137/25M1760143 (published online July 10, 2026).

**Upstream MATLAB reference:** https://github.com/Mitchell-Cxyk/SketchPowerIteration at `752be34fbd26595f8d608a25e7dcdea586a6e0ca`. No root LICENSE found at check time; treat third-party source as **not licensed for copying** unless permission is established. No upstream code was copied.

## R1: dimensions and mathematical prototype

Let target sketch Y be m×k, auxiliary sketch Z be m×ell with 0<k≤m and k≤ell. (ell>m is allowed: ZZ* is still a valid m×m PSD operator; typical use has ell≪m.) Model the sketch-based positive-semidefinite operator M=ZZ* (not the original AA*). The **subspace** target for q steps is span(M^q Y), assuming sufficient rank and stable arithmetic. q=0 returns span(Y).

This is a *mathematical exploration kernel*, not verification of the paper's exact Algorithm 2.x pseudocode or its full low-rank reconstruction.

## R2: tensorization

Avoid forming m×m M. Compute `Z.mH @ Q`, reduced QR, `Z @ middle_Q`, reduced QR. The two QR factorizations stabilize the evolving subspace (full-rank cases). PyTorch primitives: `matmul` and `torch.linalg.qr`. No custom CUDA/Triton.

**Relation to paper Eq. (2.6).** The paper iterates `X_j = qr(Z^T Yhat_{j-1}).Q`, `Yhat_j = Z X_j` with one final QR. This kernel also orthonormalizes `Yhat_{j-1}` as `Q R` before each step. If `R` is invertible, `range(Z^T Q) = range(Z^T Yhat_{j-1})`, so `X_j` spans the same space and `Z X_j` has the same range; only the basis (not the subspace) differs. Hence both agree in range exactly when every intermediate matrix has full column rank.

*Proof (induction, exact arithmetic).* Let `Ŷ_0 = Y = Q_0 R_0` with `R_0` invertible. Suppose `range(Q_{j-1}) = range(Ŷ_{j-1})` where `Ŷ_{j-1} = Z X_{j-1}` is the paper's iterate. Then `Z^T Ŷ_{j-1} = (Z^T Q_{j-1}) R_{j-1}` for an invertible `R_{j-1}` (the paper's iterate and ours differ by a right factor), so `range(Z^T Ŷ_{j-1}) = range(Z^T Q_{j-1})`. Both thin QRs therefore return orthonormal bases `X_j`, `X_j'` of one `s`-dimensional space, `X_j' = X_j U` with `U` orthogonal, and `Z X_j' = (Z X_j) U` has the same range as `Ŷ_j = Z X_j`. The kernel's `Q_j = qr(Z X_j').Q` then spans `range(Ŷ_j)` provided `Z X_j'` has rank `s`, which is the full-rank hypothesis. The paper's final `qr(Ŷ_q).Q` spans the same space, so both outputs have equal range; the code's tests check this through projectors against both the dense oracle and a literal implementation of Eq. (2.6) (`tests/test_paper_setting.py`). This covers the in-memory kernel only, not Algorithm 2.1 as a whole.

**Paper dimension inconsistency (recorded, not transcribed).** Eqs. (2.3) and (2.5) of the paper need `Ψ ∈ R^{d×m}`, `Φ ∈ R^{n×ℓ}`, `Ω ∈ R^{n×s}` for `Y = AΩ`, `Z = AΦ`, `W = ΨA ∈ R^{d×n}`. The *Require* line of Algorithm 2.1 states `Ψ ∈ R^{d×n}` and `Φ ∈ R^{m×ℓ}`, which is incompatible with `ΨA` and `AΦ` for rectangular `A`. This is a dimension-check inference by the Architect's audit and is not used here; this repository only consumes `Y` and `Z`.

**Rank-deficiency contract.** If `Y` or any `Z^H Q` has numerical rank `r < k` (tolerance `max(shape)*eps*s_max`, the `torch.linalg.matrix_rank` default; for the cross-product `Z^H Q` the reference scale is `max(s_max, ||Z||_F)`, so that a product which is only rounding noise, e.g. `Z^H Y = 0` up to `eps`, counts as rank 0 instead of passing a check relative to its own tiny `s_max`), the powered range has dimension `r < k`. Reduced QR then completes the basis with arbitrary orthonormal columns that need **not** lie in `range(Z)`, and `rank(Z @ middle) = rank(Z^H Q)` no longer follows. The implementation therefore raises `RankDeficiencyError` by default; `on_rank_deficient="warn"` returns the basis with a warning (trailing `k - r` columns arbitrary), `"ignore"` skips the checks. If the paper uses a different normalization, compare subspaces rather than columnwise matrices.

## R3: falsifiable experiment

For small random Y and Z compare the projector of the returned Q with the projector of `torch.linalg.qr((Z @ Z.mH)^q @ Y).Q` at q=0,1,2; check orthogonality and invalid shapes/dtypes. This oracle uses dense M **only in tests**. Tests cover q=0,1,2, float32/64, complex, shape edges (k=ell, ell=m, ell>m), invalid input, `Z^H Y = 0`, near-rank-deficient `Z^H Q` on both sides of the tolerance, rank-deficient `Y`, rank loss at a later step, and the three policies. Committed-head CPU evidence is recorded in PR #2. GPU, one-pass construction and paper-equivalence of the full algorithm were not tested.

## Reuse-first assessment

- PyTorch built-ins (exact version used in pilot: 2.10.0+cpu), `torch.linalg.qr`, `@`: **REUSE**.
- Chang–Yang MATLAB upstream commit pinned above: reference for later read-only algorithm comparison; license not found: **DO NOT COPY**.
- Package implementation: **BUILD a small independent composition**. Novelty claim is not a new mathematical algorithm; portability, streaming interface and evidence are proposed engineering contributions, not yet verified.
- torch.compile, GPU, one-pass construction/reconstruction, matched-memory speedups: **NOT RUN / UNVERIFIED**.

**Next science gate:** Inspect authoritative pseudocode and all relevant upstream MATLAB routines; prove paper-specific equivalence before marking `RESEARCH_READY`.
