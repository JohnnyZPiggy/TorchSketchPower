# Sketch-power iteration: preliminary R1–R3 and Reuse Report

**Issue:** #1. **Mode:** EXPLORE. **Research decision:** SCOPED_HYPOTHESIS, not paper-equivalent RESEARCH_READY.

**Primary paper:** Chang and Yang, *Improving Sketching Algorithms for Low-Rank Matrix Approximation via Sketch-Power Iterations*, SIAM J. Matrix Anal. Appl. 47(3), 2026, DOI: 10.1137/25M1760143 (published online July 10, 2026).

**Upstream MATLAB reference:** https://github.com/Mitchell-Cxyk/SketchPowerIteration at `752be34fbd26595f8d608a25e7dcdea586a6e0ca`. No root LICENSE found at check time; treat third-party source as **not licensed for copying** unless permission is established. No upstream code was copied.

## R1: dimensions and mathematical prototype

Let target sketch Y be m×k, auxiliary sketch Z be m×ell with 0<k≤m and k≤ell. (ell>m is allowed: ZZ* is still a valid m×m PSD operator; typical use has ell≪m.) Model the sketch-based positive-semidefinite operator M=ZZ* (not the original AA*). The **subspace** target for q steps is span(M^q Y), assuming sufficient rank and stable arithmetic. q=0 returns span(Y).

This is a *mathematical exploration kernel*, not verification of the paper's exact Algorithm 2.x pseudocode or its full low-rank reconstruction.

## R2: tensorization

Avoid forming m×m M. Compute `Z.mH @ Q`, reduced QR, `Z @ middle_Q`, reduced QR. The two QR factorizations stabilize the evolving subspace (full-rank cases). PyTorch primitives: `matmul` and `torch.linalg.qr`. No custom CUDA/Triton.

**Important limitation:** For rank-deficient intermediate sketches, QR may choose arbitrary completion columns; these columns must not be interpreted as the unique rank-deficient range. Full-rank theory and rank-aware output require a separate validation step. The implementation now detects this case: it checks the numerical rank of `Y` and of each `Z^H Q` (equal to the rank of that step's output, since `Z` is injective on `range(Z^H)`) with the `torch.linalg.matrix_rank` default tolerance and emits `RankDeficiencyWarning`; output semantics are unchanged. If the paper uses a different normalization, compare subspaces rather than columnwise matrices.

## R3: falsifiable experiment

For small random Y and Z compare the projector of the returned Q with the projector of `torch.linalg.qr((Z @ Z.mH)^q @ Y).Q` at q=0,1,2; check orthogonality and invalid shapes/dtypes. This oracle uses dense M **only in tests**. Real CPU test evidence: Python 3 environment with PyTorch 2.10.0+cpu, `PYTHONPATH=src pytest -q` yielded **8 passed** on 2026-10-22. No package installation, GPU or paper-implementation equivalence was tested.

## Reuse-first assessment

- PyTorch built-ins (exact version used in pilot: 2.10.0+cpu), `torch.linalg.qr`, `@`: **REUSE**.
- Chang–Yang MATLAB upstream commit pinned above: reference for later read-only algorithm comparison; license not found: **DO NOT COPY**.
- Package implementation: **BUILD a small independent composition**. Novelty claim is not a new mathematical algorithm; portability, streaming interface and evidence are proposed engineering contributions, not yet verified.
- torch.compile, GPU, one-pass construction/reconstruction, matched-memory speedups: **NOT RUN / UNVERIFIED**.

**Next science gate:** Inspect authoritative pseudocode and all relevant upstream MATLAB routines; prove paper-specific equivalence before marking `RESEARCH_READY`.
