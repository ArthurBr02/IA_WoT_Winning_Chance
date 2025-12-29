# -*- coding: utf-8 -*-
"""
Chargeur de variables d'environnement depuis le fichier .env
Compatible Python 2.7 (pas de python-dotenv disponible)
"""

import os


def get_wot_root():
    """Essaie de déterminer le dossier racine de World of Tanks.

    Objectif:
    - trouver un chemin du type C:\\Games\\World_of_Tanks_EU
    - éviter les heuristiques basées sur __file__ (peu fiable en .wotmod)
    """

    # 0) Forcer via variable d'environnement (pratique pour debug)
    forced = os.environ.get('WOT_ROOT')
    if forced and os.path.isdir(forced):
        return forced

    # 1) Basé sur sys.executable (souvent ...\win64\WorldOfTanks.exe)
    try:
        import sys
        exe = getattr(sys, 'executable', None)
        if exe and os.path.exists(exe):
            exe_dir = os.path.dirname(exe)
            base = os.path.basename(exe_dir).lower()
            root = os.path.dirname(exe_dir) if base in ('win64', 'win32') else exe_dir

            # Vérification légère
            if os.path.exists(os.path.join(root, 'win64', 'WorldOfTanks.exe')) or os.path.exists(
                os.path.join(root, 'win32', 'WorldOfTanks.exe')
            ):
                return root

            # Si l'exe est déjà à la racine (cas atypique)
            if os.path.exists(os.path.join(root, 'WorldOfTanks.exe')):
                return root
    except Exception:
        pass

    # 2) Basé sur le répertoire courant + remontée
    try:
        cur = os.getcwd()
        if cur and os.path.isdir(cur):
            probe = cur
            for _ in range(8):
                if os.path.exists(os.path.join(probe, 'win64', 'WorldOfTanks.exe')) or os.path.exists(
                    os.path.join(probe, 'win32', 'WorldOfTanks.exe')
                ):
                    return probe
                parent = os.path.dirname(probe)
                if parent == probe:
                    break
                probe = parent
    except Exception:
        pass

    return None


def load_env():
    """
    Charge les variables d'environnement depuis le fichier .env
    Cherche dans le dossier racine de WoT
    """
    # Trouver le fichier .env

    # Méthode 1: racine WoT déterminée de façon robuste
    wot_root = get_wot_root()
    if wot_root:
        try:
            env_path = os.path.join(wot_root, '.env')
            if os.path.exists(env_path):
                _parse_env_file(env_path)
                print("[BattleDataCollector] Variables d'environnement chargees depuis: {}".format(env_path))
                return True
        except Exception:
            pass

    # Méthode 2: dossier courant (fallback)
    try:
        env_path = os.path.join(os.getcwd(), '.env')
        if os.path.exists(env_path):
            _parse_env_file(env_path)
            print("[BattleDataCollector] Variables d'environnement chargees depuis: {}".format(env_path))
            return True
    except Exception:
        pass
    
    # Option: créer un template minimal dans la racine WoT (ou cwd en fallback)
    try:
        target_dir = get_wot_root() or os.getcwd()
        env_path = os.path.join(target_dir, '.env')
        if not os.path.exists(env_path):
            with open(env_path, 'w') as f:
                f.write('# Battle Data Collector - configuration\n')
                f.write('# L\'API locale (FastAPI) fait le proxy vers Wargaming + Tomato\n')
                f.write('INTERNAL_API_BASE_URL=http://127.0.0.1:8000/api\n')
                f.write('# Si configuree cote API: header X-API-Key\n')
                f.write('INTERNAL_API_KEY=\n')
                f.write('# IMPORTANT: la cle Wargaming se configure cote API (api/.env)\n')
                f.write('# WARGAMING_API_KEY=YOUR_API_KEY_HERE\n')
                f.write('SERVER_REGION=eu\n')
                f.write('OUTPUT_DIR=battle_data\n')
                f.write('API_TIMEOUT=5\n')
                f.write('COLLECT_PLAYER_STATS=true\n')
                f.write('DEBUG_MODE=false\n')
            print("[BattleDataCollector] .env créé automatiquement: {}".format(env_path))
            print("[BattleDataCollector] Editez ce fichier et redémarrez WoT")
    except Exception:
        pass

    print("[BattleDataCollector] Fichier .env non trouve, utilisation des valeurs par defaut")
    return False


def _parse_env_file(filepath):
    """
    Parse le fichier .env et charge les variables dans os.environ
    
    Args:
        filepath: Chemin vers le fichier .env
    """
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Ignorer les lignes vides et les commentaires
                if not line or line.startswith('#'):
                    continue
                
                # Parser la ligne KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Retirer les guillemets si présents
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # Définir la variable d'environnement
                    os.environ[key] = value
    
    except IOError as e:
        print("[BattleDataCollector] Erreur lecture .env: {}".format(str(e)))


def get_env(key, default=None):
    """
    Récupère une variable d'environnement avec une valeur par défaut
    
    Args:
        key: Nom de la variable
        default: Valeur par défaut si la variable n'existe pas
    
    Returns:
        str: Valeur de la variable ou default
    """
    return os.environ.get(key, default)


def get_env_bool(key, default=False):
    """
    Récupère une variable d'environnement booléenne
    
    Args:
        key: Nom de la variable
        default: Valeur par défaut
    
    Returns:
        bool: True si la valeur est 'true', '1', 'yes', 'on' (case insensitive)
    """
    value = get_env(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')


def get_env_int(key, default=0):
    """
    Récupère une variable d'environnement entière
    
    Args:
        key: Nom de la variable
        default: Valeur par défaut
    
    Returns:
        int: Valeur convertie en entier
    """
    try:
        return int(get_env(key, str(default)))
    except (ValueError, TypeError):
        return default
