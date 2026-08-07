from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from .common import read_text, sha256_file, write_text

KNOWLEDGE_SCHEMA_VERSION = "1.0"
BENCH_SCHEMA_VERSION = "1.0"
VALID_KINDS = ("rule", "api", "schema", "context", "state", "skill", "artifact")
KIND_PRIORITY = {
    "rule": 1,
    "state": 2,
    "api": 3,
    "schema": 4,
    "skill": 5,
    "context": 6,
    "artifact": 7,
}
MARKDOWN_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
MD_LINK_RE = re.compile(r"\]\(([^)#]+\.md)(?:#[^)]*)?\)")
EXTERNAL_LINK_RE = re.compile(r"^(?:https?://|mailto:|#|/)", re.IGNORECASE)
CREATE_TABLE_OPEN_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?([A-Za-z0-9_]+)`?\s*\(",
    re.IGNORECASE,
)
COLUMN_RE = re.compile(r"^\s*`?([A-Za-z0-9_]+)`?\s+([A-Za-z0-9_(), ]+?)(?:\s|$)", re.IGNORECASE)
COMMENT_RE = re.compile(r"COMMENT\s+['\"]([^'\"]*)['\"]", re.IGNORECASE)
CLASS_MAPPING_RE = re.compile(r"@RequestMapping\(\s*(?:\"(.*?)\"|value\s*=\s*\"(.*?)\")", re.IGNORECASE)
METHOD_MAPPING_RE = re.compile(
    r"@(?:Get|Post|Put|Delete|Patch|Request)Mapping\(\s*(?:\"(.*?)\"|value\s*=\s*\"(.*?)\")",
    re.IGNORECASE,
)
METHOD_SIGNATURE_RE = re.compile(r"\b(?:public|private|protected)\s+[\w<>\[\],\s.]+\s+([A-Za-z_]\w*)\s*\(")


def knowledge_dir(root: Path) -> Path:
    return root / ".harness" / "knowledge"


def index_path(root: Path) -> Path:
    return knowledge_dir(root) / "index.json"


def api_dir(root: Path) -> Path:
    return knowledge_dir(root) / "api"


def schema_dir(root: Path) -> Path:
    return knowledge_dir(root) / "schema"


def bench_dir(root: Path) -> Path:
    return root / ".harness" / "benchmarks" / "knowledge"


def cases_path(root: Path) -> Path:
    return bench_dir(root) / "cases.json"


def baseline_path(root: Path) -> Path:
    return bench_dir(root) / "baseline.json"


def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text.lower()).strip("-")
    return slug or "top"


def split_markdown_sections(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    offset = 0
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                offset = index + 1
                break
    sections: list[dict[str, Any]] = []
    title = ""
    start = offset + 1
    for index in range(offset, len(lines)):
        line_no = index + 1
        match = MARKDOWN_HEADING_RE.match(lines[index])
        if match:
            if title or start <= line_no - 1:
                sections.append({"title": title, "start": start, "end": line_no - 1})
            title = match.group(2).strip()
            start = line_no
    if title or not sections:
        sections.append({"title": title, "start": start, "end": len(lines)})
    return sections


def _tokens(text: str) -> list[str]:
    parts = re.split(r"[\s,，。；;：:、()（）\[\]【】{}<>/\\|_\-]+", text)
    return [part for part in parts if len(part) >= 2]


def _first_content_line(lines: list[str]) -> str:
    for line in lines:
        cleaned = line.strip().lstrip("#*- ").strip()
        if cleaned and not cleaned.startswith("```"):
            return cleaned[:120]
    return ""


def _routes_for(kind: str, path: Path, title: str, skill_yaml: dict | None = None) -> list[str]:
    stem = path.stem.lower()
    routes = [stem]
    if kind == "rule":
        aliases = {
            "git-workflow": ["git", "commit", "push", "pr", "提交", "推送"],
            "sql-and-migration": ["sql", "表", "字段", "迁移", "migration"],
            "coding-standard": ["编码", "coding", "代码", "规范"],
            "comment-guardrail": ["注释", "comment"],
            "comment-review-checklist": ["注释", "检查", "comment"],
            "documentation-change-rule": ["文档", "doc", "同步"],
            "requirement-alignment-rule": ["需求", "requirement", "纠偏"],
            "tool-access": ["工具", "tool", "命令", "权限"],
            "development-flow": ["开发流程", "流程", "development"],
            "project-structure": ["模块", "结构", "目录", "structure"],
            "backend-module-boundary": ["模块边界", "module", "依赖"],
        }
        routes.extend(aliases.get(stem, []))
    elif kind == "context":
        aliases = {
            "api-contract": ["api", "接口", "契约", "错误码"],
            "data-model": ["表", "字段", "数据模型", "schema", "数据库"],
            "business-domain": ["业务", "对象", "领域", "domain"],
            "frontend-integration": ["前端", "联调", "对接", "frontend"],
            "runtime-and-deployment": ["部署", "配置", "profile", "环境", "deploy"],
            "yudao-framework": ["框架", "starter", "模块", "framework"],
            "migration-guide": ["迁移", "harness", "migration"],
        }
        routes.extend(aliases.get(stem, []))
        if "平台核心" in path.name or "rbac" in path.name.lower() or "oauth" in path.name.lower():
            routes.extend(["平台核心", "rbac", "oauth2", "权限", "client"])
        if "feature-design" in path.parts:
            routes.extend(["设计", "方案", "feature", "评审"])
    elif kind == "state":
        if stem == "feature-list":
            routes.extend(["feature", "功能", "状态", "F-", "wip"])
        elif stem == "progress":
            routes.extend(["进度", "progress", "会话"])
        else:
            routes.extend(["入口", "路由", "agents", "边界"])
    elif kind == "skill" and skill_yaml:
        routes.extend(str(item) for item in skill_yaml.get("trigger") or [])
    if title:
        routes.extend(_tokens(title))
    seen: list[str] = []
    for route in routes:
        value = route.strip().lower()
        if value and value not in seen:
            seen.append(value)
    return seen


def _load_yaml_items(path: Path) -> list[dict[str, Any]]:
    try:
        data = yaml.safe_load(read_text(path))
    except Exception:
        return []
    if isinstance(data, dict):
        items = data.get("items")
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
        return []
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def _skill_yaml(skill_dir: Path) -> dict | None:
    path = skill_dir / "skill.yaml"
    if not path.exists():
        return None
    try:
        data = yaml.safe_load(read_text(path))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _expected_scope(root: Path) -> list[tuple[Path, str]]:
    harness = root / ".harness"
    scope: list[tuple[Path, str]] = []
    for base, kind in ((harness / "rules", "rule"), (harness / "wiki", "context")):
        if base.exists():
            for path in sorted(base.rglob("*.md")):
                scope.append((path, kind))
    wiki = harness / "wiki"
    if wiki.exists():
        for path in sorted(wiki.rglob("*.html")):
            scope.append((path, "artifact"))
    skills = harness / "skills"
    if skills.exists():
        for child in sorted(skills.iterdir()):
            if child.is_dir() and (child / "SKILL.md").exists():
                scope.append((child / "SKILL.md", "skill"))
    for relative in ("AGENTS.md", ".harness/PROGRESS.md", ".harness/changes/active/feature-list.json"):
        if (root / relative).exists():
            kind = "state" if "PROGRESS" in relative or "feature-list" in relative else "context"
            scope.append((root / relative, kind))
    agents_d = root / "AGENTS.d"
    if agents_d.exists():
        for path in sorted(agents_d.glob("*.md")):
            scope.append((path, "context"))
    for base, kind in ((api_dir(root), "api"), (schema_dir(root), "schema")):
        if base.exists():
            for path in sorted(base.iterdir()):
                if path.suffix.lower() in (".yaml", ".yml", ".json"):
                    scope.append((path, kind))
    return scope


def _markdown_entries(
    root: Path,
    path: Path,
    kind: str,
    skill_yaml: dict | None = None,
) -> list[dict[str, Any]]:
    text = read_text(path)
    file_hash = sha256_file(path)
    relative = path.relative_to(root).as_posix()
    entries: list[dict[str, Any]] = []
    for section in split_markdown_sections(text):
        section_lines = text.splitlines()[section["start"] - 1 : section["end"]]
        title = section["title"]
        summary = _first_content_line(section_lines)
        content_hash = sha256_file(path)
        if section_lines:
            content_hash = _sha256_text("\n".join(section_lines))
        entry_id = f"{kind}:{relative}"
        if title:
            entry_id = f"{entry_id}#{slugify(title)}"
        entries.append(
            {
                "id": entry_id,
                "kind": kind,
                "file": relative,
                "title": title,
                "summary": summary,
                "keywords": _tokens(f"{title} {summary} {path.stem}")[:12],
                "routes": _routes_for(kind, path, title, skill_yaml),
                "section": title,
                "line_start": section["start"],
                "line_end": section["end"],
                "file_hash": file_hash,
                "content_hash": content_hash,
            }
        )
    return entries


def _structured_entries(root: Path, path: Path, kind: str) -> list[dict[str, Any]]:
    file_hash = sha256_file(path)
    relative = path.relative_to(root).as_posix()
    entries: list[dict[str, Any]] = []
    for item in _load_yaml_items(path):
        item_id = str(item.get("id") or "")
        if not item_id:
            continue
        name = str(item.get("name") or item_id)
        if kind == "api":
            summary = f"{item.get('method', '')} {item.get('path', '')}".strip()
            routes = [item_id, name, str(item.get("path") or "")]
        else:
            summary = f"表 {item.get('table', item_id)}"
            routes = [item_id, name, str(item.get("table") or "")]
        entries.append(
            {
                "id": item_id,
                "kind": kind,
                "file": relative,
                "title": name,
                "summary": summary,
                "keywords": _tokens(f"{item_id} {name} {summary} {relative}")[:12],
                "routes": [value for value in routes if value],
                "section": None,
                "line_start": None,
                "line_end": None,
                "file_hash": file_hash,
                "content_hash": _sha256_text(json.dumps(item, ensure_ascii=False, sort_keys=True)),
            }
        )
    return entries


def _artifact_entries(root: Path, path: Path) -> list[dict[str, Any]]:
    return [
        {
            "id": f"artifact:{path.relative_to(root).as_posix()}",
            "kind": "artifact",
            "file": path.relative_to(root).as_posix(),
            "title": path.name,
            "summary": "静态原型或 HTML 附件",
            "keywords": _tokens(path.stem),
            "routes": [path.stem.lower()],
            "section": None,
            "line_start": None,
            "line_end": None,
            "file_hash": sha256_file(path),
            "content_hash": sha256_file(path),
        }
    ]


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_index(root: Path, check_only: bool = False) -> int:
    entries: list[dict[str, Any]] = []
    for path, kind in _expected_scope(root):
        if not path.exists():
            continue
        if path.suffix.lower() == ".md":
            skill_yaml = None
            if kind == "skill" and path.parent.name:
                skill_yaml = _skill_yaml(path.parent)
            entries.extend(_markdown_entries(root, path, kind, skill_yaml))
        elif kind in ("api", "schema"):
            entries.extend(_structured_entries(root, path, kind))
        elif kind == "artifact":
            entries.extend(_artifact_entries(root, path))
        elif kind == "state" and path.name == "feature-list.json":
            relative = path.relative_to(root).as_posix()
            entries.append(
                {
                    "id": f"state:{relative}",
                    "kind": "state",
                    "file": relative,
                    "title": "功能状态清单",
                    "summary": "机器可读功能状态权威：feature、状态、commit、PR",
                    "keywords": ["feature", "功能", "状态", "F-", "wip", "commit", "pr"],
                    "routes": ["feature", "功能", "状态", "F-", "wip"],
                    "section": None,
                    "line_start": None,
                    "line_end": None,
                    "file_hash": sha256_file(path),
                    "content_hash": sha256_file(path),
                }
            )

    entries.sort(key=lambda entry: entry["id"])
    unique_ids = {entry["id"] for entry in entries}
    if len(unique_ids) != len(entries):
        print("[knowledge index] duplicate entry ids detected; aborting", file=__import__("sys").stderr)
        return 1

    data = {
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "updated_at": date.today().isoformat(),
        "generated_by": "harness knowledge index",
        "entries": entries,
    }
    if not check_only:
        path = index_path(root)
        path.parent.mkdir(parents=True, exist_ok=True)
        write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"[knowledge index] {len(entries)} entries")
    return 0


def load_index(root: Path) -> dict[str, Any]:
    path = index_path(root)
    if not path.exists():
        raise FileNotFoundError(f"knowledge index missing: {path}")
    data = json.loads(read_text(path))
    if not isinstance(data, dict):
        raise ValueError("knowledge index must be a mapping")
    return data


def _score_entry(entry: dict[str, Any], query: str) -> float:
    lowered = query.lower()
    score = 0.0
    for route in entry.get("routes") or []:
        value = str(route).lower()
        if value and value in lowered:
            score += 3.0
        elif value and lowered in value:
            score += 1.0
    for keyword in entry.get("keywords") or []:
        value = str(keyword).lower()
        if value and value in lowered:
            score += 2.0
        elif value and lowered in value:
            score += 0.5
    title = str(entry.get("title") or "").lower()
    if title and title in lowered:
        score += 1.0
    elif title and lowered in title:
        score += 0.5
    file_path = str(entry.get("file") or "").lower()
    if file_path and lowered in file_path:
        score += 0.3
    return score


def route_entries(root: Path, query: str, top_k: int = 5) -> list[dict[str, Any]]:
    data = load_index(root)
    scored = []
    for entry in data.get("entries") or []:
        score = _score_entry(entry, query)
        if score > 0:
            priority = KIND_PRIORITY.get(entry.get("kind"), 9)
            scored.append((-score, priority, entry.get("id", ""), entry))
    scored.sort()
    return [item[3] for item in scored[:top_k]]


def search_entries(root: Path, query: str, top_k: int = 10) -> list[dict[str, Any]]:
    data = load_index(root)
    scored = []
    for entry in data.get("entries") or []:
        score = _score_entry(entry, query)
        if score > 0:
            priority = KIND_PRIORITY.get(entry.get("kind"), 9)
            scored.append((-score, priority, entry.get("id", ""), entry))
    scored.sort()
    return [item[3] for item in scored[:top_k]]


def _print_entries(entries: list[dict[str, Any]]) -> None:
    for entry in entries:
        print(f"{entry.get('id')}  [{entry.get('kind')}]  {entry.get('file')}")
        print(f"  title: {entry.get('title') or ''}")
        if entry.get("summary"):
            print(f"  summary: {entry.get('summary')}")
        if entry.get("line_start"):
            print(f"  lines: {entry.get('line_start')}-{entry.get('line_end')}")


def cmd_route(root: Path, query: str, top_k: int = 5) -> int:
    try:
        entries = route_entries(root, query, top_k)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not entries:
        print("[knowledge route] no matches; try 'harness knowledge search <terms>'")
        return 1
    _print_entries(entries)
    return 0


def cmd_search(root: Path, query: str, top_k: int = 10) -> int:
    try:
        entries = search_entries(root, query, top_k)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not entries:
        print("[knowledge search] no matches")
        return 1
    _print_entries(entries)
    return 0


def cmd_get(root: Path, entry_id: str, max_lines: int = 0) -> int:
    try:
        data = load_index(root)
        entry = next((item for item in data.get("entries") or [] if item.get("id") == entry_id), None)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if entry is None:
        print(f"[knowledge get] entry not found: {entry_id}", file=sys.stderr)
        return 1
    file_path = root / str(entry["file"])
    if not file_path.exists():
        print(f"error: source file missing: {file_path}", file=sys.stderr)
        return 1
    if entry.get("kind") in ("api", "schema"):
        item = next(
            (item for item in _load_yaml_items(file_path) if item.get("id") == entry_id),
            None,
        )
        if item is None:
            print(f"error: structured entry missing in {file_path}", file=sys.stderr)
            return 1
        print(f"# {entry_id}  ({entry['file']})")
        print(yaml.safe_dump(item, allow_unicode=True, sort_keys=False).rstrip())
        return 0
    lines = read_text(file_path).splitlines()
    start = int(entry.get("line_start") or 1)
    end = int(entry.get("line_end") or len(lines))
    if max_lines > 0 and end - start + 1 > max_lines:
        end = start + max_lines - 1
    print(f"# {entry_id}  ({entry['file']}:{start}-{end})")
    for line in lines[start - 1 : end]:
        print(line)
    return 0


def _structured_files(base: Path) -> list[Path]:
    if not base.exists():
        return []
    return sorted(
        path
        for path in base.iterdir()
        if path.is_file() and path.suffix.lower() in (".yaml", ".yml", ".json")
    )


def _normalize_path(value: str) -> str:
    return value.strip().strip("/").lower()


def lookup_api(root: Path, query: str, top_k: int = 5) -> list[dict[str, Any]]:
    normalized = _normalize_path(query)
    scored: list[tuple[float, str, dict[str, Any]]] = []
    for path in _structured_files(api_dir(root)):
        for item in _load_yaml_items(path):
            item_path = _normalize_path(str(item.get("path") or ""))
            item_id = str(item.get("id") or "").lower()
            name = str(item.get("name") or "").lower()
            score = 0.0
            if item_path and item_path == normalized:
                score += 4.0
            if item_id and item_id == normalized:
                score += 3.0
            if item_path and normalized and (normalized in item_path or item_path in normalized):
                score += 2.0
            if name and normalized and (normalized in name or name in normalized):
                score += 1.0
            if item_id and normalized and normalized in item_id:
                score += 1.0
            if score:
                scored.append((-score, item_id, item))
    scored.sort()
    return [item for _, _, item in scored[:top_k]]


def lookup_table(root: Path, query: str, top_k: int = 5) -> list[dict[str, Any]]:
    normalized = query.strip().lower()
    scored: list[tuple[float, str, dict[str, Any]]] = []
    for path in _structured_files(schema_dir(root)):
        for item in _load_yaml_items(path):
            table = str(item.get("table") or "").lower()
            item_id = str(item.get("id") or "").lower()
            score = 0.0
            if table == normalized:
                score += 4.0
            if item_id == normalized:
                score += 3.0
            if normalized and (normalized in table or table in normalized):
                score += 2.0
            if item_id and normalized and normalized in item_id:
                score += 1.0
            if score:
                scored.append((-score, item_id, item))
    scored.sort()
    return [item for _, _, item in scored[:top_k]]


def cmd_api(root: Path, query: str, top_k: int = 5) -> int:
    matches = lookup_api(root, query, top_k)
    if not matches:
        print(f"[knowledge api] no match: {query}", file=sys.stderr)
        return 1
    for item in matches:
        print(yaml.safe_dump(item, allow_unicode=True, sort_keys=False).rstrip())
        print("---")
    return 0


def cmd_table(root: Path, query: str, top_k: int = 5) -> int:
    matches = lookup_table(root, query, top_k)
    if not matches:
        print(f"[knowledge table] no match: {query}", file=sys.stderr)
        return 1
    for item in matches:
        print(yaml.safe_dump(item, allow_unicode=True, sort_keys=False).rstrip())
        print("---")
    return 0


def _relative_md_links(text: str) -> list[str]:
    targets: list[str] = []
    for match in MD_LINK_RE.finditer(text):
        target = match.group(1).strip()
        if not target or EXTERNAL_LINK_RE.match(target) or "://" in target:
            continue
        targets.append(target)
    return targets


def knowledge_check(root: Path) -> list[str]:
    errors: list[str] = []
    path = index_path(root)
    if not path.exists():
        return ["knowledge index missing; run 'harness knowledge index'"]
    try:
        data = json.loads(read_text(path))
    except Exception as exc:
        return [f"knowledge index invalid: {exc}"]
    if not isinstance(data, dict):
        return ["knowledge index must be a mapping"]
    if data.get("schema_version") != KNOWLEDGE_SCHEMA_VERSION:
        errors.append("knowledge index schema_version must be 1.0")
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append("knowledge index has no entries")
        return errors
    seen: set[str] = set()
    covered: set[str] = set()
    for entry in entries:
        entry_id = entry.get("id")
        if not entry_id:
            errors.append("knowledge entry missing id")
            continue
        if entry_id in seen:
            errors.append(f"duplicate knowledge entry id: {entry_id}")
        seen.add(entry_id)
        kind = entry.get("kind")
        if kind not in VALID_KINDS:
            errors.append(f"invalid knowledge kind for {entry_id}: {kind}")
        relative = entry.get("file")
        if not relative:
            errors.append(f"knowledge entry missing file: {entry_id}")
            continue
        file_path = root / relative
        if not file_path.exists():
            errors.append(f"knowledge entry file missing: {relative}")
            continue
        covered.add(relative)
        if kind != "state" and sha256_file(file_path) != entry.get("file_hash"):
            errors.append(f"knowledge index stale for {relative}; run 'harness knowledge index'")
        line_start = entry.get("line_start")
        line_end = entry.get("line_end")
        if line_start is not None and line_end is not None:
            if not isinstance(line_start, int) or not isinstance(line_end, int) or line_end < line_start:
                errors.append(f"invalid line range for {entry_id}")
            else:
                line_count = len(read_text(file_path).splitlines())
                if line_end > line_count:
                    errors.append(f"line range exceeds file for {entry_id}")
    expected = _expected_scope(root)
    for file_path, kind in expected:
        relative = file_path.relative_to(root).as_posix()
        if relative not in covered:
            errors.append(f"knowledge index missing {relative}")
        if kind in ("api", "schema"):
            for item in _load_yaml_items(file_path):
                item_id = item.get("id")
                if not item_id:
                    errors.append(f"{relative}: structured item missing id")
                elif not any(e.get("id") == item_id and e.get("kind") == kind for e in entries):
                    errors.append(f"knowledge index missing structured entry {item_id}")
        if kind in ("rule", "context", "skill", "state") and file_path.suffix.lower() == ".md":
            for target in _relative_md_links(read_text(file_path)):
                resolved = (file_path.parent / target).resolve()
                if not resolved.exists():
                    errors.append(f"broken md link in {relative}: {target}")
    return errors


def cmd_knowledge_check(root: Path) -> int:
    errors = knowledge_check(root)
    print(f"[knowledge check] {len(errors)} error(s)")
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    return 1 if errors else 0


def _candidate_ids(root: Path, mode: str, query: str, top_k: int) -> list[str]:
    if mode == "api":
        return [str(item.get("id") or "") for item in lookup_api(root, query, top_k)]
    if mode == "table":
        return [str(item.get("id") or "") for item in lookup_table(root, query, top_k)]
    if mode == "search":
        return [str(entry.get("id") or "") for entry in search_entries(root, query, top_k)]
    return [str(entry.get("id") or "") for entry in route_entries(root, query, top_k)]


def run_knowledge_bench(root: Path, save: bool = False, compare: bool = False) -> int:
    started = time.monotonic()
    path = cases_path(root)
    if not path.exists():
        print("[knowledge bench] no cases found; add .harness/benchmarks/knowledge/cases.json")
        return 1
    try:
        cases_data = json.loads(read_text(path))
    except Exception as exc:
        print(f"[knowledge bench] invalid cases: {exc}", file=sys.stderr)
        return 1
    if not isinstance(cases_data, dict):
        print("[knowledge bench] cases must be a mapping", file=sys.stderr)
        return 1
    if cases_data.get("schema_version") != BENCH_SCHEMA_VERSION:
        print("[knowledge bench] cases schema_version must be 1.0", file=sys.stderr)
        return 1
    cases = cases_data.get("cases")
    if not isinstance(cases, list) or not cases:
        print("[knowledge bench] no cases", file=sys.stderr)
        return 1
    results: list[dict[str, Any]] = []
    for case in cases:
        case_id = case.get("id")
        mode = case.get("mode") or "route"
        query = case.get("question") or ""
        expected = [str(item) for item in case.get("expected") or []]
        top_k = int(case.get("k") or 3)
        try:
            candidates = _candidate_ids(root, mode, query, top_k)
        except Exception as exc:
            results.append(
                {
                    "id": case_id,
                    "ok": False,
                    "mode": mode,
                    "candidates": [],
                    "expected": expected,
                    "errors": [str(exc)],
                }
            )
            continue
        hit = any(
            candidate == expected_item or candidate.startswith(expected_item)
            for candidate in candidates
            for expected_item in expected
        )
        results.append(
            {
                "id": case_id,
                "ok": hit,
                "mode": mode,
                "candidates": candidates,
                "expected": expected,
                "errors": [],
            }
        )
    passed = sum(1 for result in results if result["ok"])
    failed = len(results) - passed
    summary = {
        "cases": len(results),
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / len(results), 4) if results else 0.0,
        "duration": round(time.monotonic() - started, 3),
    }
    data = {
        "schema_version": BENCH_SCHEMA_VERSION,
        "updated_at": date.today().isoformat(),
        "summary": summary,
        "results": results,
    }
    baseline = baseline_path(root)
    if save:
        if summary["failed"] > 0:
            print("[knowledge bench] failures present; baseline not saved", file=sys.stderr)
            return 1
        baseline.parent.mkdir(parents=True, exist_ok=True)
        write_text(baseline, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        print(f"[knowledge bench] baseline saved: {baseline}")
    regression = False
    if compare:
        if not baseline.exists():
            print("[knowledge bench] no baseline found; run with --save first", file=sys.stderr)
            return 1
        try:
            base = json.loads(read_text(baseline))
        except Exception as exc:
            print(f"[knowledge bench] invalid baseline: {exc}", file=sys.stderr)
            return 1
        base_summary = base.get("summary") or {}
        if base_summary.get("cases", 0) == 0 or base_summary.get("failed", 0) > 0:
            print(
                "[knowledge bench] baseline is empty or contains failures; re-run with --save",
                file=sys.stderr,
            )
            return 1
        if summary["failed"] > base_summary.get("failed", 0):
            print(f"[knowledge bench] regression: failed {base_summary.get('failed')} -> {summary['failed']}")
            regression = True
        if summary["pass_rate"] < base_summary.get("pass_rate", 1.0):
            print(
                f"[knowledge bench] regression: pass rate "
                f"{base_summary.get('pass_rate')} -> {summary['pass_rate']}"
            )
            regression = True
        base_cases = {str(item.get("id")) for item in base.get("results") or []}
        current_cases = {str(item.get("id")) for item in results}
        removed = base_cases - current_cases
        if removed:
            print(f"[knowledge bench] removed cases: {', '.join(sorted(removed))}")
            regression = True
        base_failing = {str(item.get("id")) for item in base.get("results") or [] if not item.get("ok")}
        new_failures = {str(item.get("id")) for item in results if not item.get("ok")} - base_failing
        if new_failures:
            print(f"[knowledge bench] new failing cases: {', '.join(sorted(new_failures))}")
            regression = True
    print(
        f"[knowledge bench] {summary['cases']} case(s), {summary['passed']} passed, "
        f"{summary['failed']} failed, pass rate {summary['pass_rate']}, {summary['duration']}s"
    )
    for result in results:
        status = "pass" if result["ok"] else "FAIL"
        print(f"  {result['id']}: {status} (mode={result['mode']})")
        if not result["ok"]:
            print(f"    expected: {', '.join(result['expected'])}")
            print(f"    candidates: {', '.join(result['candidates'])}")
    return 1 if regression else 0


def _split_sql_block(block: str) -> list[str]:
    block = re.sub(r"/\*.*?\*/", "", block, flags=re.DOTALL)
    lines: list[str] = []
    current: list[str] = []
    depth = 0
    in_string = ""
    for char in block:
        if in_string:
            current.append(char)
            if char == in_string:
                in_string = ""
            continue
        if char in ("'", '"', "`"):
            in_string = char
            current.append(char)
        elif char == "(":
            depth += 1
            current.append(char)
        elif char == ")":
            depth -= 1
            current.append(char)
        elif char == "," and depth == 0:
            lines.append("".join(current))
            current = []
        else:
            current.append(char)
    if "".join(current).strip():
        lines.append("".join(current))
    return lines


def _parse_sql_columns(block: str) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []
    for segment in _split_sql_block(block):
        line = segment.strip()
        if not line or line.startswith("--"):
            continue
        upper = line.upper()
        if upper.startswith(
            (
                "PRIMARY KEY",
                "KEY",
                "UNIQUE KEY",
                "UNIQUE",
                "CONSTRAINT",
                "INDEX",
                "FOREIGN KEY",
                "CHECK",
            )
        ):
            continue
        match = COLUMN_RE.match(line)
        if not match:
            continue
        comment_match = COMMENT_RE.search(line)
        fields.append(
            {
                "name": match.group(1),
                "type": match.group(2).strip(),
                "nullable": "NOT NULL" not in upper,
                "comment": comment_match.group(1) if comment_match else "",
            }
        )
    return fields


def extract_schema(sql_dir: Path, out_dir: Path) -> tuple[int, dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(sql_dir.rglob("*.sql")) if sql_dir.exists() else []
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    report: dict[str, Any] = {"files": len(files), "tables": 0, "skipped": 0}
    for file_path in files:
        try:
            text = read_text(file_path)
        except Exception:
            report["skipped"] += 1
            continue
        for match in CREATE_TABLE_OPEN_RE.finditer(text):
            table = match.group(1)
            start = match.end()
            depth = 1
            index = start
            while index < len(text) and depth:
                if text[index] == "(":
                    depth += 1
                elif text[index] == ")":
                    depth -= 1
                index += 1
            if depth != 0:
                report["skipped"] += 1
                continue
            fields = _parse_sql_columns(text[start : index - 1])
            if not fields:
                report["skipped"] += 1
                continue
            if table in seen:
                report["skipped"] += 1
                continue
            seen.add(table)
            items.append(
                {
                    "id": table,
                    "table": table,
                    "module": "",
                    "fields": fields,
                    "indexes": [],
                    "relations": [],
                    "source_file": file_path.as_posix(),
                }
            )
    report["tables"] = len(items)
    if items:
        write_text(
            out_dir / "generated.yaml",
            yaml.safe_dump(
                {"schema_version": KNOWLEDGE_SCHEMA_VERSION, "items": items},
                allow_unicode=True,
                sort_keys=False,
            ),
        )
    print(
        f"[knowledge extract] sql files={report['files']}, tables={report['tables']}, "
        f"skipped={report['skipped']}"
    )
    return 0, report


def extract_api(controllers_dir: Path, out_dir: Path) -> tuple[int, dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(controllers_dir.rglob("*.java")) if controllers_dir.exists() else []
    items: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    report: dict[str, Any] = {"files": len(files), "endpoints": 0, "skipped": 0}
    for file_path in files:
        try:
            text = read_text(file_path)
        except Exception:
            report["skipped"] += 1
            continue
        if "@RestController" not in text and "@Controller" not in text:
            continue
        class_match = CLASS_MAPPING_RE.search(text)
        class_prefix = (class_match.group(1) or class_match.group(2) or "").strip() if class_match else ""
        module = file_path.stem.replace("Controller", "") or file_path.parent.name
        for method_match in METHOD_MAPPING_RE.finditer(text):
            annotation = method_match.group(0)
            if annotation.lower().startswith("@requestmapping"):
                continue
            method_path = (method_match.group(1) or method_match.group(2) or "").strip()
            method = "GET"
            annotation = text[method_match.start() : method_match.start() + 30]
            if "@PostMapping" in annotation:
                method = "POST"
            elif "@PutMapping" in annotation:
                method = "PUT"
            elif "@DeleteMapping" in annotation:
                method = "DELETE"
            elif "@PatchMapping" in annotation:
                method = "PATCH"
            signature = METHOD_SIGNATURE_RE.search(text[method_match.end() : method_match.end() + 600])
            name = signature.group(1) if signature else method_path.strip("/").replace("/", "-") or "endpoint"
            parts = [part.strip("/") for part in (class_prefix, method_path) if part.strip("/")]
            combined = "/" + "/".join(parts) if parts else "/"
            item_id = f"{module}-{name}"
            item_id = re.sub(r"[^A-Za-z0-9_-]+", "-", item_id).strip("-").lower()
            base_id = item_id
            suffix = 2
            while item_id in seen_ids:
                item_id = f"{base_id}-{suffix}"
                suffix += 1
            seen_ids.add(item_id)
            items.append(
                {
                    "id": item_id,
                    "name": name,
                    "method": method,
                    "path": combined,
                    "module": module,
                    "request": [],
                    "response": [],
                    "errors": [],
                    "source_file": file_path.as_posix(),
                }
            )
    report["endpoints"] = len(items)
    if items:
        write_text(
            out_dir / "generated.yaml",
            yaml.safe_dump(
                {"schema_version": KNOWLEDGE_SCHEMA_VERSION, "items": items},
                allow_unicode=True,
                sort_keys=False,
            ),
        )
    print(
        f"[knowledge extract] controllers={report['files']}, endpoints={report['endpoints']}, "
        f"skipped={report['skipped']}"
    )
    return 0, report
