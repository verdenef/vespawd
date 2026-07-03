#!/usr/bin/env python3
"""One-time Vespawd setup for a new machine: verify Python, install the Vedaws runtime, verify."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

MIN_PYTHON = (3, 11)


def _framework_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _check_python() -> None:
    if sys.version_info < MIN_PYTHON:
        major, minor = sys.version_info[:2]
        print(
            f"error: Vespawd requires Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+; found {major}.{minor}",
            file=sys.stderr,
        )
        print("Install a newer Python from https://www.python.org/downloads/ and re-run.", file=sys.stderr)
        raise SystemExit(1)
    print(f"[ok] Python {sys.version_info.major}.{sys.version_info.minor} detected")


def _validate_framework(root: Path) -> None:
    missing = [rel for rel in ("vedaws", "paws022", "main/bridge", "main/executor") if not (root / rel).exists()]
    if missing:
        print(f"error: framework root {root} is missing: {', '.join(missing)}", file=sys.stderr)
        print("Run this from inside the Vespawd framework (the folder cloned from git).", file=sys.stderr)
        raise SystemExit(1)
    print(f"[ok] Framework found at {root}")


def _check_pip() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("error: pip is not available for this Python interpreter", file=sys.stderr)
        print("Install pip (https://pip.pypa.io/en/stable/installation/) and re-run.", file=sys.stderr)
        raise SystemExit(1)
    print(f"[ok] {result.stdout.strip()}")


def _pip_install_editable(package_dir: Path, *, dev: bool, label: str) -> None:
    target = f"{package_dir}[dev]" if dev else str(package_dir)
    print(f"Installing {label} ...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", target],
        cwd=package_dir,
        text=True,
    )
    if result.returncode != 0:
        print(f"error: failed to install {label}", file=sys.stderr)
        raise SystemExit(1)
    print(f"[ok] {label} installed")


def _verify_vedaws(framework: Path) -> None:
    if shutil.which("vedaws"):
        result = subprocess.run(["vedaws", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[ok] vedaws command available: {result.stdout.strip()}")
            return
    env = dict(os.environ)
    env["PYTHONPATH"] = str(framework / "vedaws" / "runtime")
    result = subprocess.run(
        [sys.executable, "-m", "vedaws", "version"],
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode == 0:
        print(f"[ok] vedaws importable: {result.stdout.strip()}")
    else:
        print("warning: could not verify vedaws after install", file=sys.stderr)


def _print_next_steps(framework: Path) -> None:
    print()
    print("=" * 60)
    print("Vespawd setup complete")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  - Create your first project (interactive):")
    print("      Windows:      double-click new-project.bat")
    print(f"      or:           python {framework / 'scripts' / 'new_project.py'}")
    print("  - Configure your external Planner and Documenter chats once:")
    print("      vespawd/paws022/.ai/planner_prompt.md")
    print("      vespawd/paws022/.ai/documenter_prompt.md")
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="One-time Vespawd machine setup")
    parser.add_argument(
        "--no-dev",
        action="store_true",
        help="Install without the dev extras (skip pytest)",
    )
    parser.add_argument(
        "--dev-all",
        action="store_true",
        help="Also install Bridge and Executor editable (for contributors)",
    )
    args = parser.parse_args(argv)

    print("Vespawd — one-time setup")
    print()

    _check_python()
    framework = _framework_root()
    _validate_framework(framework)
    _check_pip()

    dev = not args.no_dev
    _pip_install_editable(framework / "vedaws", dev=dev, label="Vedaws runtime")

    if args.dev_all:
        _pip_install_editable(framework / "main" / "bridge", dev=dev, label="Vespawd Bridge")
        _pip_install_editable(framework / "main" / "executor", dev=dev, label="Vespawd Executor")

    _verify_vedaws(framework)
    _print_next_steps(framework)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
