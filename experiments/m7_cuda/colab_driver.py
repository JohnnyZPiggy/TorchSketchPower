"""Self-contained remote driver for the SAE Colab controller: M7 CUDA correctness (PROBE_ONLY).

Staged alone on the Colab VM by ``tools/compute/colab_control.py --driver``; it receives the exact
source commit in ``SAE_CANDIDATE_SHA``. It clones the repository at that commit, runs the M7 oracle
runner and the CUDA test file on the GPU, and writes ONE artifact, ``m7-cuda-report.json``, then prints
the controller's ``ARTIFACT <name> <bytes> <sha256>`` line. No GitHub writes, no credentials, standard
library only.

``status`` in the artifact is the controller's transport status: ``PASS`` means "the driver ran to
completion on a CUDA device and produced a parseable report". It is NOT the numerical verdict, which is
``m7_oracle_status`` (PASS/FAIL/BLOCKED) inside the same file, and nothing here is accepted as GPU
correctness until the Architect reviews it. ``FAIL`` marks a run that never reached the GPU oracles.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

NAME = "m7-cuda-report.json"
SHA = os.environ.get("SAE_CANDIDATE_SHA", "")
DRY_RUN = os.environ.get("M7_DRIVER_DRY_RUN") == "1"  # local logic check on a CPU machine; never used by the controller
WORK = os.environ.get("M7_WORKDIR", "/content")
REPO_URL = os.environ.get("M7_REPO_URL", "https://github.com/JohnnyZPiggy/TorchSketchPower.git")
MAX_ARTIFACT_BYTES = 900_000


def sh(cmd, timeout, cwd=None, env=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd, env=env)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -9, "", "TIMEOUT"
    except OSError as exc:
        return -1, "", f"OSError: {exc}"


def tail(text, n=1500):
    return text[-n:] if text else ""


def parse_pytest_summary(text):
    """Counts from the final pytest line, e.g. '46 passed, 3 skipped, 1 warning in 12.3s'."""
    last = [ln for ln in text.strip().splitlines() if re.search(r"\b(passed|failed|skipped|error|errors)\b", ln) and " in " in ln]
    counts = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0}
    if not last:
        return None
    for num, word in re.findall(r"(\d+) (passed|failed|skipped|errors?)", last[-1]):
        counts["errors" if word.startswith("error") else word] = int(num)
    return counts


def decide_status(dry_run, cuda_available, results):
    """Transport status of the artifact (see module docstring); never an oracle verdict."""
    if dry_run:
        return "DRY_RUN_CPU"
    if cuda_available and isinstance(results, dict) and results.get("gpu_evidence") is True:
        return "PASS"
    return "FAIL"


def main():
    t0 = time.time()
    report = {"source_sha": SHA, "tool": "m7-colab-driver-1", "status": "FAIL", "stage": "start", "reason": None,
              "m7_oracle_status": None, "classification": "PROBE_ONLY", "dry_run": DRY_RUN,
              "status_meaning": "PASS = the driver completed on a CUDA device and produced a parseable report; "
                                "the numerical verdict is m7_oracle_status; not accepted until Architect review",
              "not_run": ["performance", "speedup", "torch.compile", "batching", "sparsesign on CUDA", "TPU"]}
    try:
        if not re.fullmatch(r"[0-9a-f]{40}", SHA):
            report["reason"] = "INVALID_SOURCE_SHA"
            raise RuntimeError("stop")
        repo, out = os.path.join(WORK, "repo"), os.path.join(WORK, "m7_out")
        shutil.rmtree(repo, ignore_errors=True)
        shutil.rmtree(out, ignore_errors=True)
        report["stage"] = "clone"
        code, _, err = sh(["git", "clone", "--quiet", REPO_URL, repo], 120)
        if code:
            report["reason"] = "CLONE_FAILED: " + tail(err, 200)
            raise RuntimeError("stop")
        code, _, err = sh(["git", "checkout", "--quiet", SHA], 60, cwd=repo)
        head = sh(["git", "rev-parse", "HEAD"], 30, cwd=repo)[1].strip()
        dirty = bool(sh(["git", "status", "--porcelain"], 30, cwd=repo)[1].strip())
        report.update(verified_head=head, head_matches=(head == SHA), working_tree_dirty=dirty)
        if code or head != SHA or dirty:
            report["reason"] = "SOURCE_NOT_EXACT"
            raise RuntimeError("stop")
        env = dict(os.environ, PYTHONPATH=os.path.join(repo, "src"), PYTHONDONTWRITEBYTECODE="1")
        device = "cpu" if DRY_RUN else "cuda"
        report["stage"] = "oracles"
        code, so, se = sh([sys.executable, "experiments/m7_cuda/run_m7_cuda.py", "--device", device, "--out", out,
                           "--source-sha", SHA, "--max-seconds", "200"], 260, cwd=repo, env=env)
        report["runner"] = {"exit_code": code, "stdout_tail": tail(so, 600), "stderr_tail": tail(se, 600)}
        results = None
        rpath = os.path.join(out, "results.json")
        if os.path.exists(rpath) and os.path.getsize(rpath) <= MAX_ARTIFACT_BYTES:
            results = json.load(open(rpath, encoding="utf-8"))
        report["results"] = results
        if results is not None:
            report["m7_oracle_status"] = results.get("status")
        report["stage"] = "pytest"
        pt = {"status": "NOT_RUN", "reason": None}
        code, _, _ = sh([sys.executable, "-c", "import pytest"], 30, cwd=repo, env=env)
        if code:
            sh([sys.executable, "-m", "pip", "install", "-q", "pytest"], 90, cwd=repo, env=env)
        code, so, se = sh([sys.executable, "-m", "pytest", "-q", "-rs", "-p", "no:cacheprovider", "tests/test_cuda_lowrank.py"],
                          120, cwd=repo, env=env)
        counts = parse_pytest_summary(so + "\n" + se)
        pt = {"exit_code": code, "counts": counts, "stdout_tail": tail(so, 1200),
              "status": "NOT_RUN" if counts is None else ("PASS" if code == 0 and counts["failed"] == 0 and counts["errors"] == 0 else "FAIL")}
        report["pytest_cuda_file"] = pt
        cuda_available = bool(results and results.get("environment", {}).get("cuda_available"))
        report["status"] = decide_status(DRY_RUN, cuda_available, results)
        if report["status"] == "FAIL":
            report["reason"] = "NO_CUDA_EVIDENCE: runner did not report a CUDA device"
        report["stage"] = "done"
    except RuntimeError:
        pass
    except Exception as exc:  # recorded; the artifact is still written
        report["reason"] = f"{type(exc).__name__}: {str(exc)[:200]}"
    report["wall_seconds"] = round(time.time() - t0, 1)
    raw = json.dumps(report, indent=1).encode("utf-8")
    if len(raw) > MAX_ARTIFACT_BYTES:  # keep only failing rows if the full row list is too large
        res = report.get("results") or {}
        res["rows"] = [r for r in res.get("rows", []) if r.get("status") != "PASS"]
        res["rows_truncated_to_non_pass"] = True
        report["results"] = res
        raw = json.dumps(report, indent=1).encode("utf-8")
    path = os.path.join(WORK, NAME)
    with open(path, "wb") as f:
        f.write(raw)
    print(f"ARTIFACT {NAME} {len(raw)} {hashlib.sha256(raw).hexdigest()}", flush=True)


if __name__ == "__main__":
    main()
