# Guide de Dépannage - Battle Data Collector

## ❌ Le mod ne se charge pas (rien dans python.log)

### Vérification 1: Emplacement du fichier .wotmod

Le fichier `.wotmod` doit être dans le dossier `mods\<VERSION>\` et **PAS** dans `mods\` ou `res_mods\`.

**✅ Correct:**
```
C:\Games\World_of_Tanks_EU\mods\2.1.0.2\mod_battle_data_collector_1.0.0.wotmod
```

**❌ Incorrect:**
```
C:\Games\World_of_Tanks_EU\mods\mod_battle_data_collector_1.0.0.wotmod
C:\Games\World_of_Tanks_EU\res_mods\2.1.0.2\mod_battle_data_collector_1.0.0.wotmod
```

### Vérification 2: Version du jeu

La version dans le chemin doit correspondre à votre version de WoT.

**Comment trouver votre version:**
1. Lancez World of Tanks
2. En bas à gauche de l'écran de connexion, vous verrez: `v2.1.0.2` (exemple)
3. Utilisez ce numéro pour le dossier

### Vérification 3: Rebuild du mod

Reconstruisez le fichier `.wotmod` depuis le projet:

```bash
cd u:\Projets\Git\IA_WoT_Winning_Chance\mod_wot
python build.py
```

Cela devrait afficher:
```
============================================================
BUILD MOD WORLD OF TANKS
============================================================
Nom: mod_battle_data_collector
Version: 1.0.0
...
✅ BUILD RÉUSSI!
```

### Vérification 4: Structure du .wotmod

Vérifiez le contenu du fichier `.wotmod` (c'est un fichier ZIP):

1. Renommez temporairement `.wotmod` en `.zip`
2. Ouvrez avec 7-Zip ou WinRAR
3. Vérifiez la structure:

```
mod_battle_data_collector_1.0.0.zip
├── meta.xml
└── res/
    └── scripts/
        └── client/
            └── gui/
                └── mods/
                    └── mod_battle_data_collector/
                        ├── __init__.py
                        ├── config.py
                        ├── env_loader.py
                        ├── battle_data_collector.py
                        ├── stats_fetcher.py
                        └── data_exporter.py
```

**Important:** Les scripts doivent être dans `res/scripts/` et **PAS** `res_mods/scripts/`

### Vérification 5: Fichier python.log

Emplacement du fichier log:
```
C:\Games\World_of_Tanks_EU\python.log
```

**Recherchez:**
- `[BattleDataCollector]` - Messages du mod
- `Error` ou `Exception` - Erreurs Python
- `mod_battle_data_collector` - Mentions du mod

**Si le fichier est vide ou n'existe pas:**
- Le jeu n'a pas été lancé depuis l'installation
- Le mod n'est pas chargé du tout

---

## ⚠️ Le mod se charge mais ne collecte pas de données

### Vérification 1: API locale démarrée

Le mod appelle uniquement l'API locale (proxy). Assurez-vous que :
- l'API locale tourne (uvicorn)
- la clé Wargaming est configurée côté serveur (`api/.env`)

### Vérification 2: Logs dans python.log

Cherchez ces messages:
```
[BattleDataCollector] Mod chargé avec succès - v1.0.0
[BattleDataCollector] Collecteur initialisé
```

### Vérification 3: Dossier de sortie

Le dossier `battle_data` devrait être créé automatiquement:
```
C:\Games\World_of_Tanks_EU\battle_data\
```

**Si le dossier n'existe pas:**
- Vérifiez les permissions d'écriture
- Consultez python.log pour les erreurs

---

## 🔧 Erreurs Courantes

### Erreur: "compression not supported"

**Message complet:**
```
[PY_DEBUG] Mod package 'mod_battle_data_collector_1.0.0.wotmod' load error: compression not supported
```

**Cause:** Le fichier `.wotmod` a été créé avec compression (ZIP_DEFLATED) mais WoT n'accepte que les archives non compressées (ZIP_STORED)

**Solution:**
1. Le script `build.py` a été corrigé pour utiliser `ZIP_STORED`
2. Supprimez l'ancien `.wotmod`:
   ```bash
   del mod_battle_data_collector_1.0.0.wotmod
   ```
3. Rebuild avec le script corrigé:
   ```bash
   python build.py
   ```
4. Réinstallez le nouveau fichier:
   ```bash
   copy mod_battle_data_collector_1.0.0.wotmod "C:\Games\World_of_Tanks_EU\mods\2.1.0.5208\"
   ```
5. Redémarrez WoT

**Vérification:** Le nouveau `.wotmod` sera plus gros (pas de compression) mais fonctionnera correctement.

### Erreur: "ImportError: No module named battle_data_collector"

**Cause:** Structure incorrecte du .wotmod

**Solution:**
1. Supprimez l'ancien `.wotmod`
2. Relancez `python build.py`
3. Vérifiez la structure avec 7-Zip

### Erreur: "API timeout" ou "Connection error"

**Cause:** Problème de connexion à l'API locale (proxy) ou à l'upstream

**Solution:**
1. Vérifiez que l'API locale tourne (uvicorn)
2. Vérifiez `API_BASE_URL` dans `res_mods/scripts/client/gui/mods/battle_data_collector/config.py`
3. Vérifiez `WARGAMING_APP_ID` dans `api/.env`
4. Augmentez `API_TIMEOUT` dans `config.py` si nécessaire

### Aucun fichier JSON n'est créé

**Causes possibles:**
1. Le mod ne détecte pas le début de bataille
2. Permissions d'écriture insuffisantes
3. Erreur dans le code

**Diagnostic:**
1. Consultez `python.log` après une bataille
2. Cherchez: `[BattleDataCollector] Début de collecte des données`
3. Cherchez: `[BattleDataCollector] Données exportées:`

---

## 🧪 Test Manuel

### Test 1: Installation Basique

```bash
# 1. Rebuild
cd u:\Projets\Git\IA_WoT_Winning_Chance\mod_wot
python build.py

# 2. Copier
copy mod_battle_data_collector_1.0.0.wotmod "C:\Games\World_of_Tanks_EU\mods\2.1.0.2\"

# 3. Configurer (si besoin)
# Editez: res_mods/scripts/client/gui/mods/battle_data_collector/config.py

# (nouvelle archi) Lancez l'API locale (dossier api/) avant WoT

# 4. Lancer WoT et vérifier python.log
```

### Test 2: Vérifier le Chargement

1. Lancez WoT
2. Ouvrez `C:\Games\World_of_Tanks_EU\python.log`
3. Cherchez (Ctrl+F): `BattleDataCollector`

**Attendu:**
```
[BattleDataCollector] Mod chargé avec succès - v1.0.0
[BattleDataCollector] Variables d'environnement chargées depuis: ...
[BattleDataCollector] Collecteur initialisé
```

### Test 3: Tester la Collecte

1. Lancez une bataille (Training Room recommandé)
2. Attendez le chargement complet
3. Après la bataille, vérifiez:
   - `C:\Games\World_of_Tanks_EU\battle_data\`
   - Devrait contenir: `battle_<map>_<timestamp>.json`

---

## 📞 Support

### Informations à fournir en cas de problème

1. **Version de WoT:** (ex: 2.1.0.2)
2. **Contenu de python.log:** (dernières 50 lignes)
3. **Structure du .wotmod:** (capture d'écran avec 7-Zip)
4. **Emplacement du .wotmod:** (chemin complet)
5. **Contenu de .env:** (SANS la clé API!)

### Checklist de Dépannage

- [ ] Le fichier `.wotmod` est dans `mods\<VERSION>\`
- [ ] La version correspond à celle du jeu
- [ ] Le fichier `.env` existe et contient la clé API
- [ ] Le fichier `.wotmod` a la bonne structure (vérifié avec 7-Zip)
- [ ] `python.log` contient des messages du mod
- [ ] Le dossier `battle_data` existe
- [ ] Les permissions d'écriture sont OK

---

## 🔄 Réinstallation Complète

Si rien ne fonctionne, réinstallez complètement:

```bash
# 1. Supprimer l'ancien mod
del "C:\Games\World_of_Tanks_EU\mods\2.1.0.2\mod_battle_data_collector_*.wotmod"

# 2. Nettoyer
cd u:\Projets\Git\IA_WoT_Winning_Chance\mod_wot
del mod_battle_data_collector_*.wotmod

# 3. Rebuild
python build.py

# 4. Copier
copy mod_battle_data_collector_1.0.0.wotmod "C:\Games\World_of_Tanks_EU\mods\2.1.0.2\"

# 5. Configurer le mod (si besoin)
# Editez: res_mods/scripts/client/gui/mods/battle_data_collector/config.py

# 6. Redémarrer WoT complètement
```

---

## 📝 Logs Utiles

### Activer le mode debug

Dans `res_mods/scripts/client/gui/mods/battle_data_collector/config.py`:
```python
DEBUG_MODE = True
```

Cela affichera plus d'informations dans `python.log`.

### Emplacement des logs

- **python.log:** `C:\Games\World_of_Tanks_EU\python.log`
- **Données collectées:** `C:\Games\World_of_Tanks_EU\battle_data\`
- **Configuration du mod:** `res_mods/scripts/client/gui/mods/battle_data_collector/config.py`
