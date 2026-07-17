"""Construction du graphe LangGraph :

    retrieve_context -> generate_sql -> execute_sql -> summarize_answer
                              ^_____________|  (retry si échec, jusqu'à max_sql_retries)
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from agent.config import settings
from agent.graph.nodes import execute_sql, generate_sql, retrieve_context, summarize_answer
from agent.graph.state import AgentState


def _route_after_generate(state: AgentState) -> str:
    if state.get("generation_error") and state.get("retry_count", 0) <= settings.max_sql_retries:
        return "generate_sql"
    if state.get("generation_error"):
        return "summarize_answer"
    return "execute_sql"


def _route_after_execute(state: AgentState) -> str:
    if state.get("generation_error") and state.get("retry_count", 0) <= settings.max_sql_retries:
        return "generate_sql"
    return "summarize_answer"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("generate_sql", generate_sql)
    graph.add_node("execute_sql", execute_sql)
    graph.add_node("summarize_answer", summarize_answer)

    graph.set_entry_point("retrieve_context")
    graph.add_edge("retrieve_context", "generate_sql")

    graph.add_conditional_edges(
        "generate_sql",
        _route_after_generate,
        {"generate_sql": "generate_sql", "execute_sql": "execute_sql", "summarize_answer": "summarize_answer"},
    )
    graph.add_conditional_edges(
        "execute_sql",
        _route_after_execute,
        {"generate_sql": "generate_sql", "summarize_answer": "summarize_answer"},
    )

    graph.add_edge("summarize_answer", END)

    return graph.compile()
