from __future__ import annotations

from harness.skills import sync_skills


def test_sync_skills_and_check(tmp_path) -> None:
    root = tmp_path / "root"
    source = root / ".harness" / "skills" / "skill-a"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("skill", encoding="utf-8")

    assert sync_skills(root, check_only=False) == 0
    target_skill = root / ".codex" / "skills" / "skill-a" / "SKILL.md"
    assert target_skill.exists()
    assert sync_skills(root, check_only=True) == 0

    target_skill.write_text("changed", encoding="utf-8")
    assert sync_skills(root, check_only=True) == 1
