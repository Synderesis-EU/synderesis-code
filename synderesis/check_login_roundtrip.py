"""Exercise the TUI's ACP authentication path with loopback PKCE and synthetic keys.
Only the isolated synderesis-test-endpoint binary accepts this fixture origin.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from check_tool_roundtrip import Handler, MARKER

INITIAL = 'sk_live_synthetic_initial'
CONNECTED = 'sk_live_synthetic_connected'
SWITCHED = 'sk_live_synthetic_switched'
observed = []
expected_exchange = {}
next_key = CONNECTED


class AuthHandler(Handler):
    def do_POST(self):
        if self.path == '/v1/auth/device/exchange':
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            challenge = base64.urlsafe_b64encode(hashlib.sha256(body['code_verifier'].encode()).digest()).decode().rstrip('=')
            assert body['state'] == expected_exchange['state']
            assert body['redirect_uri'] == expected_exchange['redirect_uri']
            assert challenge == expected_exchange['code_challenge']
            assert body['code'] == 'synthetic-approved-code'
            self.send(json.dumps({'api_key': next_key}).encode())
        else:
            observed.append(self.headers.get('Authorization'))
            if not self.headers.get('Authorization'):
                self.send_error(401, 'Synthetic signed-out account')
                return
            super().do_POST()


class Client:
    def __init__(self, binary, cwd, env):
        self.process = subprocess.Popen([binary, 'agent', '--no-leader', 'stdio'], cwd=cwd, env=env,
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        text=True, encoding='utf-8', errors='replace')
        self.inbox = queue.Queue()
        self.pending = {}
        self.count = 0
        self.errors = []
        def read():
            for line in self.process.stdout:
                try:
                    item = json.loads(line)
                except ValueError:
                    continue
                if 'id' in item and 'method' not in item:
                    self.inbox.put(item)
                elif 'id' in item:
                    self.process.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': item['id'], 'error': {'code': -32601, 'message': 'Fixture capability unavailable'}}) + '\n')
                    self.process.stdin.flush()
        threading.Thread(target=read, daemon=True).start()
        def errors():
            for line in self.process.stderr:
                self.errors.append(line)
        threading.Thread(target=errors, daemon=True).start()

    def send(self, method, params):
        self.count += 1
        self.process.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': self.count, 'method': method, 'params': params}) + '\n')
        self.process.stdin.flush()
        return self.count

    def receive(self, ident, allow_error=False):
        deadline = time.monotonic() + 60
        while ident not in self.pending:
            item = self.inbox.get(timeout=max(0.1, deadline - time.monotonic()))
            self.pending[item['id']] = item
        item = self.pending.pop(ident)
        if not allow_error:
            assert 'error' not in item, item
        return item if allow_error else item['result']

    def call(self, method, params=None):
        return self.receive(self.send(method, params or {}))

    def begin_login(self, seq):
        ident = self.send('authenticate', {'methodId': 'grok.com', '_meta': {'force_interactive': True, 'request_seq': seq}})
        for _ in range(60):
            url = self.call('_x.ai/auth/get_url').get('auth_url')
            if url:
                parsed = urllib.parse.urlparse(url)
                assert parsed.hostname == '127.0.0.1' and parsed.path == '/account/', url
                params = dict(urllib.parse.parse_qsl(parsed.query))
                assert params['client'] == 'synderesis-code' and params['code_challenge_method'] == 'S256'
                return ident, params
            time.sleep(0.05)
        raise AssertionError('No Synderesis login URL')


def callback(params, state=None):
    url = params['redirect_uri'] + '?' + urllib.parse.urlencode({'state': state or params['state'], 'code': 'synthetic-approved-code'})
    return urllib.request.urlopen(url, timeout=5).read()


def main():
    global next_key, expected_exchange
    binary = str(Path(os.environ['SYNDERESIS_CODE_TEST_BINARY']).resolve())
    server = ThreadingHTTPServer(('127.0.0.1', 0), AuthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with tempfile.TemporaryDirectory(prefix='synderesis-login-') as directory:
        env = dict(os.environ, SYNDERESIS_API_KEY=INITIAL, SYNDERESIS_CODE_HOME=str(Path(directory, 'state')),
                   SYNDERESIS_CODE_TEST_BASE_URL=f'http://127.0.0.1:{server.server_port}/v1/code',
                   SYNDERESIS_CODE_TEST_AUTH_ORIGIN=f'http://127.0.0.1:{server.server_port}')
        Path(directory, 'release-check.txt').write_text(MARKER)
        client = Client(binary, directory, env)
        try:
            init = client.call('initialize', {'protocolVersion': 1, 'clientCapabilities': {}})
            assert any(m['name'] == 'Synderesis' for m in init['authMethods']), init['authMethods']
            assert not any(m['name'] == 'Grok' for m in init['authMethods'])
            client.call('authenticate', {'methodId': 'xai.api_key'})
            session = client.call('session/new', {'cwd': directory, 'mcpServers': [], '_meta': {'yoloMode': True}})['sessionId']
            def prompt(key):
                observed.clear()
                client.call('session/prompt', {'sessionId': session, 'prompt': [{'type': 'text', 'text': 'Say hello without using tools.'}]})
                assert observed and set(observed) == {'Bearer ' + key}, 'Existing session sent a stale credential'
            prompt(INITIAL)
            ident, params = client.begin_login(1)
            client.call('_x.ai/auth/cancel', {'request_seq': 1})
            assert 'error' in client.receive(ident, allow_error=True)
            prompt(INITIAL)
            ident, params = client.begin_login(2)
            expected_exchange = params
            try:
                callback(params, 'wrong-state')
                raise AssertionError('Wrong-state callback accepted')
            except urllib.error.HTTPError as error:
                assert error.code == 400
            assert b'connected' in callback(params)
            client.receive(ident)
            prompt(CONNECTED)
            result = client.call('_x.ai/auth/logout')
            assert result['api_key_still_set'] is False
            assert client.call('_x.ai/getApiKey')['result']['key'] is None
            assert client.call('_x.ai/auth/getBearerToken')['result']['token'] is None
            assert 'error' in client.receive(client.send('authenticate', {'methodId': 'xai.api_key'}), allow_error=True)
            observed.clear()
            client.receive(client.send('session/prompt', {'sessionId': session, 'prompt': [{'type': 'text', 'text': 'This must not use the signed-out credential.'}]}), allow_error=True)
            assert all(value is None for value in observed), 'Logout reused a stale credential'
            assert 'error' in client.receive(client.send('_x.ai/setApiKey', {'key': INITIAL}), allow_error=True)
            next_key = SWITCHED
            ident, params = client.begin_login(3)
            expected_exchange = params
            callback(params)
            client.receive(ident)
            prompt(SWITCHED)
            for file in Path(directory).rglob('*'):
                if file.is_file():
                    data = file.read_bytes()
                    assert not any(key.encode() in data for key in (INITIAL, CONNECTED, SWITCHED)), f'Credential persisted in {file.name}'
            print('PASS: interactive Synderesis PKCE login, wrong-state rejection, cancel, existing-session model call, logout, account switch, no plaintext credential files')
        finally:
            client.process.terminate()
            try:
                client.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                client.process.kill()
                client.process.wait(timeout=5)
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    main()
