"""Exceptions métier typées (convention du projet)."""


class DomainError(Exception):
    """Base de toutes les erreurs métier."""


class NotFoundError(DomainError):
    """Entité demandée introuvable."""


class ValidationError(DomainError):
    """Données d'entrée invalides."""
