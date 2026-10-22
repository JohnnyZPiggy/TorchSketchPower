# SAE Framework V3.3 — 能力路线图

> [English](../../../docs/ROADMAP.md) 为规范版本 | 简体中文译本

本仓库提供 Agent 协作协议，**不是**已部署的后台自主执行系统。文档接口不代表程序已经实现。

## 据 Scientist 交接已验证（2026-10-19）
Windows Codex → WSL2 Ubuntu 24.04 → Colab CLI 0.7.4 → 真实 T4 GPU smoke test，结果 JSON/SHA-256 校验和会话释放（最终活动会话为零）。这不是 SAE 完整实验或 GitHub Publisher 端到端测试。

## P0 — Codex 实验委托闭环
- 实测 Colab CLI CPU 和使用真实算法 Benchmark CLI 的有限 GPU 实验，固定源码 SHA 并验证数值参考。
- 验证下载完整性、失败传播、会话释放和使用仓库最小权限凭据的 GitHub 报告分支/PR 发布。
- 独立验证 TPU 分配与 PyTorch/XLA，不根据设备菜单推断支持。
- Codex 直接使用现有账户设备，不设 Scientist 签核；遵守实际服务商限制、有限超时与资源释放，不强制绑定 NVIDIA/CUDA。

## P1 — 跨项目复用
- 从固定 SAE commit 安全幂等初始化：dry-run、不覆盖、在目标项目检查链接和配置。
- 实测跨项目复用 Colab CLI，不重复 OAuth 或偷偷升级协议。
- 可选 `sae.yaml`、实验报告本地 Schema 验证；不使用 GitHub Actions。

## P2 — 体验优化
- 简洁 Issue/PR 摘要、经审查的版本迁移与学习记录。

每个里程碑需要明确 Issue 与真实执行证据。实验三个阶段独立：固定 SHA 安装 → **不写 GitHub** 的 Benchmark → 可选的校验后发布。详见[计算实验](../../../workflows/GPU_EXPERIMENT.md)。
