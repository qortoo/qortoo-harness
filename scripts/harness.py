#!/usr/bin/env python3
"""Local qortoo control plane. Requires Python 3.11 or newer."""

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

from harness_manifest import ManifestError, load_manifest, repositories_with_harness

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest='command', required=True)
    doctor = subcommands.add_parser('doctor', help='Inspect local state without modifying checkouts')
    doctor.add_argument('--repo', help='Inspect one catalog repository or qortoo-harness')
    doctor.add_argument('--json', action='store_true', help='Emit structured diagnostic findings')
    sync = subcommands.add_parser('sync', help='Synchronize policy blocks and all shared agent adapters')
    sync.add_argument('--repo', help='Select one policy repository; shared agents are still included')
    sync.add_argument('--check', action='store_true', help='Fail on drift without writing')
    sync.add_argument('--diff', action='store_true', help='Preview changes without writing')
    sync.add_argument('--initialize', action='store_true', help='Enroll missing or unmarked policy files')
    args = parser.parse_args()
    try:
        manifest = load_manifest(ROOT)
    except ManifestError as error:
        parser.exit(2, f'Cannot load manifest: {error}\n')
    if args.repo and args.repo not in repositories_with_harness(manifest):
        parser.error(f'Unknown repository: {args.repo}')
    # Imports after version/configuration validation keep old-runtime failures clear.
    if args.command == 'doctor':
        from harness_doctor import diagnose
        try:
            report = diagnose(manifest, args.repo)
        except (OSError, ValueError) as error:
            parser.exit(2, f'Cannot diagnose: {error}\n')
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print('Scope: ' + ', '.join(report['scope']) + '; all harness shared agents')
            for item in report['findings']:
                print(f"[{item['status'].upper()}] {item['target']} / {item['check']}: {item['message']}")
        return int(any(item['status'] == 'error' for item in report['findings']))
    from harness_sync import plan_sync
    from sync_conventions import finish_deployments
    try:
        deployments = plan_sync(manifest, args.repo, args.initialize)
        return finish_deployments(deployments, check=args.check, diff=args.diff)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Cannot synchronize: {error}\n')


if __name__ == '__main__':
    sys.exit(main())
