# SAE 子项目初始化冒烟验收（不使用 GitHub Actions）

> 语言：[English](../../../docs/ADOPTION_SMOKE_TEST.md) | **简体中文**

**目的：** 验证 SAE 规则复制到**新算法项目后**仍能工作，而不仅是母仓库的链接正常。这里只定义检查程序，**不代表已经运行测试**。

## 检查 1：操作前审查
1. 选择临时测试仓库或得到明确授权的目标项目，先记录原文件和默认分支。
2. 使用**真实不可变 commit SHA**（或固定 release）锁定 SAE Framework，不能只依赖漂移的 `main`。
3. 先提出待修改计划/分支，不经审查不得覆盖原 `AGENTS.md` 等文件。

## 检查 2：协议副本完整且路径正确

```text
<项目>/
  AGENTS.md                       # 适配目标项目根目录
  sae.yaml                        # 包含真实框架 SHA
  .sae/
    AGENTS.md
    README.md / README.zh-CN.md
    SAE_BOOTSTRAP.md / CHANGELOG.md
    docs/                         # 架构图与相关文档
    examples/                     # 模板关联引用
    protocols/
    workflows/                    # 含 MATHEMATICAL_RESEARCH.md
    templates/                    # 含 TENSORIZATION_STUDY.md
    i18n/zh-CN/                   # 双语导航与文档
```

`.sae/` 必须来自**同一固定版本**。在子项目目录中检查相对路径，防止它们指向缺失的母仓库目录。根 `AGENTS.md` 是**经过适配**的项目入口，需检查项目名称、SHA、角色路径和中文说明的链接。

## 检查 3：用实际指令演练
- **导师 / GPT：** 执行「推进导师工作」时由 GPT 自主记录可检验数学假设，决定 EXPLORE、`RESEARCH_READY` 或有界例外；没有 Scientist 审批，正式验收才需完整数学证据。
- **架构师：** 「推进架构师工作」直接交付一个[Lean Lab 有界批次](../../../workflows/LEAN_RESEARCH_LAB.md)：目标、模式、源码身份、数值 oracle、有限超时及资源释放；不等待 Scientist 签字，正式 VALIDATE 仍须研究证据。
- **工程师：** 「推进工程师工作」领取一个真实就绪 Issue（缺标签时检查正文），在同一有界任务内完成实现→测试→修复→复测；无需每次 EXPLORE 运行创建新 Issue/PR，不虚报。
- **Colab：** Codex 直接使用真实可用的本地/Colab CLI 资源，无 Scientist 算力审批；保留真实权限、任务超时、单会话和释放检查。Publisher 未真实验收时标 `NOT VERIFIED`，不虚报 GPU/TPU 通过。

## 检查 4：配置与快速通道
- 检查 `sae.yaml`：`research_gate.scientist_review_required: false`、`research_gate.required_before_formal_acceptance: true`、`collaboration.per_pr_scientist_approval_required: false`、`experiments.gpu_tpu_require_scientist_budget_approval: false`、`experiments.new_billing_requires_explicit_user_approval: true`。
- 检查 `workflow.default_mode: EXPLORE`、支持 VALIDATE、有限超时、最多一个 Colab 会话及有界修复；探针不算正式验收。
- 远程正式复现必须固定精确 SHA；本地 dirty 原型须如实标记。

## 检查 5：证据和权限
- CPU 测试必须按真实命令与结果记录 `PASS/FAIL/NOT RUN/BLOCKED`。
- 不添加 `.github/workflows/` Actions，不同步 Drive，不向 Git 提交密钥。
- 改动通过可审查 PR，不静默覆盖/合并，不 force-push。

## 输出
列出真实路径、固定 SHA、Issue/PR、PASS/FAIL/NOT RUN/BLOCKED 与风险；仅新增付费、非公开敏感披露或外部账户权限等真实操作需要用户单独决定。

**说明：** 这是冒烟检查协议，不是已通过测试的证明。
