# -*- coding: utf-8 -*-
"""
Motor de efeitos de pedal (numpy + scipy), usado pelo estudo de Pedais.

Tudo aqui e processamento offline de um trecho curto em loop: o estudo gera
um "audio base" de guitarra sintetizada (riff, power chords, acordes, notas
soltas ou nota longa), passa pelo efeito escolhido com os parametros atuais e
devolve um array estereo pronto para virar pygame.mixer.Sound.

Como o trecho toca em loop, cada efeito e calculado em cima de DUAS copias
seguidas do audio base e so a segunda metade e aproveitada. Assim a cauda do
delay, do reverb, do chorus etc. que "vazaria" do fim do loop ja aparece no
comeco dele, e o loop soa continuo, como se voce estivesse tocando sem parar.
Os osciladores de modulacao (LFO) tem a frequencia arredondada para caber um
numero inteiro de ciclos no loop, pelo mesmo motivo.

Sem dependencia de pygame: da para testar e ouvir (gerando WAV) sem janela.
"""
import numpy as np
from scipy import signal

SR_PADRAO = 44100
BPM = 100
TEMPO = 60.0 / BPM            # duracao de uma seminima, em segundos
BATIDAS_LOOP = 8              # dois compassos 4/4
DURACAO_LOOP = TEMPO * BATIDAS_LOOP


# ===========================================================================
# AUDIO BASE: guitarra sintetizada por sintese aditiva de corda pinçada
# ===========================================================================

def _freq(midi):
    return 440.0 * 2 ** ((midi - 69) / 12.0)


def _corda(freq, duracao, sr, vel=1.0, abafada=False, cauda=1.5):
    """
        Como funciona: soma harmonicos levemente inarmonicos, cada um com
        decaimento proprio (agudos morrem antes), mais um ruido curtinho de
        palheta no ataque. 'abafada' simula palm mute (tudo decai rapido).
        Para que serve: gerar uma nota de guitarra limpa sem SoundFont.
    """
    total = duracao + (0.05 if abafada else cauda)
    n = int(total * sr)
    t = np.arange(n) / sr
    y = np.zeros(n)
    tau0 = (0.10 if abafada else 2.4) * (220.0 / freq) ** 0.3
    posicao_palheta = 0.18
    k = 1
    while k * freq < min(9000.0, sr * 0.45) and k <= 40:
        fk = k * freq * np.sqrt(1 + 0.00008 * k * k)
        ak = abs(np.sin(np.pi * k * posicao_palheta)) / k
        tauk = tau0 / (1 + (k * freq / 1400.0) ** 1.4)
        y += ak * np.exp(-t / tauk) * np.sin(2 * np.pi * fk * t + k * 0.7)
        k += 1
    # ataque suave de 2 ms + ruido de palheta
    ataque = int(0.002 * sr)
    y[:ataque] *= np.linspace(0, 1, ataque)
    ruido = np.random.default_rng(int(freq * 10)).standard_normal(int(0.006 * sr))
    ruido *= np.linspace(1, 0, ruido.size) * 0.08
    y[:ruido.size] += ruido
    # abafa ao fim da duracao (mao direita/esquerda soltando a corda)
    fim = int(duracao * sr)
    queda = int((0.03 if abafada else 0.08) * sr)
    env = np.ones(n)
    if fim < n:
        env[fim:fim + queda] = np.linspace(1, 0, min(queda, n - fim))
        env[fim + queda:] = 0.0
    y *= env
    pico = np.max(np.abs(y)) or 1.0
    return y / pico * vel


# Cada nota: (midis, inicio em batidas, duracao em batidas, velocidade, abafada)
E5, G5, A5, D5 = (40, 47, 52), (43, 50, 55), (45, 52, 57), (38, 45, 50)
EM = (40, 47, 52, 55, 59, 64)
C_MAIOR = (48, 52, 55, 60, 64)
G_MAIOR = (43, 47, 50, 55, 59, 67)
D_MAIOR = (50, 57, 62, 66)

BASES = {
    'riff': {
        'nome': 'Riff',
        'descricao': 'Frase de pentatonica de La menor, nota a nota.',
        'notas': [((57,), 0, .5, .9, False), ((60,), .5, .5, .8, False),
                  ((62,), 1, .5, .85, False), ((64,), 1.5, .5, .8, False),
                  ((67,), 2, .5, .95, False), ((64,), 2.5, .5, .75, False),
                  ((62,), 3, 1, .85, False), ((60,), 4, .5, .8, False),
                  ((62,), 4.5, .5, .75, False), ((57,), 5, 1.5, .95, False),
                  ((55,), 6.5, .5, .7, False), ((57,), 7, 1, .85, False)],
    },
    'power': {
        'nome': 'Power chords',
        'descricao': 'Palhetada abafada em E5 com acentos em G5 e A5.',
        'notas': [(E5, 0, .25, .8, True), (E5, .5, .25, .7, True),
                  (E5, 1, .25, .75, True), (G5, 1.5, .9, 1.0, False),
                  (E5, 2.5, .25, .7, True), (E5, 3, .25, .75, True),
                  (A5, 3.5, .9, 1.0, False), (E5, 4.5, .25, .7, True),
                  (E5, 5, .25, .75, True), (D5, 5.5, .5, .95, False),
                  (E5, 6, 2, 1.0, False)],
    },
    'acorde': {
        'nome': 'Acordes',
        'descricao': 'Em, C, G e D abertos, deixando soar.',
        'notas': [(EM, 0, 2, .9, False), (C_MAIOR, 2, 2, .85, False),
                  (G_MAIOR, 4, 2, .9, False), (D_MAIOR, 6, 2, .85, False)],
        'rasgueado': 0.014,
    },
    'staccato': {
        'nome': 'Notas soltas',
        'descricao': 'Poucas notas curtas com silencio entre elas: otimo para ouvir caudas.',
        'notas': [((64,), 0, .35, .95, False), ((67,), 2, .35, .9, False),
                  ((69,), 4, .35, .95, False), ((72,), 5.5, .35, .85, False)],
    },
    'nota': {
        'nome': 'Nota longa',
        'descricao': 'Duas notas sustentadas (La e Mi): o efeito fica bem exposto.',
        'notas': [((57,), 0, 3.9, 1.0, False), ((64,), 4, 3.9, 1.0, False)],
    },
}
ORDEM_BASES = ['riff', 'power', 'acorde', 'staccato', 'nota']

_cache_bases = {}


def gerar_base(chave, sr=SR_PADRAO):
    """
        Como funciona: sintetiza as notas da base e dobra a cauda que passa do
        fim do loop de volta para o comeco (loop sem emenda).
        Devolve (audio mono float64, lista de instantes de ataque em segundos).
    """
    chave = chave if chave in BASES else 'riff'
    if (chave, sr) in _cache_bases:
        return _cache_bases[(chave, sr)]
    dados = BASES[chave]
    n_loop = int(round(DURACAO_LOOP * sr))
    buf = np.zeros(n_loop * 2)
    ataques = []
    rasg = dados.get('rasgueado', 0.0)
    for midis, inicio, dur, vel, abafada in dados['notas']:
        t0 = inicio * TEMPO
        ataques.append(t0)
        for i, m in enumerate(midis):
            nota = _corda(_freq(m), dur * TEMPO - i * rasg, sr, vel, abafada)
            a = int((t0 + i * rasg) * sr)
            b = min(buf.size, a + nota.size)
            buf[a:b] += nota[:b - a] / np.sqrt(len(midis))
    base = buf[:n_loop] + buf[n_loop:]
    base = base / (np.max(np.abs(base)) or 1.0) * 0.5
    _cache_bases[(chave, sr)] = (base, ataques)
    return base, ataques


# ===========================================================================
# FERRAMENTAS DE DSP
# ===========================================================================

def _db(x):
    return 10 ** (x / 20.0)


def _lp(x, fc, sr, ordem=1):
    fc = float(np.clip(fc, 20, sr * 0.45))
    b, a = signal.butter(ordem, fc / (sr / 2), 'low')
    return signal.lfilter(b, a, x, axis=0)


def _hp(x, fc, sr, ordem=1):
    fc = float(np.clip(fc, 10, sr * 0.45))
    b, a = signal.butter(ordem, fc / (sr / 2), 'high')
    return signal.lfilter(b, a, x, axis=0)


def _biquad(tipo, fc, sr, ganho_db=0.0, q=0.707):
    """Coeficientes RBJ (peaking, lowshelf, highshelf, bandpass)."""
    A = 10 ** (ganho_db / 40.0)
    w0 = 2 * np.pi * float(np.clip(fc, 20, sr * 0.45)) / sr
    cw, sw = np.cos(w0), np.sin(w0)
    alfa = sw / (2 * q)
    if tipo == 'peaking':
        b = [1 + alfa * A, -2 * cw, 1 - alfa * A]
        a = [1 + alfa / A, -2 * cw, 1 - alfa / A]
    elif tipo == 'lowshelf':
        s = 2 * np.sqrt(A) * alfa
        b = [A * ((A + 1) - (A - 1) * cw + s), 2 * A * ((A - 1) - (A + 1) * cw),
             A * ((A + 1) - (A - 1) * cw - s)]
        a = [(A + 1) + (A - 1) * cw + s, -2 * ((A - 1) + (A + 1) * cw),
             (A + 1) + (A - 1) * cw - s]
    elif tipo == 'highshelf':
        s = 2 * np.sqrt(A) * alfa
        b = [A * ((A + 1) + (A - 1) * cw + s), -2 * A * ((A - 1) + (A + 1) * cw),
             A * ((A + 1) + (A - 1) * cw - s)]
        a = [(A + 1) - (A - 1) * cw + s, 2 * ((A - 1) - (A + 1) * cw),
             (A + 1) - (A - 1) * cw - s]
    else:  # bandpass com ganho de pico 0 dB
        b = [alfa, 0.0, -alfa]
        a = [1 + alfa, -2 * cw, 1 - alfa]
    b, a = np.array(b), np.array(a)
    return b / a[0], a / a[0]


def _filtro(x, tipo, fc, sr, ganho_db=0.0, q=0.707):
    b, a = _biquad(tipo, fc, sr, ganho_db, q)
    return signal.lfilter(b, a, x)


def _filtro_variavel(x, fcs_por_bloco, sr, q, bloco):
    """Bandpass com frequencia mudando bloco a bloco (wah, auto-wah)."""
    y = np.zeros_like(x)
    zi = np.zeros(2)
    for i, fc in enumerate(fcs_por_bloco):
        a0 = i * bloco
        seg = x[a0:a0 + bloco]
        if seg.size == 0:
            break
        b, a = _biquad('bandpass', fc, sr, q=q)
        y[a0:a0 + seg.size], zi = signal.lfilter(b, a, seg, zi=zi)
    return y


def _envelope(x, sr, tau=0.01):
    """Envelope RMS com filtro de um polo."""
    alfa = np.exp(-1.0 / (tau * sr))
    return np.sqrt(np.maximum(signal.lfilter([1 - alfa], [1, -alfa], x * x), 1e-12))


def _suavizar(x, sr, tau):
    alfa = np.exp(-1.0 / (max(tau, 1e-4) * sr))
    return signal.lfilter([1 - alfa], [1, -alfa], x)


def _lfo_freq(freq, dur):
    """Arredonda a frequencia para caber um numero inteiro de ciclos no loop."""
    ciclos = max(1, int(round(freq * dur)))
    return ciclos / dur


def _ler_atrasado(x, atraso_amostras):
    """x(n - d(n)) com d fracionario (interpolacao linear)."""
    n = np.arange(x.size, dtype=np.float64)
    pos = np.clip(n - atraso_amostras, 0, x.size - 1)
    return np.interp(pos, n, x)


def _conv_circular(x, ir):
    """Convolucao circular: a cauda que passa do loop volta para o comeco."""
    n = x.size
    dobrada = np.zeros(n)
    for i in range(0, ir.size, n):
        pedaco = ir[i:i + n]
        dobrada[:pedaco.size] += pedaco
    return np.real(np.fft.ifft(np.fft.fft(x) * np.fft.fft(dobrada)))


# ===========================================================================
# EFEITOS  (cada um recebe x mono, t em segundos, sr, parametros p, ctx)
# ===========================================================================

def fx_boost(x, t, sr, p, ctx):
    y = x * _db(p['ganho'])
    y = _filtro(y, 'highshelf', 2500, sr, p['brilho'] * 6)
    # amplificador levemente saturado depois do pedal
    drive = 1 + p['amp'] * 6
    return np.tanh(y * drive) / drive * 1.6


def fx_overdrive(x, t, sr, p, ctx):
    # "corcova" de medios: corta graves antes de saturar (estilo Tube Screamer)
    pre = _hp(x, 720, sr) + 0.25 * x
    g = 1 + p['drive'] * 60
    y = np.tanh(pre * g) * (0.55 + 0.45 / (1 + p['drive'] * 4))
    y += 0.15 * x                     # um pouco de sinal limpo misturado
    y = _lp(y, 700 + p['tone'] ** 2 * 6500, sr, 2)
    return y * p['level'] * 0.5


def fx_distorcao(x, t, sr, p, ctx):
    pre = _hp(x, 90, sr)
    g = 8 + p['dist'] * 400
    y = np.clip(pre * g, -1, 1)
    y = np.tanh(1.8 * y)
    y = _lp(y, 5500, sr, 2)           # tira o "zumbido de abelha" do extremo agudo
    y = _lp(y, 500 + p['tone'] ** 2 * 7500, sr, 1)
    return y * p['level'] * 0.24


def fx_fuzz(x, t, sr, p, ctx):
    g = 30 + p['fuzz'] * 900
    vies = p['bias'] * 0.02
    env = _envelope(x, sr, 0.004)
    y = np.tanh((x + vies) * g) - np.tanh(vies * g)
    # bias alto = transistor "morrendo": sinal fraco some e o som picota
    if p['bias'] > 0:
        limiar = p['bias'] * 0.06
        y *= np.clip((env - limiar * 0.5) / (limiar * 0.5 + 1e-6), 0, 1)
    y = np.clip(y, -1.2, 0.9)          # corte assimetrico
    y = _lp(y, 4500, sr, 2)
    y = _lp(y, 600 + p['tone'] ** 2 * 6000, sr, 1)
    return y * p['volume'] * 0.26


def fx_compressor(x, t, sr, p, ctx):
    limiar_db = -12 - p['sustain'] * 30
    razao = 2 + p['sustain'] * 10
    env_db = 20 * np.log10(_envelope(x, sr, 0.012))
    excesso = np.maximum(0, env_db - limiar_db)
    ganho_db = -excesso * (1 - 1 / razao)
    ganho = _db(_suavizar(ganho_db, sr, p['attack'] / 1000.0))
    compensacao = _db(-limiar_db * (1 - 1 / razao) * 0.3)
    return x * ganho * compensacao * p['level'] * 1.4


def fx_gate(x, t, sr, p, ctx):
    env_db = 20 * np.log10(_envelope(x, sr, 0.005))
    aberto = (env_db > p['limiar']).astype(float)
    # segura aberto por 'release' e fecha suave
    janela = max(1, int(p['release'] / 1000.0 * sr))
    from scipy.ndimage import maximum_filter1d
    segurado = maximum_filter1d(aberto, size=janela, origin=-(janela // 2))
    ganho = _suavizar(segurado, sr, 0.002 + p['release'] / 4000.0)
    return x * ganho


def fx_volume(x, t, sr, p, ctx):
    ataques = np.array(ctx['ataques_s'])
    L = ctx['duracao']
    tl = t % L
    idx = np.searchsorted(ataques, tl, side='right') - 1
    ultimo = np.where(idx >= 0, ataques[np.maximum(idx, 0)], ataques[-1] - L)
    desde = tl - ultimo
    if p['ataque'] > 0.01:
        env = np.clip(desde / p['ataque'], 0, 1) ** 2
        env = _suavizar(env, sr, 0.006)       # o reinicio a cada nota nao estala
    else:
        env = np.ones_like(x)
    return x * env * p['pedal'] ** 2 * 1.3


def fx_eq(x, t, sr, p, ctx):
    y = _filtro(x, 'lowshelf', 180, sr, p['graves'])
    y = _filtro(y, 'peaking', p['freq_medios'], sr, p['medios'], q=1.0)
    y = _filtro(y, 'highshelf', 3000, sr, p['agudos'])
    return y * _db(p['level'])


def _fc_wah(pos):
    return 350.0 * (2300.0 / 350.0) ** np.clip(pos, 0, 1)


def fx_wah(x, t, sr, p, ctx):
    bloco = 128
    tb = t[::bloco]
    if p['auto'] > 0.05:
        # o pe automatico balanca em volta da posicao escolhida no Pedal
        f = _lfo_freq(p['auto'], ctx['duracao'])
        pos = np.clip(p['pedal'] + 0.45 * np.sin(2 * np.pi * f * tb), 0, 1)
    else:
        pos = np.full(tb.size, p['pedal'])
    y = _filtro_variavel(x, _fc_wah(pos), sr, p['q'], bloco)
    return y * (1.9 + p['q'] * 0.2) + 0.08 * x


def fx_autowah(x, t, sr, p, ctx):
    bloco = 128
    env = _envelope(x, sr, 0.004)
    env = _suavizar(env, sr, p['resposta'] / 1000.0)
    ref = np.percentile(env, 95) or 1.0
    pos = np.clip(env / ref * (0.3 + p['sens'] * 1.2), 0, 1)
    if p['direcao'] >= 0.5:
        pos = 1 - pos
    fcs = 250.0 * (3000.0 / 250.0) ** pos[::bloco]
    y = _filtro_variavel(x, fcs, sr, p['q'], bloco)
    return y * (3.2 + p['q'] * 0.3) + 0.06 * x


def fx_tremolo(x, t, sr, p, ctx):
    f = _lfo_freq(p['rate'], ctx['duracao'])
    s = np.sin(2 * np.pi * f * t)
    k = 1 + p['forma'] * 20
    onda = np.tanh(k * s) / np.tanh(k)          # 0 = senoide, 1 = quase quadrada
    ganho = 1 - p['depth'] * (0.5 - 0.5 * onda)
    return x * ganho * (1 + p['depth'] * 0.3)


def fx_chorus(x, t, sr, p, ctx):
    f = _lfo_freq(p['rate'], ctx['duracao'])
    base = 0.016 * sr
    swing = p['depth'] * 0.006 * sr
    e = _ler_atrasado(x, base + swing * np.sin(2 * np.pi * f * t))
    d = _ler_atrasado(x, base + swing * np.sin(2 * np.pi * f * t + np.pi * 0.5))
    m = p['mix']
    return np.stack([x * (1 - m * 0.5) + e * m, x * (1 - m * 0.5) + d * m], axis=1) * 0.85


def fx_flanger(x, t, sr, p, ctx):
    f = _lfo_freq(p['rate'], ctx['duracao'])
    manual = p['manual'] / 1000.0 * sr
    atraso = manual * (1 + p['depth'] * 0.95 * np.sin(2 * np.pi * f * t))
    atraso = np.maximum(atraso, 1.0)
    fb = p['feedback']
    y = x.copy()
    acum = x.copy()
    ganho = 1.0
    for k in range(1, 9):
        acum = _ler_atrasado(x, atraso * k)
        y += ganho * acum
        ganho *= fb
        if ganho < 0.01:
            break
    return y * 0.9 / (1 + fb)


def fx_phaser(x, t, sr, p, ctx):
    bloco = 256
    f = _lfo_freq(p['rate'], ctx['duracao'])
    tb = t[::bloco]
    lfo = 0.5 - 0.5 * np.cos(2 * np.pi * f * tb)
    fmin, fmax = 250.0, 250.0 + p['depth'] * 2500.0
    fcs = fmin * (fmax / fmin) ** lfo
    estagios = int(p['estagios'])
    tan = np.tan(np.pi * np.clip(fcs, 20, sr * 0.45) / sr)
    coefs = (tan - 1) / (tan + 1)
    y = x.copy()
    for _ in range(estagios):
        saida = np.zeros_like(y)
        zi = np.zeros(1)
        for i, a1 in enumerate(coefs):
            a0 = i * bloco
            seg = y[a0:a0 + bloco]
            if seg.size == 0:
                break
            saida[a0:a0 + seg.size], zi = signal.lfilter([a1, 1.0], [1.0, a1], seg, zi=zi)
        y = saida
    m = p['mix']
    return x * (1 - m * 0.5) + y * m * 0.9


def fx_vibrato(x, t, sr, p, ctx):
    f = _lfo_freq(p['rate'], ctx['duracao'])
    swing = p['depth'] * 0.004 * sr
    return _ler_atrasado(x, 0.005 * sr + swing * (1 + np.sin(2 * np.pi * f * t)))


def fx_delay(x, t, sr, p, ctx):
    T = p['time'] / 1000.0
    fb = p['feedback']
    n = int(max(T * 12, 3.0) * sr)
    ir = np.zeros(n)
    ir[0] = 1.0
    pulso = np.zeros(int(0.02 * sr))
    pulso[0] = 1.0
    # cada repeticao passa pelo filtro de novo: fica mais escura (delay analogico)
    fc = 1200 + p['tom'] ** 2 * 12000
    ganho = p['mix']
    repeticao = pulso
    for k in range(1, 40):
        repeticao = _lp(repeticao, fc, sr, 1) if p['tom'] < 0.98 else repeticao
        a = int(k * T * sr)
        if a >= n or ganho < 0.003:
            break
        b = min(n, a + repeticao.size)
        ir[a:b] += ganho * repeticao[:b - a]
        ganho *= fb
    seco = 1 - p['mix'] * 0.35
    ir[0] = seco
    return _conv_circular(x, ir)


def fx_reverb(x, t, sr, p, ctx):
    dec = p['decay']
    n = int((dec * 1.3 + p['predelay'] / 1000.0) * sr)
    rng = np.random.default_rng(7)
    tt = np.arange(n) / sr
    saidas = []
    for canal in range(2):
        ruido = rng.standard_normal(n)
        escuro = _lp(ruido, 2500, sr, 1)
        brilho = ruido - escuro
        fator_brilho = 0.15 + p['tom'] * 0.85
        ir = escuro * np.exp(-6.9 * tt / dec) + \
            brilho * np.exp(-6.9 * tt / (dec * fator_brilho)) * (0.3 + p['tom'] * 0.7)
        # reflexoes iniciais
        for atraso, g in ((0.011, .5), (0.019, .4), (0.027, .35), (0.041, .3)):
            i = int((atraso + canal * 0.003) * sr)
            if i < n:
                ir[i] += g * 6
        ir[:int(0.004 * sr)] *= np.linspace(0, 1, int(0.004 * sr))
        ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
        pre = int(p['predelay'] / 1000.0 * sr)
        ir = np.concatenate([np.zeros(pre), ir])
        molhado = _conv_circular(x, ir) * 1.6
        saidas.append(x * (1 - p['mix'] * 0.6) + molhado * p['mix'])
    return np.stack(saidas, axis=1)


def fx_octaver(x, t, sr, p, ctx):
    rastreio = _lp(_hp(x, 60, sr), 350, sr, 2)
    env = _envelope(x, sr, 0.01)
    # oitava abaixo: flip-flop que troca de lado a cada ciclo da nota
    sinal_pos = rastreio > 0.0005
    subidas = np.flatnonzero(sinal_pos[1:] & ~sinal_pos[:-1]) + 1
    # o loop so emenda se cada volta tiver um numero par de viradas
    n_loop = int(round(ctx['duracao'] * sr))
    na_volta = subidas[subidas >= n_loop]
    if na_volta.size % 2 == 1:
        subidas = subidas[subidas != na_volta[-1]]
    contagem = np.zeros(x.size, dtype=np.int64)
    contagem[subidas] = 1
    contagem = np.cumsum(contagem)
    quadrada = np.where(contagem % 2 == 0, 1.0, -1.0)
    sub = _lp(quadrada * env, 900, sr, 2) * 1.6
    # oitava acima: retificacao (dobra a onda, dobra a frequencia)
    cima = _hp(np.abs(x), 120, sr, 2) * 1.8
    return x * p['seco'] + sub * p['sub'] + cima * p['cima']


def fx_whammy(x, t, sr, p, ctx):
    semitons = p['intervalo']
    if p['movimento'] > 0.02:
        f = _lfo_freq(p['movimento'], ctx['duracao'])
        pos = (0.5 - 0.5 * np.cos(2 * np.pi * f * t)) * p['pedal']
    else:
        pos = np.full(x.size, p['pedal'])
    razao = 2 ** (semitons * pos / 12.0)
    janela = 0.045 * sr
    fase = np.cumsum(1 - razao) / janela
    fase = fase - np.floor(fase)
    f2 = (fase + 0.5) % 1.0
    y = np.sin(np.pi * fase) ** 2 * _ler_atrasado(x, fase * janela) + \
        np.sin(np.pi * f2) ** 2 * _ler_atrasado(x, f2 * janela)
    m = p['mix']
    return x * (1 - m) + y * m * 1.05


def fx_ring(x, t, sr, p, ctx):
    f = _lfo_freq(p['freq'], ctx['duracao'])
    y = x * np.sin(2 * np.pi * f * t) * 1.4
    return x * (1 - p['mix']) + y * p['mix']


EFEITOS = {
    'boost': fx_boost, 'overdrive': fx_overdrive, 'distorcao': fx_distorcao,
    'fuzz': fx_fuzz, 'compressor': fx_compressor, 'gate': fx_gate,
    'volume': fx_volume, 'eq': fx_eq, 'wah': fx_wah, 'autowah': fx_autowah,
    'tremolo': fx_tremolo, 'chorus': fx_chorus, 'flanger': fx_flanger,
    'phaser': fx_phaser, 'vibrato': fx_vibrato, 'delay': fx_delay,
    'reverb': fx_reverb, 'octaver': fx_octaver, 'whammy': fx_whammy,
    'ring': fx_ring,
}

# Efeitos lineares e sem modulacao: usam convolucao circular direto no loop
_CIRCULARES = {'delay', 'reverb'}


def _preparar_entrada(chave_efeito, base, sr):
    """Alguns pedais precisam de um sinal de entrada especial para fazer sentido."""
    if chave_efeito == 'gate':
        # o gate so mostra servico com chiado: distorce e poe ruido de fundo
        rng = np.random.default_rng(3)
        chiado = _hp(rng.standard_normal(base.size), 1500, sr) * 0.0012
        sujo = np.tanh((base + chiado) * 60) * 0.35
        return _lp(sujo, 5000, sr, 2)
    return base


def renderizar(chave_efeito, params, chave_base='riff', ligado=True, sr=SR_PADRAO):
    """
        Como funciona: gera (ou pega do cache) a base, aplica o efeito em duas
        copias seguidas e devolve a segunda, ja em estereo float32 entre -1 e 1.
        Para que serve: o audio de cada ajuste do estudo de Pedais.
        Onde e usada: Estudos/estudo_pedais.py e as suites de validacao.
    """
    base, ataques = gerar_base(chave_base, sr)
    entrada = _preparar_entrada(chave_efeito, base, sr)
    n = entrada.size
    if not ligado or chave_efeito not in EFEITOS:
        y = entrada
    else:
        ctx = {'duracao': n / sr, 'ataques_s': ataques}
        fx = EFEITOS[chave_efeito]
        if chave_efeito in _CIRCULARES:
            t = np.arange(n) / sr
            y = fx(entrada, t, sr, params, ctx)
        else:
            dobro = np.concatenate([entrada, entrada])
            t = np.arange(dobro.size) / sr
            saida = np.asarray(fx(dobro, t, sr, params, ctx), dtype=np.float64)
            y = saida[n:].copy()
            # emenda: nos ultimos 12 ms, funde com o trecho que antecede o
            # comeco do loop, para o fim encaixar no inicio sem estalo mesmo
            # quando o efeito tem estado (flip-flop do octaver, por exemplo)
            m = min(n, int(0.012 * sr))
            w = np.linspace(0.0, 1.0, m)
            if y.ndim == 2:
                w = w[:, None]
            y[-m:] = y[-m:] * (1 - w) + saida[n - m:n] * w
    y = np.asarray(y, dtype=np.float64)
    if y.ndim == 1:
        y = np.stack([y, y], axis=1)
    pico = np.max(np.abs(y))
    if pico > 0.95:                     # limitador de seguranca
        y = np.tanh(y / pico * 1.4) / np.tanh(1.4) * 0.95
    return y.astype(np.float32)


def para_int16(estereo, canais=2):
    """Converte o float estereo para o formato do mixer do pygame."""
    dados = np.clip(estereo * 32767 * 0.9, -32768, 32767).astype(np.int16)
    if canais == 1:
        return np.ascontiguousarray(dados.mean(axis=1).astype(np.int16))
    return np.ascontiguousarray(dados)


def forma_de_onda(estereo, pontos=400):
    """Picos por fatia, para desenhar a forma de onda do loop."""
    mono = np.abs(estereo).max(axis=1)
    fatias = np.array_split(mono, pontos)
    return np.array([f.max() if f.size else 0.0 for f in fatias])


def salvar_wav(caminho, estereo, sr=SR_PADRAO):
    from scipy.io import wavfile
    wavfile.write(caminho, sr, para_int16(estereo))
