# Battle Data Collector - Mod World of Tanks

Mod pour World of Tanks qui collecte automatiquement les données de bataille pour alimenter un modèle d'IA de prédiction.

## Données Collectées

- **Noms des joueurs** (30 joueurs, 15 par équipe)
- **Points de spawn** (équipe 1 ou 2)
- **Nom de la map**
- **Statistiques des joueurs** (via API locale -> proxy Wargaming + Tomato):
  - Nombre de batailles
  - Taux de victoire
  - Dégâts moyens
  - Frags moyens
  - Spotting moyen

## Installation

### Méthode 1: Fichier .wotmod (Recommandé)

1. Téléchargez `mod_battle_data_collector_1.0.0.wotmod`
2. Copiez-le dans `<World_of_Tanks>/mods/<version>/`
   - Exemple: `C:\Games\World_of_Tanks_EU\mods\1.28.0.0\`
3. Configurez l'API locale + le mod (voir Configuration)

### Méthode 2: Installation manuelle

1. Copiez le dossier `res_mods/` dans `<World_of_Tanks>/res_mods/`
2. Configurez l'API locale + le mod (voir Configuration)

## Configuration

### 1. Configurer l'API locale (FastAPI)

Le mod n'appelle plus directement Wargaming/Tomato. Il appelle uniquement l'API locale dans le dossier `api/`.

1. Dans `api/.env`, configurez:
  - `WARGAMING_APP_ID=<votre Application ID>` (ou `WARGAMING_API_KEY`)
2. Lancez l'API:
  ```bash
  cd api
  uvicorn main:app --reload --port 8000
  ```

### 2. (Optionnel) Obtenir une clé API Wargaming

1. Créez un compte sur [Wargaming Developers](https://developers.wargaming.net/)
2. Créez une nouvelle application
3. Copiez votre `Application ID`

### 3. Configurer le mod (config.py)

Éditez directement:
```
res_mods/scripts/client/gui/mods/battle_data_collector/config.py
```

Principaux paramètres:
```python
API_BASE_URL = 'http://127.0.0.1:8000/api'
SERVER_REGION = 'eu'  # Options: 'eu', 'na', 'ru', 'asia'
COLLECT_PLAYER_STATS = True
```

## Utilisation

1. Lancez World of Tanks
2. Vérifiez dans `python.log` la ligne: `[BattleDataCollector] Mod chargé avec succès`
3. Jouez une bataille
4. Les données sont automatiquement exportées dans `<WoT>/battle_data/`

## Format des Données

Exemple de fichier JSON généré:

```json
{
  "timestamp": "2024-12-29T15:45:32.123456",
  "map": {
    "id": 15,
    "name": "Prokhorovka",
    "geometry_name": "15_komarin",
    "game_mode": "random"
  },
  "teams": {
    "spawn_1": [
      {
        "name": "Player1",
        "vehicle_id": 123456,
        "tank": "IS-7",
        "tank_tier": 10,
        "tank_type": "heavyTank",
        "clan": "ABC",
        "is_alive": true,
        "stats": {
          "battles": 15234,
          "wins": 8123,
          "win_rate": 53.32,
          "avg_damage": 2145.67,
          "avg_frags": 1.23,
          "avg_spotted": 0.87
        }
      }
    ],
    "spawn_2": [...]
  }
}
```

## Build

Pour créer le fichier `.wotmod`:

```bash
python build.py
```

## Dépannage

### Le mod ne se charge pas

- Vérifiez que le dossier est dans le bon chemin
- Consultez `<WoT>/python.log` pour les erreurs
- Vérifiez la version du mod correspond à la version du jeu

### Les statistiques ne sont pas récupérées

- Vérifiez votre clé API dans `config.py`
- Vérifiez votre connexion Internet
- Consultez `python.log` pour les erreurs API

### Aucun fichier JSON n'est créé

- Vérifiez les permissions d'écriture dans le dossier WoT
- Le dossier `battle_data/` devrait être créé automatiquement

## Structure du Projet

```
mod_wot/
├── meta.xml                          # Métadonnées du mod
├── build.py                          # Script de build
├── README.md                         # Ce fichier
└── res_mods/
    └── scripts/
        └── client/
            └── gui/
                └── mods/
                    └── mod_battle_data_collector/
                        ├── __init__.py              # Point d'entrée
                        ├── config.py                # Configuration
                        ├── battle_data_collector.py # Collecteur principal
                        ├── stats_fetcher.py         # Récupération stats API
                        └── data_exporter.py         # Export JSON
```

## Licence

Ce mod est fourni tel quel pour usage personnel.

## Support

Pour toute question ou problème, consultez les logs dans `<WoT>/python.log`.
