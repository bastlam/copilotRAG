"""Service métier utilisateurs : illustre les conventions du projet."""

from __future__ import annotations

from .errors import NotFoundError, ValidationError
from .logging_utils import get_logger
from .user_repository import User, UserRepository

_logger = get_logger(__name__)


class UserService:
    """Cas d'usage liés aux utilisateurs.

    Args:
        repository: accès aux données, injecté (pattern repository).
    """

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def get_user(self, user_id: int) -> User:
        """Récupère un utilisateur ou lève NotFoundError.

        Args:
            user_id: identifiant de l'utilisateur.

        Returns:
            L'utilisateur correspondant.

        Raises:
            NotFoundError: si aucun utilisateur n'a cet identifiant.
        """
        user = self._repository.get_by_id(user_id)
        if user is None:
            _logger.warning("Utilisateur %s introuvable", user_id)
            raise NotFoundError(f"Utilisateur {user_id} introuvable")
        return user

    def register_user(self, user_id: int, email: str, display_name: str) -> User:
        """Enregistre un nouvel utilisateur après validation.

        Raises:
            ValidationError: si l'email est vide ou invalide.
        """
        if "@" not in email:
            raise ValidationError(f"Email invalide : {email!r}")
        user = self._repository.save(User(id=user_id, email=email, display_name=display_name))
        _logger.info("Utilisateur %s enregistré", user.id)
        return user
