"""Client LLM : encapsule Claude (Anthropic) via LangChain, avec sortie structurée Pydantic.

Aucun appel réseau n'est effectué à l'import de ce module : le client n'est
instancié (et donc n'a besoin d'une clé API valide) qu'au moment où
`get_sql_generator()` est réellement invoqué par un nœud du graphe.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_anthropic import ChatAnthropic

from agent.config import settings
from agent.schemas import SQLGenerationResult


@lru_cache(maxsize=1)
def get_chat_model() -> ChatAnthropic:
    """Instancie le modèle Claude configuré (paresseux, mis en cache)."""
    return ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=0,
        max_tokens=1024,
    )


@lru_cache(maxsize=1)
def get_sql_generator():
    """Retourne un modèle Claude contraint à produire un `SQLGenerationResult` valide.

    `with_structured_output` s'appuie sur le tool-calling natif de Claude : le modèle
    est forcé d'émettre des arguments conformes au schéma Pydantic, qui est ensuite
    validé côté client. En cas d'échec de validation, LangChain lève une erreur que
    le graphe peut intercepter pour déclencher une nouvelle tentative.
    """
    return get_chat_model().with_structured_output(SQLGenerationResult)
