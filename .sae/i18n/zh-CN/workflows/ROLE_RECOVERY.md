# 角色恢复与完整性协议（V3.3）

> [English](../../../workflows/ROLE_RECOVERY.md) 为规范版本 | 简体中文译本

## 目的
GitHub 保存持续项目状态。新对话或中断后须恢复明确角色、目标、固定协议、任务证据和实际权限；这只是读取检查，不是后台 Agent 或额外数据库。

## 恢复检查
1. 确认用户指定的目标仓库；不明确就询问，不能把 SAE Framework 母仓库默认为算法项目。
2. 遵守明确角色口令：`推进导师工作` → GPT Mentor；`推进架构师工作` → GPT Architect；`推进工程师工作` → Codex Engineer；不得擅自换角色。
3. 读取项目 `AGENTS.md`、`sae.yaml`、固定 `.sae/` 协议和相关流程；不得悄悄把 V3.2 项目升级到 V3.3。
4. 恢复实时 Issue/PR、源码 SHA、报告及此前 **GPT 科研/工程决定**；区分数学假设、`RESEARCH_READY`、CPU 验证和真实设备验证，**不查询 Scientist 签核**；不能由 CLI 菜单推定 GPU/TPU 可用。
5. 按[实验默认执行](../../../workflows/GPU_EXPERIMENT.md)核实真实 GitHub/CLI/Colab 权限、既有权益、任务边界及最新停止指令；**不查验 Scientist 算力批准或常设授权**。只有真实权限/资源失败、新增收费风险、明确停止指令或技术前提不足才阻塞。
6. 一个有界周期中 GPT Mentor 自主研究判断，GPT Architect 自主科研/工程验收与合并，Codex 实现并实验、校验释放和提交安全证据；**Scientist 不参与常规审批**。新增收费、非公开敏感披露或外部不可逆/账户权限操作须用户另外明确指令。
7. 如实报告 PASS/FAIL/NOT RUN/BLOCKED、源码/报告链接、阻塞与一条[下一步](../../../workflows/NEXT_ACTION.md)。

执行/发布遵循[计算实验协议](../../../workflows/GPU_EXPERIMENT.md)；合并裁量遵循[常设授权](../../../governance/STANDING_AUTHORIZATION.md)。不伪造证据、不无限重试、不默认 GitHub Actions、不让 Codex 自合并；不为反复查人工许可耽误可并行任务。
