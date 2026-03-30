# MetaKitchen Agent Guide

This is a multi-repository workspace. Each sub-repo may have its own agent instruction files.

## Structure

```
meta-repo/
├── .claude/CLAUDE.md                ← root instructions (read by ALL agents)
├── AGENTS.md                        ← you are here
├── CUSTOM.md                        ← project-wide rules for all agents
├── metak-shared/                    ← shared docs: architecture, API contracts, glossary
│   ├── overview.md                  ← project goals and current state
│   ├── architecture.md              ← system boundaries and data flow
│   ├── api-contracts/               ← interface specs between components
│   ├── coding-standards.md          ← linting, commits, reviews
│   ├── glossary.md                  ← domain terms
│   └── LEARNED.md                   ← discovered methods and tricks
├── metak-orchestrator/              ← orchestrator workspace (TASKS.md, STATUS.md, EPICS.md)
├── repo-*/                          ← application sub-repos
└── <project>.code-workspace         ← VS Code multi-root workspace
```

## Agent Roles

### Orchestrator

The orchestrator agent coordinates cross-repo work. It:

- **Writes and maintains `metak-shared/` docs** (overview, architecture, API contracts, glossary) for user review.
- **Breaks work into tasks** in `metak-orchestrator/TASKS.md` with acceptance criteria.
- **Configures workers** by writing `CUSTOM.md` files in each target repo.
- **Spawns worker agents** scoped to individual repos and monitors progress.
- **Reviews completed work** against acceptance criteria and product goals, iterating with follow-up tasks until quality is met.
- **Never writes application code** — only shared docs, tasks, and CUSTOM.md files.

See `metak-orchestrator/AGENTS.md` for full orchestrator instructions.

### Worker Agents

Worker agents operate within a single sub-repo. They:

- Read their assignment from the orchestrator (or `metak-orchestrator/TASKS.md`).
- Read `AGENTS.md` and `CUSTOM.md` in their target directory for instructions.
- Consult `metak-shared/api-contracts/` for interfaces they must conform to.
- Update `metak-orchestrator/STATUS.md` when done or blocked.
- **Treat `metak-shared/` as read-only.** Propose changes via the orchestrator.
- **Document learnings** in `metak-shared/LEARNED.md`.

## Agent Rules

1. **Read `.claude/CLAUDE.md` at the repo root** — it determines your role based on the task scope.
2. **One agent, one subfolder, one repo.** Workers do not work across multiple repos.
3. **API contracts live in `metak-shared/api-contracts/`.** Always reference these for cross-component interfaces.
4. **Consult `metak-shared/architecture.md`** for system boundaries and data flow.

## Coding Standards

Follow `metak-shared/coding-standards.md` for your repo's language.

## Custom Instructions

Read and follow `CUSTOM.md` at the project root for project-wide rules that apply to all agents.
