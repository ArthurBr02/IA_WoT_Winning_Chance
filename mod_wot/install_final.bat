@echo off
REM Installation finale - approche simplifiée
echo ============================================================
echo INSTALLATION FINALE - MOD BATTLE DATA COLLECTOR
echo ============================================================

set WOT_PATH=C:\Games\World_of_Tanks_EU
set WOT_VERSION=2.1.0.2

echo.
echo [1/4] Nettoyage des anciennes installations...
if exist "%WOT_PATH%\mods\%WOT_VERSION%\mod_battle_data_collector_1.0.0.wotmod" (
    del "%WOT_PATH%\mods\%WOT_VERSION%\mod_battle_data_collector_1.0.0.wotmod"
    echo    OK: .wotmod supprime
)

echo.
echo [2/4] Build du .wotmod (necessite Python 2.7 via PY27_EXE)...
python build.py
if errorlevel 1 (
    echo ERREUR lors du build
    pause
    exit /b 1
)

echo.
echo [3/4] Installation du .wotmod...
if not exist "%WOT_PATH%\mods\%WOT_VERSION%" mkdir "%WOT_PATH%\mods\%WOT_VERSION%"
copy /Y "mod_battle_data_collector_1.0.0.wotmod" "%WOT_PATH%\mods\%WOT_VERSION%\mod_battle_data_collector_1.0.0.wotmod" >nul
echo    OK: .wotmod copie

echo.
echo [4/4] Configuration .env...
if not exist "%WOT_PATH%\.env" (
    if exist ".env.example" (
        copy ".env.example" "%WOT_PATH%\.env"
        echo    OK: .env cree depuis .env.example
        echo    IMPORTANT: Editez %WOT_PATH%\.env et ajoutez votre cle API
    )
) else (
    echo    OK: .env existe deja
)

echo.
echo ============================================================
echo INSTALLATION TERMINEE
echo ============================================================
echo.
echo Fichier installe dans:
echo   %WOT_PATH%\mods\%WOT_VERSION%\mod_battle_data_collector_1.0.0.wotmod
echo.
echo Configuration:
echo   %WOT_PATH%\.env
echo.
echo IMPORTANT:
echo   1. Editez %WOT_PATH%\.env
echo   2. Ajoutez votre cle API Wargaming
echo   3. FERMEZ COMPLETEMENT WoT (pas juste redemarrer)
echo   4. Relancez WoT
echo   5. Cherchez dans python.log:
echo      [BattleDataCollector] init() appelee par WoT
echo.
pause
