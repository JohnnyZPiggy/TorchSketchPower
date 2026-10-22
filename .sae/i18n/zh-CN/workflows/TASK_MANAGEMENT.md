# GitHub 任务管理与交接协议

> 语言：[English](../../../workflows/TASK_MANAGEMENT.md) | **简体中文**

**唯一正式任务队列：GitHub Issues**，不是不可追踪的私下聊天记录。

## 推荐标签体系
- 负责人：`role:engineer`、`role:architect`、`role:mentor`、`human:scientist`；旧 Issue 的 `agent:codex` 标签保持兼容。
- 状态：`status:ready`、`status:in-progress`、`status:review`、`status:experiment`、`status:blocked`、`status:accepted`。
- 工作类型：`kind:math`、`kind:engineering`、`kind:experiment`、`kind:learning`。
- 优先级：`priority:p0`、`priority:p1`、`priority:p2`。

如果缺少创建标签的权限，就在 Issue 评论里写出真实状态；不要假装已应用标签。Assignee 必须是真正的 GitHub 账户，不能使用不存在的机器人用户名。

## 工程任务前的数学研究关口
新算法/重大改写由 Mentor/Architect 自主记录简明 `RESEARCH_READY` 报告或限定数学假设/例外，详见[数学研究](MATHEMATICAL_RESEARCH.md)，**无需 Scientist 签批**。只要有可检验的工程范围，Engineer Issue 即可标 `status:ready`；独立探针、参考实现与初始化可和 R1/R2 并行，正式验收仍需证据。

## Issue/PR 与三文档关联
按[三文档交接协议](THREE_ARTIFACT_HANDOFF.md)关联 Mentor/Architect 决定的数学研究、精简工程报告和 Engineer 实测证据。实验 PR 应指明被测源码 SHA 及上游 Issue/PR；不建立第四份状态日报，模板不能冒充实测证据。

## Lean Lab 精简执行
以[Lean Research Lab](../../../workflows/LEAN_RESEARCH_LAB.md)为统一的 **EXPLORE / VALIDATE** 模式和有界批次契约。EXPLORE 在**同一个 Issue 或工作分支**只需假设/源码/命令/结果简记，不为每次探针建 PR 或写全套三文档；VALIDATE 才集中关联正式数学、工程和实验依据。Architect 按证据切换模式，无需 Scientist 签字。

## 生命周期
1. **Architect 立即派单：** 使用现有或一个新 Issue，写明源码身份、模式、最小 oracle、实验目的、有限超时和清理计划；有安全可执行的任务就标就绪，不等待人类签批。
2. **Engineer 领取任务：** 在 Issue 留下接受评论并改为 in-progress，同一项任务只允许一个当前负责人。
3. **批内实施与实验：** 使用 `feat/<issue-number>-<slug>` 分支，在任务超时和有界尝试内完成实现→测试→诊断→修复→复测，每次尝试不另行请求批准；积累可用成果后再创建 PR。只有满足全部验收时才用 `Closes #N`，GPU 待验证时用 `Refs #N`。
4. **Architect 做一次基于证据的审核：** 核对 SHA/Diff 和相关正确性证据；Engineer 可同时跑合适 CPU/GPU 探针，再根据结果进行正式 Benchmark，不无谓串行。
5. **Engineer 默认使用现有账户 Colab CLI：** 远程安装固定精确 SHA，默认同一时间一个活动会话，有限超时并核实清理；多次探索合并为**一次批次证据汇总**，可选发布须单独实测验证。无 Scientist 算力/价格关口，真实数值、权限或收费阻塞须记录。
6. **Architect 做一次实质审查并自主决定 MERGE / DO_NOT_MERGE：** 核验真实 Diff/SHA/测试/权限，问题在**同一 Issue**明确派回修复，不增加重复交接或 Scientist 签字。
7. **Mentor 总结：** 可选记录相关数学/工程学习要点，不能用学习笔记替代测试。

## 状态一致性
GitHub API 写入可能失败、标签缺失、PR 评论可能过时；关键操作后重新读取状态。引用 Issue、PR、run ID 和源码 SHA 交接；不能未经说明混用不同版本 Benchmark。组织流程是可反复交替的迭代，而不是固定流水线。
## 每轮结束的下一步口令
每轮实质性工作发送最终回复前执行[下一步交接完成关卡](NEXT_ACTION.md)：提供真实状态、证据、一条完整可复制的推荐口令，确有不同路径时最多两条备选。

## 角色恢复与防止出戏
每轮开始按[角色恢复协议](ROLE_RECOVERY.md)检查身份、固定协议、真实证据和权限；角色不匹配时停止并交接。

## 全部本人公开仓库由架构师永久独立决定是否合并
Architect 对本人公开仓库的合格 PR 依[常设授权](../governance/STANDING_AUTHORIZATION.md)独立作出 MERGE / DO_NOT_MERGE 决定，前提是实时核实所有权、公开状态、权限、真实 Diff/SHA/证据，不设 Scientist 科研/T3 审批。不需逐 PR 申请合并许可；Engineer 不自合并、不后台扫仓库。具体范围、T1/T2/T3 与合并关口以所链接治理协议为准。

