# M7 CUDA correctness: bounded run procedure

**Status: GPU correctness is BLOCKED / NOT RUN.** The Engineer's runtime had no authorized CUDA environment (no NVIDIA GPU, torch `+cpu`, no Colab CLI), so nothing here has run on a GPU. This directory contains the oracles and a single self-contained entry point so that someone with a CUDA device can produce the evidence for one fixed commit. A CPU run (`--device cpu`) only checks the oracle logic and is labelled `DRY_RUN_CPU`; it is never GPU evidence.

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

Interpretation: `status: PASS` with `gpu_evidence: true` means every oracle row passed on that device. Any `FAIL` or `BLOCKED` row is a finding to report as is; do not rerun to hide it. In the pytest log the GPU tests must show as passed, not skipped: `skipped` means CUDA was not visible. This run is `PROBE_ONLY` until the Architect independently reviews it.

## Local CPU dry run

```bash
python experiments/m7_cuda/run_m7_cuda.py --device cpu --out out_m7_dry --quick     # logic only, status DRY_RUN_CPU
python experiments/m7_cuda/run_m7_cuda.py --device cuda --out out_m7_blocked          # without CUDA: status BLOCKED, exit code 2
```
