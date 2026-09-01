import os
import json
import shutil
import subprocess
from celery import Celery
from basic_pitch.inference import predict_and_save
from basic_pitch import ICASSP_2022_MODEL_PATH
import music21
import uuid
import librosa

# Configuração do Celery
celery_app = Celery('transcription_tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

# Pasta para arquivos temporários
UPLOAD_DIR = "temp_audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def detectar_bpm(audio_path):
    """Detecta o BPM aproximado de um arquivo de áudio."""
    try:
        y, sr = librosa.load(audio_path, sr=None)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        # O tempo retornado pode ser um array em versões novas do librosa
        if hasattr(tempo, "__len__"):
            tempo = tempo[0]
        return round(float(tempo))
    except Exception as e:
        print(f"[IA BPM] Falha ao detectar BPM: {e}")
        return 120

def midi_to_json(midi_path):
    """Converte um arquivo MIDI para um formato JSON simplificado para o frontend."""
    if not os.path.exists(midi_path):
        return []
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
def process_transcription(self, file_path, target_instrument="other"):
    """
    Pipeline assíncrono: 
    Demucs (Isolamento de Instrumento) -> Basic Pitch (Transcrição) -> Conversão JSON
    
    target_instrument: 'vocals', 'drums', 'bass', 'other' (guitarra/piano)
    """
    try:
        task_id = self.request.id
        output_path = os.path.join(UPLOAD_DIR, f"result_{task_id}")
        os.makedirs(output_path, exist_ok=True)

        current_audio_path = file_path

        # 1. Isolamento com Demucs
        # Usamos subprocess para rodar o demucs via CLI para evitar conflitos de threads/CUDA
        print(f"[IA] Isolando instrumento: {target_instrument}")
        try:
            # -n htdemucs_ft (modelo rápido e bom)
            # --two-stems seria mais rápido se só quiséssemos um, mas o 4 stems dá mais flexibilidade
            subprocess.run([
                "demucs", 
                "--out", output_path, 
                "--filename", "{stem}.{ext}",
                file_path
            ], check=True)
            
            # O Demucs cria uma pasta htdemucs/nome_do_arquivo/{stem}.wav
            # Mas com --filename {stem}.{ext} ele simplifica
            isolated_path = os.path.join(output_path, "htdemucs", f"{target_instrument}.wav")
            
            if os.path.exists(isolated_path):
                current_audio_path = isolated_path
                print(f"[IA] Sucesso ao isolar {target_instrument}")
            else:
                # Fallback: tentar localizar na estrutura padrão se o --filename falhar
                print("[IA] Procurando arquivo isolado na estrutura padrão...")
                nome_base = os.path.splitext(os.path.basename(file_path))[0]
                isolated_path = os.path.join(output_path, "htdemucs", nome_base, f"{target_instrument}.wav")
                if os.path.exists(isolated_path):
                    current_audio_path = isolated_path

        except Exception as e:
            print(f"Aviso: Demucs falhou ou não instalado. Erro: {e}")

        # 2. Transcrição com Basic Pitch
        predict_and_save(
            audio_path_list=[current_audio_path],
            output_directory=output_path,
            save_midi=True,
            sonify_midi=False,
            save_model_outputs=False,
            save_notes=True,
            model_or_model_path=ICASSP_2022_MODEL_PATH
        )
        
        # Localizar MIDI gerado
        nome_base_audio = os.path.splitext(os.path.basename(current_audio_path))[0]
        midi_file = os.path.join(output_path, f"{nome_base_audio}_basic_pitch.mid")

        if not os.path.exists(midi_file):
            raise FileNotFoundError(f"IA não gerou notas para o instrumento selecionado.")

        # 3. Conversão para JSON e Detecção de BPM
        json_data = midi_to_json(midi_file)
        bpm_detectado = detectar_bpm(file_path) # Detectar do arquivo original para melhor precisão rítmica
        
        return {
            "status": "completed",
            "notes": json_data,
            "bpm": bpm_detectado,
            "instrument_used": target_instrument
        }

    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }