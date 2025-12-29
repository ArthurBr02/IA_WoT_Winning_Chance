@echo off
REM Script d'installation automatique du mod Battle Data Collector
REM Usage: install.bat

echo ============================================================
echo INSTALLATION MOD BATTLE DATA COLLECTOR
echo ============================================================
echo.

REM Détecter la version de WoT
set WOT_PATH=C:\Games\World_of_Tanks_EU
set WOT_VERSION=2.1.0.5208

echo [1/4] Verification de l'installation WoT...
if not exist "%WOT_PATH%" (
    echo ERREUR: World of Tanks non trouve dans %WOT_PATH%
    echo Veuillez modifier WOT_PATH dans ce script
    pause
    exit /b 1
)
echo    OK: WoT trouve dans %WOT_PATH%

REM Créer le dossier mods/<version> s'il n'existe pas
echo.
echo [2/4] Creation du dossier mods\%WOT_VERSION%...
if not exist "%WOT_PATH%\mods\%WOT_VERSION%" (
    mkdir "%WOT_PATH%\mods\%WOT_VERSION%"
    echo    OK: Dossier cree
) else (
    echo    OK: Dossier existe deja
)

REM Vérifier que le fichier .wotmod existe
echo.
echo [3/4] Verification du fichier .wotmod...
if not exist "mod_battle_data_collector_1.0.0.wotmod" (
    echo ERREUR: Fichier .wotmod non trouve
    echo Executez d'abord: python build.py
    pause
    exit /b 1
)
echo    OK: Fichier .wotmod trouve

REM Copier le fichier .wotmod
echo.
echo [4/4] Installation du mod...
copy /Y "mod_battle_data_collector_1.0.0.wotmod" "%WOT_PATH%\mods\%WOT_VERSION%\"
if errorlevel 1 (
    echo ERREUR: Impossible de copier le fichier
    pause
    exit /b 1
)
echo    OK: Mod installe

echo.
echo ============================================================
echo INSTALLATION TERMINEE
echo ============================================================
echo.
echo Fichier installe dans:
echo   %WOT_PATH%\mods\%WOT_VERSION%\mod_battle_data_collector_1.0.0.wotmod
echo.
echo PROCHAINES ETAPES:
echo   1. Lancez l'API locale (dossier api/) avant WoT
echo   2. (Si besoin) Editez la config du mod dans:
echo      res_mods\scripts\client\gui\mods\battle_data_collector\config.py
echo   3. Lancez World of Tanks
echo   4. Verifiez python.log pour:
echo      [BattleDataCollector] Mod charge avec succes
echo.
echo Les donnees seront exportees dans:
echo   %WOT_PATH%\battle_data\
echo.
pause
