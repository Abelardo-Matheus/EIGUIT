import subprocess
import os
import time
import requests

def iniciar_servicos_ia():
    """Inicia o Redis (se necessário), Celery e FastAPI em consoles separados."""
    base_path = os.path.join(os.getcwd(), "services", "transcription")
    venv_python = os.path.join(os.getcwd(), "services", "venv_ia", "Scripts", "python.exe")

    print("[IA] Verificando serviços...")

    # 1. Tentar verificar se o FastAPI já está rodando
    try:
        requests.get("http://localhost:8000/", timeout=1)
        print("[IA] Servidor API já está online.")
        return # Se a API responde, assumimos que tudo está OK
    except:
        pass

    print("[IA] Iniciando componentes de Inteligência Artificial...")

    # Comando para abrir um novo console e rodar o Celery
    cmd_celery = f'start "IA - Motor Celery" /min "{venv_python}" -m celery -A tasks worker --loglevel=info -P solo'
    
    # Comando para abrir um novo console e rodar o FastAPI
    cmd_fastapi = f'start "IA - Servidor API" /min "{venv_python}" main.py'

    try:
        # Inicia Celery
        subprocess.Popen(cmd_celery, shell=True, cwd=base_path)
        print("[IA] Motor Celery disparado (Minimizado).")
        
        # Espera um pouco antes de subir a API
        time.sleep(2)
        
        # Inicia FastAPI
        subprocess.Popen(cmd_fastapi, shell=True, cwd=base_path)
        print("[IA] Servidor API disparado (Minimizado).")
        
        print("[IA] Tudo pronto! A transcrição funcionará automaticamente.")
    except Exception as e:
        print(f"[IA] Erro ao iniciar serviços automaticamente: {e}")

if __name__ == "__main__":
    iniciar_servicos_ia()
