# Ecosystem-Aware Architecture — Lightweight Build-vs-Reuse Gate

> English (normative) | [简体中文](../i18n/zh-CN/workflows/ECOSYSTEM_REVIEW.md)

## When and who

**Owner: GPT Chief Architect.** In parallel with GPT Mentor's initial mathematical analysis and Codex preparation, briefly check reusable building blocks **without waiting for Scientist acceptance** or delaying a safe implementation/probe task. For a dependency update or small bug fix, review only what changed. This does not bypass the research gate.

## Three-pass bounded discovery

1. **PyTorch native first:** check actual APIs and version constraints for `torch`, `torch.linalg`, `torch.func`/`vmap`, `torch.sparse`, `torch.compile` and native tensor operators where relevant. Prefer compositions exposing matrix/vector products, batching or matrix-free operators.
2. **Targeted ecosystem:** if native coverage is insufficient, check only directly relevant maintained PyTorch-compatible libraries (e.g. linear operators, differentiable solvers, domain tools). Inspect official documentation/repositories and *actual* license, release/maintenance, dependencies and device claims.
3. **Algorithm reference code:** inspect paper-author or upstream implementations as a correctness oracle or a candidate adapter. Distinguish a reference baseline from a redistributable licensed dependency and from a production-quality portable implementation.

**Time box:** small tasks should need a short check, not an exhaustive survey. Usually shortlist **at most three serious candidates**; deepen the search only for material correctness, licensing or complexity uncertainty. If current external search is unavailable, label the review **PARTIAL / UNVERIFIED**, name the unresolved assumption and create a narrowly scoped verification task. Do not fabricate package facts or pretend that a repository was inspected.

## Compare approaches

Evaluate **REUSE** (native/direct), **ADAPT** (thin adapter/composition), and **BUILD** (implement distinctive mathematics only). For each plausible choice consider:

- Mathematical equivalence to the GPT-reviewed derivation and numerical stability / error tolerances.
- Maintenance, license compatibility and provenance; transitive dependency cost and clean pinned-SHA install.
- CPU support by default; device-agnostic tensor operations, dtype and autograd requirements where applicable.
- `torch.compile` suitability, dynamic shapes, host synchronizations and fallback for unsupported devices.
- Reproducible reference/oracle tests, package version pinning, public API stability and honest performance measurement.

**Decision rule:** prefer native or light dependency reuse when equally correct and maintainable; reject reuse if it harms correctness, portability, licensing or reproducibility. Do not rewrite robust existing infrastructure just for originality, or retain a heavy dependency just to avoid a small core implementation. Do not claim acceleration or hardware support without actual tests.

## One small record; no extra report

Use **section 2a, Ecosystem Review**, in `templates/ENGINEERING_REPORT.md`: list checked candidate(s) and sources/date, key tradeoffs, chosen REUSE/ADAPT/BUILD decision, and unknowns. `NATIVE_REUSE` permits a one-line entry where obvious. Turn the decision into concrete Codex Issue scope: API/dependency versions, adapter boundary, baseline, CPU tests, clean install, compile smoke test and fallback. Codex validates in its own CPU environment; Architect reviews results; Formal GPU benchmarks are Codex-run after technical readiness, with **no Scientist compute authorization**; bounded `PROBE_ONLY` device checks may run earlier.

## Guardrails

No mandatory GitHub Actions, new agent, new document, GPU-before-CPU, vendor lock-in, speculative benchmarks or automatic dependency upgrades. When tools cannot inspect a package, mark the evidence unknown rather than claim verified compatibility. End with the standard role Next-Action handoff.
