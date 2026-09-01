import pygame
import numpy as np
import os
from scipy import signal

class SintetizadorTablatura:
    """
    Motor de áudio profissional com suporte a SoundFont, Estéreo Real e Reverb.
    """
    def __init__(self):
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
        
        # Panning por corda para realismo (E grave -> Esquerda, e aguda -> Direita)
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
        
        self.sf2_path = os.path.join("assets", "audio", "sonivox.sf2")
        self.motor_profissional = None
        self._inicializar_motor_sf2()

    def _inicializar_motor_sf2(self):
        if not os.path.exists(self.sf2_path):
            print(f"[SYNTH] SoundFont não encontrado em {self.sf2_path}.")
            return

        try:
            import fluidsynth
            self.fs = fluidsynth.Synth()
            self.fs.start(driver="none")
            self.sfid = self.fs.sfload(self.sf2_path)
            # Presets: 24=Nylon, 32=Acoustic Bass, 0=Piano (Voz), 118=Synth Drum
            self.instrumentos_presets = {
                "Guitarra": 24,
                "Baixo": 32,
                "Voz": 0,
                "Bateria": 118
            }
            # Canal 0 padrão Guitarra
            self.fs.program_select(0, self.sfid, 0, 24)
            self.fs.set_reverb(0.4, 0.3, 0.5, 0.2)
            self.motor_profissional = 'fluidsynth'
            print("[SYNTH] FluidSynth Multi-Instrumento inicializado!")
        except:
            try:
                import tinysoundfont
                self.tsf = tinysoundfont.SoundFont(self.sf2_path)
                self.motor_profissional = 'tinysoundfont'
                print("[SYNTH] tinysoundfont Multi-Instrumento inicializado!")
            except Exception as e:
                print(f"[SYNTH] Erro ao carregar motores SF2: {e}.")

    def alternar_instrumento_synth(self, nome):
        """Muda o timbre do sintetizador dependendo da trilha."""
        if self.motor_profissional == 'fluidsynth' and hasattr(self, 'instrumentos_presets'):
            preset = self.instrumentos_presets.get(nome, 24)
            self.fs.program_select(0, self.sfid, 0, preset)
            print(f"[SYNTH] Timbre alterado para {nome} (Preset {preset})")

    def aplicar_reverb(self, audio_data):
        """Simulação de Reverb por Convolução simplificada para áudio básico."""
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32) / 32767.0
            
        # Cria um impulso de reverb curto
        impulse_len = int(self.sample_rate * 0.1)
        impulse = np.exp(-5.0 * np.linspace(0, 1, impulse_len)) * np.random.normal(0, 0.05, impulse_len)
        
        if audio_data.ndim == 2:
            left = signal.convolve(audio_data[:, 0], impulse, mode='full')[:len(audio_data)]
            right = signal.convolve(audio_data[:, 1], impulse, mode='full')[:len(audio_data)]
            audio_reverb = np.column_stack((left + audio_data[:, 0], right + audio_data[:, 1]))
        else:
            audio_reverb = signal.convolve(audio_data, impulse, mode='full')[:len(audio_data)] + audio_data
            
        return (np.clip(audio_reverb, -1, 1) * 32767).astype(np.int16)

    def gerar_audio_sf2(self, midi_note, duracao, volume=100):
        num_samples = int(self.sample_rate * (duracao + 0.2)) # Release extra
        
        if self.motor_profissional == 'fluidsynth':
            self.fs.noteon(0, midi_note, volume)
            audio = self.fs.get_samples(num_samples)
            self.fs.noteoff(0, midi_note)
            return np.array(audio).astype(np.int16)
            
        elif self.motor_profissional == 'tinysoundfont':
            audio = self.tsf.render_note(midi_note, volume, duracao, self.sample_rate)
            # Reverb artificial para tinysoundfont
            return self.aplicar_reverb(audio)
            
        return None

    def gerar_audio_basico(self, freq_ini, freq_fim, duracao):
        num_samples = int(self.sample_rate * (duracao + 0.1))
        t = np.linspace(0, duracao + 0.1, num_samples, False)
        
        def gerar_onda(f_i, f_f):
            freqs = np.linspace(f_i, f_f, len(t))
            phase = 2 * np.pi * np.cumsum(freqs) / self.sample_rate
            # Harmônicos ricos
            onda = np.sin(phase) * 1.0
            onda += np.sin(2 * phase) * 0.4
            onda += np.sin(3 * phase) * 0.2
            onda += np.sin(4 * phase) * 0.1
            return onda

        audio_raw = gerar_onda(freq_ini, freq_fim)
        envelope = np.exp(-4.0 * t / duracao)
        audio_final = (audio_raw * envelope * 0.25 * 32767).astype(np.int16)
        
        # Garantir estéreo e aplicar reverb básico
        stereo = np.column_stack((audio_final, audio_final))
        return self.aplicar_reverb(stereo)

    def reproduzir_nota(self, corda, casa, tecnica='', duracao=0.8, volume=100):
        freq_inicial = (self.freqs_base[corda - 1] * (2 ** (casa / 12.0))) if 1 <= corda <= 6 else 0
        if freq_inicial == 0: return

        midi_note = self.midi_base[corda - 1] + casa
        # Cache considera volume e técnica para variação dinâmica
        cache_key = (midi_note, tecnica, round(duracao, 2), volume, self.motor_profissional)
        
        if cache_key in self.cache_sons:
            audio = self.cache_sons[cache_key]
        else:
            if self.motor_profissional:
                audio = self.gerar_audio_sf2(midi_note, duracao, volume)
                if audio is not None and self.channels == 2 and audio.ndim == 1:
                    audio = np.column_stack((audio, audio))
            else:
                freq_final = freq_inicial
                if 'b' in tecnica: freq_final *= (2 ** (1/12.0))
                audio = self.gerar_audio_basico(freq_inicial, freq_final, duracao)
            
            if len(self.cache_sons) < 300:
                self.cache_sons[cache_key] = audio

        try:
            som = pygame.sndarray.make_sound(audio)
            canal = self.canais_cordas[corda - 1]
            # Aplicar Panning
            p_l, p_r = self.pans_cordas[corda - 1]
            canal.set_volume(p_l * (volume/100.0), p_r * (volume/100.0))
            canal.play(som)
        except Exception as e:
            print(f"[ERRO SYNTH] {e}")



# Exemplo de uso:
# synth = SintetizadorTablatura()
# synth.reproduzir_nota(6, 0) # E grave solto
