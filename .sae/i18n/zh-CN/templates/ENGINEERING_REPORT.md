# SAE 工程设计与实现报告 — <算法名称>

> 语言：[English](../../../templates/ENGINEERING_REPORT.md) | **简体中文**

**目标项目：** `<owner/repo>`  
**算法 / 里程碑：** <名称>  
**关联 Issue / 代码 PR：** <链接>  
**数学研究文档：** `docs/research/<algorithm>-tensorization.md` — 已批准 `RESEARCH_READY` / 明确有限例外 / 仓库初始化任务不适用  
**总架构师：** GPT · **工程师：** Codex · **科学负责人：** 人类 Scientist  
**被测源码 commit：** `<真实 40 位 SHA 或 NOT YET AVAILABLE>`  
**进度：** SPECIFIED / IMPLEMENTING / REVIEW / CPU_VERIFIED / BLOCKED（写清真实证据）

## 1. 数学与工程契约（GPT 架构师）
链接已审核的数学报告，明确参考版和张量版、张量维度、dtype、支持的设备、数值参考判据、误差容差、边界和数学假设。**引用数学方程，不复制整篇研究报告。**

## 2. 工程设计（架构师 → Codex）
记录模块位置、Python 接口、CLI 参数、输入输出结构、按需使用的 batching/`torch.compile`、硬件可移植性与资源限制。提出工程任务、依赖及验收关口。

## 2a. 生态复用评估 — Build vs. Reuse（架构师，派单前）

**调查深度：** NATIVE_REUSE（可仅写一行） / TARGETED_REVIEW / DEEP_REVIEW（须说明理由）  
**检索日期与来源：** <PyTorch 官方文档、候选库官方链接、论文参考实现；或 NOT VERIFIED>  

| 方案 / 候选工具 | 数学与接口适配 | 许可证、维护和依赖 | CPU、跨设备、编译与精度风险 | 决策 |
| --- | --- | --- | --- | --- |
| PyTorch 原生算子 | <证据> | <版本/无> | <已知 / UNKNOWN> | REUSE / ADAPT / REJECT |
| 第三方包（如相关） | <链接及版本> | <许可证、维护情况或 UNKNOWN> | <已核实 / UNKNOWN> | REUSE / ADAPT / REJECT |
| 算法参考实现 / 自研 | <论文、代码> | <许可证或 UNKNOWN> | <基线、风险> | REUSE / ADAPT / BUILD |

**最终 Build-vs-Reuse 方案与理由：** <1–3 句，区分已核实事实和假设>。  
**Codex 交接：** <依赖与版本约束、适配接口、回退方案、CPU 数值/边界测试、干净安装和编译冒烟测试>。  
**未证实声明或后续核验：** <NONE / 明确任务>。  

尽量精简，不创建第四份项目报告。存在工具包不等于验证了正确性、性能或设备兼容性。参见 [生态评估协议](../workflows/ECOSYSTEM_REVIEW.md)。

## 3. 实际实现记录（Codex）
| 模块与修改路径 | 对应数学结构 / 功能 | 实现取舍与限制 |
| --- | --- | --- |
| `src/...` | | |
| `tests/...` | | |
| `benchmarks/...` | | |

偏离数学规格由 GPT Architect 自主决定并记录依据，不需要 Scientist 签核，也不能无记录地改动数学问题。

## 4. 真实验证证据（Codex）
| 测试或基线比较 | PASS / FAIL / NOT RUN / BLOCKED | 实际命令、环境、种子和证据 |
| --- | --- | --- |
| 原始算法/参考结果对照 | NOT RUN | |
| CPU 单元与回归测试 | NOT RUN | |
| 随机与特殊边界情况 | NOT RUN | |
| CPU Benchmark（如适用） | NOT RUN | |
| GPU / TPU 实验（Codex 默认执行，正式验收需证据） | NOT RUN | 链接实验报告，不能编造结果 |

仅在实际测量后才报告最大/相对误差，描述容差和失败；GPU 加速结论引用 `reports/gpu/<run-id>/summary.md`，不重复抄性能数值。

## 5. 复现与交接（Codex）
- **测试源码 commit SHA：** <真实 SHA / NOT RUN>
- **Python/PyTorch、dtype、设备：** <真实环境 / NOT RUN>
- **命令、输入、种子：** <实际命令>
- **Issue / PR / 附件：** <链接>
- **交付 Codex 的有界 Colab 实验说明（无须算力审批）：** <候选 SHA、CLI、规模、容差>
- **已知问题与限制：** <说明>

## 6. 审核与后续（GPT 架构师）
- **架构师审查：** REQUEST_CHANGES / CONDITIONALLY_READY / ACCEPTED（附理由和链接）。
- **GPT 科研/工程决定：** <状态、真实证据或不确定性链接>，无需人类签字。
- **下一步：** 修复 / 重跑 CPU / Colab 实验 / 返回数学研究。
- **学习收获：** 可选的一条数学或数值洞见，不强制长文记录。

工程文档**不取代 GitHub PR 正式审查**，不能把没有执行的 GPU 测试写成通过，也不能覆盖其他证据。
