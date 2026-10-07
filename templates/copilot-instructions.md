# Instructions Copilot — Base RAG `copilot-rag`

> Modèle à destination des projets qui exploitent la base RAG locale
> CopilotRAG. À copier dans `.github/copilot-instructions.md` de chaque
> projet consommateur.

## Règle impérative : exploiter la base RAG

Ce projet est outillé du serveur MCP **`copilot-rag`**, qui indexe le code et
la documentation des projets de référence de l'organisation. Son utilisation
est **obligatoire** dans ce workspace :

1. **AVANT d'écrire du nouveau code** (classe, fonction, endpoint, script) :
   appeler `search_code` avec une description du besoin. Si des implémentations
   proches existent dans les projets indexés, **les réutiliser ou s'en inspirer**
   au lieu d'en inventer de nouvelles.
2. **AVANT d'appliquer une convention** (nommage, logging, gestion des erreurs,
   structure de projet, configuration) : appeler `search_documentation` pour
   retrouver les guides et README indexés.
3. **APRÈS avoir écrit du code** : appeler `find_similar_code` avec l'extrait
   produit pour détecter les doublons ; si un code quasi identique existe déjà,
   proposer une factorisation.
4. En cas de doute sur le contenu de la base : `list_projects` et `index_stats`
   donnent les projets indexés et leurs volumes — vérifier avant de conclure
   que « rien n'existe ».

Alignement attendu : le code généré doit respecter les patterns trouvés
(nommage, structure, gestion des erreurs, logging). Si la recherche ne retourne
rien de pertinent, le **dire explicitement** dans la réponse avant de proposer
une implémentation nouvelle.

Si le serveur `copilot-rag` est indisponible (outils introuvables ou en erreur),
le signaler à l'utilisateur et **ne pas générer de code « à l'aveugle »** tant
que la base n'est pas de nouveau accessible. L'utilisateur vérifiera la
configuration MCP (`.vscode/mcp.json` du workspace ou configuration MCP
utilisateur) et l'état de la base côté dépôt CopilotRAG.

## Outils disponibles

| Outil | Quand l'utiliser |
|---|---|
| `search_code` | Avant d'écrire une classe, fonction, endpoint ou script |
| `find_similar_code` | Après avoir écrit du code, pour détecter les doublons |
| `search_documentation` | Avant d'appliquer une convention (nommage, logging, erreurs, structure) |
| `list_projects` | Pour savoir quels projets de référence sont indexés |
| `index_stats` | Pour évaluer le volume indexé par projet et par langage |

## Périmètre et limites de la base

- Le contenu interrogeable dépend des projets déclarés dans la configuration
  du dépôt CopilotRAG : les langages, frameworks et conventions couverts sont
  ceux des projets indexés. **Adapter** les patterns trouvés au contexte du
  présent projet, ne pas les copier aveuglément.
- La base est un référentiel **en lecture seule** : ne jamais tenter de
  modifier les projets indexés via ces outils.
- Fraîcheur : la base reflète la dernière ingestion. Si une implémentation
  récente semble manquer, le signaler à l'utilisateur plutôt que de la
  réinventer.
