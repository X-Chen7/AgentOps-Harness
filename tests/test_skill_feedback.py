from __future__ import annotations

import json

from harness.skill_feedback import promote_feedback, record_feedback

from .test_skill_test import _add_skill


def test_record_feedback_appends_jsonl(tmp_path) -> None:
    _add_skill(tmp_path)
    assert record_feedback(tmp_path, "skill-a", "pass", note="ok") == 0
    assert record_feedback(tmp_path, "skill-a", "fail", note="broken") == 0

    path = tmp_path / ".harness" / "skills" / "skill-a" / "feedback.jsonl"
    lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [line["status"] for line in lines] == ["pass", "fail"]
    assert lines[0]["skill"] == "skill-a"


def test_record_rejects_unknown_skill(tmp_path) -> None:
    assert record_feedback(tmp_path, "missing", "pass") == 1


def test_promote_creates_fixture_skeleton(tmp_path) -> None:
    _add_skill(tmp_path)
    assert promote_feedback(tmp_path, "skill-a", "real-case", task_text="do the thing") == 0
    case_dir = tmp_path / ".harness" / "skills" / "skill-a" / "fixtures" / "real-case"
    assert (case_dir / "task.md").exists()
    assert (case_dir / "expected.md").exists()
    assert not (case_dir / "checks.yaml").exists()


def test_promote_rejects_path_traversal(tmp_path) -> None:
    _add_skill(tmp_path)
    assert promote_feedback(tmp_path, "skill-a", "..") == 1
    skill_dir = tmp_path / ".harness" / "skills" / "skill-a"
    assert not (skill_dir / "task.md").exists()
