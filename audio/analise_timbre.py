# -*- coding: utf-8 -*-
"""
Analisador IA: pre-processamento, alinhamento e "perfil de timbre".

Tudo aqui e numpy + scipy, sem pygame e sem rede: da para rodar nos testes,
numa thread da interface ou num script solto. O librosa e o soundfile so sao
usados (se existirem) para LER formatos de audio que o scipy nao le.

Fluxo
    ler_audio -> preprocessar (mono, 32 kHz, sem DC) -> normalizar_loudness
    (LUFS, BS.1770) -> alinhar (tempo do playback + latencia, refinado por
    correlacao cruzada do envelope de ataques) -> AnaliseSinal (STFT, energia,
    regioes com nota/decaimento/silencio, altura por YIN) -> perfil_timbre.

O perfil de timbre e um dict com as MESMAS medidas para qualquer sinal:
    'medidas': {chave: {'valor', 'unidade', 'confianca', 'familia', 'nome'}}
    'curvas' : listas para os graficos (espectro medio, envelope, decaimento)
As medidas sao comparadas em audio/sugestoes_timbre.py; os efeitos sao
reconhecidos em audio/detectores_efeitos.py a partir da AnaliseSinal.

Os limiares e as bandas ficam em audio/config_analise/<instrumento>.json.
"""
import json
import os
from functools import lru_cache

import numpy as np
from scipy import signal

SR_ANALISE = 32000          # taxa comum da analise (Nyquist 16 kHz: sobra para guitarra)
N_FFT = 2048                # 64 ms
HOP = 512                   # 16 ms
PASTA_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config_analise')
INSTRUMENTOS = ('guitarra', 'violao', 'baixo')
EPS = 1e-12


# ===========================================================================
# CONFIGURACAO POR INSTRUMENTO
# ===========================================================================

def _mesclar(base, extra):
    saida = dict(base)
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(saida.get(k), dict):
            saida[k] = _mesclar(saida[k], v)
        else:
            saida[k] = v
    return saida


@lru_cache(maxsize=8)
def _ler_config_json(nome):
    with open(os.path.join(PASTA_CONFIG, f'{nome}.json'), encoding='utf-8') as f:
        return json.load(f)


def listar_instrumentos():
    """[(id, nome)] dos instrumentos com arquivo de configuracao."""
    itens = []
    for nome in sorted(os.listdir(PASTA_CONFIG)):
        if nome.endswith('.json') and not nome.startswith('_'):
            chave = nome[:-5]
            try:
                itens.append((chave, _ler_config_json(chave).get('nome', chave)))
            except (OSError, ValueError):
                continue
    ordem = {k: i for i, k in enumerate(INSTRUMENTOS)}
    return sorted(itens, key=lambda it: ordem.get(it[0], 99))


def carregar_config(instrumento='guitarra'):
    """
        Como funciona: le audio/config_analise/_padrao.json e sobrepoe o
        arquivo do instrumento (so o que muda precisa estar nele).
        Para que serve: bandas, faixas de altura e limiares dos detectores
        num lugar so, nunca espalhados no codigo.
        Onde e usada: perfil_timbre, detectores, sugestoes e a interface.
    """
    base = _ler_config_json('_padrao')
    try:
        extra = _ler_config_json(instrumento)
    except OSError:
        extra = {}
    cfg = _mesclar(base, extra)
    cfg['instrumento'] = instrumento if extra else 'guitarra'
    return cfg


# ===========================================================================
# LEITURA E PRE-PROCESSAMENTO
# ===========================================================================

def ler_audio(caminho):
    """
        Como funciona: tenta soundfile (WAV/FLAC/OGG/MP3), depois librosa e
        por fim o leitor de WAV do scipy.
        Devolve (float64 (N,) ou (N, canais), sr). Levanta ValueError com uma
        mensagem amigavel se nada conseguir ler.
    """
    erros = []
    try:
        import soundfile as sf
        dados, sr = sf.read(caminho, dtype='float64', always_2d=False)
        return np.asarray(dados, dtype=np.float64), int(sr)
    except Exception as erro:              # formato nao suportado, lib ausente...
        erros.append(f'soundfile: {erro}')
    try:
        import librosa
        dados, sr = librosa.load(caminho, sr=None, mono=False)
        dados = np.asarray(dados, dtype=np.float64)
        if dados.ndim == 2:
            dados = dados.T
        return dados, int(sr)
    except Exception as erro:
        erros.append(f'librosa: {erro}')
    try:
        from scipy.io import wavfile
        sr, dados = wavfile.read(caminho)
        dados = np.asarray(dados)
        if dados.dtype.kind == 'i':
            dados = dados / float(np.iinfo(dados.dtype).max)
        elif dados.dtype.kind == 'u':
            dados = (dados - 128.0) / 128.0
        return dados.astype(np.float64), int(sr)
    except Exception as erro:
        erros.append(f'wav: {erro}')
    raise ValueError('Não consegui ler o arquivo de áudio. Formatos aceitos: WAV, FLAC, OGG '
                     'e MP3 (MP3/M4A podem precisar do ffmpeg). Detalhes: ' + ' | '.join(erros))


def salvar_wav(caminho, x, sr):
    """Grava float (-1..1) mono ou (N, c) em WAV 16 bits."""
    from scipy.io import wavfile
    pasta = os.path.dirname(caminho)
    if pasta:
        os.makedirs(pasta, exist_ok=True)
    dados = np.clip(np.asarray(x, dtype=np.float64) * 32767, -32768, 32767).astype(np.int16)
    wavfile.write(caminho, int(sr), dados)


def para_mono(x, canal=None):
    """Mono: media dos canais ou so o canal pedido."""
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        return x
    if canal is not None and 0 <= canal < x.shape[1]:
        return x[:, canal].copy()
    return x.mean(axis=1)


def reamostrar(x, sr, sr_alvo=SR_ANALISE):
    """Troca a taxa com filtro polifasico (sem pular amostras)."""
    if int(sr) == int(sr_alvo) or x.size == 0:
        return np.asarray(x, dtype=np.float64)
    from math import gcd
    g = gcd(int(sr), int(sr_alvo))
    return signal.resample_poly(x, int(sr_alvo) // g, int(sr) // g, axis=0)


def remover_dc(x, sr):
    """Passa-altas de 20 Hz (tira DC e ronco subsonico)."""
    if x.size < 16:
        return x
    sos = signal.butter(2, 20.0 / (sr / 2), 'high', output='sos')
    return signal.sosfiltfilt(sos, x) if x.size > 64 else x - np.mean(x)


def preprocessar(x, sr, canal=None, sr_alvo=SR_ANALISE):
    """Mono (ou um canal), taxa comum e sem DC."""
    return remover_dc(reamostrar(para_mono(x, canal), sr, sr_alvo), sr_alvo)


# --------------------------------------------------------------- LUFS -----

def _filtro_k(sr):
    """Coeficientes do filtro K da ITU-R BS.1770 (prefiltro shelving + RLB)."""
    # estagio 1: high-shelf (+4 dB acima de ~1,5 kHz)
    f0, g, q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    k = np.tan(np.pi * f0 / sr)
    vh = 10 ** (g / 20.0)
    vb = vh ** 0.4996667741545416
    a0 = 1.0 + k / q + k * k
    b1 = [(vh + vb * k / q + k * k) / a0, 2.0 * (k * k - vh) / a0, (vh - vb * k / q + k * k) / a0]
    a1 = [1.0, 2.0 * (k * k - 1.0) / a0, (1.0 - k / q + k * k) / a0]
    # estagio 2: passa-altas RLB (~38 Hz)
    f0, q = 38.13547087602444, 0.5003270373238773
    k = np.tan(np.pi * f0 / sr)
    a0 = 1.0 + k / q + k * k
    b2 = [1.0, -2.0, 1.0]
    a2 = [1.0, 2.0 * (k * k - 1.0) / a0, (1.0 - k / q + k * k) / a0]
    return (b1, a1), (b2, a2)


def lufs(x, sr):
    """
        Como funciona: loudness integrada da BS.1770-4 (filtro K, blocos de
        400 ms com 75% de sobreposicao, portas absoluta -70 LUFS e relativa
        -10 LU). Mono.
        Para que serve: igualar o volume da referencia e da gravacao para que
        diferenca de volume nao seja confundida com ganho.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.size < int(0.4 * sr):
        rms = np.sqrt(np.mean(x ** 2) + EPS)
        return float(20 * np.log10(rms + EPS) - 0.691)
    (b1, a1), (b2, a2) = _filtro_k(sr)
    y = signal.lfilter(b2, a2, signal.lfilter(b1, a1, x))
    bloco, passo = int(0.4 * sr), int(0.1 * sr)
    quad = np.concatenate([[0.0], np.cumsum(y * y)])
    inicios = np.arange(0, y.size - bloco + 1, passo)
    energia = (quad[inicios + bloco] - quad[inicios]) / bloco
    nivel = -0.691 + 10 * np.log10(energia + EPS)
    validos = energia[nivel > -70]
    if validos.size == 0:
        return -70.0
    relativo = -0.691 + 10 * np.log10(np.mean(validos) + EPS) - 10
    validos = energia[(nivel > -70) & (nivel > relativo)]
    if validos.size == 0:
        return -70.0
    return float(-0.691 + 10 * np.log10(np.mean(validos) + EPS))


def normalizar_loudness(x, sr, alvo=-23.0):
    """Devolve (x com loudness = alvo, ganho aplicado em dB)."""
    atual = lufs(x, sr)
    if atual <= -69.9:
        return np.asarray(x, dtype=np.float64), 0.0
    ganho = alvo - atual
    return np.asarray(x, dtype=np.float64) * 10 ** (ganho / 20.0), float(ganho)


# ===========================================================================
# STFT, ATAQUES E ALINHAMENTO
# ===========================================================================

def enquadrar(x, janela, hop):
    """Matriz (quadros, janela) sem copia (as_strided), com zero no fim."""
    x = np.asarray(x, dtype=np.float64)
    if x.size < janela:
        x = np.pad(x, (0, janela - x.size))
    n = 1 + (x.size - janela) // hop
    return np.lib.stride_tricks.as_strided(x, shape=(n, janela),
                                           strides=(x.strides[0] * hop, x.strides[0]))


def stft_mag(x, n_fft=N_FFT, hop=HOP):
    """Magnitude |STFT| (bins, quadros) com janela de Hann centrada."""
    x = np.pad(np.asarray(x, dtype=np.float64), (n_fft // 2, n_fft // 2))
    quadros = enquadrar(x, n_fft, hop) * np.hanning(n_fft)
    return np.abs(np.fft.rfft(quadros, axis=1)).T


def fluxo_espectral(S, lag=2, limiar_db=6.0):
    """
        Envelope de ataques (ideia do SuperFlux): em cada faixa, quanto o
        nivel em dB passa do MAXIMO das faixas vizinhas 'lag' quadros antes.
        So conta subida maior que 'limiar_db': tremolo e swell (subidas
        lentas) e vibrato (harmonico que so escorrega para a faixa do lado)
        nao viram ataque; nota nova e palhetada sim.
    """
    from scipy.ndimage import maximum_filter1d
    L = 20 * np.log10(S + EPS)
    teto = np.max(L)
    L = np.maximum(L, teto - 80.0)
    ref = maximum_filter1d(L, size=9, axis=0)
    ref = np.concatenate([np.repeat(ref[:, :1], lag, axis=1), ref[:, :-lag]], axis=1)
    d = L - ref
    peso = np.clip((L - (teto - 70.0)) / 40.0, 0, 1)
    fluxo = (np.clip(d - limiar_db, 0, 30.0) * peso).sum(axis=0)
    return fluxo / (np.max(fluxo) + EPS)


def picos_ataque(fluxo, sr=SR_ANALISE, hop=HOP, sensibilidade=1.0, intervalo_min=0.07):
    """Instantes (s) dos ataques: picos do fluxo acima de uma media movel."""
    if fluxo.size < 3:
        return np.array([])
    janela = max(3, int(0.25 * sr / hop))
    media = np.convolve(fluxo, np.ones(janela) / janela, mode='same')
    limiar = media * 1.3 + 0.06 / max(sensibilidade, 1e-3)
    distancia = max(1, int(intervalo_min * sr / hop))
    picos, _ = signal.find_peaks(fluxo, height=limiar, distance=distancia)
    return picos * hop / sr


def alinhar(ref, rec, sr=SR_ANALISE, deslocamento_inicial=0.0, busca=0.4):
    """
        Como funciona: parte do deslocamento conhecido (tempo do playback +
        latencia) e refina com a correlacao cruzada normalizada dos envelopes
        de ataque dentro de +-busca segundos.
        Devolve (deslocamento_s, confianca 0..1): a gravacao esta atrasada
        'deslocamento_s' em relacao a referencia (positivo = rec atrasada).
        Para que serve: comparar o mesmo trecho nos dois sinais.
    """
    hop = 256
    fr = fluxo_espectral(stft_mag(ref, 1024, hop))
    fg = fluxo_espectral(stft_mag(rec, 1024, hop))
    d0 = int(round(deslocamento_inicial * sr / hop))
    maximo = int(round(busca * sr / hop))
    fr = fr - fr.mean()
    fg = fg - fg.mean()
    melhor, melhor_lag, valores = -2.0, d0, []
    for lag in range(d0 - maximo, d0 + maximo + 1):
        if lag >= 0:
            a, b = fr[:max(0, fg.size - lag)], fg[lag:]
        else:
            a, b = fr[-lag:], fg[:max(0, fr.size + lag)]
        n = min(a.size, b.size)
        if n < 20:
            valores.append(0.0)
            continue
        a, b = a[:n], b[:n]
        c = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + EPS))
        valores.append(c)
        if c > melhor:
            melhor, melhor_lag = c, lag
    # refino sub-quadro por parabola
    i = melhor_lag - (d0 - maximo)
    fino = float(melhor_lag)
    if 0 < i < len(valores) - 1:
        y0, y1, y2 = valores[i - 1], valores[i], valores[i + 1]
        den = y0 - 2 * y1 + y2
        if abs(den) > 1e-9:
            fino += float(np.clip(0.5 * (y0 - y2) / den, -0.5, 0.5))
    valores = np.array(valores)
    contraste = melhor - float(np.median(valores)) if valores.size else 0.0
    confianca = float(np.clip(melhor, 0, 1) * np.clip(contraste / 0.3, 0, 1))
    return fino * hop / sr, confianca


def recortar_alinhado(ref, rec, deslocamento, sr=SR_ANALISE):
    """Mesmo trecho nos dois sinais, dado o atraso da gravacao."""
    d = int(round(deslocamento * sr))
    if d >= 0:
        rec = rec[d:]
    else:
        ref = ref[-d:]
    n = min(ref.size, rec.size)
    return ref[:n], rec[:n]


# ===========================================================================
# ALTURA (YIN vetorizado)
# ===========================================================================

def yin(x, sr, fmin=60.0, fmax=1400.0, hop_s=0.005, janela_s=0.064, limiar=0.15):
    """
        Como funciona: YIN (de Cheveigne & Kawahara) em todos os quadros de
        uma vez, com a funcao diferenca calculada via FFT. Roda a 16 kHz.
        Devolve (tempos s, f0 Hz (0 = sem altura), aperiodicidade 0..1).
        Para que serve: vibrato, oitavas, harmonicidade (ring mod) e para
        separar trechos com uma nota so.
    """
    sr_y = 16000
    xy = reamostrar(x, sr, sr_y)
    W = int(janela_s * sr_y)
    hop = max(1, int(hop_s * sr_y))
    tau_min = max(2, int(sr_y / fmax))
    tau_max = min(W // 2, int(sr_y / fmin) + 1)
    quadros = enquadrar(np.pad(xy, (W // 2, W // 2)), W, hop)
    n_q = quadros.shape[0]
    f0 = np.zeros(n_q)
    aper = np.ones(n_q)
    nfft = 1 << int(np.ceil(np.log2(2 * W)))
    for a in range(0, n_q, 400):
        bloco = quadros[a:a + 400]
        F = np.fft.rfft(bloco, nfft, axis=1)
        r = np.fft.irfft(F * np.conj(F), nfft, axis=1)[:, :tau_max + 2]
        quad = np.cumsum(bloco * bloco, axis=1)
        taus = np.arange(tau_max + 2)
        total = quad[:, -1][:, None]
        e0 = np.where(taus[None, :] > 0,
                      quad[:, np.clip(W - 1 - taus, 0, W - 1)], total)
        e0[:, 0] = total[:, 0]
        et = total - np.where(taus[None, :] > 0, quad[:, np.clip(taus - 1, 0, W - 1)], 0.0)
        d = np.maximum(e0 + et - 2 * r, 0.0)
        d[:, 0] = 0.0
        acum = np.cumsum(d[:, 1:], axis=1)
        cmnd = np.ones_like(d)
        cmnd[:, 1:] = d[:, 1:] * taus[None, 1:] / (acum + EPS)
        faixa = cmnd[:, tau_min:tau_max + 1]
        abaixo = faixa < limiar
        tem = abaixo.any(axis=1)
        primeiro = np.argmax(abaixo, axis=1)
        # a partir do primeiro que cruza o limiar, desce ate o minimo local
        sobe = np.zeros_like(abaixo)
        sobe[:, :-1] = faixa[:, 1:] > faixa[:, :-1]
        idx_cols = np.arange(faixa.shape[1])[None, :]
        cand = sobe & (idx_cols >= primeiro[:, None])
        local = np.where(cand.any(axis=1), np.argmax(cand, axis=1), primeiro)
        glob = np.argmin(faixa, axis=1)
        escolha = np.where(tem, local, glob)
        linhas = np.arange(faixa.shape[0])
        valor = faixa[linhas, escolha]
        # interpolacao parabolica
        esq = faixa[linhas, np.clip(escolha - 1, 0, faixa.shape[1] - 1)]
        dir_ = faixa[linhas, np.clip(escolha + 1, 0, faixa.shape[1] - 1)]
        den = esq - 2 * valor + dir_
        desl = np.where(np.abs(den) > 1e-12, 0.5 * (esq - dir_) / (den + EPS), 0.0)
        desl = np.clip(desl, -0.5, 0.5)
        tau = escolha + tau_min + desl
        energia = total[:, 0] / W
        ok = (energia > 1e-9) & (tau > 0)
        f0[a:a + bloco.shape[0]] = np.where(ok, sr_y / np.maximum(tau, 1e-6), 0.0)
        aper[a:a + bloco.shape[0]] = np.where(ok, np.clip(valor, 0, 1), 1.0)
    tempos = np.arange(n_q) * hop / sr_y
    return tempos, f0, aper


# ===========================================================================
# ANALISE DE UM SINAL (intermediarios compartilhados)
# ===========================================================================

def bandas_terco_oitava(fmin=31.5, fmax=12500.0):
    """Centros e bordas das bandas de 1/3 de oitava (base 1 kHz)."""
    n = np.arange(-15, 14)
    centros = 1000.0 * 2 ** (n / 3.0)
    centros = centros[(centros >= fmin * 0.99) & (centros <= fmax * 1.01)]
    return centros, centros * 2 ** (-1 / 6), centros * 2 ** (1 / 6)


class AnaliseSinal:
    """
        Como funciona: guarda o sinal (mono, 32 kHz, loudness normalizada) e
        calcula sob demanda os intermediarios caros (STFT, energia por quadro,
        regioes, ataques, YIN, bandas), cada um uma vez so.
        Para que serve: o perfil de timbre e os detectores de efeito usam os
        mesmos calculos sem repetir trabalho.
        Onde e usada: perfil_timbre, detectores_efeitos, testes.
    """

    def __init__(self, x, sr=SR_ANALISE, cfg=None, ja_preparado=False, normalizar=True):
        self.cfg = cfg or carregar_config('guitarra')
        if not ja_preparado:
            x = preprocessar(x, sr)
            sr = SR_ANALISE
        self.sr = sr
        self.lufs_original = lufs(x, sr)
        if normalizar:
            x, self.ganho_norm_db = normalizar_loudness(x, sr, self.cfg['analise']['alvo_lufs'])
        else:
            self.ganho_norm_db = 0.0
        self.x = np.asarray(x, dtype=np.float64)
        self.duracao = self.x.size / sr
        self._cache = {}

    # ----------------------------------------------------------- basicos --
    def _memo(self, chave, funcao):
        if chave not in self._cache:
            self._cache[chave] = funcao()
        return self._cache[chave]

    @property
    def S(self):
        return self._memo('S', lambda: stft_mag(self.x))

    @property
    def freqs(self):
        return np.fft.rfftfreq(N_FFT, 1.0 / self.sr)

    @property
    def tempos(self):
        return np.arange(self.S.shape[1]) * HOP / self.sr

    @property
    def energia_db(self):
        """Nivel de cada quadro em dB (relativo a escala cheia do sinal normalizado)."""
        def calc():
            quadros = enquadrar(np.pad(self.x, (N_FFT // 2, N_FFT // 2)), N_FFT, HOP)
            n = min(quadros.shape[0], self.S.shape[1])
            rms = np.sqrt(np.mean(quadros[:n] ** 2, axis=1) + EPS)
            return 20 * np.log10(rms + EPS)
        return self._memo('energia_db', calc)

    @property
    def regioes(self):
        """
            Mascaras por quadro: 'ativo' (nota soando), 'silencio' (abaixo do
            piso + margem) e 'decaimento' (depois do pico de uma nota, sem novo
            ataque perto). Mais piso de ruido e nivel de pico em dB.
        """
        def calc():
            e = self.energia_db
            limiar_ativo, pico, piso = self.regioes_basicas()
            ativo = e > limiar_ativo
            silencio = e < min(piso + 6.0, pico - 50.0)
            # decaimento: quadros que estao a mais de 60 ms do ultimo ataque e
            # abaixo do nivel do ataque, antes do proximo ataque
            ataques = self.ataques
            idx_at = np.round(ataques * self.sr / HOP).astype(int)
            decai = np.zeros_like(ativo)
            proximos = np.append(idx_at[1:], e.size)
            for i0, i1 in zip(idx_at, proximos):
                a0 = i0 + int(0.06 * self.sr / HOP)
                decai[min(a0, e.size):min(i1 - 1, e.size)] = True
            return {'ativo': ativo, 'silencio': silencio, 'decaimento': decai & ~silencio,
                    'piso_db': piso, 'pico_db': pico}
        return self._memo('regioes', calc)

    @property
    def fluxo(self):
        return self._memo('fluxo', lambda: fluxo_espectral(self.S))

    @property
    def ataques(self):
        def calc():
            at_s = picos_ataque(self.fluxo, self.sr, HOP)
            # o trecho ja comeca com nota soando: conta o comeco como ataque
            e = self.energia_db
            if e.size > 4 and np.max(e[:4]) > self.regioes_basicas()[0] and \
                    (at_s.size == 0 or at_s[0] > 0.1):
                at_s = np.concatenate([[0.0], at_s])
            return at_s
        return self._memo('ataques', calc)

    def regioes_basicas(self):
        """(limiar de nota soando, pico, piso) em dB, sem depender dos ataques."""
        e = self.energia_db
        pico = float(np.percentile(e, 99)) if e.size else -90.0
        piso = float(np.percentile(e, 3)) if e.size else -90.0
        a = self.cfg['analise']
        limiar = pico - a['faixa_ativa_db']
        if piso + a['margem_piso_db'] < pico - 20.0:
            limiar = max(limiar, piso + a['margem_piso_db'])
        return limiar, pico, piso

    @property
    def altura(self):
        """(tempos, f0, aperiodicidade) do YIN na faixa do instrumento."""
        def calc():
            fmin, fmax = self.cfg['faixa_f0']
            return yin(self.x, self.sr, fmin=fmin, fmax=fmax)
        return self._memo('altura', calc)

    @property
    def bandas(self):
        """(centros, energia por banda de 1/3 oitava x quadro) em potencia."""
        def calc():
            fmin, fmax = self.cfg['faixa_espectro']
            centros, lo, hi = bandas_terco_oitava(fmin, min(fmax, self.sr * 0.45))
            P = self.S ** 2
            f = self.freqs
            E = np.zeros((centros.size, P.shape[1]))
            for i, (a, b) in enumerate(zip(lo, hi)):
                sel = (f >= a) & (f < b)
                if not sel.any():
                    sel = np.zeros_like(f, dtype=bool)
                    sel[np.argmin(np.abs(f - centros[i]))] = True
                E[i] = P[sel].sum(axis=0)
            return centros, E
        return self._memo('bandas', calc)

    def envelope_db(self, passo_s=0.005, janela_s=0.010):
        """Envelope RMS fino (para tremolo, ataque e decaimento)."""
        chave = ('env', passo_s, janela_s)
        def calc():
            passo = max(1, int(passo_s * self.sr))
            janela = max(passo, int(janela_s * self.sr))
            q = enquadrar(np.pad(self.x, (janela // 2, janela // 2)), janela, passo)
            rms = np.sqrt(np.mean(q ** 2, axis=1) + EPS)
            return np.arange(q.shape[0]) * passo / self.sr, 20 * np.log10(rms + EPS)
        return self._memo(chave, calc)


# ===========================================================================
# FAMILIAS DE MEDIDAS
# ===========================================================================

def _medida(valor, unidade, confianca, familia, nome):
    return {'valor': None if valor is None else float(valor), 'unidade': unidade,
            'confianca': float(np.clip(confianca, 0, 1)), 'familia': familia, 'nome': nome}


def espectro_medio(an):
    """LTAS: potencia media dos quadros com nota, por banda de 1/3 oitava (dB relativos)."""
    centros, E = an.bandas
    ativo = an.regioes['ativo']
    if not ativo.any():
        ativo = np.ones(E.shape[1], dtype=bool)
    media = E[:, ativo[:E.shape[1]]].mean(axis=1)
    total = media.sum() + EPS
    return centros, 10 * np.log10(media / total + EPS)


def _suavizar_oitava(centros, db, fracao=1.0):
    """Media movel em log-frequencia (largura em oitavas)."""
    lf = np.log2(centros)
    saida = np.empty_like(db)
    for i, c in enumerate(lf):
        sel = np.abs(lf - c) <= fracao / 2
        saida[i] = 10 * np.log10(np.mean(10 ** (db[sel] / 10)) + EPS)
    return saida


def medidas_eq(an, medidas, curvas):
    cfg = an.cfg
    centros, ltas = espectro_medio(an)
    curvas['bandas_hz'] = centros.tolist()
    curvas['ltas_db'] = ltas.tolist()
    pot = 10 ** (ltas / 10)
    for chave, (a, b) in cfg['bandas_macro'].items():
        sel = (centros >= a) & (centros < b)
        v = 10 * np.log10(pot[sel].sum() + EPS) if sel.any() else None
        medidas[f'eq_{chave}'] = _medida(v, 'dB', 0.9 if sel.any() else 0.0, 'eq',
                                         cfg['nomes_bandas'].get(chave, chave))
    # centroide, rolloff e inclinacao com o espectro completo (quadros com nota)
    S = an.S
    ativo = an.regioes['ativo'][:S.shape[1]]
    P = (S[:, ativo] ** 2) if ativo.any() else S ** 2
    f = an.freqs
    lo, hi = cfg['faixa_espectro']
    banda = (f >= lo) & (f <= hi)
    ps = P[banda].mean(axis=1)
    fb = f[banda]
    centroide = float(np.sum(fb * ps) / (np.sum(ps) + EPS))
    acum = np.cumsum(ps) / (np.sum(ps) + EPS)
    rolloff = float(fb[min(np.searchsorted(acum, 0.85), fb.size - 1)])
    sel = (centros >= 100) & (centros <= 8000)
    inclinacao = float(np.polyfit(np.log2(centros[sel]), ltas[sel], 1)[0]) if sel.sum() > 2 else 0.0
    medidas['centroide'] = _medida(centroide, 'Hz', 0.9, 'eq', 'Centróide espectral (brilho)')
    medidas['rolloff'] = _medida(rolloff, 'Hz', 0.8, 'eq', 'Rolloff 85%')
    medidas['inclinacao'] = _medida(inclinacao, 'dB/oitava', 0.8, 'eq', 'Inclinação espectral')
    # ressonancia fixa (wah parado, filtro): pico estreito do espectro medio
    fino = _suavizar_oitava(centros, ltas, 1 / 3.0)
    largo = _suavizar_oitava(centros, ltas, 1.5)
    faixa = (centros >= 300) & (centros <= 3000)
    resson = float(np.max((fino - largo)[faixa])) if faixa.any() else 0.0
    f_res = float(centros[faixa][np.argmax((fino - largo)[faixa])]) if faixa.any() else 0.0
    medidas['ressonancia_db'] = _medida(resson, 'dB', 0.6, 'eq', 'Pico ressonante no espectro médio')
    medidas['ressonancia_hz'] = _medida(f_res, 'Hz', 0.5, 'eq', 'Frequência do pico ressonante')


def _janelas_ativas(an, janela_s=0.05, perto_de_ataque=None):
    """
        Janelas de 50 ms com nota soando. Com perto_de_ataque (s), so as que
        comecam ate esse tempo depois de um ataque: e ali que o som limpo tem
        pico (a palhetada) e o saturado ja chega achatado. No corpo de uma
        nota longa, mesmo o som limpo vira quase um seno e engana a crista.
    """
    n = int(janela_s * an.sr)
    passo = n // 2
    q = enquadrar(an.x, n, passo)
    inicio = np.arange(q.shape[0]) * passo / an.sr
    centro = inicio + janela_s / 2
    idx = np.clip((centro * an.sr / HOP).astype(int), 0, an.regioes['ativo'].size - 1)
    sel = an.regioes['ativo'][idx]
    rms = np.sqrt(np.mean(q ** 2, axis=1) + EPS)
    sel &= rms > 10 ** ((an.regioes['pico_db'] - 30) / 20)
    if perto_de_ataque is not None and an.ataques.size:
        d = inicio[:, None] - an.ataques[None, :]
        perto = np.any((d >= -0.01) & (d <= perto_de_ataque), axis=1)
        if (sel & perto).sum() >= 4:
            sel &= perto
    return q[sel] if sel.any() else q


def medidas_ganho(an, medidas):
    """Fator de crista, planura, curtose, assimetria, harmonicos e clipping."""
    q = _janelas_ativas(an, perto_de_ataque=0.1)
    rms = np.sqrt(np.mean(q ** 2, axis=1) + EPS)
    pico = np.max(np.abs(q), axis=1) + EPS
    crista = float(np.median(20 * np.log10(pico / rms)))
    z = (q - q.mean(axis=1, keepdims=True)) / rms[:, None]
    curtose = float(np.median(np.mean(z ** 4, axis=1)))
    assimetria = float(np.median(np.abs(np.mean(z ** 3, axis=1))))
    # clipping: fracao das amostras coladas no pico da janela (topo achatado)
    colado = float(np.median(np.mean(np.abs(q) > 0.93 * pico[:, None], axis=1)))
    # planura espectral e riqueza harmonica (quadros com nota)
    S = an.S
    ativo = an.regioes['ativo'][:S.shape[1]]
    P = S[:, ativo] ** 2 if ativo.any() else S ** 2
    f = an.freqs
    banda = (f >= 100) & (f <= 8000)
    Pb = P[banda] + EPS
    planura = float(np.median(10 * np.log10(np.exp(np.mean(np.log(Pb), axis=0))
                                            / np.mean(Pb, axis=0))))
    # densidade de parciais: fracao da energia acima de 1,5 kHz fora dos picos
    medidas['crista_db'] = _medida(crista, 'dB', 0.8, 'ganho', 'Fator de crista nas palhetadas')
    medidas['planura'] = _medida(planura, 'dB', 0.7, 'ganho', 'Planura espectral')
    medidas['curtose'] = _medida(curtose, '', 0.6, 'ganho', 'Curtose da forma de onda')
    medidas['assimetria'] = _medida(assimetria, '', 0.5, 'ganho', 'Assimetria da forma de onda')
    medidas['clipping'] = _medida(colado, 'fração', 0.5, 'ganho', 'Topo achatado (clipping)')
    h = harmonicos(an)
    medidas['harm_agudos'] = _medida(h['riqueza'], 'dB', h['confianca'], 'ganho',
                                     'Riqueza harmônica (harmônicos 4-10 / 1-3)')
    medidas['pares_impares'] = _medida(h['pares_impares'], 'dB', h['confianca'], 'ganho',
                                       'Harmônicos pares / ímpares')
    # indice de ganho 0..1: combinacao calibrada no config
    k = an.cfg['ganho']
    partes = [
        np.clip((k['crista_limpa'] - crista) / (k['crista_limpa'] - k['crista_saturada']), 0, 1),
        np.clip((planura - k['planura_limpa']) / (k['planura_saturada'] - k['planura_limpa']), 0, 1),
        np.clip((k['curtose_limpa'] - curtose) / (k['curtose_limpa'] - k['curtose_saturada']), 0, 1),
        np.clip((h['riqueza'] - k['riqueza_limpa']) / (k['riqueza_saturada'] - k['riqueza_limpa']), 0, 1)
        if h['confianca'] > 0.2 else None,
    ]
    pesos = k['pesos']
    num = sum(p * w for p, w in zip(partes, pesos) if p is not None)
    den = sum(w for p, w in zip(partes, pesos) if p is not None)
    indice = float(num / den) if den else 0.0
    medidas['indice_ganho'] = _medida(indice, '0-1', 0.7, 'ganho', 'Índice de ganho estimado')


def harmonicos(an):
    """
        Amplitudes dos harmonicos 1..10 nos quadros com uma nota clara (YIN),
        mais medidas de sub-oitava (octaver) e de inarmonicidade (ring mod).
    """
    def calc():
        t_y, f0, aper = an.altura
        S = an.S
        f = an.freqs
        passo_bin = f[1]
        idx_q = np.clip(np.round(t_y * an.sr / HOP).astype(int), 0, S.shape[1] - 1)
        ativo = an.regioes['ativo'][:S.shape[1]]
        lim = an.cfg['analise']['limiar_aperiodicidade']
        sel = (f0 > 0) & (aper < lim) & ativo[idx_q]
        resultado = {'riqueza': 0.0, 'pares_impares': 0.0, 'sub_oitava': -30.0,
                     'impar_agudo': 0.0, 'confianca': 0.0, 'fracao_vozeada': 0.0,
                     'n_quadros': 0}
        ativos_y = ativo[idx_q]
        resultado['fracao_vozeada'] = float(sel.sum() / max(1, ativos_y.sum()))
        if sel.sum() < 8:
            return resultado
        # um quadro de STFT por quadro de YIN escolhido (sem repetir)
        quadros = {}
        for qi, f00 in zip(idx_q[sel], f0[sel]):
            quadros.setdefault(qi, []).append(f00)
        amps, subs, imp_ag, par_ag = [], [], [], []

        def amp(col, freq):
            if freq >= f[-1] - 2 * passo_bin:
                return 0.0
            b = int(round(freq / passo_bin))
            return float(np.max(col[max(0, b - 1):b + 2]))

        for qi, lista in quadros.items():
            ff = float(np.median(lista))
            col = S[:, qi]
            a = np.array([amp(col, k * ff) for k in range(1, 11)])
            if a[0] + a[1] < EPS:
                continue
            amps.append(a)
            sub = amp(col, ff / 2) + amp(col, 1.5 * ff)
            subs.append(sub / (a[0] + a[1] + EPS))
            ks = np.arange(1, 41)
            fk = ks * ff
            ok = (fk > 1200) & (fk < 6000)
            if ok.sum() >= 4:
                vals = np.array([amp(col, x) for x in fk[ok]])
                impar = vals[(ks[ok] % 2) == 1]
                par = vals[(ks[ok] % 2) == 0]
                if impar.size and par.size:
                    imp_ag.append(np.mean(impar ** 2))
                    par_ag.append(np.mean(par ** 2))
        if not amps:
            return resultado
        A = np.array(amps) ** 2
        m = A.mean(axis=0) + EPS
        resultado['riqueza'] = float(10 * np.log10(m[3:].sum() / m[:3].sum()))
        pares = m[1::2].sum()
        impares = m[2::2].sum()           # impares sem a fundamental
        resultado['pares_impares'] = float(10 * np.log10(pares / (impares + EPS)))
        resultado['sub_oitava'] = float(20 * np.log10(np.median(subs) + EPS))
        if imp_ag:
            resultado['impar_agudo'] = float(10 * np.log10((np.median(imp_ag) + EPS)
                                                           / (np.median(par_ag) + EPS)))
        resultado['n_quadros'] = len(amps)
        resultado['confianca'] = float(np.clip(len(amps) / 40.0, 0, 1) * 0.8)
        return resultado
    return an._memo('harmonicos', calc)


def _inclinacoes_decaimento(an):
    """Taxa de queda (dB/s) de cada nota entre 60 e 400 ms depois do ataque."""
    t, e = an.envelope_db(0.005, 0.02)
    taxas, ataques_db, subidas = [], [], []
    at = an.ataques
    proximos = np.append(at[1:], an.duracao)
    for a, b in zip(at, proximos):
        i0 = int((a + 0.06) / 0.005)
        i1 = int(min(a + 0.4, b - 0.02) / 0.005)
        # para antes do corte da nota (abafada/solta): cauda de reverb/delay
        # depois do corte nao e sustain da nota
        if i1 - i0 > 8 and i1 + 8 < e.size:
            queda = e[i0:i1] - e[i0 + 8:i1 + 8]
            corte = np.flatnonzero(queda >= 10.0)
            if corte.size:
                i1 = i0 + corte[0]
        if i1 - i0 < 12 or i1 >= e.size:
            continue
        seg = e[i0:i1]
        if seg.max() < an.regioes['pico_db'] - 35:
            continue
        taxas.append(-np.polyfit(np.arange(seg.size) * 0.005, seg, 1)[0])
        j0 = max(0, int((a - 0.03) / 0.005))
        j1 = min(e.size, int(min(a + 1.2, b) / 0.005))
        trecho = e[j0:j1]
        if trecho.size < 4:
            continue
        # a subida comeca no vale logo antes/depois do ataque (a nota anterior
        # pode estar soando ate ali)
        i_min = int(np.argmin(trecho[:min(trecho.size, 22)]))
        resto = trecho[i_min:]
        pico_i = int(np.argmax(resto))
        ataques_db.append(resto[pico_i])
        # tempo de subida 10% -> 90% da amplitude (em dB: pico-20 -> pico-1)
        base = resto[:pico_i + 1]
        a10 = np.flatnonzero(base >= resto[pico_i] - 20)
        a90 = np.flatnonzero(base >= resto[pico_i] - 1)
        if a10.size and a90.size:
            subidas.append((a90[0] - a10[0]) * 0.005)
    return np.array(taxas), np.array(ataques_db), np.array(subidas)


def medidas_dinamica(an, medidas, curvas):
    taxas, niveis, subidas = _inclinacoes_decaimento(an)
    conf = float(np.clip(taxas.size / 6.0, 0, 1))
    decai = float(np.median(taxas)) if taxas.size else None
    faixa = float(np.percentile(niveis, 90) - np.percentile(niveis, 10)) if niveis.size > 2 else None
    subida = float(np.median(subidas)) if subidas.size else None
    e = an.energia_db[an.regioes['ativo']] if an.regioes['ativo'].any() else an.energia_db
    var_rms = float(np.std(e)) if e.size else 0.0
    medidas['decaimento_nota'] = _medida(decai, 'dB/s', conf * 0.8, 'dinamica',
                                         'Queda das notas (quanto maior, menos sustain)')
    medidas['faixa_dinamica'] = _medida(faixa, 'dB', conf * 0.7, 'dinamica',
                                        'Faixa dinâmica entre notas (p90-p10)')
    medidas['tempo_ataque'] = _medida(subida, 's', conf * 0.7, 'dinamica', 'Tempo de ataque das notas')
    medidas['variancia_rms'] = _medida(var_rms, 'dB', 0.7, 'dinamica', 'Desvio do nível (quadros com nota)')
    medidas['densidade_ataques'] = _medida(an.ataques.size / max(an.duracao, 1e-3), 'ataques/s', 0.8,
                                           'dinamica', 'Ataques por segundo')
    t, env = an.envelope_db(0.02, 0.04)
    curvas['env_t'] = t.tolist()
    curvas['env_db'] = env.tolist()
    # decaimento da nota com mais espaco ate a proxima (grafico de reverb/delay)
    t5, e5 = an.envelope_db(0.005, 0.02)
    at_s = an.ataques
    if at_s.size:
        fins = np.append(at_s[1:], an.duracao)
        i = int(np.argmax(fins - at_s))
        i0, i1 = int(at_s[i] / 0.005), int(min(fins[i], at_s[i] + 2.0) / 0.005)
        trecho = e5[i0:i1]
        if trecho.size > 20:
            ip = int(np.argmax(trecho[:40]))
            trecho = trecho[ip:]
            curvas['decaimento_t'] = (np.arange(trecho.size) * 0.005).tolist()
            curvas['decaimento_db'] = (trecho - trecho[0]).tolist()


def medidas_altura(an, medidas, curvas):
    """
        Croma (energia por classe de nota, 80 Hz-2 kHz) e altura mediana das
        notas soltas (YIN). Servem para achar transposicao (whammy, afinacao,
        capotraste) e oitava diferente (octaver) na comparacao. MIDI nao
        entra aqui: altura vem sempre do audio.
    """
    S = an.S
    f = an.freqs
    ativo = an.regioes['ativo'][:S.shape[1]]
    P = (S[:, ativo] ** 2).mean(axis=1) if ativo.any() else (S ** 2).mean(axis=1)
    sel = (f >= 80) & (f <= 2000)
    midi = 69 + 12 * np.log2(f[sel] / 440.0)
    classe = np.mod(np.round(midi), 12).astype(int)
    croma = np.bincount(classe, weights=P[sel], minlength=12)
    croma = croma / (croma.sum() + EPS)
    curvas['croma'] = croma.tolist()
    t, f0, aper = an.altura
    ok = (f0 > 0) & (aper < an.cfg['analise']['limiar_aperiodicidade'])
    if ok.sum() >= 20:
        m = 69 + 12 * np.log2(f0[ok] / 440.0)
        mediana = float(np.median(m))
        conf = float(np.clip(ok.mean() * 1.5, 0, 0.9))
    else:
        mediana, conf = None, 0.0
    medidas['altura_mediana'] = _medida(mediana, 'MIDI', conf, 'pitch', 'Altura mediana das notas')


def perfil_timbre(x, sr=SR_ANALISE, cfg=None, analise=None, efeitos=True, separado=False):
    """
        Como funciona: monta a AnaliseSinal (ou usa a que veio), calcula as
        familias de medidas (EQ, ganho, dinamica) e, se 'efeitos', roda os
        detectores (delay, reverb, modulacoes, filtros, pitch, ruido), que
        tambem acrescentam as proprias medidas.
        Devolve o perfil (dict serializavel em JSON, sem arrays numpy).
        Para que serve: e o que a comparacao referencia x gravacao usa.
        Onde e usada: Analisador IA, sugestoes_timbre, cadeia_pedais, testes.
    """
    an = analise or AnaliseSinal(x, sr, cfg)
    medidas, curvas = {}, {}
    medidas_eq(an, medidas, curvas)
    medidas_ganho(an, medidas)
    medidas_dinamica(an, medidas, curvas)
    medidas_altura(an, medidas, curvas)
    medidas['lufs_original'] = _medida(an.lufs_original, 'LUFS', 1.0, 'nivel', 'Loudness original')
    reg = an.regioes
    medidas['piso_ruido'] = _medida(reg['piso_db'] - reg['pico_db'], 'dB', 0.8, 'ruido',
                                    'Piso de ruído relativo ao pico')
    perfil = {'versao': 1, 'duracao': an.duracao, 'instrumento': an.cfg['instrumento'],
              'medidas': medidas, 'curvas': curvas, 'efeitos': {}}
    if efeitos:
        from audio import detectores_efeitos as det
        perfil['efeitos'] = det.detectar_todos(an, medidas, curvas, separado)
        perfil['separado'] = bool(separado)
    return perfil


def vetor_caracteristicas(perfil, chaves=None):
    """Vetor numerico (para o classificador da Fase 3) na ordem de 'chaves'."""
    med = perfil['medidas']
    chaves = chaves or sorted(med)
    return np.array([np.nan if med.get(k, {}).get('valor') is None else med[k]['valor']
                     for k in chaves], dtype=np.float64), chaves
