# =============================================================================
# limpeza_eiguit.ps1 - Limpeza de arquivos e codigo nao usado no EIGUIT
#
# Uso (na raiz do repositorio):
#   powershell -ExecutionPolicy Bypass -File .\limpeza_eiguit.ps1
#   powershell -ExecutionPolicy Bypass -File .\limpeza_eiguit.ps1 -Dependencias
#
# O que faz:
#   - Cria a branch "limpeza-codigo" (a main nao e tocada)
#   - Faz 3 commits separados, um por etapa, para poder reverter so uma se precisar
#   - Etapa 1: tira do git node_modules, __pycache__, caches e binarios soltos
#   - Etapa 2: apaga scripts one-shot e modulos mortos; corrige 2 bugs
#   - Etapa 3: remove imports nao usados com ruff e valida (compileall + F821)
#   - Opcional (-Dependencias): limpa o pyproject.toml com uv
# =============================================================================
param(
    [string]$Branch = 'limpeza-codigo',
    [switch]$Dependencias,
    [switch]$SemConfirmar
)

$ErrorActionPreference = 'Stop'

$GitExe = (Get-Command git -CommandType Application | Select-Object -First 1).Source

function Invoke-Git {
    # Avisos do git no stderr (ex.: LF/CRLF) nao devem abortar o script
    $ErrorActionPreference = 'Continue'
    & $GitExe @args
    if ($LASTEXITCODE -ne 0) { throw "git $($args -join ' ') falhou (codigo $LASTEXITCODE)" }
}

function Titulo($texto) {
    Write-Host ''
    Write-Host "=== $texto ===" -ForegroundColor Cyan
}

function Remover-DoGit([string[]]$caminhos) {
    # Apaga do git e do disco; ignora o que ja nao existir
    Invoke-Git rm -r -q --ignore-unmatch -- @caminhos
}

function Parar-DeVersionar([string[]]$caminhos) {
    # Tira do git mas MANTEM o arquivo no seu computador
    Invoke-Git rm -r -q --cached --ignore-unmatch -- @caminhos
}

function Editar-Texto([string]$arquivo, [scriptblock]$transformacao) {
    # Le e grava preservando UTF-8 sem BOM e as quebras de linha originais
    $caminho = (Resolve-Path -LiteralPath $arquivo).Path
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    $antes = [System.IO.File]::ReadAllText($caminho, $utf8)
    $depois = & $transformacao $antes
    if ($depois -ne $antes) {
        [System.IO.File]::WriteAllText($caminho, $depois, $utf8)
        return $true
    }
    return $false
}

function Rodar-Ruff([string[]]$argumentos) {
    if (Get-Command uvx -ErrorAction SilentlyContinue) {
        & uvx ruff @argumentos | Out-Host
    } elseif (Get-Command ruff -ErrorAction SilentlyContinue) {
        & ruff @argumentos | Out-Host
    } else {
        & python -m ruff @argumentos | Out-Host
    }
    return $LASTEXITCODE
}

# -----------------------------------------------------------------------------
# Verificacoes iniciais
# -----------------------------------------------------------------------------
if (-not (Test-Path -LiteralPath 'main.py') -or -not (Test-Path -LiteralPath 'core')) {
    throw 'Rode este script na raiz do repositorio EIGUIT (onde fica o main.py).'
}
# Arquivos novos nao rastreados (como este script) nao atrapalham;
# so bloqueia se houver alteracoes em arquivos que ja estao no git
$pendentes = @(git status --porcelain --untracked-files=no)
if ($pendentes.Count -gt 0) {
    Write-Host 'Existem alteracoes nao commitadas em arquivos do repositorio:' -ForegroundColor Yellow
    $pendentes | ForEach-Object { Write-Host "  $_" }
    Write-Host ''
    Write-Host 'Faca commit (git add -A; git commit -m "wip") ou guarde (git stash) e rode de novo.'
    exit 1
}

Write-Host 'Este script vai criar a branch' -NoNewline
Write-Host " $Branch " -ForegroundColor Yellow -NoNewline
Write-Host 'e fazer 3 commits de limpeza nela.'
Write-Host 'A branch atual nao sera alterada.'
if (-not $SemConfirmar) {
    $resp = Read-Host 'Continuar? (s/n)'
    if ($resp -notmatch '^[sSyY]') { Write-Host 'Cancelado.'; exit 0 }
}

$branchOriginal = (git rev-parse --abbrev-ref HEAD).Trim()
Invoke-Git checkout -q -b $Branch

# -----------------------------------------------------------------------------
# ETAPA 1 - Arquivos que nao deveriam estar no git
# -----------------------------------------------------------------------------
Titulo 'Etapa 1/3: arquivos versionados indevidamente'

# Dependencias e bytecode: saem do git, continuam no seu disco
Parar-DeVersionar @('web_frontend/node_modules')
$bytecode = @(git ls-files | Where-Object { $_ -match '(^|/)__pycache__/|\.pyc$' })
if ($bytecode.Count -gt 0) { Parar-DeVersionar $bytecode }

# Estado local do usuario: sai do git, continua no seu disco
Parar-DeVersionar @(
    'sessao_cache.json',
    'translation_cache.json',
    'config_eiguit.json',
    'Perfis/Meu_Setupsss.json'
)

# Binarios soltos, backups e assets sem referencia no codigo
Remover-DoGit @(
    'rec_a5915a3e.wav',
    '1.png',
    'audio.rar',
    'Estudos.rar',
    '_preview_design',
    'assets/images/fundo_jogo.png',
    'assets/audio/sonivox.sf2',
    'assets/audio/teste_ia.wav',
    'assets/audio/teste_ia.ogg',
    'assets/audio/tick.ogg',
    'assets/audio/tick_high.ogg',
    'assets/fila.txt',
    'tasks_docstrings.json',
    'dist'
)

# Garante que nao voltem para o git
$novosIgnores = @(
    '',
    '# Estado local do app (gerado em tempo de execucao)',
    'sessao_cache.json',
    'translation_cache.json',
    'config_eiguit.json',
    'Perfis/Meu_*.json',
    'rec_*.wav',
    'temp_recording.wav',
    '*.rar',
    '_preview_design/'
)
$ignoreAtual = Get-Content -LiteralPath '.gitignore' -Raw
$faltando = $novosIgnores | Where-Object { $_ -eq '' -or $_.StartsWith('#') -or ($ignoreAtual -notmatch [regex]::Escape($_)) }
if ($faltando | Where-Object { $_ -and -not $_.StartsWith('#') }) {
    Add-Content -LiteralPath '.gitignore' -Value $faltando -Encoding utf8
}
Invoke-Git add .gitignore
Invoke-Git commit -q -m 'chore: remove node_modules, pycache, caches e binarios nao usados do git'
Write-Host 'OK' -ForegroundColor Green

# -----------------------------------------------------------------------------
# ETAPA 2 - Scripts one-shot e modulos mortos + 2 correcoes de bug
# -----------------------------------------------------------------------------
Titulo 'Etapa 2/3: scripts e modulos sem uso'

Remover-DoGit @(
    # Scripts de refatoracao/investigacao que ja cumpriram o papel
    'fix_imports.py',
    'fix_imports2.py',
    'fix_imports3.py',
    'refactor_clean_arch.py',
    'docstring_generator.py',
    'utils',
    # Jogos vazios
    'Jogos/jogo3.py',
    'Jogos/jogo4.py',
    # Modulos substituidos por versoes novas e nunca importados
    'core/modulos/modulo_synth.py',
    'core/modulos/modulo_synth_guitarra.py',
    'core/modulos/modulo_leitor_midi.py',
    'core/constantes_ui.py',
    'ui/blocks/painel_caged.py',
    'ui/renderizador_criador_tab.py',
    # Importado mas nunca instanciado (e o que so ele usava)
    'ui/renderizador_tablatura.py',
    'core/modulos/gerenciador_servicos_ia.py',
    # Workflow pygbag que nao consegue compilar este app
    '.github/workflows/deploy.yml'
)

# O import do renderizador removido
$mudou = Editar-Texto 'ui/renderizador_ui.py' {
    param($t) $t -replace '(?m)^from ui\.renderizador_tablatura import RenderizadorTablatura\r?\n', ''
}
if ($mudou) { Write-Host '  - import de RenderizadorTablatura removido de ui/renderizador_ui.py' }

# BUG 1: leitor_midi usa os.path mas nunca importa os -> ler() sempre falhava
$mudou = Editar-Texto 'core/modulos/leitor_midi.py' {
    param($t)
    if ($t -match '(?m)^import os\s*$') { return $t }
    $nl = if ($t -match "`r`n") { "`r`n" } else { "`n" }
    $t -replace '(?m)^import struct', ("import os" + $nl + "import struct")
}
if ($mudou) { Write-Host '  - BUG corrigido: faltava "import os" em core/modulos/leitor_midi.py' }

# BUG 2: arquivo " G#.wav" com espaco no nome -> a nota G# nunca carregava
$gAntigo = 'assets/audio/ G#.wav'
$gNovo = 'assets/audio/G#.wav'
if ((git ls-files -- $gAntigo) -and -not (Test-Path -LiteralPath $gNovo)) {
    Invoke-Git mv -- $gAntigo $gNovo
    Write-Host '  - BUG corrigido: " G#.wav" renomeado para "G#.wav"'
}

Invoke-Git add -u -- ui core
Invoke-Git commit -q -m 'refactor: remove scripts one-shot e modulos mortos; corrige import os e G#.wav'
Write-Host 'OK' -ForegroundColor Green

# -----------------------------------------------------------------------------
# ETAPA 3 - Imports nao usados (ruff) + validacao
# -----------------------------------------------------------------------------
Titulo 'Etapa 3/3: imports nao usados'

# So correcoes "seguras" do ruff: nao mexe em re-exports de __init__.py
# nem em imports dentro de try/except (checagem de disponibilidade)
$null = Rodar-Ruff @('check', '.', '--exclude', 'web_frontend,_validacao',
                     '--select', 'F401', '--fix', '--quiet', '--exit-zero')

Write-Host 'Validando...'
& python -m compileall -q -x 'node_modules|\.venv|venv' . | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host 'ERRO de sintaxe apos a limpeza. Veja a saida acima.' -ForegroundColor Red
    Write-Host "Para desfazer tudo: git checkout $branchOriginal; git branch -D $Branch"
    exit 1
}
$codF821 = Rodar-Ruff @('check', '.', '--exclude', 'web_frontend',
                         '--select', 'F821', '--output-format', 'concise')
if ($codF821 -ne 0) {
    Write-Host 'ATENCAO: ha nomes indefinidos (F821) listados acima. Confira antes de fazer merge.' -ForegroundColor Yellow
}

if (git status --porcelain --untracked-files=no) {
    Invoke-Git add -u
    Invoke-Git commit -q -m 'style: remove imports nao usados (ruff F401)'
}
Write-Host 'OK' -ForegroundColor Green

# -----------------------------------------------------------------------------
# OPCIONAL - Dependencias do pyproject.toml
# -----------------------------------------------------------------------------
if ($Dependencias) {
    Titulo 'Extra: dependencias'
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host 'uv nao encontrado; pulando.' -ForegroundColor Yellow
    } else {
        & uv remove mss pydub pyautogui pyinstaller
        & uv add --dev pyautogui pyinstaller
        if ($LASTEXITCODE -eq 0) {
            Invoke-Git add pyproject.toml uv.lock
            Invoke-Git commit -q -m 'build: remove deps sem uso; pyautogui e pyinstaller viram dev'
            Write-Host 'OK' -ForegroundColor Green
        }
    }
}

# -----------------------------------------------------------------------------
# Resumo
# -----------------------------------------------------------------------------
Titulo 'Pronto'
Invoke-Git --no-pager log --oneline "$branchOriginal..HEAD"
Write-Host ''
Write-Host 'Proximos passos:'
Write-Host '  1. Rode o app (uv run python main.py) e teste as abas principais.'
Write-Host "  2. Se estiver tudo certo:  git checkout $branchOriginal; git merge $Branch"
Write-Host "  3. Para desfazer tudo:     git checkout $branchOriginal; git branch -D $Branch"
Write-Host ''
Write-Host 'Obs.: node_modules e os caches JSON continuam no seu disco, so sairam do git.'
