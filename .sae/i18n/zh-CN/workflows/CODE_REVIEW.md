# 技术审查与合并关口

> 语言：[English](../../../workflows/CODE_REVIEW.md) | **简体中文**

## GPT 总架构师依据证据审查
- **数学：** 目标、假设、不变量、参考基线、证明或反例是否有效。
- **API/代码：** 模块化、dtype/设备、形状契约、内存与可维护性。
- **正确性：** 回归、边界、随机、对抗样例及有依据的误差容忍度。
- **CPU 证据：** 真实命令、测试结果、环境和失败日志。
- **GPU 证据：** 若声称 CUDA 加速，必须用对应源码 SHA 提供 Colab 精度/性能报告。
- **诚信：** 不虚构测量；明确哪些测试未运行或因工具缺失而阻塞。
- **安全：** 不泄露 PAT、token、私人文件、假数据；Publisher 凭证严格限权。
- **流程：** 不添加 GitHub Actions/付费 CI；关联 Issue、PR 清晰；GPT 按常设本人公开仓库权限自主合并，毋须 Scientist 逐次签批。

## 审查结果
- **REQUEST_CHANGES：** 有缺陷、歧义、证据不足或不可信。
- **CONDITIONALLY_READY：** 若 GPU 是正式验收条件但未运行，Codex 直接开展实验；GPU 非验收项的 CPU-only PR 可以按真实证据合并，无 Scientist 审批。
- **ACCEPTED：** 验收证据满足任务要求，GPT 记录理由。
- **MERGED：** 只有 GitHub 实际合并成功才能标记为已合并；审查评论不等于合并。

## 合并政策
Codex 不得自我合并。GPT 依[常设授权](../../../governance/STANDING_AUTHORIZATION.md)自主决定合格 T1/T2/T3 PR 合并，不再请求 Scientist 研究/工程/合并签核；仍须核实真实仓库所有权、公开状态、测试 SHA、权限及分支保护。包括实验报告在内，优先使用 PR，而不是直接修改 `main`。不得 force-push 保护分支或覆盖历史。不使用 GitHub Actions 时写 `CI: NOT CONFIGURED (by design)`，不能写“CI Passed”。

## 性能审查
比较时确保问题规模、设备、dtype、结果正确性相同；如实披露编译时间、预热、GPU 同步、重复次数、聚合方式和波动，速度不能取代正确性。