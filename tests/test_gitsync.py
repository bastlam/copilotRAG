"""Tests de synchronisation git.

Nécessitent l'exécutable git (skip sinon). Un dépôt local sert de "remote"
(git accepte un chemin de dossier comme URL), ce qui évite tout accès réseau.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from copilot_rag.gitsync import GitSyncError, sync_repo

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git absent du PATH")


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    )
    return proc.stdout.strip()


def _make_remote(tmp_path: Path) -> Path:
    """Crée un dépôt git local jouant le rôle de remote, avec un commit."""
    remote = tmp_path / "remote"
    remote.mkdir()
    _git(remote, "init")
    _git(remote, "config", "user.name", "test")
    _git(remote, "config", "user.email", "test@example.com")
    (remote / "app.py").write_text("x = 1\n", encoding="utf-8")
    _git(remote, "add", ".")
    _git(remote, "commit", "-m", "initial")
    return remote


def test_clone_then_update(tmp_path):
    remote = _make_remote(tmp_path)
    dest = tmp_path / "cache" / "proj"

    commit1 = sync_repo(str(remote), dest)
    assert (dest / "app.py").read_text(encoding="utf-8") == "x = 1\n"
    assert commit1 == _git(remote, "rev-parse", "--short", "HEAD")

    # Nouveau commit sur la remote -> mis à jour au prochain sync
    (remote / "app.py").write_text("x = 2\n", encoding="utf-8")
    (remote / "new.py").write_text("y = 3\n", encoding="utf-8")
    _git(remote, "add", ".")
    _git(remote, "commit", "-m", "update")

    commit2 = sync_repo(str(remote), dest)
    assert commit2 == _git(remote, "rev-parse", "--short", "HEAD")
    assert (dest / "app.py").read_text(encoding="utf-8") == "x = 2\n"
    assert (dest / "new.py").is_file()


def test_sync_specific_ref(tmp_path):
    remote = _make_remote(tmp_path)
    _git(remote, "branch", "feature")

    dest = tmp_path / "cache" / "proj"
    sync_repo(str(remote), dest, ref="feature")
    assert _git(dest, "rev-parse", "--short", "HEAD") == _git(
        remote, "rev-parse", "--short", "feature"
    )


def test_existing_non_git_directory_rejected(tmp_path):
    dest = tmp_path / "cache" / "proj"
    dest.mkdir(parents=True)
    with pytest.raises(GitSyncError, match="n'est pas un dépôt git"):
        sync_repo("https://example.com/repo.git", dest)


def test_invalid_url_raises_gitsync_error(tmp_path):
    with pytest.raises(GitSyncError):
        sync_repo(str(tmp_path / "inexistant"), tmp_path / "cache" / "proj")
