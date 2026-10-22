# SAE Engineering Design & Implementation Report — <algorithm>

> Language: **English** | [简体中文](../i18n/zh-CN/templates/ENGINEERING_REPORT.md)

**Target project:** `<owner/repo>`  
**Algorithm / milestone:** <name>  
**Related Issue(s) / implementation PR:** <links>  
**Mathematical Research:** `docs/research/<algorithm>-tensorization.md` — approved `RESEARCH_READY` / documented narrow exception / N/A for scaffolding  
**Architect:** GPT Chief Architect · **Engineer:** Codex · **Scientific owner:** Human Scientist  
**Candidate implementation source commit:** `<40-char-SHA or NOT YET AVAILABLE>`  
**Status:** SPECIFIED / IMPLEMENTING / REVIEW / CPU_VERIFIED / BLOCKED (describe actual evidence)

## 1. Mathematical and engineering contract (Architect)
Link the approved mathematical study. Specify **exactly** what is implemented: original and tensorized variants, shapes, dtypes, supported device semantics, reference oracle, numerical tolerances, boundaries and assumptions. Refer to equations; do not duplicate the entire math study.

## 2. Software design (Architect → Codex)
Specify module locations, Python public API, CLI arguments, input/output schema, optional `torch.compile`/batching path, platform portability requirements and expected resource constraints. Identify implementation tasks, dependencies and acceptance gates.

## 2a. Ecosystem Review — Build vs. Reuse (Architect; before Codex dispatch)

**Review depth:** NATIVE_REUSE (one-line sufficient) / TARGETED_REVIEW / DEEP_REVIEW (only if justified)  
**Search date and sources:** <official PyTorch docs, maintained package URLs, upstream/reference code; or NOT VERIFIED>  

| Option / candidate | Mathematical/API fit | License, maintenance, dependencies | CPU + cross-device / compile / dtype risks | Decision |
| --- | --- | --- | --- | --- |
| Native PyTorch primitives | <evidence> | <version/none> | <known / UNKNOWN> | REUSE / ADAPT / REJECT |
| Third-party package (if relevant) | <link/version> | <license/status or UNKNOWN> | <supported / UNKNOWN> | REUSE / ADAPT / REJECT |
| Algorithm reference / own implementation | <paper/code link> | <license or UNKNOWN> | <baseline and risks> | REUSE / ADAPT / BUILD |

**Selected Build-vs-Reuse approach and reason:** <one to three sentences; distinguish verified facts from hypotheses>.  
**Codex handoff:** <version constraints, minimal dependencies, adapter boundaries, fallback, CPU oracle/edge tests, clean install and compile smoke tests>.  
**Unverified claims / follow-up:** <NONE / specific verification task>.  

Keep this review short; do not add a fourth project artifact. A library's presence is not evidence of correctness, acceleration or device portability. See [Ecosystem Review](../workflows/ECOSYSTEM_REVIEW.md).

## 3. Implementation record (Codex)
| Component / changed path | Purpose and math link | Design choice / limitation |
| --- | --- | --- |
| `src/...` | | |
| `tests/...` | | |
| `benchmarks/...` | | |

Document deviations with an explicit GPT Architect scientific/engineering decision and rationale, not silent assumptions or a Scientist signoff.

## 4. Actual validation evidence (Codex)
| Test / correctness comparison | PASS / FAIL / NOT RUN / BLOCKED | Real command, environment, seed and evidence link |
| --- | --- | --- |
| Reference/oracle equivalence | NOT RUN | |
| CPU unit and regression tests | NOT RUN | |
| Randomized/adversarial edge cases | NOT RUN | |
| CPU benchmark (if applicable) | NOT RUN | |
| GPU / TPU (Codex-run by default; formal acceptance evidence required) | NOT RUN | Link separate experimental report, **do not invent GPU runs** |

State measured maximum/relative error *only if actually measured*, tolerance policy and known failures. For GPU performance conclusions, link `reports/gpu/<run-id>/summary.md` instead of copying its values.

## 5. Reproduction and handoff (Codex)
- **Tested source commit SHA:** <real SHA / NOT RUN>
- **Python/PyTorch/dtype/device:** <versions / NOT RUN>
- **Commands, inputs, seeds:** <actual commands>
- **Open PR / Issue and artifacts:** <links>
- **Scoped CPU/GPU/TPU experiment instruction for Codex (no compute signoff):** <candidate SHA, CLI, dataset/size, tolerances>
- **Known blockers and risks:** <details>

## 6. Review and decision (GPT Architect)
- **Architect review:** REQUEST_CHANGES / CONDITIONALLY_READY / ACCEPTED (with rationale and link).
- **GPT scientific/engineering decision:** <status, evidence or uncertainty link>; no human approval.
- **Follow-up:** Fix / rerun CPU / Colab experiment / revisit mathematics.
- **Learning insight:** optional single algorithmic or numerical insight, not a mandatory essay.

This engineering document is **not a substitute for GitHub PR review**, cannot certify unexecuted GPU tests, and must not overwrite other evidence.
