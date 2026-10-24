"""Bounded subprocess probes with read-only Git environment defaults."""

import os
from pathlib import Path
import subprocess


def git_environment() -> dict[str, str]:
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0')
    for name in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR'):
        env.pop(name, None)
    return env


class ProbeError(RuntimeError):
    pass


def run(command: list[str]) -> subprocess.CompletedProcess:
    env = git_environment()
    try:
        return subprocess.run(command, env=env, capture_output=True, text=True, errors='replace', timeout=10)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ProbeError(f'{command[0]} could not complete the local probe') from error


def git(path: Path, *args: str) -> subprocess.CompletedProcess:
    return run(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-C', str(path), *args])


