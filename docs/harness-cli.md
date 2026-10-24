# Harness CLI

The harness CLI provides local diagnostics and synchronization for the repository
catalog. Run `python3.12 scripts/harness.py <command>` with Python 3.11 or newer.
Its scope is the manifest's product checkouts plus the harness that owns the command.

## Doctor

`doctor` reads checkout state and reports each finding with a target, check name,
status, and message. `--json` emits the same findings as structured data.
`--repo <name>` limits repository checks to that catalog entry or `qortoo-harness`;
all shared harness agents and harness artifact checks remain included. The output
identifies both scopes.

| Check | Meaning |
| --- | --- |
| Repository | The directory exists and is the root of a Git working tree. Bare repositories and inherited parent checkouts fail. |
| Remote | A single effective `origin` URL matches the catalog's expected identity. No expected URL means skipped. Remote URLs are not printed. |
| Working tree / branch | Dirty/untracked files, detached HEAD, and a branch other than the configured default are warnings, without changing them. |
| Local tracking | Ahead/behind counts refer only to the cached `origin/<default_branch>` ref. Unavailable refs are unknown. |
| Tools | Required executables exist on PATH and their version probe succeeds. `go` uses `version`; other tools use `--version`. These checks report versions without enforcing SDK-specific minimum versions. |
| Policy / agents | Managed blocks and generated adapters agree with their canonical sources. Missing, malformed, or stale outputs are errors. Unmanaged policy files are skipped. |
| Worktrees | Additional registrations are listed. Missing/prunable, locked, repository-internal, or nonstandard staging paths are warnings. They are never pruned. |
| Artifacts | Root `.local/*.log`, dependency-bump dumps, `validation/`, and directories under `.local/worktrees/` are misplaced-artifact warnings. |

Git probes disable optional index locks and filesystem monitor use. Doctor does not
fetch, stage changes, modify refs, prune registrations, or generate files. External
version probes have a ten-second timeout. This is a bounded local check; tool installation,
PR/CI/merge/publication checks, recursive artifact scans, task-metadata lifecycle
validation, and log-retention decisions are outside its scope. Worktree warnings are
observations, not authorization or proof that a checkout is safe to delete.

## Sync

`sync` first renders and validates every selected managed policy block and every shared
agent adapter without writing. It then applies stale files. `--repo` selects policy
scope only; all shared harness agents remain included. Selecting an unmanaged policy
entry fails rather than claiming that a policy was checked.

- `sync --check` returns nonzero on drift without writing.
- `sync --diff` previews changes without writing. Combine it with `--check` for a
  failing exit status when the preview contains drift.
- `sync --repo <name> --initialize` explicitly enrolls missing/unmarked policy files,
  preserving their existing text. It does not clone a missing repository directory.

Missing managed repositories, invalid policy markers, invalid agent definitions,
symlink outputs, escaping agent targets, and overlapping generated targets fail
preflight. An agent error prevents policy writes as well. Adapter outputs must remain
under a plugin's `agents/` directory and `.codex/agents/` in the harness.
The standalone `scripts/sync_conventions.py` uses the same policy planning logic.

Before application, all stale outputs are compared with their preflight contents; a
concurrent edit aborts the operation. Writes across separate repositories do not form
a filesystem transaction: an I/O failure during application can leave earlier files
updated. Inspect the reported files, resolve the failure, and rerun. Generation does
not commit, push, create a PR, or merge.

## Statuses and exit codes

| Status | Interpretation |
| --- | --- |
| `ok` | The local check completed successfully. |
| `warning` | Observed state needs attention but is allowed, such as ongoing local work. |
| `error` | A required diagnostic or synchronization contract failed. |
| `unknown` | Information is unavailable or requires external verification. |
| `skipped` | No contract applies to that check, such as an unmanaged policy file. |

Doctor exits 0 with no errors, even if warnings or unknown findings remain; it exits 1
when any finding is an error. Invalid arguments, unknown repository names, invalid
manifests, and unsupported Python versions exit 2. Sync exits 1 for drift in check mode,
invalid selected targets, or generation/application errors, and 0 on successful
application or preview. A zero exit status never proves live delivery or worktree
cleanup eligibility.

## Code map

- [`scripts/harness.py`](../scripts/harness.py): command routing, output, exit codes.
- [`scripts/harness_doctor.py`](../scripts/harness_doctor.py): local diagnostic findings.
- [`scripts/harness_sync.py`](../scripts/harness_sync.py): combined generation preflight.
- [`scripts/sync_conventions.py`](../scripts/sync_conventions.py): policy planning and
  generated-file application.
- [`scripts/sync_agents.py`](../scripts/sync_agents.py): agent adapter rendering.
- [`tests/test_harness_cli.py`](../tests/test_harness_cli.py): disposable local Git
  scenarios, drift, failure isolation, and read-only checks including Git index/refs.

See [repository manifest](repository-manifest.md) for configuration and remote identity,
and [repository hygiene](repository-hygiene.md) for isolation and artifact policy.
