"""M11 bounded semantic regression and negative-result retention; CPU only."""
import copy
import importlib.util
from pathlib import Path
import pytest
import torch

p=Path(__file__).resolve().parents[1]/'experiments/m11_concat/run_m11.py'
spec=importlib.util.spec_from_file_location('m11',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


@pytest.mark.parametrize('dtype',m.DTYPES)
@pytest.mark.parametrize('steps',[0,1,2])
def test_regular_public_replay_and_two_concat_layouts(dtype,steps):
    torch.set_num_threads(1);a=torch.randn(48,24,dtype=dtype,generator=torch.Generator().manual_seed(123))
    row=m.audit_case(a,(3,4,7,9,steps),314,'unit_regular')
    assert row['public_replay_verified'] and row['status']=='EQUIVALENT_IN_TEST'
    assert row['paths']['concat_view']['Y_Z_share_backing']
    assert not row['paths']['concat_copy']['Y_Z_share_backing']
    assert row['paths']['concat_view']['intermediates']['Y']['stride']==[11,1]
    assert row['paths']['concat_copy']['intermediates']['Y']['contiguous']
    assert row['paths']['concat_copy']['copy_payload_bytes']['output_repack']==48*11*a.element_size()


@pytest.mark.parametrize('dtype',m.DTYPES)
def test_failure_keeps_two_draws_but_does_not_draw_Psi(dtype):
    a=torch.zeros(16,17,dtype=dtype);row=m.audit_case(a,(3,4,7,9,2),314,'zero')
    assert row['status']=='EQUIVALENT_IN_TEST'
    expected=torch.Generator().manual_seed(314)
    torch.randn(17,4,dtype=dtype,generator=expected);torch.randn(17,7,dtype=dtype,generator=expected)
    assert row['public']['rng_after']==m.digest(expected.get_state())
    for result in row['paths'].values():
        assert result['error']['stage']=='rank_Y' and result['error']['class']=='RankDeficiencyError'
        assert result['draws']['Psi'] is None and result['rng_after']==row['public']['rng_after']


def test_branch_or_rng_or_warning_difference_never_counts_as_equivalent():
    a=torch.zeros(16,17,dtype=torch.float64);row=m.audit_case(a,(3,4,7,9,0),314,'zero')
    ref=row['public'];changed=copy.deepcopy(ref);changed['rng_after']='different'
    assert not m.equivalent_records(ref,changed)
    changed=copy.deepcopy(ref);changed['error']['message']='different first failure'
    assert not m.equivalent_records(ref,changed)
    changed=copy.deepcopy(ref);changed['warnings']=[{'class':'IllConditionedWarning','message':'retained warning'}]
    assert not m.equivalent_records(ref,changed)


def test_near_threshold_records_raw_semantics_without_relaxing_gate():
    a,params=m.threshold_input(torch.float32,315,'cross',1.)
    row=m.audit_case(a,params,315,'near_cross')
    assert row['public_replay_verified']
    for mode,comp in row['comparisons'].items():
        if not comp['semantic_equal']:
            assert row['status']=='NOT_EQUIVALENT'
            assert not comp['equivalent_in_test']
            assert row['paths'][mode]['error']!=row['public']['error'] or row['paths'][mode]['rng_after']!=row['public']['rng_after'] or row['paths'][mode]['warnings']!=row['public']['warnings']


@pytest.mark.parametrize('dtype',m.DTYPES)
def test_corange_rank_condition_and_nonorthogonal_fixtures(dtype):
    rows=m.downstream_fixtures(dtype);assert len(rows)==6 and all(r['status']=='EQUIVALENT_IN_TEST' for r in rows)
    ill=rows[0]['records'][0];assert ill['error'] is None and any(w['class']=='IllConditionedWarning' for w in ill['warnings'])
    assert rows[1]['records'][0]['error']['stage']=='rank_C'
    assert rows[-1]['records'][0]['error']['stage']=='Gram_Q'


def test_invalid_generators_fail_before_any_global_rng_change():
    rows=m.invalid_generator_cases();assert len(rows)==2 and all(r['status']=='EQUIVALENT_IN_TEST' for r in rows)
    assert all(rec['global_rng_unchanged'] and rec['error'] is not None for row in rows for rec in row['records'])
