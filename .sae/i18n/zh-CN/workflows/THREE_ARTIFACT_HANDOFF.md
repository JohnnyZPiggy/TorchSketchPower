# 三文档交接协议：数学、工程、实验

> 语言：[English](../../../workflows/THREE_ARTIFACT_HANDOFF.md) | **简体中文**

## 为什么要建立三类文档？
SAE 在**VALIDATE 正式验收**阶段用三个关联的科学研发成果交接，而不依赖聊天历史或重复日报。**EXPLORE 探索**按[Lean Lab](../../../workflows/LEAN_RESEARCH_LAB.md)只用一份简短批次记录，**无需每次试错写全套报告**。这三类文档保存在**每个算法项目自己的 GitHub 仓库**；SAE Framework 母仓库提供的是协议和模板。GitHub Issues/PR 仍负责任务和审查状态。

| 文档及算法项目路径 | 负责人 / 决策权 | 主要回答的问题 | 更新时机 |
| --- | --- | --- | --- |
| **数学研究文档** `docs/research/<algorithm>-tensorization.md` | **GPT 科学导师**研究并自主决定；Architect 可复核 | 原算法有哪些矩阵向量/matrix-free/张量性质？哪些数学等价变换成立？ | 新算法、重要数学改动或新发现 |
| **工程实现文档** `docs/engineering/<algorithm>-engineering.md` | **GPT 总架构师**设定接口和验收；**Codex**记录实现及真实测试；架构师审查 | 代码如何实现？什么被真正测试过？ | 工程设计交接、重要 PR 或版本 |
| **实验验证文档** `reports/gpu/<run-id>/summary.md`，并附结构化结果 | **Codex** 直接运行现有账户 CPU/GPU/TPU 实验，GPT 审核证据 | 哪个 SHA、设备、精度与规模真正完成验证？ | **每次发布或正式验收的 VALIDATE 运行**保留唯一 run ID；探索只需批次简记 |

## 三段交接契约
- **数学 → 工程：** 正式 VALIDATE 由 GPT 记录 `RESEARCH_READY`（或有界假设）、推导、张量形状和参考基线；EXPLORE 可更早启动可检验原型与 `PROBE_ONLY`，但不得冒充正式验收。
- **工程 → 实验：** 工程报告通过实际源码 **commit SHA**、CLI、CPU 正确性证据和架构师的实验矩阵确定下一步 Colab 工作。**CPU 通过不意味着 GPU 通过。**
- **实验 → 数学/工程：** 将精度失败、硬件瓶颈、真实测量反馈给相关 Issue/PR，必要时回到导师研究或 Codex 工程。
- **避免重复：** Issue/PR 管理状态，文档保存数学理由、实现契约与实测证据；性能数字存于实验报告，其他文档通过 SHA/链接引用，不反复复制。
- **学习同步发生：** 导师在这些交接中帮助科学家理解；重要学习成果可记录到对应文档，不强制另写日报。

## 模板与位置
- [数学文档模板](../../../templates/TENSORIZATION_STUDY.md) / [中文](../templates/TENSORIZATION_STUDY.md)
- [工程文档模板](../../../templates/ENGINEERING_REPORT.md) / [中文](../templates/ENGINEERING_REPORT.md)
- [实验文档模板](../../../templates/EXPERIMENT_REPORT.md) / [中文](../templates/EXPERIMENT_REPORT.md)

## 典型迭代
1. GPT 导师完成简明推导并自主作出 `RESEARCH_READY` 或限制结论，**无须 Scientist 签批**；`PROBE_ONLY` 探针不代表正式验收。
2. GPT 架构师从数学报告定义接口、验收和实验需求，填写工程报告的规格部分或关联 Issue。
3. Codex 实现并真实进行 CPU 测试；EXPLORE 可在同一任务内多轮迭代并只记录一次批次证据，正式 VALIDATE 或有价值代码成熟后更新工程报告并提交 PR；不得自我合并。
4. Codex 在真实本地/Colab CPU/GPU/TPU 运行固定 SHA，校验结果和会话释放，常规提交安全、非敏感的精简证据 PR；科学结论与工程证据由 GPT 决定。
5. GPT Architect 根据三份互相链接的证据自主验收或退回；有数学问题可重新交 GPT Mentor，不重复寻找 Scientist 签字。

## 模板实例化时的链接

将母仓库模板复制为项目正式报告时，必须替换占位符，并**删除或改写模板开头仅在母仓库 `templates/` 位置有效的语言切换链接**，让它指向当前项目固定版本的 `.sae/` 文档。复制到 `docs/research/`、`docs/engineering/` 或 `reports/gpu/` 后，不能假设相对路径还会自动有效。

## 轻量与诚信原则
数学和工程文档是**持续更新的里程碑记录**，无需每次对话复制一份；实验按不同 run-id 分开归档。写清公式、代码、命令、真实结果和链接即可，避免形式主义。

未执行的测试标记 `NOT RUN`；实验报告发布 commit 与**被测试的源码 commit** 必须区分。新增收费及非公开敏感发布保留用户独立同意；常规公开非敏感证据由 GPT 审核，不使用 GitHub Actions，不把 Drive 当同步平台。
