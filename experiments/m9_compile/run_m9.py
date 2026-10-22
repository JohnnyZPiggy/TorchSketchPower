"""Bounded M9 compilation probe; all production checks remain enabled."""
import argparse
import csv
import hashlib
import io
import json
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
from torchsketchpower import sketch_power_low_rank, sketch_power_subspace, reconstruct_from_corange
from torchsketchpower import RankDeficiencyError, IllConditionedWarning, solve_corange_coefficient

SEED = 314


def fixed_sketches(a, omega, phi, psi):
    return a @ omega, a @ phi, psi @ a


def inputs(dtype, device, m, n):
    g = torch.Generator(device=device).manual_seed(123)
    a = torch.randn(m, n, generator=g, dtype=dtype, device=device)
    g.manual_seed(SEED)
    return a, (torch.randn(n, 6, generator=g, dtype=dtype, device=device),
               torch.randn(n, 8, generator=g, dtype=dtype, device=device),
               torch.randn(10, m, generator=g, dtype=dtype, device=device))


def pipeline(a, sketches, steps):
    omega, phi, psi = sketches
    y, z, w = fixed_sketches(a, omega, phi, psi)
    return reconstruct_from_corange(sketch_power_subspace(y, z, steps=steps), psi, w, 3)


def approx(out):
    return (out[0] * out[1]) @ out[2]


def compare(a, got, want):
    tol = 1e-3 if a.dtype == torch.float32 else 1e-9  # existing CPU oracle contract
    x, y = approx(got), approx(want)
    finite = all(bool(torch.isfinite(t).all()) for t in got)
    if not finite:
        return {'status':'CORRECTNESS_FAIL','finite':False,'reason':'nonfinite output; timing stopped'}
    delta = float(torch.linalg.vector_norm((x-y).double()))
    singular_delta = float(torch.linalg.vector_norm((got[1]-want[1]).double()))
    limit = tol * max(1., float(torch.linalg.vector_norm(y.double())))
    ok = finite and delta <= limit and singular_delta <= tol * max(1., float(want[1].double().norm()))
    return {'status':'SUPPORTED' if ok else 'CORRECTNESS_FAIL','finite':finite,
            'reconstruction_delta_fro':delta,'reconstruction_limit':limit,'singular_value_delta':singular_delta,
            'eager_residual_fro':float((a-y).double().norm()),'compiled_residual_fro':float((a-x).double().norm()),
            'rank':len(got[1]),'comparison':'reconstructed matrices and singular values, not vector signs'}


def explanation(fn, args, kwargs):
    try:
        e = torch._dynamo.explain(fn)(*args, **kwargs)
        return {'status':'SUPPORTED','graph_count':e.graph_count,'graph_break_count':e.graph_break_count,
                'op_count':e.op_count,'break_reasons':[str(x) for x in e.break_reasons],
                'compile_times':str(e.compile_times),'raw':str(e)}
    except Exception:
        return {'status':'UNSUPPORTED','exception':traceback.format_exc()}


def timed(fn, device):
    if device == 'cuda':
        torch.cuda.synchronize();before=torch.cuda.memory_allocated();reserved=torch.cuda.memory_reserved()
        torch.cuda.reset_peak_memory_stats();start=torch.cuda.Event(enable_timing=True);end=torch.cuda.Event(enable_timing=True)
    t=time.perf_counter()
    if device=='cuda':start.record()
    out=fn()
    if device=='cuda':end.record();torch.cuda.synchronize()
    data={'wall_ms':(time.perf_counter()-t)*1000,'event_ms':start.elapsed_time(end) if device=='cuda' else None,
          'memory':{'allocated_before':before,'reserved_before':reserved,'peak_allocated':torch.cuda.max_memory_allocated(),
                    'delta_peak_allocated':torch.cuda.max_memory_allocated()-before,'peak_reserved':torch.cuda.max_memory_reserved()} if device=='cuda' else None}
    return out,data


def controls(eager, compiled, a, sketches, steps, helper):
    results=[]
    for label, matrix, extra in [('rank_deficient',torch.zeros_like(a),{}),('forced_condition_limit_warning',a,{'max_condition':1.})]:
        observed=[]
        for fn in (eager,compiled):
            with warnings.catch_warnings(record=True) as ws:
                warnings.simplefilter('always')
                try:
                    if helper:
                        omega,phi,psi=sketches;y,z,w=fn(matrix,omega,phi,psi)
                        reconstruct_from_corange(sketch_power_subspace(y,z,steps=steps),psi,w,3,**extra)
                    else:fn(matrix,3,6,8,10,steps=steps,generator=torch.Generator(device=a.device).manual_seed(SEED),**extra)
                    exception=None
                except Exception as exc:exception=type(exc).__name__
                observed.append({'exception':exception,'warnings':[x.category.__name__ for x in ws]})
        ok=(all(x['exception']=='RankDeficiencyError' for x in observed) if label=='rank_deficient' else
            all(x['exception'] is None and 'IllConditionedWarning' in x['warnings'] for x in observed))
        results.append({'case':label,'status':'SUPPORTED' if ok else 'CORRECTNESS_FAIL','observed':observed})
    return results


def corange_control(case, device):
    dtype=getattr(torch,case['dtype']);q=torch.eye(4,2,dtype=dtype,device=device)
    psi=torch.zeros(2,4,dtype=dtype,device=device);psi[0,0]=1.;psi[1,1]=1e-10
    expected=torch.ones(2,3,dtype=dtype,device=device);w=psi@q@expected
    row=dict(case,classification='UNSUPPORTED',trials=[],controls=[],exceptions=[])
    try:
        compiled=torch.compile(solve_corange_coefficient,backend=case['backend'],fullgraph=False,dynamic=False)
        for label,p in [('ill_conditioned',psi),('rank_deficient',psi*torch.tensor([[1.],[0.]],device=device))]:
            observations=[]
            for fn in (solve_corange_coefficient,compiled):
                with warnings.catch_warnings(record=True) as ws:
                    warnings.simplefilter('always')
                    try:
                        value=fn(q,p,w);torch.testing.assert_close(value,expected,rtol=1e-9,atol=1e-9);error=None
                    except Exception as exc:error=type(exc).__name__
                    observations.append({'exception':error,'warnings':[x.category.__name__ for x in ws]})
            ok=all(x['exception']=='RankDeficiencyError' for x in observations) if label=='rank_deficient' else all(x['exception'] is None and 'IllConditionedWarning' in x['warnings'] for x in observations)
            row['controls'].append({'case':label,'status':'SUPPORTED' if ok else 'CORRECTNESS_FAIL','observed':observations})
        row['explain']=explanation(solve_corange_coefficient,(q,psi,w),{})
        row['classification']='CORRECTNESS_FAIL' if any(c['status']=='CORRECTNESS_FAIL' for c in row['controls']) else ('GRAPH_BREAK' if row['explain'].get('graph_break_count',0)>0 else 'SUPPORTED')
    except Exception:row['exceptions'].append(traceback.format_exc())
    return row


def worker(case, device):
    torch.set_num_threads(1)
    if device=='cuda':torch.backends.cuda.matmul.allow_tf32=False
    if case['kind']=='corange':return corange_control(case,device)
    dtype=getattr(torch,case['dtype']);m,n=(256,128) if device=='cuda' else (32,24)
    a,sketches=inputs(dtype,device,m,n);buf=io.BytesIO();torch.save(a.cpu(),buf)
    report=dict(case,classification='UNSUPPORTED',shape=[m,n],r=3,s=6,ell=8,d=10,matrix_seed=123,sketch_seed=SEED,
                tensor_torch_save_sha256=hashlib.sha256(buf.getvalue()).hexdigest(),trials=[],warnings=[],exceptions=[])
    helper=case['kind']=='helper';fn=fixed_sketches if helper else sketch_power_low_rank
    args=(a,*sketches) if helper else (a,3,6,8,10)
    def kwargs():return {} if helper else {'steps':case['steps'],'generator':torch.Generator(device=device).manual_seed(SEED)}
    try:
        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter('always')
            eager,trial=timed(lambda:fn(*args,**kwargs()),device);report['trials'].append(dict(trial,phase='eager_first'))
            t=time.perf_counter();compiled=torch.compile(fn,backend=case['backend'],fullgraph=case['fullgraph'],dynamic=False)
            report['wrapper_creation_ms']=(time.perf_counter()-t)*1000
            compile_attempt_start=time.perf_counter()
            got,trial=timed(lambda:compiled(*args,**kwargs()),device);report['trials'].append(dict(trial,phase='compiled_first_compile_plus_run'))
            if helper:
                for x,y in zip(got,eager):torch.testing.assert_close(x,y,rtol=1e-3 if dtype==torch.float32 else 1e-9,atol=1e-5 if dtype==torch.float32 else 1e-10)
                def compose(outputs):return reconstruct_from_corange(sketch_power_subspace(outputs[0],outputs[1],steps=case['steps']),sketches[2],outputs[2],3)
                report['accuracy']=compare(a,compose(got),compose(eager))
                public=sketch_power_low_rank(a,3,6,8,10,steps=case['steps'],generator=torch.Generator(device=device).manual_seed(SEED))
                report['public_pairing']=compare(a,compose(got),public)
            else:report['accuracy']=compare(a,got,eager)
            if report['accuracy']['status']=='CORRECTNESS_FAIL' or report.get('public_pairing',{}).get('status')=='CORRECTNESS_FAIL':
                report['classification']='CORRECTNESS_FAIL';return report
            for mode,call in [('eager',fn),('compiled',compiled)]:
                timed(lambda:call(*args,**kwargs()),device)  # one unmeasured warmup per mode
                for i in range(3):
                    _,trial=timed(lambda:call(*args,**kwargs()),device);report['trials'].append(dict(trial,phase=mode+'_warm',repeat=i))
            report['controls']=controls(fn,compiled,a,sketches,case['steps'],helper)
            if any(c['status']=='CORRECTNESS_FAIL' for c in report['controls']):report['classification']='CORRECTNESS_FAIL';return report
            # Explanation runs after cold/warm timings, so it cannot warm the measured first call.
            report['explain']=explanation(fn,args,kwargs())
            report['classification']='GRAPH_BREAK' if report['explain'].get('graph_break_count',0)>0 else 'SUPPORTED'
            report['warnings']=[{'category':x.category.__name__,'message':str(x.message)} for x in ws]
    except Exception:
        if 'compile_attempt_start' in locals():report['failed_attempt_wall_ms']=(time.perf_counter()-compile_attempt_start)*1000
        report['exceptions'].append(traceback.format_exc())
    finally:
        if 'ws' in locals():report['warnings']=[{'category':x.category.__name__,'message':str(x.message)} for x in ws]
    return report


def plan():
    cases=[]
    for dtype in ('float32','float64'):
        for kind,backend,fullgraph,steps in [('helper','inductor',True,1),('helper','aot_eager',True,1),
                                           ('public','aot_eager',False,0),('public','aot_eager',False,1)]:
            cases.append(dict(kind=kind,backend=backend,fullgraph=fullgraph,steps=steps,dtype=dtype))
    cases += [dict(kind='public',backend='inductor',fullgraph=False,steps=1,dtype='float64'),
              dict(kind='public',backend='aot_eager',fullgraph=True,steps=1,dtype='float64')]
    cases.append(dict(kind='corange',backend='aot_eager',fullgraph=False,steps=0,dtype='float64'))
    return cases


def run(out, source_sha, device='cpu', max_seconds=360):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);start=time.monotonic()
    report={'source_sha':source_sha,'status':'PROBE_ONLY','cases':[],'environment':{'torch':torch.__version__,'python':sys.version,
             'platform':platform.platform(),'cuda_build':torch.version.cuda,'device':device,'threads':1},
             'methodology':{'timing':'first call compile+run separate from three warm whole-call trials, one warmup each; no kernel-only or headline speedup',
                            'rng':'seed314 reset device-matched generator per public call, inside timed-call wrapper; fixed helper sketches pre-generated',
                            'helper':'only three matmuls compiled; production rank/conditioning checks remain eager when composing; not end-to-end compiled timing',
                            'backend':'aot_eager is debugging/AOT tracing without optimized codegen; inductor separately tested',
                            'cache':'private per-case inductor cache, fresh worker; first call is not machine cold; explain after timings',
                            'exceptions':'same rank error and ill-conditioning warning must be observed; never use ignore rank policy'},
             'gpu':'NOT_RUN' if device=='cpu' else 'ACTUAL_CUDA_PROBE','cleanup':'controller-owned if GPU; no CPU session allocated'}
    if device=='cuda':report['environment']['gpu_name']=torch.cuda.get_device_name(0)
    unavailable=set()
    for i,case in enumerate(plan()):
        remaining=max_seconds-(time.monotonic()-start)
        row=dict(case,case_id=i,classification='NOT_RUN')
        if remaining<5 or (case['backend'] in unavailable):
            row['reason']='batch deadline or previous backend failure; no automatic retry';report['cases'].append(row);continue
        casefile=out/f'case-{i}.json';env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',TORCHINDUCTOR_CACHE_DIR=str((out/f'cache-{i}').resolve()))
        args=[sys.executable,'-I',str(Path(__file__).resolve()),'--worker',json.dumps(case),'--device',device,'--out',str(casefile)]
        try:
            p=subprocess.run(args,capture_output=True,stdin=subprocess.DEVNULL,timeout=min(60 if device=='cpu' else 40,remaining),env=env)
            (out/f'case-{i}.stdout.log').write_bytes(p.stdout);(out/f'case-{i}.stderr.log').write_bytes(p.stderr)
            row=json.loads(casefile.read_bytes()) if casefile.exists() else dict(row,classification='UNSUPPORTED',exception='worker produced no result')
            row.update(case_id=i,exit_code=p.returncode,worker_stdout=p.stdout.decode(errors='replace'),worker_stderr=p.stderr.decode(errors='replace'))
        except subprocess.TimeoutExpired as exc:
            (out/f'case-{i}.stdout.log').write_bytes(exc.stdout or b'');(out/f'case-{i}.stderr.log').write_bytes(exc.stderr or b'')
            row.update(classification='UNSUPPORTED',exception=traceback.format_exc(),reason='bounded worker timeout; no retry',worker_stdout=(exc.stdout or b'').decode(errors='replace'),worker_stderr=(exc.stderr or b'').decode(errors='replace'))
        if row['classification']=='UNSUPPORTED' and not case['fullgraph']:unavailable.add(case['backend'])
        if row['classification']=='UNSUPPORTED' and case['kind']=='helper':unavailable.add(case['backend'])
        report['cases'].append(row)
        (out/'results.partial.json').write_text(json.dumps(report,allow_nan=False))
    report['cpu_justifies_gpu']=device=='cpu' and any(c['kind']=='helper' and c['backend']=='inductor' and c['classification']=='SUPPORTED' for c in report['cases']) and not any(c['classification']=='CORRECTNESS_FAIL' for c in report['cases'])
    report['wall_seconds']=time.monotonic()-start
    (out/'results.json').write_text(json.dumps(report,allow_nan=False,separators=(',',':')))
    with (out/'trials.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['case_id','kind','backend','dtype','steps','phase','repeat','wall_ms','event_ms','memory']);w.writeheader()
        for c in report['cases']:
            for t in c.get('trials',[]):w.writerow(dict({k:c[k] for k in ('case_id','kind','backend','dtype','steps')},**{k:json.dumps(v) if isinstance(v,dict) else v for k,v in t.items()}))
    summary=['# M9 bounded compile probe',f'Source {source_sha}; {device}; no compile-success-to-speedup inference.','']
    for c in report['cases']:summary.append(f"case{c['case_id']}: {c['kind']}/{c['backend']}/{c['dtype']}/steps{c['steps']}/fullgraph{c['fullgraph']}: {c['classification']}")
    (out/'summary.md').write_text('\n'.join(summary)+'\n')
    manifest={'source_sha':source_sha,'files':{n:{'bytes':(out/n).stat().st_size,'sha256':hashlib.sha256((out/n).read_bytes()).hexdigest()} for n in ('results.json','trials.csv','summary.md')}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2));return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--worker');p.add_argument('--source-sha');p.add_argument('--device',choices=['cpu','cuda'],default='cpu');p.add_argument('--out',required=True);p.add_argument('--max-seconds',type=float,default=360);args=p.parse_args()
    if args.worker:Path(args.out).write_text(json.dumps(worker(json.loads(args.worker),args.device),allow_nan=False))
    else:
        repo=Path(__file__).resolve().parents[2]
        if subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()!=args.source_sha or subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True).strip():p.error('exact clean source required')
        r=run(args.out,args.source_sha,args.device,args.max_seconds);print(json.dumps({'cases':[{k:c[k] for k in ('case_id','classification')} for c in r['cases']],'cpu_justifies_gpu':r['cpu_justifies_gpu']}))
