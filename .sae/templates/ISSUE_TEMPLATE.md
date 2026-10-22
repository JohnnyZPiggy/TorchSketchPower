# [SAE Engineering Task] <short title>

> Language: **English** | [简体中文](../i18n/zh-CN/templates/ISSUE_TEMPLATE.md)


**Owner:** Codex / Architect / Scientist
**Priority:** P0 / P1 / P2
**Status:** ready / in-progress / review / experiment / blocked / accepted
**Kind:** math / engineering / experiment / learning
**Depends on:** #<issue-number> (or none)

## Scientific purpose
What problem does this solve, and why does it matter?

## Pre-engineering mathematical research gate
**GPT-decided structure/tensorization study:** `docs/research/<algorithm>-tensorization.md` / link  
**GPT research decision:** RESEARCH_READY / scoped hypothesis-exception / RESEARCH_BLOCKED  
**Matrix-vector / tensor structure and limitations:** <summary>  
*Repository scaffolding-only issues can mark this as not applicable.*

## Mathematical / numerical contract
Definitions, assumptions, reference baseline, invariants, input/output shapes, dtype/device constraints, tolerance policy.

## Deliverables
- [ ] Scoped Python modules, CLI or design artifact
- [ ] Tests/benchmark source
- [ ] Documentation and reproduction commands

## Compute delivery gate (algorithm implementation tasks)
- [ ] Source SHA pinned; actual CPU packaging/CLI/numerical tests recorded PASS / FAIL / NOT RUN; safe `PROBE_ONLY` device checks may start in parallel
- [ ] Benchmark CLI writes local reports **without GitHub writes**; optional safe/non-sensitive Publisher is a separately verifiable stage directed by GPT (do not imply implemented)
- [ ] Codex-run Colab CPU/GPU/TPU results, independent publication and cleanup have distinct PASS / FAIL / NOT RUN / BLOCKED evidence; no Scientist compute signoff. Short `PROBE_ONLY` device checks are not formal benchmark acceptance.
- [ ] Record tested source SHA, actual commands, outputs and failures

## Acceptance criteria
- [ ] Spec and reference baseline agree
- [ ] Correctness/edge-case checks specified
- [ ] Actual CPU validation recorded
- [ ] If GPU-relevant, exact candidate SHA tested in Colab
- [ ] No GitHub Actions and no secret leakage

## Handoff
Target branch, linked PR/report, open questions, known blockers.
