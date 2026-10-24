# Worktree Workflow

Use standard Git commands to create and remove worktrees. The harness provides
read-only observations through `doctor`; no separate worktree manager, JSON metadata,
state machine, or `clean` command is required.

## Create outside repositories

Place worktrees under `../qortoo-worktrees/` relative to the harness, outside every
product checkout. Choose an unused path and branch, and an explicit base. From the
harness root, for example:

```sh
git -C ../qortoo-rs worktree list
git -C ../qortoo-rs worktree add -b feature/example ../qortoo-worktrees/qortoo-rs.example main
```

This uses the local `main` snapshot; it does not fetch. Record the checkout path,
branch, and purpose in the existing task plan when one is in use. Preserve the
source checkout's current branch and local changes.

## Before removal

1. Confirm the checkout's purpose and that the task is finished. Leave existing
   dependency checkouts or worktrees of unknown purpose in place.
2. Inspect staged, unstaged, untracked, and ignored files. For example:
   `git -C ../qortoo-worktrees/qortoo-rs.example status --short --ignored`.
   Preserve personal files; remove disposable build output only after identifying it.
3. Confirm that task commits were delivered and that no commits were added afterward.
   For squash merges, inspect the PR's merged status and included head; the original
   commit need not be an ancestor of `main`. A pushed branch or clean status alone
   is insufficient. For a task with no new commits, confirm that its work is complete.
4. If the purpose, files, or delivery state is uncertain, keep the worktree.

## Remove the selected worktree

After those checks and within the authorized task scope, leave the target directory
and remove only that linked worktree:

```sh
git -C ../qortoo-rs worktree remove ../qortoo-worktrees/qortoo-rs.example
git -C ../qortoo-rs worktree list
```

If Git refuses, investigate rather than adding `--force` or deleting the directory
recursively. Keep the branch unless branch deletion is separately authorized.
Update the task plan with the outcome. `doctor` warnings help locate issues but do
not establish that removal is safe.

See [repository hygiene](repository-hygiene.md) for artifact storage and
[CLI usage](harness-cli.md) for diagnostics.
