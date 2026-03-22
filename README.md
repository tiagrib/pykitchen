# MetaKitchen: Multi-Repository Development with AI agents

A multi-root VS Code workspace for coordinating AI coding agents across multiple repositories.

---

## Prerequisites

- **VS Code** (or VS Code Insiders) with an AI coding agent extension
- **Git** — each sub-repo is its own git repository

---

## Getting Started

Open `meta.code-workspace` in VS Code — never open individual folders. This gives you:

- All repos visible in the Explorer sidebar
- Independent git tracking per repo
- Unified search across all codebases
- Shared settings and launch configs

---

## Repository Structure

```
meta-repo/
├── AGENTS.md                        ← shared agent instructions (all AI agents read this)
├── meta.code-workspace              ← open this in VS Code
├── GEMINI.md                        ← Gemini CLI pointer to AGENTS.md
├── .claude/CLAUDE.md                ← Claude Code → AGENTS.md
├── .cursor/rules/README.mdc         ← Cursor → AGENTS.md
├── .github/copilot-instructions.md  ← GitHub Copilot → AGENTS.md
├── .windsurfrules                   ← Windsurf → AGENTS.md
├── .clinerules                      ← Cline → AGENTS.md
├── .amazonq/rules/README.md         ← Amazon Q → AGENTS.md
├── .roo/rules/README.md             ← Roo Code → AGENTS.md
├── .junie/guidelines.md             ← JetBrains Junie → AGENTS.md
│
├── shared/                          ← read-only shared context
│   ├── architecture.md              ← system-level architecture overview and ADRs
│   ├── api-contracts/               ← OpenAPI specs, protobuf definitions, shared schemas
│   ├── coding-standards.md          ← language-specific conventions, linting rules
│   └── glossary.md                  ← domain terminology
│
├── orchestrator/                    ← orchestrator agent workspace
│   ├── AGENTS.md                    ← orchestrator-specific instructions
│   ├── TASKS.md                     ← task breakdown (orchestrator writes, workers read)
│   └── STATUS.md                    ← execution status updated by workers
│
├── repo-a/                          ← sub-repo (e.g. frontend)
│   ├── .git/
│   ├── AGENTS.md                    ← repo-specific agent instructions
│   └── ...
│
├── repo-b/                          ← sub-repo (e.g. backend)
│   ├── .git/
│   ├── AGENTS.md
│   └── ...
│
└── .vscode/
    └── launch.json                  ← workspace-level compound launch configs
```

---

## Key Files

### `meta.code-workspace`

Entry point for VS Code. Contains workspace folder definitions, shared settings, extension recommendations, and task definitions.

### `AGENTS.md` (root level and per-repo)

Shared agent instructions that any AI coding agent should read. Contains the meta-repo structure, rules, and coding standards. Each sub-repo can have its own `AGENTS.md` for repo-specific instructions. Agent-specific files (e.g. `.claude/CLAUDE.md`) should just point here.

### `shared/`

The shared ground truth that all agents can read but should never modify without user approval. Contains architecture docs, API contracts, coding standards, and a domain glossary.

### `orchestrator/`

Workspace for a coordinating agent. Contains `TASKS.md` (task definitions) and `STATUS.md` (worker progress). The orchestrator plans and delegates but never writes application code directly.

---

## Workflows

### Orchestrated Multi-Repo Task

Use when a feature spans multiple repositories.

1. **Brief the orchestrator.** Open an agent terminal in `orchestrator/` and describe the goal.
2. **The orchestrator plans.** It reads `shared/` for context and writes a task breakdown to `TASKS.md`.
3. **Execute with worker agents.** Open an agent terminal in each target repo and point it at its task in `TASKS.md`.
4. **The orchestrator verifies.** Return to the orchestrator terminal to review `STATUS.md` and confirm cross-repo consistency.

### Single-Repo Focused Work

For changes isolated to one repo, skip the orchestrator. Open an agent terminal directly in the target repo — it picks up the root `AGENTS.md` standards.

### Updating Shared Context

1. Make changes to `shared/` yourself or have the orchestrator propose them for your review
2. Notify relevant agents by updating `TASKS.md` or mentioning the change in your next interaction
3. Never let a worker agent modify `shared/` without explicit approval

---

## Agent Configuration

### `AGENTS.md` — the canonical source

All agent instructions live in `AGENTS.md` files (root level for shared rules, per-repo for repo-specific rules). Any AI agent should read these.

### Agent-specific pointer files

Each AI agent has its own config file convention. We create a minimal pointer in each so the agent discovers it natively and gets directed to `AGENTS.md`:

| Agent | Pointer file |
|---|---|
| Claude Code | `.claude/CLAUDE.md` |
| Cursor | `.cursor/rules/README.mdc` |
| GitHub Copilot | `.github/copilot-instructions.md` |
| OpenAI Codex CLI | `AGENTS.md` (native) |
| Gemini CLI | `GEMINI.md` |
| Windsurf | `.windsurfrules` |
| Cline | `.clinerules` |
| Roo Code | `.roo/rules/README.md` |
| Amazon Q | `.amazonq/rules/README.md` |
| JetBrains Junie | `.junie/guidelines.md` |

Each pointer file contains a single line: _"Read and follow `AGENTS.md` at the repository root."_ This keeps instructions in one place while ensuring every agent finds them through its native discovery mechanism.

---

## Tips

- **Always open the `.code-workspace` file**, not individual folders.
- **One agent per terminal, one repo per agent.** Use the orchestrator for cross-repo coordination.
- **Treat `shared/` as a contract boundary.** Changes there are deliberate decisions, not side effects.
- **Keep instructions in `AGENTS.md`**, not scattered across agent-specific config files.
- **`TASKS.md` and `STATUS.md` are plain markdown.** Keep them simple.
- **Git remains per-repo.** The meta-repo structure is a local dev convenience — it doesn't affect CI/CD.
