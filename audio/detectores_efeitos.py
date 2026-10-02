# -*- coding: utf-8 -*-
"""
Detectores de efeito do Analisador IA: um por pedal do motor
(audio/efeitos_pedais.py), todos por regras de DSP, sem rede e sem chave.

Cada detector recebe a AnaliseSinal (audio/analise_timbre.py) e devolve
    {'presenca': 'sim' | 'nao' | 'incerto',
     'confianca': 0..1   (quanto confiar na resposta 'presenca'),
     'score': 0..1       (quao forte e o sinal do efeito),
     'parametros': {...} (valores estimados, nas unidades do curriculo),
     'motivo': texto curto para a interface}

As medidas usadas ("caracteristicas") ficam em funcoes _caracteristicas_*;
os limiares ficam em audio/config_analise/_padrao.json -> 'detectores' (e
podem ser sobrepostos por instrumento). Nada de numero magico de decisao
espalhado aqui: o que e limiar vem de cfg['detectores'][<id>].

Interacoes consideradas (reduzem a confianca):
    distorcao alta  -> esconde modulacao e ressonancia de wah
    reverb longo    -> esconde o delay e as quedas do noise gate
    referencia separada (Demucs) -> artefatos parecem reverb/chorus
    poucas pausas   -> reverb e gate ficam 'incerto'
"""
import numpy as np
from scipy import signal

from audio import analise_timbre as at

EPS = 1e-12

# Grupo de cada efeito (mesmos ids e grupos do curriculo de pedais)
GRUPO = {
    'boost': 'ganho', 'overdrive': 'ganho', 'distorcao': 'ganho', 'fuzz': 'ganho',
    'volume': 'dinamica', 'compressor': 'dinamica', 'gate': 'dinamica',
    'eq': 'filtros', 'wah': 'filtros', 'autowah': 'filtros',
    'tremolo': 'modulacao', 'chorus': 'modulacao', 'flanger': 'modulacao',
    'phaser': 'modulacao', 'vibrato': 'modulacao',
    'delay': 'ambiencia', 'reverb': 'ambiencia',
    'octaver': 'pitch', 'whammy': 'pitch', 'ring': 'pitch',
}
# Categoria do indice de compatibilidade de cada efeito
CATEGORIA = {
    'ganho': 'ganho', 'dinamica': 'dinamica', 'filtros': 'eq', 'modulacao': 'modulacao',
    'ambiencia': 'ambiencia', 'pitch': 'modulacao',
}


def _resultado(score, cfg_det, parametros=None, motivo='', confianca_base=1.0):
    """Converte o score (0..1) em presenca + confianca usando os limiares do config."""
    sim, nao = cfg_det.get('limiar_sim', 0.6), cfg_det.get('limiar_nao', 0.3)
    score = float(np.clip(score, 0, 1))
    if score >= sim:
        presenca = 'sim'
        conf = 0.5 + 0.5 * (score - sim) / max(1e-6, 1 - sim)
    elif score <= nao:
        presenca = 'nao'
        conf = 0.5 + 0.5 * (nao - score) / max(1e-6, nao)
    else:
        presenca = 'incerto'
        conf = 0.35
    return {'presenca': presenca, 'confianca': float(np.clip(conf * confianca_base, 0, 1)),
            'score': score, 'parametros': parametros or {}, 'motivo': motivo}


def _rampa(v, a, b):
    """0 em a, 1 em b (a pode ser maior que b: rampa invertida)."""
    if v is None or not np.isfinite(v):
        return 0.0
    if b == a:
        return float(v >= b)
    return float(np.clip((v - a) / (b - a), 0, 1))


def _periodograma(segmentos, freqs):
    """
        Espectro de modulacao de varios trechos (t absoluto, r residuo).
        Devolve (potencia incoerente, coerencia de fase entre trechos,
        amplitude media do seno) por frequencia.
    """
    incoerente = np.zeros(freqs.size)
    coerente = np.zeros(freqs.size, dtype=complex)
    soma_abs = np.zeros(freqs.size)
    amp = np.zeros(freqs.size)
    peso_total = 0.0
    for t, r in segmentos:
        if t.size < 8:
            continue
        w = np.hanning(t.size)
        base = np.exp(-2j * np.pi * np.outer(freqs, t))
        C = base @ (r * w)
        incoerente += np.abs(C) ** 2
        coerente += C
        soma_abs += np.abs(C)
        amp += 2 * np.abs(C) / (w.sum() + EPS) * t.size
        peso_total += t.size
    if peso_total == 0:
        return incoerente, np.zeros(freqs.size), amp
    coer = np.abs(coerente) / (soma_abs + EPS)
    return incoerente, coer, amp / peso_total


def _pico_modulacao(segmentos, fmin, fmax, passo=0.05):
    """Frequencia, proeminencia, coerencia e amplitude do pico de modulacao."""
    freqs = np.arange(fmin, fmax + passo / 2, passo)
    pot, coer, amp = _periodograma(segmentos, freqs)
    if not np.any(pot > 0):
        return {'freq': None, 'proeminencia': 0.0, 'coerencia': 0.0, 'amplitude': 0.0,
                'n_trechos': 0}
    i = int(np.argmax(pot))
    fundo = float(np.median(pot)) + EPS
    return {'freq': float(freqs[i]), 'proeminencia': float(pot[i] / fundo),
            'coerencia': float(coer[i]), 'amplitude': float(amp[i]),
            'n_trechos': len(segmentos)}


def _trechos_entre_ataques(an, minimo_s, margem_ini=0.06, margem_fim=0.02):
    """Intervalos [a, b] (s) entre ataques, com nota soando, de duracao >= minimo_s."""
    at_s = an.ataques
    if at_s.size == 0:
        at_s = np.array([0.0])
    fins = np.append(at_s[1:], an.duracao)
    trechos = []
    for a, b in zip(at_s, fins):
        a2, b2 = a + margem_ini, b - margem_fim
        if b2 - a2 >= minimo_s:
            trechos.append((a2, b2))
    # sem ataques (ou nota unica): usa o sinal inteiro em janelas de 2 s
    if not trechos and an.duracao > minimo_s:
        passos = np.arange(0, an.duracao - minimo_s, 2.0)
        trechos = [(p, min(an.duracao, p + 2.0)) for p in passos]
    return trechos


# ===========================================================================
# CARACTERISTICAS
# ===========================================================================

def _cepstro_eco(an):
    """Cepstro de potencia do sinal inteiro (150 Hz-5 kHz), em quefrencias de 50 ms a 1,6 s."""
    x = an.x
    sr = an.sr
    n = 1 << int(np.ceil(np.log2(max(x.size, 2))))
    X = np.fft.rfft(x * np.hanning(x.size), n)
    f = np.fft.rfftfreq(n, 1.0 / sr)
    banda = (f >= 150) & (f <= 5000)
    L = np.log(np.abs(X) ** 2 + EPS)
    L_b = L[banda]
    k = max(3, int(40.0 / (f[1] + EPS)) | 1)
    suave = np.convolve(L_b, np.ones(k) / k, mode='same')
    Lz = np.zeros_like(L)
    Lz[banda] = L_b - suave
    c = np.fft.irfft(Lz, n) / (banda.mean() + EPS)
    q = np.arange(c.size) / sr
    faixa = (q >= 0.05) & (q <= 1.6)
    return q[faixa], c[faixa]


def caracteristicas_eco(an):
    """
        Delay: um delay devolve COPIAS do som (so um pouco filtradas). No
        cepstro de potencia, uma copia de ganho a no atraso L vira um pico de
        altura ~a na quefrencia L, e o feedback cria outro em 2L. Notas
        repetidas de verdade nunca sao copias exatas (fase, afinacao e tempo
        mudam), entao o ritmo quase nao aparece. Mede o pico (z robusto em
        janelas de 1 ms), a altura (-> mix) e o pico em 2L (-> feedback).
    """
    def calc():
        q, c = _cepstro_eco(an)
        passo = max(1, int(0.001 * an.sr))
        m = c.size // passo
        if m < 10:
            return {'lag': 0.0, 'z': 0.0, 'amp1': 0.0, 'amp2': 0.0, 'z2': 0.0,
                    'curva_q': [], 'curva_z': []}
        blocos = c[:m * passo].reshape(m, passo)
        pos = blocos.argmax(axis=1)
        pico = blocos.max(axis=1)
        qb = q[:m * passo].reshape(m, passo)[np.arange(m), pos]
        med = np.median(pico)
        mad = 1.4826 * np.median(np.abs(pico - med)) + EPS
        z = (pico - med) / mad
        i = int(np.argmax(z))
        lag = float(qb[i])

        def em(alvo):
            j = np.flatnonzero(np.abs(qb - alvo) <= 0.004)
            if j.size == 0:
                return 0.0, 0.0
            k = j[np.argmax(pico[j])]
            return float(pico[k]), float(z[k])
        amp2, z2 = em(2 * lag)
        return {'lag': lag, 'z': float(z[i]), 'amp1': float(pico[i]), 'amp2': amp2, 'z2': z2,
                'curva_q': qb[::5].tolist(), 'curva_z': np.clip(z[::5], -5, None).tolist()}
    return an._memo('eco', calc)


def caracteristicas_ambiencia(an):
    """
        Reverb: acha as pausas "de verdade" (a nota e cortada: o nivel cai
        mais de 10 dB em 40 ms) e, do fim do corte ate o proximo ataque, mede
        a curva de decaimento (integral de Schroeder, sem o ruido), o RT60
        pela reta entre -5 e -25 dB e o nivel da cauda (50-300 ms) relativo
        a nota. Nota que so vai morrendo sozinha nao conta como pausa.
    """
    def calc():
        passo = 0.005
        t, e = an.envelope_db(passo, 0.02)
        pico = an.regioes['pico_db']
        piso = an.regioes['piso_db']
        ataques = an.ataques
        fins = np.append(ataques[1:], an.duracao)
        k40 = int(0.04 / passo)
        limiar_corte = 6.0
        eco = caracteristicas_eco(an)
        c_delay = an.cfg['detectores']['delay']
        limite_eco = 10 ** 9
        if eco['z'] >= c_delay['z_min'] and eco['amp1'] >= c_delay['amp_min']:
            limite_eco = max(12, int(0.9 * eco['lag'] / passo))
        rts, caudas, quedas, curvas = [], [], [], []
        for a, b in zip(ataques, fins):
            i0, i1 = int(a / passo), int(b / passo) - 2
            if i1 - i0 < 40 or i1 >= e.size:
                continue
            seg = e[i0:i1]
            ip = int(np.argmax(seg[:min(seg.size, 60)]))
            nivel = seg[ip]
            if nivel < pico - 25:
                continue
            # corte: a maior queda em 40 ms depois do pico (a nota foi abafada)
            if seg.size - ip <= k40 + 1:
                continue
            queda40 = seg[ip:-k40] - seg[ip + k40:]
            k = ip + int(np.argmax(queda40))
            if queda40.max() < limiar_corte:
                continue
            # fim do corte: quando a queda em 40 ms fica menor que 1/3 do corte
            j = k
            while j + k40 < seg.size and seg[j] - seg[j + k40] >= queda40.max() / 3:
                j += 1
            j = min(seg.size - 1, j + k40 // 2)
            depois = seg[j:]
            # pausa de verdade: depois do corte o nivel so cai (ou fica), nao
            # volta a subir (tremolo, swell e a propria nota fazem isso)
            liso = np.convolve(depois, np.ones(7) / 7, mode='same') if depois.size > 7 else depois
            subida = np.flatnonzero(liso - np.minimum.accumulate(liso) > 6.0)
            if subida.size:
                depois = depois[:subida[0]]
            if depois.size < 30:                 # pausa curta demais (<150 ms)
                continue
            quedas.append((j - ip) * passo)
            pot = np.maximum(10 ** (depois / 10) - 10 ** ((piso + 3) / 10), 0)
            cauda = 10 * np.log10(np.mean(10 ** (depois[:50] / 10)) + EPS) - nivel
            caudas.append(cauda)
            acima = np.flatnonzero(depois > piso + 8.0)
            if cauda < -50 or acima.size < 10:
                rts.append(0.05)
            else:
                # reta no envelope em dB da cauda (ate 1,5 s, so acima do ruido e
                # antes do primeiro eco, se houver delay: o eco "levantaria" a cauda)
                fim = min(acima[-1] + 1, 300, limite_eco)
                tt = np.arange(fim) * passo
                yy = depois[:fim]
                ok = yy > piso + 8.0
                inclin = np.polyfit(tt[ok], yy[ok], 1)[0] if ok.sum() >= 10 else -600.0
                rts.append(float(np.clip(-60.0 / min(inclin, -1e-3), 0.05, 12.0)))
            if not curvas and depois.size >= 60:
                ini = max(0, ip)
                trecho = seg[ini:ini + 500]
                curvas.append((np.arange(trecho.size) * passo, trecho - nivel))
        return {'n_pausas': len(caudas),
                'rt60': float(np.median(rts)) if rts else None,
                'cauda_db': float(np.median(caudas)) if caudas else None,
                'queda_s': float(np.median(quedas)) if quedas else None,
                'curva': curvas[0] if curvas else None,
                'contraste_db': float(pico - piso)}
    return an._memo('ambiencia', calc)


def caracteristicas_mod_amplitude(an, cfg):
    """Tremolo: espectro de modulacao do envelope em dB dentro das notas."""
    def calc():
        t, e = an.envelope_db(0.005, 0.02)
        segs = []
        for a, b in _trechos_entre_ataques(an, cfg.get('trecho_minimo_s', 0.35)):
            i0, i1 = int(a / 0.005), int(b / 0.005)
            tt, ee = t[i0:i1], e[i0:i1]
            if tt.size < 20 or ee.max() < an.regioes['pico_db'] - 35:
                continue
            r = ee - np.polyval(np.polyfit(tt - tt[0], ee, 2), tt - tt[0])
            segs.append((tt, r))
        return _pico_modulacao(segs, cfg.get('taxa_min_hz', 2.0), cfg.get('taxa_max_hz', 14.0))
    return an._memo('mod_amplitude', calc)


def caracteristicas_mod_altura(an, cfg):
    """Vibrato/chorus: modulacao periodica da altura (cents) dentro de cada nota."""
    def calc():
        t, f0, aper = an.altura
        ok = (f0 > 0) & (aper < cfg.get('aperiodicidade_max', 0.3))
        segs, profundidades = [], []
        passo = t[1] - t[0] if t.size > 1 else 0.005
        minimo = int(cfg.get('trecho_minimo_s', 0.35) / passo)
        i = 0
        while i < f0.size:
            if not ok[i]:
                i += 1
                continue
            j = i
            ref = f0[i]
            while j < f0.size and ok[j] and abs(1200 * np.log2(f0[j] / ref)) < 120:
                ref = 0.9 * ref + 0.1 * f0[j]
                j += 1
            if j - i >= minimo:
                tt = t[i:j]
                c = 1200 * np.log2(f0[i:j] / np.median(f0[i:j]))
                c = c - np.polyval(np.polyfit(tt - tt[0], c, 2), tt - tt[0])
                segs.append((tt, c))
                profundidades.append(np.std(c))
            i = j + 1
        r = _pico_modulacao(segs, cfg.get('taxa_min_hz', 1.5), cfg.get('taxa_max_hz', 12.0))
        r['desvio_cents'] = float(np.median(profundidades)) if profundidades else 0.0
        return r
    return an._memo('mod_altura', calc)


def _trechos_quadros(an, minimo_s):
    """Trechos entre ataques em indices de quadro da STFT, so com nota soando."""
    ativo = an.regioes['ativo']
    saida = []
    for a, b in _trechos_entre_ataques(an, minimo_s):
        i0, i1 = int(a * an.sr / at.HOP), min(int(b * an.sr / at.HOP), ativo.size)
        if i1 - i0 >= 8 and ativo[i0:i1].mean() > 0.8:
            saida.append((i0, i1))
    return saida


def caracteristicas_mod_espectral(an, cfg):
    """
        Phaser (e wah automatico): a FORMA do espectro (bandas de 1/3 de
        oitava menos a media entre bandas) oscila dentro das notas, com a
        mesma fase de uma nota para a outra (o LFO nao reinicia na palhetada).
        Mede a potencia coerente somada nas bandas e a razao coerente /
        incoerente (0..1: 1 = todos os trechos na mesma fase).
    """
    def calc():
        centros, E = an.bandas
        sel_b = (centros >= 200) & (centros <= 6000)
        B = 10 * np.log10(E[sel_b] + EPS)
        forma = B - B.mean(axis=0, keepdims=True)
        tq = an.tempos[:B.shape[1]]
        freqs = np.arange(0.2, 8.0001, 0.025)
        coer = np.zeros((forma.shape[0], freqs.size), dtype=complex)
        incoer = np.zeros(freqs.size)
        residuos, pesos = [], []
        trechos = _trechos_quadros(an, cfg.get('trecho_minimo_s', 0.3))
        for i0, i1 in trechos:
            tt = tq[i0:i1]
            x0 = tt - tt[0]
            G = forma[:, i0:i1]
            c = np.polyfit(x0, G.T, 1)
            R = G - (np.outer(c[0], x0) + c[1][:, None])
            residuos.append(np.std(R, axis=1))
            pesos.append(i1 - i0)
            C = R @ np.exp(-2j * np.pi * np.outer(freqs, tt)).T
            coer += C
            incoer += np.sum(np.abs(C) ** 2, axis=0)
        n = len(trechos)
        if n < 2:
            return {'flutuacao_db': 0.0, 'freq': None, 'proeminencia': 0.0, 'coerencia': 0.0,
                    'n_trechos': n}
        P = np.sum(np.abs(coer) ** 2, axis=0)
        i = int(np.argmax(P))
        Rm = np.average(np.array(residuos), axis=0, weights=pesos)
        return {'flutuacao_db': float(np.median(Rm)), 'freq': float(freqs[i]),
                'proeminencia': float(P[i] / (np.median(P) + EPS)),
                'coerencia': float(P[i] / (incoer[i] * n + EPS)), 'n_trechos': n}
    return an._memo('mod_espectral', calc)


def caracteristicas_pureza(an):
    """
        Chorus: mistura o som com uma copia de afinacao oscilando, e os
        harmonicos deixam de ser "linhas finas". Em janelas longas (256 ms),
        mede quanto da energia de cada pico (400 Hz-1,2 kHz, onde a guitarra
        tem harmonicos fortes e as caudas de reverb/delay atrapalham menos)
        fica no proprio pico (+-1 bin) em vez de espalhar para os lados
        (+-8 bins). Seco ~0,97; chorus ~0,8.
    """
    def calc():
        n_fft, hop = 8192, 2048
        S = at.stft_mag(an.x, n_fft, hop)
        f = np.fft.rfftfreq(n_fft, 1.0 / an.sr)
        e = 20 * np.log10(S.max(axis=0) + EPS)
        # quadros longe de ataques (o ataque espalha qualquer pico)
        t_q = np.arange(S.shape[1]) * hop / an.sr
        ataques = an.ataques
        longe = np.ones(S.shape[1], dtype=bool)
        if ataques.size:
            dist = np.min(np.abs(t_q[:, None] - ataques[None, :]), axis=1)
            longe = dist > 0.13
        # so o "corpo" da nota (perto do nivel do ultimo ataque): caudas de
        # reverb/delay sozinhas nao contam
        from scipy.ndimage import maximum_filter1d
        recente = maximum_filter1d(e, size=5, origin=2)
        corpo = e >= recente - 8.0
        cols = np.flatnonzero((e > e.max() - 30) & longe & corpo)
        valores = []
        for c in cols:
            m = S[:, c] ** 2
            pk, _ = signal.find_peaks(m, height=m.max() * 1e-3, distance=8)
            pk = pk[(f[pk] > 400) & (f[pk] < 1200) & (pk > 8) & (pk < m.size - 9)]
            if pk.size < 2:
                continue
            pk = pk[np.argsort(m[pk])[::-1][:8]]
            valores.append(np.median([m[p - 1:p + 2].sum() / (m[p - 8:p + 9].sum() + EPS) for p in pk]))
        return {'pureza': float(np.median(valores)) if valores else None, 'n': len(valores)}
    return an._memo('pureza', calc)


def caracteristicas_pente(an):
    """
        Flanger: cepstro curto de cada quadro procura um pico em 0,4-8 ms que
        NAO seja multiplo do periodo da nota. Dentro de cada nota o flanger
        faz esse pico andar (o atraso varia); o "pente" natural da guitarra
        (posicao da palhetada) fica parado. Mede quanto ele anda (ms) dentro
        das notas e em que fracao dos quadros ele e forte.
    """
    def calc():
        S = an.S
        f = an.freqs
        banda = (f >= 300) & (f <= 9000)
        t_y, f0, _aper = an.altura
        dt_y = (t_y[1] - t_y[0]) if t_y.size > 1 else 0.005
        n = 1 << int(np.ceil(np.log2(2 * banda.sum())))
        q = np.arange(n) / (n * f[1])
        faixa = (q >= 0.0004) & (q <= 0.008)
        qq = q[faixa]
        movimentos, fortes, total = [], 0, 0
        for i0, i1 in _trechos_quadros(an, 0.3):
            cols = np.arange(i0, i1)
            L = np.log(S[banda][:, cols] ** 2 + EPS)
            L = L - L.mean(axis=0, keepdims=True)
            C = np.fft.irfft(L, n, axis=0)[faixa]
            posicoes = []
            for k, col in enumerate(cols):
                c = C[:, k].copy()
                iy = min(f0.size - 1, int(round(col * at.HOP / an.sr / dt_y))) if f0.size else 0
                ff = f0[iy] if f0.size else 0.0
                if ff > 0:
                    T0 = 1.0 / ff
                    mult = np.abs(qq / T0 - np.round(qq / T0))
                    c[(mult < 0.06) & (qq > 0.8 * T0)] = np.median(c)
                med = np.median(c)
                mad = 1.4826 * np.median(np.abs(c - med)) + EPS
                j = int(np.argmax(c))
                total += 1
                if (c[j] - med) / mad > 8:
                    fortes += 1
                    posicoes.append(qq[j])
            if len(posicoes) >= 4:
                p = np.array(posicoes) * 1000
                movimentos.append(float(np.std(p)))
        return {'fracao': float(fortes / max(1, total)),
                'movimento_ms': float(np.median(movimentos)) if movimentos else 0.0,
                'n_trechos': len(movimentos)}
    return an._memo('pente', calc)


def caracteristicas_filtro_movel(an):
    """
        Wah / envelope filter: centroide espectral (log2 Hz) dentro de cada
        nota. Wah: o centroide oscila (residuo depois de tirar a reta) e
        percorre uma faixa grande. Envelope filter: o centroide despenca do
        ataque para o fim da nota, junto com o volume (o som seco tambem
        escurece quando a nota morre, mas bem menos).
    """
    def calc():
        S = an.S
        f = an.freqs
        banda = (f >= 150) & (f <= 6000)
        P = S[banda] ** 2
        cent = np.log2(np.sum(f[banda][:, None] * P, axis=0) / (P.sum(axis=0) + EPS) + EPS)
        tq = an.tempos[:cent.size]
        residuos, quedas, faixas, segs = [], [], [], []
        for i0, i1 in _trechos_quadros(an, 0.25):
            c = cent[i0:i1]
            tt = tq[i0:i1]
            x0 = tt - tt[0]
            r = c - np.polyval(np.polyfit(x0, c, 1), x0)
            residuos.append(np.std(r))
            segs.append((tt, r))
            quedas.append(np.mean(c[:3]) - np.mean(c[-3:]))
            faixas.append(np.percentile(c, 95) - np.percentile(c, 5))
        if not residuos:
            return {'oscilacao_oit': 0.0, 'queda_oit': 0.0, 'faixa_oit': 0.0, 'freq': None,
                    'coerencia': 0.0, 'centroide_hz': float(2 ** np.median(cent)) if cent.size else 0.0,
                    'n_trechos': 0}
        mod = _pico_modulacao(segs, 0.3, 8.0)
        return {'oscilacao_oit': float(np.median(residuos)), 'queda_oit': float(np.median(quedas)),
                'faixa_oit': float(np.median(faixas)), 'freq': mod['freq'],
                'coerencia': mod['coerencia'], 'centroide_hz': float(2 ** np.median(cent)),
                'n_trechos': len(residuos)}
    return an._memo('filtro_movel', calc)


def caracteristicas_inarmonia(an):
    """
        Ring modulator: nos quadros com UMA nota clara (YIN), quanta energia
        dos picos espectrais cai fora dos harmonicos da nota (aceitando
        tambem a sub-oitava, para nao confundir com octaver). Guitarra seca
        ~0; ring com portadora fora do tom ~0,2-0,5. Com portadora afinada
        com as notas o resultado quase nao muda (o som continua "musical").
    """
    def calc():
        t, f0, aper = an.altura
        S = an.S
        f = an.freqs
        idx = np.clip(np.round(t * an.sr / at.HOP).astype(int), 0, S.shape[1] - 1)
        ativo = an.regioes['ativo'][:S.shape[1]]
        sel = (f0 > 0) & (aper < 0.35) & ativo[idx]
        fracs = []
        for qi, ff in list(zip(idx[sel], f0[sel]))[::6]:
            m = S[:, qi]
            pk, _ = signal.find_peaks(m, height=m.max() * 0.03, distance=3)
            pk = pk[(f[pk] > 50) & (f[pk] < 6000)]
            if pk.size < 3:
                continue
            a = m[pk] ** 2
            ok = np.zeros(pk.size, dtype=bool)
            for base in (ff, ff / 2):
                r = f[pk] / base
                k = np.round(r)
                ok |= (np.abs(r - k) < 0.06 * np.maximum(1, k / 4)) & (k >= 1)
            fracs.append(1 - a[ok].sum() / (a.sum() + EPS))
        vozeado = float(sel.sum() / max(1, ativo[idx].sum()))
        return {'inarmonia': float(np.median(fracs)) if fracs else 0.0, 'n': len(fracs),
                'fracao_vozeada': vozeado}
    return an._memo('inarmonia', calc)


def caracteristicas_ruido(an):
    """Noise gate: piso de ruido nas pausas, silencio digital e corte abrupto."""
    def calc():
        e = an.energia_db
        reg = an.regioes
        sil = reg['silencio']
        pico = reg['pico_db']
        amb = caracteristicas_ambiencia(an)
        fr_sil = float(sil.mean())
        piso_rel = float(np.median(e[sil]) - pico) if sil.any() else float(reg['piso_db'] - pico)
        return {'fracao_silencio': fr_sil, 'piso_rel_db': piso_rel,
                'digital': float(np.mean(e[sil] < -100)) if sil.any() else 0.0,
                'queda_s': amb['queda_s'], 'n_pausas': amb['n_pausas']}
    return an._memo('ruido', calc)


# ===========================================================================
# DETECTORES (limiares em cfg['detectores'])
# ===========================================================================

def _cfg(an, chave):
    """Limiares de um detector; o config precisa ter todos (nada escondido aqui)."""
    return an.cfg['detectores'][chave]


def _fator_distorcao(an, medidas):
    """Quanto a saturacao atrapalha medir modulacao e filtros (1 = nada)."""
    c = an.cfg['detectores']['interacoes']
    g = medidas.get('indice_ganho', {}).get('valor') or 0.0
    return float(1.0 - c['penalidade_ganho'] * _rampa(g, c['ganho_inicio'], 1.0))


def _nao_medido(motivo, score=0.0):
    return {'presenca': 'incerto', 'confianca': 0.2, 'score': score, 'parametros': {},
            'motivo': motivo}


def detectar_ganho(an, medidas):
    """
        Boost, overdrive, distorcao e fuzz a partir do indice de ganho: so o
        estagio que melhor explica o indice recebe 'sim'. Fuzz so se distingue
        da distorcao pela assimetria da onda (e fica 'possivel').
    """
    c = _cfg(an, 'ganho')
    g = medidas['indice_ganho']['valor'] or 0.0
    assim = medidas['assimetria']['valor'] or 0.0
    colado = medidas['clipping']['valor'] or 0.0
    nome = 'limpo'
    for inicio, n in an.cfg['ganho']['faixas_pedal']:
        if g >= inicio:
            nome = n
    res = {}
    for pedal in ('boost', 'overdrive', 'distorcao', 'fuzz'):
        centro = c['centros'][pedal]
        score = float(np.exp(-0.5 * ((g - centro) / c['largura']) ** 2))
        if pedal == 'distorcao' and g >= c['centros']['distorcao']:
            score = 1.0
        if pedal == 'fuzz':
            score = min(1.0, score if g >= c['centros']['fuzz'] else score) * \
                _rampa(assim, c['assimetria_fuzz_min'], c['assimetria_fuzz_max'])
        if pedal != nome and not (pedal == 'fuzz' and nome == 'distorcao'):
            score = min(score, c['teto_vizinho'])
        par = {}
        if pedal == 'overdrive':
            par = {'drive': round(float(np.clip((g - 0.35) / 0.4, 0.05, 1)), 2)}
        elif pedal == 'distorcao':
            par = {'dist': round(float(np.clip((g - 0.6) / 0.35, 0.1, 1)), 2)}
        elif pedal == 'fuzz':
            par = {'fuzz': round(float(np.clip((g - 0.6) / 0.35, 0.2, 1)), 2)}
        elif pedal == 'boost':
            par = {'ganho': float(round(np.clip((g - 0.15) * 50, 4, 20)))}
        res[pedal] = _resultado(score, c, par, f'índice de ganho {g:.2f} (clipping {colado:.2f})',
                                c['confianca'])
    res['_ganho'] = {'indice': g, 'classe': nome}
    return res


def detectar_delay(an, medidas):
    c = _cfg(an, 'delay')
    e = caracteristicas_eco(an)
    score = min(_rampa(e['z'], c['z_min'], c['z_max']), _rampa(e['amp1'], c['amp_min'], c['amp_max']))
    conf = 1.0
    amb = caracteristicas_ambiencia(an)
    if amb['rt60'] is not None and amb['rt60'] > c['rt_mascara_s']:
        conf *= c['fator_mascara']              # reverb longo espalha o eco
    mix = float(np.clip(e['amp1'] * c['escala_mix'], 0, 1))
    fb = 0.0
    if e['z2'] > c['z_feedback'] and e['amp1'] > 0:
        fb = float(np.clip((e['amp2'] / e['amp1'] + e['amp1'] / 2) * c['escala_feedback'], 0, 0.9))
    presente = score >= c['limiar_nao']
    par = {'time': round(e['lag'] * 1000.0), 'feedback': round(fb, 2), 'mix': round(mix, 2)}
    medidas['delay_tempo'] = at._medida(e['lag'] * 1000.0 if presente else None, 'ms', score,
                                        'ambiencia', 'Tempo do delay')
    medidas['delay_mix'] = at._medida(mix if presente else 0.0, '0-1', max(score, 0.4) * 0.8,
                                      'ambiencia', 'Volume das repetições do delay')
    medidas['delay_feedback'] = at._medida(fb if presente else 0.0, '0-1', max(score, 0.3) * 0.5,
                                           'ambiencia', 'Feedback do delay')
    medidas['delay_forca'] = at._medida(e['z'], 'z', 0.7, 'ambiencia', 'Força do eco (cepstro)')
    return _resultado(score, c, par, f"cópia do som {e['lag'] * 1000:.0f} ms depois (z={e['z']:.0f})", conf)


def detectar_reverb(an, medidas, separado=False):
    c = _cfg(an, 'reverb')
    amb = caracteristicas_ambiencia(an)
    rt, cauda = amb['rt60'], amb['cauda_db']
    if amb['n_pausas'] < c['pausas_minimas'] or rt is None:
        medidas['reverb_rt60'] = at._medida(None, 's', 0.0, 'ambiencia', 'Cauda do reverb (RT60)')
        medidas['reverb_cauda'] = at._medida(None, 'dB', 0.0, 'ambiencia', 'Nível da cauda do reverb')
        r = _nao_medido('sem pausas no trecho para medir a cauda', 0.4)
        r['sem_pausas'] = True
        return r
    score = c['peso_rt'] * _rampa(rt, c['rt_min'], c['rt_max']) + \
        (1 - c['peso_rt']) * _rampa(cauda, c['cauda_min_db'], c['cauda_max_db'])
    conf = float(np.clip(amb['n_pausas'] / c['pausas_confiaveis'], 0.3, 1.0))
    if separado:
        conf *= c['fator_separado']
    mix = float(np.clip((cauda - c['cauda_min_db']) / (c['cauda_max_db'] - c['cauda_min_db']) * 0.6,
                        0.05, 1.0))
    medidas['reverb_rt60'] = at._medida(rt if score > c['limiar_nao'] else 0.1, 's', conf,
                                        'ambiencia', 'Cauda do reverb (RT60)')
    medidas['reverb_cauda'] = at._medida(cauda, 'dB', conf, 'ambiencia', 'Nível da cauda (50-250 ms após o corte)')
    par = {'decay': round(float(np.clip(rt, 0.3, 8.0)), 1), 'mix': round(mix, 2)}
    return _resultado(score, c, par, f'cauda de ~{rt:.1f} s ({cauda:.0f} dB) em {amb["n_pausas"]} pausas', conf)


def detectar_tremolo(an, medidas):
    c = _cfg(an, 'tremolo')
    m = caracteristicas_mod_amplitude(an, c)
    pp = 2 * m['amplitude']
    depth = float(np.clip(1 - 10 ** (-pp / 20), 0, 1))
    score = min(_rampa(m['proeminencia'], c['prom_min'], c['prom_max']),
                _rampa(pp, c['pp_min_db'], c['pp_max_db']),
                _rampa(m['coerencia'], c['coer_min'], c['coer_max']))
    conf = float(np.clip(m['n_trechos'] / 3.0, 0.3, 1.0))
    presente = score >= c['limiar_nao']
    medidas['tremolo_taxa'] = at._medida(m['freq'] if presente else None, 'Hz', score, 'modulacao',
                                         'Taxa do tremolo')
    medidas['tremolo_prof'] = at._medida(depth if presente else 0.0, '0-1', max(score, 0.4), 'modulacao',
                                         'Profundidade do tremolo')
    par = {'rate': round(m['freq'] or 0.0, 2), 'depth': round(depth, 2)}
    return _resultado(score, c, par, f"volume oscila {m['freq'] or 0:.1f} Hz ({pp:.1f} dB)", conf)


def detectar_modulacoes(an, medidas):
    """Vibrato, chorus, flanger e phaser juntos (as medidas se confundem)."""
    cv, cc, cf, cp = (_cfg(an, k) for k in ('vibrato', 'chorus', 'flanger', 'phaser'))
    alt = caracteristicas_mod_altura(an, cv)
    esp = caracteristicas_mod_espectral(an, cp)
    pur = caracteristicas_pureza(an)
    pente = caracteristicas_pente(an)
    trem = caracteristicas_mod_amplitude(an, _cfg(an, 'tremolo'))
    fm = caracteristicas_filtro_movel(an)
    fator = _fator_distorcao(an, medidas)
    res = {}
    # vibrato: a altura oscila forte e na mesma fase de uma nota para a outra
    cents = 2 * alt['amplitude']
    s_vib = min(_rampa(alt['proeminencia'], cv['prom_min'], cv['prom_max']),
                _rampa(cents, cv['cents_min'], cv['cents_max']),
                _rampa(alt['coerencia'], cv['coer_min'], cv['coer_max']))
    res['vibrato'] = _resultado(s_vib * fator, cv,
                                {'rate': round(alt['freq'] or 0, 2),
                                 'depth': round(float(np.clip(cents / cv['cents_por_depth'], 0, 1)), 2)},
                                f"afinação oscila {alt['freq'] or 0:.1f} Hz (±{cents / 2:.0f} cents)")
    # chorus: harmonicos "borrados" (copia com afinacao oscilando), sem ser
    # vibrato (que borra muito mais), tremolo (bandas laterais) ou wah
    p = pur['pureza']
    s_ch = _rampa(p, cc['pureza_seco'], cc['pureza_chorus']) if p is not None else 0.0
    s_ch *= 1 - _rampa(s_vib, 0.3, 0.6)
    trem_forte = 2 * trem['amplitude'] >= _cfg(an, 'tremolo')['pp_min_db'] and \
        trem['coerencia'] >= _cfg(an, 'tremolo')['coer_min']
    if trem_forte:
        s_ch *= cc['fator_tremolo']
    s_ch *= 1 - 0.7 * _rampa(fm['oscilacao_oit'], cc['wah_osc_min'], cc['wah_osc_max'])
    res['chorus'] = _resultado(s_ch * fator, cc, {'rate': round(alt['freq'] or 0.8, 2),
                                                  'mix': round(float(0.3 + 0.5 * s_ch), 2)},
                               f"pureza dos harmônicos {p if p is not None else 0:.2f}",
                               1.0 if pur['n'] >= 5 else 0.5)
    # varredura (phaser/flanger): a forma do espectro anda dentro das notas
    s_varre = _rampa(esp['flutuacao_db'], cp['flut_min_db'], cp['flut_max_db'])
    s_varre = max(s_varre, _rampa(fm['oscilacao_oit'], cp['osc_min_oit'], cp['osc_max_oit']) * 0.8)
    s_varre *= 1 - _rampa(s_vib, 0.3, 0.6)
    s_varre *= 1 - 0.7 * _rampa(fm['faixa_oit'], cf['faixa_wah_min'], cf['faixa_wah_max'])
    s_pente = _rampa(pente['fracao'], cf['pente_min'], cf['pente_max'])
    s_puro = _rampa(p if p is not None else 1.0, cp['pureza_min'], cp['pureza_max'])
    s_fl = s_varre * max(s_pente, 1 - s_puro)
    s_ph = s_varre * s_puro * (1 - 0.8 * s_pente) * (0.6 + 0.4 * _rampa(esp['coerencia'], 0.3, 0.6))
    taxa_ph = (esp['freq'] or 1.2) / 2.0        # cada banda passa pelo vale 2x por ciclo
    res['flanger'] = _resultado(s_fl * fator, cf, {'rate': round(taxa_ph, 2)},
                                f"espectro varre ({esp['flutuacao_db']:.1f} dB) com pente em "
                                f"{pente['fracao'] * 100:.0f}% dos quadros")
    res['phaser'] = _resultado(s_ph * fator, cp, {'rate': round(taxa_ph, 2)},
                               f"espectro varre {taxa_ph:.2f} Hz sem pente regular")
    medidas['vibrato_cents'] = at._medida(cents / 2, 'cents', max(s_vib, 0.4), 'modulacao',
                                          'Oscilação de afinação (±)')
    medidas['vibrato_taxa'] = at._medida(alt['freq'] if s_vib >= cv['limiar_nao'] else None, 'Hz', s_vib,
                                         'modulacao', 'Taxa da oscilação de afinação')
    medidas['pureza_harmonicos'] = at._medida(p, '0-1', 0.6 if pur['n'] >= 5 else 0.3, 'modulacao',
                                              'Pureza dos harmônicos (chorus borra)')
    medidas['varredura_espectral'] = at._medida(esp['flutuacao_db'], 'dB', 0.5, 'modulacao',
                                                'Varredura do espectro dentro das notas')
    return res


def detectar_filtros(an, medidas):
    cw, ca = _cfg(an, 'wah'), _cfg(an, 'autowah')
    fm = caracteristicas_filtro_movel(an)
    resson = medidas.get('ressonancia_db', {}).get('valor') or 0.0
    fator = _fator_distorcao(an, medidas)
    if fm['n_trechos'] == 0:
        return {'wah': _nao_medido('notas curtas demais para seguir o filtro'),
                'autowah': _nao_medido('notas curtas demais para seguir o filtro')}
    faixa = _rampa(fm['faixa_oit'], cw['faixa_min_oit'], cw['faixa_max_oit'])
    monotono = fm['queda_oit'] / (fm['faixa_oit'] + EPS)
    s_auto = min(_rampa(fm['queda_oit'], ca['queda_min_oit'], ca['queda_max_oit']),
                 _rampa(monotono, ca['monotono_min'], ca['monotono_max']))
    s_wah = min(faixa, _rampa(fm['oscilacao_oit'], cw['osc_min_oit'], cw['osc_max_oit'])) * \
        (1 - 0.7 * s_auto)
    s_wah = max(s_wah, _rampa(resson, cw['resson_min_db'], cw['resson_max_db']) * cw['peso_fixo'])
    medidas['filtro_faixa_oit'] = at._medida(fm['faixa_oit'], 'oitavas', 0.5, 'eq',
                                             'Quanto o brilho anda dentro das notas')
    fc = fm['centroide_hz'] or 700.0
    pos = float(np.clip(np.log(max(fc * 1.3, 350) / 350.0) / np.log(2300 / 350.0), 0, 1))
    return {
        'wah': _resultado(s_wah * fator, cw, {'pedal': round(pos, 2), 'auto': round(fm['freq'] or 0.0, 2)},
                          f"brilho oscila {fm['oscilacao_oit']:.2f} oitava dentro das notas"),
        'autowah': _resultado(s_auto * fator, ca, {'sens': round(float(0.4 + 0.5 * s_auto), 2)},
                              f"brilho cai {fm['queda_oit']:.1f} oitava junto com o volume da nota"),
    }


def detectar_pitch(an, medidas):
    co, cr = _cfg(an, 'octaver'), _cfg(an, 'ring')
    h = at.harmonicos(an)
    ir = caracteristicas_inarmonia(an)
    vozeado = h['fracao_vozeada'] >= co['vozeado_min']
    if vozeado:
        s_sub = min(_rampa(-h['impar_agudo'], co['impar_min_db'], co['impar_max_db']),
                    _rampa(h['sub_oitava'], co['sub_min_db'], co['sub_max_db']))
        oct_res = _resultado(s_sub, co, {'sub': round(float(0.3 + 0.5 * s_sub), 2)},
                             f"harmônicos ímpares somem {-h['impar_agudo']:.0f} dB (nota uma oitava abaixo)",
                             max(0.4, h['confianca']))
    else:
        s_sub = 0.0
        oct_res = _nao_medido('precisa de notas soltas (uma de cada vez) para medir a oitava')
    medidas['sub_oitava'] = at._medida(-h['impar_agudo'] if vozeado else None, 'dB',
                                       max(0.3, h['confianca']) if vozeado else 0.0, 'pitch',
                                       'Oitava abaixo (falta de harmônicos ímpares)')
    if ir['fracao_vozeada'] >= cr['vozeado_min']:
        s_ring = _rampa(ir['inarmonia'], cr['inarm_min'], cr['inarm_max'])
        ring_res = _resultado(s_ring, cr, {}, f"{ir['inarmonia'] * 100:.0f}% da energia fora da série harmônica")
    else:
        ring_res = _nao_medido('precisa de notas soltas para medir a série harmônica')
    medidas['inarmonia'] = at._medida(ir['inarmonia'], 'fração', 0.5, 'pitch',
                                      'Energia fora da série harmônica')
    return {
        'octaver': oct_res,
        'ring': ring_res,
        # sozinho, o whammy so muda a nota: ele aparece na comparacao
        # (transposicao entre referencia e gravacao)
        'whammy': _nao_medido('aparece só na comparação (notas transpostas)'),
    }


def detectar_dinamica(an, medidas):
    cc, cv, cg = _cfg(an, 'compressor'), _cfg(an, 'volume'), _cfg(an, 'gate')
    decai = medidas['decaimento_nota']['valor']
    faixa = medidas['faixa_dinamica']['valor']
    g = medidas['indice_ganho']['valor'] or 0.0
    s_sust = _rampa(decai, cc['decai_limpo'], cc['decai_comprimido']) if decai is not None else 0.0
    s_faixa = _rampa(faixa, cc['faixa_limpa_db'], cc['faixa_comprimida_db']) if faixa is not None else 0.0
    s_comp = (cc['peso_sustain'] * s_sust + (1 - cc['peso_sustain']) * s_faixa) * \
        (1 - _rampa(g, cc['ganho_mascara_ini'], cc['ganho_mascara_fim']))
    conf_c = max(0.3, medidas['decaimento_nota']['confianca'])
    subida = medidas['tempo_ataque']['valor']
    s_swell = _rampa(subida, cv['ataque_min_s'], cv['ataque_max_s']) if subida is not None else 0.0
    r = caracteristicas_ruido(an)
    if r['fracao_silencio'] < cg['silencio_min']:
        gate = _nao_medido('sem pausas para ver o ruído de fundo')
    else:
        s_gate = max(_rampa(-r['piso_rel_db'], cg['piso_aberto_db'], cg['piso_fechado_db']),
                     _rampa(r['digital'], cg['digital_min'], cg['digital_max']))
        gate = _resultado(s_gate, cg, {'limiar': -40.0 if s_gate > 0.5 else -60.0},
                          f"ruído nas pausas {r['piso_rel_db']:.0f} dB abaixo do pico")
    medidas['ruido_pausas'] = at._medida(r['piso_rel_db'] if r['fracao_silencio'] >= cg['silencio_min'] else None,
                                         'dB', 0.6, 'ruido', 'Ruído nas pausas (relativo ao pico)')
    return {
        'compressor': _resultado(s_comp, cc, {'sustain': round(float(0.3 + 0.6 * s_comp), 2)},
                                 f"notas caem {decai if decai is not None else 0:.0f} dB/s", conf_c),
        'volume': _resultado(s_swell, cv, {'ataque': round(float(subida or 0), 2)},
                             f"ataque médio de {1000 * (subida or 0):.0f} ms"),
        'gate': gate,
    }


def _rebaixar(res, chave, fator, motivo):
    """Diminui o score de um detector por causa de outro efeito que o imita."""
    r = res[chave]
    if r['score'] <= 0:
        return
    novo = r['score'] * fator
    r['score'] = float(novo)
    r['motivo'] += f' ({motivo})'
    if r['presenca'] == 'sim' and novo < 0.6:
        r['presenca'] = 'incerto' if novo > 0.3 else 'nao'
        r['confianca'] = 0.35 if novo > 0.3 else 0.5


def _aplicar_interacoes(an, res, medidas):
    """
        Um efeito pode imitar outro: modulacao periodica vira "eco" no
        cepstro, reverb e distorcao borram os harmonicos (parece chorus),
        ecos de delay mexem na forma do espectro (parece phaser/flanger) e a
        saturacao faz o brilho pular (parece wah). Quando o efeito "de
        verdade" e forte, o imitado perde forca. Fatores no config.
    """
    c = an.cfg['detectores']['interacoes']
    forte = lambda k: res.get(k, {}).get('presenca') == 'sim'
    for mod in ('vibrato', 'tremolo'):
        taxa = res[mod]['parametros'].get('rate') or 0
        lag = (res['delay']['parametros'].get('time') or 0) / 1000.0
        if forte(mod) and taxa > 0 and lag > 0:
            ciclos = lag * taxa
            if abs(ciclos - round(ciclos)) < 0.08:
                _rebaixar(res, 'delay', c['fator_delay_por_modulacao'], f'eco explicado pelo {mod}')
    if forte('delay'):
        for k in ('phaser', 'flanger'):
            _rebaixar(res, k, c['fator_varredura_por_delay'], 'ecos do delay mexem no espectro')
    if forte('delay'):
        _rebaixar(res, 'reverb', c['fator_reverb_por_delay'], 'as repetições do delay também formam cauda')
    if forte('reverb'):
        _rebaixar(res, 'chorus', c['fator_chorus_por_reverb'], 'a cauda do reverb também borra os harmônicos')
    g = medidas.get('indice_ganho', {}).get('valor') or 0.0
    if g > c['ganho_inicio']:
        fator = 1.0 - c['penalidade_extra_filtros'] * _rampa(g, c['ganho_inicio'], 1.0)
        for k in ('chorus', 'wah', 'autowah', 'phaser', 'flanger'):
            _rebaixar(res, k, fator, 'saturação alta atrapalha a medida')


def detectar_todos(an, medidas, curvas, separado=False):
    """
        Como funciona: roda todos os detectores e junta num dict por id do
        pedal (mesmos ids do motor). Guarda tambem curvas para os graficos
        (decaimento de uma pausa e a curva de eco).
        Para que serve: o campo 'efeitos' do perfil de timbre.
        Onde e usada: analise_timbre.perfil_timbre.
    """
    res = {}
    ganho = detectar_ganho(an, medidas)
    info_ganho = ganho.pop('_ganho')
    res.update(ganho)
    res.update(detectar_dinamica(an, medidas))
    res.update(detectar_filtros(an, medidas))
    res['tremolo'] = detectar_tremolo(an, medidas)
    res.update(detectar_modulacoes(an, medidas))
    res['delay'] = detectar_delay(an, medidas)
    res['reverb'] = detectar_reverb(an, medidas, separado)
    res.update(detectar_pitch(an, medidas))
    res['eq'] = {'presenca': 'incerto', 'confianca': 0.0, 'score': 0.0, 'parametros': {},
                 'motivo': 'o EQ é comparado banda a banda (Timbre base)'}
    _aplicar_interacoes(an, res, medidas)
    if separado:
        fator = an.cfg['detectores']['interacoes']['fator_separado_modulacao']
        for chave in ('chorus', 'flanger', 'phaser', 'vibrato'):
            res[chave]['confianca'] *= fator
    eco = caracteristicas_eco(an)
    curvas['eco_q'] = eco['curva_q']
    curvas['eco_z'] = eco['curva_z']
    curvas['classe_ganho'] = info_ganho['classe']
    # modelo treinado localmente (Fase 3), se existir: reforca as regras
    try:
        from audio import treinar_detector
        treinar_detector.reforcar(res, medidas, an.cfg)
    except Exception:
        pass
    for chave, r in res.items():
        r['grupo'] = GRUPO.get(chave, '')
    return res
