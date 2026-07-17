"""Modèles Pydantic utilisés pour valider les données qui circulent dans le graphe LangGraph.

Le point clé : la génération SQL par le LLM est contrainte à produire un objet
`SQLGenerationResult` (via structured output / tool calling), ce qui évite d'avoir
à parser du texte libre et garantit un contrat de données stable entre les nœuds.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class RetrievedChunk(BaseModel):
    """Un fragment de documentation de schéma récupéré depuis ChromaDB."""

    content: str
    source: str = Field(description="Nom du fichier ou de la table d'origine")
    score: float = Field(ge=0.0, le=1.0, description="Score de similarité (0 = éloigné, 1 = identique)")


class SQLGenerationResult(BaseModel):
    """Sortie structurée attendue du LLM pour la génération de requête SQL."""

    sql: str = Field(description="Requête SQL SELECT générée, sans point-virgule final")
    explanation: str = Field(description="Explication courte, en langage naturel, de ce que fait la requête")
    tables_used: list[str] = Field(default_factory=list, description="Tables référencées dans la requête")
    confidence: float = Field(ge=0.0, le=1.0, description="Confiance du modèle dans la validité de la requête")

    @field_validator("sql")
    @classmethod
    def strip_trailing_semicolon(cls, value: str) -> str:
        return value.strip().rstrip(";").strip()


class SafetyCheck(BaseModel):
    """Résultat de la validation de sécurité/lecture-seule d'une requête SQL."""

    is_safe: bool
    reason: str = ""


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    EMPTY = "empty"
    ERROR = "error"
    REJECTED_UNSAFE = "rejected_unsafe"


class ExecutionResult(BaseModel):
    """Résultat structuré de l'exécution SQL contre la base cible."""

    status: ExecutionStatus
    columns: list[str] = Field(default_factory=list)
    rows: list[list] = Field(default_factory=list)
    row_count: int = 0
    error_message: str | None = None


class AgentAnswer(BaseModel):
    """Réponse finale renvoyée à l'utilisateur, prête à être affichée (CLI, API, Power BI)."""

    question: str
    sql: str
    explanation: str
    columns: list[str]
    rows: list[list]
    row_count: int
    summary: str = Field(description="Résumé en langage naturel des résultats")
