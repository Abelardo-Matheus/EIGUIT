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

import atexit
import os
import threading
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
# Música inteira pré-renderizada: o play sai na hora, só recortando o trecho
# ----------------------------------------------------------------------------
CAUDA_COMPLETA = 1.5      # segundos de "rabo" depois da última nota


def renderizar_guitarra_completa(p, bpm: float, taxa: int = 44100, timbre: str = "sintetico",
                                 info: Optional[dict] = None, progresso=None, cancelado=None) -> np.ndarray:
    """Guitarra da música inteira (sem metrônomo) em float32 (n, 2), no BPM pedido.
    Com o sampler, o amp roda em blocos (memória baixa) e `progresso(prontas, buffer)`
    é chamado a cada bloco, para o começo da música já poder tocar."""
    fator = bpm / p.bpm_inicial
    s0 = p.segundos(Fraction(0))

    def seg(q):
        return (p.segundos(q) - s0) / fator

    dur = seg(p.fim) + CAUDA_COMPLETA
    notas = []
    for nt in p.notas:
        if nt.altura is None:
            continue
        t0 = seg(nt.inicio)
        notas.append(sint.NotaAudio(t0, seg(nt.fim) - t0, nt.altura, nt.velocidade,
                                    nt.bend_semitons, nt.tecnica, nt.corda))
    alvo = next((pr for tid, _, pr in sint.TIMBRES if tid == timbre), None)
    if isinstance(alvo, str) and alvo.startswith("amp:") and sint.sampler_disponivel()[0]:
        from . import amp_guitarra as amp
        from . import sampler_guitarra as sg
        if info is not None:
            info["backend"] = "sampler"
        preset = alvo[4:]
        n = max(1, int(round(dur * taxa)))
        saida = np.zeros((n, 2), np.float32)
        if preset != "di":
            amp.ganho_fixo(preset, taxa)                 # mede o nível uma vez (rápido)

        def ao_bloco(ini, fim, di):
            # DI pronto até `fim`: passa este bloco pelo amp e já libera para tocar
            if preset == "di":
                saida[ini:fim] = np.clip(di[ini:fim] * np.float32(0.6 / amp.PICO_ENTRADA_FIXO), -1, 1)
            else:
                amp.processar_bloco(di, ini, fim, preset, taxa, saida)
            if progresso:
                progresso(fim, saida)

        sg.render_di_em_blocos(notas, dur, taxa, dobrar=True, ao_bloco=ao_bloco, cancelado=cancelado)
        return saida
    buf, usado = sint.render_notas(notas, dur, taxa, timbre, loop=False, pico=0.6)
    if info is not None:
        info["backend"] = usado
    buf = buf.astype(np.float32, copy=False)
    if progresso:
        progresso(len(buf), buf)
    return buf


def montar_trecho(p, completo: np.ndarray, q_ini: Fraction, q_fim: Fraction, bpm: float,
                  taxa: int = 44100, canais: int = 2, metronomo: bool = True, guitarra: bool = True,
                  loop: bool = True, vol_met: float = 0.8, vol_gtr: float = 0.9,
                  subdivisao: bool = False) -> Tuple[np.ndarray, float]:
    """Recorta o trecho da guitarra já pronta e soma o metrônomo: leva milissegundos.
    No loop, o rabo das notas do fim entra no começo (emenda sem estalo)."""
    fator = bpm / p.bpm_inicial
    s0 = p.segundos(Fraction(0))
    t_ini = (p.segundos(q_ini) - s0) / fator
    t_fim = (p.segundos(q_fim) - s0) / fator
    i0, i1 = int(round(t_ini * taxa)), int(round(t_fim * taxa))
    n = max(1, i1 - i0)
    gtr = np.zeros((n, 2), np.float32)
    if guitarra and completo is not None:
        pedaco = completo[i0:i1]
        gtr[:len(pedaco)] = pedaco
        if loop:
            rabo = completo[i1:i1 + int(CAUDA_COMPLETA * taxa)]
            m = min(len(rabo), n)
            if m:
                # só o que ainda soa depois do fim do trecho (as notas de dentro dele)
                gtr[:m] += rabo[:m] * np.linspace(1, 0, m, dtype=np.float32)[:, None]
    met = np.zeros(n, np.float32)
    if metronomo:
        forte, fraco = _click(taxa, True), _click(taxa, False)
        sub = fraco * 0.35
        for c in p.compassos:
            if c.fim <= q_ini or c.inicio >= q_fim:
                continue
            for k in range(c.num):
                qb = c.inicio + c.dur_tempo * k
                if q_ini <= qb < q_fim:
                    _somar(met, forte if k == 0 else fraco,
                           int(round(((p.segundos(qb) - s0) / fator - t_ini) * taxa)), False)
                if subdivisao:
                    qm = qb + c.dur_tempo / 2
                    if q_ini <= qm < q_fim:
                        _somar(met, sub, int(round(((p.segundos(qm) - s0) / fator - t_ini) * taxa)), False)
    mix = np.clip(gtr * vol_gtr + met[:, None] * vol_met, -1, 1)
    out = (mix * 32000).astype(np.int16)
    if canais == 1:
        out = out.mean(axis=1).astype(np.int16)
    elif canais > 2:
        out = np.concatenate([out] + [out[:, :1]] * (canais - 2), axis=1)
    return np.ascontiguousarray(out), n / taxa


def cliques_do_trecho(p, q_ini: Fraction, q_fim: Fraction, bpm: float, taxa: int,
                      subdivisao: bool = False) -> list:
    """Posições (em amostras, a partir de q_ini) e tipo de cada batida do metrônomo."""
    fator = bpm / p.bpm_inicial
    s_ini = p.segundos(q_ini)
    saida = []
    for c in p.compassos:
        if c.fim <= q_ini or c.inicio >= q_fim:
            continue
        for k in range(c.num):
            qb = c.inicio + c.dur_tempo * k
            if q_ini <= qb < q_fim:
                saida.append((int(round((p.segundos(qb) - s_ini) / fator * taxa)), 0 if k == 0 else 1))
            if subdivisao:
                qm = qb + c.dur_tempo / 2
                if q_ini <= qm < q_fim:
                    saida.append((int(round((p.segundos(qm) - s_ini) / fator * taxa)), 2))
    return sorted(saida)


_CLIQUES: dict = {}


def metronomo_janela(cliques: list, i0: int, i1: int, taxa: int) -> np.ndarray:
    """Só o pedaço [i0, i1) do metrônomo (para tocar em pedaços sem montar tudo)."""
    if taxa not in _CLIQUES:
        forte, fraco = _click(taxa, True), _click(taxa, False)
        _CLIQUES[taxa] = (forte, fraco, fraco * 0.35)
    sons = _CLIQUES[taxa]
    out = np.zeros(i1 - i0, np.float32)
    maior = len(sons[0])
    import bisect
    k = bisect.bisect_left(cliques, (i0 - maior, -1))
    while k < len(cliques) and cliques[k][0] < i1:
        pos, tipo = cliques[k]
        som = sons[tipo]
        a, b = max(pos, i0), min(pos + len(som), i1)
        if a < b:
            out[a - i0:b - i0] += som[a - pos:b - pos]
        k += 1
    return out


_GRAVANDO = threading.Lock()
PARAR = threading.Event()          # ligado ao fechar o programa: os renders param no próximo bloco
_THREADS: list = []


def registrar_thread(th: threading.Thread) -> None:
    _THREADS.append(th)
    _THREADS[:] = [t for t in _THREADS if t.is_alive() or t is th]


def _encerrar_ao_sair():
    # Fechar o programa com um render/gravação em andamento derrubava o Python
    # (thread no meio do numpy/libsndfile). Pede para parar e espera um pouco.
    PARAR.set()
    for th in list(_THREADS):
        th.join(timeout=5)
    if _GRAVANDO.acquire(timeout=8):
        _GRAVANDO.release()


atexit.register(_encerrar_ao_sair)


def salvar_audio(caminho: str, buf: np.ndarray, taxa: int) -> None:
    import soundfile as sf
    with _GRAVANDO:
        tmp = caminho + ".tmp"
        sf.write(tmp, np.clip(buf, -1, 1), taxa, subtype="PCM_16", format="FLAC")
        os.replace(tmp, caminho)


def ler_audio(caminho: str, taxa: int) -> Optional[np.ndarray]:
    try:
        import soundfile as sf
        dados, fs = sf.read(caminho, dtype="float32", always_2d=True)
    except Exception:
        return None
    if fs != taxa or dados.shape[1] != 2:
        return None
    return dados


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
        self._stream = None       # tocando em pedaços enquanto o resto ainda é preparado

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

    def tocar_em_pedacos(self, obter, n_total: int, loop: bool, pos: float = 0.0,
                         pedaco_s: float = 3.0) -> None:
        """Toca um áudio que ainda está sendo preparado: `obter(i0, i1)` devolve o
        pedaço int16 (ou None se ainda não ficou pronto). Os pedaços entram em fila
        sem emenda; se o preparo atrasar, o relógio do cursor espera junto."""
        self._garantir()
        self.canal.stop()
        taxa, _ = self.formato()
        self.buf, self.som, self.loop = None, None, loop
        self.dur = n_total / taxa
        tam = max(1, int(pedaco_s * taxa))
        i = int(max(0.0, min(pos, self.dur - 0.01)) * taxa)
        self._stream = {"obter": obter, "n": n_total, "tam": tam, "prox": i, "taxa": taxa,
                        "faminto": None, "tocou": False}
        self._t0 = time.perf_counter() - pos
        self.tocando, self.pausado = True, False
        self._alimentar()

    def _alimentar(self):
        import pygame
        st = self._stream
        if st["prox"] >= st["n"]:
            if not self.loop:
                return
            st["prox"] = 0
        i0 = st["prox"]
        i1 = min(st["n"], i0 + st["tam"])
        pedaco = st["obter"](i0, i1)
        ocioso = not self.canal.get_busy()
        if pedaco is None:
            if ocioso and st["faminto"] is None and st["tocou"]:
                st["faminto"] = time.perf_counter()        # acabou o pronto: segura o cursor
            return
        som = pygame.sndarray.make_sound(np.ascontiguousarray(pedaco))
        if ocioso:
            self.canal.play(som)
            if st["faminto"] is not None:
                self._t0 += time.perf_counter() - st["faminto"]
                st["faminto"] = None
        elif self.canal.get_queue() is None:
            self.canal.queue(som)
        else:
            return
        st["tocou"] = True
        st["prox"] = i1

    def tocar(self, buf: np.ndarray, dur: float, loop: bool, pos: float = 0.0) -> None:
        import pygame
        self._garantir()
        self.canal.stop()
        self._stream = None
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
        if self.canal and self.tocando and not loop and self._stream is None:
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
        self._stream = None
        self.tocando = self.pausado = False

    def posicao(self) -> float:
        if not self.tocando:
            return 0.0
        agora = self._tp if self.pausado else time.perf_counter()
        if self._stream is not None and self._stream["faminto"] is not None:
            agora = self._stream["faminto"]
        t = agora - self._t0
        if self.loop and self.dur > 0:
            return t % self.dur
        return min(t, self.dur)

    def atualizar(self) -> bool:
        """Chame a cada quadro. Devolve False quando terminou (sem loop)."""
        if not self.tocando or self.pausado:
            return self.tocando
        if self._stream is not None:
            st = self._stream
            if not self.loop and st["prox"] >= st["n"] and not self.canal.get_busy():
                self.tocando = False
                self._stream = None
                return False
            self._alimentar()
            return True
        if self.loop:
            if self.canal.get_queue() is None and self.som is not None:
                self.canal.queue(self.som)
        elif time.perf_counter() - self._t0 >= self.dur + 0.05 and not self.canal.get_busy():
            self.tocando = False
        return self.tocando
