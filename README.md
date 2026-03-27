# MetaKitchen

MetaKitchen is a language-agnostic scaffold for AI-driven development across multiple repositories. It pre-wires every major AI coding agent to read a single `AGENTS.md`, so whichever agent a developer uses, it picks up the same shared instructions — no extra setup.

## Motivation

AI coding agents are multiplying fast — Claude Code, Cursor, Copilot, Codex, and more — but each has its own convention for discovering project instructions. On a collaborative open-source project, one contributor might use Claude Code while another uses Cursor and a third uses Copilot. Without a shared standard, each person's agent operates in isolation, unaware of the project's architecture, coding standards, or task plan.

MetaKitchen solves this by giving every agent a single entry point (`AGENTS.md`) through their native discovery mechanisms. Write your instructions once; every agent finds them automatically.

The name combines **meta-programming** with **kitchen orchestration** — a head chef (the orchestrator agent) directs multiple cooks (worker agents), each responsible for a different part of the meal, all following the same recipes.

## What You Get

- **Agent pointer files** for 9 AI coding agents (Claude Code, Cursor, GitHub Copilot, Codex CLI, Cline, Roo Code, Junie, Windsurf, Gemini CLI) — all pointing at one `AGENTS.md`.
- **`metak-shared/`** — read-only shared context: architecture docs, coding standards, API contracts, and a domain glossary.
- **`metak-orchestrator/`** — a workspace for a coordinating agent that plans work across repos and spawns worker agents.
- **`meta.code-workspace`** — a VS Code multi-root workspace so all repos appear in one sidebar.
- **`CUSTOM.md`** files for project-specific instructions that won't be overwritten by updates.
- **Updates to the template** — as contributors add improvements to the scaffold code, they can be pulled into existing projects without overwriting custom instructions.


## Quickstart

The instructions below have been tested in Windows 10/11. If you are on a different OS, you may need to adjust the environment variable setup step. 

Please contribute back any OS-specific instructions you find to the documentation!

### 1. Install MetaKitchen (one-time)

Clone this repo and run setup:

```bash
git clone https://github.com/pfriedrich/metakitchen.git
cd metakitchen
pip install -e .
metak setup
```

This sets the `METAK_HOME` environment variable and adds `metak` to your PATH. You only need to do this once.

### 2. Initialize a project

In your project's root directory, run:

```bash
cd my-project
metak install
```

This copies the MetaKitchen template into your project — agent pointer files, `AGENTS.md`, `metak-shared/`, `metak-orchestrator/`, and the workspace file. Existing files are not overwritten (use `--force` to update them, except `CUSTOM.md` files which are always preserved).

### 3. Add sub-repos

Add your repos and register them in the workspace. MetaKitchen supports both submodule and monorepo layouts:

```bash
# Submodule layout (each repo is a separate git repository)
git submodule add https://github.com/your-org/frontend frontend
metak add frontend

# Monorepo layout (all code in one git repository)
mkdir backend
metak add backend
```

You can also have a mix of both — for example, folders for separate services that are part of the same repo as your workspace, and submodules for external dependencies or other components.

Either way, `metak add` registers each folder in `meta.code-workspace` and scaffolds a starter `AGENTS.md` inside it. See [Usage](metakitchen/usage.md) for details on both layouts.

### 4. Open the workspace

```bash
code meta.code-workspace
```

Then edit `AGENTS.md` at the root and fill in `metak-shared/` to describe your project. Any AI agent opened in any sub-repo will automatically pick up those instructions.

## How Orchestration Works

Open one agent session in `metak-orchestrator/` and describe the goal. The orchestrator plans the work, writes a task breakdown to `TASKS.md`, then spawns a worker agent per repo to implement each task — all in the same session.

If your agent doesn't support subagent spawning, the orchestrator will tell you which tasks to run manually and in which repo folder.

## Commands

| Command | Description |
|---|---|
| `metak setup` | Set `METAK_HOME` and add to PATH (one-time) |
| `metak install [target]` | Copy MetaKitchen template into a project directory |
| `metak add <folder>` | Register a sub-repo in the workspace and scaffold its `AGENTS.md` |

## Documentation

See the [metakitchen/](metakitchen/) folder for detailed guides:

- [File Structure](metakitchen/file-structure.md) — layout and what each part is for
- [Usage](metakitchen/usage.md) — workflows and common operations
- [Configuration](metakitchen/configuration.md) — agent pointer files and customization
- [Tips](metakitchen/tips.md) — practical guidance for day-to-day use

## Prerequisites

- **Python 3.7+** — for the `metak` CLI (no extra packages needed)
- **Git** — each sub-repo is its own git repository
- **VS Code** (recommended) — for the multi-root workspace experience

## License

[MIT](metakitchen/LICENSE)
