from __future__ import annotations

import shutil
from pathlib import Path

from .common import sha256_file

SYNC_EXCLUDE_PARTS = {"fixtures", "feedback.jsonl"}


def _is_excluded(relative: str) -> bool:
    return any(part in SYNC_EXCLUDE_PARTS for part in Path(relative).parts)


def _file_map(base: Path, exclude: bool = True) -> dict:
    result = {}
    if not base.exists():
        return result
    for path in base.rglob("*"):
        if path.is_file():
            relative = path.relative_to(base).as_posix()
            if not exclude or not _is_excluded(relative):
                result[relative] = sha256_file(path)
    return result


def _source_entries(source: Path) -> set[str]:
    entries = set()
    for path in source.rglob("*"):
        relative = path.relative_to(source).as_posix()
        if not _is_excluded(relative):
            entries.add(relative)
    return entries


def _remove_stale(target: Path, keep: set[str]) -> None:
    stale = [path for path in target.rglob("*") if path.relative_to(target).as_posix() not in keep]
    for path in sorted(stale, key=lambda item: len(item.parts), reverse=True):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)


def sync_skills(root: Path, check_only: bool = False) -> int:
    source = root / ".harness" / "skills"
    target = root / ".codex" / "skills"

    if not source.exists():
        print(f"FAILED: source not found: {source}")
        return 2

    if not check_only:
        keep = _source_entries(source)
        for path in source.rglob("*"):
            relative = path.relative_to(source).as_posix()
            if _is_excluded(relative):
                continue
            destination = target / relative
            if path.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)
        _remove_stale(target, keep)
        skill_count = sum(1 for child in source.iterdir() if child.is_dir())
        print(f"Synced {skill_count} skills to {target}")
        return 0

    source_map = _file_map(source, exclude=True)
    target_map = _file_map(target, exclude=False)
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
