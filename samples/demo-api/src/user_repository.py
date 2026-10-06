"""Accès aux données utilisateurs via le pattern repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class User:
    id: int
    email: str
    display_name: str


class UserRepository(Protocol):
    """Contrat d'accès aux utilisateurs (injecté dans les services)."""

    def get_by_id(self, user_id: int) -> User | None: ...

    def save(self, user: User) -> User: ...


class InMemoryUserRepository:
    """Implémentation de démonstration en mémoire."""

    def __init__(self) -> None:
        self._users: dict[int, User] = {}

    def get_by_id(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    def save(self, user: User) -> User:
        self._users[user.id] = user
        return user
