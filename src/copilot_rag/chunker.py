"""Découpage des fichiers source en chunks annotés (projet, chemin, lignes, langage)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

import pathspec

from .config import ChunkingConfig

EXTENSION_LANGUAGE = {
    ".cs": "csharp", ".py": "python", ".ts": "typescript", ".tsx": "typescriptreact",
    ".js": "javascript", ".jsx": "javascriptreact", ".java": "java", ".kt": "kotlin",
    ".go": "go", ".rs": "rust", ".cpp": "cpp", ".hpp": "cpp", ".c": "c", ".h": "c",
    ".sql": "sql", ".ps1": "powershell", ".sh": "bash", ".yaml": "yaml", ".yml": "yaml",
    ".toml": "toml", ".md": "markdown", ".txt": "text",
}


@dataclass
class Chunk:
    project: str
    path: str  # chemin relatif POSIX dans le projet
    language: str
    start_line: int
    end_line: int
    text: str
    file_hash: str

    @property
    def chunk_id(self) -> str:
        raw = f"{self.project}|{self.path}|{self.start_line}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:32]

    @property
    def metadata(self) -> dict:
        return {
            "project": self.project,
            "path": self.path,
            "language": self.language,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "file_hash": self.file_hash,
        }


def is_binary(data: bytes) -> bool:
    return b"\0" in data[:8192]


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def iter_project_files(
    root: Path, include: Iterable[str], exclude: Iterable[str]
) -> Iterator[tuple[Path, str]]:
    """Itère les fichiers indexables d'un projet.

    Combine les exclusions par défaut + le .gitignore du projet s'il existe.
    Retourne des tuples (chemin absolu, chemin relatif POSIX).
    """
    excludes = list(exclude)
    gitignore = root / ".gitignore"
    if gitignore.is_file():
        excludes.extend(gitignore.read_text(encoding="utf-8", errors="replace").splitlines())

    incl_spec = pathspec.PathSpec.from_lines("gitwildmatch", include)
    excl_spec = pathspec.PathSpec.from_lines("gitwildmatch", excludes)

    for candidate in sorted(root.rglob("*")):
        if not candidate.is_file():
            continue
        rel = candidate.relative_to(root).as_posix()
        if excl_spec.match_file(rel):
            continue
        if not incl_spec.match_file(rel):
            continue
        yield candidate, rel


def chunk_text(
    text: str,
    project: str,
    path: str,
    language: str,
    fhash: str,
    max_chars: int = 1600,
    overlap_chars: int = 200,
) -> list[Chunk]:
    """Découpe un texte en chunks de lignes avec recouvrement."""
    chunks: list[Chunk] = []
    buffer: list[str] = []
    buffer_start = 1
    size = 0

    def flush(end_line: int) -> None:
        nonlocal buffer, buffer_start, size
        content = "\n".join(buffer)
        if content.strip():
            chunks.append(
                Chunk(project, path, language, buffer_start, end_line, content, fhash)
            )
        # Recouvrement : conserve les dernières lignes dans la limite de overlap_chars
        keep: list[str] = []
        kept = 0
        for line in reversed(buffer):
            if kept + len(line) + 1 > overlap_chars:
                break
            keep.append(line)
            kept += len(line) + 1
        keep.reverse()
        buffer = keep
        buffer_start = end_line - len(buffer) + 1
        size = kept

    for lineno, line in enumerate(text.splitlines(), start=1):
        line_size = len(line) + 1
        if buffer and size + line_size > max_chars:
            flush(lineno - 1)
        if not buffer:
            buffer_start = lineno
            size = 0
        buffer.append(line)
        size += line_size

    if buffer:
        flush(len(text.splitlines()))

    return chunks


def chunk_file(
    path: Path, rel: str, project: str, cfg: ChunkingConfig, fhash: str | None = None
) -> list[Chunk]:
    """Lit et découpe un fichier. Retourne [] si binaire, trop gros ou vide."""
    data = path.read_bytes()
    if len(data) > cfg.max_file_bytes or is_binary(data):
        return []
    text = data.decode("utf-8", errors="replace")
    language = EXTENSION_LANGUAGE.get(path.suffix.lower(), "text")
    return chunk_text(
        text,
        project,
        rel,
        language,
        fhash or hashlib.sha256(data).hexdigest(),
        max_chars=cfg.max_chars,
        overlap_chars=cfg.overlap_chars,
    )
