"""Exercise a test-feature CLI through HTTP and a real local file tool.
Uses only a loopback fixture and synthetic credentials; never ship the test binary.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MARKER = 'SYNDERESIS_READ_' + uuid.uuid4().hex
seen_tool_result = False
requests = []



class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, data, content_type='application/json'):
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self.send(json.dumps({'object': 'list', 'data': [{'id': 'synderesis-code', 'object': 'model', 'created': 1, 'owned_by': 'synderesis'}]}).encode())

    def do_POST(self):
        global seen_tool_result
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        assert self.path == '/v1/code/chat/completions', self.path
        names = [tool.get('function', {}).get('name') for tool in body.get('tools', [])]
        results = [item for item in body.get('messages', []) if item.get('role') == 'tool' and item.get('tool_call_id') == 'call_fixture']
        requests.append({'path': self.path, 'tools': names, 'tool_results': len(results)})
        if results and MARKER in json.dumps(results):
            seen_tool_result = True
        if 'read_file' in names and not results:
            message = {'role': 'assistant', 'tool_calls': [{'id': 'call_fixture', 'type': 'function', 'function': {'name': 'read_file', 'arguments': json.dumps({'target_file': 'release-check.txt'})}}]}
            finish = 'tool_calls'
        else:
            message = {'role': 'assistant', 'content': MARKER if results and seen_tool_result else 'Fixture session'}
            finish = 'stop'
        base = {'id': 'chatcmpl_' + uuid.uuid4().hex, 'created': 1, 'model': 'synderesis-code'}
        usage = {'prompt_tokens': 100, 'completion_tokens': 20, 'total_tokens': 120}
        if body.get('stream'):
            delta = dict(message)
            if 'tool_calls' in delta:
                delta['tool_calls'] = [dict(call, index=i) for i, call in enumerate(delta['tool_calls'])]
            chunks = [
                {**base, 'object': 'chat.completion.chunk', 'choices': [{'index': 0, 'delta': delta, 'finish_reason': None}]},
                {**base, 'object': 'chat.completion.chunk', 'choices': [{'index': 0, 'delta': {}, 'finish_reason': finish}], 'usage': usage},
            ]
            wire = ''.join('data: ' + json.dumps(chunk) + '\n\n' for chunk in chunks) + 'data: [DONE]\n\n'
            self.send(wire.encode(), 'text/event-stream')
        else:
            self.send(json.dumps({**base, 'object': 'chat.completion', 'choices': [{'index': 0, 'message': message, 'finish_reason': finish}], 'usage': usage}).encode())



def main():
    binary = str(Path(os.environ['SYNDERESIS_CODE_TEST_BINARY']).resolve())
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix='synderesis-protocol-') as directory:
            Path(directory, 'release-check.txt').write_text(MARKER + '\n', encoding='utf-8')
            env = dict(os.environ, SYNDERESIS_API_KEY='sk_live_synthetic_fixture_only', SYNDERESIS_CODE_HOME=str(Path(directory, 'state')), SYNDERESIS_CODE_TEST_BASE_URL=f'http://127.0.0.1:{server.server_port}/v1/code')
            result = subprocess.run([binary, '-p', 'Read release-check.txt with read_file and reply with its content.', '--output-format', 'plain', '--disable-web-search', '--tools', 'read_file', '--allow', 'Read', '--max-turns', '3'], cwd=directory, env=env, capture_output=True, text=True, timeout=120, encoding='utf-8', errors='replace')
            print(json.dumps({'returncode': result.returncode, 'received_file_content': seen_tool_result, 'requests': requests, 'stdout': result.stdout[-2000:], 'stderr': result.stderr[-3000:]}))
            assert result.returncode == 0 and seen_tool_result and MARKER in result.stdout, 'HTTP/file-tool roundtrip failed'
            assert 'mcp.stripe.com' not in result.stderr and 'mcp.vercel.com' not in result.stderr
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)


if __name__ == '__main__':
    main()
