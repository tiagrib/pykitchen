# File Structure

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
├── .roo/rules/README.md             ← Roo Code → AGENTS.md
├── .junie/guidelines.md             ← JetBrains Junie → AGENTS.md
│
├── metakitchen/                     ← MetaKitchen documentation (this folder)
│   ├── README.md                    ← index
│   ├── file-structure.md            ← this file
│   ├── usage.md
│   ├── configuration.md
│   └── tips.md
│
├── metak-shared/                    ← read-only shared context
│   ├── architecture.md              ← system-level architecture overview and ADRs
│   ├── api-contracts/               ← OpenAPI specs, protobuf definitions, shared schemas
│   ├── coding-standards.md          ← language-specific conventions, linting rules
│   └── glossary.md                  ← domain terminology
│
├── metak-orchestrator/              ← orchestrator agent workspace
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

## Key Files

### `meta.code-workspace`

Entry point for VS Code. Contains workspace folder definitions, shared settings, extension recommendations, and task definitions.

### `AGENTS.md` (root level and per-repo)

Shared agent instructions that any AI coding agent should read. Contains the meta-repo structure, rules, and coding standards. Each sub-repo can have its own `AGENTS.md` for repo-specific instructions. Agent-specific files (e.g. `.claude/CLAUDE.md`) should just point here.

### `metak-shared/`

The shared ground truth that all agents can read but should never modify without user approval. Contains architecture docs, API contracts, coding standards, and a domain glossary.

### `metak-orchestrator/`

Workspace for a coordinating agent. Contains `TASKS.md` (task definitions) and `STATUS.md` (worker progress). The orchestrator plans and delegates but never writes application code directly.
