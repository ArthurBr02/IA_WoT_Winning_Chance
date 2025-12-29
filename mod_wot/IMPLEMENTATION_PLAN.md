Plan d'Implémentation : Mod WoT - Collecteur de Données de Bataille
Description du Projet
Création d'un mod World of Tanks permettant de récupérer automatiquement les informations suivantes au début de chaque bataille :

Noms des joueurs de chaque équipe
Points de spawn (équipe 1 ou 2)
Nom de la map jouée
Ces données seront exportées au format JSON pour alimenter un modèle d'IA de prédiction des chances de victoire.

Architecture Technique
Environnement de Modding WoT
World of Tanks utilise le moteur BigWorld et ses mods sont écrits en Python 2.7. Les mods sont chargés depuis :

<WoT_Installation>/mods/<version>/ (fichiers .wotmod)
<WoT_Installation>/res_mods/<version>/ (scripts Python)
Structure d'un Mod WoT
mod_battle_data_collector/
├── res_mods/
│   └── <version>/
│       └── scripts/
│           └── client/
│               └── gui/
│                   └── mods/
│                       └── mod_battle_data_collector/
│                           ├── __init__.py
│                           ├── battle_data_collector.py
│                           └── data_exporter.py
├── meta.xml
└── README.md
Proposed Changes
Phase 1 : Configuration et Structure de Base
[NEW] 
meta.xml
Fichier de métadonnées du mod requis par WoT :

<root>
    <id>mod_battle_data_collector</id>
    <version>1.0.0</version>
    <name>Battle Data Collector</name>
    <description>Collecte les données de bataille pour l'IA de prédiction</description>
</root>
[NEW] 
init
.py
Point d'entrée du mod, enregistrement des hooks sur les événements de bataille.

# -*- coding: utf-8 -*-
"""
Battle Data Collector Mod
Collecte les noms de joueurs, spawns et maps
"""
from battle_data_collector import BattleDataCollector
# Instance globale
g_battleDataCollector = None
def init():
    """Initialisation du mod au chargement"""
    global g_battleDataCollector
    g_battleDataCollector = BattleDataCollector()
    print("[BattleDataCollector] Mod chargé avec succès")
Phase 2 : Collecte des Données de Bataille
[NEW] 
battle_data_collector.py
Module principal qui intercepte les événements de bataille et collecte les données.

API BigWorld utilisées :

Fonction/Module	Description
BigWorld.player()	Récupère l'objet du joueur local
Avatar.arena	Accès aux informations de l'arène (bataille)
arena.arenaType	Informations sur la map (nom, ID)
arena.vehicles	Dictionnaire de tous les véhicules/joueurs
PlayerEvents	Événements du joueur (entrée en bataille, etc.)
Structure de la classe :

# -*- coding: utf-8 -*-
import BigWorld
import json
from datetime import datetime
from PlayerEvents import g_playerEvents
from data_exporter import DataExporter
class BattleDataCollector(object):
    
    def __init__(self):
        self.exporter = DataExporter()
        self._battleData = None
        self._registerEvents()
    
    def _registerEvents(self):
        """Enregistre les callbacks sur les événements de bataille"""
        g_playerEvents.onAvatarBecomePlayer += self._onBattleStart
        g_playerEvents.onAvatarBecomeNonPlayer += self._onBattleEnd
    
    def _onBattleStart(self):
        """Appelé quand le joueur entre dans une bataille"""
        arena = BigWorld.player().arena
        if arena is None:
            return
        
        self._battleData = {
            'timestamp': datetime.now().isoformat(),
            'map': self._getMapInfo(arena),
            'teams': self._getTeamsInfo(arena)
        }
        
        self.exporter.export(self._battleData)
    
    def _getMapInfo(self, arena):
        """Récupère les informations de la map"""
        arenaType = arena.arenaType
        return {
            'id': arenaType.id,
            'name': arenaType.name,
            'geometry_name': arenaType.geometryName
        }
    
    def _getTeamsInfo(self, arena):
        """Récupère les informations des deux équipes"""
        team1 = []
        team2 = []
        
        for vehicleID, vehicleInfo in arena.vehicles.items():
            playerData = {
                'name': vehicleInfo['name'],
                'vehicle_id': vehicleID,
                'tank': vehicleInfo.get('vehicleType', {}).get('name', 'Unknown'),
                'clan': vehicleInfo.get('clanAbbrev', '')
            }
            
            # team == 1 ou 2
            if vehicleInfo['team'] == 1:
                team1.append(playerData)
            else:
                team2.append(playerData)
        
        return {
            'spawn_1': team1,  # Équipe au spawn 1
            'spawn_2': team2   # Équipe au spawn 2
        }
    
    def _onBattleEnd(self):
        """Appelé quand la bataille se termine"""
        self._battleData = None
Phase 3 : Export des Données
[NEW] 
data_exporter.py
Module d'export des données au format JSON.

# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime
class DataExporter(object):
    
    def __init__(self, output_dir=None):
        if output_dir is None:
            # Dossier par défaut dans le répertoire WoT
            self.output_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '..', '..', '..', '..', '..', 'battle_data'
            )
        else:
            self.output_dir = output_dir
        
        self._ensureOutputDir()
    
    def _ensureOutputDir(self):
        """Crée le dossier de sortie si nécessaire"""
        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir)
            except OSError:
                print("[BattleDataCollector] Erreur création dossier: {}".format(
                    self.output_dir
                ))
    
    def export(self, battle_data):
        """Exporte les données de bataille en JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = 'battle_{}.json'.format(timestamp)
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(battle_data, f, indent=2, ensure_ascii=False)
            print("[BattleDataCollector] Données exportées: {}".format(filepath))
        except IOError as e:
            print("[BattleDataCollector] Erreur export: {}".format(str(e)))
        
        return filepath
Phase 4 : Packaging du Mod
[NEW] 
build.py
Script de build pour créer le fichier .wotmod distribuable.

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de build pour créer le fichier .wotmod
"""
import zipfile
import os
import shutil
MOD_NAME = 'mod_battle_data_collector'
VERSION = '1.0.0'
WOT_VERSION = '1.28.0.0'  # À adapter selon la version du jeu
def build():
    output_name = '{}_{}.wotmod'.format(MOD_NAME, VERSION)
    
    with zipfile.ZipFile(output_name, 'w', zipfile.ZIP_DEFLATED) as wotmod:
        # Ajouter meta.xml
        wotmod.write('meta.xml', 'meta.xml')
        
        # Ajouter les scripts Python
        scripts_path = 'res_mods/scripts/client/gui/mods/{}'.format(MOD_NAME)
        for root, dirs, files in os.walk(scripts_path):
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    arc_path = full_path.replace('res_mods/', 'res/')
                    wotmod.write(full_path, arc_path)
    
    print("Build terminé: {}".format(output_name))
if __name__ == '__main__':
    build()
Format des Données de Sortie
Exemple de fichier JSON généré (battle_20241229_154532.json) :

{
  "timestamp": "2024-12-29T15:45:32.123456",
  "map": {
    "id": 15,
    "name": "Prokhorovka",
    "geometry_name": "15_komarin"
  },
  "teams": {
    "spawn_1": [
      {
        "name": "Player1",
        "vehicle_id": 123456,
        "tank": "IS-7",
        "clan": "ABC"
      }
      // ... 14 autres joueurs
    ],
    "spawn_2": [
      {
        "name": "Player16",
        "vehicle_id": 789012,
        "tank": "Obj. 140",
        "clan": "XYZ"
      }
      // ... 14 autres joueurs
    ]
  }
}
Diagramme de Flux
Oui
Oui
Non
Non
Démarrage WoT
Chargement du Mod
Enregistrement des Event Handlers
Entrée en Bataille?
onAvatarBecomePlayer
Récupération arena.arenaType
Récupération arena.vehicles
Création structure BattleData
Export JSON
Fichier sauvegardé
Fin de Bataille?
onAvatarBecomeNonPlayer
Verification Plan
Tests Automatisés
CAUTION

Les tests automatisés pour les mods WoT sont limités car ils requièrent l'environnement BigWorld. Nous utiliserons des tests unitaires pour les composants isolés.

Test du DataExporter (hors environnement WoT)
# Depuis le dossier mod_wot/
python -m pytest tests/test_data_exporter.py -v
Fichier de test à créer : tests/test_data_exporter.py

import unittest
import os
import json
import tempfile
import shutil
# Mock minimal pour tester hors WoT
class TestDataExporter(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_export_creates_json_file(self):
        # Import local pour éviter les dépendances BigWorld
        import sys
        sys.path.insert(0, 'res_mods/scripts/client/gui/mods/mod_battle_data_collector')
        from data_exporter import DataExporter
        
        exporter = DataExporter(output_dir=self.test_dir)
        test_data = {
            'timestamp': '2024-12-29T15:00:00',
            'map': {'name': 'Test Map'},
            'teams': {'spawn_1': [], 'spawn_2': []}
        }
        
        filepath = exporter.export(test_data)
        
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, 'r') as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data['map']['name'], 'Test Map')
if __name__ == '__main__':
    unittest.main()
Tests Manuels
IMPORTANT

Ces tests doivent être effectués dans le jeu World of Tanks après installation du mod.

Test 1 : Installation du Mod
Copier le dossier res_mods/ dans <WoT_Installation>/res_mods/<version>/
Lancer World of Tanks
Vérifier dans python.log la présence de : [BattleDataCollector] Mod chargé avec succès
Test 2 : Collecte de Données en Bataille
Lancer une bataille (Random Battle ou Training Room)
Attendre le début de la bataille
Après la bataille, vérifier le dossier <WoT_Installation>/battle_data/
Ouvrir le fichier JSON généré et vérifier :
 Présence du champ map avec id, name, geometry_name
 Présence de teams.spawn_1 avec 15 joueurs
 Présence de teams.spawn_2 avec 15 joueurs
 Chaque joueur a les champs name, vehicle_id, tank
Test 3 : Vérification des Données
Comparer les noms de joueurs dans le JSON avec l'écran de chargement
Vérifier que tous les 30 joueurs sont présents
Confirmer que les équipes correspondent aux spawns (côté de la map)
User Review Required
IMPORTANT

Points nécessitant votre validation :

Version de WoT ciblée : Quelle version du jeu utilisez-vous ? (ex: 1.28.0.0)

Cela affecte le chemin d'installation et potentiellement l'API disponible
Chemin d'installation personnalisé : Où est installé votre WoT ?

Défaut : C:\Games\World_of_Tanks_EU\
Données additionnelles souhaitées : Voulez-vous collecter d'autres informations ?

Stats des joueurs (WN8, taux de victoire) via API externe
Type de bataille (Random, Ranked, etc.)
Niveau des chars
Format de sortie : Le JSON est-il adapté ou préférez-vous un autre format ?

CSV pour analyse directe
SQLite pour stockage local
Prochaines Étapes
Après validation, l'implémentation suivra cet ordre :

Création de la structure de dossiers
Implémentation du meta.xml
Implémentation du __init__.py
Implémentation du battle_data_collector.py
Implémentation du data_exporter.py
Création des tests unitaires
Script de build .wotmod
Documentation d'installation