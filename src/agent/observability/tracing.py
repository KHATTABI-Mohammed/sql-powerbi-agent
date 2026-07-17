"""Intégration Langfuse : trace chaque étape du graphe (retrieval, génération, exécution).

Le client Langfuse est créé de façon paresseuse et silencieuse : si les clés
`LANGFUSE_*` ne sont pas renseignées, `is_enabled()` retourne False et
`observe_node` devient un simple passe-plat (no-op), pour ne jamais bloquer
l'exécution locale/hors-ligne de l'agent.
"""

from __future__ import annotations

import functools
from typing import Callable, TypeVar

from agent.config import settings

F = TypeVar("F", bound=Callable)


def is_enabled() -> bool:
    return bool(settings.langfuse_public_key and settings.langfuse_secret_key)


@functools.lru_cache(maxsize=1)
def get_langfuse_client():
    if not is_enabled():
        return None
    from langfuse import Langfuse

    return Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )


def get_langchain_callback_handler():
    """Callback à passer aux appels LangChain (`.invoke(..., config={"callbacks": [...]})`)."""
    if not is_enabled():
        return None
    from langfuse.callback import CallbackHandler

    return CallbackHandler(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )


def observe_node(name: str) -> Callable[[F], F]:
    """Décorateur pour tracer un nœud du graphe LangGraph comme un span Langfuse nommé.

    Utilise `langfuse.decorators.observe` si Langfuse est configuré, sinon
    retourne la fonction telle quelle (aucun overhead, aucune dépendance dure).
    """

    def decorator(func: F) -> F:
        if not is_enabled():
            return func

        from langfuse.decorators import observe

        return observe(name=name)(func)

    return decorator
