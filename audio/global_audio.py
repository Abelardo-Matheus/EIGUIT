# -*- coding: utf-8 -*-
"""
Cadeia de sinal de entrada do EIGUIT Studio.

Fluxo: captura (sounddevice) -> buffer circular -> remocao de DC e passa-alta
-> portao de ruido adaptativo -> deteccao de altura (YIN) com correcao de
oitava e suavizacao -> nota, desvio em cents e confianca.

O callback de audio roda em thread de tempo real: ele apenas copia amostras
para um buffer pre-alocado, sem alocar memoria nem fazer contas pesadas.
Toda a analise acontece em atualizar_analise_ia(), chamada pelo loop principal.
"""
import math
import threading
import time

import numpy as np

try:
    import sounddevice as sd
except (ImportError, OSError) as _erro_audio:
    # Sem PortAudio ou sem a biblioteca: o estudio abre mesmo assim, so que
    # sem captura de audio. Melhor que derrubar o programa inteiro.
    sd = None
    print(f'[GLOBAL AUDIO] Captura indisponivel ({_erro_audio}). '
          'O programa segue sem afinador e sem jogos de audio.')

NOTAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def _tabela_frequencias(oitava_min=0, oitava_max=6, referencia=440.0):
    """Gera {'C4': 261.63, ...} a partir do temperamento igual."""
    tabela = {}
    for oitava in range(oitava_min, oitava_max + 1):
        for i, nome in enumerate(NOTAS):
            semitons = (oitava - 4) * 12 + (i - 9)
            tabela[f'{nome}{oitava}'] = round(referencia * (2 ** (semitons / 12.0)), 2)
    return tabela


# Mantida para compatibilidade: usada pelo afinador de referencia por corda
FREQS_NOTAS = _tabela_frequencias()

# Faixas de busca por familia de instrumento (Hz)
FAIXAS_INSTRUMENTO = {
    'guitarra': (70.0, 1320.0),   # E2 ate E6 aproximadamente
    'guitarra7': (55.0, 1320.0),  # inclui o Si grave da setima corda
    'baixo': (30.0, 500.0),       # B0 do baixo de 5 cordas ate ~B4
    'teclado': (55.0, 2100.0),
    'voz': (75.0, 1100.0),
    'ukulele': (240.0, 1200.0),
}
FAIXA_PADRAO = (55.0, 1320.0)


def freq_para_nota(freq, referencia_la=440.0):
    """
    Converte uma frequencia em (nome, oitava, desvio_em_cents).
    Devolve (None, None, 0.0) quando a frequencia nao e utilizavel.
    """
    try:
        f = float(freq)
    except (TypeError, ValueError):
        return None, None, 0.0
    if f < 16.0:
        return None, None, 0.0
    semitons_exatos = 12.0 * math.log2(f / referencia_la)
    semitons = int(round(semitons_exatos))
    cents = (semitons_exatos - semitons) * 100.0
    indice = (semitons + 9) % 12
    oitava = 4 + (semitons + 9) // 12
    return NOTAS[indice], int(oitava), cents


class GlobalAudioEngine:
    """
        Como funciona: Captura o audio de entrada em um buffer circular e
        analisa altura, nivel e ataques sob demanda.
        Para que serve: Fonte unica de informacao de audio para afinador,
        jogos e estudos.
        Onde e usada: Instanciada em main.py e passada aos modulos.
    """

    # Quantas estimativas de altura entram na mediana de suavizacao
    JANELA_SUAVIZACAO = 5
    # Intervalo minimo entre analises pesadas
    INTERVALO_ANALISE_MS = 30

    def __init__(self, sample_rate=48000, segundos_buffer=0.1):
        self.sr = sample_rate
        self.canais = 1
        self.device_id = sd.default.device[0] if (sd and sd.default.device) else None
        self.stream = None
        self.ativo = False

        # --- buffer circular pre-alocado -----------------------------------
        self.tamanho_buffer = int(self.sr * segundos_buffer)
        self._buffer = np.zeros(self.tamanho_buffer, dtype=np.float32)
        self._escrita = 0
        self._lock = threading.Lock()

        # --- leituras publicas ---------------------------------------------
        self.freq_detectada = 0.0
        self.nota_detectada = ''
        self.oitava_detectada = None
        self.cents_detectados = 0.0
        self.confianca = 0.0
        self.nota_unicao = ''
        self.notas_polifonicas = []
        self.volume_atual = 0.0
        self.nivel_db = -90.0

        # --- estado interno da analise -------------------------------------
        self.instrumento = 'guitarra'
        self.referencia_la = 440.0
        self.piso_ruido_db = -60.0
        self.margem_gate_db = 8.0
        self._historico_freq = []
        self._ultima_freq_boa = 0.0
        self._ultimo_processamento = 0.0
        self._dc = 0.0
        self._hp_anterior_entrada = 0.0
        self._hp_anterior_saida = 0.0

        # --- deteccao de ataque --------------------------------------------
        self._envelope = 0.0
        self._envelope_lento = 0.0
        self._ultimo_ataque = 0.0
        self.refratario_ataque = 0.08
        self._ataque_pendente = False

        # --- gravacao -------------------------------------------------------
        self.gravando = False
        self.frames_gravacao = []

        self._librosa = None
        self.iniciar()

    # ------------------------------------------------------------- captura
    def callback_audio(self, indata, frames, time_info, status):
        """
        Roda na thread de audio. Faz o minimo possivel: copia o bloco para o
        buffer circular e guarda o RMS. Sem alocacoes nem numpy pesado.
        """
        try:
            bloco = indata[:, 0]
        except (IndexError, TypeError):
            return

        n = len(bloco)
        if n == 0:
            return

        with self._lock:
            fim = self._escrita + n
            if fim <= self.tamanho_buffer:
                self._buffer[self._escrita:fim] = bloco
            else:
                corte = self.tamanho_buffer - self._escrita
                self._buffer[self._escrita:] = bloco[:corte]
                self._buffer[:n - corte] = bloco[corte:]
            self._escrita = fim % self.tamanho_buffer

        self.volume_atual = float(np.sqrt(np.mean(bloco.astype(np.float32) ** 2)))

        if self.gravando:
            self.frames_gravacao.append(indata.copy())

    def instantaneo(self):
        """Copia do buffer circular em ordem cronologica."""
        with self._lock:
            escrita = self._escrita
            dados = np.concatenate((self._buffer[escrita:], self._buffer[:escrita]))
        return dados

    @property
    def buffer(self):
        """Compatibilidade: leitura cronologica do buffer circular."""
        return self.instantaneo()

    # ------------------------------------------------- condicionamento ----
    def _condicionar(self, sinal):
        """
        Remove nivel continuo e corta graves inuteis (zumbido de rede,
        ruido de manuseio) com um passa-alta de um polo.
        """
        if sinal.size == 0:
            return sinal
        # Remocao de DC pela media do bloco
        sinal = sinal - np.mean(sinal)

        # Passa-alta simples: corte proporcional a menor nota procurada
        fmin, _ = self.faixa_atual()
        corte = max(20.0, fmin * 0.7)
        rc = 1.0 / (2 * math.pi * corte)
        alpha = rc / (rc + 1.0 / self.sr)

        saida = np.empty_like(sinal)
        anterior_entrada = self._hp_anterior_entrada
        anterior_saida = self._hp_anterior_saida
        # Implementacao vetorizada aproximada: filtra em blocos com lfilter
        try:
            from scipy.signal import lfilter
            b = [alpha, -alpha]
            a = [1.0, -alpha]
            saida = lfilter(b, a, sinal).astype(np.float32)
        except Exception:
            # Sem scipy: laco simples, ainda barato para 4800 amostras
            for i, x in enumerate(sinal):
                y = alpha * (anterior_saida + x - anterior_entrada)
                saida[i] = y
                anterior_entrada = x
                anterior_saida = y
            self._hp_anterior_entrada = float(anterior_entrada)
            self._hp_anterior_saida = float(anterior_saida)
        return saida

    def faixa_atual(self):
        """Faixa de busca de altura para o instrumento selecionado."""
        return FAIXAS_INSTRUMENTO.get(self.instrumento, FAIXA_PADRAO)

    def definir_instrumento(self, nome):
        """Ajusta a faixa de busca conforme o instrumento em uso."""
        if nome in FAIXAS_INSTRUMENTO:
            self.instrumento = nome
            self._historico_freq.clear()

    # ------------------------------------------------------ nivel e gate --
    def _atualizar_nivel(self, sinal):
        """Calcula o nivel em dBFS e mantem um piso de ruido adaptativo."""
        rms = float(np.sqrt(np.mean(sinal ** 2))) if sinal.size else 0.0
        self.volume_atual = rms
        self.nivel_db = 20 * math.log10(rms) if rms > 1e-7 else -90.0

        # O piso sobe devagar e desce rapido, acompanhando o ambiente
        if self.nivel_db < self.piso_ruido_db:
            self.piso_ruido_db += (self.nivel_db - self.piso_ruido_db) * 0.25
        else:
            self.piso_ruido_db += (self.nivel_db - self.piso_ruido_db) * 0.002
        self.piso_ruido_db = max(-90.0, min(-20.0, self.piso_ruido_db))
        return rms

    def passou_do_gate(self, gate_db=None):
        """Diz se o sinal atual esta acima do portao de ruido."""
        limite = gate_db if gate_db is not None else self.piso_ruido_db + self.margem_gate_db
        return self.nivel_db > limite

    # ------------------------------------------------------------ ataques --
    def _detectar_ataque(self, rms):
        """
        Marca um ataque quando a energia sobe rapido acima da media recente.
        Bem mais confiavel que comparar o volume com um limiar fixo.
        """
        self._envelope += (rms - self._envelope) * 0.55
        self._envelope_lento += (rms - self._envelope_lento) * 0.06

        agora = time.time()
        subida = self._envelope > self._envelope_lento * 1.8 + 0.004
        if subida and (agora - self._ultimo_ataque) > self.refratario_ataque:
            self._ultimo_ataque = agora
            self._ataque_pendente = True

    def houve_ataque(self):
        """Consome e devolve True se houve um ataque desde a ultima chamada."""
        if self._ataque_pendente:
            self._ataque_pendente = False
            return True
        return False

    # ------------------------------------------------------------ altura --
    def _corrigir_oitava(self, freq):
        """
        YIN erra oitava com facilidade em cordas graves. Quando a nova leitura
        e o dobro ou a metade da anterior, fica com a que estiver mais perto.
        """
        anterior = self._ultima_freq_boa
        if anterior <= 0 or freq <= 0:
            return freq
        fmin, fmax = self.faixa_atual()
        candidatos = [freq, freq * 2.0, freq / 2.0]
        validos = [c for c in candidatos if fmin <= c <= fmax]
        if not validos:
            return freq
        return min(validos, key=lambda c: abs(math.log2(c / anterior)))

    def _suavizar(self, freq):
        """Mediana das ultimas leituras, para tirar o tremor da agulha."""
        self._historico_freq.append(freq)
        if len(self._historico_freq) > self.JANELA_SUAVIZACAO:
            self._historico_freq.pop(0)
        return float(np.median(self._historico_freq))

    def atualizar_analise_ia(self, sensitivity=0.3, gate_db=None):
        """
            Como funciona: Condiciona o sinal, aplica o portao de ruido e roda
            a deteccao de altura com correcao de oitava e suavizacao.
            Para que serve: Atualizar nota, cents, confianca e nivel.
            Onde e usada: Chamado a cada quadro por main.py.
        """
        agora = time.time() * 1000.0
        if agora - self._ultimo_processamento < self.INTERVALO_ANALISE_MS:
            return
        self._ultimo_processamento = agora

        bruto = self.instantaneo()
        if bruto.size == 0:
            return

        sinal = self._condicionar(bruto)
        rms = self._atualizar_nivel(sinal)
        self._detectar_ataque(rms)

        if not self.passou_do_gate(gate_db):
            self.freq_detectada = 0.0
            self.nota_detectada = ''
            self.oitava_detectada = None
            self.cents_detectados = 0.0
            self.confianca = 0.0
            self.nota_unicao = ''
            self.notas_polifonicas = []
            self._historico_freq.clear()
            return

        if self._librosa is None:
            try:
                import librosa
                self._librosa = librosa
            except ImportError:
                self._librosa = False
        if not self._librosa:
            return

        fmin, fmax = self.faixa_atual()
        try:
            f0 = self._librosa.yin(sinal, fmin=fmin, fmax=fmax, sr=self.sr,
                                   trough_threshold=max(0.05, min(0.9, sensitivity)))
            validos = f0[(f0 > fmin) & (f0 < fmax)]
            if validos.size:
                bruta = float(np.median(validos))
                # Confianca: quanto as leituras do bloco concordam entre si
                dispersao = float(np.std(validos)) / max(bruta, 1e-6)
                self.confianca = float(max(0.0, min(1.0, 1.0 - dispersao * 6.0)))

                freq = self._corrigir_oitava(bruta)
                freq = self._suavizar(freq)
                self.freq_detectada = freq
                self._ultima_freq_boa = freq

                nome, oitava, cents = freq_para_nota(freq, self.referencia_la)
                self.nota_detectada = nome or ''
                self.oitava_detectada = oitava
                self.cents_detectados = cents
                self.nota_unicao = f'{nome}{oitava}' if nome else ''
            else:
                self.freq_detectada = 0.0
                self.confianca = 0.0
        except Exception:
            self.freq_detectada = 0.0
            self.confianca = 0.0

        # Analise polifonica so quando ha sinal forte: e a parte mais cara
        if self.nivel_db > self.piso_ruido_db + 18:
            try:
                chroma = self._librosa.feature.chroma_stft(y=sinal, sr=self.sr,
                                                           tuning=0.0)
                media = np.mean(chroma, axis=1)
                media = media / (np.max(media) + 1e-06)
                self.notas_polifonicas = [NOTAS[i] for i, v in enumerate(media)
                                          if v > 0.8]
            except Exception:
                self.notas_polifonicas = []
        else:
            self.notas_polifonicas = []

    # ---------------------------------------------------------- gravacao --
    def iniciar_gravacao(self):
        """Comeca a acumular os blocos de entrada em memoria."""
        print('[GLOBAL AUDIO] Gravacao iniciada.')
        self.frames_gravacao = []
        self.gravando = True

    def parar_gravacao(self, output_path='temp_recording.wav'):
        """Encerra a gravacao e grava um WAV de 16 bits."""
        if not self.gravando:
            return None
        self.gravando = False
        if not self.frames_gravacao:
            return None

        import wave
        try:
            dados = np.concatenate(self.frames_gravacao, axis=0)
            inteiros = np.clip(dados * 32767, -32768, 32767).astype(np.int16)
            with wave.open(output_path, 'wb') as arq:
                arq.setnchannels(self.canais)
                arq.setsampwidth(2)
                arq.setframerate(self.sr)
                arq.writeframes(inteiros.tobytes())
            print(f'[GLOBAL AUDIO] Gravacao salva em {output_path}')
            return output_path
        except Exception as e:
            print(f'[GLOBAL AUDIO] Erro ao salvar gravacao: {e}')
            return None

    # ----------------------------------------------------------- stream ---
    def iniciar(self):
        """Abre o stream de entrada, tentando taxas alternativas se preciso."""
        if self.ativo or sd is None:
            return
        for taxa in [self.sr, 44100, 48000, 22050]:
            try:
                self.stream = sd.InputStream(
                    samplerate=taxa, channels=self.canais, device=self.device_id,
                    callback=self.callback_audio, blocksize=1024, latency='high')
                self.stream.start()
                if taxa != self.sr:
                    self.sr = taxa
                    self.tamanho_buffer = int(self.sr * 0.1)
                    with self._lock:
                        self._buffer = np.zeros(self.tamanho_buffer, dtype=np.float32)
                        self._escrita = 0
                self.ativo = True
                print(f'[GLOBAL AUDIO] Captura iniciada no ID {self.device_id} @ {self.sr}Hz')
                return
            except Exception as e:
                print(f'[GLOBAL AUDIO] Falha ao iniciar @ {taxa}Hz: {e}')
        print('[GLOBAL AUDIO] Nenhum dispositivo de entrada disponivel. '
              'O programa segue funcionando sem audio.')

    def parar(self):
        """Fecha o stream de entrada."""
        if self.ativo and self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.ativo = False

    def mudar_dispositivo(self, novo_id):
        """Troca a entrada de audio em uso."""
        self.parar()
        self.device_id = novo_id
        self._historico_freq.clear()
        self._ultima_freq_boa = 0.0
        self.iniciar()

    def obter_lista_entradas(self):
        """Lista os dispositivos de entrada disponiveis."""
        if sd is None:
            return []
        try:
            dispositivos = sd.query_devices()
        except Exception:
            return []
        return [{'id': i, 'nome': d['name']} for i, d in enumerate(dispositivos)
                if d['max_input_channels'] > 0]
