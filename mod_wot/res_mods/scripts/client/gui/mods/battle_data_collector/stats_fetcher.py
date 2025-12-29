# -*- coding: utf-8 -*-
"""Module de récupération des statistiques des joueurs.

Tous les appels externes (Wargaming + Tomato.gg) passent par l'API locale (FastAPI).
"""

import urllib
import urllib2
import json
from threading import Thread
try:
    from . import config
except Exception:
    import config


class StatsFetcher(object):
    """Récupère les statistiques des joueurs via l'API locale (proxy)."""
    
    def __init__(self):
        # Compat: certains fichiers de config utilisent API_BASE_URL, d'autres INTERNAL_API_BASE_URL.
        self.api_base_url = (
            getattr(config, 'INTERNAL_API_BASE_URL', None)
            or getattr(config, 'API_BASE_URL', None)
            or 'http://127.0.0.1:8000/api'
        )
        self._cache = {}  # Cache pour éviter les requêtes multiples
        self._tomato_cache = {}  # Cache Tomato (account_id -> data)

    def _api_get(self, endpoint, params):
        """GET helper compatible Python 2.7 vers l'API locale."""
        if not self.api_base_url:
            raise Exception('API base URL non configure (API_BASE_URL / INTERNAL_API_BASE_URL)')

        try:
            query = urllib.urlencode(params)
        except Exception:
            # fallback minimal
            query = '&'.join(['%s=%s' % (k, v) for (k, v) in params.items()])

        base = self.api_base_url.rstrip('/')
        path = endpoint.lstrip('/')
        url = '{}/{}?{}'.format(base, path, query)

        req = urllib2.Request(url)

        response = urllib2.urlopen(req, timeout=config.API_TIMEOUT)
        return json.loads(response.read())

    def _tomato_get_overall(self, server, account_id):
        """Récupère les stats overall via Tomato.gg.

        Endpoint:
          /player/overall/{server}/{player_id}
        """
        if not account_id:
            return None

        cached = self._tomato_cache.get(account_id)
        if cached is not None:
            return cached

        server = server or getattr(config, 'TOMATO_SERVER', getattr(config, 'SERVER_REGION', 'eu'))

        try:
            payload = self._api_get('tomato/player/overall/{}/{}'.format(server, int(account_id)), {})
        except Exception as e:
            print('[BattleDataCollector] Tomato proxy error for {}: {}'.format(account_id, str(e)))
            self._tomato_cache[account_id] = None
            return None

        self._tomato_cache[account_id] = payload
        return payload

    def _get_account_id_for_name(self, player_name):
        """Retourne account_id pour un nickname exact (ou None)."""
        if not player_name:
            return None

        # Cache hit (y compris miss)
        cached = self._cache.get(player_name)
        if cached is not None:
            return cached.get('account_id')

        # Résolution via l'API locale (proxy WG).
        try:
            search = player_name
            try:
                if isinstance(search, unicode):
                    search = search.encode('utf-8')
            except Exception:
                pass

            data = self._api_get('wg/account/list', {
                'search': search,
                'limit': 5,
                'region': getattr(config, 'SERVER_REGION', 'eu'),
            })

            if data.get('status') != 'ok':
                print("[BattleDataCollector] Erreur API account/list: {}".format(data.get('error', 'Unknown')))
                self._cache[player_name] = {'account_id': None}
                return None

            candidates = data.get('data') or []
            for player in candidates:
                try:
                    if player.get('nickname') == player_name:
                        account_id = player.get('account_id')
                        self._cache[player_name] = {'account_id': account_id}
                        return account_id
                except Exception:
                    continue

            self._cache[player_name] = {'account_id': None}
            return None

        except Exception as e:
            print("[BattleDataCollector] Exception _get_account_id_for_name: {}".format(str(e)))
            self._cache[player_name] = {'account_id': None}
            return None

    def _get_account_ids_exact_batch(self, player_names):
        """Résout une liste de nicknames via une requête account/list en mode exact.

        Certains serveurs/versions de l'API acceptent plusieurs nicknames séparés par des virgules
        si 'type=exact' est fourni.

        Returns:
            dict {player_name: account_id}
        """
        if not player_names:
            return {}

        # Filtrer + conserver l'ordre
        names = []
        seen = set()
        for n in player_names:
            if not n or n in seen:
                continue
            names.append(n)
            seen.add(n)

        # Exclure ceux déjà en cache
        result = {}
        unresolved = []
        for n in names:
            cached = self._cache.get(n)
            if cached is not None:
                aid = cached.get('account_id')
                if aid:
                    result[n] = aid
            else:
                unresolved.append(n)

        if not unresolved:
            return result

        # Encoder en utf-8 pour urllib.urlencode
        try:
            encoded = []
            for n in unresolved:
                try:
                    if isinstance(n, unicode):
                        encoded.append(n.encode('utf-8'))
                    else:
                        encoded.append(n)
                except Exception:
                    encoded.append(n)
            search_value = ','.join(encoded)
        except Exception:
            search_value = ','.join(unresolved)

        data = self._api_get('wg/account/list', {
            'search': search_value,
            'type': 'exact',
            'limit': len(unresolved) if len(unresolved) < 100 else 100,
            'region': getattr(config, 'SERVER_REGION', 'eu'),
        })

        if data.get('status') != 'ok':
            raise Exception('account/list batch failed: {}'.format(data.get('error', 'Unknown')))

        candidates = data.get('data') or []
        # Indexer par nickname
        by_name = {}
        for p in candidates:
            try:
                nick = p.get('nickname')
                if nick:
                    by_name[nick] = p
            except Exception:
                continue

        for n in unresolved:
            p = by_name.get(n)
            aid = None
            if p:
                try:
                    aid = p.get('account_id')
                except Exception:
                    aid = None
            self._cache[n] = {'account_id': aid}
            if aid:
                result[n] = aid

        return result
    
    def fetch_player_stats_async(self, player_names, callback):
        """
        Récupère les stats des joueurs de manière asynchrone
        
        Args:
            player_names: Liste des noms de joueurs
            callback: Fonction appelée avec les résultats (dict player_name -> stats)
        """
        thread = Thread(target=self._fetch_stats_thread, args=(player_names, callback))
        thread.daemon = True
        thread.start()
    
    def _fetch_stats_thread(self, player_names, callback):
        """Thread de récupération des stats"""
        try:
            # Étape 1: Récupérer les account_id à partir des noms
            account_ids = self._get_account_ids(player_names)
            
            # Étape 2: Récupérer les statistiques pour ces IDs
            stats = self._get_player_stats(account_ids)
            
            # Callback avec les résultats
            if callback:
                callback(stats)
        except Exception as e:
            print("[BattleDataCollector] Erreur récupération stats: {}".format(str(e)))
            if callback:
                callback({})
    
    def _get_account_ids(self, player_names):
        """
        Convertit les noms de joueurs en account_id
        
        Returns:
            dict: {player_name: account_id}
        """
        if not player_names:
            return {}
        
        account_ids = {}

        # Tentative 1: recherche batch "exact" (nick1,nick2,...) si supportée par l'API.
        try:
            account_ids.update(self._get_account_ids_exact_batch(player_names))
        except Exception as e:
            print("[BattleDataCollector] Batch account/list exact non supporte, fallback 1-par-1: {}".format(str(e)))

        # Fallback: Résoudre 1 par 1
        for name in player_names:
            try:
                if name in account_ids:
                    continue
                aid = self._get_account_id_for_name(name)
                if aid:
                    account_ids[name] = aid
            except Exception:
                continue

        return account_ids
    
    def _get_player_stats(self, account_ids):
        """
        Récupère les statistiques détaillées des joueurs
        
        Args:
            account_ids: dict {player_name: account_id}
        
        Returns:
            dict: {player_name: stats_dict}
        """
        if not account_ids:
            return {}

        # Inverser le mapping account_id -> player_name
        id_to_name = {v: k for k, v in account_ids.items()}

        stats_by_name = {}
        server = getattr(config, 'TOMATO_SERVER', getattr(config, 'SERVER_REGION', 'eu'))

        for aid, player_name in id_to_name.items():
            try:
                payload = self._tomato_get_overall(server, aid)
                if not payload or not isinstance(payload, dict):
                    continue

                data = payload.get('data') or {}
                if not isinstance(data, dict):
                    continue

                # Réduire la taille du JSON: retirer le détail par char
                # (le dataset veut uniquement l'overall).
                try:
                    data_slim = dict(data)
                    if 'tanks' in data_slim:
                        del data_slim['tanks']
                except Exception:
                    data_slim = data

                # On copie tout le bloc "data" de Tomato, et on expose aussi les champs attendus au top-level.
                battles = data.get('battles')
                wins = data.get('wins')
                losses = data.get('losses')

                stats_by_name[player_name] = {
                    # Données Tomato brutes (réutilisable côté IA)
                    'tomato_overall': data_slim,

                    # Champs "features" attendus
                    'battles': battles,
                    'wins': wins,
                    'losses': losses,
                    'overallWN8': data.get('overallWN8'),
                    'overallWNX': data.get('overallWNX'),
                    'winrate': data.get('winrate'),
                    'dpg': data.get('dpg'),
                    'assist': data.get('assist'),
                    'frags': data.get('frags'),
                    'survival': data.get('survival'),
                    'spots': data.get('spots'),
                    'cap': data.get('cap'),
                    'def': data.get('def'),
                    'xp': data.get('xp'),
                    'kd': data.get('kd'),

                    # Totaux utiles (si présents)
                    'total_damage': data.get('totalDamage'),
                    'total_frags': data.get('totalFrags'),
                }
            except Exception as e:
                print('[BattleDataCollector] Exception Tomato overall for {}: {}'.format(player_name, str(e)))
                continue

        return stats_by_name
