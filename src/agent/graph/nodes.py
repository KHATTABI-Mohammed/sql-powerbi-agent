"""Nœuds du graphe LangGraph : chaque fonction prend l'`AgentState` et retourne
un dict partiel avec les clés qu'elle met à jour.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from agent.graph.state import AgentState
from agent.llm import get_sql_generator
from agent.observability.tracing import observe_node
from agent.rag.retriever import SchemaRetriever
from agent.schemas import ExecutionStatus
from agent.sql.executor import SQLExecutor

SYSTEM_PROMPT = """Tu es un expert SQL qui traduit des questions métier en requêtes SQLite \
en lecture seule (SELECT uniquement), destinées à alimenter des rapports Power BI.

Règles strictes :
- N'utilise QUE les tables et colonnes présentes dans le contexte de schéma fourni.
- Génère uniquement des requêtes SELECT (jamais INSERT/UPDATE/DELETE/DDL).
- Si la question est ambiguë, fais l'hypothèse la plus raisonnable et explique-la.
- Renseigne `tables_used` avec les tables réellement référencées.
- Renseigne `confidence` (0-1) selon ta certitude que la requête répond à la question."""


@observe_node(name="retrieve_context")
def retrieve_context(state: AgentState) -> dict:
    retriever = SchemaRetriever()
    chunks = retriever.retrieve(state["question"])
    return {
        "retrieved_chunks": chunks,
        "context_text": retriever.format_context(chunks),
    }


@observe_node(name="generate_sql")
def generate_sql(state: AgentState) -> dict:
    generator = get_sql_generator()

    user_prompt = f"Contexte de schéma:\n{state['context_text']}\n\nQuestion: {state['question']}"
    if state.get("generation_error"):
        user_prompt += (
            f"\n\nLa tentative précédente a échoué avec l'erreur suivante, corrige la requête: "
            f"{state['generation_error']}"
        )

    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_prompt)]

    try:
        result = generator.invoke(messages)
        return {"sql_result": result, "generation_error": None}
    except Exception as exc:  # erreur de validation Pydantic ou d'appel LLM
        return {"generation_error": str(exc), "retry_count": state.get("retry_count", 0) + 1}


@observe_node(name="execute_sql")
def execute_sql(state: AgentState) -> dict:
    executor = SQLExecutor()
    sql_result = state["sql_result"]
    execution = executor.execute(sql_result.sql)

    if execution.status in (ExecutionStatus.ERROR, ExecutionStatus.REJECTED_UNSAFE):
        return {
            "execution_result": execution,
            "generation_error": execution.error_message,
            "retry_count": state.get("retry_count", 0) + 1,
        }

    return {"execution_result": execution, "generation_error": None}


@observe_node(name="summarize_answer")
def summarize_answer(state: AgentState) -> dict:
    execution = state.get("execution_result")

    if execution is None or execution.status in (ExecutionStatus.ERROR, ExecutionStatus.REJECTED_UNSAFE):
        reason = state.get("generation_error") or "Erreur inconnue."
        return {"summary": f"Impossible de répondre à la question : {reason}", "error": reason}

    if execution.status == ExecutionStatus.EMPTY:
        return {"summary": "La requête s'est exécutée correctement mais n'a retourné aucune ligne.", "error": None}

    preview = execution.rows[:5]
    summary = (
        f"{execution.row_count} ligne(s) trouvée(s) sur les colonnes {execution.columns}. "
        f"Aperçu: {preview}"
    )
    return {"summary": summary, "error": None}
