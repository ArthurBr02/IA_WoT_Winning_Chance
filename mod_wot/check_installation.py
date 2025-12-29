# -*- coding: utf-8 -*-
"""
Script de vérification du mod installé
Vérifie la structure du .wotmod et les logs
"""

import os
import zipfile
import sys

def check_wotmod_structure(wotmod_path):
    """Vérifie la structure interne du fichier .wotmod"""
    print("\n" + "="*60)
    print("VERIFICATION DE LA STRUCTURE DU .WOTMOD")
    print("="*60)
    
    if not os.path.exists(wotmod_path):
        print("❌ Fichier non trouvé: {}".format(wotmod_path))
        return False
    
    print("✓ Fichier trouvé: {}".format(wotmod_path))
    print("  Taille: {:.2f} KB".format(os.path.getsize(wotmod_path) / 1024.0))
    
    try:
        with zipfile.ZipFile(wotmod_path, 'r') as z:
            files = z.namelist()
            print("\n📦 Contenu de l'archive ({} fichiers):".format(len(files)))
            
            for f in sorted(files):
                info = z.getinfo(f)
                compress_type = "STORED" if info.compress_type == 0 else "DEFLATED"
                print("  - {} [{}]".format(f, compress_type))
            
            # Vérifications
            print("\n🔍 Vérifications:")
            
            required_files = [
                'res/scripts/client/gui/mods/mod_battle_data_collector/__init__.py',
                'res/scripts/client/gui/mods/mod_battle_data_collector/battle_data_collector.py',
                'res/scripts/client/gui/mods/mod_battle_data_collector/config.py',
                'res/scripts/client/gui/mods/mod_battle_data_collector/data_exporter.py',
                'res/scripts/client/gui/mods/mod_battle_data_collector/stats_fetcher.py',
                'res/scripts/client/gui/mods/mod_battle_data_collector/env_loader.py'
            ]
            
            all_ok = True
            for req_file in required_files:
                if req_file in files:
                    print("  ✓ {}".format(req_file))
                else:
                    print("  ❌ MANQUANT: {}".format(req_file))
                    all_ok = False
            
            # Vérifier la compression
            print("\n📊 Type de compression:")
            for f in files:
                info = z.getinfo(f)
                if info.compress_type != 0:
                    print("  ⚠ {} utilise la compression (incompatible WoT!)".format(f))
                    all_ok = False
            
            if all_ok:
                print("  ✓ Tous les fichiers utilisent ZIP_STORED (OK)")
            
            return all_ok
            
    except Exception as e:
        print("❌ Erreur lors de la lecture: {}".format(str(e)))
        return False


def check_python_log(log_path):
    """Vérifie le fichier python.log pour les messages du mod"""
    print("\n" + "="*60)
    print("VERIFICATION DU FICHIER PYTHON.LOG")
    print("="*60)
    
    if not os.path.exists(log_path):
        print("❌ Fichier python.log non trouvé: {}".format(log_path))
        return
    
    print("✓ Fichier trouvé: {}".format(log_path))
    
    try:
        with open(log_path, 'r') as f:
            lines = f.readlines()
        
        print("  Taille: {} lignes".format(len(lines)))
        
        # Chercher les messages du mod
        mod_messages = [line for line in lines if 'BattleDataCollector' in line or 'mod_battle_data_collector' in line]
        
        if mod_messages:
            print("\n📝 Messages du mod ({} trouvés):".format(len(mod_messages)))
            for msg in mod_messages[-20:]:  # Derniers 20 messages
                print("  " + msg.strip())
        else:
            print("\n⚠ Aucun message du mod trouvé dans python.log")
            print("  Le mod n'est probablement pas chargé")
        
        # Chercher les erreurs
        error_lines = [line for line in lines if 'mod_battle_data_collector' in line.lower() and ('error' in line.lower() or 'exception' in line.lower())]
        
        if error_lines:
            print("\n❌ Erreurs détectées:")
            for err in error_lines[-10:]:
                print("  " + err.strip())
    
    except Exception as e:
        print("❌ Erreur lors de la lecture: {}".format(str(e)))


def check_battle_data_folder(folder_path):
    """Vérifie le dossier battle_data"""
    print("\n" + "="*60)
    print("VERIFICATION DU DOSSIER BATTLE_DATA")
    print("="*60)
    
    if not os.path.exists(folder_path):
        print("⚠ Dossier non trouvé: {}".format(folder_path))
        print("  Le dossier sera créé automatiquement lors de la première bataille")
        return
    
    print("✓ Dossier trouvé: {}".format(folder_path))
    
    json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    
    if json_files:
        print("  {} fichiers JSON trouvés:".format(len(json_files)))
        for f in json_files[:10]:  # Premiers 10 fichiers
            print("    - {}".format(f))
    else:
        print("  ⚠ Aucun fichier JSON trouvé")
        print("  Jouez une bataille pour générer des données")


def main():
    print("="*60)
    print("DIAGNOSTIC MOD BATTLE DATA COLLECTOR")
    print("="*60)
    
    # Chemins
    wot_path = r"C:\Games\World_of_Tanks_EU"
    version = "2.1.0.5208"
    
    wotmod_path = os.path.join(wot_path, "mods", version, "mod_battle_data_collector_1.0.0.wotmod")
    log_path = os.path.join(wot_path, "python.log")
    battle_data_path = os.path.join(wot_path, "battle_data")
    
    # Vérifications
    check_wotmod_structure(wotmod_path)
    check_python_log(log_path)
    check_battle_data_folder(battle_data_path)
    
    print("\n" + "="*60)
    print("DIAGNOSTIC TERMINÉ")
    print("="*60)
    print("\n💡 PROCHAINES ÉTAPES:")
    print("  1. Si le .wotmod a des problèmes: relancez 'python build.py'")
    print("  2. Si aucun message dans python.log: le mod ne se charge pas")
    print("  3. Si des erreurs: partagez-les pour diagnostic")
    print("  4. Si tout OK: jouez une bataille pour tester")
    print()


if __name__ == '__main__':
    main()
    input("\nAppuyez sur Entrée pour quitter...")
