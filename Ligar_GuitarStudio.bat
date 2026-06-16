@echo off
echo ===================================================
echo     Iniciando a Orquestra do Guitar Studio...
echo ===================================================

:: 1. Ligar o Mensageiro (Redis via Docker)
echo [1/4] Iniciando o Docker/Redis...
start "Redis (Mensageiro)" cmd /k "docker run -d -p 6379:6379 redis && echo Redis iniciado com sucesso!"

timeout /t 2 /nobreak > NUL

:: 2. Ligar o Servidor Backend (FastAPI)
echo [2/4] Iniciando Servidor FastAPI...
start "FastAPI (Servidor Web)" cmd /k "cd services\transcription && .\venv_ia\Scripts\activate && python main.py"

:: 3. Ligar o Motor da IA (Celery)
echo [3/4] Iniciando a IA (Celery)...
start "Celery (Inteligencia Artificial)" cmd /k "cd services\transcription && .\venv_ia\Scripts\activate && python -m celery -A tasks worker --loglevel=info -P solo"

:: 4. Ligar a Interface Visual (React)
echo [4/4] Iniciando o Frontend React...
start "React (Interface Web)" cmd /k "cd web_frontend && npm start"

echo.
echo Tudo ligado! As janelas dos servidores foram abertas separadamente.
echo O seu navegador deve abrir em instantes.
timeout /t 5 > NUL