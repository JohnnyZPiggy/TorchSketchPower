"""CPU-only status and install-provenance regressions; no remote resources."""
import json
import contextlib
import importlib.metadata
import io
import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "experiments", "m7_cuda"))
import colab_driver as driver
import run_m7_cuda as runner


def mock_plan(monkeypatch, rows, *, cuda=True, devices=1):
    monkeypatch.setattr(runner.torch.cuda, "is_available", lambda: cuda)
    monkeypatch.setattr(runner, "environment", lambda dev: {"cuda_device_count": devices})
    monkeypatch.setattr(runner, "build_plan", lambda quick: [("negative", {})])
    monkeypatch.setattr(runner.lib, "negative_cases", lambda dev: rows)


def row(status="PASS", case="control", reason=None):
    return {"case": case, "device": "cuda", "dtype": "float64", "status": status, "reason": reason}


def run_report(tmp_path, *args):
    code = runner.main(["--device", "cuda", "--out", str(tmp_path), *args])
    return code, json.loads((tmp_path / "results.json").read_text())


@pytest.mark.parametrize("limit", [-1, 0])
def test_timeout_before_any_job_cannot_pass(monkeypatch, tmp_path, limit):
    mock_plan(monkeypatch, [row()])
    code, rep = run_report(tmp_path, "--max-seconds", str(limit))
    assert code == 2 and rep["status"] == "BLOCKED" and not rep["plan_complete"]
    assert rep["completed_jobs"] == 0 and rep["gpu_evidence"] is False
    assert rep["rows"][0]["status"] == "NOT_RUN"


@pytest.mark.parametrize("last_job", [False, True])
def test_timeout_after_results_preserves_rows_but_blocks(monkeypatch, tmp_path, last_job):
    mock_plan(monkeypatch, [row()])
    monkeypatch.setattr(runner, "build_plan", lambda quick: [("negative", {})] * (1 if last_job else 2))
    clock = [0.0]
    monkeypatch.setattr(runner.time, "time", lambda: clock[0])

    def slow(dev):
        clock[0] = 2.0
        return [row()]

    monkeypatch.setattr(runner.lib, "negative_cases", slow)
    code, rep = run_report(tmp_path, "--max-seconds", "1")
    assert code == 2 and rep["status"] == "BLOCKED" and not rep["plan_complete"]
    assert rep["rows"][0]["status"] == "PASS" and rep["completed_jobs"] == 1
    if not last_job:
        assert rep["rows"][1]["reason"] == "time limit reached"


@pytest.mark.parametrize("empty_plan", [False, True])
def test_empty_plan_or_missing_result_cannot_pass(monkeypatch, tmp_path, empty_plan):
    mock_plan(monkeypatch, [])
    if empty_plan:
        monkeypatch.setattr(runner, "build_plan", lambda quick: [])
    code, rep = run_report(tmp_path)
    assert code == 2 and rep["status"] == "BLOCKED" and not rep["plan_complete"]


@pytest.mark.parametrize("status,expected,code", [
    ("PASS", "PASS", 0), ("FAIL", "FAIL", 1), ("BLOCKED", "BLOCKED", 2),
    ("NOT_RUN", "BLOCKED", 2), ("UNKNOWN", "BLOCKED", 2),
])
def test_required_result_status(monkeypatch, tmp_path, status, expected, code):
    rows = [row(status)]
    mock_plan(monkeypatch, rows)
    got, rep = run_report(tmp_path)
    assert got == code and rep["status"] == expected and rep["rows"] == rows


@pytest.mark.parametrize("devices,reason,expected", [
    (1, "only one CUDA device", "PASS"),
    (2, "only one CUDA device", "BLOCKED"),
    (1, "time limit reached", "BLOCKED"),
])
def test_only_designated_single_gpu_exclusion_is_optional(monkeypatch, tmp_path, devices, reason, expected):
    rows = [row(), row("NOT_RUN", "mixed CUDA indices", reason)]
    mock_plan(monkeypatch, rows, devices=devices)
    _, rep = run_report(tmp_path)
    assert rep["status"] == expected and rep["rows"] == rows and rep["plan_complete"]


@pytest.mark.parametrize("status,expected,code", [("FAIL", "FAIL", 1), ("NOT_RUN", "BLOCKED", 2)])
def test_cpu_dry_run_does_not_hide_failed_or_missing_required_result(monkeypatch, tmp_path, status, expected, code):
    mock_plan(monkeypatch, [row(status)], cuda=False)
    got = runner.main(["--device", "cpu", "--out", str(tmp_path)])
    rep = json.loads((tmp_path / "results.json").read_text())
    assert got == code and rep["status"] == expected and not rep["gpu_evidence"]


@pytest.mark.parametrize("failure", ["install", "import", "identity"])
def test_install_failure_stops_before_running_scientific_code(monkeypatch, failure):
    calls = []

    def sh(args, timeout, **kwargs):
        calls.append((args, timeout, kwargs))
        if (len(calls) == 1 and failure == "install") or (len(calls) == 2 and failure == "import"):
            return 1, "", "failed"
        return 0, json.dumps({"verified": True, "source_sha": "wrong"}), ""

    monkeypatch.setattr(driver, "sh", sh)
    with pytest.raises(ValueError, match="PACKAGE_"):
        driver.install_project("checkout", {})
    assert len(calls) == (1 if failure == "install" else 2)


def test_noneditable_install_and_isolated_import_probe_are_bounded(monkeypatch):
    calls = []
    identity = {"verified": True, "source_sha": "a" * 40, "editable": False}

    def sh(args, timeout, **kwargs):
        calls.append((args, timeout, kwargs))
        return 0, json.dumps(identity), ""

    monkeypatch.setattr(driver, "SHA", identity["source_sha"])
    monkeypatch.setattr(driver, "sh", sh)
    assert driver.install_project("checkout", {}) == identity
    install, probe = calls
    assert install[0][:6] == [sys.executable, "-I", "-m", "pip", "install", "--no-deps"]
    assert install[0][-1] == "." and "-e" not in install[0] and "--force-reinstall" in install[0]
    assert install[1] == 120 and install[2]["cwd"] == "checkout"
    assert probe[0][:3] == [sys.executable, "-I", "-c"] and probe[1] == 30


@pytest.mark.parametrize("fault", [None, "source", "editable", "modified", "unowned"])
def test_import_probe_checks_actual_path_metadata_and_file_bytes(monkeypatch, tmp_path, fault):
    import torchsketchpower

    repo = tmp_path / "repo"
    source = repo / "src/torchsketchpower"
    source.mkdir(parents=True)
    (source / "__init__.py").write_bytes(b"# exact source\n")
    installed = source if fault == "source" else tmp_path / "site-packages/torchsketchpower"
    installed.mkdir(parents=True, exist_ok=True)
    (installed / "__init__.py").write_bytes(b"# stale\n" if fault == "modified" else b"# exact source\n")
    monkeypatch.setattr(torchsketchpower, "__file__", str(installed / "__init__.py"))
    dist = SimpleNamespace(
        locate_file=lambda name: installed.parent / name,
        read_text=lambda name: json.dumps({"dir_info": {"editable": fault == "editable"}}),
        files=[] if fault == "unowned" else ["torchsketchpower/__init__.py"], version="0.1.0",
    )
    monkeypatch.setattr(importlib.metadata, "distribution", lambda name: dist)

    def sh(args, timeout, **kwargs):
        if "-c" not in args:
            return 0, "", ""  # isolate the verification from pip in this unit test
        monkeypatch.setattr(sys, "argv", ["probe", *args[4:]])
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                exec(args[3], {})
        except AssertionError as exc:
            return 1, "", str(exc)
        return 0, out.getvalue(), ""

    monkeypatch.setattr(driver, "sh", sh)
    if fault:
        with pytest.raises(ValueError, match="PACKAGE_IMPORT_VERIFICATION_FAILED"):
            driver.install_project(str(repo), {})
    else:
        identity = driver.install_project(str(repo), {})
        assert identity["verified"] and not identity["editable"]
        assert identity["module_file"] == str((installed / "__init__.py").resolve())
