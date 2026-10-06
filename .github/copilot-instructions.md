# CopilotRAG — Instructions Copilot

## But du dépôt

Ce dépôt construit une **base RAG locale** qui indexe le code de plusieurs projets
de référence et l'expose à GitHub Copilot via un **serveur MCP** (`copilot-rag`).
Objectif : homogénéiser le code généré avec les patterns des projets existants.

## Architecture

- `src/copilot_rag/config.py` : chargement de `config/projects.yaml`.
- `src/copilot_rag/chunker.py` : découpage des fichiers en chunks (avec recouvrement),
  respect des `.gitignore` et des patterns include/exclude (gitwildmatch).
- `src/copilot_rag/embeddings.py` : embeddings locaux via sentence-transformers
  (aucune clé API, vecteurs normalisés).
- `src/copilot_rag/store.py` : persistance ChromaDB (`data/chroma`, similarité cosinus).
- `src/copilot_rag/ingest.py` : ingestion incrémentale (hash de fichier, purge des
  fichiers supprimés). CLI : `python -m copilot_rag.ingest`.
- `src/copilot_rag/server.py` : serveur MCP stdio (`MCPServer` du SDK officiel),
  outils `search_code`, `find_similar_code`, `search_documentation`,
  `list_projects`, `index_stats`.

## Documentation du SDK MCP Python (v2)

Références officielles à consulter avant de modifier `server.py` :

- Get started : https://py.sdk.modelcontextprotocol.io/get-started/
- Référence API : https://py.sdk.modelcontextprotocol.io/api/mcp/
- Repo et exemples : https://github.com/modelcontextprotocol/python-sdk
- Spécification MCP : https://modelcontextprotocol.io/specification/latest

Points d'attention v2 : importer `MCPServer` depuis `mcp.server.mcpserver`
(et non l'ancien `mcp.server.fastmcp`), passer les paramètres du constructeur
par mot-clé après `name`, démarrer en stdio avec `mcp.run()`.

## Règles de contribution

- Utiliser le serveur MCP `copilot-rag` (outils `search_code`, `search_documentation`)
  avant d'écrire du nouveau code, et s'aligner sur les patterns trouvés.
- Docstrings style Google, typage explicite, exceptions métier typées.
- Commandes : ingestion `python -m copilot_rag.ingest`, tests `pytest`,
  smoke test MCP `python scripts/smoke_test.py`.
