"""Offline M8 benchmark contracts, numerical accuracy and failure handling."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import warnings

import pytest
import torch

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/'experiments/m8_gpu'))
import run_m8 as m8


def test_bounded_preregistered_grid():
    plan=m8.matrix_plan()
    assert len(plan)==14 and len(set(plan))==14
    assert {x[:2] for x in plan}=={(256,128),(1024,512),(2048,1024)}
    report=m8.run('cpu',True,'a'*40,max_seconds=-1)
    assert report['status']=='BLOCKED' and report['completed_configs']==0
    assert len(m8.methods())*len(plan)+2*len(m8.methods())==80
    assert m8.REPEATS==3 and m8.WARMUP==1 and m8.TIERS==(1.1,1.5)
    assert {c['steps'] for c in m8.methods() if c['method']=='spi'}=={0,1}
    assert {c['niter'] for c in m8.methods() if c['method']=='svd_lowrank'}=={0,1}


@pytest.mark.parametrize('spectrum',['geometric','polynomial','near_flat'])
def test_seeded_matrix_and_spectrum(spectrum):
    a=m8.make_matrix(24,16,spectrum)
    assert torch.equal(a,m8.make_matrix(24,16,spectrum))
    assert not torch.equal(a,m8.make_matrix(24,16,spectrum,seed=124))
    values=torch.linalg.svdvals(a)
    assert float(values[0])==pytest.approx(1.)
    expected={'geometric':1e-4,'polynomial':1/16,'near_flat':.95}[spectrum]
    assert float(values[-1])==pytest.approx(expected)


@pytest.mark.parametrize('dtype',[torch.float32,torch.float64])
@pytest.mark.parametrize('shape',[(24,16),(16,24)])
def test_all_baselines_accuracy_orientation_and_replay(dtype,shape):
    a=m8.make_matrix(*shape,'polynomial').to(dtype)
    ref=torch.linalg.svdvals(a)
    for cfg in m8.methods(True):
        out=m8.call_method(a,cfg)
        replay=m8.call_method(a,cfg)
        assert out[0].shape==(shape[0],2) and out[1].shape==(2,) and out[2].shape==(2,shape[1])
        torch.testing.assert_close(out[0].mH@out[0],torch.eye(2,dtype=dtype),atol=1e-5,rtol=1e-5)
        torch.testing.assert_close(out[2]@out[2].mH,torch.eye(2,dtype=dtype),atol=1e-5,rtol=1e-5)
        torch.testing.assert_close((out[0]*out[1])@out[2],(replay[0]*replay[1])@replay[2])
        result=m8.accuracy(a,out,ref)
        assert result['status']=='PASS' and result['ey_ok'] and result['svd_fro_audit']<1e-3
        assert result['rel_fro']>=0 and result['rel_spectral']>=0
        assert len(result['residual_singular_values'])==min(shape)
        if cfg['method']=='dense_svd':
            assert result['fro_ratio']==pytest.approx(1.,rel=1e-5)
            assert result['spectral_ratio']==pytest.approx(1.,rel=1e-5)


def test_svd_lowrank_public_mapping(monkeypatch):
    seen=[]
    def low(a,**kwargs):
        seen.append(kwargs)
        u,s,vh=torch.linalg.svd(a,full_matrices=False)
        return u,s,vh.mH
    monkeypatch.setattr(torch,'svd_lowrank',low)
    a=m8.make_matrix(24,16,'geometric')
    cfg=next(c for c in m8.methods(True) if c['method']=='svd_lowrank' and c['niter']==1)
    u,s,vh=m8.call_method(a,cfg)
    assert seen==[{'q':4,'niter':1}] and vh.shape==(2,16)
    assert m8.accuracy(a,(u,s,vh),torch.linalg.svdvals(a))['fro_ratio']==pytest.approx(1.)


def test_cuda_timing_and_allocator_order(monkeypatch):
    calls=[]
    class Event:
        def __init__(self,**kwargs):assert kwargs=={'enable_timing':True}
        def record(self):calls.append('record')
        def elapsed_time(self,other):calls.append('elapsed');return 1.25
    monkeypatch.setattr(torch.cuda,'Event',Event)
    monkeypatch.setattr(torch.cuda,'synchronize',lambda:calls.append('sync'))
    monkeypatch.setattr(torch.cuda,'reset_peak_memory_stats',lambda:calls.append('reset'))
    for name,value in [('memory_allocated',10),('memory_reserved',20),('max_memory_allocated',40),('max_memory_reserved',60)]:
        monkeypatch.setattr(torch.cuda,name,lambda value=value:value)
    out,t=m8.timed_call(lambda:(calls.append('call'),123)[1],torch.device('cuda'))
    assert calls==['sync','reset','record','call','record','sync','elapsed']
    assert out==123 and t['status']=='PASS' and t['event_ms']==1.25 and t['wall_ms']>=0
    assert t['memory']=={'allocated_before':10,'reserved_before':20,'peak_allocated':40,'peak_reserved':60,'delta_peak_allocated':30,'delta_peak_reserved':40}


def test_full_exception_and_warning_are_retained():
    def bad():
        warnings.warn('warning retained')
        raise RuntimeError('complete failure payload')
    out,t=m8.timed_call(bad,torch.device('cpu'))
    assert out is None and t['status']=='FAIL' and t['event_ms'] is None and t['memory'] is None
    assert 'RuntimeError: complete failure payload' in t['exception'] and 'Traceback' in t['exception']
    assert t['warnings']==[{'type':'UserWarning','message':'warning retained'}]


def test_method_failure_stops_without_retry(monkeypatch):
    calls=[]
    def bad(a,cfg):
        calls.append(cfg)
        raise RuntimeError('original failure, no retry')
    monkeypatch.setattr(m8,'call_method',bad)
    r=m8.run('cpu',True,'b'*40)
    assert r['status']=='BLOCKED' and len(calls)==1 and r['completed_configs']==0
    assert 'original failure, no retry' in r['trials'][0]['exception']
    assert any(c['status']=='NOT_RUN' for c in r['configs'])


def test_cpu_smoke_schema_checkpoint_and_hashes(tmp_path):
    cp=tmp_path/'checkpoint.json'
    r=m8.run('cpu',True,'b'*40,checkpoint=cp)
    assert r['status']=='DRY_RUN_CPU' and not r['gpu_evidence']
    assert r['completed_configs']==r['planned_configs']==5 and len(r['trials'])==25
    assert len(json.loads(cp.read_text())['trials'])==25
    assert all(t['event_ms'] is None and t['memory'] is None for t in r['trials'])
    assert all(s['n_warm']==3 for s in r['summaries'])
    out=tmp_path/'report';manifest=m8.write_report(r,out)
    for name,meta in manifest['files'].items():
        raw=(out/name).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==meta['sha256'] and len(raw)==meta['bytes']
    reconstructed=json.dumps(json.loads((out/'results.json').read_bytes()),separators=(',',':'),allow_nan=False).encode()
    assert hashlib.sha256(reconstructed).hexdigest()==manifest['files']['results.json']['sha256']
    assert len((out/'trials.csv').read_text().splitlines())==26
    assert json.loads((out/'manifest.json').read_text())['source_sha']=='b'*40


def test_quality_tier_can_have_no_eligible_method():
    c={'config_id':'x','matrix_id':0,'device':'cpu','status':'PASS','accuracy':{'fro_ratio':2.}}
    trials=[{'config_id':'x','phase':'warm','status':'PASS','wall_ms':float(x),'event_ms':None,'memory':None} for x in (1,2,3)]
    summary,comparisons=m8.summarize([c],trials)
    assert summary[0]['wall_median_ms']==2 and summary[0]['wall_iqr_ms']==1
    assert all(x['eligible']==[] and x['fastest'] is None for x in comparisons)


def test_cpu_only_device_missing_is_explicit(monkeypatch):
    monkeypatch.setattr(torch.cuda,'is_available',lambda:False)
    r=m8.run('cuda',True,'b'*40)
    assert r['status']=='BLOCKED' and r['trials']==[] and not r['gpu_evidence']


def test_cli_rejects_wrong_source_sha_before_measurement(tmp_path):
    p=subprocess.run([sys.executable,str(HERE/'experiments/m8_gpu/run_m8.py'),'--source-sha','0'*40,'--device','cpu','--smoke','--out',str(tmp_path/'out')],capture_output=True,text=True,timeout=20)
    assert p.returncode!=0 and 'source SHA mismatch' in p.stderr and not (tmp_path/'out').exists()


def test_driver_manifest_and_invalid_sha_failure_are_offline(monkeypatch,tmp_path):
    spec=importlib.util.spec_from_file_location('m8_driver',HERE/'experiments/m8_gpu/colab_driver.py')
    d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
    manifest=json.loads((HERE/'experiments/m8_gpu/artifacts.json').read_text())
    assert manifest=={'artifacts':[{'name':d.NAME}]}
    monkeypatch.setattr(d,'WORK',tmp_path);monkeypatch.setattr(d,'SHA','invalid')
    d.main();report=json.loads((tmp_path/d.NAME).read_bytes())
    assert report['benchmark_status']=='BLOCKED' and report['logs']==[]
    assert 'invalid source SHA' in report['exceptions'][0]


def test_driver_correctness_gate_failure_prevents_benchmark(monkeypatch,tmp_path):
    spec=importlib.util.spec_from_file_location('m8_driver_gate',HERE/'experiments/m8_gpu/colab_driver.py')
    d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
    monkeypatch.setattr(d,'WORK',tmp_path);monkeypatch.setattr(d,'SHA','a'*40)
    helper=SimpleNamespace(install_project=lambda repo,env:{'verified':True})
    monkeypatch.setattr(d.importlib.util,'spec_from_file_location',lambda *a:SimpleNamespace(loader=SimpleNamespace(exec_module=lambda m:None)))
    monkeypatch.setattr(d.importlib.util,'module_from_spec',lambda s:helper)
    calls=[]
    def execute(args,**kwargs):
        calls.append(args)
        if 'experiments/m7_cuda/run_m7_cuda.py' in args:
            gate=tmp_path/'m8_gate';gate.mkdir()
            (gate/'results.json').write_text(json.dumps({'status':'FAIL','plan_complete':False,'source_sha_verified':True}))
            return SimpleNamespace(returncode=1,stdout='gate failed',stderr='complete gate exception')
        return SimpleNamespace(returncode=0,stdout='a'*40 if 'rev-parse' in args else '',stderr='')
    monkeypatch.setattr(d.subprocess,'run',execute)
    d.main();r=json.loads((tmp_path/d.NAME).read_bytes())
    assert r['benchmark_status']=='BLOCKED' and 'benchmark' not in r and r['correctness_gate']['status']=='FAIL'
    assert not any('experiments/m8_gpu/run_m8.py' in cmd for cmd in calls)
    assert r['logs'][-1]['stderr']=='complete gate exception'
