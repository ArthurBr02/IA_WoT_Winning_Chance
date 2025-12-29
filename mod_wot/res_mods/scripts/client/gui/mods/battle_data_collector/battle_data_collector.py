# -*- coding: utf-8 -*-
"""
Module principal de collecte des données de bataille
"""

import BigWorld
import json
from datetime import datetime
from PlayerEvents import g_playerEvents
try:
    from .data_exporter import DataExporter
    from .stats_fetcher import StatsFetcher
    from . import config
except Exception:
    from data_exporter import DataExporter
    from stats_fetcher import StatsFetcher
    import config


class BattleDataCollector(object):
    """Collecteur principal des données de bataille"""
    
    def __init__(self):
        print("[BattleDataCollector] Construction du collecteur...")
        
        try:
            self.exporter = DataExporter()
            print("[BattleDataCollector] DataExporter initialise")
            
            self.stats_fetcher = StatsFetcher() if config.COLLECT_PLAYER_STATS else None
            if self.stats_fetcher:
                print("[BattleDataCollector] StatsFetcher initialise")
            else:
                print("[BattleDataCollector] StatsFetcher desactive")
            
            self._battleData = None
            self._pendingStats = False
            self._collectCallbackPending = False
            
            self._registerEvents()
            print("[BattleDataCollector] Collecteur initialise avec succes")
            
        except Exception as e:
            print("[BattleDataCollector] ERREUR dans __init__:")
            print("[BattleDataCollector] {}".format(str(e)))
            import traceback
            traceback.print_exc()
    
    def _registerEvents(self):
        """Enregistre les callbacks sur les événements de bataille"""
        try:
            print("[BattleDataCollector] Enregistrement des evenements...")
            g_playerEvents.onAvatarBecomePlayer += self._onBattleStart
            g_playerEvents.onAvatarBecomeNonPlayer += self._onBattleEnd
            print("[BattleDataCollector] Evenements enregistres")
        except Exception as e:
            print("[BattleDataCollector] ERREUR lors de l'enregistrement des evenements:")
            print("[BattleDataCollector] {}".format(str(e)))
            import traceback
            traceback.print_exc()
    
    def destroy(self):
        """Désenregistre les événements"""
        g_playerEvents.onAvatarBecomePlayer -= self._onBattleStart
        g_playerEvents.onAvatarBecomeNonPlayer -= self._onBattleEnd
    
    def _onBattleStart(self):
        """Appelé quand le joueur entre dans une bataille"""
        try:
            arena = BigWorld.player().arena
            if arena is None:
                print("[BattleDataCollector] Arena non disponible")
                return
            
            print("[BattleDataCollector] Début de collecte des données")

            # La liste des véhicules peut être vide juste après l'événement.
            # On réessaie quelques fois avec un délai court.
            self._collectBattleDataWithRetry(arena, retries=10, delay=0.5)
        
        except Exception as e:
            print("[BattleDataCollector] Erreur _onBattleStart: {}".format(str(e)))

    def _collectBattleDataWithRetry(self, arena, retries, delay):
        try:
            teams = self._getTeamsInfo(arena)
            count = 0
            try:
                count = len(teams.get('spawn_1', [])) + len(teams.get('spawn_2', []))
            except Exception:
                count = 0

            if count == 0 and retries > 0:
                if not self._collectCallbackPending:
                    self._collectCallbackPending = True

                    def _cb():
                        self._collectCallbackPending = False
                        self._collectBattleDataWithRetry(arena, retries=retries - 1, delay=delay)

                    BigWorld.callback(delay, _cb)
                return

            map_info = self._getMapInfo(arena)
            map_value = map_info.get('geometry_name') or map_info.get('name') or 'unknown'

            # Collecter les données de base (avec équipes)
            self._battleData = {
                'timestamp': datetime.now().isoformat(),
                'map': map_info,
                'teams': teams
            }

            # Normaliser les joueurs: ajouter spawn + stats (schema stable)
            self._hydratePlayers(map_value)

            player_names = self._getAllPlayerNames()

            # Prédiction de victoire via l'API (ne récupère pas les stats côté mod)
            try:
                if getattr(config, 'COLLECT_PREDICTION', False) and self.stats_fetcher and player_names:
                    self.stats_fetcher.fetch_prediction_async(player_names)
            except Exception:
                pass

            # Récupérer les statistiques des joueurs si activé
            if config.COLLECT_PLAYER_STATS and self.stats_fetcher and player_names:
                print("[BattleDataCollector] Récupération stats pour {} joueurs".format(len(player_names)))
                self._pendingStats = True
                self.stats_fetcher.fetch_player_stats_async(player_names, self._onStatsReceived)
            else:
                # Exporter directement sans stats
                self.exporter.export(self._battleData)

        except Exception as e:
            print("[BattleDataCollector] Erreur _collectBattleDataWithRetry: {}".format(str(e)))

    def _defaultStats(self):
        # Schéma stable: toujours les mêmes clés
        return {
            'battles': None,
            'overallWN8': None,
            'overallWNX': None,
            'winrate': None,
            'dpg': None,
            'assist': None,
            'frags': None,
            'survival': None,
            'spots': None,
            'cap': None,
            'def': None,
            'xp': None,
            'kd': None
        }

    def _hydratePlayers(self, map_value):
        """Ajoute spawn + stats (schema stable) dans teams."""
        try:
            for spawn_id, team_key in ((1, 'spawn_1'), (2, 'spawn_2')):
                players = []
                try:
                    players = self._battleData.get('teams', {}).get(team_key, [])
                except Exception:
                    players = []

                for p in players:
                    try:
                        p['spawn'] = spawn_id
                        # stats doit être un dict (pas None) avec les clés attendues
                        if not isinstance(p.get('stats'), dict):
                            p['stats'] = self._defaultStats()
                        else:
                            # compléter si incomplet
                            d = self._defaultStats()
                            d.update(p['stats'])
                            p['stats'] = d
                    except Exception:
                        continue
        except Exception:
            pass
    
    def _getMapInfo(self, arena):
        """Récupère les informations de la map"""
        try:
            arenaType = arena.arenaType
            return {
                'id': arenaType.id,
                'name': arenaType.name,
                'geometry_name': arenaType.geometryName,
                'game_mode': arena.guiType
            }
        except Exception as e:
            print("[BattleDataCollector] Erreur _getMapInfo: {}".format(str(e)))
            return {'name': 'Unknown', 'id': -1}
    
    def _getTeamsInfo(self, arena):
        """Récupère les informations des deux équipes"""
        try:
            team1 = []
            team2 = []
            
            for vehicleID, vehicleInfo in arena.vehicles.items():
                try:
                    # vehicleInfo est généralement un dict, mais certains champs (vehicleType)
                    # peuvent être des objets (VehicleDescriptor / VehicleTypeDescriptor).
                    if hasattr(vehicleInfo, 'get'):
                        v_team = vehicleInfo.get('team', 0)
                        v_name = vehicleInfo.get('name', 'Unknown')
                        v_clan = vehicleInfo.get('clanAbbrev', '')
                        v_alive = vehicleInfo.get('isAlive', True)
                        v_type = vehicleInfo.get('vehicleType', None)
                    else:
                        v_team = getattr(vehicleInfo, 'team', 0)
                        v_name = getattr(vehicleInfo, 'name', 'Unknown')
                        v_clan = getattr(vehicleInfo, 'clanAbbrev', '')
                        v_alive = getattr(vehicleInfo, 'isAlive', True)
                        v_type = getattr(vehicleInfo, 'vehicleType', None)

                    tank_name, tank_tier, tank_class = self._extractVehicleTypeInfo(v_type)

                    playerData = {
                        'name': v_name,
                        'vehicle_id': vehicleID,
                        'tank': tank_name,
                        'tank_tier': tank_tier,
                        'tank_type': tank_class,
                        'clan': v_clan,
                        'is_alive': v_alive
                    }

                    # team == 1 ou 2
                    if v_team == 1:
                        team1.append(playerData)
                    elif v_team == 2:
                        team2.append(playerData)

                except Exception as e:
                    print("[BattleDataCollector] Erreur parsing vehicle {}: {}".format(vehicleID, str(e)))
            
            return {
                'spawn_1': team1,  # Équipe au spawn 1
                'spawn_2': team2   # Équipe au spawn 2
            }
        except Exception as e:
            print("[BattleDataCollector] Erreur _getTeamsInfo: {}".format(str(e)))
            return {'spawn_1': [], 'spawn_2': []}

    def _extractVehicleTypeInfo(self, vehicle_type):
        """Extrait (name, tier, classTag) depuis un dict OU un descripteur WoT."""
        tank_name = 'Unknown'
        tank_tier = 0
        tank_class = 'unknown'

        try:
            if vehicle_type is None:
                return tank_name, tank_tier, tank_class

            # Cas: dict
            if hasattr(vehicle_type, 'get'):
                tank_name = vehicle_type.get('name', tank_name)
                tank_tier = vehicle_type.get('level', tank_tier)
                tank_class = vehicle_type.get('classTag', tank_class)
                return tank_name, tank_tier, tank_class

            # Cas: descripteur (VehicleTypeDescriptor)
            name_attr = getattr(vehicle_type, 'name', None)
            level_attr = getattr(vehicle_type, 'level', None)
            class_attr = getattr(vehicle_type, 'classTag', None)

            if name_attr is not None:
                tank_name = name_attr
            if level_attr is not None:
                tank_tier = level_attr
            if class_attr is not None:
                tank_class = class_attr

            # Cas: VehicleDescriptor (possède parfois .type)
            if tank_name == 'Unknown' or tank_tier == 0 or tank_class == 'unknown':
                inner = getattr(vehicle_type, 'type', None)
                if inner is not None:
                    if tank_name == 'Unknown':
                        tank_name = getattr(inner, 'name', tank_name)
                    if tank_tier == 0:
                        tank_tier = getattr(inner, 'level', tank_tier)
                    if tank_class == 'unknown':
                        tank_class = getattr(inner, 'classTag', tank_class)

        except Exception:
            pass

        return tank_name, tank_tier, tank_class
    
    def _getAllPlayerNames(self):
        """Extrait tous les noms de joueurs des deux équipes"""
        names = []
        if self._battleData and 'teams' in self._battleData:
            for player in self._battleData['teams']['spawn_1']:
                names.append(player['name'])
            for player in self._battleData['teams']['spawn_2']:
                names.append(player['name'])
        return names
    
    def _onStatsReceived(self, stats_dict):
        """
        Callback appelé quand les stats sont récupérées
        
        Args:
            stats_dict: dict {player_name: stats}
        """
        try:
            print("[BattleDataCollector] Stats reçues pour {} joueurs".format(len(stats_dict)))
            
            # Ajouter les stats aux données des joueurs
            if self._battleData and 'teams' in self._battleData:
                for player in self._battleData['teams']['spawn_1']:
                    s = stats_dict.get(player.get('name'))
                    d = self._defaultStats()
                    if isinstance(s, dict):
                        d.update(s)
                    player['stats'] = d
                
                for player in self._battleData['teams']['spawn_2']:
                    s = stats_dict.get(player.get('name'))
                    d = self._defaultStats()
                    if isinstance(s, dict):
                        d.update(s)
                    player['stats'] = d

            # Recomposer les records plats avec les stats mises à jour
            try:
                map_info = self._battleData.get('map', {})
                map_value = map_info.get('geometry_name') or map_info.get('name') or 'unknown'
                self._hydratePlayers(map_value)
            except Exception:
                pass
            
            # Exporter les données complètes
            self.exporter.export(self._battleData)
            self._pendingStats = False
        
        except Exception as e:
            print("[BattleDataCollector] Erreur _onStatsReceived: {}".format(str(e)))
    
    def _onBattleEnd(self):
        """Appelé quand la bataille se termine"""
        print("[BattleDataCollector] Fin de bataille")
        self._battleData = None
        self._pendingStats = False
