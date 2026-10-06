"""Couche d'accès à la base vectorielle ChromaDB (persistante, locale)."""

from __future__ import annotations

from pathlib import Path

import chromadb

from .chunker import Chunk

DOC_LANGUAGES = ("markdown", "text")


class CodeStore:
    def __init__(self, db_path: Path, collection: str):
        db_path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(db_path))
        self._col = self._client.get_or_create_collection(
            name=collection, metadata={"hnsw:space": "cosine"}
        )

    # ---------- écriture ----------

    def existing_file_hash(self, project: str, path: str) -> str | None:
        res = self._col.get(
            where={"$and": [{"project": project}, {"path": path}]},
            include=["metadatas"],
            limit=1,
        )
        if res["ids"]:
            return res["metadatas"][0].get("file_hash")
        return None

    def delete_file(self, project: str, path: str) -> None:
        self._col.delete(where={"$and": [{"project": project}, {"path": path}]})

    def project_paths(self, project: str) -> set[str]:
        res = self._col.get(where={"project": project}, include=["metadatas"])
        return {md["path"] for md in res["metadatas"]}

    def upsert_chunks(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        if not chunks:
            return
        self._col.upsert(
            ids=[c.chunk_id for c in chunks],
            embeddings=embeddings,
            documents=[c.text for c in chunks],
            metadatas=[c.metadata for c in chunks],
        )

    # ---------- lecture ----------

    def search(
        self, embedding: list[float], top_k: int, where: dict | None = None
    ) -> list[dict]:
        res = self._col.query(
            query_embeddings=[embedding], n_results=top_k, where=where
        )
        results = []
        for i in range(len(res["ids"][0])):
            results.append(
                {
                    "document": res["documents"][0][i],
                    "metadata": res["metadatas"][0][i],
                    # distance cosinus -> similarité
                    "similarity": round(1 - res["distances"][0][i], 3),
                }
            )
        return results

    def count(self) -> int:
        return self._col.count()

    def counts_by(self, field: str) -> dict[str, int]:
        res = self._col.get(include=["metadatas"])
        counts: dict[str, int] = {}
        for md in res["metadatas"]:
            key = str(md.get(field, "?"))
            counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items()))
