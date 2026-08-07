from __future__ import annotations

from pathlib import Path

from harness.skill_contract import validate_all_skills


def _write_skill(root: Path, skill_id: str, body: str | None = None) -> Path:
    skill_dir = root / ".harness" / "skills" / skill_id
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# skill", encoding="utf-8")
    if body is not None:
        (skill_dir / "skill.yaml").write_text(body, encoding="utf-8")
    return skill_dir


VALID_YAML = """\
schema_version: "1.0"
id: skill-a
name: Skill A
version: "1.0.0"
description: Test skill
trigger:
  - task A
inputs:
  - repo
outputs:
  - report
dependencies: []
"""


def test_validate_passes_on_valid_skill(tmp_path) -> None:
    _write_skill(tmp_path, "skill-a", VALID_YAML)
    assert validate_all_skills(tmp_path) == 0


def test_validate_fails_without_yaml(tmp_path) -> None:
    _write_skill(tmp_path, "skill-a")
    assert validate_all_skills(tmp_path) == 1


def test_validate_fails_without_skill_md(tmp_path) -> None:
    skill_dir = tmp_path / ".harness" / "skills" / "skill-a"
    skill_dir.mkdir(parents=True)
    (skill_dir / "skill.yaml").write_text(VALID_YAML, encoding="utf-8")
    assert validate_all_skills(tmp_path) == 1


def test_validate_fails_on_id_mismatch(tmp_path) -> None:
    _write_skill(tmp_path, "skill-a", VALID_YAML.replace("id: skill-a", "id: other"))
    assert validate_all_skills(tmp_path) == 1


def test_validate_fails_on_unknown_dependency(tmp_path) -> None:
    body = VALID_YAML.replace("dependencies: []", "dependencies:\n  - ghost")
    _write_skill(tmp_path, "skill-a", body)
    assert validate_all_skills(tmp_path) == 1


def test_validate_fails_on_self_dependency(tmp_path) -> None:
    body = VALID_YAML.replace("dependencies: []", "dependencies:\n  - skill-a")
    _write_skill(tmp_path, "skill-a", body)
    assert validate_all_skills(tmp_path) == 1


def test_validate_fails_on_dependency_cycle(tmp_path) -> None:
    body_a = VALID_YAML.replace("dependencies: []", "dependencies:\n  - skill-b")
    _write_skill(tmp_path, "skill-a", body_a)
    body_b = VALID_YAML.replace("id: skill-a", "id: skill-b").replace(
        "dependencies: []", "dependencies:\n  - skill-a"
    )
    _write_skill(tmp_path, "skill-b", body_b)
    assert validate_all_skills(tmp_path) == 1
