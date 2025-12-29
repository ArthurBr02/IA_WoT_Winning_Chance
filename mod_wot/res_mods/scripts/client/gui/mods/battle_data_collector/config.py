# -*- coding: utf-8 -*-
"""Configuration du mod Battle Data Collector.

Ce mod est exécuté dans le runtime BigWorld (Python 2.7). Pour simplifier le
déploiement et éviter les fichiers externes, la configuration est définie ici
directement (sans chargement de fichier `.env`).
"""

# ============================================================================
# API (proxy locale)
# ============================================================================
# Tous les appels externes (Wargaming + Tomato) passent par l'API locale.
# Exemple: http://127.0.0.1:8000/api
API_BASE_URL = 'http://127.0.0.1:8000/api'

# ============================================================================
# RÉGION DU SERVEUR
# ============================================================================
# Options: 'eu', 'na', 'ru', 'asia'
SERVER_REGION = 'eu'

# URLs de l'API par région
API_URLS = {
    'eu': 'https://api.worldoftanks.eu/wot/',
    'na': 'https://api.worldoftanks.com/wot/',
    'ru': 'https://api.worldoftanks.ru/wot/',
    'asia': 'https://api.worldoftanks.asia/wot/'
}

# ============================================================================
# PARAMÈTRES D'EXPORT
# ============================================================================
# Chemin de sortie des données (relatif au dossier WoT)
OUTPUT_DIR = 'battle_data'

# ============================================================================
# PARAMÈTRES API
# ============================================================================
# Timeout pour les requêtes API (secondes)
API_TIMEOUT = 5

# Stats à collecter
STATS_FIELDS = [
    'battles',
    'wins',
    'losses',
    'damage_dealt',
    'frags',
    'survived_battles',
    'spotted',
    'capture_points',
    'dropped_capture_points',
    'xp',
    # NOTE: ces champs ne sont pas disponibles sur tous les serveurs/versions
    # de l'API WoT. On les calcule à 0 si absents.
    # 'damage_assisted_track',
    # 'damage_assisted_radio'
]

# ============================================================================
# OPTIONS AVANCÉES
# ============================================================================
# Mode debug
DEBUG_MODE = False
