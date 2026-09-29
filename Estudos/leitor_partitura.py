# -*- coding: utf-8 -*-
"""
Leitor de partituras/tablaturas para o ESTUDOS > Tempo.

Entradas:
  * MIDI (.mid/.midi)  -> leitura local, sem dependências externas.
  * PDF                -> leitura via API da Anthropic (visão), que devolve JSON
                          com corda/casa/figura de cada evento.

Saída: um objeto `Partitura` com compassos -> tempos -> grade de subdivisão,
pronto para desenhar, tocar e imprimir. Todas as posições são `Fraction`
em SEMÍNIMAS a partir do início da música (sem erro de arredondamento).

Regras de honestidade (iguais às do prompt de análise):
  * MIDI não traz corda/casa. A digitação é SUGERIDA por algoritmo e marcada
    como tal (`Partitura.digitacao_sugerida`).
  * Se a soma de um tempo não fechar, isso vira alerta no compasso; nada é
    forçado a caber.
"""
from __future__ import annotations

import base64
import functools
import json
import math
import os
import re
import struct
import urllib.request
from dataclasses import dataclass, field
from fractions import Fraction
from functools import reduce
from typing import Callable, List, Optional, Tuple

# ----------------------------------------------------------------------------
# Constantes
# ----------------------------------------------------------------------------
AFINACAO_PADRAO = [64, 59, 55, 50, 45, 40]      # 1ª..6ª corda (E4 B3 G3 D3 A2 E2)
NOMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
CASA_MAX = 24
MODELO_PDF = "claude-sonnet-5-5"                 # troque aqui se quiser outro modelo
PAGINAS_POR_LOTE = 2

# denominadores "musicais" usados para limpar arredondamento de ticks
_DENOMS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 20, 24, 28, 32, 48, 64]


def nome_nota(p: Optional[int]) -> str:
    if p is None:
        return "?"
    return f"{NOMES[p % 12]}{p // 12 - 1}"


def _lcm(a: int, b: int) -> int:
    return a * b // math.gcd(a, b)


# ----------------------------------------------------------------------------
# Modelo de dados
# ----------------------------------------------------------------------------
@dataclass
class Nota:
    inicio: Fraction                 # semínimas
    duracao: Fraction                # semínimas (quanto tempo SOA)
    altura: Optional[int]            # MIDI pitch
    corda: Optional[int] = None      # 1..6 (1 = mais aguda)
    casa: Optional[int] = None
    tecnica: str = ""
    velocidade: int = 90
    bend_semitons: float = 0.0

    @property
    def fim(self) -> Fraction:
        return self.inicio + self.duracao

    @property
    def nome(self) -> str:
        return nome_nota(self.altura)

    def rotulo(self) -> str:
        return str(self.casa) if self.casa is not None else self.nome


@dataclass
class Evento:
    """Um ataque (nota ou acorde), uma pausa ou uma ligadura (sustentação)."""
    inicio: Fraction
    notas: List[Nota] = field(default_factory=list)
    duracao_notada: Optional[Fraction] = None   # vem do PDF; no MIDI é None
    pausa: bool = False
    ligadura: bool = False


@dataclass
class Tempo:
    indice: int                      # 1..n dentro do compasso
    inicio: Fraction
    duracao: Fraction                # semínimas
    grade: int = 1                   # em quantas partes o tempo é dividido
    descricao: str = ""
    quialtera: str = ""              # "" | "tercina" | "quintina"...
    celulas: List[str] = field(default_factory=list)       # rótulo de cada parte
    celulas_corda: List[str] = field(default_factory=list)
    celulas_tecnica: List[str] = field(default_factory=list)
    ataques: List[Tuple[Fraction, List[Nota], Fraction]] = field(default_factory=list)
    # (offset dentro do tempo em fração do tempo, notas, valor notado em fração do tempo)
    grupos_quialtera: List[Tuple[Fraction, Fraction, int]] = field(default_factory=list)
    # (offset_ini, offset_fim, número mostrado)


@dataclass
class Compasso:
    numero: int
    num: int
    den: int
    inicio: Fraction
    bpm: float
    tempos: List[Tempo] = field(default_factory=list)
    alertas: List[str] = field(default_factory=list)
    legato_total: bool = False

    @property
    def duracao(self) -> Fraction:
        return Fraction(self.num * 4, self.den)

    @property
    def fim(self) -> Fraction:
        return self.inicio + self.duracao

    @property
    def dur_tempo(self) -> Fraction:
        return Fraction(4, self.den)

    @property
    def formula(self) -> str:
        return f"{self.num}/{self.den}"


@dataclass
class Partitura:
    titulo: str = ""
    fonte: str = ""                              # "midi" | "pdf"
    arquivo: str = ""
    notas: List[Nota] = field(default_factory=list)
    eventos: List[Evento] = field(default_factory=list)
    compassos: List[Compasso] = field(default_factory=list)
    mapa_bpm: List[Tuple[Fraction, float]] = field(default_factory=lambda: [(Fraction(0), 120.0)])
    afinacao: List[int] = field(default_factory=lambda: list(AFINACAO_PADRAO))
    digitacao_sugerida: bool = False
    avisos: List[str] = field(default_factory=list)
    faixas: List[str] = field(default_factory=list)
    faixa_idx: int = 0
    _dados_midi: object = None                  # para trocar de faixa sem reler

    # ---- tempo musical <-> segundos (no BPM original da partitura) ----
    @property
    def bpm_inicial(self) -> float:
        return float(self.mapa_bpm[0][1]) if self.mapa_bpm else 120.0

    @property
    def fim(self) -> Fraction:
        return self.compassos[-1].fim if self.compassos else Fraction(0)

    def segundos(self, q: Fraction) -> float:
        t = 0.0
        mapa = self.mapa_bpm
        for i, (q0, bpm) in enumerate(mapa):
            q1 = mapa[i + 1][0] if i + 1 < len(mapa) else None
            if q1 is not None and q >= q1:
                t += float(q1 - q0) * 60.0 / bpm
            else:
                t += float(q - q0) * 60.0 / bpm
                break
        return t

    def q_de_segundos(self, s: float) -> Fraction:
        t = 0.0
        mapa = self.mapa_bpm
        for i, (q0, bpm) in enumerate(mapa):
            q1 = mapa[i + 1][0] if i + 1 < len(mapa) else None
            dt = float(q1 - q0) * 60.0 / bpm if q1 is not None else None
            if dt is None or t + dt > s:
                return q0 + Fraction(s - t).limit_denominator(100000) * Fraction(bpm).limit_denominator(1000) / 60
            t += dt
        return Fraction(0)

    def bpm_em(self, q: Fraction) -> float:
        bpm = self.bpm_inicial
        for q0, b in self.mapa_bpm:
            if q0 <= q:
                bpm = b
        return bpm

    def compasso_em(self, q: Fraction) -> Optional[int]:
        for i, c in enumerate(self.compassos):
            if c.inicio <= q < c.fim:
                return i
        return None


# ----------------------------------------------------------------------------
# 1) Leitura de MIDI (Standard MIDI File, formato 0 e 1)
# ----------------------------------------------------------------------------
def _vlq(d: bytes, i: int) -> Tuple[int, int]:
    v = 0
    while True:
        b = d[i]
        i += 1
        v = (v << 7) | (b & 0x7F)
        if not b & 0x80:
            return v, i


def ler_midi_bruto(caminho: str) -> dict:
    with open(caminho, "rb") as f:
        d = f.read()
    if d[:4] != b"MThd":
        raise ValueError("Arquivo não é um MIDI válido (cabeçalho MThd ausente).")
    hlen = struct.unpack(">I", d[4:8])[0]
    fmt, ntrk, div = struct.unpack(">HHH", d[8:14])
    if div & 0x8000:
        raise ValueError("MIDI com divisão SMPTE não é suportado (precisa de PPQ).")
    ppq = div
    i = 8 + hlen
    faixas = []
    tempos, formulas = [], []
    for t in range(ntrk):
        while d[i:i + 4] != b"MTrk":          # pula blocos desconhecidos
            ln = struct.unpack(">I", d[i + 4:i + 8])[0]
            i += 8 + ln
            if i >= len(d):
                break
        ln = struct.unpack(">I", d[i + 4:i + 8])[0]
        j, fim = i + 8, i + 8 + ln
        i = fim
        tick, status = 0, 0
        nome, ev = "", []
        while j < fim:
            dt, j = _vlq(d, j)
            tick += dt
            b = d[j]
            if b == 0xFF:
                tipo = d[j + 1]
                ln2, j = _vlq(d, j + 2)
                dados = d[j:j + ln2]
                j += ln2
                if tipo == 0x51 and ln2 == 3:
                    tempos.append((tick, int.from_bytes(dados, "big")))
                elif tipo == 0x58 and ln2 >= 2:
                    formulas.append((tick, dados[0], 2 ** dados[1]))
                elif tipo == 0x03 and not nome:
                    nome = dados.decode("latin-1", "replace").strip()
                elif tipo == 0x2F:
                    break
                continue
            if b in (0xF0, 0xF7):
                ln2, j = _vlq(d, j + 1)
                j += ln2
                continue
            if b & 0x80:
                status = b
                j += 1
            tipo, canal = status & 0xF0, status & 0x0F
            if tipo in (0xC0, 0xD0):
                a = d[j]; j += 1
                ev.append((tick, tipo, canal, a, 0))
            else:
                a, c = d[j], d[j + 1]; j += 2
                ev.append((tick, tipo, canal, a, c))
        faixas.append({"nome": nome, "eventos": ev})
    return {"ppq": ppq, "formato": fmt, "faixas": faixas,
            "tempos": sorted(tempos), "formulas": sorted(formulas)}


def _limpar(q: Fraction, ppq: int) -> Fraction:
    """Encaixa a posição na fração musical mais simples compatível com o tick."""
    return _limpar_frac(q, ppq)


@functools.lru_cache(maxsize=65536)
def _limpar_tick(tick: int, ppq: int) -> Fraction:
    """Versão rápida, em inteiros: tick -> fração de semínima (com cache por tick)."""
    inteiro, resto = divmod(tick, ppq)
    tol2 = 3                                  # 1,5 tick, em meio-ticks
    for dn in _DENOMS:
        k = (2 * resto * dn + ppq) // (2 * ppq)       # round(resto*dn/ppq)
        if abs(2 * (resto * dn - k * ppq)) <= tol2 * dn:
            return inteiro + Fraction(k, dn)
    return inteiro + Fraction(resto, ppq).limit_denominator(64)


def _limpar_frac(q: Fraction, ppq: int) -> Fraction:
    inteiro = math.floor(q)
    frac = q - inteiro
    tol = max(Fraction(3, 2 * ppq), Fraction(1, 1000))
    for dn in _DENOMS:
        f = Fraction(round(frac * dn), dn)
        if abs(frac - f) <= tol:
            return inteiro + f
    return inteiro + frac.limit_denominator(64)


def _notas_da_faixa(bruto: dict, chave) -> List[Nota]:
    ppq = bruto["ppq"]
    idx_faixa, canal_alvo = chave
    ev = bruto["faixas"][idx_faixa]["eventos"]
    abertas, notas = {}, []
    bends = {}  # canal -> [(tick, semitons)]
    rng = {}    # canal -> alcance do pitch bend (RPN 0), padrão 2
    rpn = {}
    for tick, tipo, canal, a, c in ev:
        if canal == 9 or (canal_alvo is not None and canal != canal_alvo):
            continue
        if tipo == 0xB0:
            if a in (101, 100):
                rpn.setdefault(canal, [None, None])[0 if a == 101 else 1] = c
            elif a == 6 and rpn.get(canal) == [0, 0]:
                rng[canal] = c
        elif tipo == 0xE0:
            v = ((c << 7) | a) - 8192
            bends.setdefault(canal, []).append((tick, v / 8192.0 * rng.get(canal, 2)))
        elif tipo == 0x90 and c > 0:
            abertas.setdefault((canal, a), []).append((tick, c))
        elif tipo == 0x80 or (tipo == 0x90 and c == 0):
            fila = abertas.get((canal, a))
            if fila:
                t0, vel = fila.pop(0)
                notas.append((t0, tick, a, vel, canal))
    notas.sort()
    saida = []
    for t0, t1, p, vel, canal in notas:
        q0 = _limpar_tick(t0, ppq)
        q1 = _limpar_tick(t1, ppq)
        if q1 <= q0:
            q1 = q0 + Fraction(1, 16)
        bmax = 0.0
        for tb, s in bends.get(canal, []):
            if t0 <= tb < t1 and abs(s) > abs(bmax):
                bmax = s
        n = Nota(q0, q1 - q0, p, velocidade=vel, bend_semitons=bmax)
        if bmax >= 1.5:
            n.tecnica = "bend 1 tom"
        elif bmax >= 0.75:
            n.tecnica = "bend ½"
        elif bmax >= 0.3:
            n.tecnica = "bend ¼"
        saida.append(n)
    return saida


def _listar_faixas(bruto: dict) -> List[Tuple[str, Tuple[int, Optional[int]], int]]:
    """[(rótulo, chave, qtd_notas)] — por faixa (formato 1) ou por canal (formato 0)."""
    progs = {}
    for fx in bruto["faixas"]:
        for tick, tipo, canal, a, c in fx["eventos"]:
            if tipo == 0xC0:
                progs.setdefault(canal, a)
    out = []
    for i, fx in enumerate(bruto["faixas"]):
        canais = {}
        for tick, tipo, canal, a, c in fx["eventos"]:
            if tipo == 0x90 and c > 0 and canal != 9:
                canais[canal] = canais.get(canal, 0) + 1
        if not canais:
            continue
        if bruto["formato"] == 0 and len(canais) > 1:
            for ch, n in sorted(canais.items()):
                out.append((f"Canal {ch + 1}", (i, ch), n, progs.get(ch, 0)))
        else:
            ch0 = max(canais, key=canais.get)
            nome = fx["nome"] or f"Faixa {i + 1}"
            out.append((nome, (i, None), sum(canais.values()), progs.get(ch0, 0)))
    return out


def _faixa_padrao(lista) -> int:
    """Prefere guitarra (programas 24–31) ou nome com 'guit'/'gtr'; senão a com mais notas."""
    melhor, pont = 0, -1
    for k, (nome, chave, n, prog) in enumerate(lista):
        p = n
        if 24 <= prog <= 31:
            p += 100000
        if re.search(r"guit|gtr|viol", nome, re.I):
            p += 200000
        if p > pont:
            melhor, pont = k, p
    return melhor


def ler_midi(caminho: str, faixa: Optional[int] = None,
             afinacao: Optional[List[int]] = None) -> Partitura:
    bruto = ler_midi_bruto(caminho)
    lista = _listar_faixas(bruto)
    if not lista:
        raise ValueError("O MIDI não tem notas (fora a bateria).")
    k = _faixa_padrao(lista) if faixa is None else max(0, min(faixa, len(lista) - 1))
    ppq = bruto["ppq"]
    notas = _notas_da_faixa(bruto, lista[k][1])

    mapa = []
    for tick, uspq in bruto["tempos"]:
        q = _limpar_tick(tick, ppq)
        bpm = round(60_000_000 / uspq, 2)
        if mapa and mapa[-1][0] == q:
            mapa[-1] = (q, bpm)
        elif not mapa or mapa[-1][1] != bpm:
            mapa.append((q, bpm))
    if not mapa or mapa[0][0] != 0:
        mapa.insert(0, (Fraction(0), mapa[0][1] if mapa else 120.0))

    formulas = []
    for tick, num, den in bruto["formulas"]:
        q = _limpar_tick(tick, ppq)
        if formulas and formulas[-1][0] == q:
            formulas[-1] = (q, num, den)
        else:
            formulas.append((q, num, den))

    p = Partitura(
        titulo=os.path.splitext(os.path.basename(caminho))[0],
        fonte="midi", arquivo=caminho, notas=notas, mapa_bpm=mapa,
        afinacao=list(afinacao or AFINACAO_PADRAO), digitacao_sugerida=True,
        faixas=[f"{n} ({q} notas)" for n, _, q, _ in lista], faixa_idx=k,
        _dados_midi=bruto,
    )
    if not bruto["formulas"]:
        p.avisos.append("O MIDI não informa a fórmula de compasso; usei 4/4.")
    if not bruto["tempos"]:
        p.avisos.append("O MIDI não informa o andamento; usei 120 BPM.")
    p.avisos.append("MIDI não traz corda/casa: a digitação mostrada é SUGERIDA.")
    fim = max((n.fim for n in notas), default=Fraction(4))
    p.compassos = _montar_compassos(formulas, fim, p)
    limpeza = _proporcao_limpa(p.notas)
    # Encaixa cada ataque na grade musical mais simples que explica o tempo.
    # MIDI de editor (Guitar Pro, MuseScore) já vem exato e passa intacto,
    # inclusive quintinas/septinas; MIDI tocado ao vivo ou "humanizado" é corrigido.
    antes = {(n.inicio, n.altura) for n in p.notas}
    p.notas = quantizar(p.notas, p.compassos, exato=limpeza >= 0.97)
    movidas = sum(1 for n in p.notas if (n.inicio, n.altura) not in antes)
    if movidas > 0.03 * max(1, len(p.notas)):
        p.avisos.append(f"MIDI com tempo 'humano' ({limpeza:.0%} das notas na grade): "
                        f"{movidas} ataques foram encaixados na subdivisão mais próxima.")
        fim = max((n.fim for n in p.notas), default=Fraction(4))
        if fim > p.compassos[-1].fim:
            p.compassos = _montar_compassos(formulas, fim, p)
    sugerir_digitacao(p.notas, p.afinacao)
    p.eventos = _agrupar_eventos(p.notas)
    analisar(p)
    return p


_DENS_LIMPOS = {1, 2, 3, 4, 5, 6, 7, 8, 12, 16, 24}


def _proporcao_limpa(notas: List[Nota]) -> float:
    """Quanto das notas já cai numa grade musical (MIDI exportado de editor ~ 100%)."""
    if not notas:
        return 1.0
    ok = sum(1 for n in notas if (n.inicio - math.floor(n.inicio)).denominator in _DENS_LIMPOS)
    return ok / len(notas)


# grades candidatas por tempo, da mais simples para a mais fina
_GRADES_QUANT = (1, 2, 4, 3, 6, 8, 12)
_NIVEIS_QUANT = ((1,), (2,), (3, 4), (6, 8), (12,))
TOLERANCIA_QUANT = Fraction(1, 11)   # fração do tempo (~45 ms a 120 BPM)
# grades aceitas sem mexer quando os ataques já caem exatamente nelas
_GRADES_EXATAS = (1, 2, 3, 4, 5, 6, 7, 8, 12, 16, 24)


def quantizar(notas: List[Nota], compassos: List["Compasso"], exato: bool = True) -> List[Nota]:
    """Encaixa os ataques de cada tempo na grade mais simples que os explica.
    A duração que soa é preservada (desloca junto com o ataque)."""
    tempos = []                      # (inicio, dur) de todos os tempos da música
    for c in compassos:
        for k in range(c.num):
            tempos.append((c.inicio + c.dur_tempo * k, c.dur_tempo))
    if not tempos:
        return notas
    inicios = [t[0] for t in tempos]

    def tempo_de(q):
        import bisect
        i = max(0, bisect.bisect_right(inicios, q) - 1)
        return i

    # agrupa por tempo, considerando que um ataque um pouco antes do tempo pertence a ele
    grupos: dict = {}
    for n in notas:
        i = tempo_de(n.inicio)
        b0, dt = tempos[i]
        if i + 1 < len(tempos) and (tempos[i + 1][0] - n.inicio) <= dt * TOLERANCIA_QUANT:
            i += 1
        grupos.setdefault(i, []).append(n)
    saida = []
    for i, ns in grupos.items():
        b0, dt = tempos[i]
        offs = [(n.inicio - b0) / dt for n in ns]
        escolhida = None
        for g in (_GRADES_EXATAS if exato else ()):   # MIDI de editor: respeita o exato
            if all((o * g).denominator == 1 for o in offs if 0 <= o < 1):
                escolhida = g
                break
        if escolhida is None:
            # Sobe de nível de complexidade até alguma grade explicar todos os ataques.
            # Dentro do mesmo nível (ex.: 3 contra 4) vence o menor erro MÉDIO: uma
            # tercina tocada um pouco torta ainda erra menos na grade de 3 que na de 4.
            escolhida = _GRADES_QUANT[-1]
            for nivel in _NIVEIS_QUANT:
                aceitas = []
                for g in nivel:
                    erros = [abs(float(o * g) - round(float(o * g))) / g for o in offs]
                    if max(erros) <= TOLERANCIA_QUANT:
                        aceitas.append((sum(erros) / len(erros), g))
                if aceitas:
                    escolhida = min(aceitas)[1]
                    break
        for n, o in zip(ns, offs):
            novo = b0 + Fraction(round(o * escolhida), escolhida) * dt
            desloc = novo - n.inicio
            fim = max(novo + Fraction(1, 32), n.fim + desloc)
            saida.append(Nota(novo, fim - novo, n.altura, n.corda, n.casa, n.tecnica,
                              n.velocidade, n.bend_semitons))
    # mesma nota duplicada no mesmo ataque (dobra de gravação) vira uma só
    vistos, limpas = set(), []
    for n in sorted(saida, key=lambda n: (n.inicio, n.altura or 0)):
        chave = (n.inicio, n.altura)
        if chave not in vistos:
            vistos.add(chave)
            limpas.append(n)
    return limpas


def trocar_faixa(p: Partitura, idx: int) -> Partitura:
    if p.fonte != "midi" or not p.arquivo:
        return p
    return ler_midi(p.arquivo, faixa=idx, afinacao=p.afinacao)


def _agrupar_eventos(notas: List[Nota]) -> List[Evento]:
    ev: dict = {}
    for n in notas:
        ev.setdefault(n.inicio, []).append(n)
    return [Evento(q, sorted(ns, key=lambda n: (n.corda or 9))) for q, ns in sorted(ev.items())]


def _montar_compassos(formulas, fim: Fraction, p: Partitura) -> List[Compasso]:
    formulas = sorted(formulas) or [(Fraction(0), 4, 4)]
    if formulas[0][0] != 0:
        formulas.insert(0, (Fraction(0), 4, 4))
    comps, q, num, den, k = [], Fraction(0), 4, 4, 0
    while q < fim or not comps:
        while k < len(formulas) and formulas[k][0] <= q:
            _, num, den = formulas[k]
            k += 1
        c = Compasso(len(comps) + 1, num, den, q, p.bpm_em(q))
        comps.append(c)
        q = c.fim
        if len(comps) > 5000:
            break
    return comps


# ----------------------------------------------------------------------------
# 2) Digitação sugerida (MIDI) — Viterbi minimizando o deslocamento da mão
# ----------------------------------------------------------------------------
def _candidatos(alturas: List[int], afin: List[int]) -> List[List[Tuple[int, int]]]:
    alturas = sorted(alturas, reverse=True)
    res: List[List[Tuple[int, int]]] = []

    def rec(i, usadas, atual):
        if len(res) > 200:
            return
        if i == len(alturas):
            casas = [c for _, c in atual if c > 0]
            if not casas or max(casas) - min(casas) <= 4:
                res.append(list(atual))
            return
        for s in range(len(afin)):
            if s in usadas:
                continue
            casa = alturas[i] - afin[s]
            if 0 <= casa <= CASA_MAX:
                # corda mais grave só depois das mais agudas (evita cruzamentos)
                if atual and s <= atual[-1][0]:
                    continue
                atual.append((s, casa))
                usadas.add(s)
                rec(i + 1, usadas, atual)
                usadas.discard(s)
                atual.pop()

    rec(0, set(), [])
    return res


def _centro(cand, anterior):
    casas = [c for _, c in cand if c > 0]
    return sum(casas) / len(casas) if casas else anterior


def sugerir_digitacao(notas: List[Nota], afin: List[int]) -> None:
    grupos: dict = {}
    for n in notas:
        if n.corda is None:
            grupos.setdefault(n.inicio, []).append(n)
    ordem = sorted(grupos)
    if not ordem:
        return
    camadas = []
    for q in ordem:
        ns = sorted(grupos[q], key=lambda n: -(n.altura or 0))
        # acorde maior que 6 notas: fica só com as 6 mais agudas
        ns_val = [n for n in ns if n.altura is not None][:len(afin)]
        cands = _candidatos([n.altura for n in ns_val], afin) if ns_val else []
        if not cands and ns_val:           # tenta sem limite de abertura
            cands = [[(s, n.altura - afin[s])] for n in ns_val[:1]
                     for s in range(len(afin)) if 0 <= n.altura - afin[s] <= CASA_MAX]
        camadas.append((ns_val, cands[:40]))

    INF = float("inf")
    custos, volta = [], []
    for li, (ns, cands) in enumerate(camadas):
        cc, vv = [], []
        for cand in cands:
            casas = [c for _, c in cand if c > 0]
            proprio = (max(casas) - min(casas) if casas else 0) * 0.6 + \
                      (sum(casas) / len(casas) if casas else 0) * 0.04
            if li == 0 or not custos or not custos[-1]:
                cc.append(proprio + _centro(cand, 3) * 0.05)
                vv.append(-1)
                continue
            melhor, arg = INF, -1
            for pj, pc in enumerate(camadas[li - 1][1]):
                d = abs(_centro(cand, _centro(pc, 3)) - _centro(pc, 3))
                v = custos[-1][pj] + d + proprio
                if v < melhor:
                    melhor, arg = v, pj
            cc.append(melhor)
            vv.append(arg)
        custos.append(cc)
        volta.append(vv)

    # reconstrói
    escolha = [None] * len(camadas)
    li = len(camadas) - 1
    while li >= 0 and not custos[li]:
        li -= 1
    if li < 0:
        return
    j = min(range(len(custos[li])), key=lambda k: custos[li][k])
    while li >= 0:
        escolha[li] = j
        j = volta[li][j] if custos[li] else -1
        li -= 1
        while li >= 0 and not custos[li]:
            li -= 1
        if j == -1 and li >= 0 and custos[li]:
            j = min(range(len(custos[li])), key=lambda k: custos[li][k])
    for (ns, cands), e in zip(camadas, escolha):
        if e is None or not cands:
            continue
        cand = cands[e]
        for n, (s, casa) in zip(ns, cand):
            n.corda, n.casa = s + 1, casa


# ----------------------------------------------------------------------------
# 3) Análise rítmica: compasso -> tempos -> grade
# ----------------------------------------------------------------------------
_BASES = [(Fraction(1), "semibreve"), (Fraction(1, 2), "mínima"),
          (Fraction(1, 4), "semínima"), (Fraction(1, 8), "colcheia"),
          (Fraction(1, 16), "semicolcheia"), (Fraction(1, 32), "fusa"),
          (Fraction(1, 64), "semifusa")]
_QUIAL = {Fraction(2, 3): "tercina", Fraction(4, 5): "quintina",
          Fraction(4, 7): "septina",
          Fraction(8, 9): "nonina"}
NIVEL_BARRAS = {"colcheia": 1, "semicolcheia": 2, "fusa": 3, "semifusa": 4}


def nome_figura(valor_semibreve: Fraction) -> Tuple[str, int, str]:
    """-> (nome, nº de barras, tipo de quiáltera ou '')."""
    v = valor_semibreve
    for base, nome in _BASES:
        if v == base:
            return nome, NIVEL_BARRAS.get(nome, 0), ""
        if v == base * Fraction(3, 2):
            return nome + " pontuada", NIVEL_BARRAS.get(nome, 0), ""
        if v == base * Fraction(7, 4):
            return nome + " duplamente pontuada", NIVEL_BARRAS.get(nome, 0), ""
    for base, nome in _BASES:
        for r, q in _QUIAL.items():
            if v == base * r:
                return f"{nome} de {q}", NIVEL_BARRAS.get(nome, 0), q
    return f"valor {v} de semibreve", 3, "irregular"


def _figuras_simples() -> List[Fraction]:
    vals = set()
    for base, _ in _BASES:
        vals.add(base)
        vals.add(base * Fraction(3, 2))
        vals.add(base * Fraction(2, 3))
    return sorted(vals, reverse=True)


_SIMPLES = _figuras_simples()


def nome_figura_composta(valor_semibreve: Fraction) -> Tuple[str, int, str]:
    """Como nome_figura, mas um valor que não é uma figura só vira figuras ligadas
    (ex.: 5/6 do tempo = semínima de tercina ligada a semicolcheia de tercina)."""
    nome, niv, q = nome_figura(valor_semibreve)
    if not nome.startswith("valor "):
        return nome, niv, q
    resto, partes = valor_semibreve, []
    for v in _SIMPLES:
        while v <= resto and len(partes) < 4:
            partes.append(v)
            resto -= v
        if resto == 0:
            break
    if resto != 0 or not partes:
        return nome, niv, q
    nomes = [nome_figura(v) for v in partes]
    return " ligada a ".join(n for n, _, _ in nomes), nomes[0][1], nomes[0][2]


def _plural(nome: str, n: int) -> str:
    if n == 1:
        return nome
    partes = nome.split(" ")
    partes[0] += "s"
    if len(partes) > 1 and partes[1].startswith("pontuada"):
        partes[1] = partes[1] + "s"
    if len(partes) > 1 and partes[1] == "duplamente":
        partes[2] += "s"
    return f"{n} " + " ".join(partes)


def analisar(p: Partitura) -> None:
    """Preenche compasso.tempos com grade, descrição, células e alertas."""
    import bisect
    eventos = p.eventos
    ataques = sorted((e for e in eventos if e.notas and not e.pausa), key=lambda e: e.inicio)
    ini_ataques = [e.inicio for e in ataques]
    especiais = sorted((e for e in eventos if e.pausa or e.ligadura), key=lambda e: e.inicio)
    ini_especiais = [e.inicio for e in especiais]
    todas = sorted(p.notas, key=lambda n: n.inicio)
    ini_notas = [n.inicio for n in todas]
    dur_max = max((n.duracao for n in todas), default=Fraction(0))

    def notas_soando(b0, b1):
        """Só as notas que se sobrepõem a [b0, b1) — busca binária, não a música inteira."""
        lo = bisect.bisect_left(ini_notas, b0 - dur_max)
        hi = bisect.bisect_left(ini_notas, b1)
        return [n for n in todas[lo:hi] if n.fim > b0]

    for c in p.compassos:
        c.tempos = []
        dt = c.dur_tempo
        for t in range(c.num):
            b0 = c.inicio + dt * t
            b1 = b0 + dt
            tp = Tempo(t + 1, b0, dt)
            i0 = bisect.bisect_left(ini_ataques, b0)
            i1 = bisect.bisect_left(ini_ataques, b1)
            na = ataques[i0:i1]
            # próximo ataque (para o valor notado da última nota)
            onsets = [e.inicio for e in na]
            prox = ini_ataques[i1:i1 + 1]
            locais = notas_soando(b0, b1)
            esp = especiais[bisect.bisect_left(ini_especiais, b0):bisect.bisect_left(ini_especiais, b1)]
            desc = []
            # início do tempo sem ataque: continuação ou pausa
            if not onsets or onsets[0] > b0:
                primeiro = onsets[0] if onsets else b1
                soando = any(n.inicio < b0 < n.fim for n in locais)
                ligado = any(e.ligadura and e.inicio < primeiro for e in esp)
                fig = nome_figura_composta((primeiro - b0) / 4)[0]
                desc.append(("continua" if (soando or ligado) else "pausa de " + fig))
            for k, e in enumerate(na):
                if e.duracao_notada is not None:
                    alvo = e.inicio + e.duracao_notada
                else:
                    alvo = onsets[k + 1] if k + 1 < len(na) else (prox[0] if prox else max(n.fim for n in e.notas))
                valor = min(alvo, b1) - e.inicio
                if valor <= 0:
                    valor = min(Fraction(1, 32), b1 - e.inicio)
                tp.ataques.append(((e.inicio - b0) / dt, e.notas, valor / dt))
                desc.append(nome_figura_composta(valor / 4)[0])
                # pausa entre o fim notado (PDF) e o próximo ataque
                if e.duracao_notada is not None:
                    fim_n = e.inicio + e.duracao_notada
                    prox_on = onsets[k + 1] if k + 1 < len(na) else b1
                    if fim_n < prox_on and fim_n < b1:
                        desc.append("pausa de " + nome_figura_composta((min(prox_on, b1) - fim_n) / 4)[0])
            # grade = mmc dos denominadores de ataques e fins dentro do tempo
            pts = [(x - b0) / dt for x in onsets]
            if p.fonte != "midi":
                # no PDF o fim notado define a grade; no MIDI o fim é só o quanto a nota
                # soa (gate) e criaria subdivisões falsas
                pts += [(n.fim - b0) / dt for e in na for n in e.notas if n.fim < b1]
            pts += [(e.inicio - b0) / dt for e in esp]
            grade = reduce(_lcm, [f.denominator for f in pts], 1)
            if grade > 48:
                grade = 48
            tp.grade = grade
            impar = grade
            while impar % 2 == 0 and impar > 1:
                impar //= 2
            tp.quialtera = {1: "", 3: "tercina", 5: "quintina", 7: "septina", 9: "nonina"}.get(impar, "quiáltera")
            tp.grupos_quialtera = _grupos_quialtera(tp.ataques, dt)
            tp.descricao = _compactar(desc)
            _celulas(tp, locais, b0, b1)
            c.tempos.append(tp)
        _conferir_soma(c, eventos)


def _grupos_quialtera(ataques, dt) -> List[Tuple[Fraction, Fraction, int]]:
    grupos, atual = [], []
    for off, notas, val in ataques + [(None, None, None)]:
        eh = off is not None and nome_figura(val * dt / 4)[2] != ""
        if eh:
            atual.append((off, val))
            continue
        if atual:
            ini = atual[0][0]
            fim = atual[-1][0] + atual[-1][1]
            unidade = min(v for _, v in atual)
            numero = round((fim - ini) / unidade)
            # 6 = 3+3 quando todos os valores são o dobro da menor unidade
            if all(v == unidade * 2 for _, v in atual):
                numero = round((fim - ini) / (unidade * 2))
            grupos.append((ini, fim, max(numero, len(atual) if numero < 2 else numero)))
            atual = []
    return grupos


def _compactar(desc: List[str]) -> str:
    out, i = [], 0
    while i < len(desc):
        j = i
        while j + 1 < len(desc) and desc[j + 1] == desc[i]:
            j += 1
        n = j - i + 1
        out.append(_plural(desc[i], n) if not desc[i].startswith(("pausa", "continua")) else
                   (desc[i] if n == 1 else f"{n}× {desc[i]}"))
        i = j + 1
    return " + ".join(out) if out else "pausa"


def _celulas(tp: Tempo, todas: List[Nota], b0: Fraction, b1: Fraction) -> None:
    n = tp.grade
    tp.celulas, tp.celulas_corda, tp.celulas_tecnica = [], [], []
    por_off = {off: notas for off, notas, _ in tp.ataques}
    for k in range(n):
        off = Fraction(k, n)
        pos = b0 + off * tp.duracao
        if off in por_off:
            ns = por_off[off]
            tp.celulas.append("/".join(x.rotulo() for x in ns))
            tp.celulas_corda.append("/".join(str(x.corda) if x.corda else "?" for x in ns))
            tp.celulas_tecnica.append(", ".join(sorted({x.tecnica for x in ns if x.tecnica})))
        else:
            soa = any(x.inicio < pos < x.fim for x in todas)
            tp.celulas.append("—" if soa else "·")
            tp.celulas_corda.append("")
            tp.celulas_tecnica.append("")


def _conferir_soma(c: Compasso, eventos: List[Evento]) -> None:
    """Só faz sentido quando há duração NOTADA (PDF). No MIDI a soma fecha por construção."""
    ev = [e for e in eventos if e.duracao_notada is not None and c.inicio <= e.inicio < c.fim]
    if not ev:
        return
    total = sum((e.duracao_notada for e in ev), Fraction(0))
    # sequência: cada evento deve começar onde o anterior termina
    pos = c.inicio
    for e in sorted(ev, key=lambda e: e.inicio):
        if e.inicio != pos:
            t = int((e.inicio - c.inicio) / c.dur_tempo) + 1
            c.alertas.append(f"Tempo {t}: há um buraco/sobreposição antes deste evento "
                             f"(esperado {float((pos - c.inicio) / c.dur_tempo) + 1:.3g}, "
                             f"lido {float((e.inicio - c.inicio) / c.dur_tempo) + 1:.3g}). Leitura duvidosa.")
            break
        pos = e.inicio + e.duracao_notada
    if total != c.duracao:
        c.alertas.append(f"A soma das figuras dá {float(total / c.dur_tempo):.4g} tempos, "
                         f"mas o compasso {c.formula} tem {c.num}. Não forcei o encaixe.")


# ----------------------------------------------------------------------------
# 4) PDF -> JSON via API da Anthropic
# ----------------------------------------------------------------------------
PROMPT_PDF = """Você é um especialista em leitura rítmica de partituras e tablaturas de guitarra.
Leia o PDF e devolva SOMENTE um JSON (sem texto antes/depois, sem ```), no formato:

{
 "titulo": "string ou null",
 "bpm": número ou null,              // andamento indicado (♩ = N)
 "afinacao": ["E","A","D","G","B","E"] ou null,   // da 6ª para a 1ª corda
 "compassos": [
  {"numero": 1, "formula": "4/4", "bpm": null, "legato_total": false,
   "eventos": [
     {"tempo": 1, "inicio": "0", "duracao": "1/2", "pausa": false,
      "notas": [{"corda": 3, "casa": 7, "tecnica": "", "ligada_da_anterior": false}]}
   ],
   "duvidas": ["texto curto"]}
 ]
}

Regras:
- "tempo": em qual tempo do compasso o evento começa (1, 2, 3...).
- "inicio": onde começa DENTRO do tempo, como fração do tempo ("0", "1/2", "1/3", "3/4").
- "duracao": valor NOTADO da figura em tempos, como fração ("1" semínima em x/4,
  "1/2" colcheia, "1/4" semicolcheia, "1/8" fusa, "3/4" colcheia pontuada,
  "1/3" colcheia de tercina, "1/6" semicolcheia de tercina, "1/7" septina...).
  Pausas também são eventos: "pausa": true e "notas": [].
- Acorde = um evento com várias notas. Corda 1 = linha de cima da tablatura.
- Leitura rítmica: sem barra = semínima; 1 barra = colcheia; 2 = semicolcheia;
  3 = fusa; ponto = +50%; barra parcial = uma barra a mais; número sob colchete
  = quiáltera (3 no lugar de 2, 5/6/7 no lugar de 4...).
- Curva entre notas de mesma altura = ligadura de valor: marque a 2ª nota com
  "ligada_da_anterior": true (ela não é atacada de novo).
- Curva entre notas diferentes = hammer-on ou pull-off ("tecnica": "hammer"/"pull").
- Técnicas: "bend ½", "bend 1 tom", "release", "slide", "slide out", "hammer",
  "pull", "vibrato", "P.M.", "harmônico", "tapping", "dead note" (casa = "x" vira null).
- A soma das durações de cada compasso tem de fechar a fórmula. Se não fechar,
  NÃO invente: registre em "duvidas" qual tempo não fecha e as leituras possíveis.
- Nunca invente notas, casas ou durações. Se algo estiver ilegível, diga em "duvidas".
- Se o trecho indicar "Do not pick any strings" / tudo ligado, "legato_total": true.
- Barras de repetição e casas de 1ª/2ª vez: escreva os compassos na ordem em que
  aparecem no papel (sem expandir repetições) e cite a repetição em "duvidas".
"""


def _chave_api(chave: Optional[str]) -> str:
    if chave:
        return chave
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    for caminho in ("chave_anthropic.txt", os.path.join(os.path.dirname(__file__), "..", "chave_anthropic.txt")):
        if os.path.exists(caminho):
            with open(caminho, encoding="utf-8") as f:
                return f.read().strip()
    raise RuntimeError("Para ler PDF é preciso uma chave da API da Anthropic: defina a variável "
                       "ANTHROPIC_API_KEY ou crie o arquivo chave_anthropic.txt na pasta do programa.")


def _contar_paginas(dados: bytes) -> int:
    try:
        import io
        from pypdf import PdfReader
        return len(PdfReader(io.BytesIO(dados)).pages)
    except Exception:
        n = len(re.findall(rb"/Type\s*/Page[^s]", dados))
        return max(n, 1)


def _chamar_claude(chave: str, modelo: str, pdf_b64: str, texto: str) -> str:
    corpo = {
        "model": modelo,
        "max_tokens": 16000,
        "system": PROMPT_PDF,
        "messages": [{"role": "user", "content": [
            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64},
             "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": texto},
        ]}],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=json.dumps(corpo).encode("utf-8"),
        headers={"content-type": "application/json", "x-api-key": chave,
                 "anthropic-version": "2023-06-01"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Erro da API ({e.code}): {e.read().decode('utf-8', 'replace')[:400]}")
    return "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text")


def _json_da_resposta(txt: str) -> dict:
    txt = re.sub(r"```(?:json)?", "", txt).strip()
    i, j = txt.find("{"), txt.rfind("}")
    return json.loads(txt[i:j + 1])


_NOME_P_SEMITOM = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def _afinacao_de_nomes(nomes: List[str]) -> Optional[List[int]]:
    """['E','A','D','G','B','E'] (6ª->1ª) -> alturas MIDI 1ª->6ª, escolhendo oitavas próximas do padrão."""
    try:
        alts = []
        for k, nm in enumerate(nomes[::-1]):          # 1ª..6ª
            nm = nm.strip().replace("♯", "#").replace("♭", "b")
            s = _NOME_P_SEMITOM[nm[0].upper()] + (1 if "#" in nm else -1 if nm[1:2] == "b" else 0)
            ref = AFINACAO_PADRAO[k] if k < 6 else 40
            cands = [o * 12 + s % 12 for o in range(2, 8)]
            alts.append(min(cands, key=lambda x: abs(x - ref)))
        return alts
    except Exception:
        return None


def partitura_de_json(dados: dict, arquivo: str = "") -> Partitura:
    p = Partitura(titulo=dados.get("titulo") or os.path.splitext(os.path.basename(arquivo))[0],
                  fonte="pdf", arquivo=arquivo, digitacao_sugerida=False)
    if dados.get("afinacao"):
        a = _afinacao_de_nomes(dados["afinacao"])
        if a:
            p.afinacao = a
    bpm0 = float(dados.get("bpm") or 0) or None
    if not bpm0:
        bpm0 = 120.0
        p.avisos.append("A partitura não mostra o andamento; usei 120 BPM.")
    p.mapa_bpm = [(Fraction(0), bpm0)]
    q = Fraction(0)
    ultima_por_corda: dict = {}
    comps = sorted(dados.get("compassos", []), key=lambda c: c.get("numero", 0))
    for cj in comps:
        try:
            num, den = [int(x) for x in str(cj.get("formula", "4/4")).split("/")]
        except ValueError:
            num, den = 4, 4
        if cj.get("bpm"):
            b = float(cj["bpm"])
            if b != p.mapa_bpm[-1][1]:
                p.mapa_bpm.append((q, b))
        c = Compasso(len(p.compassos) + 1, num, den, q, p.bpm_em(q),
                     legato_total=bool(cj.get("legato_total")))
        c.alertas += [f"Dúvida de leitura: {d}" for d in cj.get("duvidas", []) if d]
        dt = c.dur_tempo
        for ej in cj.get("eventos", []):
            try:
                ini = q + (int(ej.get("tempo", 1)) - 1 + Fraction(str(ej.get("inicio", "0")))) * dt
                dur = Fraction(str(ej.get("duracao", "1"))) * dt
            except (ValueError, ZeroDivisionError):
                c.alertas.append(f"Evento ilegível ignorado: {ej}")
                continue
            if ej.get("pausa") or not ej.get("notas"):
                p.eventos.append(Evento(ini, [], dur, pausa=True))
                continue
            notas = []
            so_ligadas = True
            for nj in ej["notas"]:
                corda = nj.get("corda")
                casa = nj.get("casa")
                tec = nj.get("tecnica") or ""
                if casa in (None, "x", "X"):
                    tec = tec or "dead note"
                    casa = None
                if nj.get("ligada_da_anterior") and corda in ultima_por_corda:
                    ant = ultima_por_corda[corda]
                    ant.duracao = ini + dur - ant.inicio
                    continue
                so_ligadas = False
                alt = None
                if corda and casa is not None and 1 <= int(corda) <= len(p.afinacao):
                    alt = p.afinacao[int(corda) - 1] + int(casa)
                n = Nota(ini, dur, alt, int(corda) if corda else None,
                         int(casa) if casa is not None else None, tec)
                if "1 tom" in tec:
                    n.bend_semitons = 2.0
                elif "½" in tec or "1/2" in tec:
                    n.bend_semitons = 1.0
                notas.append(n)
                if corda:
                    ultima_por_corda[corda] = n
            if notas:
                p.notas += notas
                p.eventos.append(Evento(ini, notas, dur))
            elif so_ligadas:
                p.eventos.append(Evento(ini, [], dur, ligadura=True))
        p.compassos.append(c)
        q = c.fim
    if not p.compassos:
        raise ValueError("A leitura do PDF não retornou nenhum compasso.")
    p.eventos.sort(key=lambda e: e.inicio)
    for c in p.compassos:
        c.bpm = p.bpm_em(c.inicio)
    analisar(p)
    return p


def ler_pdf(caminho: str, progresso: Optional[Callable[[str], None]] = None,
            chave: Optional[str] = None, modelo: str = MODELO_PDF) -> Partitura:
    chave = _chave_api(chave)
    with open(caminho, "rb") as f:
        dados = f.read()
    b64 = base64.standard_b64encode(dados).decode("ascii")
    npag = _contar_paginas(dados)
    total = {"titulo": None, "bpm": None, "afinacao": None, "compassos": []}
    for a in range(1, npag + 1, PAGINAS_POR_LOTE):
        b = min(npag, a + PAGINAS_POR_LOTE - 1)
        if progresso:
            progresso(f"Lendo PDF com IA: páginas {a}–{b} de {npag}…")
        ult = total["compassos"][-1] if total["compassos"] else None
        ctx = (f"Analise SOMENTE as páginas {a} a {b} do PDF (de {npag}). " +
               (f"O último compasso já lido foi o nº {ult['numero']} (fórmula {ult.get('formula')}); "
                f"continue a numeração a partir do {ult['numero'] + 1}. " if ult else
                "Comece no compasso 1. ") +
               "Se não houver partitura nessas páginas, devolva \"compassos\": [].")
        txt = _chamar_claude(chave, modelo, b64, ctx)
        try:
            parte = _json_da_resposta(txt)
        except Exception:
            raise RuntimeError(f"A IA não devolveu um JSON válido para as páginas {a}–{b}.")
        for k in ("titulo", "bpm", "afinacao"):
            if total[k] is None and parte.get(k):
                total[k] = parte[k]
        total["compassos"] += parte.get("compassos", [])
    p = partitura_de_json(total, caminho)
    p.avisos.insert(0, "Leitura de PDF feita por IA: confira os compassos com alerta.")
    # guarda o JSON ao lado do PDF para não precisar reler (e para corrigir à mão)
    try:
        with open(os.path.splitext(caminho)[0] + ".tempo.json", "w", encoding="utf-8") as f:
            json.dump(total, f, ensure_ascii=False, indent=1)
    except OSError:
        pass
    return p


def carregar(caminho: str, progresso=None) -> Partitura:
    ext = os.path.splitext(caminho)[1].lower()
    if ext in (".mid", ".midi", ".kar"):
        return ler_midi(caminho)
    if ext == ".json":
        with open(caminho, encoding="utf-8") as f:
            return partitura_de_json(json.load(f), caminho)
    if ext == ".pdf":
        cache = os.path.splitext(caminho)[0] + ".tempo.json"
        if os.path.exists(cache) and os.path.getmtime(cache) >= os.path.getmtime(caminho):
            with open(cache, encoding="utf-8") as f:
                p = partitura_de_json(json.load(f), caminho)
            p.avisos.insert(0, "PDF já lido antes: usei a leitura salva (.tempo.json).")
            return p
        return ler_pdf(caminho, progresso)
    raise ValueError(f"Formato não suportado: {ext} (use .mid, .midi ou .pdf)")


# ----------------------------------------------------------------------------
# 5) Relatório em texto (mesmo formato do prompt de análise)
# ----------------------------------------------------------------------------
def relatorio_markdown(p: Partitura) -> str:
    L = [f"# {p.titulo}", "", f"Fonte: {p.fonte.upper()} — andamento inicial ♩ = {p.bpm_inicial:g}", ""]
    L += [f"> {a}" for a in p.avisos] + [""]
    for c in p.compassos:
        L.append(f"### Compasso {c.numero} ({c.formula}, ♩ = {c.bpm:g})")
        if c.legato_total:
            L.append("**Compasso inteiro em legato (não palhetar).**")
        for a in c.alertas:
            L.append(f"> ⚠ {a}")
        for t in c.tempos:
            L.append("")
            L.append(f"**Tempo {t.indice} — {t.descricao}**" + (f" ({t.quialtera})" if t.quialtera else ""))
            L.append("")
            n = len(t.celulas)
            L.append("| Parte | " + " | ".join(str(i + 1) for i in range(n)) + " |")
            L.append("|---" * (n + 1) + "|")
            L.append("| Nota | " + " | ".join(t.celulas) + " |")
            if any(t.celulas_corda):
                L.append("| Corda | " + " | ".join(t.celulas_corda) + " |")
            if any(t.celulas_tecnica):
                L.append("| Técnica | " + " | ".join(t.celulas_tecnica) + " |")
        L.append("")
    return "\n".join(L)
