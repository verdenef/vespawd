#!/usr/bin/env python3
"""Bootstrap a new Vespawd project by copying the framework into <project>/vespawd/."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

MIN_PYTHON = (3, 11)
PROJECT_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")

COPY_COMPONENTS = ("vedaws", "paws022", "main/bridge", "main/executor")

DOC_RESET_FILES = (
    "docs/HANDOFF_FOR_DOCUMENTER.md",
    "docs/architecture.md",
    "docs/api_contracts.md",
    "docs/db_schema.md",
    "docs/decisions.md",
)

IGNORE_DIR_NAMES = frozenset(
    {
        ".git",
        ".vedaws",
        "__pycache__",
        ".pytest_cache",
        ".venv",
        "venv",
        ".eggs",
        "dist",
        "build",
        "node_modules",
    }
)

PROJECT_GITIGNORE = """# Runtime orchestration state (auto-managed)
vespawd/main/.vedaws/

# Python
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
dist/
build/
.venv/
venv/

# Test / tooling caches
.pytest_cache/
.mypy_cache/
.coverage
htmlcov/

# OS / logs
.DS_Store
Thumbs.db
*.log
*.tmp

# Environment secrets
.env
.env.*
"""

INTAKE_TEMPLATE = """# Intake (optional)

Dump **raw** context here before planning — assignment text, rubric, links, half-formed ideas.

Your **planner** (external) or **executor** can turn this into a structured Master Prompt. No special format required.

---

_Paste below:_

"""

CURRENT_TASK_TEMPLATE = """# Current Task (POS Scheduler)

> **Runtime state** for this repo. After copying the POS template, set to **idle** or your first real goal (see [BOOTSTRAP.md](../BOOTSTRAP.md)).

**Status:** `idle` | `in_progress` | `blocked`
**Started:** —
**Owner:** —

## Goal

_No active task. Pull from `backlog.md` or define the first goal here._

## Acceptance Criteria

- [ ]

## Notes

## Progress Log

| Date | Update |
|------|--------|
| | |
"""

BACKLOG_TEMPLATE = """# Backlog (POS Scheduler)

> **Per-project** queue. Clear template lines after bootstrap.

Prioritized future work. **One item** moves to `current_task.md` when started.

## Item Format

```markdown
- [ ] **Title** — description _(priority: high | medium | low)_
```

## Items

- [ ] _{First real backlog item}_
"""

VESPAWD_CURSOR_RULE = """---
alwaysApply: true
---
# Vespawd project layout

This repository is a **Vespawd** project. Open this folder (the project root) in your IDE.

- **POS memory** (project brain) lives under `vespawd/paws022/`:
  - `vespawd/paws022/.ai/project_context.md` — product, stack, constraints
  - `vespawd/paws022/.ai/executor_rules.md` — how the executor must behave (follow this)
  - `vespawd/paws022/tasks/current_task.md` — the single active task
  - `vespawd/paws022/tasks/backlog.md` — future phases
  - `vespawd/paws022/docs/` — architecture, db_schema, api_contracts, HANDOFF_FOR_DOCUMENTER
- **Application code** goes in `main/src/` (a sibling of `vespawd/`). Never put app code in `vespawd/paws022/`.
- **Managed automatically — do not hand-edit:** `vespawd/vedaws/`, `vespawd/main/` (bridge, executor, `.vedaws/` state).

## Executor behavior

When the user pastes a `# POS MASTER PROMPT` (or says "Execute this"):
1. Follow `vespawd/paws022/.ai/executor_rules.md` in full.
2. Write POS memory (current_task, project_context, backlog, HANDOFF) under `vespawd/paws022/`.
3. Implement code only under `main/src/`, with minimal diffs.
4. **Sync orchestration as your final step.** After the task's acceptance criteria are met and `vespawd/paws022/tasks/current_task.md` is updated, run this from the project root so Vedaws stays in sync:

```
py -3 vespawd/scripts/sync_orchestration.py
```

   (Use `python vespawd/scripts/sync_orchestration.py` if `py` is unavailable.) This calls the Bridge, advances the Vedaws workflow/state, and refreshes `vespawd/paws022/tasks/status.md`. Report the resulting state and any warnings. Do NOT pass `--complete` yourself — that is for the human to run after they have tested and accepted a phase.

The Vespawd Executor CLI, when invoked, uses `--workspace vespawd`. Orchestration (Vedaws) runs automatically via the Bridge — you never edit `vespawd/vedaws/` or `vespawd/main/.vedaws/` by hand. If you cannot run the sync command, tell the user to double-click `sync-orchestration.bat`.
"""

PROJECT_SYNC_BAT = """@echo off
REM Sync PAWS current_task.md to Vedaws (run after each executor phase).
setlocal
set "SCRIPT=%~dp0vespawd\\scripts\\sync_orchestration.py"
if not exist "%SCRIPT%" (
    echo ERROR: missing vespawd\\scripts\\sync_orchestration.py
    pause
    exit /b 1
)
where py >nul 2>nul
if %ERRORLEVEL%==0 (py -3 "%SCRIPT%" %*) else (python "%SCRIPT%" %*)
set "RC=%ERRORLEVEL%"
echo.
if %RC% NEQ 0 pause
exit /b %RC%
"""

STATUS_TEMPLATE = """# POS status

| Field | Value |
|-------|--------|
| Phase | 1 |
| App | idle |
| Handoff | stale |
| Docs (submission) | pending |
| Last_master_prompt | — |

_Executor updates this file when phases complete._
"""


def _framework_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _check_python() -> None:
    if sys.version_info < MIN_PYTHON:
        major, minor = sys.version_info[:2]
        print(
            f"error: Vespawd requires Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+; found {major}.{minor}",
            file=sys.stderr,
        )
        raise SystemExit(1)


def _validate_framework(root: Path) -> None:
    missing = []
    for rel in ("vedaws", "paws022", "main/bridge", "main/executor"):
        if not (root / rel).exists():
            missing.append(rel)
    if missing:
        print(f"error: framework root {root} is missing: {', '.join(missing)}", file=sys.stderr)
        raise SystemExit(1)


def _default_parent_dir() -> Path:
    for candidate in (Path("C:/dev"), Path.home() / "dev", Path.cwd()):
        if candidate.is_dir():
            return candidate.resolve()
    return Path.cwd().resolve()


def _prompt(text: str, default: str | None = None, *, required: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        try:
            value = input(f"{text}{suffix}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print(file=sys.stderr)
            raise SystemExit(130) from None
        if not value:
            if default is not None:
                return default
            if required:
                print("  (required — please enter a value)")
                continue
            return ""
        return value


def _confirm(text: str, *, default_yes: bool = True) -> bool:
    hint = "Y/n" if default_yes else "y/N"
    try:
        answer = input(f"{text} [{hint}]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print(file=sys.stderr)
        raise SystemExit(130) from None
    if not answer:
        return default_yes
    return answer in {"y", "yes"}


def _validate_project_name(name: str) -> str | None:
    if not name:
        return "project name is required"
    if not PROJECT_NAME_RE.match(name):
        return "use letters, numbers, hyphens, and underscores only (no spaces or path separators)"
    return None


def _copy_ignore(_dir: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        if name in IGNORE_DIR_NAMES:
            ignored.add(name)
        if name.endswith(".egg-info") or name.endswith(".pyc"):
            ignored.add(name)
    return ignored


def _copy_component(src: Path, dst: Path, *, force: bool) -> None:
    if dst.exists():
        if not force:
            raise FileExistsError(f"already exists: {dst}")
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=_copy_ignore)


def _patch_manifest_cli(manifest_path: Path) -> None:
    text = manifest_path.read_text(encoding="utf-8")
    text = re.sub(
        r'^cli\s*=\s*".*"$',
        'cli = "../vedaws"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    manifest_path.write_text(text, encoding="utf-8")


def _application_code_path(app_folder: str) -> str:
    return f"../../{app_folder}/src"


def _write_project_context(path: Path, project_name: str, app_folder: str) -> None:
    app_code = _application_code_path(app_folder)
    content = f"""# Project Context (POS Memory)

> Single source of truth for this repository. Generated by Vespawd new-project setup.

## Product

- **Name:** {project_name}
- **Summary:** _TBD_
- **Users / stakeholders:** _TBD_

## Tech Stack

| Area | Choice |
|------|--------|
| Language(s) | _TBD_ |
| Framework | _TBD_ |
| Database | _TBD_ |
| Auth | _TBD_ |
| Deployment | _TBD_ |

## Layout

| Field | Value |
|-------|--------|
| Mode | sidecar |
| POS folder (sidecar) | paws022/ |
| Application code | `{app_code}` |

## Repository Layout (POS)

| Path | Role |
|------|------|
| .ai/ | Kernel: how agents and devs work |
| docs/ | Architecture, APIs, schema, ADRs |
| tasks/ | Current work, backlog, completed log |
| {app_folder}/src/ | Application code (userspace, sibling of vespawd/) |

## Environment

- **Required env vars:** _TBD_
- **Local setup:** _TBD_
- **Run tests:** _TBD_
- **Run app:** _TBD_

## Constraints

- Security / compliance: _TBD_
- Performance: _TBD_
- Compatibility: _TBD_

## Agent Notes

- _Add domain vocabulary and hard rules here._

## Links

- Issue tracker: _TBD_
- CI: _TBD_
- Docs / wiki: _TBD_
- Staging / production: _TBD_
"""
    path.write_text(content, encoding="utf-8")


def _reset_paws_memory(
    framework: Path,
    paws_root: Path,
    project_name: str,
    app_folder: str,
) -> None:
    _write_project_context(paws_root / ".ai" / "project_context.md", project_name, app_folder)
    (paws_root / "tasks" / "intake.md").write_text(INTAKE_TEMPLATE, encoding="utf-8")
    (paws_root / "tasks" / "current_task.md").write_text(CURRENT_TASK_TEMPLATE, encoding="utf-8")
    (paws_root / "tasks" / "backlog.md").write_text(BACKLOG_TEMPLATE, encoding="utf-8")
    (paws_root / "tasks" / "status.md").write_text(STATUS_TEMPLATE, encoding="utf-8")
    for rel in DOC_RESET_FILES:
        src = framework / "paws022" / rel
        dst = paws_root / rel
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def _vedaws_env(vedaws_root: Path) -> dict[str, str]:
    env = dict(os.environ)
    runtime = vedaws_root / "runtime"
    env["PYTHONPATH"] = str(runtime)
    return env


def _run_vedaws_init(vedaws_root: Path, vespawd_main: Path, project_name: str) -> None:
    marker = vespawd_main / ".vedaws" / "project.toml"
    if marker.is_file():
        return
    cmd = [sys.executable, "-m", "vedaws", "init", "--template", "software", "--name", project_name, "."]
    result = subprocess.run(
        cmd,
        cwd=vespawd_main,
        env=_vedaws_env(vedaws_root),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        print("error: vedaws init failed", file=sys.stderr)
        raise SystemExit(1)
    if result.stdout.strip():
        print(result.stdout.strip())


def _write_cursor_rule(target: Path) -> None:
    rule_path = target / ".cursor" / "rules" / "vespawd.mdc"
    rule_path.parent.mkdir(parents=True, exist_ok=True)
    rule_path.write_text(VESPAWD_CURSOR_RULE, encoding="utf-8")


def _install_sync_helper(framework: Path, target: Path, vespawd_dst: Path) -> None:
    src = framework / "scripts" / "sync_orchestration.py"
    if not src.is_file():
        return
    dst = vespawd_dst / "scripts" / "sync_orchestration.py"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    (target / "sync-orchestration.bat").write_text(PROJECT_SYNC_BAT, encoding="utf-8")


def _run_git_init(target: Path) -> None:
    if shutil.which("git") is None:
        print("note: git not found — skipping git init")
        return
    gitignore = target / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(PROJECT_GITIGNORE, encoding="utf-8")
    if (target / ".git").exists():
        return
    subprocess.run(["git", "init"], cwd=target, check=False)


def _run_verify(target: Path, vespawd_root: Path) -> bool:
    executor = vespawd_root / "main" / "executor" / "bin" / "executor"
    if not executor.is_file():
        print("warning: executor CLI not found — skipping verify", file=sys.stderr)
        return True
    result = subprocess.run(
        [sys.executable, str(executor), "startup", "--workspace", str(vespawd_root)],
        cwd=target,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)
    try:
        payload = json.loads(result.stdout)
        return bool(payload.get("ok"))
    except json.JSONDecodeError:
        return result.returncode == 0


def _print_next_steps(target: Path, app_folder: str) -> None:
    print()
    print("=" * 60)
    print("Vespawd project created successfully")
    print("=" * 60)
    print()
    print(f"  Project root:  {target}")
    print(f"  Framework:     {target / 'vespawd'}")
    print(f"  Application:   {target / app_folder / 'src'}")
    print()
    print("Next steps:")
    print(f"  1. Open {target} in your IDE")
    print("  2. Configure external agents (one time):")
    print("     - Planner:    vespawd/paws022/.ai/planner_prompt.md")
    print("     - Documenter: vespawd/paws022/.ai/documenter_prompt.md")
    print("     - See:        vespawd/paws022/docs/EXTERNAL_AGENTS_SETUP.md")
    print("  3. Write your assignment in vespawd/paws022/tasks/intake.md")
    print("  4. Ask your Planner for a POS MASTER PROMPT (Phase 1 only)")
    print('  5. Paste the Master Prompt into your IDE with "Execute this."')
    print("     (The executor auto-syncs Vedaws via .cursor/rules/vespawd.mdc)")
    print("  6. If status.md looks stale: double-click sync-orchestration.bat")
    print()
    print("Executor workspace path (for reference):")
    print(f"  {target / 'vespawd'}")
    print()


def _resolve_inputs(args: argparse.Namespace) -> tuple[Path, str, str]:
    if args.target:
        target = Path(args.target).expanduser().resolve()
        name = args.name or target.name
        app_folder = args.app_folder
        return target, name, app_folder

    if args.name and not args.target:
        parent = Path(args.parent).expanduser().resolve() if args.parent else _default_parent_dir()
        if not args.yes:
            parent = Path(_prompt("Parent directory", str(parent))).expanduser().resolve()
        name = args.name
        app_folder = args.app_folder
        target = (parent / name).resolve()
        return target, name, app_folder

    print("Vespawd — new project setup")
    print()
    parent = Path(_prompt("Parent directory", str(_default_parent_dir()))).expanduser().resolve()
    while True:
        name = _prompt("Project name", required=True)
        err = _validate_project_name(name)
        if err:
            print(f"  {err}")
            continue
        break
    app_folder = _prompt("App folder name", args.app_folder) or args.app_folder
    target = (parent / name).resolve()
    return target, name, app_folder


def _check_nonempty_target(target: Path, *, force: bool, skip_confirm: bool) -> None:
    if not target.exists():
        return
    if not target.is_dir():
        print(f"error: {target} exists and is not a directory", file=sys.stderr)
        raise SystemExit(1)
    if not any(target.iterdir()):
        return
    if force:
        return
    print(f"warning: {target} already exists and is not empty")
    if skip_confirm:
        print("error: use --force to set up in a non-empty directory", file=sys.stderr)
        raise SystemExit(1)
    if not _confirm("Continue anyway?"):
        print("Aborted.")
        raise SystemExit(0)


def _confirm_layout(
    target: Path,
    app_folder: str,
    *,
    skip: bool,
    force: bool,
) -> None:
    vespawd_dst = target / "vespawd"
    app_src = target / app_folder / "src"
    print()
    print("Will create:")
    print(f"  {vespawd_dst}\\   (framework copy)")
    print(f"  {app_src}\\  (your application)")
    print()
    _check_nonempty_target(target, force=force, skip_confirm=skip)
    if not skip and not _confirm("Proceed?"):
        print("Aborted.")
        raise SystemExit(0)


def _bootstrap_project(
    framework: Path,
    target: Path,
    project_name: str,
    app_folder: str,
    *,
    force: bool,
    no_init: bool,
    no_git: bool,
    verify: bool,
) -> None:
    vespawd_dst = target / "vespawd"
    if vespawd_dst.exists() and not force:
        print(f"error: {vespawd_dst} already exists (use --force to replace)", file=sys.stderr)
        raise SystemExit(1)

    target.mkdir(parents=True, exist_ok=True)

    if vespawd_dst.exists() and force:
        shutil.rmtree(vespawd_dst)

    for rel in COPY_COMPONENTS:
        src = framework / rel
        dst = vespawd_dst / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        print(f"Copying {rel} ...")
        _copy_component(src, dst, force=force)

    app_src = target / app_folder / "src"
    app_src.mkdir(parents=True, exist_ok=True)
    gitkeep = app_src / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")

    manifest_path = vespawd_dst / "main" / "bridge" / "manifest.toml"
    _patch_manifest_cli(manifest_path)
    _reset_paws_memory(framework, vespawd_dst / "paws022", project_name, app_folder)
    _write_cursor_rule(target)
    _install_sync_helper(framework, target, vespawd_dst)

    if not no_init:
        print("Initializing Vedaws orchestration ...")
        _run_vedaws_init(vespawd_dst / "vedaws", vespawd_dst / "main", project_name)

    if not no_git:
        print("Initializing git repository ...")
        _run_git_init(target)

    if verify:
        print("Verifying executor startup ...")
        ok = _run_verify(target, vespawd_dst)
        if not ok:
            print("warning: executor startup reported issues (see output above)", file=sys.stderr)

    _print_next_steps(target, app_folder)


def main(argv: list[str] | None = None) -> int:
    _check_python()

    parser = argparse.ArgumentParser(
        description="Create a new Vespawd project with embedded framework copy",
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Project root directory (non-interactive mode)",
    )
    parser.add_argument("--name", help="Project name (folder name, Vedaws name, product name)")
    parser.add_argument("--parent", help="Parent directory for interactive/semi-interactive mode")
    parser.add_argument("--app-folder", default="main", help="Application folder name (default: main)")
    parser.add_argument("--force", action="store_true", help="Replace existing vespawd/ copy")
    parser.add_argument("--no-init", action="store_true", help="Skip vedaws init")
    parser.add_argument("--no-git", action="store_true", help="Skip git init and .gitignore")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--verify", action="store_true", default=True, help="Run executor startup verify (default)")
    parser.add_argument("--no-verify", action="store_false", dest="verify", help="Skip executor startup verify")

    args = parser.parse_args(argv)
    framework = _framework_root()
    _validate_framework(framework)

    target, project_name, app_folder = _resolve_inputs(args)
    err = _validate_project_name(project_name)
    if err:
        print(f"error: invalid project name: {err}", file=sys.stderr)
        return 1

    if not args.yes:
        _confirm_layout(target, app_folder, skip=False, force=args.force)
    else:
        _check_nonempty_target(target, force=args.force, skip_confirm=True)

    _bootstrap_project(
        framework,
        target,
        project_name,
        app_folder,
        force=args.force,
        no_init=args.no_init,
        no_git=args.no_git,
        verify=args.verify,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
