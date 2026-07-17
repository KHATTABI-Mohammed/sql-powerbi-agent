"""Exécution sécurisée des requêtes SQL générées, contre une base SQLite en lecture seule.

Deux niveaux de protection :
1. Un contrôle syntaxique (`check_is_safe`) qui rejette tout ce qui n'est pas
   un unique `SELECT` (pas de DDL/DML, pas de requêtes empilées).
2. L'ouverture de la connexion SQLite en mode URI `?mode=ro`, qui refuse toute
   écriture au niveau du moteur lui-même, indépendamment de la validation ci-dessus.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from agent.config import settings
from agent.schemas import ExecutionResult, ExecutionStatus, SafetyCheck

_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|ATTACH|REPLACE|PRAGMA|VACUUM|REINDEX)\b",
    re.IGNORECASE,
)


def check_is_safe(sql: str) -> SafetyCheck:
    """Valide qu'une requête est un SELECT unique, sans mot-clé de mutation."""
    stripped = sql.strip().rstrip(";").strip()

    if not stripped:
        return SafetyCheck(is_safe=False, reason="Requête vide.")

    if ";" in stripped:
        return SafetyCheck(is_safe=False, reason="Requêtes empilées (';') interdites.")

    if not re.match(r"(?is)^\s*(WITH\b.*)?SELECT\b", stripped):
        return SafetyCheck(is_safe=False, reason="Seules les requêtes SELECT (ou CTE WITH ... SELECT) sont autorisées.")

    if _FORBIDDEN_KEYWORDS.search(stripped):
        return SafetyCheck(is_safe=False, reason="Mot-clé de mutation/DDL détecté dans la requête.")

    return SafetyCheck(is_safe=True)


class SQLExecutor:
    """Exécute des requêtes SELECT validées contre la base SQLite configurée."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = Path(db_path or settings.sqlite_db_path)

    def execute(self, sql: str, row_limit: int = 500) -> ExecutionResult:
        safety = check_is_safe(sql)
        if not safety.is_safe:
            return ExecutionResult(status=ExecutionStatus.REJECTED_UNSAFE, error_message=safety.reason)

        if not self.db_path.exists():
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                error_message=f"Base introuvable: {self.db_path}. Lance d'abord data/seed_db.py.",
            )

        uri = f"file:{self.db_path.as_posix()}?mode=ro"
        try:
            with sqlite3.connect(uri, uri=True) as conn:
                cursor = conn.execute(sql)
                columns = [d[0] for d in cursor.description] if cursor.description else []
                rows = [list(row) for row in cursor.fetchmany(row_limit)]
        except sqlite3.Error as exc:
            return ExecutionResult(status=ExecutionStatus.ERROR, error_message=str(exc))

        status = ExecutionStatus.SUCCESS if rows else ExecutionStatus.EMPTY
        return ExecutionResult(status=status, columns=columns, rows=rows, row_count=len(rows))
