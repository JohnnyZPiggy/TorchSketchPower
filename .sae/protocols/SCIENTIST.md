# Scientist Protocol — Human Research Owner (V3.3)

> English normative | [简体中文](../i18n/zh-CN/protocols/SCIENTIST.md)

The Scientist is the research goal-setter and optional stop/redirect authority, **not a routine scientific, experimental or merge approver**. GPT holds delegated in-scope decisions under [Standing Authorization](../governance/STANDING_AUTHORIZATION.md).

## Human direction, not a signoff queue
- Set broad research goals, preferences and explicit new stop/revocation instructions; GPT decides mathematical assumptions, `RESEARCH_READY / RESEARCH_BLOCKED / NOT_TENSORIZABLE`, scientific interpretation and scoped experiment acceptance.
- GPT Mentor/Architect selects experiments, baselines, numerical tolerances, scientific alternatives and trade-offs autonomously; the Scientist may participate but no approval is required.
- **No compute-approval role:** under [Experiment by Default](../workflows/GPU_EXPERIMENT.md), Codex directly executes existing-account CPU/GPU/TPU work with real access and technical readiness. Do not request or validate any Scientist compute approval, including a standing-grant record. Scientist may stop/narrow future work at any time; new purchases/pay-as-you-go charges still require explicit user approval.
- GPT independently decides **in-scope** research, internal governance/engineering and eligible PR merges. Creating new monetary commitments, changing external account permissions, disclosing sensitive/nonpublic data or executing irreversible external destructive actions still needs distinct explicit user instruction; real provider restrictions remain binding.

## Delegated operations
Codex handles local CPU and eligible Colab CLI CPU/GPU/TPU execution, artifact download/integrity checks, session shutdown and GitHub branch/PR evidence submission. GPT reviews and decides scientific significance; Scientist can optionally question or redirect without being required to read/run notebooks or approve deliverables.

See [Compute Experiment Protocol](../workflows/GPU_EXPERIMENT.md), [Mathematical Research](../workflows/MATHEMATICAL_RESEARCH.md) and [Three-Artifact Handoff](../workflows/THREE_ARTIFACT_HANDOFF.md). Google Drive is optional notebook/temporary workspace only, not a results exchange layer.

Hardware support and publication must be marked verified only after real tests. TPU/PyTorch-XLA and end-to-end automatic GitHub publishing were not verified as of 2026-10-19.
