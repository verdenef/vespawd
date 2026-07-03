#!/usr/bin/env python3
"""Friendly Vespawd control console.

A menu-driven wrapper over the Vedaws CLI so users never type
`py -3 -m vedaws ... --path vespawd/main`. Double-click vespawd.bat, or run:

    py -3 vespawd/scripts/vespawd_console.py [project_root]
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def _find_project_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        if (candidate / "vespawd" / "main" / "bridge" / "bin" / "bridge").is_file():
            return candidate
        if (candidate / "main" / "bridge" / "bin" / "bridge").is_file() and (candidate / "vedaws").is_dir():
            # Running from inside the framework repo itself.
            return candidate
    return None


def _vedaws_env(vespawd: Path) -> dict[str, str]:
    env = dict(os.environ)
    runtime = vespawd / "vedaws" / "runtime"
    if runtime.is_dir():
        existing = env.get("PYTHONPATH")
        env["PYTHONPATH"] = str(runtime) + (os.pathsep + existing if existing else "")
    return env


def _workflow_id(vespawd: Path) -> str:
    manifest = vespawd / "main" / "bridge" / "manifest.toml"
    if manifest.is_file():
        try:
            data = tomllib.loads(manifest.read_text(encoding="utf-8"))
            return str(data.get("vedaws", {}).get("workflow_id", "software"))
        except (OSError, tomllib.TOMLDecodeError):
            pass
    return "software"


class Console:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.vespawd = root / "vespawd"
        self.vedaws_main = self.vespawd / "main"
        self.paws = self.vespawd / "paws022"
        self.env = _vedaws_env(self.vespawd)
        self.workflow_id = _workflow_id(self.vespawd)

    # --- low-level runners -------------------------------------------------

    def _vedaws(self, args: list[str], *, with_path: bool = True) -> tuple[int, str, str]:
        cmd = [sys.executable, "-m", "vedaws", *args]
        if with_path:
            cmd += ["--path", str(self.vedaws_main)]
        proc = subprocess.run(cmd, capture_output=True, text=True, env=self.env)
        return proc.returncode, proc.stdout, proc.stderr

    def _sync(self, *, complete: bool) -> int:
        script = SCRIPT_DIR / "sync_orchestration.py"
        cmd = [sys.executable, str(script), str(self.root)]
        if complete:
            cmd.append("--complete")
        return subprocess.run(cmd).returncode

    # --- helpers -----------------------------------------------------------

    def _state(self) -> str:
        rc, out, _ = self._vedaws(["state"])
        if rc != 0:
            return "unknown"
        m = re.search(r"Current state:\s*(\S+)", out)
        return m.group(1) if m else "unknown"

    def _progress(self) -> tuple[str, str | None]:
        rc, out, _ = self._vedaws(["workflow", "show", self.workflow_id])
        if rc != 0:
            return "unknown", None
        progress = ""
        ready: str | None = None
        for line in out.splitlines():
            if "Progress:" in line:
                progress = line.split("Progress:", 1)[1].strip()
            m = re.match(r"\s*(\S+)\s+\[ready\]", line)
            if m and ready is None:
                ready = m.group(1)
        return progress or "unknown", ready

    def _status_md_field(self, field: str) -> str:
        path = self.paws / "tasks" / "status.md"
        if not path.is_file():
            return "—"
        m = re.search(rf"\|\s*{re.escape(field)}\s*\|\s*(.+?)\s*\|", path.read_text(encoding="utf-8"))
        return m.group(1) if m else "—"

    # --- menu actions ------------------------------------------------------

    def action_status(self) -> None:
        print("Where your project stands")
        print("-" * 40)
        state = self._state()
        progress, ready = self._progress()
        print(f"  Project state : {state}")
        print(f"  Lifecycle     : {progress}")
        if ready:
            print(f"  Next stage    : {ready}  (accept a phase to advance)")
        print(f"  App           : {self._status_md_field('App')}")
        print(f"  Handoff       : {self._status_md_field('Handoff')}")
        print(f"  Last synced   : {self._status_md_field('Last_sync')}")

    def action_health(self) -> None:
        print("Checking project health (Vedaws doctor)...")
        rc, out, err = self._vedaws(["doctor"])
        passes = out.count("[PASS]")
        fails = out.count("[FAIL]")
        overall = "PASS" if "Overall: PASS" in out else ("FAIL" if fails else "unknown")
        print("-" * 40)
        print(f"  Result: {overall}   ({passes} checks passed, {fails} failed)")
        if fails or rc != 0:
            print()
            print(out.strip() or err.strip())
        else:
            print("  Everything looks healthy.")

    def action_sync(self) -> None:
        print("Refreshing orchestration status...")
        print("-" * 40)
        self._sync(complete=False)

    def action_accept(self) -> None:
        progress, ready = self._progress()
        print("Accept the current phase")
        print("-" * 40)
        print(f"  Lifecycle now : {progress}")
        if not ready:
            print("  Nothing to accept right now (no stage is ready).")
            return
        print(f"  This will mark : {ready}  as done and advance one stage.")
        print("  Only do this if you have TESTED the app and are happy with this phase.")
        print()
        answer = input("  Type Y then Enter to confirm (anything else cancels): ").strip().lower()
        if answer not in {"y", "yes"}:
            print("  Cancelled - nothing changed.")
            return
        self._sync(complete=True)

    def action_progress(self) -> None:
        print("Lifecycle checklist")
        print("-" * 40)
        rc, out, err = self._vedaws(["workflow", "show", self.workflow_id])
        print(out.strip() or err.strip())

    def action_state_history(self) -> None:
        print("Project state history")
        print("-" * 40)
        rc, out, err = self._vedaws(["state", "history"])
        print(out.strip() or err.strip())

    def action_docs(self) -> None:
        print("Documentation checklist (Vedaws software artifacts)")
        print("-" * 40)
        rc, out, err = self._vedaws(["software", "artifacts"])
        print(out.strip() or err.strip())

    def action_automation(self) -> None:
        print("Automation rules")
        print("-" * 40)
        rc, out, err = self._vedaws(["automation", "list"])
        print(out.strip() or err.strip())

    def action_ai(self) -> None:
        print("AI providers")
        print("-" * 40)
        rc, out, err = self._vedaws(["ai", "providers"])
        print(out.strip() or err.strip())

    def action_events(self) -> None:
        print("Event bus statistics")
        print("-" * 40)
        rc, out, err = self._vedaws(["events"])
        print(out.strip() or err.strip())

    def action_full_status(self) -> None:
        print("Full runtime status")
        print("-" * 40)
        rc, out, err = self._vedaws(["status"])
        print(out.strip() or err.strip())

    def action_raw(self) -> None:
        print("Advanced: run a raw Vedaws command")
        print("  (type the part after 'vedaws', e.g.  workflow show software  )")
        print("  --path is added automatically. Leave blank to cancel.")
        raw = input("  vedaws ").strip()
        if not raw:
            print("  Cancelled.")
            return
        args = raw.split()
        with_path = args[0] not in {"version"}
        rc, out, err = self._vedaws(args, with_path=with_path)
        print("-" * 40)
        print(out.strip() or err.strip() or f"(exit code {rc})")


MENU = [
    ("BASIC", None),
    ("1", "Status - where does my project stand?", "action_status"),
    ("2", "Health check - is everything OK?", "action_health"),
    ("3", "Sync - refresh status after the executor worked", "action_sync"),
    ("4", "Accept phase - advance one stage (after testing)", "action_accept"),
    ("5", "Progress - show the lifecycle checklist", "action_progress"),
    ("ADVANCED", None),
    ("6", "Project state history", "action_state_history"),
    ("7", "Documentation checklist", "action_docs"),
    ("8", "Automation rules", "action_automation"),
    ("9", "AI providers", "action_ai"),
    ("10", "Event bus statistics", "action_events"),
    ("11", "Full runtime status (plugins + workers)", "action_full_status"),
    ("12", "Run a raw Vedaws command", "action_raw"),
]


def _print_menu(root: Path) -> None:
    print()
    print("=" * 52)
    print(f" Vespawd Console  -  {root.name}")
    print("=" * 52)
    for entry in MENU:
        if entry[1] is None:
            print(f"\n  {entry[0]}")
        else:
            key, label, _ = entry
            print(f"    {key:>2}. {label}")
    print("\n     0. Exit")
    print("-" * 52)


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    start = Path(argv[0]).expanduser().resolve() if argv else Path.cwd()
    root = _find_project_root(start)
    if root is None:
        print("error: could not find a Vespawd project (looked for vespawd/main/bridge).", file=sys.stderr)
        print("Run this from your project root, or pass the path as an argument.", file=sys.stderr)
        return 1

    console = Console(root)
    actions = {key: name for key, label, name in (e for e in MENU if e[1] is not None)}

    while True:
        _print_menu(root)
        try:
            choice = input(" Choose a number: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if choice == "0":
            return 0
        action_name = actions.get(choice)
        if not action_name:
            print("  Not a valid choice.")
            continue
        print()
        try:
            getattr(console, action_name)()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        except Exception as exc:  # keep the console alive on any single-action failure
            print(f"  error: {exc}", file=sys.stderr)
        print()
        try:
            input(" Press Enter to return to the menu... ")
        except (EOFError, KeyboardInterrupt):
            print()
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
