# SAE Bootstrap — Project Adoption Protocol (V3.3)

> English normative | [简体中文](i18n/zh-CN/SAE_BOOTSTRAP.md)

**Command:** `按照 SAE Framework V3.3 初始化这个项目`

## Inputs and preflight
Confirm target `owner/repo`, default branch, scientific goal, actual tool permissions, existing AGENTS/config, Issues/PRs and a **real immutable SAE commit SHA**. Read the selected framework revision rather than assuming a URL loads it. Do not silently overwrite existing content or upgrade a project's pinned snapshot.

## Adopt a self-contained pinned snapshot
1. Create or update project-root `AGENTS.md` using [project template](examples/project/AGENTS.md) and `sae.yaml` using [config](examples/project/sae.yaml), replacing every placeholder.
2. Copy **one pinned SAE commit** into project `.sae/`, including constitution, bootstrap, protocols, workflows, templates, governance, documentation, examples and bilingual mirrors. Preserve working relative links and record the exact source SHA. This is a documentation snapshot, not a runtime or credential grant.
3. Propose changes on a new branch/PR. Do not install GitHub Actions, paid hosted CI, or a Google Drive synchronization layer.
4. Verify pinned links and config in the **target project layout**, not just this source repository. Use [Adoption Smoke Test](docs/ADOPTION_SMOKE_TEST.md) for manual checks; an automatic bootstrap tool is not assumed to exist.

## Research and engineering initialization
- For new algorithms/major tensorization redesigns, GPT Mentor/Architect prepares a concise [mathematical study](workflows/MATHEMATICAL_RESEARCH.md) and **autonomously decides** `RESEARCH_READY` or scoped hypothesis; no Scientist signoff. Parallel safe probes and reference preparation are allowed.
- Architect applies [Lean Research Lab](workflows/LEAN_RESEARCH_LAB.md): choose `EXPLORE` for rapid, bounded hypothesis/PROBE_ONLY tests and `VALIDATE` for formal evidence; perform a brief parallel [Ecosystem Review](workflows/ECOSYSTEM_REVIEW.md), then dispatch **one bounded Codex Issue batch**, not a sequence of manual approvals.
- Codex implements Python/CLI, reference/edge tests and direct local/Colab CPU/GPU/TPU work; GPT owns scientific conclusions, readiness and acceptance, **without Scientist approvals**. Use finite task timeout, default single active Colab session and real evidence; new billing and sensitive external actions require separate user instruction.
- Use [Compute Experiment Protocol](workflows/GPU_EXPERIMENT.md): pinned source SHA install → benchmark without GitHub writes → optional separately authorized safe report publication to a GitHub branch/PR. No claim of working Publisher, TPU/PyTorch-XLA or automatic cross-project execution without real tests.
- GitHub holds task and report evidence. Drive, if used, is only a lightweight Colab notebook/temporary workspace.

## Acceptance and failure
Check root AGENTS, `sae.yaml` **without Scientist research/compute approval flags**, complete pinned `.sae/` snapshot including Lean Lab, bilingual relative links, `EXPLORE/VALIDATE` behavior, role recovery, task timeout, one-session default and formal evidence gates. Codex records actual CPU/accelerator outcomes; Architect reviews and exercises eligible final merge discretion under [Standing Authorization](governance/STANDING_AUTHORIZATION.md), subject to real tool permissions and external new-billing/sensitive-data constraints, not Scientist research signoff.

Re-running bootstrap is **idempotent**: inspect and propose a diff, never silently replace user work, force-push, expose secrets, publish data or merge without applicable authority. Report COMPLETED / NOT RUN / BLOCKED and next action. Existing projects opt into V3.3 through a reviewed pinned-snapshot update; do not change them implicitly.
