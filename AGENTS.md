# MetaKitchen Agent Guide

This is a multi-repository workspace. Each sub-repo has its own `.git` and may have its own agent instruction files.

## Structure

```
meta-repo/
├── AGENTS.md                    ← you are here — start by reading this file
├── metak-shared/                ← read-only shared context (architecture, API contracts, glossary)
├── metak-orchestrator/          ← coordination workspace (TASKS.md, STATUS.md)
├── repo-*/                      ← application sub-repos
└── meta.code-workspace          ← VS Code multi-root workspace file
```

## Agent Rules

1. **Read this file and any agent instructions in your working repo before starting work.**
2. **`metak-shared/` is read-only.** Never modify files there without explicit user approval.
3. **One agent, one repo.** Do not work across multiple repos in a single session. Use the orchestrator pattern for cross-repo work.
4. **Orchestrated tasks:** Read your assignment from `metak-orchestrator/TASKS.md`. Update `metak-orchestrator/STATUS.md` when done or blocked.
5. **API contracts live in `metak-shared/api-contracts/`.** Always reference these for schemas — never import directly from another repo's source.
6. **Consult `metak-shared/architecture.md`** for system boundaries and service interactions.

## Coding Standards

- All code must pass linting and tests before committing.
- Commit messages follow Conventional Commits: `type(scope): description`
- Never import directly from another repo's source code. Use shared contracts in `metak-shared/api-contracts/`.
- When in doubt about system boundaries, consult `metak-shared/architecture.md`.
