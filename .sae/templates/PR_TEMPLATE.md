# SAE Pull Request: <title>

> Language: **English** | [简体中文](../i18n/zh-CN/templates/PR_TEMPLATE.md)


Closes/Refs: #<issue>
Candidate source commit: `<SHA>`

## Scope and mathematical motivation
Describe changes, problem, assumptions and any changes to public API.

## Evidence (no implied execution)
| Check | Status: PASS / FAIL / NOT RUN / BLOCKED | Command / link |
| --- | --- | --- |
| Unit/regression tests | NOT RUN | |
| Numerical baseline comparison | NOT RUN | |
| CPU performance benchmark | NOT RUN | |
| Colab GPU correctness | NOT RUN | |
| Colab GPU performance | NOT RUN | |

## Three-artifact links
- GPT-reviewed formal mathematics (VALIDATE): `docs/research/<algorithm>-tensorization.md` / N/A for EXPLORE or infrastructure
- Engineering and actual CPU evidence: `docs/engineering/<algorithm>-engineering.md`
- Actual Colab experiment: `reports/gpu/<run-id>/summary.md` / NOT RUN
- Tested source commit SHA: `<SHA>` (distinct from report publication SHA)

## Reproduction
Python/PyTorch version, device, seed, exact commands, data source.

## Risks / limitations
State numerical differences, untested hardware, accuracy/performance trade-offs, skipped checks.

## Review requests
GPT Architect: review actual tested SHA, numerical evidence and risk, then accept / request fixes / merge. No Scientist experimental signoff. For EXPLORE, summarize one batch instead of requiring a PR for every probe.

## Learning opportunity (optional)
One question or insight worth discussing in Mentor mode.
