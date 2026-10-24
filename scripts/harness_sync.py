"""Plan shared policy and agent deployments together before applying changes."""

from pathlib import Path

import sync_agents
from harness_manifest import Manifest
from sync_conventions import Deployment, plan_conventions


def plan_agents(root: Path) -> list[Deployment]:
    sources = sorted((root / 'agents').glob('*.md'))
    if not sources:
        raise ValueError('No shared agent definitions found under agents/')
    deployments = []
    for source in sources:
        for path, target in sync_agents.render_agent(source.stem).items():
            current = path.read_bytes().decode('utf-8') if path.exists() else None
            deployments.append(Deployment(str(path.relative_to(root)), path, current, target))
    seen = set()
    for item in deployments:
        path = item.path.resolve()
        if path in seen:
            raise ValueError(f'{item.name}: multiple agents share an adapter output')
        seen.add(path)
    return deployments


def plan_sync(manifest: Manifest, repo: str | None = None, initialize: bool = False) -> list[Deployment]:
    deployments = plan_conventions(manifest, repo, initialize) + plan_agents(manifest.harness_root)
    paths = set()
    sources = {path.resolve() for path in (manifest.harness_root / 'agents').glob('*.md')}
    sources.add((manifest.harness_root / 'policies/shared-conventions.md').resolve())
    for item in deployments:
        resolved = item.path.resolve()
        if resolved in paths or resolved in sources:
            raise ValueError(f'{item.name}: generated output overlaps another output or canonical source')
        paths.add(resolved)
    return deployments
