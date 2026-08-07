from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import check as check_mod
from . import dod as dod_mod
from . import git_ops as git_mod
from . import hooks as hooks_mod
from . import init_project as init_mod
from . import knowledge as knowledge_mod
from . import lint as lint_mod
from . import skill_bench as skill_bench_mod
from . import skill_contract as skill_contract_mod
from . import skill_feedback as skill_feedback_mod
from . import skill_test as skill_test_mod
from . import skills as skills_mod
from . import sync as sync_mod
from .common import HarnessError


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    while current != current.parent:
        if (current / ".harness").exists() and (current / "AGENTS.md").exists():
            return current
        current = current.parent
    return start.resolve()


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=".", help="Repository root (default: current directory)")

    parser = argparse.ArgumentParser(prog="harness", description="AgentOps-Harness CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", parents=[common], help="Validate harness structure and state")
    p_check.add_argument("--strict", action="store_true", help="Keep for compatibility")
    p_check.add_argument("--backend", action="store_true", help="Include backend module tests and packaging")
    p_check.add_argument("--compile", action="store_true", help="Include backend compile gate")
    p_check.add_argument("--ci", action="store_true", help="Treat warnings as errors")
    p_check.add_argument("--sql", action="store_true", help="Run SQL migration checks")

    sub.add_parser("lint", parents=[common], help="Run ruff lint and format check")

    sub.add_parser("dod", parents=[common], help="Validate Definition of Done")

    p_sync = sub.add_parser("sync", parents=[common], help="Validate feature-list and git sync state")
    p_sync.add_argument("--push-gate", action="store_true", help="Treat uncommitted paths as errors")

    p_skills = sub.add_parser("sync-skills", parents=[common], help="Sync .harness/skills to .codex/skills")
    p_skills.add_argument(
        "--check", dest="check_only", action="store_true", help="Compare files without copying"
    )

    p_skill = sub.add_parser(
        "skill", parents=[common], help="Skill contracts, tests, benchmarks and feedback"
    )
    skill_sub = p_skill.add_subparsers(dest="skill_command", required=True)
    skill_sub.add_parser("validate", parents=[common], help="Validate skill.yaml contracts")
    p_skill_test = skill_sub.add_parser("test", parents=[common], help="Run skill fixture tests")
    p_skill_test.add_argument("--skill", default="", help="Run tests for one skill id")
    p_skill_test.add_argument("--smoke", action="store_true", help="Run one case per skill")
    p_skill_bench = skill_sub.add_parser("bench", parents=[common], help="Run skill benchmark")
    p_skill_bench.add_argument("--save", action="store_true", help="Save current results as baseline")
    p_skill_bench.add_argument("--compare", action="store_true", help="Compare against baseline")
    p_skill_record = skill_sub.add_parser("record", parents=[common], help="Record real execution feedback")
    p_skill_record.add_argument("--skill", required=True, help="Skill id")
    p_skill_record.add_argument("--status", required=True, choices=["pass", "fail", "partial"])
    p_skill_record.add_argument("--note", default="", help="Short note about the execution")
    p_skill_promote = skill_sub.add_parser(
        "promote", parents=[common], help="Promote a real case into fixtures"
    )
    p_skill_promote.add_argument("--skill", required=True, help="Skill id")
    p_skill_promote.add_argument("--case", required=True, help="New fixture case id")
    p_skill_promote.add_argument("--task-text", default="", help="Task description for task.md")

    p_knowledge = sub.add_parser(
        "knowledge", parents=[common], help="Knowledge index, retrieval, facts, check and benchmark"
    )
    knowledge_sub = p_knowledge.add_subparsers(dest="knowledge_command", required=True)
    p_knowledge_index = knowledge_sub.add_parser("index", parents=[common], help="Build knowledge index")
    p_knowledge_index.add_argument(
        "--check", dest="check_only", action="store_true", help="Validate without writing"
    )
    p_knowledge_route = knowledge_sub.add_parser(
        "route", parents=[common], help="Route a task to knowledge entries"
    )
    p_knowledge_route.add_argument("text", help="Task text")
    p_knowledge_route.add_argument("--top", type=int, default=5, help="Number of entries to return")
    p_knowledge_search = knowledge_sub.add_parser("search", parents=[common], help="Keyword search")
    p_knowledge_search.add_argument("text", help="Search terms")
    p_knowledge_search.add_argument("--top", type=int, default=10, help="Number of entries to return")
    p_knowledge_get = knowledge_sub.add_parser("get", parents=[common], help="Read one knowledge entry")
    p_knowledge_get.add_argument("entry_id", help="Entry id from index")
    p_knowledge_get.add_argument("--max-lines", type=int, default=0, help="Limit markdown excerpt lines")
    p_knowledge_api = knowledge_sub.add_parser("api", parents=[common], help="Lookup API facts")
    p_knowledge_api.add_argument("query", help="API path or name")
    p_knowledge_api.add_argument("--top", type=int, default=5, help="Number of matches to return")
    p_knowledge_table = knowledge_sub.add_parser("table", parents=[common], help="Lookup table facts")
    p_knowledge_table.add_argument("query", help="Table name")
    p_knowledge_table.add_argument("--top", type=int, default=5, help="Number of matches to return")
    knowledge_sub.add_parser("check", parents=[common], help="Validate knowledge index freshness")
    p_knowledge_bench = knowledge_sub.add_parser("bench", parents=[common], help="Run retrieval benchmark")
    p_knowledge_bench.add_argument("--save", action="store_true", help="Save current results as baseline")
    p_knowledge_bench.add_argument("--compare", action="store_true", help="Compare against baseline")
    p_knowledge_extract = knowledge_sub.add_parser(
        "extract", parents=[common], help="Extract API/schema facts from code"
    )
    p_knowledge_extract.add_argument("--controllers", default="", help="Java controllers directory")
    p_knowledge_extract.add_argument("--sql", default="", help="SQL directory")

    p_init = sub.add_parser("init", parents=[common], help="Initialize harness in a target project")
    p_init.add_argument("--target", required=True, help="Target project directory")
    p_init.add_argument("--project-name", default="", help="Project name used in AGENTS.md")

    p_hooks = sub.add_parser("install-hooks", parents=[common], help="Install git pre-push hook")
    p_hooks.add_argument("--force", action="store_true", help="Overwrite an existing hook")
    p_hooks.add_argument(
        "--pre-commit",
        dest="use_pre_commit",
        action="store_true",
        help="Install via pre-commit framework",
    )
    p_hooks.add_argument(
        "--legacy",
        dest="use_legacy",
        action="store_true",
        help="Install the simple handwritten pre-push hook",
    )

    for name in ("commit", "push", "pr"):
        p_git = sub.add_parser(name, parents=[common], help=f"Git {name} for a harness feature")
        p_git.add_argument("--feature", required=True, help="Feature id, e.g. F-011")
        p_git.add_argument("--message", default="", help="Optional commit message")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.root == ".":
        root = find_repo_root(Path.cwd())
    else:
        root = Path(args.root).resolve()
    try:
        if args.command == "check":
            return check_mod.cmd_check(
                root,
                strict=args.strict,
                backend=args.backend,
                compile=args.compile,
                ci=args.ci,
                sql=args.sql,
            )
        if args.command == "lint":
            return lint_mod.run_lint(root)
        if args.command == "dod":
            return dod_mod.run_dod(root)
        if args.command == "sync":
            return sync_mod.sync_changes(root, push_gate=args.push_gate)
        if args.command == "sync-skills":
            return skills_mod.sync_skills(root, check_only=args.check_only)
        if args.command == "skill":
            if args.skill_command == "validate":
                return skill_contract_mod.validate_all_skills(root)
            if args.skill_command == "test":
                return skill_test_mod.run_skill_tests(root, skill_id=args.skill or None, smoke=args.smoke)[0]
            if args.skill_command == "bench":
                return skill_bench_mod.run_skill_bench(root, save=args.save, compare=args.compare)
            if args.skill_command == "record":
                return skill_feedback_mod.record_feedback(root, args.skill, args.status, note=args.note)
            if args.skill_command == "promote":
                return skill_feedback_mod.promote_feedback(
                    root, args.skill, args.case, task_text=args.task_text
                )
        if args.command == "knowledge":
            if args.knowledge_command == "index":
                return knowledge_mod.build_index(root, check_only=args.check_only)
            if args.knowledge_command == "route":
                return knowledge_mod.cmd_route(root, args.text, top_k=args.top)
            if args.knowledge_command == "search":
                return knowledge_mod.cmd_search(root, args.text, top_k=args.top)
            if args.knowledge_command == "get":
                return knowledge_mod.cmd_get(root, args.entry_id, max_lines=args.max_lines)
            if args.knowledge_command == "api":
                return knowledge_mod.cmd_api(root, args.query, top_k=args.top)
            if args.knowledge_command == "table":
                return knowledge_mod.cmd_table(root, args.query, top_k=args.top)
            if args.knowledge_command == "check":
                return knowledge_mod.cmd_knowledge_check(root)
            if args.knowledge_command == "bench":
                return knowledge_mod.run_knowledge_bench(root, save=args.save, compare=args.compare)
            if args.knowledge_command == "extract":
                controllers = root / args.controllers if args.controllers else None
                sql_dir = root / args.sql if args.sql else None
                return _run_knowledge_extract(root, controllers, sql_dir)
        if args.command == "init":
            return init_mod.init_harness(root, args.target, args.project_name)
        if args.command == "install-hooks":
            use_pre_commit: bool | None = None
            if args.use_pre_commit:
                use_pre_commit = True
            elif args.use_legacy:
                use_pre_commit = False
            return hooks_mod.install_hooks(root, force=args.force, use_pre_commit=use_pre_commit)
        if args.command == "commit":
            return git_mod.cmd_commit(root, args.feature, args.message or None)
        if args.command == "push":
            return git_mod.cmd_push(root, args.feature)
        if args.command == "pr":
            return git_mod.cmd_pr(root, args.feature)
    except HarnessError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def _run_knowledge_extract(
    root: Path,
    controllers: Path | None,
    sql_dir: Path | None,
) -> int:
    status = 0
    if controllers:
        status = max(
            status,
            knowledge_mod.extract_api(controllers, knowledge_mod.api_dir(root))[0],
        )
    if sql_dir:
        status = max(
            status,
            knowledge_mod.extract_schema(sql_dir, knowledge_mod.schema_dir(root))[0],
        )
    if not controllers and not sql_dir:
        print("error: provide --controllers and/or --sql", file=sys.stderr)
        return 1
    return status


if __name__ == "__main__":
    sys.exit(main())
