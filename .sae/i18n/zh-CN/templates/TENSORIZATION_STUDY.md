# 数学结构与张量化重构研究报告 — <算法名称>

> 语言：[English](../../../templates/TENSORIZATION_STUDY.md) | **简体中文**

**目标项目 / Issue：** `<owner/repo>` / #<编号>  
**研究负责人：** GPT 科学导师  
**科研决策人：** GPT Mentor / Architect（无 Scientist 签字）  
**状态：** NOT_STARTED / RESEARCH_READY / RESEARCH_BLOCKED / NOT_TENSORIZABLE  
**论文/参考算法：** <链接>  
**报告版本/决策时间：** <commit / 日期>

## 1. 原始数学问题
输入、维度、定义域、假设、目标量、原算法推导和可验证的参考解。

## 2. 数学结构清单
| 结构或候选算子 | 方程和维度 | 依赖关系 / 并行性 | 条件与障碍 |
| --- | --- | --- | --- |
| 矩阵向量积 / matrix-free / 批处理 / 低秩 / 稀疏等 | | | |

明确指出**哪些结构不适合张量化，以及原因**。

## 3. 张量化数学推导
按步骤写出原始公式 → 变换公式，注明指标和张量形状，说明证明条件、有效区间和所有近似；给出 CPU 参考式与候选张量式。

## 4. 数值正确性契约
参考判据、误差度量、容差、精度稳定性、边界情况、异常传播和可能的反例。**未运行测试不能声称通过。**

## 5. 算法复杂度及硬件可行性
理论计算量、内存、数据迁移、并行深度、编译和控制流限制；CPU/GPU/TPU 适用性**仅提出待验证假设**，不捏造加速比。

## 6. 初步工程与实验建议（尚未执行）
PyTorch 操作/API、参考与张量版比较、正确性优先的实验规模/dtype/种子/设备与测量要求；列出尚未测试项。

## 与三文档闭环的交接

这份文件是 [三文档交接协议](../workflows/THREE_ARTIFACT_HANDOFF.md) 中的**数学研究文档**，保存为目标算法项目的 `docs/research/<algorithm>-tensorization.md`。

GPT 自主作出科研决定后，架构师和 Codex 基于 [工程报告模板](ENGINEERING_REPORT.md) 建立 `docs/engineering/<algorithm>-engineering.md`；Codex 真实运行 Colab 后，才创建 `reports/gpu/<run-id>/summary.md`。实验数值通过链接关联，不复制到数学研究报告里，也不能把假设写成测量结论。

## 7. 备选路径、风险和 GPT 科研决定
- **结论：** RESEARCH_READY / RESEARCH_BLOCKED / NOT_TENSORIZABLE
- **已证明：** …
- **待验证假设：** …
- **尚未检验：** …
- **GPT 科研决定与依据链接：** …
- **交给架构师的 Issue：** …
- **下一研究问题：** …

这是进入工程前的**数学研究记录**，不是 GPU Benchmark。研究阻塞时 GPT 自行决定有界假设/备选或暂停正式验收；独立 `PROBE_ONLY` 与参考准备可并行。
