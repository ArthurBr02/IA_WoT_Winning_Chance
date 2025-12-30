# -*- coding: utf-8 -*-
"""
Module principal de collecte des données de bataille
"""

import BigWorld
import json
from datetime import datetime
from PlayerEvents import g_playerEvents

# NOTE: le module GUI n'est pas forcément importable au chargement.
# On l'importe de façon "lazy" au moment de créer l'overlay.
GUI = None

unicode = globals().get('unicode', str)
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
            self.exporter = None
            if getattr(config, 'EXPORT_BATTLE_DATA', True):
                self.exporter = DataExporter()
                print("[BattleDataCollector] DataExporter initialise")
            else:
                print("[BattleDataCollector] Export JSON desactive")
            
            self.stats_fetcher = None
            if config.COLLECT_PLAYER_STATS or getattr(config, 'COLLECT_PREDICTION', False):
                self.stats_fetcher = StatsFetcher()
            if self.stats_fetcher:
                print("[BattleDataCollector] StatsFetcher initialise")
            else:
                print("[BattleDataCollector] StatsFetcher desactive")
            
            self._battleData = None
            self._pendingStats = False
            self._collectCallbackPending = False
            self._predictionOverlay = None
            self._overlayInitPending = False
            self._overlayInitAttempts = 0
            self._overlayLastText = None
            self._overlayLastColor = None
            self._inBattle = False
            
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
        print("[BattleDataCollector] Destruction du collecteur...")
        self._destroyOverlay()
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
            self._inBattle = True

            # Debug: valider GUI.Text immédiatement
            try:
                if getattr(config, 'DEBUG_GUI_OVERLAY', False):
                    self._createOverlay(u"[IA] GUI.Text TEST", (255, 255, 255, 255))
            except Exception:
                pass

            # La liste des véhicules peut être vide juste après l'événement.
            # On réessaie quelques fois avec un délai court.
            self._collectBattleDataWithRetry(arena, retries=10, delay=0.5)
        
        except Exception as e:
            print("[BattleDataCollector] Erreur _onBattleStart: {}".format(str(e)))

    def _onBattleEnd(self):
        """Appelé quand le joueur quitte une bataille"""
        try:
            print("[BattleDataCollector] Fin de bataille")
            self._inBattle = False
            self._destroyOverlay()
        except Exception as e:
            print("[BattleDataCollector] Erreur _onBattleEnd: {}".format(str(e)))

    def _collectBattleDataWithRetry(self, arena, retries, delay):
        try:
            teams = self._getTeamsInfo(arena)
            count = 0
            try:
                count = len(teams.get('spawn_1', [])) + len(teams.get('spawn_2', []))
            except Exception:
                count = 0

            # Tant que les 30 joueurs ne sont pas visibles, on retente.
            # Sinon, on risque de prédire avec des équipes incomplètes.
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
            # Prédiction de victoire via l'API (sans stats côté mod)
            # On envoie uniquement les joueurs présents + leur spawn; le padding est côté API.
            try:
                if getattr(config, 'COLLECT_PREDICTION', False) and self.stats_fetcher and teams:
                    team1_names = []
                    team2_names = []
                    try:
                        team1_names = [p.get('name') for p in (teams.get('spawn_1') or []) if p.get('name')]
                        team2_names = [p.get('name') for p in (teams.get('spawn_2') or []) if p.get('name')]
                    except Exception:
                        team1_names = []
                        team2_names = []

                    if team1_names or team2_names:
                        try:
                            print('[BattleDataCollector] Prediction request: spawn_1={} spawn_2={}'.format(len(team1_names), len(team2_names)))
                        except Exception:
                            pass
                        self.stats_fetcher.fetch_prediction_async(team1_names, team2_names, callback=self._onPredictionReceived)
            except Exception:
                pass
            # Récupérer les statistiques des joueurs si activé
            if config.COLLECT_PLAYER_STATS and self.stats_fetcher and player_names:
                print("[BattleDataCollector] Récupération stats pour {} joueurs".format(len(player_names)))
                self._pendingStats = True
                self.stats_fetcher.fetch_player_stats_async(player_names, self._onStatsReceived)
            else:
                # Exporter directement sans stats (si activé)
                if self.exporter:
                    self.exporter.export(self._battleData)

        except Exception as e:
            print("[BattleDataCollector] Erreur _collectBattleDataWithRetry: {}".format(str(e)))

    def _onPredictionReceived(self, prediction):
        """Callback après réception de la prédiction."""
        print("[BattleDataCollector] *** _onPredictionReceived appelé ***")
        print("[BattleDataCollector] Prediction reçue: {}".format(prediction))
        
        try:
            def _fmt_pct(v):
                try:
                    return u"{:.1f}%".format(float(v))
                except Exception:
                    return None

            def _normalize_prediction(pred):
                if isinstance(pred, dict):
                    try:
                        predicted = pred.get('predicted')
                    except Exception:
                        predicted = None
                    try:
                        pct_str = _fmt_pct(pred.get('prob_user'))
                    except Exception:
                        pct_str = None

                    if predicted not in (True, False):
                        try:
                            v = float(pred.get('prob_user'))
                            predicted = True if v > 50.0 else False
                        except Exception:
                            predicted = None
                    return predicted, pct_str

                if pred in (True, False):
                    return pred, None
                return None, None

            predicted_bool, pct_str = _normalize_prediction(prediction)
            print("[BattleDataCollector] Normalized: predicted={}, pct={}".format(predicted_bool, pct_str))

            # Formatter le message final
            prefix = getattr(config, 'PREDICTION_MESSAGE_PREFIX', '[IA]')
            if predicted_bool is True:
                if pct_str:
                    msg = u"{} VICTOIRE ({})".format(prefix, pct_str)
                    chat_msg = u"{} Prédiction: VICTOIRE ({})".format(prefix, pct_str)
                else:
                    msg = u"{} VICTOIRE".format(prefix)
                    chat_msg = u"{} Prédiction: VICTOIRE".format(prefix)
                color = (100, 255, 100, 255)  # Vert
            elif predicted_bool is False:
                if pct_str:
                    msg = u"{} DEFAITE ({})".format(prefix, pct_str)
                    chat_msg = u"{} Prédiction: DEFAITE ({})".format(prefix, pct_str)
                else:
                    msg = u"{} DEFAITE".format(prefix)
                    chat_msg = u"{} Prédiction: DEFAITE".format(prefix)
                color = (255, 100, 100, 255)  # Rouge
            else:
                msg = u"{} ???".format(prefix)
                chat_msg = u"{} Prédiction indisponible".format(prefix)
                color = (255, 255, 100, 255)  # Jaune

            print("[BattleDataCollector] Messages formatés:")
            print("[BattleDataCollector]   Overlay: {}".format(msg))
            print("[BattleDataCollector]   Chat: {}".format(chat_msg))
            print("[BattleDataCollector]   Couleur: {}".format(color))

            # Créer l'overlay permanent
            show_screen = getattr(config, 'SHOW_PREDICTION_ON_SCREEN', True)
            send_chat = getattr(config, 'SEND_PREDICTION_TO_CHAT', True)
            
            print("[BattleDataCollector] Config: SHOW_PREDICTION_ON_SCREEN={}".format(show_screen))
            print("[BattleDataCollector] Config: SEND_PREDICTION_TO_CHAT={}".format(send_chat))
            
            if show_screen:
                print("[BattleDataCollector] Appel _createOverlay...")
                self._createOverlay(msg, color)
            else:
                print("[BattleDataCollector] Overlay désactivé dans config")
            
            # Envoyer dans le chat d'équipe
            if send_chat:
                print("[BattleDataCollector] Appel _sendTeamChatMessage...")
                self._sendTeamChatMessage(chat_msg)
            else:
                print("[BattleDataCollector] Chat désactivé dans config")

        except Exception as e:
            print("[BattleDataCollector] ERREUR _onPredictionReceived: {}".format(str(e)))
            import traceback
            traceback.print_exc()

    def _createOverlay(self, text, color=(255, 255, 255, 255)):
        """Crée un overlay persistant via GUI.Text.

        Important: sur certains clients, GUI n'est importable qu'après init de l'UI.
        On retente plusieurs fois via BigWorld.callback jusqu'à succès.
        """
        self._overlayLastText = text
        self._overlayLastColor = color
        self._overlayInitAttempts = 0

        def _get_screen_size():
            # Best-effort
            try:
                fn = getattr(BigWorld, 'screenSize', None)
                if callable(fn):
                    w, h = fn()
                    return int(w), int(h)
            except Exception:
                pass
            try:
                fn = getattr(BigWorld, 'screenResolution', None)
                if callable(fn):
                    w, h = fn()
                    return int(w), int(h)
            except Exception:
                pass
            return None, None

        def _import_gui():
            global GUI
            if GUI is not None:
                return GUI
            try:
                import GUI as _GUI
                GUI = _GUI
                return GUI
            except Exception:
                pass

            # Certains clients exposent GUI via BigWorld.GUI
            try:
                bw_gui = getattr(BigWorld, 'GUI', None)
                if bw_gui is not None and hasattr(bw_gui, 'Text') and hasattr(bw_gui, 'addRoot'):
                    return bw_gui
            except Exception:
                pass

            return None

        def _try_create():
            self._overlayInitPending = False
            self._overlayInitAttempts += 1

            gui = _import_gui()
            if gui is None:
                # UI pas prête / module non exposé dans cette phase
                if self._overlayInitAttempts in (1, 5, 10, 20, 40):
                    print("[BattleDataCollector] GUI import impossible (tentative {})".format(self._overlayInitAttempts))
                if self._overlayInitAttempts < 60:
                    try:
                        BigWorld.callback(0.25, _schedule)
                    except Exception:
                        pass
                return

            try:
                self._destroyOverlay()
            except Exception:
                pass

            try:
                try:
                    import Math
                except Exception:
                    Math = None

                overlay = gui.Text(self._overlayLastText)

                # Font (pour le "gras", on essaye des fonts plus grosses/bold en premier)
                try:
                    candidates = getattr(config, 'GUI_TEXT_FONT_CANDIDATES', None)
                except Exception:
                    candidates = None
                if not candidates:
                    candidates = ['system_big.font', 'system_large.font', 'default_large.font', 'system_medium.font', 'default_medium.font']

                for font_id in candidates:
                    try:
                        overlay.font = font_id
                        break
                    except Exception:
                        continue

                # Couleur
                try:
                    overlay.colour = self._overlayLastColor
                except Exception:
                    pass

                # Anchors (certains clients attendent des constantes, pas des strings)
                def _set_anchor(attr_name, string_value, const_names):
                    # 1) constante sur la classe Text
                    for const_name in const_names:
                        try:
                            const_val = getattr(getattr(gui, 'Text', None), const_name, None)
                            if const_val is not None:
                                setattr(overlay, attr_name, const_val)
                                return True
                        except Exception:
                            pass
                    # 2) constante sur le module GUI
                    for const_name in const_names:
                        try:
                            const_val = getattr(gui, const_name, None)
                            if const_val is not None:
                                setattr(overlay, attr_name, const_val)
                                return True
                        except Exception:
                            pass
                    # 3) string (fallback)
                    try:
                        setattr(overlay, attr_name, string_value)
                        return True
                    except Exception:
                        return False

                _set_anchor('horizontalAnchor', 'RIGHT', ['HA_RIGHT', 'HORIZONTAL_ANCHOR_RIGHT', 'ANCHOR_RIGHT'])
                _set_anchor('verticalAnchor', 'TOP', ['VA_TOP', 'VERTICAL_ANCHOR_TOP', 'ANCHOR_TOP'])

                # Scale (si supporté)
                try:
                    overlay.scale = (2.0, 2.0)
                except Exception:
                    try:
                        overlay.scale = (2.0, 2.0, 1.0)
                    except Exception:
                        pass

                try:
                    overlay.visible = True
                except Exception:
                    pass

                # Position: on essaye plusieurs modes car les clients WoT varient.
                w, h = _get_screen_size()
                try:
                    margin = getattr(config, 'GUI_TEXT_MARGIN_PX', (40, 40))
                    mx = float(margin[0])
                    my = float(margin[1])
                except Exception:
                    mx, my = 40.0, 40.0

                try:
                    y_offset = float(getattr(config, 'GUI_TEXT_Y_OFFSET_PX', -30.0))
                except Exception:
                    y_offset = -30.0

                try:
                    pos_mode = getattr(config, 'GUI_TEXT_POS_MODE', 'pixel_center')
                except Exception:
                    pos_mode = 'pixel_center'

                def _safe_str(v):
                    try:
                        return str(v)
                    except Exception:
                        return '<unprintable>'

                def _get_pos_snapshot():
                    # Snapshot léger (pour diagnostiquer si la position "stick")
                    try:
                        p = overlay.position
                    except Exception:
                        p = None
                    try:
                        x = getattr(overlay, 'x', None)
                    except Exception:
                        x = None
                    try:
                        y = getattr(overlay, 'y', None)
                    except Exception:
                        y = None
                    return (_safe_str(p), _safe_str(x), _safe_str(y))

                def _set_pos(x, y, z=None):
                    before = _get_pos_snapshot()

                    # 1) position tuple
                    try:
                        overlay.position = (x, y) if z is None else (x, y, z)
                    except Exception:
                        pass

                    # 2) Math.Vector2 / Vector3 (souvent requis)
                    if Math is not None:
                        try:
                            if z is None and hasattr(Math, 'Vector2'):
                                overlay.position = Math.Vector2(float(x), float(y))
                        except Exception:
                            pass
                        try:
                            if z is not None and hasattr(Math, 'Vector3'):
                                overlay.position = Math.Vector3(float(x), float(y), float(z))
                        except Exception:
                            pass

                    # 3) muter position.x/y si disponible
                    try:
                        p = getattr(overlay, 'position', None)
                        if p is not None and hasattr(p, 'x') and hasattr(p, 'y'):
                            try:
                                p.x = float(x)
                                p.y = float(y)
                            except Exception:
                                pass
                    except Exception:
                        pass

                    # 4) x/y attrs
                    try:
                        overlay.x = float(x)
                        overlay.y = float(y)
                    except Exception:
                        pass

                    # 5) setPosition method
                    try:
                        fn = getattr(overlay, 'setPosition', None)
                        if callable(fn):
                            fn(float(x), float(y))
                    except Exception:
                        pass

                    after = _get_pos_snapshot()
                    if before != after:
                        return True, before, after
                    return False, before, after

                def _apply_position(tag):
                    # Position: on essaye plusieurs modes car les clients WoT varient.
                    w, h = _get_screen_size()
                    try:
                        margin = getattr(config, 'GUI_TEXT_MARGIN_PX', (40, 40))
                        mx = float(margin[0])
                        my = float(margin[1])
                    except Exception:
                        mx, my = 40.0, 40.0

                    try:
                        y_offset = float(getattr(config, 'GUI_TEXT_Y_OFFSET_PX', -30.0))
                    except Exception:
                        y_offset = -30.0

                    try:
                        x_offset = float(getattr(config, 'GUI_TEXT_X_OFFSET_PX', 0.0))
                    except Exception:
                        x_offset = 0.0

                    try:
                        pos_mode = getattr(config, 'GUI_TEXT_POS_MODE', 'pixel_center')
                    except Exception:
                        pos_mode = 'pixel_center'

                    # on prépare une liste de positions candidates: mode préféré d'abord, puis fallbacks
                    candidates = []

                    py = my + y_offset

                    if w and h:
                        # A) pixel centre (repère centré)
                        x_c = float((w / 2.0) - mx + x_offset)
                        y_c = float((-h / 2.0) + py)
                        # B) pixel top-left
                        x_tl = float(w - mx + x_offset)
                        y_tl = float(py)
                        # C) normalisé 0..1 (top-right = (1,0))
                        x_n01 = float(1.0 - (mx / float(w)) + (x_offset / float(w)))
                        y_n01 = float(max(0.0, py) / float(h))
                        # D) normalisé -1..1 (top-right = (1,-1) ou (1,1) selon clients)
                        x_n11 = float(1.0 - (2.0 * mx / float(w)) + (2.0 * x_offset / float(w)))
                        y_n11_top = float(-1.0 + (2.0 * max(0.0, py) / float(h)))
                        y_n11_top_alt = float(1.0 - (2.0 * max(0.0, py) / float(h)))
                    else:
                        x_c, y_c = 0.0, 0.0
                        x_tl, y_tl = 0.0, 0.0
                        x_n01, y_n01 = 0.98, 0.02
                        x_n11, y_n11_top, y_n11_top_alt = 0.98, -0.98, 0.98

                    if pos_mode == 'pixel_topleft':
                        candidates.append(('pixel_topleft', x_tl, y_tl))
                    elif pos_mode == 'normalized':
                        candidates.append(('normalized01', x_n01, y_n01))
                    else:
                        candidates.append(('pixel_center', x_c, y_c))

                    # fallbacks (on tente plusieurs repères)
                    candidates.extend([
                        ('normalized01', x_n01, y_n01),
                        ('normalized11_a', x_n11, y_n11_top),
                        ('normalized11_b', x_n11, y_n11_top_alt),
                        ('pixel_center', x_c, y_c),
                        ('pixel_topleft', x_tl, y_tl),
                    ])

                    last_before = None
                    last_after = None
                    for mode_name, x, y in candidates:
                        ok, before, after = _set_pos(x, y)
                        last_before, last_after = before, after
                        if ok:
                            print('[BattleDataCollector] GUI.Text pos {} {} => {} (mode={}, phase={})'.format(mode_name, before, after, pos_mode, tag))
                            return True

                    print('[BattleDataCollector] GUI.Text pos inchangée (phase={}): {} => {}'.format(tag, last_before, last_after))
                    return False

                # Essayer avant addRoot
                _apply_position('preRoot')

                # Ajouter au root: certains clients n'appliquent correctement position/anchors
                # qu'une fois l'objet attaché.
                gui.addRoot(overlay)

                # Re-appliquer après addRoot
                _apply_position('postRoot')

                self._predictionOverlay = overlay
                print("[BattleDataCollector] GUI.Text overlay OK (tentative {})".format(self._overlayInitAttempts))
                return
            except Exception as e:
                # UI pas encore prête, ou API différente
                if self._overlayInitAttempts in (1, 5, 10, 20, 40):
                    print("[BattleDataCollector] GUI.Text erreur tentative {}: {}".format(self._overlayInitAttempts, str(e)))
                if self._overlayInitAttempts < 60:
                    try:
                        BigWorld.callback(0.25, _schedule)
                    except Exception:
                        pass

        def _schedule():
            if self._overlayInitPending:
                return
            self._overlayInitPending = True
            try:
                BigWorld.callback(0.0, _try_create)
            except Exception:
                _try_create()

        _schedule()
    
    def _destroyOverlay(self):
        """Détruit l'overlay"""
        if self._predictionOverlay is None:
            return
        
        print("[BattleDataCollector] Destruction de l'overlay...")
        try:
            if hasattr(BigWorld, 'GUI') and hasattr(BigWorld.GUI, 'delRoot'):
                BigWorld.GUI.delRoot(self._predictionOverlay)
                print("[BattleDataCollector] Overlay détruit via BigWorld.GUI")
            elif GUI is not None and hasattr(GUI, 'delRoot'):
                GUI.delRoot(self._predictionOverlay)
                print("[BattleDataCollector] Overlay détruit via GUI")
        except Exception as e:
            print("[BattleDataCollector] Erreur destruction overlay: {}".format(str(e)))
        finally:
            self._predictionOverlay = None
    
    def _sendTeamChatMessage(self, msg):
        """Envoie un message dans le chat d'équipe (visible par tous)"""
        try:
            # Méthode 1: Via MessengerEntry (API moderne)
            try:
                from messenger import MessengerEntry
                from messenger.proto.events import g_messengerEvents
                from gui.shared import g_eventBus, events, EVENT_BUS_SCOPE
                
                if MessengerEntry.g_instance:
                    controller = MessengerEntry.g_instance.protos.BW_CHAT2.channelsCtrl
                    if controller:
                        # Envoyer au canal d'équipe
                        controller.sendMessage(msg.encode('utf-8') if isinstance(msg, unicode) else msg)
                        print("[BattleDataCollector] Message envoyé (MessengerEntry): {}".format(msg))
                        return
            except Exception as e1:
                print("[BattleDataCollector] MessengerEntry failed: {}".format(str(e1)))
            
            # Méthode 2: Via base.sendCommand
            try:
                avatar = BigWorld.player()
                if avatar and hasattr(avatar, 'base'):
                    # Commande chat d'équipe
                    avatar.base.sendCommand(1, msg.encode('utf-8') if isinstance(msg, unicode) else msg)
                    print("[BattleDataCollector] Message envoyé (base.sendCommand): {}".format(msg))
                    return
            except Exception as e2:
                print("[BattleDataCollector] base.sendCommand failed: {}".format(str(e2)))

            # Pas de fallback: si on ne peut pas envoyer au chat, on log seulement.
            print("[BattleDataCollector] Impossible d'envoyer au chat d'équipe sur ce client")
                
        except Exception as e:
            print("[BattleDataCollector] Erreur envoi chat: {}".format(str(e)))

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
            
            # Exporter les données complètes (si activé)
            if self.exporter:
                self.exporter.export(self._battleData)
            self._pendingStats = False
        
        except Exception as e:
            print("[BattleDataCollector] Erreur _onStatsReceived: {}".format(str(e)))
