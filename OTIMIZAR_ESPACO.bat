@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0otimizar_espaco.ps1" %*
echo.
pause
