# Colab CLI 三阶段兼容入口（V3.3）

> 保留历史文件名以兼容旧链接与固定快照 | [English](../../../workflows/COLAB_TWO_COMMAND.md) 为规范版本

旧版双命令及 Scientist 手动运行流程已被替代。**Codex** 通过 CLI 调度获授权的 Colab CPU/GPU/TPU 实验；Scientist 负责科研目标和计算资源边界，不再日常手动操作 Notebook。

仍保留三个**逻辑阶段**：
1. 安装精确源码 commit SHA。
2. 执行正确性/Benchmark CLI，**不写 GitHub**。
3. 在相关授权范围内，可选地校验并将已有安全报告发布至独立 GitHub 分支/PR；不自动合并。

以上是接口要求，**不代表** Benchmark Publisher 或 GitHub 自动发布端到端已实现。Notebook 可选且应保持轻量。Colab 中名为 `GITHUB_TOKEN` 的 Secret 不保证被所有子进程自动继承；必须安全传递凭据，不得将 token 打印、拼接进 shell 字符串或日志。细粒度 token 须有目标仓库必要权限；缺少凭据或发布授权时标记 BLOCKED，不得虚报成功。

硬件额度、TPU/PyTorch-XLA 验证、证据结构、下载完整性、会话释放及失败状态统一以[计算实验协议](../../../workflows/GPU_EXPERIMENT.md)为准，此处不再重复。
