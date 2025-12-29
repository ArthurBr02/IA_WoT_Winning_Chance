@echo off
REM Installation COMPLETE avec compilation
echo ============================================================
echo INSTALLATION COMPLETE - MOD BATTLE DATA COLLECTOR
echo ============================================================

set WOT_PATH=C:\Games\World_of_Tanks_EU
set WOT_VERSION=2.1.0.2

echo.
echo [1/4] Compilation des fichiers Python en bytecode (.pyc)...
python compile_mod.py
if errorlevel 1 (
    echo ERREUR lors de la compilation
    pause
    exit /b 1
)

echo.
echo [2/4] Nettoyage...
if exist "%WOT_PATH%\mods\%WOT_VERSION%\*.wotmod" (
    del "%WOT_PATH%\mods\%WOT_VERSION%\*.wotmod"
    echo    OK: Anciens .wotmod supprimes
)

echo.
echo [3/4] Installation des fichiers compiles (.pyc)...
set TARGET_DIR=%WOT_PATH%\res_mods\%WOT_VERSION%\scripts\client\gui\mods\mod_battle_data_collector

if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

xcopy /Y /Q "res_mods\scripts\client\gui\mods\mod_battle_data_collector\*.pyc" "%TARGET_DIR%\"
echo    OK: Fichiers .pyc copies

echo.
echo [4/4] Configuration .env...
if not exist "%WOT_PATH%\.env" (
    if exist ".env.example" (
        copy ".env.example" "%WOT_PATH%\.env"
        echo    OK: .env cree
    )
) else (
    echo    OK: .env existe
)

echo.
echo ============================================================
echo INSTALLATION TERMINEE
echo ============================================================
echo.
echo Fichiers .pyc installes dans:
echo   %TARGET_DIR%
echo.
echo IMPORTANT:
echo   1. Editez %WOT_PATH%\.env
echo   2. Ajoutez votre cle API Wargaming
echo   3. FERMEZ COMPLETEMENT WoT
echo   4. Relancez WoT
echo   5. Cherchez dans python.log:
echo      [BattleDataCollector]
echo.
pause
