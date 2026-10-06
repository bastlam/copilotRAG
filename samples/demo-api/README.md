# demo-api — Conventions du projet

Projet d'exemple utilisé pour démontrer la base RAG. Ces conventions doivent être
suivies par tout nouveau code.

## Structure

- `src/` : code métier uniquement, un module par domaine.
- Pas de logique métier dans les points d'entrée (controllers / main).

## Nommage

- Modules et fonctions : `snake_case`.
- Classes : `PascalCase`.
- Constantes : `MAJUSCULES_SNAKE`.

## Patterns imposés

- **Accès aux données** : toujours via un *repository* (protocole `UserRepository`),
  jamais d'accès direct au stockage depuis un service.
- **Logging** : toujours via `logging_utils.get_logger(__name__)`,
  jamais de `print` ni de logger construit à la main.
- **Erreurs** : lever des exceptions métier typées (`NotFoundError`, `ValidationError`),
  jamais de `Exception` générique.
- **Docstrings** : style Google (`Args:`, `Returns:`, `Raises:`).
