# -*- coding: utf-8 -*-
"""
Module d'export des données au format JSON
"""

import json
import os
from datetime import datetime
try:
    from . import config
    from .env_loader import get_wot_root
except Exception:
    import config
    try:
        from env_loader import get_wot_root
    except Exception:
        get_wot_root = None


class DataExporter(object):
    """Exporte les données de bataille au format JSON"""
    
    def __init__(self, output_dir=None):
        if output_dir is None:
            # Dossier par défaut dans la racine WoT (fiable en .wotmod)
            wot_root = None
            try:
                if get_wot_root is not None:
                    wot_root = get_wot_root()
            except Exception:
                wot_root = None

            if wot_root:
                self.output_dir = os.path.join(wot_root, config.OUTPUT_DIR)
            else:
                # Fallback: heuristique historique (peut sur-remonter)
                self.output_dir = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    '..', '..', '..', '..', '..', '..', config.OUTPUT_DIR
                )
        else:
            self.output_dir = output_dir

        self.output_dir = os.path.abspath(os.path.normpath(self.output_dir))
        
        self._ensureOutputDir()
    
    def _ensureOutputDir(self):
        """Crée le dossier de sortie si nécessaire"""
        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir)
                print("[BattleDataCollector] Dossier créé: {}".format(self.output_dir))
            except OSError as e:
                print("[BattleDataCollector] Erreur création dossier: {}".format(str(e)))
    
    def export(self, battle_data):
        """
        Exporte les données de bataille en JSON
        
        Args:
            battle_data: dict contenant toutes les données de bataille
        
        Returns:
            str: chemin du fichier créé
        """
        if not battle_data:
            print("[BattleDataCollector] Aucune donnée à exporter")
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        map_name = battle_data.get('map', {}).get('name', 'unknown')
        filename = 'battle_{}_{}.json'.format(map_name, timestamp)
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(battle_data, f, indent=2, ensure_ascii=False)
            print("[BattleDataCollector] Données exportées: {}".format(filepath))
            return filepath
        except IOError as e:
            print("[BattleDataCollector] Erreur export: {}".format(str(e)))
            return None
