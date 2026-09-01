import os
import pygame
import numpy as np
from scipy import signal

class MotorAudioDual:
    """
    Motor Dual-Engine: 
    - Modo 'sintetico': Usa Pygame e Numpy (sempre disponível, não bloqueante).
    - Modo 'realista': Usa FluidSynth + SoundFont GM (depende de C++ libs).
    """
    def __init__(self, modo="sintetico"):
        self.modo = modo
        self.motor_realista_ok = False
        
        # Setup do Pygame/Numpy (Modo Sintético)
        mixer_init = pygame.mixer.get_init()
        if mixer_init:
            self.sample_rate = mixer_init[0]
            self.channels = mixer_init[2]
        else:
            self.sample_rate = 44100
            self.channels = 2
            pygame.mixer.init(self.sample_rate, -16, self.channels, 1024)
        
        pygame.mixer.set_num_channels(64)
        self.canais_cordas = [pygame.mixer.Channel(i) for i in range(6)]
        
        # Panning estéreo
        self.pans_cordas = [
            (0.3, 0.7), # e (aguda)
            (0.4, 0.6), # B
            (0.5, 0.5), # G
            (0.5, 0.5), # D
            (0.6, 0.4), # A
            (0.7, 0.3)  # E (grave)
        ]
        
        self.freqs_base = [329.63, 246.94, 196.00, 146.83, 110.00, 82.41]
        self.midi_base = [64, 59, 55, 50, 45, 40]
        self.cache_sons = {}
        
        # Setup do FluidSynth (Modo Realista)
        self.sf2_path = os.path.join("assets", "audio", "soundfonts", "general_midi.sf2")
        self.fs = None
        self.sfid = None
        
        self.inicializar_realista()

    def inicializar_realista(self):
        """Injeta a DLL no PATH e tenta carregar o FluidSynth."""
        bin_dir = os.path.join(os.getcwd(), "assets", "bin", "fluidsynth")
        if os.path.exists(bin_dir):
            if bin_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(bin_dir)

        if not os.path.exists(self.sf2_path):
            print(f"[DUAL-ENGINE] SoundFont GM não encontrado em {self.sf2_path}. O modo Realista não funcionará.")
            return

        try:
            import fluidsynth
            self.fs = fluidsynth.Synth()
            self.fs.start(driver="dsound") # 'dsound' ou 'none' se for usar get_samples
            # Usaremos o motor interno do pyfluidsynth para que ele não bloqueie
            
            self.sfid = self.fs.sfload(self.sf2_path)
            
            # Preset Mapping GM:
            # Guitarra = 27 (Clean Electric) ou 24 (Acoustic)
            # Baixo = 33 (Electric Bass Finger)
            # Bateria = Modo percussão canal 9 (API usa canal 9 p/ canal 10 MIDI)
            # Voz = 52 (Choir Aahs)
            self.instrumentos_presets = {
                "Guitarra": 27,
                "Baixo": 33,
                "Bateria": 0, # Tratado no canal de percussão
                "Voz": 52
            }
            
            # Setando os presets iniciais
            self.fs.program_select(0, self.sfid, 0, self.instrumentos_presets["Guitarra"])
            self.fs.set_reverb(0.4, 0.3, 0.5, 0.2)
            self.motor_realista_ok = True
            print("[DUAL-ENGINE] FluidSynth inicializado com sucesso!")
        except Exception as e:
            print(f"[DUAL-ENGINE] Erro ao carregar FluidSynth: {e}")
            self.motor_realista_ok = False

    def alternar_modo(self, novo_modo):
        if novo_modo == "realista" and not self.motor_realista_ok:
            print("[DUAL-ENGINE] Aviso: Modo realista indisponível. Mantendo sintético.")
            self.modo = "sintetico"
            return False
        self.modo = novo_modo
        print(f"[DUAL-ENGINE] Modo alterado para: {self.modo}")
        return True

    def alternar_instrumento_synth(self, nome):
        self.instrumento_atual = nome
        if self.motor_realista_ok and self.fs:
            if nome == "Bateria":
                # Canal 9 do FluidSynth é o Canal 10 do MIDI (Percussão)
                print("[DUAL-ENGINE] Instrumento alterado para Bateria (Canal Percussão)")
            else:
                preset = self.instrumentos_presets.get(nome, 27)
                self.fs.program_select(0, self.sfid, 0, preset)
                print(f"[DUAL-ENGINE] Timbre alterado para {nome} (Preset GM {preset})")

    def reproduzir_nota(self, corda, casa, tecnica='', duracao=0.8, volume=100):
        # Proteção para bateria:
        is_bateria = getattr(self, "instrumento_atual", "") == "Bateria"
        
        if self.modo == "realista" and self.motor_realista_ok:
            canal_midi = 9 if is_bateria else 0
            # Mapeamento de bateria simples na corda/casa
            if is_bateria:
                # Exemplo: Bumbo=36, Caixa=38, HiHat=42
                midi_note = 36 + casa + (corda - 1)
            else:
                midi_note = self.midi_base[corda - 1] + casa
            
            # Aplicar Bend
            if 'b' in tecnica and not is_bateria:
                self.fs.pitch_bend(canal_midi, 8192 + 2000) # sobe o pitch
            else:
                self.fs.pitch_bend(canal_midi, 8192) # reseta pitch
            
            # Usar threading para desligar a nota após a duração sem bloquear a UI
            import threading
            self.fs.noteon(canal_midi, midi_note, volume)
            
            def desligar():
                pygame.time.wait(int(duracao * 1000))
                self.fs.noteoff(canal_midi, midi_note)
            threading.Thread(target=desligar, daemon=True).start()
            
            return # Finaliza fluxo realista
            
        # --- FLUXO SINTÉTICO (Fallback) ---
        freq_inicial = (self.freqs_base[corda - 1] * (2 ** (casa / 12.0))) if 1 <= corda <= 6 else 0
        if freq_inicial == 0: return

        cache_key = (corda, casa, tecnica, round(duracao, 2), volume)
        if cache_key in self.cache_sons:
            audio = self.cache_sons[cache_key]
        else:
            freq_final = freq_inicial
            if 'b' in tecnica: freq_final *= (2 ** (1/12.0))
            audio = self.gerar_audio_basico(freq_inicial, freq_final, duracao)
            if len(self.cache_sons) < 300:
                self.cache_sons[cache_key] = audio

        try:
            som = pygame.sndarray.make_sound(audio)
            canal = self.canais_cordas[corda - 1]
            p_l, p_r = self.pans_cordas[corda - 1]
            canal.set_volume(p_l * (volume/100.0), p_r * (volume/100.0))
            canal.play(som)
        except Exception as e:
            print(f"[ERRO SYNTH] {e}")

    def gerar_audio_basico(self, freq_ini, freq_fim, duracao):
        num_samples = int(self.sample_rate * (duracao + 0.1))
        t = np.linspace(0, duracao + 0.1, num_samples, False)
        
        freqs = np.linspace(freq_ini, freq_fim, len(t))
        phase = 2 * np.pi * np.cumsum(freqs) / self.sample_rate
        onda = np.sin(phase) * 1.0 + np.sin(2 * phase) * 0.4 + np.sin(3 * phase) * 0.2
        
        envelope = np.exp(-4.0 * t / duracao)
        audio_final = (onda * envelope * 0.25 * 32767).astype(np.int16)
        stereo = np.column_stack((audio_final, audio_final))
        return stereo
