# SAE V3.3 Architecture and Boundaries

> English normative | [简体中文](../i18n/zh-CN/docs/ARCHITECTURE.md)

![SAE V3.3 native card-style organization architecture (English)](figures/SAE_Framework_V3.3.en.svg)

[View high-resolution vector SVG](figures/SAE_Framework_V3.3.en.svg)

[Editable Mermaid source (.mmd)](figures/SAE_Framework_V3.3.en.mmd)

The standalone SVGs were redrawn from the confirmed ChatGPT native-card layout for the **post-PR #33 GPT Autonomous Fast Lane**. The Scientist is the goal-setter (not a review gate), GPT Mentor/Architect owns scientific and engineering decisions, Codex executes bounded experiments, and GitHub feeds evidence back to GPT. The `.mmd` sources and README Mermaid remain separate editable *logical* diagrams. Both language variants preserve real tool/data/billing and verification boundaries; changing these rules requires updating all presentation views.

[Current role contracts](../AGENTS.md)

## Two equal outcomes
**Engineering Productivity:** reproducible, correct, maintainable algorithm packages at low coordination and compute cost.

**Scientific Learning:** deepen the Scientist's understanding of mathematical structure, numerical methods, PyTorch, device execution and performance interpretation.

## Authority and execution
- **Scientist:** sets or changes goals and may stop work; not a routine mathematics, experiment, budget, T3 or merge approver.
- **GPT Architect + Mentor:** autonomously decides scientific readiness, mathematics, scoped exceptions, engineering acceptance and eligible PR merges; mentors the Scientist and reviews true evidence under [Standing Authorization](../governance/STANDING_AUTHORIZATION.md).
- **Codex Engineer:** writes/tests code, directly runs eligible existing-account local and Colab CLI CPU/GPU/TPU experiments, verifies artifacts/session cleanup, opens safe evidence PRs and never self-merges.
- **GitHub:** only durable task and evidence hub (Issues, PRs, source SHAs and the three linked scientific reports).
- **Colab CLI:** compute execution surface, not the report exchange layer. Google Drive is optional temporary notebook scratch, not synchronization.

## Iterative operating loop
GPT-decided concise mathematical study + parallel Build-vs-Reuse, reference CPU work and `PROBE_ONLY` device readiness → Codex implementation/experiments → real GitHub evidence PR → GPT scientific/technical acceptance and eligible merge. No Scientist approval queue. Numerical or mathematical failures return to earlier stages; this is not a linear waterfall.

Experiments separate **(1)** exact SHA installation, **(2)** correctness/benchmark without GitHub writes, **(3)** optional GPT-reviewed sanitized evidence PRs; sensitive/nonpublic release and new charges still require explicit user authorization. TPU requires separately verified PyTorch/XLA support. No GitHub Actions or mandatory paid CI.

## Evidence and capability honesty
A 2026-10-19 handoff reports Windows Codex → WSL2 → Colab CLI → T4 GPU smoke test, SHA-256 checking and runtime cleanup. Colab CPU, TPU/PyTorch-XLA, automated GitHub publication and full cross-project workflow remain **NOT VERIFIED** until actual tests establish them.

See [Research Pipeline](../workflows/RESEARCH_PIPELINE.md), [Three Artifacts](../workflows/THREE_ARTIFACT_HANDOFF.md) and [Compute Experiments](../workflows/GPU_EXPERIMENT.md). Existing pinned project snapshots do not upgrade automatically.
