# TorchSketchPower — research closeout (October 2026)

**Lifecycle:** paused / archival research snapshot. **No release or tag; no further M12 experiment was executed.** This page supersedes historical progress statuses retained in older issue/report descriptions. No new CPU or GPU test was run for this closeout; counts below originate from archived Engineer logs and previously reviewed artifacts.

## Scope and math

Given resident dense `A`, draw `Omega`, `Phi`, `Psi` sequentially and form `Y=A@Omega`, `Z=A@Phi`, `W=Psi@A`. A checked subspace `Q` is refined by QR-stabilized steps using `Z@Z.H`, then a checked least-squares solve and SVD yield rank-r factors. The code is **not** a verified one-pass streaming method or a reproduction of the paper's complete Algorithm 2.1. Numerical-rank/conditioning and seed-dependent failure behavior are part of the public checked contract.

## What was learned

| Work | Archived evidence | Interpretation / limitations |
|---|---|---|
| M4–M5 CPU studies | [CPU results](cpu-results.md) | Synthetic reconstruction and error decomposition; finite-grid numerical tests, not universal rates |
| M7 CUDA numerical gate | [M7 raw experiment](../reports/m7_cuda/m7-t4-20261022-185647/m7-cuda-report.json) | Real T4, 171 oracle PASS / one second-device-only NOT RUN; one tested environment/source, not universal GPU validation |
| M8 low-rank comparisons | [First T4 review](../reports/m8_gpu/m8-t4-20261022-193439/review.md), [second T4 review](../reports/m8_gpu/m8-ref-t4-20261022-195451/review.md), [float64 CPU audit](../experiments/m8_gpu/FLOAT64_AUDIT.md) | Second run 75 of 80 configs warm-complete, 380 trials; float32 precision reference corrected, later float64 dense-SVD strict audit FAIL scientifically unresolved. Observed native comparisons favored `torch.svd_lowrank(niter=1)` in the measured paired subset. Do not generalize or call it full-grid PASS |
| M9 `torch.compile` | [T4 review](../reports/m9_compile/m9-t4-20261022-204314/review.md) | Some helper graphs supported; checked public pipeline graph breaks; all three measured T4 Inductor pairs slower warm than eager; first compile+run roughly 4–8 seconds |
| M10 mathematical cost model | [Derivation](../experiments/m10_cost/README.md), [raw](../reports/m10_cost/m10-20261022-210437/observations.json) | 236 Engineer-reported scoped CPU tests PASS; leading FLOP and memory models are not GPU stage timing. H1 concat GEMM conditional before M11; H2 scalar-threshold optimization deferred |
| M11 semantic counterexample | [CPU review](../reports/m11_concat/m11-20261022-214747/review.md), [replay](../reports/m11_concat/m11-20261022-214747/counterexample-replay.json) | 140 full-pipeline cases, 17 NOT_EQUIVALENT: rank-threshold branch and final RNG state can change after concatenating otherwise independent Gaussian sketches. H1 unrestricted substitution **REJECTED**; no GPU run |
| M12 proposed spectral study | [Issue #28](https://github.com/JohnnyZPiggy/TorchSketchPower/issues/28) | **Not run**, intentionally deferred on closeout; no phase-diagram results exist |

Each run has its own **tested source SHA**, report hash and device/runtime record. Main branch's later squash-merge SHA is *not* automatically the exact tested benchmark code SHA. Original adverse rows, caveats, timing/memory definitions, and hashes must be read in their source reports.

## Reproduction and code

- [Root README](../README.md) — install, Python API, minimal example and historical milestones.
- [Mathematics](math.md) — dimensions, rank contracts, error identities.
- [GPU readiness](gpu-readiness.md) — **historical pre-M7 audit**; later real T4 result supersedes its old “not run” status.
- [Experiments](../experiments/) and [raw reports](../reports/) — immutable scientific provenance.
- SAE governance remains pinned in [`sae.yaml`](../sae.yaml) and [`.sae/`](../.sae/) at `65338eb1aa67971e110db982a07cf43161c23446`.

**Do not infer** a reproducible GPU speedup, production-safe `torch.compile` support, full one-pass equivalence, validated TPU support, or all-input numerical correctness from these bounded experiments. Tests and scientific outcomes have separate verdicts. No license file is included at this snapshot; a license choice and independent release audit would be needed before a public distribution.

## Resume only if research priorities change

The most worthwhile unexecuted direction is the [M12 spectral error phase diagram](https://github.com/JohnnyZPiggy/TorchSketchPower/issues/28): evaluate accuracy by spectral family, subspace angle and fixed logical sketch budget. This is **future work, not promised work**. No automated workflow, GPU resources or background jobs are attached to the paused project.
