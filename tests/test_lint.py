from __future__ import annotations

import pytest

from harness.lint import run_lint

from .conftest import REPO_ROOT


def test_lint_passes() -> None:
    pytest.importorskip("ruff")
    assert run_lint(REPO_ROOT) == 0
