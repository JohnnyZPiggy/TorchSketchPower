# Proposed CPU float64 dense-SVD audit (not a replacement GPU gate)

Issue #20 / Draft PR #21; Architect instruction 6347684217. This audit changes no production algorithm, benchmark acceptance gate, timing, driver or fixed SAE protocol. It proposes a model to review; it is not an authorization to reclassify historical results or run CUDA.

## The question and immutable evidence

The historical `(2048,1024)` geometric float64 rank-8 dense-SVD result had residual/reference ratio 0.9999999999998166, below 1-500 eps64 = 0.999999999999889. That configured check **FAILS** and remains FAIL. The two archived T4 runs and all 75/80 completed configurations remain immutable. The final five configurations have cold calls only: four accuracy PASS and one FAIL; five warmups plus fifteen warm calls are NOT RUN. Raw adverse rows cannot be replaced by an offline verdict.

## Independent model and derivation

Use real binary64 round-to-nearest arithmetic, unit roundoff u=eps64/2, no under/overflow, and gamma_k=ku/(1-ku). Matrix product formation obeys a componentwise dot-product error model, giving the conservative Frobenius bound gamma_k ||X||F ||Y||F. The scale of this model follows dimensions/operations, not the observed failing gap. LAPACK documents SVD backward stability and dimension-dependent error; it does not justify any universal dimension-free 500-eps constant. [LAPACK SVD error analysis](https://netlib.org/lapack/lug/node97.html), [Higham and Mary, rounding error model](https://epubs.siam.org/doi/abs/10.1137/18M1226312).

For a computed norm of N entries, take relative evaluation uncertainty gamma_(N+2) from products, accumulation and square root. Convert to an absolute bound using norm_hat * gamma/(1-gamma). Norms used in other bounds are enlarged by this amount. These deliberately conservative bounds can greatly exceed observed errors. They are arithmetic-model estimates, not directed-rounding interval certificates for a vendor BLAS implementation.

Given a full thin decomposition U,S,Vh, form B=USVh and measure ||A-B||F. For each computed Gram matrix Q^T Q, bound its true defect d by the observed Frobenius defect plus gamma_m ||Q||F^2, subtraction and norm-evaluation uncertainty. If d<1, polar decomposition gives an exactly orthonormal Q0 and

    ||Q-Q0||F <= d / (1+sqrt(1-d)).

This follows by applying |sqrt(lambda)-1|=|lambda-1|/(sqrt(lambda)+1) to the Gram eigenvalues, bounding their spectral defect by the Frobenius defect. With distances dU,dV,

    ||USVh-Q_U S Q_Vh||F <= s_max * (dU * ||V||F + dV).

Add measured full reconstruction error, reconstruction formation and evaluation errors to get beta, an upper model for ||A-Q_U S Q_Vh||F. This validates a posteriori without selecting an SVD-specific empirical constant. Sorted nonnegative full S and complete thin factors are required. Near-loss of orthogonality invalidates this construction.

The function t_r(A)=min_rank(X)<=r ||A-X||F is 1-Lipschitz: apply the triangle inequality to the best rank-r approximation in each direction. Thus |t_r(A)-||S[r:]||2| <= beta. This argument needs no singular-vector forward-conditioning assumption; poor spectral gaps can rotate vectors while retaining backward accuracy. The diagnostic reports condition number and rank-boundary gap separately.

The values-only reference may differ from the full-decomposition S. Add their observed tail-norm difference and norm-evaluation uncertainties to beta, obtaining eta_ref. For the candidate, include rank-r scaled multiplication, GEMM (inner dimension r), subtraction and norm evaluation, obtaining eta_candidate. Let Delta=eta_ref+eta_candidate. This also distinguishes a formed floating-point residual from the exact residual of the returned rank-r factors. The total-minus-leading-energy check is only a second observation: its recorded cancellation bound covers arithmetic in that expression; reference error remains in eta_ref. A cancellation-sized/negative remainder is not a replacement oracle.

## Proposed decisions, fixed before any future experiment

This policy is for the **dense optimal-SVD control**, not approximate SPI quality tiers. It does not demand optimality from arbitrary low-rank methods.

1. **FAIL** for nonfinite/invalid factors or reference, or a material two-sided dense-optimality mismatch |residual-tail| > Delta when the model resolves it. Two-sided checking matters: a zero rank-r candidate satisfies the EY lower bound but is not a correct optimal dense-SVD control.
2. **INCONCLUSIVE** when the arithmetic model is unsupported, Gram-distance bound fails, or Delta exceeds sqrt(u)||A||F. The last ceiling is a prespecified resolution requirement retaining at least half the binary64 significant digits, not a tuned pass tolerance; increasing uncertainty can never force acceptance.
3. **CONSISTENT_WITH_ROUNDOFF** if finite/valid, the model is applicable/resolved, and the two residual/reference intervals overlap. This is a conditional numerical consistency observation, **not scientific PASS**, proof of exact optimality or GPU validation. Grossly bad zero-candidate, invalid orthogonality and nonfinite controls must FAIL. An inflated reference that destroys reference resolution must be INCONCLUSIVE, not PASS. Tests fix these requirements independently of the problematic numerical gap.

No fixed replacement relative tolerance is proposed. The existing M8 runner retains its 500-eps gate. The CPU case cannot retroactively certify GPU factors that were not archived, and serialization mismatch prevents claiming exact GPU input reproduction. If a strict certificate is needed, outward-rounded/high-precision independent arithmetic or a separately approved narrow saved-input/factor experiment would be required; neither is performed here.

## Partial evidence merge option (Architect decision)

The PR can be considered for **partial exploratory evidence**, without forcing full-grid PASS: both original runs, fixed tested source SHAs, single-session/seed limitations, three replayed warm repeats, exact SPI/native/dense methods, allocator semantics and unresolved float64 FAIL remain visible. Of the second run, 65 GPU+10 CPU configs completed; last five GPU configs lack all warm trials. Completed comparisons and negative outcomes can be useful despite the missing final timings. No universal speedup/work-equivalence claim follows. The Engineer keeps Draft and does not merge.
