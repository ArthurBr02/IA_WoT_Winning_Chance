# API Python (FastAPI) — requêtes HTTP

## Installation
Dans le dossier `api/` :

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

## Configuration
- Copie/édite `.env` (un exemple est fourni dans `.env.example`).
- Les routes et clés se configurent via variables d’environnement.

## Lancer le serveur
```bash
uvicorn main:app --reload --port 8000
```

Puis:
- Santé: `GET http://127.0.0.1:8000${API_PREFIX}${ROUTE_HEALTH}`

## Routes dédiées (utilisées par le mod WoT)
Ces routes existent pour que **chaque appel externe du mod** passe par l'API.

- Wargaming (résolution account_id):
  - `GET http://127.0.0.1:8000/api/wg/account/list?search=<nick1,nick2>&type=exact&limit=100&region=eu`
  - Requiert `WARGAMING_APP_ID` dans `api/.env`

- Tomato.gg (stats overall):
  - `GET http://127.0.0.1:8000/api/tomato/player/overall/<server>/<account_id>`
  - Exemple: `.../overall/eu/123456789`

### Auth
Pas d'authentification interne: l'API est prévue pour être utilisée localement.
