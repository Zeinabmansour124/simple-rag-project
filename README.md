# AI Space — un assistant pour relire du code Java (projet T24)

## Pourquoi ce projet

Dans une équipe technique qui maintient un système T24, une bonne partie du temps part dans la relecture de code : comprendre ce qu'un collègue a écrit, repérer une erreur qui traîne, se souvenir de comment telle classe fonctionne. Ce projet est né de l'idée qu'un assistant local, capable de fouiller dans la documentation existante *et* de relire un extrait de code qu'on lui colle, pourrait faire gagner un peu de ce temps-là — sans dépendre d'un service cloud, et sans envoyer de code à l'extérieur.

C'est un chatbot qui tourne entièrement en local (Ollama + Mistral), avec un compte par utilisateur, et qui apprend au fil de l'eau : chaque correction qu'il propose vient enrichir sa propre base de connaissance.

## Ce qu'il sait faire

- **Répondre à des questions** sur du code Java déjà indexé — "que fait cette classe", "comment est géré tel cas" — en allant chercher les passages pertinents avant de répondre.
- **Relire un extrait de code** qu'on lui colle directement dans le chat, repérer un problème (même mineur), et proposer une correction.
- **Se souvenir de la conversation** — une deuxième question qui fait référence à la première est comprise normalement.
- **Distinguer les utilisateurs** — chacun a ses propres fichiers et sa propre mémoire, strictement privés, en plus d'une base commune partagée par toute l'équipe. Un fichier ajouté par un utilisateur n'est jamais visible ni utilisé pour répondre aux questions d'un autre utilisateur.
- **S'améliorer avec l'usage** — une correction validée est automatiquement ajoutée à la base personnelle de celui qui l'a demandée, pour que le contexte s'accumule au fil du temps.

## Comment c'est construit

Le projet repose sur quatre briques qui se répondent :

```
Question posée dans le chat
            │
            ▼
     Un petit routeur
   décide : c'est une question, ou du code à corriger ?
            │
    ┌───────┴────────┐
    ▼                 ▼
 Recherche         Un serveur MCP
 dans la doc       relit le code avec
 (ChromaDB)        un vrai parseur Java
    │              (javalang, pas juste
    │               une lecture de mots-clés)
    └───────┬────────┘
            ▼
      Mistral rédige
      la réponse finale
```

**La base de connaissance** est en deux parties : une base commune, partagée par toute l'équipe (pour l'instant alimentée par du code de démonstration, en attendant d'y mettre du vrai code T24), et une base personnelle par utilisateur, strictement privée, qui grandit avec ses propres fichiers et ses propres corrections. Au moment de répondre, le système interroge les deux bases et combine les résultats, mais la base personnelle d'un utilisateur n'est jamais accessible à un autre.

**Le serveur MCP** est ce qui distingue ce projet d'un simple RAG : plutôt que de laisser le modèle deviner la structure d'un code à partir de son texte brut, un vrai parseur Java (`javalang`) l'analyse d'abord — noms de méthodes, paramètres, exceptions — et ces faits vérifiés sont donnés au modèle avant qu'il ne rédige quoi que ce soit. Ça limite le risque qu'il invente des détails qui n'existent pas dans le code.

**Pour la correction**, le modèle est contraint de répondre dans un format JSON structuré (explication et code séparés dès le départ), et le code qu'il propose est re-vérifié syntaxiquement avant d'être sauvegardé — s'il n'est pas valide, il n'entre pas dans la base personnelle.

## Installer et lancer

Il faut Python 3.11+ et [Ollama](https://ollama.com) installé et lancé (`ollama serve`), avec les deux modèles suivants téléchargés :

```bash
ollama pull mistral:7b-instruct-q4_0
ollama pull nomic-embed-text
```

Ensuite, les dépendances Python :

```bash
pip install -r requirements.txt
```

Il reste à préparer deux fichiers de configuration avant le premier lancement :

- `config.yaml`, avec la liste des emails autorisés à créer un compte (`preauthorized.emails`)
- `.streamlit/secrets.toml`, avec une clé de session :
  ```toml
  [cookie]
  cookie_key = "une_cle_longue_et_aleatoire_a_toi"
  ```

Et enfin :

```bash
streamlit run simple-rag.py
```

L'application s'ouvre sur `http://localhost:8501`.

### Avec Docker

Une image Docker de l'application est disponible (`Dockerfile` à la racine du projet) :

```bash
docker build -t simple-rag-app .
docker run --rm -p 8501:8501 simple-rag-app
```

Ollama reste installé et lancé sur la machine hôte (pas conteneurisé), l'application y accède via `host.docker.internal`. La construction de l'image a été validée avec succès ; le fonctionnement complet en parallèle d'Ollama n'a pas pu être testé de bout en bout en conditions réelles, en raison d'une contrainte temporaire de RAM sur la machine de développement (8 Go au lieu de 16 Go, suite à une panne matérielle en cours de résolution).

## Ce qui compose le projet

```
simple-rag.py            → l'application principale
mcp-test.py                → le serveur MCP (l'outil d'analyse de code)
clientTest.py               → un petit script pour tester le serveur MCP seul
upload.py                    → le composant d'ajout de fichiers
auth_utils.py                 → lecture/écriture de la config d'authentification
config.yaml                    → comptes et liste blanche (à ne pas versionner)
test_code/                      → base de code commune
test_code_{utilisateur}/         → base personnelle de chacun (privée)
chroma_db_java*/                  → les bases vectorielles, persistantes sur disque
Dockerfile                          → construction de l'image de l'application
```

## Ce que le projet fait moins bien, pour l'instant

Je préfère le dire clairement plutôt que de le découvrir en démo :

**Le modèle est quantifié** (`q4_0`), pour tourner correctement sur une machine aux ressources limitées. Ça a un coût réel sur la qualité du raisonnement : sur des cas de correction complexes, il arrive que le modèle contourne un problème plutôt que de le résoudre vraiment, ou qu'il affirme qu'un code est correct alors qu'il ne l'est pas totalement. Un modèle plus lourd donnerait probablement de meilleurs résultats, au prix de plus de ressources machine.

**La base commune est provisoire.** En l'absence d'accès à du vrai code T24 au moment du développement, elle contient un projet Java public de gestion de comptes bancaires, choisi pour sa proximité thématique — à remplacer par du vrai contenu T24 dès que possible.

**La validation automatique ne porte que sur la syntaxe.** Le système garantit que le code corrigé est syntaxiquement valide, pas qu'il est logiquement juste. Une relecture humaine reste nécessaire avant d'intégrer une correction proposée.

**Base commune et base personnelle ne sont pas hiérarchisées.** Les deux sont interrogées et combinées à chaque question, sans priorité claire entre elles — un fichier personnel court peut parfois être éclipsé par un contenu plus riche de la base commune.

**Dockerisation non validée en conditions réelles**, comme précisé plus haut, en raison d'une contrainte matérielle temporaire.

## Et ensuite

Quelques pistes pour la suite, si le temps le permet :

- Valider la dockerisation complète une fois la RAM de la machine restaurée
- Remplacer la base commune par du vrai code T24
- Comparer les résultats avec un modèle non quantifié, pour mesurer précisément l'écart de qualité
- Introduire une vraie priorité entre base personnelle et base commune dans la recherche
