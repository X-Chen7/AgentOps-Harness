from __future__ import annotations

from harness.sync import sync_changes


def test_sync_passes_on_copy(repo_copy) -> None:
    assert sync_changes(repo_copy) == 0


def test_sync_missing_feature_list_fails(repo_copy) -> None:
    (repo_copy / ".harness" / "changes" / "active" / "feature-list.json").unlink()
    assert sync_changes(repo_copy) == 1
