from __future__ import annotations

import json
from pathlib import Path

from harness import knowledge as knowledge_mod


def _make_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / ".harness" / "rules").mkdir(parents=True)
    (root / ".harness" / "wiki").mkdir(parents=True)
    (root / ".harness" / "knowledge" / "api").mkdir(parents=True)
    (root / ".harness" / "knowledge" / "schema").mkdir(parents=True)
    (root / ".harness" / "changes" / "active").mkdir(parents=True)
    (root / "AGENTS.md").write_text("# Project\n\n## 入口\n\n入口说明。\n", encoding="utf-8")
    (root / ".harness" / "rules" / "git-workflow.md").write_text(
        "# Git 工作流\n\n## 提交规则\n\n先提交后推送。\n",
        encoding="utf-8",
    )
    (root / ".harness" / "wiki" / "api-contract.md").write_text(
        "# 接口契约\n\n## OAuth2\n\nBearer Token。\n",
        encoding="utf-8",
    )
    (root / ".harness" / "PROGRESS.md").write_text("# Progress\n", encoding="utf-8")
    (root / ".harness" / "changes" / "active" / "feature-list.json").write_text(
        json.dumps({"schema_version": "1.2", "features": []}, ensure_ascii=False),
        encoding="utf-8",
    )
    return root


def _write_example_facts(root: Path) -> None:
    (root / ".harness" / "knowledge" / "api" / "example.yaml").write_text(
        """\
schema_version: "1.0"
items:
  - id: ping
    name: 健康检查
    method: GET
    path: /ping
    module: demo
    request: []
    response: [status]
    errors: []
    docs_ref: ".harness/wiki/api-contract.md"
    source_file: ""
""",
        encoding="utf-8",
    )
    (root / ".harness" / "knowledge" / "schema" / "example.yaml").write_text(
        """\
schema_version: "1.0"
items:
  - id: demo_table
    table: demo_table
    module: demo
    fields:
      - name: id
        type: bigint
        nullable: false
        comment: 主键
    indexes: []
    relations: []
    docs_ref: ""
    source_file: ""
""",
        encoding="utf-8",
    )


def _write_cases(root: Path) -> None:
    path = knowledge_mod.cases_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "cases": [
                    {
                        "id": "kb-route",
                        "mode": "route",
                        "question": "git 提交 推送",
                        "expected": ["rule:.harness/rules/git-workflow.md"],
                        "k": 3,
                    },
                    {
                        "id": "kb-api",
                        "mode": "api",
                        "question": "ping",
                        "expected": ["ping"],
                        "k": 1,
                    },
                    {
                        "id": "kb-table",
                        "mode": "table",
                        "question": "demo_table",
                        "expected": ["demo_table"],
                        "k": 1,
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_build_index_and_check(tmp_path) -> None:
    root = _make_repo(tmp_path)
    _write_example_facts(root)
    assert knowledge_mod.build_index(root) == 0
    assert knowledge_mod.index_path(root).exists()
    assert knowledge_mod.knowledge_check(root) == []


def test_check_missing_index(tmp_path) -> None:
    root = _make_repo(tmp_path)
    errors = knowledge_mod.knowledge_check(root)
    assert any("knowledge index missing" in error for error in errors)


def test_check_detects_stale_index(tmp_path) -> None:
    root = _make_repo(tmp_path)
    assert knowledge_mod.build_index(root) == 0
    (root / ".harness" / "rules" / "git-workflow.md").write_text(
        "# Git 工作流\n\n## 提交规则\n\n改过了。\n",
        encoding="utf-8",
    )
    errors = knowledge_mod.knowledge_check(root)
    assert any("stale" in error for error in errors)


def test_check_detects_duplicate_id(tmp_path) -> None:
    root = _make_repo(tmp_path)
    rule = root / ".harness" / "rules" / "git-workflow.md"
    index = knowledge_mod.index_path(root)
    index.parent.mkdir(parents=True, exist_ok=True)
    index.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "entries": [
                    {
                        "id": "rule:git",
                        "kind": "rule",
                        "file": ".harness/rules/git-workflow.md",
                        "title": "规则",
                        "summary": "",
                        "keywords": [],
                        "routes": ["git"],
                        "section": None,
                        "line_start": None,
                        "line_end": None,
                        "file_hash": knowledge_mod.sha256_file(rule),
                        "content_hash": knowledge_mod.sha256_file(rule),
                    },
                    {
                        "id": "rule:git",
                        "kind": "rule",
                        "file": ".harness/rules/git-workflow.md",
                        "title": "规则",
                        "summary": "",
                        "keywords": [],
                        "routes": ["git"],
                        "section": None,
                        "line_start": None,
                        "line_end": None,
                        "file_hash": knowledge_mod.sha256_file(rule),
                        "content_hash": knowledge_mod.sha256_file(rule),
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    errors = knowledge_mod.knowledge_check(root)
    assert any("duplicate knowledge entry id" in error for error in errors)


def test_route_get_and_api_table(tmp_path) -> None:
    root = _make_repo(tmp_path)
    _write_example_facts(root)
    assert knowledge_mod.build_index(root) == 0
    routed = knowledge_mod.route_entries(root, "git 提交 推送")
    assert any(entry["file"] == ".harness/rules/git-workflow.md" for entry in routed)
    assert knowledge_mod.cmd_get(root, routed[0]["id"], max_lines=5) == 0
    api_matches = knowledge_mod.lookup_api(root, "ping")
    assert api_matches and api_matches[0]["id"] == "ping"
    table_matches = knowledge_mod.lookup_table(root, "demo_table")
    assert table_matches and table_matches[0]["table"] == "demo_table"


def test_bench_save_and_compare(tmp_path) -> None:
    root = _make_repo(tmp_path)
    _write_example_facts(root)
    _write_cases(root)
    assert knowledge_mod.build_index(root) == 0
    assert knowledge_mod.run_knowledge_bench(root, save=True) == 0
    assert knowledge_mod.run_knowledge_bench(root, compare=True) == 0


def test_bench_detects_regression(tmp_path) -> None:
    root = _make_repo(tmp_path)
    _write_example_facts(root)
    _write_cases(root)
    assert knowledge_mod.build_index(root) == 0
    assert knowledge_mod.run_knowledge_bench(root, save=True) == 0
    cases = json.loads(knowledge_mod.cases_path(root).read_text(encoding="utf-8-sig"))
    cases["cases"][0]["question"] = "完全不存在的内容"
    knowledge_mod.cases_path(root).write_text(
        json.dumps(cases, ensure_ascii=False),
        encoding="utf-8",
    )
    assert knowledge_mod.run_knowledge_bench(root, compare=True) == 1


def test_bench_detects_removed_case(tmp_path) -> None:
    root = _make_repo(tmp_path)
    _write_example_facts(root)
    _write_cases(root)
    assert knowledge_mod.build_index(root) == 0
    assert knowledge_mod.run_knowledge_bench(root, save=True) == 0
    cases = json.loads(knowledge_mod.cases_path(root).read_text(encoding="utf-8-sig"))
    cases["cases"] = [case for case in cases["cases"] if case["id"] != "kb-table"]
    knowledge_mod.cases_path(root).write_text(
        json.dumps(cases, ensure_ascii=False),
        encoding="utf-8",
    )
    assert knowledge_mod.run_knowledge_bench(root, compare=True) == 1


def test_bench_does_not_save_failed_baseline(tmp_path) -> None:
    root = _make_repo(tmp_path)
    _write_example_facts(root)
    _write_cases(root)
    assert knowledge_mod.build_index(root) == 0
    cases = json.loads(knowledge_mod.cases_path(root).read_text(encoding="utf-8-sig"))
    cases["cases"][0]["question"] = "完全不存在的内容"
    knowledge_mod.cases_path(root).write_text(
        json.dumps(cases, ensure_ascii=False),
        encoding="utf-8",
    )
    assert knowledge_mod.run_knowledge_bench(root, save=True) == 1
    assert not knowledge_mod.baseline_path(root).exists()


def test_bench_rejects_non_mapping_cases(tmp_path) -> None:
    root = _make_repo(tmp_path)
    path = knowledge_mod.cases_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("[]", encoding="utf-8")
    assert knowledge_mod.run_knowledge_bench(root) == 1


def test_extract_schema(tmp_path) -> None:
    root = _make_repo(tmp_path)
    sql_dir = root / "sql"
    sql_dir.mkdir()
    (sql_dir / "init.sql").write_text(
        """\
CREATE TABLE `demo_user` (
  `id` bigint NOT NULL COMMENT '主键',
  `name` varchar(64) DEFAULT NULL COMMENT '名称',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;
""",
        encoding="utf-8",
    )
    status, report = knowledge_mod.extract_schema(sql_dir, knowledge_mod.schema_dir(root))
    assert status == 0
    assert report["tables"] == 1
    generated = knowledge_mod.schema_dir(root) / "generated.yaml"
    assert generated.exists()
    items = knowledge_mod._load_yaml_items(generated)
    assert items[0]["table"] == "demo_user"
    assert len(items[0]["fields"]) == 2


def test_extract_schema_decimal_type(tmp_path) -> None:
    root = _make_repo(tmp_path)
    sql_dir = root / "sql"
    sql_dir.mkdir()
    (sql_dir / "finance.sql").write_text(
        """\
CREATE TABLE `demo_balance` (
  `id` bigint NOT NULL,
  `amount` decimal(10,2) NOT NULL COMMENT '金额',
  PRIMARY KEY (`id`)
);
""",
        encoding="utf-8",
    )
    status, _ = knowledge_mod.extract_schema(sql_dir, knowledge_mod.schema_dir(root))
    assert status == 0
    items = knowledge_mod._load_yaml_items(knowledge_mod.schema_dir(root) / "generated.yaml")
    amount = next(field for field in items[0]["fields"] if field["name"] == "amount")
    assert amount["type"] == "decimal(10,2)"


def test_extract_api(tmp_path) -> None:
    root = _make_repo(tmp_path)
    controllers = root / "controllers"
    controllers.mkdir()
    (controllers / "DemoController.java").write_text(
        """\
@RestController
@RequestMapping("/demo")
public class DemoController {
    @GetMapping("/ping")
    public String ping() { return "pong"; }
}
""",
        encoding="utf-8",
    )
    status, report = knowledge_mod.extract_api(controllers, knowledge_mod.api_dir(root))
    assert status == 0
    assert report["endpoints"] == 1
    generated = knowledge_mod.api_dir(root) / "generated.yaml"
    assert generated.exists()
    items = knowledge_mod._load_yaml_items(generated)
    assert items[0]["path"] == "/demo/ping"
    assert items[0]["method"] == "GET"


def test_extract_api_deduplicates_ids(tmp_path) -> None:
    root = _make_repo(tmp_path)
    controllers = root / "controllers"
    (controllers / "admin").mkdir(parents=True)
    (controllers / "app").mkdir(parents=True)
    (controllers / "admin" / "OrgController.java").write_text(
        """\
@RestController
@RequestMapping("/admin/org")
public class OrgController {
    @GetMapping("/page")
    public String page() { return "ok"; }
}
""",
        encoding="utf-8",
    )
    (controllers / "app" / "OrgController.java").write_text(
        """\
@RestController
@RequestMapping("/app/org")
public class OrgController {
    @GetMapping("/page")
    public String page() { return "ok"; }
}
""",
        encoding="utf-8",
    )
    status, report = knowledge_mod.extract_api(controllers, knowledge_mod.api_dir(root))
    assert status == 0
    assert report["endpoints"] == 2
    items = knowledge_mod._load_yaml_items(knowledge_mod.api_dir(root) / "generated.yaml")
    ids = [item["id"] for item in items]
    assert len(ids) == len(set(ids))
