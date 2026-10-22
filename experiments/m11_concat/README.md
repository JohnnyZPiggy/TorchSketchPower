# M11 separate-draw concatenated GEMM: CPU semantic gate

Issue #26; verified starting main `cdb1346072d062bc67fb52d36b26326772fa86af`, fixed SAE `65338eb1aa67971e110db982a07cf43161c23446`. One experimental runner and one new test file. No production/public API replacement, source/protocol/dependency/historical edits, compiler/profiler infrastructure or new environment harness.

## Definition and predeclared gate

Over exact arithmetic, `A @ cat(Omega,Phi)[:, :s] = A @ Omega` and the other block equals `A @ Phi`. The experiment **still makes two separate Gaussian draws**, in original order and dtype/device, using the caller's generator. It calls the unchanged checked subspace, draws Psi only after that succeeds, then calls the unchanged checked reconstruction. Algebraic equality does not imply equal floating-point rounding, near-threshold branches or final RNG state on failure. A single wide random draw is not this hypothesis and was already rejected by M10.

Three research paths: `separate` independent replay, `concat_view` column views, `concat_copy` explicit contiguous copies. The actual unmodified installed public API is called independently. Source identity is explicitly verified against pinned `src/`; installed package is reused without an install. Replay validity requires first error class/message/stage, warnings, final generator state and reconstructed output to agree with the actual public call. Individual Omega/Phi/Psi values are captured in the verified replay, not by monkey-patching public RNG. Their logical-value SHA256, shape/dtype/device and final generator-state hashes are compared with both candidates. Public errors retain full tracebacks.

Numerical tolerances are fixed before formal execution: Frobenius/max-1 normalization1e-3 for float32/complex64,1e-9 for float64/complex128 (existing well-conditioned CPU oracle scales). Individual Y/Z, Q projectors, final reconstructions/singular values and residuals are recorded. Raw max-absolute/relative differences and observed bitwise equality are disclosed, never asserted universal. Error class/message/occurrence stage, warning class/message and RNG state are exact comparisons; **no tolerance applies to a changed exception branch**. Any semantic or numerical/replay mismatch fails the CPU gate and forbids GPU in this task.

## Bounded coverage

-72 regular configurations: tall48x24,wide24x48,square32x32;4dtypes;steps0/1/2;seeds314/315; r3/s4/ell7/d9; A seed123. Both concat variants compared within each configuration.
-20 targeted full-pipeline cases: zero/rank-one A for steps0/2 in4dtypes, plus forced condition-limit warnings on well-conditioned data (max_condition1). Failures before Psi must leave its trace absent and generator state after exactly Omega/Phi.
-48 sharp-threshold adversarial cases:4dtypes x2seeds x3factors for each of Y/cross. Construct realized A from prescribed sketches via `A=target @ pinv(cat(Omega,Phi))`; this synthesis is a test fixture, not a production path. Y factors0.99/1/1.01 around m*eps; cross factors0.8/1/1.2 around ell*eps*norm(Z). Single-column cross fixture s1/ell3 isolates a case where different floating-point products can alter a sharp rank gate. Actual replayed singular values/thresholds, not intended pre-rounding targets, decide the observed branch.
-24 downstream-only fixtures: full-rank ill-conditioned C, zero/below/exact/above rank threshold C, nonorthogonal Q in4dtypes. Compare original reconstruction on equal contiguous/noncontiguous Q; retain expected RankDeficiencyError, IllConditionedWarning and orthogonality rejection. These fixtures do not claim a synthesized random full-pipeline C failure.
-2 invalid generator objects: wrong type or wrong-device descriptor; same first failure and no global RNG advancement. No GPU generator constructed. Prototype assumes the valid shapes/Gaussian domain above and is not a proof for arbitrary invalid public arguments or all devices.

The initial single-column float32/seed315/exact-target cross case already shows a real counterexample under torch2.14.1+cpu: actual public pipeline succeeds, concatenated path raises cross-rank deficiency before drawing Psi. Formal exact-SHA results, complete corpus and saved first-failure A determine the final verdict. This is the expected mathematical risk of hard numerical rank thresholds, not a reason to loosen a guard. All targeted cases remain in the report even after one fails.

## Layout/copy cost and failure evidence

Separate Y/Z have distinct output storage. View paths share an m*(s+ell) backing block and typically row stride s+ell; they are not independently packed. Copy paths explicitly call `.contiguous()` on each output and record their actual strides/contiguity/backing bytes. Note singleton dimensions may have unusual valid strides; logical-byte hashing handles them without reinterpreting strides. Initial auditor byte-view hashing failed for such a singleton stride; that instrumentation exception is archived and fixed without changing math or acceptance.

Input cat creates n*(s+ell)*element_size bytes and copies that payload; explicit output repack adds m*(s+ell)*element_size bytes. Reading+writing each copy implies at least twice its payload in an operand-boundary model, not measured DRAM traffic. Per-case copy payloads and actual backing-storage sizes/sharing are recorded. These are not CUDA allocator peak measurements or latency estimates; copy timing is NOT_RUN. A saved GEMM call saves no leading FLOPs; retained checks and layout/packing can change total cost.

Any NOT_EQUIVALENT result is retained with complete public/candidate traces, missing/present Psi and differing final state. The first exact realized counterexample A is saved as a tensor with serialized SHA256 and logical-value hash for independent same-environment replay. Raw report manifests cover all files. Independently recomputed gate diagnostics on captured inputs do not change actual public execution or RNG.

## Optional GPU decision and handoff

Issue #26 explicitly requires **STOP on any CPU semantic failure**. A confirmed failing gate means **GPU/Colab CLI/entitlement/preflight/usage/T4 timings NOT_RUN**; do not build a driver or provision to seek a favorable result. No new cleanup state is claimed. If a future separately reviewed restricted-domain hypothesis is desired, GPT Architect must scope it; this task does not automatically integrate concatenation into production.

CPU runner refuses dirty/mismatched HEAD, uses one CPU thread and the existing verified installed package, writes raw JSON/SHA256 and returns a research report even on a scientific gate FAIL. A successfully emitted report is not gate PASS.

    python -I -m pytest tests/test_m11_concat.py tests/test_core.py tests/test_lowrank.py tests/test_reconstruct.py -q -p no:cacheprovider
    python -I experiments/m11_concat/run_m11.py --source-sha EXACT_SHA --out NEW_DIRECTORY

Reuse: M10 H1 `experiments/m10_cost/run_m10.py` and `reports/m10_cost/m10-20261022-210437/observations.json`; original M7 CUDA contract/gate data, both M8 partial/failed runs and M9 negative compile/timing evidence are read-only context. No new speedup claim, Actions, paid commitment, source/math change, merge or hidden GPU retry. Unique Draft PR linked to Issue #26 goes to GPT independent T2.
