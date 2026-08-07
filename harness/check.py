from __future__ import annotations

import json
import os
import re
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path

from .common import git_repo_available, read_text, run_cmd, sha256_file
from .sqlcheck import run_sql_check

VALID_FEATURE_STATUSES = (
    "todo",
    "in_progress",
    "ready_for_review",
    "committed",
    "pushed",
    "merged",
    "blocked",
    "done",
)
VALID_PUSH_STATUSES = ("none", "local", "pushed", "merged")
VALID_PIPELINE_STATUSES = ("not_started", "running", "blocked", "done")
VALID_STAGE_STATUSES = ("queued", "running", "passed", "failed", "skipped")

AGENTS_IMPORT_RE = re.compile(r"(?m)^@\s*([^\r\n]+)")
AGENTS_PATH_RE = re.compile(r"\.harness/[^\s`\)\]\|\}]+")
COMPLETED_PLAN_RE = re.compile(r"状态：\s*(?:completed|已完成)", re.IGNORECASE)
INDEX_LINK_RE = re.compile(r"\]\(([^\)]+\.md)\)")
TECH_DEBT_RESOLVED_RE = re.compile(r"^\| TD-\d+ .*\| resolved \|", re.IGNORECASE)


class CheckContext:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)


def assert_no_dependency_cycle(ctx: CheckContext, stages: Sequence[dict], label: str) -> None:
    stage_ids = [stage.get("id") for stage in stages]
    resolved: list[str] = []
    remaining = list(stage_ids)
    while remaining:
        progress = False
        for stage_id in list(remaining):
            stage = next((s for s in stages if s.get("id") == stage_id), None)
            deps_ok = True
            for dep in stage.get("depends_on") or []:
                if dep not in resolved:
                    deps_ok = False
                    break
            if deps_ok:
                resolved.append(stage_id)
                remaining.remove(stage_id)
                progress = True
        if not progress:
            ctx.error(f"{label}: dependency cycle: {', '.join(str(x) for x in remaining)}")
            break


def assert_no_write_scope_conflict(ctx: CheckContext, stages: Sequence[dict], label: str) -> None:
    for i in range(len(stages)):
        for j in range(i + 1, len(stages)):
            a = stages[i]
            b = stages[j]
            a_deps = a.get("depends_on") or []
            b_deps = b.get("depends_on") or []
            if b.get("id") in a_deps or a.get("id") in b_deps:
                continue
            a_scope = a.get("write_scope") or []
            b_scope = b.get("write_scope") or []
            overlap = [x for x in a_scope if x in b_scope]
            if overlap:
                ctx.error(
                    f"{label}: parallel stages {a.get('id')} and {b.get('id')} "
                    f"have overlapping write_scope: {', '.join(overlap)}"
                )


def assert_active_stages(ctx: CheckContext, state: dict, label: str) -> None:
    if state.get("schema_version") != "1.1":
        return
    active_stages = state.get("active_stages")
    if active_stages is None:
        ctx.error(f"{label} missing active_stages for schema 1.1")
        return
    if isinstance(active_stages, str):
        active_stages = [active_stages]
    stages_by_id = {s.get("id"): s for s in state.get("stages") or []}
    for active_id in active_stages:
        stage = stages_by_id.get(active_id)
        if stage is None:
            ctx.error(f"{label} active_stages has unknown stage: {active_id}")
        elif stage.get("status") != "running":
            ctx.error(f"{label} active_stage not running: {active_id}")
        else:
            for dep in stage.get("depends_on") or []:
                dep_stage = stages_by_id.get(dep)
                if dep_stage is None or dep_stage.get("status") != "passed":
                    ctx.error(f"{label} active_stage dependency not passed: {active_id} -> {dep}")


def run_check(root: Path, strict: bool = False) -> tuple[list[str], list[str]]:
    ctx = CheckContext()
    harness = root / ".harness"

    agents = root / "AGENTS.md"
    agents_text = ""
    if not agents.exists():
        ctx.error("AGENTS.md is missing")
    else:
        agents_text = read_text(agents)
        scanned = agents_text
        for import_rel_raw in AGENTS_IMPORT_RE.findall(agents_text):
            import_rel = import_rel_raw.strip()
            import_path = root / import_rel
            if not import_path.exists():
                ctx.error(f"Broken AGENTS import: {import_rel}")
            else:
                scanned += "\n" + read_text(import_path)

        seen_paths: list[str] = []
        for match in AGENTS_PATH_RE.finditer(scanned):
            path = match.group(0).rstrip(".,;)]}")
            if path not in seen_paths:
                seen_paths.append(path)
        for path in seen_paths:
            candidate = root / re.sub(r"^\./", "", path)
            if not candidate.exists():
                ctx.error(f"Broken AGENTS path: {path}")

        if "frontend-backend-integration" not in scanned:
            ctx.error("AGENTS.md does not route frontend-backend-integration")

    if harness.exists():
        for file in harness.rglob("*-spec.md"):
            parts = file.relative_to(root).parts
            if any(part.lower() == "archive" or part.lower() == ".zread" for part in parts):
                continue
            ctx.error(f"Live spec draft found: {file}")

    skills_dir = harness / "skills"
    if (skills_dir / "skills").exists():
        ctx.error("Nested skills/skills directory still exists")
    if skills_dir.exists():
        for child in sorted(skills_dir.iterdir()):
            if child.is_dir() and not (child / "SKILL.md").exists():
                ctx.error(f"Skill directory has no SKILL.md: {child.name}")

    active_dir = harness / "changes" / "active"
    if active_dir.exists():
        for file in sorted(active_dir.glob("*.md")):
            if file.name == "README.md":
                continue
            if COMPLETED_PLAN_RE.search(read_text(file)):
                ctx.error(f"Completed plan still in active: {file.name}")

    if (harness / ".zread").exists():
        ctx.error(".harness/.zread should be moved to docs/zread/harness")

    if agents.exists():
        line_count = len(read_text(agents).splitlines())
        if line_count > 120:
            ctx.warning(f"AGENTS.md has {line_count} lines; keep near 100")

    progress = harness / "PROGRESS.md"
    if not progress.exists():
        ctx.error("Missing .harness/PROGRESS.md")

    feature_list = harness / "changes" / "active" / "feature-list.json"
    features: dict = {}
    feature_items: list[dict] = []
    if not feature_list.exists():
        ctx.error("Missing changes/active/feature-list.json")
    else:
        try:
            parsed = json.loads(read_text(feature_list))
            features = parsed if isinstance(parsed, dict) else {}
            feature_items = features.get("features") or []
            for feature in feature_items:
                feature_id = feature.get("id")
                if feature.get("status") not in VALID_FEATURE_STATUSES:
                    ctx.error(f"Invalid feature status: {feature_id} -> {feature.get('status')}")
                if feature.get("plan"):
                    plan_path = root / re.sub(r"^\./", "", feature["plan"])
                    if not plan_path.exists():
                        ctx.error(f"Broken feature plan link: {feature['plan']}")
            in_progress = sum(1 for f in feature_items if f.get("status") == "in_progress")
            wip_limit = features.get("wip_limit", 0) if isinstance(features.get("wip_limit"), int) else 0
            if in_progress > wip_limit:
                ctx.error(f"WIP exceeded: {in_progress} in_progress, wip_limit={wip_limit}")
            for feature in feature_items:
                feature_id = feature.get("id")
                if feature.get("push_status") and feature["push_status"] not in VALID_PUSH_STATUSES:
                    ctx.error(f"Invalid push_status: {feature_id} -> {feature['push_status']}")
                if feature.get("status") in ("committed", "pushed", "merged") and not feature.get("commit"):
                    ctx.error(f"Feature {feature_id} status {feature.get('status')} requires commit")
                if not feature.get("owner"):
                    ctx.warning(f"Feature {feature_id} has no owner")
                if feature.get("history"):
                    for entry in feature["history"]:
                        if not entry.get("status") or not entry.get("at") or not entry.get("by"):
                            ctx.error(f"Feature {feature_id} history entry requires status/at/by")
                        if entry.get("status") and entry["status"] not in VALID_FEATURE_STATUSES:
                            ctx.error(f"Invalid history status: {feature_id} -> {entry['status']}")
        except Exception as exc:
            ctx.error(f"feature-list.json is not valid JSON: {exc}")

    git_repo = git_repo_available(root)
    if git_repo:
        diff_proc = run_cmd(["git", "diff", "--check"], cwd=root)
        if diff_proc.returncode != 0:
            ctx.error(f"git diff --check failed: {(diff_proc.stdout + diff_proc.stderr).strip()}")
        status_proc = run_cmd(["git", "status", "--porcelain"], cwd=root)
        porcelain_lines = [line for line in status_proc.stdout.splitlines() if line.strip()]
        if porcelain_lines:
            ctx.warning(f"{len(porcelain_lines)} uncommitted path(s) present (git status)")
        if features:
            for feature in feature_items:
                feature_id = feature.get("id")
                if feature.get("commit"):
                    verify_proc = run_cmd(
                        ["git", "rev-parse", "--verify", f"{feature['commit']}^{{commit}}"], cwd=root
                    )
                    if verify_proc.returncode != 0:
                        ctx.error(f"Feature {feature_id} references unknown commit: {feature['commit']}")
                branch = feature.get("branch")
                if branch and not branch.startswith("未"):
                    branch_proc = run_cmd(["git", "rev-parse", "--verify", f"refs/heads/{branch}"], cwd=root)
                    if branch_proc.returncode != 0 and os.environ.get("CI") != "true":
                        ctx.warning(f"Feature {feature_id} branch not found locally: {branch}")
            git_sync = features.get("git_sync")
            if git_sync and not git_sync.get("enabled"):
                ctx.warning("git repo detected but git_sync.enabled is false")
    elif features and features.get("git_sync") and features["git_sync"].get("enabled"):
        ctx.warning("git_sync.enabled is true but not a git repository")
    else:
        print("Git sync checks skipped: not a git repository")

    if progress.exists() and feature_list.exists() and features:
        progress_text = read_text(progress)
        updated_at = features.get("updated_at")
        if updated_at and updated_at not in progress_text:
            ctx.warning(f"PROGRESS.md does not contain feature-list updated_at {updated_at}")
        for feature in feature_items:
            if feature.get("status") == "in_progress" and feature.get("id") not in progress_text:
                ctx.warning(f"PROGRESS.md does not mention in_progress feature {feature.get('id')}")

    required_files = [
        "script/check.ps1",
        ".harness/rules/git-workflow.md",
        "script/sync-changes.ps1",
        "script/install-hooks.ps1",
        ".harness/init-contract.md",
        ".harness/rules/tool-access.md",
    ]
    for rel in required_files:
        if not (root / rel).exists():
            ctx.error(f"Missing {rel}")

    required_templates = [
        "PROGRESS.md.template",
        "feature-list.json.template",
        "init-contract.md.template",
        "session-handoff.md.template",
        "commit-message.md.template",
        "pr-description.md.template",
        "pipeline-task-card.md.template",
        "pipeline-report.md.template",
        "pipeline-handoff.md.template",
    ]
    for template in required_templates:
        if not (harness / "templates" / template).exists():
            ctx.error(f"Missing template: {template}")

    codex_dir = root / ".codex"
    for rel in (".codex/config.toml", ".codex/README.md"):
        if not (root / rel).exists():
            ctx.error(f"Missing {rel}")

    codex_skills = codex_dir / "skills"
    if skills_dir.exists():
        for child in sorted(skills_dir.iterdir()):
            if not child.is_dir():
                continue
            target_skill = codex_skills / child.name / "SKILL.md"
            if not target_skill.exists():
                ctx.error(f"Codex skill not synced: {child.name}")
            else:
                source_hash = sha256_file(child / "SKILL.md")
                target_hash = sha256_file(target_skill)
                if source_hash.lower() != target_hash.lower():
                    ctx.error(f"Codex skill out of sync: {child.name}")

    codex_artifacts = [
        "harness-template/AGENTS.md.template",
        "harness-template/README.md",
        "script/harness-init.ps1",
        "script/sync-skills.ps1",
        "benchmark/README.md",
    ]
    for rel in codex_artifacts:
        if not (root / rel).exists():
            ctx.error(f"Missing Codex harness artifact: {rel}")

    handoff_template = harness / "templates" / "pipeline-handoff.md.template"
    if handoff_template.exists():
        handoff_text = read_text(handoff_template)
        for placeholder in ("{{feature_id}}", "{{stage}}", "{{conclusion}}", "{{next_stage_contract}}"):
            if placeholder not in handoff_text:
                ctx.error(f"pipeline-handoff.md.template missing placeholder: {placeholder}")

    sticky_wall = harness / "templates" / "sticky-wall.md.template"
    for rel in (
        "pipelines/desktop-pipeline.json",
        "templates/pipeline-handoff.md.template",
        "templates/pipeline-handoff.example.md",
        "templates/pipeline-state.example.json",
        "templates/sticky-wall.md.template",
    ):
        if not (harness / rel).exists():
            ctx.error(f"Missing desktop pipeline artifact: {rel}")

    if sticky_wall.exists():
        wall_text = read_text(sticky_wall)
        for placeholder in ("{{feature_id}}", "{{author}}", "{{stage}}", "{{content}}"):
            if placeholder not in wall_text:
                ctx.error(f"sticky-wall.md.template missing placeholder: {placeholder}")

    desktop_pipeline = harness / "pipelines" / "desktop-pipeline.json"
    pipeline_config: dict = {}
    if desktop_pipeline.exists():
        try:
            pipeline_config = json.loads(read_text(desktop_pipeline))
            if pipeline_config.get("schema_version") != "1.0":
                ctx.error("desktop-pipeline.json schema_version must be 1.0")
            stages = pipeline_config.get("stages") or []
            stage_ids: list[str] = []
            for stage in stages:
                stage_id = stage.get("id")
                if stage_id in stage_ids:
                    ctx.error(f"Duplicate pipeline stage id: {stage_id}")
                stage_ids.append(stage_id)
                if not stage.get("role"):
                    ctx.error(f"Pipeline stage {stage_id} missing role")
                else:
                    role_file = harness / "agents" / "pipeline" / f"{stage['role']}.md"
                    if not role_file.exists():
                        ctx.error(f"Missing role contract for {stage_id}: {role_file}")
                if not stage.get("gate"):
                    ctx.error(f"Pipeline stage {stage_id} missing gate")
                else:
                    gate_file = stage["gate"].split()[0]
                    gate_path = root / re.sub(r"^\./", "", gate_file)
                    if not gate_path.exists():
                        ctx.error(f"Pipeline stage {stage_id} gate file missing: {gate_file}")
                max_attempts = stage.get("max_attempts")
                if max_attempts is None or max_attempts < 1:
                    ctx.error(f"Pipeline stage {stage_id} max_attempts must be >= 1")
                for dep in stage.get("depends_on") or []:
                    if dep == stage_id:
                        ctx.error(f"Pipeline stage {stage_id} depends on itself")
                    elif not any(s.get("id") == dep for s in stages):
                        ctx.error(f"Pipeline stage {stage_id} has unknown dependency: {dep}")
            if not stage_ids:
                ctx.error("desktop-pipeline.json has no stages")
            else:
                assert_no_dependency_cycle(ctx, stages, "desktop-pipeline.json")
            assert_no_write_scope_conflict(ctx, stages, "desktop-pipeline.json")
        except Exception as exc:
            ctx.error(f"desktop-pipeline.json is not valid JSON: {exc}")

    config_stage_ids = [s.get("id") for s in pipeline_config.get("stages") or []] if pipeline_config else []

    parallel_path = harness / "pipelines" / "desktop-pipeline.parallel.example.json"
    if parallel_path.exists():
        try:
            parallel_config = json.loads(read_text(parallel_path))
            if parallel_config.get("schema_version") != "1.0":
                ctx.error("desktop-pipeline.parallel.example.json schema_version must be 1.0")
            parallel_stages = parallel_config.get("stages") or []
            parallel_ids: list[str] = []
            for stage in parallel_stages:
                stage_id = stage.get("id")
                if stage_id in parallel_ids:
                    ctx.error(f"Duplicate parallel example stage id: {stage_id}")
                parallel_ids.append(stage_id)
                for dep in stage.get("depends_on") or []:
                    if not any(s.get("id") == dep for s in parallel_stages):
                        ctx.error(f"Parallel example stage {stage_id} has unknown dependency: {dep}")
            assert_no_dependency_cycle(ctx, parallel_stages, "desktop-pipeline.parallel.example.json")
            assert_no_write_scope_conflict(ctx, parallel_stages, "desktop-pipeline.parallel.example.json")
        except Exception as exc:
            ctx.error(f"desktop-pipeline.parallel.example.json is not valid JSON: {exc}")

    state_example = harness / "templates" / "pipeline-state.example.json"
    if state_example.exists():
        try:
            example = json.loads(read_text(state_example))
            if example.get("schema_version") not in ("1.0", "1.1"):
                ctx.error("pipeline-state.example.json schema_version must be 1.0 or 1.1")
            assert_active_stages(ctx, example, "pipeline-state.example.json")
            example_stages = example.get("stages") or []
            if not example_stages:
                ctx.error("pipeline-state.example.json has no stages")
            if example.get("journal") is None:
                ctx.error("pipeline-state.example.json missing journal")
            if example.get("status") not in VALID_PIPELINE_STATUSES:
                ctx.error(f"pipeline-state.example.json has invalid status: {example.get('status')}")
            for stage in example_stages:
                if stage.get("status") not in VALID_STAGE_STATUSES:
                    ctx.error(
                        f"pipeline-state.example.json stage {stage.get('id')} has invalid status: "
                        f"{stage.get('status')}"
                    )
            for entry in example.get("journal") or []:
                if entry.get("seq") is None or entry.get("at") is None or entry.get("type") is None:
                    ctx.error("pipeline-state.example.json journal entry missing seq/at/type")
            if config_stage_ids:
                example_stage_ids = [s.get("id") for s in example_stages]
                for stage_id in config_stage_ids:
                    if stage_id not in example_stage_ids:
                        ctx.error(f"pipeline-state.example.json missing stage: {stage_id}")
                for stage_id in example_stage_ids:
                    if stage_id not in config_stage_ids:
                        ctx.error(f"pipeline-state.example.json has unknown stage: {stage_id}")
        except Exception as exc:
            ctx.error(f"pipeline-state.example.json is not valid JSON: {exc}")

    state_dir = harness / "state"
    if state_dir.exists():
        for state_file in sorted(state_dir.glob("pipeline-*.json")):
            try:
                state = json.loads(read_text(state_file))
                if state.get("schema_version") not in ("1.0", "1.1"):
                    ctx.error(f"Pipeline state schema_version must be 1.0 or 1.1 in {state_file.name}")
                assert_active_stages(ctx, state, state_file.name)
                if state.get("status") not in VALID_PIPELINE_STATUSES:
                    ctx.error(f"Invalid pipeline state status in {state_file.name}: {state.get('status')}")
                state_stage_ids = [s.get("id") for s in state.get("stages") or []]
                if state.get("current_stage") and state["current_stage"] not in state_stage_ids:
                    ctx.error(
                        f"Pipeline state current_stage not found in {state_file.name}: "
                        f"{state.get('current_stage')}"
                    )
                if config_stage_ids:
                    for stage_id in config_stage_ids:
                        if stage_id not in state_stage_ids:
                            ctx.error(f"Pipeline state missing stage {stage_id} in {state_file.name}")
                    for stage_id in state_stage_ids:
                        if stage_id not in config_stage_ids:
                            ctx.error(f"Pipeline state has unknown stage {stage_id} in {state_file.name}")
                for stage in state.get("stages") or []:
                    if stage.get("status") not in VALID_STAGE_STATUSES:
                        ctx.error(
                            f"Invalid stage status in {state_file.name} for {stage.get('id')}: "
                            f"{stage.get('status')}"
                        )
                journal = state.get("journal")
                if journal is None:
                    ctx.error(f"Pipeline state missing journal in {state_file.name}")
                else:
                    for entry in journal:
                        if entry.get("seq") is None or entry.get("at") is None or entry.get("type") is None:
                            ctx.error(f"Journal entry missing fields in {state_file.name}")
                feature_exists = any(f.get("id") == state.get("feature_id") for f in feature_items)
                if not feature_exists:
                    ctx.error(f"Pipeline state references unknown feature: {state.get('feature_id')}")
                if feature_exists:
                    feature = next(f for f in feature_items if f.get("id") == state.get("feature_id"))
                    pipeline_block = feature.get("pipeline") or {}
                    if state.get("status") == "done" and pipeline_block.get("status") != "done":
                        ctx.error(
                            f"Pipeline state done but feature-list status is {pipeline_block.get('status')} "
                            f"for {state.get('feature_id')}"
                        )
                    if state.get("status") == "blocked" and pipeline_block.get("status") != "blocked":
                        ctx.error(
                            f"Pipeline state blocked but feature-list status is "
                            f"{pipeline_block.get('status')} "
                            f"for {state.get('feature_id')}"
                        )
            except Exception as exc:
                ctx.error(f"Invalid pipeline state file {state_file.name}: {exc}")

    if features:
        if features.get("schema_version") != "1.2":
            ctx.error("feature-list schema_version must be 1.2")
        for feature in feature_items:
            feature_id = feature.get("id")
            if feature.get("pipeline") is None:
                ctx.error(f"Feature {feature_id} missing pipeline block (schema 1.2)")
            elif feature["pipeline"].get("status") not in VALID_PIPELINE_STATUSES:
                ctx.error(
                    f"Feature {feature_id} has invalid pipeline.status: {feature['pipeline'].get('status')}"
                )

    tech_debt = harness / "changes" / "tech-debt-tracker.md"
    if tech_debt.exists():
        in_main_list = False
        for line in read_text(tech_debt).splitlines():
            if re.match(r"^## 5\.", line):
                in_main_list = True
            elif re.match(r"^## 6\.", line):
                in_main_list = False
            elif in_main_list and TECH_DEBT_RESOLVED_RE.search(line):
                ctx.error(f"Resolved tech debt still in main list: {line}")

    completed_index = harness / "changes" / "completed" / "INDEX.md"
    if not completed_index.exists():
        ctx.error("Missing changes/completed/INDEX.md")
    else:
        index_text = read_text(completed_index)
        for match in INDEX_LINK_RE.finditer(index_text):
            relative = match.group(1)
            if relative.startswith("completed/"):
                relative = relative[len("completed/") :]
            candidate = completed_index.parent / relative
            if not candidate.exists():
                ctx.error(f"Broken completed INDEX link: {match.group(1)}")

    for base in (harness / "wiki", harness / "changes"):
        if base.exists():
            for file in base.rglob("*"):
                if file.is_file() and file.stat().st_size > 40 * 1024 and file.suffix.lower() != ".html":
                    ctx.warning(f"Large doc ({round(file.stat().st_size / 1024, 1)} KB): {file}")

    for base in (root / "docs" / "zread", root / ".zread"):
        if base.exists():
            for dirpath in base.rglob(".obsidian"):
                if dirpath.is_dir():
                    ctx.warning(f"Obsidian editor state found: {dirpath}")

    return ctx.errors, ctx.warnings


def run_mvn_gate(root: Path, mode: str) -> list[str]:
    mvn = shutil.which("mvn")
    pom = root / "pom.xml"
    failures: list[str] = []
    if mode == "backend":
        if mvn is None or not pom.exists():
            print("[check] no Maven project found; skipping backend verification")
            return failures
        commands = [
            ["-pl", "app-module-user", "-am", "test"],
            ["-pl", "app-module-infra", "-am", "test"],
            ["-pl", "app-server", "-am", "package", "-DskipTests"],
        ]
        for command in commands:
            label = "mvn " + " ".join(command)
            print(f"[check] {label}")
            proc = run_cmd(["mvn", *command], cwd=root)
            if proc.returncode != 0:
                failures.append(label)
        return failures
    if mode == "compile":
        if mvn is None or not pom.exists():
            print("[check] no Maven project found; skipping compile gate")
            return failures
        command = ["-pl", "app-server", "-am", "compile", "-DskipTests"]
        label = "mvn " + " ".join(command)
        print(f"[check] {label}")
        proc = run_cmd(["mvn", *command], cwd=root)
        if proc.returncode != 0:
            failures.append(label)
    return failures


def cmd_check(
    root: Path,
    strict: bool = False,
    backend: bool = False,
    compile: bool = False,
    ci: bool = False,
    sql: bool = False,
) -> int:
    errors, warnings = run_check(root, strict=strict)
    print(f"Harness check: {len(errors)} error(s), {len(warnings)} warning(s)")
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    failures: list[str] = []
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        failures.append("harness-check")
    elif ci and warnings:
        print("[check] CI mode: warnings are treated as errors", file=sys.stderr)
        failures.append("harness-check")

    if sql and run_sql_check(root) != 0:
        failures.append("sqlcheck")

    if backend:
        failures.extend(run_mvn_gate(root, "backend"))
    elif compile:
        failures.extend(run_mvn_gate(root, "compile"))
    else:
        print("[check] backend checks skipped; run with --backend to include Maven verification")

    if failures:
        print("[check] failed:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("[check] ok")
    return 0
