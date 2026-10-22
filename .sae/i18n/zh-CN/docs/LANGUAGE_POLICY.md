# 双语文档与维护规范

> 语言：[English](../../../docs/LANGUAGE_POLICY.md) | **简体中文**

## 如何切换语言
- [English README](../../../README.md)：GitHub 默认首页，AI 执行协议的规范版本。
- [中文 README](../../../README.zh-CN.md)：完整中文版首页及中文架构 SVG。
- [中文文档目录](../README.md)：角色、流程、示例与模板。

GitHub 仓库 README **不会自动根据浏览器语言切换**。请使用每页顶部的 `English | 简体中文` 链接手动选择。英文和中文各有对应的 SVG 架构图。

## 哪些文档具有执行效力？
项目根 `AGENTS.md`、`SAE_BOOTSTRAP.md`、`protocols/`、`workflows/` 的英文原文是智能体规范。中文译本用于帮助阅读和学习，**不作为一套独立竞争的执行指令**，也不应默认复制到下游项目 `.sae/`。

`sae.yaml` 键、JSON 字段、Issue labels、路径、CLI 参数和 PASS/FAIL/NOT RUN/BLOCKED 保留原样；三条“推进……工作”指令也是固定触发字符串。配置文件保持英文结构，另配中文说明。

如中英文发生冲突，依照英文规范、用户最新停止/范围指令和 GPT 常设决策授权执行，并创建 Issue 纠正翻译。

## 共同维护
修改角色、权限、任务或 GPU 规则时，先更新英文，再同步中文，检查链接及机器字段；执行决策与角色文字变化先同步规范文档及 README Mermaid；SVG 如未同步则明确标为说明性旧图并单独追踪，不能把旧图作为权限来源；通过 PR 证据审查后合并。

GitHub 新建 Issue 可以选中文模板；默认 PR 模板仍为英文，可根据需求采用中文可选模板。
