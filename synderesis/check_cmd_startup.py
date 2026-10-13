"""Native CMD + ConPTY interactive startup against a synthetic loopback API."""
import os
import gc
from contextlib import ExitStack
import json
from pathlib import Path
import queue
import subprocess
import tempfile
import threading
import time
from winpty import PtyProcess
from terminal_fixture_server import terminal_fixture_server


def main():
    binary = Path(os.environ['SYNDERESIS_CODE_TEST_BINARY']).resolve()
    with terminal_fixture_server() as server_port, ExitStack() as stack:
        diagnostic_root = os.environ.get('SYNDERESIS_TEST_DIAGNOSTIC_DIR')
        if diagnostic_root:
            Path(diagnostic_root).mkdir(parents=True, exist_ok=True)
            directory = tempfile.mkdtemp(prefix='CMD-', dir=diagnostic_root)
        else:
            directory = stack.enter_context(tempfile.TemporaryDirectory(prefix='Synderesis CMD console '))
        env = dict(os.environ, PATH=str(binary.parent) + os.pathsep + os.environ['PATH'],
                   SYNDERESIS_API_KEY='sk_live_synthetic_fixture_only',
                   SYNDERESIS_CODE_HOME=str(Path(directory, 'state')),
                   SYNDERESIS_CODE_TEST_BASE_URL=f'http://127.0.0.1:{server_port}/v1/code')
        arguments = json.loads(os.environ.get('SYNDERESIS_TEST_CLI_ARGS', '[]'))
        if diagnostic_root:
            arguments += ['--debug-file', str(Path(directory, 'startup.log'))]
        command = 'cmd.exe /d /c ' + subprocess.list2cmdline([str(binary), *arguments])
        process = PtyProcess.spawn(command, cwd=directory,
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
            if diagnostic_root:
                Path(directory, 'terminal.txt').write_text(text, encoding='utf-8')
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


if __name__ == '__main__':
    main()
