from __future__ import annotations

import sys
from pathlib import Path

from .common import run_cmd


def run_lint(root: Path) -> int:
    check_proc = run_cmd([sys.executable, "-m", "ruff", "check", "."], cwd=root)
    if check_proc.returncode != 0:
        print(check_proc.stdout + check_proc.stderr, end="")
        print("[lint] ruff check failed")
        return 1

    format_proc = run_cmd([sys.executable, "-m", "ruff", "format", "--check", "."], cwd=root)
    if format_proc.returncode != 0:
        print(format_proc.stdout + format_proc.stderr, end="")
        print("[lint] ruff format check failed")
        return 1

    print("[lint] ruff check + format OK")
    return 0
