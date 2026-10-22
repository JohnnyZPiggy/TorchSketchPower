# M7 CUDA correctness: bounded run procedure

**Status: no GPU result is recorded in this file.** The Windows runtime has no CUDA, but the Engineer can reach the Colab CLI 0.7.4 from WSL (login shell) through the SAE compute controller; evidence of any controller-managed run is posted in Issue #18, not here. An earlier note that no Colab CLI was available was wrong (wrong shell context) and is superseded. This directory contains the oracles and a single self-contained entry point so that someone with a CUDA device can produce the evidence for one fixed commit. A CPU run (`--device cpu`) only checks the oracle logic and is labelled `DRY_RUN_CPU`; it is never GPU evidence.

Correctness only: no timing, no benchmark, no speed claim. One bounded session (a free or already-entitled T4 is enough), nothing to purchase, no credentials, no GitHub writes.

## What it does

`run_m7_cuda.py` runs the oracles O1 to O6 of [docs/gpu-readiness.md](../../docs/gpu-readiness.md) through the production API on the device:

- O1/O2/O3: the corange coefficient (CUDA `gels` after the rank gate) against an SVD-pseudoinverse computed on the device and against a CPU float64 SVD-pseudoinverse of the *transferred identical* `C`, `W`; the normal-equation residual; singular values and the rank-r reconstruction. float32, float64, complex64, complex128; tall, square, wide; `d = s` and `d > s`; condition numbers up to the gate.
- O4: end to end. Mode A: sketches drawn on the CPU and transferred (device result compared with the CPU float64 pipeline on the same sketches). Mode B: device-local draws; only invariants (both M5 squared-error identities, Eckart-Young bound, orthonormality, finiteness, replay equality), at least five seeds for real dtypes.
- O5: negative controls (rank(A) < s, exactly and nearly rank-deficient `C`, ill-conditioned warning, non-orthonormal `Q`, dtype mismatch, mixed CPU/CUDA tensors, CPU generator with CUDA input, `sparsesign` on CUDA, `d < s`, invalid `r`, unsupported device type).
- O6: a spy counts `.cpu()`, `.numpy()`, `.tolist()` and `.to(cpu)` during every production call (must be zero); scalar reads for the rank gates are expected and are a device synchronization.

Tolerances are pre-registered in `m7lib.py` from backward-error arguments, not tuned. Every row stores the observed error, the tolerance and their ratio. A dtype or driver that CUDA does not support is recorded as `BLOCKED` with the error text, never omitted. `sparsesign` on CUDA is rejected by the API and reported as such.

## Colab procedure (fixed commit, one T4 session)

Replace `<SHA>` with the exact 40-character commit given in the Issue #18 comment (the PR head being tested).

1. Open a new Colab notebook. `Runtime > Change runtime type > T4 GPU`. Do not enable any paid option.
2. Cell 1 (environment and exact source):

```bash
%%bash
set -euo pipefail
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
SHA=<SHA>
git clone -q https://github.com/JohnnyZPiggy/TorchSketchPower.git /content/repo
cd /content/repo
git checkout -q "$SHA"
test "$(git rev-parse HEAD)" = "$SHA"
test -z "$(git status --short)"
python -m pip -q install --no-deps /content/repo pytest
```

3. Cell 2 (the bounded run; correctness only):

```bash
%%bash
cd /content/repo
SHA=<SHA>
timeout 900 python experiments/m7_cuda/run_m7_cuda.py --device cuda --out /content/m7_out --source-sha "$SHA" --max-seconds 800 | tee /content/m7_run.log
timeout 900 python -m pytest -q -rs -p no:cacheprovider 2>&1 | tee /content/m7_pytest.log
```

4. Cell 3 (evidence to attach):

```bash
%%bash
cd /content
sha256sum m7_out/results.json m7_out/summary.md m7_out/manifest.json m7_run.log m7_pytest.log
head -40 m7_out/summary.md
python - <<'PY'
import json
r = json.load(open("/content/m7_out/results.json"))
print(r["status"], r["counts"], r["gpu_evidence"], r["environment"].get("gpu_name"), r["source_sha_verified"])
PY
```

5. Download `results.json`, `summary.md`, `manifest.json` and the two logs (or paste cell outputs) and attach them to Issue #18.
6. Cleanup: `Runtime > Disconnect and delete runtime`, then confirm in `Manage sessions` that no session remains, and state that in the Issue.

Interpretation: scientific `PASS` requires a complete plan with every applicable row passing. Timeout, missing required results or unexpected `NOT_RUN` produce `BLOCKED` (exit 2); observed failures produce `FAIL` (exit 1), including in CPU dry runs. The only CUDA `NOT_RUN` exemption is mixed CUDA indices on a single GPU, with the explicit hardware reason retained. CPU dry runs retain the four CUDA-only negative-control exclusions. `plan_complete`, `planned_jobs` and `completed_jobs` disclose coverage; all returned rows are preserved. GPU-only pytest cases must actually execute; the no-CUDA-only negative test may legitimately skip on CUDA. Runs remain `PROBE_ONLY` until independently reviewed.

## Local CPU dry run

```bash
python experiments/m7_cuda/run_m7_cuda.py --device cpu --out out_m7_dry --quick     # logic only, status DRY_RUN_CPU
python experiments/m7_cuda/run_m7_cuda.py --device cuda --out out_m7_blocked          # without CUDA: status BLOCKED, exit code 2
```

## Controller-managed run (SAE Compute Adapter, one bounded T4 session)

`colab_driver.py` and `artifacts.json` are the project adapter for the pinned SAE controller (`tools/compute/colab_control.py`, SAE-Framework `65338eb1aa67971e110db982a07cf43161c23446`, Colab CLI 0.7.4). The controller reads both as Git blobs at `--source-sha`, stages the driver alone on the Colab VM and passes the commit in `SAE_CANDIDATE_SHA`. The driver clones that exact commit, performs a non-editable `pip install --no-deps --no-build-isolation --no-cache-dir --force-reinstall .`, and verifies an isolated import against distribution-owned files and the exact checkout's Python source bytes. It records package path, distribution version, non-editable status, source SHA and file hashes in `installed_package`; installation or identity failure stops before the oracles. Runner and pytest use `python -I` with no source PYTHONPATH. The driver writes one artifact, `m7-cuda-report.json`; outer `status` remains transport-only, and `m7_oracle_status` plus the full rows/tests carry the independent scientific verdict. From the WSL login shell that has `colab`:

```sh
python3 <SAE>/tools/compute/colab_control.py --preflight-only --cli colab --repo-path <clone> --source-sha <SHA> --run-id <id> --out <new-dir>
python3 <SAE>/tools/compute/colab_control.py --cli colab --repo-path <clone> --source-sha <SHA> \
  --driver experiments/m7_cuda/colab_driver.py --artifacts experiments/m7_cuda/artifacts.json \
  --device T4 --run-id <id2> --out <new-dir2> --task-seconds 900 --allocation-seconds 600 --cleanup-seconds 60 --work-timeout 420
```
