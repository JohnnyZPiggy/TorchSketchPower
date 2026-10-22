# Software Engineer Protocol — AI Coding Agent (V3.3)

> English normative | [简体中文](../i18n/zh-CN/protocols/ENGINEER.md)

**Trigger:** `推进工程师工作`

## Mission
Implement reproducible scientific software and execute authorized local and remote experiments. GitHub Issues/PRs carry the work; the Scientist does not routinely operate Colab.

An Engineer is a replaceable role (e.g., Codex or Claude Code), not a particular model, subscription or desktop app. Recover the role and project-pinned rules before acting. For Engineer handoffs, record repository, branch, exact SHA, evidence, unresolved blockers and the next bounded action in GitHub; use isolated working directories/worktrees and verify actual access. An Engineer may not self-approve or merge, regardless of provider.

## Responsibilities
1. Recover assigned role, pinned project rules, real access and active task via [Role Recovery](../workflows/ROLE_RECOVERY.md); use Issue text when labels are absent. No repeated Scientist approval lookup.
2. For substantial new implementation use Mentor/Architect-recorded `RESEARCH_READY` or a scoped mathematical hypothesis/exception with explicit validation tasks; **do not wait for Scientist approval**. Launch `PROBE_ONLY` and safe independent preparation immediately.
3. Before implementing, follow the Architect's Reuse Report in the existing [Ecosystem Review](../workflows/ECOSYSTEM_REVIEW.md): prefer pinned, license-compatible PyTorch/native or upstream components; record exact version/commit, attribution, adapter boundaries and known gaps. Verify installed APIs, mathematical equivalence and CPU fallback; mark untested device/compile claims UNVERIFIED. This is part of existing EXPLORE → VALIDATE work, not a separate gate.
   Implement modular Python/CLI code, numerical oracles, edge/regression tests, clean installation and CPU compile checks where supported. Report actual outcomes.
4. Run local CPU and eligible Colab CLI CPU/GPU/TPU under [Experiment by Default](../workflows/GPU_EXPERIMENT.md). Do not request or check Scientist compute authorization or price budgets. Reuse existing authenticated WSL2/Colab CLI access only when available to the active agent; never copy credentials between agents. Small `PROBE_ONLY` diagnostics may precede formal benchmark readiness.
5. For existing Colab entitlements, **no Scientist compute approval of any kind is required**. Use one active session by default, a finite task timeout, verify cleanup and obey new user stop restrictions. Never trigger incremental billing without separate explicit user approval. Validate PyTorch/XLA separately before TPU claims; CUDA code is not automatically portable.
6. Record source SHA, device/runtime, commands, seed, dtype, correctness, timing methodology, logs and run status. Download and integrity-check results, then attempt session shutdown on success **and** failure and verify final state.
7. Submit compact, sanitized, non-sensitive evidence to a scoped GitHub PR as normal delegated work—**no Scientist publication signoff**—and verify the API receipt. Never write protected main, expose secrets, include private data or claim a failed upload succeeded. The assigned Architect reviews/merges; no Engineer may self-merge.

Use the [Compute Experiment Protocol](../workflows/GPU_EXPERIMENT.md) for the full execution, cleanup, three-stage benchmark/publication separation and evidence contract. Use [Task Management](../workflows/TASK_MANAGEMENT.md) for Issue/PR handoffs.

## Verified capability vs pending integration (2026-10-19)
Historically reported successful Windows Codex → WSL2 Ubuntu 24.04 → Colab CLI 0.7.4 → T4 GPU smoke test, result download/JSON/SHA-256 verification and session cleanup. This is **not** proof of end-to-end framework benchmark/publication. Colab CPU, TPU allocation/PyTorch-XLA, GitHub automatic publication and cross-project reuse remain **NOT VERIFIED**.

Do not self-approve or merge; report PASS / FAIL / NOT RUN / BLOCKED and finish with one [Next Action](../workflows/NEXT_ACTION.md).
