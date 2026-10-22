# reports/m5_cpu - M5 CPU numerical diagnostics outputs (Issue #12)

Raw, generated outputs of `experiments/m5_cpu/run_m5.py` (EXPLORE, CPU only). Nothing here was edited by hand.

- `samples.csv` / `samples.json` - one row per diagnostic case (65): 45 baseline rows that replay the M4 `A_q` ids and seeds, 14 controlled-Psi rows (A and Q fixed), 6 tiny oracle / negative-control rows (2 expected `RankDeficiencyError` rows, 1 `IllConditionedWarning` row).
- `summary.md` - tables computed from the CSV (identity checks, error terms by stage, controlled Psi variation, oracle and failure tables).
- `manifest.json` - environment, invocation, source SHA (`096cce0bb78974d0aeff53c723c1cf10cbd71519`, clean tree), SHA-256 of the committed M4 reference file and of every output file, definitions and tolerances.

Reproduce (clean checkout of the source SHA, non-editable install): `python experiments/m5_cpu/run_m5.py --out <dir>`. Outputs are deterministic in a given environment.

Notes: the raw absolute identity residuals in the first table are dominated by the deliberately ill-conditioned oracle row (terms of size ~1e15); the row labelled relative to the largest term is the meaningful number. Limits: in-memory only; Gaussian only; no timing; GPU/TPU/torch.compile/streaming NOT RUN; paper Algorithm 2.1 equivalence UNVERIFIED.
