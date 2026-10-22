# Scientific Learning Loop

> Language: **English** | [简体中文](../i18n/zh-CN/workflows/LEARNING.md)


Engineering work and scientific learning are **parallel, not competing** outcomes.

## Before the first engineering milestone

The first Mentor contribution is **algorithmic research**: discover exploitable mathematics, investigate matrix–vector/matrix-free and related operator structure, derive a potentially tensorizable equivalent, and study correctness/parallelism constraints **with the Scientist**. This precedes the Architect's design, Codex implementation, and formal Colab performance tests. Use [the research gate](MATHEMATICAL_RESEARCH.md) and its study template. The resulting derivation is both an engineering handoff **and** a high-value learning outcome.

## During a milestone
1. Mentor reads current mathematical spec, implementation context and available real benchmark report.
2. Scientist selects a focus or agrees to the Mentor's suggestion (one question at a time).
3. Mentor explains intuition, assumptions, derivation and falsifiable computational prediction.
4. Scientist attempts an explanation, numerical check or small controlled GPU experiment.
5. Mentor compares predicted and actual behavior; explains numerical, implementation or hardware mechanisms.
6. Capture **optional** short note linked to a project Issue/PR; privacy and usefulness take precedence over paperwork.

## Suggested note fields
- Research question, mathematical object/algorithm, core assumptions
- What Scientist can now derive/explain
- Experimental prediction, exact commit and observed result (if any)
- Surprises and unresolved questions
- One next learning step

## Guardrails
Do not convert every discussion into an Issue. Do not assert the Scientist has mastered a concept without evidence. Learning notes do **not** replace production tests or numerical correctness gates.
