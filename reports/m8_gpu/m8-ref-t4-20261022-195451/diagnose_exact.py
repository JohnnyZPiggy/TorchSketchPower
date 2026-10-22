import sys,json,io,hashlib,torch,subprocess
from pathlib import Path
repo=Path(sys.argv[1]);root=Path(sys.argv[2]);sys.path.insert(0,str(repo/'experiments/m8_gpu'));import run_m8 as m
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip();torch.set_num_threads(1)
a=m.make_matrix(1024,512,'near_flat',seed=123).float();raw=io.BytesIO();torch.save(a,raw);raw=raw.getvalue();assert torch.equal(torch.load(io.BytesIO(raw),weights_only=True),a)
ref,meta=m.reference_spectrum(a,8);out=m.call_method(a,m.methods()[-1]);result=m.accuracy(a,out,ref)
old=json.loads((repo/'reports/m8_gpu/m8-t4-20261022-193439/results.json').read_bytes());old_cfg=next(c for c in old['configs'] if c['config_id']=='m10-cuda-4')
native_tail=float(torch.tensor(meta['native_reference_singular_values'],dtype=torch.float64)[8:].norm())
record={'source_sha':sha,'torch':torch.__version__,'shape':[1024,512],'dtype':'float32','seed':123,'rank':8,'serialized_sha256':hashlib.sha256(raw).hexdigest(),'tensor_bytes_sha256':hashlib.sha256(a.numpy().tobytes()).hexdigest(),'roundtrip_equal':True,'reference':meta,'accuracy':result,'cpu_native_tail':native_tail,'historical_failure':old_cfg,'historical_tensor_save_sha256':next(x for x in old['matrices'] if x['matrix_id']==10)['tensor_torch_save_sha256'],'historical_residual_over_cpu_double_tail_diagnostic_only':old_cfg['accuracy']['residual_fro2']**.5/meta['tail_svd_fro'],'decision':'SUPPORTED: double reference EY PASS; CPU native does not reproduce CUDA bias. Serialized hashes differ across torch/runtime; no cross-runtime bit identity claimed. Historical old failure immutable. Mathematical protocol references actual rounded A, not intended spectrum; one bounded completion attempt warranted.'}
assert result['status']=='PASS' and result['ey_ok'] and abs(meta['energy_tail_fro']/meta['tail_svd_fro']-1)<1e-12
(root/'diagnostic-actual-a.pt').write_bytes(raw);(root/'diagnostic-decision.json').write_text(json.dumps(record,indent=2));print(json.dumps({k:v for k,v in record.items() if k not in ('reference','accuracy','historical_failure')},indent=2))
