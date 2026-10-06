"""Serveur MCP exposant la base RAG à GitHub Copilot (transport stdio).

Démarré automatiquement par VS Code via .vscode/mcp.json :
    python -m copilot_rag.server [--config CONFIG]

Documentation du SDK : https://py.sdk.modelcontextprotocol.io/
"""

from __future__ import annotations

import argparse
import sys

from mcp.server.mcpserver import MCPServer

from .config import RagConfig, load_config
from .embeddings import embed_texts
from .store import DOC_LANGUAGES, CodeStore

# --- Initialisation (config via --config ou COPILOT_RAG_CONFIG) -------------
_parser = argparse.ArgumentParser()
_parser.add_argument("--config", default=None)
_args, _ = _parser.parse_known_args()

_cfg: RagConfig = load_config(_args.config)
_store = CodeStore(_cfg.database_path, _cfg.collection)

mcp = MCPServer(
    "copilot-rag",
    version="0.1.0",
    instructions=(
        "Cette base RAG contient le code et la documentation de projets de référence. "
        "AVANT de générer du nouveau code, appelez search_code pour trouver des "
        "implémentations existantes et alignez-vous sur leurs conventions "
        "(nommage, structure, gestion des erreurs, logging). "
        "Utilisez search_documentation pour les conventions rédigées (README, guides), "
        "et find_similar_code pour comparer un extrait de code à l'existant."
    ),
)


# --- Helpers -----------------------------------------------------------------


def _where(
    project: str | None = None,
    language: str | None = None,
    languages: tuple[str, ...] | None = None,
) -> dict | None:
    conds: list[dict] = []
    if project:
        conds.append({"project": project})
    if language:
        conds.append({"language": language})
    if languages:
        conds.append({"language": {"$in": list(languages)}})
    if not conds:
        return None
    return conds[0] if len(conds) == 1 else {"$and": conds}


def _format_results(results: list[dict]) -> str:
    if not results:
        return (
            "Aucun résultat. Vérifiez que l'ingestion a été lancée "
            "(python -m copilot_rag.ingest) ou élargissez la requête."
        )
    parts = []
    for r in results:
        md = r["metadata"]
        parts.append(
            f"### {md['path']} — lignes {md['start_line']}–{md['end_line']} "
            f"(projet `{md['project']}`, similarité {r['similarity']})\n"
            f"```{md['language']}\n{r['document']}\n```"
        )
    return "\n\n".join(parts)


def _embed(query: str) -> list[float]:
    return embed_texts([query], _cfg.embedding_model)[0]


# --- Outils MCP ---------------------------------------------------------------


@mcp.tool()
def search_code(
    query: str,
    project: str | None = None,
    language: str | None = None,
    top_k: int = 8,
) -> str:
    """Recherche sémantique de code dans les projets de référence indexés.

    À utiliser AVANT d'écrire du nouveau code afin de réutiliser les patterns
    existants et de produire un code homogène avec les autres projets.

    Args:
        query: description en langage naturel ou extrait de code recherché.
        project: filtre sur un projet indexé (voir list_projects), optionnel.
        language: filtre par langage (csharp, python, typescript, sql...), optionnel.
        top_k: nombre de résultats (1 à 20, défaut 8).
    """
    top_k = max(1, min(top_k, 20))
    results = _store.search(_embed(query), top_k, _where(project, language))
    return _format_results(results)


@mcp.tool()
def find_similar_code(snippet: str, top_k: int = 5) -> str:
    """Trouve du code existant similaire à un extrait donné (doublons, réutilisation).

    Args:
        snippet: extrait de code à comparer avec la base.
        top_k: nombre de résultats (1 à 20, défaut 5).
    """
    top_k = max(1, min(top_k, 20))
    results = _store.search(_embed(snippet), top_k)
    return _format_results(results)


@mcp.tool()
def search_documentation(
    query: str, project: str | None = None, top_k: int = 5
) -> str:
    """Recherche dans la documentation indexée (README, guides de conventions).

    Args:
        query: sujet recherché (ex. "conventions de nommage", "gestion des erreurs").
        project: filtre sur un projet indexé, optionnel.
        top_k: nombre de résultats (1 à 20, défaut 5).
    """
    top_k = max(1, min(top_k, 20))
    results = _store.search(_embed(query), top_k, _where(project, languages=DOC_LANGUAGES))
    return _format_results(results)


@mcp.tool()
def list_projects() -> str:
    """Liste les projets indexés dans la base RAG avec leur volume de chunks."""
    counts = _store.counts_by("project")
    if not counts:
        return "Base vide. Lancez l'ingestion : python -m copilot_rag.ingest"
    lines = [f"- {name} : {n} chunks" for name, n in counts.items()]
    return "Projets indexés :\n" + "\n".join(lines)


@mcp.tool()
def index_stats() -> str:
    """Statistiques de la base : volumes par projet et par langage."""
    total = _store.count()
    if total == 0:
        return "Base vide. Lancez l'ingestion : python -m copilot_rag.ingest"
    projects = _store.counts_by("project")
    languages = _store.counts_by("language")
    out = [f"Total : {total} chunks", "", "Par projet :"]
    out += [f"- {k} : {v}" for k, v in projects.items()]
    out.append("")
    out.append("Par langage :")
    out += [f"- {k} : {v}" for k, v in languages.items()]
    return "\n".join(out)


def main() -> None:
    # Transport stdio : VS Code lance ce process et parle JSON-RPC sur stdin/stdout.
    mcp.run()


if __name__ == "__main__":
    main()
