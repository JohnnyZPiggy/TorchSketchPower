# M8: one T4 performance attempt â€” BLOCKED, partial data retained

Tested source `e986a1b03abf772e383778865ef47d16687bb77d`, starting main `697389ab6795912b857a95ce2351ff839c76bd36`; fixed SAE `65338eb1aa67971e110db982a07cf43161c23446`. Issue #20 / Draft PR #21.

Installed-package provenance and short M7 CUDA gate PASS (39 PASS, 1 legitimate single-GPU NOT_RUN). Actual Tesla T4, Python 3.13.15, torch 2.11.0+cu130, CUDA 13.0, one CPU thread, TF32 disabled. One allocation, no retry. Stop succeeded and strict fresh AUTHENTICATED_ZERO confirmed at 2026-10-22 17:36:04 UTC.

Overall M8 **BLOCKED**, not transport PASS: 60/80 configs completed warm measurements (50 GPU, 10 CPU). 305 actual calls retained, no runtime failures or timed warnings. One accuracy-audit FAIL; 4 additional configs have cold-only results; 15 configurations NOT RUN. Do not infer complete or validated speedup.

Failure: m10-cuda-4, dense SVD, 1024x512 near-flat float32. Observed Frobenius / reference optimum = 0.9999256131718273, below preset 1 - 500 eps = 0.9999403953552246. The direct residual norm is 21.88224310079404; CUDA reference optimum is 21.88387097254383. Full exception and all residual/reference singular values are retained. The intended pre-cast spectrum gives 21.88224308110135, suggesting a reference-precision issue, but this is an offline hypothesis, not an independent realized-input oracle. No threshold was loosened and no rerun occurred. See reference-audit.json.

First preregistered matrix: 256x128 geometric float32, rank 8. Wall/event are whole-call milliseconds, not kernel-only. Three warm repeats; allocator delta is not true per-call/device-wide allocation.

| device | method | steps / niter | wall median ms | wall IQR ms | event median ms | Fro / optimal | peak allocated delta MiB |
|---|---|---|---|---|---|---|---|
| cpu | spi | 0 | 1.4302 | 0.0672 | NOT MEASURED | 1.425559 | NOT MEASURED |
| cpu | spi | 1 | 1.6278 | 0.0687 | NOT MEASURED | 1.272156 | NOT MEASURED |
| cpu | svd_lowrank | 0 | 1.0205 | 0.1057 | NOT MEASURED | 1.093193 | NOT MEASURED |
| cpu | svd_lowrank | 1 | 1.1794 | 0.0238 | NOT MEASURED | 1.003890 | NOT MEASURED |
| cpu | dense_svd | None | 3.5534 | 0.0528 | NOT MEASURED | 1.000000 | NOT MEASURED |
| cuda | spi | 0 | 3.8383 | 0.7607 | 3.7896 | 1.488145 | 3.1509 |
| cuda | spi | 1 | 5.5725 | 0.9959 | 5.5333 | 1.242969 | 3.1509 |
| cuda | svd_lowrank | 0 | 1.6905 | 0.3165 | 1.6548 | 1.162747 | 3.0493 |
| cuda | svd_lowrank | 1 | 2.0846 | 0.5168 | 2.0478 | 1.005561 | 3.0493 |
| cuda | dense_svd | None | 9.2421 | 1.1611 | 9.1836 | 0.999998 | 3.3145 |

In the 20 completed GPU SPI configurations, preplanned native svd_lowrank niter=1 had both smaller median wall time and no worse Frobenius ratio in 20/20 paired cases. This scoped observation is not an arithmetic-equivalence or general algorithm claim. Full matched-quality sets (tiers 1.10/1.50) and Pareto comparisons are retained, including adverse outcomes.

NOT RUN: full-grid completion; 1024x512 near-flat float64 and 2048x1024 both dtypes; warm trials for 1024x512 near-flat float32; full GPU pytest in this cycle; complex performance, kernel-only timing, compile, TPU, sparse-sign performance and streaming.

Raw artifact m8-report.json is byte-identical to the downloaded transport payload. Its zlib/base64 benchmark decodes to exact results.json bytes; decoded CSV/summary/benchmark manifest match remote hashes. Full command logs/exceptions and all adverse rows remain. colab-control.json/controller stdout redact only the account balance. No raw usage payload or credentials are published. CPU report is a fresh noneditable install with system dependency reuse: 540 passed / 46 CUDA skipped; 18 new M8 tests.

Limits: one independent matrix/sketch seed and one T4 session; three repeats do not establish replicates. CPU covers only the smallest geometric dtype pair; events are not kernel-only; first measured calls followed correctness/reference work; initial clock snapshot does not quantify thermal/clock variability. Actual A tensors are not archived, but seeds, serialization hashes, full reference/residual spectra and direct residual Frobenius checks are.

Next: Chief Architect independently reviews the reference-precision failure, partial coverage, raw timings/memory, provenance and cleanup before deciding the next bounded experiment. No automatic second allocation or self-merge.
