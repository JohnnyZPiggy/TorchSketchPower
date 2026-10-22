# SPDX-License-Identifier: MIT
# Copyright (c) 2026 JohnnyZPiggy
"""Explicit offline diagnostic. Run with the existing CLI's Python, not `colab`.

No credentials, persistent stores, real HTTP, CLI main, or runtime are used.
Mock hangs ignore HTTP timeouts deliberately; only the parent kills those children.
"""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
from importlib import metadata
import inspect
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
from unittest.mock import Mock, patch


def deny_network(*args, **kwargs):
    raise AssertionError('NETWORK_DISABLED')


def dependencies():
    # Install the socket guard before importing third-party modules.
    assert metadata.version('google-colab-cli') == '0.7.4', 'CLI_VERSION_MISMATCH'
    import requests
    from google.auth.credentials import AnonymousCredentials
    from google.auth.transport.requests import AuthorizedSession
    from colab_cli import client, common
    from colab_cli.commands import session
    return requests, AnonymousCredentials, AuthorizedSession, client, common, session


def run_child(mode):
    requests, Anonymous, Authorized, client, common, session = dependencies()
    state = common.State()
    state._store, state._history = Mock(), Mock()
    with Authorized(Anonymous()) as transport:
        transport.trust_env = False  # No netrc credentials or environment proxies.
        state._client = client.Client(client.Prod(), transport)

        def send(request, **kwargs):
            # Do not print URLs, headers, bodies, tokens, paths or exception text.
            print(json.dumps({'method': request.method, 'timeout': kwargs.get('timeout')}), flush=True)
            assert kwargs['timeout'] == 120
            if mode == request.method:
                time.sleep(60)
                raise AssertionError('PARENT_DID_NOT_KILL_CHILD')
            response = requests.Response()
            response.status_code, response.reason, response.request = 200, 'OK', request
            data = ({'acc': 'T4', 'nbh': 'mock', 'token': 'synthetic', 'variant': 'GPU'}
                    if request.method == 'GET' else
                    {'accelerator': 'T4', 'endpoint': 'synthetic', 'variant': 1,
                     'runtimeProxyInfo': {'token': 'synthetic', 'tokenExpiresInSeconds': 600,
                                          'url': 'https://runtime.invalid'}})
            response._content = json.dumps(data).encode()
            return response

        with patch.object(common, 'state', state), \
             patch.object(common, 'get_credentials', side_effect=deny_network), \
             patch.object(requests.sessions, 'get_netrc_auth', side_effect=deny_network), \
             patch.object(requests.adapters.HTTPAdapter, 'send', side_effect=send), \
             patch.object(session.typer, 'echo'):
            if mode == 'OUTER':
                print(json.dumps({'stage': 'BEFORE_ASSIGN'}), flush=True)
                time.sleep(60)
                raise AssertionError('PARENT_DID_NOT_KILL_CHILD')
            session.new(session='offline-synthetic', gpu='T4', tpu=None, high_mem=False)
            state.store.add.assert_called_once()


def source_record(obj):
    path = Path(inspect.getsourcefile(obj))
    lines, first = inspect.getsourcelines(obj)
    # Module-relative basename and digest only; no installed private root.
    return {'file': obj.__module__.replace('.', '/') + '.py',
            'first_line': first, 'last_line': first + len(lines) - 1,
            'file_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def diagnose():
    started, tick = datetime.now(timezone.utc).isoformat(), time.monotonic()
    requests, Anonymous, Authorized, client, common, session = dependencies()
    auth_signature = inspect.signature(Authorized.request)
    assert auth_signature.parameters['timeout'].default == 120
    assert auth_signature.parameters['max_allowed_time'].default is None
    assert inspect.signature(requests.Session.request).parameters['timeout'].default is None
    scalar = requests.adapters.TimeoutSauce(connect=120, read=120)
    assert scalar.connect_timeout == scalar.read_timeout == 120
    with Authorized(Anonymous()) as transport:
        auth_defaults = {'refresh_timeout': transport._refresh_timeout,
                         'max_refresh_attempts': transport._max_refresh_attempts,
                         'auth_transport_retries': transport._auth_request_session.adapters['https://'].max_retries.total,
                         'api_transport_retries': transport.adapters['https://'].max_retries.total}
    cases = []
    # Each process imports real installed code but intercepts HTTPAdapter.send.
    for mode in ('PASS', 'GET', 'POST', 'OUTER'):
        before = time.monotonic()
        timed_out = False
        try:
            result = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--child', mode],
                                    capture_output=True, timeout=3, stdin=subprocess.DEVNULL)
            raw = result.stdout
            assert result.returncode == 0 and not result.stderr, 'OFFLINE_CHILD_FAILED'
        except subprocess.TimeoutExpired as exc:
            raw, timed_out = exc.stdout or b'', True
        trace = [json.loads(line) for line in raw.decode().splitlines()]
        expected = ([{'stage': 'BEFORE_ASSIGN'}] if mode == 'OUTER' else
                    [{'method': method, 'timeout': 120} for method in
                     (['GET'] if mode == 'GET' else ['GET', 'POST'])])
        assert trace == expected and timed_out == (mode != 'PASS'), 'UNEXPECTED_MOCK_TRACE'
        cases.append({'case': mode, 'status': 'PASS', 'trace': trace,
                      'outer_timeout_expected': timed_out, 'outer_timeout_seconds': 3,
                      'elapsed_seconds': time.monotonic() - before})

    # Real status/sync implementation, fake client and memory-only stores.
    state = common.State()
    state._store, state._history = Mock(), Mock()
    state._store.list.return_value = {}
    state._store.get.return_value = None
    state._client = Mock()
    state._client.list_assignments.return_value = []
    with patch.object(common, 'state', state), patch.object(session.typer, 'echo'), \
         patch.object(common, 'get_credentials', side_effect=deny_network):
        for _ in range(2):
            session.status(session='offline-synthetic')
    assert state.client.list_assignments.call_count == 2
    state.store.remove.assert_not_called()
    # Local state can also be pruned; status is not a local read-only observer.
    stale = Mock(endpoint='synthetic')
    state._sessions = None
    state.store.list.return_value = {'offline-synthetic': stale}
    with patch.object(common.typer, 'echo'):
        state.sync_sessions()
    state.store.remove.assert_called_once_with('offline-synthetic')
    # Empty-store auth SystemExit is swallowed upstream: no unconditional zero proof.
    state._sessions = None
    state.store.list.return_value = {}
    state.client.list_assignments.side_effect = SystemExit(1)
    local, assignments = state.sync_sessions()
    assert local == {} and assignments == []
    cases.append({'case': 'STATUS_REMOTE_SYNC', 'status': 'PASS',
                  'two_status_calls_assignment_requests': 2, 'stale_local_state_pruned': True,
                  'empty_store_auth_systemexit_returns_empty': True})
    return {'classification': 'LOCAL_MOCK_NO_PROVIDER_CALLS', 'status': 'PASS',
            'utc_start': started, 'utc_end': datetime.now(timezone.utc).isoformat(),
            'elapsed_seconds': time.monotonic() - tick, 'python_version': sys.version.split()[0],
            'versions': {name: metadata.version(name) for name in ('google-colab-cli', 'google-auth', 'requests')},
            'authorized_http_timeout_seconds': 120, 'authorized_max_allowed_time': None,
            'plain_requests_timeout': None, 'requests_scalar_connect_read_seconds': [120, 120],
            'mock_boundary': 'requests.adapters.HTTPAdapter.send', 'auth_defaults': auth_defaults,
            'diagnostic_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'sources': [source_record(obj) for obj in (session.new, client.Client.assign,
                        client.Client._get_assignment, client.Client._post_assignment,
                        client.Client._issue_request, common.State.client.fget,
                        common.get_credentials, Authorized.request, requests.Session.request,
                        requests.Session.send, requests.adapters.HTTPAdapter.send,
                        session.status, common.State.sync_sessions)],
            'cases': cases, 'real_allocation_attempts': 0, 'real_provider_requests': 0,
            'real_credentials_loaded': False, 'live_ready': 'NOT_GRANTED',
            'limitation': 'Mock hangs ignore socket timers; they prove forwarding and process bounds, not provider root cause or live release.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--child', choices=('PASS', 'GET', 'POST', 'OUTER'))
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    with ExitStack() as guard:
        for name in ('connect', 'connect_ex'):
            guard.enter_context(patch.object(socket.socket, name, side_effect=deny_network))
        guard.enter_context(patch.object(socket, 'create_connection', side_effect=deny_network))
        if args.child:
            run_child(args.child)
        else:
            report = diagnose()
            raw = json.dumps(report, indent=2) + '\n'
            if args.out:
                with args.out.open('x', encoding='utf-8', newline='\n') as handle:
                    handle.write(raw)
            print(raw, end='')
