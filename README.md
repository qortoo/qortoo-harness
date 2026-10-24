# qortoo-harness

Shared Claude Code and Codex tooling for the `qortoo-*` project family (`qortoo-rs`, `qortoo-go`, `qortoo-bench`, `qortoo`, ...). Claude Code tooling is distributed as a [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces); Codex agents use native TOML definitions.

## Principle: this is the only repo with Claude/Codex tooling

Every other `qortoo-*` repo should carry **no Claude Code or Codex config of its own** — no `.claude/settings.json`, no `CLAUDE.md`, no local `agents/`/`commands/`. The one accepted exception is each repo's own root `AGENTS.md`, since that file's content is inherently repo-specific (architecture, build commands, feature flags) and AGENTS.md is a multi-tool open standard (Codex, Claude Code, Cursor, Copilot, ...) rather than Claude-specific config. See [Personal workspace convention](#personal-workspace-convention) below for why `.claude/agent-memory/` and `.local/` still exist on disk without violating this — they're gitignored, so they carry no tracked content in the repo.

The marketplace/plugin registration itself lives in the *developer's* global `~/.claude/settings.json`, not in any repo — see [Connecting a repo to this harness](#connecting-a-repo-to-this-harness).

## What's here

- `AGENTS.md` — canonical text for the conventions shared across every qortoo repo (commit/PR format, documentation philosophy, SOLID/English rules). Each consuming repo copies the relevant sections into its own root `AGENTS.md`; there's no automatic sync, since tools like Codex don't follow imports into subdirectories.
- `agents/bench-agent.md` — canonical benchmark developer role shared by both tools.
- `.codex/agents/` — generated project-scoped Codex agent definitions.
- `plugins/qortoo-shared/` — language-agnostic agents/commands: `bench-agent` and `commit-message-writer` agents, `/commit`, `/pr`, `/doc-new` commands.
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

Codex loads [custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents) from project `.codex/agents/` or user `~/.codex/agents/`. The generated benchmark developer definition lives in this harness's `.codex/agents/`; Claude plugin registration does not register it with Codex.

Start a new Codex session in qortoo-harness and request: "Use the bench-agent subagent to work on qortoo-bench. Run local smoke validation and report the changed scope." Include the actual task, setup status, and relevant plan path. Check the subagent activity to verify the selected role and model; file validation alone does not establish runtime discovery.

To make the same definition available when starting in another repository, link it into the user agent directory. Replace the example checkout path with your own. These commands intentionally do not overwrite an existing definition:

```sh
mkdir -p ~/.codex/agents
ln -s /absolute/path/to/qortoo-harness/.codex/agents/bench-agent.toml ~/.codex/agents/bench-agent.toml
```

No Codex configuration is added to qortoo-bench or the SDK repositories. Keep copying shared conventions into each consuming repo's root `AGENTS.md` when those conventions change. Only explicitly provided Codex adapters are supported; Claude commands and other agents are not automatically translated.

## Bench agent

The [shared role](agents/bench-agent.md) defines scope, measurement contracts, execution authority, completion criteria, and model policy. It covers qortoo-bench development and initial SDK integration; after setup, changes are restricted to benchmark-related work. SDK product optimization is a separately requested task. Local checks and smoke validation are autonomous; full measurements, remote CI, publication, and each Git delivery stage require the corresponding request.

| Tool | Definition | Model during setup |
| --- | --- | --- |
| Claude Code | [qortoo-shared agent](plugins/qortoo-shared/agents/bench-agent.md) | `inherit` |
| Codex | [native agent](.codex/agents/bench-agent.toml) | `gpt-6.1-sol`, reasoning `high` |

Claude Code receives the agent through the existing qortoo-shared plugin. Ask it to use `qortoo-shared:bench-agent` and provide a concrete task. For local harness changes, use the local marketplace source described above; a GitHub-backed install uses the published repository version.

Edit the shared role, then regenerate both adapters with Python 3.9 or newer:

```sh
python3 scripts/sync_agents.py
python3 scripts/sync_agents.py --check
```

Model settings live in the generator. At setup completion, record that decision in the active personal plan and review the model settings. Keep Sol for complex work; evaluate a more economical model on representative bounded tasks before changing the configuration. The pinned Codex definition takes precedence over invocation defaults, so selecting another model requires updating or selecting a different definition. There is no automatic model routing. Compare quality and total usage including retries; a lower model price does not guarantee fewer tokens.

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
