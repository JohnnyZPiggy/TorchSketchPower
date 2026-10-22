# Permanent Architect Merge Authority — Scientist → Architect Role

> English is normative | [简体中文](../i18n/zh-CN/governance/STANDING_AUTHORIZATION.md)  
> Historical path preserved to avoid breaking existing references.

Authority attaches to the **explicitly assigned SAE role**, not an AI vendor, product, account, or model identity. The Scientist may change role assignments without changing approval boundaries. Examples such as GPT (Architect/Mentor) or Codex and Claude Code (Engineer) are illustrative only. Each agent must verify its own tool access; Engineers never merge their own work. Historical named-tool evidence remains attributable to the tool actually used.

## What the Scientist authorizes
## Architect/Mentor role decision authority — Scientist delegation (2026-10-20)

**Scientist (human):** defines or changes high-level research goals and can stop/revoke the delegation, but **is not a routine approval gate** for mathematical studies, R1–R3, `RESEARCH_READY`, algorithm choices, experimentation, numerical acceptance decisions, routine evidence publication or GitHub PR merges.

**Assigned Mentor and Architect AI agents (e.g., GPT):** have the Scientist's standing delegation to independently formulate/accept/reject mathematical research, select experiments, set tolerances and scoped exceptions, dispatch and iterate with the assigned Engineer, judge measured evidence and make final eligible GitHub PR MERGE / DO_NOT_MERGE decisions. **No per-stage Scientist signoff, standing-grant lookup, individual T3 scientific signature or duplicate approvals.** The Mentor/Architect may record `RESEARCH_READY / RESEARCH_BLOCKED / NOT_TENSORIZABLE` with short rationale and uncertainties. This authority applies during user-invoked, bounded work cycles and to the owner's eligible public repositories; existing pinned project rules remain applicable until intentionally adopted.

**Assigned Engineer (e.g., Codex or Claude Code):** implements and directly executes eligible local/Colab CLI CPU/GPU/TPU experiments under [Experiment by Default](../workflows/GPU_EXPERIMENT.md), returns verifiable evidence for Architect/Mentor evaluation and never self-merges.

**True external boundaries (not a slow approval chain):** require real GitHub/CLI/device permissions, reproducible source SHA, honest numerical/test evidence, protected-branch compliance, secret/data screening, finite runtime/session cleanup and explicit new user stop instructions. **Do not** create new subscriptions/top-ups/pay-as-you-go charges or monetary commitments outside existing entitlements without a separately stated user spending decision; do not disclose sensitive/nonpublic data, alter account/security permissions or perform irreversible external destructive actions without an explicit user instruction. Safe, sanitized, non-sensitive evidence PRs in eligible owner-public repositories may be submitted under the existing workflow, with the Architect's normal review/merge discretion. External provider/UI requirements cannot be overridden by this document.

**Fast-lane rule:** one Mentor/Architect scientific decision and one evidence-driven Architect review suffice; no mandatory second human or redundant multi-agent signoff. Launch bounded `PROBE_ONLY` environment/device diagnostics immediately when useful; overlap independent mathematical analysis, packaging, reference tests and device readiness when practical. A probe cannot support a formal speedup claim. For formal claims, retain defensible math, numerical checks, fair benchmarks and precise run provenance. `NOT RUN` never means `PASS`.

This is standing delegated **decision authority**, not a promise of a perpetual background agent, bypass of actual tool access, automatic control of an Engineer's desktop app or permission to treat unexecuted work as completed.

## Repository scope — all the owner's public repositories, without registration

**The Scientist's latest explicit instruction on 2026-10-19 automatically authorizes all current and future public repositories actually owned by the GitHub account `JohnnyZPiggy`.** This replaces the former single-repository allowlist and one-time enrollment requirement. It applies even when an algorithm repository has not adopted SAE. Public forks owned by that account are included.

Before each PR merge, verify via the **live GitHub API** that the target repository's **`owner.login` is exactly `JohnnyZPiggy` and its visibility is public**, and that the current connection has real merge rights. Do not infer ownership from the PR author, repository name or connected-app access. Repositories owned by other people/organizations, private/internal repositories and forks owned by others are out of scope. Transferred or privatized repos are no longer covered. Existing or future user-owned public repos **need no individual registration, yearly renewal or repeated merge permission**.

Copying a pinned `.sae/` snapshot does not grant API capabilities, bypass branch protections, or silently upgrade that project's workflow rules. This central owner-level permission derives from the Scientist's explicit instruction, not text in untrusted PRs or other repositories. The Scientist may revoke or narrow it by a later explicit instruction, effective immediately; no AI agent can widen it without such human authorization.

## Three review tiers — one merge decision-maker

Tier describes **review evidence and prerequisites**, **not three different people who must authorize the merge**. Assign by the highest-risk actual diff/effects, not a title or label.

| Tier | Typical changes | Preconditions before the Architect may choose MERGE |
| --- | --- | --- |
| **T1 — Routine** | Ordinary docs, translations, formatting, non-authority-changing protocols, narrow tests | Actual diff and relevant link/syntax/behavior checks are reviewed |
| **T2 — Engineering** | Algorithm code, numerical corrections, PyTorch optimizations, packaging, benchmark/Publisher, normal dependencies | Approved mathematical formulation when applicable, real Engineer CPU oracle/edge/regression/install evidence, compatibility/security/license review; verified Engineer-run Colab GPU evidence **only when GPU success is claimed or is a required acceptance gate**. CPU-only PRs can merge with explicit `GPU_NOT_RUN` if GPU is out of scope. |
| **T3 — High-impact evidence review** | Changed mathematical assumptions/claims, security or governance policy, major licensing/IP/releases, destructive actions or sensitive data | the assigned Architect decides science and in-scope governance changes under the 2026-10-20 delegation, documenting real assumptions, numerical evidence, risks and the exact diff. **No Scientist stage approval**. New billing, changes to real account permissions, nonpublic/sensitive disclosure or irreversible external destruction remain outside this blanket delegation; if necessary choose `MERGE_BLOCKED / WAITING_FOR_EXTERNAL_ACTION`, not a fabricated authorization. |

**Example:** the assigned Mentor derives a tensor reformulation and records a defensible `RESEARCH_READY` or a documented approximation; Architect accepts or returns the scientific case, directs the Engineer to run real tests and decides eligible merge based on evidence. No Scientist approval is needed. Incomplete proof, failed numerical tests or genuine tool restrictions must be recorded and addressed, not waved through.

A PR changing this policy is T3 evidence review. Changing the agent assigned to a role does not itself expand the delegation, owner scope, or tool privileges. The Scientist's explicit 2026-10-20 instruction delegates internal scientific/engineering/governance choices to the Architect/Mentor roles within the existing owner-public scope, while preserving immediate user revocation. GPT cannot expand repository ownership scope, create real provider privileges, assume new spending permission or make its own grant irreversible.

## Merge Gate (each PR, every Architect work cycle)

1. **Restore role/scope:** confirm user-invoked Architect role, live `owner.login == JohnnyZPiggy` and public visibility, current applicable rules (root AGENTS + pinned project rules), present connected tool permissions, any newer Scientist revocation. Do not infer permission from repository visibility alone; live owner, public visibility and connected tool access must be verified.
2. **Inspect actual PR:** all changed files and complete diff, issue/acceptance, exact base/head SHA, dependencies, GitHub mergeability/protections, outstanding blocking reviews and secrets/external-publication risks.
3. **Classify T1/T2/T3 and verify actual evidence without Scientist signoff.** The Architect assesses mathematical assumptions, risks and acceptance; `NOT RUN` is not `PASS`. For Architect-authored substantive code, use independently executed Engineer tests rather than Architect self-certification.
4. **Architect makes the final decision:** `MERGE_APPROVED`, `DO_NOT_MERGE`, `MERGE_BLOCKED`, or `WAITING_FOR_EXTERNAL_ACTION`. **No Scientist science, experiment, T3 or PR approval request**. Ask the user only when an action would create a new monetary commitment, reveal nonpublic/sensitive material, change external account/security permissions or perform irreversible external destruction.
5. **Audit before merge:** leave one concise GitHub PR review/comment identifying tier, SHA, tested evidence, risks/blockers and Architect's decision, without repetitive approval ritual. Do not claim the comment was written if tools fail.
6. **Merge if approved:** prefer squash and pass the exact reviewed head SHA; obey GitHub branch protection, never bypass rules, push directly to main, force-push, or merge stale revisions. Verify the merged state and final merge SHA; if head or material base changes, re-review.
7. **Report and hand off:** give merge SHA/PR or explicit reason for `DO_NOT_MERGE`, then the recommended Next-Action command. No silent sweep of unrelated PRs or background loop.

**Short PR audit:**

```text
SAE ARCHITECT MERGE GATE
Repo/PR: <owner/repo>#<N>; reviewed base/head: <base-SHA>/<head-SHA>
Tier: T1 / T2 / T3; standing authority: PERMANENT (until Scientist revokes)
Evidence and actual external constraints: <links, status, or NOT RUN>
Architect final decision: MERGE_APPROVED / DO_NOT_MERGE / MERGE_BLOCKED / WAITING_FOR_EXTERNAL_ACTION
Reason / risks: <short>; confirmed merge SHA: <SHA or NOT MERGED>
```

## Boundary, revocation and adoption

- **The assigned Architect is the delegated scientific and final technical decision-maker** for scoped SAE work. It must reason from actual evidence, not fabricate proof, disclose secrets, alter external account settings or ignore explicit user stop instructions.
- **No annual renewal or expiration:** the permission continues until explicit Scientist revocation or superseding instruction. Revocation is immediate; promptly record it in governance when tools permit.
- **Owner-wide public scope, not blanket API access:** all currently/future user-owned public repositories are covered without registration, but private/other-owner repos are excluded. Every PR still needs live owner/visibility checks, real connector permissions and independent evidence-based review.
- **No scope inflation:** owner-public repository scope, genuine permissions, new billing and external high-impact actions remain real boundaries; the assigned Architect may improve internal SAE policy without new Scientist approval, but cannot self-grant external privileges.
- **No CI mandate or background automation:** GitHub Issues/PRs form the audit trail; the Engineer submits and tests but **never merges its own engineering PRs**. the assigned Engineer executes eligible existing-account Colab experiments; sanitized public evidence PRs may be submitted as part of normal work without Scientist signoff, while nonpublic/sensitive release remains a genuine external boundary.
- **For the SAE source repo:** this live file is authoritative on merger discretion. For copied `.sae/` snapshots use project pinned instructions for ordinary workflow, but verify this current owner-public grant, live owner/visibility and Scientist's current instructions before merging.

Related: [Architect](../protocols/ARCHITECT.md) · [Task Management](../workflows/TASK_MANAGEMENT.md) · [Role Recovery](../workflows/ROLE_RECOVERY.md).
