from __future__ import annotations

import json
from pathlib import Path

from .common import timestamp_str, write_text
from .skill_contract import iter_skill_dirs

VALID_STATUSES = ("pass", "fail", "partial")


def _find_skill(root: Path, skill_id: str) -> Path | None:
    for skill_dir in iter_skill_dirs(root):
        if skill_dir.name == skill_id:
            return skill_dir
    return None


def record_feedback(root: Path, skill_id: str, status: str, note: str = "") -> int:
    skill_dir = _find_skill(root, skill_id)
    if skill_dir is None:
        print(f"[skill feedback] skill not found: {skill_id}")
        return 1
    if status not in VALID_STATUSES:
        print(f"[skill feedback] status must be one of: {', '.join(VALID_STATUSES)}")
        return 1

    entry = {
        "skill": skill_id,
        "status": status,
        "note": note,
        "at": timestamp_str(),
    }
    path = skill_dir / "feedback.jsonl"
    if path.is_symlink():
        print(f"[skill feedback] refusing symlink: {path}")
        return 1
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"[skill feedback] recorded {status} for {skill_id}: {path}")
    return 0


def promote_feedback(root: Path, skill_id: str, case_id: str, task_text: str = "") -> int:
    skill_dir = _find_skill(root, skill_id)
    if skill_dir is None:
        print(f"[skill feedback] skill not found: {skill_id}")
        return 1
    if not case_id or any(char in case_id for char in "/\\:") or case_id in (".", ".."):
        print("[skill feedback] case_id must be a plain directory name")
        return 1

    case_dir = skill_dir / "fixtures" / case_id
    fixtures_dir = (skill_dir / "fixtures").resolve()
    if not case_dir.resolve().is_relative_to(fixtures_dir):
        print("[skill feedback] case_id must stay inside fixtures")
        return 1
    case_dir.mkdir(parents=True, exist_ok=True)
    task_path = case_dir / "task.md"
    if task_path.exists():
        print(f"[skill feedback] fixture already exists: {task_path}")
        return 1
    write_text(task_path, task_text or f"# {case_id}\n\n补充真实任务输入与期望行为。\n")
    expected_path = case_dir / "expected.md"
    if not expected_path.exists():
        write_text(expected_path, f"# {case_id} 期望产出\n\n补充可验证的期望行为。\n")
    print(f"[skill feedback] promoted case: {case_dir}")
    return 0
