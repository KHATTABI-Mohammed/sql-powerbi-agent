import sqlite3

import pytest

from agent.schemas import ExecutionStatus
from agent.sql.executor import SQLExecutor, check_is_safe


@pytest.mark.parametrize(
    "sql,expected",
    [
        ("SELECT * FROM customers", True),
        ("select id from orders where status = 'Livrée'", True),
        ("WITH t AS (SELECT 1) SELECT * FROM t", True),
        ("DROP TABLE customers", False),
        ("SELECT * FROM customers; DROP TABLE customers", False),
        ("INSERT INTO customers VALUES (1, 'x')", False),
        ("", False),
    ],
)
def test_check_is_safe(sql, expected):
    assert check_is_safe(sql).is_safe is expected


@pytest.fixture
def sample_db(tmp_path):
    db_path = tmp_path / "test.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO customers VALUES (1, 'Alice'), (2, 'Bob')")
        conn.commit()
    return db_path


def test_executor_runs_select(sample_db):
    executor = SQLExecutor(db_path=str(sample_db))
    result = executor.execute("SELECT * FROM customers ORDER BY id")
    assert result.status == ExecutionStatus.SUCCESS
    assert result.columns == ["id", "name"]
    assert result.rows == [[1, "Alice"], [2, "Bob"]]


def test_executor_rejects_unsafe_sql(sample_db):
    executor = SQLExecutor(db_path=str(sample_db))
    result = executor.execute("DROP TABLE customers")
    assert result.status == ExecutionStatus.REJECTED_UNSAFE


def test_executor_missing_db_returns_error(tmp_path):
    executor = SQLExecutor(db_path=str(tmp_path / "missing.db"))
    result = executor.execute("SELECT 1")
    assert result.status == ExecutionStatus.ERROR
