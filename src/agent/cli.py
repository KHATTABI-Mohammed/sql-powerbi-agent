"""CLI interactif : pose une question en langage naturel, l'agent répond.

Usage:
    python -m agent.cli "Quel est le chiffre d'affaires total par pays ?"
    python -m agent.cli            # mode interactif
"""

from __future__ import annotations

import sys

from rich.console import Console
from rich.table import Table

from agent.graph.build import build_graph

console = Console()


def run_question(question: str) -> dict:
    app = build_graph()
    return app.invoke({"question": question, "retry_count": 0})


def display_result(state: dict) -> None:
    execution = state.get("execution_result")
    sql_result = state.get("sql_result")

    if sql_result:
        console.print(f"\n[bold cyan]SQL généré:[/bold cyan] {sql_result.sql}")
        console.print(f"[dim]{sql_result.explanation}[/dim]")

    if execution and execution.columns:
        table = Table(show_header=True, header_style="bold magenta")
        for col in execution.columns:
            table.add_column(col)
        for row in execution.rows[:20]:
            table.add_row(*[str(v) for v in row])
        console.print(table)

    console.print(f"\n[bold green]Résumé:[/bold green] {state.get('summary')}")


def main() -> None:
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        display_result(run_question(question))
        return

    console.print("[bold]sql-powerbi-agent[/bold] — pose une question (Ctrl+C pour quitter)\n")
    while True:
        try:
            question = console.input("[bold blue]> [/bold blue]")
        except (KeyboardInterrupt, EOFError):
            break
        if not question.strip():
            continue
        display_result(run_question(question))


if __name__ == "__main__":
    main()
