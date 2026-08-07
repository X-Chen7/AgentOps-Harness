from __future__ import annotations

import json
import sys
from pathlib import Path

from .check import COMPLETED_PLAN_RE, VALID_FEATURE_STATUSES, VALID_PUSH_STATUSES
from .common import git_repo_available, read_text, run_cmd


def _validate_feature_list(features: dict, errors: list[str]) -> None:
    feature_items = features.get("features") or []
    for feature in feature_items:
        feature_id = feature.get("id")
        if feature.get("status") not in VALID_FEATURE_STATUSES:
            errors.append(f"Invalid feature status: {feature_id} -> {feature.get('status')}")
        if feature.get("push_status") and feature["push_status"] not in VALID_PUSH_STATUSES:
            errors.append(f"Invalid push_status: {feature_id} -> {feature['push_status']}")
        if feature.get("status") in ("committed", "pushed", "merged") and not feature.get("commit"):
            errors.append(f"Feature {feature_id} status {feature.get('status')} requires commit")
        if feature.get("history"):
            for entry in feature["history"]:
                if not entry.get("status") or not entry.get("at") or not entry.get("by"):
                    errors.append(f"Feature {feature_id} history entry requires status/at/by")
    in_progress = sum(1 for f in feature_items if f.get("status") == "in_progress")
    wip_limit = features.get("wip_limit", 0) if isinstance(features.get("wip_limit"), int) else 0
    if in_progress > wip_limit:
        errors.append(f"WIP exceeded: {in_progress} in_progress, wip_limit={wip_limit}")


def sync_changes(root: Path, push_gate: bool = False) -> int:
    harness = root / ".harness"
    feature_list = harness / "changes" / "active" / "feature-list.json"
    progress = harness / "PROGRESS.md"
    errors: list[str] = []
    warnings: list[str] = []

    git_repo = git_repo_available(root)
    features: dict | None = None
    feature_items: list[dict] = []

    if not feature_list.exists():
        errors.append(f"Missing {feature_list}")
    else:
        try:
            parsed = json.loads(read_text(feature_list))
            features = parsed if isinstance(parsed, dict) else {}
            feature_items = features.get("features") or []
            _validate_feature_list(features, errors)
        except Exception as exc:
            errors.append(f"feature-list.json is not valid JSON: {exc}")

    if not progress.exists():
        errors.append(f"Missing {progress}")
    elif features and features.get("updated_at"):
        progress_text = read_text(progress)
        if features["updated_at"] not in progress_text:
            message = f"PROGRESS.md does not contain feature-list updated_at {features['updated_at']}"
            if push_gate:
                errors.append(message)
            else:
                warnings.append(message)

    active_dir = harness / "changes" / "active"
    if active_dir.exists():
        for file in sorted(active_dir.glob("*.md")):
            if file.name == "README.md":
                continue
            if COMPLETED_PLAN_RE.search(read_text(file)):
                errors.append(f"Completed plan still in active: {file.name}")

    if not git_repo:
        print("[sync-changes] not a git repository; git-specific checks skipped")
    else:
        diff_proc = run_cmd(["git", "diff", "--check"], cwd=root)
        if diff_proc.returncode != 0:
            errors.append(f"git diff --check failed: {(diff_proc.stdout + diff_proc.stderr).strip()}")
        status_proc = run_cmd(["git", "status", "--porcelain"], cwd=root)
        porcelain_lines = [line for line in status_proc.stdout.splitlines() if line.strip()]
        if porcelain_lines:
            message = f"{len(porcelain_lines)} uncommitted path(s) present before push"
            if push_gate:
                errors.append(message)
            else:
                warnings.append(message)
        if features:
            for feature in feature_items:
                feature_id = feature.get("id")
                if feature.get("commit"):
                    verify_proc = run_cmd(
                        ["git", "rev-parse", "--verify", f"{feature['commit']}^{{commit}}"], cwd=root
                    )
                    if verify_proc.returncode != 0:
                        errors.append(f"Feature {feature_id} references unknown commit: {feature['commit']}")
                branch = feature.get("branch")
                if branch and not branch.startswith("未"):
                    branch_proc = run_cmd(["git", "rev-parse", "--verify", f"refs/heads/{branch}"], cwd=root)
                    if branch_proc.returncode != 0:
                        warnings.append(f"Feature {feature_id} branch not found locally: {branch}")

    feature_summary = ", ".join(f"{f.get('id')}={f.get('status')}" for f in feature_items)
    print(f"[sync-changes] features: {feature_summary}")
    print(f"[sync-changes] {len(errors)} error(s), {len(warnings)} warning(s)")
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    return 0
