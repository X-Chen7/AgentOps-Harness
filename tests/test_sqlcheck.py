from __future__ import annotations

from harness.sqlcheck import run_sql_check


def test_no_sql_dir_skips(tmp_path) -> None:
    assert run_sql_check(tmp_path) == 0


def test_safe_sql_passes(tmp_path) -> None:
    migrations = tmp_path / "sql" / "migrations"
    migrations.mkdir(parents=True)
    (migrations / "v1__init.sql").write_text("CREATE TABLE t (id INT);", encoding="utf-8")
    assert run_sql_check(tmp_path) == 0


def test_destructive_sql_fails(tmp_path) -> None:
    migrations = tmp_path / "sql" / "migrations"
    migrations.mkdir(parents=True)
    (migrations / "v2__drop.sql").write_text("DROP TABLE t;", encoding="utf-8")
    assert run_sql_check(tmp_path) == 1


def test_bad_filename_fails(tmp_path) -> None:
    sql_dir = tmp_path / "sql"
    sql_dir.mkdir()
    (sql_dir / "Bad Name.sql").write_text("SELECT 1;", encoding="utf-8")
    assert run_sql_check(tmp_path) == 1
