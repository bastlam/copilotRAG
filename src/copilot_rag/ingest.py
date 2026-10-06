"""Pipeline d'ingestion : scan -> chunk -> embeddings -> ChromaDB.

Incrémental : un fichier n'est ré-indexé que si son hash a changé.
Les fichiers supprimés du disque sont purgés de la base.

Usage :
    python -m copilot_rag.ingest [--config CONFIG] [--project NOM] [--force]
"""

from __future__ import annotations

import argparse
import sys

from .chunker import chunk_file, file_hash, iter_project_files
from .config import load_config
from .embeddings import embed_texts
from .store import CodeStore


def ingest(
    config_path: str | None = None,
    only_project: str | None = None,
    force: bool = False,
) -> int:
    cfg = load_config(config_path)
    store = CodeStore(cfg.database_path, cfg.collection)
    print(f"Config : {cfg.config_path}")
    print(f"Base   : {cfg.database_path} (collection '{cfg.collection}')")
    print(f"Modèle : {cfg.embedding_model}\n")

    total_indexed = 0
    for project in cfg.projects:
        if only_project and project.name != only_project:
            continue
        if not project.path.is_dir():
            print(f"[SKIP] {project.name} : dossier introuvable ({project.path})")
            continue

        seen: set[str] = set()
        pending = []
        scanned = unchanged = 0

        for fpath, rel in iter_project_files(project.path, project.include, project.exclude):
            seen.add(rel)
            scanned += 1
            h = file_hash(fpath)
            if not force and store.existing_file_hash(project.name, rel) == h:
                unchanged += 1
                continue
            store.delete_file(project.name, rel)
            pending.extend(chunk_file(fpath, rel, project.name, cfg.chunking, fhash=h))

        # Purge des fichiers supprimés du disque
        purged = 0
        for old_path in store.project_paths(project.name) - seen:
            store.delete_file(project.name, old_path)
            purged += 1

        # Embeddings + upsert par lots
        bs = cfg.chunking.batch_size
        for i in range(0, len(pending), bs):
            batch = pending[i : i + bs]
            vectors = embed_texts([c.text for c in batch], cfg.embedding_model, bs)
            store.upsert_chunks(batch, vectors)

        total_indexed += len(pending)
        print(
            f"[OK] {project.name} : {scanned} fichiers analysés, "
            f"{unchanged} inchangés, {len(pending)} chunks indexés, {purged} fichiers purgés"
        )

    print(f"\nTerminé : {total_indexed} nouveaux chunks, {store.count()} chunks au total.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Indexe les projets dans la base RAG.")
    parser.add_argument("--config", help="Chemin de projects.yaml (défaut : config/projects.yaml)")
    parser.add_argument("--project", help="N'indexer qu'un seul projet")
    parser.add_argument("--force", action="store_true", help="Ré-indexer même les fichiers inchangés")
    args = parser.parse_args(argv)
    try:
        return ingest(args.config, args.project, args.force)
    except FileNotFoundError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
