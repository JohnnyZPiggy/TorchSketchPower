"""Self-contained M9 bootstrap using the existing M7 installed-package helper and SAE transport."""
import hashlib
import base64
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import traceback
import zlib

NAME = "m9-report.json"
SHA = os.environ.get("SAE_CANDIDATE_SHA", "")
WORK = Path(os.environ.get("M9_WORKDIR", "/content"))
DRY_RUN = os.environ.get("M9_DRIVER_DRY_RUN") == "1"
REPO_URL = os.environ.get("M9_REPO_URL", "https://github.com/JohnnyZPiggy/TorchSketchPower.git")


def main():
    report = {"source_sha": SHA, "status": "PASS", "status_meaning": "transported report, NOT scientific acceptance",
              "benchmark_status": "BLOCKED", "stage": "bootstrap", "logs": [], "exceptions": []}
    def sh(args, timeout, cwd=None, env=None):
        try:
            p = subprocess.run(args, timeout=timeout, cwd=cwd, env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL)
            code, so, se = p.returncode, p.stdout, p.stderr
        except subprocess.TimeoutExpired as exc:
            code, so, se = -9, exc.stdout or b"", exc.stderr or b""
            so = so.decode(errors="replace") if isinstance(so, bytes) else so
            se = se.decode(errors="replace") if isinstance(se, bytes) else se
            se += "\n" + traceback.format_exc()
        report["logs"].append({"operation":args[1:4],"exit_code":code,"timeout":timeout,"stdout":so,"stderr":se})
        return code, so, se
    def required(args, timeout, cwd=None, env=None):
        code, so, se = sh(args, timeout, cwd, env)
        if code:raise RuntimeError("bounded command failed; full output retained in logs")
        return so
    try:
        if not re.fullmatch(r"[0-9a-f]{40}", SHA):raise ValueError("invalid source SHA")
        repo = WORK / "m9_repo"
        required(["git", "clone", "--quiet", REPO_URL, str(repo)], 60)
        required(["git", "checkout", "--quiet", SHA], 30, repo)
        head = required(["git", "rev-parse", "HEAD"], 15, repo).strip()
        dirty = bool(required(["git", "status", "--porcelain"], 15, repo).strip())
        if head != SHA or dirty:raise ValueError("source mismatch or dirty checkout")
        report.update(verified_head=head,clean_tree=True)
        spec = importlib.util.spec_from_file_location("m7_install", repo / "experiments/m7_cuda/colab_driver.py")
        helper = importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
        helper.SHA = SHA;helper.sh = sh
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PIP_DISABLE_PIP_VERSION_CHECK="1", PIP_NO_INDEX="1")
        env.pop("PYTHONPATH", None)
        report["stage"] = "installed_package"
        report["installed_package"] = helper.install_project(str(repo), env)
        device = "cpu" if DRY_RUN else "cuda"
        report["stage"] = "correctness_gate"
        gateout = WORK / "m9_gate"
        code, so, se = sh([sys.executable,"-I","experiments/m7_cuda/run_m7_cuda.py","--device",device,"--quick","--source-sha",SHA,"--out",str(gateout),"--max-seconds","25"],40,repo,env)
        gate = json.loads((gateout/"results.json").read_text());report["correctness_gate"] = gate
        expected = "DRY_RUN_CPU" if DRY_RUN else "PASS"
        if code or gate["status"] != expected or not gate["plan_complete"] or not gate["source_sha_verified"]:
            raise RuntimeError("installed-package correctness gate failed; benchmark NOT RUN")
        if not DRY_RUN and (not gate["gpu_evidence"] or "T4" not in gate["environment"].get("gpu_name", "")):
            raise RuntimeError("actual T4 identity not established")
        report["stage"] = "benchmark"
        out=WORK/"m9_out"
        args=[sys.executable,"-I","experiments/m9_compile/run_m9.py","--device",device,"--source-sha",SHA,"--out",str(out),"--max-seconds","160"]
        if DRY_RUN:args.append("--smoke")
        code,so,se=sh(args,185,repo,env)
        if (out/"results.json").exists():
            raw=(out/"results.json").read_bytes();benchmark=json.loads(raw)
            report["benchmark_status"]=benchmark["status"]
            report["benchmark_counts"]={"planned_cases":len(benchmark["cases"]),"classifications":[c["classification"] for c in benchmark["cases"]]}
            report["benchmark_json_sha256"]=hashlib.sha256(raw).hexdigest()
            report["benchmark_zlib_base64"]=base64.b64encode(zlib.compress(raw)).decode("ascii")
            report["benchmark_json_encoding"]="zlib.decompress(base64.b64decode(benchmark_zlib_base64)); exact raw results.json bytes"
            report["raw_files"]={n:(out/n).read_bytes().decode("utf-8") for n in ("trials.csv","summary.md","manifest.json")}
        elif Path(str(out)+".partial.json").exists():
            raw=Path(str(out)+".partial.json").read_bytes()
            report["benchmark_zlib_base64"]=base64.b64encode(zlib.compress(raw)).decode("ascii")
            report["benchmark_json_sha256"]=hashlib.sha256(raw).hexdigest()
            report["benchmark_checkpoint"]=True
            report["exceptions"].append("External runner timeout/failure; last completed-matrix checkpoint retained, later work NOT RUN/unobserved")
        else:
            raise RuntimeError("runner produced no benchmark file; full exception retained")
        if code:report["benchmark_status"]="BLOCKED"
        report["stage"]="done"
    except Exception:
        report["exceptions"].append(traceback.format_exc())
    raw=json.dumps(report,separators=(",",":"),allow_nan=False).encode()
    # No adverse rows/logs are truncated to satisfy the transport limit.
    path=WORK/NAME;path.write_bytes(raw)
    print(f"ARTIFACT {NAME} {len(raw)} {hashlib.sha256(raw).hexdigest()}",flush=True)


if __name__=="__main__":
    main()
