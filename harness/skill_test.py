from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import yaml

from .common import read_text
from .skill_contract import iter_skill_dirs

CHECK_TYPES = ("exit_code", "file_exists", "contains", "not_contains")
RUN_TIMEOUT_SECONDS = 120


def _run_shell(command: str, cwd: Path) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            command,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=RUN_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=command,
            returncode=124,
            stdout="",
            stderr=f"timed out after {RUN_TIMEOUT_SECONDS}s",
        )


def _load_checks(case_dir: Path) -> dict[str, Any]:
    path = case_dir / "checks.yaml"
    data = yaml.safe_load(read_text(path))
    if not isinstance(data, dict):
        raise ValueError("checks.yaml must be a mapping")
    if data.get("schema_version") != "1.0":
        raise ValueError("checks.yaml schema_version must be 1.0")
    if "run" in data and not isinstance(data["run"], str):
        raise ValueError("checks.yaml run must be a string")
    checks = data.get("checks") or []
    if not isinstance(checks, list):
        raise ValueError("checks.yaml checks must be a list")
    for check in checks:
        if not isinstance(check, dict):
            raise ValueError("each check must be a mapping")
        if check.get("type") not in CHECK_TYPES:
            raise ValueError(f"unknown check type: {check.get('type')}")
    return data


def _resolved_in_workdir(workdir: Path, relative: str) -> Path | None:
    base = workdir.resolve()
    target = (workdir / relative).resolve()
    if not target.is_relative_to(base):
        return None
    return target


def _apply_checks(
    workdir: Path,
    checks: dict[str, Any],
    run_result: subprocess.CompletedProcess | None,
    errors: list[str],
) -> None:
    for check in checks.get("checks") or []:
        check_type = check.get("type")
        if check_type not in CHECK_TYPES:
            errors.append(f"unknown check type: {check_type}")
            continue
        if check_type == "exit_code":
            expected = check.get("expected", 0)
            actual = run_result.returncode if run_result is not None else -1
            if actual != expected:
                errors.append(f"exit_code expected {expected}, got {actual}")
        elif check_type == "file_exists":
            path = _resolved_in_workdir(workdir, str(check.get("path", "")))
            if path is None:
                errors.append(f"path escapes fixture workdir: {check.get('path')}")
            elif not path.exists():
                errors.append(f"file not found: {check.get('path')}")
        elif check_type in ("contains", "not_contains"):
            path = _resolved_in_workdir(workdir, str(check.get("path", "")))
            text = str(check.get("text", ""))
            if path is None:
                errors.append(f"path escapes fixture workdir: {check.get('path')}")
            elif not path.exists():
                errors.append(f"file not found: {check.get('path')}")
            else:
                content = read_text(path)
                if check_type == "contains" and text not in content:
                    errors.append(f"missing text in {check.get('path')}: {text}")
                if check_type == "not_contains" and text in content:
                    errors.append(f"forbidden text in {check.get('path')}: {text}")


def _run_case(case_dir: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "case": case_dir.name,
        "ok": None,
        "manual": False,
        "errors": [],
        "duration": 0.0,
    }
    if not (case_dir / "task.md").exists():
        result["errors"].append("missing task.md")
        result["ok"] = False
        return result
    if not (case_dir / "checks.yaml").exists():
        result["manual"] = True
        result["ok"] = None
        return result

    try:
        checks = _load_checks(case_dir)
    except Exception as exc:
        result["errors"].append(f"invalid checks.yaml: {exc}")
        result["ok"] = False
        return result

    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="harness-skill-") as tmp:
        workdir = Path(tmp)
        fixture = case_dir / "fixture"
        if fixture.exists():
            shutil.copytree(fixture, workdir, dirs_exist_ok=True)

        for command in checks.get("setup") or []:
            proc = _run_shell(command, workdir)
            if proc.returncode != 0:
                result["errors"].append(f"setup failed: {command}\n{proc.stdout + proc.stderr}")
                break

        run_command = str(checks.get("run") or "").strip()
        run_result = _run_shell(run_command, workdir) if run_command else None
        if run_result is not None and run_result.returncode != 0:
            output = (run_result.stdout + run_result.stderr).strip()
            result["errors"].append(f"run failed ({run_result.returncode}): {run_command}\n{output}")

        _apply_checks(workdir, checks, run_result, result["errors"])
    result["duration"] = round(time.monotonic() - started, 3)
    result["ok"] = not result["errors"]
    return result


def run_skill_tests(
    root: Path,
    skill_id: str | None = None,
    smoke: bool = False,
) -> tuple[int, list[dict[str, Any]]]:
    skill_dirs = [path for path in iter_skill_dirs(root) if skill_id is None or path.name == skill_id]
    if skill_id and not skill_dirs:
        print(f"[skill test] skill not found: {skill_id}")
        return 1, []

    all_results: list[dict[str, Any]] = []
    failed = False
    automated = 0
    for skill_dir in skill_dirs:
        fixtures = skill_dir / "fixtures"
        if not fixtures.exists():
            continue
        cases = sorted(path for path in fixtures.iterdir() if path.is_dir())
        if smoke and cases:
            cases = cases[:1]
        for case_dir in cases:
            result = _run_case(case_dir)
            result["skill"] = skill_dir.name
            automated += 0 if result["manual"] else 1
            if result["ok"] is False:
                failed = True
            all_results.append(result)

    passed = sum(1 for item in all_results if item["ok"] is True)
    manual = sum(1 for item in all_results if item["manual"])
    print(
        f"[skill test] {len(all_results)} case(s), {passed} passed, "
        f"{len(all_results) - passed - manual} failed, {manual} manual"
    )
    for item in all_results:
        if item["manual"]:
            print(f"  {item['skill']}/{item['case']}: manual")
        elif item["ok"]:
            print(f"  {item['skill']}/{item['case']}: pass ({item['duration']}s)")
        else:
            print(f"  {item['skill']}/{item['case']}: FAIL ({item['duration']}s)")
            for error in item["errors"]:
                print(f"    - {error}")
    return (1 if failed else 0), all_results
