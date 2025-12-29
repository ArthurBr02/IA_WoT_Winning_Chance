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

echo [1/5] Verification de l'installation WoT...
if not exist "%WOT_PATH%" (
    echo ERREUR: World of Tanks non trouve dans %WOT_PATH%
    echo Veuillez modifier WOT_PATH dans ce script
    pause
    exit /b 1
)
echo    OK: WoT trouve dans %WOT_PATH%

REM Créer le dossier mods/<version> s'il n'existe pas
echo.
echo [2/5] Creation du dossier mods\%WOT_VERSION%...
if not exist "%WOT_PATH%\mods\%WOT_VERSION%" (
    mkdir "%WOT_PATH%\mods\%WOT_VERSION%"
    echo    OK: Dossier cree
) else (
    echo    OK: Dossier existe deja
)

REM Vérifier que le fichier .wotmod existe
echo.
echo [3/5] Verification du fichier .wotmod...
if not exist "mod_battle_data_collector_1.0.0.wotmod" (
    echo ERREUR: Fichier .wotmod non trouve
    echo Executez d'abord: python build.py
    pause
    exit /b 1
)
echo    OK: Fichier .wotmod trouve

REM Copier le fichier .wotmod
echo.
echo [4/5] Installation du mod...
copy /Y "mod_battle_data_collector_1.0.0.wotmod" "%WOT_PATH%\mods\%WOT_VERSION%\"
if errorlevel 1 (
    echo ERREUR: Impossible de copier le fichier
    pause
    exit /b 1
)
echo    OK: Mod installe

REM Vérifier la configuration
echo.
echo [5/5] Verification de la configuration...
if not exist ".env" (
    echo ATTENTION: Fichier .env non trouve
    echo Copiez .env.example en .env et configurez votre cle API
    echo.
    echo Voulez-vous creer .env maintenant? (O/N)
    choice /C ON /N
    if errorlevel 2 goto skip_env
    if errorlevel 1 (
        copy ".env.example" ".env"
        echo    OK: Fichier .env cree
        echo    IMPORTANT: Editez .env et ajoutez votre cle API Wargaming
        notepad .env
    )
) else (
    echo    OK: Fichier .env existe
)

:skip_env
echo.
echo ============================================================
echo INSTALLATION TERMINEE
echo ============================================================
echo.
echo Fichier installe dans:
echo   %WOT_PATH%\mods\%WOT_VERSION%\mod_battle_data_collector_1.0.0.wotmod
echo.
echo PROCHAINES ETAPES:
echo   1. Configurez votre cle API dans .env
echo   2. Lancez World of Tanks
echo   3. Verifiez python.log pour:
echo      [BattleDataCollector] Mod charge avec succes
echo.
echo Les donnees seront exportees dans:
echo   %WOT_PATH%\battle_data\
echo.
pause
