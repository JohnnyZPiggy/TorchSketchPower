# GPU readiness audit (M6)

**Status: AUDIT AND DESIGN ONLY. CUDA is NOT IMPLEMENTED and NOT RUN.** Nothing in this document is a GPU result. The audit used source reading, the installed PyTorch documentation, the official PyTorch pages, and CPU-only probes (including the `meta` device, which executes no kernels). The machine used has `torch 2.14.1+cpu` (`torch.version.cuda` is `None`, `torch.cuda.is_available()` is `False`), so no CUDA code path could have been exercised.

- Base: `main` `8eae3c63c04a6b43a463f1b5f8d1670c0fd33fe2`; task: [Issue #16](https://github.com/JohnnyZPiggy/TorchSketchPower/issues/16); SAE pin `JohnnyZPiggy/SAE-Framework@65338eb1aa67971e110db982a07cf43161c23446` (unchanged).
- Production code, tests, experiments and reports are untouched by this audit.
- Scope decision recorded in Issue #16: V1 is an **independent PyTorch implementation including real GPU development and validated acceleration**; V2 is later reuse or integration of Panther, skerch and other ecosystems. The CPU baseline (M0 to M5, [results](cpu-results.md)) stays valid evidence but is no longer the whole V1 target. Roadmap gates M7 to M10 are in [Section 8](#8-gates-m7-to-m10).

## 1. Sources and how each claim was checked

| Claim used below | Source | Check |
|---|---|---|
| `torch.linalg.lstsq`: on CUDA the only valid driver is `gels`, which assumes `A` is full rank; CPU drivers are `gels`, `gelsy`, `gelsd`, `gelss`; default driver is `gelsy` on CPU and `gels` on CUDA | [lstsq](https://docs.pytorch.org/docs/main/generated/torch.linalg.lstsq.html) | page fetched during this audit; same text in the installed 2.14.1 docstring |
| `torch.linalg.svd`: the `driver` keyword (`gesvd`, `gesvdj`, `gesvda`) works on CUDA inputs only; default calls `gesvdj` and falls back to `gesvd` if it fails; `gesvd` is the choice "if precision is relevant" | [svd](https://docs.pytorch.org/docs/main/generated/torch.linalg.svd.html) | page fetched; installed docstring |
| `torch.linalg.svdvals`, `cond`, `pinv`, `matrix_rank`: on CUDA the function synchronizes the device with the CPU | [svdvals](https://docs.pytorch.org/docs/main/generated/torch.linalg.svdvals.html) (and the other docstrings) | svdvals page fetched; the others from the installed docstrings |
| `torch.linalg.qr`: signs are not unique and inputs on different devices may give different valid decompositions; QR of a matrix whose first `k` columns are dependent raises no error and may be incorrect | [qr](https://docs.pytorch.org/docs/main/generated/torch.linalg.qr.html) | page fetched; installed docstring |
| Results may not be reproducible between CPU and GPU executions, even with identical seeds | [randomness note](https://docs.pytorch.org/docs/main/notes/randomness.html) | page fetched |
| `allow_tf32` for CUDA matmul defaults to `False` since PyTorch 1.12; `torch.set_float32_matmul_precision` also controls float32 matmul precision | [CUDA notes](https://docs.pytorch.org/docs/main/notes/cuda.html) | page fetched |
| `torch.cuda.set_sync_debug_mode` warns or errors on synchronizing operations, but is experimental and does not cover every synchronizing operation | [set_sync_debug_mode](https://docs.pytorch.org/docs/main/generated/torch.cuda.set_sync_debug_mode.html) | page fetched |
| A CPU generator used with a CUDA device raises inside torch | docstring of `gaussian_test_matrix` (`src/torchsketchpower/sketch.py`, earlier audit) | **not executed** (no CUDA); treat as UNVERIFIED |

Documentation reflects the PyTorch `main` branch and torch 2.14.1; behaviour on other versions is not claimed.

## 2. Audit matrix

CPU status is "tested" when covered by the committed 444 tests. "CUDA (docs)" is what the PyTorch documentation says about the operations used, never a statement that this code works on CUDA.

| Function | CPU today | CUDA (docs) | Blockers and hazards | Risk |
|---|---|---|---|---|
| `sketch_power_low_rank` | tested; raises `ValueError` for non-CPU `A` and for a non-CPU generator (by design) | composes the functions below | the guard must be lifted only together with the solver decision (Section 6); error messages and generator rule must be specified first | High |
| `construct_sketches` | tested | `matmul`, `randn`, `rand`, `randint` have CUDA kernels; complex `randn` on CUDA UNVERIFIED | no device guard of its own (meta probe, Section 4); generator device must equal `A.device`; CPU and CUDA random streams differ; float32 matmul precision setting must be recorded | Medium |
| `construct_corange_sketch` | tested | as above (`Psi @ A`) | same as `construct_sketches` | Medium |
| `sketch_power_subspace` | tested | `qr`, `matmul`, `svdvals` supported | per rank check: `svdvals` (documented sync), `max(s.max(), scale)` (a Python comparison on a device tensor) and `int((s > tol).sum())`, plus one `float(vector_norm(z))` per call (host reads by source reading, **not measured**); `qr` sign/phase not unique across devices; QR of rank-deficient input is silently wrong, so the rank gate is the only protection; `on_rank_deficient="ignore"` removes both gate and syncs | Medium-high |
| `solve_corange_coefficient` | tested | `lstsq` accepts only `gels` on CUDA and assumes full rank; `svdvals` syncs | **hard blocker:** `driver="gelsd"` is not valid for CUDA input; `float(gram_err)`, `float(sv[0])`, `float(sv[-1])` and the failure-branch `int(...)` are host reads; the thresholds `50 m eps` and `eps^(-1/2)` were chosen on CPU; no automatic CPU copy is allowed (it would not be a GPU result) | High |
| `reconstruct_from_corange` | tested | `svd(full_matrices=False)` supported, CUDA `driver` choice (`gesvdj` then `gesvd`; `gesvd` for accuracy; `gesvda` for very tall or wide) | blocked by the solve; driver trade-off between accuracy and speed to be measured; singular vectors only unique up to sign/phase | Medium |
| `gaussian_test_matrix` | tested | `torch.randn(..., generator=, device=, dtype=)` | generator must live on `device`; stream differs from CPU; complex on CUDA UNVERIFIED | Low-medium |
| `sparse_sign_test_matrix` | tested; not used in the committed experiments | `rand`, `topk`, `randint`, `scatter_` have CUDA kernels (UNVERIFIED here) | dense `long x short` score matrix (memory); tie handling in `topk`; fixed-nonzero distribution not shown paper-equivalent; recommend leaving CUDA for sparse-sign until Gaussian is validated | Medium |

## 3. Hazards and the falsifiable oracle for each

| ID | Hazard | Evidence | Oracle that would expose it (see Section 7) |
|---|---|---|---|
| H1 | Device handling exists only in `sketch_power_low_rank`; lower-level functions accept any device and fail in confusing ways | meta probe, Section 4 | O5: every public function either rejects a wrong device with a documented error or runs wholly on one device |
| H2 | `gelsd` cannot run on CUDA | lstsq docs | O1 on CUDA: calling the current code raises; after the M7 change, forward error against the CPU float64 oracle |
| H3 | `gels` assumes full rank and returns finite but wrong results otherwise | CPU `gels` proxy, Section 4 (not CUDA evidence) | O5: exactly and nearly rank-deficient `Psi Q` must raise `RankDeficiencyError`, never return a finite wrong `B` |
| H4 | The rank gate is a rank test, not an accuracy test: it admits float32 `C` up to `cond ~ 1/(max(shape) eps)` (about 3.5e5 for `24 x 12`), while the CPU proxy error of `gels` grows from 6.6e-5 at `cond = 1e4` to 8.0e-3 at `cond = 1e6` | CPU proxy table, Section 4 | O1: error bounded by a condition-scaled tolerance across float32/float64 and `cond(C)` from 1 up to the gate |
| H5 | QR/SVD outputs differ across devices by sign, phase and rotation | qr, svd docs | O3: compare matrices, singular values and projectors only, never vectors |
| H6 | CUDA SVD driver changes accuracy | svd docs | O3 with `gesvd` versus default on an ill-conditioned `B`; the driver used is recorded in every manifest |
| H7 | Host synchronizations (documented for `svdvals`; explicit `float()`/`int()` in the code) | docs and source | M8: timing with explicit synchronization, plus `torch.cuda.set_sync_debug_mode("warn")` as a hint only (experimental, incomplete) |
| H8 | The same seed gives different samples on CPU and CUDA; the generator must match the device | randomness note | O4 mode A (transferred tensors) versus mode B (device-local draws, invariants only) |
| H9 | float32 matmul precision (TF32 setting) changes results | CUDA notes | record `torch.get_float32_matmul_precision()` and `allow_tf32`; O1/O4 float32 tolerances are condition-scaled and the setting is part of the manifest |
| H10 | A CPU fallback reported as GPU success | design rule | O6: device assertions on every output; spy on `.cpu()`, `.numpy()` and `.to("cpu")` during the production path; any hybrid path is labelled separately |
| H11 | Complex dtypes: plain transpose instead of the Hermitian adjoint; CUDA complex support unverified | M5 tests on CPU | O3/O4 on complex64/complex128 with a `.T` negative control |
| H12 | Memory and cuSOLVER failure modes (out of memory, solver failure) | general | M7: small sizes only, errors recorded as `BLOCKED`/`FAIL` rows, never retried silently |
| H13 | Run-to-run non-determinism of GPU libraries | randomness note | tolerances, never bitwise equality; seeds and settings recorded |

## 4. CPU-side probes run for this audit

These are CPU and `meta`-device runs. They are evidence about the current code's structure and about the `gels` algorithm on CPU as a proxy. They are **not** CUDA evidence.

**Probe A: what the unguarded functions do with a non-CPU device** (`meta` device; no kernels run):

```python
import torch
from torchsketchpower import *

meta = lambda *s: torch.empty(*s, dtype=torch.float64, device="meta")
for name, fn in {
    "construct_sketches(meta A)": lambda: construct_sketches(meta(10, 8), 3, 6),
    "construct_corange_sketch(meta A)": lambda: construct_corange_sketch(meta(10, 8), 4),
    "sketch_power_subspace(meta y,z)": lambda: sketch_power_subspace(meta(10, 3), meta(10, 6)),
    "solve_corange_coefficient(meta)": lambda: solve_corange_coefficient(meta(10, 3), meta(5, 10), meta(5, 8)),
    "sketch_power_low_rank(meta A)": lambda: sketch_power_low_rank(meta(10, 8), 1, 3, 6, 3),
}.items():
    try:
        out = fn()
        print(name, "-> returned", type(out).__name__)
    except Exception as e:
        print(name, "->", type(e).__name__ + ":", str(e)[:70])
```

Observed (torch 2.14.1+cpu):

```
construct_sketches(meta A) -> returned tuple
construct_corange_sketch(meta A) -> returned tuple
sketch_power_subspace(meta y,z) -> RuntimeError: Tensor.item() cannot be called on meta tensors
solve_corange_coefficient(meta) -> RuntimeError: Tensor.item() cannot be called on meta tensors
sketch_power_low_rank(meta A) -> ValueError: a must be on the CPU, got device meta; other devices are not supported
```

Reading: only the top-level function rejects a non-CPU device cleanly (H1). The sketch constructors silently produce tensors on the foreign device; the rank-checking functions fail at the first host read. This also confirms that the host reads (`.item()` through `float()`/`int()`) sit on the path of every gate.

**Probe B: `gels` versus `gelsd` against an SVD-pseudoinverse oracle** (CPU only; `gels` is the same QR-based driver family that CUDA is restricted to, but this is a **proxy**, not the CUDA implementation). `C` is `24 x 12` with prescribed singular values, `W` is random `24 x 20`; the oracle is computed in float64 from the same (rounded) `C`:

```python
import torch

d, s, n = 24, 12, 20
g = torch.Generator().manual_seed(1)
u = torch.linalg.qr(torch.randn(d, s, generator=g, dtype=torch.float64)).Q
v = torch.linalg.qr(torch.randn(s, s, generator=g, dtype=torch.float64)).Q
W = torch.randn(d, n, generator=torch.Generator().manual_seed(2), dtype=torch.float64)

def oracle(c, w):
    uc, sv, vh = torch.linalg.svd(c.double(), full_matrices=False)
    return vh.mH @ ((uc.mH @ w.double()) / sv[:, None])

for dtype in (torch.float64, torch.float32):
    for cond in (1e0, 1e2, 1e4, 1e6, 1e8, 1e10):
        sv = torch.logspace(0, -torch.log10(torch.tensor(cond)).item(), s, dtype=torch.float64)
        c, w = ((u * sv) @ v.mH).to(dtype), W.to(dtype)
        ref = oracle(c, w)
        err = {drv: float(torch.linalg.matrix_norm(torch.linalg.lstsq(c, w, driver=drv).solution.double() - ref)
                          / torch.linalg.matrix_norm(ref)) for drv in ("gelsd", "gels")}
        print(f"{str(dtype)[6:]:8s} cond {cond:6.0e}  gelsd {err['gelsd']:.2e}  gels {err['gels']:.2e}")
```

Observed:

| dtype | cond(C) | `gelsd` rel. error | `gels` rel. error |
|---|---|---|---|
| float64 | 1e0 | 4.7e-16 | 6.2e-16 |
| float64 | 1e2 | 7.9e-16 | 1.1e-15 |
| float64 | 1e4 | 7.9e-16 | 8.7e-15 |
| float64 | 1e6 | 4.5e-16 | 4.9e-15 |
| float64 | 1e8 | 5.6e-16 | 3.0e-15 |
| float64 | 1e10 | 5.1e-16 | 1.5e-15 |
| float32 | 1e0 | 2.9e-7 | 1.9e-7 |
| float32 | 1e2 | 1.6e-6 | 1.6e-6 |
| float32 | 1e4 | 6.7e-5 | 6.6e-5 |
| float32 | 1e6 | 9.7e-1 | 8.0e-3 |
| float32 | 1e8 | 1.0e0 | 8.8e-1 |
| float32 | 1e10 | 1.0e0 | 8.9e-1 |

Reading (CPU, one problem, one seed, so indicative only): in float64 the QR-based driver stayed close to the oracle even at `cond = 1e10`; in float32 the error follows roughly `eps * cond` up to `cond ~ 1e4` and degrades beyond it, and `gelsd` truncates small singular values by its default `rcond` (giving a different answer from the oracle) while `gels` does not. So any CUDA tolerance has to be condition- and dtype-scaled, and the gate thresholds must be re-derived on the device, not inherited from CPU.

**Probe C: `gels` on an exactly rank-deficient `C`** (CPU, `8 x 3` with a duplicated column):

```python
import torch

g = torch.Generator().manual_seed(3)
C = torch.randn(8, 3, generator=g, dtype=torch.float64)
C[:, 2] = C[:, 0]                                    # exactly rank 2
W = torch.randn(8, 4, generator=g, dtype=torch.float64)
for drv in ("gelsd", "gelsy", "gelss", "gels"):
    x = torch.linalg.lstsq(C, W, driver=drv).solution
    print(f"{drv:6s} ||x||={float(torch.linalg.matrix_norm(x)):.3e}  ||Cx-W||={float(torch.linalg.matrix_norm(C @ x - W)):.3f}")
```

Observed:

```
gelsd  ||x||=8.283e-01  ||Cx-W||=3.561
gelsy  ||x||=8.283e-01  ||Cx-W||=3.561
gelss  ||x||=8.283e-01  ||Cx-W||=3.561
gels   ||x||=8.372e+15  ||Cx-W||=3.511
```

The rank-revealing drivers return the minimum-norm solution; `gels` returns finite values of norm about `8e15` and no error. The `gels` residual is not meaningful at that magnitude (cancellation in `C @ x`). This is the failure the explicit rank gate has to prevent on CUDA (H3); the existing `RankDeficiencyError` gate catches exact duplication in the CPU path (tested in M2).

## 5. Existing CPU behaviour that must not change

Every future change must keep: the 444 CPU tests passing; CPU `gelsd` solve, thresholds (`50 m eps`, `eps^(-1/2)`, `max(shape) eps s_max`) and exceptions unchanged; byte-identical regeneration of `reports/m4_cpu/samples.csv` and `reports/m5_cpu/samples.csv`; `.sae/` and the SAE pin unchanged.

## 6. Solver design decision record (DR-1)

**Decision (proposed for Architect approval; no code changed in M6):** keep CPU as is. For CUDA, the candidate path is `torch.linalg.lstsq(C, W, driver="gels")` **only after** the explicit gate already used on CPU (orthonormal `Q`; `svdvals(C)` rank test; conditioning warning), with the thresholds re-validated on the device. The result is accepted only if it passes oracles O1 and O2 against (a) CPU `gelsd` on transferred copies and (b) an SVD-pseudoinverse oracle computed on the device on a small problem.

- No normal equations (`C^H C`), no explicit inverse.
- If `gels` fails O1/O2 within the agreed condition-scaled tolerance, the fallbacks to evaluate with native primitives are: (A) SVD-based solve on CUDA, `B = V diag(1/sigma) U^H W` from `svd(C)` (rank-revealing, uses the same factorization as the gate); (B) `qr(C)` then `solve_triangular`, which has the same full-rank assumption as `gels`. Neither is pre-selected and no performance is assumed.
- A hybrid that moves `C`/`W` to the CPU for the solve is **not** a GPU result and may exist only as a separately labelled, measured option.
- The driver is chosen internally by device; no new public flag is added without Architect approval. Choosing the SVD driver (`gesvdj` default with fallback, `gesvd`, `gesvda`) is an M7 measurement, recorded in every manifest.
- Generator rule to specify before M7: a CUDA call takes a generator on `A.device` (or none); mixed cases raise a specific `ValueError` before any sketch is drawn.

## 7. Oracle plan (GPU tests, to be implemented in M7 and later)

Common rules: every GPU test is skipped, never passed, when CUDA is absent, and the evidence report counts skips as `NOT RUN`:

```python
import pytest, torch

cuda = pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")

@cuda
def test_example(): ...
```

All matrix operations run on the device; transfers to the CPU are allowed only for the independent reference and are listed. Compare matrices, singular values and projectors, not vectors. Tolerances are `kappa * eps(dtype) * cond(C) * ||ref||` with a constant `kappa` agreed with the Architect after looking at data (not set here).

| ID | Oracle | Grid |
|---|---|---|
| O1 | coefficient `B` on the device versus CPU float64 SVD-pseudoinverse of the transferred `C`, `W` | dtypes float32, float64, complex64, complex128; tall and wide `W`; `d = s` and `d > s`; `Q` orthonormal; `cond(C)` from 1 to near the gate |
| O2 | normal-equation residual `||C^H (C B - W)||` and optimality against the oracle | same grid |
| O3 | singular values of `B`, rank-`r` reconstruction `Q B_r`, projectors, versus the CPU oracle; `gesvd` versus the default driver; Hermitian adjoint with a plain-transpose negative control | same grid plus ill-conditioned `B` |
| O4 | end to end. Mode A: sketches drawn on the CPU and transferred, outputs compared with the CPU result as matrices. Mode B: device-local draws, so only invariants are checked (M5 identities I and II including the cross term, Eckart-Young lower bound, finiteness, rank); the CPU and GPU error distributions over at least 5 seeds are reported as observations, not pass/fail | M4/M5 baseline cases, small first |
| O5 | negative matrix: `rank(A) < s`; exactly rank-deficient `C` (duplicated `Psi` row); nearly rank-deficient and ill-conditioned but full-rank `C` (warning); non-orthonormal `Q`; mixed CPU/CUDA tensors; dtype mismatch; generator on the wrong device; non-CUDA input to the CUDA path; `d < s`; invalid `r`. None may return a finite wrong answer or silently fall back to the CPU | each case a row |
| O6 | device placement: outputs and intermediates are CUDA tensors; spies on `.cpu()`, `.numpy()`, `.to("cpu")` record zero calls in the production path | all O1 to O4 runs |
| O7 | regression: 444 CPU tests and byte-identical regeneration of the committed CPU sample files | each PR |

Mode A versus mode B matters because the same seed does not give the same samples on CPU and CUDA ([randomness note](https://docs.pytorch.org/docs/main/notes/randomness.html)); results from mode B cannot be compared element for element.

## 8. Gates M7 to M10

Status of every gate except M6: **NOT RUN**. Execution rules come from the pinned SAE protocol ([`GPU_EXPERIMENT.md`](../.sae/workflows/GPU_EXPERIMENT.md)): exact source SHA, one session, finite timeout, verified cleanup, benchmark without GitHub writes, no new billing, short device probes marked `PROBE_ONLY` and never counted as acceptance. Whether an authenticated GPU environment is available to the Engineer is NOT VERIFIED; if it is not, M7 is `BLOCKED`, not skipped.

| Gate | Purpose | Entry | Exit (all required) | Explicit non-claims |
|---|---|---|---|---|
| M6 (this PR) | readiness audit, decision record, oracle plan | Issue #16 | Architect T2 review of this document | no GPU result |
| M7 | GPU native correctness (EXPLORE) | M6 merged; DR-1 approved; a real CUDA environment confirmed; Gaussian first (sparse-sign only if the Architect asks) | O1 to O7 pass on CUDA for the approved dtypes, with manifest (device, driver, CUDA and torch versions, seeds, TF32 setting, SVD driver); CPU behaviour unchanged | no speed, no compile, no sparse-sign equivalence |
| M8 | GPU performance experiments (VALIDATE) | M7 merged; Architect marks accelerator readiness | benchmark with warmup, explicit `torch.cuda.synchronize()`, repeats, median and p95, transfers stated, memory high-water, CPU baseline with thread count, sizes beyond 96 x 96, equal correctness at every size | a speedup is claimed only for the measured sizes, dtypes and device |
| M9 | `torch.compile` validation | M7 merged | CPU eager versus compile and GPU compile checked for correctness; graph breaks and compile time reported separately (the host reads in the rank gates are expected graph-break sources); fallback documented | nothing about compile is claimed before this gate |
| M10 | independent CPU/GPU validation | M7 to M9 done or waived by the Architect | M4/M5-style experiments rerun on CPU and GPU with the same protocol, identities I and II on the GPU, independent rerun by the Architect, evidence packet for the V1 release decision | a V1 tag still needs the T3 review in [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) |

## 9. SAE GPU readiness gate (template filled with facts; the decision is the Architect's)

| Gate | Status | Evidence |
|---|---|---|
| Scoped mathematical readiness | PASS for the in-memory CPU pipeline; GPU numerical contract is design only | Issues #4, #6, #8, [math.md](math.md) |
| CPU oracle, randomized and edge correctness | PASS (Engineer-run) | 444 tests; [cpu-results.md](cpu-results.md) |
| CPU eager and `torch.compile` execution | eager PASS; compile NOT RUN | |
| CPU fullgraph / graph-break diagnostics | NOT RUN | |
| CPU benchmark and numerical tolerance | NOT RUN as a formal benchmark; M4 timings are indicative only | [cpu-results.md](cpu-results.md) |
| Clean pinned-SHA install | PASS (non-editable install); no packaged CLI exists | README |
| GPU workload defaults, device failure and report design | design only (this document) | Sections 2 to 8 |
| Colab CLI plan, three stages, source SHA | planned; GPU environment for the Engineer NOT VERIFIED | Section 8 |

**GPU_READY: not set by the Engineer.** Per the template, formal VALIDATE acceptance requires the mandatory gates above, several of which are NOT RUN. Short `EXPLORE` / `PROBE_ONLY` correctness work (M7) is a separate decision for the Architect. This table asserts nothing about GPU correctness, compilation or speed.
