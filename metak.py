#!/usr/bin/env python3
"""
metak - MetaKitchen CLI

Commands:
    metak setup              Set METAK_HOME env var and add to PATH (one-time)
    metak install            Initialize MetaKitchen template in the current directory
    metak uninstall          Remove MetaKitchen files from the current directory
    metak add <folder>       Register a sub-repo in the workspace and scaffold AGENTS.md
    metak feedback           Analyze project customizations and suggest template improvements
    metak update             Pull latest templates and suggest project updates

Prerequisites:
    - Python 3.7+
    - No additional packages required
    - Claude Code CLI required for `feedback` and `update` (npm install -g @anthropic-ai/claude-code)

Examples:
    metak setup
    cd my-project && metak install
    metak add frontend
    metak feedback
    metak feedback --cached
    metak update
    metak update --cached
    metak uninstall
"""

import argparse
import difflib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

__version__ = "0.1.0"
__author__ = "Tiago Ribeiro"
__license__ = "MIT"

# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------
def git_available():
    """Return True if git is found on PATH."""
    try:
        subprocess.run(
            ["git", "--version"],
            capture_output=True, check=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def git_has_uncommitted(target):
    """Return True if the working tree at *target* has uncommitted changes.

    Only meaningful inside a git repository — returns False if *target*
    is not tracked by git.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=str(target),
        )
        return bool(result.stdout.strip())
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def git_commit_files(target, paths, message):
    """Stage *paths* (relative to *target*) and commit with *message*.

    Paths that are covered by .gitignore are silently skipped.
    Returns True on success, False on failure (or if nothing to commit).
    """
    str_paths = [str(p) for p in paths]

    # Filter out gitignored paths so `git add` doesn't fail.
    try:
        result = subprocess.run(
            ["git", "check-ignore", "--"] + str_paths,
            capture_output=True, text=True, cwd=str(target),
        )
        ignored = set(result.stdout.strip().splitlines())
    except (FileNotFoundError, subprocess.CalledProcessError):
        ignored = set()

    stageable = [p for p in str_paths if p not in ignored]
    if ignored:
        for p in sorted(ignored):
            print("  [=] {} (gitignored, skipping commit)".format(p))

    if not stageable:
        print("Nothing to commit (all changed files are gitignored).")
        return False

    try:
        subprocess.run(
            ["git", "add", "--"] + stageable,
            check=True, cwd=str(target),
        )
        subprocess.run(
            ["git", "commit", "-m", message],
            check=True, cwd=str(target),
        )
        return True
    except subprocess.CalledProcessError as exc:
        print("Warning: git commit failed: {}".format(exc))
        return False


GIT_RECOMMENDED_MSG = (
    "Git is highly recommended when using metak to ensure nondestructive changes."
)


def _check_git_or_warn():
    """Warn if git is not available.  Used by `setup` and bare `metak`."""
    if not git_available():
        print("Warning: git is not available on PATH.")
        print(GIT_RECOMMENDED_MSG)
        print()


def _check_git_or_exit(skip_git):
    """Error and exit if git is not available, unless *skip_git* is True."""
    if skip_git:
        return
    if not git_available():
        print("Error: git is not available on PATH.")
        print(GIT_RECOMMENDED_MSG)
        print("Pass --skip-git to proceed without git.")
        sys.exit(1)


def _check_dirty_tree(target, skip_git, force):
    """Warn about uncommitted changes.  Exits unless *skip_git* or *force*."""
    if skip_git or force:
        return
    if git_has_uncommitted(target):
        print("Warning: there are uncommitted changes in {}.".format(target))
        print("Commit or stash your changes before running metak to avoid mixing")
        print("your work with scaffold changes.")
        print("Pass --force to proceed anyway, or --skip-git to skip all git checks.")
        sys.exit(1)


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
    if not args.skip_git:
        _check_git_or_warn()

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
    skip_git = args.skip_git
    commit = args.commit
    target = Path(args.target).resolve()

    if commit and skip_git:
        print("Error: --commit and --skip-git are mutually exclusive.")
        print("--commit requires git to stage and commit files.")
        sys.exit(1)

    _check_git_or_exit(skip_git)
    _check_dirty_tree(target, skip_git, args.force)

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
    touched = []  # relative paths of files created/updated (for --commit)

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
        touched.append(rel)
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
        touched.append(rel)
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
            touched.append(ws_name)
            copied += 1

    print()
    print("Done. {} copied, {} skipped.".format(copied, skipped))
    if skipped and not args.force:
        print("Use --force to overwrite existing files.")

    if commit and touched:
        print()
        if git_commit_files(target, touched, "chore: add metakitchen scaffold"):
            print("Committed: chore: add metakitchen scaffold")
    elif commit and not touched:
        print("Nothing to commit (no files were changed).")


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
    skip_git = args.skip_git
    target = Path(args.target).resolve()

    _check_git_or_exit(skip_git)
    _check_dirty_tree(target, skip_git, args.force)

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
    skip_git = args.skip_git
    commit = args.commit
    folder_name = args.folder.strip("/\\")
    force = args.force
    root = Path.cwd()
    folder_path = root / folder_name

    if commit and force:
        print("Error: --commit and --force are mutually exclusive.")
        print("--commit requires a clean working tree and will not commit your own code.")
        sys.exit(1)

    _check_git_or_exit(skip_git)
    _check_dirty_tree(root, skip_git, force)

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
    touched = []  # relative paths for --commit

    try:
        workspace_path = find_workspace_file(root)
    except (FileNotFoundError, ValueError) as e:
        print("Error: {}".format(e))
        sys.exit(1)

    if add_to_workspace(workspace_path, folder_name):
        print("  [+] Added '{}' to {}".format(folder_name, workspace_path.name))
        touched.append(str(workspace_path.relative_to(root)))
    else:
        print("  [=] '{}' already in {}".format(folder_name, workspace_path.name))

    if scaffold_agents_md(folder_path, folder_name, root, force=force):
        verb = "Replaced" if force else "Created"
        print("  [+] {} {}/AGENTS.md".format(verb, folder_name))
        touched.append("{}/AGENTS.md".format(folder_name))
    else:
        print("  [=] {}/AGENTS.md already exists, skipping".format(folder_name))

    if scaffold_custom_md(folder_path, folder_name, root):
        print("  [+] Created {}/CUSTOM.md".format(folder_name))
        touched.append("{}/CUSTOM.md".format(folder_name))
    else:
        print("  [=] {}/CUSTOM.md already exists, skipping (protected)".format(folder_name))

    if scaffold_claude_md(folder_path, folder_name, root, force=force):
        verb = "Replaced" if force else "Created"
        print("  [+] {} {}/.claude/CLAUDE.md".format(verb, folder_name))
        touched.append("{}/.claude/CLAUDE.md".format(folder_name))
    else:
        print("  [=] {}/.claude/CLAUDE.md already exists, skipping".format(folder_name))

    print()
    print("Done. Open {} in VS Code.".format(workspace_path.name))

    if commit and touched:
        print()
        msg = "chore: add {} sub-repo".format(folder_name)
        if git_commit_files(root, touched, msg):
            print("Committed: {}".format(msg))
    elif commit and not touched:
        print("Nothing to commit (no files were changed).")


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


def _strip_jsonc(text):
    """Strip comments and trailing commas so strict JSON can parse VS Code JSONC files."""
    import re
    # Tokenize: match strings, single-line comments, block comments, or other chars.
    # This ensures we never modify content inside quoted strings.
    token_re = re.compile(
        r'"(?:[^"\\]|\\.)*"'   # double-quoted string
        r"|'(?:[^'\\]|\\.)*'"  # single-quoted string
        r'|//[^\n]*'           # single-line comment
        r'|/\*.*?\*/'          # block comment
        r'|[^"\'/]+',          # everything else
        re.DOTALL,
    )
    result = []
    for m in token_re.finditer(text):
        tok = m.group()
        if tok.startswith('//') or tok.startswith('/*'):
            continue  # drop comments
        result.append(tok)
    text = ''.join(result)
    # Remove trailing commas before } or ]
    text = re.sub(r',\s*([}\]])', r'\1', text)
    return text


def add_to_workspace(workspace_path, folder_name):
    text = workspace_path.read_text(encoding="utf-8")
    workspace = json.loads(_strip_jsonc(text))

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


def scaffold_agents_md(folder_path, folder_name, root, *, force=False):
    target = folder_path / "AGENTS.md"
    if target.exists() and not force:
        return False
    template = _load_agents_template(root)
    target.write_text(
        template.format(name=folder_name),
        encoding="utf-8",
    )
    return True


def scaffold_custom_md(folder_path, folder_name, root, *, force=False):
    target = folder_path / "CUSTOM.md"
    if target.exists() and not force:
        return False
    template = _load_custom_template(root)
    target.write_text(
        template.format(name=folder_name),
        encoding="utf-8",
    )
    return True


def scaffold_claude_md(folder_path, folder_name, root, *, force=False):
    """Create .claude/CLAUDE.md with worker identity in a sub-repo folder."""
    target = folder_path / ".claude" / "CLAUDE.md"
    if target.exists() and not force:
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
# feedback command
# ===================================================================

# Cached feedback analysis — one per METAK_HOME, gitignored.
FEEDBACK_CACHE_FILE = ".metak-feedback-cache.md"

# Files in the target project that can be diffed against their METAK_HOME originals.
DIFFABLE_FILES = [
    "AGENTS.md",
    "metak-orchestrator/AGENTS.md",
    "metak-shared/coding-standards.md",
]


def _compute_diff(original, modified, label):
    """Return a unified diff string between two files, or empty string if identical."""
    orig_lines = original.read_text(encoding="utf-8").splitlines(keepends=True)
    mod_lines = modified.read_text(encoding="utf-8").splitlines(keepends=True)
    diff = difflib.unified_diff(
        orig_lines, mod_lines,
        fromfile="original/" + label,
        tofile="project/" + label,
    )
    return "".join(diff)


def _is_placeholder_only(content):
    """Return True if the content is only the template placeholder (no real instructions)."""
    stripped = content.strip()
    # Empty or only HTML comments and headings — no actionable content
    import re
    without_comments = re.sub(r"<!--.*?-->", "", stripped, flags=re.DOTALL)
    without_headings = re.sub(r"^#+\s+.*$", "", without_comments, flags=re.MULTILINE)
    return not without_headings.strip()


def _get_workspace_subrepo_folders(target):
    """Return a list of sub-repo folder names from the workspace file.

    Excludes '.', 'metak-shared', and 'metak-orchestrator' since those are
    metak infrastructure, not user sub-repos.
    """
    try:
        ws_path = find_workspace_file(target)
    except (FileNotFoundError, ValueError):
        return []

    text = ws_path.read_text(encoding="utf-8")
    workspace = json.loads(_strip_jsonc(text))
    infra = {".", "./metak-shared", "./metak-orchestrator",
             "metak-shared", "metak-orchestrator"}
    folders = []
    for entry in workspace.get("folders", []):
        path = entry.get("path", "")
        if path in infra:
            continue
        # Normalise ./folder to folder
        clean = path.lstrip("./").rstrip("/")
        if clean:
            folders.append(clean)
    return folders


def _build_feedback_prompt(diffs, customs, subrepo_files, learned_content):
    """Assemble the prompt that will be sent to Claude CLI."""
    sections = []

    sections.append("""\
You are analyzing customizations made to MetaKitchen scaffold files in a project.
MetaKitchen installs agent instructions (AGENTS.md, CUSTOM.md) into projects to
guide AI coding agents.

Your task: identify instructions, rules, or patterns in the project's customized
files that could be valuable to feed back into the main MetaKitchen's AGENTS.md template so
ALL future projects benefit.

FOCUS ON:
- New rules or conventions that are generally applicable (not project-specific)
- Improved wording or structure for existing instructions
- New agent behaviors that would benefit most projects
- Coding standards or workflow improvements worth standardizing
- Learned methods, procedures, or tricks that are broadly useful
- Projects' CUSTOM.md files and modifications to AGENTS.md that can be consolidated into the main AGENTS.md template


IGNORE:
- Project-specific details (API endpoints, team names, tech stack choices)
- Customizations that only make sense for this particular project
- Content that is clearly placeholder or boilerplate""")

    if diffs:
        sections.append("\n═══ DIFFS FROM ORIGINAL TEMPLATES ═══")
        for label, diff_text in diffs.items():
            sections.append("\n### {}\n```diff\n{}\n```".format(label, diff_text.rstrip()))

    if customs:
        sections.append("\n═══ CUSTOM INSTRUCTION FILES (user-created, no original template) ═══")
        for label, content in customs.items():
            sections.append("\n### {}\n```markdown\n{}\n```".format(label, content.rstrip()))

    if subrepo_files:
        sections.append(
            "\n═══ SUB-REPO AGENT FILES ═══\n"
            "(Generated from a template — look for additions beyond the standard\n"
            "boilerplate sections: Repo Overview, Agent Rules, Coding Standards)"
        )
        for label, content in subrepo_files.items():
            sections.append("\n### {}\n```markdown\n{}\n```".format(label, content.rstrip()))

    if learned_content:
        sections.append("\n═══ LEARNED.md (discovered methods and tricks) ═══")
        sections.append("\n```markdown\n{}\n```".format(learned_content.rstrip()))

    sections.append("""
═══════════════════════════

For each suggestion, provide:
1. Which template file to update (e.g., AGENTS.md, CUSTOM.md.template, coding-standards.md, LEARNED.md)
2. What to add or change (be specific)
3. Why it's generally useful across projects
4. Suggested wording for the template

If nothing is worth upstreaming, say so explicitly.""")

    return "\n".join(sections)


def _invoke_claude_print(claude_bin, prompt):
    """Invoke Claude CLI in print mode, returning its output."""
    result = subprocess.run(
        [claude_bin, "-p"],
        input=prompt,
        encoding="utf-8",
        capture_output=True,
    )
    return result.stdout or ""


APPLY_PROMPT_TEMPLATE = """\
You are updating MetaKitchen template files based on feedback from a project.
The analysis below identifies instructions, rules, and patterns from a real
project that could improve the default templates for ALL future projects.

Your working directory is the MetaKitchen repo root. The template files you
may edit include:

- AGENTS.md — root agent instructions (copied to every project)
- CUSTOM.md — root custom instructions template
- metak-orchestrator/AGENTS.md — orchestrator agent instructions
- metak-shared/coding-standards.md — shared coding standards
- metak-shared/LEARNED.md — discovered methods and tricks
- metak-shared/templates/AGENTS.md.template — template for sub-repo AGENTS.md
- metak-shared/templates/CUSTOM.md.template — template for sub-repo CUSTOM.md

Rules:
- Only apply changes that are GENERALLY useful across projects.
- Skip anything project-specific (tech stack, team names, endpoints).
- Preserve existing template structure and placeholder variables ({{name}}, etc.).
- Show me each proposed change and wait for my approval before editing.

═══ ANALYSIS FROM PROJECT ═══

{}"""


def _invoke_claude_interactive(claude_bin, system_prompt, initial_message, cwd):
    """Launch Claude CLI interactively in the given directory.

    The system prompt is written to a temp file and passed via
    --append-system-prompt-file to avoid command-line length limits.
    *initial_message* is the first user message that kicks off the session.
    """
    import tempfile
    fd, prompt_path = tempfile.mkstemp(suffix=".md", prefix="metak-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(system_prompt)
        subprocess.run(
            [
                claude_bin,
                "--append-system-prompt-file", prompt_path,
                initial_message,
            ],
            cwd=str(cwd),
        )
    finally:
        try:
            os.unlink(prompt_path)
        except OSError:
            pass


def _prompt_and_apply(claude_bin, analysis, apply_template, initial_message,
                      target_dir, target_label):
    """Ask the user whether to apply suggestions, then launch interactive session.

    *apply_template* is a format string with one ``{}`` for the analysis text.
    *target_dir* is the working directory for the interactive session.
    *target_label* is a human-readable name shown in the prompt (e.g. "METAK_HOME").
    """
    print()
    try:
        answer = input("Apply these suggestions to {} templates? [y/N] "
                       .format(target_label)).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if answer not in ("y", "yes"):
        print("Skipped. You can review the suggestions above and apply them manually.")
        return

    print()
    print("Launching interactive Claude session in {} ({})...".format(
        target_label, target_dir))
    print("Review and approve each change. Exit when done.")
    print()
    system_prompt = apply_template.format(analysis)
    _invoke_claude_interactive(claude_bin, system_prompt, initial_message, target_dir)


def cmd_feedback(args):
    """Analyze project customizations and suggest upstream improvements."""
    target = Path(args.target).resolve()

    # -- Pre-flight checks --------------------------------------------------
    metak_home = _resolve_metak_home()

    if not target.exists():
        print("Error: target directory '{}' does not exist.".format(target))
        sys.exit(1)

    if target == metak_home:
        print("Error: cannot run feedback on the MetaKitchen repo itself.")
        sys.exit(1)

    # Git must be available
    if not git_available():
        print("Error: git is not available on PATH.")
        print(GIT_RECOMMENDED_MSG)
        sys.exit(1)

    # METAK_HOME must have a clean working tree
    if git_has_uncommitted(metak_home):
        print("Error: METAK_HOME has uncommitted changes.")
        print("Please commit or stash changes in {} before running feedback,".format(metak_home))
        print("so any template updates are cleanly tracked.")
        sys.exit(1)

    # Claude CLI must be available
    claude_bin = shutil.which("claude")
    if not claude_bin:
        print("Error: Claude Code CLI is not installed.")
        print()
        print("Install it with:")
        print("  npm install -g @anthropic-ai/claude-code")
        print()
        print("For more info: https://docs.anthropic.com/en/docs/claude-code/overview")
        sys.exit(1)

    # -- Cached mode: skip analysis, go straight to apply --------------------
    if args.cached:
        cache_path = metak_home / FEEDBACK_CACHE_FILE
        if not cache_path.exists():
            print("Error: no cached feedback found at {}".format(cache_path))
            print("Run `metak feedback` first to generate the analysis.")
            sys.exit(1)
        analysis = cache_path.read_text(encoding="utf-8")
        print("Using cached feedback from {}".format(cache_path))
        print()
        print(analysis)
        _prompt_and_apply(
            claude_bin, analysis, APPLY_PROMPT_TEMPLATE,
            "Apply the feedback suggestions from the system prompt. "
            "Show each proposed change and ask for approval before editing.",
            metak_home, "METAK_HOME",
        )
        return

    # -- Collect diffs -------------------------------------------------------
    print("Scanning project customizations in: {}".format(target))
    print()

    diffs = {}
    for rel_path in DIFFABLE_FILES:
        original = metak_home / rel_path
        modified = target / rel_path
        if original.exists() and modified.exists():
            diff_text = _compute_diff(original, modified, rel_path)
            if diff_text:
                diffs[rel_path] = diff_text
                print("  [~] {} (modified)".format(rel_path))
            else:
                print("  [=] {} (unchanged)".format(rel_path))
        elif modified.exists():
            print("  [?] {} (no original to compare)".format(rel_path))
        else:
            print("  [-] {} (not present)".format(rel_path))

    # -- Collect CUSTOM.md files ---------------------------------------------
    customs = {}

    # Root CUSTOM.md
    root_custom = target / "CUSTOM.md"
    if root_custom.exists():
        content = root_custom.read_text(encoding="utf-8")
        if not _is_placeholder_only(content):
            customs["CUSTOM.md (root)"] = content
            print("  [+] CUSTOM.md (has content)")
        else:
            print("  [=] CUSTOM.md (placeholder only)")

    # Orchestrator CUSTOM.md
    orch_custom = target / "metak-orchestrator" / "CUSTOM.md"
    if orch_custom.exists():
        content = orch_custom.read_text(encoding="utf-8")
        if not _is_placeholder_only(content):
            customs["metak-orchestrator/CUSTOM.md"] = content
            print("  [+] metak-orchestrator/CUSTOM.md (has content)")
        else:
            print("  [=] metak-orchestrator/CUSTOM.md (placeholder only)")

    # -- Collect LEARNED.md --------------------------------------------------
    learned_content = ""
    learned_path = target / "metak-shared" / "LEARNED.md"
    if learned_path.exists():
        content = learned_path.read_text(encoding="utf-8")
        if not _is_placeholder_only(content):
            learned_content = content
            print("  [+] metak-shared/LEARNED.md (has content)")
        else:
            print("  [=] metak-shared/LEARNED.md (placeholder only)")

    # -- Collect sub-repo files ----------------------------------------------
    subrepo_files = {}
    subrepo_folders = _get_workspace_subrepo_folders(target)

    for folder in subrepo_folders:
        for filename in ("AGENTS.md", "CUSTOM.md"):
            path = target / folder / filename
            if path.exists():
                content = path.read_text(encoding="utf-8")
                if not _is_placeholder_only(content):
                    label = "{}/{}".format(folder, filename)
                    subrepo_files[label] = content
                    print("  [+] {} (has content)".format(label))

    # -- Check if anything was found -----------------------------------------
    if not diffs and not customs and not subrepo_files and not learned_content:
        print()
        print("No customizations found. Nothing to feed back.")
        return

    # -- Build prompt --------------------------------------------------------
    prompt = _build_feedback_prompt(diffs, customs, subrepo_files, learned_content)

    # -- Summary -------------------------------------------------------------
    parts = []
    if diffs:
        parts.append("{} diff{}".format(len(diffs), "s" if len(diffs) != 1 else ""))
    if customs:
        parts.append("{} custom file{}".format(len(customs), "s" if len(customs) != 1 else ""))
    if subrepo_files:
        parts.append("{} sub-repo file{}".format(len(subrepo_files), "s" if len(subrepo_files) != 1 else ""))
    if learned_content:
        parts.append("LEARNED.md")

    print()
    print("Found {} to analyze.".format(", ".join(parts)))

    if args.dry_run:
        print()
        print("--- DRY RUN: prompt that would be sent to Claude CLI ---")
        print()
        print(prompt)
        return

    # -- Phase 1: analyze ----------------------------------------------------
    print("Sending to Claude CLI for analysis (this may take a minute)...")
    print()
    analysis = _invoke_claude_print(claude_bin, prompt)
    print(analysis)

    if not analysis.strip():
        print("No analysis returned.")
        return

    # Save to cache
    cache_path = metak_home / FEEDBACK_CACHE_FILE
    cache_path.write_text(analysis, encoding="utf-8")
    print("(Cached to {})".format(cache_path))

    # -- Phase 2: ask to apply -----------------------------------------------
    _prompt_and_apply(
        claude_bin, analysis, APPLY_PROMPT_TEMPLATE,
        "Apply the feedback suggestions from the system prompt. "
        "Show each proposed change and ask for approval before editing.",
        metak_home, "METAK_HOME",
    )


# ===================================================================
# update command
# ===================================================================

UPDATE_CACHE_FILE = ".metak-update-cache.md"


def _build_update_prompt(template_diffs, project_customs, project_subrepo_files,
                         project_learned):
    """Assemble the prompt for analyzing template updates against a project."""
    sections = []

    sections.append("""\
You are analyzing updates to MetaKitchen's template files to determine how they
should be incorporated into an existing project. The project was previously
installed from an older version of these templates and may have its own
customizations.

Your task: identify which template improvements should be applied to the
project's files, while PRESERVING any project-specific customizations.

FOCUS ON:
- New rules, conventions, or agent behaviors added to the templates
- Improved wording or structure in the templates
- New sections or instructions that the project doesn't have yet
- Changes to coding standards or workflow guidelines

PRESERVE:
- Project-specific details (API endpoints, team names, tech stack choices)
- Custom rules that only apply to this project
- Any content in CUSTOM.md files (these are entirely project-owned)
- Repo-specific instructions in sub-repo AGENTS.md files

DO NOT suggest removing or overwriting project customizations — only ADD or
MERGE template improvements alongside them.""")

    if template_diffs:
        sections.append("\n═══ TEMPLATE CHANGES (new METAK_HOME vs project's current files) ═══")
        sections.append("These diffs show how the updated templates differ from the project's files.")
        sections.append("The project files may include both outdated template content AND project "
                        "customizations — distinguish between the two.")
        for label, diff_text in template_diffs.items():
            sections.append("\n### {}\n```diff\n{}\n```".format(label, diff_text.rstrip()))

    if project_customs:
        sections.append("\n═══ PROJECT CUSTOM FILES (preserve these) ═══")
        sections.append("These are entirely project-owned. Do NOT suggest removing any content here.")
        for label, content in project_customs.items():
            sections.append("\n### {}\n```markdown\n{}\n```".format(label, content.rstrip()))

    if project_subrepo_files:
        sections.append(
            "\n═══ SUB-REPO AGENT FILES (for context) ═══\n"
            "These may need updates if the sub-repo AGENTS.md template changed."
        )
        for label, content in project_subrepo_files.items():
            sections.append("\n### {}\n```markdown\n{}\n```".format(label, content.rstrip()))

    if project_learned:
        sections.append("\n═══ LEARNED.md (project's discoveries — preserve) ═══")
        sections.append("\n```markdown\n{}\n```".format(project_learned.rstrip()))

    sections.append("""
═══════════════════════════

For each suggestion, provide:
1. Which project file to update
2. What to add or change (be specific — show the text to insert or modify)
3. Why this template improvement matters
4. How it merges with any existing project customizations in that file

If the project is already up to date, say so explicitly.""")

    return "\n".join(sections)


UPDATE_APPLY_TEMPLATE = """\
You are updating a project's agent instruction files to incorporate improvements
from the latest MetaKitchen templates. The analysis below identifies what
template changes should be applied to this project.

Your working directory is the project root. Files you may edit include:

- AGENTS.md — root agent instructions
- metak-orchestrator/AGENTS.md — orchestrator agent instructions
- metak-shared/coding-standards.md — shared coding standards
- metak-shared/LEARNED.md — discovered methods and tricks
- Sub-repo AGENTS.md files (e.g. frontend/AGENTS.md)

Rules:
- PRESERVE all project-specific customizations — merge, don't replace.
- Do NOT modify CUSTOM.md files — those are entirely project-owned.
- Show me each proposed change and wait for my approval before editing.

═══ ANALYSIS OF TEMPLATE UPDATES ═══

{}"""


def cmd_update(args):
    """Pull latest MetaKitchen templates and suggest project updates."""
    target = Path(args.target).resolve()

    # -- Pre-flight checks --------------------------------------------------
    metak_home = _resolve_metak_home()

    if not target.exists():
        print("Error: target directory '{}' does not exist.".format(target))
        sys.exit(1)

    if target == metak_home:
        print("Error: cannot run update on the MetaKitchen repo itself.")
        sys.exit(1)

    # Git must be available
    if not git_available():
        print("Error: git is not available on PATH.")
        print(GIT_RECOMMENDED_MSG)
        sys.exit(1)

    # METAK_HOME must have a clean working tree
    if git_has_uncommitted(metak_home):
        print("Error: METAK_HOME has uncommitted changes.")
        print("Please commit or stash changes in {} before running update.".format(metak_home))
        sys.exit(1)

    # Target project must have a clean working tree
    if git_has_uncommitted(target):
        print("Error: project has uncommitted changes.")
        print("Please commit or stash changes in {} before running update.".format(target))
        sys.exit(1)

    # Claude CLI must be available
    claude_bin = shutil.which("claude")
    if not claude_bin:
        print("Error: Claude Code CLI is not installed.")
        print()
        print("Install it with:")
        print("  npm install -g @anthropic-ai/claude-code")
        print()
        print("For more info: https://docs.anthropic.com/en/docs/claude-code/overview")
        sys.exit(1)

    # -- Cached mode ---------------------------------------------------------
    if args.cached:
        cache_path = metak_home / UPDATE_CACHE_FILE
        if not cache_path.exists():
            print("Error: no cached update analysis found at {}".format(cache_path))
            print("Run `metak update` first to generate the analysis.")
            sys.exit(1)
        analysis = cache_path.read_text(encoding="utf-8")
        print("Using cached update analysis from {}".format(cache_path))
        print()
        print(analysis)
        _prompt_and_apply(
            claude_bin, analysis, UPDATE_APPLY_TEMPLATE,
            "Apply the update suggestions from the system prompt. "
            "Show each proposed change and ask for approval before editing.",
            target, "project",
        )
        return

    # -- Pull latest in METAK_HOME -------------------------------------------
    if not args.skip_pull:
        print("Pulling latest changes in METAK_HOME ({})...".format(metak_home))
        result = subprocess.run(
            ["git", "pull"],
            cwd=str(metak_home),
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print("Error: git pull failed in METAK_HOME.")
            print(result.stderr.strip())
            sys.exit(1)
        pull_output = result.stdout.strip()
        print("  {}".format(pull_output))
        print()

        if "Already up to date" in pull_output and not args.force:
            print("Templates are already up to date. Nothing to do.")
            print("Pass --force to analyze anyway.")
            return

    # -- Collect diffs (METAK_HOME as source of truth) -----------------------
    print("Comparing updated templates against project: {}".format(target))
    print()

    template_diffs = {}
    for rel_path in DIFFABLE_FILES:
        template = metak_home / rel_path
        project = target / rel_path
        if template.exists() and project.exists():
            diff_text = _compute_diff(project, template, rel_path)
            if diff_text:
                template_diffs[rel_path] = diff_text
                print("  [~] {} (differs)".format(rel_path))
            else:
                print("  [=] {} (identical)".format(rel_path))
        elif template.exists():
            print("  [+] {} (new in templates, not in project)".format(rel_path))
        else:
            print("  [-] {} (not in templates)".format(rel_path))

    # -- Collect project CUSTOM.md files (as context to preserve) ------------
    project_customs = {}

    root_custom = target / "CUSTOM.md"
    if root_custom.exists():
        content = root_custom.read_text(encoding="utf-8")
        if not _is_placeholder_only(content):
            project_customs["CUSTOM.md (root)"] = content
            print("  [i] CUSTOM.md (has customizations to preserve)")

    orch_custom = target / "metak-orchestrator" / "CUSTOM.md"
    if orch_custom.exists():
        content = orch_custom.read_text(encoding="utf-8")
        if not _is_placeholder_only(content):
            project_customs["metak-orchestrator/CUSTOM.md"] = content
            print("  [i] metak-orchestrator/CUSTOM.md (has customizations to preserve)")

    # -- Collect LEARNED.md --------------------------------------------------
    project_learned = ""
    learned_path = target / "metak-shared" / "LEARNED.md"
    if learned_path.exists():
        content = learned_path.read_text(encoding="utf-8")
        if not _is_placeholder_only(content):
            project_learned = content
            print("  [i] metak-shared/LEARNED.md (has content to preserve)")

    # -- Collect sub-repo files ----------------------------------------------
    project_subrepo_files = {}
    subrepo_folders = _get_workspace_subrepo_folders(target)

    for folder in subrepo_folders:
        for filename in ("AGENTS.md", "CUSTOM.md"):
            path = target / folder / filename
            if path.exists():
                content = path.read_text(encoding="utf-8")
                if not _is_placeholder_only(content):
                    label = "{}/{}".format(folder, filename)
                    project_subrepo_files[label] = content
                    print("  [i] {} (has content)".format(label))

    # -- Check if anything differs -------------------------------------------
    if not template_diffs:
        print()
        print("No differences found between templates and project. Already up to date.")
        return

    # -- Build prompt --------------------------------------------------------
    prompt = _build_update_prompt(template_diffs, project_customs,
                                  project_subrepo_files, project_learned)

    # -- Summary -------------------------------------------------------------
    print()
    print("Found {} file{} with template differences.".format(
        len(template_diffs), "s" if len(template_diffs) != 1 else ""))

    if args.dry_run:
        print()
        print("--- DRY RUN: prompt that would be sent to Claude CLI ---")
        print()
        print(prompt)
        return

    # -- Phase 1: analyze ----------------------------------------------------
    print("Sending to Claude CLI for analysis (this may take a minute)...")
    print()
    analysis = _invoke_claude_print(claude_bin, prompt)
    print(analysis)

    if not analysis.strip():
        print("No analysis returned.")
        return

    # Save to cache
    cache_path = metak_home / UPDATE_CACHE_FILE
    cache_path.write_text(analysis, encoding="utf-8")
    print("(Cached to {})".format(cache_path))

    # -- Phase 2: ask to apply -----------------------------------------------
    _prompt_and_apply(
        claude_bin, analysis, UPDATE_APPLY_TEMPLATE,
        "Apply the update suggestions from the system prompt. "
        "Show each proposed change and ask for approval before editing.",
        target, "project",
    )


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
    p_setup.add_argument(
        "--skip-git",
        action="store_true",
        help="Suppress the git availability warning",
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
    p_install.add_argument(
        "--skip-git",
        action="store_true",
        help="Skip git availability and dirty-tree checks",
    )
    p_install.add_argument(
        "--commit",
        action="store_true",
        help="Commit the scaffolded files (mutually exclusive with --skip-git)",
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
    p_uninstall.add_argument(
        "--skip-git",
        action="store_true",
        help="Skip git availability and dirty-tree checks",
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
    p_add.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing scaffold files (AGENTS.md, .claude/CLAUDE.md). CUSTOM.md is never overwritten.",
    )
    p_add.add_argument(
        "--skip-git",
        action="store_true",
        help="Skip git availability and dirty-tree checks",
    )
    p_add.add_argument(
        "--commit",
        action="store_true",
        help="Commit the scaffolded files (mutually exclusive with --skip-git)",
    )

    # -- feedback --
    p_feedback = sub.add_parser(
        "feedback",
        help="Analyze project customizations and suggest improvements for metak templates",
    )
    p_feedback.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target project directory (default: current directory)",
    )
    p_feedback.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the prompt that would be sent to Claude CLI without executing it",
    )
    p_feedback.add_argument(
        "--cached",
        action="store_true",
        help="Skip analysis and apply previously cached feedback suggestions",
    )

    # -- update --
    p_update = sub.add_parser(
        "update",
        help="Pull latest metak templates and suggest updates for the project",
    )
    p_update.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target project directory (default: current directory)",
    )
    p_update.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the prompt that would be sent to Claude CLI without executing it",
    )
    p_update.add_argument(
        "--cached",
        action="store_true",
        help="Skip analysis and apply previously cached update suggestions",
    )
    p_update.add_argument(
        "--skip-pull",
        action="store_true",
        help="Skip the git pull step in METAK_HOME (use current state)",
    )
    p_update.add_argument(
        "--force",
        action="store_true",
        help="Analyze even if git pull reports no changes",
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
    elif args.command == "feedback":
        cmd_feedback(args)
    elif args.command == "update":
        cmd_update(args)
    else:
        _check_git_or_warn()
        parser.print_help()


if __name__ == "__main__":
    main()
