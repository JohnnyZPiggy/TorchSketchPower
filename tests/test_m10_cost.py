"""M10 bounded numerical identities/negative controls; CPU only, no installations."""
import importlib.util
from pathlib import Path
import pytest
import torch

p=Path(__file__).resolve().parents[1]/'experiments/m10_cost/run_m10.py'
spec=importlib.util.spec_from_file_location('m10',p);m10=importlib.util.module_from_spec(spec);spec.loader.exec_module(m10)


@pytest.mark.parametrize('dtype',m10.DTYPES)
def test_same_draw_concat_and_unchanged_rank_errors(dtype):
    torch.set_num_threads(1)
    for t in (0,1):
        result=m10.h1_case(dtype,t)
        assert result['status']=='PASS' and result['same_final_rng_state']
        assert not result['single_wide_draw_equals_separate_cat']
        assert result['YZ_contiguous']==[False,False]


@pytest.mark.parametrize('dtype',m10.DTYPES)
def test_rank_threshold_both_sides_and_exact_boundary(dtype):
    assert all(row['status']=='PASS' for row in m10.rank_cases(dtype))


@pytest.mark.parametrize('dtype',m10.DTYPES)
def test_rejected_reuse_normal_equations_and_nonorthogonal_Q(dtype):
    torch.set_num_threads(1);result=m10.counterexamples(dtype)
    tol=1e-4 if dtype in (torch.float32,torch.complex64) else 1e-10
    assert result['unseen_delta_Y_norm']<tol and result['unseen_delta_Z_norm']<tol
    assert result['changed_W_norm']>1
    assert 'IllConditionedWarning' in result['warnings']
    assert result['normal_equations']['exception'] is not None
    assert result['checked_lstsq_error']<tol
    assert result['isometric_svd_delta']<tol and result['skew_svd_delta']>.01
    assert result['skew_q_exception']=='ValueError'


def test_cost_conservation_and_not_physical_pass_claim():
    c=m10.cost(1024,512,8,16,32,32,1,4)
    assert c['gemm_total']==87818240 and c['gemm_calls']==8
    assert c['source_scalar_consumptions_success']==8 and c['qr_calls']==3
    assert c['A_logical_GEMM_operands']==3 and c['svdvals_calls']==3 and c['thin_svd_calls']==1
    assert c['H1_extra_concat_bytes']==98304 and c['H1_ideal_operand_traffic_saving_bytes']==1900544
    assert m10.cost(24,17,3,4,7,9,0,8)['source_scalar_consumptions_success']==6
    with pytest.raises(AssertionError):m10.cost(4,2,1,3,4,4,0,8)
