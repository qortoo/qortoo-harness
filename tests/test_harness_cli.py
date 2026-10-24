"""End-to-end CLI contracts using disposable local Git repositories."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(sys.version_info < (3, 11), 'Harness CLI requires Python 3.11+')
class HarnessCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / 'harness'
        self.product = self.base / 'product'
        (self.root / 'scripts').mkdir(parents=True)
        for path in (ROOT / 'scripts').glob('*.py'):
            shutil.copyfile(path, self.root / 'scripts' / path.name)
        (self.root / 'policies').mkdir()
        shutil.copyfile(ROOT / 'policies/shared-conventions.md', self.root / 'policies/shared-conventions.md')
        (self.root / 'agents').mkdir()
        (self.root / 'agents/sample.md').write_text('# Shared role\n\nKeep task scope bounded.\n')
        (self.root / 'manifest.toml').write_text('''[workspace]
root = '..'
[repositories.product]
path = 'product'
remote = 'https://example.com/team/product.git'
role = 'sdk'
tier = 'public'
agents_md = 'managed'
''')
        self.product.mkdir()
        for path in (self.root, self.product):
            self.git(path, 'init', '-b', 'main')
        self.git(self.product, 'remote', 'add', 'origin', 'git@example.com:team/product.git')
        self.assertEqual(self.cli('sync', '--initialize').returncode, 0)
        for path in (self.root, self.product):
            self.git(path, 'add', '.')
            self.git(path, 'commit', '-m', 'fixture')

    def git(self, root, *args):
        result = subprocess.run([
            'git', '-c', 'user.name=Harness Test', '-c', 'user.email=harness@example.invalid',
            '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false', '-C', str(root), *args,
        ], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def cli(self, *args):
        return subprocess.run([sys.executable, str(self.root / 'scripts/harness.py'), *args],
                              cwd=self.base, capture_output=True, text=True,
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))

    def snapshot(self):
        return {str(path.relative_to(self.base)): (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
                for path in self.base.rglob('*') if path.is_file() and not path.is_symlink()}

    def doctor(self, *args):
        result = self.cli('doctor', '--json', *args)
        return result, json.loads(result.stdout)

    def test_healthy_doctor_and_sync_checks_are_read_only_and_offline(self):
        snapshot = self.snapshot()
        result, report = self.doctor()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(report['offline'])
        self.assertEqual(report['scope'], ['product', 'qortoo-harness'])
        remote = next(x for x in report['findings'] if x['target'] == 'product' and x['check'] == 'remote')
        self.assertEqual(remote['status'], 'ok')
        self.assertTrue(any(x['check'] == 'remote-delivery' and x['status'] == 'unknown' for x in report['findings']))
        self.assertEqual(self.cli('sync', '--check').returncode, 0)
        self.assertEqual(self.cli('sync', '--diff').returncode, 0)
        self.assertEqual(snapshot, self.snapshot())

    def test_dirty_and_feature_branch_are_warnings_without_checkout_changes(self):
        self.git(self.product, 'switch', '-c', 'feature/local')
        (self.product / 'notes.txt').write_text('Keep this untracked file.')
        snapshot = self.snapshot()
        result, report = self.doctor('--repo', 'product')
        self.assertEqual(result.returncode, 0, result.stderr)
        findings = report['findings']
        self.assertTrue(any(x['check'] == 'working-tree' and x['status'] == 'warning' for x in findings))
        self.assertTrue(any(x['check'] == 'branch' and x['message'] == 'feature/local' for x in findings))
        self.assertEqual(snapshot, self.snapshot())

    def test_missing_repository_fails_doctor_and_sync_without_partial_policy_writes(self):
        self.product.rename(self.base / 'saved-product')
        source = self.root / 'policies/shared-conventions.md'
        source.write_text(source.read_text() + '\n- New shared rule.\n')
        snapshot = self.snapshot()
        result, report = self.doctor()
        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(x['check'] == 'repository' and x['status'] == 'error' for x in report['findings']))
        self.assertEqual(self.cli('sync').returncode, 1)
        self.assertEqual(snapshot, self.snapshot())

    def test_remote_mismatch_and_missing_tool_are_actionable_errors(self):
        self.git(self.product, 'remote', 'set-url', 'origin', 'https://example.com/wrong/product.git')
        manifest = self.root / 'manifest.toml'
        manifest.write_text(manifest.read_text() + 'tools = ["nonexistent-harness-fixture-tool"]\n')
        result, report = self.doctor('--repo', 'product')
        self.assertEqual(result.returncode, 1)
        for check in ('remote', 'tool'):
            self.assertTrue(any(x['check'] == check and x['status'] == 'error' for x in report['findings']))

    def test_agent_drift_fails_selected_repository_check_and_sync_repairs_both(self):
        (self.root / '.codex/agents/sample.toml').write_text('stale adapter')
        policy = self.root / 'policies/shared-conventions.md'
        policy.write_text(policy.read_text() + '\n- Additional policy.\n')
        result, report = self.doctor('--repo', 'product')
        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(x['check'] == 'agent' and x['status'] == 'error' for x in report['findings']))
        self.assertEqual(self.cli('sync', '--check').returncode, 1)
        self.assertEqual(self.cli('sync').returncode, 0)
        self.assertEqual(self.cli('sync', '--check').returncode, 0)
        self.assertIn('Additional policy.', (self.product / 'AGENTS.md').read_text())
        self.assertIn('Keep task scope bounded.', (self.root / '.codex/agents/sample.toml').read_text())

    def test_invalid_agent_prevents_policy_write_and_escaping_outputs(self):
        policy = self.root / 'policies/shared-conventions.md'
        policy.write_text(policy.read_text() + '\n- Must remain unapplied.\n')
        source = self.root / 'agents/sample.md'
        source.write_text('---\ntarget_plugin: ../outside.md\n---\n\nRole.\n')
        snapshot = self.snapshot()
        result = self.cli('sync')
        self.assertEqual(result.returncode, 1)
        self.assertFalse((self.base / 'outside.md').exists())
        self.assertEqual(snapshot, self.snapshot())

    def test_unknown_and_unmanaged_selection_never_report_false_sync_success(self):
        self.assertEqual(self.cli('doctor', '--repo', 'unknown').returncode, 2)
        self.assertEqual(self.cli('sync', '--repo', 'unknown', '--check').returncode, 2)
        manifest = self.root / 'manifest.toml'
        manifest.write_text(manifest.read_text().replace("agents_md = 'managed'", "agents_md = 'unmanaged'"))
        self.assertEqual(self.cli('sync', '--repo', 'product', '--check').returncode, 1)
        result, report = self.doctor('--repo', 'product')
        self.assertEqual(result.returncode, 0)
        self.assertTrue(any(x['check'] == 'policy' and x['status'] == 'skipped' for x in report['findings']))

    def test_non_repository_directory_is_not_mistaken_for_parent_checkout(self):
        self.git(self.product, 'init', '--bare', str(self.base / 'bare.git'))
        manifest = self.root / 'manifest.toml'
        manifest.write_text(manifest.read_text().replace("path = 'product'", "path = 'bare.git'"))
        result, report = self.doctor('--repo', 'product')
        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(x['check'] == 'repository' and x['status'] == 'error' for x in report['findings']))

    def test_stale_worktrees_and_misplaced_artifacts_are_reported_without_pruning(self):
        worktree = self.base / 'qortoo-worktrees/product.task'
        self.git(self.product, 'worktree', 'add', '--detach', str(worktree))
        shutil.rmtree(worktree)
        local = self.root / '.local'
        local.mkdir()
        (local / 'temporary.log').write_text('Preserve log.')
        snapshot = self.snapshot()
        result, report = self.doctor('--repo', 'product')
        self.assertEqual(result.returncode, 0, result.stderr)
        for check in ('worktree', 'artifacts'):
            self.assertTrue(any(x['check'] == check and x['status'] == 'warning' for x in report['findings']))
        self.assertEqual(snapshot, self.snapshot())
        self.assertIn(str(worktree), self.git(self.product, 'worktree', 'list', '--porcelain'))


if __name__ == '__main__':
    unittest.main()
