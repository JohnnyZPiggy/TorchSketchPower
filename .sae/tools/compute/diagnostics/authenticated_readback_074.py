# SPDX-License-Identifier: MIT
# Copyright (c) 2026 JohnnyZPiggy
"""Local mocks of installed CLI authenticated readback; never invoke CLI main."""
import argparse
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import socket
import sys
import time
from unittest.mock import patch

from colab_cli_074 import deny_network, dependencies, source_record

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from colab_control import authenticated_usage


def diagnose():
    started, tick = datetime.now(timezone.utc).isoformat(), time.monotonic()
    requests, _, Authorized, client, common, session = dependencies()
    from colab_cli.commands import usage
    from google.oauth2.credentials import Credentials

    results = []
    for case in ('AUTHENTICATED_EMPTY', 'NONEMPTY', 'SWALLOWED_AUTH_EMPTY',
                 'EXPIRED_CREDENTIALS', 'UNAUTHORIZED', 'REMOTE_TIMEOUT', 'EMPTY_BODY', 'MISSING_COUNT'):
        state = common.State()  # No lazy file stores are accessed by usage.
        sends = []
        creds = Credentials(token='synthetic', expiry=datetime.now(timezone.utc).replace(tzinfo=None) +
                            timedelta(hours=-1 if case == 'EXPIRED_CREDENTIALS' else 1))
        with Authorized(creds) as transport:
            transport.trust_env = False
            if case != 'SWALLOWED_AUTH_EMPTY':
                state._client = client.Client(client.Prod(), transport)

            def send(request, **kwargs):
                assert request.method == 'GET' and kwargs['timeout'] == 120
                assert request.headers.get('authorization') == 'Bearer synthetic'
                sends.append({'method': 'GET', 'timeout': kwargs['timeout'], 'synthetic_auth_header': True})
                if case == 'REMOTE_TIMEOUT':
                    raise requests.exceptions.ReadTimeout('synthetic secret omitted')
                response = requests.Response()
                response.status_code = 403 if case == 'UNAUTHORIZED' else 200
                response.reason, response.request = 'Synthetic', request
                body = {'currentBalance': 10.0, 'consumptionRateHourly': 0.0,
                        'assignmentsCount': 1 if case == 'NONEMPTY' else 0}
                if case == 'MISSING_COUNT':
                    del body['assignmentsCount']
                response._content = b'' if case == 'EMPTY_BODY' else json.dumps(body).encode()
                return response

            def invoke(action):
                output, errors, exit_code = io.StringIO(), io.StringIO(), 0
                try:
                    with redirect_stdout(output), redirect_stderr(errors):
                        action()
                except (SystemExit, usage.typer.Exit) as exc:
                    exit_code = exc.code if isinstance(exc, SystemExit) else exc.exit_code
                # No raw stderr/exception/headers/body is returned or published.
                return exit_code, output.getvalue()

            with patch.object(common, 'state', state), \
                 patch.object(common, 'get_credentials', side_effect=SystemExit(1)), \
                 patch.object(requests.sessions, 'get_netrc_auth', side_effect=deny_network), \
                 patch.object(requests.adapters.HTTPAdapter, 'send', side_effect=send):
                legacy_false_zero = False
                if case == 'SWALLOWED_AUTH_EMPTY':
                    from unittest.mock import Mock
                    state._store = Mock()
                    state.store.list.return_value = {}
                    legacy_code, legacy_output = invoke(session.sessions_command)
                    legacy_false_zero = legacy_code == 0 and 'No active sessions found on server.' in legacy_output
                    assert legacy_false_zero
                code, output = invoke(usage.usage)
                parsed = authenticated_usage(output) if code == 0 else None
                if case in ('AUTHENTICATED_EMPTY', 'NONEMPTY'):
                    assert code == 0 and parsed == {'balance': 10.0, 'assignments': int(case == 'NONEMPTY')}
                else:
                    assert code != 0 and parsed is None
                results.append({'case': case, 'test_status': 'PASS', 'usage_exit_code': code,
                                'readback_status': 'READBACK_UNVERIFIED' if parsed is None else (
                                    'AUTHENTICATED_ZERO' if parsed['assignments'] == 0 else 'ACTIVE_ASSIGNMENTS'),
                                'legacy_false_zero_reproduced': legacy_false_zero, 'mock_requests': sends})
    return {'classification': 'LOCAL_MOCK_NO_PROVIDER_CALLS', 'status': 'PASS',
            'utc_start': started, 'utc_end': datetime.now(timezone.utc).isoformat(),
            'elapsed_seconds': time.monotonic() - tick, 'python_version': sys.version.split()[0],
            'cases': results, 'cli_version': '0.7.4', 'provider': 'NOT_RUN',
            'real_provider_requests': 0, 'real_credentials_loaded': False, 'live_ready': 'NOT_GRANTED',
            'diagnostic_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'controller_sha256': hashlib.sha256((Path(__file__).resolve().parents[1]/'colab_control.py').read_bytes()).hexdigest(),
            'sources': [source_record(obj) for obj in (usage.usage, client.Client.get_consumption_user_info,
                        common.State.sync_sessions, session.sessions_command)],
            'limitation': 'Synthetic credentials and HTTP responses only; no live authentication or current server state verified.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    with ExitStack() as guard:
        for name in ('connect', 'connect_ex'):
            guard.enter_context(patch.object(socket.socket, name, side_effect=deny_network))
        guard.enter_context(patch.object(socket, 'create_connection', side_effect=deny_network))
        report = diagnose()
        with args.out.open('x', encoding='utf-8', newline='\n') as handle:
            json.dump(report, handle, indent=2)
            handle.write('\n')
        print(json.dumps({'status': report['status'], 'cases': len(report['cases']), 'provider': 'NOT_RUN'}))
