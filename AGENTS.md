# qortoo — Shared Conventions

This file is the canonical source for conventions shared across every `qortoo-*` repository (Rust, Go, or otherwise). Each repo keeps its own root `AGENTS.md` / `CLAUDE.md` with these sections copied in verbatim, plus repo-specific content appended. When this file changes, copy the updated section into each consuming repo — there is no automatic sync (tools like Codex don't follow imports into subdirectories).

The `qortoo-shared` Claude Code plugin (`plugins/qortoo-shared/`) in this repo provides the actual commit/PR/doc-scaffolding automation described below.

## Critical guidelines

- All code comments and documentation must be written in **English**.
- Favor SOLID principles, especially Single Responsibility (SRP) and Open/Closed (OCP), where practical. Check for these during review.
- Structure important concepts under `./docs/` so they're easy to follow from Markdown and diagrams grounded in the actual code. Use the `/qortoo-shared:doc-new` command to scaffold a new concept document.
- Individual plans, task lists, and working notes belong in the gitignored `.local/` at the repo root — never commit them or propose committing them. Claude Code's project-scoped agent memory (`.claude/agent-memory/`) is likewise personal and gitignored, not shared team knowledge.

## Commit & Pull Request Guidelines

- Commit messages follow an emoji + conventional format: `🧬feat(scope): summary`, `🪲fix(scope): summary`, `📜docs(scope): summary`, `💿CI/CD(scope): summary`. See `/qortoo-shared:commit` for the full emoji/type table and scope guidance.
- Keep scopes specific to the affected module or package.
- PRs should include a concise summary, testing notes (commands run), and links to issues if applicable. Target branch is always `main`; PRs are squash-merged, so the PR title/body becomes the final commit message (`/qortoo-shared:pr` automates this).
- If behavior changes, update docs and add/adjust tests.

## Documentation Guidelines

- Qortoo has not been released yet, so `docs/` should describe only the current intended behavior.
- Do not add development-history or migration notes for intermediate, unreleased changes (for example, that a field or label previously existed and was removed) unless the user explicitly asks for that history.
- Add compatibility or migration guidance only for behavior that has appeared in a released version.
- Concept docs describe the system as it is now and the rule that holds it in place — write principles, not history. Leave out what was tried before, what was removed, or what was "learned the hard way"; git history already carries that.
