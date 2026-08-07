from __future__ import annotations

import shutil
from pathlib import Path

from .common import sha256_file


def _file_map(base: Path) -> dict:
    result = {}
    if not base.exists():
        return result
    for path in base.rglob("*"):
        if path.is_file():
            result[path.relative_to(base).as_posix()] = sha256_file(path)
    return result


def sync_skills(root: Path, check_only: bool = False) -> int:
    source = root / ".harness" / "skills"
    target = root / ".codex" / "skills"

    if not source.exists():
        print(f"FAILED: source not found: {source}")
        return 2

    if not check_only:
        shutil.copytree(source, target, dirs_exist_ok=True)
        skill_count = sum(1 for child in source.iterdir() if child.is_dir())
        print(f"Synced {skill_count} skills to {target}")
        return 0

    source_map = _file_map(source)
    target_map = _file_map(target)
    difference_count = 0

    for relative in sorted(source_map):
        if relative not in target_map:
            print(f"MISSING: {relative}")
            difference_count += 1
        elif source_map[relative] != target_map[relative]:
            print(f"DIFF: {relative}")
            difference_count += 1

    for relative in sorted(target_map):
        if relative not in source_map:
            print(f"EXTRA: {relative}")
            difference_count += 1

    if difference_count > 0:
        print(f"FAILED: {difference_count} difference(s)")
        return 1

    print("OK: files match")
    return 0
