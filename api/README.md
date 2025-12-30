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

Variables utiles (Tomato):
- `TOMATO_API_BASE_URL` (défaut: `https://api.tomato.gg/api`)
- `TOMATO_CACHE_TTL_SECONDS` (défaut: `86400`) — cache success 24h par joueur
- `TOMATO_CACHE_ERROR_TTL_SECONDS` (défaut: `3600`) — cache erreur (évite de spammer en cas de panne)
- `TOMATO_CACHE_FILE` (défaut: `.cache/tomato_cache.json`) — cache persistant (créé automatiquement)

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

- Prédiction — booléen "victoire utilisateur":
  - `GET http://127.0.0.1:8000/api/predict/win?user=MonPseudo&user_spawn=1&map_id=1&spawn_1=a,b,c&spawn_2=d,e,f&region=eu`
  - `POST http://127.0.0.1:8000/api/predict/win?region=eu` avec body JSON:

  Réponse (GET/POST):
  ```json
  {
    "predicted": true,
    "prob_user": 63.4
  }
  ```
    - `{ "user": "MonPseudo", "user_spawn": 2, "map_id": 1, "spawn_1": ["a"], "spawn_2": ["b"] }`
  - Si `spawn_1/spawn_2` ne sont pas fournis, l'API peut fallback sur `pseudos` (30 pseudos) et découper 15/15.

- Prédiction — features (objet complet pour IA):
  - `GET http://127.0.0.1:8000/api/predict/features?user=MonPseudo&user_spawn=1&map_id=1&spawn_1=a,b,c&spawn_2=d,e,f&region=eu`
  - `POST http://127.0.0.1:8000/api/predict/features?region=eu` avec body JSON:
    - `{ "user": "MonPseudo", "user_spawn": 2, "map_id": 1, "spawn_1": ["a"], "spawn_2": ["b"] }`
  - La réponse contient `players` (par pseudo) avec `account_id` + `stats` (incluant `tomato_overall` et les champs `overallWN8`, `winrate`, `dpg`, etc.).

## Modèle PyTorch (ml/)
- L'API charge les artefacts d'inférence depuis `../ml/` par défaut:
  - `ml/wot_model_map.pth` (state_dict)
  - `ml/scaler.pkl` (StandardScaler)
  - `ml/map_index.pkl` (mapping map_id -> index embedding)
- Variables d'env optionnelles: `MODEL_PATH`, `SCALER_PATH`, `MAP_INDEX_PATH`.

### Auth
Pas d'authentification interne: l'API est prévue pour être utilisée localement.
