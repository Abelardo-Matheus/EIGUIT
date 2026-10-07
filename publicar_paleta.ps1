# =============================================================================
# publicar_paleta.ps1 - Aplica a paleta de acordes + limpeza e publica no GitHub
#
# Uso: dois cliques no PUBLICAR_PALETA.bat (com esta pasta dentro da raiz do
# EIGUIT ou ao lado dela). O que faz, em ordem:
#   1. Acha o repositorio EIGUIT e guarda alteracoes locais num stash
#   2. Vai para a main, puxa o GitHub e junta os 2 commits do paleta.bundle
#   3. Tira do git (sem apagar do PC) os caches que o .gitignore ja ignora:
#      sessao_cache.json, translation_cache.json, config_eiguit.json
#   4. Roda as suites de validacao; se alguma falhar, desfaz tudo e para
#   5. Faz push para o GitHub, devolve o stash e apaga esta pasta
# =============================================================================
# Cada comando confere $LASTEXITCODE; 'Continue' evita que aviso no stderr vire erro
$ErrorActionPreference = 'Continue'
$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
$bundle = Join-Path $aqui 'paleta.bundle'

function Passo($t) { Write-Host "`n==> $t" -ForegroundColor Cyan }
function Falha($t) { Write-Host "`nERRO: $t" -ForegroundColor Red; exit 1 }

# 1. Repositorio
$raiz = $null
foreach ($c in @((Split-Path $aqui -Parent), $aqui, (Join-Path (Split-Path $aqui -Parent) 'EIGUIT'))) {
    if ($c -and (Test-Path (Join-Path $c 'main.py')) -and (Test-Path (Join-Path $c '.git'))) { $raiz = $c; break }
}
if (-not $raiz) {
    $raiz = Read-Host 'Nao achei o EIGUIT. Cole o caminho da pasta do repositorio'
    if (-not (Test-Path (Join-Path $raiz '.git'))) { Falha "$raiz nao e um repositorio git" }
}
Set-Location $raiz
Passo "Repositorio: $raiz"

$guardou = $false
if (git status --porcelain --untracked-files=no) {
    git stash push -m 'antes-da-paleta' | Out-Null
    $guardou = $true
    Write-Host 'Alteracoes locais guardadas no stash "antes-da-paleta".'
}

# 2. main atualizada + commits do pacote
Passo 'Atualizando a main e juntando a paleta de acordes'
git checkout main
git pull --ff-only origin main
if ($LASTEXITCODE -ne 0) { Falha 'nao consegui atualizar a main (pull)' }
$antes = (git rev-parse HEAD).Trim()
git pull --no-edit $bundle main
if ($LASTEXITCODE -ne 0) {
    git merge --abort 2>$null
    git reset --hard $antes | Out-Null
    Falha 'conflito ao juntar o pacote; nada foi alterado'
}

# 3. Caches fora do git, mas mantidos no PC
Passo 'Tirando caches do git (os arquivos continuam no seu PC)'
$caches = @('sessao_cache.json', 'translation_cache.json', 'config_eiguit.json')
$tirou = $false
foreach ($a in $caches) {
    if (git ls-files $a) { git rm --cached -q $a; $tirou = $true; Write-Host "  - $a" }
}
if ($tirou) { git commit -q -m 'Tira do git caches locais que o .gitignore ja ignora' }

# 4. Validacao
Passo 'Rodando as suites de validacao'
$usaUv = [bool](Get-Command uv -ErrorAction SilentlyContinue)
$suites = 'teste_paleta_acordes', 'teste_blocos', 'teste_acordes', 'smoke2',
          'teste_responsivo', 'teste_cabecalho', 'teste_preferencias'
foreach ($s in $suites) {
    $arq = "_validacao/$s.py"
    if (-not (Test-Path $arq)) { continue }
    Write-Host "  $s ..." -NoNewline
    if ($usaUv) { $saida = & uv run python $arq 2>&1 } else { $saida = & python $arq 2>&1 }
    if ($LASTEXITCODE -ne 0) {
        Write-Host ' FALHOU' -ForegroundColor Red
        $saida | Select-Object -Last 25 | ForEach-Object { Write-Host "    $_" }
        git reset --hard $antes | Out-Null
        if ($guardou) { git stash pop | Out-Null }
        Falha "a suite $s falhou; a main voltou a como estava e nada foi publicado"
    }
    Write-Host ' ok' -ForegroundColor Green
}

# 5. Publicar
Passo 'Publicando no GitHub'
git push origin main
if ($LASTEXITCODE -ne 0) { Falha 'o push falhou (login do GitHub?). Os commits ficaram na sua main local; rode "git push" depois.' }
if ($guardou) {
    git stash pop
    if ($LASTEXITCODE -ne 0) { Write-Host 'Aviso: o stash "antes-da-paleta" nao voltou sozinho; rode "git stash pop".' -ForegroundColor Yellow }
}

Passo 'Pronto! Paleta de acordes publicada na main.'
git log --oneline -4
# Esta pasta ja cumpriu o papel
Set-Location $raiz
Start-Process -WindowStyle Hidden powershell -ArgumentList '-NoProfile', '-Command', "Start-Sleep 2; Remove-Item -Recurse -Force '$aqui'"
