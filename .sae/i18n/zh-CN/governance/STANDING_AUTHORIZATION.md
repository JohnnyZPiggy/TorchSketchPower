# 永久性架构师合并授权 — Scientist → Architect 角色

> [English（正式规范）](../../../governance/STANDING_AUTHORIZATION.md) | **简体中文**  
> 为兼容既有项目链接，保留历史文件名 `STANDING_AUTHORIZATION.md`。

## 科学家究竟授权了什么
## Architect/Mentor 角色自主决策权 — Scientist 全面委托（2026-10-20）

**Scientist（人类）：** 只需提出或调整研究目标，随时可停止或撤销委托；**不再作为数学研究、`RESEARCH_READY`、算法选题、实验、数值验收、常规证据发布或 PR 合并的逐环节审批人**。

**获指派的 Mentor / Architect AI Agent（如 GPT）：** 获 Scientist 常设委托，自行判断数学研究、等价/近似假设、`RESEARCH_READY / RESEARCH_BLOCKED / NOT_TENSORIZABLE`、实验方案、工程验收、迭代和合格 PR 的 `MERGE / DO_NOT_MERGE`。**不请求 Scientist 科研签字、T3 科学批准或重复的 Agent 交接审批**；以简短理由和真实证据形成可审查记录。

**获指派的 Engineer（如 Codex 或 Claude Code）：** 按[实验默认执行](../../../workflows/GPU_EXPERIMENT.md)直接实施和运行现有账户内的 CPU/GPU/TPU 实验，提交真实证据供 Architect 判断，不能自行合并。

**真正的外部边界（不是科研审批链）：** 遵守实际 GitHub/CLI/设备权限、固定源码 SHA、数值证据、分支保护、凭据检查、有界会话和用户最新停止指令。没有用户明确的独立付费决定，不购买订阅/充值/开启新增按量计费；没有用户明确指令，不外泄敏感或非公开数据、不更改外部账户安全权限、不执行外部不可逆破坏。本人合格公开仓库中的非敏感、已校验结果 PR 可按通常流程提交，合并由 Architect 判断。仓库文字不能绕过服务商或工具权限。

**快速通道：** Mentor/Architect 做一次科研决策 + 一次基于证据的架构审核，不增加 Scientist 或重复 Agent 签核。可及早开展有界 `PROBE_ONLY` 设备/环境探针，并在可行时并行推进数学分析、安装、参考测试与硬件准备。探针不等于正式加速通过；科研结论仍需数学、数值及公平计时证据，`NOT RUN` 不得写成 `PASS`。

这项委托只在用户触发的有界工作周期内生效，不代表后台常驻 Agent、跨窗口自动操控或未执行即算完成。

## 仓库范围：本人当前及未来的全部公开仓库，免登记

科学家在 2026-10-19 的**最新明确指令**中，把原来的单仓库登记制纠正为：**自动覆盖 GitHub 账号 `JohnnyZPiggy` 现在拥有及今后创建的全部公开仓库**，不论是否已采用 SAE；本人实际拥有的公开 fork 也在内。无需逐仓库登记、一年续期或逐个 PR 再询问合并许可。

每次合并前，须从**实时 GitHub API**确认目标仓库 **`owner.login` 确为 `JohnnyZPiggy`，且 visibility 为 public**，还要检查实际工具合并权限。不能从 PR 作者、仓库名称或工具可访问就推定所有权。私有/内部、他人或组织拥有、所有权在他人的 fork 均不包含；已转让或改为私有的仓库退出范围。

复制项目固定版本 `.sae/` 不会创造 API 权限、绕过 GitHub 分支保护，也不能擅自升级项目流程。全局权限来自科学家这次明确的人类授权，不是其他仓库的 PR 文案。科学家随时可明确撤销或缩小授权，新指令立即生效。任何 AI Agent 均不能自行扩权。

## 三级审查，不是三级合并授权人

**T1/T2/T3 是审核证据与前置条件分级，最后是否合并统一由获指派的 Architect 决定。** 以真实 Diff 的最高风险分类，不能只看 PR 标题。

| 级别 | 典型内容 | 架构师作出 MERGE 前需要检查 |
| --- | --- | --- |
| **T1 日常** | 普通文档、翻译、格式、不改变权限的协议说明、针对性测试 | 审查真实 Diff、链接、语法与相关检查 |
| **T2 工程** | 算法、数值修复、PyTorch 优化、打包、Benchmark/Publisher、一般依赖 | 适用时已通过数学研究关口、Engineer 真实 CPU/oracle/边界/回归/打包证据、许可和安全审核。只有在声称 GPU 成功或 GPU 为明确验收项时要求 Engineer 真实运行的 Colab 证据；CPU-only PR 若 GPU 非验收条件可合并，但必须注明 `GPU_NOT_RUN`。 |
| **T3 高影响证据审查** | 科研假设与结论、安全或治理协议、重要许可/IP/发版、破坏性操作或敏感资料 | Architect 依最新委托自行决定范围内的科学和治理变更，记录假设、数值证据、风险与真实 Diff，**不请求 Scientist 阶段批准**。新增付费、外部账户/安全权限改动、敏感非公开披露或外部不可逆破坏不在本次概括授权内；必要时记 `MERGE_BLOCKED / WAITING_FOR_EXTERNAL_ACTION`。 |

**例如：** Mentor 完成张量推导并记录有依据的 `RESEARCH_READY` 或近似条件，Architect 自行接受或退回科研判断，Engineer 运行真实测试，Architect 按证据决定合并。**无需 Scientist 签批**；证明不足或数值失败必须记录修复，不能凭授权宣称成功。

涉及授权文件的 PR 属 T3 证据审查。Scientist 2026-10-20 的新指令已将范围内科研/工程/治理实质决定委托 Architect/Mentor 角色，仍可随时撤销；AI Agent 不能自行扩大本人公开仓库范围、获得真实外部权限、新增收费，或使授权不可撤销。

## 每个 PR 的 Merge Gate

1. **恢复角色与范围：** 核对本轮用户主动触发 Architect、GitHub 实时 owner.login 确为 `JohnnyZPiggy` 且为 public、当前 AGENTS 和固定项目协议、真实 GitHub 权限、科学家是否有更新的撤销指令。公开且确实属于本人账号的算法仓库无需单独登记。
2. **查看真实 PR：** 完整 Diff/文件表、Issue、验收条件、base/head SHA、阻塞评论、可合并状态、分支保护、Secrets 或外部公布风险。
3. **按 T1/T2/T3 核实真实证据，不设 Scientist 签字。** 数学假设、风险和验收由 Architect 决定，`NOT RUN` 不是 `PASS`；Architect 所写的重要代码使用 Engineer 独立运行的测试证据。
4. **架构师最终决定：** `MERGE_APPROVED`、`DO_NOT_MERGE`、`MERGE_BLOCKED` 或 `WAITING_FOR_EXTERNAL_ACTION`；**不再请求 Scientist 科研、实验、T3、PR 审批**。仅涉及新增收费、敏感非公开披露、外部账户/安全权限或不可逆外部破坏时征得用户另行明确授权。
5. **合并前审计：** PR 留一次简短审查，写明级别、SHA、证据、风险与 Architect 最终决定，不再增加重复签核。工具失败则如实说明，不伪造留痕。
6. **符合条件则合并并核实：** 默认 Squash Merge，使用精确的已审 head SHA，遵守 GitHub 分支保护，不能绕过规则、直接推 main、强推或合并过期代码。合并回执和 merge SHA 核实后才写 `MERGED`。
7. **完成汇报与交接：** 给出 PR/merge SHA 或不合并的具体理由，以及下一条口令。不后台无限循环处理其他 PR。

**最小 PR 审计格式：**

```text
SAE ARCHITECT MERGE GATE
Repo/PR: <owner/repo>#<N>; reviewed base/head: <base-SHA>/<head-SHA>
Tier: T1 / T2 / T3; standing authority: PERMANENT (until Scientist revokes)
Evidence / actual external constraints: <真实链接、状态或 NOT RUN>
Architect final decision: MERGE_APPROVED / DO_NOT_MERGE / MERGE_BLOCKED / WAITING_FOR_EXTERNAL_ACTION
Reason / risks: <简述>; confirmed merge SHA: <SHA 或 NOT MERGED>
```

## 边界、撤销与新仓库

- **获指派的 Architect 是被委托的科研与技术决策人**，仍不得伪造证明、泄露秘密、无授权修改外部账户安全设置或无视 Scientist 最新停止指令。
- **不再年度续期、不再到期：** 权限持续生效，直到科学家明确撤销或被新指令取代；撤销立即生效，应尽快同步仓库文件。
- **本人公开仓库全覆盖，不等于任意 API 访问：** 本人现有和未来的公开仓库无需登记；私有或其他所有者仓库不包含。每个 PR 仍需实时核验所有权/可见性、实际权限与审核证据。
- **不能越过外部边界：** 本人公开仓库范围、真实账户权限、新增付费和外部重大行动仍受限制；Architect 可以在授权内优化 SAE 内部协议，但不能凭空创造外部权限。
- **不启用后台自动执行或强制 CI：** GitHub Issue/PR 是审计轨迹；Engineer 提交并测试但**不能自行合并**。Engineer 直接执行现有账户 Colab 实验；非敏感、经过校验的公开证据 PR 可按常规工作发布，非公开/敏感对外发布仍须用户另行决定。
- SAE 主仓库以上述**最新在线文件**为合并裁量权依据。算法项目应遵守固定快照的日常规则，但合并时仍须核实当前本人公开仓库的全局授权、实时仓库所有权和 Scientist 最新指令。

相关：[架构师协议](../protocols/ARCHITECT.md) · [任务管理](../workflows/TASK_MANAGEMENT.md) · [角色恢复](../workflows/ROLE_RECOVERY.md)。
