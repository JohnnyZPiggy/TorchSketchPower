# Compute Experiment Protocol — CPU / GPU / TPU (V3.3)

> Historical path retained for compatibility | [简体中文](../i18n/zh-CN/workflows/GPU_EXPERIMENT.md)

## Ownership and prerequisites
- **Scientist:** sets goals and may stop/change work, **not** a scientific, experiment or compute signoff role. The assigned Architect decides scoped scientific readiness and conclusions.
- **Architect:** experiment matrix, readiness/acceptance criteria, review of evidence and final eligible PR merge discretion.
- **Engineer (e.g., Codex or Claude Code):** local/Colab CLI execution, correctness/benchmark tooling, artifact verification, session cleanup and safe non-sensitive GitHub evidence PRs as normal work.
- **GitHub:** shared code/task/report source of truth. Drive is optional temporary Colab workspace only.

For new algorithms/major tensorization work, the Mentor/Architect decides a concise [mathematical study](MATHEMATICAL_RESEARCH.md) and Architect experiment plan without human approval. Start independent probes, packaging/reference CPU and hardware preparation concurrently; **formal acceleration claims** need justified math, actual numerical correctness and fair measurements. Never claim device performance without execution.

## Three separate logical stages
1. **Pinned install:** run exact source commit SHA in the selected local/Colab environment.
2. **Benchmark:** execute correctness and performance CLI; **no GitHub writes**.
3. **Optional publication:** after evidence validation and independent secret/sensitive-data checks; routine safe non-sensitive public PRs need no Scientist signoff, publish only reviewed safe artifacts to a dedicated GitHub branch/PR.

The existing [three-stage compatibility entry](COLAB_TWO_COMMAND.md) retains its historical filename. Its illustrative notebook commands are not proof of a working CLI. The assigned Engineer may orchestrate these stages via Colab CLI without requiring the Scientist to click notebook cells. Publisher remains unverified until end-to-end tested.

## Experiment by Default — no Scientist compute gate (2026-10-20)

**CPU/GPU/TPU experimentation is a normal Engineer execution responsibility, not a Scientist authorization workflow.** Within an already connected Colab account's included or prepaid resources, neither the Architect nor Engineer shall request, verify, cite or wait for **Scientist compute permission**, standing-grant confirmation, individual device approval, price quotation, Compute Unit estimate, per-run budget or elapsed-time signoff. The Architect/Mentor autonomously decide scientific direction within the user's goal and acceptance of research conclusions; explicit user stop/change instructions override future work.

- **Fast start:** On a user-invoked, bounded SAE task, the assigned Engineer may run local or Colab CLI CPU/GPU/TPU experiments once the concrete task, exact source SHA, available authenticated tool/account and applicable technical readiness are established. Architect selects acceptance criteria and reviews results; the Engineer executes without a human compute-approval checkpoint.
- **Exploratory hardware probes:** Short, bounded environment/TPU-XLA/GPU smoke tests may precede formal `RESEARCH_READY` / CPU benchmark readiness **solely to establish real device availability or diagnose tooling**. Mark such results `PROBE_ONLY`; they cannot substitute for Architect/Mentor-reviewed mathematical justification, numerical correctness or formal performance acceptance. Formal accelerator claims still require the mathematical and engineering gates.
- **Safe execution defaults:** One active Colab session maximum, finite per-task timeout, no unbounded automatic retry/background scheduler, and verified cleanup after success, failure or interruption. Honor explicit new Scientist restrictions and provider-enforced limits. Genuine permission failures, unavailable device or exhausted resources are real blockers; predicted cost is not.
- **New billing exception:** A purchase, credit top-up, new subscription/account/provider, enabling pay-as-you-go, or any **new monetary commitment outside existing entitlements** requires separate explicit user approval. If the current account would generate incremental charges without a safely enforceable pre-existing entitlement boundary, stop rather than guess. No billing-setting changes by default.
- **Delegated decisions:** the assigned Architect decides in-scope scientific correctness criteria, algorithm acceptance, routine non-sensitive GitHub evidence publication and engineering signoff. No Scientist research/T3/experiment approval. New monetary commitments, nonpublic/sensitive disclosure or external destructive/account-permission actions need separate explicit user instruction.

## Compute and hardware controls

Reuse existing WSL2/Colab CLI OAuth where actually available. Before a run check the **real** account/tool permissions, exact source SHA, environment, task scope and finite timeout—**not** a Scientist compute authorization record. Select devices according to the experiment. Verify artifact identity and shut down allocated sessions. For TPU, confirm real allocation, PyTorch/XLA installation, supported operations and numerical behavior; a listed device option is not proof of functionality.

On success, failure or interruption: attempt to stop every allocated session, verify final session state, and report cleanup failures. Do not silently leave resources running.

## Required evidence
- `manifest.json`: run ID/time, exact source SHA, Issue/PR, device, software environment, seed, dtype, commands, status and methodology.
- `correctness.json`: reference, tolerances, errors and PASS/FAIL/NOT RUN.
- `benchmark.csv`: workloads, timing units, repetitions, warmup/synchronization, median/p95 and compilation cost where relevant.
- `summary.md`: actual observations, limitations, failures, cleanup outcome and evidence links.
- Download integrity verification (e.g. SHA-256), local/remote artifact identity and publication status.

Avoid large datasets, raw secrets and unnecessary logs. Never report a speedup without equivalent baselines and numerical correctness.

## GitHub publication and failure handling
After independent publication and security checks, validate artifact schemas/size/secrets; create an immutable run-specific branch/PR, link source SHA and Issue/code PR, verify API success, and leave merging to Architect. Public draft PRs are still public. No direct protected-main writes, force pushes or self-merges. Keep credentials in secure stores, never in checked-in files or logs.

Use `PUBLISH_FAILED` for upload/API failure; `NOT RUN` for untested hardware; `BLOCKED` for real execution permission failure, unapproved new billing, source mismatch or unavailable environment. Report failed cleanup explicitly.

## Verified state as of 2026-10-19
User-provided handoff reports a real T4 GPU smoke test via Windows Codex → WSL2 Ubuntu 24.04 → Colab CLI 0.7.4, remote Python 3.13.15 / PyTorch 2.11.0+cu130 / CUDA 13.0, 1024×1024 float32 matmul (20 timings, mean 0.736283 ms), JSON/SHA-256 verification and zero active sessions after stop. This establishes basic GPU remote execution only. Colab CPU, TPU v5e1/v6e1 allocation and PyTorch/XLA, automated GitHub publication and cross-project reuse remain unverified.
