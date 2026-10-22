"""M7 device-correctness runner: one bounded, self-contained entry point.

    python experiments/m7_cuda/run_m7_cuda.py --device cuda --out m7_out --source-sha <40-hex>
    python experiments/m7_cuda/run_m7_cuda.py --device cpu  --out dry --quick     # logic check, NOT GPU evidence

Correctness only (no timing, no benchmark, no speedup). Writes ``results.json`` (every case row),
``manifest.json`` (environment and file hashes) and ``summary.md``, then prints one
``ARTIFACT <name> <bytes> <sha256>`` line for the primary report. If ``--device cuda`` is requested and
CUDA is not available the report is written with status BLOCKED and the exit code is 2; a CPU run is
labelled ``DRY_RUN_CPU`` and can never be a GPU result. No network access, no GitHub writes.
"""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import torch  # noqa: E402
import m7lib as lib  # noqa: E402

TOOL_VERSION = "m7-1"
LIMITS = {"float32": (1.0, 1e2, 1e3), "complex64": (1.0, 1e2, 1e3), "float64": (1.0, 1e3, 1e6), "complex128": (1.0, 1e3, 1e6)}
SHAPES = ((40, 24, 6, 10), (30, 30, 6, 6), (24, 40, 6, 12))  # (m, n, s, d): d > s, d = s square, wide
E2E_SHAPE = (40, 30)
SPECTRA = ("geometric", "polynomial", "flat")


def build_plan(quick):
    plan = []
    dtypes = lib.DTYPES if not quick else (torch.float64, torch.complex128)
    for dt in dtypes:
        name = str(dt).replace("torch.", "")
        for (m, n, s, d) in (SHAPES if not quick else SHAPES[:1]):
            for cond in (LIMITS[name] if not quick else LIMITS[name][:2]):
                plan.append(("coefficient", dict(dtype=dt, m=m, n=n, s=s, d=d, cond=cond, seed=11)))
        for sp in (SPECTRA if not quick else SPECTRA[:1]):
            for q in (0, 1):
                plan.append(("end_to_end_A", dict(dtype=dt, m=E2E_SHAPE[0], n=E2E_SHAPE[1], spectrum=sp, seed=3, q_steps=q)))
                seeds = (range(5) if not dt.is_complex else range(2)) if not quick else range(1)
                for sd in seeds:
                    plan.append(("end_to_end_B", dict(dtype=dt, m=E2E_SHAPE[0], n=E2E_SHAPE[1], spectrum=sp, seed=sd, q_steps=q)))
    plan.append(("negative", {}))
    return plan


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def environment(device):
    env = {
        "python": sys.version.split()[0], "platform": platform.platform(), "torch": torch.__version__,
        "torch_cuda_build": torch.version.cuda, "cuda_available": torch.cuda.is_available(),
        "device_requested": device, "lstsq_driver_cuda": "gels", "lstsq_driver_cpu": "gelsd",
        "svd_driver": "torch default (CUDA: gesvdj with gesvd fallback per PyTorch docs)",
        "float32_matmul_precision": torch.get_float32_matmul_precision(),
        "cuda_matmul_allow_tf32": bool(torch.backends.cuda.matmul.allow_tf32),
        "torch_threads": torch.get_num_threads(),
        "sync_policy": "rank/conditioning gates read scalars to the host (float()/int()), which synchronizes the device",
    }
    if torch.cuda.is_available():
        p = torch.cuda.get_device_properties(0)
        env.update(gpu_name=p.name, gpu_total_memory_bytes=int(p.total_memory), gpu_capability=list(p.major_minor) if hasattr(p, "major_minor") else [p.major, p.minor],
                   cuda_device_count=torch.cuda.device_count(), cudnn=torch.backends.cudnn.version())
    return env


def git_head():
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=HERE)
        d = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=HERE)
        return (r.stdout.strip() or None), (bool(d.stdout.strip()) if r.stdout.strip() else None)
    except Exception:
        return None, None


def summarize(rows):
    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return counts


def summary_md(report):
    rows = report["rows"]
    lines = ["# M7 device-correctness report", "",
             f"Status: **{report['status']}** (device: `{report['device']}`; GPU evidence: **{report['gpu_evidence']}**)", "",
             f"Source SHA: `{report['source_sha']}` (verified against git HEAD: {report['source_sha_verified']})", "",
             "| case | PASS | FAIL | BLOCKED | NOT_RUN | max margin (observed error / tolerance) |", "|---|---|---|---|---|---|"]
    for case in sorted({r["case"] for r in rows}):
        rs = [r for r in rows if r["case"] == case]
        c = summarize(rs)
        margins = [r[k] for r in rs for k in ("margin_o1", "margin_o2", "margin_o3", "margin") if k in r and r[k] is not None]
        lines.append(f"| {case} | {c.get(lib.PASS, 0)} | {c.get(lib.FAIL, 0)} | {c.get(lib.BLOCKED, 0)} | {c.get(lib.NOT_RUN, 0)} | "
                     f"{('%.3e' % max(margins)) if margins else 'n/a'} |")
    bad = [r for r in rows if r["status"] in (lib.FAIL, lib.BLOCKED)]
    lines += ["", "## Failures and blocked rows", ""]
    if not bad:
        lines.append("none")
    for r in bad:
        lines.append(f"- `{r['case']}` {r['dtype']} {r.get('reason') or r.get('observed', '')} " + json.dumps({k: r[k] for k in ("m", "n", "s", "d", "cond_designed", "spectrum", "seed", "q") if k in r}))
    lines += ["", "Margins above 1 are failures; margins close to 1 deserve review. A skipped or NOT_RUN row is not a pass.", ""]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda", choices=("cuda", "cpu"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--source-sha", default=None)
    ap.add_argument("--max-seconds", type=float, default=900.0)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args(argv)
    t0 = time.time()
    os.makedirs(args.out, exist_ok=True)
    head, dirty = git_head()
    verified = (head == args.source_sha) if (head and args.source_sha) else None
    env = environment(args.device)
    rows, blocked_reason = [], None
    if args.device == "cuda" and not torch.cuda.is_available():
        blocked_reason = "torch.cuda.is_available() is False in this environment; no CUDA test was run"
    else:
        dev = torch.device(args.device)
        for kind, kw in build_plan(args.quick):
            if time.time() - t0 > args.max_seconds:
                rows.append({"case": kind, "device": str(dev), "dtype": "n/a", "status": lib.NOT_RUN, "reason": "time limit reached"})
                break
            if kind == "coefficient":
                rows.append(lib.coefficient_case(dev, kw["dtype"], kw["m"], kw["n"], kw["s"], kw["d"], kw["cond"], kw["seed"]))
            elif kind == "end_to_end_A":
                rows.append(lib.end_to_end_mode_a(dev, kw["dtype"], kw["m"], kw["n"], kw["spectrum"], kw["seed"], kw["q_steps"]))
            elif kind == "end_to_end_B":
                rows.append(lib.end_to_end_mode_b(dev, kw["dtype"], kw["m"], kw["n"], kw["spectrum"], kw["seed"], kw["q_steps"]))
            else:
                rows.extend(lib.negative_cases(dev))
    counts = summarize(rows)
    gpu = args.device == "cuda" and torch.cuda.is_available()
    if blocked_reason:
        status = "BLOCKED"
    elif not gpu:
        status = "DRY_RUN_CPU"
    elif counts.get(lib.FAIL, 0) or counts.get(lib.BLOCKED, 0):
        status = "FAIL" if counts.get(lib.FAIL, 0) else "BLOCKED"
    else:
        status = "PASS"
    report = {
        "tool_version": TOOL_VERSION, "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_sha": args.source_sha or head, "source_sha_verified": verified, "git_dirty": dirty,
        "status": status, "device": args.device, "gpu_evidence": bool(gpu and status in ("PASS", "FAIL", "BLOCKED") and rows),
        "reason": blocked_reason, "counts": counts, "environment": env, "quick": args.quick,
        "tolerances": {"C_BWD": lib.C_BWD, "note": "pre-registered backward-error bounds, see m7lib docstrings"},
        "not_run": ["performance", "speedup", "torch.compile", "batching", "sparsesign on CUDA", "TPU"],
        "rows": rows, "wall_seconds": round(time.time() - t0, 2),
    }
    p_res = os.path.join(args.out, "results.json")
    with open(p_res, "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=1)
    with open(os.path.join(args.out, "summary.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(summary_md(report))
    manifest = {"files": {n: {"sha256": sha256_file(os.path.join(args.out, n)), "bytes": os.path.getsize(os.path.join(args.out, n))}
                          for n in ("results.json", "summary.md")},
                "invocation": " ".join([sys.executable, *sys.argv]), "status": status, "source_sha": report["source_sha"]}
    with open(os.path.join(args.out, "manifest.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=1)
    print(f"status={status} counts={counts} device={args.device} gpu_evidence={report['gpu_evidence']}")
    print(f"ARTIFACT results.json {manifest['files']['results.json']['bytes']} {manifest['files']['results.json']['sha256']}")
    return {"PASS": 0, "DRY_RUN_CPU": 0, "FAIL": 1, "BLOCKED": 2}[status]


if __name__ == "__main__":
    sys.exit(main())
