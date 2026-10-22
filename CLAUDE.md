@AGENTS.md

# Claude Code 工作约定

## 角色
- 我的角色是 **Engineer**（见 `.sae/protocols/ENGINEER.md`）：实现代码、跑测试、提交证据。
- 我不自己合并 PR，也不自己批准科学结论；审查和合并由 Architect（GPT）负责。
- 触发词 `推进工程师工作` 表示按 Engineer 协议执行一个有限批次。

## 工作流程
- 目标仓库：JohnnyZPiggy/TorchSketchPower，任务中心 Issue #1。
- 只在 `feat/<issue号>-<slug>` 分支上工作，不直接写 main。
- 动手前确认当前分支、HEAD SHA、对应 Issue。
- 一个里程碑对应一个 Issue、一个分支、一个 PR；探索性尝试不另开 PR。
- 用户已授权：在 feature 分支上自主完成实现、测试、提交和推送，不需要逐步确认。

## 红线
- `.sae/` 是固定快照（SAE-Framework@65338eb），不得修改、不得升级。
- 不启用 GitHub Actions，不引入付费服务，不强推，不合并。
- 上游 MATLAB（Mitchell-Cxyk/SketchPowerIteration）没有 LICENSE：只读论文和逻辑，禁止复制代码。
- 没有证据时，不声称 one-pass 重建正确、与论文等价或 GPU 加速。

## 证据与汇报
- 状态只用 PASS / FAIL / NOT RUN / BLOCKED，没跑的写 NOT RUN。
- PR 描述写清：被测 SHA、命令、Python 与 torch 版本、设备、种子、结果；模板见 `.sae/templates/`。
- GPU 与 `torch.compile` 在验证前一律标 UNVERIFIED。
- 回复保持简短：做了什么、结果、下一步。
- 用户要求：只管工作，做完提交并推送；不提出自己的下一步建议，不要求用户打字或确认。回复只报告做了什么、结果、未验证项。

## 环境（Windows）
- 主 shell 是 PowerShell；路径含空格，需加引号。
- `python` 在 PATH 上是占位程序，用 `py`（Anaconda 3.14）。
- 测试：`PYTHONPATH=src py -m pytest -q`
- 提交信息末尾加 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`。
