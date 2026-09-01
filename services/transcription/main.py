from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from tasks import process_transcription, celery_app
import os
import uuid

app = FastAPI(title="Guitar Studio - Audio Transcription API")

# Habilitar CORS para o frontend (React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção, especifique a URL do seu frontend
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "temp_audio"

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...), instrument: str = "other"):
    try:
        if not file.filename.endswith(('.mp3', '.wav', '.ogg')):
            raise HTTPException(status_code=400, detail="Formato de arquivo não suportado.")

        # Validar instrumento
        valid_instruments = ["vocals", "drums", "bass", "other"]
        if instrument not in valid_instruments:
            instrument = "other"

        # Garantir diretório existe
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

        # Gerar nome único e salvar arquivo
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
        
        print(f"[API] Recebendo arquivo: {file.filename} -> {file_path}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Disparar tarefa no Celery
        print(f"[API] Enfileirando tarefa Celery para {instrument}...")
        try:
            task = process_transcription.delay(file_path, instrument)
            return {"task_id": task.id, "status": "processing", "instrument": instrument}
        except Exception as celery_err:
            print(f"[API ERROR] Falha ao conectar ao Celery/Redis: {celery_err}")
            raise HTTPException(status_code=503, detail=f"Serviço de fila indisponível (Redis está rodando?): {celery_err}")

    except Exception as e:
        print(f"[API ERROR] Erro interno: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    task_result = celery_app.AsyncResult(task_id)
    
    if task_result.state == 'PENDING':
        return {"status": "waiting"}
    elif task_result.state == 'SUCCESS':
        result_data = task_result.result
        # Se o status interno for failed, retorna erro
        if result_data.get("status") == "failed":
            return {"status": "failed", "error": result_data.get("error")}
        return {"status": "completed", "result": result_data}
    elif task_result.state == 'FAILURE':
        return {"status": "failed", "error": str(task_result.info)}
    
    return {"status": task_result.state}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
