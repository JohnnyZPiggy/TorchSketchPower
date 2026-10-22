# Technical Review and Merge Gates

> Language: **English** | [简体中文](../i18n/zh-CN/workflows/CODE_REVIEW.md)


## Architect review is evidence-driven
- **Mathematics:** objective, assumptions, invariant, oracle/baseline, proof or counterexample as relevant.
- **API/code:** modular design, dtype/device handling, shape contracts, memory behavior, maintainability.
- **Correctness:** deterministic regressions, reference comparison, randomized and adversarial cases; explicitly justify tolerances.
- **CPU evidence:** actual test commands, results, environment and failing logs where applicable.
- **GPU evidence:** exact tested commit, Colab environment, correctness and performance; **required for any CUDA speedup claim**.
- **Integrity:** real measurements only; distinguish partial tests, unavailable tooling and skipped checks.
- **Security:** no leaked PATs, tokens, private files, fake data or unrestricted publisher scopes.
- **Process:** no GitHub Actions/paid CI, Issue link, coherent PR diff, existing GPT owner-public merge delegation and real tool permissions; no per-PR Scientist signoff.

## Decision outcome
- **REQUEST_CHANGES:** defects, ambiguities, inaccurate claims or missing mandatory tests.
- **CONDITIONALLY_READY:** evidence for a required GPU/formal acceptance condition is NOT RUN; Codex may execute without Scientist approval. CPU-only scope can merge if GPU is not required.
- **ACCEPTED:** required evidence complete; Architect records rationale.
- **MERGED:** only after authorized action succeeds. A review comment does not mean merged.

## Merge policy
- Codex never self-merges.
- GPT Architect independently decides eligible T1/T2/T3 PR merges under [Standing Authorization](../governance/STANDING_AUTHORIZATION.md) without Scientist approval; verify real owner/public access, diff/tested SHA, evidence and merge protections.
- Prefer reviewable PR over direct `main` edits, including experiment reports.
- Never force-push protected branches or overwrite others' history.
- If GitHub checks are unavailable because Actions are disabled, display `CI: NOT CONFIGURED (by design)`; this is **not** a passed test.

## Performance gates
Compare identical problem sizes, dtype, correctness level, device, clock/setup and data transfers consistently. Disclose compilation cost, warmup, GPU synchronization, repetitions, distribution and variability. Avoid interpreting raw speedup as numerical quality.
