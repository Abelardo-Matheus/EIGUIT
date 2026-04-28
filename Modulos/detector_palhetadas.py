import sys
import numpy as np
import time
# Aumentei o escudo para garantir compatibilidade com novas versões do Pygbag
NO_NAVEGADOR = sys.platform in ["emscripten", "wasm32"]

if not NO_NAVEGADOR:
    import librosa # <-- Se o seu detector usava librosa, proteja ele aqui!
    # import scipy (se usar, proteja também!)
class DetectorPalhetadas:
    def __init__(self):
        # Limiar de volume (0.0 a 1.0). 
        # Quanto menor, mais sensível. Se captar respiração, aumente este valor!
        self.limiar_volume = 0.05 
        
        # Tempo de "cegueira" em segundos para evitar disparos duplos (150ms é um bom padrão)
        self.cooldown = 0.15 
        
        self.ultimo_disparo = 0.0
        self.volume_atual = 0.0

    def processar_buffer(self, buffer_audio):
        """Recebe o pedaço de áudio do microfone e devolve True se ouviu uma palhetada"""
        if buffer_audio is None or len(buffer_audio) == 0:
            return False

        # 1. Segurança matemática: converte para float para evitar estouro de limite (int16)
        audio_float = np.array(buffer_audio, dtype=np.float32) 
        
        # 2. Normaliza os dados se a sua placa de áudio enviar números gigantes (ex: -32768 a 32767)
        if np.max(np.abs(audio_float)) > 1.0:
            audio_float = audio_float / 32768.0 

        # 3. Calcula a Energia RMS (Root Mean Square) -> O Volume verdadeiro da onda
        rms = np.sqrt(np.mean(audio_float**2))
        self.volume_atual = rms
        
        tempo_atual = time.time()

        # 4. A Mágica do Onset (Ataque): O volume passou da linha vermelha e o cooldown zerou?
        if rms > self.limiar_volume and (tempo_atual - self.ultimo_disparo) > self.cooldown:
            self.ultimo_disparo = tempo_atual
            return True # PALHETADA DETECTADA!

        return False