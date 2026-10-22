# SPDX-License-Identifier: MIT
# Copyright (c) 2026 JohnnyZPiggy
"""Transport fixture only: no algorithm, hardware claim, install or network."""
import hashlib
import json
import os
from pathlib import Path
import re


def main():
    sha = os.environ['SAE_CANDIDATE_SHA']
    if not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise ValueError('Expected exact candidate SHA')
    directory = Path(os.environ.get('SAE_ARTIFACT_DIR', '/content'))
    directory.mkdir(parents=True, exist_ok=True)
    name = 'transport-check.json'
    raw = (json.dumps({'source_sha': sha, 'status': 'PASS',
                      'classification': 'TRANSPORT_FIXTURE_NO_SCIENTIFIC_TEST',
                      'live_gpu': 'NOT_RUN', 'tpu': 'NOT_RUN', 'compilation': 'NOT_RUN'})+'\n').encode()
    (directory / name).write_bytes(raw)
    print('ARTIFACT', name, len(raw), hashlib.sha256(raw).hexdigest(), flush=True)


if __name__ == '__main__':
    main()
