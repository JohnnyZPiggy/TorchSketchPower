# 研究先行、CPU 验证、获授权异构实验（V3.3）

> [English](../../../workflows/RESEARCH_PIPELINE.md) 为规范版本 | 简体中文译本

SAE 采用**证据优先、积极并行**，不是 CPU→GPU 逐级审批瀑布。[Lean Lab](../../../workflows/LEAN_RESEARCH_LAB.md) 的 `EXPLORE` 只需有界批次与简记，`VALIDATE` 才集中完整科研/实验证据。技术允许时数学研究、参考实现、打包和有界设备探针并行；正式结论仍要数学与数值证据。三个阶段可循环回退；GitHub 保存证据，不默认使用 GitHub Actions、Drive 同步或后台 Agent。

## I. 数学研究 — GPT Mentor/Architect
探索数学形式、参考算法、批量/张量算子、matrix-free 结构、稳定性与复杂度，EXPLORE 先在任务中记录最小数学假设，VALIDATE 再在 `docs/research/<algorithm>-tensorization.md` 汇总推导证据。**GPT 自主决定 `RESEARCH_READY / RESEARCH_BLOCKED / NOT_TENSORIZABLE` 或有界假设，不设 Scientist 签批**；设备探针及参考实现可并行。

## II. 工程与 CPU 正确性 — Architect + Codex
Architect 评估生态复用、制定规格并派发 Issue。Codex 实现可安装 Python 模块，真实运行 CPU 参考/边界/随机/dtype 测试、适用时的 `torch.compile`、固定 SHA 干净安装及 Benchmark CLI 冒烟。EXPLORE 每批简记真实源码身份、命令与观察，VALIDATE 再在工程报告中引用正式 SHA 和测试结果。CPU compile 不证明 GPU/TPU 兼容或加速。

正式加速评估应在数学、数值及打包技术准备具备后由 Architect 标 `ACCELERATOR_READY`（兼容旧 `GPU_READY`）；提前开展 `PROBE_ONLY` 设备探针不依赖此标记，**就绪不等于真实验证**。

## III. 设备实验 — Codex 默认执行、Architect 审核
依[实验默认执行](../../../workflows/GPU_EXPERIMENT.md)，Codex 使用现有权益直接进行 CPU/GPU/TPU 实验，**不需要 Scientist 算力授权、常设授权检查或价格预测**。`PROBE_ONLY` 有界设备诊断可早于正式数学研究/Benchmark 准备，但正式性能结论仍需数学和数值验收。默认一个 Colab 活动会话、有限超时、固定 SHA、真实权限、证据校验及会话释放；用户最新停止指令与新增收费独立审批仍有效。TPU/XLA 必须真实测试，菜单选项不代表支持。

遵循[计算实验协议](../../../workflows/GPU_EXPERIMENT.md)：固定 SHA 安装 → **不写 GitHub** 的 Benchmark → 可选、经校验的非敏感 GitHub 证据分支/PR（由 GPT 授权与审核，无 Scientist 签字）。Architect 按[常设授权](../../../governance/STANDING_AUTHORIZATION.md)审核并合并合格 PR；Codex 不自合并。只有真实 GitHub 回执才能称发布成功。

设备问题返回第二阶段，数学问题返回第一阶段。VALIDATE 保留数学、工程、实验三类关联证据；EXPLORE 只需一份简短批次记录；始终如实区分 `PASS` / `FAIL` / `NOT RUN` / `BLOCKED`。范围内科研、证据验收和内部治理由 GPT 自主决定，不设 Scientist 审批；仍遵守真实权限、新增收费和非公开数据边界。旧项目 V3.2 固定快照不自动升级。
