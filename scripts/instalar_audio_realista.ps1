$ErrorActionPreference = 'Stop'

$fluidSynthUrl = "https://github.com/FluidSynth/fluidsynth/releases/download/v2.3.4/fluidsynth-2.3.4-win10-x64.zip"
$soundFontUrl = "https://cdn.jsdelivr.net/npm/@coderline/alphatab@latest/dist/soundfont/sonivox.sf2"

$baseDir = $PSScriptRoot + "\.."
$binDir = "$baseDir\assets\bin\fluidsynth"
$sfDir = "$baseDir\assets\audio\soundfonts"
$zipPath = "$baseDir\assets\bin\fluidsynth.zip"
$sfPath = "$sfDir\general_midi.sf2"

# Criar pastas se não existirem
if (!(Test-Path $binDir)) { New-Item -ItemType Directory -Path $binDir -Force | Out-Null }
if (!(Test-Path $sfDir)) { New-Item -ItemType Directory -Path $sfDir -Force | Out-Null }

Write-Host "Baixando FluidSynth (binários)..."
Invoke-WebRequest -Uri $fluidSynthUrl -OutFile $zipPath

Write-Host "Extraindo FluidSynth..."
Expand-Archive -Path $zipPath -DestinationPath $binDir -Force
Remove-Item $zipPath -Force

# Ajustar a estrutura da pasta, pois o zip extrai uma pasta dentro de fluidsynth
$extractedFolder = Get-ChildItem -Path $binDir | Where-Object { $_.PSIsContainer } | Select-Object -First 1
if ($extractedFolder) {
    Write-Host "Movendo arquivos para a raiz do bin..."
    Move-Item -Path "$($extractedFolder.FullName)\*" -Destination $binDir -Force
    Remove-Item -Path $extractedFolder.FullName -Recurse -Force
}

Write-Host "Baixando SoundFont General MIDI..."
Invoke-WebRequest -Uri $soundFontUrl -OutFile $sfPath

Write-Host "Instalação concluída com sucesso!"
Write-Host "FluidSynth: $binDir\bin\fluidsynth.exe"
Write-Host "SoundFont: $sfPath"
