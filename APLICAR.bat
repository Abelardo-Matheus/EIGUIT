@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0aplicar_e_unificar.ps1"
echo.
pause
