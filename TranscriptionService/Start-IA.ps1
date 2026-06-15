Write-Host "Iniciando setup da IA (Python 3.11)..." -ForegroundColor Cyan
py -3.11 -m venv venv_ia
Write-Host "Instalando dependencias pesadas (Isso pode demorar alguns minutos na primeira vez)..." -ForegroundColor Yellow
.\venv_ia\Scripts\python.exe -m pip install -r requirements.txt
Write-Host "Ligando o motor de Inteligência Artificial (Celery)..." -ForegroundColor Green
.\venv_ia\Scripts\python.exe -m celery -A tasks worker --loglevel=info -P solo