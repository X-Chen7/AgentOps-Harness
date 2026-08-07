from __future__ import annotations

from harness.init_project import init_harness

from .conftest import REPO_ROOT


def test_init_creates_harness(tmp_path) -> None:
    target = tmp_path / "new-project"
    assert init_harness(REPO_ROOT, str(target), "demo") == 0
    assert (target / "AGENTS.md").exists()
    assert (target / ".harness" / "rules").is_dir()
    assert (target / ".harness" / "changes" / "active").is_dir()
    content = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "demo" in content
    assert "TODO: Describe project in one or two sentences." in content


def test_init_skips_existing_agents(tmp_path) -> None:
    target = tmp_path / "existing"
    target.mkdir()
    (target / "AGENTS.md").write_text("keep", encoding="utf-8")
    assert init_harness(REPO_ROOT, str(target), "demo") == 0
    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "keep"
