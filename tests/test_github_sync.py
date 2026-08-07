from __future__ import annotations

import copy

from harness.github_sync import (
    GitHubIssue,
    GitHubPR,
    reconcile_ledger,
)


def _ledger() -> dict:
    return {
        "schema_version": "1.3",
        "wip_limit": 1,
        "updated_at": "2026-08-08",
        "git_sync": {"enabled": True, "repo": "test/repo", "remote": "https://github.com/test/repo"},
        "features": [
            {
                "id": "F-014",
                "title": "Existing feature",
                "status": "merged",
                "push_status": "merged",
                "commit": "a" * 40,
                "pipeline": {"status": "not_started"},
                "history": [],
                "blocked_by": [],
                "issue_number": None,
                "issue_url": "",
                "pr_number": None,
            }
        ],
    }


def _issue(number: int = 1, title: str = "New issue", body: str = "", state: str = "open") -> GitHubIssue:
    return GitHubIssue(
        number=number,
        title=title,
        body=body,
        state=state,
        url=f"https://github.com/test/repo/issues/{number}",
        updated_at="2026-08-08T10:00:00Z",
    )


def _pr(
    number: int = 10,
    title: str = "feat(F-015): work",
    body: str = "Feature ID: F-015",
    state: str = "open",
    merged: bool = False,
    merge_sha: str = "b" * 40,
    head_ref: str = "feature/F-015-work",
) -> GitHubPR:
    return GitHubPR(
        number=number,
        title=title,
        body=body,
        state=state,
        merged=merged,
        merge_commit_sha=merge_sha,
        head_ref=head_ref,
        url=f"https://github.com/test/repo/pull/{number}",
        updated_at="2026-08-08T10:00:00Z",
        author="tester",
    )


def test_issue_opened_without_fid_creates_feature() -> None:
    features, actions = reconcile_ledger(_ledger(), [_issue(body="do the thing")], [])
    assert actions[0]["type"] == "create_feature"
    assert actions[1]["type"] == "create_plan"
    created = next(f for f in features["features"] if f["id"] == "F-015")
    assert created["status"] == "todo"
    assert created["issue_number"] == 1
    assert any(a["type"] == "update_issue_body" for a in actions)


def test_issue_opened_with_fid_links_existing_feature() -> None:
    ledger = _ledger()
    ledger["features"][0]["id"] = "F-015"
    ledger["features"][0]["status"] = "in_progress"
    ledger["features"][0]["pipeline"] = {"status": "not_started"}
    _, actions = reconcile_ledger(ledger, [_issue(title="F-015: known")], [])
    assert any(a["type"] == "link_issue" for a in actions)


def test_issue_title_synced_only_before_commit() -> None:
    ledger = _ledger()
    feature = ledger["features"][0]
    feature["id"] = "F-015"
    feature["status"] = "todo"
    feature["issue_number"] = 1
    _, actions = reconcile_ledger(
        ledger,
        [_issue(title="F-015: new title")],
        [],
    )
    assert any(a["type"] == "sync_title" for a in actions)

    feature["status"] = "committed"
    _, actions = reconcile_ledger(
        copy.deepcopy(ledger),
        [_issue(title="F-015: new title")],
        [],
    )
    assert not any(a["type"] == "sync_title" for a in actions)


def test_pr_opened_links_and_pushes_feature() -> None:
    ledger = _ledger()
    feature = ledger["features"][0]
    feature["id"] = "F-015"
    feature["status"] = "in_progress"
    feature["pipeline"] = {"status": "not_started"}
    features, actions = reconcile_ledger(ledger, [], [_pr()])
    updated = next(f for f in features["features"] if f["id"] == "F-015")
    assert updated["status"] == "pushed"
    assert updated["push_status"] == "pushed"
    assert updated["pr_number"] == 10
    assert any(a["type"] == "link_pr" for a in actions)


def test_pr_merged_archives_and_closes_issue() -> None:
    ledger = _ledger()
    feature = ledger["features"][0]
    feature["id"] = "F-015"
    feature["status"] = "pushed"
    feature["push_status"] = "pushed"
    feature["pr_number"] = 10
    feature["issue_number"] = 1
    features, actions = reconcile_ledger(
        ledger,
        [_issue(title="F-015: done", state="open")],
        [_pr(state="closed", merged=True)],
    )
    updated = next(f for f in features["features"] if f["id"] == "F-015")
    assert updated["status"] == "merged"
    assert updated["push_status"] == "merged"
    assert updated["commit"] == "b" * 40
    assert any(a["type"] == "archive" for a in actions)
    assert any(a["type"] == "close_issue" and a["issue_number"] == 1 for a in actions)


def test_pr_closed_unmerged_reverts_to_in_progress() -> None:
    ledger = _ledger()
    feature = ledger["features"][0]
    feature["id"] = "F-015"
    feature["status"] = "pushed"
    feature["push_status"] = "pushed"
    feature["pr_number"] = 10
    features, actions = reconcile_ledger(
        ledger,
        [],
        [_pr(state="closed", merged=False)],
    )
    updated = next(f for f in features["features"] if f["id"] == "F-015")
    assert updated["status"] == "in_progress"
    assert updated["pr_url"] == ""
    assert updated["pr_number"] is None
    assert any(a["type"] == "pr_closed_unmerged" for a in actions)


def test_issue_closed_unmerged_blocks_feature() -> None:
    ledger = _ledger()
    feature = ledger["features"][0]
    feature["id"] = "F-015"
    feature["status"] = "in_progress"
    feature["issue_number"] = 1
    features, actions = reconcile_ledger(
        ledger,
        [_issue(title="F-015: blocked", state="closed")],
        [],
    )
    updated = next(f for f in features["features"] if f["id"] == "F-015")
    assert updated["status"] == "blocked"
    assert updated["blocked_by"]
    assert any(a["type"] == "mark_blocked" for a in actions)


def test_issue_reopened_unblocks_feature() -> None:
    ledger = _ledger()
    feature = ledger["features"][0]
    feature["id"] = "F-015"
    feature["status"] = "blocked"
    feature["blocked_by"] = ["GitHub issue #1 closed without merge"]
    feature["issue_number"] = 1
    features, actions = reconcile_ledger(
        ledger,
        [_issue(title="F-015: reopened", state="open")],
        [],
    )
    updated = next(f for f in features["features"] if f["id"] == "F-015")
    assert updated["status"] == "in_progress"
    assert updated["blocked_by"] == []
    assert any(a["type"] == "unblock" for a in actions)


def test_reconcile_is_idempotent() -> None:
    ledger = _ledger()
    issue = _issue(title="F-015: work")
    pr = _pr()
    updated, _ = reconcile_ledger(ledger, [issue], [pr])
    applied_pr = _pr(body="Feature ID: F-015\nCloses #1")
    _, actions = reconcile_ledger(updated, [issue], [applied_pr])
    assert actions == []


def test_sync_pr_is_ignored() -> None:
    ledger = _ledger()
    pr = _pr(head_ref="harness-sync/issues-1-abc123")
    _, actions = reconcile_ledger(ledger, [], [pr])
    assert actions == []


def test_secondary_merged_pr_does_not_rearchive() -> None:
    ledger = _ledger()
    feature = ledger["features"][0]
    feature["id"] = "F-015"
    feature["status"] = "merged"
    feature["push_status"] = "merged"
    feature["commit"] = "a" * 40
    feature["pr_number"] = 8
    feature["pr_url"] = "https://github.com/test/repo/pull/8"
    features, actions = reconcile_ledger(
        ledger,
        [],
        [_pr(number=9, state="closed", merged=True, merge_sha="b" * 40)],
    )
    updated = next(f for f in features["features"] if f["id"] == "F-015")
    assert updated["commit"] == "a" * 40
    assert updated["pr_number"] == 8
    assert not any(a["type"] == "archive" for a in actions)


def test_open_followup_pr_does_not_relink_merged_feature() -> None:
    ledger = _ledger()
    feature = ledger["features"][0]
    feature["id"] = "F-015"
    feature["status"] = "merged"
    feature["push_status"] = "merged"
    feature["commit"] = "a" * 40
    feature["pr_number"] = 8
    feature["pr_url"] = "https://github.com/test/repo/pull/8"
    feature["issue_number"] = 1
    features, actions = reconcile_ledger(
        ledger,
        [_issue(title="F-015: done", state="open")],
        [_pr(number=9, state="open", merged=False)],
    )
    updated = next(f for f in features["features"] if f["id"] == "F-015")
    assert updated["pr_number"] == 8
    assert not any(a["type"] == "link_pr" for a in actions)
    assert not any(a["type"] == "update_pr_body" for a in actions)


def test_auto_created_feature_respects_wip_limit() -> None:
    features, _ = reconcile_ledger(_ledger(), [_issue(body="new work")], [])
    created = next(f for f in features["features"] if f["id"] == "F-015")
    assert created["status"] == "todo"
