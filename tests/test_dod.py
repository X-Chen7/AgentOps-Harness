from __future__ import annotations

import json

from harness.dod import run_dod


def _event_file(tmp_path, title: str, body: str):
    event = tmp_path / "event.json"
    event.write_text(
        json.dumps({"pull_request": {"title": title, "body": body}}, ensure_ascii=False),
        encoding="utf-8",
    )
    return event


def test_dod_passes_on_repo_copy(repo_copy) -> None:
    assert run_dod(repo_copy) == 0


def test_dod_missing_feature_list_fails(repo_copy) -> None:
    (repo_copy / ".harness" / "changes" / "active" / "feature-list.json").unlink()
    assert run_dod(repo_copy) == 1


def test_dod_rejects_bad_pr(repo_copy, tmp_path, monkeypatch) -> None:
    event = _event_file(tmp_path, "bad title", "no sections")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    assert run_dod(repo_copy) == 1


def test_dod_accepts_good_pr(repo_copy, tmp_path, monkeypatch) -> None:
    body = "## Summary\nchange\n\n## Verification\npytest\n\nFeature ID: F-012"
    event = _event_file(tmp_path, "feat(F-012): CI gate", body)
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    assert run_dod(repo_copy) == 0
