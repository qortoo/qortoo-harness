---
description: Propose a commit message for the current changes, following this project's convention.
---

## Steps

1. Run `git diff --staged` to see staged changes.
2. If nothing is staged, run `git diff HEAD` and `git status` to see all pending changes and explain that nothing is staged yet.
3. Analyze the changes to determine type, scope, and description.
4. Propose 2–3 commit message candidates, ranked by best fit.

## Commit message format

```
<emoji><type>(<scope>): <description>

<body>
```

- Subject line: emoji and type on the same line, no trailing period, imperative mood, lowercase description.
- Blank line between subject and body.
- Body: bullet points summarizing what changed and why. Each bullet is one complete sentence.
- All content must be in **English**.

## Emoji and type reference

| Emoji | Type | When to use |
|-------|------|-------------|
| 🧬 | `feat` | New feature or capability |
| 🪲 | `fix` | Bug fix |
| 💄 | `refactor` | Code restructuring without behavior change |
| 🧩 | `chore` | Tooling, dependencies, config, CI config |
| 💿 | `CI/CD` | GitHub Actions workflows, CI/CD pipeline changes |
| 📜 | `docs` | Documentation under `./docs/`, README, CLAUDE.md |
| 🧪 | `test` | Tests only, no production code change |
| ⚡ | `perf` | Performance improvement |

## Scope guidelines

Use the most specific affected area:
- Source module: `datatypes`, `connectivity`, `operations`, `errors`, `client`
- Sub-component: `event_loop`, `handler`, `tx_record`, `wired`
- Cross-cutting: `observability`, `docker`, `workflow`
- Omit scope only if the change is truly project-wide

## Output

For each candidate, show:
1. The full commit message (subject + blank line + body) in a code block
2. One sentence explaining why this framing fits

Then ask the user which one to use, or whether to adjust scope/description.
Do not run `git commit` unless the user explicitly confirms.
