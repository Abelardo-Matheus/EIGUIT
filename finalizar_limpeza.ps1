# =============================================================================
# finalizar_limpeza.ps1 - Sincroniza, testa, corrige e publica a limpeza do EIGUIT
#
# Uso (na raiz do repositorio):
#   powershell -ExecutionPolicy Bypass -File .\finalizar_limpeza.ps1
#
# O que faz, em ordem:
#   1. Guarda alteracoes locais pendentes num stash (nada e perdido)
#   2. Vai para a main e faz pull do GitHub
#   3. Faz merge da branch limpeza-codigo (se ainda houver algo a juntar)
#   4. Testa o import de todos os modulos do app
#      -> se algum modulo apagado ainda for usado, restaura do historico sozinho
#   5. Faz commit da correcao (se houve) e push para o GitHub
# =============================================================================
param(
    [string]$Principal = 'main',
    [string]$BranchLimpeza = 'limpeza-codigo',
    [switch]$SemPush
)

$ErrorActionPreference = 'Stop'
$GitExe = (Get-Command git -CommandType Application | Select-Object -First 1).Source

function Invoke-Git {
    $ErrorActionPreference = 'Continue'
    & $GitExe @args
    if ($LASTEXITCODE -ne 0) { throw "git $($args -join ' ') falhou (codigo $LASTEXITCODE)" }
}
function Titulo($t) { Write-Host ''; Write-Host "=== $t ===" -ForegroundColor Cyan }
function Parar($msg) { Write-Host ''; Write-Host $msg -ForegroundColor Red; exit 1 }

if (-not (Test-Path -LiteralPath 'main.py') -or -not (Test-Path -LiteralPath '.git')) {
    Parar 'Rode este script na raiz do repositorio EIGUIT (onde fica o main.py).'
}

# Python do projeto: prefere a .venv, depois uv, depois o python do PATH
$Python = $null
foreach ($c in @('.venv\Scripts\python.exe', '.venv/bin/python')) {
    if (Test-Path -LiteralPath $c) { $Python = @((Resolve-Path -LiteralPath $c).Path); break }
}
if (-not $Python) {
    if (Get-Command uv -ErrorAction SilentlyContinue) { $Python = @('uv', 'run', 'python') }
    else { $Python = @('python') }
}

# -----------------------------------------------------------------------------
# Teste de fumaca: importa todos os modulos do app e lista os que faltam
# -----------------------------------------------------------------------------
$testePy = @'
import os, sys, ast, importlib
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
raiz = os.getcwd()
sys.path.insert(0, raiz)
PACOTES = ["core", "ui", "audio", "Estudos", "Jogos", "config", "BD", "DragDrop"]
locais = set(PACOTES) | {f[:-3] for f in os.listdir(".") if f.endswith(".py")}

def existe(mod):
    base = os.path.join(raiz, *mod.split("."))
    return os.path.isfile(base + ".py") or os.path.isdir(base)

def eh_pasta(mod):
    return os.path.isdir(os.path.join(raiz, *mod.split(".")))

arquivos = ["main.py"]
for pac in PACOTES:
    for r, _, arqs in os.walk(pac):
        if "__pycache__" not in r:
            arquivos += [os.path.join(r, a) for a in arqs if a.endswith(".py")]

# 1) Checagem estatica: todo import de modulo local precisa apontar para um arquivo
#    que existe (inclui imports dentro de funcoes). Nao depende das bibliotecas.
faltas = set()
for arq in arquivos:
    try:
        arvore = ast.parse(open(arq, encoding="utf-8-sig").read())
    except SyntaxError as e:
        print(f"ERRO:{arq}: erro de sintaxe na linha {e.lineno}")
        continue
    for n in ast.walk(arvore):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name.split(".")[0] in locais and not existe(a.name):
                    faltas.add(a.name)
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
            if n.module.split(".")[0] not in locais:
                continue
            if not existe(n.module):
                faltas.add(n.module)
            elif eh_pasta(n.module) and not os.path.isfile(os.path.join(raiz, *n.module.split("."), "__init__.py")):
                for a in n.names:
                    if a.name != "*" and not existe(n.module + "." + a.name):
                        faltas.add(n.module + "." + a.name)

# 2) Teste real de import (pega nomes que sumiram de dentro dos modulos)
modulos = sorted({a[:-3].replace(os.sep, ".").replace("/", ".") for a in arquivos})
modulos = [m[:-9] if m.endswith(".__init__") else m for m in modulos]
erros, avisos = [], 0
for m in modulos:
    try:
        importlib.import_module(m)
    except ModuleNotFoundError as e:
        if (e.name or "").split(".")[0] in locais:
            faltas.add(e.name)
        else:
            avisos += 1
    except ImportError as e:
        if "cannot import name" in str(e) and any(p in str(e) for p in locais):
            erros.append(f"{m}: {e}")
        else:
            avisos += 1
    except BaseException:
        avisos += 1
for f in sorted(faltas):
    print("FALTA:" + f)
for e in erros:
    print("ERRO:" + e)
print(f"TESTADOS:{len(modulos)} AVISOS:{avisos}")
'@
$arquivoTeste = Join-Path ([System.IO.Path]::GetTempPath()) 'eiguit_teste_imports.py'
[System.IO.File]::WriteAllText($arquivoTeste, $testePy, (New-Object System.Text.UTF8Encoding($false)))

function Testar-Imports {
    $exe = $Python[0]
    $resto = @()
    if ($Python.Count -gt 1) { $resto = $Python[1..($Python.Count - 1)] }
    $ErrorActionPreference = 'Continue'
    $saida = & $exe @resto $arquivoTeste 2>$null
    return @($saida)
}

function Restaurar-Modulo([string]$modulo) {
    # Procura o commit que apagou o arquivo e traz de volta a versao anterior
    $base = $modulo -replace '\.', '/'
    foreach ($caminho in @("$base.py", "$base/__init__.py")) {
        $commit = (& $GitExe rev-list -n 1 HEAD -- $caminho) | Select-Object -First 1
        if ($commit) {
            Invoke-Git checkout "$commit^" -- $caminho
            Write-Host "  + restaurado: $caminho" -ForegroundColor Yellow
            return $true
        }
    }
    return $false
}

# -----------------------------------------------------------------------------
# 1. Guardar alteracoes locais
# -----------------------------------------------------------------------------
Titulo '1/5 Alteracoes locais'
$pendentes = @(& $GitExe status --porcelain --untracked-files=no)
$fezStash = $false
if ($pendentes.Count -gt 0) {
    $pendentes | ForEach-Object { Write-Host "  $_" }
    $marca = 'antes-finalizar-limpeza ' + (Get-Date -Format 'yyyy-MM-dd HH:mm')
    Invoke-Git stash push -q -m $marca
    $fezStash = $true
    Write-Host "Guardadas no stash '$marca' (recupere com: git stash pop)" -ForegroundColor Yellow
} else {
    Write-Host 'Nenhuma alteracao pendente.'
}

# -----------------------------------------------------------------------------
# 2. Main atualizada com o GitHub
# -----------------------------------------------------------------------------
Titulo "2/5 Atualizando '$Principal' com o GitHub"
Invoke-Git checkout -q $Principal
Invoke-Git fetch -q origin
Invoke-Git pull -q --no-rebase --no-edit origin $Principal

# -----------------------------------------------------------------------------
# 3. Merge da branch de limpeza
# -----------------------------------------------------------------------------
Titulo "3/5 Merge de '$BranchLimpeza'"
& $GitExe show-ref --verify --quiet "refs/heads/$BranchLimpeza"
if ($LASTEXITCODE -eq 0) {
    $ErrorActionPreference = 'Continue'
    & $GitExe merge -q --no-edit $BranchLimpeza
    $codMerge = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($codMerge -ne 0) {
        Parar ("Conflito no merge. Resolva os arquivos marcados e rode 'git commit', " +
               "ou cancele com 'git merge --abort'. Depois rode este script de novo.")
    }
} else {
    Write-Host "Branch '$BranchLimpeza' nao existe localmente (ja foi juntada pelo GitHub)."
}

# -----------------------------------------------------------------------------
# 4. Teste de imports com auto-correcao
# -----------------------------------------------------------------------------
Titulo '4/5 Testando os imports do app'
Write-Host "Python: $($Python -join ' ')"
$restaurados = @()
for ($rodada = 1; $rodada -le 6; $rodada++) {
    $saida = Testar-Imports
    $faltas = @($saida | Where-Object { $_ -like 'FALTA:*' } | ForEach-Object { $_.Substring(6) })
    $erros = @($saida | Where-Object { $_ -like 'ERRO:*' } | ForEach-Object { $_.Substring(5) })
    $resumo = $saida | Where-Object { $_ -like 'TESTADOS:*' }
    if (-not $resumo) { Parar 'O teste de imports nao rodou. Verifique se o Python da .venv funciona.' }
    if ($faltas.Count -eq 0) { break }
    Write-Host "Modulos ainda usados mas apagados: $($faltas -join ', ')"
    $algum = $false
    foreach ($f in $faltas) {
        if ($restaurados -notcontains $f -and (Restaurar-Modulo $f)) { $restaurados += $f; $algum = $true }
    }
    if (-not $algum) { Parar "Nao consegui restaurar: $($faltas -join ', '). Nada foi enviado ao GitHub." }
}
if ($faltas.Count -gt 0) { Parar 'Ainda faltam modulos apos 6 tentativas. Nada foi enviado ao GitHub.' }
if ($erros.Count -gt 0) {
    $erros | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    Parar 'Ha imports quebrados (nomes que nao existem mais). Nada foi enviado ao GitHub.'
}
Write-Host "OK ($resumo)" -ForegroundColor Green
Write-Host '(AVISOS = modulos que nao abrem fora da tela cheia ou dependem de algo externo; e normal)'

if ($restaurados.Count -gt 0) {
    Invoke-Git add -A -- core ui audio Estudos Jogos config BD DragDrop
    Invoke-Git commit -q -m "fix: restaura modulos ainda usados ($($restaurados -join ', '))"
    Write-Host 'Commit de correcao criado.' -ForegroundColor Green
}

# -----------------------------------------------------------------------------
# 5. Push
# -----------------------------------------------------------------------------
Titulo '5/5 Enviando para o GitHub'
$aFrente = [int]((& $GitExe rev-list --count "origin/$Principal..$Principal") | Select-Object -First 1)
if ($SemPush) {
    Write-Host "Push pulado (-SemPush). Commits locais a enviar: $aFrente"
} elseif ($aFrente -gt 0) {
    Invoke-Git push origin $Principal
    Write-Host "Enviados $aFrente commit(s)." -ForegroundColor Green
} else {
    Write-Host 'GitHub ja esta atualizado, nada a enviar.'
}

# Limpeza da branch local ja juntada
& $GitExe show-ref --verify --quiet "refs/heads/$BranchLimpeza"
if ($LASTEXITCODE -eq 0) {
    & $GitExe merge-base --is-ancestor $BranchLimpeza $Principal
    if ($LASTEXITCODE -eq 0) { Invoke-Git branch -q -d $BranchLimpeza; Write-Host "Branch local '$BranchLimpeza' apagada (ja esta na $Principal)." }
}

Remove-Item -LiteralPath $arquivoTeste -ErrorAction SilentlyContinue

Titulo 'Pronto'
Invoke-Git --no-pager log --oneline -5
if ($fezStash) {
    Write-Host ''
    Write-Host 'Suas alteracoes anteriores estao guardadas no stash:' -ForegroundColor Yellow
    & $GitExe stash list | Select-Object -First 3 | ForEach-Object { Write-Host "  $_" }
    Write-Host '  Ver conteudo:  git stash show -p'
    Write-Host '  Reaplicar:     git stash pop'
    Write-Host '  (se reaplicar e voltar o erro do renderizador_tablatura, apague a linha 11 do ui/renderizador_ui.py)'
}
Write-Host ''
Write-Host 'Agora rode o app:  .venv\Scripts\python.exe main.py'
