# 薄 Colab Notebook 示例说明

> 语言：[English](../../../../examples/colab/README.md) | **简体中文**

此处为说明性 Cell，并非实测命令。Codex 负责获授权的 Colab CLI 实验，Scientist 负责科研决策和 GPU/TPU 资源预审批；参见 [Colab 三步契约](../../../../workflows/COLAB_TWO_COMMAND.md)。

```python
!pip install "git+https://github.com/OWNER/REPO.git@<EXACT_SOURCE_COMMIT_SHA>"
!python -m <package>.benchmarks.run --device cuda --out reports/gpu/<run-id>
!python -m <package>.benchmarks.publish --report-dir reports/gpu/<run-id>
```

第三个 Cell 可选，须先核对结果。`GITHUB_TOKEN` 是 Colab Secret；子进程访问须真实验证或通过安全 `subprocess.run` 备用方案，不得明文输出密钥。Publisher 验收前仍为未实现。
