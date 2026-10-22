# Colab CLI Three-Stage Compatibility Guide (V3.3)

> Historical filename retained for existing links and pinned snapshots | [简体中文](../i18n/zh-CN/workflows/COLAB_TWO_COMMAND.md)

The old two-command/manual-Scientist workflow is superseded. **Codex** orchestrates authorized Colab CPU/GPU/TPU experiments through CLI; the Scientist sets scientific objectives and compute limits rather than routinely operating notebooks.

The three **logical stages** remain:
1. Install the exact source commit SHA.
2. Run a correctness/benchmark CLI **without GitHub writes**.
3. Optionally validate and publish a safe existing report through a separate GitHub branch/PR, only within applicable authorization; never merge automatically.

These are interface requirements, **not proof** that the benchmark Publisher or end-to-end GitHub automation is implemented. A notebook is optional and thin. Colab Secrets named `GITHUB_TOKEN` are not automatically available to every subprocess; use secure runtime credential handling, never echo/interpolate secrets into shell strings or logs. A fine-grained repository-scoped token must have the necessary permissions. If credentials or publication permission are missing, mark publication BLOCKED rather than claiming success.

The complete, authoritative workflow—including hardware quotas, TPU/PyTorch-XLA checks, evidence schema, download integrity, session cleanup and failure states—is [Compute Experiment Protocol](GPU_EXPERIMENT.md). Do not duplicate it here.
