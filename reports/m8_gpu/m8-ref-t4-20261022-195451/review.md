# M8 reference correction: one bounded T4 completion attempt

Status **BLOCKED**. Tested source `116d6c299b3b84a3477363c2529f6efd37972055`; fixed SAE `65338eb1aa67971e110db982a07cf43161c23446`; Issue #20 / Draft PR #21.

Coverage 75/80 complete (65 GPU, 10 CPU), 380 calls; 0 runtime failures; 0 timed warnings. Accuracy FAIL configs: ['m13-cuda-4']; NOT RUN configs: []. Full errors/statuses retained in results.json and m8-report.json.

Fresh noneditable installed-package verification PASS; short M7 CUDA gate PASS, counts {'PASS': 39, 'NOT_RUN': 1}. Actual device/runtime: Tesla T4, torch 2.11.0+cu130, CUDA 13.0.

One allocation only; no automatic retry. Stop and strict fresh AUTHENTICATED_ZERO cleanup confirmed. Final controller readback: {"phase": "cleanup", "method": "CLI_074_AUTHENTICATED_CCU_INFO", "status": "AUTHENTICATED_ZERO", "assignments": 0}

CPU prerequisite: clean exact source, fresh venv using existing system CPU dependencies, noneditable installation, 544 PASS / 46 CUDA SKIP; 22 M8 targeted tests PASS. Offline driver smoke and artifact/canonical hashes PASS. Reproduction commands and CPU reference values are in diagnostic-comment.md; diagnose_exact.py writes the exact serialized generated A and diagnostics. diagnostic-actual-a.pt matches diagnostic-decision.json SHA256. CPU vs historical serialized hashes differ; no cross-runtime bit identity asserted.

All methods use the same float64 SVD of the actual dtype-rounded A per device. Native float32 reference is non-authoritative only. Reference work occurs outside method timing/allocator windows. Energy subtraction has cancellation guard and is diagnostic only. Original runner thresholds, algorithms, parameter grid and timings unchanged. The original failed T4 run m8-t4-20261022-193439 remains immutable and historically BLOCKED.

Offending-case retest m10-cuda-4: PASS; authoritative Fro ratio 1.000000000948626. See review.json for complete reference metadata/native alternative and results.json for every raw spectrum and timing.

Raw m8-report.json is byte-identical to downloaded transport; compressed benchmark decodes to exact results.json bytes. benchmark-manifest.json hashes decoded JSON/CSV/summary; publication-manifest.json hashes published files. Account balance is redacted in controller evidence; no credentials/raw usage text published.

NOT RUN: full GPU pytest this cycle, independent seed/session replications, complex performance, kernel-only timing, compile, TPU, sparse-sign performance, streaming. CPU timing is only smallest geometric dtype pair. Three warm repeats share seeds, not independent science replicates. Event timing includes default-stream idle; memory is allocator peak/delta, not device-wide/per-call true allocation. Initial clocks/temperature snapshot only. No speedup claim or post-hoc parameter tuning.

Next: GPT Chief Architect independently reviews the reference correction, all numerical/performance rows and cleanup. PR stays Draft; Engineer has not merged.

New failure: m13-cuda-4, (2048,1024) geometric float64 dense SVD. Fro ratio 0.9999999999998166 < unchanged EY minimum 0.999999999999889 (500 eps64). Finite true; residual Fro/SVD audit 3.580601652522215e-13. This tiny numerical mismatch is not an algorithm/EY theorem violation, but the configured gate really FAILS. No threshold changed. Last matrix has five cold results only (four PASS, one FAIL): all five warmups and 15 warm calls are **NOT RUN**, 20 unrun calls total. Thus zero NOT_RUN configuration statuses must not be read as complete timing coverage. No second allocation. Further tolerance/reference numerical analysis is for independent Architect review.

Old-case reference comparison: {"same_torch_save_sha256": true, "new_serialized_sha256": "7f66b46e3128085ed25cafcc8c4b7fcf4db48a55bb26855ceb26fdb07389f085", "historical_serialized_sha256": "7f66b46e3128085ed25cafcc8c4b7fcf4db48a55bb26855ceb26fdb07389f085", "native_opt_fro": 21.88387097254383, "double_opt_fro": 21.882243080035973, "independent_energy_opt_fro": 21.882243080034065, "native_relative_bias": 7.439331068126442e-05}

reference-fix.diff contains the complete minimal code/test/doc diff from the prior evidence head to tested source. No changes to production src, SAE, driver, CLI, grid, tiers or timing.
