# -*- coding: utf-8 -*-
"""
ESTUDOS > Tempo  (cartão "Estudo de Tempo")

Abra um MIDI ou PDF (botão, ou arraste o arquivo para a janela). A música é
desenhada inteira: cada compasso separado em tempos, cada tempo em partes,
com a figura rítmica em cima e a tablatura embaixo; a barra colorida atrás
de cada casa mostra por quanto tempo a nota soa.

Controles
  clique / arrastar em compassos .... seleciona o trecho (Shift+clique estende)
  botão direito / Esc ............... limpa a seleção (volta a tocar tudo)
  Espaço ............................ play / pause
  L / M / G / T ..................... loop / metrônomo / guitarra / timbre
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
    from audio import motor_tempo as mt                  # type: ignore
    from audio import sintetizador as sint               # type: ignore
else:
    from . import leitor_partitura as lp
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
        self.casa = pygame.font.SysFont(nome, s(14), bold=True)
        self.peq = pygame.font.SysFont(nome, s(11))
        self.peq_b = pygame.font.SysFont(nome, s(11), bold=True)
        self.med = pygame.font.SysFont(nome, s(13))
        self.med_b = pygame.font.SysFont(nome, s(13), bold=True)
        self.grande = pygame.font.SysFont(nome, s(17), bold=True)
        self.titulo = pygame.font.SysFont(nome, s(24), bold=True)
        self.formula = pygame.font.SysFont(nome, s(19), bold=True)
        self.mono = pygame.font.SysFont(mono, s(13))
        self.mono_b = pygame.font.SysFont(mono, s(13), bold=True)


def _txt(surf, fonte, texto, cor, pos, ancora="topleft"):
    img = fonte.render(str(texto), True, cor)
    r = img.get_rect(**{ancora: pos})
    surf.blit(img, r)
    return r


# ----------------------------------------------------------------------------
# Diagramação (serve para a tela e para a impressão)
# ----------------------------------------------------------------------------
class Diagramacao:
    def __init__(self, p: lp.Partitura, largura: int, esc: float = 1.0):
        self.p, self.esc, self.largura = p, esc, largura
        s = esc
        self.head = int(26 * s)
        self.ritmo = int(58 * s)
        self.ls = int(13 * s)
        self.baixo = int(30 * s)
        self.gap = int(16 * s)
        self.alt_sist = self.head + self.ritmo + 5 * self.ls + self.baixo + self.gap
        self.sistemas: List[dict] = []
        self.onde: dict = {}
        medidas = []
        ant = None
        for i, c in enumerate(p.compassos):
            mostra_formula = ant is None or (c.num, c.den) != ant
            ant = (c.num, c.den)
            pad_l = int((14 + (24 if mostra_formula else 0)) * s)
            pad_r = int(6 * s)
            bws = []
            for t in c.tempos:
                g = min(t.grade, 16)
                bws.append(max(58, 17 * g) * s)
            medidas.append([i, pad_l, pad_r, bws, mostra_formula])
        # quebra de linha
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

    # --- geometria ---
    def tab_y(self, corda: int) -> int:        # relativo ao topo do sistema
        return self.head + self.ritmo + (corda - 1) * self.ls

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

    def compasso_em(self, x: float, y: float) -> Optional[int]:
        si = int(y // self.alt_sist)
        if not 0 <= si < len(self.sistemas):
            return None
        if y - si * self.alt_sist > self.alt_sist - self.gap:
            return None
        for cl in self.sistemas[si]["comps"]:
            if cl["x"] <= x < cl["x"] + cl["w"]:
                return cl["i"]
        return None


def desenhar_sistema(surf, d: Diagramacao, si: int, ox: int, oy: int, T: dict, F: Fontes,
                     sel: Optional[Tuple[int, int]] = None, foco: Optional[int] = None) -> None:
    p, s = d.p, d.esc
    sist = d.sistemas[si]
    y_r0 = oy + d.head                     # topo da faixa rítmica
    y_t0 = oy + d.tab_y(1)                 # 1ª corda
    y_t5 = oy + d.tab_y(6)                 # 6ª corda
    y_cont = y_t5 + int(14 * s)            # contagem
    x0s = ox + sist["comps"][0]["x"]
    x1s = ox + sist["comps"][-1]["x"] + sist["comps"][-1]["w"]

    for cl in sist["comps"]:
        c = p.compassos[cl["i"]]
        cx = ox + cl["x"]
        # fundo: seleção e tempos alternados
        if sel and sel[0] <= cl["i"] <= sel[1]:
            pygame.draw.rect(surf, T["sel"], (cx, oy + 2, cl["w"], d.alt_sist - d.gap - 2))
        bx = cx + cl["pad"]
        for k, bw in enumerate(cl["bw"]):
            if k % 2 == 1 and not (sel and sel[0] <= cl["i"] <= sel[1]):
                pygame.draw.rect(surf, T["alt"], (bx, y_r0, bw, y_cont - y_r0 + int(12 * s)))
            bx += bw
        # cabeçalho
        _txt(surf, F.peq_b, c.numero, T["fraco"], (cx + 3, oy + 4))
        if cl["i"] == 0 or c.bpm != p.compassos[cl["i"] - 1].bpm:
            _txt(surf, F.peq_b, f"BPM {c.bpm:g}", T["destaque"],
                 (cx + int(26 * s), oy + 4))
        if c.alertas:
            ax = cx + cl["w"] - int(14 * s)
            pygame.draw.polygon(surf, T["aviso"], [(ax, oy + 16 * s), (ax + 6 * s, oy + 4 * s), (ax + 12 * s, oy + 16 * s)])
            _txt(surf, F.peq_b, "!", T["fundo"], (ax + 6 * s, oy + 11 * s), "center")
        if c.legato_total:
            _txt(surf, F.peq, "legato", T["quialtera"], (cx + cl["w"] - 50 * s, oy + 4))
        # linhas da tablatura
        for corda in range(1, 7):
            y = oy + d.tab_y(corda)
            pygame.draw.line(surf, T["linha"], (cx, y), (cx + cl["w"], y), 1)
        pygame.draw.line(surf, T["barra"], (cx, y_t0), (cx, y_t5), max(1, int(2 * s)))
        if cl["formula"]:
            fx = cx + int(18 * s)
            _txt(surf, F.formula, c.num, T["texto"], (fx, y_t0 + 1.4 * d.ls), "center")
            _txt(surf, F.formula, c.den, T["texto"], (fx, y_t0 + 3.6 * d.ls), "center")
        # contagem + marcas de subdivisão
        bx = cx + cl["pad"]
        for tp, bw in zip(c.tempos, cl["bw"]):
            pygame.draw.line(surf, T["fraco"], (bx, y_cont - 5 * s), (bx, y_cont + 3 * s), 1)
            _txt(surf, F.med_b, tp.indice, T["texto"], (bx + 2, y_cont + 3 * s))
            if tp.grade <= 16:
                for k in range(1, tp.grade):
                    xx = bx + bw * k / tp.grade
                    meio = tp.grade % 2 == 0 and k == tp.grade // 2 and not tp.quialtera
                    pygame.draw.line(surf, T["fraco"], (xx, y_cont - (4 if meio else 2) * s), (xx, y_cont), 1)
                    if meio:
                        _txt(surf, F.peq, "e", T["fraco"], (xx + 1, y_cont + 3 * s))
            bx += bw
        _desenhar_ritmo(surf, d, cl, c, ox, oy, T, F)

    # barra final do sistema
    pygame.draw.line(surf, T["barra"], (x1s - 1, y_t0), (x1s - 1, y_t5), max(1, int(2 * s)))

    # notas: barras de sustentação e depois as casas
    q0, q1 = sist["q0"], sist["q1"]
    vis = [n for n in p.notas if n.inicio < q1 and n.fim > q0]
    alt_s = max(3, int(d.ls * 0.42))
    for n in vis:
        if not n.corda:
            continue
        a, b = max(n.inicio, q0), min(n.fim, q1)
        _, xa = d.x_de_q(a)
        _, xb = d.x_de_q(b, fim=True)
        y = oy + d.tab_y(n.corda)
        pygame.draw.rect(surf, T["sustain"], (ox + xa, y - alt_s // 2, max(2, xb - xa - 2), alt_s),
                         border_radius=2)
    for n in vis:
        if n.inicio < q0:
            continue
        _, xa = d.x_de_q(n.inicio)
        corda = n.corda or 1
        y = oy + d.tab_y(corda)
        rot = "x" if n.tecnica == "dead note" else n.rotulo()
        img = (F.casa if n.casa is not None else F.peq_b).render(rot, True, T["texto"] if n.corda else T["aviso"])
        r = img.get_rect(midleft=(ox + xa - 1, y))
        pygame.draw.rect(surf, T["nota_bg"], r.inflate(4, 0))
        surf.blit(img, r)
        ab = ABREV.get(n.tecnica, n.tecnica[:3] if n.tecnica else "")
        if ab and ab != "x":
            _txt(surf, F.peq_b, ab, T["destaque"], (r.right + 1, y - 2 * s), "bottomleft")


def _desenhar_ritmo(surf, d: Diagramacao, cl: dict, c: lp.Compasso, ox, oy, T, F) -> None:
    s = d.esc
    y_barra = oy + d.head + int(8 * s)
    y_pe = oy + d.head + d.ritmo - int(8 * s)
    esp = max(3, int(5 * s))
    grossa = max(2, int(3 * s))
    bx = ox + cl["x"] + cl["pad"]
    eventos_pausa = [e for e in d.p.eventos if e.pausa and c.inicio <= e.inicio < c.fim]
    vazio = all(not tp.ataques for tp in c.tempos) and not any(
        n.inicio < c.fim and n.fim > c.inicio for n in d.p.notas)
    if vazio:
        largura = sum(cl["bw"])
        cx = bx + largura / 2
        ym = (y_barra + y_pe) / 2
        pygame.draw.rect(surf, T["fraco"], (cx - 9 * s, ym - 3 * s, 18 * s, 6 * s))
        _txt(surf, F.peq, "compasso em pausa", T["fraco"], (cx, ym + 6 * s), "midtop")
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
            pygame.draw.line(surf, T["texto"], (x, y_barra), (x, y_pe), max(1, int(1.5 * s)))
            if pont:
                pygame.draw.circle(surf, T["texto"], (int(x + 5 * s), int(y_pe - 3 * s)), max(2, int(2 * s)))
        # barras (colcheias etc.)
        if len(hastes) == 1 and hastes[0][1] > 0:
            x, nivel, _ = hastes[0]
            for k in range(nivel):
                yy = y_barra + k * esp
                pygame.draw.line(surf, T["texto"], (x, yy), (x + 7 * s, yy + 7 * s), grossa)
        elif len(hastes) > 1:
            maxniv = max(h[1] for h in hastes)
            for nivel in range(1, maxniv + 1):
                yy = y_barra + (nivel - 1) * esp
                if nivel == 1:
                    com = [h for h in hastes if h[1] >= 1]
                    if len(com) >= 2:
                        pygame.draw.rect(surf, T["texto"], (com[0][0], yy, com[-1][0] - com[0][0] + 1, grossa))
                    continue
                for j, (x, nv, _) in enumerate(hastes):
                    if nv < nivel:
                        continue
                    viz_d = j + 1 < len(hastes) and hastes[j + 1][1] >= nivel
                    viz_e = j > 0 and hastes[j - 1][1] >= nivel
                    if viz_d:
                        pygame.draw.rect(surf, T["texto"], (x, yy, hastes[j + 1][0] - x + 1, grossa))
                    elif not viz_e:          # "toquinho" de barra
                        dx = 8 * s if j + 1 < len(hastes) else -8 * s
                        pygame.draw.rect(surf, T["texto"], (min(x, x + dx), yy, abs(dx), grossa))
        # quiálteras
        for ini, fim, numero in tp.grupos_quialtera:
            xs = [bx + float(off) * bw for off, _, _ in tp.ataques if ini <= off < fim]
            if not xs:
                continue
            xa, xb = xs[0], max(xs[-1], xs[0] + 10 * s)
            yq = y_barra - int(5 * s)
            cor = T["quialtera"]
            img = F.peq_b.render(str(numero), True, cor)
            r = img.get_rect(center=((xa + xb) / 2, yq))
            pygame.draw.lines(surf, cor, False, [(xa, yq + 4 * s), (xa, yq), (r.left - 2, yq)], 1)
            pygame.draw.lines(surf, cor, False, [(r.right + 2, yq), (xb, yq), (xb, yq + 4 * s)], 1)
            surf.blit(img, r)
        # pausas
        pausas = []
        if tp.descricao.startswith("pausa"):
            pausas.append(bx)
        for e in eventos_pausa:
            if tp.inicio <= e.inicio < tp.inicio + tp.duracao:
                pausas.append(bx + float((e.inicio - tp.inicio) / tp.duracao) * bw)
        for x in pausas:
            ym = (y_barra + y_pe) / 2
            pygame.draw.rect(surf, T["fraco"], (x - 1, ym - 3 * s, 9 * s, 5 * s))
            _txt(surf, F.peq, "pausa", T["fraco"], (x - 1, ym + 4 * s))
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
    T = TEMA_CLARO
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
    base = os.path.splitext(p.arquivo)[0] if p.arquivo else os.path.join(tempfile.gettempdir(), p.titulo or "partitura")
    alvo = base + sufixo
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
        if texto:
            _txt(surf, F.med_b, texto, txt_cor, (x, cy), "midleft")


# ----------------------------------------------------------------------------
# Tela
# ----------------------------------------------------------------------------
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
        self.detalhes = True
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
        self.botoes1 = [
            Botao(_t("Abrir MIDI / PDF"), self.abrir_dialogo),
            Botao(lambda: _t("Pausar") if self.rep.tocando and not self.rep.pausado else _t("Tocar"),
                  self.play_pause, icone=lambda: "pause" if self.rep.tocando and not self.rep.pausado else "play"),
            Botao(_t("Parar"), self.parar, icone="stop"),
            Botao(_t("Loop"), self.alternar_loop, ligado=lambda: self.loop),
            Botao(_t("Metrônomo"), self.alternar_met, ligado=lambda: self.metronomo),
            Botao(_t("Guitarra"), self.alternar_gtr, ligado=lambda: self.guitarra),
            Botao(_t("Contar 'e'"), self.alternar_sub, ligado=lambda: self.subdivisao),
            Botao(lambda: f"Timbre: {sint.nome_timbre(self.timbre)}", self.proximo_timbre,
                  dica="Clique para trocar; arraste um .sf2/.sf3 para usar outro SoundFont"),
        ]
        self.botoes2 = [
            Botao("−", lambda: self.mudar_bpm(-1), largura=34),
            Botao(lambda: f"BPM {self.bpm:g}", None, largura=96),
            Botao("+", lambda: self.mudar_bpm(+1), largura=34),
            Botao(lambda: f"BPM da partitura ({self.p.bpm_inicial:g})" if self.p else "BPM da partitura",
                  self.bpm_partitura),
            Botao(lambda: f"Faixa: {self._nome_faixa()}", self.proxima_faixa),
            Botao(_t("Tocar tudo"), self.limpar_selecao),
            Botao(_t("Detalhes"), self.alternar_det, ligado=lambda: self.detalhes),
            Botao(_t("Imprimir"), self.imprimir),
            Botao(_t("Exportar análise"), self.exportar_analise),
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
        barra = pygame.Rect(r.x, r.y, r.w, 112)
        det_h = 212 if (self.detalhes and self.p) else 0
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

        def job():
            try:
                p = lp.carregar(caminho, progresso=lambda m: setattr(self, "carregando", m))
                self._resultado_carga = ("ok", p)
            except Exception as e:
                self._resultado_carga = ("erro", str(e))

        threading.Thread(target=job, daemon=True).start()

    def _aplicar_partitura(self, p: lp.Partitura) -> None:
        self.p = p
        self.bpm = p.bpm_inicial           # metrônomo vai direto para o andamento da partitura
        self.sel = None
        self.foco = 0 if p.compassos else None
        self.scroll = 0
        self.scroll_det = 0
        self.diag = None
        self._render_ok = None
        self._atual = None
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

    def _pedir_render(self, q_tocar: Optional[Fraction]) -> None:
        self._render_pedido = (self._params(), q_tocar)

    def _rodar_render(self):
        if self._render_thread and self._render_thread.is_alive():
            return
        if not self._render_pedido:
            return
        params, q_tocar = self._render_pedido
        self._render_pedido = None
        p = self.p

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
        self.avisar("Preparando o áudio…")

    def parar(self):
        """Para o áudio (botão Parar e também chamado pelo gerenciador ao sair do estudo)."""
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
            self._pedir_render(q)
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

    def proximo_timbre(self):
        sf_ok, _ = sint.soundfont_disponivel()
        sm_ok, _ = sint.sampler_disponivel()
        for _ in range(len(sint.TIMBRES)):
            self.timbre = sint.proximo_timbre(self.timbre)
            real = self.timbre.startswith("real_")
            if self.timbre == "sintetico" or (real and sm_ok) or (not real and sf_ok):
                break
        self.avisar(f"Timbre: {sint.nome_timbre(self.timbre)}")
        self._reiniciar_se_tocando()

    def alternar_det(self):
        self.detalhes = not self.detalhes

    def mudar_bpm(self, d: float):
        self.bpm = float(max(self.BPM_MIN, min(self.BPM_MAX, round(self.bpm + d))))
        self._reiniciar_se_tocando()

    def bpm_partitura(self):
        if self.p:
            self.bpm = self.p.bpm_inicial
            self._reiniciar_se_tocando()

    def limpar_selecao(self):
        self.sel = None
        self._reiniciar_se_tocando()

    # ------------------------------------------------------------ ciclo de vida
    def desativar(self):
        self.parar()

    def atualizar(self):
        if self._resultado_carga:
            st, val = self._resultado_carga
            self._resultado_carga = None
            self.carregando = ""
            if st == "ok":
                self._aplicar_partitura(val)
            else:
                self.avisar(f"Não consegui ler: {val}")
        if self._render_pedido and time.time() >= self._debounce:
            self._rodar_render()
        if self._render_ok:
            buf, dur, params, q_tocar, p = self._render_ok
            self._render_ok = None
            if p is self.p and not self._render_pedido:
                pos = self._seg_de_q(params, q_tocar) if q_tocar is not None else 0.0
                self.rep.tocar(buf, dur, params[3], pos)
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
        if ev.type == pygame.KEYDOWN:
            shift = ev.mod & pygame.KMOD_SHIFT
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
            if vista.collidepoint(m) and self.diag:
                maxs = max(0, self.diag.altura - vista.h + 40)
                self.scroll = max(0, min(maxs, self.scroll - ev.y * 70))
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
                        self.abrir_dialogo()
                        return True
                    i = self._comp_no_mouse(pos)
                    if i is not None:
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT and self.ancora is not None:
                            self.sel = (min(self.ancora, i), max(self.ancora, i))
                        else:
                            self.ancora = i
                            self.sel = (i, i)
                            self.arrastando = True
                        self.foco = i
                        self.scroll_det = 0
                    return True
            elif ev.button in (4, 5) and vista.collidepoint(pos) and self.diag:
                maxs = max(0, self.diag.altura - vista.h + 40)
                self.scroll = max(0, min(maxs, self.scroll + (-70 if ev.button == 4 else 70)))
                return True
            elif ev.button == 3 and vista.collidepoint(pos):
                self.limpar_selecao()
                return True
        if ev.type == pygame.MOUSEMOTION and self.arrastando:
            i = self._comp_no_mouse(pos)
            if i is not None and self.ancora is not None:
                self.sel = (min(self.ancora, i), max(self.ancora, i))
            return True
        if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1 and self.arrastando:
            self.arrastando = False
            self._reiniciar_se_tocando()
            return True
        return False

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
        T, F = self.T, self.F
        barra, vista, det = self._areas()
        pygame.draw.rect(tela, T["fundo"], self.rect, border_radius=8)
        mouse = self._mouse

        # ---- barra de ferramentas
        pygame.draw.rect(tela, T["painel"], barra)
        x, y = barra.x + 10, barra.y + 8
        for b in self.botoes1:
            w = b.largura or (F.med_b.size(b.texto() if callable(b.texto) else b.texto)[0] + 20 +
                              (18 if b.icone else 0))
            b.rect = pygame.Rect(x, y, max(w, 70 if b.icone else 0), 32)
            b.desenhar(tela, T, F, mouse)
            x = b.rect.right + 6
        x, y = barra.x + 10, barra.y + 46
        for b in self.botoes2:
            w = b.largura or (F.med_b.size(b.texto() if callable(b.texto) else b.texto)[0] + 20)
            b.rect = pygame.Rect(x, y, w, 32)
            b.desenhar(tela, T, F, mouse)
            x = b.rect.right + 6
        # linha de status
        ys = barra.y + 88
        if self.carregando:
            status, cor = self.carregando, T["destaque"]
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
        if not self.p:
            r = vista.inflate(-80, -80)
            pygame.draw.rect(tela, T["borda"], r, 2, border_radius=16)
            _txt(tela, F.titulo, "Estudo de Tempo", T["texto"], (r.centerx, r.centery - 40), "center")
            _txt(tela, F.med, "Clique aqui ou arraste um arquivo MIDI ou PDF de partitura/tablatura.",
                 T["fraco"], (r.centerx, r.centery), "center")
            _txt(tela, F.med, "Cada compasso é separado em tempos e subdivisões; selecione um trecho e toque em loop com metrônomo.",
                 T["fraco"], (r.centerx, r.centery + 24), "center")
            return
        largura = vista.w - 24
        if self.diag is None or self._largura_diag != largura or self.diag.p is not self.p:
            self.diag = Diagramacao(self.p, largura)
            self._largura_diag = largura
        if getattr(self, "_rolar_para", None) is not None and self._rolar_para in self.diag.onde:
            si, _ = self.diag.onde[self._rolar_para]
            self.scroll = max(0, min(self.diag.sistemas[si]["y"] - 10, self.diag.altura - vista.h + 40))
            self._rolar_para = None
        d = self.diag
        clip_ant = tela.get_clip()
        tela.set_clip(vista)
        ox, oy = vista.x + 12, vista.y + 14 - int(self.scroll)
        for si, sist in enumerate(d.sistemas):
            y = oy + sist["y"]
            if y + d.alt_sist < vista.y or y > vista.bottom:
                continue
            desenhar_sistema(tela, d, si, ox, y, T, F, self.sel, self.foco)
        # foco
        if self.foco is not None and self.foco in d.onde:
            si, k = d.onde[self.foco]
            cl = d.sistemas[si]["comps"][k]
            pygame.draw.rect(tela, T["foco"], (ox + cl["x"], oy + d.sistemas[si]["y"] + 1, cl["w"],
                                               d.alt_sist - d.gap), 1, border_radius=3)
        # cursor
        q = self.posicao_q()
        if q is not None and (self.rep.tocando or self._pos_q is not None):
            si, xc = d.x_de_q(q)
            yy = oy + d.sistemas[si]["y"]
            pygame.draw.line(tela, T["cursor"], (ox + xc, yy + d.head - 4), (ox + xc, yy + d.tab_y(6) + 6), 2)
        tela.set_clip(clip_ant)
        # barra de rolagem
        if d.altura > vista.h:
            h = max(30, vista.h * vista.h / (d.altura + 40))
            yb = vista.y + (vista.h - h) * self.scroll / max(1, d.altura - vista.h + 40)
            pygame.draw.rect(tela, T["borda"], (vista.right - 7, yb, 5, h), border_radius=3)

        if det.h:
            self._desenhar_detalhes(tela, det)

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
