import os
import json
from celery import Celery
from basic_pitch.inference import predict_and_save
import music21
import uuid

# Configuração do Celery
celery_app = Celery('transcription_tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

# Pasta para arquivos temporários
UPLOAD_DIR = "temp_audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def midi_to_json(midi_path):
    """Converte um arquivo MIDI para um formato JSON simplificado para o frontend."""
    score = music21.converter.parse(midi_path)
    notes_data = []
    
    for part in score.parts:
        for element in part.flat.notes:
            if isinstance(element, music21.note.Note):
                notes_data.append({
                    "pitch": element.pitch.ps,
                    "name": element.pitch.nameWithOctave,
                    "duration": float(element.duration.quarterLength),
                    "offset": float(element.offset)
                })
            elif isinstance(element, music21.chord.Chord):
                for note in element:
                    notes_data.append({
                        "pitch": note.pitch.ps,
                        "name": note.pitch.nameWithOctave,
                        "duration": float(element.duration.quarterLength),
                        "offset": float(element.offset)
                    })
    
    return sorted(notes_data, key=lambda x: x['offset'])

@celery_app.task(bind=True)
def process_transcription(self, file_path):
    """Pipeline assíncrono: Transcrição Direta -> Conversão JSON"""
    try:
        task_id = self.request.id
        output_path = os.path.join(UPLOAD_DIR, f"result_{task_id}")
        os.makedirs(output_path, exist_ok=True)

        # Transcrição Direta (Basic Pitch) - Sem Spleeter
        predict_and_save(
            audio_path_list=[file_path],
            output_directory=output_path,
            save_midi=True,
            sonify_midi=False,
            save_model_outputs=False,
            save_notes=True
        )
        
        # O Basic Pitch salva o arquivo terminando em _basic_pitch.mid
        nome_arquivo_base = os.path.splitext(os.path.basename(file_path))[0]
        midi_file = os.path.join(output_path, f"{nome_arquivo_base}_basic_pitch.mid")

        # Conversão para JSON
        json_data = midi_to_json(midi_file)
        
        return {
            "status": "completed",
            "notes": json_data
        }

    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise e