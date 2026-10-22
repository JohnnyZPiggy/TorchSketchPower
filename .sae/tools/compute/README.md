# Local preflight and bounded Colab transport

> English | [简体中文](README.zh-CN.md)

Status: **LOCAL_VALIDATED + SCOPED LIVE_READY (CLI 0.7.4, T4-requested transport-only)**, evidenced by [SAE PR #48](https://github.com/JohnnyZPiggy/SAE-Framework/pull/48) on pinned source `8081b6e02eee0754903898d5afe5b112f1bb23d0`. One real remote kernel/driver/artifact-hash/stop/authenticated-zero cycle passed; actual T4 identity was not observed in this transport experiment. [TorchYAND PR #22](https://github.com/JohnnyZPiggy/TorchYAND/pull/22) separately validated a scientific pilot on an observed Tesla T4, not universal transport/science capability. Extracted from owner-authored SAE_Test PR 3; [source/license/dependency provenance](NOTICE.md). This is three standalone Python files, not a package, daemon, bootstrap installer or publisher. Only transport is generic; algorithms, numerical oracles, installation commands and experimental interpretation belong to the project driver.

| Component | Dependency | Scope |
|---|---|---|
| `environment_preflight.py` | Python standard library + installed Git | Exact commit, dirty state, blob export, writable non-synced temporary paths |
| `colab_control.py`, `kernel_smoke.py` | Standard library + existing `colab` executable | One bounded T4 allocation, default short probe, transport and cleanup |
| Explicit `--install-local` | Existing Python pip/build backend | Optional no-deps temporary project install; never default |
| Project adapter | Project chooses dependencies | Scientific code, exact-source install, real device checks and outputs |

Windows Python 3.12.14 and WSL Python 3.12.3 are tested locally. External CLI 0.7.4 was locally version-checked in WSL; other versions/device flags remain unverified. Phase one accepts only `--device T4`, a requested variant, not proof of actual hardware. CPU/TPU/XLA runners and native compilation are not implemented by this transport.

## Pinning and local-only use

For future projects, copy/reference only the three runtime files from an **exact SAE commit/tag** with their MIT notice. Keep them adjacent. Record that tool pin separately from the algorithm's `--source-sha`; the report records runtime-file hashes. No floating `main`, migration of existing project `.sae/`, all-document-snapshot copy, package publishing or bootstrap/publisher changes are required.

From the same shell that will launch production (an existing WSL login shell if needed):

```sh
python tools/compute/colab_control.py --preflight-only --cli colab \
  --repo-path path/to/project --source-sha CANDIDATE_40_HEX_SHA \
  --run-id local-check-1 --out local-evidence/new-run
```

Replace the path/SHA with an existing local project checkout and full immutable commit. Preflight only calls CLI `version` and local Git/filesystem operations; no credentials, sessions, usage, allocation, driver execution or login fallback. Exact export uses `ls-tree`/`cat-file` bytes independent of dirty CRLF checkout. `.sae/` is excluded from temporary project export; its immutable documentation is not copied into every command. Other regular tracked files are exported; symlinks/submodules/unsafe paths are rejected. Temporary build/cache paths must be writable, outside checkout and Dropbox; `--temp-root` overrides OS temp without global settings changes. `--install-local` is explicit and uses existing pip/build requirements with no dependency installation; default is no install.

## Project-owned adapter contract

Live execution is **not needed** to use the example or complete local validation. In a separately scoped compute task, add `--driver scripts/my_driver.py --artifacts experiments/artifacts.json` and remove `--preflight-only`. Both paths must refer to regular committed files **inside `--repo-path` at `--source-sha`**. Absolute/traversal paths and symlink adapters are rejected. Dirty local adapters are ignored; exact Git blobs are used. The self-contained driver is temporarily staged outside the checkout and its transport SHA is recorded separately. It receives `SAE_CANDIDATE_SHA` with the verified project commit, and decides how to install/run project code without GitHub writes. Generic transport does not contain repository URLs or algorithm installation logic.

The project's small manifest is:

```json
{"artifacts": [{"name": "measurement.json"}]}
```

Initial contract: 1–16 JSON output basenames, each at most 1 MiB, remote `/content/<name>`; no nested/absolute paths, control-report collision, Windows reserved device name or case-insensitive duplicate. Manifest is at most 64 KiB; driver at most 1 MiB. Each declared artifact must be a JSON object with exact `source_sha` and `status: "PASS"`. A non-passing required artifact fails transport. Put optional `NOT_RUN` observations inside a passing primary report rather than declaring them passing required outputs. Duplicate JSON keys are rejected. Driver emits exactly one line per required file:

```text
ARTIFACT measurement.json BYTE_COUNT SHA256_HEX
```

After bounded downloads, the controller verifies byte count/hash, JSON source identity and declared status. This is **not a numerical oracle**: `PASS` with `TRANSPORT_ONLY_SCIENCE_UNREVIEWED` means transport/provenance and declared status passed, not GPT scientific acceptance. The project must preserve independent mathematical/numerical evidence. Artifact payloads remain project-owned and are not secret-scrubbed by transport; separate publication must screen them.

The [example driver](../../examples/compute_adapter/driver.py) and [manifest](../../examples/compute_adapter/artifacts.json) only emit a transport fixture, explicitly `live_gpu/tpu/compilation: NOT_RUN`. A regression test runs it in a local temporary directory with a real local Git SHA, requiring no provider allocation or package install:

```sh
python -m unittest discover -s tools/compute/tests -v
```

## Bounds and evidence

For allocation failures, see the [offline CLI 0.7.4 call-chain diagnosis](diagnostics/README.md). HTTP request timeouts differ from the outer process bound; an outer timeout cannot identify GET versus POST. Do not poll `status` during allocation: it synchronizes remote assignments and may modify local session state. This controller has no status observer loop.

New output directory and explicit run ID are required; existing output is never overwritten. Before allocation, unknown/unrelated active sessions or unconfirmed positive entitlement block. Every fresh `new` gets `kernel_smoke.py` with a default 30-second remote/35-second external limit, capped by remaining main budget. Missing marker, error or timeout records `KERNEL_PROBE_FAILED`, skips workload and enters cleanup. Later workloads can still hang; they have separate finite external bounds. No assertion that this fixes the original pilot hang.

Defaults: task 5400s, allocation 600s (max 2700), cleanup reserve 60s, kernel 30s (max 60), workload 240s (max 420). Allocation/work deadlines reserve cleanup even after main-budget exhaustion. At most two stop+authenticated-zero readback checks share the finite cleanup allowance; partial allocation/error/interrupt also attempts cleanup. Unknown release is `CLEANUP_FAILED`, never PASS. No overlapping allocation, implicit billing purchase, new authentication/token manager, diagnostic monkeypatch, background retry or approval stage is added. Abrupt OS termination or provider/network failure can still prevent release; mocks do not verify live cleanup.

Readback is pinned to the audited CLI **0.7.4** path: `usage` directly performs authenticated `GET /tun/m/ccu-info`, validates the response and formats balance/rate/assignment count. It does not use `sync_sessions()` or swallow authentication SystemExit. Before allocation, require exit 0, the complete three-line stdout contract, assignment count 0 and positive balance. After stop, require a fresh complete usage response with count 0 **and successful stop**; cleanup does not require positive balance. `sessions` exit 0/empty text, empty stdout, warnings, duplicates, malformed output, auth failure, unsupported CLI version and timeouts cannot establish authenticated zero. They block allocation with `READBACK_UNVERIFIED` or leave `cleanup_confirmed=false` / `CLEANUP_FAILED`; nonzero assignments also block. Raw stderr is never parsed as success evidence. A positive usage balance is existing entitlement, not proof of exact charges. This trusts the audited installed CLI/Google authenticated-response semantics, not arbitrary executables reporting that version, and does not attest concurrent account activity after the response. No new provider API, credential handling or vendor patch is introduced.

Reports contain safe codes, command operation/timing, UTC/monotonic events, source and adapter hashes. Raw output/argv, private roots, OAuth/session URLs and environment dumps are omitted. Unobserved installation/CPU/publication/human approval/handoff fields remain null; no GitHub write occurs in this tool. Live GPU, TPU and compilation remain NOT_RUN in this extraction. [Local evidence](../../reports/compute-issue38/summary.md) records exact tested source and observed tests; GPT reviews and decides merge independently.
