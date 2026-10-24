"""Manifest format, merge, identity, and path isolation contracts."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from harness_manifest import ManifestError, load_manifest, remotes_equivalent


@unittest.skipIf(sys.version_info < (3, 11), 'Manifest tools require Python 3.11+')
class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / 'harness'
        self.root.mkdir()
        self.path = self.root / 'manifest.toml'
        self.base = '''[workspace]
root = '..' # Inline comments are valid TOML.
[repositories.sdk]
path = 'sdk'
remote = 'https://example.com/team/sdk.git'
role = 'core-sdk'
tier = 'public'
tools = [
  'cargo', # Multiline arrays and trailing commas are valid.
  'rustc',
]
agents_md = 'managed'
'''
        self.path.write_text(self.base)

    def test_standard_toml_and_defaults(self):
        manifest = load_manifest(self.root)
        self.assertEqual(manifest.workspace_root, self.root.parent)
        repo = manifest.repositories['sdk']
        self.assertEqual(repo.path, self.root.parent / 'sdk')
        self.assertEqual(repo.tools, ('cargo', 'rustc'))
        self.assertEqual(repo.default_branch, 'main')
        self.assertFalse(repo.path.exists())

    def test_overlay_merges_fields_and_replaces_arrays_without_touching_files(self):
        (self.root / 'manifest.local.toml').write_text('''[workspace]
root = '../alternate'
[repositories.sdk]
path = 'custom'
remote = 'git@example.com:team/sdk.git'
tools = ['make']
[repositories.private]
path = 'private'
role = 'reference'
tier = 'internal'
''')
        manifest = load_manifest(self.root)
        repo = manifest.repositories['sdk']
        self.assertEqual(repo.path, self.root.parent / 'alternate/custom')
        self.assertEqual(repo.role, 'core-sdk')
        self.assertEqual(repo.tools, ('make',))
        self.assertEqual(repo.agents_md, 'managed')
        private = manifest.repositories['private']
        self.assertIsNone(private.remote)
        self.assertEqual(private.agents_md, 'unmanaged')
        self.assertEqual(load_manifest(self.root, include_local=False).repositories.keys(), {'sdk'})
        self.assertFalse(manifest.workspace_root.exists())
        self.assertEqual(self.path.read_text(), self.base)

    def test_absolute_paths_are_independent_of_workspace(self):
        absolute = self.root.parent / 'elsewhere/sdk'
        (self.root / 'manifest.local.toml').write_text(f'[repositories.sdk]\npath = "{absolute}"\n')
        self.assertEqual(load_manifest(self.root).repositories['sdk'].path, absolute)

    def test_invalid_schema_and_public_remote_are_rejected(self):
        invalid = [
            self.base.replace("path = 'sdk'", ''),
            self.base.replace("role = 'core-sdk'", ''),
            self.base.replace("tier = 'public'", ''),
            self.base.replace("remote = 'https://example.com/team/sdk.git'", ''),
            self.base.replace("root = '..'", 'root = false'),
            self.base.replace("path = 'sdk'", 'path = 42'),
            self.base.replace("tier = 'public'", "tier = 'private'"),
            self.base.replace("agents_md = 'managed'", "agents_md = 'typo'"),
            self.base.replace("'rustc',", "'cargo',"),
            self.base.replace("tools = [", 'tools = [4,'),
            self.base.replace('role =', 'rol ='),
            self.base.replace('[workspace]', '[workspace]\nextra = true'),
            self.base.replace('[repositories.sdk]', '[repositories.qortoo-harness]'),
            self.base.replace("https://example.com/team/sdk.git", "https://user:secret@example.com/team/sdk"),
            'repositories = []',
            'unknown = true',
        ]
        for text in invalid:
            with self.subTest(text=text):
                self.path.write_text(text)
                with self.assertRaises(ManifestError):
                    load_manifest(self.root)

    def test_invalid_overlay_and_toml_fail_without_fallback(self):
        overlay = self.root / 'manifest.local.toml'
        for text in ['[repositories.sdk]\ntools = "cargo"', '[repositories.sdk', 'workspace = []']:
            with self.subTest(text=text):
                overlay.write_text(text)
                with self.assertRaises(ManifestError):
                    load_manifest(self.root)
                self.assertIn('sdk', load_manifest(self.root, include_local=False).repositories)
        self.path.write_text("[workspace]\nroot = '.'\nroot = '..'")
        with self.assertRaises(ManifestError):
            load_manifest(self.root, include_local=False)

    def test_overlapping_paths_and_symlink_aliases_are_rejected(self):
        overlay = self.root / 'manifest.local.toml'
        for path in ['sdk', 'sdk/nested', '.', 'harness', 'harness/nested']:
            with self.subTest(path=path):
                overlay.write_text(f'[repositories.other]\npath = "{path}"\nrole = "sdk"\ntier = "internal"\n')
                with self.assertRaisesRegex(ManifestError, 'overlaps'):
                    load_manifest(self.root)
        (self.root.parent / 'sdk').mkdir()
        alias = self.root.parent / 'alias'
        alias.symlink_to(self.root.parent / 'sdk', target_is_directory=True)
        overlay.write_text('[repositories.other]\npath = "alias"\nrole = "sdk"\ntier = "internal"\n')
        with self.assertRaisesRegex(ManifestError, 'overlaps'):
            load_manifest(self.root)

    def test_non_directory_path_is_rejected(self):
        (self.root.parent / 'sdk').write_text('Do not replace me.')
        with self.assertRaisesRegex(ManifestError, 'not a directory'):
            load_manifest(self.root)
        self.assertEqual((self.root.parent / 'sdk').read_text(), 'Do not replace me.')

    def test_missing_catalog_and_file_workspace_are_errors(self):
        self.path.unlink()
        with self.assertRaisesRegex(ManifestError, 'Cannot read manifest.toml'):
            load_manifest(self.root)
        (self.root / 'file').write_text('Preserve this file.')
        self.path.write_text(self.base.replace("root = '..'", "root = 'file'"))
        with self.assertRaisesRegex(ManifestError, 'workspace.root is not a directory'):
            load_manifest(self.root)


class RemoteIdentityTests(unittest.TestCase):
    def test_transport_equivalence_preserves_repository_and_custom_port_identity(self):
        https = 'https://example.com/team/sdk.git'
        for remote in ['git@example.com:team/sdk.git', 'ssh://git@EXAMPLE.com/team/sdk', 'https://example.com:443/team/sdk/', 'ssh://git@example.com:22/team/sdk.git']:
            with self.subTest(remote=remote):
                self.assertTrue(remotes_equivalent(https, remote))
        for remote in ['https://elsewhere.com/team/sdk', 'https://example.com/other/sdk', 'ssh://git@example.com:2222/team/sdk', 'https://example.com/team/SDK']:
            self.assertFalse(remotes_equivalent(https, remote))

        self.assertFalse(remotes_equivalent('https://example.com:2222/team/sdk', 'ssh://git@example.com:2222/team/sdk'))

    def test_local_file_remotes_remain_distinct_from_network_urls(self):
        self.assertTrue(remotes_equivalent('file:///tmp/a/../sdk.git', 'file://localhost/tmp/sdk.git'))
        self.assertFalse(remotes_equivalent('file:///tmp/sdk.git', 'https://example.com/tmp/sdk.git'))

    def test_invalid_remote_error_does_not_echo_credentials(self):
        for remote in ['https://token:secret@example.com/team/sdk', 'http://example.com/team/sdk', 'ssh://git@example.com:bad/team/sdk', 'https://example.com', 'https://example.com/team/../sdk']:
            with self.subTest(remote=remote):
                with self.assertRaises(ManifestError) as error:
                    remotes_equivalent(remote, 'https://example.com/team/sdk')
                self.assertNotIn('secret', str(error.exception))


if __name__ == '__main__':
    unittest.main()
