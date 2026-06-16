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
    if not file.filename.endswith(('.mp3', '.wav', '.ogg')):
        raise HTTPException(status_code=400, detail="Formato de arquivo não suportado.")

    # Validar instrumento
    valid_instruments = ["vocals", "drums", "bass", "other"]
    if instrument not in valid_instruments:
        instrument = "other"

    # Gerar nome único e salvar arquivo
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # Disparar tarefa no Celery com o instrumento alvo
    task = process_transcription.delay(file_path, instrument)
    
    return {"task_id": task.id, "status": "processing", "instrument": instrument}

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
