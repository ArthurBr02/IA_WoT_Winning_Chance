# -*- coding: utf-8 -*-
"""
Hook de mod pour World of Tanks
Ce fichier DOIT être dans: res_mods/<version>/scripts/client/gui/mods/
"""

import BigWorld
from gui.mods import mod_battle_data_collector

print("[BattleDataCollector] Hook charge depuis gui.mods")

# Initialiser le mod
if hasattr(mod_battle_data_collector, 'init'):
    mod_battle_data_collector.init()
    print("[BattleDataCollector] Mod initialise via hook")
else:
    print("[BattleDataCollector] ERREUR: init() non trouve")
