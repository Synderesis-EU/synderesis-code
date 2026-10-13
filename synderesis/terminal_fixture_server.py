"""Keep the loopback server independent of the terminal driver's Python lock."""
from contextlib import contextmanager
from http.server import ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys

from check_tool_roundtrip import Handler


@contextmanager
def terminal_fixture_server():
    worker = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve())],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        port = worker.stdout.readline().strip()
        if not port.isdigit():
            raise RuntimeError('Loopback terminal fixture did not start')
        yield int(port)
    finally:
        worker.terminate()
        worker.communicate(timeout=10)


if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    print(server.server_port, flush=True)
    server.serve_forever()
