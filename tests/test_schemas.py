import pytest
from pydantic import ValidationError

from agent.schemas import ExecutionResult, ExecutionStatus, SQLGenerationResult


def test_sql_generation_result_strips_trailing_semicolon():
    result = SQLGenerationResult(
        sql="SELECT * FROM customers;",
        explanation="Liste tous les clients",
        tables_used=["customers"],
        confidence=0.9,
    )
    assert result.sql == "SELECT * FROM customers"


def test_sql_generation_result_confidence_must_be_between_0_and_1():
    with pytest.raises(ValidationError):
        SQLGenerationResult(
            sql="SELECT 1",
            explanation="test",
            tables_used=[],
            confidence=1.5,
        )


def test_execution_result_defaults():
    result = ExecutionResult(status=ExecutionStatus.EMPTY)
    assert result.rows == []
    assert result.columns == []
    assert result.row_count == 0
