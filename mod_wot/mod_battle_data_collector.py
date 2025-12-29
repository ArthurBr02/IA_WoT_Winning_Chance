# -*- coding: utf-8 -*-
"""
Point d'entrée principal du mod pour World of Tanks
Ce fichier DOIT être à la racine du .wotmod pour que WoT l'initialise
"""

import BigWorld

print("[BattleDataCollector] mod_battle_data_collector.py charge")

def init():
    """
    Fonction appelée par WoT au chargement du mod
    """
    print("[BattleDataCollector] init() appelee par WoT")
    
    try:
        # Importer et initialiser le module principal
        import gui.mods.mod_battle_data_collector as mod_main
        
        if hasattr(mod_main, 'init'):
            mod_main.init()
            print("[BattleDataCollector] Module principal initialise")
        else:
            print("[BattleDataCollector] ERREUR: init() non trouve dans le module principal")
    
    except ImportError as e:
        print("[BattleDataCollector] ERREUR ImportError:")
        print("[BattleDataCollector] {}".format(str(e)))
        import traceback
        traceback.print_exc()
    
    except Exception as e:
        print("[BattleDataCollector] ERREUR Exception:")
        print("[BattleDataCollector] {}".format(str(e)))
        import traceback
        traceback.print_exc()


def fini():
    """
    Fonction appelée par WoT à la fermeture
    """
    print("[BattleDataCollector] fini() appelee par WoT")
    
    try:
        import gui.mods.mod_battle_data_collector as mod_main
        
        if hasattr(mod_main, 'fini'):
            mod_main.fini()
    
    except Exception as e:
        print("[BattleDataCollector] ERREUR dans fini():")
        print("[BattleDataCollector] {}".format(str(e)))


# Log de chargement du module
print("[BattleDataCollector] Point d'entree charge - pret pour init()")
