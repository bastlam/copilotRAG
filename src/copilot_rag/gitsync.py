"""Synchronisation locale de dépôts git (clone / mise à jour shallow).

Les dépôts déclarés avec la clé `git:` dans projects.yaml sont clonés dans
`repos_cache/<nom-du-projet>` puis mis à jour à chaque ingestion
(fetch + reset --hard, --depth 1 pour limiter l'espace disque).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

GIT_DEPTH = "1"  # clone shallow : seul le dernier commit est rapatrié


class GitSyncError(RuntimeError):
    """Échec de synchronisation d'un dépôt git (clone ou fetch)."""


def _run_git(args: list[str], cwd: Path | None = None) -> str:
    """Exécute une commande git. Lève GitSyncError en cas d'échec, retourne stdout."""
    cmd = ["git", *args]
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        raise GitSyncError(f"{' '.join(cmd)} : {detail}")
    return proc.stdout.strip()


def sync_repo(url: str, dest: Path, ref: str | None = None) -> str:
    """Clone ou met à jour un dépôt git dans `dest` (shallow).

    Args:
        url: URL du dépôt (https, ssh ou chemin local acceptés par git).
        dest: dossier de destination (cache local).
        ref: branche, tag ou commit à synchroniser (défaut : branche principale).

    Returns:
        Le hash court du commit synchronisé.

    Raises:
        GitSyncError: si git est absent du PATH, si `dest` existe sans être un
            dépôt git, ou si une commande git échoue.
    """
    if shutil.which("git") is None:
        raise GitSyncError("git introuvable sur le PATH")

    if (dest / ".git").is_dir():
        # Mise à jour : fetch du ref demandé (ou de la branche par défaut) + reset
        fetch_args = ["fetch", "--depth", GIT_DEPTH, "origin"]
        if ref:
            fetch_args.append(ref)
        _run_git(fetch_args, cwd=dest)
        _run_git(["reset", "--hard", "FETCH_HEAD"], cwd=dest)
    else:
        if dest.exists():
            raise GitSyncError(
                f"{dest} existe mais n'est pas un dépôt git ; supprimez-le."
            )
        dest.parent.mkdir(parents=True, exist_ok=True)
        clone_args = ["clone", "--depth", GIT_DEPTH]
        if ref:
            clone_args += ["--branch", ref]
        clone_args += [url, str(dest)]
        _run_git(clone_args)

    return _run_git(["rev-parse", "--short", "HEAD"], cwd=dest)
