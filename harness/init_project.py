from __future__ import annotations

import sys
from pathlib import Path

from .common import read_text, write_text


def init_harness(root: Path, target: str, project_name: str = "") -> int:
    template_path = root / "harness-template" / "AGENTS.md.template"
    if not template_path.exists():
        print(f"Template not found: {template_path}", file=sys.stderr)
        return 1

    target_path = Path(target).resolve()
    agents_path = target_path / "AGENTS.md"

    if agents_path.exists():
        print(f"SKIP: AGENTS.md already exists at {target_path}")
        return 0

    target_path.mkdir(parents=True, exist_ok=True)
    if not project_name:
        project_name = target_path.name or "UnnamedProject"

    harness_dir = target_path / ".harness"
    directories = (
        "rules",
        "skills",
        "changes/active",
        "changes/completed",
        "wiki",
        "templates",
        "agents",
    )
    for relative in directories:
        (harness_dir / relative).mkdir(parents=True, exist_ok=True)

    content = read_text(template_path)
    content = content.replace("{{PROJECT_NAME}}", project_name)
    content = content.replace("{{PROJECT_DESC}}", "TODO: Describe project in one or two sentences.")
    content = content.replace("{{ENABLED_MODULES}}", "TODO: List enabled modules.")
    write_text(agents_path, content)

    print(f"OK: initialized harness at {harness_dir}")
    return 0
