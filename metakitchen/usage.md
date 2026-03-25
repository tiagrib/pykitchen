# Usage

## What MetaKitchen Provides

MetaKitchen is a starting point, not a framework. It gives you:

- **A folder structure** — `metak-orchestrator/` for coordination, `metak-shared/` for cross-repo context, and placeholders for your sub-repos.
- **Agent pointer files** — every major AI coding agent has its own config file convention (`.claude/CLAUDE.md`, `.cursor/rules/README.mdc`, `.windsurfrules`, etc.). MetaKitchen pre-wires all of them to point at a single `AGENTS.md`, so whichever agent a developer uses, it reads the same instructions.
- **`AGENTS.md`** — a starting template. **You are expected to edit this** to reflect your project's actual structure, rules, and coding standards. The pointer files stay as-is; only `AGENTS.md` needs to grow with your project.

The goal is that any agent, on any machine, opened in any sub-repo, automatically picks up the same shared instructions without any extra setup.

## Prerequisites

- **VS Code** (or VS Code Insiders) with an AI coding agent extension
- **Git** — each sub-repo is its own git repository
- **Python 3.7+** — for the `metak.py` helper script (no extra packages needed)

## Getting Started

1. Fork or clone this repository to start a new project.
2. Open `meta.code-workspace` in VS Code — never open individual folders. This gives you:
   - All repos visible in the Explorer sidebar
   - Independent git tracking per repo
   - Unified search across all codebases
   - Shared settings and launch configs
3. Add sub-repos as git submodules (see [Adding a Sub-Repo](#adding-a-sub-repo) below).
4. Adapt `AGENTS.md` to your project — describe your actual repo structure, team rules, and coding standards. Fill in `metak-shared/architecture.md`, `metak-shared/coding-standards.md`, and `metak-shared/glossary.md` as your project takes shape.

## Adding a Sub-Repo

Each sub-repo is a git submodule — a separate git repository tracked at a fixed commit inside the meta-repo.

### Add a new submodule

```bash
git submodule add <repo-url> <folder-name>
# e.g.
git submodule add https://github.com/your-org/frontend frontend
```

This creates the folder, clones the repo into it, and registers it in `.gitmodules`. Then run `metak` to finish the setup:

```bash
python metak.py frontend
```

This will:
- Add the folder to `meta.code-workspace` so it appears in the VS Code Explorer sidebar
- Create a starter `AGENTS.md` in the folder if one doesn't already exist

Then commit everything:

```bash
git add .gitmodules frontend meta.code-workspace
git commit -m "chore: add frontend submodule"
```

### Clone the meta-repo with submodules

Anyone cloning the meta-repo needs to initialise submodules too:

```bash
git clone --recurse-submodules <meta-repo-url>
# or, if already cloned:
git submodule update --init --recursive
```

### Update a submodule to its latest commit

```bash
cd <folder-name>
git pull origin main
cd ..
git add <folder-name>
git commit -m "chore: bump <folder-name> to latest"
```

### Remove a submodule

```bash
git submodule deinit -f <folder-name>
git rm <folder-name>
rm -rf .git/modules/<folder-name>
git commit -m "chore: remove <folder-name> submodule"
```

## Workflows

### Orchestrated Multi-Repo Task

Use when a feature spans multiple repositories.

1. **Brief the orchestrator.** Open an agent session in `metak-orchestrator/` and describe the goal.
2. **The orchestrator plans.** It reads `metak-shared/` for context and writes a task breakdown to `TASKS.md` — one task per target repo, each with acceptance criteria.
3. **The orchestrator spawns workers.** It launches a worker agent per task, scoped to the target repo folder. Workers implement their task and update `STATUS.md` when done or blocked.
4. **The orchestrator verifies.** Once all workers finish, it checks cross-repo consistency and reports back.

You stay in the orchestrator session throughout — you don't open or manage per-repo sessions yourself.

#### Manual fallback

If your agent doesn't support subagent spawning, the orchestrator will tell you which tasks to run manually. Open an agent session in each target repo and tell it to implement its task from `TASKS.md`.

Subagent support by agent:

| Agent | Mechanism | Notes |
|---|---|---|
| **Claude Code** | `Agent` tool | Workers run with full tool access in a scoped folder. |
| **Roo Code** | `new_task` tool (Boomerang Tasks) | Set mode to `code` or `architect` per task. Parent task pauses and resumes when subtask returns. |
| **Cursor** | Native subagents | Cursor 2.0+ runs workers in isolated git worktrees. Up to 8 parallel agents per request. |
| **Cline** | `use_subagents` tool | Each subagent runs with its own context window. Results returned as a report. |
| **OpenAI Codex CLI** | Explicit subagent invocation | Spawn via the Agents SDK. Only spawns when explicitly asked. |
| **GitHub Copilot** | `/fleet` command | Pass the task plan; Copilot breaks it into parallel subtasks automatically. |
| **JetBrains Junie** | Subagents via Air | Define subagents with Agent Skills; Air manages concurrent execution. |

> **Not supported:** Amazon Q Developer (no native orchestration). Windsurf and Gemini CLI have partial/experimental support — use manual fallback with these.

### Single-Repo Focused Work

For changes isolated to one repo, skip the orchestrator. Open an agent terminal directly in the target repo — it picks up the root `AGENTS.md` standards.

### Updating Shared Context

1. Make changes to `metak-shared/` yourself or have the orchestrator propose them for your review.
2. Notify relevant agents by updating `TASKS.md` or mentioning the change in your next interaction.
3. Never let a worker agent modify `shared/` without explicit approval.
