@echo off
rem Aplica o patch do guia de instalacao no EIGUIT e publica na main do GitHub.
rem Pode ficar em Downloads: ele usa o caminho do repositorio abaixo.
setlocal
set "REPO=C:\Users\Usuario\Documents\Python\EIGUIT"
set "PATCH=%~dp0instalacao_eiguit.patch"

if not exist "%REPO%\.git" (
    echo Nao achei o repositorio em %REPO%
    set /p "REPO=Cole o caminho da pasta do EIGUIT: "
)
cd /d "%REPO%" || goto :erro

echo.
echo ==^> Guardando alteracoes locais (se houver)
git stash push -m antes-da-instalacao >nul 2>&1

echo ==^> Atualizando a main
git checkout main || goto :erro
git pull --ff-only origin main || goto :erro

echo ==^> Aplicando o guia de instalacao (2 commits)
git am --3way "%PATCH%"
if errorlevel 1 (
    git am --abort
    echo O patch nao encaixou; nada foi alterado.
    goto :erro
)

echo ==^> Publicando no GitHub
git push origin main || goto :erro

git stash pop >nul 2>&1
echo.
echo Pronto! README e instaladores publicados.
echo Obs.: o sessao_cache.json saiu do repositorio; faca login uma vez ao abrir o app.
pause
exit /b 0

:erro
git stash pop >nul 2>&1
echo.
echo ERRO: veja a mensagem acima. Nada foi publicado.
pause
exit /b 1
