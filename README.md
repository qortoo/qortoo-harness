# qortoo-harness

Shared Claude Code configuration for the `qortoo-*` project family (`qortoo-rs`, `qortoo-go`, `qortoo`, ...), distributed as a [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces).

## What's here

- `AGENTS.md` — canonical text for the conventions shared across every qortoo repo (commit/PR format, documentation philosophy, SOLID/English rules). Each consuming repo copies the relevant sections into its own root `AGENTS.md`/`CLAUDE.md`; there's no automatic sync, since tools like Codex don't follow imports into subdirectories.
- `plugins/qortoo-shared/` — language-agnostic agents/commands: `commit-message-writer` agent, `/commit`, `/pr`, `/doc-new` commands.
- `plugins/qortoo-rust/` — Rust-specific agents/commands: `rust-code-reviewer`, `qortoo-api-designer`, `documentation-reviewer` agents; `/pre-commit`, `/doc-generate`, `/doc-review` commands.

## Connecting a repo to this harness

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

Then, in the repo, run `/reload-plugins` and copy the relevant sections of this repo's `AGENTS.md` into the repo's own `AGENTS.md`/`CLAUDE.md`.

Installed commands/agents are namespaced by plugin name, e.g. `/qortoo-shared:commit`, `/qortoo-rust:pre-commit`.

## Adding a new language tier

When a repo (e.g. `qortoo-go`) needs its own language-specific agents/commands, add `plugins/qortoo-go/` following the same structure as `plugins/qortoo-rust/` and register it in `.claude-plugin/marketplace.json`.

## Why a plugin marketplace instead of git submodule + symlinks

A submodule would let files be shared via symlinks, but Claude Code plugins already solve this natively: `.claude/settings.json` can declare the marketplace and default-enabled plugins so they're versioned with the repo, and installed plugins merge into the session without any filesystem wiring. The only real trade-off is that commands are namespaced by plugin name (`/qortoo-shared:commit` instead of `/commit`).
