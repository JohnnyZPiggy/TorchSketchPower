# TorchSketchPower

An independent **in-memory PyTorch research implementation** of sketch-power low-rank approximation on CPU and a **boundedly validated CUDA/T4 path**, inspired by Chang and Yang, *Improving Sketching Algorithms for Low-Rank Matrix Approximation via Sketch-Power Iterations*, SIAM J. Matrix Anal. Appl. 47(3), 2026, DOI [10.1137/25M1760143](https://doi.org/10.1137/25M1760143).

Given a resident matrix `A` (`m x n`), it returns a rank-`r` factorization `A ~ U diag(sigma) Vh` from random sketches of `A`, a power iteration on an auxiliary sketch, and a small least-squares solve. It comes with exact-SVD baselines, two committed CPU experiment reports, and a stated list of what it does not do.

## Research closeout (October 2026)

**Status: research snapshot; active experiments paused. No V1 release or performance claim.** Code and historical evidence are retained for reproduction. The current implementation is an **in-memory, multi-GEMM** approximation, **not** a one-pass/streaming reproduction of the paper's full algorithm. A bounded real Tesla T4 correctness run was performed (M7); broader CUDA correctness, portability, releases and speedups are *not* established. Details and limitations: [research closeout](docs/RESEARCH_CLOSEOUT.md).

| Milestone | Evidence-based finding |
|---|---|
| [M7 — CUDA correctness](experiments/m7_cuda/README.md) | Actual single-T4 numerical oracle: 171 PASS / 1 second-device-only NOT RUN; GPU test subset passed. Specific tested source/runtime only. |
| [M8 — accuracy/performance](reports/m8_gpu/m8-ref-t4-20261022-195451/review.md) | Exploratory T4/CPU runs; second run **75/80 fully measured**, one configured float64 dense-SVD oracle FAIL remains unresolved, other five GPU configs cold-only. Measured native `torch.svd_lowrank` often outperformed SPI in this tested regime; no general ranking. |
| [M9 — compilation](reports/m9_compile/m9-t4-20261022-204314/review.md) | Partial `torch.compile` graph capture and graph breaks; three tested Inductor warm pairs were slower than eager on one T4. |
| [M10 — cost model](experiments/m10_cost/README.md) | Symbolic operation, memory and synchronization audit; no measured GPU stage bottlenecks. |
| [M11 — concatenated GEMM](reports/m11_concat/m11-20261022-214747/review.md) | **REJECT** as an unrestricted API-preserving optimization: a saved CPU input changes numerical-rank branching and final RNG state. No GPU attempted. |
| [M12 — spectral phase diagram](https://github.com/JohnnyZPiggy/TorchSketchPower/issues/28) | Planned only, **NOT RUN**; deferred at research closeout. |

**Licensing:** no root `LICENSE` was present at this snapshot; this README does not grant reuse rights. No release/tag was created.

## Historical V1 development status (pre-M7; superseded by the closeout above)

| | |
|---|---|
| Stage | **V1 in development; release NOT APPROVED.** V1 is defined (Scientist decision, [Issue #16](https://github.com/JohnnyZPiggy/TorchSketchPower/issues/16)) as an independent PyTorch implementation that also includes GPU development and validated acceleration; V2 is later reuse of Panther, skerch and similar ecosystems. Milestones M0-M5 (the CPU baseline) are merged; M6 (GPU readiness audit, [docs/gpu-readiness.md](docs/gpu-readiness.md)) is merged as a design document; M7 (GPU native correctness) has a code candidate whose GPU run is **BLOCKED** (no CUDA environment available to the Engineer; nothing has run on a GPU), and M8-M10 (GPU performance, `torch.compile`, independent CPU/GPU validation) are **NOT RUN**. At the time of writing no tag and no GitHub Release exists (inventory and gates in the [release checklist](docs/RELEASE_CHECKLIST.md)). Package version in `pyproject.toml`: `0.1.0`. |
| Is | A bounded, tested, documented PyTorch implementation of: sketch construction, the subspace power kernel, corange least-squares recovery, and their composition, with CPU numerical evidence. |
| Is not | A verified reproduction of the paper's complete Algorithm 2.1; a one-pass or streaming implementation; accelerator-validated (GPU/TPU, `torch.compile` all NOT RUN); evidence of any speedup; a convergence proof or rate. |
| Tested on | Windows 11, Python 3.14.6, torch 2.14.1+cpu, pytest 9.1.1 (493 passed and 46 GPU tests skipped, Engineer-run, not independently re-run by the Architect). `requires-python >= 3.10` and `torch >= 2.2` in `pyproject.toml` are declared but **not verified** on other versions. |

## Install and test (CPU)

From a clean checkout, in a fresh virtual environment (Python with a CPU build of `torch` available):

```bash
python -m venv .venv
. .venv/bin/activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install .         # non-editable install; installs torch>=2.2 if missing
python -m pip install pytest
python -m pytest -q             # run from the repository root: 493 passed, 46 GPU-only tests skipped (NOT RUN) without CUDA
```

For development use `python -m pip install -e '.[test]'` instead. Tests need no GPU and no network access beyond installing dependencies.

## Minimal example

```python
import torch
from torchsketchpower import sketch_power_low_rank, RankDeficiencyError

m, n, r = 120, 80, 4
g = torch.Generator().manual_seed(0)
u0 = torch.linalg.qr(torch.randn(m, n, generator=g, dtype=torch.float64)).Q
v0 = torch.linalg.qr(torch.randn(n, n, generator=g, dtype=torch.float64)).Q
sigma0 = 0.5 ** torch.arange(n, dtype=torch.float64)          # geometric spectrum
A = (u0 * sigma0) @ v0.mH

u, sigma, vh = sketch_power_low_rank(
    A, r=r, s=8, ell=16, d=16, steps=1, generator=torch.Generator().manual_seed(1)
)
A_hat = (u * sigma) @ vh
print(u.shape, sigma.shape, vh.shape)                           # (120, 4) (4,) (4, 80)
rel = torch.linalg.matrix_norm(A - A_hat) / torch.linalg.matrix_norm(A)
opt = (sigma0[r:] ** 2).sum().sqrt() / (sigma0 ** 2).sum().sqrt()
print(f"relative Frobenius error {rel:.3e}; optimal rank-{r} error {opt:.3e}")

low = torch.randn(m, 2, generator=g, dtype=torch.float64) @ torch.randn(2, n, generator=g, dtype=torch.float64)
try:                                                            # rank(A) = 2 < s = 4
    sketch_power_low_rank(low, r=2, s=4, ell=8, d=8, generator=torch.Generator().manual_seed(2))
except RankDeficiencyError as exc:
    print("RankDeficiencyError:", exc)
```

Expected output on the tested environment (the last digits can vary with the torch build):

```
torch.Size([120, 4]) torch.Size([4]) torch.Size([4, 80])
relative Frobenius error 6.265e-02; optimal rank-4 error 6.250e-02
RankDeficiencyError: y has numerical rank 2 < k=4; the powered range is not k-dimensional
```

## What it computes

For `A` (`m x n`), `1 <= r <= s <= m`, `r <= n`, `s < ell` (`ell` may exceed `m`), `d >= s`, `q >= 0`:

1. Draw `Omega` (`n x s`), `Phi` (`n x ell`); form `Y = A Omega` (`m x s`), `Z = A Phi` (`m x ell`).
2. `Q = orth( (Z Z^H)^q Y )` (`m x s`, never forming `Z Z^H`), by alternating QR on `Z^H Q` and `Z X`.
3. Draw `Psi` (`d x m`); form `W = Psi A` (`d x n`).
4. Solve `B = argmin || (Psi Q) B - W ||_F` (`s x n`) by least squares; return the rank-`r` truncated SVD of `Q B` as `U` (`m x r`), `sigma` (`r`), `Vh` (`r x n`), without forming `Q B`.

Complex dtypes use the conjugate transpose throughout. This is three matrix products over a resident `A`: **not** one-pass and **not** streaming. Full derivations, the assumptions, and the error identities (including the cross term that must not be dropped) are in [docs/math.md](docs/math.md).

## API

All names are importable from `torchsketchpower`.

| Function | Returns | Purpose |
|---|---|---|
| `sketch_power_low_rank(a, r, s, ell, d, *, steps=1, distribution="gaussian", generator=None, max_condition=None, **kw)` | `(u, sigma, vh)` | End-to-end CPU pipeline above. `**kw` (e.g. `sparsity`) goes to the test matrix constructor. |
| `sketch_power_subspace(y, z, steps=1, on_rank_deficient="raise")` | `Q` | Orthonormal basis of `span((z z^H)^steps y)`. |
| `construct_sketches(a, s, ell, *, distribution, generator, **kw)` | `(Y, Z)` | `A @ Omega`, `A @ Phi` with independent draws. |
| `construct_corange_sketch(a, d, *, distribution, generator, **kw)` | `(Psi, W)` | `Psi` and `Psi @ A`. |
| `solve_corange_coefficient(q, psi, w, *, max_condition=None)` | `B` | Least-squares coefficients with rank and conditioning checks. |
| `reconstruct_from_corange(q, psi, w, r, *, max_condition=None)` | `(u, sigma, vh)` | Rank-`r` truncated SVD of `Q B`. |
| `gaussian_test_matrix`, `sparse_sign_test_matrix`, `test_matrix` | tensor | Random test matrices. `sparse_sign_test_matrix` is an exploratory fixed-nonzero distribution, not shown equivalent to the paper's. |

**Failure and warning behaviour.**

- `ValueError` / `TypeError`: wrong shape, non-floating input, parameters out of range, unknown `distribution`, non-CPU input to `sketch_power_low_rank`, or `Q` not orthonormal.
- `RankDeficiencyError`: `Y`, a cross product `Z^H Q`, or `Psi Q` is numerically rank deficient (for example `rank(A) < s`). It is the default and `sketch_power_low_rank` never suppresses it.
- `IllConditionedWarning`: `cond(Psi Q)` exceeds `eps^(-1/2)` (or `max_condition`); a result is still returned. `RankDeficiencyWarning` appears only when `sketch_power_subspace` is called with `on_rank_deficient="warn"`.
- A finite, orthonormal output alone does not mean a correct result; the rank checks exist for that reason.

**Numerical notes.** The rank tolerance is `max(shape) * eps * s_max`. The least-squares solve uses SVD-based `lstsq` (`gelsd`) with no explicit inverse. The tolerances `50 * m * eps` (orthonormality) and `eps^(-1/2)` (conditioning warning) are engineering choices, not derived bounds. Tested dtypes: float32, float64, complex64, complex128.

## Evidence

Two committed, reproducible CPU experiments on synthetic matrices with a prescribed spectrum (80 x 60, `r = 6`, 5 seeds per setting). Details, tables, caveats and links: [docs/cpu-results.md](docs/cpu-results.md).

- **M4 accuracy and cost** ([`reports/m4_cpu`](reports/m4_cpu/README.md), [PR #11](https://github.com/JohnnyZPiggy/TorchSketchPower/pull/11), [Issue #10](https://github.com/JohnnyZPiggy/TorchSketchPower/issues/10)): 110 accuracy rows (105 ok, 5 expected `RankDeficiencyError`), 96 timing rows, 8 working-set measurements. With a geometric spectrum the median Frobenius error is within about 2% of the SVD optimum at `q = 1`; with the polynomial and flat spectra it is not (median ratio about 1.4 for both at `q = 1`). More power steps did not improve every seed.
- **M5 error decomposition** ([`reports/m5_cpu`](reports/m5_cpu/README.md), [PR #13](https://github.com/JohnnyZPiggy/TorchSketchPower/pull/13), [Issue #12](https://github.com/JohnnyZPiggy/TorchSketchPower/issues/12)): 65 cases (63 ok, 2 expected failures). Both exact squared-error identities hold to about 1e-15 relative; for the flat spectrum the range `Q` is near optimal but the corange recovery adds a large error whose size tracks `s / (d - s - 1)` in the tested draws.
- Timings are sub-2 ms single-machine measurements and **support no speed claim**; working-set numbers are process high-water marks, not per-call allocations; buffer sizes are estimates.

Earlier milestones: [PR #2](https://github.com/JohnnyZPiggy/TorchSketchPower/pull/2) (M0 subspace kernel, [Issue #1](https://github.com/JohnnyZPiggy/TorchSketchPower/issues/1)), [PR #5](https://github.com/JohnnyZPiggy/TorchSketchPower/pull/5) (M1, [Issue #4](https://github.com/JohnnyZPiggy/TorchSketchPower/issues/4)), [PR #7](https://github.com/JohnnyZPiggy/TorchSketchPower/pull/7) (M2, [Issue #6](https://github.com/JohnnyZPiggy/TorchSketchPower/issues/6)), [PR #9](https://github.com/JohnnyZPiggy/TorchSketchPower/pull/9) (M3, [Issue #8](https://github.com/JohnnyZPiggy/TorchSketchPower/issues/8)).

## Limitations

- In-memory only: **bounded single-T4 CUDA correctness was validated in M7**, while end-to-end portability, full GPU regression coverage and broader numerical validation remain unestablished. M8 includes incomplete runs and an unresolved numerical-oracle FAIL. See the [closeout](docs/RESEARCH_CLOSEOUT.md) for current evidence; historical M7-readiness documents are pre-run snapshots.
- Not a verified implementation of the paper's Algorithm 2.1; paper-level equivalence is **UNVERIFIED**. The paper's *Require* line has a dimension inconsistency recorded in the [research note](docs/research/spi-tensorization.md).
- The sparse-sign option is an exploratory fixed-nonzero distribution; it was not exercised in the committed experiments.
- Results cover only the tested synthetic grid (small sizes, 5 seeds, four spectra). No general accuracy, rate or speed claim is made.
- `rank(A) >= s` is required; below that the call raises by design.
- The declared minimums (`python >= 3.10`, `torch >= 2.2`) are not verified; only the environment in the Status table was tested.
- No `LICENSE` file exists in the repository root; reuse terms are not established. The upstream MATLAB implementation also has no root license, so none of its code was copied.

## Reproducing the results

The reports are generated by the committed runners. From a clean checkout, in a fresh environment with `python -m pip install .` done as above:

```bash
python experiments/m4_cpu/run_m4.py --out out_m4      # about 20 to 25 s on the tested machine
python experiments/m5_cpu/run_m5.py --out out_m5      # a few seconds; reads reports/m4_cpu/samples.csv
```

Both write `samples.csv/json`, a generated `summary.md` and a `manifest.json` with environment details and SHA-256 hashes (M4 additionally writes timings and memory). Expected: sample files are deterministic in a given environment, so `samples.csv` reproduces the committed rows byte for byte on the tested environment; timings and memory differ run to run. On another machine, thread count or torch build, expect the same structure but possibly different last digits and different timings. The committed manifests record the experiment source SHAs (M4 `36e94999b7cf6f64d6437d0c2179fe1eb762386e`, M5 `096cce0bb78974d0aeff53c723c1cf10cbd71519`); the code under `experiments/` and `src/` on `main` is byte-identical to those revisions, although the commit SHAs differ because the PRs were squash-merged. A quick check that the install works:

```bash
python -c "import torchsketchpower as t; print(sorted(t.__all__))"
```

## Documentation

[Research closeout and evidence index](docs/RESEARCH_CLOSEOUT.md) is the current milestone reference; earlier readiness and status pages describe historical phases and may retain their original pre-run wording.


[docs/README.md](docs/README.md) lists the documents: [mathematics](docs/math.md), [CPU results](docs/cpu-results.md), [GPU readiness audit](docs/gpu-readiness.md), [research note](docs/research/spi-tensorization.md) and the [release checklist](docs/RELEASE_CHECKLIST.md).

## Provenance and project process

- Paper: Chang and Yang (2026), DOI [10.1137/25M1760143](https://doi.org/10.1137/25M1760143). Upstream MATLAB reference (read only, not copied): [Mitchell-Cxyk/SketchPowerIteration](https://github.com/Mitchell-Cxyk/SketchPowerIteration) at `752be34fbd26595f8d608a25e7dcdea586a6e0ca`, which has no root license.
- Developed with the SAE V3.3 workflow (Scientist / Architect / Engineer roles; GitHub Issues and PRs as the record). The framework is pinned and snapshotted verbatim in [`.sae/`](.sae/) from `JohnnyZPiggy/SAE-Framework@65338eb1aa67971e110db982a07cf43161c23446`; see [`AGENTS.md`](AGENTS.md) and [`sae.yaml`](sae.yaml). The Engineer role does not merge or release.
- Third-party RandNLA libraries (for example Panther or skerch) are **not** part of V1 and are not dependencies; any such comparison belongs to separate V2 work.
