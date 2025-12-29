# Système de Sauvegarde de Progression du Scraper

## Vue d'ensemble

Le scraper dispose désormais d'un système de sauvegarde automatique de la progression qui permet de reprendre le scraping là où il s'est arrêté en cas de plantage ou d'interruption.

## Fonctionnalités

### 1. Sauvegarde Automatique
- La progression est sauvegardée automatiquement toutes les 5 itérations
- Un fichier de backup est créé avant chaque sauvegarde pour éviter la corruption de données
- La sauvegarde inclut :
  - Les batailles déjà récupérées (`BattleDetail`)
  - Les IDs des arenas déjà traitées
  - Les IDs des joueurs déjà traités
  - Les joueurs restants à traiter
  - L'index actuel de progression
  - Les horodatages de début et dernière mise à jour

### 2. Reprise Automatique
- Au démarrage, le programme vérifie s'il existe une progression sauvegardée
- Si oui, il reprend automatiquement là où il s'était arrêté
- Si non, il démarre une nouvelle session de scraping

### 3. Fichiers de Progression

Les fichiers de progression sont stockés dans le répertoire du projet :
- `scraper_progress.json` : Fichier principal de progression
- `scraper_progress.backup.json` : Fichier de sauvegarde (backup)

Ces fichiers sont automatiquement supprimés après une exécution réussie.

## Structure des Données Sauvegardées

```json
{
  "initialPlayerId": "532440001",
  "startTime": "2025-12-29T...",
  "lastUpdateTime": "2025-12-29T...",
  "battleDetails": [...],
  "processedArenaIds": [...],
  "processedPlayerIds": [...],
  "pendingPlayerIds": [...],
  "players": [...],
  "currentPlayerIndex": 25,
  "totalPlayersToFetch": 50
}
```

## Utilisation

### Démarrage Normal
```bash
./gradlew run
```
- Si aucune progression n'existe, démarre une nouvelle session
- Si une progression existe, reprend automatiquement

### Forcer un Nouveau Démarrage
Si vous voulez ignorer la progression sauvegardée et recommencer depuis le début, supprimez manuellement les fichiers de progression :
```bash
rm scraper_progress.json
rm scraper_progress.backup.json
```

### Vérifier la Progression
Vous pouvez consulter le fichier `scraper_progress.json` pour voir l'état actuel du scraping :
- Nombre de batailles récupérées
- Nombre de joueurs traités
- Progression actuelle (currentPlayerIndex / totalPlayersToFetch)

## Gestion des Erreurs

### En Cas de Plantage
1. Le programme sauvegarde automatiquement la progression avant de se terminer
2. Les logs indiquent : "Error during scraping - progress has been saved"
3. Au prochain démarrage, la progression sera automatiquement reprise

### Récupération depuis le Backup
Si le fichier principal `scraper_progress.json` est corrompu :
1. Le programme tente automatiquement de charger depuis `scraper_progress.backup.json`
2. Si réussi, le fichier principal est restauré depuis le backup

## Logs

Le système de progression génère des logs détaillés :

### Au Démarrage
```
INFO  - Starting scraper
INFO  - No existing progress file found. Starting fresh.
```
ou
```
INFO  - Starting scraper
INFO  - Resuming from previous session
INFO  - Progress loaded: 150 battles, 25 players processed, 25/50 players total
INFO  - Last update: Sun Dec 29 14:30:00 CET 2025
```

### Pendant l'Exécution
```
INFO  - Processing player 26/50: 123456789
INFO  - Progress saved: 175 battles, 26 players processed, 26/50 players total
```

### À la Fin
```
INFO  - Scraping completed: 500 battles, 50 players
INFO  - Exported data to export_data_1735481234567.json
INFO  - Progress file deleted
INFO  - Backup file deleted
```

## Architecture Technique

### Classes Impliquées

1. **ProgressState** (`utils/ProgressState.java`)
   - POJO contenant toutes les données de progression
   - Sérialisable en JSON via Jackson

2. **ProgressManager** (`utils/ProgressManager.java`)
   - Gère la sauvegarde et le chargement de la progression
   - Crée des backups automatiques
   - Gère la récupération en cas d'erreur

3. **Main** (`Main.java`)
   - Modifié pour utiliser le système de progression
   - Méthodes séparées :
     - `initializeNewProgress()` : Initialise une nouvelle session
     - `executeScraping()` : Exécute le scraping avec sauvegarde

### Fréquence de Sauvegarde

La progression est sauvegardée :
- Après l'initialisation
- Toutes les 5 itérations de traitement de joueurs
- Après chaque joueur en cas d'erreur
- À la fin du scraping

Cette fréquence peut être ajustée en modifiant la condition dans `Main.executeScraping()` :
```java
if ((i + 1) % 5 == 0) {  // Changer 5 par la fréquence souhaitée
    ProgressManager.saveProgress(state);
}
```

## Avantages

1. **Résilience** : Ne perd plus de données en cas de plantage
2. **Flexibilité** : Permet d'arrêter et reprendre le scraping à volonté
3. **Traçabilité** : Logs détaillés de la progression
4. **Sécurité** : Système de backup pour éviter la corruption de données
5. **Performance** : Évite de refaire le travail déjà effectué

## Limitations

- Les fichiers de progression peuvent devenir volumineux si beaucoup de données sont collectées
- La sérialisation JSON peut prendre du temps pour de très grandes quantités de données
- La sauvegarde est synchrone et peut légèrement ralentir le scraping

## Dépannage

### Le Programme Ne Reprend Pas la Progression
1. Vérifiez que `scraper_progress.json` existe
2. Vérifiez les logs pour voir si le fichier a été chargé
3. Vérifiez que le fichier n'est pas corrompu (doit être du JSON valide)

### Erreur de Lecture du Fichier de Progression
1. Le programme tentera de charger le backup automatiquement
2. Si les deux fichiers sont corrompus, supprimez-les et redémarrez

### Vouloir Réinitialiser Complètement
Supprimez les fichiers de progression :
```bash
rm scraper_progress.json scraper_progress.backup.json
```

