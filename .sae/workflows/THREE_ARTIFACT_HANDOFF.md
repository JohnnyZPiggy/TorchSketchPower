# Three Research Artifacts — Mathematics, Engineering, Experiment

> Language: **English** | [简体中文](../i18n/zh-CN/workflows/THREE_ARTIFACT_HANDOFF.md)

## Purpose
For **VALIDATE** and accepted research, SAE coordinates through **three linked scientific artifacts**, rather than relying on chat history or unnecessary status paperwork. During **EXPLORE**, [Lean Lab](LEAN_RESEARCH_LAB.md) uses a single concise batch note instead; full reports are **not required per exploratory attempt**. They live in each **algorithm project repository**, **not** in the SAE Framework repository itself. GitHub Issues and PRs remain the coordination and review system.

| Deliverable and target-project path | Owner / decision authority | Question answered | When updated |
| --- | --- | --- | --- |
| **Mathematical Research** — `docs/research/<algorithm>-tensorization.md` | GPT Scientific Mentor drafts and decides; Architect may challenge/revise | What is the mathematical structure? Which matvec/matrix-free/tensor formulations are justified, and when? | New algorithm, significant redesign, or new mathematical finding |
| **Engineering Report** — `docs/engineering/<algorithm>-engineering.md` | GPT Chief Architect defines specification & acceptance; **Codex owns implementation/test evidence**; Architect reviews | What interfaces/algorithms were implemented, where is the code, and what actually passed? | Architect handoff; then significant engineering PR/revision |
| **Experimental Report** — `reports/gpu/<run-id>/summary.md`, with small machine-readable results | **Codex directly executes** existing-account Colab CPU/GPU/TPU experiments; GPT owns scientific conclusions and evidence review | On which source SHA, device, dtype and workload were correctness and performance actually measured? | **Each published/accepted VALIDATE run**; preserve unique run identity; exploratory probes need only a compact batch note |

## Contract: one question, one authority, connected evidence
- **Math → Engineering:** for formal VALIDATE acceptance, the GPT-decided research study supplies equations, assumptions, tensor shapes, oracle, limits and `RESEARCH_READY` (or a bounded documented hypothesis). EXPLORE may start testable local prototypes and `PROBE_ONLY` checks earlier but must not imply formal acceptance.
- **Engineering → Experiment:** the Architect's acceptance criteria and Codex's exact candidate **source commit SHA**, CLI, correctness evidence and reproducible commands define the experiment. CPU verification is **not** GPU verification.
- **Experiment → Research/Engineering:** measured failures and bottlenecks link back to the responsible code PR and mathematical study; GPT decides whether to revise math or implementation.
- **No second source of truth:** do not re-copy benchmark numbers into multiple reports. Use links and SHAs. A GitHub Issue/PR records work status; documents record *scientific reasoning and evidence*.
- **Scientific learning:** Mentor explains the math and observations during these handoffs. Important learned facts can be incorporated in the relevant document without forcing a separate learning log.

## Templates (in this Framework repo)
- [Mathematical Research template](../templates/TENSORIZATION_STUDY.md) — already established as the required research gate.
- [Engineering Report template](../templates/ENGINEERING_REPORT.md) — new engineering interface, implementation and CPU evidence record.
- [Experimental Report template](../templates/EXPERIMENT_REPORT.md) — Codex-operated authorized compute experiment narrative; complements `manifest.json`, `correctness.json` and `benchmark.csv`.

## Minimal lifecycle
1. **Mentor:** documents a concise mathematical case and autonomously records `RESEARCH_READY` or limits; **no Scientist approval**. Early `PROBE_ONLY` checks do not count as production acceptance.
2. **Architect:** specifies software contract, acceptance and formal experiment plan in the Engineering Report or linked Issue; submits a scoped Codex task referencing the mathematical study.
3. **Codex:** implements on branch and runs real CPU tests; EXPLORE may iterate repeatedly under one task with a compact batch note. Update the Engineering Report and open a PR when formal VALIDATE evidence or useful code is ready. Never self-merge or invent PASS.
4. **Codex:** runs the pinned candidate on available local/Colab CPU/GPU/TPU, verifies artifacts and cleanup, and submits safe non-sensitive per-run evidence PRs; GPT judges science and technical evidence.
5. **Architect:** briefly checks SHA-linked artifacts, accepts/returns work and revisits Mentor mathematics whenever evidence challenges assumptions; no human approval round.

## Template instantiation

When creating a new project document from a Framework template, replace placeholders and **remove or rewrite the template's source-repository language-switch link** to reference the project's pinned `.sae/` snapshot. A link valid in `templates/` may not work when the finished document lives in `docs/research/`, `docs/engineering/` or `reports/gpu/`. Do not blindly copy relative links.

## Lightweight rules
- A document is a **living milestone record**; don't create new copies for every minor edit or chat. GPU runs are inherently immutable run-by-run records.
- Not every project needs elaborate prose. Short exact equations, code paths, links, commands and statuses beat lengthy claims.
- Missing evidence is **NOT RUN**, never `PASS`; a planned run is not an executed experiment.
- No claim of automatic writes merely because a command is shown; respect real tool access, new-billing/data boundaries and reviewable PRs.
- No GitHub Actions; Codex directly operates eligible Colab CLI experiments; Drive is optional Notebook workspace only.

## Handoff integrity check
The research study, engineering report and experiment summary must cross-reference the same algorithm/Issue and **the actual relevant commits**. Record separate **implementation source SHA** and **report publication SHA** where applicable; do not confuse them.
