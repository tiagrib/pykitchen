# Usage

## What MetaKitchen Provides

MetaKitchen is a scaffold, not a framework. It gives you:

- **A folder structure** — `metak-orchestrator/` for coordination, `metak-shared/` for cross-repo context, and placeholders for your sub-repos.
- **Agent pointer files** — every major AI coding agent has its own config file convention (`.claude/CLAUDE.md`, `.cursor/rules/README.mdc`, `.windsurfrules`, etc.). MetaKitchen pre-wires all of them to point at a single `AGENTS.md`, so whichever agent a developer uses, it reads the same instructions.
- **`AGENTS.md`** — a starting template. **You are expected to edit this** to reflect your project's actual structure, rules, and coding standards. The pointer files stay as-is; only `AGENTS.md` needs to grow with your project.

The goal is that any agent, on any machine, opened in any sub-repo, automatically picks up the same shared instructions without any extra setup.

## Prerequisites

- **Python 3.7+** — for the `metak` CLI (no extra packages needed)
- **Git** — each sub-repo is its own git repository
- **VS Code** (or VS Code Insiders) with an AI coding agent extension (recommended)

## Git Integration

Git is highly recommended when using metak to ensure nondestructive changes. The CLI checks for git at every step:

- **`metak` (no args) and `metak setup`** — warn if git is not available.
- **`metak install`, `metak add`, `metak uninstall`** — error and stop if git is not available. Pass `--skip-git` to proceed without git.
- **Dirty-tree check** — before `install`, `add`, or `uninstall` modifies files, metak checks for uncommitted changes. If the working tree is dirty, it asks you to commit or stash first. Pass `--force` to bypass the warning, or `--skip-git` to skip all git checks.
- **Auto-commit** — `metak install` and `metak add` accept `--commit` to automatically stage and commit only the files metak touched. `--commit` is mutually exclusive with `--skip-git` since it requires git to work.

## Installation

### One-time setup

Clone the MetaKitchen repository and run setup:

```bash
git clone https://github.com/pfriedrich/metakitchen.git
cd metakitchen
metak setup
```

This does two things:
1. Sets the `METAK_HOME` environment variable pointing to the MetaKitchen repo.
2. Adds the MetaKitchen directory to your PATH so `metak` is available everywhere.

If you're running `metak setup` from a different directory, pass `--path` to point at the MetaKitchen repo explicitly:

```bash
metak setup --path /path/to/metakitchen
```

`metak setup` will warn if git is not found on your PATH. Pass `--skip-git` to suppress the warning.

On Windows this uses `setx` and the registry. On macOS/Linux it appends to your shell profile (`.zshrc` or `.bashrc`). You may need to restart your terminal for the changes to take effect.

### Initialize a project

Navigate to your project's root directory and run:

```bash
cd my-project
metak install
```

This copies the MetaKitchen template into your project:
- Agent pointer files (`.claude/CLAUDE.md` with role routing, `.cursor/rules/`, etc.)
- `AGENTS.md` and `CUSTOM.md`
- `metak-shared/` with overview, architecture, api-contracts, coding standards, glossary, and LEARNED.md templates
- `metak-orchestrator/` with TASKS.md, STATUS.md, EPICS.md, DECISIONS.md, and orchestrator CLAUDE.md
- `<project>.code-workspace` for VS Code multi-root workspace (named after your folder)
- `GEMINI.md` and other agent-specific files

Existing files are **not overwritten** unless you pass `--force`. `CUSTOM.md` files are **never overwritten**, even with `--force` — they are yours to customize.

To automatically commit the scaffolded files:

```bash
metak install --commit
```

This stages only the files metak created and commits them with the message `chore: add metakitchen scaffold`. `--commit` requires git and cannot be combined with `--skip-git`.

Pass `--skip-git` to skip all git checks (availability and dirty-tree):

```bash
metak install --skip-git
```

You can also install into a specific directory:

```bash
metak install /path/to/my-project
```

### Uninstall MetaKitchen from a project

To remove all MetaKitchen files from a project, run:

```bash
metak uninstall
```

By default this is a **dry run** — it shows which files and directories would be removed without deleting anything. When you're satisfied with the preview, pass `--force` to actually remove them:

```bash
metak uninstall --force
```

You can also target a specific directory:

```bash
metak uninstall /path/to/my-project --force
```

This removes all template files, agent pointer files, `metak-shared/`, `metak-orchestrator/`, and the `.code-workspace` file. Empty parent directories are cleaned up automatically.

Pass `--skip-git` to skip git checks:

```bash
metak uninstall --force --skip-git
```

### Open the workspace

```bash
code my-project.code-workspace
```

Always open the `.code-workspace` file, not individual folders. This gives you:
- All repos visible in the Explorer sidebar
- Independent git tracking per repo
- Unified search across all codebases
- Shared settings and launch configs

### Customize for your project

1. Edit `AGENTS.md` to reflect your project's structure, rules, and coding standards.
2. Fill in `metak-shared/overview.md`, `metak-shared/architecture.md`, `metak-shared/coding-standards.md`, and `metak-shared/glossary.md` as your project takes shape.
3. Edit `CUSTOM.md` for any project-wide preferences (tech stack, deployment targets, team conventions).
4. Define API contracts in `metak-shared/api-contracts/` (one file per contract) as your system's interfaces become clear.

## Adding a Sub-Repo

MetaKitchen supports two project layouts: **submodules** (each repo is an independent git repository) and **monorepo** (all code lives in one git repository). The agent instructions, orchestration, and workspace features work identically in both — the only difference is how you manage git.

### Option A: Submodule layout

Each sub-repo is a git submodule — a separate git repository tracked at a fixed commit inside your project.

```bash
git submodule add <repo-url> <folder-name>
# e.g.
git submodule add https://github.com/your-org/frontend frontend
```

This creates the folder, clones the repo into it, and registers it in `.gitmodules`. Then run `metak add` to finish the setup:

```bash
metak add frontend
```

Commit everything:

```bash
git add .gitmodules frontend *.code-workspace
git commit -m "chore: add frontend submodule"
```

#### Submodule operations

Clone a project with submodules:

```bash
git clone --recurse-submodules <project-url>
# or, if already cloned:
git submodule update --init --recursive
```

Update a submodule to its latest commit:

```bash
cd <folder-name>
git pull origin main
cd ..
git add <folder-name>
git commit -m "chore: bump <folder-name> to latest"
```

Remove a submodule:

```bash
git submodule deinit -f <folder-name>
git rm <folder-name>
rm -rf .git/modules/<folder-name>
git commit -m "chore: remove <folder-name> submodule"
```

### Option B: Monorepo layout

If all your code lives in a single git repository, just create the folder and register it:

```bash
mkdir backend
metak add backend
```

That's it. No submodule commands needed. Git tracks everything in one repository, and `metak add` handles the workspace registration and `AGENTS.md` scaffolding the same way.

This works well when:
- You want a single commit history across all services
- Your CI/CD already handles a monorepo
- You don't need independent version control per service

### What `metak add` does

Regardless of layout, `metak add <folder>` will:
- Add the folder to the `.code-workspace` file so it appears in the VS Code Explorer sidebar
- Create a starter `AGENTS.md` in the folder if one doesn't already exist
- Create a `CUSTOM.md` for repo-specific instructions
- Create a `.claude/CLAUDE.md` with worker identity (scoped to that folder, with correct relative paths to metak-shared and metak-orchestrator)

Pass `--force` to overwrite existing `AGENTS.md` and `.claude/CLAUDE.md` files (useful after a MetaKitchen update). `CUSTOM.md` is always protected and never overwritten, even with `--force`.

To automatically commit the changes:

```bash
metak add frontend --commit
```

This stages only the files metak touched and commits them with the message `chore: add frontend sub-repo`. `--commit` requires git and cannot be combined with `--skip-git`.

Pass `--skip-git` to skip all git checks:

```bash
metak add frontend --skip-git
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
3. Never let a worker agent modify `metak-shared/` without explicit approval.
4. When any agent discovers useful methods, procedures, or tricks during development or testing, they should document them in `metak-shared/LEARNED.md` so the knowledge is available to all agents and future projects.

## Feeding Back Customizations

After using MetaKitchen in a project for a while, you may find that some of your customizations — new agent rules, coding standards, learned tricks — are useful enough to be part of the default templates for all future projects.

The `metak feedback` command analyzes your project's customizations and uses the Claude Code CLI to identify what's worth upstreaming:

```bash
cd my-project
metak feedback
```

This will:
1. Diff your `AGENTS.md` and `metak-orchestrator/AGENTS.md` against the originals in `METAK_HOME`
2. Collect all `CUSTOM.md` files (root, orchestrator, sub-repos) that have real content
3. Collect `metak-shared/LEARNED.md` entries
4. Scan sub-repo `AGENTS.md` and `CUSTOM.md` files for additions beyond the template boilerplate
5. Send everything to Claude CLI for analysis of what could improve the templates

**Prerequisites:**
- **Git** must be available
- **METAK_HOME** must have a clean working tree (commit or stash first)
- **Claude Code CLI** must be installed (`npm install -g @anthropic-ai/claude-code`)

To preview the prompt without sending it to Claude:

```bash
metak feedback --dry-run
```

You can also target a specific project directory:

```bash
metak feedback /path/to/my-project
```

The command is read-only — it never modifies any files. After reviewing Claude's suggestions, you manually update the templates in `METAK_HOME`.

## Updating MetaKitchen

To get the latest MetaKitchen templates and tooling:

```bash
cd $METAK_HOME    # or wherever you cloned metakitchen
git pull
```

Then re-install in any project you want to update:

```bash
cd my-project
metak install --force
```

This updates all template files while preserving your `CUSTOM.md` files.
