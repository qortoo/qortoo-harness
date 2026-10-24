"""Clone missing catalog repositories without updating or replacing existing paths."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess

from harness_git import ProbeError, git, git_environment
from harness_manifest import Manifest, ManifestError, Repository, remotes_equivalent


class BootstrapError(ValueError):
    """Bootstrap cannot proceed without risking existing data or violating the catalog."""


@dataclass(frozen=True)
class BootstrapAction:
    repository: Repository
    state: str


def _path_guard(repo: Repository) -> None:
    configured = repo.configured_path or repo.path
    if configured.is_symlink() or repo.path.is_symlink():
        raise BootstrapError(f'{repo.name}: symlink destination is not a bootstrap target')
    if configured.resolve() != repo.path or repo.path.resolve() != repo.path:
        raise BootstrapError(f'{repo.name}: destination path changed after manifest validation')


def _existing(repo: Repository) -> None:
    if not repo.path.is_dir():
        raise BootstrapError(f'{repo.name}: existing destination is not a directory')
    top = git(repo.path, 'rev-parse', '--show-toplevel')
    if top.returncode or Path(top.stdout.strip()).resolve() != repo.path:
        raise BootstrapError(f'{repo.name}: existing directory is not the expected Git working-tree root')
    if repo.remote is None:
        return
    result = git(repo.path, 'remote', 'get-url', '--all', 'origin')
    urls = result.stdout.splitlines()
    try:
        match = result.returncode == 0 and len(urls) == 1 and remotes_equivalent(repo.remote, urls[0])
    except ManifestError:
        match = False
    if not match:
        raise BootstrapError(f'{repo.name}: origin missing, ambiguous, unsupported, or mismatched; directory preserved')


def plan_bootstrap(manifest: Manifest, repo: str | None = None, *, public_only: bool = False) -> list[BootstrapAction]:
    """Preflight all selected entries, including blocked paths, without any mutations."""
    if repo and repo not in manifest.repositories:
        raise BootstrapError(f'Not a product repository: {repo}')
    actions = []
    errors = []
    for name, entry in sorted(manifest.repositories.items()):
        if repo and name != repo:
            continue
        if public_only and entry.tier != 'public':
            actions.append(BootstrapAction(entry, 'excluded'))
            continue
        try:
            _path_guard(entry)
            if entry.path.exists():
                _existing(entry)
                actions.append(BootstrapAction(entry, 'existing'))
                continue
            if entry.remote is None:
                raise BootstrapError(f'{name}: missing repository has no clone remote; use --public-only to exclude internal entries')
            branch = git(manifest.harness_root, 'check-ref-format', '--branch', entry.default_branch)
            if branch.returncode:
                raise BootstrapError(f'{name}: default_branch is not a valid Git branch name')
            ancestor = next((path for path in entry.path.parents if path.exists()), None)
            if ancestor is None or not ancestor.is_dir():
                raise BootstrapError(f'{name}: destination parent is not a directory')
            enclosing = git(ancestor, 'rev-parse', '--show-toplevel')
            if enclosing.returncode == 0:
                raise BootstrapError(f'{name}: missing destination would nest inside another Git checkout')
            actions.append(BootstrapAction(entry, 'clone'))
        except (OSError, ProbeError, BootstrapError) as error:
            errors.append(str(error))
    if errors:
        raise BootstrapError('Preflight failed; no clones started:\n' + '\n'.join(errors))
    return actions


def _remove_owned_empty(path: Path, identity: tuple[int, int]) -> bool:
    try:
        stat = path.lstat()
        if (stat.st_dev, stat.st_ino) == identity and not path.is_symlink():
            path.rmdir()
            return True
    except OSError:
        pass
    return False


def _clone(repo: Repository) -> None:
    _path_guard(repo)
    repo.path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents adopting even an empty directory created by someone else.
    repo.path.mkdir()
    stat = repo.path.lstat()
    identity = stat.st_dev, stat.st_ino
    try:
        result = subprocess.run([
            'git', '--no-optional-locks', '-c', f'core.hooksPath={os.devnull}',
            '-c', 'core.fsmonitor=false', 'clone', '--quiet', '--no-recurse-submodules',
            '--branch', repo.default_branch, '--', repo.remote, str(repo.path),
        ], env=git_environment(), capture_output=True, text=True, timeout=120)
        if result.returncode:
            # Git diagnostics can include credential-helper or URL details; report the target only.
            raise BootstrapError(f'{repo.name}: clone failed (Git exit {result.returncode})')
        _existing(repo)
        branch = git(repo.path, 'symbolic-ref', '--quiet', '--short', 'HEAD')
        if branch.returncode or branch.stdout.strip() != repo.default_branch:
            raise BootstrapError(f'{repo.name}: clone did not create the configured branch')
    except (OSError, ProbeError, BootstrapError, subprocess.TimeoutExpired) as error:
        removed = _remove_owned_empty(repo.path, identity)
        recovery = 'owned empty destination removed; safe to retry' if removed else 'destination retained; inspect it before retrying'
        reason = str(error) if isinstance(error, BootstrapError) else ('clone timed out after 120 seconds' if isinstance(error, subprocess.TimeoutExpired) else 'Git execution or filesystem operation failed')
        raise BootstrapError(f'{reason}; {recovery}') from error


def bootstrap(actions: list[BootstrapAction], *, dry_run: bool = False) -> None:
    for action in actions:
        repo = action.repository
        if action.state == 'excluded':
            print(f'[SKIPPED] {repo.name}: internal entry excluded by --public-only')
        elif action.state == 'existing':
            print(f'[PRESERVED] {repo.name}: existing checkout; no pull, reset, or branch change')
        elif dry_run:
            print(f'[WOULD CLONE] {repo.name}: {repo.path} (branch {repo.default_branch})')
        else:
            try:
                _clone(repo)
            except (OSError, ProbeError, BootstrapError) as error:
                raise BootstrapError(f'{repo.name}: {error}') from error
            print(f'[CLONED] {repo.name}: {repo.path}')
