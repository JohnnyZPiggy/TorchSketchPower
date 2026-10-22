# 实验 manifest 配置说明（中文）

> 语言：[English](../../../../examples/reports/manifest.example.json) | **简体中文**

[manifest.example.json](../../../../examples/reports/manifest.example.json) 是 JSON 数据示例，而不是已执行实验的结果。JSON 键名必须保持英文以兼容将来的 Publisher 和验证器。

重要字段：
- `schema_version`：报告结构版本。
- `run_id`：当前实验独立 ID。
- `timestamp_utc`：UTC 时间。
- `status`：PASS / FAIL / NOT RUN / BLOCKED，未跑不能标记 PASS。
- `source_commit_sha`：**被测源码**真实 SHA（不是实验报告 PR 的 commit）。
- `issue_number` 与 `code_pr_number`：关联任务与代码 PR。
- `device`：实际 CPU/GPU 型号。
- `environment`：Python、PyTorch、CUDA 版本。
- `dtype`、`seed`、`command`：精度、随机种子与真实命令。
- `measurement`：同步、预热、重复次数与编译时间是否包含在计时内。

示例中 `NOT_RUN` 和占位符**不是测试通过证据**。