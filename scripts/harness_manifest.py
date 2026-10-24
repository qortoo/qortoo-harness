"""Validated repository catalog shared by harness commands (Python 3.11+)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


class ManifestError(ValueError):
    """Configuration is invalid or cannot be loaded safely."""


@dataclass(frozen=True)
class Repository:
    name: str
    path: Path
    remote: str | None
    role: str
    tier: str
    default_branch: str
    tools: tuple[str, ...]
    agents_md: str
    configured_path: Path | None = None


@dataclass(frozen=True)
class Manifest:
    harness_root: Path
    workspace_root: Path
    repositories: dict[str, Repository]


def canonical_remote(remote: str) -> tuple[str, str, str]:
    """Compare repository identity across HTTPS and Git SSH transport spellings."""
    if not isinstance(remote, str) or not remote or any(c.isspace() for c in remote):
        raise ManifestError('remote must be a nonempty URL without whitespace')
    scp = re.fullmatch(r'git@([^/:]+):(.+)', remote)
    if scp:
        host, path = scp.groups()
        port = ''
    else:
        try:
            url = urlsplit(remote)
            if url.scheme == 'file' and url.netloc in ('', 'localhost'):
                if url.query or url.fragment or not url.path.startswith('/'):
                    raise ValueError('invalid file remote')
                return ('file', '', str(Path(unquote(url.path)).resolve()))
            if url.scheme not in ('https', 'ssh') or not url.hostname:
                raise ValueError('unsupported remote scheme')
            if url.query or url.fragment or url.password is not None:
                raise ValueError('remote credentials/query/fragment are unsupported')
            if url.username is not None and not (url.scheme == 'ssh' and url.username == 'git'):
                raise ValueError('unsupported remote user')
            host, path = url.hostname, url.path.lstrip('/')
            default_port = 443 if url.scheme == 'https' else 22
            port = '' if url.port in (None, default_port) else f'{url.scheme}:{url.port}'
        except ValueError as error:
            # Do not reproduce credential-bearing URLs in diagnostics.
            raise ManifestError('remote must be an HTTPS, Git SSH, or absolute file URL') from error
    path = path.rstrip('/')
    if path.endswith('.git'):
        path = path[:-4]
    if not host or not path or any(part in ('', '.', '..') for part in path.split('/')):
        raise ManifestError('remote must identify a repository path')
    return (host.lower(), port, path)


def remotes_equivalent(left: str, right: str) -> bool:
    """Return whether two supported remotes identify the same host/path/port."""
    return canonical_remote(left) == canonical_remote(right)


def _read_toml(path: Path) -> dict:
    if sys.version_info < (3, 11):
        raise ManifestError('Manifest tools require Python 3.11 or newer; run with python3.12 or another supported interpreter')
    import tomllib

    try:
        with path.open('rb') as stream:
            return tomllib.load(stream)
    except (OSError, ValueError) as error:
        raise ManifestError(f'Cannot read {path.name}: {error}') from error


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or any(ord(c) < 32 for c in value):
        raise ManifestError(f'{label} must be a nonempty string without surrounding whitespace or control characters')
    return value


def _shape(config: dict, label: str) -> None:
    if set(config) - {'workspace', 'repositories'}:
        raise ManifestError(f'{label}: unknown top-level fields')
    workspace = config.get('workspace', {})
    repos = config.get('repositories', {})
    if not isinstance(workspace, dict) or set(workspace) - {'root'}:
        raise ManifestError(f'{label}: workspace must be a table containing only root')
    if 'root' in workspace:
        _text(workspace['root'], f'{label}: workspace.root')
    if not isinstance(repos, dict):
        raise ManifestError(f'{label}: repositories must be a table')
    fields = {'path', 'remote', 'role', 'tier', 'default_branch', 'tools', 'agents_md'}
    for name, properties in repos.items():
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', name) or name == 'qortoo-harness':
            raise ManifestError(f'{label}: invalid or reserved repository name: {name}')
        if not isinstance(properties, dict) or set(properties) - fields:
            raise ManifestError(f'{label}: repositories.{name} has invalid or unknown fields')
        for key, value in properties.items():
            field = f'{label}: repositories.{name}.{key}'
            if key == 'tools':
                if not isinstance(value, list) or any(not isinstance(tool, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.+-]*', tool) for tool in value):
                    raise ManifestError(f'{field} must be a list of executable names')
                if len(set(value)) != len(value):
                    raise ManifestError(f'{field} contains duplicates')
            else:
                _text(value, field)


def load_manifest(harness_root: Path, *, include_local: bool = True) -> Manifest:
    """Merge field overrides, validate contracts, and resolve paths without mutations."""
    root = harness_root.resolve()
    config = _read_toml(root / 'manifest.toml')
    _shape(config, 'manifest.toml')
    local = root / 'manifest.local.toml'
    if include_local and local.exists():
        overlay = _read_toml(local)
        _shape(overlay, 'manifest.local.toml')
        config.setdefault('workspace', {}).update(overlay.get('workspace', {}))
        repos = config.setdefault('repositories', {})
        for name, values in overlay.get('repositories', {}).items():
            repos.setdefault(name, {}).update(values)

    workspace = (root / config.get('workspace', {}).get('root', '..')).resolve()
    if workspace.exists() and not workspace.is_dir():
        raise ManifestError('workspace.root is not a directory')
    repositories = {}
    paths = {'qortoo-harness': root}
    for name, values in config.get('repositories', {}).items():
        for required in ('path', 'role', 'tier'):
            if required not in values:
                raise ManifestError(f'repositories.{name}: missing required field {required}')
        tier = values['tier']
        if tier not in ('public', 'internal'):
            raise ManifestError(f'repositories.{name}.tier must be public or internal')
        agents_md = values.get('agents_md', 'unmanaged')
        if agents_md not in ('managed', 'unmanaged'):
            raise ManifestError(f'repositories.{name}.agents_md must be managed or unmanaged')
        remote = values.get('remote')
        if remote is None and tier == 'public':
            raise ManifestError(f'repositories.{name}: public repositories require remote')
        if remote is not None:
            try:
                canonical_remote(remote)
            except ManifestError as error:
                raise ManifestError(f'repositories.{name}: {error}') from error
        branch = values.get('default_branch', 'main')
        if branch.startswith('-') or any(c.isspace() for c in branch):
            raise ManifestError(f'repositories.{name}.default_branch must be a branch name')
        configured_path = workspace / values['path']
        path = configured_path.resolve()
        if path.exists() and not path.is_dir():
            raise ManifestError(f'repositories.{name}.path is not a directory')
        for other_name, other in paths.items():
            if path == other or path in other.parents or other in path.parents:
                raise ManifestError(f'repositories.{name}.path overlaps {other_name}')
        paths[name] = path
        repositories[name] = Repository(
            name, path, remote, values['role'], tier, branch,
            tuple(values.get('tools', [])), agents_md, configured_path,
        )
    return Manifest(root, workspace, repositories)


def repositories_with_harness(manifest: Manifest) -> dict[str, Repository]:
    """Include the command's own checkout without accepting a manifest override."""
    repositories = dict(manifest.repositories)
    repositories['qortoo-harness'] = Repository(
        'qortoo-harness', manifest.harness_root, None, 'control-plane',
        'public', 'main', (), 'managed',
    )
    return repositories
