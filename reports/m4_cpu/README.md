# reports/m4_cpu - M4 CPU validation outputs (Issue #10)

Raw, generated outputs of `experiments/m4_cpu/run_m4.py` (EXPLORE, CPU only). Nothing here was edited by hand.

- `samples.csv` / `samples.json` - one row per algorithm sample (110), including recorded failures (5 expected `RankDeficiencyError` rows).
- `timings.csv` - per-repeat wall times (cold, warm, full-SVD baseline) from one fresh process per configuration.
- `memory.csv` - OS process working-set high-water marks and buffer-size ESTIMATES (estimates are not measurements).
- `summary.md` - tables computed from the CSVs.
- `manifest.json` - environment, thread settings, invocation, source SHA (`36e94999b7cf6f64d6437d0c2179fe1eb762386e`, clean tree), file SHA-256 hashes.

Reproduce (from a clean checkout of the source SHA, non-editable install): `python experiments/m4_cpu/run_m4.py --out <dir>`. `samples.*` are deterministic in a given environment; timings and memory are not.

Limits: in-memory only, not one-pass or streaming; Gaussian only (`sparsesign` NOT RUN); float32 rows use their own RNG stream (no matched float32/float64 draws); timings are sub-2 ms single-machine measurements and support no speed claim; GPU/TPU/torch.compile NOT RUN; paper Algorithm 2.1 equivalence UNVERIFIED.
