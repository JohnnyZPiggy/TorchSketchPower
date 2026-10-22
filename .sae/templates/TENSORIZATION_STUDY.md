# Mathematical Structure & Tensorization Study — <algorithm>

> Language: **English** | [简体中文](../i18n/zh-CN/templates/TENSORIZATION_STUDY.md)

**Target repository / Issue:** `<owner/repo>` / #<number>  
**Research owner:** GPT — Scientific Mentor  
**Research decision:** GPT Mentor / GPT Architect (no Scientist signoff)  
**Status:** NOT_STARTED / RESEARCH_READY / RESEARCH_BLOCKED / NOT_TENSORIZABLE  
**Source paper/reference:** <link>  
**Study revision and decision date:** <commit / date>

## 1. Reference mathematical problem
State inputs, shapes, domains, assumptions, target quantities and original algorithm (citations/equations); identify numerical oracle.

## 2. Structure inventory
| Structure / candidate operator | Equation and shapes | Dependency/parallelism | Preconditions / obstacles |
| --- | --- | --- | --- |
| Matvec / matmul / matrix-free / batch / low rank / sparse / etc. | | | |

Explicitly state **what is not tensorizable** and why.

## 3. Derivation of the tensorized formulation
Write original → transformed equations with indices/dimensions. Show proof obligations, equivalent domain and any approximations; identify CPU reference and candidate tensor expression.

## 4. Numerical and correctness contract
Reference oracle, error metrics, tolerance rationale, precision stability, shape/edge cases, failure modes and possible counterexamples. **Do not claim tests passed unless executed.**

## 5. Complexity and hardware feasibility
Expected arithmetic work, memory, data movement, parallel depth, communication, likely `torch.compile` or functional control-flow barriers; CPU/GPU/TPU hypotheses **without invented speedups**.

## 6. Proposed architecture and experiments (not yet run)
Candidate operations and PyTorch API; baseline vs tensorized comparison; correctness-first experiment matrix with device, sizes, dtypes, seeds and measurements. Specify what remains untested.

## Handoff into the three-artifact chain
This file is the **Mathematical Research** record in the [Three-Artifact Handoff](../workflows/THREE_ARTIFACT_HANDOFF.md).

- **Source of truth:** `docs/research/<algorithm>-tensorization.md` in the algorithm project.
- **Next record, after GPT research decision (no human approval):** `docs/engineering/<algorithm>-engineering.md` based on [Engineering Report template](ENGINEERING_REPORT.md).
- **Later real measurements:** `reports/gpu/<run-id>/summary.md`; link the actual run only when executed.

Do not copy downstream performance numbers into this study; refer to them by links and distinguish conjectures from measurements.

## 7. Alternatives, risks and scientist decision
- **Outcome:** RESEARCH_READY / RESEARCH_BLOCKED / NOT_TENSORIZABLE
- **Proved:** …
- **Hypothesized:** …
- **Unverified:** …
- **GPT research decision / rationale link:** …
- **Architect handoff Issue:** …
- **Next research question:** …

This document is a **pre-engineering research artifact**, not a benchmark report. If blocked, GPT documents a bounded hypothesis/exception or pauses formal acceptance; independent `PROBE_ONLY` and reference preparation can proceed.
