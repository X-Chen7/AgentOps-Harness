from __future__ import annotations

import json
import subprocess

from harness.git_ops import cmd_commit, cmd_pr


def _git_init(path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=path, check=True, capture_output=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True, capture_output=True)


def _write_feature_list(path, feature: dict) -> None:
    fl = path / ".harness" / "changes" / "active" / "feature-list.json"
    fl.parent.mkdir(parents=True)
    data = {
        "schema_version": "1.2",
        "wip_limit": 1,
        "updated_at": "2026-08-07",
        "features": [feature],
    }
    fl.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def test_commit_creates_feature_branch(tmp_path) -> None:
    _git_init(tmp_path)
    _write_feature_list(
        tmp_path,
        {"id": "F-TEST", "title": "Test feature", "status": "todo", "pipeline": {"status": "not_started"}},
    )
    (tmp_path / "hello.txt").write_text("hello", encoding="utf-8")

    assert cmd_commit(tmp_path, "F-TEST") == 0
    branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=tmp_path, capture_output=True, text=True
    ).stdout.strip()
    assert branch == "feature/F-TEST"

    data = json.loads(
        (tmp_path / ".harness" / "changes" / "active" / "feature-list.json").read_text(encoding="utf-8")
    )
    assert data["features"][0]["status"] == "committed"


def test_pr_without_gh_writes_report(tmp_path, monkeypatch) -> None:
    _git_init(tmp_path)
    _write_feature_list(
        tmp_path,
        {
            "id": "F-TEST",
            "title": "Test feature",
            "status": "pushed",
            "push_status": "pushed",
            "branch": "feature/F-TEST",
            "commit": "0" * 40,
            "pipeline": {"status": "not_started"},
        },
    )
    monkeypatch.setattr("harness.git_ops.shutil.which", lambda _name: None)

    assert cmd_pr(tmp_path, "F-TEST") == 1
    report = tmp_path / ".harness" / "state" / "reports" / "pr-F-TEST.md"
    assert report.exists()
    assert "Feature ID: F-TEST" in report.read_text(encoding="utf-8")
