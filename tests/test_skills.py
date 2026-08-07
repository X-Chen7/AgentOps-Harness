from __future__ import annotations

import shutil

from harness.skills import sync_skills


def test_sync_skills_and_check(tmp_path) -> None:
    root = tmp_path / "root"
    source = root / ".harness" / "skills" / "skill-a"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("skill", encoding="utf-8")
    fixture = source / "fixtures" / "case" / "task.md"
    fixture.parent.mkdir(parents=True)
    fixture.write_text("task", encoding="utf-8")

    assert sync_skills(root, check_only=False) == 0
    target_skill = root / ".codex" / "skills" / "skill-a" / "SKILL.md"
    assert target_skill.exists()
    assert not (root / ".codex" / "skills" / "skill-a" / "fixtures").exists()
    assert sync_skills(root, check_only=True) == 0

    target_skill.write_text("changed", encoding="utf-8")
    assert sync_skills(root, check_only=True) == 1


def test_sync_removes_deleted_skill(tmp_path) -> None:
    root = tmp_path / "root"
    source = root / ".harness" / "skills" / "skill-a"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("skill", encoding="utf-8")
    assert sync_skills(root, check_only=False) == 0
    assert (root / ".codex" / "skills" / "skill-a" / "SKILL.md").exists()

    shutil.rmtree(source)
    assert sync_skills(root, check_only=False) == 0
    assert not (root / ".codex" / "skills" / "skill-a").exists()


def test_sync_check_reports_stale_excluded(tmp_path) -> None:
    root = tmp_path / "root"
    source = root / ".harness" / "skills" / "skill-a"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("skill", encoding="utf-8")
    assert sync_skills(root, check_only=False) == 0

    stale = root / ".codex" / "skills" / "skill-a" / "fixtures" / "case" / "task.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale", encoding="utf-8")
    assert sync_skills(root, check_only=True) == 1
