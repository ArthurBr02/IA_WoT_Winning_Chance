# Plan d'Implémentation - Application Mobile WoT Scraper

## 📋 Vue d'Ensemble

Ce document présente le plan d'implémentation détaillé pour le développement de l'application mobile Android WoT Scraper, basé sur le cahier des charges.

**Durée totale estimée** : 15-21 jours (3-4 semaines)  
**Méthodologie** : Approche itérative par sprints d'une semaine

---

## 🗓️ Planning Global

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TIMELINE DU PROJET                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Semaine 1        Semaine 2        Semaine 3        Semaine 4               │
│  ──────────       ──────────       ──────────       ──────────              │
│  │ PHASE 1 │      │ PHASE 2 │      │ PHASE 3 │      │ PHASE 4 │             │
│  │ Setup & │      │ Scraper │      │   UI &  │      │ Polish  │             │
│  │  Base   │      │  Core   │      │ Features│      │& Release│             │
│  └─────────┘      └─────────┘      └─────────┘      └─────────┘             │
│                                                                              │
│  ▸ Config projet  ▸ Adaptation     ▸ Interface      ▸ Bugs                  │
│  ▸ Architecture   ▸ Services API   ▸ Notifications  ▸ Optimisation          │
│  ▸ Foreground Svc ▸ Progression    ▸ Export         ▸ Documentation         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 PHASE 1 : Configuration & Architecture de Base
### 🗓️ Semaine 1 (Jours 1-5)

Cette phase établit les fondations du projet Android et implémente le service en arrière-plan.

---

### Sprint 1.1 : Configuration du Projet (Jours 1-2)

#### Objectifs
- Créer le projet Android Studio
- Configurer Gradle et les dépendances
- Mettre en place l'architecture de base

#### Tâches

| # | Tâche | Durée | Priorité | Dépendances |
|---|-------|-------|----------|-------------|
| 1.1.1 | Créer le projet Android Studio avec package `fr.arthurbr02.wotscraper` | 1h | Haute | - |
| 1.1.2 | Configurer `build.gradle` avec les dépendances (OkHttp, Gson, AndroidX) | 1h | Haute | 1.1.1 |
| 1.1.3 | Configurer `AndroidManifest.xml` avec toutes les permissions requises | 30min | Haute | 1.1.1 |
| 1.1.4 | Créer la structure de packages selon l'architecture définie | 1h | Haute | 1.1.1 |
| 1.1.5 | Configurer les ressources de base (strings.xml, colors.xml, themes) | 1h | Moyenne | 1.1.1 |
| 1.1.6 | Créer `MainActivity.java` avec navigation de base | 2h | Haute | 1.1.4 |
| 1.1.7 | Implémenter `PreferencesManager.java` pour SharedPreferences | 2h | Haute | 1.1.4 |

#### Livrables Sprint 1.1
- [x] Projet Android compilable
- [x] Structure de packages créée
- [x] MainActivity fonctionnelle avec navigation vide
- [x] PreferencesManager opérationnel

#### Critères d'Acceptation
```
✓ L'application se lance sans erreur
✓ La structure de packages correspond à l'architecture définie
✓ Les préférences peuvent être lues/écrites
```

---

### Sprint 1.2 : Foreground Service (Jours 3-5)

#### Objectifs
- Implémenter le service de scraping en arrière-plan
- Gérer les notifications persistantes
- Mettre en place la communication Service ↔ UI

#### Tâches

| # | Tâche | Durée | Priorité | Dépendances |
|---|-------|-------|----------|-------------|
| 1.2.1 | Créer `ScraperService.java` étendant Service | 2h | Critique | 1.1.6 |
| 1.2.2 | Implémenter le cycle de vie du Foreground Service | 2h | Critique | 1.2.1 |
| 1.2.3 | Créer `ScraperNotificationManager.java` pour les notifications | 3h | Haute | 1.2.1 |
| 1.2.4 | Implémenter la notification persistante avec progression | 2h | Haute | 1.2.3 |
| 1.2.5 | Créer le Binder pour la communication Service ↔ Activity | 2h | Haute | 1.2.1 |
| 1.2.6 | Implémenter `BootReceiver.java` pour le redémarrage auto | 2h | Haute | 1.2.1 |
| 1.2.7 | Implémenter `NetworkReceiver.java` pour la connectivité | 2h | Haute | 1.2.1 |
| 1.2.8 | Déclarer les receivers et service dans le Manifest | 1h | Haute | 1.2.6, 1.2.7 |

#### Livrables Sprint 1.2
- [x] ScraperService fonctionnel en Foreground
- [x] Notification persistante affichée
- [x] BootReceiver configuré
- [x] NetworkReceiver configuré

#### Critères d'Acceptation
```
✓ Le service démarre et reste actif en arrière-plan
✓ La notification persiste même si l'app est fermée
✓ L'app redémarre après un reboot (si progression existante)
✓ La perte de connexion est détectée
```

---

## ⚙️ PHASE 2 : Adaptation du Scraper
### 🗓️ Semaine 2 (Jours 6-10)

Cette phase adapte le code Java existant du scraper pour Android.

---

### Sprint 2.1 : Modèles et Client API (Jours 6-7)

#### Objectifs
- Copier et adapter les modèles de données
- Créer le client HTTP Android

#### Tâches

| # | Tâche | Durée | Priorité | Dépendances |
|---|-------|-------|----------|-------------|
| 2.1.1 | Copier les classes modèles depuis `scraper/` vers `mobile/` | 1h | Haute | Phase 1 |
| 2.1.2 | Adapter les imports et annotations Jackson → Gson | 2h | Haute | 2.1.1 |
| 2.1.3 | Créer `ApiClient.java` avec OkHttp | 3h | Critique | 1.1.2 |
| 2.1.4 | Implémenter la gestion des timeouts et retry | 2h | Haute | 2.1.3 |
| 2.1.5 | Créer les intercepteurs OkHttp pour le logging | 1h | Moyenne | 2.1.3 |
| 2.1.6 | Implémenter la gestion du rate limiting | 2h | Haute | 2.1.3 |

#### Classes à Copier/Adapter

```
scraper/                              →    mobile/
├── battledetail/                          ├── scraper/model/
│   ├── BattleDetail.java            →    │   ├── BattleDetail.java
│   ├── Player.java                  →    │   ├── BattlePlayer.java
│   └── ...                                │   └── ...
├── combinedbattles/                       │
│   ├── CombinedBattles.java         →    │   ├── CombinedBattles.java
│   └── ...                                │   └── ...
├── player/                                │
│   ├── Player.java                  →    │   ├── Player.java
│   └── tanks/                             │   └── tanks/
└── export/                                │
    └── ExportData.java              →    │   └── ExportData.java
```

#### Livrables Sprint 2.1
- [x] Tous les modèles de données adaptés
- [x] ApiClient fonctionnel avec OkHttp
- [x] Système de retry implémenté

#### Critères d'Acceptation
```
✓ Les modèles se sérialisent/désérialisent correctement en JSON
✓ Les requêtes API fonctionnent depuis Android
✓ Le retry fonctionne en cas d'erreur réseau
```

---

### Sprint 2.2 : Services de Scraping (Jours 8-9)

#### Objectifs
- Adapter les services de scraping pour Android
- Implémenter les callbacks de progression

#### Tâches

| # | Tâche | Durée | Priorité | Dépendances |
|---|-------|-------|----------|-------------|
| 2.2.1 | Créer `CombinedBattlesService.java` adapté Android | 2h | Critique | 2.1.3 |
| 2.2.2 | Créer `BattleDetailService.java` adapté Android | 2h | Critique | 2.1.3 |
| 2.2.3 | Créer `PlayerService.java` adapté Android | 2h | Critique | 2.1.3 |
| 2.2.4 | Définir l'interface `ScraperCallback` pour les événements | 1h | Haute | - |
| 2.2.5 | Implémenter les callbacks dans chaque service | 2h | Haute | 2.2.4 |
| 2.2.6 | Créer `ScraperEngine.java` orchestrant les 3 étapes | 3h | Critique | 2.2.1-3 |

#### Interface ScraperCallback

```java
public interface ScraperCallback {
    void onPhaseChanged(ScrapingPhase phase);
    void onProgressUpdate(int current, int total, String message);
    void onLog(LogLevel level, String message);
    void onError(Exception e, boolean fatal);
    void onDataCollected(ExportData partialData);
    void onComplete(ExportData finalData);
}
```

#### Livrables Sprint 2.2
- [x] 3 services de scraping fonctionnels
- [x] ScraperEngine orchestrant le flux
- [x] Callbacks de progression implémentés

#### Critères d'Acceptation
```
✓ Chaque service peut récupérer ses données depuis l'API
✓ Les callbacks sont appelés à chaque progression
✓ Le ScraperEngine exécute les 3 étapes dans l'ordre
```

---

### Sprint 2.3 : Système de Progression (Jour 10)

#### Objectifs
- Implémenter la sauvegarde/restauration de progression
- Gérer la reprise automatique

#### Tâches

| # | Tâche | Durée | Priorité | Dépendances |
|---|-------|-------|----------|-------------|
| 2.3.1 | Créer `ProgressState.java` avec toutes les variables | 2h | Critique | 2.2.6 |
| 2.3.2 | Créer `ProgressManager.java` pour la persistance | 3h | Critique | 2.3.1 |
| 2.3.3 | Implémenter la sauvegarde automatique périodique | 1h | Critique | 2.3.2 |
| 2.3.4 | Implémenter la restauration au démarrage | 1h | Critique | 2.3.2 |
| 2.3.5 | Créer `ProgressValidator.java` pour la validation | 1h | Haute | 2.3.2 |
| 2.3.6 | Intégrer le système de progression dans ScraperEngine | 2h | Critique | 2.3.2 |

#### Livrables Sprint 2.3
- [x] ProgressState complet avec toutes les variables
- [x] ProgressManager avec sauvegarde/restauration
- [x] Validation de l'intégrité des données

#### Critères d'Acceptation
```
✓ La progression est sauvegardée toutes les N itérations
✓ Le scraping reprend exactement là où il s'est arrêté
✓ Les données corrompues sont détectées
✓ Aucune donnée n'est perdue en cas d'arrêt inattendu
```

---

## 🎨 PHASE 3 : Interface Utilisateur & Fonctionnalités
### 🗓️ Semaine 3 (Jours 11-15)

Cette phase implémente l'interface utilisateur et les fonctionnalités avancées.

---

### Sprint 3.1 : Interface Principale (Jours 11-12)

#### Objectifs
- Créer l'écran principal avec les contrôles
- Afficher la progression en temps réel

#### Tâches

| # | Tâche | Durée | Priorité | Dépendances |
|---|-------|-------|----------|-------------|
| 3.1.1 | Créer le layout `fragment_main.xml` selon les maquettes | 2h | Haute | - |
| 3.1.2 | Implémenter `MainFragment.java` | 2h | Haute | 3.1.1 |
| 3.1.3 | Créer `ScraperViewModel.java` avec LiveData | 2h | Haute | Phase 2 |
| 3.1.4 | Implémenter les 3 barres de progression par étape | 2h | Haute | 3.1.2 |
| 3.1.5 | Connecter les boutons Start/Stop au service | 2h | Haute | 3.1.2, 1.2.5 |
| 3.1.6 | Afficher les statistiques en temps réel | 1h | Moyenne | 3.1.3 |
| 3.1.7 | Gérer l'état de l'UI selon l'état du scraping | 2h | Haute | 3.1.3 |

#### Layout fragment_main.xml (Structure)

```xml
<androidx.constraintlayout.widget.ConstraintLayout>
    <!-- État et temps -->
    <com.google.android.material.card.MaterialCardView>
        <TextView android:id="@+id/tvStatus" />
        <TextView android:id="@+id/tvElapsedTime" />
    </com.google.android.material.card.MaterialCardView>
    
    <!-- Progression Étape 1 -->
    <TextView android:text="Étape 1: CombinedBattles" />
    <ProgressBar android:id="@+id/progressStep1" style="@style/Widget.AppCompat.ProgressBar.Horizontal" />
    <TextView android:id="@+id/tvStep1Details" />
    
    <!-- Progression Étape 2 -->
    <TextView android:text="Étape 2: BattleDetails" />
    <ProgressBar android:id="@+id/progressStep2" style="@style/Widget.AppCompat.ProgressBar.Horizontal" />
    <TextView android:id="@+id/tvStep2Details" />
    
    <!-- Progression Étape 3 -->
    <TextView android:text="Étape 3: Players" />
    <ProgressBar android:id="@+id/progressStep3" style="@style/Widget.AppCompat.ProgressBar.Horizontal" />
    <TextView android:id="@+id/tvStep3Details" />
    
    <!-- Boutons -->
    <Button android:id="@+id/btnStart" />
    <Button android:id="@+id/btnStop" />
    
    <!-- Actions -->
    <Button android:id="@+id/btnViewLogs" />
    <Button android:id="@+id/btnExport" />
</androidx.constraintlayout.widget.ConstraintLayout>
```

#### Livrables Sprint 3.1
- [x] Écran principal fonctionnel
- [x] Barres de progression mises à jour en temps réel
- [x] Boutons Start/Stop opérationnels

#### Critères d'Acceptation
```
✓ L'UI reflète l'état du scraping en temps réel
✓ Les 3 barres de progression s'actualisent correctement
✓ Start démarre le service, Stop l'arrête proprement
```

---

### Sprint 3.2 : Écrans Secondaires (Jours 13-14)

#### Objectifs
- Créer l'écran des logs
- Créer l'écran des paramètres

#### Tâches

| # | Tâche | Durée | Priorité | Dépendances |
|---|-------|-------|----------|-------------|
| 3.2.1 | Créer `fragment_logs.xml` avec RecyclerView | 1h | Haute | - |
| 3.2.2 | Créer `LogAdapter.java` pour afficher les logs | 2h | Haute | 3.2.1 |
| 3.2.3 | Implémenter `LogsFragment.java` avec auto-scroll | 2h | Haute | 3.2.2 |
| 3.2.4 | Créer `LogManager.java` pour stocker les logs en mémoire | 1h | Haute | - |
| 3.2.5 | Créer `fragment_settings.xml` selon la maquette | 2h | Moyenne | - |
| 3.2.6 | Implémenter `SettingsFragment.java` | 3h | Moyenne | 3.2.5 |
| 3.2.7 | Connecter les paramètres à PreferencesManager | 1h | Moyenne | 3.2.6, 1.1.7 |
| 3.2.8 | Implémenter la navigation entre fragments | 1h | Haute | 3.2.3, 3.2.6 |

#### Paramètres à Implémenter

| Paramètre | Type | Valeur par défaut | Clé SharedPreferences |
|-----------|------|-------------------|----------------------|
| Délai entre requêtes | SeekBar (100-2000ms) | 500ms | `pref_request_delay` |
| Timeout connexion | SeekBar (10-60s) | 30s | `pref_timeout` |
| Nombre de joueurs | EditText (number) | 100 | `pref_players_count` |
| ID joueur initial | EditText | 532440001 | `pref_initial_player` |
| Fréquence sauvegarde | RadioGroup (5/10/20) | 5 | `pref_save_frequency` |
| Export automatique | Switch | true | `pref_auto_export` |
| Notif. de fin | Switch | true | `pref_notif_complete` |
| Notif. d'erreur | Switch | true | `pref_notif_error` |
| Notif. d'étape | Switch | false | `pref_notif_phase` |

#### Livrables Sprint 3.2
- [x] Écran des logs fonctionnel avec auto-scroll
- [x] Écran des paramètres complet
- [x] Navigation entre les 3 écrans

#### Critères d'Acceptation
```
✓ Les logs s'affichent en temps réel avec coloration par niveau
✓ Tous les paramètres sont modifiables et persistés
✓ La navigation fonctionne via bottom navigation
```

---

### Sprint 3.3 : Notifications & Export (Jour 15)

#### Objectifs
- Implémenter les notifications avancées
- Créer le système d'export

#### Tâches

| # | Tâche | Durée | Priorité | Dépendances |
|---|-------|-------|----------|-------------|
| 3.3.1 | Implémenter les notifications de fin d'étape | 1h | Moyenne | 1.2.3 |
| 3.3.2 | Implémenter la notification de fin de scraping | 1h | Haute | 1.2.3 |
| 3.3.3 | Implémenter les notifications d'erreur | 1h | Haute | 1.2.3 |
| 3.3.4 | Créer `ExportManager.java` pour l'export JSON | 2h | Haute | - |
| 3.3.5 | Implémenter l'export manuel depuis l'UI | 1h | Haute | 3.3.4 |
| 3.3.6 | Implémenter l'export automatique périodique | 1h | Critique | 3.3.4 |
| 3.3.7 | Ajouter le partage de fichier via Intent | 1h | Basse | 3.3.4 |

#### Format d'Export Final

```java
public class ExportManager {
    public static File exportToJson(Context context, ExportData data) {
        // Format: export_data_YYYYMMDD_HHmmss.json
        String filename = "export_data_" + 
            new SimpleDateFormat("yyyyMMdd_HHmmss").format(new Date()) + ".json";
        
        File exportDir = new File(context.getExternalFilesDir(null), "exports");
        exportDir.mkdirs();
        
        File exportFile = new File(exportDir, filename);
        
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        String json = gson.toJson(data);
        
        // Écriture du fichier...
        return exportFile;
    }
}
```

#### Livrables Sprint 3.3
- [x] Notifications configurables
- [x] Export JSON fonctionnel
- [x] Export automatique actif

#### Critères d'Acceptation
```
✓ Les notifications respectent les préférences utilisateur
✓ L'export génère un fichier JSON valide
✓ L'export automatique se déclenche toutes les 50 batailles
```

---

### Sprint 4.1 : Consultation des Exports (Jour 16)

#### Objectifs
- Ajouter un écran pour consulter les fichiers exportés (historique)
- Implémenter une liste optimisée (pas de parsing JSON, chargement asynchrone)
- Ajouter une page de détail pour consulter le contenu d'un export (métadonnées + visualisation JSON)
- Permettre de replier/déplier des rubriques du JSON (comme dans un IDE)

#### Tâches

| # | Tâche | Durée | Priorité | Dépendances |
|---|-------|-------|----------|-------------|
| 4.1.1 | Définir un modèle `ExportFileItem` (nom, date, taille, chemin) | 30min | Moyenne | - |
| 4.1.2 | Créer `fragment_exports.xml` (RecyclerView + état vide) | 1h | Haute | - |
| 4.1.3 | Créer `ExportListAdapter.java` (DiffUtil + IDs stables) | 2h | Haute | 4.1.2 |
| 4.1.4 | Implémenter `ExportsFragment.java` (chargement asynchrone) | 2h | Haute | 4.1.2 |
| 4.1.5 | Ajouter une méthode `ExportManager.listExports(...)` (scan répertoire + métadonnées) | 1h | Haute | 3.3.4 |
| 4.1.6 | Ajouter la navigation vers l'écran “Exports” depuis le bouton Export | 1h | Haute | 4.1.4 |
| 4.1.7 | Ajouter action “Partager”/“Ouvrir” pour un export (Intent) | 1h | Moyenne | 3.3.7 |
| 4.1.8 | Créer `fragment_export_detail.xml` (header métadonnées + zone contenu) | 1h | Haute | - |
| 4.1.9 | Implémenter `ExportDetailFragment.java` (lecture fichier asynchrone) | 2h | Haute | 4.1.8 |
| 4.1.10 | Définir un modèle de nœud JSON (type, clé, valeur courte, profondeur, état replié) | 1h | Haute | - |
| 4.1.11 | Implémenter un parser JSON streaming vers nœuds (sans bloquer l'UI) | 3h | Haute | 4.1.10 |
| 4.1.12 | Créer `JsonTreeAdapter.java` (RecyclerView) avec expand/collapse par rubrique | 3h | Haute | 4.1.10 |
| 4.1.13 | Ajouter l'interaction UI (tap pour replier/déplier, indicateur chevron) | 1h | Haute | 4.1.12 |

#### Notes de Performance (Gros Fichiers)

```
✓ Ne jamais charger / parser le JSON pour afficher la liste
✓ Lire uniquement les métadonnées fichier (nom, taille, lastModified)
✓ Chargement hors UI thread (Executor/Handler, ViewModel, etc.)
✓ Adapter RecyclerView avec DiffUtil pour limiter les rebinds
✓ Pour l'écran détail : parsing streaming et construction progressive de la liste de nœuds
✓ Repli/dépli : ne rebind que la plage impactée (DiffUtil / payloads)
```

#### Livrables Sprint 4.1
- [x] Écran “Exports” (historique) fonctionnel
- [x] Liste fluide et stable même avec des exports volumineux
- [x] Écran détail export (métadonnées + contenu JSON)
- [x] Visualisation JSON avec rubriques repliables

#### Critères d'Acceptation
```
✓ L'écran affiche la liste des exports présents dans /exports
✓ Aucun ANR : le scan des fichiers se fait en arrière-plan
✓ L'ouverture de l'écran ne parse pas le contenu JSON
✓ En ouvrant un export, l'écran détail affiche : nom, date, type, taille, chemin
✓ Le contenu JSON est consultable avec repli/dépli des rubriques (objets/arrays)
```

---

## 🚀 PHASE 4 : Finalisation & Release
### 🗓️ Semaine 4 (Jours 16-21)

Cette phase finalise l'application avec les corrections et optimisations.

---

### Sprint 4.2 : Corrections & Stabilisation (Jours 17-19)

#### Objectifs
- Corriger les bugs identifiés
- Améliorer la stabilité

#### Tâches

| # | Tâche | Durée | Priorité | Dépendances |
|---|-------|-------|----------|-------------|
| 4.2.1 | Tester le scénario de perte de connexion | 2h | Critique | - |
| 4.2.2 | Tester le scénario de fermeture forcée de l'app | 2h | Critique | - |
| 4.2.3 | Tester le scénario de redémarrage de l'appareil | 2h | Critique | - |
| 4.2.4 | Corriger les fuites mémoire éventuelles | 2h | Haute | - |
| 4.2.5 | Optimiser la consommation batterie | 2h | Haute | - |
| 4.2.6 | Gérer les cas limites (espace disque, etc.) | 2h | Moyenne | - |
| 4.2.7 | Améliorer la gestion des erreurs API | 2h | Haute | - |

#### Scénarios de Test Critiques

```
┌─────────────────────────────────────────────────────────────────┐
│                    MATRICE DE TESTS CRITIQUES                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Scénario                          │ Résultat Attendu           │
│  ─────────────────────────────────────────────────────────────  │
│  Fermer l'app pendant scraping     │ Service continue           │
│  Kill app via task manager         │ Progression sauvegardée    │
│  Perte WiFi pendant scraping       │ Pause auto, notif affichée │
│  Retour WiFi après perte           │ Reprise automatique        │
│  Reboot appareil                   │ Reprise après boot         │
│  Batterie faible                   │ Notification + sauvegarde  │
│  Espace disque insuffisant         │ Alerte utilisateur         │
│  API renvoie erreur 500            │ Retry puis skip si échec   │
│  API renvoie JSON invalide         │ Log erreur, continuer      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Livrables Sprint 4.2
- [x] Tous les scénarios critiques validés
- [x] Bugs corrigés
- [x] Application stable

---

### Sprint 4.3 : Optimisation & Documentation (Jours 20-21)

#### Objectifs
- Optimiser les performances
- Documenter le code et l'utilisation

#### Tâches

| # | Tâche | Durée | Priorité | Dépendances |
|---|-------|-------|----------|-------------|
| 4.3.1 | Optimiser la sérialisation JSON | 1h | Moyenne | - |
| 4.3.2 | Réduire la consommation mémoire | 2h | Moyenne | - |
| 4.3.3 | Ajouter ProGuard rules pour la minification | 1h | Moyenne | - |
| 4.3.4 | Écrire les commentaires Javadoc | 2h | Moyenne | - |
| 4.3.5 | Créer le README.md du projet mobile | 2h | Haute | - |
| 4.3.6 | Documenter les paramètres de configuration | 1h | Moyenne | - |
| 4.3.7 | Générer l'APK de debug | 30min | Haute | - |
| 4.3.8 | Générer l'APK de release signé | 1h | Haute | 4.3.7 |
| 4.3.9 | Tester l'APK release sur plusieurs appareils | 2h | Haute | 4.3.8 |

#### Livrables Sprint 4.3
- [x] Code optimisé et documenté
- [x] README.md complet
- [x] APK debug et release générés

---

## 📊 Récapitulatif des Livrables par Phase

| Phase | Sprint | Livrables Clés | Jalon |
|-------|--------|----------------|-------|
| **Phase 1** | 1.1 | Projet configuré, PreferencesManager | - |
| | 1.2 | Foreground Service, Notifications, Receivers | **M1: Service de base** |
| **Phase 2** | 2.1 | Modèles adaptés, ApiClient OkHttp | - |
| | 2.2 | Services de scraping, ScraperEngine | - |
| | 2.3 | Système de progression complet | **M2: Scraper fonctionnel** |
| **Phase 3** | 3.1 | Écran principal avec progression | - |
| | 3.2 | Écrans logs et paramètres | - |
| | 3.3 | Notifications, Export JSON | **M3: App complète** |
| **Phase 4** | 4.1 | Écran consultation exports (historique) | - |
| | 4.2 | Bugs corrigés, stabilité | - |
| | 4.3 | APK release, documentation | **M4: Version 1.0** |

---

## 📋 Checklist de Validation Finale

### Fonctionnalités Critiques

- [ ] **F04** : Reprise automatique après interruption
- [ ] **F21** : Exécution en arrière-plan
- [ ] **F22** : Survie au mode veille
- [ ] **F23** : Reprise après redémarrage
- [ ] **F24** : Sauvegarde anti-perte (export régulier)

### Fonctionnalités Hautes

- [ ] **F01** : Démarrer le scraping
- [ ] **F02** : Arrêter le scraping
- [ ] **F05** : Barre de progression globale
- [ ] **F06** : Progression par étape (3 barres)
- [ ] **F07** : Logs en temps réel
- [ ] **F10** : Configuration nombre de joueurs
- [ ] **F13** : Notification persistante
- [ ] **F15** : Notification de fin
- [ ] **F16** : Notification d'erreur
- [ ] **F17** : Export JSON
- [ ] **F18** : Export automatique régulier

### Performance

- [ ] Consommation mémoire < 100 MB
- [ ] Temps de démarrage < 2s
- [ ] Réponse UI < 100ms

### Qualité

- [ ] Aucun crash lors des tests
- [ ] Logs clairs et informatifs
- [ ] Gestion gracieuse des erreurs

---

## 🔧 Outils & Ressources

### Outils de Développement

| Outil | Usage |
|-------|-------|
| Android Studio | IDE principal |
| Android Profiler | Analyse mémoire/CPU |
| Layout Inspector | Debug UI |
| Logcat | Analyse des logs |

### Ressources Utiles

- [Documentation Android Foreground Services](https://developer.android.com/guide/components/foreground-services)
- [Documentation OkHttp](https://square.github.io/okhttp/)
- [Documentation Gson](https://github.com/google/gson)
- [Android Architecture Components](https://developer.android.com/topic/libraries/architecture)

---

## 📝 Notes de Version

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | - | Version initiale |

---

*Document créé le 2 janvier 2026*
