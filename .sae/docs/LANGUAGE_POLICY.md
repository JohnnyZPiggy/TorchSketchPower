# Documentation Language Policy

> Language: **English** | [简体中文](../i18n/zh-CN/docs/LANGUAGE_POLICY.md)

## Language choices
- **English:** [default repository README](../README.md), the canonical AI-agent protocol.
- **简体中文:** [中文首页](../README.zh-CN.md) and [中文文档索引](../i18n/zh-CN/README.md).

GitHub repository README content does **not** automatically change based on the viewer's browser locale. Use the `English | 简体中文` links to switch. Both README files display their own localized SVG architecture diagram.

## Canonical technical contract
- The original root `AGENTS.md`, `SAE_BOOTSTRAP.md`, `protocols/`, and `workflows/` are the agent-facing **normative specifications**.
- Chinese counterparts in `i18n/zh-CN/` are faithful reading translations, **not a second set of competing binding instructions**; do not silently copy them into an adopting project's `.sae/`.
- Keep machine identifiers unchanged: `sae.yaml` keys, JSON keys, GitHub labels, `PASS/FAIL/NOT RUN/BLOCKED`, shell flags, paths, and the exact three Chinese trigger commands.
- YAML/JSON examples have one canonical machine-readable version and separate Chinese explanations.
- Resolve any conflict using the canonical protocol, latest user stop/scope instructions and GPT delegated decisions, and open an Issue to correct translation drift.

## Maintaining translations
When a role, task, experiment, security, or permission rule changes:
1. Update the English canonical page.
2. Update its matching Chinese document.
3. Validate technical identifiers and both directions of navigation links.
4. Update both localized SVG architecture figures and Mermaid diagrams if roles or boundaries change.
5. Submit for PR review before merging.

The issue creation menu offers English and Chinese templates. The default PR template remains English; the optional Chinese PR template can be selected through GitHub's template URL parameter or copied from the translation.
