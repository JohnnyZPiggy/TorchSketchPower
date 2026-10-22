# SAE V3.3 架构与边界

> [English](../../../docs/ARCHITECTURE.md) 为规范版本 | 简体中文说明

![SAE V3.3 原生卡片式组织架构图](../../../docs/figures/SAE_Framework_V3.3.zh-CN.svg)

[查看高清 SVG 矢量原图](../../../docs/figures/SAE_Framework_V3.3.zh-CN.svg)

[可编辑 Mermaid 源码 (.mmd)](../../../docs/figures/SAE_Framework_V3.3.zh-CN.mmd)

中英文独立 SVG 依据已确认的 ChatGPT 原生卡片布局重绘，展示 **PR #33 后 GPT 自主决策快速通道**：Scientist 设定目标而不担任常规审批人；GPT Mentor/Architect 自主判断科研及工程，Codex 执行有界实验，GitHub 证据回流 GPT。`.mmd` 和 README Mermaid 保留为可编辑的*逻辑图*；两种语言的展示图均体现真实权限、数据/付费边界及实测证据要求。


## 两个同等重要的目标
**工程生产力：** 以低协调与计算成本构建正确、可复现、可维护的算法包。  
**科学学习：** 深化 Scientist 对数学结构、数值方法、PyTorch、异构计算与性能结果的理解。

## 职责
- **Scientist：** 设定或调整目标、随时叫停；不负责常规数学、实验、费用额度、T3 或合并审批。
- **GPT Architect + Mentor：** 自主作出数学、科研准备、工程验收和合格 PR 合并决定，开展指导、派单与真实证据审核，依据[常设授权](../../../governance/STANDING_AUTHORIZATION.md)执行。
- **Codex Engineer：** 实现和测试，直接执行本地 CPU 与现有账户 Colab CLI CPU/GPU/TPU 实验，校验下载结果、释放会话、提交证据 PR；不得自合并。
- **GitHub：** 唯一长期任务与证据中心（Issues、PR、源码 SHA、数学/工程/实验报告）。
- **Colab CLI：** 计算执行端；Google Drive 仅可选 Notebook 临时空间，不是结果同步渠道。

## 多轮循环
GPT 自主决定简明数学研究，与生态复用、CPU 参考及 `PROBE_ONLY` 设备探针并行 → Codex 实现/实验 → 真实 GitHub 证据 PR → GPT 科研/工程验收、合并与导师讲解；无 Scientist 签批。失败可以回到数学或工程阶段，并非单向流水线。

实验分为 **固定 SHA 安装 → 不写 GitHub 的正确性/Benchmark → 可选、GPT 审核的非敏感安全报告 PR** 三个阶段（敏感/非公开发布及新增收费仍需用户独立授权）。TPU/PyTorch-XLA 需单独实测，不使用 GitHub Actions 或强制付费 CI。

## 已验证与未验证
据 2026-10-19 交接，Windows Codex 经 WSL2/Colab CLI 完成 T4 GPU smoke test、SHA-256 校验和会话清理。Colab CPU、TPU/PyTorch-XLA、GitHub 自动发布和跨项目闭环仍属 **NOT VERIFIED**。

参见[研发流程](../../../workflows/RESEARCH_PIPELINE.md)、[三文档交接](../../../workflows/THREE_ARTIFACT_HANDOFF.md)和[计算实验](../../../workflows/GPU_EXPERIMENT.md)。旧项目固定快照不会自动升级。
