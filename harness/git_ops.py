from __future__ import annotations

import shutil
import sys
from pathlib import Path

from .common import (
    HarnessError,
    git_repo_available,
    read_json,
    run_cmd,
    today_str,
    write_json,
    write_text,
)


def _feature_list_path(root: Path) -> Path:
    return root / ".harness" / "changes" / "active" / "feature-list.json"


def _load_feature_list(root: Path) -> dict:
    path = _feature_list_path(root)
    if not path.exists():
        raise HarnessError(f"Missing file: {path}")
    data = read_json(path)
    if not isinstance(data, dict):
        raise HarnessError(f"Invalid feature-list: {path}")
    return data


def _find_feature(features: dict, feature_id: str) -> dict:
    for feature in features.get("features") or []:
        if feature.get("id") == feature_id:
            return feature
    raise HarnessError(f"Feature not found: {feature_id}")


def _feature_branch(feature: dict, feature_id: str) -> str:
    branch = feature.get("branch")
    if branch and not branch.startswith("未"):
        return branch
    return f"feature/{feature_id}"


def _add_history(feature: dict, status: str, note: str) -> None:
    history = feature.get("history") or []
    history.append(
        {
            "status": status,
            "at": today_str(),
            "by": "harness-git",
            "note": note,
        }
    )
    feature["history"] = history


def _porcelain(root: Path) -> list[str]:
    proc = run_cmd(["git", "status", "--porcelain"], cwd=root)
    return [line for line in proc.stdout.splitlines() if line.strip()]


def _assert_git_repo(root: Path) -> None:
    if not git_repo_available(root):
        raise HarnessError("Not a git repository; run git init first")


def _checkout_branch(root: Path, branch: str) -> None:
    current = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root).stdout.strip()
    if current == branch:
        return
    exists = (
        run_cmd(["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"], cwd=root).returncode == 0
    )
    if exists:
        proc = run_cmd(["git", "checkout", branch], cwd=root)
    else:
        proc = run_cmd(["git", "checkout", "-b", branch], cwd=root)
    if proc.returncode != 0:
        raise HarnessError(f"Failed to switch to branch {branch}")


def _commit_status(root: Path, feature_id: str, message: str) -> None:
    feature_list = _feature_list_path(root)
    proc = run_cmd(["git", "add", str(feature_list)], cwd=root)
    if proc.returncode != 0:
        raise HarnessError("git add failed")
    if not _porcelain(root):
        return
    proc = run_cmd(["git", "commit", "-m", message], cwd=root)
    if proc.returncode != 0:
        raise HarnessError("git commit failed")


def _save_feature_list(root: Path, features: dict) -> None:
    write_json(_feature_list_path(root), features)


def _run_harness(root: Path, args: list[str]) -> int:
    proc = run_cmd([sys.executable, "-m", "harness", *args, "--root", str(root)], cwd=root)
    return proc.returncode


def cmd_commit(root: Path, feature_id: str, message: str | None = None) -> int:
    _assert_git_repo(root)
    features = _load_feature_list(root)
    feature = _find_feature(features, feature_id)
    branch = _feature_branch(feature, feature_id)
    _checkout_branch(root, branch)

    proc = run_cmd(["git", "add", "-A"], cwd=root)
    if proc.returncode != 0:
        raise HarnessError("git add failed")
    if not _porcelain(root):
        print(f"[harness-git] no changes to commit for {feature_id}")
        return 0

    commit_message = message or f"feat({feature_id}): {feature.get('title', '')} Ref: {feature_id}"
    proc = run_cmd(["git", "commit", "-m", commit_message], cwd=root)
    if proc.returncode != 0:
        raise HarnessError("git commit failed")

    commit = run_cmd(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip()
    feature["status"] = "committed"
    feature["branch"] = branch
    feature["commit"] = commit
    feature["push_status"] = "none"
    _add_history(feature, "committed", f"committed on {branch}")
    features["updated_at"] = today_str()
    _save_feature_list(root, features)
    _commit_status(root, feature_id, f"chore({feature_id}): update feature-list status Ref: {feature_id}")

    print(f"[harness-git] committed {feature_id} on {branch} at {commit}")
    return 0


def cmd_push(root: Path, feature_id: str) -> int:
    _assert_git_repo(root)
    features = _load_feature_list(root)
    feature = _find_feature(features, feature_id)

    remotes = [line for line in run_cmd(["git", "remote"], cwd=root).stdout.splitlines() if line.strip()]
    if not remotes:
        print("[harness-git] no git remote configured; add origin first")
        return 1

    if feature.get("status") != "committed" or not feature.get("commit"):
        print(f"[harness-git] feature {feature_id} is not committed yet; run commit first")
        return 1

    branch = _feature_branch(feature, feature_id)
    _checkout_branch(root, branch)

    print("[harness-git] running harness check before push")
    if _run_harness(root, ["check"]) != 0:
        print("[harness-git] check failed; push aborted")
        return 1

    print("[harness-git] running harness sync --push-gate")
    if _run_harness(root, ["sync", "--push-gate"]) != 0:
        print("[harness-git] push gate failed; push aborted")
        return 1

    proc = run_cmd(["git", "push", "-u", "origin", branch], cwd=root)
    if proc.returncode != 0:
        raise HarnessError("git push failed")

    feature["status"] = "pushed"
    feature["push_status"] = "pushed"
    feature["remote_branch"] = branch
    _add_history(feature, "pushed", f"pushed to origin/{branch}")
    features["updated_at"] = today_str()
    _save_feature_list(root, features)
    _commit_status(
        root, feature_id, f"chore({feature_id}): update feature-list push status Ref: {feature_id}"
    )

    proc = run_cmd(["git", "push", "origin", branch], cwd=root)
    if proc.returncode != 0:
        raise HarnessError("git push (status) failed")

    print(f"[harness-git] pushed {feature_id} to origin/{branch}")
    return 0


def cmd_pr(root: Path, feature_id: str) -> int:
    _assert_git_repo(root)
    features = _load_feature_list(root)
    feature = _find_feature(features, feature_id)

    if feature.get("push_status") != "pushed":
        print(f"[harness-git] feature {feature_id} is not pushed yet; run push first")
        return 1

    branch = _feature_branch(feature, feature_id)
    title = f"feat({feature_id}): {feature.get('title', '')}"
    body = "\n".join(
        [
            "## Related",
            f"- Feature ID: {feature_id}",
            f"- Branch: {branch}",
            f"- Commit: {feature.get('commit', '')}",
            "",
            "## Summary",
            f"- See commit {feature.get('commit', '')}",
            "",
            "## Verification",
            "- script/check.ps1 passed before push",
        ]
    )

    if shutil.which("gh") is None:
        report_dir = root / ".harness" / "state" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"pr-{feature_id}.md"
        write_text(report_path, body)
        print(f"[harness-git] gh CLI not found; PR description written to {report_path}")
        return 1

    proc = run_cmd(
        ["gh", "pr", "create", "--base", "main", "--head", branch, "--title", title, "--body", body],
        cwd=root,
    )
    if proc.returncode != 0:
        print(f"[harness-git] gh pr create failed: {(proc.stdout + proc.stderr).strip()}")
        return 1

    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    url = lines[-1].strip() if lines else ""
    feature["pr_url"] = url
    _add_history(feature, "pushed", f"PR created: {url}")
    features["updated_at"] = today_str()
    _save_feature_list(root, features)
    _commit_status(root, feature_id, f"chore({feature_id}): update feature-list PR URL Ref: {feature_id}")

    proc = run_cmd(["git", "push", "origin", branch], cwd=root)
    if proc.returncode != 0:
        raise HarnessError("git push (PR status) failed")

    print(f"[harness-git] PR created: {url}")
    return 0
