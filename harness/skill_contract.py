from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .common import read_text

SKILL_SCHEMA_VERSION = "1.0"
REQUIRED_FIELDS = (
    "schema_version",
    "id",
    "name",
    "version",
    "description",
    "trigger",
    "inputs",
    "outputs",
    "dependencies",
)
LIST_FIELDS = ("trigger", "inputs", "outputs", "dependencies")


def skills_root(root: Path) -> Path:
    return root / ".harness" / "skills"


def iter_skill_dirs(root: Path) -> list[Path]:
    base = skills_root(root)
    if not base.exists():
        return []
    return sorted(path for path in base.iterdir() if path.is_dir() and (path / "SKILL.md").exists())


def load_skill_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(read_text(path))
    if not isinstance(data, dict):
        raise ValueError("skill.yaml must be a mapping")
    return data


def validate_skill(root: Path, skill_dir: Path, known_ids: set[str], errors: list[str]) -> None:
    skill_id = skill_dir.name
    if not (skill_dir / "SKILL.md").exists():
        errors.append(f"{skill_id}: missing SKILL.md")
    yaml_path = skill_dir / "skill.yaml"
    if not yaml_path.exists():
        errors.append(f"{skill_id}: missing skill.yaml")
        return

    try:
        data = load_skill_yaml(yaml_path)
    except Exception as exc:
        errors.append(f"{skill_id}: skill.yaml is not valid: {exc}")
        return

    if data.get("schema_version") != SKILL_SCHEMA_VERSION:
        errors.append(f"{skill_id}: schema_version must be {SKILL_SCHEMA_VERSION}")
    if data.get("id") != skill_id:
        errors.append(f"{skill_id}: skill.yaml id must match directory name")
    for field in REQUIRED_FIELDS:
        value = data.get(field)
        if value is None or value == "":
            errors.append(f"{skill_id}: missing required field {field}")
    for field in LIST_FIELDS:
        value = data.get(field)
        if value is not None and not isinstance(value, list):
            errors.append(f"{skill_id}: {field} must be a list")
        elif value is not None and any(not isinstance(item, str) for item in value):
            errors.append(f"{skill_id}: {field} items must be strings")
    dependencies = data.get("dependencies") or []
    for dependency in dependencies:
        if not isinstance(dependency, str):
            errors.append(f"{skill_id}: dependency must be a string")
            continue
        if dependency not in known_ids:
            errors.append(f"{skill_id}: unknown dependency {dependency}")


def _find_dependency_cycle(graph: dict[str, list[str]]) -> list[str] | None:
    visited: set[str] = set()
    stack: list[str] = []
    in_stack: set[str] = set()

    def visit(node: str) -> list[str] | None:
        if node in in_stack:
            return stack[stack.index(node) :] + [node]
        if node in visited:
            return None
        visited.add(node)
        stack.append(node)
        in_stack.add(node)
        for dependency in graph.get(node) or []:
            cycle = visit(dependency)
            if cycle:
                return cycle
        stack.pop()
        in_stack.remove(node)
        return None

    for node in graph:
        cycle = visit(node)
        if cycle:
            return cycle
    return None


def validate_all_skills(root: Path) -> int:
    base = skills_root(root)
    skill_dirs = sorted(path for path in base.iterdir() if path.is_dir()) if base.exists() else []
    known_ids = {path.name for path in skill_dirs}
    errors: list[str] = []
    for skill_dir in skill_dirs:
        validate_skill(root, skill_dir, known_ids, errors)

    graph: dict[str, list[str]] = {}
    for skill_dir in skill_dirs:
        yaml_path = skill_dir / "skill.yaml"
        if not yaml_path.exists():
            continue
        try:
            data = load_skill_yaml(yaml_path)
        except Exception:
            continue
        dependencies = data.get("dependencies") or []
        for dependency in dependencies:
            if dependency == skill_dir.name:
                errors.append(f"{skill_dir.name}: skill cannot depend on itself")
        graph[skill_dir.name] = [dep for dep in dependencies if isinstance(dep, str)]
    cycle = _find_dependency_cycle(graph)
    if cycle:
        errors.append(f"skill dependency cycle: {' -> '.join(cycle)}")

    print(f"[skill validate] {len(skill_dirs)} skill(s), {len(errors)} error(s)")
    for error in errors:
        print(f"error: {error}")
    return 1 if errors else 0
