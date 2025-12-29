# Gestion de la Configuration

## Fichiers de Configuration

La configuration du mod est définie directement dans le code (pas de fichier `.env`).

### Fichier `config.py` (mod)

Éditez:
```
res_mods/scripts/client/gui/mods/battle_data_collector/config.py
```

## Structure des Fichiers

```
mod_wot/
└── res_mods/
    └── scripts/client/gui/mods/battle_data_collector/
        ├── config.py
        └── env_loader.py
```

## Variables Disponibles

| Variable | Type | Défaut | Description |
|----------|------|--------|-------------|
| `API_BASE_URL` | string | `http://127.0.0.1:8000/api` | Base URL de l'API locale (proxy) |
| `SERVER_REGION` | string | `eu` | Région du serveur (eu/na/ru/asia) |
| `COLLECT_PLAYER_STATS` | boolean | `true` | Activer collecte de stats |
| `API_TIMEOUT` | integer | `5` | Timeout API en secondes |
| `OUTPUT_DIR` | string | `battle_data` | Dossier de sortie |
| `DEBUG_MODE` | boolean | `false` | Mode debug |

## Sécurité

### ⚠️ NE JAMAIS :
- ❌ Partager votre clé API
- ❌ Publier des screenshots contenant des secrets

### ✅ TOUJOURS :
- ✅ Configurer la clé Wargaming côté serveur (`api/.env`)
- ✅ Générer une nouvelle clé si compromise

## Dépannage

### La configuration ne semble pas prise en compte

Si vous modifiez `config.py`, assurez-vous de réinstaller le mod (ou rebuild le `.wotmod`) avant de relancer WoT.

### Valeurs booléennes

Les valeurs suivantes sont considérées comme `true` :
- `true`, `True`, `TRUE`
- `1`
- `yes`, `Yes`, `YES`
- `on`, `On`, `ON`

Toute autre valeur = `false`

## Pour les Développeurs

Le module `env_loader.py` reste utilisé pour des utilitaires (ex: détection du dossier WoT),
mais le mod ne charge plus de fichier `.env`.
