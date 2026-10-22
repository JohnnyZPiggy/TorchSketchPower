# Colab CLI 0.7.4: offline timeout diagnosis

This diagnostic imports the **existing CLI interpreter's installed modules**, not the CLI main entry point. It never calls the provider, loads account credentials, creates a real runtime, or opens persistent session/history/settings stores. Standard-library mocks replace the HTTP adapter, credential lookup and stores; socket connect operations are denied. No dependency is installed and no third-party file is patched. Do not run it with `colab exec` or a live diagnostic wrapper.

Run with the Python executable from the installed `colab` script's shebang, from a shell where that interpreter already works:

```sh
EXISTING_CLI_PYTHON tools/compute/diagnostics/colab_cli_074.py --out NEW_REPORT.json
```

`EXISTING_CLI_PYTHON` means that existing executable, not a request to install another Python. System Python may have no CLI distribution; the CLI may use its own uv environment. Only version 0.7.4 is accepted. The output path must be new and its parent must exist. Each local child has a 3-second process timeout; synthetic sleeps deliberately ignore HTTP timers. A slow import can fail the diagnostic rather than imply provider failure. The normal standard-library suite remains independent of CLI internals:

```sh
python -m unittest discover -s tools/compute/tests -v
```

## Installed call chain and timeout distinction

`commands.session.new` → lazy `common.State.client` → `auth.get_credentials` → `AuthorizedSession(creds)` → `Client.assign` → `_get_assignment` → `_issue_request` → `AuthorizedSession.request` → `requests.Session.request` → `Session.send` → `HTTPAdapter.send` → urllib3. GET can return an existing `Assignment` and bypass POST; otherwise `assign` calls `_post_assignment`, then the same request stack with POST. New session state/history is saved only after assign returns. Authentication can occur before either assignment HTTP call.

CLI `_get_assignment`, `_post_assignment` and `_issue_request` do not supply a timeout. **That does not mean unbounded HTTP:** the installed google-auth 2.62.0 AuthorizedSession defaults to `timeout=120`, `max_allowed_time=None`; Requests 2.34.2 receives 120 on both mocked GET and POST at the adapter boundary. Plain Requests alone defaults to `timeout=None`. HTTPAdapter converts scalar 120 to connect=120/read=120; those are individual connection/read waits, not a whole CLI wall-clock guarantee. Headers/body processing, authentication, redirects and sequential GET/POST can add time. Credential refresh defaults to two refresh attempts and its own transport has three connection retries; the API adapter defaults to zero retries. These library defaults are inspected, not new controller allocation retries or live authentication tests.

The controller retains `min(120, remaining_work_budget)` for the single `new` subprocess. This outer bound covers startup, authentication and the complete assignment path; it can terminate before an individual HTTP timeout finishes. `ALLOCATION_FAILED` stays compatible. New safe fields distinguish `CLI_SUBPROCESS_TIMEOUT` from `CLI_COMMAND_FAILED` and explicitly record `allocation_http_phase=UNKNOWN`. They do not infer GET/POST, quota exhaustion, device availability, or successful allocation from raw output. No debug logging or response-body capture is enabled: upstream debug logging can contain credentials and URLs.

## Status observer policy

**No status polling during allocation.** `status` calls `State.sync_sessions()` before looking up a named session. Even an empty or already cached local state invokes `client.list_assignments()`; stale local entries may be pruned, and surviving entries have proxy information persisted. Two mocked status calls produce two assignment queries. A status exit code of zero does not prove hardware exists.

PR #41's temporary host observer made 71 such status calls; it is discontinued, and its local polling block has been removed without rerunning it. The reusable controller itself has no status loop. Use its existing bounded subprocess result and cleanup report; do not replace status with high-frequency `sessions` queries. For a separately authorized future live task, preserve the mandatory stop and bounded server readback, single allocation, finite cleanup reserve and independent abort. Device identity stays unobserved when no reliable evidence exists.

An additional upstream limitation is reproduced locally: with an empty store, `sync_sessions()` catches authentication `SystemExit` and returns an empty assignment list. Thus a printed empty list alone is not unconditional proof of successful authenticated server readback. This does not establish that authentication failed in PR #41. No third-party authentication or cleanup behavior is changed here; GPT should assess a separate, minimal authenticated-readback fix before relying on that edge case in future live acceptance.

Issue #43 replaces the controller's text-only sessions check with the existing CLI 0.7.4 authenticated `usage`/ccu-info path; see the current [readback contract](../README.md#bounds-and-evidence). To check that installed path locally, run the following **with the existing CLI's Python** (same network/credential guards and fresh output requirement):

```sh
EXISTING_CLI_PYTHON tools/compute/diagnostics/authenticated_readback_074.py --out NEW_REPORT.json
```

This mocks backend authentication success with a synthetic bearer token and a schema-valid HTTP 200 response, and separately covers swallowed auth exit, expired credentials, HTTP 403, timeout, empty body, missing count and nonempty assignments. It does not load real credentials or call CLI main/new. Tests require the full usage success path, not exit status or empty lists alone. [Issue 43 evidence](../../../reports/compute-issue43/summary.md) distinguishes simulated authenticated responses from real provider verification.

## Evidence limits

[Recorded local evidence](../../../reports/colab-cli-074-offline-diagnosis/summary.md) includes installed source SHA-256 and function line ranges. No upstream code is vendored. Mocks test GET/POST timeout forwarding, hangs and parent process termination, plus status synchronization; they do **not** test socket timer accuracy, real credential refresh, provider root cause, current remote session state, live release or LIVE_READY. Keep Issue #40's observed timeout and verified cleanup evidence unchanged.
