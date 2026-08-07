from __future__ import annotations

import shutil
import sys
from pathlib import Path

from .common import git_repo_available, run_cmd, write_text


def install_hooks(root: Path, force: bool = False, use_pre_commit: bool | None = None) -> int:
    if shutil.which("git") is None:
        print("[install-hooks] git is not available")
        return 1

    if not git_repo_available(root):
        print("[install-hooks] not a git repository; skip hook installation")
        return 0

    if use_pre_commit is None:
        use_pre_commit = shutil.which("pre-commit") is not None

    if use_pre_commit:
        args = [
            sys.executable,
            "-m",
            "pre_commit",
            "install",
            "--hook-type",
            "pre-commit",
            "--hook-type",
            "pre-push",
        ]
        if force:
            args.append("--overwrite")
        proc = run_cmd(args, cwd=root)
        if proc.returncode != 0:
            print(proc.stdout + proc.stderr, end="")
            print("[install-hooks] pre-commit install failed")
            return 1
        print("[install-hooks] installed pre-commit + pre-push hooks")
        return 0

    git_dir_raw = run_cmd(["git", "rev-parse", "--git-dir"], cwd=root).stdout.strip()
    git_dir = Path(git_dir_raw)
    if not git_dir.is_absolute():
        git_dir = root / git_dir

    hook = git_dir / "hooks" / "pre-push"
    content = "\n".join(
        [
            "#!/bin/sh",
            "# Harness changes git sync gate (installed by harness install-hooks)",
            "python -m harness sync --push-gate",
            "",
        ]
    )

    if hook.exists() and not force:
        print(f"[install-hooks] pre-push hook already exists; use --force to overwrite: {hook}")
        return 0

    hook.parent.mkdir(parents=True, exist_ok=True)
    write_text(hook, content)
    print(f"[install-hooks] installed pre-push hook: {hook}")
    return 0
