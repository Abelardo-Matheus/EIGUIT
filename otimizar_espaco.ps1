# =============================================================================
# otimizar_espaco.ps1 - Libera espaco no EIGUIT tirando o que o programa nao usa
#
# Uso (dois cliques no OTIMIZAR_ESPACO.bat, ou na raiz do EIGUIT):
#   powershell -ExecutionPolicy Bypass -File .\otimizar_espaco.ps1            # pergunta grupo a grupo
#   powershell -ExecutionPolicy Bypass -File .\otimizar_espaco.ps1 -SoMostrar # so lista, nao mexe
#   powershell -ExecutionPolicy Bypass -File .\otimizar_espaco.ps1 -Tudo      # aceita todos os grupos
#   ... -Dependencias  tambem limpa o pyproject (uv): tira o pydub (nao usado) e
#                      passa pyinstaller/pyautogui/mss para dependencias de desenvolvimento
#
# Nada e apagado de vez: tudo vai para a LIXEIRA do Windows. Se precisar, e so
# restaurar de la. Nao toca em .venv, Perfis, assets em uso, nem no seu codigo.
# =============================================================================
param(
    [switch]$SoMostrar,
    [switch]$Tudo,
    [switch]$Dependencias
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path -LiteralPath 'main.py')) { throw 'Rode na raiz do EIGUIT (onde fica o main.py).' }
Add-Type -AssemblyName Microsoft.VisualBasic

function Tamanho([string]$caminho) {
    if (-not (Test-Path -LiteralPath $caminho)) { return 0 }
    $item = Get-Item -LiteralPath $caminho -Force
    if ($item.PSIsContainer) {
        $soma = (Get-ChildItem -LiteralPath $caminho -Recurse -Force -File -ErrorAction SilentlyContinue |
                 Measure-Object -Property Length -Sum).Sum
        if ($soma) { return [int64]$soma } else { return 0 }
    }
    return [int64]$item.Length
}

function Legivel([int64]$bytes) {
    if ($bytes -ge 1GB) { return '{0:N2} GB' -f ($bytes / 1GB) }
    if ($bytes -ge 1MB) { return '{0:N1} MB' -f ($bytes / 1MB) }
    if ($bytes -ge 1KB) { return '{0:N0} KB' -f ($bytes / 1KB) }
    return "$bytes B"
}

function Para-Lixeira([string]$caminho) {
    $completo = (Resolve-Path -LiteralPath $caminho).Path
    $opcoes = [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs
    $lixeira = [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin
    if ((Get-Item -LiteralPath $completo -Force).PSIsContainer) {
        [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory($completo, $opcoes, $lixeira)
    } else {
        [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile($completo, $opcoes, $lixeira)
    }
}

# Pastas de cache espalhadas (fora dos ambientes Python)
$caches = Get-ChildItem -Path . -Recurse -Force -Directory -ErrorAction SilentlyContinue |
    Where-Object {
        ($_.Name -in '__pycache__', '.ruff_cache', '.pytest_cache') -and
        ($_.FullName -notmatch '[\\/](\.venv|venv_novo|venv_ia|TranscriptionService|node_modules)[\\/]')
    } | ForEach-Object { Resolve-Path -LiteralPath $_.FullName -Relative }

$grupos = @(
    @{ Nome = 'Builds antigos do PyInstaller (recriados com pyinstaller quando precisar)';
       Itens = @('build', 'dist') },
    @{ Nome = 'Ambiente Python duplicado (o VS Code e o uv usam o .venv)';
       Itens = @('venv_novo') },
    @{ Nome = 'Caches do Python e do ruff (o Python recria sozinho)';
       Itens = @($caches) },
    @{ Nome = 'Arquivos da atualizacao ja aplicada';
       Itens = @('EIGUIT_atualizacao.bundle', 'ATUALIZAR.bat', 'atualizar.ps1') },
    @{ Nome = 'Scripts de limpeza antigos (ja rodados)';
       Itens = @('limpeza_eiguit.ps1', 'finalizar_limpeza.ps1') },
    @{ Nome = 'Sobras: robo de cliques, tablatura exportada solta, simbolos de depuracao, pastas vazias';
       Itens = @('robo_testes_ui.py', 'Nova_Música.txt', 'assets\bin\fluidsynth\libinstpatch-2.pdb',
                 'Ideias', 'Claude outputs') }
)

Write-Host ''
Write-Host '=== EIGUIT - liberar espaco ===' -ForegroundColor Cyan
if ($SoMostrar) { Write-Host '(modo -SoMostrar: nada sera movido)' -ForegroundColor Yellow }

$liberado = [int64]0
foreach ($g in $grupos) {
    $existentes = @($g.Itens | Where-Object { $_ -and (Test-Path -LiteralPath $_) })
    if (-not $existentes) { continue }
    $total = [int64]0
    foreach ($i in $existentes) { $total += Tamanho $i }
    Write-Host ''
    Write-Host ("{0}  [{1}]" -f $g.Nome, (Legivel $total)) -ForegroundColor White
    foreach ($i in $existentes | Select-Object -First 12) {
        Write-Host ("   - {0}  ({1})" -f $i, (Legivel (Tamanho $i))) -ForegroundColor DarkGray
    }
    if ($existentes.Count -gt 12) { Write-Host ("   ... e mais {0}" -f ($existentes.Count - 12)) -ForegroundColor DarkGray }
    if ($SoMostrar) { continue }
    $ok = $Tudo
    if (-not $ok) {
        $resp = Read-Host '   Mandar para a lixeira? (s/N)'
        $ok = $resp -match '^(s|sim|y|yes)$'
    }
    if (-not $ok) { Write-Host '   mantido.' -ForegroundColor DarkYellow; continue }
    foreach ($i in $existentes) {
        try { Para-Lixeira $i } catch { Write-Host "   nao consegui mover $i : $_" -ForegroundColor Red }
    }
    $liberado += $total
    Write-Host '   enviado para a lixeira.' -ForegroundColor Green
}

if ($Dependencias -and -not $SoMostrar) {
    Write-Host ''
    Write-Host '=== Dependencias (uv) ===' -ForegroundColor Cyan
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv remove pydub
        uv remove pyinstaller pyautogui mss
        uv add --dev pyinstaller pyautogui mss
        uv sync
    } else {
        Write-Host 'uv nao encontrado no PATH: pulei esta etapa.' -ForegroundColor Yellow
    }
}

Write-Host ''
Write-Host ("Pronto. Espaco liberado: {0} (esvazie a lixeira para recuperar de vez)." -f (Legivel $liberado)) -ForegroundColor Cyan
