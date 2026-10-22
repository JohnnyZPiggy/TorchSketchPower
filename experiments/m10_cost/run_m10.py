"""M10 CPU-only cost/identity audit; no production edits, timing or installation."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import warnings

import torch
import torchsketchpower
from torchsketchpower import sketch_power_low_rank, sketch_power_subspace, reconstruct_from_corange, solve_corange_coefficient
from torchsketchpower.core import _numerical_rank

DTYPES=(torch.float32,torch.float64,torch.complex64,torch.complex128)


def cost(m,n,r,s,ell,d,t,b):
    assert 1<=r<=s<=min(m,n) and s<ell and d>=s and t>=0
    gemms={'Y':2*m*n*s,'Z':2*m*n*ell,'W':2*d*m*n,'power':4*t*m*ell*s,
           'Gram':2*m*s*s,'C':2*d*m*s,'U':2*m*s*r}
    qr=lambda a:4*a*s*s-4*s**3/3
    return {'shape':[m,n],'r':r,'s':s,'ell':ell,'d':d,'steps':t,'element_bytes':b,
            'convention':'real leading FLOPs, multiply/add each1, FMA2; not exact vendor work',
            'gemm_flops':gemms,'gemm_total':sum(gemms.values()),'gemm_calls':6+2*t,
            'qr_calls':1+2*t,'qr_with_explicit_q_leading_flops':qr(m)+t*(qr(ell)+qr(m)),
            'svdvals_calls':t+2,'thin_svd_calls':1,'lstsq_calls':1,
            'cuda_gels_householder_leading_model':2*d*s*s-2*s**3/3+4*d*s*n-s*s*n,
            'svdvals_shape_terms':{'Y':m*s*s,'cross_total':t*ell*s*s,'C':d*s*s},
            'B_svd_shape_term':n*s*s+s**3,
            'rng_tensor_entries':n*(s+ell)+d*m,'A_logical_GEMM_operands':3,
            'A_operand_bytes_no_cross_call_cache_model':3*m*n*b,
            'source_scalar_consumptions_success':2*t+6,
            'H1_extra_concat_bytes':n*(s+ell)*b,
            'H1_extra_concat_and_optional_output_repack_bytes':[n*(s+ell)*b,(n+m)*(s+ell)*b],
            'H1_ideal_operand_traffic_saving_bytes':b*n*(m-2*(s+ell)),
            'logical_elements':{'A':m*n,'Omega_Phi':n*(s+ell),'Y_Z':m*(s+ell),'Q':m*s,
                                'cross_middle_each':ell*s,'Psi':d*m,'W':d*n,'C':d*s,'Gram_R_each':s*s,
                                'B':s*n,'U_B':s*s,'Vh_backing':s*n,'U_output':m*r,'sigma_backing':s}}


def combined(a,s,ell,d,r,steps,seed=314):
    g=torch.Generator().manual_seed(seed);omega=torch.randn(a.shape[1],s,generator=g,dtype=a.dtype)
    phi=torch.randn(a.shape[1],ell,generator=g,dtype=a.dtype)
    yz=a@torch.cat((omega,phi),dim=1);y,z=yz[:,:s],yz[:,s:]
    q=sketch_power_subspace(y,z,steps=steps)  # unchanged checks BEFORE Psi draw
    psi=torch.randn(d,a.shape[0],generator=g,dtype=a.dtype);w=psi@a
    return reconstruct_from_corange(q,psi,w,r),g.get_state(),(y,z)


def approx(out):return (out[0]*out[1])@out[2]


def rank_tensor_threshold(a,scale=0.):
    values=torch.linalg.svdvals(a)
    threshold=max(a.shape)*torch.finfo(values.dtype).eps*torch.maximum(values.max(),values.new_tensor(scale))
    return int((values>threshold).sum())


def scalar_events(fn):
    with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU]) as p:fn()
    return {event.key:event.count for event in p.key_averages() if event.key in ('aten::_local_scalar_dense','aten::linalg_svdvals','aten::linalg_qr','aten::linalg_lstsq')}


def h1_case(dtype,steps):
    m,n,s,ell,d,r=24,17,4,7,9,3
    a=torch.randn(m,n,generator=torch.Generator().manual_seed(123),dtype=dtype)
    g=torch.Generator().manual_seed(314)
    baseline=sketch_power_low_rank(a,r,s,ell,d,steps=steps,generator=g)
    got,state,(y,z)=combined(a,s,ell,d,r,steps)
    delta=float((approx(got)-approx(baseline)).norm());refnorm=float(approx(baseline).norm())
    tol=1e-3 if dtype in (torch.float32,torch.complex64) else 1e-9
    independent=torch.Generator().manual_seed(314)
    omega=torch.randn(n,s,generator=independent,dtype=dtype);phi=torch.randn(n,ell,generator=independent,dtype=dtype)
    rng=torch.Generator().manual_seed(314);wide=torch.randn(n,s+ell,generator=rng,dtype=dtype)
    same_draws=torch.equal(wide,torch.cat((omega,phi),dim=1))
    zero=[]
    for fn in ('public','combined'):
        try:
            if fn=='public':sketch_power_low_rank(torch.zeros_like(a),r,s,ell,d,steps=steps,generator=torch.Generator().manual_seed(314))
            else:combined(torch.zeros_like(a),s,ell,d,r,steps)
            zero.append(None)
        except Exception as exc:zero.append(type(exc).__name__)
    return {'dtype':str(dtype),'steps':steps,'status':'PASS' if delta<=tol*max(1,refnorm) and torch.equal(state,g.get_state()) and zero==['RankDeficiencyError']*2 else 'FAIL',
            'reconstruction_delta':delta,'limit':tol*max(1,refnorm),'baseline_residual':float((a-approx(baseline)).norm()),'combined_residual':float((a-approx(got)).norm()),
            'same_final_rng_state':torch.equal(state,g.get_state()),'single_wide_draw_equals_separate_cat':same_draws,
            'single_wide_draw_same_rng_state':torch.equal(rng.get_state(),independent.get_state()),
            'YZ_bitwise_equal':[torch.equal(y,a@omega),torch.equal(z,a@phi)],'YZ_strides':[list(y.stride()),list(z.stride())],
            'YZ_contiguous':[y.is_contiguous(),z.is_contiguous()],'zero_A_errors':zero}


def rank_cases(dtype):
    real=torch.float32 if dtype in (torch.float32,torch.complex64) else torch.float64
    eps=torch.finfo(real).eps;rows=[]
    for scale in (0.,2.):
        threshold=4*eps*max(1.,scale)
        for factor in (0.,1-8*eps,1.,1+8*eps):
            a=torch.diag(torch.tensor([1.,threshold*factor,0.,0.],dtype=dtype))
            old=_numerical_rank(a,scale);new=rank_tensor_threshold(a,scale)
            rows.append({'dtype':str(dtype),'scale':scale,'boundary_factor':factor,'old_rank':old,'new_rank':new,'status':'PASS' if old==new else 'FAIL'})
    return rows


def counterexamples(dtype):
    # Same Y,Z do not in general determine an independent left sketch W.
    g=torch.Generator().manual_seed(9);omega=torch.randn(19,3,generator=g,dtype=dtype);phi=torch.randn(19,5,generator=g,dtype=dtype)
    v=torch.linalg.qr(torch.cat((omega,phi),1),mode='complete').Q[:,-1]
    u=torch.ones(20,1,dtype=dtype);delta=u@v.conj().unsqueeze(0)
    psi=torch.randn(9,20,generator=g,dtype=dtype)
    # Full-rank C with nearly parallel columns; normal equations square conditioning.
    small=1e-4 if dtype in (torch.float32,torch.complex64) else 1e-10
    c=torch.tensor([[1.,1.],[small,-small]],dtype=dtype);q=torch.eye(4,2,dtype=dtype)
    p=torch.zeros(2,4,dtype=dtype);p[:,:2]=c;expected=torch.ones(2,3,dtype=dtype);w=c@expected
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter('always');solution=solve_corange_coefficient(q,p,w)
    try:
        normal=torch.linalg.solve(c.mH@c,c.mH@w);normal_result={'exception':None,'error':float((normal-expected).norm())}
    except Exception as exc:normal_result={'exception':type(exc).__name__,'message':str(exc)}
    # Existing small SVD identity depends on orthogonality; a skew Q breaks it.
    b=torch.randn(2,6,generator=g,dtype=dtype);skew=q.clone();skew[:,0]*=2
    svdb=torch.linalg.svdvals(b);goodsvd=torch.linalg.svdvals(q@b)[:2];badsvd=torch.linalg.svdvals(skew@b)[:2]
    try:solve_corange_coefficient(skew,p,w);skew_error=None
    except Exception as exc:skew_error=type(exc).__name__
    return {'dtype':str(dtype),'unseen_delta_Y_norm':float((delta@omega).norm()),'unseen_delta_Z_norm':float((delta@phi).norm()),'changed_W_norm':float((psi@delta).norm()),
            'condition_C':float(torch.linalg.cond(c)),'checked_lstsq_error':float((solution-expected).norm()),'warnings':[x.category.__name__ for x in ws],
            'normal_equations':normal_result,'isometric_svd_delta':float((svdb-goodsvd).norm()),'skew_svd_delta':float((svdb-badsvd).norm()),'skew_q_exception':skew_error}


def evidence(repo):
    paths=['reports/m7_cuda/m7-t4-20261022-185647/m7-cuda-report.json','reports/m8_gpu/m8-t4-20261022-193439/results.json',
           'reports/m8_gpu/m8-ref-t4-20261022-195451/results.json','reports/m9_compile/m9-t4-20261022-204314/cpu-results.json',
           'reports/m9_compile/m9-t4-20261022-204314/gpu-results.json']
    rows=[]
    for name in paths:
        raw=(repo/name).read_bytes();data=json.loads(raw);row={'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'source_sha':data['source_sha'],'historical_status':data['status']}
        if 'configs' in data:
            sm={x['config_id']:x for x in data['summaries']};complete=[c for c in data['configs'] if c['device']=='cuda' and c['method']=='spi' and sm[c['config_id']]['n_warm']==3 and c['status']=='PASS'];advantage=0
            for c in complete:
                ref=next(x for x in data['configs'] if x['matrix_id']==c['matrix_id'] and x['device']=='cuda' and x['method']=='svd_lowrank' and x['niter']==1)
                advantage+=sm[ref['config_id']]['wall_median_ms']<sm[c['config_id']]['wall_median_ms'] and ref['accuracy']['fro_ratio']<=c['accuracy']['fro_ratio']
            row.update(completed_configs=data['completed_configs'],planned_configs=data['planned_configs'],native_niter1_advantage_pairs=int(advantage),completed_gpu_spi_pairs=len(complete),failed_configs=[c['config_id'] for c in data['configs'] if c['status']=='FAIL'])
        if 'cases' in data:row['classes']=dict(collections.Counter(c['classification'] for c in data['cases']))
        rows.append(row)
    return rows


def run(repo,sha):
    torch.set_num_threads(1)
    result={'source_sha':sha,'status':'CPU_RESEARCH_ONLY','torch':torch.__version__,'python':sys.version,'threads':1,
            'base_main':'345ee660bd1baed2c7a9c5ae7c58ec45f6feff93','sae_pin':'65338eb1aa67971e110db982a07cf43161c23446',
            'gpu':'NOT RUN','colab_cli':'NOT RUN','install_changes':'NONE; reused CPU environment',
            'evidence':evidence(repo),'h1':[h1_case(dt,t) for dt in DTYPES for t in (0,1)],
            'h2':[row for dt in DTYPES for row in rank_cases(dt)],'counterexamples':[counterexamples(dt) for dt in DTYPES],
            'cost_examples':[cost(m,n,8,16,32,32,t,b) for m,n in ((256,128),(1024,512),(2048,1024)) for t in (0,1) for b in (4,8)]}
    a=torch.randn(24,17,generator=torch.Generator().manual_seed(123),dtype=torch.float64)
    result['cpu_ATen_events']={str(t):scalar_events(lambda:sketch_power_low_rank(a,3,4,7,9,steps=t,generator=torch.Generator().manual_seed(314))) for t in (0,1)}
    diag=torch.eye(4,dtype=torch.float64)
    result['h2_cpu_ATen_events']={'original':scalar_events(lambda:_numerical_rank(diag,2.)),'tensor_threshold':scalar_events(lambda:rank_tensor_threshold(diag,2.)),'svdvals_only':scalar_events(lambda:torch.linalg.svdvals(diag))}
    result['cpu_profiler_scope']='CPU counts include library checks; not exact CUDA barrier counts or latency. Source-level consumers modeled separately.'
    package=Path(torchsketchpower.__file__).parent
    result['production_text_identity']={p.name:(p.read_text()==(package/p.name).read_text()) for p in (repo/'src/torchsketchpower').glob('*.py')}
    assert all(result['production_text_identity'].values()),'reused installed source differs'
    assert all(c['status']=='PASS' for c in result['h1']+result['h2'])
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-sha',required=True);p.add_argument('--out',required=True);args=p.parse_args();repo=Path(__file__).resolve().parents[2]
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()!=args.source_sha or subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True).strip():p.error('exact clean source required')
    result=run(repo,args.source_sha);out=Path(args.out);out.mkdir(parents=True,exist_ok=False);raw=(json.dumps(result,indent=2,allow_nan=False)+'\n').encode();(out/'observations.json').write_bytes(raw)
    (out/'manifest.json').write_bytes((json.dumps({'source_sha':args.source_sha,'files':{'observations.json':{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}}},indent=2)+'\n').encode())
    print(json.dumps({'status':result['status'],'h1_cases':len(result['h1']),'h2_cases':len(result['h2']),'cpu_ATen_events':result['cpu_ATen_events'],'h2_cpu_ATen_events':result['h2_cpu_ATen_events']}))
