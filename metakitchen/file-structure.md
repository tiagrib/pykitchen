# File Structure

After running `metak install` in your project, the following structure is created:

```
my-project/
├── AGENTS.md                        ← shared agent instructions (all AI agents read this)
├── CUSTOM.md                        ← project-specific custom instructions (never overwritten)
├── <project>.code-workspace          ← open this in VS Code (named after your folder)
├── GEMINI.md                        ← Gemini CLI pointer to AGENTS.md
├── .claude/CLAUDE.md                ← Claude Code: role router (orchestrator vs worker)
├── .cursor/rules/README.mdc         ← Cursor → AGENTS.md
├── .github/copilot-instructions.md  ← GitHub Copilot → AGENTS.md
├── .windsurfrules                   ← Windsurf → AGENTS.md
├── .clinerules                      ← Cline → AGENTS.md
├── .roo/rules/README.md             ← Roo Code → AGENTS.md
├── .junie/guidelines.md             ← JetBrains Junie → AGENTS.md
├── .amazonq/rules/README.md         ← Amazon Q Developer → AGENTS.md
│
├── metak-shared/                    ← read-only shared context
│   ├── overview.md                  ← project goals and current state
│   ├── architecture.md              ← system boundaries, data flow, ADRs
│   ├── api-contracts/               ← interface specs between components
│   ├── coding-standards.md          ← language-specific conventions, linting rules
│   ├── glossary.md                  ← domain terminology
│   ├── LEARNED.md                   ← methods, procedures, and tricks discovered during work
│   └── templates/                   ← templates used by `metak add`
│       ├── AGENTS.md.template
│       ├── CUSTOM.md.template
│       └── CLAUDE.md.worker.template
│
├── metak-orchestrator/              ← orchestrator agent workspace
│   ├── .claude/CLAUDE.md            ← declares orchestrator identity
│   ├── AGENTS.md                    ← orchestrator-specific instructions and workflow
│   ├── CUSTOM.md                    ← orchestrator-specific custom instructions
│   ├── TASKS.md                     ← task breakdown (orchestrator writes, workers read)
│   ├── STATUS.md                    ← execution status updated by workers
│   ├── EPICS.md                     ← high-level epic grouping
│   └── DECISIONS.md                 ← decision log for choices made under uncertainty
│
├── repo-a/                          ← sub-repo (e.g. frontend)
│   ├── .git/
│   ├── .claude/CLAUDE.md            ← worker identity for this repo
│   ├── AGENTS.md                    ← repo-specific agent instructions
│   ├── CUSTOM.md                    ← repo-specific custom instructions
│   └── ...
│
├── repo-b/                          ← sub-repo (e.g. backend)
│   ├── .git/
│   ├── .claude/CLAUDE.md
│   ├── AGENTS.md
│   ├── CUSTOM.md
│   └── ...
│
└── .vscode/
    └── launch.json                  ← workspace-level compound launch configs
```

## Key Files

### `<project>.code-workspace`

Entry point for VS Code, named after your project folder (e.g. `my-project.code-workspace`). Contains workspace folder definitions, shared settings, extension recommendations, and task definitions.

### `.claude/CLAUDE.md` (root)

Read by ALL agents (Claude Code walks up from cwd). Contains role-routing logic: cross-repo work activates the orchestrator role, single-repo work activates the worker role. Does NOT claim a specific role itself — that would be inherited by all agents.

### `.claude/CLAUDE.md` (per sub-repo)

Declares the worker identity for that sub-repo. Created by `metak add`. Instructs the agent to read its local AGENTS.md and CUSTOM.md, consult api-contracts, and update STATUS.md when done.

### `AGENTS.md` (root level and per-repo)

Shared agent instructions that any AI coding agent should read. Contains the project structure, roles, rules, and coding standards. Each sub-repo can have its own `AGENTS.md` for repo-specific instructions. Agent-specific pointer files (e.g. `.cursor/rules/README.mdc`) redirect here.

### `CUSTOM.md` (root level and per-repo)

Project-specific or repo-specific custom instructions. These files are **never overwritten** by `metak install --force` or `metak add` — they are yours to customize freely. The orchestrator writes project-specific context into repo-level CUSTOM.md files to configure workers.

### `metak-shared/`

The shared ground truth that all agents can read but should never modify without user approval. Contains overview, architecture docs, API contracts, coding standards, glossary, and learned methods.

### `metak-orchestrator/`

Workspace for a coordinating agent. Contains TASKS.md (task definitions), STATUS.md (worker progress), EPICS.md (high-level grouping), and DECISIONS.md (decision log). The orchestrator plans and delegates but never writes application code directly.
