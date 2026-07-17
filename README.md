# sql-powerbi-agent

Agent IA conversationnel qui traduit des questions en langage naturel en requêtes SQL,
conçu pour alimenter des workflows de reporting type Power BI.

- **Orchestration** : [LangGraph](https://github.com/langchain-ai/langgraph) — pipeline explicite avec boucle de retry
- **RAG** : [ChromaDB](https://www.trychroma.com/) + embeddings locaux (`sentence-transformers`) pour ancrer la génération SQL sur le schéma réel
- **LLM** : [Claude](https://www.anthropic.com) (Anthropic) via `langchain-anthropic`, sortie contrainte par tool-calling
- **Validation** : [Pydantic](https://docs.pydantic.dev/) pour toutes les données qui circulent entre les nœuds (pas de parsing de texte libre)
- **Observabilité** : [Langfuse](https://langfuse.com/) — tracing de chaque nœud du graphe (retrieval, génération, exécution)

## Architecture du pipeline

```
question (NL)
      │
      ▼
┌─────────────────┐
│ retrieve_context │  ChromaDB : récupère les docs de schéma pertinents (top-k)
└─────────────────┘
      │
      ▼
┌─────────────────┐
│   generate_sql    │  Claude + with_structured_output(SQLGenerationResult)
└─────────────────┘◄──┐
      │                │ retry (max_sql_retries) si erreur de génération/exécution
      ▼                │
┌─────────────────┐    │
│    execute_sql     │──┘
└─────────────────┘  SQLite en lecture seule, requêtes SELECT uniquement
      │
      ▼
┌─────────────────┐
│ summarize_answer  │  Résumé en langage naturel du résultat
└─────────────────┘
      │
      ▼
   réponse
```

Chaque nœud est une fonction pure `AgentState -> dict` (voir `src/agent/graph/nodes.py`),
assemblée dans un `StateGraph` LangGraph (`src/agent/graph/build.py`). Les échecs de
génération ou d'exécution SQL renvoient l'agent vers `generate_sql` avec le message
d'erreur en contexte, jusqu'à `max_sql_retries` tentatives.

## Structure du projet

```
sql-powerbi-agent/
├── src/agent/
│   ├── config.py              # Settings (pydantic-settings), lues depuis .env
│   ├── schemas.py             # Modèles Pydantic (contrat de données du graphe)
│   ├── llm.py                 # Client Claude + sortie structurée
│   ├── cli.py                 # CLI interactif
│   ├── rag/
│   │   ├── ingest.py          # Indexation des docs de schéma dans ChromaDB
│   │   └── retriever.py       # Recherche top-k dans ChromaDB
│   ├── sql/
│   │   └── executor.py        # Exécution SQLite lecture-seule + garde-fou anti-injection
│   ├── graph/
│   │   ├── state.py           # AgentState (TypedDict)
│   │   ├── nodes.py           # retrieve_context / generate_sql / execute_sql / summarize_answer
│   │   └── build.py           # Assemblage du StateGraph LangGraph
│   └── observability/
│       └── tracing.py         # Intégration Langfuse (no-op si non configuré)
├── data/
│   ├── schema_docs/*.md       # Documentation des tables (source du RAG)
│   ├── seed_db.py             # Crée data/powerbi_sample.db (SQLite) avec des données d'exemple
│   └── chroma/                # Persistance ChromaDB (générée, ignorée par git)
├── examples/
│   └── end_to_end_example.py  # Exemple complet : question -> ... -> réponse
├── tests/
│   ├── test_schemas.py
│   └── test_sql_executor.py
├── requirements.txt
└── pyproject.toml
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copie les variables d'environnement nécessaires (clé Anthropic, clés Langfuse optionnelles)
dans un fichier `.env` à la racine du projet :

```
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-5

CHROMA_PERSIST_DIR=./data/chroma
CHROMA_COLLECTION_NAME=schema_docs

SQLITE_DB_PATH=./data/powerbi_sample.db

LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

MAX_SQL_RETRIES=2
RAG_TOP_K=4
```

Langfuse est optionnel : si `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` sont absentes,
le tracing est simplement désactivé (aucune erreur).

## Démarrage rapide

```bash
# 1. Créer la base SQLite d'exemple (clients / produits / commandes)
python data/seed_db.py

# 2. Indexer la documentation de schéma dans ChromaDB (embeddings locaux, pas d'appel API)
python -m agent.rag.ingest

# 3. Lancer le pipeline end-to-end sur une question d'exemple
python examples/end_to_end_example.py

# 4. Ou en mode interactif
python -m agent.cli "Quel est le chiffre d'affaires total par pays ?"
```

## Tests

```bash
pytest
```

Les tests couvrent la validation Pydantic (`schemas.py`) et le garde-fou de sécurité SQL
(`sql/executor.py`) ; ils ne nécessitent aucune clé API.

## Sécurité

- L'exécuteur SQL (`sql/executor.py`) rejette toute requête qui n'est pas un `SELECT`
  (ou `WITH ... SELECT`) unique, et ouvre la connexion SQLite en mode `?mode=ro`
  (lecture seule au niveau moteur, indépendamment de la validation applicative).
- Le LLM ne génère jamais de SQL exécuté à l'aveugle : la sortie est d'abord validée par
  le schéma Pydantic `SQLGenerationResult`, puis re-vérifiée par `check_is_safe` avant exécution.

## Adapter à une autre base cible

Le jeu de données fourni (`customers` / `products` / `orders` / `order_items`) est un
exemple minimal de type "ventes". Pour brancher l'agent sur ton propre entrepôt de données :

1. Remplace `data/schema_docs/*.md` par la documentation de tes tables réelles.
2. Ajuste `SQLITE_DB_PATH` (ou adapte `sql/executor.py` pour un autre moteur : Postgres,
   SQL Server, etc. — le connecteur Power BI consommera le même contrat `ExecutionResult`).
3. Relance `python -m agent.rag.ingest` pour ré-indexer.
