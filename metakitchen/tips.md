# Tips

- **Always open the `.code-workspace` file**, not individual folders.
- **One agent per terminal, one repo per agent.** Use the orchestrator for cross-repo coordination.
- **Treat `metak-shared/` as a contract boundary.** Changes there are deliberate decisions, not side effects.
- **Keep instructions in `AGENTS.md`**, not scattered across agent-specific config files.
- **`TASKS.md` and `STATUS.md` are plain markdown.** Keep them simple.
- **Git remains per-repo.** The meta-repo structure is a local dev convenience — it doesn't affect CI/CD.
- **Delete what you don't need.** If you're only using one AI agent, remove the other pointer files. If you don't need the orchestrator pattern, remove that folder.
- **`metakitchen/` is documentation only.** Agents don't need to read it — point them at `AGENTS.md`.
