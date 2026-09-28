# Cooking Papa

Un carnet de recettes familial où l'on ne se contente pas de lire un plat : on
peut **demander qu'il soit préparé**. La demande est enregistrée, puis envoyée
en message privé Discord à la personne aux fourneaux, avec la liste des
ingrédients et une note éventuelle.

FastAPI, SQLite et HTMX, rendu côté serveur, un seul conteneur.

## Fonctionnalités

- Recettes avec ingrédients, quantités et photo
- Recherche, et autocomplétion sur les ingrédients déjà connus
- **Demande de préparation** : enregistrée en base, puis poussée en MP Discord
  (facultatif — sans Discord, la demande est simplement conservée)
- Photos normalisées à l'envoi : recadrage carré centré, 1024 px maximum, JPEG
  recompressé — un téléphone peut envoyer n'importe quoi sans gonfler le disque
- Interface sombre/claire, pensée pour le téléphone

## Choix techniques

- **Pas d'API publique** : `docs_url`, `redoc_url` et `openapi_url` sont
  désactivés. L'application ne sert que ses propres pages.
- **CSRF** : un jeton signé est posé en cookie par un middleware et vérifié sur
  chaque formulaire mutant.
- **En-têtes de sécurité** appliqués globalement (voir `app/security.py`).
- **Téléversements filtrés** par type MIME et taille (20 Mo par défaut).

## Mise en route

```bash
cp .env.example .env
python3 -c "import secrets; print('CSRF_SECRET=' + secrets.token_urlsafe(32))"  # à coller dans .env
docker compose up -d --build
```

L'application écoute sur http://127.0.0.1:8090.

Derrière un reverse-proxy ou un tunnel, mieux vaut ne rien publier sur l'hôte et
brancher le conteneur sur un réseau partagé : copier
`docker-compose.override.yml.example` en `docker-compose.override.yml` et
l'adapter. `ports: !reset []` y efface le port du compose versionné.

## Configuration

| Variable | Défaut | Rôle |
|---|---|---|
| `CSRF_SECRET` | — (obligatoire) | Signature des jetons CSRF |
| `DISCORD_ENABLED` | `false` | Active l'envoi du MP |
| `DISCORD_HOST` | `http://host.docker.internal:5000` | Bot exposant `POST /dm/send` |
| `DISCORD_TARGET_USER` | — | Destinataire du MP (identifiant ou pseudo) |
| `MAX_UPLOAD_MB` | `20` | Taille maximale d'une photo |
| `IMAGE_SIZE` | `1024` | Côté du carré après recadrage |
| `DATABASE_URL` | `sqlite:////app/data/cooking.db` | Base SQLite |

Le bot attendu est une petite API qui accepte `{"user": ..., "message": ...}`
sur `/dm/send` ; n'importe quelle implémentation fait l'affaire.

## Ce qui n'est pas versionné

`.env`, la base (`data/`), les photos envoyées (`uploads/`) et l'override local.
