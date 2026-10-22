# Documentation

Start with the [project README](../README.md) (scope, install, example, API, limitations).

| Document | Read it for |
|---|---|
| [math.md](math.md) | What is computed, in which dimensions, under which assumptions: M0 power kernel and rank loss, M1 sketches, M2 least squares with complex adjoints, M3 pipeline, and the M5 error identities including the signed cross term |
| [cpu-results.md](cpu-results.md) | The M4 (accuracy, cost) and M5 (error decomposition) CPU results, summarized from the committed raw data, with caveats and what they do not show |
| [research/spi-tensorization.md](research/spi-tensorization.md) | Original research note for the subspace kernel: paper context, dimension inconsistency in the paper's *Require* line, Eq. (2.6) argument, rank-deficiency contract (unchanged by the V1 documentation work) |
| [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) | Gated plan for a V1 reference tag: current tag inventory, open decisions, review gates; no tag or release has been created |

Raw data and generators:

- [`reports/m4_cpu/`](../reports/m4_cpu/README.md) and [`reports/m5_cpu/`](../reports/m5_cpu/README.md): CSV/JSON rows, generated summaries and manifests with SHA-256 hashes.
- [`experiments/m4_cpu/`](../experiments/m4_cpu/run_m4.py) and [`experiments/m5_cpu/`](../experiments/m5_cpu/run_m5.py): the runners that produced them.
- [`tests/`](../tests/): unit and regression tests (444 on the tested environment).

Project process (not part of the algorithm): [`AGENTS.md`](../AGENTS.md), [`sae.yaml`](../sae.yaml) and the pinned framework snapshot in [`.sae/`](../.sae/AGENTS.md).
