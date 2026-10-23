# Repository Hygiene and Agent Token Optimization Guidelines

## Purpose

This document defines the repository hygiene standards and resource isolation policies across the `qortoo-*` multi-repository ecosystem. Its primary objective is to prevent **context window pollution**, **catastrophic token bloat**, and **code hallucination** when working with AI coding agents (Claude Code, OpenAI Codex, Cursor, etc.).

---

## 1. Worktree Isolation Policy

### Strict External Path Convention

Git worktrees must **never** be placed inside `qortoo-harness` or inside any individual product repository. All isolated development and verification worktrees must reside in the dedicated sibling directory:

```text
/path/to/workspace/
├── qortoo-harness/                    # Control plane
├── qortoo-rs/                         # Core SDK repository
├── qortoo-go/                         # Go binding repository
├── qortoo-bench/                      # Benchmark repository
└── ../qortoo-worktrees/               # ⭐️ Isolated worktree staging directory
    ├── qortoo-rs.feature-xyz/
    └── qortoo-bench.ci-ubicloud/
```

### Rationale: Preventing Search Pollution and Token Explosion

When worktrees are created inside a repository tree (e.g., `.local/worktrees/`), search and exploration tools (`grep`, `find`, ripgrep, agent file indexing) traverse multiple complete copies of the codebase. This causes:
1. **Severe Token Waste**: Single search requests ingest tens or hundreds of thousands of redundant tokens into the model context.
2. **Obsolete Code Hallucination**: Agents inadvertently read outdated implementations from legacy worktrees instead of the active branch, producing incorrect recommendations and regressions.

### Worktree Teardown SOP (Standard Operating Procedure)

Every worktree is ephemeral. Once a task reaches delivery (PR created and merged), the worktree must be retired:

1. **Verify Cleanliness**: Run `git status --porcelain` inside the worktree to ensure no uncommitted or untracked changes remain.
2. **Verify Delivery**: Confirm that the branch commits have been pushed and merged into `origin/main` (or a preserved PR branch).
3. **Remove Worktree**: From the parent repository, run:
   ```sh
   git worktree remove /path/to/qortoo-worktrees/<worktree-name>
   git branch -d <branch-name>
   git worktree prune
   ```

---

## 2. Artifact and Log Containment

### Directory Structure Standards

All personal, temporary, and diagnostic files reside exclusively in the gitignored `.local/` directory of `qortoo-harness`. Root-level pollution in `.local/` is prohibited.

```text
qortoo-harness/.local/
├── plans/              # Active task plans (Active only; read by agents)
├── legacy/             # Completed task plans (Archived personal history)
├── logs/               # Active diagnostic logs
│   └── archive/        # Rotated historical test/benchmark logs
├── validations/        # Consolidated verification and review reports
└── worktrees/          # Worktree metadata JSON only (no source checkouts)
```

### Search Shielding (`.gitignore`, `.claudeignore`, `.ignore`)

Heavy output files, raw telemetry dumps, and virtual environments must be shielded from agent discovery:
- **Tracked Ignore Files**: `.gitignore`, `.claudeignore`, and `.ignore` must remain synchronized and explicitly exclude `*.log`, `*.json` test dumps, `resource-measurements/`, and `.venv/`.
- **Zero Raw Dumps in Git**: Never track raw execution logs, benchmark time-series shards, or binary fixtures in Git.

---

## 3. Agent System Prompt Token Budget

### High-Density Imperative Policy

Shared conventions in `AGENTS.md` are injected into the agent's system prompt on **every session turn**. Every additional line imposes a recurring token fee on every prompt across every project repository.

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
- [ ] Base repositories are on `main` and clean (`git status`).
- [ ] Active plan document exists under `qortoo-harness/.local/plans/`.
- [ ] If isolation is required, spawn the worktree under `../qortoo-worktrees/`.

### When Completing a Task
- [ ] PR is created, CI passes, and changes are squash-merged into `main`.
- [ ] Associated worktree is removed via `git worktree remove` and pruned.
- [ ] Diagnostic logs are moved to `.local/logs/archive/`.
- [ ] Plan document is updated with final outcomes and moved to `.local/legacy/`.
- [ ] Confirm clean workspace: `git status` shows no untracked clutter.
