# File Structure

After running `metak install` in your project, the following structure is created:

```
my-project/
├── AGENTS.md                        ← shared agent instructions (all AI agents read this)
├── CUSTOM.md                        ← project-specific custom instructions (never overwritten)
├── meta.code-workspace              ← open this in VS Code
├── GEMINI.md                        ← Gemini CLI pointer to AGENTS.md
├── .claude/CLAUDE.md                ← Claude Code → AGENTS.md
├── .cursor/rules/README.mdc         ← Cursor → AGENTS.md
├── .github/copilot-instructions.md  ← GitHub Copilot → AGENTS.md
├── .windsurfrules                   ← Windsurf → AGENTS.md
├── .clinerules                      ← Cline → AGENTS.md
├── .roo/rules/README.md             ← Roo Code → AGENTS.md
├── .junie/guidelines.md             ← JetBrains Junie → AGENTS.md
├── .amazonq/rules/README.md         ← Amazon Q Developer → AGENTS.md
│
├── metak-shared/                    ← read-only shared context
│   ├── architecture.md              ← system-level architecture overview and ADRs
│   ├── coding-standards.md          ← language-specific conventions, linting rules
│   ├── glossary.md                  ← domain terminology
│   ├── LEARNED.md                   ← methods, procedures, and tricks discovered during work
│   └── templates/                   ← templates used by `metak add`
│       ├── AGENTS.md.template
│       └── CUSTOM.md.template
│
├── metak-orchestrator/              ← orchestrator agent workspace
│   ├── AGENTS.md                    ← orchestrator-specific instructions
│   ├── CUSTOM.md                    ← orchestrator-specific custom instructions
│   ├── TASKS.md                     ← task breakdown (orchestrator writes, workers read)
│   └── STATUS.md                    ← execution status updated by workers
│
├── repo-a/                          ← sub-repo (e.g. frontend)
│   ├── .git/
│   ├── AGENTS.md                    ← repo-specific agent instructions
│   ├── CUSTOM.md                    ← repo-specific custom instructions
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

Shared agent instructions that any AI coding agent should read. Contains the project structure, rules, and coding standards. Each sub-repo can have its own `AGENTS.md` for repo-specific instructions. Agent-specific files (e.g. `.claude/CLAUDE.md`) just point here.

### `CUSTOM.md` (root level and per-repo)

Project-specific or repo-specific custom instructions. These files are **never overwritten** by `metak install --force` or `metak add` — they are yours to customize freely.

### `metak-shared/`

The shared ground truth that all agents can read but should never modify without user approval. Contains architecture docs, API contracts, coding standards, and a domain glossary.

### `metak-orchestrator/`

Workspace for a coordinating agent. Contains `TASKS.md` (task definitions) and `STATUS.md` (worker progress). The orchestrator plans and delegates but never writes application code directly.
