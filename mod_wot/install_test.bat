@echo off
REM Test si WoT charge les scripts Python
echo Installation du fichier de test...

set WOT_PATH=C:\Games\World_of_Tanks_EU
set WOT_VERSION=2.1.0.2

REM Copier dans scripts/client/ directement
copy /Y test_mod.py "%WOT_PATH%\res_mods\%WOT_VERSION%\scripts\client\test_mod.py"

echo.
echo Fichier de test installe dans:
echo %WOT_PATH%\res_mods\%WOT_VERSION%\scripts\client\test_mod.py
echo.
echo Lancez WoT et cherchez dans python.log:
echo [TEST] MOD DE TEST CHARGE !
echo.
pause
