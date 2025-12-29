# -*- coding: utf-8 -*-
"""Point d'entrée WoT (GUI mod).

Structure calquée sur l'exemple fonctionnel (Quick Demount):
- res/scripts/client/gui/mods/mod_<name>.pyc  (entrypoint importé au démarrage)
- res/scripts/client/gui/mods/<name>/...      (package)

WoT utilise Python 2.7: les .pyc doivent être compilés avec Python 2.7.
"""

import BigWorld

try:
    from debug_utils import LOG_NOTE, LOG_ERROR, LOG_CURRENT_EXCEPTION
except Exception:
    LOG_NOTE = None
    LOG_ERROR = None
    LOG_CURRENT_EXCEPTION = None


def _log_note(msg):
    if LOG_NOTE is not None:
        LOG_NOTE('[BattleDataCollector] %s' % msg)
    else:
        try:
            print('[BattleDataCollector] %s' % msg)
        except Exception:
            pass


def _log_error(msg):
    if LOG_ERROR is not None:
        LOG_ERROR('[BattleDataCollector] %s' % msg)
    else:
        try:
            print('[BattleDataCollector][ERROR] %s' % msg)
        except Exception:
            pass


g_battleDataCollector = None


def init():
    """Appelée automatiquement par WoT au chargement des mods GUI."""
    global g_battleDataCollector

    if g_battleDataCollector is not None:
        _log_note('init() ignorée: déjà initialisé')
        return

    _log_note('init() appelée par WoT')

    try:
        from gui.mods.battle_data_collector.battle_data_collector import BattleDataCollector
        g_battleDataCollector = BattleDataCollector()
        _log_note('Instance BattleDataCollector créée')

    except Exception as e:
        _log_error('Erreur init(): %s' % e)
        if LOG_CURRENT_EXCEPTION is not None:
            LOG_CURRENT_EXCEPTION()
        else:
            import traceback
            traceback.print_exc()


def fini():
    """Appelée par WoT à la fermeture."""
    global g_battleDataCollector

    _log_note('fini() appelée par WoT')
    g_battleDataCollector = None


_log_note('module chargé (en attente de init())')
