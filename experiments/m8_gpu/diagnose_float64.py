"""CPU-only proposed dense-SVD audit; does not change the M8 acceptance gate."""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import sys

import torch
from run_m8 import make_matrix


def gamma(k):
    u = torch.finfo(torch.float64).eps / 2
    return k * u / (1 - k * u) if k * u < 1 else math.inf


def norm(x):
    return float(torch.linalg.vector_norm(x))


def norm_error(x):
    # Conservative sequential sum-of-squares/sqrt model, not a fitted SVD constant.
    g = gamma(x.numel() + 2)
    return g * norm(x) / (1 - g) if g < 1 else math.inf


def formation_error(u, s, vh, residual):
    scaled = u * s
    return ((gamma(len(s)) + gamma(1)) * (norm(scaled) + norm_error(scaled)) * (norm(vh) + norm_error(vh))
            + gamma(1) * (norm(residual) + norm_error(residual)) + norm_error(residual))


def orthogonal_distance_bound(q):
    gram = q.T @ q
    delta = gram - torch.eye(q.shape[1], dtype=q.dtype)
    defect = norm(delta)
    bound = (defect + gamma(q.shape[0]) * (norm(q) + norm_error(q)) ** 2
             + gamma(1) * (norm(gram) + math.sqrt(q.shape[1])) + norm_error(delta))
    # Polar-factor distance: |sqrt(lambda)-1| = |lambda-1|/(sqrt(lambda)+1).
    distance = bound / (1 + math.sqrt(1 - bound)) if bound < 1 else math.inf
    return distance, {"observed_gram_defect_fro": defect, "gram_defect_upper_model": bound,
                      "distance_to_orthonormal_upper_model": distance}


def classify_dense(residual, optimum, uncertainty, a_norm, valid=True):
    if not valid or not all(math.isfinite(x) for x in (residual, optimum, a_norm)) or min(residual, optimum) < 0:
        return "FAIL"
    # Resolution requirement: retain at least half the float64 significant digits.
    if not math.isfinite(uncertainty) or uncertainty < 0 or uncertainty > math.sqrt(torch.finfo(torch.float64).eps / 2) * a_norm:
        return "INCONCLUSIVE"
    if abs(residual - optimum) > uncertainty:
        return "FAIL"
    return "CONSISTENT_WITH_ROUNDOFF"  # Neither a scientific PASS nor full-grid completion.


def audit(a, factors, reference_s, full_factors):
    if a.device.type != 'cpu' or a.dtype != torch.float64:
        raise ValueError('diagnostic supports CPU real float64 only')
    all_values = (a, *factors, reference_s, *full_factors)
    if any(x.dtype != torch.float64 or x.device.type != 'cpu' for x in all_values):
        raise ValueError('diagnostic supports CPU real float64 only')
    if not all(bool(torch.isfinite(x).all()) for x in all_values):
        return {"status": "FAIL", "reason": "nonfinite data"}
    r = len(factors[1]);u, s, vh = full_factors
    residual = a - (factors[0] * factors[1]) @ factors[2]
    full_residual = a - (u * s) @ vh
    du, mu = orthogonal_distance_bound(u);dv, mv = orthogonal_distance_bound(vh.T)
    # B=USV^T is close to Q_U S Q_V^T, whose singular values are exactly s.
    polar_error = float(s[0]) * (du * (norm(vh) + norm_error(vh)) + dv)
    backward = norm(full_residual)
    beta = backward + formation_error(u, s, vh, full_residual) + polar_error
    tail = norm(reference_s[r:]);full_tail = norm(s[r:])
    # Distance to the rank-r set is 1-Lipschitz in Frobenius norm (triangle inequality).
    ref_uncertainty = beta + abs(tail - full_tail) + norm_error(s[r:]) + norm_error(reference_s[r:])
    candidate_uncertainty = formation_error(*factors, residual)
    uncertainty = ref_uncertainty + candidate_uncertainty
    cu, cmu = orthogonal_distance_bound(factors[0]);cv, cmv = orthogonal_distance_bound(factors[2].T)
    sorted_nonnegative = bool((s >= 0).all() and (s[:-1] >= s[1:]).all() and (reference_s >= 0).all() and (reference_s[:-1] >= reference_s[1:]).all())
    valid = (sorted_nonnegative and len(s) == min(a.shape) and r < len(s)
             and factors[0].shape == (a.shape[0], r) and factors[2].shape == (r, a.shape[1])
             and math.isfinite(cu + cv) and cmu['gram_defect_upper_model'] <= math.sqrt(torch.finfo(a.dtype).eps / 2)
             and cmv['gram_defect_upper_model'] <= math.sqrt(torch.finfo(a.dtype).eps / 2))
    # Underflow/overflow invalidate the standard relative-error model rather than pass.
    normal_model = all(not bool(((x.abs() > 0) & (x.abs() < math.sqrt(torch.finfo(x.dtype).tiny))).any()) for x in all_values)
    status = classify_dense(norm(residual), tail, uncertainty if normal_model else math.inf, norm(a), valid)
    return {"status": status, "scope": "proposed CPU dense-optimality audit only; not historical reclassification",
            "model": "real float64 standard arithmetic; gamma_k=k*u/(1-k*u), u=eps/2; no underflow/overflow",
            "residual_fro": norm(residual), "reference_tail_fro": tail, "full_svd_tail_fro": full_tail,
            "signed_gap": norm(residual) - tail, "relative_gap": norm(residual)/tail-1,
            "uncertainty_fro": uncertainty, "uncertainty_relative_to_a": uncertainty/norm(a),
            "reference_uncertainty_fro": ref_uncertainty, "candidate_formation_uncertainty_fro": candidate_uncertainty,
            "full_backward_residual_fro": backward, "full_backward_residual_relative": backward/norm(a),
            "polar_error_upper_model": polar_error, "full_backward_plus_polar_upper_model": beta,
            "full_u": mu, "full_v": mv, "candidate_u": cmu, "candidate_v": cmv,
            "normal_model": normal_model, "valid": valid}


def diagnose(source_sha):
    torch.set_num_threads(1)
    a = make_matrix(2048, 1024, 'geometric', seed=123).to(torch.float64)
    buf = io.BytesIO();torch.save(a, buf);raw = buf.getvalue()
    assert torch.equal(a, torch.load(io.BytesIO(raw), weights_only=True))
    ref = torch.linalg.svdvals(a);u, s, vh = torch.linalg.svd(a, full_matrices=False)
    factors = u[:, :8], s[:8], vh[:8]
    result = audit(a, factors, ref, (u, s, vh))
    residual = a - (factors[0] * factors[1]) @ factors[2]
    total2 = norm(a)**2;leading2 = float((ref[:8]**2).sum());energy_tail2 = total2-leading2
    energy_uncertainty = (2*norm_error(a)*norm(a) + gamma(10)*leading2 + gamma(1)*(abs(total2)+abs(leading2)))
    wrong = audit(a, (factors[0], torch.zeros_like(factors[1]), factors[2]), ref, (u, s, vh))
    inflated = audit(a, factors, ref*1.01, (u, s, vh))
    result.update(source_sha=source_sha, torch=torch.__version__, threads=torch.get_num_threads(), shape=list(a.shape), spectrum='geometric', dtype='float64', seed=123, rank=8,
                  serialized_sha256=hashlib.sha256(raw).hexdigest(), tensor_bytes_sha256=hashlib.sha256(a.numpy().tobytes()).hexdigest(), serialization_roundtrip_equal=True,
                  reference_singular_values=ref.tolist(), full_svd_singular_values=s.tolist(),
                  direct_fro_squared=norm(residual)**2, fsum_residual_fro_squared=math.fsum(float(x)*float(x) for x in residual.flatten()),
                  total_energy=total2, leading_energy=leading2, energy_tail_squared=energy_tail2, energy_tail_uncertainty_model=energy_uncertainty,
                  energy_tail_reliable=energy_tail2>energy_uncertainty,
                  energy_tail_relative_uncertainty=energy_uncertainty/energy_tail2,
                  energy_uncertainty_scope='arithmetic/cancellation only; singular-reference error accounted separately by reference_uncertainty_fro',
                  condition_number_2_observed=float(ref[0]/ref[-1]), rank_boundary_gap=float(ref[7]-ref[8]),
                  historical_gpu_serialized_sha256='f5b892c32d0d7259f9578f0fd1ef36172d794cdec3419d5f24084018b3d76996',
                  historical_gpu_input_hash_matches=hashlib.sha256(raw).hexdigest()=='f5b892c32d0d7259f9578f0fd1ef36172d794cdec3419d5f24084018b3d76996',
                  historical_gpu_diagnosis='INCONCLUSIVE: full GPU factors/A not saved, CPU serialization differs; no byte-identical reproduction or retrospective PASS', energy_tail_fro=math.sqrt(energy_tail2) if energy_tail2>energy_uncertainty else None,
                  historical_500eps_check_cpu=norm(residual)>=norm(ref[8:])*(1-500*torch.finfo(a.dtype).eps),
                  negative_controls={'zero_candidate':wrong, 'inflated_reference':inflated},
                  cuda='NOT RUN; no CLI invocation', history='Both GPU run directories remain immutable; prior configured FAIL remains FAIL.')
    assert wrong['status']=='FAIL' and inflated['status']=='INCONCLUSIVE'
    return result


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-sha',required=True);p.add_argument('--out',required=True);args=p.parse_args()
    repo=Path(__file__).resolve().parents[2]
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()!=args.source_sha or subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True).strip():
        p.error('exact clean source required')
    result=diagnose(args.source_sha);out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
    (out/'diagnostic.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('reference_singular_values','full_svd_singular_values','negative_controls')},indent=2))
