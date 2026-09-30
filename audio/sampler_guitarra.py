# -*- coding: utf-8 -*-
"""
Sampler de guitarra DI (nível 2) — lê bibliotecas SFZ e toca as notas da
tablatura como uma guitarra de verdade, antes do amplificador.

Biblioteca incluída: Karoryfer "Emilyguitar" (CC0, domínio público): guitarra
elétrica gravada direto (DI), 4 camadas de dinâmica, 3 round-robins por nota,
ruídos de soltar a corda e notas abafadas. Fica em assets/audio/guitarra_di/.
Outras bibliotecas SFZ podem ser colocadas em assets/audio/<pasta>/ (veja `instrumento.json`).

O que o sampler faz com cada nota
  * escolhe o sample pela altura, dinâmica e round-robin (nunca repete o mesmo
    sample duas vezes seguidas na mesma nota, como a mão real);
  * pitch variável no tempo (bend, release, vibrato, slide) por reamostragem;
  * monofonia por corda: nota nova na mesma corda corta a anterior;
  * hammer-on / pull-off: pula o "clique" da palheta (offset) e ataca mais fraco;
  * slide: a nota nova sai deslizando da anterior, sem ataque; slide out cai no fim;
  * palm mute: aproximado (filtro passa-baixa + decaimento curto) — a Emily não
    tem samples de P.M.; dead note usa os samples de corda abafada;
  * no fim de cada nota toca o ruído de soltar a corda (release samples);
  * dobra de gravação (double tracking): segunda "tomada" com outros samples,
    5–12 ms de folga e 3 cents de diferença, abrindo em estéreo.
"""
from __future__ import annotations

import functools
import json
import math
import os
import re
import time
from typing import Dict, List, Optional, Tuple

import numpy as np

_NOTA = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}


def _num_nota(s) -> int:
    s = str(s).strip().lower()
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    m = re.fullmatch(r"([a-g])([#b]?)(-?\d+)", s)
    if not m:
        raise ValueError(f"nota inválida no SFZ: {s!r}")
    n = _NOTA[m.group(1)] + (1 if m.group(2) == "#" else -1 if m.group(2) == "b" else 0)
    return (int(m.group(3)) + 1) * 12 + n


# ----------------------------------------------------------------------------
# Leitor SFZ (subconjunto usado por bibliotecas de guitarra)
# ----------------------------------------------------------------------------
class Regiao(dict):
    def _f(self, k, d=0.0):
        try:
            return float(self.get(k, d))
        except ValueError:
            return d

    @property
    def lokey(self):
        return _num_nota(self.get("lokey", self.get("key", 0)))

    @property
    def hikey(self):
        return _num_nota(self.get("hikey", self.get("key", 127)))

    @property
    def centro(self):
        return _num_nota(self.get("pitch_keycenter", self.get("key", 60)))

    @property
    def lovel(self):
        return int(self._f("lovel", 0))

    @property
    def hivel(self):
        return int(self._f("hivel", 127))


def ler_sfz(caminho: str, raiz: Optional[str] = None) -> List[Regiao]:
    regioes: List[Regiao] = []
    base = os.path.dirname(caminho)
    raiz = raiz or base
    defs: Dict[str, str] = {}
    ctx = {"global": {}, "master": {}, "group": {}}
    estado = {"cur": None, "tipo": None, "default_path": ""}

    def fechar():
        if estado["cur"] is not None and estado["tipo"] == "region":
            r = Regiao()
            for k in ("global", "master", "group"):
                r.update(ctx[k])
            r.update(estado["cur"])
            if "sample" in r:
                s = r["sample"].replace("\\", "/")
                r["sample"] = os.path.normpath(os.path.join(raiz, estado["default_path"], s))
                regioes.append(r)
        estado["cur"] = None

    with open(caminho, encoding="utf-8", errors="ignore") as f:
        linhas = f.readlines()
    for linha in linhas:
        linha = linha.split("//")[0].strip()
        if not linha:
            continue
        if linha.startswith("#include"):
            inc = re.search(r'"(.*)"', linha).group(1).replace("\\", "/")
            fechar()
            regioes.extend(ler_sfz(os.path.join(base, inc), raiz))
            continue
        if linha.startswith("#define"):
            _, k, v = linha.split(None, 2)
            defs[k] = v
            continue
        for k, v in defs.items():
            linha = linha.replace(k, v)
        for tok in re.split(r"(?=<\w+>)", linha):
            tok = tok.strip()
            if not tok:
                continue
            m = re.match(r"<(\w+)>(.*)", tok, re.S)
            if m:
                fechar()
                tipo = m.group(1)
                estado["tipo"] = tipo
                if tipo in ctx:
                    ctx[tipo] = {}
                    if tipo == "global":
                        ctx["master"], ctx["group"] = {}, {}
                    elif tipo == "master":
                        ctx["group"] = {}
                    estado["cur"] = ctx[tipo]
                else:
                    estado["cur"] = {}
                resto = m.group(2).strip()
            else:
                resto = tok
            for kv in re.split(r"\s+(?=[a-zA-Z_]\w*=)", resto):
                if "=" not in kv:
                    continue
                k, v = kv.split("=", 1)
                k, v = k.strip(), v.strip()
                if estado["tipo"] == "control":
                    if k == "default_path":
                        estado["default_path"] = v.replace("\\", "/")
                    continue
                if estado["cur"] is not None:
                    estado["cur"][k] = v
    fechar()
    return regioes


@functools.lru_cache(maxsize=2048)
def _carregar(caminho: str, taxa: int) -> np.ndarray:
    import soundfile as sf
    dados, fs = sf.read(caminho, dtype="float32", always_2d=True)
    x = dados.mean(axis=1)
    if fs != taxa:
        from scipy.signal import resample_poly
        g = math.gcd(fs, taxa)
        x = resample_poly(x, taxa // g, fs // g).astype(np.float32)
    return np.ascontiguousarray(x)


# ----------------------------------------------------------------------------
# Instrumento
# ----------------------------------------------------------------------------
class Instrumento:
    def __init__(self, pasta: str):
        self.pasta = pasta
        cfg_p = os.path.join(pasta, "instrumento.json")
        self.cfg = {}
        if os.path.exists(cfg_p):
            with open(cfg_p, encoding="utf-8") as f:
                self.cfg = json.load(f)
        sfz = self.cfg.get("sfz") or next((f for f in sorted(os.listdir(pasta)) if f.endswith(".sfz")), None)
        if not sfz:
            raise FileNotFoundError(f"nenhum .sfz em {pasta}")
        self.nome = self.cfg.get("nome", os.path.basename(pasta))
        todas = [r for r in ler_sfz(os.path.join(pasta, sfz))
                 if float(r.get("locc64", 0)) <= 0 and "sw_last" not in r]
        mudo = set(self.cfg.get("teclas_abafadas", []))
        ruido = set(self.cfg.get("teclas_ruido", [])) | mudo
        self.ataque = [r for r in todas if r.get("trigger", "attack") == "attack" and r.lokey not in ruido]
        self.release = [r for r in todas if r.get("trigger") == "release"]
        self.abafadas = [r for r in todas if r.lokey in mudo]
        if not self.ataque:
            raise ValueError("a biblioteca não tem regiões de nota")
        self._ultimo: Dict[Tuple[int, int, int], str] = {}

    def escolher(self, altura: int, vel: int, rng, lista=None) -> Optional[Regiao]:
        lista = lista if lista is not None else self.ataque
        cand = [r for r in lista if r.lokey <= altura <= r.hikey and r.lovel <= vel <= r.hivel]
        if not cand:
            cand = [r for r in lista if r.lokey <= altura <= r.hikey]
        if not cand:
            if not lista:
                return None
            perto = min(lista, key=lambda r: min(abs(altura - r.lokey), abs(altura - r.hikey)))
            cand = [r for r in lista if (r.lokey, r.hikey) == (perto.lokey, perto.hikey)]
            cand = [r for r in cand if r.lovel <= vel <= r.hivel] or cand
        chave = (cand[0].lokey, cand[0].lovel, id(lista))
        ult = self._ultimo.get(chave)
        opcoes = [r for r in cand if r["sample"] != ult] or cand
        r = opcoes[int(rng.integers(len(opcoes)))]
        self._ultimo[chave] = r["sample"]
        return r


_INSTRUMENTOS: Dict[str, Instrumento] = {}


def pasta_biblioteca() -> Optional[str]:
    """assets/audio/guitarra_di (incluída) ou a primeira pasta de assets/audio/ com um .sfz dentro."""
    from . import sintetizador as sint
    env = os.environ.get("EIGUIT_SFZ")
    if env and os.path.isdir(env):
        return env
    pref = os.path.join(sint.PASTA_SONS, "guitarra_di")
    if os.path.isdir(pref):
        return pref
    if os.path.isdir(sint.PASTA_SONS):
        for d in sorted(os.listdir(sint.PASTA_SONS)):
            p = os.path.join(sint.PASTA_SONS, d)
            if os.path.isdir(p) and any(f.endswith(".sfz") for f in os.listdir(p)):
                return p
    return None


def instrumento() -> Instrumento:
    p = pasta_biblioteca()
    if not p:
        raise FileNotFoundError("nenhuma biblioteca SFZ em assets/audio/")
    if p not in _INSTRUMENTOS:
        _INSTRUMENTOS.clear()
        _INSTRUMENTOS[p] = Instrumento(p)
    return _INSTRUMENTOS[p]


def disponivel() -> Tuple[bool, str]:
    try:
        import soundfile  # noqa: F401
        import scipy  # noqa: F401
    except ImportError:
        return False, "instale: pip install soundfile scipy"
    p = pasta_biblioteca()
    if not p:
        return False, "nenhuma biblioteca SFZ em assets/audio/"
    return True, os.path.basename(p)


# ----------------------------------------------------------------------------
# Render
# ----------------------------------------------------------------------------
def _passa_baixa(x: np.ndarray, fc: float, taxa: int) -> np.ndarray:
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(2, fc, fs=taxa, output="sos"), x).astype(np.float32)


def _preparar(notas) -> list:
    """Aplica monofonia por corda e descobre de onde vem cada slide/legato."""
    por_corda: Dict[int, list] = {}
    livres = []
    for n in notas:
        (por_corda.setdefault(n.corda, []) if n.corda else livres).append(n)
    saida = []
    for corda, lst in por_corda.items():
        lst.sort(key=lambda n: n.t0)
        for i, n in enumerate(lst):
            prox = lst[i + 1] if i + 1 < len(lst) else None
            ant = lst[i - 1] if i > 0 else None
            fim = n.t0 + n.dur
            cortada = prox is not None and prox.t0 < fim + 0.02
            if cortada:
                fim = max(n.t0 + 0.02, prox.t0 + 0.004)        # a nova corta a anterior
            liga = ant is not None and abs((ant.t0 + ant.dur) - n.t0) < 0.03
            saida.append((n, fim, ant if liga else None, cortada))
    for n in livres:
        saida.append((n, n.t0 + n.dur, None, False))
    return saida


def _curva_pitch(n, ant, t: np.ndarray, dur: float) -> np.ndarray:
    """Semitons em relação à altura da nota ao longo do tempo t (s desde o ataque)."""
    s = np.zeros_like(t)
    tec = n.tecnica or ""
    if n.bend:
        a, b = 0.2 * dur, 0.45 * dur
        f = np.clip((t - a) / max(b - a, 1e-3), 0, 1)
        s += n.bend * (1 - (1 - f) ** 2)
        if "release" in tec:
            c = 0.72 * dur
            s -= n.bend * np.clip((t - c) / max(b - a, 1e-3), 0, 1)
    if "vibrato" in tec or tec == "~":
        amp = np.clip((t - 0.25 * dur) / 0.15, 0, 1) * 0.45
        s += amp * np.sin(2 * np.pi * 5.5 * t)
    if "slide" in tec and "out" not in tec and ant is not None and ant.altura is not None:
        de = ant.altura - n.altura
        s += de * (1 - np.clip(t / 0.07, 0, 1))
    if "slide out" in tec:
        c = 0.6 * dur
        s -= 7 * np.clip((t - c) / max(0.4 * dur, 1e-3), 0, 1) ** 1.5
    return s


def _tocar(inst: Instrumento, reg: Regiao, altura: int, curva_semi: np.ndarray, taxa: int,
           offset: int, detune_cents: float) -> np.ndarray:
    smp = _carregar(reg["sample"], taxa)
    base = altura - reg.centro + reg._f("transpose") + (reg._f("tune") + detune_cents) / 100.0
    razao = 2.0 ** ((base + curva_semi) / 12.0)
    pos = offset + int(reg._f("offset")) + np.concatenate(([0.0], np.cumsum(razao[:-1])))
    ok = pos < len(smp) - 1
    n = int(ok.sum())
    if n <= 0:
        return np.zeros(0, np.float32)
    i = pos[:n].astype(np.int64)
    fr = (pos[:n] - i).astype(np.float32)
    return (smp[i] * (1 - fr) + smp[i + 1] * fr).astype(np.float32) * (10 ** (reg._f("volume") / 20))


def _render_tomada(inst, notas_prep, n_total, taxa, rng, folga=(0.0, 0.0), detune=0.0) -> np.ndarray:
    out = np.zeros(n_total, np.float32)
    rel = int(0.09 * taxa)
    for k_nota, (n, fim, ant, cortada) in enumerate(notas_prep):
        if k_nota % 6 == 5:
            time.sleep(0)          # render em 2º plano: devolve a vez para a tela não engasgar
        if n.altura is None:
            continue
        tec = n.tecnica or ""
        t0 = n.t0 + (float(rng.uniform(*folga)) if folga[1] else 0.0)
        dur = max(0.02, fim - n.t0)
        vel = int(np.clip(n.vel + rng.integers(-5, 6), 1, 127))
        legato = "hammer" in tec or "pull" in tec or ("slide" in tec and "out" not in tec and ant is not None)
        if legato:
            vel = int(vel * 0.75)
        pm = "P.M." in tec or "palm" in tec.lower()
        morta = "dead note" in tec
        if morta and inst.abafadas:
            reg = inst.escolher(n.altura, vel, rng, inst.abafadas)
            sinal = _carregar(reg["sample"], taxa).copy() * (vel / 127) * 0.8
            dur = len(sinal) / taxa
        else:
            reg = inst.escolher(n.altura, vel, rng)
            if reg is None:
                continue
            m = int((dur + 0.09) * taxa)
            t = np.arange(m, dtype=np.float32) / taxa
            curva = _curva_pitch(n, ant, t, dur)
            offset = int(0.025 * taxa) if legato else 0
            sinal = _tocar(inst, reg, n.altura, curva, taxa, offset, detune)
            if not len(sinal):
                continue
            # dinâmica: a camada já muda o timbre; ajuste fino de volume dentro da camada
            sinal *= 0.55 + 0.45 * (vel / 127)
            if legato:
                a = min(len(sinal), int(0.006 * taxa))
                sinal[:a] *= np.linspace(0.2, 1, a, dtype=np.float32)
            if pm or morta:
                sinal = _passa_baixa(sinal, 750 if pm else 400, taxa)
                tt = np.arange(len(sinal), dtype=np.float32) / taxa
                sinal *= np.exp(-tt / (0.13 if pm else 0.03)) * (1.6 if pm else 1.2)
            # solta a corda: fade no fim + ruído de release
            k = int(dur * taxa)
            if k < len(sinal):
                r = min(len(sinal) - k, rel)
                sinal[k:k + r] *= np.linspace(1, 0, r, dtype=np.float32) ** 2
                sinal[k + r:] = 0
                sinal = sinal[:k + r]
        i0 = int(round(t0 * taxa))
        if i0 >= n_total:
            continue
        j = min(n_total, i0 + len(sinal))
        out[i0:j] += sinal[:j - i0]
        if inst.release and not pm and not morta and not cortada and dur > 0.12:
            rr = inst.escolher(n.altura, vel, rng, inst.release)
            if rr is not None:
                ruido = _carregar(rr["sample"], taxa) * (10 ** (rr._f("volume") / 20)) * 0.5 * (vel / 127)
                a = int(round((t0 + dur) * taxa))
                if a < n_total:
                    b = min(n_total, a + len(ruido))
                    out[a:b] += ruido[:b - a]
    return out


def aquecer(taxa: int = 44100) -> None:
    """Carrega a biblioteca e todos os samples na memória (chame numa thread ao abrir o programa)."""
    inst = instrumento()
    for r in inst.ataque + inst.release + inst.abafadas:
        _carregar(r["sample"], taxa)


def render_di(notas, dur: float, taxa: int = 44100, dobrar: bool = True, semente: int = 11,
              cauda: float = 1.5) -> np.ndarray:
    """Sinal DI (antes do amp). -> float32 (n + cauda, 2)."""
    inst = instrumento()
    n_total = int(round((dur + cauda) * taxa))
    prep = _preparar(notas)
    rng = np.random.default_rng(semente)
    a = _render_tomada(inst, prep, n_total, taxa, rng)
    if not dobrar:
        return np.stack([a, a], axis=1)
    b = _render_tomada(inst, prep, n_total, taxa, np.random.default_rng(semente + 101),
                       folga=(0.005, 0.012), detune=3.0)
    # 1ª tomada mais à esquerda, 2ª mais à direita (como duas guitarras gravadas)
    return np.stack([0.8 * a + 0.35 * b, 0.35 * a + 0.8 * b], axis=1)
