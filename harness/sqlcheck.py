from __future__ import annotations

import re
import sys
from pathlib import Path

from .common import read_text

DESTRUCTIVE_RE = re.compile(
    r"\b(?:DROP\s+(?:TABLE|DATABASE|SCHEMA)|TRUNCATE\s+TABLE|DELETE\s+FROM)\b",
    re.IGNORECASE,
)
VALID_NAME_RE = re.compile(r"^[a-z0-9_\-]+\.sql$")


def run_sql_check(root: Path) -> int:
    sql_dir = root / "sql"
    if not sql_dir.exists():
        print("[sqlcheck] no sql directory found; skipping")
        return 0

    files = sorted(sql_dir.rglob("*.sql"))
    errors = []
    for file in files:
        relative = file.relative_to(root).as_posix()
        if not VALID_NAME_RE.match(file.name):
            errors.append(f"{relative}: filename must be lowercase snake_case")
        content = read_text(file)
        if DESTRUCTIVE_RE.search(content):
            errors.append(f"{relative}: destructive statement found (DROP/TRUNCATE/DELETE FROM)")

    print(f"[sqlcheck] {len(files)} sql file(s), {len(errors)} error(s)")
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    return 1 if errors else 0
