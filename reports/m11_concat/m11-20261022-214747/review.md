# M11: CPU semantic gate FAIL — no T4 allocation

Tested source `2510723c36618fb61358e5d348264e9fbdabb307`; base main `cdb1346072d062bc67fb52d36b26326772fa86af`; SAE `65338eb1aa67971e110db982a07cf43161c23446`. Issue #26. Verdict **REJECT unrestricted checked-pipeline substitution**; any future restricted-domain performance question is DEFERRED to independent GPT Architect review. No production integration.

246 scoped CPU tests PASS, including23M11 tests. This validates the auditor/negative controls, not the scientific gate. Existing noneditable CPU package/source identity verified, torch2.14.1+cpu, no environment or dependency change. All140actual-public/separate-replay comparisons verified; individual RNG draws captured in replay, never by patching public RNG.

72regular configurations (3shapes,4dtypes,steps0/1/2,2seeds) pass in the tested domain. Of140full-pipeline configurations,123pass and17are NOT_EQUIVALENT:16numerical-only differences beyond the fixed thresholds and1strict first-error/RNG-branch mismatch (index33), both concat view/copy modes. All24downstream rank/condition/nonorthogonal-Q fixtures and2invalid-generator fixtures agree. All complete negatives remain in results.json; no tolerance widened.

## Decisive public API counterexample (case33)

A shape16x17,float32,seed315,r1/s1/ell3/d4,steps1,near-cross target factor1. Omega/Phi exact draws and initial RNG state agree. Actual public eager succeeds and draws Psi; concat_view AND concat_copy instead raise:

    RankDeficiencyError: z.mH @ q at step 1 has numerical rank 0 < k=1; the powered range is not k-dimensional

Independently replayed first-cross singular value public6.223863806553709e-7, concatenated5.970535426058632e-7; unchanged threshold6.194297981210184e-7. Their ratios to the threshold are1.0047730712 and0.9638760428. Y differs by at most2.2351741790771484e-8 (sketch Fro delta2.7877519926234643e-8, well within ordinary dtype tolerance); Z is bitwise equal. This tiny perturbation changes a hard branch. It is not proof of a production algorithm bug or a reason to relax the gate. Vendor kernel dispatch was not profiled; different floating-point products are the observed fact.

Public final RNG SHA256 `0a49bec5eab69f9170565535b7b9a0aa451d9ae5959dcf95944a0290cfd0bbd3`; candidate `b3a63f9acfb665b0616f6b03b29a28942a9bd11aa998e1b27df5de3093d62c0d`. Public advances through Psi, candidate stops after Omega/Phi. Explicit contiguous copies cannot repair this counterexample. Exact realized A is saved as branch-counterexample-A.pt with SHA256 `ad9e5cf9f96b0183a7647a714202cb4b08fa00294cf82367a3d00fcd15cf19a4` and logical hash `ce57394be1ee56e6830a7f32dfa555e19d319d66fe166519170f2a3e26539ce4`. It was loaded weights_only and independently replayed successfully; complete replay traces are in counterexample-replay.json.

The earlier first failed numeric case26 (seed314,factor0.8) is separately saved as first-failure-A.pt. Its same-warning/same-RNG paths still change the Q projector by0.02437 and reconstruction by0.00726, exceeding the predeclared1e-3 test bound. Near-singular cross-products amplify rounding; these16numerical comparisons are reported as failure of the chosen equivalence gate, not universal accuracy claims.

## Layout, copies and provenance

Raw per-case metadata includes strides, contiguity, sharing and actual backing bytes. concat_view generally has row stride s+ell and shared m*(s+ell)storage. concat_copy adds explicit output payload m*(s+ell)*element_size; cat input payload n*(s+ell)*element_size is incurred in both candidates. These are allocation/copy payloads, not measured GPU traffic/peak or latency. Copy timing NOT_RUN. For regular48x24,f32,s4/ell7: input cat1056bytes, explicit output repack2112bytes; separate Y/Z do not share storage, views do. No free-copy or saved-FLOP claim.

Original M10/M7/M8/M9 raw files were re-read/hashed; provenance is in review.json. They remain untouched. M10's limited8successful H1 cases never established general semantics; this broader study supplies a counterexample. Existing M7 CUDA contracts and M8/M9 negative/partial timings are context only, not new M11 GPU evidence. Initial audit hashing failed on a valid singleton stride; the retained log documents the fix to logical-byte serialization, with no math or acceptance change.

## Hard stop and next action

CPU gate FAIL => **GPU, Colab CLI, entitlement/preflight/usage checks, full-pipeline T4 and GEMM-only T4 timings NOT_RUN**. No controller/driver added, no allocation/retry or new cleanup proof claimed. No src/.sae/dependency/historical edits, Actions, extra billing or merge. Independent GPT Chief Architect T2 reviews the counterexample and verdict in the unique Draft PR before any future restricted study. Engineer does not self-approve or integrate H1.
