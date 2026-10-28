# =============================================================================
# instalar.ps1 - Instala o EIGUIT no Windows 10/11
#
# Uso: dois cliques no INSTALAR.bat (na pasta do EIGUIT), ou no PowerShell:
#     powershell -ExecutionPolicy Bypass -File instalar.ps1
#     powershell -ExecutionPolicy Bypass -File instalar.ps1 -Desinstalar
#
# O que faz, em ordem:
#   1. Instala o uv (gerenciador de Python do projeto), se ainda nao houver
#   2. Cria o ambiente .venv com o Python 3.12 e as versoes do uv.lock
#      (o uv baixa o Python 3.12 sozinho se ele nao estiver instalado)
#   3. Pergunta a URL do banco (login) e grava em %APPDATA%\EIGUIT\banco.txt
#   4. Cria atalhos "EIGUIT" na Area de Trabalho e no Menu Iniciar
#
# Nada aqui precisa de administrador. Os DLLs do FluidSynth e os SoundFonts
# ja vem dentro de assets\, entao nao ha mais nada para baixar.
# =============================================================================
param([switch]$Desinstalar)

# Cada passo confere o proprio resultado; 'Continue' evita que aviso no
# stderr de um programa externo vire erro fatal no PowerShell 5
$ErrorActionPreference = 'Continue'
$Raiz = Split-Path -Parent $MyInvocation.MyCommand.Path
$Shell = New-Object -ComObject WScript.Shell
$AtalhoMesa = Join-Path ([Environment]::GetFolderPath('Desktop')) 'EIGUIT.lnk'
$AtalhoMenu = Join-Path ([Environment]::GetFolderPath('Programs')) 'EIGUIT.lnk'
$PastaConfig = Join-Path $env:APPDATA 'EIGUIT'

function Passo($t) { Write-Host "`n==> $t" -ForegroundColor Cyan }
function Aviso($t) { Write-Host $t -ForegroundColor Yellow }
function Falha($t) {
    Write-Host "`nERRO: $t" -ForegroundColor Red
    exit 1
}

# --------------------------------------------------------------- desinstalar
if ($Desinstalar) {
    Passo 'Removendo o EIGUIT do sistema'
    Remove-Item $AtalhoMesa, $AtalhoMenu -Force -ErrorAction SilentlyContinue
    Remove-Item (Join-Path $Raiz '.venv') -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host 'Atalhos e .venv removidos.'
    Write-Host "Seus perfis e a URL do banco continuam em $PastaConfig (apague a pasta se quiser)."
    exit 0
}

if (-not (Test-Path (Join-Path $Raiz 'main.py'))) {
    Falha 'rode este script de dentro da pasta do EIGUIT'
}
Set-Location $Raiz

# ------------------------------------------------------------------- 1. uv
Passo 'Conferindo o uv'
$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host 'Instalando o uv (https://docs.astral.sh/uv/)...'
    powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Falha 'o uv nao ficou disponivel. Instale com "winget install astral-sh.uv" e rode de novo.'
}
uv --version

# ---------------------------------------------------------- 2. dependencias
Passo 'Instalando as dependencias Python (primeira vez demora alguns minutos)'
uv sync --frozen
if ($LASTEXITCODE -ne 0) { uv sync }
if ($LASTEXITCODE -ne 0) { Falha 'o uv sync falhou (veja a mensagem acima)' }

$Python = Join-Path $Raiz '.venv\Scripts\python.exe'
$PythonW = Join-Path $Raiz '.venv\Scripts\pythonw.exe'
& $Python -c "import pygame, cv2, sounddevice, soundfile, customtkinter, librosa, tinysoundfont" 2>$null
if ($LASTEXITCODE -ne 0) { Falha 'as dependencias foram instaladas, mas alguma nao carrega' }
Write-Host 'Dependencias OK.'

# ---------------------------------------------------------------- 3. banco
Passo 'Banco de dados do login'
$ArqBanco = Join-Path $PastaConfig 'banco.txt'
if ((Test-Path $ArqBanco) -or $env:EIGUIT_DB_URL) {
    Write-Host 'URL do banco ja configurada.'
} else {
    Write-Host 'O EIGUIT pede login, que usa um banco PostgreSQL na nuvem.'
    $Url = Read-Host 'Cole a URL do banco (postgresql://...) ou Enter para pular'
    if ($Url) {
        New-Item -ItemType Directory -Path $PastaConfig -Force | Out-Null
        # Sem BOM: o app le o arquivo como UTF-8 puro
        [IO.File]::WriteAllText($ArqBanco, $Url.Trim())
        Write-Host "Gravado em $ArqBanco"
    } else {
        Aviso "Pulado. Sem a URL o login nao conecta; crie $ArqBanco depois."
    }
}

# --------------------------------------------------------------- 4. atalhos
Passo 'Criando atalhos na Area de Trabalho e no Menu Iniciar'
foreach ($Caminho in @($AtalhoMesa, $AtalhoMenu)) {
    $Atalho = $Shell.CreateShortcut($Caminho)
    $Atalho.TargetPath = $PythonW            # pythonw: abre sem janela de console
    $Atalho.Arguments = 'main.py'
    $Atalho.WorkingDirectory = $Raiz         # o app usa caminhos relativos a pasta
    $Atalho.IconLocation = (Join-Path $Raiz 'assets\images\icone.ico')
    $Atalho.Description = 'EIGUIT - estudio de guitarra'
    $Atalho.Save()
}

Passo 'Pronto!'
Write-Host 'Abra pelo atalho "EIGUIT" na Area de Trabalho ou no Menu Iniciar.'
Write-Host 'Para ver mensagens de erro, rode no terminal: .venv\Scripts\python main.py'
