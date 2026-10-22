# SPDX-License-Identifier: MIT
# Copyright (c) 2026 JohnnyZPiggy
"""Local-only checks and exact Git export; never authenticate or allocate Colab."""
import argparse
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import time


class PreflightError(RuntimeError):
    def __init__(self, code, report=None):
        self.code, self.report = code, report
        super().__init__(code)


def resolve_cli(command):
    path = shutil.which(command)
    if not path:
        raise PreflightError('CLI_UNAVAILABLE')
    return str(Path(path).resolve())


def preflight(root, sha, cli, temp_root=None, install=False, deadline=None):
    start = time.monotonic()
    report = {'status': 'FAIL', 'python_version': sys.version.split()[0],
              'source_sha': sha if re.fullmatch(r'[0-9a-f]{40}', sha) else None,
              'events': {}, 'cli_verified': False}
    deadline = deadline if deadline is not None else start + 120

    def command(args, **kwargs):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise PreflightError('PREFLIGHT_TIMEOUT')
        try:
            if 'input' not in kwargs:
                kwargs['stdin'] = subprocess.DEVNULL
            result = subprocess.run(args, capture_output=True,
                                    timeout=min(60, remaining), **kwargs)
        except subprocess.TimeoutExpired:
            raise PreflightError('PREFLIGHT_TIMEOUT') from None
        except OSError:
            raise PreflightError('EXECUTABLE_FAILED') from None
        if result.returncode:
            raise PreflightError('PREFLIGHT_COMMAND_FAILED')
        return result.stdout

    def event(name, action):
        tick = time.monotonic()
        state = report['events'][name] = {'utc_start': datetime.now(timezone.utc).isoformat(), 'status': 'FAIL'}
        try:
            result = action()
            state['status'] = 'PASS'
            return result
        finally:
            state.update(utc_end=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic() - tick)

    try:
        if not re.fullmatch(r'[0-9a-f]{40}', sha):
            raise PreflightError('INVALID_SOURCE_SHA')
        git = resolve_cli('git')
        version = event('cli_version', lambda: command([cli, 'version']))
        match = re.search(rb'Version:\s*([0-9.]+)', version)
        report['cli_version'] = match[1].decode() if match else None
        report['cli_verified'] = True
        actual = event('source_verification', lambda: command(
            [git, '-C', str(root), 'rev-parse', '--verify', sha + '^{commit}'])).decode().strip()
        if actual != sha:
            raise PreflightError('SOURCE_SHA_MISMATCH')
        report['working_tree_dirty'] = bool(command([git, '-C', str(root), 'status', '--porcelain']))
        temp = Path(temp_root or tempfile.gettempdir()).resolve()
        if temp == root.resolve() or root.resolve() in temp.parents or any('dropbox' in part.lower() for part in temp.parts):
            raise PreflightError('UNSAFE_TEMP_ROOT')
        with tempfile.TemporaryDirectory(prefix='sae-preflight-', dir=temp) as staging:
            staging = Path(staging)
            env = os.environ.copy()
            def check_paths():
                for name in ('tmp', 'build', 'cache'):
                    directory = staging / name
                    directory.mkdir()
                    probe = directory / 'write-check'
                    probe.write_bytes(b'ok')
                    probe.unlink()
            event('temp_build_cache', check_paths)
            env.update(TMPDIR=str(staging / 'tmp'), TEMP=str(staging / 'tmp'), TMP=str(staging / 'tmp'),
                       PIP_CACHE_DIR=str(staging / 'cache'))
            report['temp_build_cache_writable'] = True

            def extract():
                entries = []
                for row in command([git, '-C', str(root), 'ls-tree', '-r', '-z', sha]).split(b'\0'):
                    if not row:
                        continue
                    meta, name = row.split(b'\t', 1)
                    if name.startswith(b'.sae/'):
                        continue
                    mode, kind, blob = meta.split()
                    path = PurePosixPath(name.decode('utf-8'))
                    if mode not in (b'100644', b'100755') or kind != b'blob' or path.is_absolute() or '..' in path.parts or '\\' in str(path) or ':' in str(path):
                        raise PreflightError('UNSAFE_GIT_ENTRY')
                    entries.append((path, blob))
                raw = command([git, '-C', str(root), 'cat-file', '--batch'], input=b''.join(blob+b'\n' for _, blob in entries))
                stream = io.BytesIO(raw)
                export = staging / 'source'
                export.mkdir()
                for path, blob in entries:
                    if time.monotonic() >= deadline:
                        raise PreflightError('PREFLIGHT_TIMEOUT')
                    header = stream.readline().split()
                    if len(header) != 3 or header[:2] != [blob, b'blob']:
                        raise PreflightError('GIT_EXPORT_INVALID')
                    data = stream.read(int(header[2]))
                    if len(data) != int(header[2]) or stream.read(1) != b'\n':
                        raise PreflightError('GIT_EXPORT_INVALID')
                    target = export.joinpath(*path.parts)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                    if target.read_bytes() != data:
                        raise PreflightError('GIT_EXPORT_INVALID')
                report['export_scope'] = 'tracked project files excluding .sae/'
                report['exported_blobs'] = len(entries)
                return export
            export = event('snapshot_extraction', extract)
            report['events']['wheel_pip_install'] = None
            if install:
                event('wheel_pip_install', lambda: command([sys.executable, '-m', 'pip', 'install',
                    '--no-deps', '--no-build-isolation', '--no-cache-dir', '--target', str(staging / 'site'),
                    str(export)], env=env, cwd=staging / 'build'))
        report['status'] = 'PASS'
    except BaseException as exc:
        report['error'] = exc.code if isinstance(exc, PreflightError) else (
            'INTERRUPTED' if isinstance(exc, KeyboardInterrupt) else 'LOCAL_PREFLIGHT_FAILED')
        raise PreflightError(report['error'], report) from None
    finally:
        report['elapsed_seconds'] = time.monotonic() - start
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-sha', required=True)
    p.add_argument('--repo-path', type=Path, required=True)
    p.add_argument('--cli', default='colab')
    p.add_argument('--temp-root', type=Path)
    p.add_argument('--install-local', action='store_true')
    args = p.parse_args()
    try:
        result = preflight(args.repo_path.resolve(), args.source_sha,
                           resolve_cli(args.cli), args.temp_root, args.install_local)
    except PreflightError as exc:
        result = exc.report or {'status': 'BLOCKED', 'error': exc.code}
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
