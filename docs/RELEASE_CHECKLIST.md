# V1 release: gated checklist

**State: V1 IN DEVELOPMENT; RELEASE NOT APPROVED.** This document plans a tag and does not create one. The Engineer role prepares documentation only; it does not merge, tag or publish. Every box below is unchecked until the named reviewer or step has actually done it and the result is recorded in the tracking Issue ([Issue #14](https://github.com/JohnnyZPiggy/TorchSketchPower/issues/14); the V1 scope below comes from [Issue #16](https://github.com/JohnnyZPiggy/TorchSketchPower/issues/16)).

## 1. What V1 is

By the Scientist's decision recorded in Issue #16, **V1 is an independently implemented PyTorch RandNLA package that includes real GPU development and validated acceleration**; V2 is the later reuse or integration of Panther, skerch and other mature ecosystems. This supersedes the earlier CPU-only release scope of this checklist; it does not invalidate the CPU evidence.

Current state: the **CPU baseline** is complete and merged: M0 subspace power kernel, M1 sketch construction, M2 corange least squares, M3 end-to-end `sketch_power_low_rank`, M4 CPU accuracy and cost evidence, M5 numerical error decomposition ([README](../README.md), [math](math.md), [results](cpu-results.md)). It is in-memory and CPU-only. **It is not the V1 release.** The GPU part is at M6, a design-only readiness audit ([gpu-readiness.md](gpu-readiness.md)); M7 (GPU native correctness), M8 (GPU performance), M9 (`torch.compile`) and M10 (independent CPU/GPU validation) are **NOT RUN**.

V1 is **not** (and the current state is not): a verified reproduction of the complete paper Algorithm 2.1; one-pass or streaming; accelerator-validated; evidence of any speedup; a convergence proof. Third-party RandNLA backends (Panther, skerch and similar) are V2 and must not appear in V1 claims, code or dependencies.

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

Re-checked for M6 on `main` `8eae3c63c04a6b43a463f1b5f8d1670c0fd33fe2`: `git ls-remote --tags origin` empty, `gh api .../git/matching-refs/tags` `[]`, `gh api .../releases` `[]`. Still no tag and no Release.

## 3. Open decisions (not decided here)

| # | Decision | Facts | Owner |
|---|---|---|---|
| D1 | Tag name versus package version | `pyproject.toml` has `version = "0.1.0"`. A tag `v0.1.0` would match it. A tag named `v1.0.0` would not, unless the version is changed first. "V1 reference" is a project milestone name, not a version number. | Architect (T3) |
| D2 | Package metadata | `description` is still "Experimental sketch-power subspace iteration in PyTorch", which understates M1-M5. Changing the version or description needs a separate, gated code/metadata PR; it is not part of this documentation PR. | Architect |
| D3 | License | There is **no `LICENSE` file** at the repository root and `pyproject.toml` declares no license. A public release without a license leaves reuse terms undefined. Adding one is a legal decision for the Scientist/owner and is outside this PR; the Engineer has not added or chosen one. | Scientist / Architect (T3) |
| D4 | Supported-version statement | `python >= 3.10` and `torch >= 2.2` are declared but only Python 3.14.6 and torch 2.14.1+cpu were tested. Either test the stated minimums or state the tested environment in the release notes. | Architect |
| D5 | Does a CPU-only baseline tag (for example a pre-release) make sense before the GPU gates, or is the first tag the V1 release after M10? | With V1 now including GPU work, a CPU-only tag must not be called V1. A pre-release or baseline label would need its own claims review. | Scientist / Architect (T3) |

Earlier, a suggested default was to keep `0.1.0` and tag `v0.1.0` as "V1 independent reference implementation". That suggestion is **withdrawn** under the Issue #16 scope: nothing is proposed now except that D1 to D5 are decided before any tag, and that the version, tag name and release notes describe only what has been validated.

## 4. Allowed and forbidden release claims

Allowed today (each already supported by committed evidence): independent PyTorch implementation of the described pipeline; in-memory CPU operation; tested on the environment in the README; two committed CPU experiment reports with manifests; documented rank and conditioning failures; the exact error identities with the cross term; that a GPU readiness audit and test plan exist (design only, [gpu-readiness.md](gpu-readiness.md)).

Forbidden unless new, independently reviewed evidence is added: "V1 released", "V1 complete" or "release candidate" before M10; "reproduces the paper" or "Algorithm 2.1"; "one-pass", "streaming" or "single-pass"; "GPU supported", "CUDA validated" or any GPU, TPU, `torch.compile` or speed/speedup/efficiency claim before M7 (correctness), M8 (performance) or M9 (`torch.compile`) pass with committed evidence; convergence rate or guarantee; equivalence of `sparsesign` to the paper's distribution; any statement about Panther, skerch or other backends (V2); "production ready".

## 5. Gates

Check a box only when the gate is satisfied and the evidence is linked in Issue #14.

- [ ] **G1: documentation PR merged** by the Architect after independent review of the full diff (T1/T2 for documentation).
- [ ] **G2: immutable target SHA.** The release target is the exact merge commit on `main` that contains the reviewed documentation; record its full 40-character SHA. No later commit is included.
- [ ] **G3: clean verification at that SHA.** In a fresh clone checked out at the target SHA with a clean tree and a new virtual environment: `python -m pip install .`, `python -m pip install pytest`, `python -m pytest -q`. Record the command output, test count, Python/torch/pytest versions and log hash. The count must be reconciled with the README (444 at the time of writing) and any difference explained.
- [ ] **G4: documentation audit.** Every relative link resolves; every README example runs on CPU and prints the stated output; every number in README, `docs/cpu-results.md` and `docs/math.md` matches the committed reports; claims are checked against Section 4.
- [ ] **G5: diff scope.** Between the target SHA and the SAE pin, `.sae/` is unchanged (`git rev-parse <SHA>:.sae` equals the pinned tree `2d044da60423a67c51b1504651654e7b6a64d947`, snapshot of `JohnnyZPiggy/SAE-Framework@65338eb1aa67971e110db982a07cf43161c23446`); `sae.yaml` unchanged; no GitHub Actions workflow files; no new dependency; no new billing or paid service.
- [ ] **G6: decisions D1 to D5 resolved** and any resulting version, metadata or license change merged through its own reviewed PR before the target SHA is fixed.
- [ ] **G7: live tag-collision check** immediately before tagging, repeating the commands in Section 2. The chosen tag must not exist; the tag must not be moved or re-pointed once created.
- [ ] **G8: Architect T3 review of the public release claims** (release notes text, Sections 1 and 4, the README Status table). Public statements about scientific scope are high-impact (see the governance notes in [`.sae/governance/STANDING_AUTHORIZATION.md`](../.sae/governance/STANDING_AUTHORIZATION.md)). The review is recorded in Issue #14.
- [ ] **G9: V1/V2 boundary.** No Panther, skerch or other third-party backend code, dependency or claim in the release; any comparison work stays in a separate V2 Issue.
- [ ] **G10: GPU gates.** M7 (GPU native correctness), M8 (GPU performance experiments), M9 (`torch.compile`) and M10 (independent CPU/GPU validation) are each PASS with committed, reviewed evidence, or explicitly waived by the Architect with the reason recorded, as defined in [gpu-readiness.md](gpu-readiness.md#8-gates-m7-to-m10). Status today: all four NOT RUN. A tag created before G10 is not a V1 release.
- [ ] **G11: execution by an authorized actor.** The tag and any GitHub Release are created only after G1 to G10, by the Architect/owner (not the Engineer), as an annotated tag on the exact SHA of G2.

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
