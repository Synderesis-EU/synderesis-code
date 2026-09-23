"""Verify production executable TLS/model routing with a deliberately invalid key.
An HTTP 401 is the expected result; this never generates a billable model response.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile

binary = str(Path(os.environ['SYNDERESIS_CODE_PRODUCTION_BINARY']).resolve())
with tempfile.TemporaryDirectory(prefix='synderesis-production-transport-') as directory:
    env = dict(os.environ, SYNDERESIS_API_KEY='sk_live_synthetic_transport_check', SYNDERESIS_CODE_HOME=str(Path(directory, 'state')))
    result = subprocess.run([binary, '-p', 'Reply OK', '--output-format', 'plain', '--disable-web-search', '--max-turns', '1'],
                            cwd=directory, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=90)
    output = result.stdout + result.stderr
    assert result.returncode != 0, 'Invalid credential unexpectedly accepted'
    assert '401' in output and ('Sign in to continue' in output or 'unauthorized' in output.lower()), output[-3000:]
    assert not any(marker in output.lower() for marker in ['invalid peer certificate', 'unknownissuer', 'certificate verify failed', 'dns error']), output[-3000:]
    print(json.dumps({'production_https_model_route_reached': True, 'expected_unauthorized': True, 'exit': result.returncode, 'billable_generation': False}))
