"""M9 experiment contracts; no codegen toolchain or GPU required for unit checks."""
import importlib.util
import json
from pathlib import Path
import sys
import pytest
import torch

p=Path(__file__).resolve().parents[1]/'experiments/m9_compile/run_m9.py'
spec=importlib.util.spec_from_file_location('m9',p);m9=importlib.util.module_from_spec(spec);spec.loader.exec_module(m9)

@pytest.mark.parametrize('dtype',[torch.float32,torch.float64])
@pytest.mark.parametrize('steps',[0,1])
def test_fixed_sketches_pair_with_public_rng_and_keep_rank_checks(dtype,steps):
    a,sk=m9.inputs(dtype,'cpu',32,24)
    public=m9.sketch_power_low_rank(a,3,6,8,10,steps=steps,generator=torch.Generator().manual_seed(m9.SEED))
    assert m9.compare(a,m9.pipeline(a,sk,steps),public)['status']=='SUPPORTED'
    with pytest.raises(m9.RankDeficiencyError):m9.pipeline(torch.zeros_like(a),sk,steps)


def test_comparison_rejects_nonfinite_and_wrong_reconstruction():
    a,sk=m9.inputs(torch.float64,'cpu',32,24);out=m9.pipeline(a,sk,1)
    bad=(out[0],out[1]*0,out[2]);assert m9.compare(a,bad,out)['status']=='CORRECTNESS_FAIL'
    assert m9.compare(a,(out[0]*float('nan'),out[1],out[2]),out)['status']=='CORRECTNESS_FAIL'


def test_expected_compile_failure_retains_full_exception_and_cost(monkeypatch):
    def compile_fn(*a,**kw):
        def bad(*a,**kw):raise RuntimeError('retained compiler failure')
        return bad
    monkeypatch.setattr(torch,'compile',compile_fn)
    c=next(x for x in m9.plan() if x['kind']=='helper')
    result=m9.worker(c,'cpu')
    assert result['classification']=='UNSUPPORTED' and result['failed_attempt_wall_ms']>=0
    assert 'retained compiler failure' in result['exceptions'][0] and 'Traceback' in result['exceptions'][0]


def test_bounded_plan_and_deadline_marks_not_run(tmp_path):
    assert len(m9.plan())==11 and all(c['steps'] in (0,1) for c in m9.plan())
    report=m9.run(tmp_path/'out','a'*40,max_seconds=-1)
    assert len(report['cases'])==11 and all(c['classification']=='NOT_RUN' for c in report['cases'])
    assert not report['cpu_justifies_gpu']
    manifest=json.loads((tmp_path/'out/manifest.json').read_bytes())
    import hashlib
    for name,value in manifest['files'].items():assert hashlib.sha256((tmp_path/'out'/name).read_bytes()).hexdigest()==value['sha256']


def test_m9_driver_invalid_sha_is_offline_and_manifest_matches(monkeypatch,tmp_path):
    spec=importlib.util.spec_from_file_location('m9driver',p.parent/'colab_driver.py')
    driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
    monkeypatch.setattr(driver,'WORK',tmp_path);monkeypatch.setattr(driver,'SHA','invalid')
    driver.main();result=json.loads((tmp_path/driver.NAME).read_bytes())
    assert result['benchmark_status']=='BLOCKED' and not result['logs']
    assert 'invalid source SHA' in result['exceptions'][0]
    assert json.loads((p.parent/'artifacts.json').read_bytes())=={'artifacts':[{'name':driver.NAME}]}
