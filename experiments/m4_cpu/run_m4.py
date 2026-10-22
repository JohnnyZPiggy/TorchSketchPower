"""M4 CPU runner: accuracy grid, process-isolated timing/RSS, manifest, summary.

    python experiments/m4_cpu/run_m4.py --out reports/m4_cpu            # full bounded run
    python experiments/m4_cpu/run_m4.py --out <dir> --smoke             # tiny script smoke

CPU only. No GPU/TPU, streaming, compile, network or extra dependency. Memory is
read from the OS (Windows ``GetProcessMemoryInfo`` via ctypes, or ``resource`` on
Unix); if neither works the field is null and the method says NOT MEASURED.
"""
import argparse
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m4lib as lib  # noqa: E402
import torch  # noqa: E402

CHILD_TIMEOUT_S = 120
WARM_REPEATS = 5


def process_memory():
    """Return ``(method, peak_bytes, current_bytes)``; bytes are None if not measurable."""
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class PMC(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            k32 = ctypes.WinDLL("kernel32")
            k32.GetCurrentProcess.restype = wintypes.HANDLE
            psapi = ctypes.WinDLL("psapi")
            psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
            pmc = PMC()
            pmc.cb = ctypes.sizeof(PMC)
            if psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
                return "win32 GetProcessMemoryInfo PeakWorkingSetSize/WorkingSetSize", int(pmc.PeakWorkingSetSize), int(pmc.WorkingSetSize)
        except Exception:
            pass
    else:
        try:
            import resource

            peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            peak = peak if sys.platform == "darwin" else peak * 1024
            return "resource.getrusage ru_maxrss", int(peak), None
        except Exception:
            pass
    return "NOT MEASURED", None, None


def _call(cfg, a, dtype):
    from torchsketchpower import sketch_power_low_rank

    gen = torch.Generator().manual_seed(cfg["sketch_seed"])
    t0 = time.perf_counter_ns()
    sketch_power_low_rank(a, cfg["r"], cfg["s"], cfg["ell"], cfg["d"], steps=cfg["q"], generator=gen)
    return (time.perf_counter_ns() - t0) / 1e9


def child_main(cfg_json: str, repeats: int):
    """Fresh process: import, build A, cold call, warm calls, SVD baseline; print one JSON line."""
    cfg = json.loads(cfg_json)
    a64, _ = lib.make_matrix(cfg["m"], cfg["n"], cfg["spectrum"], cfg["a_seed"])
    a = a64.to(torch.float64)
    method, peak0, _ = process_memory()
    timings = [("cold", 0, _call(cfg, a, a.dtype))]
    _, peak1, _ = process_memory()
    for i in range(repeats):
        timings.append(("warm", i, _call(cfg, a, a.dtype)))
    t0 = time.perf_counter_ns()
    torch.linalg.svd(a, full_matrices=False)
    timings.append(("svd_baseline_cold", 0, (time.perf_counter_ns() - t0) / 1e9))
    for i in range(repeats):
        t0 = time.perf_counter_ns()
        torch.linalg.svd(a, full_matrices=False)
        timings.append(("svd_baseline_warm", i, (time.perf_counter_ns() - t0) / 1e9))
    _, peak2, cur2 = process_memory()
    print(json.dumps({"method": method, "peak0": peak0, "peak1": peak1, "peak2": peak2,
                      "cur2": cur2, "timings": timings}))


def run_timing_config(cfg, repeats=WARM_REPEATS):
    """Run one timing/RSS child; return (timing_rows, memory_row, failure_or_None)."""
    cid = cfg["sample_id"]
    est = lib.estimate_buffer_bytes(cfg["m"], cfg["n"], cfg["r"], cfg["s"], cfg["ell"], cfg["d"], cfg["q"], torch.float64)
    cmd = [sys.executable, os.path.abspath(__file__), "--child", json.dumps(cfg), "--repeats", str(repeats)]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=CHILD_TIMEOUT_S)
        if p.returncode != 0:
            return [], None, {"config_id": cid, "reason": f"exit {p.returncode}: {p.stderr[-300:]}"}
        res = json.loads(p.stdout.strip().splitlines()[-1])
    except Exception as exc:  # timeout / parse errors are recorded
        return [], None, {"config_id": cid, "reason": f"{type(exc).__name__}: {exc}"}
    trows = [{"config_id": cid, "phase": ph, "repeat": i, "seconds": float(sec)} for ph, i, sec in res["timings"]]
    mrow = {"config_id": cid, "method": res["method"], "peak_before_call_bytes": res["peak0"],
            "peak_after_cold_call_bytes": res["peak1"], "peak_after_all_calls_bytes": res["peak2"],
            "current_after_all_calls_bytes": res["cur2"], "est_buffer_bytes": est}
    return trows, mrow, None


def git_info():
    def run(*a):
        try:
            return subprocess.run(["git", *a], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__))).stdout.strip()
        except Exception:
            return ""
    return {"head": run("rev-parse", "HEAD") or None, "dirty": bool(run("status", "--porcelain")) if run("rev-parse", "HEAD") else None}


def manifest(args, out, files, n_samples, failures, t_total):
    import torchsketchpower

    cfgstr = torch.__config__.show()
    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "invocation": " ".join([sys.executable, *sys.argv]),
        "source": git_info(),
        "package_file": torchsketchpower.__file__,
        "os": platform.platform(), "python": sys.version.split()[0], "torch": torch.__version__,
        "cpu": os.environ.get("PROCESSOR_IDENTIFIER") or platform.processor() or "unknown",
        "logical_cpus": os.cpu_count(), "torch_threads": torch.get_num_threads(),
        "torch_interop_threads": torch.get_num_interop_threads(),
        "thread_env": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
        "torch_config": cfgstr, "device": "cpu",
        "grid": "smoke" if args.smoke else "full", "n_accuracy_samples": n_samples,
        "timing_scope": "one call of sketch_power_low_rank (validation, sketches, rank checks, power steps, reconstruction); "
                        "perf_counter_ns; fresh generator per call; matrix construction excluded; "
                        "cold = first call in a fresh child process; warm = next repeats; svd_baseline = torch.linalg.svd(A, full_matrices=False)",
        "memory_scope": "OS process high-water mark read inside a fresh child process per configuration. Imports and torch runtime "
                        "dominate it, so the before/after difference is usually 0 and is NOT a per-call allocation. "
                        "est_buffer_bytes is a sum of buffer sizes (an ESTIMATE, not measured).",
        "timing_failures": failures, "wall_seconds_total": round(t_total, 2),
        "files": {name: {"sha256": lib.sha256_file(os.path.join(out, name)), "bytes": os.path.getsize(os.path.join(out, name))} for name in files},
        "not_run": ["GPU", "TPU", "torch.compile", "streaming/one-pass", "sparsesign", "matched float32/float64 draws", "Actions", "paid services"],
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/m4_cpu")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--child")
    ap.add_argument("--repeats", type=int, default=WARM_REPEATS)
    args = ap.parse_args(argv)
    if args.child:
        return child_main(args.child, args.repeats)

    t_start = time.time()
    os.makedirs(args.out, exist_ok=True)
    if args.smoke:
        cfgs = lib.build_grid(seeds=2, shapes=((20, 16), (16, 20), (24, 24)), scale="smoke")
        tcfgs = lib.timing_configs()[:1]
    else:
        cfgs = lib.build_grid()
        tcfgs = lib.timing_configs()
    rows = [lib.run_sample(c) for c in cfgs]
    lib.write_csv(os.path.join(args.out, "samples.csv"), rows)
    with open(os.path.join(args.out, "samples.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=1)

    trows, mrows, failures = [], [], []
    for c in tcfgs:
        t, mr, fail = run_timing_config(c, repeats=2 if args.smoke else WARM_REPEATS)
        trows += t
        if mr:
            mrows.append(mr)
        if fail:
            failures.append(fail)
    lib.write_csv(os.path.join(args.out, "timings.csv"), trows, lib.TIMING_SCHEMA)
    lib.write_csv(os.path.join(args.out, "memory.csv"), mrows, lib.MEMORY_SCHEMA)

    summary = ["# M4 CPU validation - generated summary", "",
               "Generated by `experiments/m4_cpu/run_m4.py`; every number is computed from `samples.csv`.", "",
               f"Samples: {len(rows)} ({sum(r['status'] == 'ok' for r in rows)} ok, "
               f"{sum(r['status'] != 'ok' for r in rows)} recorded failures). Error columns are relative to ||A||.", "",
               lib.summary_markdown(rows), "", "## Paired q comparison (block A_q: same A, same draws)", "",
               "| spectrum | pairs | q=1 < q=0 | q=2 < q=1 | q=2 < q=0 |", "|---|---|---|---|---|"]
    for sp, t in lib.paired_q_table(rows).items():
        summary.append(f"| {sp} | {t['pairs']} | {t['q1_lt_q0']} | {t['q2_lt_q1']} | {t['q2_lt_q0']} |")
    with open(os.path.join(args.out, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(summary) + "\n")

    files = ["samples.csv", "samples.json", "timings.csv", "memory.csv", "summary.md"]
    man = manifest(args, args.out, files, len(rows), failures, time.time() - t_start)
    with open(os.path.join(args.out, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, indent=1)
    print(f"wrote {len(rows)} samples, {len(trows)} timing rows, {len(mrows)} memory rows, {len(failures)} timing failures")


if __name__ == "__main__":
    main()
