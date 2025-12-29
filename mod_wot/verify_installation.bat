@echo off
REM Script de verification de l'installation
echo ============================================================
echo VERIFICATION DE L'INSTALLATION
echo ============================================================
echo.

set WOT_PATH=C:\Games\World_of_Tanks_EU
set WOT_VERSION=2.1.0.2

echo [1] Verification du dossier res_mods...
set TARGET_DIR=%WOT_PATH%\res_mods\%WOT_VERSION%\scripts\client\gui\mods\mod_battle_data_collector

if exist "%TARGET_DIR%" (
    echo    OK: Dossier existe
    echo    Chemin: %TARGET_DIR%
    echo.
    echo    Fichiers Python trouves:
    dir /B "%TARGET_DIR%\*.py"
) else (
    echo    ERREUR: Dossier non trouve
    echo    Attendu: %TARGET_DIR%
)

echo.
echo [2] Verification du fichier .env...
if exist "%WOT_PATH%\.env" (
    echo    OK: .env trouve
    echo    Chemin: %WOT_PATH%\.env
) else (
    echo    ATTENTION: .env non trouve
)

echo.
echo [3] Verification de python.log...
if exist "%WOT_PATH%\python.log" (
    echo    OK: python.log existe
    echo    Taille: 
    dir "%WOT_PATH%\python.log" | find "python.log"
    echo.
    echo    Recherche de messages du mod...
    findstr /C:"BattleDataCollector" /C:"mod_battle_data_collector" "%WOT_PATH%\python.log" > nul
    if errorlevel 1 (
        echo    AUCUN message du mod trouve
    ) else (
        echo    Messages du mod trouves:
        findstr /C:"BattleDataCollector" /C:"mod_battle_data_collector" "%WOT_PATH%\python.log"
    )
) else (
    echo    ERREUR: python.log non trouve
)

echo.
echo [4] Verification de la structure...
echo    Attendu:
echo    %WOT_PATH%\res_mods\%WOT_VERSION%\scripts\client\gui\mods\mod_battle_data_collector\__init__.py
if exist "%TARGET_DIR%\__init__.py" (
    echo    OK: __init__.py existe
) else (
    echo    ERREUR: __init__.py manquant
)

echo.
echo ============================================================
echo DIAGNOSTIC
echo ============================================================
echo.

if not exist "%TARGET_DIR%\__init__.py" (
    echo PROBLEME: Les fichiers ne sont pas installes
    echo SOLUTION: Executez install_direct.bat
    goto :end
)

if not exist "%WOT_PATH%\python.log" (
    echo PROBLEME: python.log n'existe pas
    echo SOLUTION: Lancez World of Tanks au moins une fois
    goto :end
)

findstr /C:"BattleDataCollector" "%WOT_PATH%\python.log" > nul
if errorlevel 1 (
    echo PROBLEME: Le mod ne se charge pas
    echo.
    echo CAUSES POSSIBLES:
    echo   1. Mauvaise version de WoT
    echo   2. Structure de dossiers incorrecte
    echo   3. Erreur Python silencieuse
    echo.
    echo SOLUTIONS:
    echo   1. Verifiez que la version est bien %WOT_VERSION%
    echo   2. Verifiez que WoT est bien dans %WOT_PATH%
    echo   3. Cherchez des erreurs dans python.log
) else (
    echo OK: Le mod semble charge
)

:end
echo.
echo ============================================================
pause
