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

Each pointer file contains a single line directing the agent to `AGENTS.md`. This keeps instructions in one place while ensuring every agent finds them through its native discovery mechanism.

You don't need to touch these files — just keep `AGENTS.md` up to date.

## `meta.code-workspace`

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

Sub-repos should be added as git submodules, not plain folders — see [Adding a Sub-Repo](usage.md#adding-a-sub-repo) in the usage guide.

Workspace-level settings, extension recommendations, and launch configs live here too.
