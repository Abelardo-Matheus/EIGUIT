# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Global Audio Engine - Motor Centralizado de Captura e Processamento
# =============================================================================

import sounddevice as sd
import numpy as np
import threading
import math
import pygame
from scipy.signal import butter, lfilter

# OTIMIZAÇÃO: Tabela de frequências pré-calculada para todas as notas comuns
FREQS_NOTAS = {
    'C0': 16.35, 'C#0': 17.32, 'D0': 18.35, 'D#0': 19.45, 'E0': 20.60, 'F0': 21.83, 'F#0': 23.12, 'G0': 24.50, 'G#0': 25.96, 'A0': 27.50, 'A#0': 29.14, 'B0': 30.87,
    'C1': 32.70, 'C#1': 34.65, 'D1': 36.71, 'D#1': 38.89, 'E1': 41.20, 'F1': 43.65, 'F#1': 46.25, 'G1': 49.00, 'G#1': 51.91, 'A1': 55.00, 'A#1': 58.27, 'B1': 61.74,
    'C2': 65.41, 'C#2': 69.30, 'D2': 73.42, 'D#2': 77.78, 'E2': 82.41, 'F2': 87.31, 'F#2': 92.50, 'G2': 98.00, 'G#2': 103.83, 'A2': 110.00, 'A#2': 116.54, 'B2': 123.47,
    'C3': 130.81, 'C#3': 138.59, 'D3': 146.83, 'D#3': 155.56, 'E3': 164.81, 'F3': 174.61, 'F#3': 185.00, 'G3': 196.00, 'G#3': 207.65, 'A3': 220.00, 'A#3': 233.08, 'B3': 246.94,
    'C4': 261.63, 'C#4': 277.18, 'D4': 293.66, 'D#4': 311.13, 'E4': 329.63, 'F4': 349.23, 'F#4': 369.99, 'G4': 392.00, 'G#4': 415.30, 'A4': 440.00, 'A#4': 466.16, 'B4': 493.88,
    'C5': 523.25, 'C#5': 554.37, 'D5': 587.33, 'D#5': 622.25, 'E5': 659.25, 'F5': 698.46, 'F#5': 739.99, 'G5': 783.99, 'G#5': 830.61, 'A5': 880.00, 'A#5': 932.33, 'B5': 987.77
}

class GlobalAudioEngine:
    """
    Motor central que gerencia o microfone e processa áudio continuamente.
    Deve ser inicializado uma vez no main.py e ficar rodando em background.
    """
    def __init__(self, sample_rate=48000):
        self.sr = sample_rate
        self.canais = 1
        self.device_id = sd.default.device[0]
        self.stream = None
        self.ativo = False
        
        # Buffer de Áudio (100ms de histórico para análise rápida)
        self.tamanho_buffer = int(self.sr * 0.1)
        self.buffer = np.zeros(self.tamanho_buffer, dtype=np.float32)
        
        # Resultados do Processamento (Acessíveis por qualquer módulo)
        self.freq_detectada = 0.0
        self.nota_unicao = ""
        self.notas_polifonicas = []
        self.volume_atual = 0.0
        
        # Controle de análise (roda mais rápido para tempo real)
        self.ultimo_processamento = 0
        self.intervalo_ms = 30 
        
        # Filtros e Janelamento
        self.b_filter, self.a_filter = self._create_filter(70, 1300)
        self.window = np.hanning(self.tamanho_buffer)
        
        # Inicializa automaticamente
        self.iniciar()

    def _create_filter(self, low, high, order=5):
        nyq = 0.5 * self.sr
        return butter(order, [low/nyq, high/nyq], btype='band')

    def callback_audio(self, indata, frames, time, status):
        # Transfere áudio do hardware para o buffer circular
        self.buffer = np.roll(self.buffer, -frames)
        self.buffer[-frames:] = indata[:, 0]
        # RMS para volume mais estável que o pico
        self.volume_atual = np.sqrt(np.mean(indata**2))

    def iniciar(self):
        if not self.ativo:
            try:
                self.stream = sd.InputStream(
                    samplerate=self.sr,
                    channels=self.canais,
                    device=self.device_id,
                    callback=self.callback_audio,
                    blocksize=512, # Menor para latência menor
                    latency='low'
                )
                self.stream.start()
                self.ativo = True
                print(f"🎤 [GLOBAL AUDIO] Captura iniciada no ID {self.device_id}")
            except Exception as e:
                print(f"❌ [GLOBAL AUDIO] Erro ao iniciar: {e}")

    def parar(self):
        if self.ativo and self.stream:
            self.stream.stop()
            self.stream.close()
            self.ativo = False

    def mudar_dispositivo(self, novo_id):
        self.parar()
        self.device_id = novo_id
        self.iniciar()

    def atualizar_analise_ia(self, sensitivity=0.3):
        """
        Executa o processamento pesado (Pitch/Chroma) de forma controlada.
        Chamado no loop principal (main.py).
        """
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_processamento < self.intervalo_ms:
            return
        
        self.ultimo_processamento = agora
        
        # Gate de ruído dinâmico
        if self.volume_atual < 0.005:
            self.freq_detectada = 0.0
            self.nota_unicao = ""
            return

        # Importações locais para otimização
        import librosa
        
        # 1. Pitch Detection (Monofônico) usando YIN otimizado
        try:
            f0 = librosa.yin(self.buffer, fmin=60, fmax=500, sr=self.sr, trough_threshold=sensitivity)
            f0_valid = f0[f0 > 0]
            if len(f0_valid) > 0:
                self.freq_detectada = np.median(f0_valid)
            else:
                self.freq_detectada = 0.0
        except:
            self.freq_detectada = 0.0
            
        # 2. Chroma Detection (Apenas se volume for alto o suficiente)
        if self.volume_atual > 0.02:
            chroma = librosa.feature.chroma_stft(y=self.buffer, sr=self.sr, tuning=0.0)
            media_chroma = np.mean(chroma, axis=1)
            media_chroma /= (np.max(media_chroma) + 1e-6)
            
            notas_escala = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            self.notas_polifonicas = [notas_escala[i] for i, v in enumerate(media_chroma) if v > 0.8]
        else:
            self.notas_polifonicas = []

    def obter_lista_entradas(self):
        dispositivos = sd.query_devices()
        return [{'id': i, 'nome': d['name']} for i, d in enumerate(dispositivos) if d['max_input_channels'] > 0]
