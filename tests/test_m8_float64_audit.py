"""Deterministic controls for proposed CPU dense-SVD audit; no GPU allocation."""
import sys
from pathlib import Path
import math
import pytest
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments/m8_gpu'))
import diagnose_float64 as d


def test_gamma_is_dimension_based():
    u=torch.finfo(torch.float64).eps/2
    assert d.gamma(1024)==1024*u/(1-1024*u)
    assert d.gamma(2048)>d.gamma(1024)


def test_uncertainty_cannot_be_broadened_into_pass():
    assert d.classify_dense(1,1.01,1e-10,2)=='FAIL'
    assert d.classify_dense(1,1.01,.1,2)=='INCONCLUSIVE'
    assert d.classify_dense(1,1,math.inf,2)=='INCONCLUSIVE'
    assert d.classify_dense(float('nan'),1,1e-12,2)=='FAIL'
    assert d.classify_dense(1,1,1e-12,2,False)=='FAIL'


def test_exact_spectrum_and_materially_wrong_dense_candidate():
    a=torch.diag(torch.tensor([4.,3.,2.,1.],dtype=torch.float64))
    u,s,vh=torch.linalg.svd(a);full=(u,s,vh);f=(u[:,:1],s[:1],vh[:1])
    result=d.audit(a,f,s,full)
    assert result['status']=='CONSISTENT_WITH_ROUNDOFF'
    wrong=d.audit(a,(u[:,:1],s[:1]*0,vh[:1]),s,full)
    assert wrong['status']=='FAIL' and abs(wrong['signed_gap'])>wrong['uncertainty_fro']
    assert d.audit(a,f,s*1.01,full)['status']=='INCONCLUSIVE'
    badu=u.clone();badu[:,0]*=2
    assert d.audit(a,(badu[:,:1],s[:1],vh[:1]),s,full)['status']=='FAIL'
    # Compensating S preserves reconstruction but must not hide nonorthogonal factors.
    assert d.audit(a,(u[:,:1]*1.1,s[:1]/1.1,vh[:1]),s,full)['status']=='FAIL'
    nan=s.clone();nan[0]=float('nan')
    assert d.audit(a,(u[:,:1],nan[:1],vh[:1]),s,full)['status']=='FAIL'


def test_audit_rejects_other_device_dtype_scope():
    with pytest.raises(ValueError,match='CPU real float64'):
        d.audit(torch.eye(2),None,None,None)
