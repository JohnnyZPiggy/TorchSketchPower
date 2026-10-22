# CPU results (M4 and M5)

All numbers on this page are read from the committed raw data in [`reports/m4_cpu/`](../reports/m4_cpu/) and [`reports/m5_cpu/`](../reports/m5_cpu/); the tables below are summaries of `samples.csv`, `timings.csv` and `memory.csv` (the generated [M4 summary](../reports/m4_cpu/summary.md) and [M5 summary](../reports/m5_cpu/summary.md) contain the same values). Nothing was re-run, edited or extrapolated for this page.

**How to read them.** These are small, CPU-only, single-machine experiments on synthetic matrices with a prescribed spectrum, with **5 seeds per setting** and medians over those seeds. They describe the tested grid. They do not establish general convergence, a rate, or behaviour on other spectra, sizes, dtypes or devices, and they are not evidence of speed. Raw rows (including failures) are in the CSV files; every claim below can be checked against them.

| | M4 ([`reports/m4_cpu/`](../reports/m4_cpu/README.md)) | M5 ([`reports/m5_cpu/`](../reports/m5_cpu/README.md)) |
|---|---|---|
| Question | Accuracy of `sketch_power_low_rank` against the exact SVD, by `q`, sketch sizes, spectrum, shape; cost | Where the error comes from: subspace (E), corange recovery (D), rank-r truncation (cross term) |
| Rows | 110 accuracy rows (105 ok, 5 expected `RankDeficiencyError`); 96 timing rows; 8 memory configurations | 65 cases (63 ok, 2 expected `RankDeficiencyError`; 1 `IllConditionedWarning` row) |
| Experiment source SHA | `36e94999b7cf6f64d6437d0c2179fe1eb762386e` (clean tree) | `096cce0bb78974d0aeff53c723c1cf10cbd71519` (clean tree) |
| Environment (per manifest) | Windows-11-10.0.26200, Python 3.14.6, torch 2.14.1+cpu, 8 torch threads, CPU only | same |
| Evidence PR / Issue | [PR #11](https://github.com/JohnnyZPiggy/TorchSketchPower/pull/11) / [Issue #10](https://github.com/JohnnyZPiggy/TorchSketchPower/issues/10) | [PR #13](https://github.com/JohnnyZPiggy/TorchSketchPower/pull/13) / [Issue #12](https://github.com/JohnnyZPiggy/TorchSketchPower/issues/12) |

The experiment code that produced both reports is byte-identical on `main` today (`experiments/` and `src/` show no difference between the two source SHAs above and the consolidated `main`), but the SHAs differ because the PRs were squash-merged. All results were produced by the project's own Engineer runs; no independent rerun by the Architect has been performed.

## Setup (both experiments)

Test matrices are `A = U diag(sigma) V^H` in float64 with seeded orthonormal `U`, `V` (80 x 60 unless noted), target rank `r = 6`, Gaussian test matrices, and (unless noted) `s = 12`, `ell = d = 24`. Spectra: `geometric` sigma_i = 0.7^(i-1), `polynomial` sigma_i = 1/i, `flat` (linear from 1 down to 0.9), and `exact_low_rank` (rank 8). "Optimal" is the exact SVD truncation to rank 6 (Eckart-Young), computed from the matrix the algorithm saw. Errors are relative to `||A||`. The `q` comparisons use the same `A` and the same random draws for every `q`; comparisons across sketch sizes change the random streams and are **not** common-random-number comparisons.

## M4: accuracy

### Effect of `q` (80 x 60, `s, ell, d = 12, 24, 24`, 5 seeds)

| spectrum | q | ok/n | median rel. Frobenius error | min..max | median optimal (SVD) | median ratio to optimal | median rel. spectral error | optimal spectral |
|---|---|---|---|---|---|---|---|---|
| geometric | 0 | 5/5 | 1.222e-01 | 1.207e-01..1.324e-01 | 1.176e-01 | 1.038 | 1.189e-01 | 1.176e-01 |
| geometric | 1 | 5/5 | 1.197e-01 | 1.192e-01..1.208e-01 | 1.176e-01 | 1.017 | 1.179e-01 | 1.176e-01 |
| geometric | 2 | 5/5 | 1.197e-01 | 1.195e-01..1.205e-01 | 1.176e-01 | 1.018 | 1.179e-01 | 1.176e-01 |
| polynomial | 0 | 5/5 | 4.655e-01 | 4.262e-01..5.306e-01 | 2.901e-01 | 1.605 | 2.944e-01 | 1.429e-01 |
| polynomial | 1 | 5/5 | 3.994e-01 | 3.726e-01..4.134e-01 | 2.901e-01 | 1.377 | 2.320e-01 | 1.429e-01 |
| polynomial | 2 | 5/5 | 4.067e-01 | 3.708e-01..4.163e-01 | 2.901e-01 | 1.402 | 2.612e-01 | 1.429e-01 |
| flat | 0 | 5/5 | 1.307e+00 | 1.152e+00..1.354e+00 | 9.435e-01 | 1.385 | 4.327e+00 | 9.898e-01 |
| flat | 1 | 5/5 | 1.281e+00 | 1.231e+00..1.324e+00 | 9.435e-01 | 1.358 | 4.076e+00 | 9.898e-01 |
| flat | 2 | 5/5 | 1.266e+00 | 1.244e+00..1.423e+00 | 9.435e-01 | 1.342 | 4.011e+00 | 9.898e-01 |

Paired on identical `A` and draws (per seed):

| spectrum | pairs | q=1 better than q=0 | q=2 better than q=1 | q=2 better than q=0 |
|---|---|---|---|---|
| geometric | 5 | 5 | 2 | 5 |
| polynomial | 5 | 5 | 2 | 5 |
| flat | 5 | 3 | 2 | 2 |

Observed: `q = 1` improved on `q = 0` in every paired seed for the geometric and polynomial spectra but in only some for the flat spectrum, and `q = 2` improved on `q = 1` in only part of the pairs. The per-seed results are not monotone in `q`, so no per-realization improvement is claimed.

### Effect of sketch sizes (`q = 1`, 80 x 60)

| spectrum | (s, ell, d) | ok/n | median rel. Frobenius error | min..max | median ratio to optimal |
|---|---|---|---|---|---|
| geometric | (8, 12, 12) | 5/5 | 2.170e-01 | 1.776e-01..2.877e-01 | 1.844 |
| geometric | (8, 16, 16) | 5/5 | 1.581e-01 | 1.463e-01..1.659e-01 | 1.344 |
| geometric | (12, 16, 16) | 5/5 | 1.247e-01 | 1.218e-01..1.308e-01 | 1.060 |
| geometric | (12, 24, 24) | 5/5 | 1.197e-01 | 1.192e-01..1.208e-01 | 1.017 |
| polynomial | (8, 12, 12) | 5/5 | 5.551e-01 | 5.306e-01..7.076e-01 | 1.914 |
| polynomial | (8, 16, 16) | 5/5 | 4.686e-01 | 4.061e-01..5.518e-01 | 1.616 |
| polynomial | (12, 16, 16) | 5/5 | 5.276e-01 | 4.870e-01..5.508e-01 | 1.819 |
| polynomial | (12, 24, 24) | 5/5 | 3.994e-01 | 3.726e-01..4.134e-01 | 1.377 |

The geometric spectrum shows the error ratio falling as the sizes grow; the polynomial spectrum does not fall monotonically over these four settings. With 5 seeds and different random streams per setting, these numbers do not separate the effect of the sizes from sampling noise.

### Shapes, exact low rank, float32

| case | configuration | ok/n | median rel. Frobenius error | median ratio to optimal |
|---|---|---|---|---|
| shape 80x60 (reference) | geometric, q=1, (12, 24, 24) | 5/5 | 1.197e-01 | 1.017 |
| shape 60x80 | geometric, q=1, (12, 24, 24) | 5/5 | 1.196e-01 | 1.016 |
| shape 96x96 | geometric, q=1, (12, 24, 24) | 5/5 | 1.193e-01 | 1.014 |
| exact rank 8, s=8 | q=1, (8, 16, 16) | 5/5 | 1.027e-01 | 1.000 |
| exact rank 8, s=12 > rank | q=1, (12, 24, 24) | 0/5 (`RankDeficiencyError`) | n/a | n/a |
| float32, q=0 | geometric, (12, 24, 24) | 5/5 | 1.303e-01 | 1.107 |
| float32, q=1 | geometric, (12, 24, 24) | 5/5 | 1.201e-01 | 1.021 |
| float32, q=2 | geometric, (12, 24, 24) | 5/5 | 1.207e-01 | 1.026 |

Notes: `exact rank 8, s=8` recovers the best rank-6 truncation (ratio 1.000). With `s` larger than the rank, `sketch_power_subspace` raises `RankDeficiencyError`; the 5 rows are kept as failures, not dropped. The float32 rows use their own random stream (no matched float32/float64 draws), so no split into stochastic and round-off error is claimed.

## M4: cost (indicative only)

One fresh process per row; the call includes validation, sketches, rank checks, power steps and reconstruction; matrix construction is excluded. Warm = the next 5 calls after the first (cold) call.

| configuration (geometric, seed 0, float64) | cold call (ms) | warm median (ms) | warm IQR (ms) | full SVD warm median (ms) | working-set high-water before / after (MB) | buffer estimate (KB, not measured) |
|---|---|---|---|---|---|---|
| 80x60-s12-l24-d24-q0 | 1.69 | 0.850 | 0.221 | 0.486 | 204.0 / 207.2 | 92.1 |
| 80x60-s12-l24-d24-q1 | 1.84 | 0.873 | 0.083 | 0.497 | 204.4 / 207.6 | 92.1 |
| 80x60-s12-l24-d24-q2 | 1.99 | 1.266 | 0.189 | 0.594 | 204.2 / 207.4 | 92.1 |
| 80x60-s8-l12-d12-q1 | 1.75 | 0.732 | 0.186 | 0.511 | 204.2 / 207.2 | 52.6 |
| 80x60-s8-l16-d16-q1 | 1.61 | 0.763 | 0.165 | 0.484 | 204.7 / 207.7 | 62.1 |
| 80x60-s12-l16-d16-q1 | 1.77 | 0.824 | 0.239 | 0.586 | 204.1 / 207.2 | 72.4 |
| 60x80-s12-l24-d24-q1 | 1.77 | 0.984 | 0.091 | 0.552 | 204.2 / 207.5 | 92.1 |
| 96x96-s12-l24-d24-q1 | 1.83 | 1.042 | 0.258 | 0.970 | 204.7 / 208.4 | 123.8 |

- These are sub-2 ms single-run, single-machine timings with a spread comparable to the differences between rows. **They support no speed, scaling or speedup claim**, and no comparison with another implementation or device was made.
- The working-set numbers are the operating-system high-water mark of the whole process; they are dominated by the PyTorch runtime and are **not** a per-call allocation. The buffer column is a sum of tensor sizes computed from the formula in `experiments/m4_cpu/m4lib.py` (`estimate_buffer_bytes`): an **estimate**, not a measurement of peak memory.

## M5: where the error comes from

Notation (full derivation in [math.md](math.md)): `E = (I - Q Q^H) A` is what the sketched range `Q` misses; `D = B - Q^H A` is the error added by recovering the coefficients from `Psi`; `tail(B)^2 = ||B - B_r||^2` is the discarded part of `B`; `cross = -2 Re <D, B - B_r>`; the final error satisfies `final^2 = E^2 + ||Q^H A - B_r||^2 = E^2 + D^2 + tail(B)^2 + cross`. "Ideal-Q" is the rank-r truncation of `Q Q^H A`, i.e. what a perfect recovery inside the sketched range would give. All squared quantities are relative to `||A||_F^2`; medians over 5 seeds (80 x 60, `s, ell, d = 12, 24, 24`).

| spectrum | q | optimal r-term error^2 | ideal-Q error^2 | E^2 | D^2 | tail(B)^2 | cross | final error^2 | final minus ideal-Q | negative cross | median D^2/E^2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| geometric | 0 | 1.384e-02 | 1.427e-02 | 1.281e-03 | 8.341e-04 | 1.386e-02 | -1.226e-03 | 1.493e-02 | 6.561e-04 | 4/5 | 0.888 |
| geometric | 1 | 1.384e-02 | 1.394e-02 | 4.455e-04 | 5.593e-04 | 1.375e-02 | -2.605e-04 | 1.432e-02 | 3.667e-04 | 5/5 | 1.203 |
| geometric | 2 | 1.384e-02 | 1.395e-02 | 4.812e-04 | 5.845e-04 | 1.370e-02 | -3.010e-04 | 1.433e-02 | 3.829e-04 | 5/5 | 1.152 |
| polynomial | 0 | 8.414e-02 | 1.177e-01 | 9.313e-02 | 9.983e-02 | 4.476e-02 | -3.463e-02 | 2.167e-01 | 8.300e-02 | 5/5 | 0.872 |
| polynomial | 1 | 8.414e-02 | 9.927e-02 | 6.872e-02 | 7.797e-02 | 4.984e-02 | -3.359e-02 | 1.596e-01 | 6.087e-02 | 5/5 | 1.145 |
| polynomial | 2 | 8.414e-02 | 1.000e-01 | 6.943e-02 | 8.030e-02 | 4.944e-02 | -3.569e-02 | 1.654e-01 | 6.538e-02 | 5/5 | 1.157 |
| flat | 0 | 8.902e-01 | 8.970e-01 | 7.990e-01 | 9.249e-01 | 2.086e-01 | -2.172e-01 | 1.708e+00 | 8.109e-01 | 5/5 | 1.158 |
| flat | 1 | 8.902e-01 | 8.969e-01 | 7.986e-01 | 8.596e-01 | 2.087e-01 | -2.182e-01 | 1.642e+00 | 7.449e-01 | 5/5 | 1.075 |
| flat | 2 | 8.902e-01 | 8.970e-01 | 7.989e-01 | 8.245e-01 | 2.117e-01 | -2.245e-01 | 1.602e+00 | 7.057e-01 | 5/5 | 1.033 |

### Identity and oracle checks

- Over the 63 successful rows the two exact squared-error identities (full `Q B` and rank-r `Q B_r`) and the cross-term expansion hold to a maximum of 1.3e-15 (identity I) and 1.7e-15 (identity II and expansion) relative to the largest term; the number of rows where a flag failed is 0. The residual is relative to the largest term because the deliberately ill-conditioned row has terms of size about 1e15.
- Maximum `||Q^H E|| / ||A||` is 7.9e-16; `B` agrees with an independent SVD-pseudoinverse solution to 3.4e-15; `D` agrees with `C^+ Psi E` to 1.3e-13.
- The diagnostic replay of the pipeline matches `sketch_power_low_rank` to 2.8e-16, and matches the final errors of the 45 committed M4 rows (same ids and seeds) to 2.8e-16 (relative).
- Negative controls recorded as rows: [('tiny_rank_def_a', 'RankDeficiencyError'), ('tiny_dup_psi', 'RankDeficiencyError')] (`RankDeficiencyError`, expected); ['tiny_illcond'] (`IllConditionedWarning`, status ok, identities still hold).

### Observations (this grid only)

- **Flat spectrum.** The subspace stage is close to optimal (the ideal-Q error is within 0.01 of the optimal error in the table), yet the final error is about 1.6 to 1.7 (relative squared), larger than the norm of `A` itself, with a relative spectral error above 4. The excess over the ideal-Q error is the corange step, not the range `Q`. `E^2` and `D^2` are of comparable size.
- **Why `D` can be large.** For a real Gaussian `Psi` independent of `(A, Q)`, the expected ratio `D^2 / E^2` is `s / (d - s - 1)` when `d > s + 1` (a classical inverse-Wishart trace; compared numerically here, not proved in this repository). At `d = 24, s = 12` that is 1.091; the measured medians are in the last column above. Holding `A` and `Q` fixed and changing only `Psi`:

| spectrum | Psi variant | d | E^2 (fixed) | D^2 | D^2/E^2 | s/(d-s-1) | cross | final error^2 | rel. Frobenius error | cond(C) |
|---|---|---|---|---|---|---|---|---|---|---|
| flat | prefix-d12 | 12 | 7.986e-01 | 9.657e+00 | 12.093 | n/a | -4.748e-01 | 1.032e+01 | 3.212e+00 | 17.876 |
| flat | prefix-d16 | 16 | 7.986e-01 | 2.028e+00 | 2.539 | 4.000 | -3.279e-01 | 2.763e+00 | 1.662e+00 | 7.020 |
| flat | prefix-d24 | 24 | 7.986e-01 | 5.873e-01 | 0.735 | 1.091 | -2.159e-01 | 1.378e+00 | 1.174e+00 | 3.457 |
| flat | prefix-d48 | 48 | 7.986e-01 | 2.971e-01 | 0.372 | 0.343 | -1.266e-01 | 1.133e+00 | 1.065e+00 | 2.834 |
| flat | seed1-d24 | 24 | 7.986e-01 | 8.951e-01 | 1.121 | 1.091 | -2.568e-01 | 1.666e+00 | 1.291e+00 | 4.195 |
| flat | seed2-d24 | 24 | 7.986e-01 | 7.727e-01 | 0.968 | 1.091 | -1.963e-01 | 1.574e+00 | 1.255e+00 | 3.681 |
| flat | seed3-d24 | 24 | 7.986e-01 | 1.130e+00 | 1.415 | 1.091 | -2.346e-01 | 1.912e+00 | 1.383e+00 | 5.021 |
| geometric | prefix-d12 | 12 | 5.133e-04 | 6.646e-02 | 129.463 | n/a | -2.103e-03 | 8.797e-02 | 2.966e-01 | 40.521 |
| geometric | prefix-d16 | 16 | 5.133e-04 | 2.436e-03 | 4.745 | 4.000 | -2.256e-03 | 1.508e-02 | 1.228e-01 | 8.978 |
| geometric | prefix-d24 | 24 | 5.133e-04 | 9.026e-04 | 1.758 | 1.091 | -7.852e-04 | 1.438e-02 | 1.199e-01 | 4.121 |
| geometric | prefix-d48 | 48 | 5.133e-04 | 2.565e-04 | 0.500 | 0.343 | 8.913e-05 | 1.405e-02 | 1.185e-01 | 2.300 |
| geometric | seed1-d24 | 24 | 5.133e-04 | 3.543e-04 | 0.690 | 1.091 | -8.023e-05 | 1.411e-02 | 1.188e-01 | 4.356 |
| geometric | seed2-d24 | 24 | 5.133e-04 | 7.102e-04 | 1.384 | 1.091 | -7.020e-04 | 1.446e-02 | 1.203e-01 | 5.556 |
| geometric | seed3-d24 | 24 | 5.133e-04 | 5.384e-04 | 1.049 | 1.091 | -8.923e-04 | 1.421e-02 | 1.192e-01 | 4.422 |

  For the flat spectrum `D^2` falls steeply as `d` grows (nested rows of one Gaussian matrix), and three independent `d = 24` draws differ from each other. `cond(C)` stays modest in these rows, so the condition number alone does not account for the size of `D`. This is a consistency check on a handful of draws (one per nested `d`, four at `d = 24`), not a proof, and nothing here recommends a particular `d`; for `d <= s + 1` the expectation is infinite, and the `d = 12` rows show large values.
- **Cross term.** `cross` is negative in 57 of 59 baseline and controlled-Psi rows, so omitting it overstates `||Q^H A - B_r||^2`. It is not zero in general and must be kept in the decomposition.
- **Geometric and polynomial spectra.** For geometric, `q` helps mainly through `Q` (`E^2` is larger at `q = 0`); for polynomial, `D^2` is at least as large as `E^2` at every `q`.

## What these results do not show

No GPU, TPU, `torch.compile`, streaming or one-pass run was made; no speedup, convergence rate or comparison with the paper's algorithm or other libraries was made; the fixed-nonzero sparse-sign test matrices were not evaluated; sizes beyond 96 x 96, other dtypes beyond float32/float64 and complex dtypes outside the unit tests were not run. See [README](../README.md#limitations).

## Reproducing

See [reproducibility instructions](../README.md#reproducing-the-results). Re-running on another machine, thread count or torch build changes timings and memory exactly, and can change the last digits of floating-point results; the sample files are deterministic in a given environment.
