"""État partagé du graphe LangGraph (`AgentState`).

LangGraph fait circuler et fusionne ce `TypedDict` entre les nœuds ; chaque
nœud ne retourne que les clés qu'il modifie.
"""

from __future__ import annotations

from typing import TypedDict

from agent.schemas import ExecutionResult, RetrievedChunk, SQLGenerationResult


class AgentState(TypedDict, total=False):
    # Entrée
    question: str

    # Étape RAG
    retrieved_chunks: list[RetrievedChunk]
    context_text: str

    # Étape génération SQL
    sql_result: SQLGenerationResult
    retry_count: int
    generation_error: str | None

    # Étape validation / exécution
    execution_result: ExecutionResult

    # Sortie
    summary: str
    error: str | None
