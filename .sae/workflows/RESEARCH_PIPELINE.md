# Research Pipeline — Scientific Gate, CPU Validation, Authorized Accelerators (V3.3)

> English normative | [简体中文](../i18n/zh-CN/workflows/RESEARCH_PIPELINE.md)

SAE is **evidence-first and aggressively parallel**, not a CPU→GPU approval waterfall. The [Lean Lab](LEAN_RESEARCH_LAB.md) `EXPLORE` mode uses short bounded batches and compact notes; `VALIDATE` assembles formal science and run evidence. Run reference code, packaging and bounded CPU/GPU/TPU probes concurrently when technically safe; formal claims still require numerical and mathematical evidence. GitHub remains the evidence hub; no default GitHub Actions, Drive sync or background agent.

## I. Mathematical research — GPT Mentor/Architect
Explore formulations, oracles, tensor/batched/matrix-free structures, stability and complexity. Record the concise math hypothesis in the task during EXPLORE and a study in `docs/research/<algorithm>-tensorization.md` for VALIDATE. **GPT decides `RESEARCH_READY / RESEARCH_BLOCKED / NOT_TENSORIZABLE` or a scoped hypothesis**, without Scientist signoff. Independent device probes and reference implementation may proceed in parallel.

## II. Engineering and CPU correctness — Architect + Codex
Architect reviews ecosystem Build-vs-Reuse, sets specifications and dispatches Issues. Codex implements installable Python modules and runs actual CPU oracle/edge/randomized/dtype tests, supported `torch.compile`, clean pinned-SHA installation and benchmark CLI smoke tests. During EXPLORE record source identity, commands and observed results in one batch note; for VALIDATE link them from the engineering report. CPU compile does **not** establish GPU/TPU compatibility or speedup.

Architect marks `ACCELERATOR_READY` (historical `GPU_READY`) for **formal** performance evaluation when required mathematical, numerical and package prerequisites are actually met. Early `PROBE_ONLY` device checks need no such marker; readiness is **not** hardware verification.

## III. Device experiments — Codex executes by default, Architect reviews
Under [Experiment by Default](GPU_EXPERIMENT.md), Codex executes existing-account CPU/GPU/TPU without any Scientist compute authorization gate, grant check or price forecast. Bounded `PROBE_ONLY` device diagnostics can precede formal research/benchmark readiness; formal performance claims still require mathematical and numerical acceptance. Use one active Colab session by default, finite timeout, exact SHA, real access, evidence validation and session cleanup. User stop instructions and separate new-billing approval remain effective. TPU/XLA capability requires actual tests, not menu entries.

Use [Compute Experiment](GPU_EXPERIMENT.md): exact-SHA install → benchmark **without GitHub writes** → optional sanitized, verified GitHub report branch/PR under existing GPT-publication delegation. Architect reviews evidence and merges only eligible PRs under [Standing Authorization](../governance/STANDING_AUTHORIZATION.md). Codex never self-merges. Publisher success requires real GitHub verification.

On device failure return to Phase II; on flawed math return to Phase I. For VALIDATE preserve linked mathematical, engineering and experimental artifacts; for EXPLORE preserve a compact batch evidence note, always with honest `PASS` / `FAIL` / `NOT RUN` / `BLOCKED` statuses. GPT makes scoped scientific, evidence and internal governance decisions. No Scientist approval queue; real permissions, new billing and nonpublic-data boundaries remain in force. Existing pinned V3.2 projects are not silently upgraded.
