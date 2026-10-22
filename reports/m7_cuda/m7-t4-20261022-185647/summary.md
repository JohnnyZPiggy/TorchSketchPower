# M7: one real T4 correctness run

Tested source: `645777724845207fbb882329c086f59dc5da8b04`. SAE tool pin: `65338eb1aa67971e110db982a07cf43161c23446`.

Engineer-observed **PROBE_ONLY single-T4 correctness PASS with exclusions**, pending independent Architect acceptance. Issue #18 / Draft PR #19. One allocation, no retry.

- Actual Tesla T4, Python 3.13.15, PyTorch 2.11.0+cu130, CUDA build 13.0; float32/float64/complex64/complex128. TF32 disabled; CUDA least-squares driver gels after rank gates.
- Full 172 oracle rows retained: 171 PASS, 1 NOT_RUN (mixed CUDA indices requires a second GPU); no FAIL or BLOCKED, no time-limit row.
- CUDA test file: 98 passed, 1 skipped in 3.89s. The skip is the CPU-only no-CUDA-request test; all 46 CUDA-only tests actually executed.
- Transport PASS; downloaded scientific JSON byte count and SHA256 match remote ARTIFACT marker. Exact source identity and clean checkout recorded.
- Stop exit 0, followed by strict fresh AUTHENTICATED_ZERO. Cleanup verified 2026-10-22 16:57:29 UTC. Allocation lifecycle approximately 33 seconds; controller task 900s / allocation 300s / cleanup reserve 60s / work flag 420s, further capped by remaining allocation budget.

The manifest hashes every retained artifact. `m7-cuda-report.json` is the unchanged downloaded raw scientific report. `colab-control.json` and controller stdout have the account balance redacted. Raw usage output is not retained. The single combined artifact retains all oracle rows and metadata, but runner stdout/stderr and pytest stdout are only bounded tails, not complete logs. No separate remote results.json/manifest/summary or complete pytest log was downloaded by this committed adapter.

This is source-path execution via PYTHONPATH, not final non-editable package validation. The known timeout/incomplete-plan false-PASS path remains a source issue; this run did not hit it. Single-GPU exclusions, source installation requirement and those status semantics remain for Architect review. No speedup, compile, batching, streaming, TPU or validated sparse-sign CUDA claim. PR stays Draft; Engineer never merges.
