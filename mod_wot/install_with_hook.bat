@echo off
REM Installation avec hook de chargement
echo ============================================================
echo INSTALLATION AVEC HOOK
echo ============================================================

set WOT_PATH=C:\Games\World_of_Tanks_EU
set WOT_VERSION=2.1.0.2

echo [1/2] Installation des fichiers du mod...
set TARGET_DIR=%WOT_PATH%\res_mods\%WOT_VERSION%\scripts\client\gui\mods\mod_battle_data_collector
xcopy /Y /Q "res_mods\scripts\client\gui\mods\mod_battle_data_collector\*.py" "%TARGET_DIR%\"
echo    OK

echo.
echo [2/2] Installation du hook de chargement...
copy /Y "mod_battledata_hook.py" "%WOT_PATH%\res_mods\%WOT_VERSION%\scripts\client\gui\mods\"
echo    OK

echo.
echo ============================================================
echo INSTALLATION TERMINEE
echo ============================================================
echo.
echo Fichiers installes:
echo   %TARGET_DIR%
echo.
echo Hook installe:
echo   %WOT_PATH%\res_mods\%WOT_VERSION%\scripts\client\gui\mods\mod_battledata_hook.py
echo.
echo Relancez WoT et verifiez python.log
echo.
pause
