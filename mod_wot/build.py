#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de build pour créer le fichier .wotmod
Structure basée sur le mod Quick Demount décompilé
Usage: python build.py
"""

import zipfile
import os
import sys
import py_compile
import shutil
import tempfile
import subprocess
import binascii

MOD_NAME = 'mod_battle_data_collector'
PACKAGE_NAME = 'battle_data_collector'
VERSION = '1.0.0'


def _read_pyc_magic(pyc_path):
    with open(pyc_path, 'rb') as f:
        return f.read(4)


def _get_expected_magic_from_reference():
    """Lit le magic number .pyc d'un mod fonctionnel décompilé.

    Quick Demount (dans mod-decompile/) est compilé avec la même version de Python
    que le client WoT, donc c'est une bonne référence.
    """
    ref = os.path.join(
        os.path.dirname(__file__),
        'mod-decompile', 'res', 'scripts', 'client', 'gui', 'mods',
        'mod_quick_demount.pyc'
    )
    if os.path.exists(ref):
        return _read_pyc_magic(ref)
    return None


def _get_current_magic():
    try:
        import importlib.util
        return importlib.util.MAGIC_NUMBER
    except Exception:
        try:
            import imp
            return imp.get_magic()
        except Exception:
            return None


def _find_python27_executable():
    """Trouve un python2.7 pour compiler des .pyc compatibles WoT."""
    candidates = []

    env_exe = os.environ.get('PY27_EXE') or os.environ.get('PYTHON2_EXE')
    if env_exe:
        candidates.append(env_exe)

    candidates.extend([
        r'C:\Python27\python.exe',
        r'C:\Python27\pythonw.exe',
    ])

    for exe in candidates:
        if exe and os.path.exists(exe):
            return exe
    return None


def _python_magic(python_exe):
    """Retourne le magic number (4 bytes) de l'interpréteur donné."""
    # Python 2.7: imp.get_magic()
    code = (
        "import binascii;\n"
        "try:\n"
        " import imp; m=imp.get_magic()\n"
        "except Exception:\n"
        " import importlib.util; m=importlib.util.MAGIC_NUMBER\n"
        "print(binascii.hexlify(m).decode('ascii') if hasattr(binascii.hexlify(m), 'decode') else binascii.hexlify(m))\n"
    )
    out = subprocess.check_output([python_exe, '-c', code])
    hex_str = out.strip().decode('ascii') if hasattr(out, 'decode') else out.strip()
    return binascii.unhexlify(hex_str)


def _compile_with_python(python_exe, source_path, pyc_dest):
    """Compile source_path vers pyc_dest via l'interpréteur donné."""
    code = (
        "import py_compile;\n"
        "py_compile.compile(r'%s', cfile=r'%s', doraise=True)\n"
    ) % (source_path.replace('\\', '\\\\'), pyc_dest.replace('\\', '\\\\'))
    subprocess.check_call([python_exe, '-c', code])

def compile_python_file(source_path, temp_dir):
    """
    Compile un fichier .py en .pyc
    Retourne le chemin du fichier .pyc compilé
    """
    try:
        # Créer un fichier temporaire pour le .pyc
        filename = os.path.basename(source_path)
        pyc_filename = filename.replace('.py', '.pyc')
        temp_pyc = os.path.join(temp_dir, pyc_filename)
        
        # Compiler le fichier Python
        py_compile.compile(source_path, temp_pyc, doraise=True)
        
        return temp_pyc
    except Exception as e:
        print("   ⚠ ERREUR compilation {}: {}".format(filename, str(e)))
        return None

def build():
    """Crée le fichier .wotmod avec la structure correcte"""
    output_name = '{}_{}.wotmod'.format(MOD_NAME, VERSION)
    
    print("="*60)
    print("BUILD MOD WORLD OF TANKS")
    print("="*60)
    print("Nom: {}".format(MOD_NAME))
    print("Version: {}".format(VERSION))
    print("Fichier de sortie: {}".format(output_name))
    print()
    
    # Supprimer l'ancien fichier si existant
    if os.path.exists(output_name):
        os.remove(output_name)
        print("[1/5] Ancien fichier supprimé")
    else:
        print("[1/5] Nouveau build")
    
    # Vérifier que les fichiers sources existent
    scripts_base = os.path.join('res_mods', 'scripts', 'client', 'gui', 'mods')
    mod_package = os.path.join(scripts_base, PACKAGE_NAME)
    
    if not os.path.exists(mod_package):
        print("\n❌ ERREUR: Dossier du package introuvable!")
        print("   Attendu: {}".format(mod_package))
        sys.exit(1)
    
    # IMPORTANT: WoT utilise Python 2.7 (magic .pyc différent de Python 3.x).
    expected_magic = _get_expected_magic_from_reference()
    current_magic = _get_current_magic()
    if expected_magic and current_magic and expected_magic != current_magic:
        print("\n⚠ Python incompatible pour compiler des .pyc WoT")
        print("   Magic attendu (WoT): {}".format(binascii.hexlify(expected_magic).decode('ascii')))
        print("   Magic actuel        : {}".format(binascii.hexlify(current_magic).decode('ascii')))
        print("   ➜ Installez Python 2.7 puis définissez PY27_EXE=C:\\Python27\\python.exe")
        print("   (ou utilisez un python.exe 2.7 portable)\n")

    py27 = _find_python27_executable()
    if not py27:
        print("❌ ERREUR: Python 2.7 introuvable pour compiler des .pyc compatibles WoT.")
        print("   Installez Python 2.7 puis définissez la variable d'env: PY27_EXE")
        print("   Exemple: setx PY27_EXE C:\\Python27\\python.exe")
        sys.exit(1)

    if expected_magic:
        try:
            py27_magic = _python_magic(py27)
        except Exception as e:
            print("❌ ERREUR: impossible de vérifier la version de {}".format(py27))
            print("   {}".format(e))
            sys.exit(1)

        if py27_magic != expected_magic:
            print("❌ ERREUR: le Python 2.7 trouvé ne correspond pas au magic WoT.")
            print("   {} => {}".format(py27, binascii.hexlify(py27_magic).decode('ascii')))
            print("   attendu => {}".format(binascii.hexlify(expected_magic).decode('ascii')))
            sys.exit(1)

    print("[2/5] Dossier source trouvé: {}".format(scripts_base))
    
    # Créer un dossier temporaire pour les fichiers .pyc
    temp_dir = tempfile.mkdtemp(prefix='wotmod_build_')
    print("[3/5] Dossier temporaire créé: {}".format(temp_dir))
    
    try:
        # Créer le fichier .wotmod
        files_added = 0
        
        # IMPORTANT: WoT ne supporte PAS la compression (ZIP_DEFLATED)
        # Il faut utiliser ZIP_STORED (pas de compression)
        with zipfile.ZipFile(output_name, 'w', zipfile.ZIP_STORED) as wotmod:
            # Ajouter meta.xml à la racine
            if os.path.exists('meta.xml'):
                wotmod.write('meta.xml', 'meta.xml')
                files_added += 1
                print("   ✓ meta.xml")
            else:
                print("   ⚠ meta.xml non trouvé (optionnel)")
            
            print("\n[4/5] Compilation et ajout des fichiers Python:")

            # STRUCTURE (comme Quick Demount):
            # 1) Point d'entrée: res/scripts/client/gui/mods/mod_battle_data_collector.pyc
            # 2) Package:        res/scripts/client/gui/mods/mod_battle_data_collector/*.pyc

            main_entry = os.path.join(scripts_base, 'mod_battle_data_collector.py')
            if not os.path.exists(main_entry):
                print("   ❌ ERREUR: {} non trouvé!".format(main_entry))
                print("      Ce fichier est OBLIGATOIRE pour l'initialisation (entrypoint)")
                sys.exit(1)

            entry_pyc = os.path.join(temp_dir, 'mod_battle_data_collector.pyc')
            _compile_with_python(py27, main_entry, entry_pyc)
            wotmod.write(entry_pyc, 'res/scripts/client/gui/mods/mod_battle_data_collector.pyc')
            files_added += 1
            print("   ✓ mod_battle_data_collector.pyc (point d'entrée)")

            # Compiler les fichiers du package
            init_found = False
            for root, dirs, files in os.walk(mod_package):
                for file in files:
                    if not file.endswith('.py'):
                        continue

                    full_path = os.path.join(root, file)
                    if file == '__init__.py':
                        init_found = True

                    pyc_filename = os.path.basename(full_path).replace('.py', '.pyc')
                    temp_pyc = os.path.join(temp_dir, pyc_filename)
                    _compile_with_python(py27, full_path, temp_pyc)

                    relative_path = os.path.relpath(full_path, 'res_mods')
                    arc_path = os.path.join('res', relative_path).replace('\\', '/')
                    arc_path = arc_path.replace('.py', '.pyc')

                    wotmod.write(temp_pyc, arc_path)
                    files_added += 1

                    if file == '__init__.py':
                        print("   ✓ {} (package)".format(pyc_filename))
                    else:
                        print("   ✓ {}".format(pyc_filename))

            if not init_found:
                print("   ❌ ERREUR: __init__.py non trouvé dans {}".format(mod_package))
                sys.exit(1)
        
        print("\n[5/5] Archive créée: {} fichiers ajoutés".format(files_added))
        
        # Vérifier le contenu de l'archive
        print("\n📦 Contenu de l'archive:")
        with zipfile.ZipFile(output_name, 'r') as wotmod:
            for info in wotmod.filelist:
                print("   - {}".format(info.filename))
        
        # Afficher les instructions d'installation
        print("\n" + "="*60)
        print("✅ BUILD RÉUSSI!")
        print("="*60)
        print("\n📦 Fichier créé: {}".format(output_name))
        print("   Taille: {:.2f} KB".format(os.path.getsize(output_name) / 1024.0))
        
        print("\n📋 INSTALLATION:")
        print("   1. Copiez le fichier .wotmod dans:")
        print("      C:\\Games\\World_of_Tanks_EU\\mods\\<VERSION>\\")
        print("      Exemple: C:\\Games\\World_of_Tanks_EU\\mods\\2.1.0.2\\")
        print()
        print("   2. Configuration:")
        print("      - Configurez l'API locale côté serveur (dossier api/.env)")
        print("      - (Si besoin) Ajustez le mod dans: res_mods\\scripts\\client\\gui\\mods\\battle_data_collector\\config.py")
        print()
        print("   3. Redémarrez World of Tanks")
        print()
        print("   4. Vérifiez dans python.log:")
        print("      [BattleDataCollector] init() appelée par WoT")
        print("\n" + "="*60)
    
    finally:
        # Nettoyer le dossier temporaire
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print("\n🧹 Dossier temporaire nettoyé")

if __name__ == '__main__':
    try:
        build()
    except Exception as e:
        print("\n❌ ERREUR lors du build:")
        print("   {}".format(str(e)))
        import traceback
        traceback.print_exc()
        sys.exit(1)

