# SAE Project Adoption Smoke Test (No GitHub Actions)

> Language: **English** | [简体中文](../i18n/zh-CN/docs/ADOPTION_SMOKE_TEST.md)

**Purpose:** confirm the **copied** SAE Framework is usable inside a target project, not merely that links work in this documentation repository. A protocol file alone does not make an autonomous agent, and this checklist does not claim tests were executed.

## Test 1 — Inspect before any write
1. Pick a disposable or explicitly authorized target repository and record its default branch and current files.
2. Fix the SAE framework at a **real commit SHA** (or immutable release). Avoid a floating reference to `main`.
3. Prepare a proposed patch/branch; do not overwrite an existing project's `AGENTS.md` or other data without review.

## Test 2 — Make the snapshot self-contained
Confirm the target project contains:

```text
<project>/
  AGENTS.md                       # project-specific, usable from THIS root
  sae.yaml                        # includes actual framework SHA
  .sae/
    AGENTS.md                     # shared SAE agent rules
    README.md / README.zh-CN.md   # documentation landing pages
    SAE_BOOTSTRAP.md / CHANGELOG.md
    docs/                         # architecture, figures and links
    examples/                     # template references
    protocols/                    # role instructions
    workflows/                    # including MATHEMATICAL_RESEARCH.md
    templates/                    # including TENSORIZATION_STUDY.md
    i18n/zh-CN/                   # matching bilingual navigation
```

All files under `.sae/` must come from **the same pinned revision**. Check that copied Markdown links resolve within `.sae/` and do not unintentionally escape into missing directories. The root `AGENTS.md` is a **generated/adapted** entry point: its language notice, paths, owner/repository placeholders and SHA must be correct for its new location. Do not assume the raw example's original relative links remain valid.

## Test 3 — Verify protocol behavior
- **Mentor / GPT:** with `推进导师工作`, check that GPT states a testable mathematical hypothesis and independently selects EXPLORE, `RESEARCH_READY` or a bounded exception. No Scientist signoff; a full study is needed only for formal acceptance.
- **Architect:** with `推进架构师工作`, check GPT autonomously dispatches a concise [Lean Lab batch](../workflows/LEAN_RESEARCH_LAB.md) with a real task goal, mode, source identity, oracle, finite timeout and cleanup, without a Scientist decision. Formal VALIDATE evidence must still meet scientific gates.
- **Engineer:** with `推进工程师工作`, locate one actual ready Issue, falling back to title/body if labels are absent. Confirm a bounded implementation→test→repair→rerun batch can reuse that Issue rather than filing one PR per EXPLORE attempt. Never invent execution.
- **Colab:** Codex owns available local/Colab CLI work (no Scientist compute signoff). Real account access, timeout, one active session and cleanup are required. Publisher stays **NOT VERIFIED** until actually tested; never report GPU/TPU success without real runs.

## Test 4 — Config and fast-lane contract
- Check copied `sae.yaml`: `research_gate.scientist_review_required: false`, `research_gate.required_before_formal_acceptance: true`, `collaboration.per_pr_scientist_approval_required: false`, `experiments.gpu_tpu_require_scientist_budget_approval: false` and `experiments.new_billing_requires_explicit_user_approval: true`.
- Check `workflow.default_mode: EXPLORE`, `workflow.supported_modes` contains `VALIDATE`, finite task timeout, maximum one active Colab session and bounded repairs. Explore probes cannot be mistaken for formal acceptance.
- Check every actual remote reproducibility claim uses exact source commit SHA; dirty local prototypes must be labelled.

## Test 5 — Evidence and security
- Actual Python/CPU tests: `PASS/FAIL/NOT RUN/BLOCKED` with commands, not guessed results.
- No `.github/workflows/` GitHub Actions, no Drive sync, no committed secrets/tokens.
- Changes proposed in a reviewable PR, never force-pushed or silently merged.

## Expected output
A short PASS/FAIL/NOT RUN/BLOCKED checklist with actual paths, SHA and real Issue/PR links; only genuine external-payment, sensitive-data or account/permission actions require user intervention.

**Status:** This document defines a smoke-test procedure; it is **not** evidence that a target project passed the test.
