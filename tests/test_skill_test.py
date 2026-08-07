from __future__ import annotations

from pathlib import Path

from harness.skill_test import run_skill_tests


def _add_skill(root: Path, skill_id: str = "skill-a") -> Path:
    skill_dir = root / ".harness" / "skills" / skill_id
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# skill", encoding="utf-8")
    (skill_dir / "skill.yaml").write_text(
        f"""\
schema_version: "1.0"
id: {skill_id}
name: Skill
version: "1.0.0"
description: Test
trigger: [x]
inputs: [repo]
outputs: [report]
dependencies: []
""",
        encoding="utf-8",
    )
    return skill_dir


def _add_case(skill_dir: Path, case_id: str, checks_yaml: str) -> Path:
    case_dir = skill_dir / "fixtures" / case_id
    case_dir.mkdir(parents=True)
    (case_dir / "task.md").write_text("# task", encoding="utf-8")
    (case_dir / "checks.yaml").write_text(checks_yaml, encoding="utf-8")
    return case_dir


def test_run_passes_and_creates_output(tmp_path) -> None:
    skill_dir = _add_skill(tmp_path)
    _add_case(
        skill_dir,
        "passing",
        """\
schema_version: "1.0"
run: python -c "open('out.txt','w').write('ok')"
checks:
  - type: exit_code
    expected: 0
  - type: file_exists
    path: out.txt
  - type: contains
    path: out.txt
    text: ok
""",
    )
    code, results = run_skill_tests(tmp_path)
    assert code == 0
    assert results[0]["ok"] is True


def test_run_fails_on_missing_file(tmp_path) -> None:
    skill_dir = _add_skill(tmp_path)
    _add_case(
        skill_dir,
        "failing",
        """\
schema_version: "1.0"
run: python -c "print('ok')"
checks:
  - type: exit_code
    expected: 0
  - type: file_exists
    path: missing.txt
""",
    )
    code, results = run_skill_tests(tmp_path)
    assert code == 1
    assert results[0]["ok"] is False


def test_manual_case_is_not_failure(tmp_path) -> None:
    skill_dir = _add_skill(tmp_path)
    case_dir = skill_dir / "fixtures" / "manual"
    case_dir.mkdir(parents=True)
    (case_dir / "task.md").write_text("# task", encoding="utf-8")
    code, results = run_skill_tests(tmp_path)
    assert code == 0
    assert results[0]["manual"] is True


def test_empty_run_does_not_crash(tmp_path) -> None:
    skill_dir = _add_skill(tmp_path)
    _add_case(
        skill_dir,
        "empty-run",
        """\
schema_version: "1.0"
run: ""
checks:
  - type: exit_code
    expected: 0
""",
    )
    code, results = run_skill_tests(tmp_path)
    assert code == 1
    assert "exit_code expected 0, got -1" in results[0]["errors"][0]


def test_missing_task_md_fails(tmp_path) -> None:
    skill_dir = _add_skill(tmp_path)
    case_dir = skill_dir / "fixtures" / "no-task"
    case_dir.mkdir(parents=True)
    (case_dir / "checks.yaml").write_text(
        """\
schema_version: "1.0"
checks: []
""",
        encoding="utf-8",
    )
    code, results = run_skill_tests(tmp_path)
    assert code == 1
    assert "missing task.md" in results[0]["errors"]


def test_check_path_cannot_escape_workdir(tmp_path) -> None:
    skill_dir = _add_skill(tmp_path)
    _add_case(
        skill_dir,
        "escape",
        """\
schema_version: "1.0"
checks:
  - type: file_exists
    path: ../outside.txt
""",
    )
    code, results = run_skill_tests(tmp_path)
    assert code == 1
    assert "path escapes fixture workdir" in results[0]["errors"][0]


def test_invalid_checks_yaml_fails(tmp_path) -> None:
    skill_dir = _add_skill(tmp_path)
    case_dir = skill_dir / "fixtures" / "bad"
    case_dir.mkdir(parents=True)
    (case_dir / "task.md").write_text("# task", encoding="utf-8")
    (case_dir / "checks.yaml").write_text('schema_version: "2.0"\nchecks: []\n', encoding="utf-8")
    code, results = run_skill_tests(tmp_path)
    assert code == 1
    assert "invalid checks.yaml" in results[0]["errors"][0]
