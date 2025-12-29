# Guide d'Installation Rapide - Battle Data Collector

## Prérequis

- World of Tanks installé
- API locale (dossier `api/`) lancée sur votre machine
- Python 2.7 (déjà inclus dans WoT)

## Installation en 5 Minutes

### Étape 1: Configurer et lancer l'API locale (2 min)

1. Obtenez un **Application ID** Wargaming sur https://developers.wargaming.net/
2. Dans `api/.env`, configurez:
   ```env
   WARGAMING_APP_ID=votre_application_id_ici
   ```
3. Lancez l'API:
   ```bash
   cd api
   uvicorn main:app --reload --port 8000
   ```

### Étape 2: Installer le Mod (1 min)

**Option A: Installation automatique (recommandé)**

1. Copiez le dossier `res_mods/` dans votre installation WoT
   ```
   Copier: res_mods/
   Vers: C:\Games\World_of_Tanks_EU\res_mods\
   ```

**Option B: Build manuel**

1. Ouvrez un terminal dans le dossier du mod
2. Exécutez:
   ```bash
   python build.py
   ```
3. Copiez le fichier `.wotmod` généré dans:
   ```
   C:\Games\World_of_Tanks_EU\mods\<version>\
   ```

### Étape 3: Configuration (1 min)

**Option A: Fichier .env (Recommandé - Plus sécurisé)**

1. Copiez le fichier exemple:
   ```bash
   copy .env.example .env
   ```

2. Éditez le fichier `.env`:
   ```env
   INTERNAL_API_BASE_URL=http://127.0.0.1:8000/api
   # si vous avez configuré INTERNAL_API_KEY côté API:
   INTERNAL_API_KEY=
   SERVER_REGION=eu
   COLLECT_PLAYER_STATS=true
   ```

3. Sauvegardez (le fichier `.env` est ignoré par Git pour votre sécurité)

**Option B: Édition directe de config.py**

1. Ouvrez le fichier:
   ```
   res_mods/scripts/client/gui/mods/mod_battle_data_collector/config.py
   ```

2. Les valeurs par défaut seront utilisées si `.env` n'existe pas

### Étape 4: Test (1 min)

1. Lancez World of Tanks
2. Ouvrez le fichier de log:
   ```
   <WoT>\python.log
   ```
3. Cherchez la ligne:
   ```
   [BattleDataCollector] Mod chargé avec succès - v1.0.0
   ```

4. Jouez une bataille (Random, Training, etc.)

5. Vérifiez le dossier:
   ```
   <WoT>\battle_data\
   ```

Vous devriez voir un fichier JSON du type:
```
battle_Prokhorovka_20241229_154532.json
```

## Vérification

Ouvrez le fichier JSON et vérifiez qu'il contient:

- ✅ Timestamp
- ✅ Informations de la map
- ✅ 30 joueurs (15 par équipe)
- ✅ Statistiques de chaque joueur

## Dépannage Rapide

| Problème | Solution |
|----------|----------|
| Mod ne se charge pas | Vérifiez le chemin d'installation |
| Pas de stats | Vérifiez que l'API locale tourne et que `INTERNAL_API_BASE_URL` est correct |
| Fichier JSON vide | Consultez `python.log` pour les erreurs |
| Erreur API | Vérifiez la config `api/.env` (WARGAMING_APP_ID) |

## Support

Pour plus de détails, consultez le fichier `README.md`.

Pour les logs détaillés:
```
<WoT>\python.log
```

## Structure des Données

Exemple de sortie:

```json
{
  "timestamp": "2024-12-29T15:45:32",
  "map": {
    "name": "Prokhorovka",
    "id": 15
  },
  "teams": {
    "spawn_1": [
      {
        "name": "Player1",
        "tank": "IS-7",
        "stats": {
          "battles": 15234,
          "win_rate": 53.32,
          "avg_damage": 2145.67
        }
      }
    ],
    "spawn_2": [...]
  }
}
```

## Prochaines Étapes

Une fois les données collectées, vous pouvez:

1. Analyser les fichiers JSON avec Python/Pandas
2. Entraîner un modèle d'IA
3. Prédire les chances de victoire

Bon jeu ! 🎮
