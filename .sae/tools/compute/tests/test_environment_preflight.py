# SPDX-License-Identifier: MIT
# Copyright (c) 2026 JohnnyZPiggy
"""Local Git/temp integration and fake CLI/pip; no Colab calls."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import environment_preflight as env

REAL_RUN = subprocess.run


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'repo'
        self.root.mkdir()
        self.git('init', '-q')
        self.git('config', 'core.autocrlf', 'false')
        (self.root / 'file.txt').write_bytes(b'original\nGit bytes\n')
        (self.root / '.sae').mkdir()
        (self.root / '.sae' / 'unchanged.md').write_bytes(b'document snapshot\n')
        self.git('add', 'file.txt')
        self.git('add', '.sae')
        self.git('-c', 'user.name=Local test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture')
        self.sha = self.git('rev-parse', 'HEAD').stdout.decode().strip()
        self.calls = []

    def git(self, *args):
        return REAL_RUN(['git', '-C', str(self.root), *args], capture_output=True, check=True)

    def fake(self, args, **kwargs):
        self.calls.append(args)
        if args[0] == 'fake-colab':
            self.assertEqual(args, ['fake-colab', 'version'])
            return subprocess.CompletedProcess(args, 0, b'Version: fake', b'')
        if args[:3] == [sys.executable, '-m', 'pip']:
            source = Path(args[-1])
            self.assertEqual((source / 'file.txt').read_bytes(), b'original\nGit bytes\n')
            self.assertFalse((source / '.sae').exists())
            child_env = kwargs['env']
            for key in ('TEMP', 'TMP', 'TMPDIR', 'PIP_CACHE_DIR'):
                self.assertTrue(Path(child_env[key]).is_dir())
                self.assertNotIn(self.root, Path(child_env[key]).parents)
            self.assertEqual(kwargs['cwd'].name, 'build')
            self.assertIn('--no-deps', args)
            return subprocess.CompletedProcess(args, 0, b'fake install', b'')
        return REAL_RUN(args, **kwargs)

    def test_exact_export_ignores_dirty_crlf_worktree_and_local_pip_paths(self):
        (self.root / 'file.txt').write_bytes(b'modified\r\ncheckout\r\n')
        with patch.object(env.subprocess, 'run', side_effect=self.fake):
            result = env.preflight(self.root, self.sha, 'fake-colab', self.base, install=True)
        self.assertEqual(result['status'], 'PASS')
        self.assertTrue(result['working_tree_dirty'])
        self.assertEqual(result['exported_blobs'], 1)
        self.assertTrue(result['temp_build_cache_writable'])
        self.assertEqual(result['events']['wheel_pip_install']['status'], 'PASS')
        self.assertNotIn(str(self.base), json.dumps(result))
        self.assertFalse(list(self.base.glob('sae-preflight-*')))

    def test_default_preflight_does_not_install_or_contact_provider(self):
        with patch.object(env.subprocess, 'run', side_effect=self.fake):
            result = env.preflight(self.root, self.sha, 'fake-colab', self.base)
        self.assertIsNone(result['events']['wheel_pip_install'])
        self.assertFalse(any('-m' in call for call in self.calls))
        for call in self.calls:
            self.assertNotIn('new', call)
            self.assertNotIn('sessions', call)

    def test_invalid_sha_before_any_command(self):
        with patch.object(env.subprocess, 'run') as run:
            with self.assertRaises(env.PreflightError) as caught:
                env.preflight(self.root, 'main', 'fake-colab', self.base)
        self.assertEqual(caught.exception.code, 'INVALID_SOURCE_SHA')
        run.assert_not_called()

    def test_reject_synced_or_checkout_temp(self):
        for target in (self.root, self.base / 'Dropbox-build'):
            with self.subTest(target=target), patch.object(env.subprocess, 'run', side_effect=self.fake):
                with self.assertRaises(env.PreflightError) as caught:
                    env.preflight(self.root, self.sha, 'fake-colab', target)
            self.assertEqual(caught.exception.code, 'UNSAFE_TEMP_ROOT')

    def test_nonwritable_temp_stops_before_pip(self):
        with patch.object(env.subprocess, 'run', side_effect=self.fake), \
             patch.object(env.tempfile, 'TemporaryDirectory', side_effect=PermissionError('/private/root token=secret')):
            with self.assertRaises(env.PreflightError) as caught:
                env.preflight(self.root, self.sha, 'fake-colab', self.base, install=True)
        self.assertEqual(caught.exception.code, 'LOCAL_PREFLIGHT_FAILED')
        self.assertNotIn('private', json.dumps(caught.exception.report))
        self.assertFalse(any('-m' in call for call in self.calls))

    def test_git_or_cli_timeout_is_bounded_and_safe(self):
        with patch.object(env.subprocess, 'run', side_effect=subprocess.TimeoutExpired('private', 1)):
            with self.assertRaises(env.PreflightError) as caught:
                env.preflight(self.root, self.sha, 'fake-colab', self.base)
        self.assertEqual(caught.exception.code, 'PREFLIGHT_TIMEOUT')
        self.assertGreaterEqual(caught.exception.report['elapsed_seconds'], 0)

    def test_cli_resolution_and_missing_cli(self):
        with patch.object(env.shutil, 'which', return_value=None):
            with self.assertRaisesRegex(env.PreflightError, 'CLI_UNAVAILABLE'):
                env.resolve_cli('absent')
        with patch.object(env.shutil, 'which', return_value=str(self.base / 'space dir' / 'colab')):
            self.assertEqual(env.resolve_cli('colab'), str((self.base / 'space dir' / 'colab').resolve()))



if __name__ == '__main__':
    unittest.main()
