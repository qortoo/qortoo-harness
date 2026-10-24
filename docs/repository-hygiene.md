# Repository Hygiene and Agent Token Optimization Guidelines

## Purpose

This document defines the repository hygiene standards and resource isolation policies across the `qortoo-*` multi-repository ecosystem. Its primary objective is to prevent **context window pollution**, **catastrophic token bloat**, and **code hallucination** when working with AI coding agents (Claude Code, OpenAI Codex, Cursor, etc.).

---

## 1. Worktree Isolation Policy

Follow the short [worktree workflow](worktree-lifecycle.md) using standard Git commands
and existing `doctor` diagnostics.
Worktrees belong under `../qortoo-worktrees/` relative to the harness, outside every
repository checkout:

```text
/path/to/workspace/
├── qortoo-harness/
├── qortoo-rs/
├── qortoo-go/
├── qortoo-bench/
└── qortoo-worktrees/
    ├── qortoo-rs.feature-xyz/
    └── qortoo-bench.runner-check/
```

### Rationale: Preventing Search Pollution and Token Explosion

Worktrees inside a repository can expose duplicate or outdated code to searches and
agent indexing. This increases unnecessary context and token use, and can lead an
agent to reason from the wrong checkout. External placement helps keep searches
focused on the intended codebase.

Exposure depends on the search root, flags, and tool ignore support. Ignore rules
provide an additional safeguard; a fixed token cost or reduction is not assumed.

### Before Removal

Before removing a worktree, confirm its purpose, local files (including ignored
files), and task delivery. Preserve anything uncertain. Worktree removal and branch
deletion are separate actions; the workflow describes the manual checks.

---

## 2. Artifact and Log Containment

### Directory Structure Standards

All personal, temporary, and diagnostic files reside exclusively in the gitignored `.local/` directory of `qortoo-harness`. Root-level pollution in `.local/` is prohibited.

```text
qortoo-harness/.local/
├── plans/              # Active task plans (Active only; read by agents)
├── archive/            # Completed plans (personal history)
├── logs/               # Active diagnostic logs
│   └── archive/        # Rotated historical test/benchmark logs
└── validations/        # Consolidated verification and review reports
```

### Search Shielding (`.gitignore`, `.claudeignore`, `.ignore`)

Heavy output files, raw telemetry dumps, and virtual environments must be shielded from agent discovery:
- **Tracked Ignore Files**: `.gitignore`, `.claudeignore`, and `.ignore` must remain synchronized and explicitly exclude `*.log`, `*.json` test dumps, `resource-measurements/`, and `.venv/`.
- **Zero Raw Dumps in Git**: Never track raw execution logs, benchmark time-series shards, or binary fixtures in Git.

---

## 3. Agent System Prompt Token Budget

### High-Density Imperative Policy

Shared conventions in `AGENTS.md` occupy instruction context when loaded by an agent.
Loading and prompt-caching behavior vary by tool; keep the common block concise.

- **Token Ceiling**: The shared conventions block must not exceed **800–1,000 tokens** (approximately 60–80 concise lines).
- **Actionable Constraints Only**: Include only concrete, non-obvious operational rules (commit format, English documentation requirement, SOLID emphasis, plan lifecycle).
- **Delegation to Documentation**: Long explanations, theoretical rationale, architectural essays, and tutorials must be placed in `./docs/` files and linked, rather than embedded directly in `AGENTS.md`.

---

## 4. Agent Local State and Memory Management

### Claude Code Agent Memory (`.claude/agent-memory/`)

Claude Code maintains persistent project-scoped memory across sessions. While useful for short-term recall, unbounded memory growth consumes context budget on every startup.
- Review `.claude/agent-memory/` periodically.
- Clear or summarize notes once the corresponding milestone is merged.

### Codex and External AI State

Do not commit temporary conversation transcripts, IDE scratch files, or model cache directories. Use `.local/` for developer scratch notes.

---

## 5. Development Cycle Checklist (Hygiene SOP)

### When Starting a Task
- [ ] Inspect the current branch and changes; preserve existing work without automatically switching or resetting repositories.
- [ ] Active plan document exists under `qortoo-harness/.local/plans/`.
- [ ] If isolation is required, spawn the worktree under `../qortoo-worktrees/`.

### When Completing a Task
- [ ] PR is created, CI passes, and changes are squash-merged into `main`.
- [ ] Review any task worktree using the [removal checklist](worktree-lifecycle.md#before-removal); remove it only when safe and authorized.
- [ ] Diagnostic logs are moved to `.local/logs/archive/`.
- [ ] Plan document is updated with final outcomes and moved to `.local/archive/`.
- [ ] Confirm clean workspace: `git status` shows no untracked clutter.
