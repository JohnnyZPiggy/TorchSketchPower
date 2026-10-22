# SAE Framework V3.3 — Capability Roadmap

> English normative | [简体中文](../i18n/zh-CN/docs/ROADMAP.md)

This repository specifies an agent collaboration protocol, **not** a hosted autonomous runner. Do not mistake written interfaces for implemented software.

## Verified in Scientist handoff (2026-10-19)
Windows Codex → WSL2 Ubuntu 24.04 → Colab CLI 0.7.4 → real T4 GPU smoke test; result JSON/SHA-256 verification and zero active sessions after cleanup. This is not an end-to-end framework experiment or GitHub Publisher test.

## P0 — End-to-end Codex experiment delegation
- Prove Colab CLI CPU execution and bounded GPU experiments using real algorithm benchmark CLIs, pinned source SHA and numerical oracle.
- Verify download integrity, failure propagation, session cleanup and GitHub report branch/PR publication with repository-scoped credentials.
- Verify TPU allocation and PyTorch/XLA independently; never infer support from listed TPU models.
- Default to direct Codex use of existing-account devices without Scientist approval; apply real provider limits, finite session timeout and cleanup, and avoid mandatory NVIDIA/CUDA-specific code.

## P1 — Reusable project adoption
- Safe idempotent bootstrap from pinned SAE commit; dry-run, no overwrite, target-project link/config validation.
- Test cross-project Colab CLI reuse without repeating OAuth setup or silently upgrading snapshots.
- Optional local schema validation for `sae.yaml` and experiment reports. No GitHub Actions.

## P2 — Quality of life
- Compact Issue/PR status summaries, reviewed version migrations and learning notes.

Each milestone needs a scoped Issue and real execution evidence. The three stages remain separate: pinned install → benchmark with **no GitHub writes** → optional validated publication. See [Compute Experiment](../workflows/GPU_EXPERIMENT.md).
