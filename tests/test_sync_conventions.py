"""Contract tests for shared policy source and deployment scope."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BEGIN = '<!-- BEGIN QORTOO-HARNESS MANAGED BLOCK -->'
END = '<!-- END QORTOO-HARNESS MANAGED BLOCK -->'


class PolicyDeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'scripts').mkdir()
        shutil.copyfile(ROOT / 'scripts/sync_conventions.py', self.root / 'scripts/sync_conventions.py')
        (self.root / 'policies').mkdir()
        self.source = self.root / 'policies/shared-conventions.md'
        self.source.write_text('## Shared Rules\n\n- Original rule.\n')
        (self.root / 'manifest.toml').write_text(
            '[workspace]\nroot = "."\n[repositories.product]\n'
            'path = "product"\nagents_md = "managed"\n'
        )
        (self.root / 'product').mkdir()
        self.targets = [self.root / 'AGENTS.md', self.root / 'product/AGENTS.md']
        for target in self.targets:
            target.write_text(f'# {target.parent.name}\n\n{BEGIN}\nstale\n{END}\n\n## Local\n\nKeep this rule.\n')

    def run_sync(self, *args):
        return subprocess.run(
            [sys.executable, str(self.root / 'scripts/sync_conventions.py'), *args],
            cwd=self.root, capture_output=True, text=True,
        )

    def test_source_edit_reaches_all_targets_and_preserves_local_text(self):
        before = [p.read_text().split(BEGIN)[0] for p in self.targets]
        self.source.write_text('## Shared Rules\n\n- Replacement rule with `code` and \\paths.\n')
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        for target, prefix in zip(self.targets, before):
            content = target.read_text()
            self.assertEqual(content.split(BEGIN)[0], prefix)
            self.assertTrue(content.endswith('\n\n## Local\n\nKeep this rule.\n'))
            self.assertIn(self.source.read_text().strip(), content)
        snapshot = [p.read_bytes() for p in self.targets]
        self.assertEqual(self.run_sync().returncode, 0)
        self.assertEqual(snapshot, [p.read_bytes() for p in self.targets])
        self.assertEqual(self.run_sync('--check').returncode, 0)

    def test_source_change_is_detected_without_writing_by_check_and_diff(self):
        self.assertEqual(self.run_sync().returncode, 0)
        snapshot = [p.read_bytes() for p in self.targets]
        self.source.write_text('## Shared Rules\n\n- New source rule.\n')
        result = self.run_sync('--check')
        self.assertEqual(result.returncode, 1)
        self.assertIn('qortoo-harness', result.stderr)
        self.assertIn('product', result.stderr)
        result = self.run_sync('--diff')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('+', result.stdout)
        self.assertIn('New source rule.', result.stdout)
        self.assertEqual(snapshot, [p.read_bytes() for p in self.targets])

    def test_missing_or_invalid_source_fails_before_any_write(self):
        snapshot = [p.read_bytes() for p in self.targets]
        self.source.unlink()
        self.assertNotEqual(self.run_sync().returncode, 0)
        for invalid in ['', BEGIN, END]:
            self.source.write_text(invalid)
            self.assertNotEqual(self.run_sync().returncode, 0)
        self.assertEqual(snapshot, [p.read_bytes() for p in self.targets])

    def test_harness_selection_updates_only_this_checkout(self):
        product_before = self.targets[1].read_bytes()
        result = self.run_sync('--repo', 'qortoo-harness')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.run_sync('--check', '--repo', 'qortoo-harness').returncode, 0)
        self.assertEqual(product_before, self.targets[1].read_bytes())
        self.targets[0].write_text(self.targets[0].read_text().replace('Original rule.', 'Local drift.'))
        self.assertEqual(self.run_sync('--check', '--repo', 'qortoo-harness').returncode, 1)

    def test_workspace_overlay_cannot_redirect_harness_deployment(self):
        other = self.root / 'other-workspace'
        other.mkdir()
        decoy = other / 'AGENTS.md'
        decoy.write_text('Do not modify this checkout.\n')
        (self.root / 'manifest.local.toml').write_text(
            '[workspace]\nroot = "other-workspace"\n'
            '[repositories.qortoo-harness]\npath = "."\nagents_md = "managed"\n'
        )
        result = self.run_sync('--repo', 'qortoo-harness')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Original rule.', self.targets[0].read_text())
        self.assertEqual(decoy.read_text(), 'Do not modify this checkout.\n')

    def test_unmarked_bench_requires_explicit_enrollment_and_keeps_all_text(self):
        manifest = self.root / 'manifest.toml'
        manifest.write_text(manifest.read_text().replace('[repositories.product]', '[repositories.qortoo-bench]'))
        original = '# Bench rules\n\n## Personal plan lifecycle\n\nCustom rule; preserve me.'
        self.targets[1].write_text(original)
        snapshot = [p.read_bytes() for p in self.targets]
        result = self.run_sync()
        self.assertEqual(result.returncode, 1)
        self.assertIn('--initialize', result.stderr)
        self.assertEqual(snapshot, [p.read_bytes() for p in self.targets])
        result = self.run_sync('--initialize', '--diff')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(snapshot, [p.read_bytes() for p in self.targets])
        result = self.run_sync('--initialize')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.targets[1].read_text().startswith(original + '\n\n'))
        self.assertEqual(self.run_sync('--check').returncode, 0)

    def test_invalid_markers_fail_preflight_even_with_initialize(self):
        malformed = [
            BEGIN, END, END + '\n' + BEGIN,
            BEGIN + '\n' + BEGIN + '\n' + END,
            BEGIN + '\n' + END + '\n' + END,
            BEGIN + '\n' + END + '\n' + BEGIN + '\n' + END,
            'inline ' + BEGIN + '\n' + END,
            BEGIN + '\n' + END + ' inline',
        ]
        # product sorts before qortoo-harness, so this also detects partial writes.
        for content in malformed:
            with self.subTest(content=content):
                self.targets[0].write_text(content)
                snapshot = [p.read_bytes() for p in self.targets]
                for args in [(), ('--check',), ('--diff',), ('--initialize',)]:
                    result = self.run_sync(*args)
                    self.assertEqual(result.returncode, 1, result.stdout)
                    self.assertIn('malformed or duplicate', result.stderr)
                    self.assertEqual(snapshot, [p.read_bytes() for p in self.targets])

    def test_missing_document_is_created_only_by_explicit_initialization(self):
        self.targets[1].unlink()
        harness_before = self.targets[0].read_bytes()
        self.assertEqual(self.run_sync().returncode, 1)
        self.assertFalse(self.targets[1].exists())
        self.assertEqual(harness_before, self.targets[0].read_bytes())
        self.assertEqual(self.run_sync('--initialize', '--check').returncode, 1)
        self.assertFalse(self.targets[1].exists())
        self.assertEqual(self.run_sync('--initialize').returncode, 0)
        self.assertEqual(self.targets[1].read_text().split(BEGIN)[0], '# Repository Guidelines\n\n')
        self.assertNotIn('npm', self.targets[1].read_text())
        self.assertNotIn('Documentation portal', self.targets[1].read_text())
        self.assertEqual(self.run_sync('--check').returncode, 0)

    def test_update_preserves_crlf_and_outside_bytes(self):
        prefix = '# Local 한글\r\n\r\n'
        suffix = '\r\n\r\n## Commands\r\nPreserve no final newline'
        self.targets[1].write_bytes((prefix + BEGIN + '\r\nold\r\n' + END + suffix).encode('utf-8'))
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        content = self.targets[1].read_bytes().decode('utf-8')
        self.assertEqual(content.split(BEGIN)[0], prefix)
        self.assertEqual(content.split(END)[1], suffix)
        self.assertNotIn('\n', content.replace('\r\n', ''))
        snapshot = self.targets[1].read_bytes()
        self.assertEqual(self.run_sync().returncode, 0)
        self.assertEqual(snapshot, self.targets[1].read_bytes())

    def test_symlink_target_is_rejected_without_modifying_either_file(self):
        external = self.root / 'external.md'
        external.write_text('Private instructions.\n')
        self.targets[1].unlink()
        self.targets[1].symlink_to(external)
        snapshot = [p.read_bytes() for p in self.targets]
        result = self.run_sync('--initialize')
        self.assertEqual(result.returncode, 1)
        self.assertIn('symlink', result.stderr)
        self.assertEqual(snapshot, [p.read_bytes() for p in self.targets])


if __name__ == '__main__':
    unittest.main()
