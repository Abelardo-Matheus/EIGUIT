@echo off
rem Instala o EIGUIT: dependencias, URL do banco e atalhos (veja instalar.ps1)
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar.ps1" %*
echo.
pause
