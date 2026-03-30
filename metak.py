#!/usr/bin/env python3
"""
metak - MetaKitchen CLI

Commands:
    metak setup              Set METAK_HOME env var and add to PATH (one-time)
    metak install            Initialize MetaKitchen template in the current directory
    metak uninstall          Remove MetaKitchen files from the current directory
    metak add <folder>       Register a sub-repo in the workspace and scaffold AGENTS.md

Prerequisites:
    - Python 3.7+
    - No additional packages required

Examples:
    metak setup
    cd my-project && metak install
    metak add frontend
    metak uninstall
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

def _resolve_metak_home():
    """Resolve the MetaKitchen repo root.

    Prefers the METAK_HOME env var (needed when pip-installed, since __file__
    points to site-packages).  Falls back to the directory containing this
    script (works when running directly from the repo).
    """
    env = os.environ.get("METAK_HOME")
    if env:
        p = Path(env)
        if p.is_dir():
            return p
    return Path(__file__).resolve().parent


METAK_HOME = _resolve_metak_home()

# ---------------------------------------------------------------------------
# Template manifest — paths relative to METAK_HOME that `install` copies.
# Directories are copied recursively.  Files are copied as-is.
# ---------------------------------------------------------------------------
TEMPLATE_FILES = [
    # Root-level agent instruction files
    "AGENTS.md",
    "CUSTOM.md",
    "GEMINI.md",
    ".clinerules",
    ".windsurfrules",
    ".gitignore",
    # Tool-specific config dirs / files
    ".claude/CLAUDE.md",
    ".cursor/rules/README.mdc",
    ".amazonq/rules/README.md",
    ".github/copilot-instructions.md",
    ".junie/guidelines.md",
    ".roo/rules/README.md",
    ".vscode/launch.json",
]

# The workspace file is handled separately — its name is derived from the
# target project folder (e.g. "my-project.code-workspace").
WORKSPACE_TEMPLATE = "meta.code-workspace"

TEMPLATE_DIRS = [
    "metak-shared",
    "metak-orchestrator",
]

# Files/dirs that should never be copied
EXCLUDED = {
    ".git",
    ".claude/settings.local.json",
    "metak.py",
    "metakitchen",
    "pyproject.toml",
    "__pycache__",
}

# User-owned files that are created on first install but never overwritten,
# even with --force.  Paths are relative to the install target.
PROTECTED_FILES = {
    "CUSTOM.md",
    "metak-orchestrator/CUSTOM.md",
}

# ---------------------------------------------------------------------------
# AGENTS.md template for sub-repos (used by `metak add`)
# ---------------------------------------------------------------------------
AGENTS_MD_TEMPLATE_FILE = "metak-shared/templates/AGENTS.md.template"
CUSTOM_MD_TEMPLATE_FILE = "metak-shared/templates/CUSTOM.md.template"
CLAUDE_MD_WORKER_TEMPLATE_FILE = "metak-shared/templates/CLAUDE.md.worker.template"

# Inline fallback used when the template file doesn't exist
AGENTS_MD_TEMPLATE_FALLBACK = """\
# {name} Agent Guide

Repo-specific agent instructions for `{name}`.
Read the root `AGENTS.md` first for global rules, project structure, and coding standards.

## Repo Overview

<!-- Describe what this repo does and its role in the system. -->

## Agent Rules

1. Follow all rules in the root `AGENTS.md`.
2. Consult `metak-shared/LEARNED.md` for useful methods, procedures, and tricks discovered during the project. Add new learnings as you discover them.
3. <!-- Add any repo-specific rules here. -->

## Coding Standards

- <!-- Language, framework, and linting conventions specific to this repo. -->
"""


def _load_agents_template(root):
    """Load the AGENTS.md template from the project, falling back to the inline default."""
    template_path = root / AGENTS_MD_TEMPLATE_FILE
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return AGENTS_MD_TEMPLATE_FALLBACK


CUSTOM_MD_TEMPLATE_FALLBACK = """\
# {name} Custom Instructions

<!-- Add your custom instructions for {name} here. -->
"""

CLAUDE_MD_WORKER_TEMPLATE_FALLBACK = """\
You are a **worker** agent operating within the `{name}/` subfolder.

## Before starting work

1. Read `AGENTS.md` in this directory if it exists, for repo-specific instructions.
2. Read `CUSTOM.md` in this directory for project-specific rules set by the orchestrator.
3. Read your task assignment — the orchestrator will have provided it, or you can find it in `{metak_orchestrator_rel}/TASKS.md`.
4. Consult `{metak_shared_rel}/api-contracts/` for interface specs you must conform to.
5. Consult `{metak_shared_rel}/architecture.md` for system boundaries.

## Rules

- Stay within `{name}/`. Do not modify files outside this directory.
- Treat `{metak_shared_rel}/` as **read-only**.
- Never import directly from another repo's source code — use the contracts in `metak-shared/api-contracts/`.
- When done or blocked, update `{metak_orchestrator_rel}/STATUS.md`.
- Follow coding standards in `{metak_shared_rel}/coding-standards.md`.
"""


def _load_custom_template(root):
    """Load the CUSTOM.md template from the project, falling back to the inline default."""
    template_path = root / CUSTOM_MD_TEMPLATE_FILE
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return CUSTOM_MD_TEMPLATE_FALLBACK


def _load_claude_worker_template(root):
    """Load the .claude/CLAUDE.md worker template, falling back to the inline default."""
    template_path = root / CLAUDE_MD_WORKER_TEMPLATE_FILE
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return CLAUDE_MD_WORKER_TEMPLATE_FALLBACK


# ===================================================================
# setup command
# ===================================================================
def cmd_setup(args):
    """Set METAK_HOME as a permanent user environment variable and add to PATH."""
    if args.path:
        metak_home = str(Path(args.path).resolve())
    else:
        # Try candidates in order: cwd first (works after pip install when
        # user runs from the repo), then __file__ parent (works when running
        # the script directly).
        candidates = [Path.cwd(), Path(__file__).resolve().parent]
        metak_home = None
        for candidate in candidates:
            if (candidate / "AGENTS.md").exists() and (candidate / "metak-shared").is_dir():
                metak_home = str(candidate)
                break

        if not metak_home:
            print("Error: cannot auto-detect the MetaKitchen repo location.")
            print("Run from the repo directory, or pass the path explicitly:")
            print("  metak setup --path /path/to/metakitchen")
            sys.exit(1)

    system = platform.system()

    if system == "Windows":
        _setup_windows(metak_home)
    else:
        _setup_unix(metak_home)


def _setup_windows(metak_home):
    """Use setx + PowerShell to persist METAK_HOME and update PATH on Windows."""
    # Set METAK_HOME
    subprocess.run(["setx", "METAK_HOME", metak_home], check=True)
    print("[+] Set METAK_HOME = {}".format(metak_home))

    # Read current user PATH from registry (setx truncates at 1024 chars, so
    # we use PowerShell to read/write the registry directly for PATH).
    read_cmd = (
        '[Environment]::GetEnvironmentVariable("PATH", "User")'
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", read_cmd],
        capture_output=True, text=True,
    )
    current_path = (result.stdout.strip() or "")

    if metak_home.lower() in current_path.lower():
        print("[=] PATH already contains METAK_HOME")
    else:
        new_path = current_path.rstrip(";") + ";" + metak_home if current_path else metak_home
        write_cmd = (
            '[Environment]::SetEnvironmentVariable("PATH", "{}", "User")'.format(
                new_path.replace('"', '`"')
            )
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", write_cmd],
            check=True,
        )
        print("[+] Added METAK_HOME to user PATH")

    print()
    print("Done. Restart your terminal for changes to take effect.")
    print("You can now run `metak` from anywhere.")


def _setup_unix(metak_home):
    """Append METAK_HOME export and PATH update to the user's shell profile."""
    home = Path.home()
    shell = os.environ.get("SHELL", "/bin/bash")

    if "zsh" in shell:
        profile = home / ".zshrc"
    else:
        profile = home / ".bashrc"

    marker = "# metak-setup"
    lines = [
        "",
        marker,
        'export METAK_HOME="{}"'.format(metak_home),
        'export PATH="$METAK_HOME:$PATH"',
    ]

    if profile.exists() and marker in profile.read_text():
        print("[=] {} already configured in {}".format("METAK_HOME", profile))
    else:
        with open(profile, "a") as f:
            f.write("\n".join(lines) + "\n")
        print("[+] Added METAK_HOME to {}".format(profile))

    print()
    print("Done. Run `source {}` or restart your terminal.".format(profile))
    print("You can then run `metak` from anywhere.")


# ===================================================================
# install command
# ===================================================================
def cmd_install(args):
    """Copy MetaKitchen template into the current (or specified) directory."""
    target = Path(args.target).resolve()

    if not target.exists():
        print("Error: target directory '{}' does not exist.".format(target))
        sys.exit(1)

    if target == METAK_HOME:
        print("Error: cannot install into the MetaKitchen repo itself.")
        sys.exit(1)

    print("Installing MetaKitchen template into: {}".format(target))
    print()

    copied = 0
    skipped = 0

    # Copy individual files
    for rel in TEMPLATE_FILES:
        src = METAK_HOME / rel
        dst = target / rel

        if not src.exists():
            continue

        if rel in PROTECTED_FILES and dst.exists():
            print("  [=] {} (protected, skipping)".format(rel))
            skipped += 1
            continue

        if dst.exists() and not args.force:
            print("  [=] {} (exists, skipping)".format(rel))
            skipped += 1
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
        print("  [+] {}".format(rel))
        copied += 1

    # Copy template directories
    for rel in TEMPLATE_DIRS:
        src = METAK_HOME / rel
        dst = target / rel

        if not src.is_dir():
            continue

        if dst.exists() and not args.force:
            print("  [=] {}/ (exists, skipping)".format(rel))
            skipped += 1
            continue

        # Back up protected files inside this directory before --force overwrites it
        saved = {}
        if dst.exists() and args.force:
            for pf in PROTECTED_FILES:
                if pf.startswith(rel + "/"):
                    pf_path = target / pf
                    if pf_path.exists():
                        saved[pf] = pf_path.read_text(encoding="utf-8")
            shutil.rmtree(str(dst))

        shutil.copytree(
            str(src), str(dst),
            ignore=shutil.ignore_patterns(*EXCLUDED),
        )

        # Restore protected files
        for pf, content in saved.items():
            pf_path = target / pf
            pf_path.parent.mkdir(parents=True, exist_ok=True)
            pf_path.write_text(content, encoding="utf-8")
            print("  [=] {} (protected, restored)".format(pf))

        print("  [+] {}/".format(rel))
        copied += 1

    # Copy workspace file, renaming to match the target folder name
    ws_src = METAK_HOME / WORKSPACE_TEMPLATE
    if ws_src.exists():
        ws_name = target.name + ".code-workspace"
        ws_dst = target / ws_name
        if ws_dst.exists() and not args.force:
            print("  [=] {} (exists, skipping)".format(ws_name))
            skipped += 1
        else:
            shutil.copy2(str(ws_src), str(ws_dst))
            print("  [+] {}".format(ws_name))
            copied += 1

    print()
    print("Done. {} copied, {} skipped.".format(copied, skipped))
    if skipped and not args.force:
        print("Use --force to overwrite existing files.")


# ===================================================================
# uninstall command
# ===================================================================
MANIFESTS_FILE = "metakitchen/manifests.json"


def _load_all_known_paths():
    """Load all file and directory paths from every manifest version.

    Returns (files, dirs) where each is a set of relative path strings.
    """
    manifests_path = METAK_HOME / MANIFESTS_FILE
    if not manifests_path.exists():
        # Fall back to current TEMPLATE_FILES / TEMPLATE_DIRS
        return set(TEMPLATE_FILES), set(TEMPLATE_DIRS)

    data = json.loads(manifests_path.read_text(encoding="utf-8"))
    all_files = set()
    all_dirs = set()
    for entry in data:
        all_files.update(entry.get("files", []))
        all_dirs.update(entry.get("dirs", []))
    return all_files, all_dirs


def cmd_uninstall(args):
    """Remove MetaKitchen files from the current (or specified) directory."""
    target = Path(args.target).resolve()

    if not target.exists():
        print("Error: target directory '{}' does not exist.".format(target))
        sys.exit(1)

    if target == METAK_HOME:
        print("Error: cannot uninstall from the MetaKitchen repo itself.")
        sys.exit(1)

    all_files, all_dirs = _load_all_known_paths()

    # Also pick up any *.code-workspace files (name may vary per project)
    for ws in target.glob("*.code-workspace"):
        all_files.add(str(ws.relative_to(target)))

    # Build lists of what actually exists in the target
    files_to_remove = []
    dirs_to_remove = []

    for rel in sorted(all_files):
        p = target / rel
        if p.exists():
            files_to_remove.append(rel)

    for rel in sorted(all_dirs):
        p = target / rel
        if p.is_dir():
            dirs_to_remove.append(rel)

    if not files_to_remove and not dirs_to_remove:
        print("No MetaKitchen files found in: {}".format(target))
        return

    # Show what will be removed
    print("The following MetaKitchen files will be removed from: {}".format(target))
    print()
    for rel in files_to_remove:
        print("  [-] {}".format(rel))
    for rel in dirs_to_remove:
        print("  [-] {}/  (entire directory)".format(rel))
    print()

    if not args.force:
        print("Run with --force to confirm removal.")
        return

    # Remove files
    removed = 0
    for rel in files_to_remove:
        p = target / rel
        p.unlink()
        removed += 1

    # Clean up empty parent directories left behind by file removal
    for rel in files_to_remove:
        parent = (target / rel).parent
        while parent != target:
            try:
                parent.rmdir()  # only succeeds if empty
            except OSError:
                break
            parent = parent.parent

    # Remove directories
    for rel in dirs_to_remove:
        p = target / rel
        if p.is_dir():
            shutil.rmtree(str(p))
            removed += 1

    print("Done. Removed {} items.".format(removed))


# ===================================================================
# add command (original metak.py logic)
# ===================================================================
def cmd_add(args):
    """Register a sub-repo folder in the workspace and scaffold AGENTS.md."""
    folder_name = args.folder.strip("/\\")
    root = Path.cwd()
    folder_path = root / folder_name

    if not folder_path.exists():
        print("Error: '{}' does not exist.".format(folder_name))
        print("Create the folder first, e.g.:")
        print("  git submodule add <url> {}".format(folder_name))
        print("  or: mkdir {}".format(folder_name))
        sys.exit(1)

    if not folder_path.is_dir():
        print("Error: '{}' is not a directory.".format(folder_name))
        sys.exit(1)

    print("Initializing '{}'...".format(folder_name))

    try:
        workspace_path = find_workspace_file(root)
    except (FileNotFoundError, ValueError) as e:
        print("Error: {}".format(e))
        sys.exit(1)

    if add_to_workspace(workspace_path, folder_name):
        print("  [+] Added '{}' to {}".format(folder_name, workspace_path.name))
    else:
        print("  [=] '{}' already in {}".format(folder_name, workspace_path.name))

    if scaffold_agents_md(folder_path, folder_name, root):
        print("  [+] Created {}/AGENTS.md".format(folder_name))
    else:
        print("  [=] {}/AGENTS.md already exists, skipping".format(folder_name))

    if scaffold_custom_md(folder_path, folder_name, root):
        print("  [+] Created {}/CUSTOM.md".format(folder_name))
    else:
        print("  [=] {}/CUSTOM.md already exists, skipping".format(folder_name))

    if scaffold_claude_md(folder_path, folder_name, root):
        print("  [+] Created {}/.claude/CLAUDE.md".format(folder_name))
    else:
        print("  [=] {}/.claude/CLAUDE.md already exists, skipping".format(folder_name))

    print()
    print("Done. Open {} in VS Code.".format(workspace_path.name))


# ---------------------------------------------------------------------------
# Helpers for `add`
# ---------------------------------------------------------------------------
def find_workspace_file(root):
    matches = sorted(root.glob("*.code-workspace"))
    if not matches:
        raise FileNotFoundError(
            "No .code-workspace file found. Run this from a MetaKitchen project root."
        )
    if len(matches) > 1:
        names = ", ".join(m.name for m in matches)
        raise ValueError(
            "Multiple .code-workspace files found: {}. "
            "Remove duplicates or rename to a single file.".format(names)
        )
    return matches[0]


def add_to_workspace(workspace_path, folder_name):
    text = workspace_path.read_text(encoding="utf-8")
    workspace = json.loads(text)

    folders = workspace.setdefault("folders", [])
    existing = {f.get("path") for f in folders}

    if folder_name in existing:
        return False

    folders.append({"path": folder_name})
    workspace_path.write_text(
        json.dumps(workspace, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return True


def scaffold_agents_md(folder_path, folder_name, root):
    target = folder_path / "AGENTS.md"
    if target.exists():
        return False
    template = _load_agents_template(root)
    target.write_text(
        template.format(name=folder_name),
        encoding="utf-8",
    )
    return True


def scaffold_custom_md(folder_path, folder_name, root):
    target = folder_path / "CUSTOM.md"
    if target.exists():
        return False
    template = _load_custom_template(root)
    target.write_text(
        template.format(name=folder_name),
        encoding="utf-8",
    )
    return True


def scaffold_claude_md(folder_path, folder_name, root):
    """Create .claude/CLAUDE.md with worker identity in a sub-repo folder."""
    target = folder_path / ".claude" / "CLAUDE.md"
    if target.exists():
        return False
    # Compute relative paths from the sub-repo to metak-shared and metak-orchestrator
    try:
        rel = folder_path.relative_to(root)
        depth = len(rel.parts)
    except ValueError:
        depth = 1
    prefix = "/".join([".."] * depth)
    metak_shared_rel = prefix + "/metak-shared"
    metak_orchestrator_rel = prefix + "/metak-orchestrator"
    template = _load_claude_worker_template(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        template.format(
            name=folder_name,
            metak_shared_rel=metak_shared_rel,
            metak_orchestrator_rel=metak_orchestrator_rel,
        ),
        encoding="utf-8",
    )
    return True


# ===================================================================
# CLI entry point
# ===================================================================
def main():
    parser = argparse.ArgumentParser(
        prog="metak",
        description="MetaKitchen CLI - scaffold and manage multi-repo AI workspaces",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    # -- setup --
    p_setup = sub.add_parser(
        "setup",
        help="Set METAK_HOME env var and add to PATH (one-time)",
    )
    p_setup.add_argument(
        "--path",
        help="Path to the MetaKitchen repo (auto-detected when running from the repo)",
    )

    # -- install --
    p_install = sub.add_parser(
        "install",
        help="Initialize MetaKitchen template in a directory",
    )
    p_install.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target directory (default: current directory)",
    )
    p_install.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite existing files",
    )

    # -- uninstall --
    p_uninstall = sub.add_parser(
        "uninstall",
        help="Remove MetaKitchen files from a directory",
    )
    p_uninstall.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target directory (default: current directory)",
    )
    p_uninstall.add_argument(
        "--force", "-f",
        action="store_true",
        help="Actually remove files (without this flag, only shows what would be removed)",
    )

    # -- add --
    p_add = sub.add_parser(
        "add",
        help="Register a sub-repo in the workspace and scaffold AGENTS.md",
    )
    p_add.add_argument(
        "folder",
        help="Sub-repo folder name (relative to project root)",
    )

    args = parser.parse_args()

    if args.command == "setup":
        cmd_setup(args)
    elif args.command == "install":
        cmd_install(args)
    elif args.command == "uninstall":
        cmd_uninstall(args)
    elif args.command == "add":
        cmd_add(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
