from __future__ import annotations

import subprocess

import pytest

from harness.hooks import install_hooks


def _git_init(path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)


def test_install_hooks_legacy(tmp_path) -> None:
    _git_init(tmp_path)
    assert install_hooks(tmp_path, use_pre_commit=False) == 0
    hook = tmp_path / ".git" / "hooks" / "pre-push"
    assert hook.exists()
    content = hook.read_text(encoding="utf-8")
    assert "harness sync --push-gate" in content

    assert install_hooks(tmp_path, use_pre_commit=False) == 0
    assert install_hooks(tmp_path, force=True, use_pre_commit=False) == 0
    assert content in hook.read_text(encoding="utf-8")


def test_install_hooks_pre_commit(tmp_path) -> None:
    pytest.importorskip("pre_commit")
    _git_init(tmp_path)
    assert install_hooks(tmp_path, use_pre_commit=True) == 0
    assert (tmp_path / ".git" / "hooks" / "pre-commit").exists()
    assert (tmp_path / ".git" / "hooks" / "pre-push").exists()
