# sae.yaml 项目配置说明（中文）

> [English canonical YAML](../../../../examples/project/sae.yaml) | **简体中文**

`sae.yaml` 是机器可读取的项目模板。使用时替换真实仓库/包名、科研目标和**固定的 40 位 SAE commit SHA**；字段名、布尔值及 `EXPLORE/VALIDATE` 状态保持英文。英文 YAML 是唯一规范配置，不以历史中文示例覆盖它。

## 角色与决策
- `roles.scientist: human`：只提出目标、调整或停止工作，不承担常规审核。
- `research_gate.decision_role: gpt`、`scientist_review_required: false`：由 GPT Mentor/Architect 独立决定科研结论。
- `research_gate.required_before_formal_acceptance: true`：数学/数值研究关口约束**正式验收和性能结论**，不阻塞早期参考实现或 `PROBE_ONLY` 探针。
- `collaboration.merge_decision_role: gpt_architect`、`merge_requires_architect_evidence_review: true`：合格 PR 仍需 GPT 基于真实 Diff/SHA/证据审查，但不逐次向 Scientist 申请签核；`per_pr_scientist_approval_required: false`。
- `collaboration.actions_enabled: false`：不使用 GitHub Actions 或付费托管 CI。

## 双模式和单批次任务
- `workflow.default_mode: EXPLORE`：默认小规模快速探索；`VALIDATE` 用于正式正确性/加速和可复现验收。
- `workflow.experiment_batch.one_issue_per_batch: true`：以一个现有或新建 Issue 交付一个完整的有界任务；不是每次探索运行创建新 Issue。
- `max_self_repair_attempts_per_failure_class: 3`：一类失败最多三次批内自主修复，无进展更早停止；可在同批次连续进行多个实验。
- `one_concise_evidence_summary_per_batch: true`：探索只需一份简洁汇总；正式验收才关联必要数学/工程/实验文档。
- `additional_per_attempt_scientist_or_gpt_signoff: false`：批内修复/重测无需人工或 GPT 逐次签批，最终科研验收仍由 GPT 完成。
- 实际流程以[Lean Research Lab（中文）](../../workflows/LEAN_RESEARCH_LAB.md)和[英文规范](../../../../workflows/LEAN_RESEARCH_LAB.md)为准。

## 算力、证据及发布
- `experiments.gpu_tpu_require_scientist_budget_approval: false`：已有 Colab 权益内不设 Scientist 算力审批。
- `experiments.new_billing_requires_explicit_user_approval: true`：新增充值/订阅/按量计费仍需用户明确批准。
- `max_active_colab_sessions: 1`、`task_timeout_required: true`：会话并发受限，任务必须有有限超时并核实资源清理。
- `install_source: pinned_github_commit_via_pip`：正式远程结果必须对应精确 SHA；探索性 dirty 本地工作树必须如实标记。
- `benchmark_cli`、`publisher` 是**目标接口**，不意味着已实现或通过 TPU/Publisher E2E 验收。Benchmark 不应写 GitHub；可选 Publisher 是独立、需验证的安全发布阶段。
- `experiments.drive_sync: false`：Drive 不用于跨 Agent 文件同步。

**适用范围：** 只影响新采用模板的项目；旧项目的固定 `.sae/` 和 `sae.yaml` 不自动迁移。协议文本并不保证有真实 Codex/Colab 后台自动化能力。
