# -*- coding: utf-8 -*-
"""
ESTUDOS > Tempo  (cartão "Estudo de Tempo")

Abra um MIDI ou PDF (botão, ou arraste o arquivo para a janela). A música é
desenhada inteira: cada compasso separado em tempos, cada tempo em partes,
com a figura rítmica em cima e a tablatura embaixo; a barra colorida atrás
de cada casa mostra por quanto tempo a nota soa.

Controles
  clique na partitura ............... põe o risco vermelho ali (a música toca dali)
  segurar e arrastar ................ seleciona os compassos do loop (segurar parado = 1 compasso)
  Shift + clique .................... estende o loop até o compasso clicado
  botão direito / Esc ............... limpa a seleção (volta a tocar tudo)
  Espaço ............................ play / pause
  L / M / G / T ..................... loop / metrônomo / guitarra / timbre
  B ................................. biblioteca (partituras já abertas nesta conta)
  Ctrl + roda  /  Ctrl + / Ctrl - ... tamanho da tablatura (zoom)
  arrastar um .sf2/.sf3 .............. instala outro SoundFont (assets/audio/soundfonts/)
  + / -  (Shift = de 5 em 5) ........ BPM
  roda do mouse ..................... rolar (no painel de detalhes: para os lados)

Integração: a classe `EstudoTempo` segue o ciclo
    tratar_evento(ev) -> bool   atualizar()   desenhar(tela)   desativar()
Rodar sozinho:  python -m Estudos.estudo_tempo [arquivo.mid|.pdf]
"""
from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
from fractions import Fraction
from typing import List, Optional, Tuple

import numpy as np
import pygame

try:                                          # design system e tradução do EIGUIT (se existirem)
    from config.design_system import TEMA, ds
except Exception:
    TEMA = ds = None
try:
    from core.i18n import _t
except Exception:
    def _t(texto):
        return texto

if __package__ in (None, ""):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from Estudos import leitor_partitura as lp          # type: ignore
    from Estudos import biblioteca_partituras as bib_mod  # type: ignore
    from audio import motor_tempo as mt                  # type: ignore
    from audio import sintetizador as sint               # type: ignore
else:
    from . import leitor_partitura as lp
    from . import biblioteca_partituras as bib_mod
    try:
        from ..audio import motor_tempo as mt
        from ..audio import sintetizador as sint
    except (ImportError, ValueError):
        from audio import motor_tempo as mt              # type: ignore
        from audio import sintetizador as sint           # type: ignore

# ----------------------------------------------------------------------------
# Temas
# ----------------------------------------------------------------------------
TEMA_ESCURO = dict(
    fundo=(22, 24, 29), painel=(31, 34, 41), painel2=(40, 44, 53), borda=(58, 63, 75),
    linha=(105, 111, 124), barra=(200, 205, 215), texto=(232, 234, 238), fraco=(138, 145, 158),
    destaque=(255, 153, 51), sel=(44, 66, 104), foco=(120, 170, 255), alt=(27, 29, 35),
    sustain=(64, 128, 196), aviso=(245, 190, 60), cursor=(255, 76, 76), nota_bg=(22, 24, 29),
    botao=(46, 51, 62), botao_on=(255, 153, 51), botao_txt_on=(20, 20, 20), quialtera=(160, 200, 255),
)
TEMA_CLARO = dict(
    fundo=(255, 255, 255), painel=(255, 255, 255), painel2=(245, 245, 245), borda=(200, 200, 200),
    linha=(95, 95, 95), barra=(0, 0, 0), texto=(0, 0, 0), fraco=(100, 100, 100),
    destaque=(190, 80, 0), sel=(255, 255, 255), foco=(0, 0, 0), alt=(246, 246, 246),
    sustain=(178, 205, 236), aviso=(190, 110, 0), cursor=(0, 0, 0), nota_bg=(255, 255, 255),
    botao=(230, 230, 230), botao_on=(190, 80, 0), botao_txt_on=(255, 255, 255), quialtera=(0, 60, 160),
)

def _cor(v, reserva):
    try:
        if ds is not None and hasattr(ds, "rgb"):
            v = ds.rgb(v)
        v = tuple(int(c) for c in v)[:3]
        return v if len(v) == 3 else reserva
    except Exception:
        return reserva


def tema_eiguit() -> dict:
    """Cores do tema do EIGUIT (config.design_system.TEMA) no formato desta tela."""
    t = dict(TEMA_ESCURO)
    if TEMA is None:
        return t
    mapa = {"fundo": "fundo", "painel": "superficie", "painel2": "superficie_alt", "borda": "borda",
            "texto": "texto", "fraco": "texto_suave", "destaque": "acento", "aviso": "aviso",
            "foco": "ciano", "quialtera": "ciano", "botao_on": "acento", "botao_txt_on": "texto_sobre_cor",
            "botao": "superficie_alt", "nota_bg": "fundo", "linha": "texto_apagado", "barra": "texto",
            "cursor": "alerta", "sustain": "ciano"}
    for nosso, deles in mapa.items():
        if hasattr(TEMA, deles):
            t[nosso] = _cor(getattr(TEMA, deles), t[nosso])
    t["alt"] = tuple(min(255, int(c * 0.9 + t["painel"][i] * 0.1)) for i, c in enumerate(t["fundo"]))
    t["sel"] = tuple(int(t["fundo"][i] * 0.7 + t["destaque"][i] * 0.3) for i in range(3))
    return t


ABREV = {"bend 1 tom": "b1", "bend ½": "b½", "bend ¼": "b¼", "release": "r", "slide": "/",
         "slide out": "\\", "hammer": "h", "pull": "p", "vibrato": "~", "P.M.": "PM",
         "harmônico": "<>", "tapping": "T", "dead note": "x"}


class Fontes:
    def __init__(self, esc: float = 1.0):
        pygame.font.init()
        nome = "segoeui,arial,dejavusans,liberationsans"
        mono = "consolas,dejavusansmono,couriernew,liberationmono"
        s = lambda v: max(8, int(v * esc))
        self.casa = pygame.font.SysFont(nome, s(15), bold=True)
        self.peq = pygame.font.SysFont(nome, s(11))
        self.peq_b = pygame.font.SysFont(nome, s(11), bold=True)
        self.med = pygame.font.SysFont(nome, s(13))
        self.med_b = pygame.font.SysFont(nome, s(13), bold=True)
        self.grande = pygame.font.SysFont(nome, s(17), bold=True)
        self.titulo = pygame.font.SysFont(nome, s(24), bold=True)
        self.formula = pygame.font.SysFont(nome, s(19), bold=True)
        self.mono = pygame.font.SysFont(mono, s(13))
        self.mono_b = pygame.font.SysFont(mono, s(13), bold=True)
        # nem toda fonte tem o símbolo ♩; se não tiver, escreve "BPM"
        try:
            self.tem_seminima = self.peq_b.metrics("♩")[0] is not None
        except Exception:
            self.tem_seminima = False


def _txt(surf, fonte, texto, cor, pos, ancora="topleft"):
    img = fonte.render(str(texto), True, cor)
    r = img.get_rect(**{ancora: pos})
    surf.blit(img, r)
    return r


# ----------------------------------------------------------------------------
# Diagramação (serve para a tela e para a impressão)
# ----------------------------------------------------------------------------
# Papel claro no estilo Songsterr (fundo branco, números grandes e escuros)
TEMA_PAPEL = dict(
    TEMA_CLARO,
    fundo=(255, 255, 255), linha=(182, 186, 194), barra=(55, 58, 66), texto=(22, 24, 30),
    fraco=(128, 132, 142), destaque=(240, 108, 0), sel=(222, 234, 255), foco=(64, 124, 238),
    alt=(249, 250, 252), sustain=(205, 223, 247), aviso=(205, 118, 0), cursor=(240, 108, 0),
    nota_bg=(255, 255, 255), quialtera=(38, 88, 196), tocando=(240, 108, 0),
)


class Diagramacao:
    """Posição de cada compasso/tempo na tela. Layout no estilo Songsterr:
    tablatura em cima, figuras rítmicas com hastes para baixo logo abaixo dela
    e, por último, a contagem dos tempos."""

    def __init__(self, p: lp.Partitura, largura: int, esc: float = 1.0):
        self.p, self.esc, self.largura = p, esc, largura
        s = esc
        self.head = int(36 * s)            # número do compasso, BPM e o espaço dos bends/vibratos
        self.ls = int(15 * s)              # distância entre as cordas
        self.abaixo_tab = int(9 * s)
        self.ritmo = int(38 * s)           # hastes e barras
        self.baixo = int(30 * s)           # quiálteras + contagem
        self.gap = int(22 * s)
        self.alt_sist = self.head + 5 * self.ls + self.abaixo_tab + self.ritmo + self.baixo + self.gap
        self.sistemas: List[dict] = []
        self.onde: dict = {}
        medidas = []
        ant = None
        for i, c in enumerate(p.compassos):
            mostra_formula = ant is None or (c.num, c.den) != ant
            ant = (c.num, c.den)
            pad_l = int((16 + (26 if mostra_formula else 0)) * s)
            pad_r = int(8 * s)
            bws = []
            for t in c.tempos:
                g = min(t.grade, 16)
                bws.append(max(54, 18 * g) * s)
            medidas.append([i, pad_l, pad_r, bws, mostra_formula])
        linha, larg = [], 0
        linhas = []
        for m in medidas:
            w = m[1] + m[2] + sum(m[3])
            if linha and larg + w > largura:
                linhas.append(linha)
                linha, larg = [], 0
            linha.append(m)
            larg += w
        if linha:
            linhas.append(linha)
        for li, ln in enumerate(linhas):
            fixo = sum(m[1] + m[2] for m in ln)
            var = sum(sum(m[3]) for m in ln)
            ultima = li == len(linhas) - 1
            fator = (largura - fixo) / var if var else 1
            if ultima and fator > 1.35:
                fator = 1.0
            x = 0.0
            comps = []
            for m in ln:
                bws = [b * fator for b in m[3]]
                w = m[1] + m[2] + sum(bws)
                comps.append(dict(i=m[0], x=x, w=w, pad=m[1], bw=bws, formula=m[4]))
                self.onde[m[0]] = (li, len(comps) - 1)
                x += w
            c0, c1 = p.compassos[ln[0][0]], p.compassos[ln[-1][0]]
            self.sistemas.append(dict(y=li * self.alt_sist, comps=comps, q0=c0.inicio, q1=c1.fim))
        self.altura = len(self.sistemas) * self.alt_sist

    # --- geometria (relativa ao topo do sistema) ---
    def tab_y(self, corda: int) -> int:
        return self.head + (corda - 1) * self.ls

    @property
    def y_haste(self) -> int:              # onde as hastes começam (logo abaixo da 6ª corda)
        return self.head + 5 * self.ls + self.abaixo_tab

    @property
    def y_barra(self) -> int:              # linha das barras de colcheia/semicolcheia
        return self.y_haste + self.ritmo

    @property
    def y_contagem(self) -> int:
        return self.y_barra + int(14 * self.esc)

    @property
    def y_fim(self) -> int:                # fim da área desenhada do sistema
        return self.alt_sist - self.gap

    def x_de_q(self, q: Fraction, fim: bool = False) -> Tuple[int, float]:
        p = self.p
        if not p.compassos:
            return 0, 0.0
        i = p.compasso_em(q)
        if i is None:
            i = len(p.compassos) - 1
            q = p.compassos[i].fim
            fim = True
        c = p.compassos[i]
        if fim and q == c.inicio and i > 0:
            i -= 1
            c = p.compassos[i]
            q = c.fim
        si, k = self.onde[i]
        cl = self.sistemas[si]["comps"][k]
        rel = (q - c.inicio) / c.dur_tempo
        b = min(int(rel), len(cl["bw"]) - 1)
        off = float(rel - b)
        return si, cl["x"] + cl["pad"] + sum(cl["bw"][:b]) + off * cl["bw"][b]

    def q_em(self, x: float, y: float) -> Optional[Fraction]:
        """Posição na música (semínimas) no ponto (x, y) da partitura."""
        i = self.compasso_em(x, y)
        if i is None:
            return None
        si, k = self.onde[i]
        cl = self.sistemas[si]["comps"][k]
        c = self.p.compassos[i]
        rel = x - cl["x"] - cl["pad"]
        if rel <= 0:
            return c.inicio
        for b, bw in enumerate(cl["bw"]):
            if rel < bw or b == len(cl["bw"]) - 1:
                frac = Fraction(max(0.0, min(rel / bw, 0.999))).limit_denominator(96)
                return c.inicio + c.dur_tempo * (b + frac)
            rel -= bw
        return c.inicio

    def compasso_em(self, x: float, y: float) -> Optional[int]:
        si = int(y // self.alt_sist)
        if not 0 <= si < len(self.sistemas):
            return None
        if y - si * self.alt_sist > self.y_fim:
            return None
        for cl in self.sistemas[si]["comps"]:
            if cl["x"] <= x < cl["x"] + cl["w"]:
                return cl["i"]
        return None


def desenhar_sistema(surf, d: Diagramacao, si: int, ox: int, oy: int, T: dict, F: Fontes,
                     sel: Optional[Tuple[int, int]] = None, foco: Optional[int] = None,
                     q_atual: Optional[Fraction] = None, mostrar_duracao: bool = True) -> None:
    p, s = d.p, d.esc
    sist = d.sistemas[si]
    y_t0 = oy + d.tab_y(1)                 # 1ª corda
    y_t5 = oy + d.tab_y(6)                 # 6ª corda
    y_cont = oy + d.y_contagem
    x1s = ox + sist["comps"][-1]["x"] + sist["comps"][-1]["w"]
    grossa_barra = max(1, int(1.6 * s))

    for cl in sist["comps"]:
        c = p.compassos[cl["i"]]
        cx = ox + cl["x"]
        selecionado = sel and sel[0] <= cl["i"] <= sel[1]
        if selecionado:
            pygame.draw.rect(surf, T["sel"], (cx, oy + 2, cl["w"], d.y_fim - 2), border_radius=int(4 * s))
        else:
            bx = cx + cl["pad"]
            for k, bw in enumerate(cl["bw"]):
                if k % 2 == 1:
                    pygame.draw.rect(surf, T["alt"], (bx, y_t0 - 6 * s, bw, oy + d.y_barra - y_t0 + 10 * s))
                bx += bw
        # cabeçalho: número do compasso, BPM, alerta
        _txt(surf, F.peq_b, c.numero, T["fraco"], (cx + 3, oy + 3))
        if cl["i"] == 0 or c.bpm != p.compassos[cl["i"] - 1].bpm:
            _txt(surf, F.peq_b, f"♩ = {c.bpm:g}" if F.tem_seminima else f"BPM {c.bpm:g}", T["destaque"],
                 (cx + int(24 * s), oy + 3))
        if c.alertas:
            ax = cx + cl["w"] - int(16 * s)
            pygame.draw.polygon(surf, T["aviso"], [(ax, oy + 17 * s), (ax + 7 * s, oy + 4 * s), (ax + 14 * s, oy + 17 * s)])
            _txt(surf, F.peq_b, "!", T["fundo"], (ax + 7 * s, oy + 12 * s), "center")
        if c.legato_total:
            _txt(surf, F.peq, "legato", T["quialtera"], (cx + cl["w"] - 56 * s, oy + 3))
        # linhas da tablatura
        for corda in range(1, 7):
            y = oy + d.tab_y(corda)
            pygame.draw.line(surf, T["linha"], (cx, y), (cx + cl["w"], y), 1)
        pygame.draw.line(surf, T["barra"], (cx, y_t0), (cx, y_t5), grossa_barra)
        if cl["formula"]:
            fx = cx + int(20 * s)
            _txt(surf, F.formula, c.num, T["texto"], (fx, y_t0 + 1.35 * d.ls), "center")
            _txt(surf, F.formula, c.den, T["texto"], (fx, y_t0 + 3.65 * d.ls), "center")
        # contagem + marcas de subdivisão (abaixo das figuras)
        bx = cx + cl["pad"]
        for tp, bw in zip(c.tempos, cl["bw"]):
            _txt(surf, F.med_b, tp.indice, T["texto"], (bx, y_cont), "midtop")
            if tp.grade <= 16:
                for k in range(1, tp.grade):
                    xx = bx + bw * k / tp.grade
                    meio = tp.grade % 2 == 0 and k == tp.grade // 2 and not tp.quialtera
                    if meio:
                        _txt(surf, F.peq, "e", T["fraco"], (xx, y_cont + 2 * s), "midtop")
                    else:
                        pygame.draw.line(surf, T["linha"], (xx, y_cont + 4 * s), (xx, y_cont + 8 * s), 1)
            bx += bw
        _desenhar_ritmo(surf, d, cl, c, ox, oy, T, F)

    pygame.draw.line(surf, T["barra"], (x1s - 1, y_t0), (x1s - 1, y_t5), grossa_barra)

    # notas: duração (discreta) e depois os números das casas, grandes
    q0, q1 = sist["q0"], sist["q1"]
    vis = [n for n in p.notas if n.inicio < q1 and n.fim > q0]
    if mostrar_duracao:
        alt_s = max(3, int(d.ls * 0.30))
        for n in vis:
            if not n.corda:
                continue
            a, b = max(n.inicio, q0), min(n.fim, q1)
            _, xa = d.x_de_q(a)
            _, xb = d.x_de_q(b, fim=True)
            y = oy + d.tab_y(n.corda)
            pygame.draw.rect(surf, T["sustain"], (ox + xa, y - alt_s // 2, max(2, xb - xa - 2), alt_s),
                             border_radius=2)
    caixas = {}                                 # id(nota) -> retângulo do número (para os arcos)
    for n in vis:
        if n.inicio < q0:
            continue
        _, xa = d.x_de_q(n.inicio)
        corda = n.corda or 1
        y = oy + d.tab_y(corda)
        rot = "x" if "dead note" in n.tecnica else n.rotulo()
        if "harmônico" in n.tecnica:
            rot = f"<{rot}>"
        tocando = q_atual is not None and n.inicio <= q_atual < n.fim
        cor = T.get("tocando", T["destaque"]) if tocando else (T["texto"] if n.corda else T["aviso"])
        img = (F.casa if n.casa is not None else F.peq_b).render(rot, True, cor)
        r = img.get_rect(center=(ox + xa + img.get_width() / 2 - 1, y))
        pygame.draw.rect(surf, T["nota_bg"], r.inflate(int(4 * s), -int(2 * s)), border_radius=int(3 * s))
        surf.blit(img, r)
        caixas[id(n)] = r
        resto = n.tecnica
        for desenhada in ("bend 1 tom", "bend ½", "bend ¼", "release", "hammer", "pull", "slide in de cima",
                          "slide in", "slide out", "slide", "vibrato", "P.M.", "dead note", "harmônico"):
            resto = resto.replace(desenhada, "")
        ab = ABREV.get(resto.strip(), resto.strip()[:3])
        if ab:
            _txt(surf, F.peq_b, ab, T["destaque"], (r.right + 1, y - 3 * s), "bottomleft")
    desenhar_tecnicas(surf, d, si, ox, oy, T, F, vis, caixas)


# ---------------------------------------------------------------------------- técnicas (estilo Songsterr)
def _curva(p0, p1, p2, passos=14):
    """Pontos de uma curva de Bézier quadrática."""
    pts = []
    for k in range(passos + 1):
        t = k / passos
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        pts.append((x, y))
    return pts


def _seta(surf, cor, ponta, direcao, tam):
    """Ponta de seta em `ponta`, apontando para `direcao` ('cima' ou 'baixo')."""
    x, y = ponta
    if direcao == "cima":
        pts = [(x, y), (x - tam * 0.6, y + tam), (x + tam * 0.6, y + tam)]
    else:
        pts = [(x, y), (x - tam * 0.6, y - tam), (x + tam * 0.6, y - tam)]
    pygame.draw.polygon(surf, cor, pts)


def _rotulo_bend(semis: float) -> str:
    if semis >= 3.5:
        return "2"
    if semis >= 2.5:
        return "1½"
    if semis >= 1.5:
        return "full"
    if semis >= 0.75:
        return "½"
    return "¼"


def desenhar_tecnicas(surf, d, si, ox, oy, T, F, vis, caixas):
    """Arco do bend (sobe para fora da pauta, com 'full'/'½'), ligadura com H/P entre
    as notas do hammer-on/pull-off, linha do slide, vibrato ondulado e P.M. — como no Songsterr."""
    s = d.esc
    sist = d.sistemas[si]
    q0, q1 = sist["q0"], sist["q1"]
    cor = T["texto"]
    fina = max(1, int(1.5 * s))
    y_topo = oy + d.tab_y(1)
    x_ini_sist = ox + sist["comps"][0]["x"]
    anteriores = {}                         # corda -> nota anterior (para ligaduras e slides)
    todas = sorted((n for n in d.p.notas if n.corda and n.inicio < q1), key=lambda n: n.inicio)
    for n in todas:
        ant = anteriores.get(n.corda)
        anteriores[n.corda] = n
        if n.inicio < q0 or id(n) not in caixas:
            continue
        r = caixas[id(n)]
        y = oy + d.tab_y(n.corda)
        tec = n.tecnica or ""
        # ----- hammer-on / pull-off: ligadura acima das duas notas + H ou P
        if ("hammer" in tec or "pull" in tec) and ant is not None:
            ra = caixas.get(id(ant))
            xa = ra.centerx if ra else x_ini_sist
            xb = r.centerx
            if xb - xa > 4:
                topo = y - d.ls * 0.95
                pts = _curva((xa, y - d.ls * 0.45), ((xa + xb) / 2, topo - d.ls * 0.35), (xb, y - d.ls * 0.45))
                pygame.draw.lines(surf, cor, False, pts, fina)
                letra = "P" if "pull" in tec else "H"
                _txt(surf, F.peq_b, letra, cor, ((xa + xb) / 2, topo - d.ls * 0.25), "midbottom")
        # ----- slide: linha inclinada entre as notas (sobe ou desce com a altura)
        if "slide in" in tec:                  # entra deslizando: risco curto antes do número
            d_y = d.ls * 0.3 * (-1 if "de cima" in tec else 1)
            pygame.draw.line(surf, cor, (r.left - 14 * s, y + d_y), (r.left - 2, y - d_y * 0.4), fina)
        elif "slide" in tec and "out" not in tec and ant is not None:
            ra = caixas.get(id(ant))
            if ra is not None:
                sobe = (n.altura or 0) >= (ant.altura or 0)
                d_y = d.ls * 0.28
                pygame.draw.line(surf, cor, (ra.right + 2, y + (d_y if sobe else -d_y)),
                                 (r.left - 2, y + (-d_y if sobe else d_y)), fina)
        if "slide out" in tec:
            pygame.draw.line(surf, cor, (r.right + 2, y - d.ls * 0.2), (r.right + 14 * s, y + d.ls * 0.35), fina)
        # ----- bend: arco saindo do número e subindo para fora da pauta, seta e 'full'/'½'
        if "bend" in tec or (n.bend_semitons and n.bend_semitons > 0.2):
            semis = n.bend_semitons or (2.0 if "1 tom" in tec else 1.0 if "½" in tec else 0.5)
            _, x_fim = d.x_de_q(min(n.fim, q1), fim=True)
            larg = max(16 * s, min(34 * s, ox + x_fim - r.right - 4 * s))
            x0, y0 = r.right + 1, y
            x1, y1 = x0 + larg, y_topo - 12 * s
            pts = _curva((x0, y0), (x1, y0), (x1, y1 + 5 * s))
            pygame.draw.lines(surf, cor, False, pts, fina)
            _seta(surf, cor, (x1, y1), "cima", 6 * s)
            _txt(surf, F.peq_b, _rotulo_bend(semis), cor, (x1, y1 - 2 * s), "midbottom")
            if "release" in tec:
                x2 = x1 + max(14 * s, larg * 0.8)
                pts = _curva((x1, y1 + 4 * s), (x2, y1 + 4 * s), (x2, y - 6 * s))
                for k in range(0, len(pts) - 1, 2):              # tracejado, como no Songsterr
                    pygame.draw.line(surf, cor, pts[k], pts[k + 1], fina)
                _seta(surf, cor, (x2, y - 2 * s), "baixo", 6 * s)
        # ----- vibrato: linha ondulada acima da pauta durante a nota
        if "vibrato" in tec:
            _, x_fim = d.x_de_q(min(n.fim, q1), fim=True)
            xa, xb = r.left, max(r.right + 18 * s, ox + x_fim - 4 * s)
            yv = y_topo - 16 * s
            pts, x, k = [], xa, 0
            while x <= xb:
                pts.append((x, yv + (3 * s if k % 2 == 0 else -3 * s)))
                x += 4 * s
                k += 1
            if len(pts) > 1:
                pygame.draw.lines(surf, cor, False, pts, fina)
    # ----- P.M.: rótulo e linha tracejada acima da pauta, juntando notas seguidas
    grupos = []
    for n in sorted((n for n in vis if "P.M." in (n.tecnica or "") and n.inicio >= q0 and id(n) in caixas),
                    key=lambda n: n.inicio):
        _, xb = d.x_de_q(min(n.fim, q1), fim=True)
        xa = caixas[id(n)].left
        if grupos and xa - grupos[-1][1] < 26 * s:
            grupos[-1][1] = max(grupos[-1][1], ox + xb)
        else:
            grupos.append([xa, ox + xb])
    for xa, xb in grupos:
        ypm = y_topo - 9 * s
        rot = _txt(surf, F.peq_b, "P.M.", cor, (xa, ypm), "midleft")
        x = rot.right + 3 * s
        while x < xb - 3 * s:
            pygame.draw.line(surf, cor, (x, ypm), (min(x + 4 * s, xb), ypm), fina)
            x += 8 * s
        pygame.draw.line(surf, cor, (xb, ypm - 4 * s), (xb, ypm + 4 * s), fina)


def _desenhar_ritmo(surf, d: Diagramacao, cl: dict, c: lp.Compasso, ox, oy, T, F) -> None:
    """Figuras rítmicas no estilo Songsterr: hastes para baixo, barras embaixo."""
    s = d.esc
    y_topo = oy + d.y_haste
    y_barra = oy + d.y_barra
    esp = max(3, int(5 * s))
    grossa = max(2, int(3.2 * s))
    fina = max(1, int(1.4 * s))
    cor = T["texto"]
    bx = ox + cl["x"] + cl["pad"]
    eventos_pausa = [e for e in d.p.eventos if e.pausa and c.inicio <= e.inicio < c.fim]
    vazio = all(not tp.ataques for tp in c.tempos) and not any(
        n.inicio < c.fim and n.fim > c.inicio for n in d.p.notas)
    if vazio:                                             # pausa de compasso inteiro
        cx = bx + sum(cl["bw"]) / 2
        ym = (y_topo + y_barra) / 2
        pygame.draw.rect(surf, T["fraco"], (cx - 10 * s, ym - 4 * s, 20 * s, 7 * s))
        return
    for tp, bw in zip(c.tempos, cl["bw"]):
        hastes = []
        for off, notas, val in tp.ataques:
            x = bx + float(off) * bw
            nome, nivel, q = lp.nome_figura(val * tp.duracao / 4)
            if nome.startswith(("semínima", "mínima", "semibreve")):
                nivel = 0
            hastes.append((x, nivel, "pontuada" in nome))
        for x, nivel, pont in hastes:
            pygame.draw.line(surf, cor, (x, y_topo), (x, y_barra), fina)
            if pont:
                pygame.draw.circle(surf, cor, (int(x + 6 * s), int(y_barra - 8 * s)), max(2, int(2.2 * s)))
        # barras embaixo (a 1ª na ponta da haste, as seguintes acima dela)
        if len(hastes) == 1 and hastes[0][1] > 0:
            x, nivel, _ = hastes[0]
            for k in range(nivel):
                yy = y_barra - k * esp
                pygame.draw.line(surf, cor, (x, yy), (x + 8 * s, yy - 8 * s), grossa)
        elif len(hastes) > 1:
            maxniv = max(h[1] for h in hastes)
            for nivel in range(1, maxniv + 1):
                yy = y_barra - (nivel - 1) * esp - grossa + 1
                if nivel == 1:
                    com = [h for h in hastes if h[1] >= 1]
                    if len(com) >= 2:
                        pygame.draw.rect(surf, cor, (com[0][0], yy, com[-1][0] - com[0][0] + fina, grossa))
                    continue
                for j, (x, nv, _) in enumerate(hastes):
                    if nv < nivel:
                        continue
                    viz_d = j + 1 < len(hastes) and hastes[j + 1][1] >= nivel
                    viz_e = j > 0 and hastes[j - 1][1] >= nivel
                    if viz_d:
                        pygame.draw.rect(surf, cor, (x, yy, hastes[j + 1][0] - x + fina, grossa))
                    elif not viz_e:          # "toquinho" de barra
                        dx = 9 * s if j + 1 < len(hastes) else -9 * s
                        pygame.draw.rect(surf, cor, (min(x, x + dx), yy, abs(dx), grossa))
        # quiálteras: colchete com o número, abaixo das barras
        for ini, fim, numero in tp.grupos_quialtera:
            xs = [bx + float(off) * bw for off, _, _ in tp.ataques if ini <= off < fim]
            if not xs:
                continue
            xa, xb = xs[0], max(xs[-1], xs[0] + 10 * s)
            yq = y_barra + int(6 * s)
            cq = T["quialtera"]
            img = F.peq_b.render(str(numero), True, cq)
            r = img.get_rect(center=((xa + xb) / 2, yq))
            pygame.draw.lines(surf, cq, False, [(xa, yq - 4 * s), (xa, yq), (r.left - 2, yq)], 1)
            pygame.draw.lines(surf, cq, False, [(r.right + 2, yq), (xb, yq), (xb, yq - 4 * s)], 1)
            surf.blit(img, r)
        # pausas dentro do tempo
        pausas = []
        if tp.descricao.startswith("pausa"):
            pausas.append(bx + 4 * s)
        for e in eventos_pausa:
            if tp.inicio <= e.inicio < tp.inicio + tp.duracao:
                pausas.append(bx + float((e.inicio - tp.inicio) / tp.duracao) * bw + 4 * s)
        for x in pausas:
            ym = (y_topo + y_barra) / 2
            pygame.draw.lines(surf, T["fraco"], False,
                              [(x, ym - 8 * s), (x + 5 * s, ym - 3 * s), (x, ym + 2 * s), (x + 5 * s, ym + 8 * s)],
                              max(1, int(2 * s)))
        bx += bw


# ----------------------------------------------------------------------------
# Impressão / exportação
# ----------------------------------------------------------------------------
def exportar_pdf(p: lp.Partitura, caminho: str, dpi: int = 150) -> int:
    """Desenha a tablatura inteira em páginas A4 e salva em PDF. -> nº de páginas."""
    from PIL import Image
    pygame.font.init()
    W, H = int(8.27 * dpi), int(11.69 * dpi)
    esc = dpi / 110
    M = int(0.45 * dpi)
    F = Fontes(esc)
    d = Diagramacao(p, W - 2 * M, esc)
    T = TEMA_PAPEL
    paginas = []

    def nova():
        sf = pygame.Surface((W, H))
        sf.fill(T["fundo"])
        return sf

    pag = nova()
    y = M
    _txt(pag, F.titulo, p.titulo, T["texto"], (M, y))
    y += int(34 * esc)
    info = f"BPM {p.bpm_inicial:g}   ·   {p.compassos[0].formula}   ·   {len(p.compassos)} compassos   ·   fonte: {p.fonte.upper()}"
    _txt(pag, F.med, info, T["fraco"], (M, y))
    y += int(20 * esc)
    for a in p.avisos:
        _txt(pag, F.peq, "• " + a, T["aviso"], (M, y))
        y += int(15 * esc)
    y += int(12 * esc)
    for si in range(len(d.sistemas)):
        if y + d.alt_sist > H - M:
            paginas.append(pag)
            pag = nova()
            y = M
        desenhar_sistema(pag, d, si, M, y, T, F)
        y += d.alt_sist
    paginas.append(pag)
    imgs = []
    for k, sf in enumerate(paginas):
        _txt(sf, F.peq, f"{p.titulo} — página {k + 1}/{len(paginas)}", T["fraco"], (W // 2, H - M // 2), "center")
        imgs.append(Image.frombytes("RGB", (W, H), pygame.image.tostring(sf, "RGB")))
    imgs[0].save(caminho, "PDF", resolution=dpi, save_all=True, append_images=imgs[1:])
    return len(imgs)


def _abrir_para_imprimir(caminho: str) -> str:
    try:
        if sys.platform.startswith("win"):
            os.startfile(caminho, "print")            # type: ignore[attr-defined]
            return "Enviado para a impressora padrão."
        import subprocess
        if sys.platform == "darwin":
            subprocess.Popen(["open", caminho])
        else:
            subprocess.Popen(["xdg-open", caminho])
        return "PDF aberto: use Imprimir no visualizador."
    except Exception as e:
        return f"PDF salvo (não consegui abrir: {e})."


def _caminho_saida(p: lp.Partitura, sufixo: str) -> str:
    docs = os.path.join(os.path.expanduser("~"), "Documents")
    pasta = os.path.join(docs if os.path.isdir(docs) else tempfile.gettempdir(), "EIGUIT")
    os.makedirs(pasta, exist_ok=True)
    nome = "".join(ch for ch in (p.titulo or "partitura") if ch not in '\\/:*?"<>|').strip() or "partitura"
    alvo = os.path.join(pasta, nome + sufixo)
    try:
        with open(alvo, "ab"):
            pass
        return alvo
    except OSError:
        return os.path.join(tempfile.gettempdir(), os.path.basename(alvo))


def _escolher_arquivo() -> str:
    try:
        import tkinter as tk
        from tkinter import filedialog
        r = tk.Tk()
        r.withdraw()
        r.attributes("-topmost", True)
        c = filedialog.askopenfilename(
            title="Abrir partitura / tablatura",
            filetypes=[("MIDI ou PDF", "*.mid *.midi *.pdf *.json"), ("SoundFont", "*.sf2 *.sf3"), ("MIDI", "*.mid *.midi"),
                       ("PDF", "*.pdf"), ("Todos", "*.*")])
        r.destroy()
        return c or ""
    except Exception:
        return ""


# ----------------------------------------------------------------------------
# Botões
# ----------------------------------------------------------------------------
class Botao:
    def __init__(self, texto, acao, ligado=None, icone=None, largura=None, dica=""):
        self.texto, self.acao, self.ligado, self.icone = texto, acao, ligado, icone
        self.largura, self.dica = largura, dica
        self.rect = pygame.Rect(0, 0, 0, 0)

    def desenhar(self, surf, T, F, mouse):
        on = bool(self.ligado and self.ligado())
        cor = T["botao_on"] if on else T["botao"]
        if self.rect.collidepoint(mouse) and not on:
            cor = tuple(min(255, v + 18) for v in cor)
        pygame.draw.rect(surf, cor, self.rect, border_radius=6)
        txt_cor = T["botao_txt_on"] if on else T["texto"]
        texto = self.texto() if callable(self.texto) else self.texto
        x = self.rect.x + 10
        cy = self.rect.centery
        ic = self.icone() if callable(self.icone) else self.icone
        if ic == "play":
            pygame.draw.polygon(surf, txt_cor, [(x, cy - 7), (x, cy + 7), (x + 12, cy)])
            x += 18
        elif ic == "pause":
            pygame.draw.rect(surf, txt_cor, (x, cy - 7, 4, 14))
            pygame.draw.rect(surf, txt_cor, (x + 7, cy - 7, 4, 14))
            x += 18
        elif ic == "stop":
            pygame.draw.rect(surf, txt_cor, (x, cy - 6, 12, 12))
            x += 18
        elif ic == "seta":                         # gaveta: seta para baixo à direita
            sx = self.rect.right - 16
            pygame.draw.polygon(surf, txt_cor, [(sx - 5, cy - 3), (sx + 5, cy - 3), (sx, cy + 3)])
        if texto:
            _txt(surf, F.med_b, texto, txt_cor, (x, cy), "midleft")


# ----------------------------------------------------------------------------
# Tela
# ----------------------------------------------------------------------------
SEGURAR_S = 0.45          # segurar o botão parado por este tempo seleciona o compasso para loop


class EstudoTempo:
    TITULO = "Estudo de Tempo"
    BPM_MIN, BPM_MAX = 20, 320

    def __init__(self, rect: Optional[pygame.Rect] = None):
        self.rect = pygame.Rect(rect) if rect else None
        self.T = tema_eiguit()
        self._mouse = (0, 0)
        self.F = Fontes(1.0)
        self.p: Optional[lp.Partitura] = None
        self.diag: Optional[Diagramacao] = None
        self.scroll = 0.0
        self.scroll_det = 0
        self.sel: Optional[Tuple[int, int]] = None
        self.ancora: Optional[int] = None
        self.foco: Optional[int] = None
        self.arrastando = False
        self.bpm = 120.0
        self.loop = True
        self.metronomo = True
        self.guitarra = True
        self.subdivisao = False
        self.timbre = sint.melhor_timbre()
        self.detalhes = bool(bib_mod.Biblioteca.ler_preferencias().get("detalhes", False))
        self.msg, self.msg_t = "", 0.0
        self.carregando = ""
        self.rep = mt.Reprodutor()
        self._render_ok = None       # (buf, dur, q_ini, q_fim, bpm, loop)
        self._render_pedido = None   # (params, q_para_tocar)
        self._render_thread = None
        self._debounce = 0.0
        self._atual = None           # render em reprodução
        self._pos_q: Optional[Fraction] = None
        self._largura_diag = 0
        self._resultado_carga = None
        # aparência (fica salva) e biblioteca de partituras da conta
        prefs = bib_mod.Biblioteca.ler_preferencias()
        self.zoom = float(prefs.get("zoom", 1.35))
        self.papel = bool(prefs.get("papel", True))
        self.mostrar_duracao = bool(prefs.get("duracao", True))
        self.rep.definir_volume(float(prefs.get("volume", 0.9)))
        self.rep.latencia = float(prefs.get("latencia", 0.08))
        self.bib: Optional[bib_mod.Biblioteca] = None
        self._usuario_bib = object()
        self.mostrar_bib = False
        self.scroll_bib = 0
        self._itens_bib: List[dict] = []
        self._rects_bib: List[Tuple[pygame.Rect, str, str]] = []
        self._id_atual: Optional[str] = None
        self._altura_barra = 112
        self._cursor_surf = None
        # áudio da música inteira já pronto (chave: partitura, timbre, bpm)
        self._completos: dict = {}
        self._completo_job = None
        self._completo_pendente = 0.0
        # desenho: cada linha da partitura vira uma imagem pronta (só muda se algo mudar)
        self._cache_linhas: dict = {}
        self._cache_chave = None
        self._overlays: dict = {}
        # gaveta de sons e busca no Songsterr
        self.gaveta_som = False
        self._rects_gaveta: List[Tuple[pygame.Rect, str]] = []
        # afinação da leitura da tablatura (escolhida aqui dentro)
        self.gaveta_afin = False
        self._rects_afin: List[Tuple[pygame.Rect, object]] = []
        self._area_afin = None
        self.songsterr = None
        self.botoes1 = [
            Botao(_t("Abrir MIDI / PDF"), self.abrir_dialogo),
            Botao(lambda: f"{_t('Biblioteca')} ({len(self._itens_bib)})", self.alternar_bib,
                  ligado=lambda: self.mostrar_bib),
            Botao(lambda: _t("Pausar") if self.rep.tocando and not self.rep.pausado else _t("Tocar"),
                  self.play_pause, icone=lambda: "pause" if self.rep.tocando and not self.rep.pausado else "play"),
            Botao(_t("Parar"), self.parar, icone="stop"),
            Botao(_t("Loop"), self.alternar_loop, ligado=lambda: self.loop),
            Botao(_t("Metrônomo"), self.alternar_met, ligado=lambda: self.metronomo),
            Botao(_t("Guitarra"), self.alternar_gtr, ligado=lambda: self.guitarra),
            Botao(_t("Contar 'e'"), self.alternar_sub, ligado=lambda: self.subdivisao),
            Botao(lambda: f"Som: {sint.nome_timbre(self.timbre).replace('Real: ', '')}", self.alternar_gaveta,
                  ligado=lambda: self.gaveta_som, icone="seta"),
            Botao("Songsterr", self.abrir_songsterr, ligado=lambda: bool(self.songsterr)),
        ]
        self.botoes2 = [
            Botao("−", lambda: self.mudar_bpm(-1), largura=34),
            Botao(lambda: f"BPM {self.bpm:g}", None, largura=96),
            Botao("+", lambda: self.mudar_bpm(+1), largura=34),
            Botao(lambda: f"Original ({self.p.bpm_inicial:g})" if self.p else "Original",
                  self.bpm_partitura),
            Botao(lambda: f"Faixa: {self._nome_faixa()}", self.proxima_faixa),
            Botao(lambda: f"Afinação: {self._nome_afin()}", self.alternar_gaveta_afin,
                  ligado=lambda: self.gaveta_afin, icone="seta"),
            Botao(_t("Tocar tudo"), self.limpar_selecao),
            Botao(_t("Detalhes"), self.alternar_det, ligado=lambda: self.detalhes),
            Botao("Vol −", lambda: self.mudar_volume(-0.1), largura=58),
            Botao(lambda: f"{self.rep.volume * 100:.0f}%", None, largura=56),
            Botao("Vol +", lambda: self.mudar_volume(+0.1), largura=58),
            Botao("A−", lambda: self.mudar_zoom(-0.15), largura=40),
            Botao(lambda: f"{self.zoom * 100:.0f}%", None, largura=58),
            Botao("A+", lambda: self.mudar_zoom(+0.15), largura=40),
            Botao(_t("Papel claro"), self.alternar_papel, ligado=lambda: self.papel),
            Botao(_t("Duração"), self.alternar_duracao, ligado=lambda: self.mostrar_duracao),
            Botao(_t("Imprimir"), self.imprimir),
            Botao(_t("Exportar"), self.exportar_analise),
        ]

    # ------------------------------------------------------------- utilidades
    def avisar(self, m: str) -> None:
        self.msg, self.msg_t = m, time.time()

    def _nome_faixa(self) -> str:
        if not self.p or not self.p.faixas:
            return "—"
        n = self.p.faixas[self.p.faixa_idx]
        return n if len(n) <= 22 else n[:21] + "…"

    def _faixa_q(self) -> Tuple[Fraction, Fraction]:
        p = self.p
        if self.sel:
            return p.compassos[self.sel[0]].inicio, p.compassos[self.sel[1]].fim
        return Fraction(0), p.fim

    def _areas(self):
        r = self.rect
        barra = pygame.Rect(r.x, r.y, r.w, self._altura_barra)
        det_h = 190 if (self.detalhes and self.p) else 0
        det = pygame.Rect(r.x, r.bottom - det_h, r.w, det_h)
        vista = pygame.Rect(r.x, barra.bottom, r.w, r.h - barra.h - det_h)
        return barra, vista, det

    # ---------------------------------------------------------------- arquivos
    def abrir_dialogo(self):
        c = _escolher_arquivo()
        if c:
            self.abrir(c)

    def abrir(self, caminho: str) -> None:
        if caminho.lower().endswith((".sf2", ".sf3")):
            try:
                sint.instalar_soundfont(caminho)
                if self.timbre == "sintetico" or self.timbre.startswith("real_"):
                    self.timbre = "clean"
                self.avisar(f"SoundFont instalado: {os.path.basename(caminho)}")
                self._reiniciar_se_tocando()
            except Exception as e:
                self.avisar(f"Não consegui instalar o SoundFont: {e}")
            return
        if self.carregando:
            return
        self.parar()
        self.carregando = f"Abrindo {os.path.basename(caminho)}…"

        bib = self._bib()

        def job():
            try:
                p = lp.carregar(caminho, progresso=lambda m: setattr(self, "carregando", m))
                pid = None
                try:
                    pid = bib.salvar(p, caminho)          # já fica guardada na conta
                except Exception as e:
                    print("[biblioteca] não consegui salvar:", e)
                self._resultado_carga = ("ok", p, pid)
            except Exception as e:
                self._resultado_carga = ("erro", str(e), None)

        threading.Thread(target=job, daemon=True).start()

    # ---------------------------------------------------------------- biblioteca
    def _bib(self, usuario=None) -> "bib_mod.Biblioteca":
        if self.bib is None:
            self.bib = bib_mod.Biblioteca(usuario)
            self._recarregar_bib()
        return self.bib

    def _definir_usuario(self, usuario):
        if usuario != self._usuario_bib:
            self._usuario_bib = usuario
            self.bib = bib_mod.Biblioteca(usuario)
            self._recarregar_bib()

    def _recarregar_bib(self):
        try:
            self._itens_bib = self.bib.listar() if self.bib is not None else []
        except OSError:
            self._itens_bib = []

    def alternar_bib(self):
        self.mostrar_bib = not self.mostrar_bib
        self.scroll_bib = 0
        self._recarregar_bib()

    def abrir_da_biblioteca(self, pid: str) -> None:
        if self.carregando:
            return
        self.parar()
        self.mostrar_bib = False
        self.carregando = "Abrindo da biblioteca…"
        bib = self._bib()

        def job():
            try:
                self._resultado_carga = ("ok", bib.abrir(pid), pid)
            except Exception as e:
                self._resultado_carga = ("erro", f"não consegui abrir da biblioteca: {e}", None)

        threading.Thread(target=job, daemon=True).start()

    def remover_da_biblioteca(self, pid: str) -> None:
        self._bib().remover(pid)
        if pid == self._id_atual:
            self._id_atual = None
        self._recarregar_bib()
        self.avisar("Partitura removida da biblioteca.")

    # ---------------------------------------------------------------- aparência
    def _gravar_prefs(self):
        bib_mod.Biblioteca.gravar_preferencias(
            {"zoom": self.zoom, "papel": self.papel, "duracao": self.mostrar_duracao,
             "detalhes": self.detalhes, "volume": self.rep.volume, "latencia": self.rep.latencia})

    def mudar_volume(self, d: float):
        """Volume geral do estudo: muda na hora, mesmo tocando (não gera o som de novo)."""
        v = self.rep.definir_volume(self.rep.volume + d)
        self.avisar(f"Volume {v * 100:.0f}%")
        self._gravar_prefs()

    def mudar_zoom(self, d: float):
        self.zoom = round(max(0.8, min(2.4, self.zoom + d)), 2)
        self.diag = None
        self._gravar_prefs()

    def alternar_papel(self):
        self.papel = not self.papel
        self._gravar_prefs()

    def alternar_duracao(self):
        self.mostrar_duracao = not self.mostrar_duracao
        self._gravar_prefs()

    def _aplicar_partitura(self, p: lp.Partitura) -> None:
        self.p = p
        self.gaveta_afin = False
        self.bpm = p.bpm_inicial           # metrônomo vai direto para o andamento da partitura
        self.sel = None
        self.foco = 0 if p.compassos else None
        self.scroll = 0
        self.scroll_det = 0
        self.diag = None
        self._render_ok = None
        self._atual = None
        self._cache_linhas = {}
        self._preparar_audio_completo()           # já começa a preparar o áudio da música inteira
        self.avisar(f"{p.titulo}: {len(p.compassos)} compassos, BPM {p.bpm_inicial:g} (metrônomo ajustado)")
        if p.notas:
            primeira = p.compasso_em(min(n.inicio for n in p.notas))
            if primeira:
                self.foco = primeira
                self._rolar_para = primeira

    def proxima_faixa(self):
        if not self.p or self.p.fonte != "midi" or len(self.p.faixas) < 2:
            self.avisar("Só há uma faixa para mostrar.")
            return
        self.parar()
        nova = lp.trocar_faixa(self.p, (self.p.faixa_idx + 1) % len(self.p.faixas))
        bpm = self.bpm
        self._aplicar_partitura(nova)
        self.bpm = bpm
        if self._id_atual:                       # a biblioteca lembra a faixa escolhida
            try:
                self._bib().salvar(nova, nova.arquivo)
                self._recarregar_bib()
            except Exception as e:
                print("[biblioteca] não consegui atualizar:", e)

    def imprimir(self):
        if not self.p:
            return
        p = self.p
        self.avisar("Gerando PDF da tablatura…")

        def job():
            try:
                alvo = _caminho_saida(p, "_tablatura.pdf")
                n = exportar_pdf(p, alvo)
                self.avisar(f"{n} página(s) em {alvo}. " + _abrir_para_imprimir(alvo))
            except Exception as e:
                self.avisar(f"Falha ao gerar o PDF: {e}")

        threading.Thread(target=job, daemon=True).start()

    def exportar_analise(self):
        if not self.p:
            return
        alvo = _caminho_saida(self.p, "_analise_ritmica.md")
        with open(alvo, "w", encoding="utf-8") as f:
            f.write(lp.relatorio_markdown(self.p))
        self.avisar(f"Análise salva em {alvo}")

    # ---------------------------------------------------------------- áudio
    def _params(self):
        q0, q1 = self._faixa_q()
        return (q0, q1, round(self.bpm, 2), self.loop, self.metronomo, self.guitarra, self.subdivisao,
                self.timbre)

    def _pedir_render(self, q_tocar: Optional[Fraction], seguir: bool = False) -> None:
        """seguir=True: a música continua de onde ESTIVER quando o novo áudio ficar pronto
        (antes voltava para onde estava no pedido — se o preparo demorava, pulava para trás)."""
        self._render_pedido = (self._params(), q_tocar)
        self._pedido_segue = seguir

    def _rodar_render(self):
        if self._render_thread and self._render_thread.is_alive():
            return
        if not self._render_pedido:
            return
        params, q_tocar = self._render_pedido
        self._render_pedido = None
        p = self.p
        if getattr(self, "_pedido_segue", False) and self._atual and self.rep.tocando and not self.rep.pausado:
            agora = self.posicao_q()
            if agora is not None and params[0] <= agora < params[1]:
                q_tocar = agora
        q0, q1, bpm, loop, met, gtr, sub, timbre = params
        chave = (id(p), timbre, round(bpm, 2))
        completo = self._completos.get(chave)
        taxa, can = mt.Reprodutor.formato()
        if completo is not None or not gtr:
            longo = (p.segundos(q1) - p.segundos(q0)) * p.bpm_inicial / bpm > 20
            if longo:
                # trecho longo: toca em pedaços (não monta minutos de áudio de uma vez)
                pronto = {"buf": completo, "pronto": len(completo) if completo is not None else 0,
                          "total": len(completo) if completo is not None else 1}
                self._tocar_em_pedacos(params, q_tocar, pronto, taxa, can)
                return
            # trecho curto: recorta e monta o loop inteiro (milissegundos)
            buf, dur = mt.montar_trecho(p, completo, q0, q1, bpm, taxa, can, met, gtr, loop, subdivisao=sub)
            self._render_ok = (buf, dur, params, q_tocar, p)
            return
        par = getattr(self, "_parcial", None)
        if par is None or par["chave"] != chave:
            # o áudio deste som/BPM ainda não começou (ou o anterior está sendo largado):
            # pede e espera — nunca gera outro áudio pesado em paralelo
            self._preparar_audio_completo()
            self._render_pedido = (self._params(), q_tocar)
            self._esperando_desde = getattr(self, "_esperando_desde", None) or time.time()
            return
        if not par["erro"]:
            # o começo da música já pode estar pronto (o resto continua em segundo plano)
            s0 = p.segundos(Fraction(0))
            precisa = int(((p.segundos(q1) - s0) * p.bpm_inicial / bpm
                           + (mt.CAUDA_COMPLETA if loop else 0)) * taxa)
            if par["buf"] is not None and par["pronto"] >= min(precisa, par["total"]):
                buf, dur = mt.montar_trecho(p, par["buf"], q0, q1, bpm, taxa, can, met, gtr, loop, subdivisao=sub)
                self._render_ok = (buf, dur, params, q_tocar, p)
                return
            # o começo do trecho já está pronto? toca em pedaços enquanto o resto é preparado
            inicio = int(((p.segundos(q_tocar if q_tocar is not None else q0) - s0) * p.bpm_inicial / bpm) * taxa)
            if par["buf"] is not None and par["pronto"] >= min(inicio + int(1.5 * taxa), par["total"]):
                self._tocar_em_pedacos(params, q_tocar, par, taxa, can)
                return
            # espera (sem gerar outro áudio em paralelo): toca sozinho quando ficar pronto
            self._render_pedido = (self._params(), q_tocar)
            self._esperando_desde = getattr(self, "_esperando_desde", None) or time.time()
            return

        def job():
            try:
                taxa, can = mt.Reprodutor.formato()
                q0, q1, bpm, loop, met, gtr, sub, timbre = params
                info = {}
                buf, dur = mt.renderizar(p, q0, q1, bpm, taxa, can, met, gtr, loop, subdivisao=sub,
                                         timbre=timbre, info=info)
                esperado = "sampler" if timbre.startswith("real_") else "soundfont"
                if gtr and timbre != "sintetico" and info.get("backend") not in (esperado, "nenhum"):
                    motivo = (sint.sampler_disponivel() if esperado == "sampler" else sint.soundfont_disponivel())[1]
                    self.avisar(f"Timbre {sint.nome_timbre(timbre)} indisponível ({motivo}); "
                                f"tocando com {info.get('backend')}.")
                self._render_ok = (buf, dur, params, q_tocar, p)
            except Exception as e:
                self.avisar(f"Erro no áudio: {e}")

        self._render_thread = threading.Thread(target=job, daemon=True)
        mt.registrar_thread(self._render_thread)
        self._render_thread.start()

    def _seg_de_q(self, params, q: Fraction) -> float:
        q0, _, bpm, *_ = params
        return (self.p.segundos(q) - self.p.segundos(q0)) / (bpm / self.p.bpm_inicial)

    def _q_de_seg(self, params, s: float) -> Fraction:
        q0, _, bpm, *_ = params
        return self.p.q_de_segundos(self.p.segundos(q0) + s * (bpm / self.p.bpm_inicial))

    def posicao_q(self) -> Optional[Fraction]:
        if self._atual and self.rep.tocando:
            return self._q_de_seg(self._atual[2], self.rep.posicao())
        return self._pos_q

    def play_pause(self):
        if not self.p:
            self.abrir_dialogo()
            return
        if self.rep.tocando and not self.rep.pausado:
            self.rep.pausar()
            return
        if self.rep.pausado:
            if self._atual and self._atual[2] == self._params():
                self.rep.retomar()
                return
            q = self.posicao_q()
            self.rep.parar()
            self._pedir_render(q)
            return
        q0, q1 = self._faixa_q()
        q = self._pos_q if (self._pos_q is not None and q0 <= self._pos_q < q1) else q0
        self._pedir_render(q)
        self._debounce = 0.0

    def parar(self):
        """Para o áudio (botão Parar e também chamado pelo gerenciador ao sair do estudo)."""
        self._esperando_desde = None
        self.rep.parar()
        self._pos_q = None
        self._render_pedido = None

    def _reiniciar_se_tocando(self):
        """Aplica mudanças (BPM, loop, seleção, sons) mantendo a posição."""
        if self.rep.tocando and not self.rep.pausado:
            q = self.posicao_q()
            q0, q1 = self._faixa_q()
            if q is None or not (q0 <= q < q1):
                q = q0
            self._pedir_render(q, seguir=True)
            self._debounce = time.time() + 0.18

    def alternar_loop(self):
        self.loop = not self.loop
        self._reiniciar_se_tocando()

    def alternar_met(self):
        self.metronomo = not self.metronomo
        self._reiniciar_se_tocando()

    def alternar_gtr(self):
        self.guitarra = not self.guitarra
        self._reiniciar_se_tocando()

    def alternar_sub(self):
        self.subdivisao = not self.subdivisao
        self._reiniciar_se_tocando()

    # ------------------------------------------------ áudio completo em segundo plano
    def _arquivo_audio(self, timbre, bpm):
        if not self._id_atual or self.bib is None:
            return None
        # "v4": camada de sample fixa + legato do Songsterr corrigido (os antigos são ignorados);
        # a afinação/capo entram no nome: trocar a afinação nunca toca o áudio velho
        import hashlib
        p = self.p
        assin = hashlib.md5(repr((list(p.afinacao), getattr(p, "capo", 0))).encode()).hexdigest()[:6] if p else "x"
        return os.path.join(self.bib.pasta, self._id_atual, f"audio_v4_{timbre}_{bpm:g}_{assin}.flac")

    def _preparar_audio_completo(self, atraso: float = 0.0):
        """Agenda o render da guitarra da música inteira (timbre e BPM atuais)."""
        self._completo_pendente = time.time() + atraso

    def _rodar_audio_completo(self):
        if not self.p or not self._completo_pendente or time.time() < self._completo_pendente:
            return
        p, timbre, bpm = self.p, self.timbre, round(self.bpm, 2)
        chave = (id(p), timbre, bpm)
        antigo = getattr(self, "_parcial", None)
        if self._completo_job and self._completo_job.is_alive():
            if antigo is not None and antigo["chave"] != chave:
                antigo["cancelado"] = True          # trocou som/BPM/música: larga o render velho
            return                                  # (ele para no próximo bloco; aí começa o novo)
        self._completo_pendente = 0.0
        if chave in self._completos:
            return
        arquivo = self._arquivo_audio(timbre, bpm)
        taxa, _ = mt.Reprodutor.formato()
        total = int(((p.segundos(p.fim) - p.segundos(Fraction(0))) * p.bpm_inicial / bpm
                     + mt.CAUDA_COMPLETA) * taxa)
        parcial = {"chave": chave, "buf": None, "pronto": 0, "total": max(1, total), "erro": None,
                   "cancelado": False}
        self._parcial = parcial

        def progresso(prontas, buf):
            parcial["buf"], parcial["pronto"] = buf, prontas

        def job():
            try:
                buf = mt.ler_audio(arquivo, taxa) if arquivo and os.path.exists(arquivo) else None
                novo = buf is None
                if novo:
                    buf = mt.renderizar_guitarra_completa(p, bpm, taxa, timbre, progresso=progresso,
                                                          cancelado=lambda: parcial["cancelado"])
                parcial.update(buf=buf, pronto=len(buf), total=len(buf))
                self._completos[chave] = buf              # já pode tocar; o disco vem depois
                while len(self._completos) > 3:
                    self._completos.pop(next(iter(self._completos)))
                if novo and arquivo and os.path.isdir(os.path.dirname(arquivo)):   # (removida da biblioteca: não grava)
                    try:
                        mt.salvar_audio(arquivo, buf, taxa)
                    except Exception as e:
                        print("[tempo] não consegui guardar o áudio:", e)
            except Exception as e:
                if mt.PARAR.is_set() or parcial["cancelado"]:
                    return
                import traceback
                traceback.print_exc()
                parcial["erro"] = f"{type(e).__name__}: {e}"
                self.avisar(f"Erro ao preparar o áudio: {parcial['erro']}")

        self._completo_job = threading.Thread(target=job, daemon=True)
        mt.registrar_thread(self._completo_job)
        self._completo_job.start()

    def _tocar_em_pedacos(self, params, q_tocar, par, taxa, can):
        p = self.p
        q0, q1, bpm, loop, met, gtr, sub, timbre = params
        s0 = p.segundos(Fraction(0))
        fator = bpm / p.bpm_inicial
        base = int(round((p.segundos(q0) - s0) / fator * taxa))
        n = max(1, int(round((p.segundos(q1) - s0) / fator * taxa)) - base)
        cliques = mt.cliques_do_trecho(p, q0, q1, bpm, taxa, sub) if met else []

        def obter(i0, i1):
            g = par["buf"]
            if gtr and (g is None or par["pronto"] < min(base + i1, par["total"])):
                return None
            m = i1 - i0
            mix = np.zeros((m, 2), np.float32)
            if gtr:
                pedaco = g[base + i0:base + i1]
                mix[:len(pedaco)] = pedaco * np.float32(0.9 * 32000)
            if cliques:
                mix += (mt.metronomo_janela(cliques, i0, i1, taxa) * np.float32(0.8 * 32000))[:, None]
            out = np.clip(mix, -32767, 32767).astype(np.int16)
            if can == 1:
                return out.mean(axis=1).astype(np.int16)
            if can > 2:
                return np.concatenate([out] + [out[:, :1]] * (can - 2), axis=1)
            return out

        pos = 0.0
        if q_tocar is not None and q0 <= q_tocar < q1:
            pos = (p.segundos(q_tocar) - p.segundos(q0)) / fator
        try:
            self.rep.tocar_em_pedacos(obter, n, loop, pos)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.avisar(f"Não consegui tocar: {type(e).__name__}: {e}")
            return
        self._atual = (None, n / taxa, params)
        self._esperando_desde = None
        self._render_pedido = None

    def progresso_audio(self) -> Optional[float]:
        """0..1 do áudio da música inteira (None se não está sendo preparado)."""
        par = getattr(self, "_parcial", None)
        if not self.p or par is None or par["chave"] != (id(self.p), self.timbre, round(self.bpm, 2)):
            return None
        return min(1.0, par["pronto"] / max(1, par["total"]))

    def audio_pronto(self) -> bool:
        return bool(self.p) and (id(self.p), self.timbre, round(self.bpm, 2)) in self._completos

    # ------------------------------------------------ Songsterr (buscar pelo nome)
    def abrir_songsterr(self):
        if self.songsterr:
            self.songsterr = None
            return
        self.gaveta_som = False
        self.mostrar_bib = False
        self.songsterr = {"texto": "", "fase": "busca", "resultados": [], "faixas": [], "meta": None,
                          "ocupado": "", "erro": "", "rects": [], "scroll": 0, "digitou": 0.0}

    def _songsterr_tarefa(self, rotulo, funcao, depois):
        st = self.songsterr
        if not st or st["ocupado"]:
            return
        st["ocupado"], st["erro"] = rotulo, ""

        def job():
            try:
                res = funcao()
                self._songsterr_resultado = (depois, res, None)
            except Exception as e:
                self._songsterr_resultado = (depois, None, str(e))

        threading.Thread(target=job, daemon=True).start()

    def _songsterr_buscar(self):
        from Estudos import importar_songsterr as imp
        texto = self.songsterr["texto"].strip()
        if texto:
            self._songsterr_tarefa(f"Buscando “{texto}”…", lambda: imp.buscar(texto), "resultados")

    def _songsterr_escolher_musica(self, item):
        from Estudos import importar_songsterr as imp
        self._songsterr_tarefa(f"Abrindo {item['titulo']}…", lambda: imp.faixas(item["id"]), "faixas")

    def _songsterr_escolher_faixa(self, faixa):
        from Estudos import importar_songsterr as imp
        meta = self.songsterr["meta"]
        self._songsterr_tarefa(f"Baixando {faixa['nome']}…", lambda: imp.baixar_faixa(meta, faixa), "baixado")

    def _songsterr_aplicar(self):
        res = getattr(self, "_songsterr_resultado", None)
        if not res or not self.songsterr:
            return
        self._songsterr_resultado = None
        depois, valor, erro = res
        st = self.songsterr
        st["ocupado"] = ""
        if erro:
            st["erro"] = f"Falhou: {erro}"
            return
        st["scroll"] = 0
        if depois == "resultados":
            st["resultados"], st["fase"] = valor, "resultados"
            if not valor:
                st["erro"] = "Nada encontrado. Tente outro nome (ex.: artista + música)."
        elif depois == "faixas":
            st["meta"], st["faixas"] = valor
            st["fase"] = "faixas"
        elif depois == "baixado":
            self.songsterr = None
            self.abrir(valor)                       # lê, desenha e guarda na biblioteca

    def _desenhar_songsterr(self, tela, area):
        T, F, st = self.T, self.F, self.songsterr
        pygame.draw.rect(tela, (0, 0, 0), area.move(0, 4), border_radius=14)
        pygame.draw.rect(tela, T["painel"], area, border_radius=14)
        pygame.draw.rect(tela, T["borda"], area, 1, border_radius=14)
        st["rects"] = []
        _txt(tela, F.grande, "Importar do Songsterr", T["texto"], (area.x + 20, area.y + 14))
        rx = pygame.Rect(area.right - 44, area.y + 12, 28, 28)
        pygame.draw.line(tela, T["texto"], (rx.x + 8, rx.y + 8), (rx.right - 8, rx.bottom - 8), 2)
        pygame.draw.line(tela, T["texto"], (rx.right - 8, rx.y + 8), (rx.x + 8, rx.bottom - 8), 2)
        st["rects"].append((rx, "fechar", None))
        # campo de busca
        campo = pygame.Rect(area.x + 20, area.y + 50, area.w - 170, 36)
        pygame.draw.rect(tela, T["fundo"], campo, border_radius=8)
        pygame.draw.rect(tela, T["destaque"], campo, 2, border_radius=8)
        texto = st["texto"] or ""
        cursor = "|" if int(time.time() * 2) % 2 == 0 else ""
        cor = T["texto"] if texto else T["fraco"]
        _txt(tela, F.med, (texto + cursor) if texto else "Digite o nome da música ou do artista e aperte Enter",
             cor, (campo.x + 12, campo.centery), "midleft")
        bb = pygame.Rect(campo.right + 10, campo.y, 120, 36)
        pygame.draw.rect(tela, T["botao_on"], bb, border_radius=8)
        _txt(tela, F.med_b, "Buscar", T["botao_txt_on"], bb.center, "center")
        st["rects"].append((bb, "buscar", None))
        y = campo.bottom + 10
        if st["ocupado"] or st["erro"]:
            _txt(tela, F.med, st["ocupado"] or st["erro"], T["destaque"] if st["ocupado"] else T["aviso"],
                 (area.x + 22, y))
        y += 26
        lista = pygame.Rect(area.x + 12, y, area.w - 24, area.bottom - y - 12)
        itens = []
        if st["fase"] == "resultados":
            itens = [(f"{r['titulo']}", r["artista"], ("musica", r)) for r in st["resultados"]]
        elif st["fase"] == "faixas":
            meta = st["meta"] or {}
            bv = pygame.Rect(area.x + 20, y - 2, 90, 26)
            pygame.draw.rect(tela, T["painel2"], bv, border_radius=6)
            _txt(tela, F.peq_b, "‹ Voltar", T["texto"], bv.center, "center")
            st["rects"].append((bv, "voltar", None))
            _txt(tela, F.med_b, f"{meta.get('artist', '')} — {meta.get('title', '')}: escolha a faixa",
                 T["texto"], (bv.right + 12, bv.centery), "midleft")
            lista.y += 30
            lista.h -= 30
            for f in st["faixas"]:
                afin = " ".join(lp.nome_nota(a) for a in reversed(f["afinacao"])) if f["afinacao"] else ""
                sub = f"{f['instrumento']}" + (f"  ·  afinação {afin}" if afin else "")
                itens.append((f["nome"], sub + ("  ·  percussão (sem tablatura)" if f["percussao"] else ""),
                              ("faixa", f)))
        clip_ant = tela.get_clip()
        tela.set_clip(lista.clip(clip_ant) if clip_ant else lista)
        alt = 48
        st["scroll"] = max(0, min(st["scroll"], max(0, len(itens) * (alt + 4) - lista.h)))
        yy = lista.y - st["scroll"]
        for titulo, sub, acao in itens:
            r = pygame.Rect(lista.x, yy, lista.w, alt)
            yy += alt + 4
            if r.bottom < lista.y or r.y > lista.bottom:
                continue
            pygame.draw.rect(tela, T["painel2"] if r.collidepoint(self._mouse) else T["fundo"], r, border_radius=8)
            _txt(tela, F.med_b, titulo, T["texto"], (r.x + 14, r.y + 6))
            _txt(tela, F.peq, sub, T["fraco"], (r.x + 14, r.y + 28))
            st["rects"].append((r, acao[0], acao[1]))
        tela.set_clip(clip_ant)
        self._area_songsterr = pygame.Rect(area)

    def _songsterr_evento(self, ev, pos) -> bool:
        st = self.songsterr
        if ev.type == pygame.TEXTINPUT:
            # acentos compostos (´ + a) só chegam por aqui; letras normais vêm no KEYDOWN
            if ev.text and not ev.text.isascii():
                st["texto"] += ev.text
            return True
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_BACKSPACE:
                st["texto"] = st["texto"][:-1]
            elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._songsterr_buscar()
            elif ev.key == pygame.K_ESCAPE:
                self.songsterr = None
            elif ev.unicode and ev.unicode.isprintable() and ev.unicode.isascii():
                st["texto"] += ev.unicode
            return True                               # teclas não vazam para o player
        area = getattr(self, "_area_songsterr", None)
        if ev.type == pygame.MOUSEWHEEL and area and area.collidepoint(self._mouse):
            st["scroll"] = max(0, st["scroll"] - ev.y * 50)
            return True
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (4, 5) and area and area.collidepoint(pos):
            st["scroll"] = max(0, st["scroll"] + (-50 if ev.button == 4 else 50))
            return True
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if area and not area.collidepoint(pos):
                return False
            for r, acao, dado in st["rects"]:
                if r.collidepoint(pos):
                    if acao == "fechar":
                        self.songsterr = None
                    elif acao == "buscar":
                        self._songsterr_buscar()
                    elif acao == "voltar":
                        st["fase"] = "resultados"
                    elif acao == "musica" and not st["ocupado"]:
                        self._songsterr_escolher_musica(dado)
                    elif acao == "faixa" and not st["ocupado"] and not dado["percussao"]:
                        self._songsterr_escolher_faixa(dado)
                    return True
            return True
        return False

    # ------------------------------------------------ gaveta de sons
    def alternar_gaveta(self):
        self.gaveta_som = not self.gaveta_som

    def escolher_timbre(self, tid: str):
        self.timbre = tid
        self.gaveta_som = False
        self.avisar(f"Som: {sint.nome_timbre(tid)}")
        self._preparar_audio_completo()
        self._reiniciar_se_tocando()

    # ------------------------------------------------ afinação da tablatura
    def _nome_afin(self) -> str:
        if not self.p:
            return "—"
        n = lp.nome_afinacao(self.p.afinacao)
        curtos = {"Padrão (E A D G B E)": "Padrão", "Meio tom abaixo (Eb)": "Eb (½ tom abaixo)",
                  "Um tom abaixo (D)": "D (1 tom abaixo)"}
        n = curtos.get(n, n)
        capo = getattr(self.p, "capo", 0)
        return f"{n} · capo {capo}" if capo else n

    def alternar_gaveta_afin(self):
        if not self.p:
            self.avisar("Abra uma partitura primeiro.")
            return
        self.gaveta_afin = not self.gaveta_afin
        if self.gaveta_afin:
            self.gaveta_som = False

    def mudar_afinacao(self, afinacao, capo: int = None) -> None:
        """Relê a tablatura com outra afinação/capotraste. Tablatura (Songsterr/PDF): o som
        muda (corda solta + casa). MIDI: a digitação é refeita. Fica salvo na biblioteca."""
        if not self.p:
            return
        capo = getattr(self.p, "capo", 0) if capo is None else max(0, min(12, int(capo)))
        if list(afinacao) == list(self.p.afinacao) and capo == getattr(self.p, "capo", 0):
            return
        tocando = self.rep.tocando and not self.rep.pausado
        q = self.posicao_q() if tocando else self._pos_q
        try:
            novo = lp.aplicar_afinacao(self.p, afinacao, capo)
        except Exception as e:
            self.avisar(f"Não consegui trocar a afinação: {e}")
            return
        if tocando:
            self.rep.parar()
        self.p = novo
        self.diag = None
        self._cache_linhas = {}
        self._render_ok = None
        self._render_pedido = None
        self._atual = None
        self._preparar_audio_completo()
        self.avisar(f"Afinação: {self._nome_afin()} — "
                    + ("digitação refeita." if novo.fonte == "midi" else "o som agora segue essa afinação."))
        if tocando:
            self._pedir_render(q)
            self._debounce = 0.0
        else:
            self._pos_q = q
        if self._id_atual:
            bib, alvo = self._bib(), novo

            def guardar():
                try:
                    bib.salvar(alvo, alvo.arquivo)
                except Exception as e:
                    print("[biblioteca] não consegui salvar a afinação:", e)

            threading.Thread(target=guardar, daemon=True).start()

    def _desenhar_gaveta_afin(self, tela):
        T, F = self.T, self.F
        botao = next(b for b in self.botoes2 if b.acao == self.alternar_gaveta_afin)
        orig = self.p.afinacao_original if getattr(self.p, "afinacao_original", None) else None
        itens = []
        if orig:
            itens.append((f"Do arquivo: {lp.nome_afinacao(orig)}", list(orig)))
        itens += [(nome, list(af)) for nome, af in lp.AFINACOES if not orig or list(af) != list(orig)]
        larg = 300
        alt = 34 + 30 * len(itens) + 70
        r = pygame.Rect(botao.rect.x, botao.rect.bottom + 4, larg, alt)
        if r.right > self.rect.right - 8:
            r.x = self.rect.right - 8 - larg
        if r.bottom > self.rect.bottom - 8:
            r.y = max(self.rect.y + 8, botao.rect.y - 4 - alt)
        pygame.draw.rect(tela, (0, 0, 0), r.move(0, 4), border_radius=12)
        pygame.draw.rect(tela, T["painel"], r, border_radius=12)
        pygame.draw.rect(tela, T["borda"], r, 1, border_radius=12)
        self._rects_afin, self._area_afin = [], r
        tipo = "muda a digitação (MIDI)" if self.p.fonte == "midi" else "muda o som da tablatura"
        _txt(tela, F.peq_b, "AFINAÇÃO — " + tipo.upper(), T["fraco"], (r.x + 14, r.y + 12))
        y = r.y + 34
        for rotulo, af in itens:
            ri = pygame.Rect(r.x + 6, y, larg - 12, 28)
            atual = af == list(self.p.afinacao)
            if atual:
                pygame.draw.rect(tela, T["botao_on"], ri, border_radius=7)
            elif ri.collidepoint(self._mouse):
                pygame.draw.rect(tela, T["painel2"], ri, border_radius=7)
            _txt(tela, F.med_b if atual else F.med, rotulo, T["botao_txt_on"] if atual else T["texto"],
                 (ri.x + 12, ri.centery), "midleft")
            self._rects_afin.append((ri, ("af", af)))
            y += 30
        y += 4
        pygame.draw.line(tela, T["borda"], (r.x + 10, y), (r.right - 10, y))
        _txt(tela, F.peq_b, "CAPOTRASTE", T["fraco"], (r.x + 14, y + 6))
        y += 26
        menos = pygame.Rect(r.x + 14, y, 30, 24)
        mais = pygame.Rect(r.x + 120, y, 30, 24)
        for rb, t in ((menos, "−"), (mais, "+")):
            pygame.draw.rect(tela, T["painel2"], rb, border_radius=6)
            _txt(tela, F.med_b, t, T["texto"], rb.center, "center")
        capo = getattr(self.p, "capo", 0)
        _txt(tela, F.med_b, f"casa {capo}" if capo else "sem capo", T["texto"],
             ((menos.right + mais.x) // 2, menos.centery), "center")
        self._rects_afin.append((menos, ("capo", -1)))
        self._rects_afin.append((mais, ("capo", +1)))

    def _itens_gaveta(self):
        sm_ok = sint.sampler_disponivel()[0]
        sf_ok = sint.soundfont_disponivel()[0]
        grupos = [("Guitarra real (samples + amplificador)", [t for t in sint.TIMBRES if t[0].startswith("real_")], sm_ok),
                  ("SoundFont", [t for t in sint.TIMBRES if isinstance(t[2], tuple)], sf_ok),
                  ("Básico", [t for t in sint.TIMBRES if t[0] == "sintetico"], True)]
        return grupos

    def _desenhar_gaveta(self, tela):
        T, F = self.T, self.F
        botao = next(b for b in self.botoes1 if b.acao == self.alternar_gaveta)
        grupos = self._itens_gaveta()
        larg = 300
        alt = sum(26 + 30 * len(itens) for _, itens, _ in grupos) + 12 + 58
        r = pygame.Rect(botao.rect.x, botao.rect.bottom + 4, larg, alt)
        if r.right > self.rect.right - 8:
            r.x = self.rect.right - 8 - larg
        pygame.draw.rect(tela, (0, 0, 0), r.move(0, 4), border_radius=12)
        pygame.draw.rect(tela, T["painel"], r, border_radius=12)
        pygame.draw.rect(tela, T["borda"], r, 1, border_radius=12)
        self._rects_gaveta = []
        self._area_gaveta = r
        y = r.y + 8
        for nome, itens, ok in grupos:
            _txt(tela, F.peq_b, nome.upper() if ok else nome.upper() + "  (indisponível)", T["fraco"], (r.x + 14, y + 5))
            y += 26
            for tid, rotulo, _ in itens:
                ri = pygame.Rect(r.x + 6, y, larg - 12, 28)
                atual = tid == self.timbre
                if atual:
                    pygame.draw.rect(tela, T["botao_on"], ri, border_radius=7)
                elif ok and ri.collidepoint(self._mouse):
                    pygame.draw.rect(tela, T["painel2"], ri, border_radius=7)
                cor = T["botao_txt_on"] if atual else (T["texto"] if ok else T["fraco"])
                _txt(tela, F.med_b if atual else F.med, rotulo.replace("Real: ", ""), cor, (ri.x + 12, ri.centery), "midleft")
                if ok:
                    self._rects_gaveta.append((ri, tid))
                y += 30
        # sincronia do cursor com o som (atraso da placa de som deste computador)
        y += 4
        pygame.draw.line(tela, T["borda"], (r.x + 10, y), (r.right - 10, y))
        _txt(tela, F.peq_b, "SINCRONIA DO CURSOR", T["fraco"], (r.x + 14, y + 6))
        _txt(tela, F.peq, "se o risco vermelho corre na frente do som, aumente", T["fraco"], (r.x + 14, y + 22))
        y += 38
        menos = pygame.Rect(r.x + 14, y, 30, 24)
        mais = pygame.Rect(r.x + 120, y, 30, 24)
        for rb, t in ((menos, "−"), (mais, "+")):
            pygame.draw.rect(tela, T["painel2"], rb, border_radius=6)
            _txt(tela, F.med_b, t, T["texto"], rb.center, "center")
        _txt(tela, F.med_b, f"{self.rep.latencia * 1000:.0f} ms", T["texto"],
             ((menos.right + mais.x) // 2, menos.centery), "center")
        self._rects_gaveta.append((menos, "lat-"))
        self._rects_gaveta.append((mais, "lat+"))

    def proximo_timbre(self):
        sf_ok, _ = sint.soundfont_disponivel()
        sm_ok, _ = sint.sampler_disponivel()
        for _ in range(len(sint.TIMBRES)):
            self.timbre = sint.proximo_timbre(self.timbre)
            real = self.timbre.startswith("real_")
            if self.timbre == "sintetico" or (real and sm_ok) or (not real and sf_ok):
                break
        self.avisar(f"Timbre: {sint.nome_timbre(self.timbre)}")
        self._preparar_audio_completo()
        self._reiniciar_se_tocando()

    def alternar_det(self):
        self.detalhes = not self.detalhes
        self._gravar_prefs()

    def mudar_bpm(self, d: float):
        self.bpm = float(max(self.BPM_MIN, min(self.BPM_MAX, round(self.bpm + d))))
        self._preparar_audio_completo(1.2)        # espera parar de mexer no BPM
        self._reiniciar_se_tocando()

    def bpm_partitura(self):
        if self.p:
            self.bpm = self.p.bpm_inicial
            self._preparar_audio_completo()
            self._reiniciar_se_tocando()

    def limpar_selecao(self):
        self.sel = None
        self._reiniciar_se_tocando()

    # ------------------------------------------------------------ ciclo de vida
    def desativar(self):
        self.parar()

    def atualizar(self):
        if self._resultado_carga:
            st, val, pid = self._resultado_carga
            self._resultado_carga = None
            self.carregando = ""
            if st == "ok":
                self._aplicar_partitura(val)
                self._id_atual = pid
                self._recarregar_bib()
            else:
                self.avisar(f"Não consegui ler: {val}")
        self._rodar_audio_completo()
        self._songsterr_aplicar()
        # segurando o botão parado: depois de um instante já mostra o compasso do loop
        if (self.arrastando and not getattr(self, "_selecionando", True)
                and time.time() - self._aperto[0] >= SEGURAR_S and self.ancora is not None):
            self._selecionando = True
            self.sel = (self.ancora, self.ancora)
        if self._render_pedido and time.time() >= self._debounce:
            self._rodar_render()
        if self._render_ok:
            buf, dur, params, q_tocar, p = self._render_ok
            self._render_ok = None
            self._esperando_desde = None
            if p is self.p and not self._render_pedido:
                pos = self._seg_de_q(params, q_tocar) if q_tocar is not None else 0.0
                try:
                    self.rep.tocar(buf, dur, params[3], pos)
                except Exception as e:                 # nunca fica "mudo" sem explicar
                    import traceback
                    traceback.print_exc()
                    self.avisar(f"Não consegui tocar: {type(e).__name__}: {e}")
                    return
                self._atual = (buf, dur, params)
                self.msg = "" if self.msg.startswith("Preparando") else self.msg
        if self.rep.tocando:
            if not self.rep.atualizar():          # terminou (sem loop)
                self._pos_q = None
            else:
                self._pos_q = self.posicao_q()
                self._seguir_cursor()

    def _seguir_cursor(self):
        if not self.diag or self._pos_q is None or self.rep.pausado:
            return
        if time.time() < getattr(self, "_rolagem_manual_ate", 0):
            return          # o usuário acabou de rolar: não puxa a tela de volta enquanto ele procura
        _, vista, _ = self._areas()
        si, _ = self.diag.x_de_q(self._pos_q)
        y = self.diag.sistemas[si]["y"]
        if y < self.scroll or y + self.diag.alt_sist > self.scroll + vista.h:
            self.scroll = max(0, min(y - 20, self.diag.altura - vista.h + 40))

    # ------------------------------------------------------------ eventos
    def tratar_evento(self, ev, pos=None) -> bool:
        if self.rect is None:
            return False
        if pos is None:
            pos = getattr(ev, "pos", None) or pygame.mouse.get_pos()
        if ev.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            self._mouse = pos
        barra, vista, det = self._areas()
        if ev.type == pygame.DROPFILE:
            self.abrir(ev.file)
            return True
        if self.songsterr:
            if self._songsterr_evento(ev, pos):
                return True
        if self.gaveta_afin and ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for r, (tipo, val) in self._rects_afin:
                if r.collidepoint(pos):
                    if tipo == "capo":
                        self.mudar_afinacao(self.p.afinacao, getattr(self.p, "capo", 0) + val)
                    else:
                        self.mudar_afinacao(val)
                        self.gaveta_afin = False
                    return True
            botao = next(b for b in self.botoes2 if b.acao == self.alternar_gaveta_afin)
            if not botao.rect.collidepoint(pos):
                self.gaveta_afin = False               # clique fora fecha
                if self._area_afin is not None and self._area_afin.collidepoint(pos):
                    return True
        if self.gaveta_som and ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for r, tid in self._rects_gaveta:
                if r.collidepoint(pos):
                    if tid in ("lat-", "lat+"):
                        self.rep.latencia = round(max(0.0, min(0.5, self.rep.latencia +
                                                               (0.01 if tid == "lat+" else -0.01))), 3)
                        self._gravar_prefs()
                        return True                     # a gaveta continua aberta
                    self.escolher_timbre(tid)
                    return True
            botao = next(b for b in self.botoes1 if b.acao == self.alternar_gaveta)
            if not botao.rect.collidepoint(pos):
                self.gaveta_som = False           # clique fora fecha a gaveta
                if getattr(self, "_area_gaveta", None) is not None and self._area_gaveta.collidepoint(pos):
                    return True
        bib_visivel = self.mostrar_bib or (not self.p and self._itens_bib)
        area_bib = getattr(self, "_area_bib", None)
        if bib_visivel and area_bib is not None:
            if ev.type == pygame.MOUSEWHEEL and area_bib.collidepoint(self._mouse):
                self.scroll_bib = max(0, self.scroll_bib - ev.y * 50)
                return True
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (4, 5) and area_bib.collidepoint(pos):
                self.scroll_bib = max(0, self.scroll_bib + (-50 if ev.button == 4 else 50))
                return True
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and area_bib.collidepoint(pos):
                for r, acao, pid in self._rects_bib:
                    if r.collidepoint(pos):
                        if acao == "remover":
                            self.remover_da_biblioteca(pid)
                        else:
                            self.abrir_da_biblioteca(pid)
                        return True
                return True
            if (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.mostrar_bib
                    and vista.collidepoint(pos)):
                self.mostrar_bib = False             # clique fora do painel fecha
                return True
        if ev.type == pygame.KEYDOWN:
            shift = ev.mod & pygame.KMOD_SHIFT
            if ev.key == pygame.K_b:
                self.alternar_bib()
                return True
            if ev.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS, pygame.K_MINUS, pygame.K_KP_MINUS) \
                    and ev.mod & pygame.KMOD_CTRL:
                self.mudar_zoom(0.15 if ev.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS) else -0.15)
                return True
            if ev.key == pygame.K_SPACE:
                self.play_pause()
            elif ev.key == pygame.K_l:
                self.alternar_loop()
            elif ev.key == pygame.K_m:
                self.alternar_met()
            elif ev.key == pygame.K_g:
                self.alternar_gtr()
            elif ev.key == pygame.K_t:
                self.proximo_timbre()
            elif ev.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                self.mudar_bpm(5 if shift else 1)
            elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self.mudar_bpm(-5 if shift else -1)
            elif ev.key == pygame.K_ESCAPE and self.sel:
                self.limpar_selecao()
            elif ev.key == pygame.K_o and ev.mod & pygame.KMOD_CTRL:
                self.abrir_dialogo()
            elif ev.key == pygame.K_p and ev.mod & pygame.KMOD_CTRL:
                self.imprimir()
            else:
                return False
            return True
        if ev.type == pygame.MOUSEWHEEL:
            m = self._mouse
            if det.collidepoint(m):
                self.scroll_det = max(0, self.scroll_det - ev.y * 60 - ev.x * 60)
                return True
            if barra.collidepoint(m) and self.botoes2[1].rect.collidepoint(m):
                self.mudar_bpm(ev.y)
                return True
            vol = next((b for b in self.botoes2 if b.acao is None and b.rect.collidepoint(m)
                        and "%" in (b.texto() if callable(b.texto) else b.texto)), None)
            if vol is not None and vol is not self.botoes2[1]:
                self.mudar_volume(0.05 * ev.y)
                return True
            if vista.collidepoint(m) and pygame.key.get_mods() & pygame.KMOD_CTRL:
                self.mudar_zoom(0.1 * ev.y)             # Ctrl + roda = zoom
                return True
            if vista.collidepoint(m) and self.diag:
                maxs = max(0, self.diag.altura - vista.h + 40)
                self.scroll = max(0, min(maxs, self.scroll - ev.y * 70))
                self._rolagem_manual_ate = time.time() + 4
                return True
            return False
        if ev.type == pygame.MOUSEBUTTONDOWN:
            if ev.button == 1:
                for b in self.botoes1 + self.botoes2:
                    if b.rect.collidepoint(pos) and b.acao:
                        b.acao()
                        return True
                if vista.collidepoint(pos):
                    if not self.p:
                        if not self._itens_bib:
                            self.abrir_dialogo()
                        return True
                    i = self._comp_no_mouse(pos)
                    if i is not None:
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT and self.ancora is not None:
                            self.sel = (min(self.ancora, i), max(self.ancora, i))   # Shift: estende o loop
                            self._reiniciar_se_tocando()
                        else:
                            # ainda não sabemos se é clique (põe o cursor) ou segurar/arrastar (loop)
                            self.ancora = i
                            self.arrastando = True
                            self._aperto = (time.time(), pos, self._q_no_mouse(pos))
                            self._selecionando = False
                        self.foco = i
                        self.scroll_det = 0
                    return True
            elif ev.button in (4, 5) and vista.collidepoint(pos) and self.diag:
                maxs = max(0, self.diag.altura - vista.h + 40)
                self.scroll = max(0, min(maxs, self.scroll + (-70 if ev.button == 4 else 70)))
                self._rolagem_manual_ate = time.time() + 4
                return True
            elif ev.button == 3 and vista.collidepoint(pos):
                self.limpar_selecao()
                return True
        if ev.type == pygame.MOUSEMOTION and self.arrastando:
            _, p0, _ = self._aperto
            if self._selecionando or abs(pos[0] - p0[0]) + abs(pos[1] - p0[1]) > 8:
                self._selecionando = True             # segurou e arrastou: seleciona o loop
                i = self._comp_no_mouse(pos)
                if i is not None and self.ancora is not None:
                    self.sel = (min(self.ancora, i), max(self.ancora, i))
            return True
        if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1 and self.arrastando:
            self.arrastando = False
            t0, _, q = self._aperto
            if self._selecionando or time.time() - t0 >= SEGURAR_S:
                if not self._selecionando and self.ancora is not None:
                    self.sel = (self.ancora, self.ancora)   # segurou parado: loop deste compasso
                self._reiniciar_se_tocando()
            elif q is not None:
                self.posicionar_cursor(q)                  # clique: só leva o risco vermelho
            return True
        return False

    def posicionar_cursor(self, q: Fraction) -> None:
        """Clique na partitura: o risco vermelho vai para lá e a música toca dali.
        Se o ponto está fora do loop selecionado, o loop é desfeito."""
        if self.sel and not (self.p.compassos[self.sel[0]].inicio <= q < self.p.compassos[self.sel[1]].fim):
            self.sel = None
        self._pos_q = q
        self._rolagem_manual_ate = 0
        if self.rep.tocando and not self.rep.pausado:
            self._pedir_render(q)                          # continua tocando, a partir do clique
            self._debounce = 0.0
        elif self.rep.pausado:
            self.rep.parar()                               # pausado: o play volta daqui
            self._pos_q = q

    def _q_no_mouse(self, pos) -> Optional[Fraction]:
        if not self.diag:
            return None
        _, vista, _ = self._areas()
        return self.diag.q_em(pos[0] - vista.x - 12, pos[1] - vista.y + self.scroll - 14)

    def _comp_no_mouse(self, pos) -> Optional[int]:
        if not self.diag:
            return None
        _, vista, _ = self._areas()
        x = pos[0] - vista.x - 12
        y = pos[1] - vista.y + self.scroll - 14
        return self.diag.compasso_em(x, y)

    # ------------------------------------------------------------ desenho
    # ------------------------------------------------ API do gerenciador de estudos
    def desenhar(self, tela, estado=None, fontes=None, meio_x=0, meio_y=0, cam_x=0, cam_y=0,
                 motor_audio=None):
        """Chamada pelo gerenciador de estudos a cada quadro (mesma área do estudo de Pedais)."""
        largura = getattr(estado, "LARGURA_TELA", tela.get_width())
        altura = getattr(estado, "ALTURA_TELA", tela.get_height())
        self.rect = pygame.Rect(int(cam_x + 40), int(cam_y + 56), int(largura - 80), int(altura - 130))
        self._definir_usuario(getattr(estado, "usuario_id_logado", None))   # biblioteca da conta
        modo_tema = getattr(TEMA, "modo", None)
        if modo_tema != getattr(self, "_modo_tema", None):      # acompanha a troca claro/escuro
            self.T = tema_eiguit()
            self._modo_tema = modo_tema
        self.atualizar()
        self.desenhar_tela(tela)

    def tratar_eventos(self, evento, pos=None, estado=None) -> bool:
        """Ponto de entrada usado pelo gerenciador de estudos."""
        return self.tratar_evento(evento, pos)

    def tratar_cliques(self, pos, estado=None) -> bool:
        ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)
        return self.tratar_evento(ev, pos)

    def desenhar_tela(self, tela) -> None:
        if self.rect is None:
            self.rect = tela.get_rect()
        if self.bib is None:
            self._bib()
        T, F = self.T, self.F
        pygame.draw.rect(tela, T["fundo"], self.rect, border_radius=8)
        mouse = self._mouse

        # ---- barra de ferramentas (quebra de linha automática se faltar espaço)
        linhas = self._posicionar_botoes(self.rect)
        self._altura_barra = 8 + linhas * 38 + 26
        barra, vista, det = self._areas()
        pygame.draw.rect(tela, T["painel"], barra)
        for b in self.botoes1 + self.botoes2:
            b.desenhar(tela, T, F, mouse)
        ys = barra.bottom - 22
        if self.carregando:
            status, cor = self.carregando, T["destaque"]
        elif self._render_pedido and getattr(self, "_esperando_desde", None):
            prog = self.progresso_audio() or 0
            status = f"Preparando o áudio da música: {prog * 100:.0f}% — começa a tocar sozinho quando ficar pronto"
            cor = T["destaque"]
        elif self.msg and time.time() - self.msg_t < 8:
            status, cor = self.msg, T["texto"]
        elif self.p:
            q0, q1 = self._faixa_q()
            trecho = (f"Compassos {self.sel[0] + 1}–{self.sel[1] + 1}" if self.sel and self.sel[0] != self.sel[1]
                      else f"Compasso {self.sel[0] + 1}" if self.sel else "Música inteira")
            dur = (self.p.segundos(q1) - self.p.segundos(q0)) * self.p.bpm_inicial / self.bpm
            status = f"{self.p.titulo}  ·  {trecho}  ·  {'loop' if self.loop else 'sem loop'}  ·  {dur:.1f} s"
            cor = T["fraco"]
        else:
            status, cor = "Abra um arquivo MIDI ou PDF (ou arraste para a janela).", T["fraco"]
        _txt(tela, F.med, status, cor, (barra.x + 12, ys))
        pygame.draw.line(tela, T["borda"], (barra.x, barra.bottom - 1), (barra.right, barra.bottom - 1))

        # ---- vista da partitura
        TP = TEMA_PAPEL if self.papel else T
        if not self.p:
            if self._itens_bib:
                self._desenhar_biblioteca(tela, vista, titulo="Suas partituras — clique para abrir")
            else:
                r = vista.inflate(-80, -80)
                pygame.draw.rect(tela, T["borda"], r, 2, border_radius=16)
                _txt(tela, F.titulo, "Estudo de Tempo", T["texto"], (r.centerx, r.centery - 40), "center")
                _txt(tela, F.med, "Clique aqui ou arraste um arquivo MIDI ou PDF de partitura/tablatura.",
                     T["fraco"], (r.centerx, r.centery), "center")
                _txt(tela, F.med, "Toda partitura aberta fica guardada na sua Biblioteca: da próxima vez é só escolher.",
                     T["fraco"], (r.centerx, r.centery + 24), "center")
            if det.h:
                self._desenhar_detalhes(tela, det)
            self._desenhar_sobreposicoes(tela, vista)
            return
        pygame.draw.rect(tela, TP["fundo"], vista)
        largura = vista.w - 24
        if getattr(self, "_F_zoom", None) is None or self._F_zoom[0] != self.zoom:
            self._F_zoom = (self.zoom, Fontes(self.zoom))
        FP = self._F_zoom[1]
        if (self.diag is None or self._largura_diag != largura or self.diag.p is not self.p
                or self.diag.esc != self.zoom):
            self.diag = Diagramacao(self.p, largura, self.zoom)
            self._largura_diag = largura
            self.scroll = min(self.scroll, max(0, self.diag.altura - vista.h + 40))
        if getattr(self, "_rolar_para", None) is not None and self._rolar_para in self.diag.onde:
            si, _ = self.diag.onde[self._rolar_para]
            self.scroll = max(0, min(self.diag.sistemas[si]["y"] - 10, self.diag.altura - vista.h + 40))
            self._rolar_para = None
        d = self.diag
        clip_ant = tela.get_clip()
        tela.set_clip(vista)
        ox, oy = vista.x + 12, vista.y + 14 - int(self.scroll)
        q = self.posicao_q()
        mostrar_cursor = q is not None and (self.rep.tocando or self._pos_q is not None)
        # cada linha é desenhada UMA vez numa imagem e depois só "colada" (sem travar)
        chave = (id(d), self.papel, self.mostrar_duracao, getattr(self, "_modo_tema", None))
        if chave != self._cache_chave:
            self._cache_linhas, self._cache_chave = {}, chave
        novas = 0
        for si, sist in enumerate(d.sistemas):
            y = oy + sist["y"]
            if y + d.alt_sist < vista.y or y > vista.bottom:
                continue
            img = self._cache_linhas.get(si)
            if img is None and novas < 3:            # no máximo 3 linhas novas por quadro
                img = pygame.Surface((largura + 12, d.alt_sist)).convert()
                img.fill(TP["fundo"])
                desenhar_sistema(img, d, si, 0, 0, TP, FP, None, None, None, self.mostrar_duracao)
                self._cache_linhas[si] = img
                novas += 1
            if img is not None:
                tela.blit(img, (ox, y))
                self._desenhar_camadas(tela, d, si, ox, y, TP, FP, q if mostrar_cursor else None)
        # foco
        if self.foco is not None and self.foco in d.onde:
            si, k = d.onde[self.foco]
            cl = d.sistemas[si]["comps"][k]
            pygame.draw.rect(tela, TP["foco"], (ox + cl["x"], oy + d.sistemas[si]["y"] + 1, cl["w"],
                                                d.y_fim), max(1, int(self.zoom)), border_radius=4)
        # cursor: faixa translúcida sobre a tablatura e as figuras (como no Songsterr)
        if mostrar_cursor:
            si, xc = d.x_de_q(q)
            yy = oy + d.sistemas[si]["y"]
            y0, y1 = yy + d.tab_y(1) - int(10 * d.esc), yy + d.y_barra + int(4 * d.esc)
            larg = max(6, int(10 * d.esc))
            if self._cursor_surf is None or self._cursor_surf.get_size() != (larg, y1 - y0):
                self._cursor_surf = pygame.Surface((larg, y1 - y0), pygame.SRCALPHA)
                self._cursor_surf.fill((*TP["cursor"], 70))
            tela.blit(self._cursor_surf, (ox + xc - larg // 2, y0))
            pygame.draw.line(tela, TP["cursor"], (ox + xc, y0), (ox + xc, y1), max(2, int(2 * d.esc)))
        tela.set_clip(clip_ant)
        # barra de rolagem
        if d.altura > vista.h:
            h = max(30, vista.h * vista.h / (d.altura + 40))
            yb = vista.y + (vista.h - h) * self.scroll / max(1, d.altura - vista.h + 40)
            pygame.draw.rect(tela, T["borda"], (vista.right - 7, yb, 5, h), border_radius=3)

        if self.mostrar_bib:
            self._desenhar_biblioteca(tela, vista.inflate(-int(vista.w * 0.18), -40),
                                      titulo="Biblioteca — clique para abrir")
        if det.h:
            self._desenhar_detalhes(tela, det)
        # indicador: o áudio da música inteira já está pronto?
        pronto = self.audio_pronto()
        prog = self.progresso_audio()
        rot = "áudio pronto" if pronto else (f"preparando áudio {prog * 100:.0f}%" if prog is not None
                                             else "preparando áudio…")
        img = F.peq_b.render(rot, True, (40, 170, 90) if pronto else T["fraco"])
        tela.blit(img, img.get_rect(bottomright=(barra.right - 12, barra.bottom - 6)))
        self._desenhar_sobreposicoes(tela, vista)

    def _desenhar_sobreposicoes(self, tela, vista):
        """Painéis que ficam por cima de tudo (Songsterr e gaveta de sons)."""
        if self.songsterr:
            self._desenhar_songsterr(tela, vista.inflate(-int(vista.w * 0.14), -30))
        if self.gaveta_som:
            self._desenhar_gaveta(tela)
        if self.gaveta_afin and self.p:
            self._desenhar_gaveta_afin(tela)

    def _transparente(self, w, h, cor, alfa):
        chave = (int(w), int(h), cor, alfa)
        img = self._overlays.get(chave)
        if img is None:
            if len(self._overlays) > 64:
                self._overlays.clear()
            img = pygame.Surface((max(1, int(w)), max(1, int(h))), pygame.SRCALPHA)
            img.fill((*cor, alfa))
            self._overlays[chave] = img
        return img

    def _desenhar_camadas(self, tela, d, si, ox, oy, TP, FP, q_atual):
        """O que muda a cada quadro por cima da linha pronta: seleção e notas soando."""
        sist = d.sistemas[si]
        if self.sel:
            for cl in sist["comps"]:
                if self.sel[0] <= cl["i"] <= self.sel[1]:
                    tela.blit(self._transparente(cl["w"], d.y_fim - 2, TP["foco"], 38), (ox + cl["x"], oy + 2))
        if q_atual is None or not (sist["q0"] <= q_atual < sist["q1"]):
            return
        cor = TP.get("tocando", TP["destaque"])
        s = d.esc
        for n in self.p.notas:
            if not (n.inicio <= q_atual < n.fim) or n.inicio < sist["q0"] or not n.corda:
                continue
            _, xa = d.x_de_q(n.inicio)
            y = oy + d.tab_y(n.corda)
            rot = "x" if "dead note" in n.tecnica else n.rotulo()
            img = FP.casa.render(rot, True, cor)
            r = img.get_rect(center=(ox + xa + img.get_width() / 2 - 1, y))
            pygame.draw.rect(tela, TP["nota_bg"], r.inflate(int(4 * s), -int(2 * s)), border_radius=int(3 * s))
            tela.blit(img, r)

    def _posicionar_botoes(self, r) -> int:
        """Distribui os botões em linhas dentro da largura disponível. -> nº de linhas."""
        F = self.F
        x, y, linhas = r.x + 10, r.y + 8, 1
        for grupo in (self.botoes1, self.botoes2):
            if x > r.x + 10:                       # cada grupo começa numa linha nova
                x, y, linhas = r.x + 10, y + 38, linhas + 1
            for b in grupo:
                texto = b.texto() if callable(b.texto) else b.texto
                w = b.largura or (F.med_b.size(texto)[0] + 20 + (18 if b.icone else 0))
                w = max(w, 70 if b.icone else 0)
                if x + w > r.right - 8 and x > r.x + 10:
                    x, y, linhas = r.x + 10, y + 38, linhas + 1
                b.rect = pygame.Rect(x, y, w, 32)
                x = b.rect.right + 6
        return linhas

    def _desenhar_biblioteca(self, tela, area, titulo):
        T, F = self.T, self.F
        ds_sombra = pygame.Rect(area).move(0, 4)
        pygame.draw.rect(tela, (0, 0, 0), ds_sombra, border_radius=14)
        pygame.draw.rect(tela, T["painel"], area, border_radius=14)
        pygame.draw.rect(tela, T["borda"], area, 1, border_radius=14)
        _txt(tela, F.grande, titulo, T["texto"], (area.x + 20, area.y + 14))
        dono = "desta conta" if (self.bib is not None and self.bib.usuario not in (None, "", 0)) else "deste computador"
        _txt(tela, F.peq, f"{len(self._itens_bib)} partitura(s) guardada(s) {dono}. "
                          "Abrir um arquivo novo também guarda ele aqui.", T["fraco"], (area.x + 20, area.y + 40))
        lista = pygame.Rect(area.x + 12, area.y + 64, area.w - 24, area.h - 76)
        self._rects_bib = []
        self._area_bib = pygame.Rect(area)
        clip_ant = tela.get_clip()
        tela.set_clip(lista.clip(clip_ant) if clip_ant else lista)
        alt = 56
        maxs = max(0, len(self._itens_bib) * (alt + 6) - lista.h)
        self.scroll_bib = max(0, min(self.scroll_bib, maxs))
        y = lista.y - self.scroll_bib
        for item in self._itens_bib:
            r = pygame.Rect(lista.x, y, lista.w, alt)
            y += alt + 6
            if r.bottom < lista.y or r.y > lista.bottom:
                continue
            atual = item["id"] == self._id_atual
            hover = r.collidepoint(self._mouse)
            cor = T["painel2"] if (hover or atual) else T["fundo"]
            pygame.draw.rect(tela, cor, r, border_radius=10)
            if atual:
                pygame.draw.rect(tela, T["destaque"], r, 2, border_radius=10)
            selo = "PDF" if item.get("fonte") == "pdf" else "MIDI"
            rs = pygame.Rect(r.x + 12, r.centery - 12, 52, 24)
            pygame.draw.rect(tela, T["destaque"] if selo == "MIDI" else T["foco"], rs, border_radius=6)
            _txt(tela, F.peq_b, selo, T["botao_txt_on"], rs.center, "center")
            _txt(tela, F.med_b, item.get("titulo", "?"), T["texto"], (r.x + 78, r.y + 9))
            quando = time.strftime("%d/%m/%Y %H:%M", time.localtime(item.get("usado", 0)))
            info = (f"{item.get('compassos', 0)} compassos  ·  BPM {item.get('bpm', 0):g}  ·  "
                    f"{item.get('faixa_nome', '')}  ·  aberta em {quando}")
            _txt(tela, F.peq, info, T["fraco"], (r.x + 78, r.y + 32))
            rx = pygame.Rect(r.right - 44, r.centery - 14, 28, 28)
            if rx.collidepoint(self._mouse):
                pygame.draw.rect(tela, T["aviso"], rx, border_radius=6)
            pygame.draw.line(tela, T["texto"], (rx.x + 8, rx.y + 8), (rx.right - 8, rx.bottom - 8), 2)
            pygame.draw.line(tela, T["texto"], (rx.right - 8, rx.y + 8), (rx.x + 8, rx.bottom - 8), 2)
            self._rects_bib.append((rx, "remover", item["id"]))
            self._rects_bib.append((r, "abrir", item["id"]))
        tela.set_clip(clip_ant)

    def _desenhar_detalhes(self, tela, det):
        T, F = self.T, self.F
        pygame.draw.rect(tela, T["painel"], det)
        pygame.draw.line(tela, T["borda"], det.topleft, det.topright)
        if self.foco is None or not self.p.compassos:
            return
        c = self.p.compassos[self.foco]
        x, y = det.x + 12, det.y + 8
        _txt(tela, F.grande, f"Compasso {c.numero}  ({c.formula}, BPM {c.bpm:g})", T["texto"], (x, y))
        info = []
        if c.legato_total:
            info.append("compasso inteiro em legato (não palhetar)")
        if self.p.digitacao_sugerida:
            info.append("digitação sugerida — o MIDI não traz corda/casa")
        _txt(tela, F.peq, "   ·   ".join(info), T["fraco"], (x + 300, y + 5))
        y += 26
        for a in c.alertas[:2]:
            _txt(tela, F.peq_b, "! " + a, T["aviso"], (x, y))
            y += 15
        clip_ant = tela.get_clip()
        area = pygame.Rect(det.x, y + 2, det.w, det.bottom - y - 4)
        tela.set_clip(area)
        cx = x - self.scroll_det
        cel_w = 34
        rotulo_w = 62
        for t in c.tempos:
            cab = f"Tempo {t.indice} — {t.descricao}" + (f"  ({t.quialtera})" if t.quialtera else "")
            n = len(t.celulas)
            largura = max(rotulo_w + n * cel_w, F.med_b.size(cab)[0] + 8)
            _txt(tela, F.med_b, cab, T["destaque"] if t.quialtera else T["texto"], (cx, y + 4))
            linhas = [("Parte", [str(k + 1) for k in range(n)]), ("Nota", t.celulas)]
            if any(t.celulas_corda):
                linhas.append(("Corda", t.celulas_corda))
            if any(t.celulas_tecnica):
                linhas.append(("Técnica", [ABREV.get(v, v) for v in t.celulas_tecnica]))
            yy = y + 26
            for li, (nome, vals) in enumerate(linhas):
                pygame.draw.rect(tela, T["painel2"] if li == 0 else T["painel"], (cx, yy, rotulo_w + n * cel_w, 22))
                _txt(tela, F.peq_b, nome, T["fraco"], (cx + 4, yy + 11), "midleft")
                for k, v in enumerate(vals):
                    r = pygame.Rect(cx + rotulo_w + k * cel_w, yy, cel_w, 22)
                    pygame.draw.rect(tela, T["borda"], r, 1)
                    fonte = F.mono_b if (li == 1 and v not in ("—", "·")) else F.mono
                    cor = T["texto"] if li == 1 and v not in ("—", "·") else T["fraco"]
                    if F.mono.size(v)[0] > cel_w - 2:
                        fonte = F.peq
                    _txt(tela, fonte, v, cor, r.center, "center")
                yy += 22
            cx += largura + 22
        tela.set_clip(clip_ant)
        _txt(tela, F.peq, "—  nota anterior ainda soando      ·  silêncio (pausa)      role a roda do mouse para ver os outros tempos",
             T["fraco"], (det.x + 12, det.bottom - 16))


# ----------------------------------------------------------------------------
# Execução avulsa
# ----------------------------------------------------------------------------
def main():
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    tela = pygame.display.set_mode((1360, 860), pygame.RESIZABLE)
    pygame.display.set_caption("EIGUIT — Estudo de Tempo")
    est = EstudoTempo(tela.get_rect())
    if len(sys.argv) > 1:
        est.abrir(sys.argv[1])
    rel = pygame.time.Clock()
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                est.desativar()
                pygame.quit()
                return
            if ev.type == pygame.VIDEORESIZE:
                est.rect = pygame.Rect(0, 0, ev.w, ev.h)
            est.tratar_evento(ev)
        est.atualizar()
        tela.fill((0, 0, 0))
        est.desenhar_tela(tela)
        pygame.display.flip()
        rel.tick(60)


if __name__ == "__main__":
    main()
