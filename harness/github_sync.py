from __future__ import annotations

import copy
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import knowledge as knowledge_mod
from .common import HarnessError, read_json, read_text, run_cmd, today_str, write_json, write_text

FEATURE_ID_RE = re.compile(r"F-\d{3,}")
PR_NUMBER_RE = re.compile(r"/pull/(\d+)")
ISSUE_CLOSE_RE = re.compile(r"(?:closes|fixes|resolves)\s+#(\d+)", re.IGNORECASE)
SYNC_BRANCH_PREFIX = "harness-sync/"


@dataclass
class GitHubIssue:
    number: int
    title: str
    body: str
    state: str
    url: str
    updated_at: str
    labels: list[str] = field(default_factory=list)


@dataclass
class GitHubPR:
    number: int
    title: str
    body: str
    state: str
    merged: bool
    merge_commit_sha: str
    head_ref: str
    url: str
    updated_at: str
    author: str


def _feature_list_path(root: Path) -> Path:
    return root / ".harness" / "changes" / "active" / "feature-list.json"


def _load_ledger(root: Path) -> dict:
    path = _feature_list_path(root)
    data = read_json(path)
    if not isinstance(data, dict):
        raise HarnessError(f"Invalid feature-list: {path}")
    return data


def _save_ledger(root: Path, features: dict) -> None:
    write_json(_feature_list_path(root), features)


def _find_feature(features: dict, feature_id: str) -> dict | None:
    for feature in features.get("features") or []:
        if feature.get("id") == feature_id:
            return feature
    return None


def _next_feature_id(features: dict) -> str:
    highest = 0
    for feature in features.get("features") or []:
        match = re.fullmatch(r"F-(\d+)", str(feature.get("id") or ""))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"F-{highest + 1:03d}"


def _extract_feature_id(*texts: str) -> str:
    for text in texts:
        match = FEATURE_ID_RE.search(text or "")
        if match:
            return match.group(0)
    return ""


def _pr_number_from_url(url: str) -> int | None:
    match = PR_NUMBER_RE.search(url or "")
    return int(match.group(1)) if match else None


def _is_sync_pr(pr: GitHubPR) -> bool:
    return (pr.head_ref or "").startswith(SYNC_BRANCH_PREFIX) or (pr.author or "").endswith("[bot]")


def _history_has(feature: dict, status: str, note: str) -> bool:
    return any(
        entry.get("status") == status and entry.get("note") == note for entry in feature.get("history") or []
    )


def _add_history(feature: dict, status: str, note: str) -> None:
    if _history_has(feature, status, note):
        return
    history = feature.get("history") or []
    history.append(
        {
            "status": status,
            "at": today_str(),
            "by": "harness-github",
            "note": note,
        }
    )
    feature["history"] = history


def _slugify(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", (text or "").lower()).strip("-")
    return slug


def _plan_rel_path(feature_id: str, title: str) -> str:
    slug = _slugify(title) or feature_id.lower().replace("-", "")
    return f".harness/changes/active/{today_str()}-{feature_id.lower()}-{slug}.md"


def _new_feature(features: dict, feature_id: str, title: str, status: str = "todo") -> dict:
    git_sync = features.get("git_sync") or {}
    plan = _plan_rel_path(feature_id, title)
    return {
        "id": feature_id,
        "title": title,
        "plan": plan,
        "status": status,
        "owner": "owner",
        "repo": git_sync.get("repo", ""),
        "branch": "",
        "commit": "",
        "push_status": "none",
        "pr_url": "",
        "remote_branch": "",
        "sync_repos": [],
        "depends_on": [],
        "issue_id": "",
        "issue_number": None,
        "issue_url": "",
        "pr_number": None,
        "last_synced_at": today_str(),
        "github_updated_at": "",
        "acceptance": [],
        "blocked_by": [],
        "pipeline": {"status": "not_started", "artifacts": [], "last_run": ""},
        "updated_at": today_str(),
        "history": [
            {
                "status": "todo",
                "at": today_str(),
                "by": "harness-github",
                "note": "created from GitHub sync",
            }
        ],
    }


def _create_feature_actions(
    actions: list[dict],
    features: dict,
    feature_id: str,
    title: str,
    status: str = "todo",
) -> None:
    feature = _new_feature(features, feature_id, title, status)
    features.setdefault("features", []).append(feature)
    actions.append({"type": "create_feature", "feature_id": feature_id, "title": title})
    actions.append({"type": "create_plan", "path": feature["plan"], "feature_id": feature_id, "title": title})


def _apply_issue(actions: list[dict], features: dict, issue: GitHubIssue) -> None:
    feature_id = _extract_feature_id(issue.title, issue.body)
    issue_title = issue.title or f"Issue #{issue.number}"
    if not feature_id:
        if issue.state == "closed":
            return
        feature_id = _next_feature_id(features)
        _create_feature_actions(actions, features, feature_id, issue_title)
        actions.append(
            {
                "type": "update_issue_body",
                "issue_number": issue.number,
                "feature_id": feature_id,
                "body": issue.body,
            }
        )

    feature = _find_feature(features, feature_id)
    if feature is None:
        _create_feature_actions(actions, features, feature_id, issue_title)
        feature = _find_feature(features, feature_id)
    if feature is None:
        return
    clean_title = re.sub(rf"^{re.escape(feature_id)}:\s*", "", issue_title).strip()

    if feature.get("issue_number") != issue.number:
        feature["issue_number"] = issue.number
        feature["issue_id"] = str(issue.number)
        feature["issue_url"] = issue.url
        feature["github_updated_at"] = issue.updated_at
        _add_history(feature, "todo", f"linked to issue #{issue.number}")
        actions.append(
            {
                "type": "link_issue",
                "feature_id": feature_id,
                "issue_number": issue.number,
            }
        )

    if feature.get("status") in ("todo", "in_progress", "blocked") and feature.get("title") != clean_title:
        feature["title"] = clean_title
        feature["updated_at"] = today_str()
        actions.append(
            {
                "type": "sync_title",
                "feature_id": feature_id,
                "issue_number": issue.number,
            }
        )

    note = f"GitHub issue #{issue.number} closed without merge"
    if issue.state == "closed":
        if feature.get("status") not in ("merged", "done"):
            blocked = feature.get("blocked_by") or []
            if feature.get("status") != "blocked" or note not in blocked:
                feature["status"] = "blocked"
                if note not in blocked:
                    blocked.append(note)
                feature["blocked_by"] = blocked
                _add_history(feature, "blocked", note)
                actions.append(
                    {
                        "type": "mark_blocked",
                        "feature_id": feature_id,
                        "issue_number": issue.number,
                    }
                )
    else:
        blocked = feature.get("blocked_by") or []
        if feature.get("status") == "blocked" and note in blocked:
            blocked.remove(note)
            feature["blocked_by"] = blocked
            feature["status"] = "in_progress"
            _add_history(feature, "in_progress", f"issue #{issue.number} reopened")
            actions.append(
                {
                    "type": "unblock",
                    "feature_id": feature_id,
                    "issue_number": issue.number,
                }
            )
        if feature.get("status") in ("merged", "done"):
            actions.append(
                {
                    "type": "close_issue",
                    "feature_id": feature_id,
                    "issue_number": issue.number,
                }
            )


def _apply_pr(actions: list[dict], features: dict, pr: GitHubPR) -> None:
    if _is_sync_pr(pr):
        return
    feature_id = _extract_feature_id(pr.head_ref, pr.title, pr.body)
    if not feature_id:
        return

    feature = _find_feature(features, feature_id)
    if feature is None:
        title = pr.title
        match = re.match(r"^(?:feat|fix|chore|docs|refactor)(\([^)]*\))?:\s*", title or "")
        if match:
            title = title[match.end() :]
        status = "merged" if pr.merged else "pushed"
        _create_feature_actions(actions, features, feature_id, title or f"PR #{pr.number}", status)
        feature = _find_feature(features, feature_id)
        if feature is not None:
            feature["branch"] = pr.head_ref
            feature["pr_url"] = pr.url
            feature["pr_number"] = pr.number
            feature["push_status"] = "merged" if pr.merged else "pushed"
            feature["commit"] = pr.merge_commit_sha or ""
            _add_history(feature, status, f"linked to PR #{pr.number}")
    if feature is None:
        return

    feature_done = feature.get("status") in ("merged", "done")
    primary_match = pr.merged and bool(pr.merge_commit_sha) and pr.merge_commit_sha == feature.get("commit")
    should_link = (
        not feature_done and (feature.get("pr_number") is None or pr.state == "open")
    ) or primary_match
    if should_link and (feature.get("pr_number") != pr.number or feature.get("pr_url") != pr.url):
        feature["pr_number"] = pr.number
        feature["pr_url"] = pr.url
        feature["github_updated_at"] = pr.updated_at
        _add_history(feature, "pushed", f"linked to PR #{pr.number}")
        actions.append(
            {
                "type": "link_pr",
                "feature_id": feature_id,
                "pr_number": pr.number,
            }
        )

    if not feature.get("branch"):
        feature["branch"] = pr.head_ref

    issue_number = feature.get("issue_number")
    if issue_number and not feature_done and not ISSUE_CLOSE_RE.search(pr.body or ""):
        actions.append(
            {
                "type": "update_pr_body",
                "pr_number": pr.number,
                "feature_id": feature_id,
                "issue_number": issue_number,
                "body": pr.body or "",
            }
        )

    if pr.state == "open":
        if feature.get("status") in ("todo", "in_progress", "ready_for_review", "committed", "pushed"):
            if feature.get("status") != "pushed":
                feature["status"] = "pushed"
                _add_history(feature, "pushed", f"PR #{pr.number} opened")
            if feature.get("push_status") != "pushed":
                feature["push_status"] = "pushed"
    elif pr.merged:
        merge_sha = pr.merge_commit_sha or feature.get("commit") or ""
        just_created = any(
            action.get("type") == "create_feature" and action.get("feature_id") == feature_id
            for action in actions
        )
        already_merged = (
            feature.get("status") in ("merged", "done") and feature.get("push_status") == "merged"
        )
        changed = just_created or not already_merged
        if changed:
            feature["status"] = "merged"
            feature["push_status"] = "merged"
            if merge_sha and (just_created or not already_merged or not feature.get("commit")):
                feature["commit"] = merge_sha
            feature["pr_number"] = pr.number
            feature["pr_url"] = pr.url
            _add_history(feature, "merged", f"merged via PR #{pr.number} (auto-synced)")
            actions.append(
                {
                    "type": "merged",
                    "feature_id": feature_id,
                    "pr_number": pr.number,
                    "commit": merge_sha,
                }
            )
            actions.append({"type": "archive", "feature_id": feature_id})
            if issue_number:
                actions.append(
                    {
                        "type": "close_issue",
                        "feature_id": feature_id,
                        "issue_number": issue_number,
                    }
                )
    elif feature.get("status") == "pushed" and feature.get("pr_number") == pr.number:
        feature["status"] = "in_progress"
        feature["pr_url"] = ""
        feature["pr_number"] = None
        _add_history(feature, "in_progress", f"PR #{pr.number} closed without merge")
        actions.append(
            {
                "type": "pr_closed_unmerged",
                "feature_id": feature_id,
                "pr_number": pr.number,
            }
        )


def reconcile_ledger(
    features: dict,
    issues: list[GitHubIssue],
    prs: list[GitHubPR],
) -> tuple[dict, list[dict]]:
    result = copy.deepcopy(features)
    actions: list[dict] = []
    for issue in issues:
        _apply_issue(actions, result, issue)
    for pr in prs:
        _apply_pr(actions, result, pr)
    if actions:
        result["updated_at"] = today_str()
    return result, actions


def _github_repo(root: Path) -> str:
    features = _load_ledger(root)
    git_sync = features.get("git_sync") or {}
    remote = git_sync.get("remote", "")
    match = re.search(r"(?:github\.com[:/])([^/\s]+/[^/\s]+?)(?:\.git)?$", remote)
    if match:
        return match.group(1)
    repo = git_sync.get("repo", "")
    if repo and "/" in repo:
        return repo
    proc = run_cmd(["git", "remote", "get-url", "origin"], cwd=root)
    url = (proc.stdout or "").strip()
    match = re.search(r"(?:github\.com[:/])([^/\s]+/[^/\s]+?)(?:\.git)?$", url)
    if match:
        return match.group(1)
    raise HarnessError("GitHub repo not found in git_sync.repo or origin remote")


def _gh_available() -> bool:
    return shutil.which("gh") is not None


def _fetch_github_state(root: Path) -> tuple[list[GitHubIssue], list[GitHubPR]]:
    repo = _github_repo(root)
    issues_proc = run_cmd(["gh", "api", f"repos/{repo}/issues?state=all&per_page=100"], cwd=root)
    if issues_proc.returncode != 0:
        raise HarnessError(f"gh api issues failed: {(issues_proc.stdout + issues_proc.stderr).strip()}")
    prs_proc = run_cmd(["gh", "api", f"repos/{repo}/pulls?state=all&per_page=100"], cwd=root)
    if prs_proc.returncode != 0:
        raise HarnessError(f"gh api pulls failed: {(prs_proc.stdout + prs_proc.stderr).strip()}")

    issues: list[GitHubIssue] = []
    for item in json.loads(issues_proc.stdout or "[]"):
        if "pull_request" in item:
            continue
        issues.append(
            GitHubIssue(
                number=int(item.get("number", 0)),
                title=str(item.get("title") or ""),
                body=str(item.get("body") or ""),
                state=str(item.get("state") or "open"),
                url=str(item.get("html_url") or ""),
                updated_at=str(item.get("updated_at") or ""),
                labels=[str(label.get("name") or "") for label in item.get("labels") or []],
            )
        )

    prs: list[GitHubPR] = []
    for item in json.loads(prs_proc.stdout or "[]"):
        prs.append(
            GitHubPR(
                number=int(item.get("number", 0)),
                title=str(item.get("title") or ""),
                body=str(item.get("body") or ""),
                state=str(item.get("state") or "open"),
                merged=bool(item.get("merged_at")),
                merge_commit_sha=str(item.get("merge_commit_sha") or ""),
                head_ref=str(item.get("head", {}).get("ref") or ""),
                url=str(item.get("html_url") or ""),
                updated_at=str(item.get("updated_at") or ""),
                author=str(item.get("user", {}).get("login") or ""),
            )
        )
    return issues, prs


def _current_pr_number() -> int | None:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path or not Path(event_path).exists():
        return None
    try:
        event = json.loads(Path(event_path).read_text(encoding="utf-8-sig"))
        pr = event.get("pull_request") or {}
        return int(pr.get("number")) if pr.get("number") else None
    except Exception:
        return None


def _ci_allowed_change(change: dict) -> bool:
    if change.get("type") != "link_pr":
        return False
    return change.get("pr_number") == _current_pr_number()


def _insert_index_row(index_text: str, table_title: str, row: str) -> str:
    if row in index_text:
        return index_text
    lines = index_text.splitlines()
    result: list[str] = []
    in_table = False
    for index, line in enumerate(lines):
        result.append(line)
        if line.startswith(f"## {table_title}"):
            in_table = True
            continue
        if in_table and line.startswith("| ---"):
            result.append(row)
            in_table = False
    return "\n".join(result)


def _update_completed_index(root: Path, feature: dict) -> None:
    path = root / ".harness" / "changes" / "completed" / "INDEX.md"
    if not path.exists():
        return
    text = read_text(path)
    repo = root / ".harness" / "changes" / "active" / "feature-list.json"
    features = read_json(repo)
    repo_name = (features.get("git_sync") or {}).get("repo", "agentops-harness")
    plan = feature.get("plan") or ""
    archive_name = Path(plan).name if plan else ""
    link = f"[archive/{archive_name}](archive/{archive_name})" if archive_name else ""
    feature_id = feature.get("id", "")
    row = (
        f"| {today_str()} | {feature.get('title', '')} | {link} | "
        f"本次 {feature_id} 提交 | 本次 {feature_id} PR | {repo_name} |"
    )
    text = _insert_index_row(text, "完成记录", row)
    row = (
        f"| {today_str()} | 执行计划：{feature.get('title', '')}（{feature_id}） | {link} | "
        f"本次 {feature_id} 提交 | 本次 {feature_id} PR | {repo_name} |"
    )
    text = _insert_index_row(text, "归档计划", row)
    write_text(path, text)


def _update_progress(root: Path, feature: dict) -> None:
    path = root / ".harness" / "PROGRESS.md"
    if not path.exists():
        return
    text = read_text(path)
    feature_id = feature.get("id", "")
    bullet = f"- {feature_id} {feature.get('title', '')}"
    if bullet not in text:
        lines = text.splitlines()
        result: list[str] = []
        inserted = False
        for line in lines:
            if line.startswith("## 已完成") and not inserted:
                result.append(line)
                result.append(
                    f"- {feature_id} {feature.get('title', '')}："
                    "GitHub Issue/PR 双向同步已自动归档（PR #auto-sync）。"
                )
                inserted = True
                continue
            result.append(line)
        text = "\n".join(result)
    lines = text.splitlines()
    result = []
    in_progress_section = False
    for line in lines:
        if line.startswith("## 进行中"):
            in_progress_section = True
        elif line.startswith("## ") and line != "## 进行中":
            in_progress_section = False
        if in_progress_section and line.startswith(f"- {feature_id} "):
            continue
        if line.startswith("- 当前状态：") and "in_progress" in line:
            result.append("- 当前状态：`merged`")
        else:
            result.append(line)
    write_text(path, "\n".join(result))


def _sync_progress_date(root: Path, updated_at: str) -> None:
    path = root / ".harness" / "PROGRESS.md"
    if not path.exists():
        return
    lines = []
    for line in read_text(path).splitlines():
        if line.startswith("- 更新日期："):
            lines.append(f"- 更新日期：{updated_at}")
        else:
            lines.append(line)
    write_text(path, "\n".join(lines))


def _write_plan_file(root: Path, path: str, feature_id: str, title: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return
    write_text(
        target,
        f"""# 执行计划：{title}

> 状态：draft
> 目标 Feature：{feature_id}

## 目标

{title}

## 验收标准

- 待补充：可验证的验收条件

## 当前状态

- 状态：draft
- 当前进展：
- 阻塞点：
""",
    )


def _archive_feature(root: Path, features: dict, feature_id: str) -> None:
    feature = _find_feature(features, feature_id)
    if feature is None:
        return
    plan = feature.get("plan") or ""
    active_dir = root / ".harness" / "changes" / "active"
    archive_dir = root / ".harness" / "changes" / "completed" / "archive"
    if plan and active_dir.exists() and (active_dir / Path(plan).name).exists():
        archive_dir.mkdir(parents=True, exist_ok=True)
        source = active_dir / Path(plan).name
        target = archive_dir / Path(plan).name
        source.replace(target)
        feature["plan"] = f".harness/changes/completed/archive/{Path(plan).name}"
    _update_completed_index(root, feature)
    _update_progress(root, feature)


def _run_gh_issue_edit(root: Path, repo: str, number: int, body: str) -> None:
    proc = run_cmd(["gh", "issue", "edit", str(number), "--repo", repo, "--body", body], cwd=root)
    if proc.returncode != 0:
        raise HarnessError(f"gh issue edit failed: {(proc.stdout + proc.stderr).strip()}")


def _run_gh_pr_edit(root: Path, repo: str, number: int, body: str) -> None:
    proc = run_cmd(["gh", "pr", "edit", str(number), "--repo", repo, "--body", body], cwd=root)
    if proc.returncode != 0:
        raise HarnessError(f"gh pr edit failed: {(proc.stdout + proc.stderr).strip()}")


def _run_gh_issue_close(root: Path, repo: str, number: int, comment: str) -> None:
    state_proc = run_cmd(
        ["gh", "api", f"repos/{repo}/issues/{number}", "--jq", ".state"],
        cwd=root,
    )
    if state_proc.returncode == 0 and state_proc.stdout.strip() == "closed":
        print(f"[github-sync] issue #{number} already closed; skipping close")
        return
    proc = run_cmd(["gh", "issue", "close", str(number), "--repo", repo, "--comment", comment], cwd=root)
    if proc.returncode != 0:
        raise HarnessError(f"gh issue close failed: {(proc.stdout + proc.stderr).strip()}")


def _apply_actions(root: Path, features: dict, actions: list[dict]) -> None:
    repo = _github_repo(root)
    for action in actions:
        kind = action.get("type")
        if kind == "create_plan":
            _write_plan_file(root, action["path"], action["feature_id"], action["title"])
        elif kind == "update_issue_body":
            body = action.get("body") or ""
            feature_id = action["feature_id"]
            if f"Feature ID: {feature_id}" not in body:
                body = f"{body}\n\nFeature ID: {feature_id}".strip()
            _run_gh_issue_edit(root, repo, action["issue_number"], body)
        elif kind == "update_pr_body":
            body = action.get("body") or ""
            feature_id = action["feature_id"]
            issue_number = action.get("issue_number")
            additions = [f"Feature ID: {feature_id}"]
            if issue_number:
                additions.append(f"Closes #{issue_number}")
            if f"Feature ID: {feature_id}" not in body:
                body = f"{body}\n\n## Related\n- " + "\n- ".join(additions)
            _run_gh_pr_edit(root, repo, action["pr_number"], body)
        elif kind == "archive":
            _archive_feature(root, features, action["feature_id"])
        elif kind == "close_issue":
            _run_gh_issue_close(
                root,
                repo,
                action["issue_number"],
                f"Closed automatically: {action.get('feature_id', '')} merged.",
            )
    knowledge_mod.build_index(root)
    features["updated_at"] = today_str()
    _sync_progress_date(root, features["updated_at"])
    _save_ledger(root, features)


def _commit_and_transport(root: Path, transport: str, actions: list[dict]) -> int:
    proc = run_cmd(["git", "add", "-A"], cwd=root)
    if proc.returncode != 0:
        raise HarnessError(f"git add failed: {(proc.stdout + proc.stderr).strip()}")
    status_proc = run_cmd(["git", "status", "--porcelain"], cwd=root)
    if not [line for line in status_proc.stdout.splitlines() if line.strip()]:
        print("[github-sync] no files changed after apply")
        return 0

    feature_ids = sorted(
        {str(action.get("feature_id") or "") for action in actions if action.get("feature_id")}
    )
    if len(feature_ids) == 1:
        message = f"chore({feature_ids[0]}): sync GitHub issue/PR state Ref: {feature_ids[0]}"
    else:
        message = "chore(harness): sync GitHub issue/PR state"
    commit_proc = run_cmd(["git", "commit", "-m", message], cwd=root)
    if commit_proc.returncode != 0:
        raise HarnessError(f"git commit failed: {(commit_proc.stdout + commit_proc.stderr).strip()}")

    if transport == "local":
        print("[github-sync] ledger changes committed locally")
        return 0

    if transport == "direct":
        push_proc = run_cmd(["git", "push", "origin", "main"], cwd=root)
        if push_proc.returncode != 0:
            raise HarnessError(f"git push main failed: {(push_proc.stdout + push_proc.stderr).strip()}")
        print("[github-sync] direct push to main completed")
        return 0

    event_name = os.environ.get("GITHUB_EVENT_NAME", "manual")
    event_number = os.environ.get("GITHUB_EVENT_NUMBER", "manual")
    head_sha = run_cmd(["git", "rev-parse", "--short", "HEAD"], cwd=root).stdout.strip()
    branch = f"{SYNC_BRANCH_PREFIX}{event_name}-{event_number}-{head_sha}"
    branch_proc = run_cmd(["git", "checkout", "-b", branch], cwd=root)
    if branch_proc.returncode != 0:
        raise HarnessError(f"git checkout -b failed: {(branch_proc.stdout + branch_proc.stderr).strip()}")
    push_proc = run_cmd(["git", "push", "-u", "origin", branch], cwd=root)
    if push_proc.returncode != 0:
        raise HarnessError(f"git push failed: {(push_proc.stdout + push_proc.stderr).strip()}")

    feature_ids_text = ", ".join(feature_ids) if feature_ids else "none"
    body = (
        "## Summary\n\n"
        "Automatic harness state sync from GitHub issue/PR events.\n\n"
        f"Feature ID: {feature_ids_text}\n\n"
        "## Verification\n\n"
        "- `harness github sync --strict`\n"
        "- `harness check`"
    )
    title = "chore(harness): sync GitHub state"
    pr_proc = run_cmd(
        ["gh", "pr", "create", "--base", "main", "--head", branch, "--title", title, "--body", body],
        cwd=root,
    )
    if pr_proc.returncode != 0:
        raise HarnessError(f"gh pr create failed: {(pr_proc.stdout + pr_proc.stderr).strip()}")
    url = [line for line in pr_proc.stdout.splitlines() if line.strip()][-1].strip()
    auto_proc = run_cmd(["gh", "pr", "merge", url, "--auto", "--squash"], cwd=root)
    if auto_proc.returncode != 0:
        raise HarnessError(f"gh pr merge --auto failed: {(auto_proc.stdout + auto_proc.stderr).strip()}")
    print(f"[github-sync] state PR created with auto-merge: {url}")
    return 0


def cmd_github_sync(root: Path, apply: bool = False, strict: bool = False, transport: str = "pr") -> int:
    if not _gh_available():
        print("error: gh CLI is required for github sync", file=sys.stderr)
        return 1
    features = _load_ledger(root)
    issues, prs = _fetch_github_state(root)
    updated, actions = reconcile_ledger(features, issues, prs)

    if not actions:
        print("[github-sync] up to date")
        return 0

    for action in actions:
        print(f"[github-sync] pending: {action.get('type')} {action.get('feature_id', '')}")

    if not apply:
        if strict:
            blocking = [action for action in actions if not _ci_allowed_change(action)]
            if blocking:
                print("[github-sync] strict check failed: ledger is out of sync", file=sys.stderr)
                return 1
            print("[github-sync] strict check passed (only current PR linkage pending)")
            return 0
        print("[github-sync] dry-run: run with --apply to apply changes")
        return 1

    _apply_actions(root, updated, actions)
    return _commit_and_transport(root, transport, actions)


def cmd_github_issue_create(root: Path, feature_id: str) -> int:
    if not _gh_available():
        print("error: gh CLI is required for issue-create", file=sys.stderr)
        return 1
    features = _load_ledger(root)
    feature = _find_feature(features, feature_id)
    if feature is None:
        raise HarnessError(f"Feature not found: {feature_id}")
    repo = _github_repo(root)
    acceptance = "\n".join(f"- {item}" for item in feature.get("acceptance") or []) or "- 待补充"
    body = f"Feature ID: {feature_id}\n\n## 目标\n\n{feature.get('title', '')}\n\n## 验收标准\n\n{acceptance}"
    title = f"{feature_id}: {feature.get('title', '')}"
    proc = run_cmd(["gh", "issue", "create", "--repo", repo, "--title", title, "--body", body], cwd=root)
    if proc.returncode != 0:
        raise HarnessError(f"gh issue create failed: {(proc.stdout + proc.stderr).strip()}")
    url = [line for line in proc.stdout.splitlines() if line.strip()][-1].strip()
    number = _pr_number_from_url(url)
    if number is None:
        number_match = re.search(r"issues/(\d+)$", url)
        number = int(number_match.group(1)) if number_match else None
    if number is None:
        raise HarnessError(f"Cannot parse issue number from: {url}")
    feature["issue_number"] = number
    feature["issue_id"] = str(number)
    feature["issue_url"] = url
    _add_history(feature, "todo", f"issue created: {url}")
    features["updated_at"] = today_str()
    _sync_progress_date(root, features["updated_at"])
    _save_ledger(root, features)
    knowledge_mod.build_index(root)
    add_proc = run_cmd(["git", "add", "-A"], cwd=root)
    if add_proc.returncode == 0:
        commit_proc = run_cmd(
            ["git", "commit", "-m", f"chore({feature_id}): link GitHub issue Ref: {feature_id}"],
            cwd=root,
        )
        if commit_proc.returncode != 0:
            detail = (commit_proc.stdout + commit_proc.stderr).strip()
            print(f"[github-sync] issue link commit skipped: {detail}")
    print(f"[github-sync] issue created: {url}")
    return 0
