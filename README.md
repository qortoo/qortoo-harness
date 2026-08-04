# qortoo-harness

Shared Claude Code configuration for the `qortoo-*` project family (`qortoo-rs`, `qortoo-go`, `qortoo`, ...), distributed as a [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces).

## What's here

- `AGENTS.md` — canonical text for the conventions shared across every qortoo repo (commit/PR format, documentation philosophy, SOLID/English rules). Each consuming repo copies the relevant sections into its own root `AGENTS.md`/`CLAUDE.md`; there's no automatic sync, since tools like Codex don't follow imports into subdirectories.
- `plugins/qortoo-shared/` — language-agnostic agents/commands: `commit-message-writer` agent, `/commit`, `/pr`, `/doc-new` commands.
- `plugins/qortoo-rust/` — Rust-specific agents/commands: `rust-code-reviewer`, `qortoo-api-designer`, `documentation-reviewer` agents; `/pre-commit`, `/doc-generate`, `/doc-review` commands.

## Connecting a repo to this harness

### Claude Code

Add to the repo's `.claude/settings.json` (committed to git, so collaborators get prompted to install on trust):

```json
{
  "extraKnownMarketplaces": {
    "qortoo-harness": {
      "source": { "source": "github", "repo": "qortoo/qortoo-harness" }
    }
  },
  "enabledPlugins": {
    "qortoo-shared@qortoo-harness": true,
    "qortoo-rust@qortoo-harness": true
  }
}
```

Drop `qortoo-rust@qortoo-harness` for non-Rust repos (e.g. `qortoo-go`) once they have their own language-specific plugin.

Then, in the repo, run `/reload-plugins` to pick up the settings.json change in the current session. Alternatively, add the marketplace ad hoc without touching settings.json:

```text
/plugin marketplace add qortoo/qortoo-harness
/plugin install qortoo-shared@qortoo-harness
/plugin install qortoo-rust@qortoo-harness
```

Installed commands/agents are namespaced by plugin name, e.g. `/qortoo-shared:commit`, `/qortoo-rust:pre-commit`.

### Codex

Codex has no plugin marketplace concept — it only reads a repo's root `AGENTS.md` and doesn't follow imports into subdirectories, so none of the above wiring applies. The only way to bring this harness's conventions to Codex is manual: copy the relevant sections of this repo's `AGENTS.md` into the consuming repo's own root `AGENTS.md`. The commands/agents under `plugins/*/commands` and `plugins/*/agents` are Claude Code-only and have no Codex equivalent.

Since there's no automatic sync either way, re-copy the relevant sections whenever this repo's `AGENTS.md` changes.

## Personal workspace convention

Individual developer notes, plans, and in-progress task lists are not shared via git. Every qortoo-* repo should gitignore:

```gitignore
.claude/settings.local.json
.claude/agent-memory/
.local/
```

- `.local/` — free-form personal workspace (plans, task lists, working notes). Not tied to any specific AI tool, so Claude, Codex, or a human can all write here.
- `.claude/agent-memory/` — Claude Code's project-scoped agent memory (e.g. the `qortoo-api-designer` agent's persistent notes). Kept local rather than shared, so its content isn't subject to review before it lands.
- `.claude/settings.local.json` — personal tool permissions/overrides.

`.claude/` itself stays git-tracked for shared config (`settings.json`, plus any repo-local `agents/`/`commands/` not yet promoted to a harness plugin).

## Adding a new language tier

When a repo (e.g. `qortoo-go`) needs its own language-specific agents/commands, add `plugins/qortoo-go/` following the same structure as `plugins/qortoo-rust/` and register it in `.claude-plugin/marketplace.json`.

## Why a plugin marketplace instead of git submodule + symlinks

A submodule would let files be shared via symlinks, but Claude Code plugins already solve this natively: `.claude/settings.json` can declare the marketplace and default-enabled plugins so they're versioned with the repo, and installed plugins merge into the session without any filesystem wiring. The only real trade-off is that commands are namespaced by plugin name (`/qortoo-shared:commit` instead of `/commit`).
