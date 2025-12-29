# -*- coding: utf-8 -*-
"""Utilitaires d'environnement (Python 2.7).

Le mod n'utilise plus de fichier `.env`. Ce module conserve:
- la détection du dossier WoT (get_wot_root)
- des helpers pour lire des variables d'environnement déjà présentes (os.environ)
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


    """Compat: ancien chargeur de `.env` (désactivé).

    La configuration du mod est désormais dans `config.py`.
    """
    return False

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
