# aplicar_e_unificar.ps1  -  EIGUIT: Estudo de Tempo + som profissional + unificação Core/core
# Coloque este arquivo, o APLICAR.bat e o EIGUIT_integracao.bundle na raiz do EIGUIT
# (a pasta do main.py) e dê dois cliques no APLICAR.bat.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
function Passo($t) { Write-Host "`n==> $t" -ForegroundColor Cyan }

if (-not (Test-Path 'main.py')) { throw 'Esta pasta não é a raiz do EIGUIT (não achei o main.py).' }
$bundle = Join-Path $PSScriptRoot 'EIGUIT_integracao.bundle'
if (-not (Test-Path $bundle)) { throw 'Não achei o EIGUIT_integracao.bundle ao lado deste script.' }

Passo 'Conferindo se não há alterações sem commit'
$sujo = git status --porcelain --untracked-files=no
if ($sujo) {
    git status --short --untracked-files=no
    throw 'Há alterações sem commit. Faça commit (ou git stash) e rode de novo.'
}

Passo 'Guardando um ponto de volta (branch backup-antes-integracao)'
git branch -f backup-antes-integracao HEAD | Out-Null

Passo 'Trazendo os dois commits (integração + unificação)'
git bundle verify $bundle
git pull --no-rebase --no-edit $bundle HEAD
if ($LASTEXITCODE -ne 0) { throw 'O git pull parou (conflito?). Resolva, faça o commit e rode de novo a partir do próximo passo.' }

Passo 'Acertando a pasta no disco (Windows não diferencia Core de core)'
$pasta = Get-ChildItem -Directory -Force | Where-Object { $_.Name -ieq 'core' } | Select-Object -First 1
if ($pasta -and $pasta.Name -cne 'core') {
    Rename-Item -LiteralPath $pasta.FullName -NewName '__core_tmp__'
    Rename-Item -LiteralPath (Join-Path $PSScriptRoot '__core_tmp__') -NewName 'core'
}
git checkout -- core          # repõe qualquer arquivo que o Windows apagou na troca de nome
git status --short --untracked-files=no

Passo 'Instalando dependências e rodando os testes'
$usaUv = [bool](Get-Command uv -ErrorAction SilentlyContinue)
if ($usaUv) { uv sync } else { python -m pip install soundfile scipy tinysoundfont }
$falhou = $false
foreach ($t in 'teste_estudo_tempo', 'teste_leitor_tempo', 'smoke2', 'teste_estudos_novos', 'teste_editor', 'teste_pedais') {
    Write-Host "  - $t"
    if ($usaUv) { uv run python "_validacao/$t.py" | Select-Object -Last 1 }
    else        { python "_validacao/$t.py" | Select-Object -Last 1 }
    if ($LASTEXITCODE -ne 0) { $falhou = $true; Write-Host "    FALHOU: $t" -ForegroundColor Red }
}

if ($falhou) {
    Write-Host "`nAlgum teste falhou. Nada foi enviado ao GitHub." -ForegroundColor Yellow
    Write-Host 'Para desfazer tudo:  git reset --hard backup-antes-integracao' -ForegroundColor Yellow
} else {
    Write-Host "`nTudo certo! Para enviar ao GitHub:  git push" -ForegroundColor Green
    Write-Host 'Depois pode apagar APLICAR.bat, aplicar_e_unificar.ps1 e EIGUIT_integracao.bundle.'
}
