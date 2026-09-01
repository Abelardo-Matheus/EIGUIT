$url = "https://cdn.jsdelivr.net/npm/@coderline/alphatab@latest/dist/soundfont/sonivox.sf2"
$outputDirWeb = "web_frontend/public/soundfonts"
$outputDirDesktop = "assets/audio"
$outputFileWeb = "$outputDirWeb/sonivox.sf2"
$outputFileDesktop = "$outputDirDesktop/sonivox.sf2"

if (!(Test-Path $outputDirWeb)) {
    New-Item -ItemType Directory -Path $outputDirWeb -Force
}
if (!(Test-Path $outputDirDesktop)) {
    New-Item -ItemType Directory -Path $outputDirDesktop -Force
}

Write-Host "Iniciando download do SoundFont (~30MB)..."
Invoke-WebRequest -Uri $url -OutFile $outputFileDesktop

Write-Host "Copiando para a pasta web..."
Copy-Item $outputFileDesktop $outputFileWeb

Write-Host "Download e cópia concluídos!"
Write-Host "Arquivo Desktop: $outputFileDesktop"
Write-Host "Arquivo Web: $outputFileWeb"
