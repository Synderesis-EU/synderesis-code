"""Reuse timestamps only for tracked files identical to a restored build commit."""
import os
from pathlib import Path
import re
import subprocess
import sys


def git(*args):
    return subprocess.check_output(['git', *args])


def main():
    match = re.fullmatch(r'windows-rust-1\.94-[0-9a-f]+-([0-9a-f]{40})', sys.argv[1])
    if not match:
        print('No compatible cached source commit; keep checkout timestamps')
        return
    cached = match.group(1)
    exists = subprocess.run(['git', 'cat-file', '-e', cached + '^{commit}'], capture_output=True)
    if exists.returncode:
        subprocess.run(['git', 'fetch', '--no-tags', 'origin', cached], check=True)
    changed = set(git('diff', '--name-only', '-z', cached, 'HEAD').split(b'\0'))
    timestamp = int(git('show', '-s', '--format=%ct', cached))
    reused = 0
    for raw in git('ls-files', '-z').split(b'\0'):
        if not raw or raw in changed:
            continue
        path = Path(os.fsdecode(raw))
        if path.is_file() and not path.is_symlink():
            os.utime(path, (timestamp, timestamp))
            reused += 1
    print(f'Reused timestamps for {reused} unchanged tracked files; changed files keep checkout timestamps')


if __name__ == '__main__':
    main()
