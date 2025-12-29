# -*- coding: utf-8 -*-
"""
Configuration du mod Battle Data Collector
Charge les paramètres depuis le fichier .env si disponible
"""

try:
    from .env_loader import load_env, get_env, get_env_bool, get_env_int
except Exception:
    from env_loader import load_env, get_env, get_env_bool, get_env_int

# Charger les variables d'environnement depuis .env
load_env()

# ============================================================================
# API (proxy locale)
# ============================================================================
# Tous les appels externes (Wargaming + Tomato) passent par l'API locale.
# Exemple: http://127.0.0.1:8000/api
INTERNAL_API_BASE_URL = get_env('INTERNAL_API_BASE_URL', 'http://127.0.0.1:8000/api')

# Header optionnel si l'API est protégée par une clé interne
INTERNAL_API_KEY = get_env('INTERNAL_API_KEY', '')

# Ancien param (conservé pour compatibilité doc) — la clé doit désormais être configurée côté API.
WARGAMING_API_KEY = get_env('WARGAMING_API_KEY', 'YOUR_API_KEY_HERE')

# ============================================================================
# RÉGION DU SERVEUR
# ============================================================================
# Options: 'eu', 'na', 'ru', 'asia'
SERVER_REGION = get_env('SERVER_REGION', 'eu')

# URLs de l'API par région
API_URLS = {
    'eu': 'https://api.worldoftanks.eu/wot/',
    'na': 'https://api.worldoftanks.com/wot/',
    'ru': 'https://api.worldoftanks.ru/wot/',
    'asia': 'https://api.worldoftanks.asia/wot/'
}

# ============================================================================
# API TOMATO.GG (WN8/WNX + stats globales)
# ============================================================================
# Base URL de l'API Tomato (publique)
TOMATO_API_BASE_URL = get_env('TOMATO_API_BASE_URL', 'https://api.tomato.gg/api')

# Serveur Tomato (souvent identique à SERVER_REGION)
TOMATO_SERVER = get_env('TOMATO_SERVER', SERVER_REGION)

# ============================================================================
# PARAMÈTRES D'EXPORT
# ============================================================================
# Chemin de sortie des données (relatif au dossier WoT)
OUTPUT_DIR = get_env('OUTPUT_DIR', 'battle_data')

# ============================================================================
# PARAMÈTRES API
# ============================================================================
# Timeout pour les requêtes API (secondes)
API_TIMEOUT = get_env_int('API_TIMEOUT', 5)

# ============================================================================
# COLLECTE DES STATISTIQUES
# ============================================================================
# Activer/désactiver la collecte de stats
COLLECT_PLAYER_STATS = get_env_bool('COLLECT_PLAYER_STATS', True)

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
DEBUG_MODE = get_env_bool('DEBUG_MODE', False)
