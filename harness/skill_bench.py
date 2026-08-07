from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path
from typing import Any

from .common import write_text
from .skill_test import run_skill_tests

BENCH_SCHEMA_VERSION = "1.0"


def _baseline_path(root: Path) -> Path:
    return root / ".harness" / "benchmarks" / "skills" / "baseline.json"


def _summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    automated = [item for item in results if not item["manual"]]
    passed = sum(1 for item in automated if item["ok"] is True)
    failed = sum(1 for item in automated if item["ok"] is False)
    return {
        "cases": len(automated),
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / len(automated), 4) if automated else 0.0,
        "duration": round(sum(item.get("duration", 0.0) for item in automated), 3),
    }


def _automated_keys(results: list[dict[str, Any]]) -> set[str]:
    return {f"{item['skill']}/{item['case']}" for item in results if not item["manual"]}


def _failing_keys(results: list[dict[str, Any]]) -> set[str]:
    return {
        f"{item['skill']}/{item['case']}" for item in results if not item["manual"] and item["ok"] is False
    }


def run_skill_bench(root: Path, save: bool = False, compare: bool = False) -> int:
    started = time.monotonic()
    test_code, results = run_skill_tests(root)
    summary = _summarize(results)
    summary["duration"] = round(time.monotonic() - started, 3)
    if test_code != 0:
        print("[skill bench] tests failed; benchmark aborted")
        return 1
    if summary["cases"] == 0:
        print("[skill bench] no automated fixtures; benchmark requires at least one automated case")
        return 1

    data = {
        "schema_version": BENCH_SCHEMA_VERSION,
        "updated_at": date.today().isoformat(),
        "summary": summary,
        "results": results,
    }

    path = _baseline_path(root)
    if save:
        path.parent.mkdir(parents=True, exist_ok=True)
        write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        print(f"[skill bench] baseline saved: {path}")

    regression = False
    if compare:
        if not path.exists():
            print("[skill bench] no baseline found; run with --save first")
            return 1
        baseline = json.loads(path.read_text(encoding="utf-8-sig"))
        base_summary = baseline.get("summary") or {}
        base_failed = base_summary.get("failed", 0)
        if base_summary.get("cases", 0) == 0 or base_failed > 0:
            print("[skill bench] baseline is empty or contains failures; re-run with --save")
            return 1
        if summary["failed"] > base_failed:
            print(f"[skill bench] regression: failed {base_failed} -> {summary['failed']}")
            regression = True
        if summary["pass_rate"] < base_summary.get("pass_rate", 1.0):
            print(
                f"[skill bench] regression: pass rate "
                f"{base_summary.get('pass_rate')} -> {summary['pass_rate']}"
            )
            regression = True
        baseline_results = baseline.get("results") or []
        removed = _automated_keys(baseline_results) - _automated_keys(results)
        if removed:
            print(f"[skill bench] regression: removed automated cases: {', '.join(sorted(removed))}")
            regression = True
        base_failing = {
            f"{item['skill']}/{item['case']}"
            for item in baseline_results
            if not item.get("manual") and item.get("ok") is False
        }
        new_failures = _failing_keys(results) - base_failing
        if new_failures:
            print(f"[skill bench] new failing cases: {', '.join(sorted(new_failures))}")
            regression = True

    print(
        f"[skill bench] {summary['cases']} case(s), {summary['passed']} passed, "
        f"{summary['failed']} failed, pass rate {summary['pass_rate']}, {summary['duration']}s"
    )
    return 1 if regression else 0
