from __future__ import annotations

import subprocess

from harness.hooks import install_hooks


def _git_init(path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)


def test_install_hooks(tmp_path) -> None:
    _git_init(tmp_path)
    assert install_hooks(tmp_path) == 0
    hook = tmp_path / ".git" / "hooks" / "pre-push"
    assert hook.exists()
    content = hook.read_text(encoding="utf-8")
    assert "harness sync --push-gate" in content

    assert install_hooks(tmp_path) == 0
    assert install_hooks(tmp_path, force=True) == 0
    assert content in hook.read_text(encoding="utf-8")
