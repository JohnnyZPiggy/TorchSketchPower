# Lean Research Lab — Explore / Validate and Engineer Experiment Batches (V3.3-compatible)

> English normative | [简体中文](../i18n/zh-CN/workflows/LEAN_RESEARCH_LAB.md)

## Purpose and precedence
This is a **lightweight execution path**, not a new agent, scheduler, approval hierarchy, experiment runtime or automatic CLI implementation. A scoped user-invoked SAE cycle can delegate one **bounded Engineer batch**; the assigned Mentor/Architect owns research hypotheses, science decisions and final evidence review. Apply [Mathematical Research](MATHEMATICAL_RESEARCH.md) for formal claims, [Compute Experiment](GPU_EXPERIMENT.md) for allocation/publication and [Standing Authorization](../governance/STANDING_AUTHORIZATION.md) for PR merges. User stop instructions and pinned project-specific rules take precedence.

## Two modes, chosen by the intended claim

| | `EXPLORE` — fast falsification | `VALIDATE` — reproducible acceptance |
| --- | --- | --- |
| Goal | Feasibility, quick numerical checks, tool/device diagnosis | Defensible correctness, speedup or merge decision |
| Start | The assigned Mentor records a testable hypothesis, minimal oracle, device/task scope; no Scientist signoff or complete study needed | the Mentor records `RESEARCH_READY` or documented, bounded assumptions; select formal acceptance criteria |
| Execution | Reference/prototype and bounded `PROBE_ONLY` GPU/TPU-XLA diagnostics may run alongside mathematical research | Pinned exact source commit SHA; applicable oracle/edge/randomized accuracy tests and fair benchmark controls |
| Evidence | One short batch log: source identity (full SHA for remotely installed code; local revision and dirty state otherwise), environment, commands, observations, actual PASS/FAIL/NOT RUN/BLOCKED | Mathematical rationale, tested SHA, correctness/benchmark methodology, device/dtype/seeds, run-specific artifact manifest, reproducible evidence |
| GitHub | Reuse the task Issue and working branch; **no PR or three full reports required for each exploratory run**. Preserve useful observations for handoff | Submit reviewed, sanitized compact evidence linked to code PR; optional report publication is separately verified |
| Claim | **HYPOTHESIS / PROBE_ONLY / UNVERIFIED**; never formal acceleration evidence | The Architect accepts/rejects only measured results; `NOT RUN` is never `PASS` |

Changing from EXPLORE to VALIDATE is an **Architect evidence decision**, not an extra Scientist approval. A smoke probe does not establish algorithm correctness, full TPU/XLA support or speedup.

## One Engineer task → one bounded engineering/experiment batch
The Architect hands off **one existing or new Issue**, not a string of independent approvals. Its compact batch contract must name:
1. **Goal and mode:** target algorithm, testable hypothesis, output expected and what counts as success/failure; list the math assumptions and smallest oracle.
2. **Source and environment:** owner/repo, branch or candidate SHA, actual existing local/Colab CLI access, hardware candidates. Formal remote tests install from exact SHA; exploratory local dirty changes are explicitly identified and never misreported as pinned remote results.
3. **Execution budget in engineering terms:** one active Colab session maximum, **task-defined finite timeout**, bounded retries (**default at most three self-repair attempts per failure class**, lower if continued attempts cannot make progress), explicit cleanup on success/failure/interruption. Reuse one running session for multiple sequential experiments when permitted; no indefinite loops or background scheduler.
4. **Autonomous actions within the batch:** inspect → implement a minimal candidate → reference/numerical test → bounded CPU/GPU/TPU probe or formal benchmark when ready → diagnose/fix → rerun, stopping on success, substantive math ambiguity, exhausted resources or a real access/security/billing boundary. The Engineer may iterate without a new Issue or Scientist/Architect signoff per attempt, **but cannot approve its own PR or scientific claim**.
5. **One return artifact:** a concise Issue/PR update with actual tested SHA/source identity, commands, device/runtime, numeric evidence, iteration/failure summary, cleanup and next blocker; attach only the necessary run artifacts. Do not create duplicate reports or one PR per exploratory attempt.

**Hard boundaries:** no new purchases, top-ups, pay-as-you-go settings or charges beyond existing entitlements without explicit user approval; no sensitive/nonpublic release or external account/security-permission changes; no protected-main write, Engineer self-merge, GitHub Actions or default paid hosted CI. Run-time permission/provider checks, precise reproduction, secret screening and honest error/status reporting are mandatory.

## Lightweight handoff and learning
- **Before dispatch:** the Architect gives one concise research decision and one executable batch contract. Build-vs-Reuse, reference preparation and device probing can proceed concurrently where dependencies permit.
- **After batch:** the Architect performs one substantive review of results and risks, accepts/merges an eligible PR or writes a targeted follow-up to the **same Issue**. If mathematical evidence fails, return to Mentor reasoning; do not pretend a full study has been approved.
- **Report only when justified:** exploration needs a compact note, not the full [Three Research Artifacts](THREE_ARTIFACT_HANDOFF.md). For formally accepted research, assemble/link the mathematics, engineering and experimental evidence without duplicating numerical tables.
- **Learning:** communicate one concise structural/numerical lesson when it materially helps; no mandatory learning diary.

## Implementation status
Protocol and task contract **only**. This document does not implement an Engineer autonomous runner, Colab CLI, Publisher or Bootstrap. A real end-to-end batch, cross-window Architect–Engineer handoff, and TPU/XLA support must be tested separately and reported `NOT RUN` until verified.
