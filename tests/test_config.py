"""Tests de chargement de la configuration (projets locaux et git)."""

from pathlib import Path

import pytest

from copilot_rag.config import load_config


def _write(tmp_path: Path, body: str) -> Path:
    cfg = tmp_path / "projects.yaml"
    cfg.write_text(body, encoding="utf-8")
    return cfg


def test_local_and_git_projects(tmp_path):
    cfg = _write(
        tmp_path,
        """
projects:
  - name: local
    path: ./src
  - name: distant
    git: https://example.com/org/repo.git
    ref: develop
""",
    )
    conf = load_config(cfg)
    local, distant = conf.projects

    assert local.path == (tmp_path / "src").resolve()
    assert local.git is None
    assert local.ref is None
    assert local.resolve_path(conf.repos_cache) == local.path

    assert distant.path is None
    assert distant.git == "https://example.com/org/repo.git"
    assert distant.ref == "develop"
    assert distant.resolve_path(conf.repos_cache) == conf.repos_cache / "distant"


def test_path_and_git_are_mutually_exclusive(tmp_path):
    cfg = _write(
        tmp_path,
        """
projects:
  - name: ko
    path: ./src
    git: https://example.com/repo.git
""",
    )
    with pytest.raises(ValueError, match="path.*git|git.*path"):
        load_config(cfg)


def test_project_requires_path_or_git(tmp_path):
    cfg = _write(tmp_path, "projects:\n  - name: vide\n")
    with pytest.raises(ValueError, match="path.*git|git.*path"):
        load_config(cfg)


def test_repos_cache_default_and_override(tmp_path):
    cfg = _write(tmp_path, "projects: []\n")
    assert load_config(cfg).repos_cache == (tmp_path / ".." / "data" / "repos").resolve()

    cfg2 = _write(tmp_path, "repos_cache: ./cache\nprojects: []\n")
    assert load_config(cfg2).repos_cache == (tmp_path / "cache").resolve()
