# Mathematical Structure Discovery & Tensorization Research Gate

> Language: **English** | [简体中文](../i18n/zh-CN/workflows/MATHEMATICAL_RESEARCH.md)

**Primary owner and research decision: GPT Scientific Mentor / GPT Architect; no Scientist signoff.**  
**Position:** evidence-based mathematical gate for **formal correctness/acceleration claims**; independent tooling/probes, baseline code and experiment preparation may run concurrently.

## Research-first principle

**Mathematical structure → equivalent tensor formulation → architecture and experiment design → engineering implementation → evidence-driven CPU/GPU validation.**

This is a compact, GPT-decided evidence gate, **not** a sequential approval queue. Codex/device probes, reference implementation, install and tooling may proceed alongside R1/R2; marked speculative tensorization code may be tested as a hypothesis. **Formal equivalence or acceleration claims** require defensible mathematics and real numerical benchmarks. Failed probes may reopen R1/R2.

## Stage R1 — Examine the mathematical problem (GPT Mentor)
1. Read the paper/reference algorithm, mathematical definitions, objective, dimensions, input distributions, numerical contract and current implementation (if any).
2. Identify data dependencies and actual operators: linear and affine maps, matrix–vector/matrix–matrix products, tensor contractions, separability, batched independent instances, matrix-free `Ax` or `Aᵀx`, Jacobian-vector / vector-Jacobian products, Hessian-vector products, low-rank/sparse/block/Kronecker structures, reductions and scans.
3. Locate *non-tensorizable* barriers: sequential recurrences, branches, irregular memory access, host sync, graph breaks, dynamic shapes, unavoidable data-dependent control flow.
4. Distinguish mathematical opportunity from implementation assumptions; do not promise speedups or equivalence without support.

## Stage R2 — Derive an equivalent tensor formulation
1. Derive the transformation from the reference algorithm **step by step**. Write both original and candidate mathematical forms with explicit shape and index notation.
2. State proof obligations: equality, valid domain and differentiability (where relevant), numerical and stability assumptions, boundary cases, precision requirements, and limits of approximation.
3. Investigate vectorization, batching, broadcasting, contraction/einsum, linear operator application, `vmap`, batched factorizations, and appropriate functional control-flow primitives—not blindly forcing every loop into a dense tensor.
4. Evaluate asymptotic work, arithmetic intensity, intermediate memory, parallel depth, data movement, compilation overhead, dtype/device portability, and likely CPU/GPU/TPU constraints.
5. Compare at least the **reference**, a **tensorized mathematical candidate**, and a **fallback** if the candidate is unproven or inefficient. If no useful tensorization exists, document this as a valid scientific outcome.

## Stage R3 — Produce a research handoff
Create/update `docs/research/<algorithm>-tensorization.md` in the **algorithm project** using the canonical [Tensorization Study template](../templates/TENSORIZATION_STUDY.md). Record source/assumptions, original-to-tensor equations and shapes, proof or approximation limits, reference oracle/tolerances, dependencies and nonparallelizable barriers, numerical risks, complexity/device hypotheses, alternatives, and **untested** experiment questions. Conclude with **RESEARCH_READY / RESEARCH_BLOCKED / NOT_TENSORIZABLE**, rationale and GPT Mentor/Architect decision; no Scientist approval field is required.

`RESEARCH_READY` permits formal engineering/benchmark evaluation, **not** a claim of correctness or acceleration. For `RESEARCH_BLOCKED` / `NOT_TENSORIZABLE`, GPT chooses a documented limited hypothesis experiment, fallback or stop; no Scientist signoff. Exploratory `PROBE_ONLY` runs remain allowed.

## Mathematics → Engineering → Experiment artifact link
The GPT-reviewed study is the first of [Three Research Artifacts](THREE_ARTIFACT_HANDOFF.md); Architect/Codex use the linked [Engineering Report](../templates/ENGINEERING_REPORT.md), while independently verified runs get separate [Experimental Reports](../templates/EXPERIMENT_REPORT.md). Do not copy measured performance into mathematical hypotheses.

## Gate to Architect and Engineer
1. GPT Mentor/Architect decides a formulation or scoped hypothesis/exception and immediately defines a minimal implementation, correctness checks and experiment matrix, distinguishing **proved / hypothesized / NOT RUN**. No human approval handoff.
2. Codex implements reference/tensorized forms, verifies CPU correctness and runs formal GPU/TPU benchmarks after technical readiness checks on the exact pinned SHA, **without Scientist compute approval**. Bounded `PROBE_ONLY` device diagnostics may run earlier; failures may reopen R1/R2.
3. Exploratory math or `PROBE_ONLY` device checks may falsify a derivation or confirm environment availability, but are **not** formal engineering validation or GPU benchmarks. Never invent evidence.

## Mentor invocation behavior
With `推进导师工作`, if no accepted study exists, quickly produce a minimal R1–R3 rationale and make a GPT research decision, while parallelizing safe tooling/probes. For approved studies, investigate new structure or numerical failures. **Do not request Scientist scientific approval**; communicate uncertainty and genuine evidence blockers.
