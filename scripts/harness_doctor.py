"""Read-only diagnostics for the local catalog, tools, policies, and worktrees."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import os
from pathlib import Path
import shutil
import subprocess
import sys

from harness_manifest import Manifest, ManifestError, Repository, remotes_equivalent, repositories_with_harness
from harness_sync import plan_agents
from sync_conventions import plan_conventions


@dataclass(frozen=True)
class Finding:
    target: str
    check: str
    status: str
    message: str


class ProbeError(RuntimeError):
    pass


def run(command: list[str]) -> subprocess.CompletedProcess:
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0')
    for name in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR'):
        env.pop(name, None)
    try:
        return subprocess.run(command, env=env, capture_output=True, text=True, errors='replace', timeout=10)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ProbeError(f'{command[0]} could not complete the local probe') from error


def git(path: Path, *args: str) -> subprocess.CompletedProcess:
    return run(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-C', str(path), *args])


def worktrees(repo: Repository, manifest: Manifest) -> list[Finding]:
    result = git(repo.path, 'worktree', 'list', '--porcelain', '-z')
    if result.returncode:
        return [Finding(repo.name, 'worktrees', 'error', 'Cannot inspect registered worktrees')]
    findings = []
    roots = [entry.path for entry in repositories_with_harness(manifest).values()]
    for block in result.stdout.strip('\0').split('\0\0'):
        fields = block.split('\0')
        path = next((Path(field[9:]) for field in fields if field.startswith('worktree ')), None)
        if path is None:
            continue
        path = path.resolve()
        if path == repo.path:
            continue
        reasons = []
        if not path.exists() or any(field.startswith('prunable') for field in fields):
            reasons.append('missing/prunable registration')
        if any(path == root or root in path.parents for root in roots):
            reasons.append('inside a catalog repository')
        staging = (manifest.harness_root.parent / 'qortoo-worktrees').resolve()
        if staging not in path.parents:
            reasons.append('outside worktree staging directory')
        if any(field.startswith('locked') for field in fields):
            reasons.append('locked')
        findings.append(Finding(repo.name, 'worktree', 'warning' if reasons else 'ok',
                                f'{path}: ' + (', '.join(reasons) if reasons else 'registered external worktree')))
    if not findings:
        findings.append(Finding(repo.name, 'worktrees', 'ok', 'No additional registered worktrees'))
    return findings


def repository_findings(repo: Repository, manifest: Manifest) -> list[Finding]:
    if not repo.path.is_dir():
        return [Finding(repo.name, 'repository', 'error', f'Missing directory: {repo.path}')]
    top = git(repo.path, 'rev-parse', '--show-toplevel')
    if top.returncode or Path(top.stdout.strip()).resolve() != repo.path:
        return [Finding(repo.name, 'repository', 'error', 'Path is not the root of a Git working tree')]
    findings = [Finding(repo.name, 'repository', 'ok', str(repo.path))]
    if repo.remote is None:
        findings.append(Finding(repo.name, 'remote', 'skipped', 'No expected remote in catalog'))
    else:
        remote = git(repo.path, 'remote', 'get-url', '--all', 'origin')
        urls = remote.stdout.splitlines()
        try:
            matches = remote.returncode == 0 and len(urls) == 1 and remotes_equivalent(repo.remote, urls[0])
        except ManifestError:
            matches = False
        findings.append(Finding(repo.name, 'remote', 'ok' if matches else 'error',
                                'origin matches catalog' if matches else 'origin missing, ambiguous, unsupported, or mismatched'))
    status = git(repo.path, 'status', '--porcelain=v1', '-z', '--untracked-files=normal')
    if status.returncode:
        findings.append(Finding(repo.name, 'working-tree', 'error', 'Cannot inspect changes'))
    else:
        findings.append(Finding(repo.name, 'working-tree', 'warning' if status.stdout else 'ok',
                                'Uncommitted or untracked changes present' if status.stdout else 'Clean'))
    branch = git(repo.path, 'symbolic-ref', '--quiet', '--short', 'HEAD')
    current = branch.stdout.strip() if branch.returncode == 0 else 'detached HEAD'
    findings.append(Finding(repo.name, 'branch', 'ok' if current == repo.default_branch else 'warning', current))
    ref = f'refs/remotes/origin/{repo.default_branch}'
    counts = git(repo.path, 'rev-list', '--left-right', '--count', f'HEAD...{ref}', '--')
    findings.append(Finding(repo.name, 'local-tracking', 'ok' if counts.returncode == 0 else 'unknown',
                            ('ahead/behind ' + '/'.join(counts.stdout.split()) + ' (local cached ref only)')
                            if counts.returncode == 0 else 'No usable cached tracking ref; remote delivery unknown'))
    findings.extend(worktrees(repo, manifest))
    return findings


def diagnose(manifest: Manifest, repo: str | None = None) -> dict:
    repositories = repositories_with_harness(manifest)
    if repo and repo not in repositories:
        raise ValueError(f'Unknown repository: {repo}')
    selected = [entry for name, entry in sorted(repositories.items()) if repo is None or name == repo]
    findings = [Finding('harness', 'runtime', 'ok', f'Python {sys.version.split()[0]}'),
                Finding('harness', 'remote-delivery', 'unknown', 'Offline: no fetch, PR, CI, merge, or publication status checked')]
    for entry in selected:
        try:
            findings.extend(repository_findings(entry, manifest))
        except ProbeError as error:
            findings.append(Finding(entry.name, 'repository', 'error', str(error)))
        if entry.agents_md == 'managed':
            try:
                plans = plan_conventions(manifest, entry.name)
                stale = any(item.stale for item in plans)
                findings.append(Finding(entry.name, 'policy', 'error' if stale else 'ok', 'Managed block drift' if stale else 'Managed block matches source'))
            except (OSError, ValueError) as error:
                findings.append(Finding(entry.name, 'policy', 'error', str(error)))
        else:
            findings.append(Finding(entry.name, 'policy', 'skipped', 'AGENTS.md is unmanaged'))
    for tool in sorted({'git'} | {tool for entry in selected for tool in entry.tools}):
        executable = shutil.which(tool)
        if not executable:
            findings.append(Finding(tool, 'tool', 'error', 'Executable not found on PATH'))
            continue
        try:
            result = run([executable, 'version' if tool == 'go' else '--version'])
            lines = (result.stdout or result.stderr).splitlines()
            findings.append(Finding(tool, 'tool', 'ok' if result.returncode == 0 else 'error',
                                    lines[0][:240] if lines else 'Version probe returned no output'))
        except ProbeError as error:
            findings.append(Finding(tool, 'tool', 'error', str(error)))
    try:
        adapters = plan_agents(manifest.harness_root)
        for item in adapters:
            findings.append(Finding('harness', 'agent', 'error' if item.stale else 'ok',
                                    f'{item.name}: ' + ('drift' if item.stale else 'matches source')))
    except (OSError, ValueError) as error:
        findings.append(Finding('harness', 'agents', 'error', str(error)))
    local = manifest.harness_root / '.local'
    clutter = sorted({path.name for pattern in ('*.log', 'dependency-bump-*.json') for path in local.glob(pattern)})
    if (local / 'validation').exists():
        clutter.append('validation/ (use validations/)')
    if (local / 'worktrees').is_dir():
        clutter.extend(str(path.relative_to(local)) for path in (local / 'worktrees').iterdir() if path.is_dir())
    findings.append(Finding('harness', 'artifacts', 'warning' if clutter else 'ok',
                            'Misplaced artifacts: ' + ', '.join(clutter) if clutter else 'No root logs, legacy validation directory, or internal worktree directories'))
    return {'scope': [entry.name for entry in selected], 'agent_scope': 'all harness shared agents',
            'offline': True, 'findings': [asdict(item) for item in findings]}
