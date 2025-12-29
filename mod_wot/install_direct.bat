@echo off
REM Installation directe dans res_mods (plus fiable que .wotmod)
REM Usage: install_direct.bat

echo ============================================================
echo INSTALLATION DIRECTE - MOD BATTLE DATA COLLECTOR
echo ============================================================
echo.

set WOT_PATH=C:\Games\World_of_Tanks_EU
set WOT_VERSION=2.1.0.2

echo [1/4] Verification de WoT...
if not exist "%WOT_PATH%" (
    echo ERREUR: WoT non trouve
    pause
    exit /b 1
)
echo    OK: %WOT_PATH%

echo.
echo [2/4] Creation de la structure res_mods...
set TARGET_DIR=%WOT_PATH%\res_mods\%WOT_VERSION%\scripts\client\gui\mods\battle_data_collector

if not exist "%TARGET_DIR%" (
    mkdir "%TARGET_DIR%"
    echo    OK: Dossier cree
) else (
    echo    OK: Dossier existe
)

echo.
echo [3/4] Copie des fichiers Python...
set SOURCE_DIR=res_mods\scripts\client\gui\mods\battle_data_collector

if not exist "%SOURCE_DIR%" (
    echo ERREUR: Dossier source non trouve: %SOURCE_DIR%
    pause
    exit /b 1
)

xcopy /Y /Q "%SOURCE_DIR%\*.py" "%TARGET_DIR%\"
if errorlevel 1 (
    echo ERREUR: Impossible de copier les fichiers
    pause
    exit /b 1
)
echo    OK: Fichiers copies

echo.
echo [4/4] Copie du fichier .env...
if exist ".env" (
    copy /Y ".env" "%WOT_PATH%\"
    echo    OK: .env copie
) else (
    echo    ATTENTION: .env non trouve
    if exist ".env.example" (
        copy ".env.example" "%WOT_PATH%\.env"
        echo    OK: .env.example copie en .env
        echo    IMPORTANT: Editez %WOT_PATH%\.env
    )
)

echo.
echo ============================================================
echo INSTALLATION TERMINEE
echo ============================================================
echo.
echo Fichiers installes dans:
echo   %TARGET_DIR%
echo.
echo Fichier .env:
echo   %WOT_PATH%\.env
echo.
echo PROCHAINES ETAPES:
echo   1. Editez %WOT_PATH%\.env
echo   2. Ajoutez votre cle API Wargaming
echo   3. Lancez World of Tanks
echo   4. Verifiez python.log
echo.
pause
