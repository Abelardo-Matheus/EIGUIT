import os
import threading
import time
from collections import OrderedDict

import pygame
import numpy as np
from scipy import signal  # noqa: F401  (mantido: outros módulos importam daqui)

try:
    from audio import sintetizador as sint
except ImportError:                                   # rodando de dentro de audio/
    try:
        from . import sintetizador as sint
    except ImportError:
        sint = None

MODOS = ("sintetico", "realista", "profissional")


class MotorAudioDual:
    """
    Motor da tablatura (nota a nota, em tempo real). Mesma API de antes:
        MotorAudioDual(modo), alternar_modo(), alternar_instrumento_synth(),
        reproduzir_nota(corda, casa, tecnica, duracao, volume)

    Modos:
    - 'sintetico'   : Pygame + Numpy (sempre disponível).
    - 'realista'    : FluidSynth + SoundFont GM (como antes). Se a DLL do FluidSynth
                      não carregar, usa o TinySoundFont (pip install tinysoundfont),
                      que não precisa de DLL.
    - 'profissional': guitarra com samples reais (DI) + amplificador + caixa
                      (audio/sampler_guitarra.py + audio/amp_guitarra.py), com o
                      timbre escolhido em definir_timbre(). Baixo, voz e bateria
                      usam o SoundFont nesse modo.

    Cada nota é renderizada uma vez e guardada em cache; a primeira vez usa um
    amp mais leve (sem oversampling) para não travar a tela, e uma thread gera a
    versão de qualidade máxima que substitui a do cache logo em seguida.
    Use preparar([...]) antes de tocar uma música para já deixar tudo pronto.
    """

    TAM_CACHE = 260

    def __init__(self, modo=None):
        self.motor_realista_ok = False
        self.fluidsynth_ok = False
        self.profissional_ok = False
        self.instrumento_atual = "Guitarra"
        self.timbre = "real_clean"

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
            (0.3, 0.7),  # e (aguda)
            (0.4, 0.6),  # B
            (0.5, 0.5),  # G
            (0.5, 0.5),  # D
            (0.6, 0.4),  # A
            (0.7, 0.3)   # E (grave)
        ]

        self.freqs_base = [329.63, 246.94, 196.00, 146.83, 110.00, 82.41]
        self.midi_base = [64, 59, 55, 50, 45, 40]
        self.cache_sons = {}

        # cache das notas renderizadas (modos realista/profissional)
        self._cache = OrderedDict()
        self._prontos = {}                 # chave -> array (qualidade máxima, vindo da thread)
        self._fila = []
        self._trava = threading.Lock()
        self._evento = threading.Event()
        self._trabalhador = None

        self.instrumentos_presets = {
            "Guitarra": 27,
            "Baixo": 33,
            "Bateria": 0,  # Tratado no canal de percussão
            "Voz": 52
        }

        # Setup do FluidSynth (Modo Realista)
        self.sf2_path = os.path.join("assets", "audio", "soundfonts", "general_midi.sf2")
        self.fs = None
        self.sfid = None

        self.inicializar_realista()
        self.inicializar_profissional()

        if modo is None:
            modo = "profissional" if self.profissional_ok else ("realista" if self.motor_realista_ok else "sintetico")
        self.modo = "sintetico"
        self.alternar_modo(modo)

    # ------------------------------------------------------------------ setup
    def inicializar_realista(self):
        """Injeta a DLL no PATH e tenta carregar o FluidSynth; se falhar, tenta o TinySoundFont."""
        bin_dir = os.path.join(os.getcwd(), "assets", "bin", "fluidsynth")
        if os.path.exists(bin_dir):
            if bin_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(bin_dir)

        if os.path.exists(self.sf2_path):
            try:
                import fluidsynth
                self.fs = fluidsynth.Synth()
                self.fs.start(driver="dsound")
                self.sfid = self.fs.sfload(self.sf2_path)
                self.fs.program_select(0, self.sfid, 0, self.instrumentos_presets["Guitarra"])
                self.fs.set_reverb(0.4, 0.3, 0.5, 0.2)
                self.fluidsynth_ok = True
                print("[DUAL-ENGINE] FluidSynth inicializado com sucesso!")
            except Exception as e:
                print(f"[DUAL-ENGINE] FluidSynth indisponível ({e}).")
                self.fs = None
        else:
            print(f"[DUAL-ENGINE] SoundFont GM não encontrado em {self.sf2_path}.")

        tsf_ok = bool(sint and sint.soundfont_disponivel()[0])
        if not self.fluidsynth_ok and tsf_ok:
            print("[DUAL-ENGINE] Modo realista via TinySoundFont (sem DLL): "
                  + sint.soundfont_disponivel()[1])
        self.motor_realista_ok = self.fluidsynth_ok or tsf_ok

    def inicializar_profissional(self):
        """Verifica o sampler de guitarra e aquece os samples numa thread."""
        if sint is None:
            return
        ok, motivo = sint.sampler_disponivel()
        self.profissional_ok = ok
        if not ok:
            print(f"[DUAL-ENGINE] Modo profissional indisponível: {motivo}")
            return
        taxa = self.sample_rate

        def aquecer():
            try:
                from audio import sampler_guitarra as sg
            except ImportError:
                from . import sampler_guitarra as sg
            try:
                sg.aquecer(taxa)
                if sint.soundfont_disponivel()[0]:
                    sint.render_gm(40, 0.05, 90, 33, taxa)      # carrega o SoundFont também
                print("[DUAL-ENGINE] Guitarra profissional pronta.")
            except Exception as e:
                print(f"[DUAL-ENGINE] Falha ao aquecer o sampler: {e}")

        threading.Thread(target=aquecer, daemon=True).start()

    # ------------------------------------------------------------------ modos
    def alternar_modo(self, novo_modo):
        if novo_modo not in MODOS:
            novo_modo = "sintetico"
        if novo_modo == "profissional" and not self.profissional_ok:
            self.modo = "realista" if self.motor_realista_ok else "sintetico"
            print(f"[DUAL-ENGINE] Aviso: modo profissional indisponível. Usando {self.modo}.")
            return False
        if novo_modo == "realista" and not self.motor_realista_ok:
            print("[DUAL-ENGINE] Aviso: Modo realista indisponível. Mantendo sintético.")
            self.modo = "sintetico"
            return False
        self.modo = novo_modo
        print(f"[DUAL-ENGINE] Modo alterado para: {self.modo}")
        return True

    def modos_disponiveis(self):
        return [m for m in MODOS if m == "sintetico"
                or (m == "realista" and self.motor_realista_ok)
                or (m == "profissional" and self.profissional_ok)]

    def definir_timbre(self, timbre):
        """Timbre da guitarra no modo profissional: real_clean, real_crunch, real_drive,
        real_highgain ou real_di (veja audio/sintetizador.TIMBRES)."""
        self.timbre = timbre

    def timbres_disponiveis(self):
        if sint is None:
            return []
        return [(i, n) for i, n, p in sint.TIMBRES if isinstance(p, str) and p.startswith("amp:")]

    def alternar_instrumento_synth(self, nome):
        self.instrumento_atual = nome
        if self.fluidsynth_ok and self.fs:
            if nome == "Bateria":
                print("[DUAL-ENGINE] Instrumento alterado para Bateria (Canal Percussão)")
            else:
                preset = self.instrumentos_presets.get(nome, 27)
                self.fs.program_select(0, self.sfid, 0, preset)
                print(f"[DUAL-ENGINE] Timbre alterado para {nome} (Preset GM {preset})")

    # --------------------------------------------------------------- técnicas
    @staticmethod
    def traduzir_tecnica(tecnica):
        """Código de técnica da tablatura -> (técnica do sintetizador, bend em semitons).
        Aceita letras (b, br, bf, h, p, /, \\, ~, v, x, pm) e palavras
        (bend, release, hammer, pull, slide, slide out, vibrato, dead, palm)."""
        t = (tecnica or "").strip().lower()
        if not t:
            return "", 0.0
        cheio = any(k in t for k in ("b1", "bf", "full", "1 tom", "b2"))
        for palavra, codigo in (("slide out", "\\"), ("vibrato", "~"), ("hammer", "h"), ("pull", "p"),
                                ("slide", "/"), ("release", "r"), ("bend", "b"), ("dead note", "x"),
                                ("dead", "x"), ("morta", "x"), ("palm mute", "M"), ("palm", "M"),
                                ("p.m.", "M"), ("p.m", "M"), ("pm", "M"), ("full", ""), ("1 tom", "")):
            t = t.replace(palavra, codigo)
        partes, bend = [], 0.0
        if "x" in t:
            partes.append("dead note")
        if "M" in t:
            partes.append("P.M.")
        if "b" in t:
            bend = 2.0 if cheio else 1.0
            partes.append("bend 1 tom" if cheio else "bend ½")
            if "r" in t:
                partes.append("release")
        if "h" in t:
            partes.append("hammer")
        if "p" in t:
            partes.append("pull")
        if "\\" in t:
            partes.append("slide out")
        elif "/" in t or t == "s":
            partes.append("slide")
        if "~" in t or "v" in t:
            partes.append("vibrato")
        return " ".join(partes), bend

    # ------------------------------------------------------------ reprodução
    def reproduzir_nota(self, corda, casa, tecnica='', duracao=0.8, volume=100):
        is_bateria = getattr(self, "instrumento_atual", "") == "Bateria"

        # --- FLUIDSYNTH (realista, como antes) ---
        if self.modo == "realista" and self.fluidsynth_ok:
            canal_midi = 9 if is_bateria else 0
            if is_bateria:
                midi_note = 36 + casa + (corda - 1)
            else:
                midi_note = self.midi_base[corda - 1] + casa
            if 'b' in (tecnica or '') and not is_bateria:
                self.fs.pitch_bend(canal_midi, 8192 + 2000)
            else:
                self.fs.pitch_bend(canal_midi, 8192)
            self.fs.noteon(canal_midi, midi_note, volume)

            def desligar():
                pygame.time.wait(int(duracao * 1000))
                self.fs.noteoff(canal_midi, midi_note)
            threading.Thread(target=desligar, daemon=True).start()
            return

        # --- RENDERIZADO (profissional ou realista sem DLL) ---
        if self.modo in ("profissional", "realista") and sint is not None and 1 <= corda <= 6:
            try:
                if self._tocar_renderizado(corda, casa, tecnica, duracao, volume, is_bateria):
                    return
            except Exception as e:
                print(f"[DUAL-ENGINE] Falha no modo {self.modo}: {e}. Usando sintético.")

        # --- FLUXO SINTÉTICO (Fallback) ---
        freq_inicial = (self.freqs_base[corda - 1] * (2 ** (casa / 12.0))) if 1 <= corda <= 6 else 0
        if freq_inicial == 0:
            return

        cache_key = (corda, casa, tecnica, round(duracao, 2), volume)
        if cache_key in self.cache_sons:
            audio = self.cache_sons[cache_key]
        else:
            freq_final = freq_inicial
            if 'b' in (tecnica or ''):
                freq_final *= (2 ** (1 / 12.0))
            audio = self.gerar_audio_basico(freq_inicial, freq_final, duracao)
            if len(self.cache_sons) < 300:
                self.cache_sons[cache_key] = audio

        try:
            som = pygame.sndarray.make_sound(audio)
            canal = self.canais_cordas[corda - 1]
            p_l, p_r = self.pans_cordas[corda - 1]
            canal.set_volume(p_l * (volume / 100.0), p_r * (volume / 100.0))
            canal.play(som)
        except Exception as e:
            print(f"[ERRO SYNTH] {e}")

    def _chave(self, corda, casa, tecnica, duracao, volume, is_bateria):
        return (self.modo, self.instrumento_atual, self.timbre if self.modo == "profissional" else "",
                corda, casa, (tecnica or "").strip().lower(), round(max(0.05, duracao) * 20) / 20,
                int(volume) // 8, is_bateria)

    def _render_array(self, chave, rapido):
        modo, inst, timbre, corda, casa, tec_txt, dur, vol8, is_bateria = chave
        vel = int(np.clip(vol8 * 8 + 4, 1, 127))
        tec, bend = self.traduzir_tecnica(tec_txt)
        taxa = self.sample_rate
        if is_bateria:
            buf = sint.render_gm(36 + casa + (corda - 1), dur, vel, 0, taxa, bateria=True)
        elif inst != "Guitarra":
            base = self.midi_base[corda - 1] - (12 if inst == "Baixo" else 0)
            buf = sint.render_gm(base + casa, dur, vel, self.instrumentos_presets.get(inst, 27),
                                 taxa, bend=bend)
        else:
            nota = sint.NotaAudio(0.0, dur, self.midi_base[corda - 1] + casa, vel, bend, tec, corda)
            tb = timbre if modo == "profissional" else "clean"
            cauda = 0.12 if "dead note" in tec else 0.35
            buf, _ = sint.render_notas([nota], dur + cauda, taxa, tb, loop=False, pico=0.8,
                                       dobrar=not rapido, rapido=rapido, cauda=0.2)
            # o render normaliza cada nota: devolve a dinâmica pela intensidade
            buf = buf * (0.35 + 0.65 * (vel / 127.0) ** 1.3)
        if buf is None:
            return None
        if not is_bateria and inst != "Guitarra":
            pico = float(np.abs(buf).max()) or 1.0
            buf = buf / pico * 0.8 * (0.35 + 0.65 * vel / 127.0)
        return buf

    def _para_som(self, buf):
        x = (np.clip(buf, -1, 1) * 30000).astype(np.int16)
        if self.channels == 1:
            x = x.mean(axis=1).astype(np.int16)
        elif self.channels > 2:
            x = np.concatenate([x] + [x[:, :1]] * (self.channels - 2), axis=1)
        return pygame.sndarray.make_sound(np.ascontiguousarray(x))

    def _guardar(self, chave, som):
        self._cache[chave] = som
        self._cache.move_to_end(chave)
        while len(self._cache) > self.TAM_CACHE:
            self._cache.popitem(last=False)

    def _aplicar_prontos(self):
        with self._trava:
            prontos, self._prontos = self._prontos, {}
        for chave, buf in prontos.items():
            if buf is not None:
                self._guardar(chave, (self._para_som(buf), True))

    def _tocar_renderizado(self, corda, casa, tecnica, duracao, volume, is_bateria):
        self._aplicar_prontos()
        chave = self._chave(corda, casa, tecnica, duracao, volume, is_bateria)
        item = self._cache.get(chave)
        if item is None:
            profissional_guitarra = (self.modo == "profissional" and self.instrumento_atual == "Guitarra"
                                     and not is_bateria)
            buf = self._render_array(chave, rapido=profissional_guitarra)
            if buf is None:
                return False
            item = (self._para_som(buf), not profissional_guitarra)
            self._guardar(chave, item)
            if profissional_guitarra:
                self._agendar(chave)
        else:
            self._cache.move_to_end(chave)
        som = item[0]
        canal = self.canais_cordas[corda - 1]      # nota nova na mesma corda corta a anterior
        p_l, p_r = self.pans_cordas[corda - 1]
        canal.set_volume(0.5 + p_l * 0.5, 0.5 + p_r * 0.5)
        canal.play(som)
        return True

    # ------------------------------------------------ qualidade máxima em 2º plano
    def _agendar(self, chave):
        with self._trava:
            if chave not in self._fila:
                self._fila.append(chave)
        self._evento.set()
        if self._trabalhador is None or not self._trabalhador.is_alive():
            self._trabalhador = threading.Thread(target=self._trabalhar, daemon=True)
            self._trabalhador.start()

    def _trabalhar(self):
        while True:
            with self._trava:
                chave = self._fila.pop(0) if self._fila else None
            if chave is None:
                self._evento.clear()
                if not self._evento.wait(5.0):
                    return
                continue
            try:
                buf = self._render_array(chave, rapido=False)
            except Exception as e:
                print(f"[DUAL-ENGINE] render em 2º plano falhou: {e}")
                buf = None
            with self._trava:
                self._prontos[chave] = buf
            time.sleep(0.001)

    def preparar(self, notas):
        """Deixa uma música pronta antes de tocar.
        notas: iterável de (corda, casa, tecnica, duracao, volume)."""
        if self.modo not in ("profissional", "realista") or sint is None:
            return
        is_bateria = self.instrumento_atual == "Bateria"
        for corda, casa, tecnica, duracao, volume in notas:
            chave = self._chave(corda, casa, tecnica, duracao, volume, is_bateria)
            item = self._cache.get(chave)
            if item is None or not item[1]:
                self._agendar(chave)

    # ------------------------------------------------ ajudantes para as telas de tablatura
    @staticmethod
    def ler_celula(celula):
        """Célula da grade ('12', '5b', '7hd2v80', '3/~') -> (casa, tecnica, colunas, volume) ou None.
        Mesma leitura do GerenciadorDadosTablatura._processar_e_tocar."""
        import re
        texto = str(celula)
        m = re.match(r"(\d+)", texto)
        if not m:
            return None
        vol = re.search(r"v(\d+)", texto)
        dur = re.search(r"d(\d+)", texto)
        tecnica = "".join(re.findall(r"[a-zA-Z/~]+", texto[len(m.group(1)):]))
        tecnica = re.sub(r"v\d*|d\d*", "", tecnica)
        return int(m.group(1)), tecnica, int(dur.group(1)) if dur else 1, int(vol.group(1)) if vol else 100

    def preparar_grade(self, grade, seg_por_coluna, sustain=1.5):
        """Pré-renderiza todas as notas de uma grade de tablatura antes do play."""
        notas = []
        for corda_idx, linha in enumerate(grade[:6]):
            for celula in linha:
                if celula == "-":
                    continue
                lida = self.ler_celula(celula)
                if lida:
                    casa, tecnica, cols, vol = lida
                    notas.append((corda_idx + 1, casa, tecnica, cols * seg_por_coluna * sustain, vol))
        self.preparar(notas)

    def rotulo_som(self):
        """Texto curto do som atual, para o botão das telas de tablatura."""
        if self.modo == "profissional" and sint is not None:
            return "Som: " + sint.nome_timbre(self.timbre).replace("Real: ", "")
        return {"realista": "Som: Realista", "sintetico": "Som: Sintético"}.get(self.modo, "Som")

    def proximo_som(self):
        """Clique no botão de som: percorre os timbres profissionais, depois realista e sintético."""
        sequencia = []
        if self.profissional_ok:
            sequencia += [("profissional", t) for t, _ in self.timbres_disponiveis() if t != "real_di"]
        if self.motor_realista_ok:
            sequencia.append(("realista", None))
        sequencia.append(("sintetico", None))
        atual = (self.modo, self.timbre if self.modo == "profissional" else None)
        i = sequencia.index(atual) if atual in sequencia else -1
        modo, timbre = sequencia[(i + 1) % len(sequencia)]
        if timbre:
            self.definir_timbre(timbre)
        self.alternar_modo(modo)
        return self.rotulo_som()

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
