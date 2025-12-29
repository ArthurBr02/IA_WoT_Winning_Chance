# -*- coding: utf-8 -*-
"""Configuration du mod Battle Data Collector.

Ce mod est exécuté dans le runtime BigWorld (Python 2.7). La configuration est
définie directement ici (pas de fichier .env).
"""

# ============================================================================
# API (proxy locale)
# ============================================================================
# Tous les appels externes (Wargaming + Tomato) passent par l'API locale.
# Exemple: http://127.0.0.1:8000/api
API_BASE_URL = 'https://maison.arthurbratigny.fr/api'

# Alias conservé pour compatibilité (anciens noms)
INTERNAL_API_BASE_URL = API_BASE_URL

# Réservé (si vous protégez l'API locale côté serveur)
INTERNAL_API_KEY = ''

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
# API TOMATO.GG (WN8/WNX + stats globales)
# ============================================================================
# Base URL de l'API Tomato (publique). Conservé pour compat/diagnostic.
TOMATO_API_BASE_URL = 'https://api.tomato.gg/api'

# Serveur Tomato (souvent identique à SERVER_REGION)
TOMATO_SERVER = SERVER_REGION

# ============================================================================
# PARAMÈTRES D'EXPORT
# ============================================================================
# Chemin de sortie des données (relatif au dossier WoT)
OUTPUT_DIR = 'battle_data'

# Export des fichiers JSON (désactivé quand on veut uniquement la prédiction)
EXPORT_BATTLE_DATA = False

# ============================================================================
# PARAMÈTRES API
# ============================================================================
# Timeout pour les requêtes API (secondes)
API_TIMEOUT = 5

# Timeout spécifique pour la prédiction (l'API peut appeler WG + Tomato, donc plus long)
PREDICTION_TIMEOUT = 30

# ============================================================================
# COLLECTE DES STATISTIQUES
# ============================================================================
# Activer/désactiver la collecte de stats
COLLECT_PLAYER_STATS = False

# Prédiction de victoire via l'API locale (/predict/win)
COLLECT_PREDICTION = True

# Stats à collecter (WG)
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
]

# ============================================================================
# OPTIONS AVANCÉES
# ============================================================================
# Mode debug
DEBUG_MODE = False