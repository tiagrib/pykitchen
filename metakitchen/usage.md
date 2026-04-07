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
- **Claude Code CLI** (optional) — required only for `metak feedback` (`npm install -g @anthropic-ai/claude-code`)

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

The `metak feedback` command analyzes your project's customizations and uses the Claude Code CLI to identify what's worth upstreaming into the main templates.

### Prerequisites

- **Git** — must be available on PATH
- **METAK_HOME** — must have a clean working tree (commit or stash first, so any template updates are cleanly tracked)
- **Claude Code CLI** — must be installed (`npm install -g @anthropic-ai/claude-code`)

### Basic usage

```bash
cd my-project
metak feedback
```

This runs a two-phase process:

**Phase 1 — Analysis.** metak scans the project for customizations and sends them to Claude CLI (in non-interactive print mode) for analysis. Specifically, it:

1. Diffs `AGENTS.md`, `metak-orchestrator/AGENTS.md`, and `metak-shared/coding-standards.md` against the originals in `METAK_HOME`
2. Collects `CUSTOM.md` files (root, orchestrator, and all sub-repos) that have real content beyond the template placeholder
3. Collects `metak-shared/LEARNED.md` if it has entries
4. Collects sub-repo `AGENTS.md` files for additions beyond template boilerplate
5. Sends everything to Claude CLI, which returns suggestions for what to upstream

The analysis output is printed to the terminal and cached to `.metak-feedback-cache.md` in `METAK_HOME` (this file is gitignored).

**Phase 2 — Apply.** After the analysis, metak asks:

```
Apply these suggestions to METAK_HOME templates? [y/N]
```

If you answer **y**, metak launches an interactive Claude Code session in the `METAK_HOME` directory with the analysis loaded as context. Claude will propose edits to the template files and wait for your approval on each change. You remain in control — review, approve, or reject each edit, then exit the session when done.

If you answer **n** (or press Enter), the suggestions remain visible in the terminal for manual reference.

### Flags

**`--dry-run`** — Show the prompt that would be sent to Claude CLI without executing it. Useful for inspecting what data is being collected:

```bash
metak feedback --dry-run
```

**`--cached`** — Skip the analysis phase and go straight to the apply prompt using the previously cached results. This avoids re-running the (slower) analysis when you've already reviewed the suggestions and want to apply them:

```bash
metak feedback --cached
```

If no cached feedback exists, the command exits with an error and instructs you to run `metak feedback` first.

### Targeting a specific project

You can point feedback at a project directory instead of using the current directory:

```bash
metak feedback /path/to/my-project
```

### What gets compared

| Source | Method | Rationale |
|--------|--------|-----------|
| `AGENTS.md` | Diff vs METAK_HOME original | Focuses on what the project actually changed |
| `metak-orchestrator/AGENTS.md` | Diff vs original | Same — identifies orchestrator instruction changes |
| `metak-shared/coding-standards.md` | Diff vs original | Catches added coding conventions |
| `CUSTOM.md` (root) | Full content | No meaningful original — template is a placeholder |
| `metak-orchestrator/CUSTOM.md` | Full content | Same |
| `metak-shared/LEARNED.md` | Full content | Accumulated learnings worth reviewing for upstream |
| Sub-repo `AGENTS.md` files | Full content | Generated from template — Claude is told to look beyond boilerplate |
| Sub-repo `CUSTOM.md` files | Full content | Entirely user-written |

Files that contain only the template placeholder text (headings and HTML comments with no real instructions) are skipped automatically.

## Updating a Project from Latest Templates

When the MetaKitchen templates are improved (new agent rules, better structure, updated conventions), the `metak update` command helps incorporate those improvements into an existing project without losing your customizations.

### Basic usage

```bash
cd my-project
metak update
```

This runs a multi-step process:

**Step 1 — Pull.** metak runs `git pull` in `METAK_HOME` to fetch the latest template changes.

**Step 2 — Compare.** metak diffs the updated templates against the project's current files. It also collects the project's `CUSTOM.md` files, `LEARNED.md`, and sub-repo files as context so Claude knows what to preserve.

**Step 3 — Analyze.** The diffs and context are sent to Claude CLI (in print mode) which identifies what template improvements should be applied and how they interact with existing project customizations. The analysis is cached to `.metak-update-cache.md` in `METAK_HOME`.

**Step 4 — Apply.** metak asks:

```
Apply these suggestions to project templates? [y/N]
```

If you answer **y**, metak launches an interactive Claude Code session in the project directory. Claude proposes edits to the project files, merging template improvements alongside your existing customizations, and waits for approval on each change.

### Prerequisites

- **Git** — must be available on PATH
- **METAK_HOME** — must have a clean working tree
- **Project** — must have a clean working tree (since files will be modified)
- **Claude Code CLI** — must be installed (`npm install -g @anthropic-ai/claude-code`)

### Flags

**`--skip-pull`** — Skip the `git pull` step and use METAK_HOME's current state:

```bash
metak update --skip-pull
```

**`--force`** — Analyze even if `git pull` reports no new changes (useful if you previously pulled but didn't run update):

```bash
metak update --force
```

**`--dry-run`** — Show the prompt that would be sent to Claude CLI without executing it:

```bash
metak update --dry-run
```

**`--cached`** — Skip the pull and analysis phases, go straight to the apply prompt using previously cached results:

```bash
metak update --cached
```

### Comparison with `metak install --force`

`metak install --force` is a blunt tool — it overwrites all template files with the latest versions (except protected `CUSTOM.md` files). This is fine for a fresh project, but for a project with customized `AGENTS.md` or `coding-standards.md`, it would erase those customizations.

`metak update` is the smart alternative: it uses Claude to merge template improvements into your existing files, preserving your project-specific additions. Use `install --force` for initial setup or full resets; use `update` for incremental improvements.

## Manual Template Update

If you prefer to update templates manually without Claude:

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
