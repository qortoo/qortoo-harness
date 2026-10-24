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

    def clone_source(self):
        remote = self.base / 'source.git'
        self.git(self.product, 'clone', '--bare', str(self.product), str(remote))
        manifest = self.root / 'manifest.toml'
        manifest.write_text(manifest.read_text().replace('https://example.com/team/product.git', remote.as_uri()))
        self.git(self.product, 'remote', 'set-url', 'origin', remote.as_uri())
        return remote

    def test_bootstrap_clones_missing_repository_and_is_idempotent(self):
        self.clone_source()
        self.product.rename(self.base / 'original-product')
        before = self.snapshot()
        preview = self.cli('bootstrap', '--dry-run')
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertIn('WOULD CLONE', preview.stdout)
        self.assertFalse(self.product.exists())
        self.assertEqual(before, self.snapshot())
        result = self.cli('bootstrap')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('CLONED', result.stdout)
        self.assertEqual(self.git(self.product, 'branch', '--show-current').strip(), 'main')
        after = self.snapshot()
        self.assertEqual(self.cli('bootstrap').returncode, 0)
        self.assertEqual(after, self.snapshot())
        for name, evidence in before.items():
            self.assertEqual(after[name], evidence)
        result, report = self.doctor()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any(x['status'] == 'error' for x in report['findings']))

    def test_bootstrap_preserves_existing_dirty_branch_without_fetching(self):
        self.clone_source()
        self.git(self.product, 'switch', '-c', 'feature/local')
        (self.product / 'untracked.txt').write_text('Keep this file.')
        (self.product / 'AGENTS.md').write_text('Keep local edits.')
        snapshot = self.snapshot()
        result = self.cli('bootstrap')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('PRESERVED', result.stdout)
        self.assertEqual(snapshot, self.snapshot())

    def test_bootstrap_preflights_all_entries_before_cloning(self):
        remote = self.clone_source()
        self.product.rename(self.base / 'original-product')
        blocked = self.base / 'z-blocked'
        blocked.mkdir()
        (blocked / 'notes.txt').write_text('Existing non-repository data.')
        with (self.root / 'manifest.toml').open('a') as stream:
            stream.write(f'\n[repositories.z-blocked]\npath = "z-blocked"\nrole = "sdk"\ntier = "public"\nremote = "{remote.as_uri()}"\n')
        snapshot = self.snapshot()
        result = self.cli('bootstrap')
        self.assertEqual(result.returncode, 1)
        self.assertIn('no clones started', result.stderr)
        self.assertFalse(self.product.exists())
        self.assertEqual(snapshot, self.snapshot())

    def test_bootstrap_mismatched_remote_and_empty_directory_are_preserved(self):
        snapshot = self.snapshot()
        self.git(self.product, 'remote', 'set-url', 'origin', 'https://example.com/wrong/product.git')
        snapshot = self.snapshot()
        self.assertEqual(self.cli('bootstrap').returncode, 1)
        self.assertEqual(snapshot, self.snapshot())
        self.product.rename(self.base / 'saved-product')
        self.product.mkdir()
        self.assertEqual(self.cli('bootstrap').returncode, 1)
        self.assertTrue(self.product.is_dir())
        self.assertEqual(list(self.product.iterdir()), [])

    def test_bootstrap_rejects_live_and_dangling_destination_symlinks(self):
        saved = self.base / 'saved-product'
        self.product.rename(saved)
        self.product.symlink_to(saved, target_is_directory=True)
        snapshot = self.snapshot()
        result = self.cli('bootstrap')
        self.assertEqual(result.returncode, 1)
        self.assertIn('symlink destination', result.stderr)
        self.assertTrue(self.product.is_symlink())
        self.assertEqual(snapshot, self.snapshot())
        self.product.unlink()
        absent = self.base / 'absent-target'
        self.product.symlink_to(absent, target_is_directory=True)
        result = self.cli('bootstrap')
        self.assertEqual(result.returncode, 1)
        self.assertTrue(self.product.is_symlink())
        self.assertFalse(absent.exists())

    def test_bootstrap_clone_failure_removes_only_owned_empty_directory_and_retries(self):
        remote = self.clone_source()
        self.product.rename(self.base / 'original-product')
        manifest = self.root / 'manifest.toml'
        correct = manifest.read_text()
        manifest.write_text(correct.replace(remote.as_uri(), (self.base / 'missing-source.git').as_uri()))
        result = self.cli('bootstrap')
        self.assertEqual(result.returncode, 1)
        self.assertIn('safe to retry', result.stderr)
        self.assertFalse(self.product.exists())
        manifest.write_text(correct)
        self.assertEqual(self.cli('bootstrap').returncode, 0)

    def test_bootstrap_public_filter_and_local_only_entries_are_explicit(self):
        self.clone_source()
        overlay = self.root / 'manifest.local.toml'
        overlay.write_text('[repositories.internal-reference]\npath = "internal-reference"\nrole = "reference"\ntier = "internal"\n')
        result = self.cli('bootstrap')
        self.assertEqual(result.returncode, 1)
        self.assertIn('no clone remote', result.stderr)
        snapshot = self.snapshot()
        result = self.cli('bootstrap', '--public-only')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('SKIPPED', result.stdout)
        self.assertEqual(snapshot, self.snapshot())
        self.assertEqual(self.cli('bootstrap', '--repo', 'internal-reference', '--public-only').returncode, 2)
        self.assertEqual(self.cli('bootstrap', '--repo', 'qortoo-harness').returncode, 2)

    def test_bootstrap_validates_branch_before_creating_destination(self):
        self.clone_source()
        self.product.rename(self.base / 'original-product')
        with (self.root / 'manifest.toml').open('a') as stream:
            stream.write('default_branch = "invalid..branch"\n')
        snapshot = self.snapshot()
        result = self.cli('bootstrap')
        self.assertEqual(result.returncode, 1)
        self.assertIn('not a valid Git branch', result.stderr)
        self.assertEqual(snapshot, self.snapshot())

    def test_bootstrap_refuses_new_checkout_inside_an_uncatalogued_git_repository(self):
        container = self.base / 'container'
        container.mkdir()
        self.git(container, 'init', '-b', 'main')
        manifest = self.root / 'manifest.toml'
        manifest.write_text(manifest.read_text().replace("path = 'product'", "path = 'container/nested'"))
        snapshot = self.snapshot()
        result = self.cli('bootstrap')
        self.assertEqual(result.returncode, 1)
        self.assertIn('nest inside another Git checkout', result.stderr)
        self.assertEqual(snapshot, self.snapshot())

    def test_bootstrap_preserves_nonempty_failed_clone_and_refuses_automatic_retry(self):
        from unittest.mock import patch
        sys.path.insert(0, str(ROOT / 'scripts'))
        from harness_bootstrap import BootstrapError, bootstrap, plan_bootstrap
        from harness_manifest import load_manifest
        self.clone_source()
        self.product.rename(self.base / 'original-product')
        actions = plan_bootstrap(load_manifest(self.root))

        def failed_clone(*args, **kwargs):
            (self.product / 'keep.txt').write_text('Partial output must be preserved.')
            return subprocess.CompletedProcess(args[0], 1)

        with patch('harness_bootstrap.subprocess.run', side_effect=failed_clone):
            with self.assertRaisesRegex(BootstrapError, 'destination retained'):
                bootstrap(actions)
        self.assertEqual((self.product / 'keep.txt').read_text(), 'Partial output must be preserved.')
        self.assertEqual(self.cli('bootstrap').returncode, 1)
        self.assertEqual((self.product / 'keep.txt').read_text(), 'Partial output must be preserved.')

    def test_bootstrap_does_not_adopt_a_destination_created_after_preflight(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        from harness_bootstrap import BootstrapError, bootstrap, plan_bootstrap
        from harness_manifest import load_manifest
        self.clone_source()
        self.product.rename(self.base / 'original-product')
        actions = plan_bootstrap(load_manifest(self.root))
        self.product.mkdir()
        snapshot = self.snapshot()
        with self.assertRaises(BootstrapError):
            bootstrap(actions)
        self.assertTrue(self.product.is_dir())
        self.assertFalse((self.product / '.git').exists())
        self.assertEqual(snapshot, self.snapshot())

    def test_bootstrap_rejects_remote_tag_in_place_of_configured_branch(self):
        self.git(self.product, 'tag', 'v1')
        self.clone_source()
        self.product.rename(self.base / 'original-product')
        with (self.root / 'manifest.toml').open('a') as stream:
            stream.write('default_branch = "v1"\n')
        result = self.cli('bootstrap')
        self.assertEqual(result.returncode, 1)
        self.assertIn('did not create the configured branch', result.stderr)
        self.assertIn('destination retained', result.stderr)
        self.assertTrue((self.product / '.git').is_dir())


if __name__ == '__main__':
    unittest.main()
