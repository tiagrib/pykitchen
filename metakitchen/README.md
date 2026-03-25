# MetaKitchen Docs

MetaKitchen is a language-agnostic template for AI-driven development across multiple repositories.
Fork or clone it to start a new project, then develop within the scaffolded structure.

## Quickstart

```bash
# 1. Fork or clone this repo
git clone https://github.com/your-org/metakitchen my-project
cd my-project

# 2. Add your first sub-repo as a git submodule
git submodule add https://github.com/your-org/your-repo your-repo

# 3. Register it in the workspace and scaffold its AGENTS.md
python metak.py your-repo

# 4. Add and register additional submodules
...

# 4. Open the workspace in VS Code
code meta.code-workspace
```

Then edit the `AGENTS.md` at the root folder, and `metak-shared/` to describe your project. Any supported AI agent opened in any sub-repo will automatically pick up those instructions.

## How Orchestration Works

Open one agent session in `metak-orchestrator/` and describe the goal. The orchestrator plans the work, writes a task breakdown to `TASKS.md`, then spawns a worker agent per repo to implement each task — all in the same session. You stay at the orchestrator level throughout; you don't open or manage per-repo sessions yourself.

If your agent doesn't support subagent spawning, the orchestrator will tell you which tasks to run manually and in which repo folder. See [Usage](usage.md) for details.

## Index

- [File Structure](file-structure.md) — layout of the meta-repo and what each part is for
- [Usage](usage.md) — getting started and common workflows
- [Configuration](configuration.md) — how agent pointer files work and how to customize them
- [Tips](tips.md) — practical guidance for day-to-day use
