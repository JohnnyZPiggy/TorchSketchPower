# 计算实验协议 — CPU / GPU / TPU（V3.3）

> 历史文件路径保留兼容 | [English](../../../workflows/GPU_EXPERIMENT.md) 为规范版本

## 职责与前置条件
- **Scientist：** 设定目标并可随时调整/停止，**不再作为科研、实验或算力签核人**；Architect 自主决定范围内研究准备及结论。
- **Architect：** 实验矩阵、准备/验收条件、证据审核及合格 PR 最终合并裁量。
- **Engineer（如 Codex 或 Claude Code）：** 本地/Colab CLI 实验、正确性与性能工具、结果校验和会话释放，常规提交安全、非敏感的 GitHub 证据 PR。
- **GitHub：** 共享代码、任务与报告。Drive 仅为可选临时 Notebook 空间。

新算法/重大张量化由 Mentor/Architect 自主决定简明[数学研究](../../../workflows/MATHEMATICAL_RESEARCH.md)及 Architect 实验计划，**无须 Scientist 签字**。设备探针、打包、参考 CPU 和硬件准备可并行；**正式加速结论**须数学依据、数值正确性及公平实测，不得凭空宣称设备性能。

## 三个独立逻辑阶段
1. **固定 SHA 安装：** 在选定本地/Colab 环境安装精确源码版本。
2. **Benchmark：** 运行正确性与性能 CLI，**不写 GitHub**。
3. **可选发布：** 校验结果、排除凭据及非公开敏感数据后；常规安全证据 PR 无须 Scientist 签批，只通过独立 GitHub 分支/PR 发布已审查的安全文件。

[三步兼容入口](../../../workflows/COLAB_TWO_COMMAND.md)保留历史文件名。示例 Notebook 命令不代表 CLI 已实现。Engineer 可经 Colab CLI 调度上述步骤，无需 Scientist 手动点击。Publisher 在端到端实测前仍为未验证。

## Experiment by Default — 实验默认执行，无 Scientist 算力授权关口（2026-10-20）

**CPU/GPU/TPU 实验是 Engineer 的常规执行职责，而不是 Scientist 授权工作流。** 对已经连接的 Colab 账户中现有、已包含或预付的计算权益，Architect/Engineer **不检查、不引用、不等待 Scientist 算力批准或所谓常设授权记录**，也不索取单次设备批准、价格报价、Compute Units 估算、预算数字或时长签批。范围内科研方向和结论由 Architect/Mentor 根据用户目标自行决定；用户最新暂停/修改指令优先。

- **快速开始：** 用户触发有范围的 SAE 工作周期后，只需明确任务、固定源码 SHA、真实账户/工具可访问及相应技术准备条件，Engineer 即可执行本地或 Colab CLI CPU/GPU/TPU 实验；Architect 设定验收、审查结果，不设人工算力授权关卡。
- **探索性设备探针：** 为真实确认 GPU/TPU-XLA 环境能力、诊断工具问题，可在正式 `RESEARCH_READY` 或 CPU Benchmark 准备完成前启动**短时、有界的设备冒烟实验**，须标为 `PROBE_ONLY`；不能替代 Mentor/Architect 数学论证、数值正确性或正式性能验收。正式加速结论仍须完整研究及工程关口。
- **安全执行默认值：** 同时最多一个 Colab 活动会话；任务设有限超时；不得无限自动重试或无人值守后台调度；成功、失败、中断均核实会话释放。Scientist 后续明确限制和服务商真实限制继续有效。权限失败、设备不可用和现有权益实际耗尽才是有效阻塞，预计价格不是。
- **新增收费例外：** 新购买、充值、订阅、新账户/服务商、开启按量付费或任何**现有权益外的新增收费承诺**，必须另获用户明确批准。若现有账户可能直接产生新增费用且不能安全限定在既有权益内，必须停止，不猜测费用；不得自行改动计费设置。
- **委托决策：** 范围内科学判断、算法验收、非敏感 GitHub 实验资料发布和工程签核由 Architect 自主决定；**无需 Scientist 科研/T3/实验审批**。新增收费、非公开敏感披露、外部破坏性或账户权限动作仍需用户另外明确指令。

## 计算资源与设备

可用时复用 WSL2/Colab CLI OAuth。运行前核实**真实的**账户/工具权限、固定源码 SHA、环境、任务范围及有限超时，**不核对 Scientist 算力授权记录**。按科研目的选择设备、校验结果和会话释放；TPU 还须验证实际分配、PyTorch/XLA 安装、算子和数值行为，设备菜单选项不代表功能已验收。

无论成功、失败或中断，均须尝试停止所有已分配会话、核实最终状态并报告释放失败；不得悄悄留下运行资源。

## 证据
- `manifest.json`：run ID/时间、源码 SHA、Issue/PR、设备、环境、种子、精度、命令、状态与方法。
- `correctness.json`：参考基线、容差、误差及 PASS/FAIL/NOT RUN。
- `benchmark.csv`：规模、单位、重复、预热/同步、median/p95 和适用时的编译开销。
- `summary.md`：真实观察、限制、失败、资源释放与证据链接。
- 下载完整性（如 SHA-256）、本地/远端文件一致性及发布状态。

不提交大型数据、密钥或无必要的日志；数值正确性与公平基线不满足时不得声称加速。

## GitHub 发布与失败
通过发布权限与安全检查后先校验文件结构、大小和秘密信息，创建不可变的独立实验分支/PR，关联源码 SHA、Issue/代码 PR 并核实 API 成功；由 Architect 决定合并。公开仓库的 Draft PR 仍公开。禁止直接写受保护主分支、强推和自合并。凭据仅存安全位置。

上传/API 失败标记 `PUBLISH_FAILED`；未测试硬件标记 `NOT RUN`；真实运行权限不足、新增收费未获许可、SHA 不一致或环境不可用标记 `BLOCKED`。资源释放失败必须明确报告。

## 截至 2026-10-19 的验证状态
据用户交接记录，Windows Codex → WSL2 Ubuntu 24.04 → Colab CLI 0.7.4 已完成 T4 GPU smoke test：远端 Python 3.13.15、PyTorch 2.11.0+cu130、CUDA 13.0、1024×1024 float32 matmul（20 次计时，平均 0.736283 ms），JSON/SHA-256 校验通过，停止后活动会话为零。仅证明基本 GPU 远程执行。Colab CPU、TPU v5e1/v6e1 与 PyTorch/XLA、GitHub 自动发布及跨项目复用仍未验证。
