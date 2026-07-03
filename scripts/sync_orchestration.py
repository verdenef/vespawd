#!/usr/bin/env python3
"""Sync PAWS current_task.md → Bridge → Vedaws (for generic IDE executors).

Run from your project root after the executor updates paws022/tasks/current_task.md,
for example when using Antigravity or Cursor without the Vespawd executor library.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def _find_project_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        if (candidate / "vespawd" / "main" / "bridge" / "bin" / "bridge").is_file():
            return candidate
    return None


def _section(text: str, heading: str) -> str:
    pattern = rf"## {re.escape(heading)}\s*\n+([\s\S]*?)(?=\n## |\Z)"
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _parse_current_task(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    goal = ""
    block_goal = re.search(r">\s*\*\*Goal:\*\*\s*(.+)", text)
    if block_goal:
        goal = block_goal.group(1).strip()
    if not goal:
        body = _section(text, "Goal")
        goal = body.strip("_").strip() if body else ""
    if not goal:
        raise SystemExit(f"error: no goal found in {path}")

    status_match = re.search(r"\*\*Status:\*\*\s*`?(\w+)`?", text)
    status = status_match.group(1) if status_match else "in_progress"

    notes = _section(text, "Notes")
    if notes:
        notes = "\n".join(
            line
            for line in notes.splitlines()
            if not re.match(r"^-\s+\*\*Vedaws phase:\*\*", line.strip())
            and not re.match(r"^-\s+\*\*Orchestration state:\*\*", line.strip())
            and not re.match(r"^-\s+\*\*Bridge sync:\*\*", line.strip())
            and not re.match(r"^-\s+\*\*Blockers:\*\*", line.strip())
        ).strip()

    return {
        "goal": goal,
        "status": status,
        "acceptance_criteria": _section(text, "Acceptance criteria") or _section(text, "Acceptance Criteria"),
        "constraints": _section(text, "Constraints"),
        "notes": notes,
    }


def _product_name(project_context: Path) -> str | None:
    if not project_context.is_file():
        return None
    match = re.search(r"\*\*Name:\*\*\s*(.+)", project_context.read_text(encoding="utf-8"))
    return match.group(1).strip() if match else None


def _invoke_bridge(bridge: Path, operation: str, context: dict, payload: dict | None = None) -> dict:
    with tempfile.TemporaryDirectory(prefix="vespawd-sync-") as tmp:
        ctx_path = Path(tmp) / "context.json"
        ctx_path.write_text(json.dumps(context), encoding="utf-8")
        cmd = [
            sys.executable,
            str(bridge),
            "invoke",
            operation,
            "--context",
            str(ctx_path),
        ]
        if payload is not None:
            inp_path = Path(tmp) / "input.json"
            inp_path.write_text(json.dumps(payload), encoding="utf-8")
            cmd.extend(["--input", str(inp_path)])
        out_path = Path(tmp) / "result.json"
        cmd.extend(["--output", str(out_path)])
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if not out_path.is_file():
            if proc.stderr:
                print(proc.stderr, file=sys.stderr)
            raise SystemExit(f"error: bridge {operation} produced no output (exit {proc.returncode})")
        result = json.loads(out_path.read_text(encoding="utf-8"))
        if proc.returncode != 0 and result.get("ok"):
            pass
        return result


def _vedaws_env(vespawd: Path) -> dict[str, str]:
    """Mirror the Bridge: run the bundled runtime so we don't rely on a global install."""
    env = dict(os.environ)
    runtime = vespawd / "vedaws" / "runtime"
    if runtime.is_dir():
        existing = env.get("PYTHONPATH")
        env["PYTHONPATH"] = str(runtime) + (os.pathsep + existing if existing else "")
    return env


def _vedaws_state(vedaws_main: Path, vespawd: Path) -> str:
    proc = subprocess.run(
        [sys.executable, "-m", "vedaws", "state", "--path", str(vedaws_main)],
        capture_output=True,
        text=True,
        env=_vedaws_env(vespawd),
    )
    if proc.returncode != 0:
        return "unknown"
    match = re.search(r"Current state:\s*(\S+)", proc.stdout)
    return match.group(1) if match else "unknown"


def _workflow_progress(vedaws_main: Path, vespawd: Path, workflow_id: str) -> tuple[str, str | None]:
    """Return (progress_line, first_ready_task_id) from `vedaws workflow show`."""
    proc = subprocess.run(
        [sys.executable, "-m", "vedaws", "workflow", "show", workflow_id, "--path", str(vedaws_main)],
        capture_output=True,
        text=True,
        env=_vedaws_env(vespawd),
    )
    if proc.returncode != 0:
        return "unknown", None
    progress = ""
    ready: str | None = None
    for line in proc.stdout.splitlines():
        if "Progress:" in line:
            progress = line.split("Progress:", 1)[1].strip()
        match = re.match(r"\s*(\S+)\s+\[ready\]", line)
        if match and ready is None:
            ready = match.group(1)
    return progress or "unknown", ready


def _complete_ready_task(vedaws_main: Path, vespawd: Path, task_id: str) -> tuple[bool, str]:
    """Complete a single ready workflow stage without triggering the automation cascade.

    Uses `vedaws tasks complete` directly (single-step) rather than the Bridge's
    post_phase_complete, which runs a dispatch loop that would auto-finish every
    remaining stage and prematurely mark the project completed.
    """
    proc = subprocess.run(
        [sys.executable, "-m", "vedaws", "tasks", "complete", task_id, "--path", str(vedaws_main)],
        capture_output=True,
        text=True,
        env=_vedaws_env(vespawd),
    )
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout or "tasks complete rejected").strip()
    return True, task_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sync paws022/tasks/current_task.md to Vedaws via the Bridge",
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        help="Project root (folder that contains vespawd/). Default: current directory",
    )
    parser.add_argument(
        "--phase-hint",
        help="Override phase keyword (e.g. implement, test, handoff)",
    )
    parser.add_argument(
        "--complete",
        action="store_true",
        help="After you have tested and accepted this phase, mark the current ready "
        "workflow stage complete so the Vedaws ledger advances (one stage per run).",
    )
    args = parser.parse_args(argv)

    start = Path(args.project_root).expanduser().resolve() if args.project_root else Path.cwd()
    project_root = _find_project_root(start)
    if project_root is None:
        print("error: could not find vespawd/main/bridge/bin/bridge under project root", file=sys.stderr)
        return 1

    vespawd = project_root / "vespawd"
    bridge = vespawd / "main" / "bridge" / "bin" / "bridge"
    paws = vespawd / "paws022"
    current_task = paws / "tasks" / "current_task.md"
    project_context = paws / ".ai" / "project_context.md"
    vedaws_main = vespawd / "main"

    if not current_task.is_file():
        print(f"error: missing {current_task}", file=sys.stderr)
        return 1

    task = _parse_current_task(current_task)
    if task["status"] == "idle":
        print("note: current_task status is idle — nothing to sync")
        return 0

    context = {
        "workspace_root": str(vespawd.resolve()).replace("\\", "/"),
        "correlation_id": "sync-orchestration",
    }
    product = _product_name(project_context)

    state_before = _vedaws_state(vedaws_main, vespawd)
    print(f"Project:  {project_root.name}")
    print(f"Vedaws:   {state_before}")
    print(f"Goal:     {task['goal'][:80]}{'...' if len(task['goal']) > 80 else ''}")
    print()

    marker = vedaws_main / ".vedaws" / "project.toml"
    if not marker.is_file():
        boot = _invoke_bridge(bridge, "bootstrap", context, {"project_name": product or project_root.name})
        if not boot.get("ok"):
            print("bootstrap failed:", boot.get("blockers") or boot.get("codes"), file=sys.stderr)
            return 1
        print("bootstrap: ok")

    ingest_payload = {
        "current_task": {
            "goal": task["goal"],
            "acceptance_criteria": task["acceptance_criteria"],
            "constraints": task["constraints"] or None,
            "notes": task["notes"] or None,
        },
        "project_context": {"product_name": product or project_root.name},
    }
    if args.phase_hint:
        ingest_payload["phase_hint"] = args.phase_hint

    ingest = _invoke_bridge(bridge, "ingest_master_prompt", context, ingest_payload)
    sync = _invoke_bridge(bridge, "sync_status", context, {})

    ok = bool(ingest.get("ok")) and bool(sync.get("ok"))
    completed_task: str | None = None
    complete_error: str | None = None

    if args.complete:
        _, ready_task = _workflow_progress(vedaws_main, vespawd, "software")
        if ready_task is None:
            complete_error = "no ready workflow stage to close (already caught up or blocked)"
        else:
            done, detail = _complete_ready_task(vedaws_main, vespawd, ready_task)
            if done:
                completed_task = detail
                # Reproject status.md through the Bridge after the ledger moved.
                sync = _invoke_bridge(bridge, "sync_status", context, {})
            else:
                complete_error = detail
                ok = False

    state_after = _vedaws_state(vedaws_main, vespawd)
    progress, next_ready = _workflow_progress(vedaws_main, vespawd, "software")

    print("ingest:   ", "ok" if ingest.get("ok") else "FAILED")
    print("sync:     ", "ok" if sync.get("ok") else "FAILED")
    if args.complete:
        if completed_task:
            print(f"complete:  {completed_task} marked done")
        else:
            print(f"complete:  {complete_error}")
    print(f"task id:  {ingest.get('vedaws_task_id') or sync.get('vedaws_task_id') or '—'}")
    print(f"state:    {state_before} -> {state_after}")
    print(f"workflow: {progress}" + (f"  (next ready: {next_ready})" if next_ready else ""))
    for warning in ingest.get("warnings") or []:
        print(f"warning:  {warning}")
    print()
    print(f"Updated:  {paws / 'tasks' / 'status.md'}")
    if not args.complete and next_ready:
        print("Tip: after you test and accept this phase, run with --complete to advance the workflow one stage.")
    print("Tip: use  py -3 -m vedaws status --path vespawd/main  (same as vedaws when not on PATH)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
