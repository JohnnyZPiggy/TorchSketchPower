# V1 reference release: gated checklist

**State: PREPARED, NOT RELEASED.** This document plans a tag and does not create one. The Engineer role prepares documentation only; it does not merge, tag or publish. Every box below is unchecked until the named reviewer or step has actually done it and the result is recorded in the tracking Issue ([Issue #14](https://github.com/JohnnyZPiggy/TorchSketchPower/issues/14)).

## 1. What V1 is

An independently implemented, bounded, in-memory, CPU-only PyTorch reference implementation: M0 subspace power kernel, M1 sketch construction, M2 corange least squares, M3 end-to-end `sketch_power_low_rank`, M4 CPU accuracy and cost evidence, M5 numerical error decomposition ([README](../README.md), [math](math.md), [results](cpu-results.md)).

V1 is **not**: a verified reproduction of the complete paper Algorithm 2.1; one-pass or streaming; accelerator-validated; evidence of any speedup; a convergence proof. Third-party RandNLA backends (Panther, skerch and similar) are V2 research only and must not appear in V1 claims, code or dependencies.

## 2. Tag inventory (authoritative, read only)

Taken on the branch that adds this document, against `main` at `b4a1080c8d904b6a49e67b5927f5d957b1fa98db` (base of this work). Commands run with the authenticated `gh` and plain `git` from this repository:

| Command | Result |
|---|---|
| `git ls-remote --tags origin` | empty output, exit 0 |
| `gh api repos/JohnnyZPiggy/TorchSketchPower/git/matching-refs/tags` | `[]`, exit 0 |
| `gh api repos/JohnnyZPiggy/TorchSketchPower/tags` | `[]`, exit 0 |
| `gh api repos/JohnnyZPiggy/TorchSketchPower/releases` | `[]`, exit 0 |
| `git tag -l` after `git fetch origin --tags` | empty |

So **no tag and no GitHub Release exists at the time of this audit**. This is a point-in-time fact: it must be re-checked immediately before tagging (Section 5, gate G7). A name is not reserved by this document.

## 3. Open decisions (not decided here)

| # | Decision | Facts | Owner |
|---|---|---|---|
| D1 | Tag name versus package version | `pyproject.toml` has `version = "0.1.0"`. A tag `v0.1.0` would match it. A tag named `v1.0.0` would not, unless the version is changed first. "V1 reference" is a project milestone name, not a version number. | Architect (T3) |
| D2 | Package metadata | `description` is still "Experimental sketch-power subspace iteration in PyTorch", which understates M1-M5. Changing the version or description needs a separate, gated code/metadata PR; it is not part of this documentation PR. | Architect |
| D3 | License | There is **no `LICENSE` file** at the repository root and `pyproject.toml` declares no license. A public release without a license leaves reuse terms undefined. Adding one is a legal decision for the Scientist/owner and is outside this PR; the Engineer has not added or chosen one. | Scientist / Architect (T3) |
| D4 | Supported-version statement | `python >= 3.10` and `torch >= 2.2` are declared but only Python 3.14.6 and torch 2.14.1+cpu were tested. Either test the stated minimums or state the tested environment in the release notes. | Architect |

A suggested default, if the Architect agrees, is: keep `0.1.0`, tag `v0.1.0`, and describe it in the release notes as "V1 independent reference implementation". This is a proposal only.

## 4. Allowed and forbidden release claims

Allowed (each already supported by committed evidence): independent PyTorch implementation of the described pipeline; in-memory CPU operation; tested on the environment in the README; two committed CPU experiment reports with manifests; documented rank and conditioning failures; the exact error identities with the cross term.

Forbidden unless new, independently reviewed evidence is added: "reproduces the paper" or "Algorithm 2.1"; "one-pass", "streaming" or "single-pass"; any GPU, TPU, `torch.compile` or speed/speedup/efficiency claim; convergence rate or guarantee; equivalence of `sparsesign` to the paper's distribution; any statement about Panther, skerch or other backends; "production ready".

## 5. Gates

Check a box only when the gate is satisfied and the evidence is linked in Issue #14.

- [ ] **G1: documentation PR merged** by the Architect after independent review of the full diff (T1/T2 for documentation).
- [ ] **G2: immutable target SHA.** The release target is the exact merge commit on `main` that contains the reviewed documentation; record its full 40-character SHA. No later commit is included.
- [ ] **G3: clean verification at that SHA.** In a fresh clone checked out at the target SHA with a clean tree and a new virtual environment: `python -m pip install .`, `python -m pip install pytest`, `python -m pytest -q`. Record the command output, test count, Python/torch/pytest versions and log hash. The count must be reconciled with the README (444 at the time of writing) and any difference explained.
- [ ] **G4: documentation audit.** Every relative link resolves; every README example runs on CPU and prints the stated output; every number in README, `docs/cpu-results.md` and `docs/math.md` matches the committed reports; claims are checked against Section 4.
- [ ] **G5: diff scope.** Between the target SHA and the SAE pin, `.sae/` is unchanged (`git rev-parse <SHA>:.sae` equals the pinned tree `2d044da60423a67c51b1504651654e7b6a64d947`, snapshot of `JohnnyZPiggy/SAE-Framework@65338eb1aa67971e110db982a07cf43161c23446`); `sae.yaml` unchanged; no GitHub Actions workflow files; no new dependency; no new billing or paid service.
- [ ] **G6: decisions D1 to D4 resolved** and any resulting version, metadata or license change merged through its own reviewed PR before the target SHA is fixed.
- [ ] **G7: live tag-collision check** immediately before tagging, repeating the commands in Section 2. The chosen tag must not exist; the tag must not be moved or re-pointed once created.
- [ ] **G8: Architect T3 review of the public release claims** (release notes text, Sections 1 and 4, the README Status table). Public statements about scientific scope are high-impact (see the governance notes in [`.sae/governance/STANDING_AUTHORIZATION.md`](../.sae/governance/STANDING_AUTHORIZATION.md)). The review is recorded in Issue #14.
- [ ] **G9: V1/V2 boundary.** No Panther, skerch or other third-party backend code, dependency or claim in the release; any comparison work stays in a separate V2 Issue.
- [ ] **G10: execution by an authorized actor.** The tag and any GitHub Release are created only after G1 to G9, by the Architect/owner (not the Engineer), as an annotated tag on the exact SHA of G2.

## 6. Commands for the authorized actor (not executed by the Engineer)

Shown for completeness; they are to be run only after the gates above, with `<TARGET_SHA>` and `<TAG>` filled from G2 and D1:

```bash
git ls-remote --tags origin '<TAG>'                  # must print nothing (G7)
git tag -a '<TAG>' <TARGET_SHA> -m 'TorchSketchPower V1 independent reference implementation'
git push origin '<TAG>'                              # no force; never re-tag
gh release create '<TAG>' --verify-tag --notes-file RELEASE_NOTES.md
```

Release notes must contain only the allowed claims of Section 4, the target SHA, the tested environment, the test count and log hash from G3, the experiment source SHAs, the list of NOT RUN items, and the license status.

## 7. Provenance to cite

- Paper: Chang and Yang (2026), DOI 10.1137/25M1760143.
- Upstream MATLAB reference, read only and not copied (no root license): `Mitchell-Cxyk/SketchPowerIteration@752be34fbd26595f8d608a25e7dcdea586a6e0ca`.
- SAE Framework pin: `JohnnyZPiggy/SAE-Framework@65338eb1aa67971e110db982a07cf43161c23446`.
- Evidence: PRs [#2](https://github.com/JohnnyZPiggy/TorchSketchPower/pull/2), [#5](https://github.com/JohnnyZPiggy/TorchSketchPower/pull/5), [#7](https://github.com/JohnnyZPiggy/TorchSketchPower/pull/7), [#9](https://github.com/JohnnyZPiggy/TorchSketchPower/pull/9), [#11](https://github.com/JohnnyZPiggy/TorchSketchPower/pull/11), [#13](https://github.com/JohnnyZPiggy/TorchSketchPower/pull/13); experiment source SHAs `36e94999b7cf6f64d6437d0c2179fe1eb762386e` (M4) and `096cce0bb78974d0aeff53c723c1cf10cbd71519` (M5).
