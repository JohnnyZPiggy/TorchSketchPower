# M10 CPU-only cost/DAG audit

Tested source `cd870297436d8a3ebca7064a702761fe2d1ded30`; starting main `345ee660bd1baed2c7a9c5ae7c58ec45f6feff93`; fixed SAE `65338eb1aa67971e110db982a07cf43161c23446`. Issue #24. Independent GPT T2 pending; Engineer has not merged.

236 scoped CPU tests PASS in the existing CPU environment, no installation changes. Normalized installed production text matches pinned source. Raw observation identity verified, including hashes of the five full M7/M8/M9 evidence files. No original source/evidence changes.

H1:8float32/64/complex64/128 steps0/1 cases pass fixed-oracle reconstruction and RNG replay; maximum reconstruction delta 0. All8final generator states agree. The naive single-wide-random-call variant differs in 8/8cases; rejected. Output Y/Z views are noncontiguous. Current small-case bitwise observations do not prove universal BLAS bit identity or rank-threshold/exception equivalence. CONDITIONAL; PROCEED only to independent CPU/API review.

H2:32zero/exact/near-rank-threshold cases pass the same rank decisions. CPU original rank gate3ATen scalar extractions vs prototype2, of which svdvals alone already has1. Whole original pipeline t0/t1 has11/14 events versus source-only modeled6/8consumers. This is not a CUDA barrier-count/latency measurement. Prototype may introduce scalar allocation/H2D copy and pointwise overhead, with nonfinite/promotion/extreme/CUDA behavior unverified. CONDITIONAL; DEFER production/performance work.

Preserved negative results: independent left sketch W is not generally recoverable from Y/Z (explicit nullspace perturbations change W while retaining Y/Z numerically); all4dtype normal-equation Gram solves fail on full-rank ill-conditioned C while checked gelsd warns/succeeds; skew Q changes B-versus-QB singular values and existing orthogonality gate rejects it. These are counterexamples, not proposed new algorithms.

The English research README contains the dependency DAG, explicit real FLOP conventions, per-stage QR/SVD/lstsq models, tensor footprints/RNG/pass distinctions, scalar gate/error ordering, classical roofline limitations and exactly two ranked hypotheses. The87,818,240GEMM subtotal for the1024x512/r8/s16/ell32/d32/t1 example excludes QR/SVD/solve/reduction work; explicit-Q QR model2,113,536FLOPs is not exact vendor work. Unknown GPU stage timings/traffic/throughput remain unknown.

Historical observations reused, never rerun: first M8 native advantage20/20completed SPI pairs; second26/26, overlapping cases not46independent observations. Both historical configured FAIL records stay immutable, including second75/80complete coverage. M9 three Inductor pairs remain negative scoped timings, public graph breaks intact. M7 original provenance/log limitations remain visible. No causal percentage for stage bottlenecks or future speedup is asserted.

NOT RUN: any GPU/Colab CLI call, new performance experiment, physical GPU traffic/sync timing, generalized threshold semantics, all-input API proof. No new session/cleanup claim. Next: GPT Chief Architect independently reviews the mathematical model, counterexamples and ranked hypotheses in the unique Issue#24 PR before deciding a separate future task. No production refactor is authorized by this report.
