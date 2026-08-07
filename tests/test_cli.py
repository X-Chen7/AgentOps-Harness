from __future__ import annotations

import subprocess
import sys

from .conftest import REPO_ROOT


def test_cli_check_smoke() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "harness", "check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0
    assert "Harness check: 0 error(s)" in proc.stdout
