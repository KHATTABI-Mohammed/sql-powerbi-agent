"""Indexation des documents de schéma (tables/colonnes) dans ChromaDB.

Les embeddings sont calculés localement via `sentence-transformers`
(modèle `all-MiniLM-L6-v2`) : l'étape d'indexation ne dépend d'aucune
API externe, seule la génération SQL appelle Claude.
"""

from __future__ import annotations

from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from agent.config import settings

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


def get_chroma_client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=settings.chroma_persist_dir)


def get_or_create_collection(client: chromadb.ClientAPI | None = None):
    client = client or get_chroma_client()
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL_NAME)
    return client.get_or_create_collection(
        name=settings.chroma_collection_name,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )


def ingest_schema_docs(schema_dir: str | Path) -> int:
    """Découpe et indexe chaque fichier `.md` de `schema_dir` (un fichier = une table).

    Retourne le nombre de documents indexés.
    """
    schema_dir = Path(schema_dir)
    collection = get_or_create_collection()

    doc_paths = sorted(schema_dir.glob("*.md"))
    if not doc_paths:
        raise FileNotFoundError(f"Aucun fichier .md trouvé dans {schema_dir}")

    ids, documents, metadatas = [], [], []
    for path in doc_paths:
        text = path.read_text(encoding="utf-8")
        ids.append(path.stem)
        documents.append(text)
        metadatas.append({"source": path.name})

    # upsert : ré-exécutable sans dupliquer les entrées
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return len(ids)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[3]
    count = ingest_schema_docs(root / "data" / "schema_docs")
    print(f"{count} documents de schéma indexés dans la collection '{settings.chroma_collection_name}'.")
