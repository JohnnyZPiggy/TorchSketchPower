# Mathematics of the V1 reference implementation

This page states exactly what the code computes, in which dimensions, under which assumptions, and what is not claimed. It is a description of the **implemented** pipeline, not a proof that it reproduces the paper's Algorithm 2.1. For the paper context, the recorded dimension inconsistency in the paper's *Require* line, and the equivalence argument for the subspace kernel, see the [research note](research/spi-tensorization.md); that note's scope and provenance are unchanged here.

Notation. `F` is the real or complex field; `X^H` is the conjugate transpose (`.mH` in the code, never plain `.T` for complex data); `||.||_F` is the Frobenius norm; `<X, Y> = tr(X^H Y)`.

## Dimensions

| Symbol | Shape | Meaning |
|---|---|---|
| `A` | `m x n` | input matrix, fully resident in memory, on the CPU |
| `r, s, ell, d, q` | integers | target rank, range-sketch width, auxiliary-sketch width, corange-sketch height, number of power steps |
| `Omega` | `n x s` | range test matrix |
| `Phi` | `n x ell` | auxiliary test matrix |
| `Psi` | `d x m` | corange test matrix |
| `Y = A Omega` | `m x s` | range sketch |
| `Z = A Phi` | `m x ell` | auxiliary sketch |
| `W = Psi A` | `d x n` | corange sketch |
| `Q` | `m x s` | orthonormal basis, `Q^H Q = I_s` |
| `C = Psi Q` | `d x s` | small matrix of the least-squares problem |
| `B` | `s x n` | coefficients, `A ~ Q B` |
| `U, sigma, Vh` | `m x r`, `r`, `r x n` | returned rank-`r` factors |

Parameter constraints enforced by `sketch_power_low_rank`: `1 <= r <= s <= m`, `r <= n`, `s < ell` (`ell` may exceed `m`), `d >= s`, `q >= 0` an integer.

## M0: the range from the auxiliary sketch (`sketch_power_subspace`)

Given `Y` (`m x k`) and `Z` (`m x ell`), the intended output is an orthonormal basis of the range of `(Z Z^H)^q Y`. The operator `Z Z^H` is never formed: starting from `Q_0 = qr(Y)`, each step computes `X = qr(Z^H Q).Q` then `Q <- qr(Z X).Q`. For `q = 0` the output is `qr(Y).Q`.

**Assumption and rank loss.** The output is the range of `(Z Z^H)^q Y` only if `Y` and, at every step, the cross product `Z^H Q` have numerical rank `k`. If the rank is lower, the powered range has dimension below `k`, and the reduced QR completes the basis with arbitrary orthonormal columns that need not lie in the range of `Z`; a finite, orthonormal output does not imply a correct range. The code therefore raises `RankDeficiencyError` by default (`on_rank_deficient="warn"` and `"ignore"` exist on `sketch_power_subspace` itself; `sketch_power_low_rank` never uses them). The rank is judged by an SVD with tolerance `max(shape) * eps * s_max`; for the cross product `s_max` is replaced by `max(s_max, ||Z||_F)` so that a product that is pure rounding noise counts as rank 0.

**Relation to the paper's iteration.** In exact arithmetic and under the full-rank hypothesis, this kernel and the paper's Eq. (2.6) iteration return the same range; the induction argument is in the [research note](research/spi-tensorization.md). This covers the subspace kernel only, not the paper's algorithm as a whole.

## M1: test matrices and sketches (`construct_sketches`, `construct_corange_sketch`)

`Y = A Omega` and `Z = A Phi`; separately `W = Psi A`. `Omega`, `Phi`, `Psi` are drawn one after another from the same `torch.Generator`, so a fixed seed reproduces all three and they differ from one another. This is deterministic replay, not a test of statistical independence.

- `gaussian`: i.i.d. standard normal entries (`torch.randn`; complex dtypes follow PyTorch's complex normal convention). This is the default and the only distribution used in the committed experiments.
- `sparsesign`: an exploratory **fixed-nonzero** distribution defined in this repository: each line along the shorter dimension has exactly `min(sparsity, shorter side)` nonzeros at uniformly random positions, with values `+-1/sqrt(nnz)`; storage is dense. It has **not** been shown equivalent to the paper's sparse Rademacher distribution or to a Johnson-Lindenstrauss embedding.

`construct_sketches` and `construct_corange_sketch` are ordinary matrix products over a resident `A`. They are not streaming and not one-pass: `A` is held in memory and multiplied three times (by `Omega`, by `Phi`, and from the left by `Psi`), as three separate products.

## M2: coefficients and truncated SVD (`solve_corange_coefficient`, `reconstruct_from_corange`)

Given `Q`, `Psi`, `W = Psi A`, the coefficient solves

```
B = argmin_X || (Psi Q) X - W ||_F ,   C = Psi Q   (d x s, d >= s)
```

If `C` has full column rank the minimizer is unique, `B = C^+ W` with `C^+ = (C^H C)^{-1} C^H`. The code uses `torch.linalg.lstsq` with the SVD driver `gelsd`, forms no explicit inverse, and never forms `Q B`. With the thin SVD `B = U_B diag(S) V_B^H` the result is

```
U = Q U_B[:, :r],   sigma = S[:r],   Vh = (V_B^H)[:r, :]   so that  A_hat = U diag(sigma) Vh = Q B_r ,
```

where `B_r` is the best rank-`r` approximation of `B`. Checks before solving: `Q` must be orthonormal (`||Q^H Q - I||_F <= 50 m eps`, else `ValueError`); `C` must be numerically full column rank (else `RankDeficiencyError`); if `cond(C)` exceeds `eps^(-1/2)` (or `max_condition`) an `IllConditionedWarning` is emitted and the result is still returned. The thresholds `50 m eps` and `eps^(-1/2)` are engineering choices, not derived bounds. Singular vectors are unique only up to sign or phase (and rotation at repeated singular values), so tests and reports compare matrices, norms and projectors, never individual vectors.

## M3: the end-to-end map (`sketch_power_low_rank`)

1. `Omega, Phi` drawn; `Y = A Omega`, `Z = A Phi`.
2. `Q = sketch_power_subspace(Y, Z, steps=q)` with the default rank safety.
3. `Psi` drawn (continuing the same generator); `W = Psi A`.
4. `B = argmin ||Psi Q B - W||_F`; return the rank-`r` truncated SVD of `Q B`.

Three products over a fully resident `A`; CPU only (non-CPU input raises `ValueError`). If `rank(A) < s`, step 2 raises `RankDeficiencyError`.

## M5: where the error comes from

Let `B* = Q^H A`, `E = (I - Q Q^H) A`, `D = B - B*`, and `B_r` the best rank-`r` approximation of `B`. Because `Q^H Q = I`, `Q^H E = 0`.

**Identity I (full `s`-rank `Q B`).** `A - Q B = E - Q D`, and `Q^H E = 0`, so

```
|| A - Q B ||_F^2  =  || E ||_F^2 + || D ||_F^2 .
```

**Identity II (final rank-`r` `Q B_r`).** `A - Q B_r = E + Q (B* - B_r)`, so

```
|| A - Q B_r ||_F^2  =  || E ||_F^2 + || B* - B_r ||_F^2 .
```

Both hold for any `B` and `B_r` once `Q` is orthonormal; they use no property of the least-squares solve. With `B = C^+ W` and `W = Psi A = C B* + Psi E` one also has `D = C^+ Psi E` (when `C` has full column rank, `C^+ C = I`), which is what makes `D` the error that the corange step adds.

**The cross term (do not add the squares).** Since `B* - B_r = -D + (B - B_r)`,

```
|| B* - B_r ||_F^2  =  || D ||_F^2 + || B - B_r ||_F^2 + cross ,    cross = -2 Re < D, B - B_r > .
```

`||B - B_r||_F^2` is the discarded tail of the singular values of `B`. The cross term is generally nonzero, and in the committed M5 data it is negative in almost all rows, so `D^2 + tail(B)^2` alone would overstate the second term. The sign convention is fixed by a hand-checkable 3 x 2 example in the tests (`tests/test_m5_diagnostics.py`, `test_hand_checkable_counterexample`).

**Reference quantities.** The optimal rank-`r` error is `||A - A_r||_F^2 = sum_{i>r} sigma_i(A)^2` (Eckart-Young). The "ideal-Q" error is `||A - Q (B*)_r||_F^2 = ||E||_F^2 + sum_{i>r} sigma_i(B*)^2`, what a perfect coefficient recovery inside `range(Q)` would give. Comparing `optimal`, `ideal-Q`, `Q B` and `Q B_r` shows which stage accounts for the observed error; this is a per-case accounting, not a causal statement about `q`, since `E` and `D` both change with `q`.

**Gaussian expectation (comparison target, not proved here).** If `Psi` has real i.i.d. standard normal entries independent of `(A, Q)` and `d > s + 1`, then `E ||D||_F^2 = s / (d - s - 1) * ||E||_F^2` (the trace of an inverse Wishart matrix). The M5 report compares measured `D^2 / E^2` with this value; the expectation is infinite for `d <= s + 1`. It is not used by the code and is not independently verified in this repository.

## Conditioning and floating point

`cond(C)` measures how much the least-squares step can amplify errors in `W`, but a small `cond(C)` does not mean a small `D`: `D = C^+ Psi E` also scales with `E`. In float64 the identities above held to about `1e-15` relative to the largest term on every successful M5 row. Behaviour for float32 is only lightly probed (M4), and `torch.float16`/`bfloat16`, matrices with rank below `s`, and very ill-conditioned `C` are outside the tested range (rank below `s` raises).
