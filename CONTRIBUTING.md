# Contributing

This repository owns shared qortoo policies, agent definitions, and the local harness
CLI. Product code and repository-specific build rules belong in their product
repositories. Shared conventions are described in [AGENTS.md](AGENTS.md).

## Local checks

Use Git and Python 3.11 or newer. The tests use the standard library and temporary
local Git repositories; they do not require remote credentials or SDK toolchains.
From the harness root:

```sh
python3.12 -m unittest discover -s tests
python3.12 scripts/harness.py sync --check
python3.12 scripts/harness.py bootstrap --public-only --dry-run
python3.12 scripts/harness.py doctor
git diff --check
```

Full workspace checks require the catalog's selected repositories. `doctor` also
checks their declared tools and can report ongoing local changes as warnings.
See [CLI contracts](docs/harness-cli.md) for diagnostic scope and exit codes.

## Editing and submission

Edit shared policy in `policies/shared-conventions.md` and shared agent roles in
`agents/`. Preview with `python3.12 scripts/harness.py sync --diff`, then regenerate
and review the affected files. Generated policy blocks and adapters are not authored
independently. Use a local overlay for personal paths; keep plans, reports, logs, and
credentials out of Git.

Update docs and relevant tests with behavior changes. PRs target `main`; include a
concise summary and the checks run, and follow the commit/PR format in `AGENTS.md`.
Review and deliver changes to consuming repositories separately. Worktrees use the
[manual workflow](docs/worktree-lifecycle.md).

The repository's license is [Apache License 2.0](LICENSE).
