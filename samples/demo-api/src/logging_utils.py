"""Fabrique centralisée de loggers (convention du projet)."""

from __future__ import annotations

import logging

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_configured = False


def _configure_once() -> None:
    global _configured
    if not _configured:
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
        _configured = True


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger configuré pour le module donné.

    Args:
        name: passer systématiquement ``__name__``.

    Returns:
        Un logger prêt à l'emploi, au format homogène du projet.
    """
    _configure_once()
    return logging.getLogger(name)
