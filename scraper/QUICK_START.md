# Guide d'Utilisation Rapide du Système de Progression

## Utilisation de Base

### 1. Démarrer le Scraper
```bash
./gradlew run
```

Le programme va :
- Vérifier s'il existe une progression sauvegardée
- Si oui → Reprendre automatiquement
- Si non → Démarrer une nouvelle session

### 2. Interruption et Reprise

**Scénario 1 : Plantage ou Erreur**
- Le programme sauvegarde automatiquement avant de se terminer
- Relancez simplement `./gradlew run`
- La progression reprend automatiquement

**Scénario 2 : Interruption Manuelle (Ctrl+C)**
- Si l'interruption se produit entre deux sauvegardes, vous perdez au maximum 5 joueurs de progression
- Relancez `./gradlew run` pour reprendre

### 3. Recommencer depuis le Début

Si vous voulez ignorer la progression sauvegardée :

**Windows PowerShell :**
```powershell
Remove-Item scraper_progress.json, scraper_progress.backup.json -ErrorAction SilentlyContinue
./gradlew run
```

**Linux/Mac :**
```bash
rm -f scraper_progress.json scraper_progress.backup.json
./gradlew run
```

## Exemples de Logs

### Nouveau Démarrage
```
2025-12-29 14:00:00 INFO  - === Starting scraper ===
2025-12-29 14:00:00 INFO  - No existing progress file found. Starting fresh.
2025-12-29 14:00:00 INFO  - Starting new scraping session
2025-12-29 14:00:00 INFO  - Fetching initial CombinedBattles for player 532440001
2025-12-29 14:00:02 INFO  - Found 10 arena IDs
2025-12-29 14:00:05 INFO  - Initialized with 10 battles and 50 players to process
2025-12-29 14:00:05 INFO  - Progress saved: 10 battles, 0 players processed, 0/50 players total
```

### Reprise Après Plantage
```
2025-12-29 15:30:00 INFO  - === Starting scraper ===
2025-12-29 15:30:00 INFO  - Resuming from previous session
2025-12-29 15:30:00 INFO  - Progress loaded: 150 battles, 25 players processed, 25/50 players total
2025-12-29 15:30:00 INFO  - Last update: 2025-12-29 15:15:00
2025-12-29 15:30:00 INFO  - Start time: 2025-12-29 14:00:00
2025-12-29 15:30:00 INFO  - Processing players from index 25 to 50
2025-12-29 15:30:00 INFO  - Processing player 26/50: 123456789
```

### Progression En Cours
```
2025-12-29 14:05:00 INFO  - Processing player 5/50: 987654321
2025-12-29 14:05:01 DEBUG - Found 8 new arenas for player 987654321
2025-12-29 14:05:05 INFO  - Progress saved: 58 battles, 5 players processed, 5/50 players total
```

### Fin Réussie
```
2025-12-29 16:00:00 INFO  - Fetching detailed player information
2025-12-29 16:00:30 INFO  - Scraping completed: 500 battles, 50 players
2025-12-29 16:00:31 INFO  - Exported data to export_data_1735491631000.json
2025-12-29 16:00:31 INFO  - Scraping completed successfully!
2025-12-29 16:00:31 INFO  - Progress file deleted
2025-12-29 16:00:31 INFO  - Backup file deleted
```

## Vérification de la Progression

Pour voir où en est le scraping sans le relancer, consultez `scraper_progress.json` :

```json
{
  "initialPlayerId" : "532440001",
  "startTime" : "2025-12-29T14:00:00.000+00:00",
  "lastUpdateTime" : "2025-12-29T15:15:00.000+00:00",
  "battleDetails" : [ ... ],
  "processedArenaIds" : [ ... ],
  "processedPlayerIds" : [ ... ],
  "pendingPlayerIds" : [ ... ],
  "players" : [ ... ],
  "currentPlayerIndex" : 25,
  "totalPlayersToFetch" : 50
}
```

**Calcul de la progression :**
```
Progression = (currentPlayerIndex / totalPlayersToFetch) * 100
Exemple : (25 / 50) * 100 = 50%
```

## Ajustement de la Fréquence de Sauvegarde

Par défaut, la progression est sauvegardée toutes les 5 itérations. Pour modifier cette fréquence :

1. Ouvrez `app/src/main/java/fr/arthurbr02/Main.java`
2. Trouvez cette ligne dans la méthode `executeScraping()` :
```java
if ((i + 1) % 5 == 0) {
    ProgressManager.saveProgress(state);
}
```
3. Changez `5` par la fréquence souhaitée :
   - `1` = Sauvegarde après chaque joueur (plus sûr mais plus lent)
   - `10` = Sauvegarde toutes les 10 itérations (plus rapide mais risque de perdre plus de progression)
   - `20` = Sauvegarde toutes les 20 itérations

## Conseils

### Performance vs Sécurité
- **Fréquence élevée (1-2)** : Maximum de sécurité, légère baisse de performance
- **Fréquence moyenne (5-10)** : Bon équilibre (recommandé)
- **Fréquence faible (20+)** : Meilleure performance, risque de perte de données

### Surveillance
Surveillez les logs pour vérifier que tout se passe bien :
```bash
tail -f logs/scraper.log
```

### Espace Disque
Le fichier `scraper_progress.json` peut devenir volumineux (plusieurs Mo). Assurez-vous d'avoir suffisamment d'espace disque.

## Dépannage Rapide

| Problème | Solution |
|----------|----------|
| Le programme ne reprend pas | Vérifiez que `scraper_progress.json` existe et contient du JSON valide |
| Erreur "Error loading progress file" | Le programme va automatiquement essayer le fichier backup |
| Vouloir recommencer | Supprimez `scraper_progress.json` et `scraper_progress.backup.json` |
| Progression trop lente | Augmentez la fréquence de sauvegarde (ex: 10 au lieu de 5) |
| Perte de données après plantage | Diminuez la fréquence de sauvegarde (ex: 1 ou 2) |

