#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script d'analyse des données de bataille collectées par le mod WoT
Lit les fichiers JSON et génère des statistiques et visualisations

Usage:
    python analyze_battles.py [chemin_vers_battle_data]
"""

import os
import sys
import json
import glob
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Configuration de l'affichage
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)


def load_battle_data(data_dir):
    """
    Charge tous les fichiers JSON de bataille
    
    Args:
        data_dir: Chemin vers le dossier battle_data
    
    Returns:
        list: Liste de dictionnaires contenant les données de bataille
    """
    json_files = glob.glob(os.path.join(data_dir, 'battle_*.json'))
    battles = []
    
    print(f"Chargement de {len(json_files)} fichiers de bataille...")
    
    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                battle = json.load(f)
                battles.append(battle)
        except Exception as e:
            print(f"Erreur lors du chargement de {filepath}: {e}")
    
    print(f"✓ {len(battles)} batailles chargées avec succès")
    return battles


def extract_player_stats(battles):
    """
    Extrait les statistiques des joueurs de toutes les batailles
    
    Returns:
        pd.DataFrame: DataFrame avec les stats de tous les joueurs
    """
    players_data = []
    
    for battle in battles:
        map_name = battle['map']['name']
        timestamp = battle['timestamp']
        
        for spawn_id, spawn_key in enumerate(['spawn_1', 'spawn_2'], 1):
            for player in battle['teams'][spawn_key]:
                player_row = {
                    'timestamp': timestamp,
                    'map': map_name,
                    'spawn': spawn_id,
                    'player_name': player['name'],
                    'tank': player['tank'],
                    'tank_tier': player['tank_tier'],
                    'tank_type': player['tank_type'],
                    'clan': player['clan']
                }
                
                # Ajouter les stats si disponibles
                if player.get('stats'):
                    stats = player['stats']
                    player_row.update({
                        'battles': stats.get('battles', 0),
                        'wins': stats.get('wins', 0),
                        'win_rate': stats.get('win_rate', 0),
                        'avg_damage': stats.get('avg_damage', 0),
                        'avg_frags': stats.get('avg_frags', 0),
                        'avg_spotted': stats.get('avg_spotted', 0)
                    })
                
                players_data.append(player_row)
    
    return pd.DataFrame(players_data)


def analyze_map_distribution(battles):
    """Analyse la distribution des maps jouées"""
    maps = [b['map']['name'] for b in battles]
    map_counts = pd.Series(maps).value_counts()
    
    plt.figure(figsize=(12, 6))
    map_counts.plot(kind='bar')
    plt.title('Distribution des Maps Jouées', fontsize=16, fontweight='bold')
    plt.xlabel('Map', fontsize=12)
    plt.ylabel('Nombre de Batailles', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('analysis_maps_distribution.png', dpi=300)
    print("✓ Graphique sauvegardé: analysis_maps_distribution.png")
    plt.close()


def analyze_player_stats(df):
    """Analyse les statistiques des joueurs"""
    if 'win_rate' not in df.columns:
        print("⚠ Pas de statistiques de joueurs disponibles")
        return
    
    # Distribution du taux de victoire
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    df['win_rate'].hist(bins=50, edgecolor='black')
    plt.title('Distribution du Taux de Victoire', fontsize=14, fontweight='bold')
    plt.xlabel('Taux de Victoire (%)', fontsize=12)
    plt.ylabel('Nombre de Joueurs', fontsize=12)
    
    # Distribution des dégâts moyens
    plt.subplot(1, 2, 2)
    df['avg_damage'].hist(bins=50, edgecolor='black', color='orange')
    plt.title('Distribution des Dégâts Moyens', fontsize=14, fontweight='bold')
    plt.xlabel('Dégâts Moyens', fontsize=12)
    plt.ylabel('Nombre de Joueurs', fontsize=12)
    
    plt.tight_layout()
    plt.savefig('analysis_player_stats.png', dpi=300)
    print("✓ Graphique sauvegardé: analysis_player_stats.png")
    plt.close()


def analyze_tank_types(df):
    """Analyse la distribution des types de chars"""
    tank_type_counts = df['tank_type'].value_counts()
    
    plt.figure(figsize=(10, 6))
    colors = sns.color_palette("husl", len(tank_type_counts))
    tank_type_counts.plot(kind='pie', autopct='%1.1f%%', colors=colors)
    plt.title('Distribution des Types de Chars', fontsize=16, fontweight='bold')
    plt.ylabel('')
    plt.tight_layout()
    plt.savefig('analysis_tank_types.png', dpi=300)
    print("✓ Graphique sauvegardé: analysis_tank_types.png")
    plt.close()


def generate_summary_stats(battles, df):
    """Génère un résumé statistique"""
    print("\n" + "="*60)
    print("RÉSUMÉ STATISTIQUE")
    print("="*60)
    
    print(f"\n📊 Batailles:")
    print(f"  - Nombre total: {len(battles)}")
    print(f"  - Nombre de joueurs: {len(df)}")
    print(f"  - Maps uniques: {df['map'].nunique()}")
    
    if 'win_rate' in df.columns:
        print(f"\n🎯 Statistiques Joueurs:")
        print(f"  - Taux de victoire moyen: {df['win_rate'].mean():.2f}%")
        print(f"  - Dégâts moyens: {df['avg_damage'].mean():.2f}")
        print(f"  - Frags moyens: {df['avg_frags'].mean():.2f}")
        print(f"  - Spotting moyen: {df['avg_spotted'].mean():.2f}")
    
    print(f"\n🎮 Types de Chars:")
    for tank_type, count in df['tank_type'].value_counts().items():
        percentage = (count / len(df)) * 100
        print(f"  - {tank_type}: {count} ({percentage:.1f}%)")
    
    print(f"\n🏆 Top 5 Maps:")
    for i, (map_name, count) in enumerate(df['map'].value_counts().head(5).items(), 1):
        print(f"  {i}. {map_name}: {count} batailles")
    
    print("\n" + "="*60)


def export_to_csv(df, output_file='battles_analysis.csv'):
    """Exporte les données vers CSV pour analyse externe"""
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"✓ Données exportées vers: {output_file}")


def main():
    """Fonction principale"""
    # Déterminer le chemin des données
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    else:
        # Chemin par défaut
        data_dir = 'battle_data'
    
    if not os.path.exists(data_dir):
        print(f"❌ Erreur: Le dossier '{data_dir}' n'existe pas")
        print(f"\nUsage: python {sys.argv[0]} [chemin_vers_battle_data]")
        sys.exit(1)
    
    print("="*60)
    print("ANALYSE DES DONNÉES DE BATAILLE - World of Tanks")
    print("="*60)
    
    # Charger les données
    battles = load_battle_data(data_dir)
    
    if not battles:
        print("❌ Aucune bataille trouvée")
        sys.exit(1)
    
    # Extraire les stats des joueurs
    df = extract_player_stats(battles)
    
    # Générer les analyses
    print("\n📈 Génération des graphiques...")
    analyze_map_distribution(battles)
    analyze_player_stats(df)
    analyze_tank_types(df)
    
    # Résumé statistique
    generate_summary_stats(battles, df)
    
    # Export CSV
    export_to_csv(df)
    
    print("\n✅ Analyse terminée avec succès!")
    print("\nFichiers générés:")
    print("  - analysis_maps_distribution.png")
    print("  - analysis_player_stats.png")
    print("  - analysis_tank_types.png")
    print("  - battles_analysis.csv")


if __name__ == '__main__':
    main()
