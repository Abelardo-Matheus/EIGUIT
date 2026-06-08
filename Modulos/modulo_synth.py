import pygame
import numpy as np

class SintetizadorTablatura:
    """
    Motor de áudio para reprodução de tablaturas usando Numpy e Pygame.
    """
    def __init__(self):
        # Tentar obter as configurações do mixer já inicializado no main.py
        mixer_init = pygame.mixer.get_init()
        if mixer_init:
            self.sample_rate = mixer_init[0]
            self.channels = mixer_init[2]
        else:
            self.sample_rate = 44100
            self.channels = 2
            pygame.mixer.init(self.sample_rate, -16, self.channels)
        
        # Frequências base para Standard E (6 cordas)
        # 1ª E4, 2ª B3, 3ª G3, 4ª D3, 5ª A2, 6ª E2
        self.freqs_base = [329.63, 246.94, 196.00, 146.83, 110.00, 82.41]
        
        # Lista para manter referências aos sons ativos e evitar coleta de lixo
        self.sons_ativos = []

    def calcular_frequencia(self, corda, casa):
        if not (1 <= corda <= 6):
            return 0
        f0 = self.freqs_base[corda - 1]
        return f0 * (2 ** (casa / 12.0))

    def gerar_onda_senoidal(self, freq, duracao, volume=0.5):
        t = np.linspace(0, duracao, int(self.sample_rate * duracao), False)
        # Envelope ADSR simplificado (Decay mais suave)
        envelope = np.exp(-2 * t / duracao)
        onda = np.sin(2 * np.pi * freq * t) * envelope
        
        # Normalizar para 16-bit
        audio = (onda * volume * 32767).astype(np.int16)
        
        # Converter para Stereo se necessário
        if self.channels == 2:
            audio = np.column_stack((audio, audio))
            
        return audio

    def reproduzir_nota(self, corda, casa, tecnica='', duracao=0.6):
        freq_inicial = self.calcular_frequencia(corda, casa)
        if freq_inicial == 0:
            return

        print(f"[SYNTH] Tocando Corda {corda}, Casa {casa}, Tec {tecnica} @ {freq_inicial:.2f}Hz")

        t = np.linspace(0, duracao, int(self.sample_rate * duracao), False)
        freq_final = freq_inicial
        
        if 'b' in tecnica: # Bend: sobe 1 tom
            freq_final = freq_inicial * (2 ** (2/12.0))
        elif '/' in tecnica: # Slide: sobe 2 tons
            freq_final = freq_inicial * (2 ** (4/12.0))
            
        if freq_final != freq_inicial:
            freqs = np.linspace(freq_inicial, freq_final, len(t))
            fase = np.cumsum(freqs) / self.sample_rate
            onda = np.sin(2 * np.pi * fase)
        else:
            onda = np.sin(2 * np.pi * freq_inicial * t)

        envelope = np.exp(-2.5 * t / duracao)
        audio_final = (onda * envelope * 0.4 * 32767).astype(np.int16)
        
        if self.channels == 2:
            audio_final = np.column_stack((audio_final, audio_final))

        try:
            som = pygame.sndarray.make_sound(audio_final)
            som.play()
            
            # Manter referência (limitar tamanho da lista)
            self.sons_ativos.append(som)
            if len(self.sons_ativos) > 20:
                self.sons_ativos.pop(0)
        except Exception as e:
            print(f"[ERRO SYNTH] Falha ao gerar som: {e}")

# Exemplo de uso:
# synth = SintetizadorTablatura()
# synth.reproduzir_nota(6, 0) # E grave solto
