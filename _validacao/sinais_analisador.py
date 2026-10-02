# -*- coding: utf-8 -*-
"""
Sinais de teste do Analisador IA: guitarra (sintetizada pelo motor de pedais
ou o sampler de DI real, se a biblioteca existir) passando por efeitos
conhecidos com parametros conhecidos. Sem pygame, sem placa de som.

Usado por teste_analisador.py, preview_analisador.py e pelo treino da Fase 3.
"""
import os
import sys

import numpy as np

_AQUI = os.path.dirname(os.path.abspath(__file__))
_RAIZ = os.path.dirname(_AQUI)
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

from audio import efeitos_pedais as motor  # noqa: E402

SR = motor.SR_PADRAO
_cache = {}


def base_sintetica(chave='riff', repeticoes=3):
    """O loop do estudo de Pedais repetido (continuo, sem emenda)."""
    base, _ = motor.gerar_base(chave, SR)
    return np.tile(base, repeticoes)


def _corda_humana(freq, duracao, sr, vel, abafada, rng):
    """Como motor._corda, mas com fase aleatoria por harmonico (nota nunca igual a outra)."""
    cauda = 1.5
    total = duracao + (0.05 if abafada else cauda)
    n = int(total * sr)
    t = np.arange(n) / sr
    y = np.zeros(n)
    tau0 = (0.10 if abafada else 2.4) * (220.0 / freq) ** 0.3
    pos = 0.18 + rng.uniform(-0.03, 0.03)
    k = 1
    while k * freq < min(9000.0, sr * 0.45) and k <= 40:
        fk = k * freq * np.sqrt(1 + 0.00008 * k * k)
        ak = abs(np.sin(np.pi * k * pos)) / k
        tauk = tau0 / (1 + (k * freq / 1400.0) ** 1.4)
        y += ak * np.exp(-t / tauk) * np.sin(2 * np.pi * fk * t + rng.uniform(0, 2 * np.pi))
        k += 1
    ataque = int(0.002 * sr)
    y[:ataque] *= np.linspace(0, 1, ataque)
    ruido = rng.standard_normal(int(0.006 * sr)) * np.linspace(1, 0, int(0.006 * sr)) * 0.08
    y[:ruido.size] += ruido
    fim = int(duracao * sr)
    queda = int((0.03 if abafada else 0.08) * sr)
    if fim < n:
        env = np.ones(n)
        env[fim:fim + queda] = np.linspace(1, 0, min(queda, n - fim))
        env[fim + queda:] = 0.0
        y *= env
    return y / (np.max(np.abs(y)) or 1.0) * vel


def base_humana(chave='riff', repeticoes=3, semente=3):
    """
        A frase do motor tocada "por uma pessoa": cada nota com fase propria,
        um pouco de variacao de tempo (+-6 ms), de forca e de afinacao
        (+-4 cents). Duas notas iguais nunca sao a mesma forma de onda, como
        numa guitarra de verdade (e diferente de um eco de delay, que e copia).
    """
    k = ('humana', chave, repeticoes, semente)
    if k in _cache:
        return _cache[k]
    rng = np.random.default_rng(semente)
    dados = motor.BASES[chave]
    rasg = dados.get('rasgueado', 0.0)
    total = repeticoes * motor.DURACAO_LOOP
    buf = np.zeros(int((total + 2.0) * SR))
    for r in range(repeticoes):
        for midis, ini, dur, vel, abafada in dados['notas']:
            t0 = (ini + r * motor.BATIDAS_LOOP) * motor.TEMPO + rng.normal(0, 0.006)
            v = vel * rng.uniform(0.85, 1.1)
            for i, m in enumerate(midis):
                f = 440.0 * 2 ** ((m - 69 + rng.normal(0, 0.04)) / 12.0)
                nota = _corda_humana(f, max(0.05, dur * motor.TEMPO - i * rasg), SR, v, abafada, rng)
                a = max(0, int((t0 + i * rasg) * SR))
                b = min(buf.size, a + nota.size)
                buf[a:b] += nota[:b - a] / np.sqrt(len(midis))
    x = buf[:int(total * SR)]
    x = x / (np.max(np.abs(x)) or 1.0) * 0.5
    _cache[k] = x
    return x


def base_di(chave='riff', repeticoes=3, semente=11):
    """
        Mesma frase, tocada pelo sampler de guitarra DI (amostras reais).
        Sem a biblioteca de amostras, cai na guitarra sintetizada.
    """
    k = (chave, repeticoes, semente)
    if k in _cache:
        return _cache[k]
    try:
        from audio import sintetizador as sint
        if not sint.sampler_disponivel()[0]:
            raise RuntimeError('sem sampler')
        notas = []
        rng = np.random.default_rng(semente)
        dados = motor.BASES[chave]
        rasg = dados.get('rasgueado', 0.0)
        for r in range(repeticoes):
            for midis, ini, dur, vel, abafada in dados['notas']:
                for i, m in enumerate(midis):
                    t0 = (ini + r * motor.BATIDAS_LOOP) * motor.TEMPO + i * rasg + rng.normal(0, 0.006)
                    d = dur * motor.TEMPO * (0.35 if abafada else 1.0)
                    notas.append(sint.NotaAudio(t0=max(0.0, t0), dur=d, altura=m,
                                                vel=int(np.clip(40 + vel * 80 * rng.uniform(0.85, 1.1), 1, 127)),
                                                bend=float(rng.normal(0, 0.04))))
        total = repeticoes * motor.DURACAO_LOOP
        buf, _ = sint.render_notas(notas, total + 0.5, SR, timbre='real_di', dobrar=False)
        x = np.asarray(buf, dtype=np.float64).mean(axis=1)[:int(total * SR)]
        x = x / (np.max(np.abs(x)) or 1.0) * 0.5
    except Exception:
        x = base_sintetica(chave, repeticoes)
    _cache[k] = x
    return x


def com_ruido(x, nivel_db=-72.0, semente=5):
    """Chiado de fundo de uma pedaleira de verdade (branco levemente filtrado)."""
    rng = np.random.default_rng(semente)
    ruido = rng.standard_normal(x.size)
    ruido = np.convolve(ruido, [0.5, 0.5], mode='same')
    ruido *= 10 ** (nivel_db / 20.0) / (np.std(ruido) + 1e-12)
    return x + ruido


def aplicar(x, efeito, **params):
    """Um pedal do motor com o padrao do curriculo e os parametros dados."""
    from Estudos import curriculo_pedais as cur
    valores = cur.valores_padrao(cur.PEDAIS_POR_ID[efeito])
    valores.update(params)
    y = motor.aplicar_efeito(x, SR, efeito, valores)
    return y.mean(axis=1) if y.ndim == 2 else y


def cadeia(x, *itens):
    """itens: (efeito, {params}) na ordem da pedaleira."""
    y = x
    for efeito, params in itens:
        y = aplicar(y, efeito, **params)
    return y
