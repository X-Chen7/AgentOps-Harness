from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional, Sequence


class HarnessError(RuntimeError):
    """Raised when a harness command cannot complete."""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def read_json(path: Path) -> Any:
    try:
        return json.loads(read_text(path))
    except Exception as exc:
        raise HarnessError(f"Invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, data: Any) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def today_str() -> str:
    return date.today().isoformat()


def timestamp_str() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def run_cmd(args: Sequence[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(args),
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def git_repo_available(cwd: Path) -> bool:
    proc = run_cmd(["git", "rev-parse", "--is-inside-work-tree"], cwd=cwd)
    return proc.returncode == 0
