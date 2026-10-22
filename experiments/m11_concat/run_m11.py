"""M11 bounded CPU semantic audit, preserving separate RNG draws and all math gates."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback
import warnings

import torch
import torchsketchpower
from torchsketchpower import sketch_power_low_rank, sketch_power_subspace, reconstruct_from_corange
from torchsketchpower._device import check_generator, require_supported_device

DTYPES=(torch.float32,torch.float64,torch.complex64,torch.complex128)
TOL={torch.float32:1e-3,torch.complex64:1e-3,torch.float64:1e-9,torch.complex128:1e-9}


def digest(t):
    return hashlib.sha256(t.detach().resolve_conj().resolve_neg().numpy().tobytes(order='C')).hexdigest()


def metrics(x,y,tol):
    if x.shape!=y.shape:return {'close':False,'reason':'shape mismatch'}
    finite=bool(torch.isfinite(x).all() and torch.isfinite(y).all())
    if not finite:return {'close':False,'reason':'nonfinite'}
    high=torch.complex128 if x.is_complex() else torch.float64
    diff=(x-y).to(high);scale=float(y.to(high).norm());delta=float(diff.norm())
    return {'close':delta<=tol*max(1.,scale),'fro_delta':delta,'max_abs':float(diff.abs().max()),
            'relative_to_max1_norm':delta/max(1.,scale),'bitwise_equal':torch.equal(x,y)}


def tensor_info(t):
    return {'shape':list(t.shape),'dtype':str(t.dtype),'device':str(t.device),'stride':list(t.stride()),
            'contiguous':t.is_contiguous(),'logical_bytes':t.numel()*t.element_size(),
            'backing_bytes':t.untyped_storage().nbytes(),'sha256':digest(t)}


def prototype(a,r,s,ell,d,*,steps,generator,mode,trace,max_condition=None):
    # Domain is the fixed valid-shape Gaussian experiment, not a replacement public API.
    require_supported_device(a.device,'a');check_generator(generator,a.device)
    trace['stage']='draw_Omega';omega=torch.randn(a.shape[1],s,generator=generator,dtype=a.dtype,device=a.device);trace['Omega']=omega
    trace['stage']='draw_Phi';phi=torch.randn(a.shape[1],ell,generator=generator,dtype=a.dtype,device=a.device);trace['Phi']=phi
    trace['stage']='Y_Z'
    if mode=='separate':y,z=a@omega,a@phi
    else:
        packed=torch.cat((omega,phi),dim=1);joint=a@packed;y,z=joint[:,:s],joint[:,s:]
        trace['copy_payload_bytes']={'input_cat':packed.numel()*packed.element_size(),'output_repack':0}
        if mode=='concat_copy':
            trace['copy_payload_bytes']['output_repack']=(y.numel()+z.numel())*y.element_size();y,z=y.contiguous(),z.contiguous()
    trace['Y'],trace['Z']=y,z
    trace['stage']='subspace';q=sketch_power_subspace(y,z,steps=steps);trace['Q']=q
    trace['stage']='draw_Psi';psi=torch.randn(d,a.shape[0],generator=generator,dtype=a.dtype,device=a.device);trace['Psi']=psi
    trace['stage']='W';w=psi@a;trace['W']=w
    trace['stage']='reconstruct';out=reconstruct_from_corange(q,psi,w,r,max_condition=max_condition)
    trace['stage']='returned';return out


def error_stage(message):
    if message.startswith('y has numerical rank'):return 'rank_Y'
    if message.startswith('z.mH @ q'):return 'rank_cross'
    if message.startswith('psi @ q'):return 'rank_C'
    if 'orthonormal' in message:return 'Gram_Q'
    if 'generator' in message or 'device' in message:return 'precheck'
    return 'other'


def capture(fn,g,trace=None):
    before=digest(g.get_state()) if isinstance(g,torch.Generator) else None
    global_before=digest(torch.get_rng_state());out=None
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter('always')
        try:out=fn();error=None
        except Exception as exc:error={'class':type(exc).__name__,'message':str(exc),'stage':error_stage(str(exc)),'traceback':traceback.format_exc()}
    result={'error':error,'warnings':[{'class':w.category.__name__,'message':str(w.message)} for w in ws],
            'rng_before':before,'rng_after':digest(g.get_state()) if isinstance(g,torch.Generator) else None,
            'global_rng_unchanged':global_before==digest(torch.get_rng_state())}
    if trace is not None:
        result['trace_stage']=trace.get('stage');result['draws']={k:tensor_info(trace[k]) if k in trace else None for k in ('Omega','Phi','Psi')}
        result['intermediates']={k:tensor_info(trace[k]) for k in ('Y','Z','Q','W') if k in trace}
        result['copy_payload_bytes']=trace.get('copy_payload_bytes',{'input_cat':0,'output_repack':0})
        if 'Y' in trace:result['Y_Z_share_backing']=trace['Y'].untyped_storage().data_ptr()==trace['Z'].untyped_storage().data_ptr()
    return result,out


def equivalent_records(x,y):
    def err(r):return None if r['error'] is None else {k:r['error'][k] for k in ('class','message','stage')}
    return err(x)==err(y) and x['warnings']==y['warnings'] and x['rng_before']==y['rng_before'] and x['rng_after']==y['rng_after'] and x['global_rng_unchanged'] and y['global_rng_unchanged']


def first_gate_diagnostics(trace,steps,error):
    if 'Y' not in trace:return {}
    y,z=trace['Y'],trace['Z'];sv=torch.linalg.svdvals(y);eps=torch.finfo(sv.dtype).eps
    threshold=max(y.shape)*eps*float(sv.max())
    info={'scope':'independent gate replay on captured inputs, not an extra execution in public API',
          'Y_singular_values':sv.tolist(),'Y_threshold':threshold}
    if steps>0 and (error is None or error['stage']=='rank_cross'):
        q0=torch.linalg.qr(y,mode='reduced').Q;cross=z.mH@q0;values=torch.linalg.svdvals(cross)
        threshold=max(cross.shape)*eps*max(float(values.max()),float(z.norm()))
        info.update(first_cross_singular_values=values.tolist(),first_cross_threshold=threshold,
                    first_cross_min_over_threshold=float(values[-1])/threshold if threshold else None)
    return info


def audit_case(a,params,seed,label,max_condition=None):
    r,s,ell,d,steps=params;tol=TOL[a.dtype]
    args=dict(steps=steps,max_condition=max_condition)
    g=torch.Generator().manual_seed(seed)
    public,pub_out=capture(lambda:sketch_power_low_rank(a,r,s,ell,d,generator=g,**args),g)
    traces={};records={};outputs={}
    for mode in ('separate','concat_view','concat_copy'):
        trace={};g=torch.Generator().manual_seed(seed)
        rec,out=capture(lambda:prototype(a,r,s,ell,d,generator=g,mode=mode,trace=trace,**args),g,trace)
        rec['gate_diagnostics']=first_gate_diagnostics(trace,steps,rec['error'])
        traces[mode]=trace;records[mode]=rec;outputs[mode]=out
    replay=equivalent_records(public,records['separate'])
    if pub_out is not None and outputs['separate'] is not None:
        replay=replay and metrics((pub_out[0]*pub_out[1])@pub_out[2],(outputs['separate'][0]*outputs['separate'][1])@outputs['separate'][2],tol)['close']
    row={'case':label,'dtype':str(a.dtype),'shape':list(a.shape),'params':list(params),'seed':seed,'max_condition':max_condition,
         'A_sha256':digest(a),'tolerance':tol,'public_replay_verified':replay,'public':public,'paths':records,'comparisons':{},'status':'EQUIVALENT_IN_TEST'}
    for mode in ('concat_view','concat_copy'):
        comp={'semantic_equal':equivalent_records(public,records[mode]),'sketch_metrics':{}}
        baseline=traces['separate'];target=traces[mode]
        for k in ('Y','Z'):
            if k in baseline and k in target:comp['sketch_metrics'][k]=metrics(target[k],baseline[k],tol)
        comp['same_draws']=all(records[mode]['draws'][k]==records['separate']['draws'][k] for k in ('Omega','Phi','Psi'))
        comp['same_initial_draws']=all(records[mode]['draws'][k]==records['separate']['draws'][k] for k in ('Omega','Phi'))
        if 'Q' in baseline and 'Q' in target:comp['Q_projector']=metrics(target['Q']@target['Q'].mH,baseline['Q']@baseline['Q'].mH,tol)
        if pub_out is not None and outputs[mode] is not None:
            got=outputs[mode];ref=(pub_out[0]*pub_out[1])@pub_out[2];recon=(got[0]*got[1])@got[2]
            comp['reconstruction']=metrics(recon,ref,tol);comp['singular_values']=metrics(got[1],pub_out[1],tol)
            comp['residuals']={'public':float((a-ref).norm()),'candidate':float((a-recon).norm())}
        checks=[c['close'] for c in comp['sketch_metrics'].values()]
        checks += [comp[k]['close'] for k in ('Q_projector','reconstruction','singular_values') if k in comp]
        comp['equivalent_in_test']=comp['semantic_equal'] and comp['same_draws'] and all(checks)
        if not comp['equivalent_in_test']:row['status']='NOT_EQUIVALENT'
        row['comparisons'][mode]=comp
    if not replay:row['status']='AUDIT_REPLAY_FAIL'
    return row


def threshold_input(dtype,seed,kind,factor):
    # Deterministic adversarial construction; all execution paths still draw their own RNG.
    m,n=16,17
    s,ell=(4,7) if kind=='Y' else (1,3)
    g=torch.Generator().manual_seed(seed);omega=torch.randn(n,s,generator=g,dtype=dtype);phi=torch.randn(n,ell,generator=g,dtype=dtype)
    right=torch.cat((omega,phi),1);target=torch.zeros(m,s+ell,dtype=dtype);eps=torch.finfo(target.real.dtype).eps
    if kind=='Y':
        target[:s,:s]=torch.diag(torch.tensor([1.,.8,.6,m*eps*factor],dtype=dtype));target[:ell,s:]=torch.eye(ell,dtype=dtype);steps=0
    else:
        target[0,0]=1;target[1,1]=target[2,2]=target[3,3]=1
        target[0,1]=ell*eps*ell**.5*factor;steps=1
    return target@torch.linalg.pinv(right),(min(3,s),s,ell,max(4,s+2),steps)


def downstream_fixtures(dtype):
    rows=[];eps=torch.finfo(torch.empty((),dtype=dtype).real.dtype).eps
    for name,tiny in [('ill_conditioned',1e-4 if eps>1e-10 else 1e-10),('rank_C_zero',0.),('rank_C_below',2*eps*(1-8*eps)),('rank_C_at',2*eps),('rank_C_above',2*eps*(1+8*eps)),('nonorthogonal_Q',1.)]:
        q=torch.eye(4,2,dtype=dtype)
        if name=='nonorthogonal_Q':q[:,0]*=2
        psi=torch.zeros(2,4,dtype=dtype);psi[0,0]=1;psi[1,1]=tiny;w=psi@q@torch.ones(2,3,dtype=dtype)
        wide=torch.zeros(4,4,dtype=dtype);wide[:,::2]=q;noncontig=wide[:,::2]
        records=[]
        for value in (q,noncontig):
            rec,out=capture(lambda:reconstruct_from_corange(value,psi,w,1),None);records.append(rec)
        rows.append({'case':name,'dtype':str(dtype),'scope':'downstream fixtures only; not a synthesized random full-pipeline C',
                     'records':records,'status':'EQUIVALENT_IN_TEST' if equivalent_records(*records) else 'NOT_EQUIVALENT'})
    return rows


def invalid_generator_cases():
    class WrongDevice:device=torch.device('meta')
    a=torch.ones(8,8,dtype=torch.float64);rows=[]
    for g in ('not_a_generator',WrongDevice()):
        records=[]
        for mode in ('public','concat_view','concat_copy'):
            fn=(lambda:sketch_power_low_rank(a,1,2,3,4,steps=0,generator=g)) if mode=='public' else (lambda:prototype(a,1,2,3,4,steps=0,generator=g,mode=mode,trace={}))
            rec,_=capture(fn,g);records.append(rec)
        rows.append({'case':type(g).__name__,'records':records,'status':'EQUIVALENT_IN_TEST' if all(equivalent_records(records[0],x) for x in records[1:]) else 'NOT_EQUIVALENT'})
    return rows


def run(sha,out):
    torch.set_num_threads(1);repo=Path(__file__).resolve().parents[2];package=Path(torchsketchpower.__file__).parent
    identity={p.name:p.read_text()==(package/p.name).read_text() for p in (repo/'src/torchsketchpower').glob('*.py')}
    assert all(identity.values()),'unverified installed production source'
    report={'source_sha':sha,'status':'CPU_GATE_PASS','gpu':'NOT_RUN','cpu_torch':torch.__version__,'python':sys.version,
            'installed_package':str(package),'production_text_identity':identity,'cases':[],'downstream':[],'invalid_generators':[],
            'tolerances':{str(k):v for k,v in TOL.items()},'scope':'72 regular configurations, targeted adversarial cases; all CPU, no compiler/profiler',
            'base_main':'cdb1346072d062bc67fb52d36b26326772fa86af','sae_pin':'65338eb1aa67971e110db982a07cf43161c23446'}
    failures=[]
    def add(a,params,seed,label,max_condition=None):
        row=audit_case(a,params,seed,label,max_condition);report['cases'].append(row)
        if row['status']!='EQUIVALENT_IN_TEST':failures.append((a.clone(),row))
    for dt in DTYPES:
        for shape in ((48,24),(24,48),(32,32)):
            for steps in (0,1,2):
                for seed in (314,315):
                    a=torch.randn(*shape,generator=torch.Generator().manual_seed(123),dtype=dt)
                    add(a,(3,4,7,9,steps),seed,'regular')
        for steps in (0,2):
            for kind in ('zero_A','rank_one_A'):
                a=torch.zeros(16,17,dtype=dt)
                if kind=='rank_one_A':a[:,0]=1.
                add(a,(3,4,7,9,steps),314,kind)
        a=torch.randn(24,17,generator=torch.Generator().manual_seed(123),dtype=dt)
        add(a,(3,4,7,9,1),314,'forced_condition_warning',1.)
        for seed in (314,315):
            for kind,factors in [('Y',(.99,1.,1.01)),('cross',(.8,1.,1.2))]:
                for factor in factors:
                    a,params=threshold_input(dt,seed,kind,factor)
                    add(a,params,seed,f'near_{kind}_{factor}')
        report['downstream']+=downstream_fixtures(dt)
    report['invalid_generators']=invalid_generator_cases()
    report['failed_cases']=[{'index':i,'case':c['case'],'dtype':c['dtype'],'seed':c['seed'],'status':c['status']} for i,c in enumerate(report['cases']) if c['status']!='EQUIVALENT_IN_TEST']
    report['cpu_gate_pass']=not failures and all(x['status']=='EQUIVALENT_IN_TEST' for x in report['downstream']+report['invalid_generators'])
    if not report['cpu_gate_pass']:report['status']='CPU_GATE_FAIL / NOT_EQUIVALENT';report['gpu_reason']='Issue26 hard stop: any CPU semantic failure forbids allocation'
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    # Preserve exact realized input of the first semantic counterexample for independent replay.
    if failures:
        torch.save(failures[0][0],out/'first-failure-A.pt');report['first_failure_case']=failures[0][1]
        report['first_failure_A_file_sha256']=hashlib.sha256((out/'first-failure-A.pt').read_bytes()).hexdigest()
    raw=(json.dumps(report,indent=2,allow_nan=False)+'\n').encode();(out/'results.json').write_bytes(raw)
    manifest={'source_sha':sha,'status':report['status'],'files':{p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in out.iterdir() if p.is_file()}}
    (out/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode());return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-sha',required=True);p.add_argument('--out',required=True);args=p.parse_args();repo=Path(__file__).resolve().parents[2]
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()!=args.source_sha or subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True).strip():p.error('exact clean source required')
    report=run(args.source_sha,args.out);print(json.dumps({k:report[k] for k in ('source_sha','status','cpu_gate_pass','failed_cases','gpu')}))
