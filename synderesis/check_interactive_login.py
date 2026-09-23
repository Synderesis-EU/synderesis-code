"""Exercise the literal /login command in a native terminal using synthetic auth."""
import os
from pathlib import Path
import queue
import re
import tempfile
import threading
import time
from http.server import ThreadingHTTPServer
from check_tool_roundtrip import Handler


def main():
    binary = str(Path(os.environ['SYNDERESIS_CODE_TEST_BINARY']).resolve())
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with tempfile.TemporaryDirectory(prefix='synderesis-slash-login-') as directory:
        env = dict(os.environ, SYNDERESIS_API_KEY='sk_live_synthetic_ui', SYNDERESIS_CODE_HOME=str(Path(directory, 'state')),
                   SYNDERESIS_CODE_TEST_BASE_URL=f'http://127.0.0.1:{server.server_port}/v1/code',
                   SYNDERESIS_CODE_TEST_AUTH_ORIGIN=f'http://127.0.0.1:{server.server_port}', TERM='xterm-256color')
        if os.name == 'nt':
            from winpty import PtyProcess
            process = PtyProcess.spawn('cmd.exe /d /s /c "' + '"' + binary + '"' + '"', cwd=directory, env=env, dimensions=(40, 160))
            read = lambda: process.read(65536)
            write = process.write
            alive = process.isalive
            close = lambda: process.close(force=True)
        else:
            import fcntl
            import pty
            import struct
            import subprocess
            import termios
            master, slave = pty.openpty()
            fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 40, 160, 0, 0))
            process = subprocess.Popen([binary], cwd=directory, env=env, stdin=slave, stdout=slave, stderr=slave, start_new_session=True)
            os.close(slave)
            read = lambda: os.read(master, 65536).decode('utf-8', 'replace')
            write = lambda text: os.write(master, text.encode())
            alive = lambda: process.poll() is None
            def close():
                if alive():
                    process.terminate()
                    process.wait(timeout=10)
                os.close(master)
        output = queue.Queue()
        def reader():
            try:
                while alive():
                    output.put(read())
            except (OSError, EOFError):
                pass
        threading.Thread(target=reader, daemon=True).start()
        text = ''
        def until(marker):
            nonlocal text
            deadline = time.monotonic() + 45
            def visible():
                return ' '.join(re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', ' ', text).split())
            while marker not in visible() and time.monotonic() < deadline:
                try:
                    text += output.get(timeout=0.5)
                except queue.Empty:
                    pass
            assert marker in visible(), visible()[-2000:]
        try:
            until('Resume session')
            text = ''
            write('/login')
            time.sleep(0.3)
            write('\r')
            until('Waiting for login to complete')
            # The ACP roundtrip check verifies this same flow's exact URL and PKCE exchange.
            assert 'accounts.x.ai' not in text and 'grok.com' not in text, 'Upstream login still shown'
            write('\x1b')
            time.sleep(0.2)
            write('\x1b')
            time.sleep(0.2)
            write('\x11')
            time.sleep(0.2)
            write('\x11')
            deadline = time.monotonic() + 10
            while alive() and time.monotonic() < deadline:
                time.sleep(0.1)
            assert not alive(), 'Could not quit after cancelling /login'
            print('PASS: native terminal /login opens Synderesis account connection, cancellation and Quit')
        finally:
            close()
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    main()
