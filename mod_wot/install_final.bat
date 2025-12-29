@echo off
REM Installation finale - approche simplifiée
echo ============================================================
echo INSTALLATION FINALE - MOD BATTLE DATA COLLECTOR
echo ============================================================

set WOT_PATH=C:\Games\World_of_Tanks_EU
set WOT_VERSION=2.1.0.2

echo.
echo [1/3] Nettoyage des anciennes installations...
if exist "%WOT_PATH%\mods\%WOT_VERSION%\mod_battle_data_collector_1.0.0.wotmod" (
    del "%WOT_PATH%\mods\%WOT_VERSION%\mod_battle_data_collector_1.0.0.wotmod"
    echo    OK: .wotmod supprime
)

echo.
echo [2/3] Build du .wotmod (necessite Python 2.7 via PY27_EXE)...
python build.py
if errorlevel 1 (
    echo ERREUR lors du build
    pause
    exit /b 1
)

echo.
echo [3/3] Installation du .wotmod...
if not exist "%WOT_PATH%\mods\%WOT_VERSION%" mkdir "%WOT_PATH%\mods\%WOT_VERSION%"
copy /Y "mod_battle_data_collector_1.0.0.wotmod" "%WOT_PATH%\mods\%WOT_VERSION%\mod_battle_data_collector_1.0.0.wotmod" >nul
echo    OK: .wotmod copie

echo.
echo ============================================================
echo INSTALLATION TERMINEE
echo ============================================================
echo.
echo Fichier installe dans:
echo   %WOT_PATH%\mods\%WOT_VERSION%\mod_battle_data_collector_1.0.0.wotmod
echo.
echo IMPORTANT:
echo   1. Lancez l'API locale (dossier api/) avant WoT
echo   2. (Si besoin) Modifiez la config du mod dans le projet:
echo      res_mods\scripts\client\gui\mods\battle_data_collector\config.py
echo   3. Rebuild (python build.py) + recopie du .wotmod
echo   4. FERMEZ COMPLETEMENT WoT (pas juste redemarrer)
echo   5. Relancez WoT
echo   6. Cherchez dans python.log:
echo      [BattleDataCollector] init() appelee par WoT
echo.
pause
