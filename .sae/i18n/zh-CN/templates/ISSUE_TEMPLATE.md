# 【SAE 工程任务】<简短标题>

> 语言：[English](../../../templates/ISSUE_TEMPLATE.md) | **简体中文**

**负责人：** Codex / Architect / Scientist  
**优先级：** P0 / P1 / P2  
**状态：** ready / in-progress / review / experiment / blocked / accepted  
**类型：** math / engineering / experiment / learning  
**依赖：** #<Issue 编号>（无则填写 none）

## 科学目的
这个任务解决什么数学或工程问题？为什么值得做？

## 数学结构研究前置审核
**研究报告：** `docs/research/<algorithm>-tensorization.md` / 链接  
**GPT 科研决定：** RESEARCH_READY / 有界假设例外 / RESEARCH_BLOCKED  
**矩阵向量 / 张量化结构与限制：** <概述>  
*仅做仓库初始化的任务可以标记不适用。*

## 数学与数值契约
定义、假设、参考基线、不变量、输入输出形状、dtype/设备要求、数值容差。

## 交付内容
- [ ] 独立的 Python 模块 / CLI / 设计说明
- [ ] 数值测试与 Benchmark 代码
- [ ] 文档和可复现运行命令

## 计算实验交付关口（算法实现任务）
- [ ] 固定源码 SHA；如实记录 CPU 打包/CLI/数值测试 PASS / FAIL / NOT RUN，独立 `PROBE_ONLY` 可并行启动
- [ ] 打包的 Benchmark CLI **不写入 GitHub**；可选 Publisher 由 GPT 决定提交安全非敏感资料，仍须独立实测验证，不能冒充已实现
- [ ] Codex 直接执行 Colab CPU/GPU/TPU，报告发布及会话清理分别标注 PASS / FAIL / NOT RUN / BLOCKED；无需 Scientist 算力审批，有界 `PROBE_ONLY` 不计入正式 Benchmark 验收
- [ ] 记录被测源码 SHA、真实命令、输出和失败

## 验收条件
- [ ] 数学契约与参考基线一致
- [ ] 指定边界和正确性测试
- [ ] 真实 CPU 验证已记录
- [ ] GPU 相关任务使用候选源码 SHA 在 Colab 测试
- [ ] 无 GitHub Actions、无密钥泄露

## 任务交接
目标分支、PR/实验报告、遗留问题与阻塞。