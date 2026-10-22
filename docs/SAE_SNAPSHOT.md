# Pinned SAE snapshot

`.sae/` is an unmodified copy of **JohnnyZPiggy/SAE-Framework@65338eb1aa67971e110db982a07cf43161c23446** (SAE V3.3, "Reuse-First, Research-Driven"). Do not edit files under `.sae/`; adopt a newer framework revision only through a reviewed snapshot-update PR.

- Files: 131 (complete `git archive` of the source commit, including bilingual `i18n/zh-CN` mirrors, tools, examples and historical reports).
- Git tree hash of `.sae/`: `2d044da60423a67c51b1504651654e7b6a64d947`, identical to `65338eb^{tree}` in the source repository.

## Verify

```bash
git rev-parse HEAD:.sae          # expect 2d044da60423a67c51b1504651654e7b6a64d947
```

## Link check (target layout)

All 412 relative Markdown links under `.sae/` were checked from this repository's layout: 404 resolve inside `.sae/`. The other 8 are in `.sae/examples/project/AGENTS.md`, a template meant to be copied to a project root. They point to `.sae/...` and resolve once the template sits at the root, as intended upstream.

This snapshot is documentation only: it grants no API, compute or merge capability. The project root `AGENTS.md` and `sae.yaml` (introduced in PR #2) should set `snapshot_complete: true` after both PRs merge.
