# -*- coding: utf-8 -*-
"""
Motor de áudio do ESTUDOS > Tempo.

* `renderizar()`  : gera (numpy int16) o trecho selecionado já no BPM escolhido,
                    com guitarra sintetizada (cordas dedilhadas, com bend) e
                    metrônomo (tempo 1 acentuado). No modo loop, o rabo das
                    notas que passa do fim volta para o começo (emenda sem estalo).
* `Reprodutor`    : toca no canal 60 do mixer do pygame (os pedais usam 62/63),
                    com play/pause, loop sem emenda (Channel.queue) e posição
                    do cursor em segundos.
"""
from __future__ import annotations

import time
from fractions import Fraction
from typing import Optional, Tuple

import numpy as np

try:
    from . import sintetizador as sint
except ImportError:                                   # rodando fora do pacote
    import sintetizador as sint                        # type: ignore

CANAL_TEMPO = 60


# ----------------------------------------------------------------------------
# Síntese
# ----------------------------------------------------------------------------
def _nota(f0: float, dur: float, taxa: int, vel: float, bend: float) -> np.ndarray:
    """Mantido por compatibilidade: a síntese agora mora em audio/sintetizador.py."""
    return sint.nota_sintetica(f0, dur, taxa, vel, bend)


def _click(taxa: int, forte: bool) -> np.ndarray:
    n = int(0.035 * taxa)
    t = np.arange(n, dtype=np.float32) / taxa
    f = 1650.0 if forte else 1100.0
    env = np.exp(-t / 0.007)
    ruido = np.random.default_rng(1).standard_normal(n).astype(np.float32) * np.exp(-t / 0.002) * 0.3
    return ((np.sin(2 * np.pi * f * t) * env + ruido) * (0.9 if forte else 0.6)).astype(np.float32)


def _somar(dest: np.ndarray, sinal: np.ndarray, i0: int, circular: bool) -> None:
    n = len(dest)
    if i0 >= n or len(sinal) == 0:
        return
    fim = i0 + len(sinal)
    if fim <= n:
        dest[i0:fim] += sinal
        return
    cabe = n - i0
    dest[i0:] += sinal[:cabe]
    if circular:
        resto = sinal[cabe:]
        while len(resto):
            m = min(len(resto), n)
            dest[:m] += resto[:m]
            resto = resto[m:]


def renderizar(p, q_ini: Fraction, q_fim: Fraction, bpm: float, taxa: int = 44100,
               canais: int = 2, metronomo: bool = True, guitarra: bool = True,
               loop: bool = True, vol_met: float = 0.8, vol_gtr: float = 0.9,
               subdivisao: bool = False, timbre: str = "sintetico",
               info: Optional[dict] = None) -> Tuple[np.ndarray, float]:
    """-> (buffer int16 [n] ou [n, canais], duração em segundos).
    `timbre`: id de audio.sintetizador.TIMBRES ("clean", "distorcao", ..., "sintetico").
    `info` (opcional) recebe {"backend": "soundfont" | "sintetico"}."""
    fator = bpm / p.bpm_inicial
    s0 = p.segundos(q_ini)

    def seg(q):
        return (p.segundos(q) - s0) / fator

    dur = seg(q_fim)
    n = max(1, int(round(dur * taxa)))
    gtr = np.zeros((n, 2), np.float32)
    met = np.zeros(n, np.float32)
    usado = "nenhum"
    if guitarra:
        notas = []
        for nt in p.notas:
            if nt.altura is None or not (q_ini <= nt.inicio < q_fim):
                continue
            t0 = seg(nt.inicio)
            notas.append(sint.NotaAudio(t0, seg(nt.fim) - t0, nt.altura, nt.velocidade,
                                        nt.bend_semitons, nt.tecnica, nt.corda))
        if notas:
            buf, usado = sint.render_notas(notas, dur, taxa, timbre, loop)
            gtr[:len(buf)] = buf[:n]
    if info is not None:
        info["backend"] = usado
    if metronomo:
        forte, fraco = _click(taxa, True), _click(taxa, False)
        sub = fraco * 0.35
        for c in p.compassos:
            if c.fim <= q_ini or c.inicio >= q_fim:
                continue
            for k in range(c.num):
                qb = c.inicio + c.dur_tempo * k
                if q_ini <= qb < q_fim:
                    _somar(met, forte if k == 0 else fraco, int(round(seg(qb) * taxa)), False)
                if subdivisao:
                    qm = qb + c.dur_tempo / 2
                    if q_ini <= qm < q_fim:
                        _somar(met, sub, int(round(seg(qm) * taxa)), False)
    mix = np.clip(gtr * vol_gtr + met[:, None] * vol_met, -1, 1)
    out = (mix * 32000).astype(np.int16)
    if canais == 1:
        out = out.mean(axis=1).astype(np.int16)
    elif canais > 2:
        out = np.concatenate([out] + [out[:, :1]] * (canais - 2), axis=1)
    return np.ascontiguousarray(out), n / taxa


# ----------------------------------------------------------------------------
# Reprodução (pygame)
# ----------------------------------------------------------------------------
class Reprodutor:
    def __init__(self, canal: int = CANAL_TEMPO):
        self.idx = canal
        self.canal = None
        self.som = None
        self.buf = None
        self.dur = 0.0
        self.loop = True
        self.tocando = False
        self.pausado = False
        self._t0 = 0.0
        self._tp = 0.0

    # -- mixer --
    @staticmethod
    def formato() -> Tuple[int, int]:
        import pygame
        if not pygame.mixer.get_init():
            pygame.mixer.init(44100, -16, 2, 512)
        taxa, _, can = pygame.mixer.get_init()
        return taxa, can

    def _garantir(self):
        import pygame
        self.formato()
        if pygame.mixer.get_num_channels() <= self.idx:
            pygame.mixer.set_num_channels(max(64, self.idx + 1))
        self.canal = pygame.mixer.Channel(self.idx)

    def tocar(self, buf: np.ndarray, dur: float, loop: bool, pos: float = 0.0) -> None:
        import pygame
        self._garantir()
        self.canal.stop()
        self.buf, self.dur, self.loop = buf, dur, loop
        self.som = pygame.sndarray.make_sound(buf)
        taxa, _ = self.formato()
        pos = max(0.0, min(pos, dur - 0.01)) if dur > 0.02 else 0.0
        i = int(pos * taxa)
        if i > 0:
            self.canal.play(pygame.sndarray.make_sound(np.ascontiguousarray(buf[i:])))
            if loop:
                self.canal.queue(self.som)
        else:
            self.canal.play(self.som)
            if loop:
                self.canal.queue(self.som)
        self._t0 = time.perf_counter() - pos
        self.tocando, self.pausado = True, False

    def trocar_loop(self, loop: bool) -> None:
        """Liga/desliga o loop sem parar o som."""
        self.loop = loop
        if self.canal and self.tocando and not loop:
            # esvazia a fila: pygame não tem 'unqueue', então reinicia do mesmo ponto
            pos = self.posicao()
            self.tocar(self.buf, self.dur, False, pos)

    def pausar(self) -> None:
        if self.canal and self.tocando and not self.pausado:
            self.canal.pause()
            self._tp = time.perf_counter()
            self.pausado = True

    def retomar(self) -> None:
        if self.canal and self.pausado:
            self.canal.unpause()
            self._t0 += time.perf_counter() - self._tp
            self.pausado = False

    def parar(self) -> None:
        if self.canal:
            self.canal.stop()
        self.tocando = self.pausado = False

    def posicao(self) -> float:
        if not self.tocando:
            return 0.0
        agora = self._tp if self.pausado else time.perf_counter()
        t = agora - self._t0
        if self.loop and self.dur > 0:
            return t % self.dur
        return min(t, self.dur)

    def atualizar(self) -> bool:
        """Chame a cada quadro. Devolve False quando terminou (sem loop)."""
        if not self.tocando or self.pausado:
            return self.tocando
        if self.loop:
            if self.canal.get_queue() is None and self.som is not None:
                self.canal.queue(self.som)
        elif time.perf_counter() - self._t0 >= self.dur + 0.05 and not self.canal.get_busy():
            self.tocando = False
        return self.tocando
