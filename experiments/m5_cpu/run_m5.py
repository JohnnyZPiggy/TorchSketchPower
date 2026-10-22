"""M5 CPU diagnostics runner.

    python experiments/m5_cpu/run_m5.py --out reports/m5_cpu
    python experiments/m5_cpu/run_m5.py --out <dir> --smoke

CPU only; no GPU/TPU, compile, streaming, network or extra dependency. Compares its replay
with the committed M4 rows (reports/m4_cpu/samples.csv) for the baseline block.
"""
import argparse
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m5lib as lib  # noqa: E402
import torch  # noqa: E402

REPO = os.path.dirname(os.path.dirname(HERE))
DEFAULT_M4 = os.path.join(REPO, "reports", "m4_cpu", "samples.csv")


def git_info():
    def run(*a):
        try:
            return subprocess.run(["git", *a], capture_output=True, text=True, cwd=HERE).stdout.strip()
        except Exception:
            return ""
    head = run("rev-parse", "HEAD")
    return {"head": head or None, "dirty": bool(run("status", "--porcelain")) if head else None}


def select(cases, smoke):
    if not smoke:
        return cases
    return [c for c in cases if c["block"] == "O_tiny"] + [c for c in cases if c["block"] == "P_baseline"][:3] \
        + [c for c in cases if c["block"] == "S_psi"][:2]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/m5_cpu")
    ap.add_argument("--m4-samples", default=DEFAULT_M4)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args(argv)
    t0 = time.time()
    os.makedirs(args.out, exist_ok=True)
    m4_rows = lib.load_m4_rows(args.m4_samples) if os.path.exists(args.m4_samples) else None
    cases = select(lib.build_cases(), args.smoke)
    rows = [lib.run_case(c, m4_rows) for c in cases]
    lib.write_csv(os.path.join(args.out, "samples.csv"), rows)
    with open(os.path.join(args.out, "samples.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(rows, f, indent=1)
    with open(os.path.join(args.out, "summary.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(lib.summary_markdown(rows))
    files = ["samples.csv", "samples.json", "summary.md"]
    import torchsketchpower

    man = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "invocation": " ".join([sys.executable, *sys.argv]), "source": git_info(),
        "package_file": torchsketchpower.__file__, "os": platform.platform(), "python": sys.version.split()[0],
        "torch": torch.__version__, "device": "cpu",
        "cpu": os.environ.get("PROCESSOR_IDENTIFIER") or platform.processor() or "unknown",
        "logical_cpus": os.cpu_count(), "torch_threads": torch.get_num_threads(),
        "grid": "smoke" if args.smoke else "full", "n_cases": len(rows),
        "m4_reference": {"path": os.path.relpath(args.m4_samples, REPO) if m4_rows is not None else None,
                         "sha256": lib.sha256_file(args.m4_samples) if m4_rows is not None else None,
                         "m4_source_sha": "36e94999b7cf6f64d6437d0c2179fe1eb762386e"},
        "tolerances": {"identity_flag": "residual <= %g * max(1, largest term), terms relative to ||A||_F^2" % lib.ID_TOL, "m4_rel": lib.M4_TOL},
        "definitions": {
            "squared_terms": "relative to ||A||_F^2",
            "cross": "-2 Re <D, B - B_r>, <X,Y> = tr(X^H Y); ||Bstar-B_r||^2 = ||D||^2 + ||B-B_r||^2 + cross",
            "cond_c": "sigma_max(C)/sigma_min(C), C = Psi Q, via torch.linalg.svdvals",
            "stationarity_rel": "||C^H (C B - W)||_F / (||C||_2 ||C B - W||_F), null when the residual is at the noise floor",
            "ideal_r": "Q (Q^H A)_r, rank-r truncation inside the sketched range",
            "psi_prefix48": "first d rows of one 48-row Gaussian Psi (seed 900000): nested draws",
            "psi_seeded": "independent 24-row Gaussian Psi (seed 900000+k), A and Q fixed",
            "sequential": "Psi drawn from the sketch generator after Omega, Phi, as in sketch_power_low_rank (M4 convention)",
        },
        "files": {n: {"sha256": lib.sha256_file(os.path.join(args.out, n)),
                      "bytes": os.path.getsize(os.path.join(args.out, n))} for n in files},
        "not_run": ["GPU", "TPU", "torch.compile", "streaming/one-pass", "batching", "sparsesign", "timing/speedup",
                    "Actions", "paid services"],
        "wall_seconds": round(time.time() - t0, 2),
    }
    with open(os.path.join(args.out, "manifest.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(man, f, indent=1)
    print(f"wrote {len(rows)} cases ({sum(r['status'] == 'ok' for r in rows)} ok)")


if __name__ == "__main__":
    main()
