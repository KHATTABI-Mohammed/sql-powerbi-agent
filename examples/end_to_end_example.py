"""Exemple end-to-end du pipeline complet :

    question (NL) -> RAG retrieval (ChromaDB) -> génération SQL (Claude, Pydantic)
                   -> exécution (SQLite) -> réponse en langage naturel

Prérequis avant de lancer ce script:
    1. pip install -r requirements.txt
    2. python data/seed_db.py                      # crée la base SQLite d'exemple
    3. python -m agent.rag.ingest                   # indexe les docs de schéma dans ChromaDB
    4. Renseigner ANTHROPIC_API_KEY (et éventuellement LANGFUSE_*) dans un fichier .env

Usage:
    python examples/end_to_end_example.py
"""

from __future__ import annotations

from agent.graph.build import build_graph

QUESTION = "Quel est le chiffre d'affaires total par client, du plus élevé au plus faible ?"


def main() -> None:
    app = build_graph()

    print(f"Question: {QUESTION}\n")
    print("--- Exécution du graphe LangGraph ---")

    final_state = app.invoke({"question": QUESTION, "retry_count": 0})

    print("\n1) Contexte RAG récupéré:")
    for chunk in final_state.get("retrieved_chunks", []):
        print(f"   - {chunk.source} (score={chunk.score})")

    sql_result = final_state.get("sql_result")
    if sql_result:
        print("\n2) SQL généré (validé par Pydantic):")
        print(f"   SQL:         {sql_result.sql}")
        print(f"   Explication: {sql_result.explanation}")
        print(f"   Tables:      {sql_result.tables_used}")
        print(f"   Confiance:   {sql_result.confidence}")

    execution = final_state.get("execution_result")
    if execution:
        print(f"\n3) Résultat d'exécution ({execution.status.value}):")
        print(f"   Colonnes: {execution.columns}")
        for row in execution.rows:
            print(f"   {row}")

    print("\n4) Réponse finale:")
    print(f"   {final_state.get('summary')}")


if __name__ == "__main__":
    main()
