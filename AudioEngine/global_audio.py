import sounddevice as sd
import numpy as np
import threading
import math
import pygame
from scipy.signal import butter, lfilter
FREQS_NOTAS = {'C0': 16.35, 'C#0': 17.32, 'D0': 18.35, 'D#0': 19.45, 'E0': 20.6, 'F0': 21.83, 'F#0': 23.12, 'G0': 24.5, 'G#0': 25.96, 'A0': 27.5, 'A#0': 29.14, 'B0': 30.87, 'C1': 32.7, 'C#1': 34.65, 'D1': 36.71, 'D#1': 38.89, 'E1': 41.2, 'F1': 43.65, 'F#1': 46.25, 'G1': 49.0, 'G#1': 51.91, 'A1': 55.0, 'A#1': 58.27, 'B1': 61.74, 'C2': 65.41, 'C#2': 69.3, 'D2': 73.42, 'D#2': 77.78, 'E2': 82.41, 'F2': 87.31, 'F#2': 92.5, 'G2': 98.0, 'G#2': 103.83, 'A2': 110.0, 'A#2': 116.54, 'B2': 123.47, 'C3': 130.81, 'C#3': 138.59, 'D3': 146.83, 'D#3': 155.56, 'E3': 164.81, 'F3': 174.61, 'F#3': 185.0, 'G3': 196.0, 'G#3': 207.65, 'A3': 220.0, 'A#3': 233.08, 'B3': 246.94, 'C4': 261.63, 'C#4': 277.18, 'D4': 293.66, 'D#4': 311.13, 'E4': 329.63, 'F4': 349.23, 'F#4': 369.99, 'G4': 392.0, 'G#4': 415.3, 'A4': 440.0, 'A#4': 466.16, 'B4': 493.88, 'C5': 523.25, 'C#5': 554.37, 'D5': 587.33, 'D#5': 622.25, 'E5': 659.25, 'F5': 698.46, 'F#5': 739.99, 'G5': 783.99, 'G#5': 830.61, 'A5': 880.0, 'A#5': 932.33, 'B5': 987.77}

class GlobalAudioEngine:
    """
        Como funciona: Mantém instâncias ativas e delega tarefas aos submódulos de 'GlobalAudioEngine'.
        Para que serve: Orquestra recursos e o ciclo de vida do módulo.
        Onde é usada: Chamado a partir do módulo ou classe base de 'global_audio'.
    """

    def __init__(self, sample_rate=48000):
        """
            Como funciona: Inicializa os atributos e o estado inicial da instância.
            Para que serve: Prepara o objeto para ser utilizado no ciclo de vida da aplicação.
            Onde é usada: Chamado a partir do módulo ou classe base de 'global_audio'.
        """
        self.sr = sample_rate
        self.canais = 1
        self.device_id = sd.default.device[0]
        self.stream = None
        self.ativo = False
        self.tamanho_buffer = int(self.sr * 0.1)
        self.buffer = np.zeros(self.tamanho_buffer, dtype=np.float32)
        self.freq_detectada = 0.0
        self.nota_unicao = ''
        self.notas_polifonicas = []
        self.volume_atual = 0.0
        self.ultimo_processamento = 0
        self.intervalo_ms = 30
        self.b_filter, self.a_filter = self._create_filter(70, 1300)
        self.window = np.hanning(self.tamanho_buffer)
        self.iniciar()

    def _create_filter(self, low, high, order=5):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação ' create filter'.
            Para que serve: Realiza as tarefas fundamentais de ' create filter' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de ' create filter'.
        """
        nyq = 0.5 * self.sr
        return butter(order, [low / nyq, high / nyq], btype='band')

    def callback_audio(self, indata, frames, time, status):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'callback audio'.
            Para que serve: Realiza as tarefas fundamentais de 'callback audio' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'callback audio'.
        """
        self.buffer = np.roll(self.buffer, -frames)
        self.buffer[-frames:] = indata[:, 0]
        self.volume_atual = np.sqrt(np.mean(indata ** 2))

    def iniciar(self):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'iniciar'.
            Para que serve: Realiza as tarefas fundamentais de 'iniciar' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'iniciar'.
        """
        if not self.ativo:
            taxas_tentar = [self.sr, 44100, 48000, 22050]
            sucesso = False
            for taxa in taxas_tentar:
                try:
                    self.sr = taxa
                    self.stream = sd.InputStream(samplerate=self.sr, channels=self.canais, device=self.device_id, callback=self.callback_audio, blocksize=1024, latency='high')
                    self.stream.start()
                    self.ativo = True
                    print(f'🎤 [GLOBAL AUDIO] Captura iniciada no ID {self.device_id} @ {self.sr}Hz')
                    sucesso = True
                    break
                except Exception as e:
                    print(f'⚠️ [GLOBAL AUDIO] Falha ao iniciar @ {taxa}Hz: {e}')
            if not sucesso:
                print(f'❌ [GLOBAL AUDIO] Erro fatal: Não foi possível abrir nenhum dispositivo de entrada.')

    def parar(self):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'parar'.
            Para que serve: Realiza as tarefas fundamentais de 'parar' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'parar'.
        """
        if self.ativo and self.stream:
            self.stream.stop()
            self.stream.close()
            self.ativo = False

    def mudar_dispositivo(self, novo_id):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'mudar dispositivo'.
            Para que serve: Realiza as tarefas fundamentais de 'mudar dispositivo' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'mudar dispositivo'.
        """
        self.parar()
        self.device_id = novo_id
        self.iniciar()

    def atualizar_analise_ia(self, sensitivity=0.3):
        """
            Como funciona: Recalcula dimensões, estados e processa alterações temporais.
            Para que serve: Garante que os dados e a interface reflitam as últimas mudanças.
            Onde é usada: Chamado a partir do módulo ou classe base de 'global_audio'.
        """
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_processamento < self.intervalo_ms:
            return
        self.ultimo_processamento = agora
        if self.volume_atual < 0.005:
            self.freq_detectada = 0.0
            self.nota_unicao = ''
            return
        import librosa
        try:
            f0 = librosa.yin(self.buffer, fmin=60, fmax=500, sr=self.sr, trough_threshold=sensitivity)
            f0_valid = f0[f0 > 0]
            if len(f0_valid) > 0:
                self.freq_detectada = np.median(f0_valid)
            else:
                self.freq_detectada = 0.0
        except:
            self.freq_detectada = 0.0
        if self.volume_atual > 0.02:
            chroma = librosa.feature.chroma_stft(y=self.buffer, sr=self.sr, tuning=0.0)
            media_chroma = np.mean(chroma, axis=1)
            media_chroma /= np.max(media_chroma) + 1e-06
            notas_escala = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            self.notas_polifonicas = [notas_escala[i] for i, v in enumerate(media_chroma) if v > 0.8]
        else:
            self.notas_polifonicas = []

    def obter_lista_entradas(self):
        """
            Como funciona: Acessa e formata dados internos ou de configuração.
            Para que serve: Retorna as informações solicitadas sobre 'lista entradas'.
            Onde é usada: Chamado a partir do módulo ou classe base de 'global_audio'.
        """
        dispositivos = sd.query_devices()
        return [{'id': i, 'nome': d['name']} for i, d in enumerate(dispositivos) if d['max_input_channels'] > 0]