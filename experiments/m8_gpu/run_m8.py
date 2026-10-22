"""M8 paired accuracy/time/allocator pilot; no production instrumentation or speedup assumptions."""
import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
import traceback
import warnings

import torch
from torchsketchpower import sketch_power_low_rank

TIERS = (1.10, 1.50)
METHODS = (("spi", 0), ("spi", 1), ("svd_lowrank", 0), ("svd_lowrank", 1), ("dense_svd", None))
REPEATS, WARMUP = 3, 1


def matrix_plan(smoke=False):
    if smoke:
        return [(24, 16, "geometric", "float64")]
    return [(m, n, sp, dt) for m, n in ((256, 128), (1024, 512), (2048, 1024))
            for sp in (("geometric",) if m == 2048 else ("geometric", "polynomial", "near_flat"))
            for dt in ("float32", "float64")]


def methods(smoke=False):
    return [{"method": name, "steps": k if name == "spi" else None,
             "niter": k if name == "svd_lowrank" else None, "q": 4 if smoke else 16,
             "r": 2 if smoke else 8, "s": 4 if smoke else 16,
             "ell": 8 if smoke else 32, "d": 8 if smoke else 32,
             "rng_seed": 2000 if name == "spi" else (3000 if name == "svd_lowrank" else None)}
            for name, k in METHODS]


def make_matrix(m, n, spectrum, seed=123):
    """CPU float64 synthesis, then one rounded tensor paired across CPU/GPU methods."""
    p = min(m, n)
    g = torch.Generator().manual_seed(seed)
    u = torch.linalg.qr(torch.randn(m, p, dtype=torch.float64, generator=g), mode="reduced")[0]
    v = torch.linalg.qr(torch.randn(n, p, dtype=torch.float64, generator=g), mode="reduced")[0]
    if spectrum == "geometric":
        s = torch.logspace(0, -4, p, dtype=torch.float64)
    elif spectrum == "polynomial":
        s = 1 / torch.arange(1, p + 1, dtype=torch.float64)
    elif spectrum == "near_flat":
        s = torch.linspace(1.0, 0.95, p, dtype=torch.float64)
    else:
        raise ValueError("unknown spectrum")
    return (u * s) @ v.mH


def call_method(a, cfg):
    r = cfg["r"]
    if cfg["method"] == "spi":
        g = torch.Generator(device=a.device).manual_seed(cfg["rng_seed"])
        return sketch_power_low_rank(a, r, cfg["s"], cfg["ell"], cfg["d"],
                                    steps=cfg["steps"], distribution="gaussian", generator=g)
    if cfg["method"] == "svd_lowrank":
        # Public API uses the device global RNG; distinct from SPI's private generator.
        if a.is_cuda:
            torch.cuda.manual_seed(cfg["rng_seed"])
        else:
            torch.manual_seed(cfg["rng_seed"])
        u, s, v = torch.svd_lowrank(a, q=cfg["q"], niter=cfg["niter"])
        return u[:, :r], s[:r], v[:, :r].mH
    if cfg["method"] == "dense_svd":
        u, s, vh = torch.linalg.svd(a, full_matrices=False)
        return u[:, :r], s[:r], vh[:r]
    raise ValueError("unknown method")


def timed_call(fn, device):
    """Whole-call wall/event time; event includes stream idle gaps, not kernel-only time."""
    cuda = device.type == "cuda"
    data = {"status": "PASS", "event_ms": None, "warnings": [], "memory": None}
    if cuda:
        torch.cuda.synchronize()
        data["memory"] = {"allocated_before": torch.cuda.memory_allocated(),
                          "reserved_before": torch.cuda.memory_reserved()}
        torch.cuda.reset_peak_memory_stats()
        start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
    output = None
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        t = time.perf_counter()
        try:
            if cuda:
                start.record()
            output = fn()
            if cuda:
                end.record()
                torch.cuda.synchronize()
        except Exception:
            data.update(status="FAIL", exception=traceback.format_exc())
        data["wall_ms"] = (time.perf_counter() - t) * 1000
        data["warnings"] = [{"type": x.category.__name__, "message": str(x.message)} for x in caught]
    if cuda:
        if data["status"] == "PASS":
            data["event_ms"] = start.elapsed_time(end)
        mem = data["memory"]
        mem.update(peak_allocated=torch.cuda.max_memory_allocated(), peak_reserved=torch.cuda.max_memory_reserved())
        mem["delta_peak_allocated"] = mem["peak_allocated"] - mem["allocated_before"]
        mem["delta_peak_reserved"] = mem["peak_reserved"] - mem["reserved_before"]
    return output, data


def accuracy(a, factors, reference_s):
    u, s, vh = factors
    residual = a - (u * s) @ vh
    singular = torch.linalg.svdvals(residual).double()
    fro2 = float(torch.linalg.vector_norm(residual.double()) ** 2)
    spectral = float(singular[0])
    norm_f = float(torch.linalg.vector_norm(reference_s.double()))
    norm_s = float(reference_s[0])
    opt_f = float(torch.linalg.vector_norm(reference_s[len(s):].double()))
    opt_s = float(reference_s[len(s)])
    floor = 100 * torch.finfo(a.dtype).eps * norm_f
    spectrum_fro2 = float((singular ** 2).sum())
    audit = abs(fro2 - spectrum_fro2) / max(fro2, floor ** 2)
    finite = all(bool(torch.isfinite(x).all()) for x in factors) and math.isfinite(fro2)
    ey_ok = math.sqrt(fro2) >= opt_f * (1 - 500 * torch.finfo(a.dtype).eps)
    return {"status": "PASS" if finite and ey_ok and audit < 1e-3 else "FAIL",
            "rel_fro": math.sqrt(fro2) / norm_f, "rel_spectral": spectral / norm_s,
            "fro_ratio": math.sqrt(fro2) / opt_f if opt_f > floor else None,
            "spectral_ratio": spectral / opt_s if opt_s > floor else None,
            "denominator_floor": floor, "opt_fro": opt_f, "opt_spectral": opt_s,
            "residual_fro2": fro2, "residual_svd_fro2": spectrum_fro2, "svd_fro_audit": audit,
            "residual_singular_values": singular.cpu().tolist(), "finite": finite, "ey_ok": ey_ok}


def quantile(xs, fraction):
    xs = sorted(xs)
    pos = (len(xs) - 1) * fraction
    lo = int(pos)
    return xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (pos - lo)


def summarize(configs, trials):
    rows = []
    for cfg in configs:
        warm = [x for x in trials if x["config_id"] == cfg["config_id"] and x["phase"] == "warm" and x["status"] == "PASS"]
        row = {"config_id": cfg["config_id"], "status": cfg["status"], "n_warm": len(warm)}
        if warm:
            wall = [x["wall_ms"] for x in warm]
            events = [x["event_ms"] for x in warm if x["event_ms"] is not None]
            row.update(wall_median_ms=statistics.median(wall), wall_iqr_ms=quantile(wall, .75)-quantile(wall, .25),
                       event_median_ms=statistics.median(events) if events else None,
                       event_iqr_ms=quantile(events, .75)-quantile(events, .25) if events else None,
                       peak_allocated=max((x["memory"]["peak_allocated"] for x in warm if x["memory"]), default=None),
                       delta_peak_allocated=max((x["memory"]["delta_peak_allocated"] for x in warm if x["memory"]), default=None))
        rows.append(row)
    comparisons = []
    byid = {x["config_id"]: x for x in rows}
    for group in sorted({(c["matrix_id"], c["device"]) for c in configs}):
        cs = [c for c in configs if (c["matrix_id"], c["device"]) == group and c["status"] == "PASS" and byid[c["config_id"]]["n_warm"] == REPEATS]
        def score(c):
            sm = byid[c["config_id"]]
            return c["accuracy"]["fro_ratio"], sm["wall_median_ms"], sm["delta_peak_allocated"] or 0
        pareto = [c["config_id"] for c in cs if not any(all(x <= y for x,y in zip(score(other),score(c))) and any(x < y for x,y in zip(score(other),score(c))) for other in cs)]
        for tier in TIERS:
            eligible = [c for c in cs if c["accuracy"]["fro_ratio"] is not None and c["accuracy"]["fro_ratio"] <= tier]
            comparisons.append({"matrix_id": group[0], "device": group[1], "tier": tier,
                                "eligible": [c["config_id"] for c in eligible],
                                "fastest": min(eligible,key=lambda c:byid[c["config_id"]]["wall_median_ms"])["config_id"] if eligible else None,
                                "pareto_accuracy_wall_allocator": pareto})
    return rows, comparisons


def run(device="cuda", smoke=False, source_sha=None, max_seconds=170, checkpoint=None):
    start = time.monotonic()
    torch.set_num_threads(1)
    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = False
    plan = matrix_plan(smoke)
    report = {"source_sha": source_sha, "status": "BLOCKED", "classification": "PROBE_ONLY",
              "gpu_evidence": False, "matrices": [], "configs": [], "trials": [], "exceptions": [],
              "tiers": list(TIERS), "warm_repeats": REPEATS, "warmup": WARMUP,
              "environment": {"python": sys.version, "platform": platform.platform(), "torch": torch.__version__,
                              "cuda_build": torch.version.cuda, "threads": torch.get_num_threads(),
                              "tf32": bool(torch.backends.cuda.matmul.allow_tf32),
                              "matmul_precision": torch.get_float32_matmul_precision(),
                              "torch_config": torch.__config__.show(),
                              "CUDA_LAUNCH_BLOCKING": os.environ.get("CUDA_LAUNCH_BLOCKING"),
                              "kernel_only": "NOT MEASURED", "clock_thermal": "NOT MEASURED"},
              "methodology": {"cold": "first measured call per configuration, after gate/reference work; not process cold",
                              "timing": "synchronized whole call incl RNG, Python, scalar sync, solve and SVD; excludes A synthesis/transfer/accuracy",
                              "events": "whole default-stream interval including idle; NOT kernel-only",
                              "memory": "allocator baseline/absolute peak/delta, not true per-call/device-wide allocation; no empty_cache",
                              "rng": "one paired A seed 123; SPI private stream 2000, svd_lowrank global stream 3000; same method seed replayed each trial; CPU/CUDA seeded draws are not identical",
                              "axes": "steps and niter are different algorithms/parameters, not equivalent work",
                              "scope": "14 GPU matrices + CPU smallest geometric dtype pair; single session, three repeats, no discarded outliers",
                              "near_flat": "M5 stage errors inform interpretation only; not proof of mechanism"}}
    if device == "cuda" and not torch.cuda.is_available():
        report["exceptions"].append({"stage": "device", "status": "BLOCKED", "exception": "CUDA unavailable; no GPU trial ran"})
        return report
    if device == "cuda":
        prop = torch.cuda.get_device_properties(0)
        report["environment"].update(gpu_name=prop.name, gpu_memory=prop.total_memory, capability=[prop.major,prop.minor])
        try:
            smi = subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version,temperature.gpu,clocks.sm,clocks.mem", "--format=csv,noheader"], capture_output=True,text=True,timeout=5)
            report["environment"]["clock_thermal"] = smi.stdout if smi.returncode==0 else "NOT MEASURED: nvidia-smi failed"
        except Exception:
            report["environment"]["clock_thermal"] = "NOT MEASURED: " + traceback.format_exc()
    for mid, (m,n,spectrum,dtype) in enumerate(plan):
        devices = ["cpu"] if device=="cpu" else (["cpu", "cuda"] if mid < 2 else ["cuda"])
        if device=="cuda" and not smoke and spectrum!="geometric":
            devices=["cuda"]
        for dev in devices:
            for idx,cfg in enumerate(methods(smoke)):
                report["configs"].append(dict(cfg,config_id=f"m{mid}-{dev}-{idx}",matrix_id=mid,device=dev,status="NOT_RUN"))
    report["planned_configs"] = len(report["configs"])
    try:
        for mid,(m,n,spectrum,dtype) in enumerate(plan):
            if time.monotonic()-start >= max_seconds:
                raise TimeoutError("matrix plan deadline")
            t=time.perf_counter(); cpu=make_matrix(m,n,spectrum).to(getattr(torch,dtype))
            synth_ms=(time.perf_counter()-t)*1000
            raw=io.BytesIO();torch.save(cpu,raw)
            matrix={"matrix_id":mid,"m":m,"n":n,"spectrum":spectrum,"dtype":dtype,"a_seed":123,
                    "tensor_torch_save_sha256":hashlib.sha256(raw.getvalue()).hexdigest(),"synthesis_ms":synth_ms,"devices":{}}
            report["matrices"].append(matrix)
            for dev in sorted({c["device"] for c in report["configs"] if c["matrix_id"]==mid}):
                t=time.perf_counter(); a=cpu.to(dev)
                if dev=="cuda":torch.cuda.synchronize()
                transfer_ms=(time.perf_counter()-t)*1000
                ref=torch.linalg.svdvals(a)
                matrix["devices"][dev]={"transfer_ms":transfer_ms,"reference_singular_values":ref.cpu().tolist()}
                cs=[c for c in report["configs"] if c["matrix_id"]==mid and c["device"]==dev]
                for phase,repeat in [("cold",0),("warmup",0)]+[("warm",i) for i in range(REPEATS)]:
                    order=cs if (repeat+(phase=="warmup"))%2==0 else list(reversed(cs))
                    for position,cfg in enumerate(order):
                        if time.monotonic()-start >= max_seconds:
                            raise TimeoutError("method plan deadline")
                        output, trial=timed_call(lambda:call_method(a,cfg),a.device)
                        trial.update(config_id=cfg["config_id"],phase=phase,repeat=repeat,order=position)
                        report["trials"].append(trial)
                        if trial["status"]!="PASS":
                            cfg["status"]="FAIL"
                            raise RuntimeError("method failure; full exception retained in trial; no retry")
                        if phase=="cold":
                            cfg["accuracy"]=accuracy(a,output,ref)
                            cfg["status"]=cfg["accuracy"]["status"]
                            if cfg["status"]!="PASS":raise RuntimeError("accuracy metadata audit failed")
                        del output
                del ref,a
            if checkpoint:
                Path(checkpoint).write_text(json.dumps(report,separators=(",",":"),allow_nan=False))
        if time.monotonic()-start >= max_seconds:raise TimeoutError("deadline after final configuration")
        if all(c["status"]=="PASS" for c in report["configs"]) and len(report["trials"])==report["planned_configs"]*(1+WARMUP+REPEATS):
            report["status"]="PASS" if device=="cuda" else "DRY_RUN_CPU"
    except Exception:
        report["exceptions"].append({"stage":"benchmark", "status":"BLOCKED", "exception":traceback.format_exc()})
    report["gpu_evidence"] = any(c["device"]=="cuda" and "accuracy" in c for c in report["configs"])
    report["summaries"],report["comparisons"]=summarize(report["configs"],report["trials"])
    report["completed_configs"]=sum(s["n_warm"]==REPEATS and s["status"]=="PASS" for s in report["summaries"])
    report["wall_seconds"]=time.monotonic()-start
    return report


def write_report(report,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    raw=json.dumps(report,separators=(",",":"),allow_nan=False).encode()
    (out/"results.json").write_bytes(raw)
    fields=["config_id","phase","repeat","order","status","wall_ms","event_ms","warnings","memory","exception"]
    with (out/"trials.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for trial in report["trials"]:
            writer.writerow({k:json.dumps(v,separators=(",",":")) if isinstance(v,(dict,list)) else v for k,v in trial.items()})
    lines=["# M8 bounded performance pilot", "",f"Status: {report['status']}; exact source: {report['source_sha']}",
           f"Completed {report.get('completed_configs',0)}/{report.get('planned_configs',0)} configs. No kernel-only, replicated or universal speedup claim.","",
           "| config | warm n | wall median ms | wall IQR ms | event median ms | Fro / optimum |", "|---|---|---|---|---|---|"]
    byid={c['config_id']:c for c in report['configs']}
    for s in report.get('summaries',[]):
        ratio=byid[s['config_id']].get('accuracy',{}).get('fro_ratio')
        lines.append(f"| {s['config_id']} | {s['n_warm']} | {s.get('wall_median_ms')} | {s.get('wall_iqr_ms')} | {s.get('event_median_ms')} | {ratio} |")
    lines += ["", "Preregistered quality tiers: 1.10 and 1.50; eligible sets and Pareto frontiers are in results.json, including NONE.",
              "Near-flat interpretation: see historical M5 projection/corange/truncation diagnostics; no mechanism is inferred from timings.",
              "Cold means first measured configuration call after correctness/reference work. Event intervals are not kernel-only.",
              "Only one matrix/algorithm seed; three warm repeats do not provide independent scientific replicates."]
    (out/'summary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    manifest={"source_sha":report['source_sha'],"status":report['status'],"files":{n:{"sha256":hashlib.sha256((out/n).read_bytes()).hexdigest(),"bytes":(out/n).stat().st_size} for n in ('results.json','trials.csv','summary.md')}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--device',choices=('cpu','cuda'),default='cuda');p.add_argument('--smoke',action='store_true');p.add_argument('--source-sha',required=True);p.add_argument('--out',required=True);p.add_argument('--max-seconds',type=float,default=170)
    args=p.parse_args()
    here=Path(__file__).resolve().parents[2]
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=here,text=True).strip()
    if head!=args.source_sha or subprocess.check_output(['git','status','--porcelain'],cwd=here,text=True).strip():
        p.error('source SHA mismatch or dirty checkout')
    report=run(args.device,args.smoke,args.source_sha,args.max_seconds,str(args.out)+".partial.json");manifest=write_report(report,args.out)
    print(json.dumps({'status':report['status'],'configs':report.get('completed_configs',0),'planned':report.get('planned_configs',0),'files':manifest['files']}))
    sys.exit(0 if report['status'] in ('PASS','DRY_RUN_CPU') else 2)
