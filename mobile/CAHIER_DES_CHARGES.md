# Cahier des Charges - Application Mobile Android WoT Scraper

## 📋 Sommaire

1. [Présentation du Projet](#1-présentation-du-projet)
2. [Objectifs](#2-objectifs)
3. [Analyse de l'Existant](#3-analyse-de-lexistant)
4. [Spécifications Fonctionnelles](#4-spécifications-fonctionnelles)
5. [Spécifications Techniques](#5-spécifications-techniques)
6. [Architecture de l'Application](#6-architecture-de-lapplication)
7. [Interface Utilisateur](#7-interface-utilisateur)
8. [Gestion des Données](#8-gestion-des-données)
9. [Gestion des Erreurs](#9-gestion-des-erreurs)
10. [Contraintes et Exigences Non-Fonctionnelles](#10-contraintes-et-exigences-non-fonctionnelles)
11. [Livrables](#11-livrables)
12. [Planning Prévisionnel](#12-planning-prévisionnel)

---

## 1. Présentation du Projet

### 1.1 Contexte

Ce projet consiste à développer une application mobile Android permettant d'exécuter un programme de scraping web en tâche de fond. L'application s'appuie sur un scraper Java existant (situé dans `./scraper/`) qui collecte des données de batailles et de joueurs depuis l'API de tomato.gg pour le jeu World of Tanks.

### 1.2 Périmètre

- **Plateforme cible** : Android (API niveau minimum à définir, recommandé : API 26 - Android 8.0 Oreo)
- **Langage de développement** : Java
- **Répertoire du projet** : `./mobile/`
- **Base de code existante** : `./scraper/` (package `fr.arthurbr02`)

### 1.3 Parties Prenantes

- Développeur principal
- Utilisateurs finaux de l'application

---

## 2. Objectifs

### 2.1 Objectif Principal

Permettre l'exécution d'un scraper web de données World of Tanks directement depuis un appareil Android, avec une interface de contrôle intuitive et une exécution fiable en arrière-plan.

### 2.2 Objectifs Secondaires

- Garantir la persistance du scraping même en cas d'interruption
- Offrir une visibilité en temps réel sur l'avancement du processus
- Permettre l'export des données collectées
- Assurer une expérience utilisateur fluide et informative

---

## 3. Analyse de l'Existant

### 3.1 Structure du Scraper Actuel

Le scraper existant est un projet Gradle Java avec la structure suivante :

```
scraper/
├── app/
│   └── src/main/java/fr/arthurbr02/
│       ├── Main.java                    # Point d'entrée principal
│       ├── battledetail/
│       │   ├── BattleDetail.java        # Modèle de données
│       │   ├── BattleDetailService.java # Service de récupération
│       │   └── ...
│       ├── combinedbattles/
│       │   ├── CombinedBattles.java
│       │   ├── CombinedBattlesService.java
│       │   └── ...
│       ├── player/
│       │   ├── Player.java
│       │   ├── PlayerService.java
│       │   └── tanks/
│       ├── export/
│       │   ├── ExportData.java
│       │   └── ExportService.java
│       └── utils/
│           ├── ProgressState.java       # État de progression
│           ├── ProgressManager.java     # Gestion de la sauvegarde
│           ├── HttpClientsUtils.java    # Client HTTP
│           └── FileUtils.java
└── build.gradle
```

### 3.2 Flux de Données Existant

Le scraping se déroule en **3 étapes distinctes** :

| Étape | Nom | Description | API Utilisée |
|-------|-----|-------------|--------------|
| 1 | CombinedBattles | Récupération des batailles combinées d'un joueur | `api.tomato.gg/api/player/combined-battles/{player_id}` |
| 2 | BattleDetails | Récupération des détails de chaque bataille | `api.tomato.gg/api/player/battle-detail/{arena_id}` |
| 3 | Players | Récupération des informations détaillées des joueurs | `api.tomato.gg/api/player/overall/eu/{player_id}` |

### 3.3 Système de Progression Existant

Le scraper dispose déjà d'un système de sauvegarde de progression (`ProgressState` / `ProgressManager`) :

- Sauvegarde automatique toutes les 5 itérations
- Fichiers de progression : `scraper_progress.json` et `scraper_progress.backup.json`
- Reprise automatique au redémarrage
- Données sauvegardées :
  - `battleDetails` : Batailles récupérées
  - `processedArenaIds` : IDs des arenas traitées
  - `processedPlayerIds` : IDs des joueurs traités
  - `pendingPlayerIds` : Joueurs restants à traiter
  - `currentPlayerIndex` : Index de progression
  - `players` : Joueurs récupérés

### 3.4 Dépendances Actuelles

```groovy
- org.apache.httpcomponents:httpcore:4.4.16
- org.apache.httpcomponents.client5:httpclient5:5.6
- com.fasterxml.jackson.core:jackson-databind:2.18.2
- org.slf4j:slf4j-api:2.0.16
- ch.qos.logback:logback-classic:1.5.13
```

---

## 4. Spécifications Fonctionnelles

### 4.1 Fonctionnalités Principales

#### 4.1.1 Contrôle du Scraping

| ID | Fonctionnalité | Description | Priorité |
|----|----------------|-------------|----------|
| F01 | Démarrer le scraping | Bouton pour lancer le processus de scraping | Haute |
| F02 | Arrêter le scraping | Bouton pour stopper proprement le scraping | Haute |
| F03 | Pause/Reprise | Possibilité de mettre en pause et reprendre | Moyenne |
| F04 | Reprise automatique | Reprise automatique après interruption inattendue | **Critique** |

#### 4.1.2 Visualisation et Monitoring

| ID | Fonctionnalité | Description | Priorité |
|----|----------------|-------------|----------|
| F05 | Barre de progression globale | Affichage de l'avancement global du scraping | Haute |
| F06 | Progression par étape | 3 barres distinctes pour CombinedBattles, BattleDetails, Players | Haute |
| F07 | Logs en temps réel | Affichage des journaux d'activité en direct | Haute |
| F08 | Statistiques | Nombre d'éléments récupérés, temps écoulé, vitesse | Moyenne |

#### 4.1.3 Configuration

| ID | Fonctionnalité | Description | Priorité |
|----|----------------|-------------|----------|
| F09 | Intervalle entre requêtes | Délai configurable entre chaque requête API | Moyenne |
| F10 | Nombre de joueurs | Limite du nombre de joueurs à récupérer (défaut: 100) | Haute |
| F11 | ID joueur initial | Configuration du joueur de départ | Moyenne |
| F12 | Fréquence de sauvegarde | Intervalle de sauvegarde automatique | Moyenne |

#### 4.1.4 Notifications

| ID | Fonctionnalité | Description | Priorité |
|----|----------------|-------------|----------|
| F13 | Notification de démarrage | Notification persistante pendant l'exécution | Haute |
| F14 | Notification d'étape | Notification à chaque fin d'étape | Moyenne |
| F15 | Notification de fin | Notification lorsque le scraping est terminé | Haute |
| F16 | Notification d'erreur | Alerte en cas d'erreur critique | Haute |

#### 4.1.5 Export de Données

| ID | Fonctionnalité | Description | Priorité |
|----|----------------|-------------|----------|
| F17 | Export JSON | Export des données au format JSON | Haute |
| F18 | Export automatique régulier | Sauvegarde périodique des données | **Critique** |
| F19 | Partage de fichier | Option de partager le fichier exporté | Basse |
| F20 | Historique des exports | Liste des exports précédents | Basse |

#### 4.1.6 Persistance et Résilience

| ID | Fonctionnalité | Description | Priorité |
|----|----------------|-------------|----------|
| F21 | Exécution en arrière-plan | Le scraping continue même si l'app est en background | **Critique** |
| F22 | Survie au mode veille | Le scraping continue même en mode veille | **Critique** |
| F23 | Reprise après redémarrage | Reprise automatique après reboot de l'appareil | **Critique** |
| F24 | Sauvegarde anti-perte | Export régulier pour ne perdre aucune donnée | **Critique** |

### 4.2 Format d'Export

Le fichier JSON exporté suivra le format suivant :

```json
{
  "combinedBattles": [
    {
      "arenaIds": [...],
      "playerData": {...}
    }
  ],
  "battleDetails": [
    {
      "arenaId": 123456789,
      "mapName": "Karelia",
      "battleTime": "2025-12-28T19:34:00.000Z",
      "players": [...],
      "result": {...}
    }
  ],
  "players": [
    {
      "playerId": 532440001,
      "nickname": "PlayerName",
      "stats": {...},
      "tanks": [...]
    }
  ]
}
```

---

## 5. Spécifications Techniques

### 5.1 Environnement de Développement

| Élément | Spécification |
|---------|---------------|
| Langage | Java 11+ (compatible Android) |
| IDE | Android Studio |
| Build System | Gradle |
| Version Android minimum | API 26 (Android 8.0 Oreo) |
| Version Android cible | API 34 (Android 14) |

### 5.2 Composants Android Requis

#### 5.2.1 Foreground Service

```java
// Service principal pour le scraping en arrière-plan
public class ScraperService extends Service {
    // Notification persistante obligatoire pour les Foreground Services
    // Gestion du cycle de vie du scraping
    // Communication avec l'UI via LocalBroadcast ou LiveData
}
```

**Justification** : Un Foreground Service est obligatoire pour :
- Maintenir l'exécution en arrière-plan
- Éviter que le système ne tue le processus
- Respecter les restrictions Android 8.0+

#### 5.2.2 Broadcast Receivers

```java
// Receiver pour le redémarrage automatique après reboot
public class BootReceiver extends BroadcastReceiver {
    // Écoute BOOT_COMPLETED
    // Relance le scraping si une progression existe
}

// Receiver pour la gestion de la connectivité
public class NetworkReceiver extends BroadcastReceiver {
    // Écoute les changements de connexion
    // Pause/Reprend le scraping selon la connectivité
}
```

#### 5.2.3 WorkManager (Alternative/Complément)

```java
// Pour les tâches périodiques de sauvegarde
public class SaveProgressWorker extends Worker {
    // Sauvegarde périodique garantie même si l'app est tuée
}
```

#### 5.2.4 SharedPreferences

Pour stocker les paramètres utilisateur :
- Intervalle entre requêtes
- Nombre de joueurs à récupérer
- ID joueur initial
- Fréquence de sauvegarde
- État du dernier scraping

### 5.3 Permissions Android Requises

```xml
<!-- Accès Internet pour les requêtes API -->
<uses-permission android:name="android.permission.INTERNET" />

<!-- Vérification de l'état du réseau -->
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

<!-- Notification de premier plan (Android 13+) -->
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />

<!-- Maintien du CPU actif pendant le scraping -->
<uses-permission android:name="android.permission.WAKE_LOCK" />

<!-- Redémarrage après reboot -->
<uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />

<!-- Service de premier plan -->
<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_DATA_SYNC" />

<!-- Stockage (si export vers stockage externe) -->
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" 
    android:maxSdkVersion="28" />
```

### 5.4 Dépendances Android

```groovy
dependencies {
    // AndroidX Core
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'androidx.core:core-ktx:1.12.0'
    implementation 'com.google.android.material:material:1.11.0'
    
    // Lifecycle & ViewModel
    implementation 'androidx.lifecycle:lifecycle-viewmodel:2.7.0'
    implementation 'androidx.lifecycle:lifecycle-livedata:2.7.0'
    implementation 'androidx.lifecycle:lifecycle-service:2.7.0'
    
    // WorkManager pour les tâches en arrière-plan
    implementation 'androidx.work:work-runtime:2.9.0'
    
    // HTTP Client (OkHttp recommandé pour Android)
    implementation 'com.squareup.okhttp3:okhttp:4.12.0'
    
    // JSON Parsing
    implementation 'com.google.code.gson:gson:2.10.1'
    // OU
    implementation 'com.fasterxml.jackson.core:jackson-databind:2.16.0'
    
    // Room Database (optionnel, pour stockage local robuste)
    implementation 'androidx.room:room-runtime:2.6.1'
    annotationProcessor 'androidx.room:room-compiler:2.6.1'
}
```

### 5.5 Adaptation du Code Existant

#### 5.5.1 Modifications Requises

| Composant Original | Adaptation Android |
|-------------------|-------------------|
| `HttpClientsUtils` (Apache HttpClient) | OkHttp ou HttpURLConnection |
| `ProgressManager` (fichiers locaux) | SharedPreferences + fichiers internes |
| `ExportService` | Export vers stockage interne/externe |
| Logback (logging) | Android Log + fichier de log |

#### 5.5.2 Classes à Réutiliser

Les classes suivantes peuvent être réutilisées avec des modifications mineures :
- Modèles de données (`BattleDetail`, `Player`, `CombinedBattles`, etc.)
- `ProgressState` (état de progression)
- `ExportData` (format d'export)

---

## 6. Architecture de l'Application

### 6.1 Structure du Projet

```
mobile/
├── app/
│   ├── build.gradle
│   └── src/
│       └── main/
│           ├── AndroidManifest.xml
│           ├── java/fr/arthurbr02/wotscraper/
│           │   ├── MainActivity.java
│           │   ├── ui/
│           │   │   ├── MainFragment.java
│           │   │   ├── LogsFragment.java
│           │   │   ├── SettingsFragment.java
│           │   │   └── adapter/
│           │   │       └── LogAdapter.java
│           │   ├── viewmodel/
│           │   │   └── ScraperViewModel.java
│           │   ├── service/
│           │   │   ├── ScraperService.java
│           │   │   └── ScraperNotificationManager.java
│           │   ├── receiver/
│           │   │   ├── BootReceiver.java
│           │   │   └── NetworkReceiver.java
│           │   ├── worker/
│           │   │   └── SaveProgressWorker.java
│           │   ├── scraper/               # Code adapté du scraper
│           │   │   ├── ScraperEngine.java
│           │   │   ├── api/
│           │   │   │   ├── ApiClient.java
│           │   │   │   ├── CombinedBattlesService.java
│           │   │   │   ├── BattleDetailService.java
│           │   │   │   └── PlayerService.java
│           │   │   ├── model/
│           │   │   │   ├── BattleDetail.java
│           │   │   │   ├── CombinedBattles.java
│           │   │   │   ├── Player.java
│           │   │   │   └── ...
│           │   │   └── progress/
│           │   │       ├── ProgressState.java
│           │   │       └── ProgressManager.java
│           │   ├── repository/
│           │   │   └── ScraperRepository.java
│           │   ├── export/
│           │   │   ├── ExportData.java
│           │   │   └── ExportManager.java
│           │   └── util/
│           │       ├── PreferencesManager.java
│           │       └── LogManager.java
│           └── res/
│               ├── layout/
│               │   ├── activity_main.xml
│               │   ├── fragment_main.xml
│               │   ├── fragment_logs.xml
│               │   └── fragment_settings.xml
│               ├── values/
│               │   ├── strings.xml
│               │   └── colors.xml
│               └── drawable/
│                   └── ic_notification.xml
├── build.gradle
├── settings.gradle
└── gradle.properties
```

### 6.2 Diagramme d'Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         UI LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ MainActivity │  │ MainFragment │  │SettingsFragment│         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                  │                   │
│         └────────────────┬┴─────────────────┘                   │
│                          │                                       │
│                ┌─────────▼─────────┐                            │
│                │  ScraperViewModel │◄────── LiveData            │
│                └─────────┬─────────┘                            │
└──────────────────────────┼──────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                          │     SERVICE LAYER                     │
│                ┌─────────▼─────────┐                            │
│                │  ScraperService   │◄────── Foreground Service  │
│                │  (Foreground)     │                            │
│                └─────────┬─────────┘                            │
│                          │                                       │
│         ┌────────────────┼────────────────┐                     │
│         │                │                │                      │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐             │
│  │BootReceiver │  │NetworkRecv  │  │ SaveWorker  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└──────────────────────────┼──────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                          │     DATA LAYER                        │
│                ┌─────────▼─────────┐                            │
│                │  ScraperEngine    │                            │
│                └─────────┬─────────┘                            │
│                          │                                       │
│    ┌─────────────────────┼─────────────────────┐                │
│    │                     │                     │                 │
│ ┌──▼───────────┐  ┌──────▼──────┐  ┌──────────▼──┐             │
│ │CombinedBattles│ │BattleDetail │  │   Player    │             │
│ │   Service     │ │  Service    │  │  Service    │             │
│ └───────────────┘ └─────────────┘  └─────────────┘             │
│                          │                                       │
│                ┌─────────▼─────────┐                            │
│                │    ApiClient      │◄────── OkHttp              │
│                └───────────────────┘                            │
│                          │                                       │
│    ┌─────────────────────┼─────────────────────┐                │
│    │                     │                     │                 │
│ ┌──▼───────────┐  ┌──────▼──────┐  ┌──────────▼──┐             │
│ │ProgressMgr   │  │ ExportMgr   │  │ PreferencesMgr│            │
│ └───────────────┘ └─────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Flux de Communication

```
┌────────────────┐      Bind/Start     ┌─────────────────┐
│   MainActivity │─────────────────────▶│  ScraperService │
│                │◀─────────────────────│                 │
│                │    LiveData/Binder   │                 │
└────────────────┘                      └────────┬────────┘
                                                 │
                                                 │ Callback
                                                 ▼
                                        ┌─────────────────┐
                                        │  ScraperEngine  │
                                        │                 │
                                        │ • onProgress()  │
                                        │ • onLog()       │
                                        │ • onError()     │
                                        │ • onComplete()  │
                                        └─────────────────┘
```

---

## 7. Interface Utilisateur

### 7.1 Écran Principal

```
┌─────────────────────────────────────┐
│  🎮 WoT Scraper                  ⚙️ │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │  État: En cours...          │   │
│  │  Temps écoulé: 00:15:32     │   │
│  └─────────────────────────────┘   │
│                                     │
│  📊 Progression                     │
│                                     │
│  Étape 1: CombinedBattles          │
│  [████████████████████] 100%       │
│  150 batailles récupérées           │
│                                     │
│  Étape 2: BattleDetails            │
│  [████████░░░░░░░░░░░░] 42%        │
│  63/150 détails récupérés          │
│                                     │
│  Étape 3: Players                  │
│  [░░░░░░░░░░░░░░░░░░░░] 0%         │
│  En attente...                      │
│                                     │
│  ┌─────────┐      ┌─────────┐      │
│  │ ▶ START │      │ ⏹ STOP  │      │
│  └─────────┘      └─────────┘      │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 📋 Voir les logs            │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 💾 Exporter les données     │   │
│  └─────────────────────────────┘   │
│                                     │
├─────────────────────────────────────┤
│  [Accueil]  [Logs]  [Paramètres]   │
└─────────────────────────────────────┘
```

### 7.2 Écran des Logs

```
┌─────────────────────────────────────┐
│  ← Logs                        🗑️  │
├─────────────────────────────────────┤
│                                     │
│  14:32:05 INFO  Starting scraper    │
│  14:32:06 INFO  Fetching battles... │
│  14:32:08 INFO  Found 150 arenas    │
│  14:32:10 DEBUG Processing arena 1  │
│  14:32:12 INFO  Battle detail saved │
│  14:32:15 WARN  Slow response...    │
│  14:32:18 INFO  Retry successful    │
│  14:32:20 INFO  Progress saved      │
│  14:32:22 DEBUG Processing arena 2  │
│  ...                                │
│                                     │
│  [Auto-scroll: ON]                  │
│                                     │
├─────────────────────────────────────┤
│  [Accueil]  [Logs]  [Paramètres]   │
└─────────────────────────────────────┘
```

### 7.3 Écran des Paramètres

```
┌─────────────────────────────────────┐
│  ← Paramètres                       │
├─────────────────────────────────────┤
│                                     │
│  📡 Connexion                       │
│  ─────────────────────────────────  │
│  Délai entre requêtes               │
│  [═══════○═══════════] 500ms       │
│                                     │
│  Timeout de connexion               │
│  [═════════════○═════] 30s         │
│                                     │
│  📊 Scraping                        │
│  ─────────────────────────────────  │
│  Nombre de joueurs                  │
│  [ 100                         ]    │
│                                     │
│  ID joueur initial                  │
│  [ 532440001                   ]    │
│                                     │
│  💾 Sauvegarde                      │
│  ─────────────────────────────────  │
│  Fréquence de sauvegarde            │
│  [○] Toutes les 5 itérations       │
│  [ ] Toutes les 10 itérations      │
│  [ ] Toutes les 20 itérations      │
│                                     │
│  Export automatique                 │
│  [═══════════════════○] ON         │
│                                     │
│  🔔 Notifications                   │
│  ─────────────────────────────────  │
│  Notification de fin   [ON]         │
│  Notification d'erreur [ON]         │
│  Notification d'étape  [OFF]        │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  🗑️ Réinitialiser paramètres │   │
│  └─────────────────────────────┘   │
│                                     │
├─────────────────────────────────────┤
│  [Accueil]  [Logs]  [Paramètres]   │
└─────────────────────────────────────┘
```

### 7.4 Notification Persistante

```
┌─────────────────────────────────────┐
│ 🎮 WoT Scraper                      │
│ Scraping en cours... 42%            │
│ 63/150 détails de bataille          │
│                         [ARRÊTER]   │
└─────────────────────────────────────┘
```

---

## 8. Gestion des Données

### 8.1 Stockage Local

| Type de Données | Méthode de Stockage | Justification |
|-----------------|---------------------|---------------|
| Préférences utilisateur | SharedPreferences | Données simples, accès rapide |
| État de progression | Fichier JSON interne | Structure complexe, doit survivre aux crashes |
| Logs | Fichier texte rotatif | Debug et historique |
| Export de données | Fichier JSON externe | Partage et récupération |

### 8.2 Chemins de Fichiers

```java
// Fichier de progression
Context.getFilesDir() + "/scraper_progress.json"

// Backup de progression
Context.getFilesDir() + "/scraper_progress.backup.json"

// Exports
Context.getExternalFilesDir(null) + "/exports/export_data_TIMESTAMP.json"

// Logs
Context.getFilesDir() + "/logs/scraper.log"
```

### 8.3 Stratégie de Sauvegarde Anti-Perte

```
┌─────────────────────────────────────────────────────────────────┐
│                    STRATÉGIE DE SAUVEGARDE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Sauvegarde de progression (toutes les N itérations)        │
│     └─▶ scraper_progress.json                                   │
│         └─▶ scraper_progress.backup.json (rotation)            │
│                                                                  │
│  2. Export automatique partiel (toutes les 50 batailles)       │
│     └─▶ exports/partial_export_TIMESTAMP.json                   │
│                                                                  │
│  3. Export final (à la fin du scraping)                        │
│     └─▶ exports/export_data_TIMESTAMP.json                      │
│                                                                  │
│  4. Avant chaque opération critique                             │
│     └─▶ Flush des données en mémoire vers le disque            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.4 Cycle de Vie des Données

```
[Démarrage]
     │
     ▼
[Vérifier progression existante]
     │
     ├── Oui ──▶ [Charger progression] ──▶ [Reprendre]
     │
     └── Non ──▶ [Nouvelle session]
                      │
                      ▼
               [Scraping en cours]
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
   [Sauvegarde   [Export      [Log
    régulière]    partiel]     activité]
        │             │             │
        └─────────────┼─────────────┘
                      │
                      ▼
              [Fin du scraping]
                      │
                      ▼
              [Export final]
                      │
                      ▼
          [Nettoyage progression]
```

### 8.5 Variables du Scraper à Sauvegarder

Cette section détaille l'ensemble des variables et structures de données qui doivent être persistées pour garantir une reprise exacte du scraping.

#### 8.5.1 Structure Complète de l'État de Progression

```java
public class ProgressState {
    // === MÉTADONNÉES DE SESSION ===
    private String sessionId;              // Identifiant unique de la session
    private String initialPlayerId;        // ID du joueur de départ (ex: "532440001")
    private Date startTime;                // Date/heure de début du scraping
    private Date lastUpdateTime;           // Date/heure de la dernière sauvegarde
    private ScrapingPhase currentPhase;    // Phase actuelle (COMBINED_BATTLES, BATTLE_DETAILS, PLAYERS)
    
    // === ÉTAPE 1: COMBINED BATTLES ===
    private List<CombinedBattles> combinedBattlesList;  // Liste des CombinedBattles récupérés
    private List<Long> allArenaIds;                      // Tous les IDs d'arenas extraits
    private int combinedBattlesProgress;                 // Nombre de joueurs traités pour cette étape
    private int combinedBattlesTotal;                    // Total de joueurs à traiter pour cette étape
    
    // === ÉTAPE 2: BATTLE DETAILS ===
    private List<BattleDetail> battleDetails;            // Liste des détails de bataille récupérés
    private Set<Long> processedArenaIds;                 // IDs des arenas déjà traitées
    private List<Long> pendingArenaIds;                  // IDs des arenas restantes à traiter
    private int battleDetailsProgress;                   // Index actuel dans la liste des arenas
    private int battleDetailsTotal;                      // Total d'arenas à traiter
    
    // === ÉTAPE 3: PLAYERS ===
    private List<Player> players;                        // Liste des joueurs récupérés
    private Set<Long> processedPlayerIds;                // IDs des joueurs déjà traités
    private List<Long> pendingPlayerIds;                 // IDs des joueurs restants à traiter
    private int currentPlayerIndex;                      // Index du joueur en cours
    private int totalPlayersToFetch;                     // Nombre total de joueurs à récupérer
    
    // === STATISTIQUES ===
    private long totalRequestsMade;                      // Nombre total de requêtes effectuées
    private long successfulRequests;                     // Requêtes réussies
    private long failedRequests;                         // Requêtes échouées
    private long totalBytesDownloaded;                   // Volume de données téléchargées
    
    // === GESTION DES ERREURS ===
    private int consecutiveErrors;                       // Compteur d'erreurs consécutives
    private String lastErrorMessage;                     // Dernier message d'erreur
    private Date lastErrorTime;                          // Date de la dernière erreur
}
```

#### 8.5.2 Enum des Phases de Scraping

```java
public enum ScrapingPhase {
    NOT_STARTED,           // Pas encore démarré
    COMBINED_BATTLES,      // Étape 1: Récupération des CombinedBattles
    BATTLE_DETAILS,        // Étape 2: Récupération des BattleDetails
    PLAYERS,               // Étape 3: Récupération des informations joueurs
    COMPLETED,             // Scraping terminé avec succès
    PAUSED,                // En pause (manuel ou perte de connexion)
    ERROR                  // Arrêté sur erreur
}
```

#### 8.5.3 Tableau Récapitulatif des Variables

| Catégorie | Variable | Type | Description | Criticité |
|-----------|----------|------|-------------|-----------|
| **Métadonnées** | `sessionId` | String | ID unique de session | Haute |
| | `initialPlayerId` | String | Joueur de départ | Haute |
| | `startTime` | Date | Début du scraping | Moyenne |
| | `lastUpdateTime` | Date | Dernière sauvegarde | Haute |
| | `currentPhase` | Enum | Phase actuelle | **Critique** |
| **Étape 1** | `combinedBattlesList` | List<CombinedBattles> | Batailles combinées | **Critique** |
| | `allArenaIds` | List<Long> | IDs d'arenas extraits | **Critique** |
| | `combinedBattlesProgress` | int | Progression étape 1 | Haute |
| | `combinedBattlesTotal` | int | Total étape 1 | Haute |
| **Étape 2** | `battleDetails` | List<BattleDetail> | Détails des batailles | **Critique** |
| | `processedArenaIds` | Set<Long> | Arenas traitées | **Critique** |
| | `pendingArenaIds` | List<Long> | Arenas restantes | **Critique** |
| | `battleDetailsProgress` | int | Progression étape 2 | Haute |
| | `battleDetailsTotal` | int | Total étape 2 | Haute |
| **Étape 3** | `players` | List<Player> | Joueurs récupérés | **Critique** |
| | `processedPlayerIds` | Set<Long> | Joueurs traités | **Critique** |
| | `pendingPlayerIds` | List<Long> | Joueurs restants | **Critique** |
| | `currentPlayerIndex` | int | Index joueur courant | **Critique** |
| | `totalPlayersToFetch` | int | Total joueurs | Haute |
| **Stats** | `totalRequestsMade` | long | Requêtes effectuées | Basse |
| | `successfulRequests` | long | Requêtes OK | Basse |
| | `failedRequests` | long | Requêtes KO | Moyenne |
| **Erreurs** | `consecutiveErrors` | int | Erreurs consécutives | Moyenne |
| | `lastErrorMessage` | String | Message d'erreur | Basse |
| | `lastErrorTime` | Date | Date dernière erreur | Basse |

#### 8.5.4 Format JSON de Sauvegarde

```json
{
  "sessionId": "session_20260102_143256",
  "initialPlayerId": "532440001",
  "startTime": "2026-01-02T14:32:56.000+01:00",
  "lastUpdateTime": "2026-01-02T15:45:12.000+01:00",
  "currentPhase": "BATTLE_DETAILS",
  
  "combinedBattlesList": [
    {
      "playerId": 532440001,
      "arenaIds": [123456789, 123456790, ...],
      "battleCount": 150
    },
    ...
  ],
  "allArenaIds": [123456789, 123456790, 123456791, ...],
  "combinedBattlesProgress": 25,
  "combinedBattlesTotal": 25,
  
  "battleDetails": [
    {
      "arenaId": 123456789,
      "mapName": "Karelia",
      "battleTime": "2025-12-28T19:34:00.000Z",
      "winnerTeam": 1,
      "players": [...]
    },
    ...
  ],
  "processedArenaIds": [123456789, 123456790, ...],
  "pendingArenaIds": [123456850, 123456851, ...],
  "battleDetailsProgress": 63,
  "battleDetailsTotal": 150,
  
  "players": [
    {
      "playerId": 532440001,
      "nickname": "PlayerName",
      "clanTag": "CLAN",
      "stats": {...},
      "tanks": [...]
    },
    ...
  ],
  "processedPlayerIds": [532440001, 532440002, ...],
  "pendingPlayerIds": [532440050, 532440051, ...],
  "currentPlayerIndex": 0,
  "totalPlayersToFetch": 100,
  
  "statistics": {
    "totalRequestsMade": 215,
    "successfulRequests": 210,
    "failedRequests": 5,
    "totalBytesDownloaded": 15728640
  },
  
  "errorState": {
    "consecutiveErrors": 0,
    "lastErrorMessage": null,
    "lastErrorTime": null
  }
}
```

#### 8.5.5 Moments de Sauvegarde

| Événement | Variables Sauvegardées | Fichier |
|-----------|------------------------|---------|
| Fin d'initialisation | Toutes | `scraper_progress.json` |
| Toutes les N itérations (configurable) | Toutes | `scraper_progress.json` |
| Changement de phase | Toutes | `scraper_progress.json` |
| Avant chaque requête API | Index courant uniquement | Mémoire → fichier si crash |
| Après erreur | Toutes + état d'erreur | `scraper_progress.json` |
| Pause manuelle | Toutes | `scraper_progress.json` |
| Perte de connexion | Toutes | `scraper_progress.json` |
| Toutes les 50 batailles | Données collectées | `partial_export_*.json` |
| Fin du scraping | Données finales | `export_data_*.json` |

#### 8.5.6 Logique de Reprise

```
[Chargement de la progression]
         │
         ▼
[Lire currentPhase]
         │
         ├── COMBINED_BATTLES ──▶ Reprendre à combinedBattlesProgress
         │
         ├── BATTLE_DETAILS ──▶ Reprendre à partir de pendingArenaIds[0]
         │
         ├── PLAYERS ──▶ Reprendre à partir de pendingPlayerIds[currentPlayerIndex]
         │
         ├── PAUSED ──▶ Reprendre à la phase précédente
         │
         └── ERROR ──▶ Afficher erreur, proposer reprise manuelle
```

#### 8.5.7 Validation de l'Intégrité des Données

Avant de reprendre une session, les vérifications suivantes sont effectuées :

```java
public class ProgressValidator {
    
    public static ValidationResult validate(ProgressState state) {
        List<String> errors = new ArrayList<>();
        
        // Vérification des métadonnées
        if (state.getSessionId() == null) {
            errors.add("Session ID manquant");
        }
        
        // Vérification de cohérence des listes
        if (state.getBattleDetails().size() != state.getProcessedArenaIds().size()) {
            errors.add("Incohérence battleDetails/processedArenaIds");
        }
        
        // Vérification des index
        if (state.getCurrentPlayerIndex() > state.getPendingPlayerIds().size()) {
            errors.add("Index joueur hors limites");
        }
        
        // Vérification que les données critiques ne sont pas corrompues
        for (BattleDetail bd : state.getBattleDetails()) {
            if (bd.getArenaId() == null) {
                errors.add("BattleDetail corrompu détecté");
                break;
            }
        }
        
        return new ValidationResult(errors.isEmpty(), errors);
    }
}
```


### 9.1 Types d'Erreurs

| Type | Cause | Comportement |
|------|-------|--------------|
| Erreur réseau | Pas de connexion | Pause automatique + notification |
| Timeout API | Serveur lent | Retry avec backoff exponentiel |
| Erreur de parsing | Réponse invalide | Log + skip + continuer |
| Erreur de stockage | Espace insuffisant | Alerte utilisateur + pause |
| Erreur fatale | Exception non gérée | Sauvegarde d'urgence + notification |

### 9.2 Stratégie de Retry

```java
public class RetryStrategy {
    private static final int MAX_RETRIES = 3;
    private static final long INITIAL_DELAY_MS = 1000;
    private static final double BACKOFF_MULTIPLIER = 2.0;
    
    // Délais: 1s, 2s, 4s
}
```

### 9.3 Gestion de la Connectivité

```
[Perte de connexion détectée]
         │
         ▼
[Sauvegarder progression immédiatement]
         │
         ▼
[Mettre le scraping en pause]
         │
         ▼
[Afficher notification "En attente de connexion"]
         │
         ▼
[NetworkReceiver écoute le réseau]
         │
         ▼
[Connexion rétablie]
         │
         ▼
[Reprendre automatiquement le scraping]
```

---

## 10. Contraintes et Exigences Non-Fonctionnelles

### 10.1 Performance

| Critère | Exigence |
|---------|----------|
| Consommation mémoire | < 100 MB en fonctionnement normal |
| Consommation batterie | Optimisée (pas de polling excessif) |
| Temps de réponse UI | < 100ms pour les interactions |
| Temps de démarrage | < 2s pour l'affichage initial |

### 10.2 Fiabilité

| Critère | Exigence |
|---------|----------|
| Perte de données | **ZÉRO** perte de données en cas d'arrêt inattendu |
| Disponibilité | L'app doit fonctionner 24/7 si nécessaire |
| Récupération | Reprise automatique < 5s après rétablissement réseau |

### 10.3 Sécurité

| Critère | Exigence |
|---------|----------|
| Stockage des données | Fichiers privés à l'application |
| Transmission | HTTPS uniquement |
| Permissions | Minimum requis (pas de permissions superflues) |

### 10.4 Compatibilité

| Critère | Exigence |
|---------|----------|
| Version Android | API 26+ (Android 8.0 Oreo et supérieur) |
| Tailles d'écran | Support phones et tablets |
| Orientation | Portrait principal, landscape supporté |

### 10.5 Maintenabilité

| Critère | Exigence |
|---------|----------|
| Séparation des couches | UI / Service / Data clairement séparés |
| Documentation code | Commentaires sur les parties critiques |

---

## 11. Livrables

### 11.1 Code Source

- Code source complet de l'application Android
- Séparation claire entre logique Android et logique de scraping
- Documentation inline (Javadoc)

### 11.2 Documentation

- Ce cahier des charges (mis à jour si nécessaire)
- README.md avec instructions d'installation et d'utilisation
- Guide de contribution (si applicable)

### 11.3 Application

- APK de debug
- APK de release signé pour la production
- Fichier de mapping ProGuard (si minification activée)

---

## 12. Planning Prévisionnel

### 12.1 Phases de Développement

| Phase | Description | Durée Estimée |
|-------|-------------|---------------|
| **Phase 1** | Configuration projet + Architecture de base | 2-3 jours |
| **Phase 2** | Adaptation du code scraper pour Android | 3-4 jours |
| **Phase 3** | Implémentation du Foreground Service | 2-3 jours |
| **Phase 4** | Interface utilisateur principale | 2-3 jours |
| **Phase 5** | Système de progression et sauvegarde | 2-3 jours |
| **Phase 6** | Notifications et gestion arrière-plan | 2 jours |
| **Phase 7** | Export de données et partage | 1-2 jours |
| **Phase 8** | Corrections de bugs et finalisation | 2-3 jours |

### 12.2 Estimation Totale

**Durée totale estimée : 15-21 jours de développement**

### 12.3 Jalons Clés

| Jalon | Description | Date Cible |
|-------|-------------|------------|
| M1 | Prototype fonctionnel (scraping de base) | Fin Phase 3 |
| M2 | Version alpha (UI + scraping) | Fin Phase 5 |
| M3 | Version beta (fonctionnalités complètes) | Fin Phase 7 |
| M4 | Version 1.0 | Fin Phase 8 |

---

## Annexes

### A. Glossaire

| Terme | Définition |
|-------|------------|
| **Arena** | Identifiant unique d'une bataille dans World of Tanks |
| **CombinedBattles** | Données combinées des batailles d'un joueur |
| **BattleDetail** | Informations détaillées d'une bataille spécifique |
| **Foreground Service** | Service Android avec notification visible, ne peut pas être tué par le système |
| **WorkManager** | API Android pour les tâches en arrière-plan garanties |

### B. Références

- [Documentation Android - Services](https://developer.android.com/guide/components/services)
- [Documentation Android - Foreground Services](https://developer.android.com/guide/components/foreground-services)
- [Documentation Android - WorkManager](https://developer.android.com/topic/libraries/architecture/workmanager)
- [API tomato.gg](https://api.tomato.gg) (source de données)

### C. Historique des Révisions

| Version | Date | Auteur | Modifications |
|---------|------|--------|---------------|
| 1.0 | 2025-01-02 | - | Version initiale |

---

*Document généré le 2 janvier 2026*
