## Critical Guidelines

- **English**: Write code comments and shared, tracked documentation in English. Personal plans under `qortoo-harness/.local/plans/` use the user's session language.
- **Design**: Favor SOLID principles, especially SRP and OCP; check them during review.
- **Tooling Ownership**: Keep shared Claude/Codex tooling in `qortoo-harness`. Other repositories carry only their root `AGENTS.md`; do not add `CLAUDE.md` or tracked `.claude/settings.json`. Personal, gitignored agent state is local.
- **Worktrees**: Create isolated worktrees outside every repository, under `../qortoo-worktrees/` relative to the harness. See `qortoo-harness/docs/repository-hygiene.md`.
- **Personal Work**: Keep plans in `qortoo-harness/.local/plans/` and any personal notes or retained evidence under its `.local/`. Use ctx history before creating duplicate records; do not save routine passing logs or duplicate validation reports. Retain evidence when exact output or reproducibility matters. Use `ctx sift` for long output when appropriate. Never commit personal `.local/` or `.claude/` state. Update the plan's status, checklist, and progress log during the work, including corrections and scope decisions.

## Implementation Completion

- Before editing, inspect related callers and existing patterns; identify which types and modules own state, invariants, validation, and conversion.
- Complete each authorized implementation stage with coherent responsibility boundaries. When types or features rule out a case, remove obsolete runtime branches and update affected callers; preserve validation at external input boundaries.
- Before reporting completion, review the final diff and directly connected code for misplaced responsibilities, duplicate state or validation, confusing names, unnecessary forwarding functions, and preserved error handling. Fix issues within the authorized scope; do not expand into unrelated cleanup or later stages.
- Prefer clear ownership and readable control flow over fewer lines or a smaller diff. For proposed merges or splits, assess readability first and explain a clearer alternative when appropriate.
- Run checks appropriate to the change. Distinguish implemented behavior, verified behavior, and unresolved decisions in the completion report; passing tests alone do not establish sound design. Scale this self-review to the change without requiring a separate agent or report.

## Commit & Pull Request Guidelines

- Use emoji + conventional messages with a specific package/module scope: `🧬feat(scope): summary`, `🪲fix(scope): summary`, `📜docs(scope): summary`, `💿CI/CD(scope): summary`, `🧩chore(scope): summary`, `🧪test(scope): summary`, `⚡perf(scope): summary`. See `/qortoo-shared:commit` for the full table.
- Target PRs at `main` and squash-merge; the PR title/body becomes the final commit message. Include a concise summary, testing commands, and issue links where applicable. See `/qortoo-shared:pr`.
- When behavior changes, update docs and add or adjust tests.

## Documentation Guidelines

- Qortoo is unreleased: document current intended behavior and principles, without intermediate development history or migration notes unless the user requests history. Add compatibility/migration guidance only for released behavior.
- Organize concept documentation under `./docs/`, with Markdown and diagrams grounded in the code. Use `/qortoo-shared:doc-new` to scaffold concepts.

## Personal Plan Lifecycle

- Keep active plans in `qortoo-harness/.local/plans/`.
- Before closing a plan, verify its checklist and external delivery state. Keep it active while any acceptance condition remains.
- Mark a finished plan complete, record its final outcome, and move it to `qortoo-harness/.local/archive/`. Retain completed plans; never commit either directory.
