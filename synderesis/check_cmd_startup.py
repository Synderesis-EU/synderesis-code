"""Native CMD + ConPTY interactive startup against a synthetic loopback API."""
import os
import gc
from pathlib import Path
import queue
import tempfile
import threading
import time
from http.server import ThreadingHTTPServer

from winpty import PtyProcess
from check_tool_roundtrip import Handler


def main():
    binary = Path(os.environ['SYNDERESIS_CODE_TEST_BINARY']).resolve()
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        with tempfile.TemporaryDirectory(prefix='Synderesis CMD console ') as directory:
            env = dict(os.environ, PATH=str(binary.parent) + os.pathsep + os.environ['PATH'],
                       SYNDERESIS_API_KEY='sk_live_synthetic_fixture_only',
                       SYNDERESIS_CODE_HOME=str(Path(directory, 'state')),
                       SYNDERESIS_CODE_TEST_BASE_URL=f'http://127.0.0.1:{server.server_port}/v1/code')
            process = PtyProcess.spawn('cmd.exe /d /c synderesis-code', cwd=directory,
                                       env=env, dimensions=(30, 100))
            output = queue.Queue()

            def read():
                try:
                    while process.isalive():
                        output.put(process.read(4096))
                except (EOFError, OSError):
                    pass

            reader = threading.Thread(target=read, daemon=True)
            reader.start()
            text = ''
            deadline = time.monotonic() + 45
            try:
                while time.monotonic() < deadline:
                    try:
                        text += output.get(timeout=1)
                    except queue.Empty:
                        if not process.isalive():
                            break
                    if 'Resume session' in text and 'Quit' in text:
                        break
                assert 'Resume session' in text and 'Quit' in text, repr(text[-3000:])
                assert 'Synderesis Code' in text, 'Branded terminal title missing'
                # The existing Quit shortcut requires a second press to confirm.
                process.write('\x11')
                time.sleep(0.2)
                process.write('\x11')
                deadline = time.monotonic() + 10
                while process.isalive() and time.monotonic() < deadline:
                    time.sleep(0.1)
                assert not process.isalive(), 'Interactive Quit did not exit CMD child'
            finally:
                # PyWinpty 3.0.3 isalive() marks the wrapper closed when the
                # child exits, although its forwarding sockets still need close().
                process.closed = False
                process.close(force=True)
                reader.join(2)
                # Drop ConPTY's host handle before deleting its working directory.
                # The CLI can already have exited while that handle remains open.
                del process
                gc.collect()
                time.sleep(0.5)
        print('PASS: native CMD interactive menu, Synderesis Code title and keyboard Quit')
    finally:
        server.shutdown()
        server.server_close()
        worker.join(2)


if __name__ == '__main__':
    main()
