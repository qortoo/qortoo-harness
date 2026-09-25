# qortoo-harness

Shared Claude Code configuration for the `qortoo-*` project family (`qortoo-rs`, `qortoo-go`, `qortoo`, ...), distributed as a [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces).

## Principle: this is the only repo with Claude/Codex tooling

Every other `qortoo-*` repo should carry **no Claude Code or Codex config of its own** — no `.claude/settings.json`, no `CLAUDE.md`, no local `agents/`/`commands/`. The one accepted exception is each repo's own root `AGENTS.md`, since that file's content is inherently repo-specific (architecture, build commands, feature flags) and AGENTS.md is a multi-tool open standard (Codex, Claude Code, Cursor, Copilot, ...) rather than Claude-specific config. See [Personal workspace convention](#personal-workspace-convention) below for why `.claude/agent-memory/` and `.local/` still exist on disk without violating this — they're gitignored, so they carry no tracked content in the repo.

The marketplace/plugin registration itself lives in the *developer's* global `~/.claude/settings.json`, not in any repo — see [Connecting a repo to this harness](#connecting-a-repo-to-this-harness).

## What's here

- `AGENTS.md` — canonical text for the conventions shared across every qortoo repo (commit/PR format, documentation philosophy, SOLID/English rules). Each consuming repo copies the relevant sections into its own root `AGENTS.md`; there's no automatic sync, since tools like Codex don't follow imports into subdirectories.
- `plugins/qortoo-shared/` — language-agnostic agents/commands: `commit-message-writer` agent, `/commit`, `/pr`, `/doc-new` commands.
- `plugins/qortoo-rust/` — Rust-specific agents/commands: `rust-code-reviewer`, `qortoo-api-designer`, `documentation-reviewer` agents; `/pre-commit`, `/doc-generate`, `/doc-review` commands.

## Connecting a repo to this harness

### Claude Code

Register the marketplace and plugins once in your own **global** `~/.claude/settings.json` — not the repo's. This keeps every qortoo-* repo free of Claude-specific files, and applies automatically whenever you open any qortoo-* project on this machine:

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

(A local `directory` source pointing at your qortoo-harness clone also works instead of `github`, and picks up uncommitted local changes immediately — convenient for iterating on the harness itself.)

Equivalently, from any Claude Code session:

```text
/plugin marketplace add qortoo/qortoo-harness
/plugin install qortoo-shared@qortoo-harness --scope user
/plugin install qortoo-rust@qortoo-harness --scope user
```

Drop `qortoo-rust@qortoo-harness` if you don't work on Rust qortoo repos, or add a future `qortoo-go@qortoo-harness` once that tier exists.

Installed commands/agents are namespaced by plugin name, e.g. `/qortoo-shared:commit`, `/qortoo-rust:pre-commit`.

**Trade-off**: since nothing is committed to the consuming repos, a new teammate cloning `qortoo-rs` gets no automatic install prompt — they need to register the marketplace themselves once, per the steps above.

### Codex

Codex has no plugin marketplace concept — it only reads a repo's root `AGENTS.md` and doesn't follow imports into subdirectories, so none of the above wiring applies. The only way to bring this harness's conventions to Codex is manual: copy the relevant sections of this repo's `AGENTS.md` into the consuming repo's own root `AGENTS.md`. The commands/agents under `plugins/*/commands` and `plugins/*/agents` are Claude Code-only and have no Codex equivalent.

Since there's no automatic sync either way, re-copy the relevant sections whenever this repo's `AGENTS.md` changes.

## Personal workspace convention

Individual developer notes, plans, and in-progress task lists are not shared via git. Every qortoo-* repo should gitignore:

```gitignore
.claude
.local/
```

- `.local/` — free-form personal workspace (plans, task lists, working notes). Active plan documents live under `.local/plans/`; after their checklist and external delivery are complete, mark them complete and move them to `.local/legacy/`. Plan documents use the language of the current user session, while other content remains free-form. The workspace is not tied to any specific AI tool, so Claude, Codex, or a human can all write here.
- `.claude/` — now holds only local, gitignored state: `settings.local.json` (personal tool permissions) and `agent-memory/` (Claude Code's project-scoped agent memory, e.g. the `qortoo-api-designer` agent's persistent notes — kept local rather than shared, so its content isn't subject to review before it lands). Nothing under `.claude/` is tracked in a qortoo-* repo other than this one.

## Adding a new language tier

When a repo (e.g. `qortoo-go`) needs its own language-specific agents/commands, add `plugins/qortoo-go/` following the same structure as `plugins/qortoo-rust/` and register it in `.claude-plugin/marketplace.json`.

## Why a plugin marketplace instead of git submodule + symlinks

A submodule would let files be shared via symlinks, but Claude Code plugins already solve this natively: the marketplace and default-enabled plugins are declared once in the developer's own global settings, and installed plugins merge into the session without any filesystem wiring or per-repo config at all. The trade-offs: commands are namespaced by plugin name (`/qortoo-shared:commit` instead of `/commit`), and a new teammate has to register the marketplace themselves once since nothing about it is committed to the consuming repos.
