# -*- coding: utf-8 -*-
"""
Analisador IA - tocar por cima: reproduz a referencia (com contagem de
entrada, metronomo e repeticoes opcionais) e grava AO MESMO TEMPO os canais
escolhidos da pedaleira, com a posicao de cada amostra gravada amarrada ao
playback. Depois compensa a latencia, confere a tomada (silencio, clipping,
duracao, musica vazando na entrada) e guarda os takes.

Sincronia
    Mesmo dispositivo de entrada e saida -> um stream duplex: o bloco k da
    entrada e o bloco k da saida vem no mesmo callback, entao a amostra i
    gravada "corresponde" a amostra i tocada; o que sobra e a latencia de ida
    e volta (calibrada na Etapa 1).
    Dispositivos diferentes -> dois streams; o primeiro bloco de cada um
    guarda o relogio do PortAudio (inputBufferAdcTime / outputBufferDacTime)
    e a diferenca e convertida em amostras.

Nada disso roda na thread da interface: GravadorPlayAlong trabalha numa
thread propria, com progresso e cancelamento. Para testar sem placa de som
existe BackendSimulado (latencia e "musico" configuraveis).
"""
import json
import os
import threading
import time

import numpy as np

from audio import dispositivos as disp


# ===========================================================================
# MONTAGEM DO QUE TOCA
# ===========================================================================

def clique(sr, forte=False):
    n = int(0.03 * sr)
    t = np.arange(n) / sr
    f = 1600.0 if forte else 1100.0
    return (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.006) * (0.9 if forte else 0.6)).astype(np.float32)


def montar_playback(ref, sr, bpm=None, compassos_contagem=1, batidas_compasso=4, metronomo=False,
                    repeticoes=1, volume_musica=1.0, volume_clique=0.7):
    """
        Como funciona: [contagem][trecho x repeticoes], estereo float32. A
        contagem e so clique; com metronomo, o clique segue durante a musica.
        Devolve (audio (N,2), inicio_musica_amostra, fim_musica_amostra).
        Para que serve: o que vai para a saida durante a gravacao.
    """
    ref = np.asarray(ref, dtype=np.float32)
    if ref.ndim == 2:
        ref = ref.mean(axis=1)
    bpm = float(bpm or 0)
    batida = 60.0 / bpm if bpm > 0 else 0.5
    n_contagem = int(round(compassos_contagem * batidas_compasso * batida * sr)) if compassos_contagem > 0 else 0
    musica = np.tile(ref * float(volume_musica), max(1, int(repeticoes)))
    total = n_contagem + musica.size + int(0.3 * sr)
    saida = np.zeros(total, dtype=np.float32)
    saida[n_contagem:n_contagem + musica.size] = musica
    cliques = []
    if n_contagem:
        for k in range(int(compassos_contagem * batidas_compasso)):
            cliques.append((int(round(k * batida * sr)), k % batidas_compasso == 0))
    if metronomo and bpm > 0:
        k = 0
        while True:
            i = n_contagem + int(round(k * batida * sr))
            if i >= n_contagem + musica.size:
                break
            cliques.append((i, k % batidas_compasso == 0))
            k += 1
    for i, forte in cliques:
        c = clique(sr, forte) * float(volume_clique)
        j = min(saida.size, i + c.size)
        saida[i:j] += c[:j - i]
    pico = float(np.max(np.abs(saida))) if saida.size else 0.0
    if pico > 0.98:
        saida *= 0.98 / pico
    return np.stack([saida, saida], axis=1), n_contagem, n_contagem + musica.size


# ===========================================================================
# BACKENDS (real e simulado)
# ===========================================================================

class BackendSoundDevice:
    """Toca 'saida' e grava 'canais' da entrada; devolve (gravado, deslocamento_amostras)."""

    def executar(self, saida, cfg, canais, progresso=None, cancelar=None):
        ok, msg = disp.disponivel()
        if not ok:
            raise RuntimeError(msg)
        sd = disp.sd
        sr, bloco = int(cfg.taxa), int(cfg.buffer)
        n_total = saida.shape[0]
        n_in = max(1, int(cfg.canais_entrada or max(canais) + 1))
        gravado = np.zeros((n_total + sr, len(canais)), dtype=np.float32)
        estado = {'pos_out': 0, 'pos_in': 0, 't_dac0': None, 't_adc0': None, 'erro': None,
                  'underflow': 0}
        fim = threading.Event()

        def gravar(indata, frames):
            p = estado['pos_in']
            k = min(frames, gravado.shape[0] - p)
            if k > 0:
                for j, c in enumerate(canais):
                    gravado[p:p + k, j] = indata[:k, min(c, indata.shape[1] - 1)]
            estado['pos_in'] += frames

        def tocar(outdata, frames):
            p = estado['pos_out']
            k = max(0, min(frames, n_total - p))
            outdata[:k] = saida[p:p + k]
            outdata[k:] = 0
            estado['pos_out'] += frames
            if p >= n_total + sr // 4:
                fim.set()

        def cb_duplex(indata, outdata, frames, tempo, status):
            if status:
                estado['underflow'] += 1
            gravar(indata, frames)
            tocar(outdata, frames)
            if cancelar is not None and cancelar.is_set():
                fim.set()

        def cb_in(indata, frames, tempo, status):
            if estado['t_adc0'] is None:
                # relogio do PortAudio e, de reserva, o do sistema (so compara igual com igual)
                estado['t_adc0'] = (float(getattr(tempo, 'inputBufferAdcTime', 0.0) or 0.0),
                                    time.perf_counter())
            gravar(indata, frames)

        def cb_out(outdata, frames, tempo, status):
            if estado['t_dac0'] is None:
                estado['t_dac0'] = (float(getattr(tempo, 'outputBufferDacTime', 0.0) or 0.0),
                                    time.perf_counter())
            tocar(outdata, frames)
            if cancelar is not None and cancelar.is_set():
                fim.set()

        streams = []
        try:
            duplex = None
            try:
                # duplex sempre que o PortAudio aceitar (mesmo host API): sincronia exata
                duplex = sd.Stream(device=(cfg.entrada_id, cfg.saida_id), samplerate=sr, blocksize=bloco,
                                   channels=(n_in, 2), dtype='float32', latency='low', callback=cb_duplex)
            except Exception:
                if cfg.entrada_id == cfg.saida_id:
                    raise
            if duplex is not None:
                streams = [duplex]
            else:
                si = sd.InputStream(device=cfg.entrada_id, samplerate=sr, blocksize=bloco, channels=n_in,
                                    dtype='float32', latency='low', callback=cb_in)
                so = sd.OutputStream(device=cfg.saida_id, samplerate=sr, blocksize=bloco, channels=2,
                                     dtype='float32', latency='low', callback=cb_out)
                streams = [si, so]
            for s in streams:
                s.start()
            inicio = time.time()
            limite = n_total / sr + 5.0
            while not fim.wait(0.05):
                if progresso:
                    progresso(min(1.0, estado['pos_out'] / max(1, n_total)))
                if time.time() - inicio > limite:
                    break
        except Exception as erro:
            raise RuntimeError(disp._mensagem_erro(erro, cfg))
        finally:
            for s in streams:
                try:
                    s.stop()
                    s.close()
                except Exception:
                    pass
        deslocamento = 0
        if len(streams) == 2 and estado['t_adc0'] is not None and estado['t_dac0'] is not None:
            # amostra da entrada que foi capturada quando o 1o bloco da saida saiu no alto-falante
            (adc_pa, adc_sis), (dac_pa, dac_sis) = estado['t_adc0'], estado['t_dac0']
            if adc_pa > 0 and dac_pa > 0:
                deslocamento = int(round((dac_pa - adc_pa) * sr))
            else:
                # sem tempo do PortAudio: hora do callback +- latencias informadas pelo stream
                try:
                    lat_in = float(streams[0].latency)
                    lat_out = float(streams[1].latency)
                except Exception:
                    lat_in = lat_out = 0.0
                deslocamento = int(round(((dac_sis + lat_out) - (adc_sis - lat_in)) * sr))
        return gravado[:estado['pos_in']], deslocamento


class BackendSimulado:
    """
        Placa de som de mentira para os testes: a entrada recebe o 'musico'
        (funcao que recebe o playback e devolve o que ele tocaria) atrasado
        pela latencia, mais ruido; opcionalmente vaza o playback na entrada.
    """

    def __init__(self, latencia_ms=0.0, musico=None, vazamento=0.0, ruido_db=-80.0, deslocamento=0):
        self.latencia_ms = latencia_ms
        self.musico = musico
        self.vazamento = vazamento
        self.ruido_db = ruido_db
        self.deslocamento = deslocamento

    def executar(self, saida, cfg, canais, progresso=None, cancelar=None):
        sr = int(cfg.taxa)
        n = saida.shape[0]
        atraso = int(round(self.latencia_ms / 1000.0 * sr))
        tocado = self.musico(saida, sr) if self.musico else np.zeros(n)
        tocado = np.asarray(tocado, dtype=np.float64)
        if tocado.ndim == 1:
            tocado = np.stack([tocado] * len(canais), axis=1)
        gravado = np.zeros((n + sr, len(canais)))
        m = min(tocado.shape[0], gravado.shape[0] - atraso - self.deslocamento)
        ini = atraso + self.deslocamento
        gravado[ini:ini + m] += tocado[:m, :len(canais)]
        if self.vazamento:
            gravado[ini:ini + n, 0] += self.vazamento * saida[:, 0]
        rng = np.random.default_rng(1)
        gravado += rng.standard_normal(gravado.shape) * 10 ** (self.ruido_db / 20)
        if progresso:
            progresso(1.0)
        return gravado.astype(np.float32), self.deslocamento


# ===========================================================================
# GRAVACAO
# ===========================================================================

def tocar_e_gravar(ref, cfg, bpm=None, compassos_contagem=1, batidas_compasso=4, metronomo=False,
                   repeticoes=1, volume_musica=1.0, backend=None, progresso=None, cancelar=None):
    """
        Como funciona: monta o playback, toca e grava pelo backend, tira o
        deslocamento entre os streams e a latencia de ida e volta e recorta
        a gravacao para comecar no primeiro compasso da musica.
        Devolve um dict (take) com:
            'audio'    float32 (N, canais) alinhado com a referencia repetida
            'sr', 'canais' (indices no dispositivo), 'referencia' (o trecho
            repetido que tocou), 'problemas' (validacao) e metadados.
        Para que serve: Etapa 4.
    """
    sr = int(cfg.taxa)
    backend = backend or BackendSoundDevice()
    saida, i_musica, f_musica = montar_playback(ref, sr, bpm, compassos_contagem, batidas_compasso,
                                                metronomo, repeticoes, volume_musica)
    canais = cfg.canais_gravados()
    gravado, deslocamento = backend.executar(saida, cfg, canais, progresso, cancelar)
    if cancelar is not None and cancelar.is_set():
        return None
    atraso = int(round(cfg.latencia_ms / 1000.0 * sr)) + int(deslocamento)
    ini = max(0, i_musica + atraso)
    fim = min(gravado.shape[0], f_musica + atraso)
    audio = gravado[ini:fim].copy()
    musica = saida[i_musica:f_musica, 0].copy()
    take = {'audio': audio, 'sr': sr, 'canais': canais, 'referencia': musica,
            'latencia_ms': cfg.latencia_ms, 'deslocamento': int(deslocamento),
            'repeticoes': int(repeticoes), 'criado': time.time()}
    take['problemas'] = validar_take(take, saida[:, 0], gravado, i_musica, atraso)
    return take


def validar_take(take, playback=None, gravado_bruto=None, i_musica=0, atraso=0):
    """
        Silencio, clipping, duracao curta e musica vazando na entrada. Devolve
        lista de (nivel, texto): nivel 'erro' impede a analise, 'aviso' nao.
    """
    problemas = []
    x = np.asarray(take['audio'], dtype=np.float64)
    sr = take['sr']
    if x.ndim == 2:
        proc = x[:, 0]
    else:
        proc = x
    dur = proc.size / sr
    if dur < 2.0:
        problemas.append(('erro', f'A tomada ficou curta ({dur:.1f} s). Grave pelo menos alguns segundos.'))
    rms = float(np.sqrt(np.mean(proc ** 2))) if proc.size else 0.0
    pico = float(np.max(np.abs(proc))) if proc.size else 0.0
    if rms < 10 ** (-55 / 20):
        problemas.append(('erro', 'A gravação está em silêncio: confira o canal da pedaleira, o volume de '
                                  'saída dela e se você tocou durante a música.'))
    elif rms < 10 ** (-40 / 20):
        problemas.append(('aviso', 'Sinal muito baixo: aumente o volume de saída USB da pedaleira.'))
    clip = float(np.mean(np.abs(proc) >= 0.99)) if proc.size else 0.0
    if clip > 0.001:
        problemas.append(('aviso' if clip < 0.01 else 'erro',
                          f'A gravação saturou ({clip * 100:.1f}% das amostras no limite): abaixe o volume '
                          'de saída da pedaleira. Clipping muda o timbre e confunde a análise de ganho.'))
    vaz = vazamento_playback(proc, take.get('referencia'), sr)
    take['vazamento'] = vaz
    if vaz > 0.35:
        problemas.append(('aviso', 'A música parece estar entrando na gravação (a pedaleira devolve o som do '
                                   'computador na entrada USB?). Desligue o "loopback"/"USB monitor" da pedaleira '
                                   'ou escolha o canal que só tem a guitarra.'))
    if pico > 0 and rms > 0 and 20 * np.log10(pico / (rms + 1e-12)) < 3.0:
        problemas.append(('aviso', 'A gravação parece ser um tom constante ou ruído, não guitarra.'))
    return problemas


def vazamento_playback(gravado, referencia, sr):
    """Correlacao normalizada maxima (0..1) entre a gravacao e a musica, com atraso de ate 300 ms."""
    if referencia is None or gravado is None or len(gravado) < sr // 2:
        return 0.0
    from audio import analise_timbre as at
    a = at.reamostrar(np.asarray(gravado, dtype=np.float64), sr, 8000)
    b = at.reamostrar(np.asarray(referencia, dtype=np.float64), sr, 8000)
    n = min(a.size, b.size)
    a, b = a[:n] - a[:n].mean(), b[:n] - b[:n].mean()
    if np.std(a) < 1e-9 or np.std(b) < 1e-9:
        return 0.0
    tam = 1 << int(np.ceil(np.log2(2 * n)))
    c = np.fft.irfft(np.fft.rfft(a, tam) * np.conj(np.fft.rfft(b, tam)), tam)
    maximo = int(0.3 * 8000)
    janela = np.concatenate([c[:maximo], c[-maximo:]])
    return float(np.max(np.abs(janela)) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


class GravadorPlayAlong:
    """
        Como funciona: roda tocar_e_gravar numa thread; a interface le
        'progresso', 'estado' ('parado' | 'gravando' | 'pronto' | 'erro') e
        pega o take em 'resultado'. cancelar() interrompe.
        Para que serve: a Etapa 4 nao travar a tela.
    """

    def __init__(self):
        self.progresso = 0.0
        self.estado = 'parado'
        self.erro = ''
        self.resultado = None
        self._cancelar = threading.Event()
        self._thread = None

    def iniciar(self, ref, cfg, **opcoes):
        if self.estado == 'gravando':
            return False
        self._cancelar.clear()
        self.progresso = 0.0
        self.resultado = None
        self.erro = ''
        self.estado = 'gravando'

        def trabalho():
            try:
                take = tocar_e_gravar(ref, cfg, progresso=self._progresso, cancelar=self._cancelar, **opcoes)
                if take is None:
                    self.estado = 'parado'
                else:
                    self.resultado = take
                    self.estado = 'pronto'
            except Exception as erro:
                self.erro = str(erro)
                self.estado = 'erro'
        self._thread = threading.Thread(target=trabalho, daemon=True)
        self._thread.start()
        return True

    def _progresso(self, p):
        self.progresso = float(p)

    def cancelar(self):
        self._cancelar.set()

    def aguardar(self, limite=30.0):
        if self._thread is not None:
            self._thread.join(limite)


# ===========================================================================
# TAKES EM DISCO
# ===========================================================================

def pasta_takes(ref_id):
    pasta = os.path.join(disp.pasta_dados(), 'takes', str(ref_id or 'sem_referencia'))
    os.makedirs(pasta, exist_ok=True)
    return pasta


def salvar_take(take, ref_id, numero):
    """Grava o WAV (todos os canais) e um JSON com os metadados."""
    from audio import analise_timbre as at
    pasta = pasta_takes(ref_id)
    base = os.path.join(pasta, f'take_{numero:02d}')
    at.salvar_wav(base + '.wav', take['audio'], take['sr'])
    meta = {k: v for k, v in take.items() if k not in ('audio', 'referencia')}
    meta['problemas'] = [list(p) for p in take.get('problemas', [])]
    with open(base + '.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1, default=float)
    take['arquivo'] = base + '.wav'
    return base + '.wav'


def listar_takes(ref_id):
    pasta = pasta_takes(ref_id)
    itens = []
    for nome in sorted(os.listdir(pasta)):
        if nome.endswith('.json'):
            try:
                with open(os.path.join(pasta, nome), encoding='utf-8') as f:
                    meta = json.load(f)
                meta['arquivo'] = os.path.join(pasta, nome[:-5] + '.wav')
                itens.append(meta)
            except (OSError, ValueError):
                continue
    return itens


# ===========================================================================
# REPRODUTOR (A/B e pre-escuta)
# ===========================================================================

class ReprodutorAB:
    """
        Como funciona: um OutputStream do sounddevice le do buffer atual a
        cada callback; trocar() muda o buffer SEM mudar a posicao (audicao
        A/B instantanea). Sem sounddevice, usa o mixer do pygame (canal 59),
        sem troca instantanea mas funcional.
        Para que serve: ouvir a referencia, os takes e o A/B do resultado.
    """

    CANAL_PYGAME = 59

    def __init__(self):
        self.buffers = {}
        self.atual = None
        self.pos = 0
        self.tocando = False
        self.loop = True
        self.sr = 48000
        self.stream = None
        self._lock = threading.Lock()
        self._inicio_pygame = 0.0

    def carregar(self, chave, audio, sr):
        x = np.asarray(audio, dtype=np.float32)
        if x.ndim == 1:
            x = np.stack([x, x], axis=1)
        elif x.shape[1] == 1:
            x = np.repeat(x, 2, axis=1)
        with self._lock:
            self.buffers[chave] = x[:, :2].copy()
            self.sr = int(sr)

    def tocar(self, chave, dispositivo=None, loop=True, desde=0.0):
        self.parar()
        if chave not in self.buffers:
            return False
        self.atual = chave
        self.loop = loop
        self.pos = int(desde * self.sr)
        ok, _ = disp.disponivel()
        if ok:
            try:
                self.stream = disp.sd.OutputStream(device=dispositivo, samplerate=self.sr, channels=2,
                                                   dtype='float32', callback=self._cb)
                self.stream.start()
                self.tocando = True
                return True
            except Exception:
                self.stream = None
        return self._tocar_pygame(desde)

    def _tocar_pygame(self, desde):
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(self.sr, -16, 2, 512)
            freq, _, canais = pygame.mixer.get_init()
            x = self.buffers[self.atual]
            if int(freq) != self.sr:
                from audio import analise_timbre as at
                x = np.stack([at.reamostrar(x[:, c], self.sr, int(freq)) for c in range(2)], axis=1)
            dados = np.ascontiguousarray((np.clip(x, -1, 1) * 32000).astype(np.int16))
            if canais == 1:
                dados = np.ascontiguousarray(dados.mean(axis=1).astype(np.int16))
            som = pygame.sndarray.make_sound(dados)
            if pygame.mixer.get_num_channels() <= self.CANAL_PYGAME:
                pygame.mixer.set_num_channels(self.CANAL_PYGAME + 1)
            pygame.mixer.Channel(self.CANAL_PYGAME).play(som, loops=-1 if self.loop else 0)
            self._inicio_pygame = time.time() - desde
            self.tocando = True
            return True
        except Exception:
            return False

    def _cb(self, outdata, frames, tempo, status):
        with self._lock:
            x = self.buffers.get(self.atual)
            if x is None:
                outdata[:] = 0
                return
            n = x.shape[0]
            i = 0
            while i < frames:
                if self.pos >= n:
                    if not self.loop:
                        outdata[i:] = 0
                        self.tocando = False
                        return
                    self.pos = 0
                k = min(frames - i, n - self.pos)
                outdata[i:i + k] = x[self.pos:self.pos + k]
                self.pos += k
                i += k

    def trocar(self, chave):
        """A/B: continua do mesmo ponto no outro audio."""
        if chave not in self.buffers:
            return
        if self.stream is None and self.tocando:
            pos = self.posicao_s()
            self.atual = chave
            self._tocar_pygame(pos % max(1e-3, self.duracao_s()))
            return
        with self._lock:
            self.atual = chave
            self.pos = min(self.pos, self.buffers[chave].shape[0] - 1)

    def posicao_s(self):
        if self.stream is None:
            return (time.time() - self._inicio_pygame) if self.tocando else 0.0
        return self.pos / float(self.sr)

    def duracao_s(self):
        x = self.buffers.get(self.atual)
        return 0.0 if x is None else x.shape[0] / float(self.sr)

    def parar(self):
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
        self.stream = None
        try:
            import pygame
            if pygame.mixer.get_init() and pygame.mixer.get_num_channels() > self.CANAL_PYGAME:
                pygame.mixer.Channel(self.CANAL_PYGAME).stop()
        except Exception:
            pass
        self.tocando = False
