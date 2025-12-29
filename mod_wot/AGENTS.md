# Projet: Mod World of Tanks - Collecteur de Données de Bataille

## Description
Mod WoT pour collecter les informations de bataille (joueurs, spawn, map) afin d'alimenter un modèle d'IA de prédiction des chances de victoire.

## Objectif Principal
Créer un mod qui extrait automatiquement les données suivantes au début de chaque bataille:
- **Noms des joueurs** : Liste complète des 30 joueurs (15 par équipe)
- **Points de spawn** : Équipe 1 ou 2 pour chaque joueur
- **Map** : Nom de la carte jouée

## Technologies
- **Langage** : Python 2.7 (compatible avec le moteur BigWorld de WoT)
- **Moteur** : BigWorld Engine
- **Format de sortie** : JSON (pour intégration avec le modèle IA)

## État du Projet
- [x] Phase 1: Configuration et structure du mod
- [x] Phase 2: Récupération des données de bataille
- [x] Phase 3: Export des données
- [x] Phase 4: Intégration API Wargaming pour les stats
- [ ] Phase 5: Tests et validation en jeu

## Fichiers Créés
- `meta.xml` - Métadonnées du mod
- `build.py` - Script de build
- `README.md` - Documentation complète
- `INSTALLATION.md` - Guide d'installation rapide
- `.gitignore` - Exclusions Git
- `example_output.json` - Exemple de sortie
- `res_mods/scripts/client/gui/mods/battle_data_collector/`:
  - `__init__.py` - Point d'entrée
  - `config.py` - Configuration (définie dans le fichier)
  - `env_loader.py` - Utilitaires (ex: détection dossier WoT)
  - `battle_data_collector.py` - Collecteur principal
  - `stats_fetcher.py` - Récupération stats API
  - `data_exporter.py` - Export JSON

## Prochaines Étapes
1. Obtenir une clé API Wargaming sur https://developers.wargaming.net/
2. Configurer la clé Wargaming côté API locale (`api/.env`)
3. Tester le mod dans World of Tanks
4. Vérifier les fichiers JSON générés dans `<WoT>/battle_data/`

## Ressources Utiles
- [XVM Mod](https://modxvm.com/) - Exemple de mod complexe
- [KoreanRandom Forum](https://koreanrandom.com/) - Communauté de modding WoT
- [WoT Blitz API Docs](https://developers.wargaming.net/) - API officielle Wargaming
