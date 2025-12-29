# Gestion de la Configuration et des Secrets

## Fichiers de Configuration

Ce projet utilise plusieurs méthodes pour gérer la configuration :

### 1. Fichier `.env` (Recommandé)

Le fichier `.env` contient vos informations sensibles (clé API) et n'est **jamais** commité dans Git.

**Avantages :**
- ✅ Sécurisé : automatiquement ignoré par Git
- ✅ Facile à modifier sans toucher au code
- ✅ Séparation claire entre code et configuration
- ✅ Pratique pour différents environnements (dev/prod)

**Utilisation :**
```bash
# 1. Copier le fichier exemple
copy .env.example .env

# 2. Éditer .env avec vos valeurs
notepad .env
```

### 2. Fichier `config.py`

Le fichier `config.py` charge automatiquement les valeurs depuis `.env` si disponible, sinon utilise des valeurs par défaut.

**Hiérarchie de chargement :**
1. Variables d'environnement (`.env`)
2. Valeurs par défaut dans `config.py`

## Structure des Fichiers

```
mod_wot/
├── .env                    # ⚠️ VOTRE configuration (ignoré par Git)
├── .env.example            # ✅ Template (commité dans Git)
└── res_mods/
    └── .../
        ├── config.py       # Charge depuis .env
        └── env_loader.py   # Module de chargement
```

## Variables Disponibles

| Variable | Type | Défaut | Description |
|----------|------|--------|-------------|
| `INTERNAL_API_BASE_URL` | string | `http://127.0.0.1:8000/api` | Base URL de l'API locale (proxy) |
| `WARGAMING_API_KEY` | string | `YOUR_API_KEY_HERE` | (Legacy) La clé Wargaming se configure désormais côté `api/.env` |
| `SERVER_REGION` | string | `eu` | Région du serveur (eu/na/ru/asia) |
| `COLLECT_PLAYER_STATS` | boolean | `true` | Activer collecte de stats |
| `API_TIMEOUT` | integer | `5` | Timeout API en secondes |
| `OUTPUT_DIR` | string | `battle_data` | Dossier de sortie |
| `DEBUG_MODE` | boolean | `false` | Mode debug |

## Exemple de `.env`

```env
# API locale (FastAPI)
INTERNAL_API_BASE_URL=http://127.0.0.1:8000/api

# Configuration serveur
SERVER_REGION=eu

# Options
COLLECT_PLAYER_STATS=true
API_TIMEOUT=5
OUTPUT_DIR=battle_data
DEBUG_MODE=false
```

## Sécurité

### ⚠️ NE JAMAIS :
- ❌ Commiter le fichier `.env`
- ❌ Partager votre clé API
- ❌ Publier des screenshots contenant `.env`

### ✅ TOUJOURS :
- ✅ Utiliser `.env.example` comme template
- ✅ Vérifier que `.env` est dans `.gitignore`
- ✅ Générer une nouvelle clé si compromise

## Dépannage

### Le mod ne trouve pas `.env`

Le module `env_loader.py` remonte automatiquement l'arborescence pour trouver `.env`. Assurez-vous que :
1. Le fichier `.env` est à la racine du projet `mod_wot/`
2. Le fichier n'a pas d'extension cachée (`.env.txt` par exemple)

### Les valeurs ne sont pas chargées

Vérifiez dans `python.log` :
```
[BattleDataCollector] Variables d'environnement chargées depuis: <chemin>
```

Si vous voyez :
```
[BattleDataCollector] Fichier .env non trouvé, utilisation des valeurs par défaut
```

Alors le fichier `.env` n'a pas été trouvé.

### Valeurs booléennes

Les valeurs suivantes sont considérées comme `true` :
- `true`, `True`, `TRUE`
- `1`
- `yes`, `Yes`, `YES`
- `on`, `On`, `ON`

Toute autre valeur = `false`

## Migration depuis l'ancienne configuration

Si vous utilisiez directement `config.py` :

1. Créez un fichier `.env`
2. Copiez vos valeurs :
   ```python
   # Ancien config.py
   WARGAMING_API_KEY = "ma_clé"
   ```
   
   Devient dans `.env` :
   ```env
   WARGAMING_API_KEY=ma_clé
   ```

3. Le `config.py` chargera automatiquement depuis `.env`

## Pour les Développeurs

Le module `env_loader.py` est compatible Python 2.7 (pas de dépendance externe).

**Fonctions disponibles :**
```python
from env_loader import load_env, get_env, get_env_bool, get_env_int

# Charger .env
load_env()

# Récupérer une variable
api_key = get_env('WARGAMING_API_KEY', 'default')

# Récupérer un booléen
debug = get_env_bool('DEBUG_MODE', False)

# Récupérer un entier
timeout = get_env_int('API_TIMEOUT', 5)
```
