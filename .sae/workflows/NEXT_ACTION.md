# Next-Action Protocol — Agent Handoff and One-Tap Continuation

> Language: **English** | [简体中文](../i18n/zh-CN/workflows/NEXT_ACTION.md)

## Purpose

At the end of **each substantive SAE Mentor, Architect or Engineer work cycle**, provide the Scientist with a short, actionable next step. This is a presentation and handoff contract, **not** an autonomous scheduler, new agent, extra task database, or permission to execute future work without a new instruction.

## Compact completion handoff (native-first)

At the end of a substantive Architect/Mentor cycle, report verified state, evidence and any real Scientist-only external boundary in the main answer, then show **SAE · Next Action** only when a meaningful continuation exists. Prefer **1–3 ChatGPT-native clickable choices**, best first, each with a short label, one-line consequence and a complete self-contained Chinese role instruction in its click action. Do **not** duplicate full instructions in visible prose. When native submission is unavailable, show short numbered choices answerable with a number; provide a full copyable command only on request. The assigned Engineer uses only controls its own client actually supports and otherwise follows its normal concise handoff.

If there is no feasible next step, clearly report DONE / BLOCKED / WAITING_FOR_EXTERNAL_ACTION without inventing a selector or action. The completion gate is about evidence and truthful communication, not mandatory decorative UI.

Choose from current **GitHub evidence, task priority, dependencies, readiness and actual permissions**, not stale chat state. Typical routing: `RESEARCH_BLOCKED` → Mentor/Architect mathematical revision; `RESEARCH_READY` → Architect; `CPU_IN_PROGRESS` → Engineer; `CPU_VALIDATED` → Architect readiness review; `GPU_READY` → Engineer experiment under [Experiment by Default](GPU_EXPERIMENT.md), **without Scientist compute authorization or grant checks**; `GPU_BLOCKED` → local Architect/Engineer diagnosis. Correctness/security blockers override the default route.

A recommended command **does not execute an Agent**, allocate compute or authorize merges. Never request formal accelerator acceptance before `GPU_READY`; bounded `PROBE_ONLY` hardware probes may run earlier, reveal credentials, bypass merge authority or promise background execution. [Task Management](TASK_MANAGEMENT.md) owns Issue/PR state; this file owns the response handoff.

## Next-Action Completion Gate — pre-send check (V3.3)

Before sending the **final user-facing reply** of every substantive Mentor, Architect or Engineer cycle, apply this self-check. Complete status/evidence reporting is mandatory; interactive choices are conditional on a useful next action and actual client capability.

1. **Status and evidence:** state what was actually completed versus NOT RUN / UNVERIFIED / BLOCKED, with verifiable Issue, PR, report or commit links when available. Never fabricate activity, approvals or progress.
2. **One recommended handoff:** when a feasible next step exists, prepare **one full, stand-alone Chinese instruction** inside the clickable action (or on request in fallback mode), naming its target and action: `推进架构师工作：…`, `推进导师工作：…`, `推进工程师工作：…`, or `Scientist：…`. No placeholders, ambiguous fragments or commands to an agent that cannot actually be invoked.
3. **Meaningful choices:** offer zero to two distinct, feasible alternatives only when there is a real fork in the workflow. Rank one as the recommendation; do not pad choices or repeat the same work with different wording.
4. **No human approval queue:** the assigned Architect/Mentor roles own scoped science, readiness, engineering and T1/T2/T3 evidence decisions; the assigned Engineer runs existing-account compute under [Experiment by Default](GPU_EXPERIMENT.md). Never recommend waiting for Scientist science, CPU/GPU, T3 or PR signoff. Preserve real access, SHA, evidence, and new-billing/nonpublic-data external boundaries; a command is not proof of execution.
5. **Final handoff:** where a useful continuation exists, finish with a compact **SAE · Next Action** selector or numbered fallback. Keep current state, evidence and genuine Scientist-only requirements clear in the answer. Do not require a selector when the answer is terminal or a direct answer is sufficient.

### Native interaction and fallback

- **ChatGPT native-first:** use actual supported `pressable` or `button` controls and `GenUI.issueNewTurn(full_instruction)` only when the current client supports them. The click starts a new bounded conversation turn, not an external engineering-client action, a successful execution or new authorization.
- **No native controls:** show 1–3 brief numbered options, recommended first, that the Scientist can select by replying with a number. Supply the full copyable command on request, not by default. Never fake buttons in Markdown, SVG or images.
- **Other agent clients (e.g., Codex, Claude Code):** use their actual supported interaction affordances only; otherwise give a concise ordinary handoff without assuming ChatGPT UI features.
- Preserve the [Standing Authorization](../governance/STANDING_AUTHORIZATION.md), exact SHA/evidence, no Scientist routine approval, no new billing or sensitive publication, and all existing experiment/merge gates. This remains a response-level convention, not an enforced runtime validator.

## Example (illustrative only)

After reporting `CPU_VALIDATED` and an evidence link, offer a native choice labeled **Review GPU readiness** whose click action contains the complete `推进架构师工作：…` instruction. If native interaction is unavailable, display **1 · Review GPU readiness** and accept a numeric reply. No claim of an actual GPU run is implied.

## Integration

The task-management workflow remains the canonical GitHub Issue/PR handoff; this protocol only standardizes **what the agent tells the Scientist after each cycle**. Root/project AGENTS and role protocols should point here. Never duplicate the entire protocol into every role file.

## Role recovery and integrity
At cycle start apply [Role Recovery](ROLE_RECOVERY.md) to validate role, pinned rules and real permissions; end with this Completion Gate.
