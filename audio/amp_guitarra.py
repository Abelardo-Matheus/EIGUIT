# -*- coding: utf-8 -*-
"""
Amplificador de guitarra para o sinal DI do sampler (nível 2).

Cadeia:  DI -> pré-filtro (aperta graves / "boost" estilo TS no high gain)
            -> 1 a 3 estágios de válvula (waveshaper assimétrico com oversampling 4x)
            -> equalização (grave / médio / agudo / presença)
            -> caixa: resposta ao impulso (IR)  -> sala curta  -> noise gate (high gain)

Caixa: por padrão usa IRs gerados aqui (curvas típicas de 2x12 e 4x12,
fase mínima), sem nenhuma questão de licença. Se você colocar arquivos .wav
de IR em assets/audio/ir/, o primeiro (ordem alfabética) passa a ser usado.
"""
from __future__ import annotations

import functools
import glob
import math
import os
import time
from typing import Optional

import numpy as np
from scipy.signal import butter, fftconvolve, resample_poly, sosfilt

AMPS = {
    # ganho, estágios, assimetria, pré passa-alta, pré "boost" médio (dB), EQ (dB), caixa, sala, gate
    "clean":    dict(ganho=1.6, est=1, assim=0.06, pre_hp=60, boost=0, grave=2, medio=-1, agudo=2, pres=2,
                     caixa="2x12", sala=0.16, gate=None),
    "crunch":   dict(ganho=9, est=2, assim=0.18, pre_hp=90, boost=2, grave=1, medio=2, agudo=1, pres=1,
                     caixa="4x12", sala=0.10, gate=None),
    "drive":    dict(ganho=28, est=2, assim=0.2, pre_hp=180, boost=4, grave=1, medio=1, agudo=0, pres=2,
                     caixa="4x12", sala=0.07, gate=-58),
    "highgain": dict(ganho=75, est=3, assim=0.22, pre_hp=420, boost=7, grave=3, medio=-3, agudo=1, pres=3,
                     caixa="4x12", sala=0.05, gate=-52),
}


# ------------------------------------------------------------------ filtros
def _biquad(tipo: str, f0: float, db: float, q: float, taxa: int) -> np.ndarray:
    """RBJ cookbook -> sos (1 seção)."""
    A = 10 ** (db / 40)
    w = 2 * math.pi * f0 / taxa
    cw, sw = math.cos(w), math.sin(w)
    if tipo == "pico":
        al = sw / (2 * q)
        b = [1 + al * A, -2 * cw, 1 - al * A]
        a = [1 + al / A, -2 * cw, 1 - al / A]
    else:
        al = sw / 2 * math.sqrt(2)
        s = 1 if tipo == "graves" else -1
        sa = 2 * math.sqrt(A) * al
        if tipo == "graves":
            b = [A * ((A + 1) - (A - 1) * cw + sa), 2 * A * ((A - 1) - (A + 1) * cw), A * ((A + 1) - (A - 1) * cw - sa)]
            a = [(A + 1) + (A - 1) * cw + sa, -2 * ((A - 1) + (A + 1) * cw), (A + 1) + (A - 1) * cw - sa]
        else:
            b = [A * ((A + 1) + (A - 1) * cw + sa), -2 * A * ((A - 1) + (A + 1) * cw), A * ((A + 1) + (A - 1) * cw - sa)]
            a = [(A + 1) - (A - 1) * cw + sa, 2 * ((A - 1) - (A + 1) * cw), (A + 1) - (A - 1) * cw - sa]
        del s
    b = np.array(b) / a[0]
    a = np.array(a) / a[0]
    return np.array([[b[0], b[1], b[2], 1.0, a[1], a[2]]])


def _filtrar(sos, x):
    return sosfilt(sos, x, axis=0)


# ------------------------------------------------------------------ caixas
_CURVAS = {
    # Hz: dB — respostas típicas de alto-falante de guitarra (medidas públicas de referência, simplificadas)
    "2x12": [(40, -24), (70, -9), (100, -2), (160, 0), (300, -1), (600, -2), (1000, -1), (1800, 1.5),
             (2600, 3), (3400, 1), (4500, -5), (6000, -14), (8000, -26), (11000, -40), (16000, -55)],
    "4x12": [(40, -22), (70, -6), (100, 0), (140, 1.5), (250, -1), (500, -3), (900, -2), (1600, 1),
             (2400, 3.5), (3200, 2), (4000, -4), (5000, -13), (6500, -26), (9000, -42), (16000, -60)],
}


@functools.lru_cache(maxsize=8)
def _ir_gerado(tipo: str, taxa: int, n: int = 4096) -> np.ndarray:
    f = np.fft.rfftfreq(n, 1 / taxa)
    pts = _CURVAS[tipo]
    lf = np.log10(np.maximum(f, 20))
    db = np.interp(lf, [math.log10(p) for p, _ in pts], [d for _, d in pts])
    # pequenas ondulações de cone para não soar "EQ de livro"
    rng = np.random.default_rng(3 if tipo == "4x12" else 5)
    db += np.convolve(rng.normal(0, 1.2, len(db)), np.ones(9) / 9, "same") * (f > 1500)
    mag = 10 ** (db / 20)
    # fase mínima por cepstro real
    espectro_log = np.log(np.maximum(np.concatenate([mag, mag[-2:0:-1]]), 1e-8))
    cep = np.fft.ifft(espectro_log).real
    janela = np.zeros(n)
    janela[0] = 1
    janela[1:n // 2] = 2
    janela[n // 2] = 1
    ir = np.fft.ifft(np.exp(np.fft.fft(cep * janela))).real[: n // 2]
    ir *= np.hanning(n)[n // 2:]
    return (ir / (np.sqrt(np.sum(ir ** 2)) + 1e-9)).astype(np.float32)


def ir_usuario() -> Optional[str]:
    from . import sintetizador as sint
    lst = sorted(glob.glob(os.path.join(sint.PASTA_SONS, "ir", "*.wav")))
    return lst[0] if lst else None


@functools.lru_cache(maxsize=8)
def _ir_arquivo(caminho: str, taxa: int) -> np.ndarray:
    import soundfile as sf
    ir, fs = sf.read(caminho, dtype="float32", always_2d=True)
    ir = ir.mean(axis=1)
    if fs != taxa:
        g = math.gcd(fs, taxa)
        ir = resample_poly(ir, taxa // g, fs // g).astype(np.float32)
    ir = ir[: int(0.5 * taxa)]
    return ir / (np.sqrt(np.sum(ir ** 2)) + 1e-9)


def caixa_ir(tipo: str, taxa: int) -> np.ndarray:
    u = ir_usuario()
    if u:
        try:
            return _ir_arquivo(u, taxa)
        except Exception:
            pass
    return _ir_gerado(tipo, taxa)


@functools.lru_cache(maxsize=4)
def _ir_sala(taxa: int, dur: float = 0.45) -> np.ndarray:
    n = int(dur * taxa)
    rng = np.random.default_rng(9)
    t = np.arange(n) / taxa
    env = np.exp(-t / 0.09)
    ir = rng.normal(0, 1, (n, 2)) * env[:, None]
    ir = sosfilt(butter(1, 4500, fs=taxa, output="sos"), ir, axis=0)
    ir[: int(0.012 * taxa)] = 0                   # pré-delay (primeira reflexão)
    return (ir / np.sqrt(np.sum(ir ** 2) / 2)).astype(np.float32)


# ------------------------------------------------------------------ amp
def _valvula(x: np.ndarray, g: float, assim: float) -> np.ndarray:
    y = np.tanh(np.float32(g) * (x + np.float32(assim)))
    y -= np.float32(math.tanh(g * assim))
    return y


_FILTRO_PERCEP: dict = {}


def nivel_percebido(x: np.ndarray, taxa: int) -> float:
    """RMS com ponderação parecida com a do ouvido (menos peso para graves e agudos extremos)."""
    if taxa not in _FILTRO_PERCEP:
        _FILTRO_PERCEP[taxa] = (butter(2, 300, "highpass", fs=taxa, output="sos"),
                                butter(1, 6000, fs=taxa, output="sos"))
    hp, lp = _FILTRO_PERCEP[taxa]
    # potência de cada lado separado (somar os lados antes criaria "filtro pente")
    y = sosfilt(lp, sosfilt(hp, x, axis=0), axis=0)
    return float(np.sqrt(np.mean(y ** 2)) + 1e-12)


def processar(di: np.ndarray, preset: str, taxa: int, rapido: bool = False,
              pico_entrada: float = None, ganho_saida: float = None) -> np.ndarray:
    """di: float32 (n, 2). -> float32 (n, 2).
    Sem ganho_saida, normaliza o resultado em 0.9 (uso para trechos curtos).
    pico_entrada/ganho_saida fixos: usados no processamento em blocos, para todos os
    blocos da música terem exatamente o mesmo nível. Tudo em float32 (memória baixa).
    rapido=True: sem oversampling e sem sala (para tocar nota a nota em tempo real)."""
    if preset not in AMPS:
        return di
    p = AMPS[preset]
    pico = (pico_entrada if pico_entrada else float(np.abs(di).max())) + 1e-9
    x = (di * np.float32(0.5 / pico)).astype(np.float32)
    envelope_in = None
    if p["gate"] is not None:
        envelope_in = sosfilt(butter(1, 25, fs=taxa, output="sos"), np.abs(x).max(axis=1)).astype(np.float32)
    x = _filtrar(butter(1, p["pre_hp"], "highpass", fs=taxa, output="sos"), x).astype(np.float32)
    if p["boost"]:
        x = _filtrar(_biquad("pico", 720, p["boost"], 0.7, taxa), x).astype(np.float32)
    # válvulas com oversampling (4x no ganho alto, 2x no resto)
    ov = 1 if rapido else (4 if p["ganho"] > 20 else 2)
    if ov > 1:
        x = resample_poly(x, ov, 1, axis=0).astype(np.float32)
    t4 = taxa * ov
    g_est = p["ganho"] ** (1 / p["est"])
    dc = butter(1, 25, "highpass", fs=t4, output="sos")
    lp = butter(1, 9000, fs=t4, output="sos")
    for k in range(p["est"]):
        x = _valvula(x, g_est * (1.4 if k == 0 else 1.0), p["assim"] * (1 if k % 2 == 0 else -0.7))
        x = sosfilt(dc, x, axis=0).astype(np.float32)
        if k < p["est"] - 1:
            x = sosfilt(lp, x, axis=0).astype(np.float32)
    if ov > 1:
        x = resample_poly(x, 1, ov, axis=0).astype(np.float32)
    # EQ do amp
    x = _filtrar(_biquad("graves", 110, p["grave"], 0.7, taxa), x).astype(np.float32)
    x = _filtrar(_biquad("pico", 650, p["medio"], 0.8, taxa), x).astype(np.float32)
    x = _filtrar(_biquad("agudos", 3000, p["agudo"], 0.7, taxa), x).astype(np.float32)
    x = _filtrar(_biquad("pico", 4800, p["pres"], 1.2, taxa), x).astype(np.float32)
    # caixa
    ir = caixa_ir(p["caixa"], taxa)
    x = np.stack([fftconvolve(x[:, c], ir)[: len(x)] for c in range(2)], axis=1).astype(np.float32)
    # sala (nível fixo: não depende do trecho)
    if p["sala"] and not rapido:
        s = _ir_sala(taxa)
        mol = np.stack([fftconvolve(x[:, c], s[:, c])[: len(x)] for c in range(2)], axis=1)
        x = x + np.float32(p["sala"] * 0.5) * mol.astype(np.float32)
    # noise gate (pelo nível do DI, com abertura rápida e fechamento suave)
    if envelope_in is not None:
        lim = 10 ** (p["gate"] / 20) * 0.5
        alvo = np.clip((envelope_in - lim) / lim, 0, 1)
        alvo = sosfilt(butter(1, 30, fs=taxa, output="sos"), alvo)
        x *= np.clip(alvo, 0, 1).astype(np.float32)[:, None]
    if ganho_saida is not None:
        return (x * np.float32(ganho_saida)).astype(np.float32)
    return (x / (np.abs(x).max() + 1e-9) * 0.9).astype(np.float32)


PICO_ENTRADA_FIXO = 1.2      # nível de referência do DI (acordes somam mais e "empurram" o amp, como no real)
_GANHO_FIXO: dict = {}


def ganho_fixo(preset: str, taxa: int) -> float:
    """Ganho de saída de cada preset, medido uma vez num riff de referência do próprio
    sampler: todos os blocos da música saem no mesmo nível sem precisar do áudio inteiro."""
    chave = (preset, taxa)
    if chave not in _GANHO_FIXO:
        from . import sampler_guitarra as sg
        from .sintetizador import NotaAudio
        ref = []
        for k, (corda, alt) in enumerate(((6, 40), (5, 47), (4, 52))):      # power chord de Mi
            ref.append(NotaAudio(0.0, 0.9, alt, 118, corda=corda))
        for k, alt in enumerate((64, 67, 69, 71, 72, 74)):
            ref.append(NotaAudio(1.0 + 0.2 * k, 0.2, alt, 110, corda=1 if alt >= 64 else 2))
        di = sg.render_di(ref, 2.4, taxa, dobrar=True, cauda=0.3)
        pico = float(np.abs(processar(di, preset, taxa, pico_entrada=PICO_ENTRADA_FIXO, ganho_saida=1.0)).max())
        _GANHO_FIXO[chave] = 1.0 / (pico + 1e-9)
    return _GANHO_FIXO[chave]


@functools.lru_cache(maxsize=512)
def nivel_nota(preset: str, altura: int, taxa: int) -> float:
    """Volume percebido de UMA nota (intensidade 100) depois do amp. O amp e a caixa
    deixam umas alturas bem mais altas que outras (no high gain, até 8 dB); com esta
    medida cada nota da música é corrigida para o mesmo volume."""
    from . import sampler_guitarra as sg
    from .sintetizador import NotaAudio
    corda = 6 if altura < 45 else 5 if altura < 50 else 4 if altura < 55 else 3 if altura < 59 else 2 if altura < 64 else 1
    di = sg.render_di([NotaAudio(0.0, 0.6, int(altura), 100, corda=corda)], 0.7, taxa, dobrar=True, cauda=0.0)
    out = processar(di, preset, taxa, pico_entrada=PICO_ENTRADA_FIXO, ganho_saida=1.0) if preset != "di" else di
    return nivel_percebido(out[: int(0.35 * taxa)], taxa)


def correcao_altura(preset: str, altura: int, taxa: int) -> float:
    """Ganho (linear) que leva a nota ao volume de referência (Lá 3), limitado a ±10 dB."""
    ref = nivel_nota(preset, 57, taxa)
    db = 20 * np.log10(ref / max(nivel_nota(preset, int(altura), taxa), 1e-9))
    return float(10 ** (max(-10.0, min(10.0, db)) / 20))


def processar_bloco(di: np.ndarray, ini: int, fim: int, preset: str, taxa: int, saida: np.ndarray,
                    pico_saida: float = 0.6, contexto_s: float = 0.8, ganho: float = None) -> None:
    """Passa pelo amp só o trecho [ini, fim) do DI (com contexto antes) e grava em `saida`."""
    a = max(0, ini - int(contexto_s * taxa))
    g = ganho if ganho is not None else ganho_fixo(preset, taxa) * pico_saida
    pedaco = processar(di[a:fim], preset, taxa, pico_entrada=PICO_ENTRADA_FIXO, ganho_saida=g)
    saida[ini:fim] = np.clip(pedaco[ini - a:], -1, 1)


def processar_em_blocos(di: np.ndarray, preset: str, taxa: int, pico_saida: float = 0.6,
                        bloco_s: float = 10.0, contexto_s: float = 0.8, progresso=None) -> np.ndarray:
    """Amp na música inteira sem estourar a memória: processa em blocos de ~10 s
    (com 0,8 s de contexto antes, para filtros, caixa e sala emendarem certinho).
    `progresso(amostras_prontas, saida)` é chamado a cada bloco: dá para tocar o
    começo da música antes de o fim ficar pronto."""
    n = len(di)
    saida = np.zeros((n, 2), np.float32)
    if n == 0:
        return saida
    pico_in = float(np.abs(di).max()) + 1e-9
    # mede o nível de saída no trecho mais forte, uma vez só, para todos os blocos
    i_max = int(np.abs(di).max(axis=1).argmax())
    a, b = max(0, i_max - int(1.5 * taxa)), min(n, i_max + int(1.5 * taxa))
    teste = processar(di[a:b], preset, taxa, pico_entrada=pico_in, ganho_saida=1.0)
    ganho = pico_saida / (float(np.abs(teste).max()) + 1e-9)
    bloco, ctx = int(bloco_s * taxa), int(contexto_s * taxa)
    for ini in range(0, n, bloco):
        fim = min(n, ini + bloco)
        a = max(0, ini - ctx)
        pedaco = processar(di[a:fim], preset, taxa, pico_entrada=pico_in, ganho_saida=ganho)
        saida[ini:fim] = np.clip(pedaco[ini - a:], -1, 1)
        if progresso:
            progresso(fim, saida)
        time.sleep(0)
    return saida
