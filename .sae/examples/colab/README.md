# Thin Colab Notebook — illustrative cell plan

> Language: **English** | [简体中文](../../i18n/zh-CN/examples/colab/README.md)


**This directory is documentation, not a working notebook or Publisher.** GPT designs orchestration; Codex implements and runs authorized Colab CLI experiments. The Scientist approves resources and reviews scientific conclusions; the cells below are illustrative only.

See the [Three-Step Colab Contract](../../workflows/COLAB_TWO_COMMAND.md).

```python
!pip install "git+https://github.com/OWNER/REPO.git@<EXACT_SOURCE_COMMIT_SHA>"
!python -m <package>.benchmarks.run --device cuda --out reports/gpu/<run-id>
!python -m <package>.benchmarks.publish --report-dir reports/gpu/<run-id>
```

The third cell is optional and must run only after inspecting results. `GITHUB_TOKEN` is a Colab Secret: subprocess access needs real validation or secure `subprocess.run` fallback; do not put token literals in notebook or logs. Publisher remains unimplemented until validated.
