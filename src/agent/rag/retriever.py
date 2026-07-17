"""Récupération de contexte de schéma pertinent depuis ChromaDB (étape RAG)."""

from __future__ import annotations

from agent.config import settings
from agent.rag.ingest import get_or_create_collection
from agent.schemas import RetrievedChunk


class SchemaRetriever:
    """Interroge la collection ChromaDB de documentation de schéma."""

    def __init__(self, top_k: int | None = None) -> None:
        self.top_k = top_k or settings.rag_top_k
        self._collection = get_or_create_collection()

    def retrieve(self, question: str) -> list[RetrievedChunk]:
        results = self._collection.query(query_texts=[question], n_results=self.top_k)

        chunks: list[RetrievedChunk] = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, distance in zip(documents, metadatas, distances):
            # ChromaDB renvoie une distance cosine (0 = identique) ; on la convertit en score de similarité.
            similarity = max(0.0, 1.0 - distance)
            chunks.append(
                RetrievedChunk(
                    content=doc,
                    source=(meta or {}).get("source", "unknown"),
                    score=round(similarity, 4),
                )
            )
        return chunks

    @staticmethod
    def format_context(chunks: list[RetrievedChunk]) -> str:
        """Sérialise les chunks récupérés en un bloc de texte utilisable dans le prompt LLM."""
        if not chunks:
            return "Aucun contexte de schéma pertinent trouvé."
        parts = [f"### {c.source} (similarité={c.score})\n{c.content}" for c in chunks]
        return "\n\n".join(parts)
