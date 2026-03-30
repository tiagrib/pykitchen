# Configuration

## `AGENTS.md` — the canonical source

All agent instructions live in `AGENTS.md` files (root level for shared rules, per-repo for repo-specific rules). Any AI agent should read these.

Customize the root `AGENTS.md` to reflect your project's structure, coding standards, and agent rules. Sub-repos should have their own `AGENTS.md` for anything specific to that repo.

## Agent pointer files

Each AI agent has its own config file convention. MetaKitchen includes a minimal pointer in each so the agent discovers it natively and gets directed to `AGENTS.md`:

| Agent | Pointer file | Sub-agent orchestration |
|---|---|---|
| Claude Code | `.claude/CLAUDE.md` | Yes |
| Cursor | `.cursor/rules/README.mdc` | Yes |
| GitHub Copilot | `.github/copilot-instructions.md` | Yes (CLI `/fleet`) |
| OpenAI Codex CLI | `AGENTS.md` (native) | Yes |
| Cline | `.clinerules` | Yes |
| Roo Code | `.roo/rules/README.md` | Yes (Boomerang Tasks) |
| JetBrains Junie | `.junie/guidelines.md` | Yes (via Air) |
| Windsurf | `.windsurfrules` | Partial (user-initiated only) |
| Gemini CLI | `GEMINI.md` | Experimental |

Every pointer file contains **role-routing logic** — it directs the agent to `AGENTS.md`, determines whether the agent acts as orchestrator or worker based on the scope of the request, and lists the shared knowledge files. Per-repo `.claude/CLAUDE.md` files (created by `metak add`) declare the worker identity for that sub-repo.

You don't need to touch the pointer files — just keep `AGENTS.md` up to date. The role selection logic is pre-configured in all of them.

## `<project>.code-workspace`

Add sub-repos to the `folders` array so VS Code includes them in the multi-root workspace. Each entry is a relative path matching the submodule folder name:

```json
{
  "folders": [
    { "path": "." },
    { "path": "repo-a" },
    { "path": "repo-b" }
  ]
}
```

Sub-repos can be added as git submodules or plain folders (monorepo) — see [Adding a Sub-Repo](usage.md#adding-a-sub-repo) in the usage guide. The `metak add` command handles this for you.

Workspace-level settings, extension recommendations, and launch configs live here too.
