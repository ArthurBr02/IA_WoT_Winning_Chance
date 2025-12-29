#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de compilation des fichiers Python en bytecode (.pyc)
WoT ne charge QUE les fichiers .pyc, pas les .py !
"""

import py_compile
import os
import sys

def compile_python_files(source_dir, target_dir):
    """Compile tous les fichiers .py en .pyc"""
    
    print("="*60)
    print("COMPILATION DES FICHIERS PYTHON")
    print("="*60)
    print()
    
    if not os.path.exists(source_dir):
        print("ERREUR: Dossier source non trouve: {}".format(source_dir))
        return False
    
    # Créer le dossier cible si nécessaire
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print("Dossier cible cree: {}".format(target_dir))
    
    compiled_count = 0
    error_count = 0
    
    # Parcourir tous les fichiers .py
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.py') and not file.startswith('__pycache__'):
                source_file = os.path.join(root, file)
                
                # Calculer le chemin relatif
                rel_path = os.path.relpath(source_file, source_dir)
                target_file = os.path.join(target_dir, rel_path + 'c')  # .pyc
                
                # Créer les sous-dossiers si nécessaire
                target_subdir = os.path.dirname(target_file)
                if not os.path.exists(target_subdir):
                    os.makedirs(target_subdir)
                
                try:
                    # Compiler le fichier
                    py_compile.compile(source_file, target_file, doraise=True)
                    print("  OK: {} -> {}".format(file, os.path.basename(target_file)))
                    compiled_count += 1
                except Exception as e:
                    print("  ERREUR: {} - {}".format(file, str(e)))
                    error_count += 1
    
    print()
    print("="*60)
    print("COMPILATION TERMINEE")
    print("="*60)
    print("Fichiers compiles: {}".format(compiled_count))
    print("Erreurs: {}".format(error_count))
    print()
    
    return error_count == 0


def main():
    source_dir = os.path.join('res_mods', 'scripts', 'client', 'gui', 'mods', 'mod_battle_data_collector')
    target_dir = source_dir  # Compiler dans le même dossier
    
    if compile_python_files(source_dir, target_dir):
        print("SUCCESS: Tous les fichiers ont ete compiles")
        print()
        print("PROCHAINES ETAPES:")
        print("  1. Executez install_final.bat")
        print("  2. Relancez World of Tanks")
        print("  3. Verifiez python.log")
        return 0
    else:
        print("ERREUR: Certains fichiers n'ont pas pu etre compiles")
        return 1


if __name__ == '__main__':
    sys.exit(main())
