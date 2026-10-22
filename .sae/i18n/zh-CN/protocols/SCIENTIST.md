# 人类科学家协议（V3.3）

> [English](../../../protocols/SCIENTIST.md) 为规范版本 | 简体中文译本

Scientist 是科研目标提出者和可随时叫停/调整的用户，**不再担任日常科研、实验或合并审批人**。范围内决定委托 GPT，详见[常设授权](../../../governance/STANDING_AUTHORIZATION.md)。

## 人类设定目标，不设签核队列
- Scientist 可提出科研方向、偏好及新的停止/撤销指令。GPT 自主判断数学假设、`RESEARCH_READY / RESEARCH_BLOCKED / NOT_TENSORIZABLE`、科研结论与有界实验验收。
- 实验目标、数值容差、参考基线和精度/性能取舍由 GPT Mentor/Architect 自主决定；Scientist 可参与但**不是必须审批**。
- **不承担算力审批职责：** 按[实验默认执行](../../../workflows/GPU_EXPERIMENT.md)，Codex 在真实权限和技术条件允许时直接使用现有账户权益开展 CPU/GPU/TPU 实验，**不查验 Scientist 算力批准或常设授权记录**。Scientist 可随时发新指令暂停/收窄未来工作；新购买、充值、按量付费仍须用户明确同意。
- GPT 自主决定范围内科研、内部治理/工程和合格 PR 合并。新增收费、外部账户权限修改、敏感非公开披露及外部不可逆破坏须用户另外明确指令；真实服务商规则继续有效。

## 委托执行
Codex 执行本地 CPU 与技术条件允许的 Colab CLI CPU/GPU/TPU 实验，下载和校验结果，释放会话，并通过 GitHub 分支/PR 提交证据。GPT 审核并决定科研意义；Scientist 可选提出质疑或修改目标，但无需日常审批、操作 Notebook 或搬运文件。

参见[计算实验](../../../workflows/GPU_EXPERIMENT.md)、[数学研究](../../../workflows/MATHEMATICAL_RESEARCH.md)和[三文档交接](../../../workflows/THREE_ARTIFACT_HANDOFF.md)。Drive 仅为可选 Notebook/临时工作空间，不作为结果交换层。

只有真实测试后才能标记硬件或发布能力为已验证。截至 2026-10-19，TPU/PyTorch-XLA 和 GitHub 自动发布端到端仍未验证。
