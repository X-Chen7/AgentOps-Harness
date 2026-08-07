from __future__ import annotations

import json

from harness.check import run_check

from .conftest import REPO_ROOT


def test_repo_itself_passes() -> None:
    errors, _ = run_check(REPO_ROOT)
    assert errors == []


def test_missing_agents(repo_copy) -> None:
    (repo_copy / "AGENTS.md").unlink()
    errors, _ = run_check(repo_copy)
    assert "AGENTS.md is missing" in errors


def test_broken_agents_import(repo_copy) -> None:
    agents = repo_copy / "AGENTS.md"
    content = agents.read_text(encoding="utf-8-sig")
    agents.write_text(content + "\n@missing-file.md\n", encoding="utf-8")
    errors, _ = run_check(repo_copy)
    assert any("Broken AGENTS import: missing-file.md" in error for error in errors)


def test_write_scope_conflict_blocked(repo_copy) -> None:
    path = repo_copy / ".harness" / "pipelines" / "desktop-pipeline.parallel.example.json"
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    for stage in data["stages"]:
        if stage["id"] == "coding-b":
            stage["write_scope"] = ["src/module-a"]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    errors, _ = run_check(repo_copy)
    assert any("overlapping write_scope" in error for error in errors)


def test_invalid_active_stages_blocked(repo_copy) -> None:
    path = repo_copy / ".harness" / "templates" / "pipeline-state.example.json"
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    data["active_stages"] = ["ghost"]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    errors, _ = run_check(repo_copy)
    assert any("active_stages has unknown stage: ghost" in error for error in errors)


def test_ci_mode_treats_warning_as_error(repo_copy) -> None:
    path = repo_copy / ".harness" / "changes" / "active" / "feature-list.json"
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    for feature in data["features"]:
        if feature["id"] == "F-011":
            feature["owner"] = ""
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    from harness.check import cmd_check

    assert cmd_check(repo_copy, ci=True) == 1
    assert cmd_check(repo_copy, ci=False) == 0
