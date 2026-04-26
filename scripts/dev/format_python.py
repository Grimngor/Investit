"""Run Ruff lint (auto-fix) then Ruff format for stable formatting.

Stages printed to stdout so pre-commit shows progress clearly.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND = ROOT / "backend"

def run(cmd: list[str]) -> int:
    proc = subprocess.run(cmd)
    return proc.returncode

def main() -> int:
    start = time.time()
    print("[ruff] phase 1: lint & autofix ...")
    rc_lint = run([sys.executable, "-m", "ruff", "check", "--fix", str(BACKEND)])
    print("[ruff] phase 2: format ...")
    rc_fmt = run([sys.executable, "-m", "ruff", "format", str(BACKEND)])
    elapsed = time.time() - start
    print(f"[ruff] completed in {elapsed:.2f}s (lint rc={rc_lint}, format rc={rc_fmt})")
    return rc_lint or rc_fmt

if __name__ == "__main__":
    raise SystemExit(main())
