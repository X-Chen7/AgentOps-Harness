from __future__ import annotations

import shutil

from harness.skill_bench import run_skill_bench

from .test_skill_test import _add_case, _add_skill


def test_bench_save_and_compare(tmp_path) -> None:
    skill_dir = _add_skill(tmp_path)
    _add_case(
        skill_dir,
        "passing",
        """\
schema_version: "1.0"
run: python -c "open('out.txt','w').write('ok')"
checks:
  - type: exit_code
    expected: 0
  - type: file_exists
    path: out.txt
""",
    )
    assert run_skill_bench(tmp_path, save=True) == 0
    assert run_skill_bench(tmp_path, compare=True) == 0


def test_bench_detects_regression(tmp_path) -> None:
    skill_dir = _add_skill(tmp_path)
    case_dir = _add_case(
        skill_dir,
        "passing",
        """\
schema_version: "1.0"
run: python -c "open('out.txt','w').write('ok')"
checks:
  - type: exit_code
    expected: 0
  - type: file_exists
    path: out.txt
""",
    )
    assert run_skill_bench(tmp_path, save=True) == 0
    checks = case_dir / "checks.yaml"
    checks.write_text(
        """\
schema_version: "1.0"
run: python -c "print('ok')"
checks:
  - type: file_exists
    path: missing.txt
""",
        encoding="utf-8",
    )
    assert run_skill_bench(tmp_path, compare=True) == 1


def test_bench_requires_baseline_for_compare(tmp_path) -> None:
    skill_dir = _add_skill(tmp_path)
    _add_case(
        skill_dir,
        "passing",
        """\
schema_version: "1.0"
checks:
  - type: file_exists
    path: task.md
""",
    )
    assert run_skill_bench(tmp_path, compare=True) == 1


def test_bench_fails_when_tests_fail(tmp_path) -> None:
    skill_dir = _add_skill(tmp_path)
    _add_case(
        skill_dir,
        "failing",
        """\
schema_version: "1.0"
checks:
  - type: file_exists
    path: missing.txt
""",
    )
    assert run_skill_bench(tmp_path) == 1
    baseline = tmp_path / ".harness" / "benchmarks" / "skills" / "baseline.json"
    assert not baseline.exists()


def test_bench_does_not_save_failed_baseline(tmp_path) -> None:
    skill_dir = _add_skill(tmp_path)
    _add_case(
        skill_dir,
        "failing",
        """\
schema_version: "1.0"
checks:
  - type: file_exists
    path: missing.txt
""",
    )
    assert run_skill_bench(tmp_path, save=True) == 1
    baseline = tmp_path / ".harness" / "benchmarks" / "skills" / "baseline.json"
    assert not baseline.exists()


def test_bench_detects_removed_case(tmp_path) -> None:
    skill_dir = _add_skill(tmp_path)
    case_dir = _add_case(
        skill_dir,
        "passing",
        """\
schema_version: "1.0"
run: python -c "open('out.txt','w').write('ok')"
checks:
  - type: file_exists
    path: out.txt
""",
    )
    assert run_skill_bench(tmp_path, save=True) == 0
    shutil.rmtree(case_dir)
    assert run_skill_bench(tmp_path, compare=True) == 1


def test_bench_manual_only_fails(tmp_path) -> None:
    skill_dir = _add_skill(tmp_path)
    case_dir = skill_dir / "fixtures" / "manual"
    case_dir.mkdir(parents=True)
    (case_dir / "task.md").write_text("# task", encoding="utf-8")
    assert run_skill_bench(tmp_path) == 1
