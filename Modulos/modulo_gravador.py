
import sys
import numpy as np

# Cria o sensor: É True se estiver rodando no navegador!
NO_NAVEGADOR = sys.platform == "emscripten"

# Só importa a biblioteca pesada se estiver no PC
if not NO_NAVEGADOR:
    import sounddevice as sd

class GravadorAudio:
    def __init__(self, device_id=None):
        self.taxa_amostragem = 48000
        self.canais = 1               
        self.device_id = None
        self.stream = None
        self.gravando = False 
        self.tamanho_buffer = int(self.taxa_amostragem * 0.2)
        self.buffer = np.zeros(self.tamanho_buffer, dtype=np.float32)

    def obter_lista_entradas(self):
        """Varre o computador e retorna apenas equipamentos que gravam áudio"""
        # --- TRAVA DE SEGURANÇA WEB ---
        if NO_NAVEGADOR:
            return [{'id': 0, 'nome': 'Microfone Web (Inativo)'}]
            
        dispositivos = sd.query_devices()
        entradas = []
        for i, d in enumerate(dispositivos):
            if d['max_input_channels'] > 0: # Filtra apenas Microfones/Inputs
                entradas.append({'id': i, 'nome': d['name']})
        return entradas

    def mudar_dispositivo(self, novo_id):
        """Troca o microfone em tempo real sem travar"""
        estava_gravando = self.gravando
        if estava_gravando:
            self.parar_stream()
            
        self.device_id = novo_id
        
        if estava_gravando:
            self.iniciar_stream()

    def callback_audio(self, indata, frames, time, status):
        if status: print(status)
        self.buffer = np.roll(self.buffer, -frames)
        self.buffer[-frames:] = indata[:, 0]

    def alternar_microfone(self):
        if NO_NAVEGADOR:
            print("Microfone desativado na versão Web!")
            return # Sai da função e não tenta ligar o mic
        if self.gravando: self.parar_stream()
        else: self.iniciar_stream()

    def iniciar_stream(self):
        if not self.gravando:
            try:
                print(f"🎤 Abrindo microfone ID [{self.device_id}]...")
                self.stream = sd.InputStream(
                    samplerate=self.taxa_amostragem,
                    channels=self.canais,
                    device=self.device_id,
                    callback=self.callback_audio,
                    blocksize=2048
                )
                self.stream.start()
                self.gravando = True
                print("✅ Microfone ABERTO!")
            except Exception as e:
                print(f"❌ Erro ao abrir microfone: {e}")

    def parar_stream(self):
        if self.gravando and self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.gravando = False
            self.buffer = np.zeros(self.tamanho_buffer, dtype=np.float32) 
            print("🔇 Microfone FECHADO.")

    def obter_array_para_ia(self):
        if self.gravando:
            if np.max(np.abs(self.buffer)) > 0.01:
                return self.buffer.copy()
        return None