# GitHub Task Management and Handoff

> Language: **English** | [简体中文](../i18n/zh-CN/workflows/TASK_MANAGEMENT.md)


**Canonical task source:** GitHub Issues, not private chat histories.

## Minimal label vocabulary
- Ownership: `role:engineer`, `role:architect`, `role:mentor`, `human:scientist`; legacy `agent:codex` remains valid for existing Issues. A GitHub username/assignee identifies the actual Engineer when available.
- State: `status:ready`, `status:in-progress`, `status:review`, `status:experiment`, `status:blocked`, `status:accepted`
- Work type: `kind:math`, `kind:engineering`, `kind:experiment`, `kind:learning`
- Priority: `priority:p0`, `priority:p1`, `priority:p2`

If labels cannot be created, write the exact intended state into an Issue comment; do not pretend labels were applied. `Assignee` must be a real GitHub username, not an imaginary bot account.

## Pre-engineering research gate
For new algorithms or substantial redesigns, Mentor/Architect agents autonomously record a concise `RESEARCH_READY` study or limited hypothesis/exception using [Mathematical Research](MATHEMATICAL_RESEARCH.md); **Scientist signoff is not required**. Mark Engineer tasks ready once testable scope is clear. Safe probes/reference code/setup may run in parallel with R1/R2; formal acceptance remains evidence-gated.

## Linked artifacts in Issue/PR handoffs
Link the Mentor/Architect-decided mathematical study, concise Engineering Report and Engineer-executed experimental evidence following [Three-Artifact Handoff](THREE_ARTIFACT_HANDOFF.md). Experiment PRs identify the exact tested source SHA and upstream Issue/PRs; do not create duplicate status reports or treat templates as proof of execution.

## Lean execution path
Use [Lean Research Lab](LEAN_RESEARCH_LAB.md) as the single **EXPLORE / VALIDATE** mode and bounded-batch contract. During EXPLORE, retain a short hypothesis/source/command/outcome record in the **same Issue or working branch**; do not make a new PR or full three-artifact packet for each probe. For VALIDATE, compile/link the required formal math, engineering and run evidence. The Architect may switch modes on evidence without Scientist signoff.

## Lifecycle
1. **Architect dispatches immediately:** use one scoped Issue (or existing Issue) with target SHA/interface, mode, minimal oracle/checks, experiment goal, finite timeout and cleanup plan. Mark ready as soon as safe work is available; do not wait for full paperwork or human research approval.
2. **Engineer claims Issue** by explicit comment and status update to in-progress; one owner at a time.
3. **Engineer batches implementation and experiments** on `feat/<issue-number>-<slug>`: implement → test → diagnose → repair → rerun within task-defined timeout and bounded attempts, without new signoff per attempt. Open an appropriate PR after useful scope/evidence accumulates; use `Closes #N` only when issue acceptance is met, otherwise `Refs #N`.
4. **Architect makes one evidence-based review** of source SHA/diff and relevant correctness results, while the assigned Engineer runs eligible CPU/GPU probes and later formal benchmarks. Do not serialize independent tasks needlessly.
5. **The assigned Engineer runs existing-account Colab CLI by default**, with exact SHA for remote installed code, one active session, finite timeout and verified cleanup. Consolidate multiple exploratory runs into **one batch evidence update**; report PR/publication remains optional and separately verified. No Scientist compute/price gate; real correctness, permissions or billing blockers must be reported.
6. **Architect performs one substantive evidence review and decides MERGE / DO_NOT_MERGE** for eligible PRs without Scientist approvals; missing/failed checks yield a targeted correction on the **same Issue**, rather than redundant handoff paperwork.
7. **Mentor may summarize** a learning insight, but learning never replaces engineering checks.

## State consistency
- GitHub API writes can fail, labels can be unavailable, PR comments can become stale. Always refetch state after critical mutations.
- Do not auto-claim overlapping Issues; link dependencies; stay inside a bounded cycle.
- Use linked Issues/PRs, run IDs and commit SHAs for all handoffs.
- Never mix numeric performance claims from different code versions without disclosure.

## Required next-action handoff
Before the final response of each substantive cycle, apply the [Next-Action Completion Gate](NEXT_ACTION.md) with verified status/evidence and one complete copyable recommendation (up to two meaningful alternatives).

## Role recovery and integrity
At cycle start apply [Role Recovery](ROLE_RECOVERY.md): check role, pinned project rules, live evidence and actual permissions. Stop on role mismatch.

## Indefinite owner-wide Architect merge decision
For eligible PRs in the owner's public repositories, the assigned Architect makes the independent final MERGE / DO_NOT_MERGE decision **only** under [Standing Authorization](../governance/STANDING_AUTHORIZATION.md), after live ownership/visibility/permissions and diff/SHA/test evidence checks; no Scientist research/T3 signoff. No per-PR merge permission, Engineer self-merge or unattended PR sweep. [Standing Authorization](../governance/STANDING_AUTHORIZATION.md) alone defines the full scope and tiered evidence requirements; evidence review is not a repeated human approval cycle.

