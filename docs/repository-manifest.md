# Repository Manifest

The repository manifest is the harness's catalog of product checkouts. It supplies
validated paths and metadata to commands without cloning, fetching, switching branches,
or modifying any checkout. Manifest tools require Python 3.11 or newer and use the
standard-library TOML parser; no third-party parser is required.

## Sources and overlay

`manifest.toml` contains the public catalog. Optional, gitignored
`manifest.local.toml` overrides local workspace settings, repository fields, and adds
internal repositories. Both files are read from the supplied harness root. Callers can
set `include_local=False` to inspect the tracked catalog alone.

Workspace fields merge by key. Repository entries merge by repository name and then by
field; arrays such as `tools` replace the complete previous array. Entries cannot be
deleted by an overlay. Unknown fields and invalid table/value types are rejected rather
than silently ignored. TOML comments, quoted strings, multiline arrays, and trailing
commas follow standard TOML syntax. Duplicate keys are errors.

## Schema

Only `workspace` and `repositories` are accepted at the top level. `workspace.root` is
a nonempty path string and defaults to `..`. Repository names use letters, digits,
hyphens, and underscores, starting with a letter or digit. `qortoo-harness` is reserved:
commands identify their own harness checkout directly, outside the product catalog.

| Repository field | Contract |
| --- | --- |
| `path` | Required nonempty path string. |
| `role` | Required nonempty description of the repository's responsibility. |
| `tier` | Required: `public` or `internal`. |
| `remote` | Required for public entries; optional for internal entries. If present, must be a supported repository URL. |
| `default_branch` | Defaults to `main`; nonempty, without whitespace or a leading dash. Git operations must also validate it as a Git ref. |
| `tools` | Defaults to `[]`; unique executable names, without arguments or directory separators. |
| `agents_md` | Defaults to `unmanaged`; accepts `managed` or `unmanaged`. |

Strings cannot be empty, contain control characters, or have surrounding whitespace.
Internal entries without a remote can describe local reference code; their presence
does not authorize a command to invent a clone source.

## Path resolution and isolation

Resolve `workspace.root` relative to the harness checkout. Resolve repository paths
relative to that workspace root. Absolute values remain absolute. The same rules apply
to overlay values; they are not relative to the current working directory. Use absolute
paths for home-directory locations; shell variables and `~` are not expanded.

Resolve symlink aliases and `..` before checking paths. No two repository paths may be
identical or nested. Product paths cannot equal, contain, or reside within the harness
checkout. These checks prevent a command from treating one checkout as two independent
targets. Missing directories are allowed so commands can diagnose or bootstrap them;
existing paths must be directories. Validation checks configuration and filesystem
layout, not whether an existing directory is the expected Git repository. The loader
also retains the configured destination path so bootstrap can reject a leaf symlink
rather than adopting its resolved target.

## Remote identity

Supported remote forms are HTTPS, `ssh://git@host/path`, `git@host:path`, and absolute
`file:///path` URLs. HTTPS credentials, query strings, fragments, and unsupported
transports are rejected. Diagnostics for remote validation do not repeat the URL.

For network identity comparison, normalize hostname case, default HTTPS/SSH ports,
one trailing `.git` suffix, and trailing path slashes. Preserve path case and custom
transport/port identity. Thus `https://example.com/team/sdk.git` and
`git@example.com:team/sdk.git` compare equal, while another owner, host, path case,
or custom port does not. This is a local comparison, not proof of access or current
remote state. File URLs compare by resolved filesystem path and remain distinct from
network URLs; `localhost` is the only permitted file URL host.

## Failures and implementation

The loader returns a `Manifest` with resolved `Repository` records, or raises
`ManifestError`. It neither creates missing directories nor changes configuration or
Git state. Invalid local overlays fail explicitly instead of falling back to the base
catalog. Policy synchronization loads and validates the catalog before writing any
managed blocks.

- [`scripts/harness_manifest.py`](../scripts/harness_manifest.py) owns parsing,
  field merging, schema/path validation, and remote identity comparison.
- [`scripts/sync_conventions.py`](../scripts/sync_conventions.py) selects managed
  repositories and adds the harness's own policy deployment.
- [`tests/test_harness_manifest.py`](../tests/test_harness_manifest.py) verifies the
  manifest contracts; [`tests/test_sync_conventions.py`](../tests/test_sync_conventions.py)
  verifies that invalid configuration prevents policy writes.
- [Repository hygiene](repository-hygiene.md) defines worktree and artifact isolation.
