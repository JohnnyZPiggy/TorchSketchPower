# Documentation

**Current project state:** [Research closeout (October 2026)](RESEARCH_CLOSEOUT.md) — M7–M11 outcomes, negative results, exact evidence links, scientific limitations and paused M12. Previous GPU-readiness and release-checklist documents are historical plans, not current status assertions.

Start with the [project README](../README.md) (scope, install, example, API, limitations).

| Document | Read it for |
|---|---|
| [math.md](math.md) | What is computed, in which dimensions, under which assumptions: M0 power kernel and rank loss, M1 sketches, M2 least squares with complex adjoints, M3 pipeline, and the M5 error identities including the signed cross term |
| [cpu-results.md](cpu-results.md) | The M4 (accuracy, cost) and M5 (error decomposition) CPU results, summarized from the committed raw data, with caveats and what they do not show |
| [gpu-readiness.md](gpu-readiness.md) | M6 GPU readiness audit (design) and the M7 status update: per-function CUDA constraints, hazards with oracles, solver decision record, oracle plan, gates M7 to M10; the M7 CUDA path is a candidate never run on a GPU |
| [research/spi-tensorization.md](research/spi-tensorization.md) | Original research note for the subspace kernel: paper context, dimension inconsistency in the paper's *Require* line, Eq. (2.6) argument, rank-deficiency contract (unchanged by the V1 documentation work) |
| [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) | Gated plan for a V1 reference tag: current tag inventory, open decisions, review gates; no tag or release has been created |

Raw data and generators:

- [`reports/m4_cpu/`](../reports/m4_cpu/README.md) and [`reports/m5_cpu/`](../reports/m5_cpu/README.md): CSV/JSON rows, generated summaries and manifests with SHA-256 hashes.
- [`experiments/m4_cpu/`](../experiments/m4_cpu/run_m4.py) and [`experiments/m5_cpu/`](../experiments/m5_cpu/run_m5.py): the runners that produced them.
- [`tests/`](../tests/): unit and regression tests (493 passed and 46 CUDA-only tests skipped on the tested CPU environment).

Project process (not part of the algorithm): [`AGENTS.md`](../AGENTS.md), [`sae.yaml`](../sae.yaml) and the pinned framework snapshot in [`.sae/`](../.sae/AGENTS.md).
