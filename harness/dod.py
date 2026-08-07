from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from .common import read_text

PR_TITLE_RE = re.compile(r"^(feat|fix|chore|docs|refactor)(\([^)]*\))?: .+", re.IGNORECASE)


def _read_pr_event() -> dict:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path or not Path(event_path).exists():
        return {}
    try:
        data = json.loads(Path(event_path).read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    return data.get("pull_request") or {}


def run_dod(root: Path) -> int:
    errors = []

    feature_list = root / ".harness" / "changes" / "active" / "feature-list.json"
    if not feature_list.exists():
        errors.append("Missing feature-list.json (DoD)")
    else:
        try:
            data = json.loads(read_text(feature_list))
            if not isinstance(data, dict) or not data.get("features"):
                errors.append("feature-list.json has no features")
            else:
                for feature in data["features"]:
                    feature_id = feature.get("id")
                    if not feature_id or not feature.get("title"):
                        errors.append("feature missing id/title")
                    if feature.get("status") in ("in_progress", "committed", "pushed") and not feature.get(
                        "plan"
                    ):
                        errors.append(f"feature {feature_id} missing plan")
                    if feature.get("status") in ("committed", "pushed", "merged") and not feature.get(
                        "commit"
                    ):
                        errors.append(f"feature {feature_id} missing commit")
        except Exception as exc:
            errors.append(f"feature-list.json is not valid JSON: {exc}")

    for relative in ("AGENTS.md", "README.md", ".harness/dod.json", "pyproject.toml"):
        if not (root / relative).exists():
            errors.append(f"Missing DoD required file: {relative}")

    dod_config = root / ".harness" / "dod.json"
    if dod_config.exists():
        try:
            config = json.loads(read_text(dod_config))
            required_checks = config.get("required_checks") if isinstance(config, dict) else None
            if not isinstance(required_checks, list) or not all(
                isinstance(item, str) for item in required_checks
            ):
                errors.append("dod.json required_checks must be a list of strings")
            elif not required_checks:
                errors.append("dod.json required_checks must not be empty")
        except Exception as exc:
            errors.append(f"dod.json is not valid JSON: {exc}")

    pr = _read_pr_event()
    if pr:
        title = (pr.get("title") or "").strip()
        body = pr.get("body") or ""
        if not PR_TITLE_RE.match(title):
            errors.append(f"PR title must match feat/fix/chore/docs/refactor pattern: {title}")
        for section in ("## Summary", "## Verification", "Feature ID:"):
            if section not in body:
                errors.append(f"PR body missing section: {section}")
    else:
        print("[dod] PR metadata not available; PR checks skipped")

    print(f"[dod] {len(errors)} error(s)")
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    return 1 if errors else 0
