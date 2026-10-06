"""Chargement de la configuration (config/projects.yaml)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# Extensions indexées par défaut (code + documentation)
DEFAULT_INCLUDE = [
    "**/*.cs", "**/*.py", "**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx",
    "**/*.java", "**/*.kt", "**/*.go", "**/*.rs", "**/*.cpp", "**/*.hpp",
    "**/*.c", "**/*.h", "**/*.sql", "**/*.ps1", "**/*.sh",
    "**/*.yaml", "**/*.yml", "**/*.toml", "**/*.md", "**/*.txt",
]

# Exclusions par défaut (artefacts de build, dépendances, VCS)
DEFAULT_EXCLUDE = [
    "**/.git/**", "**/.vs/**", "**/.idea/**", "**/.vscode/**",
    "**/node_modules/**", "**/bin/**", "**/obj/**", "**/dist/**",
    "**/build/**", "**/out/**", "**/target/**", "**/__pycache__/**",
    "**/.venv/**", "**/venv/**", "**/packages/**", "**/coverage/**",
    "**/*.min.js", "**/*.map", "**/package-lock.json", "**/*.lock",
]


@dataclass
class ChunkingConfig:
    max_chars: int = 1600
    overlap_chars: int = 200
    max_file_bytes: int = 200_000
    batch_size: int = 64


@dataclass
class ProjectConfig:
    name: str
    path: Path
    include: list[str] = field(default_factory=lambda: list(DEFAULT_INCLUDE))
    exclude: list[str] = field(default_factory=lambda: list(DEFAULT_EXCLUDE))


@dataclass
class RagConfig:
    config_path: Path
    embedding_model: str
    database_path: Path
    collection: str
    chunking: ChunkingConfig
    projects: list[ProjectConfig]


def default_config_path() -> Path:
    """Chemin du fichier de config : $COPILOT_RAG_CONFIG ou config/projects.yaml du dépôt."""
    env = os.environ.get("COPILOT_RAG_CONFIG")
    if env:
        return Path(env).expanduser().resolve()
    return (Path(__file__).resolve().parents[2] / "config" / "projects.yaml").resolve()


def load_config(path: Path | str | None = None) -> RagConfig:
    cfg_path = Path(path).expanduser().resolve() if path else default_config_path()
    if not cfg_path.is_file():
        raise FileNotFoundError(f"Configuration introuvable : {cfg_path}")

    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    base = cfg_path.parent

    chunk_raw = raw.get("chunking", {}) or {}
    chunking = ChunkingConfig(
        **{k: v for k, v in chunk_raw.items() if k in ChunkingConfig.__dataclass_fields__}
    )

    db_path = Path(raw.get("database_path", "../data/chroma"))
    if not db_path.is_absolute():
        db_path = (base / db_path).resolve()

    projects: list[ProjectConfig] = []
    for p in raw.get("projects", []) or []:
        ppath = Path(p["path"])
        if not ppath.is_absolute():
            ppath = (base / ppath).resolve()
        projects.append(
            ProjectConfig(
                name=p["name"],
                path=ppath,
                include=list(p.get("include") or DEFAULT_INCLUDE),
                exclude=[*DEFAULT_EXCLUDE, *(p.get("exclude") or [])],
            )
        )

    return RagConfig(
        config_path=cfg_path,
        embedding_model=raw.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2"),
        database_path=db_path,
        collection=raw.get("collection", "code_chunks"),
        chunking=chunking,
        projects=projects,
    )
