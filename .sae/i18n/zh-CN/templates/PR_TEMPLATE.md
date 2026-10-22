# SAE Pull Request：<标题>

> 语言：[English](../../../templates/PR_TEMPLATE.md) | **简体中文**

关联 Issue：#<编号>  
候选源码 commit：`<SHA>`

## 改动范围与数学动机
说明解决的问题、数学假设、实现与公共 API 的变化。

## 验证证据（未执行不能写通过）
| 检查 | 状态：PASS / FAIL / NOT RUN / BLOCKED | 命令与链接 |
| --- | --- | --- |
| 单元/回归测试 | NOT RUN | |
| 数值参考对照 | NOT RUN | |
| CPU 性能测试 | NOT RUN | |
| Colab GPU 正确性 | NOT RUN | |
| Colab GPU 性能 | NOT RUN | |

## 三份文档的关联
- GPT 审核的正式数学研究（VALIDATE）：`docs/research/<algorithm>-tensorization.md` / EXPLORE 或基础设施 N/A
- 工程实现与 CPU 证据：`docs/engineering/<algorithm>-engineering.md`
- 真实 Colab 实验报告：`reports/gpu/<run-id>/summary.md` / NOT RUN
- 被测源码 SHA：`<SHA>`（与报告发布 SHA 区分）

## 复现
Python/PyTorch 版本、设备、随机种子、命令、数据来源。

## 风险与限制
数值差异、未测试硬件、精度与性能取舍、跳过的测试。

## 需要审查的事项
GPT Architect 核对被测 SHA、数值证据与风险，自主接受 / 退回 / 合并；无需 Scientist 实验签批。EXPLORE 仅汇总一次有界批次，不要求每次设备探针单独建 PR。

## 学习主题（可选）
值得在导师模式中进一步讨论的一个问题。