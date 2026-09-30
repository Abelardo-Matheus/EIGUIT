# -*- coding: utf-8 -*-
"""
Sintetizador de guitarra compartilhado (ESTUDOS > Tempo, área de Partitura, etc.).

Backends
  * "sampler"  : nível 2 — samples reais de guitarra DI (assets/audio/guitarra_di, SFZ) + amplificador,
                 caixa (IR) e sala (audio/sampler_guitarra.py + audio/amp_guitarra.py).
                 Timbres "real_*". Precisa de: pip install soundfile scipy
  * "soundfont": toca um banco .sf2/.sf3 com TinySoundFont (pip install tinysoundfont).
                 Render offline, amostra a amostra, sem placa de som envolvida.
  * "sintetico": o sintetizador numpy antigo (sempre disponível, usado como reserva).

Como é "guitarra" e não piano GM:
  * cada corda num canal MIDI próprio -> bend/vibrato numa corda não entorta as outras,
    e uma nota nova na mesma corda CORTA a anterior (como no instrumento real);
  * palm mute / dead note vão para o timbre "Muted Guitar" nos canais-espelho;
  * bend = glissando de pitch bend; vibrato = modulação ±¼ de tom;
  * hammer/pull atacam mais fraco; acordes saem "palhetados" (6 ms entre cordas,
    da grave para a aguda) e há pequena variação de dinâmica, como mão humana.

Uso:
    from audio import sintetizador as sint
    buf, usado = sint.render_notas(notas, duracao_s, taxa=44100, timbre="clean", loop=False)
    # notas: lista de sint.NotaAudio(t0, dur, altura, vel=90, bend=0, tecnica="", corda=None)
    # buf: float32 (n, 2) em -1..1 ; usado: "soundfont" ou "sintetico"

Arquivos de som ficam em assets/audio/ (a mesma pasta de assets do EIGUIT):
  assets/audio/soundfonts/  -> .sf2/.sf3 (GeneralUser GS incluído; padrao.txt escolhe o padrão)
  assets/audio/guitarra_di/ -> biblioteca SFZ do sampler (Emilyguitar, CC0)
  assets/audio/ir/          -> IRs de caixa .wav opcionais
"""
from __future__ import annotations

import functools
import glob
import os
import shutil
import threading
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PASTA_SONS = os.path.join(RAIZ, "assets", "audio")          # mesma pasta de assets do EIGUIT
PASTA_SF = os.path.join(PASTA_SONS, "soundfonts")

# (id, nome na tela, (banco, preset) no padrão GM/GS; None = sintético)
TIMBRES: List[Tuple[str, str, object]] = [
    # nível 2: sampler de guitarra DI + amplificador (audio/sampler_guitarra.py + amp_guitarra.py)
    ("real_clean", "Real: Clean", "amp:clean"),
    ("real_crunch", "Real: Crunch", "amp:crunch"),
    ("real_drive", "Real: Drive", "amp:drive"),
    ("real_highgain", "Real: High gain", "amp:highgain"),
    ("real_di", "Real: DI (sem amp)", "amp:di"),
    # nível 1: SoundFont GM
    ("clean", "Clean", (0, 27)),
    ("chorus", "Clean chorus", (8, 27)),
    ("jazz", "Jazz", (0, 26)),
    ("aco", "Violão aço", (0, 25)),
    ("nylon", "Violão nylon", (0, 24)),
    ("overdrive", "Overdrive", (0, 29)),
    ("distorcao", "Distorção", (0, 30)),
    ("sintetico", "Sintético", None),
]
ABAFADO = (0, 28)                       # Muted Guitar
CANAIS_CORDA = [0, 1, 2, 3, 4, 5]       # 1ª..6ª corda
CANAIS_ABAFADO = [10, 11, 12, 13, 14, 15]
FAIXA_BEND = 4.0                        # semitons (cobre bend de 2 tons)
CAUDA_S = 1.6                           # quanto de "rabo" renderizar após o fim


@dataclass
class NotaAudio:
    t0: float                  # segundos
    dur: float                 # segundos (quanto a nota soa)
    altura: int                # MIDI
    vel: int = 90              # 1..127
    bend: float = 0.0          # semitons (+ sobe)
    tecnica: str = ""
    corda: Optional[int] = None


def nome_timbre(tid: str) -> str:
    return next((n for i, n, _ in TIMBRES if i == tid), tid)


def proximo_timbre(tid: str) -> str:
    ids = [i for i, _, _ in TIMBRES]
    return ids[(ids.index(tid) + 1) % len(ids)] if tid in ids else ids[0]


# ----------------------------------------------------------------------------
# Localizar / instalar SoundFont
# ----------------------------------------------------------------------------
def caminho_soundfont() -> Optional[str]:
    env = os.environ.get("EIGUIT_SOUNDFONT")
    if env and os.path.exists(env):
        return env
    achados = []
    for pasta in (PASTA_SF, PASTA_SONS, os.path.join(RAIZ, "sons")):
        for ext in ("*.sf2", "*.sf3"):
            achados += glob.glob(os.path.join(pasta, ext))
    if not achados:
        return None
    # preferido marcado em soundfonts/padrao.txt; senão o maior (em geral o mais completo)
    pref = os.path.join(PASTA_SF, "padrao.txt")
    if os.path.exists(pref):
        with open(pref, encoding="utf-8") as f:
            nome = f.read().strip()
        for a in achados:
            if os.path.basename(a) == nome:
                return a
    return max(achados, key=os.path.getsize)


def instalar_soundfont(origem: str) -> str:
    """Copia um .sf2/.sf3 para assets/audio/soundfonts/ e marca como padrão. -> caminho final."""
    os.makedirs(PASTA_SF, exist_ok=True)
    destino = os.path.join(PASTA_SF, os.path.basename(origem))
    if os.path.abspath(origem) != os.path.abspath(destino):
        shutil.copyfile(origem, destino)
    with open(os.path.join(PASTA_SF, "padrao.txt"), "w", encoding="utf-8") as f:
        f.write(os.path.basename(destino))
    _MOTOR.clear()
    return destino


def soundfont_disponivel() -> Tuple[bool, str]:
    """-> (ok, motivo/arquivo)."""
    try:
        import tinysoundfont  # noqa: F401
    except ImportError:
        return False, "instale o pacote: pip install tinysoundfont"
    sf = caminho_soundfont()
    if not sf:
        return False, "nenhum .sf2/.sf3 em assets/audio/soundfonts/"
    return True, os.path.basename(sf)


# ----------------------------------------------------------------------------
# Backend SoundFont
# ----------------------------------------------------------------------------
_MOTOR: dict = {}
_TRAVA = threading.Lock()


def _motor(taxa: int):
    import tinysoundfont
    sf = caminho_soundfont()
    chave = (sf, taxa)
    if chave not in _MOTOR:
        _MOTOR.clear()
        synth = tinysoundfont.Synth(samplerate=taxa)
        sfid = synth.sfload(sf, max_voices=192)
        _MOTOR[chave] = (synth, sfid)
    return _MOTOR[chave]


def _curva_bend(n: NotaAudio, taxa: int, passo: float = 0.008):
    """Lista de (amostra, semitons) para bend e vibrato desta nota."""
    pts = []
    if n.bend:
        a, b = n.t0 + 0.2 * n.dur, n.t0 + 0.45 * n.dur
        k = max(2, int((b - a) / passo))
        for i in range(k + 1):
            f = i / k
            pts.append((a + (b - a) * f, n.bend * (1 - (1 - f) ** 2)))   # sobe rápido e assenta
        if "release" in n.tecnica:
            c = n.t0 + 0.75 * n.dur
            for i in range(1, k + 1):
                pts.append((c + (b - a) * i / k, n.bend * (1 - i / k)))
    if "vibrato" in n.tecnica or n.tecnica == "~":
        base = n.bend if n.bend else 0.0
        t = n.t0 + 0.3 * n.dur
        while t < n.t0 + n.dur:
            fase = (t - n.t0) * 2 * np.pi * 5.5
            pts.append((t, base + 0.5 * np.sin(fase)))
            t += passo
    return [(int(round(t * taxa)), s) for t, s in pts]


def _render_soundfont(notas: List[NotaAudio], dur: float, taxa: int, timbre: str, loop: bool) -> np.ndarray:
    preset = next((p for i, _, p in TIMBRES if i == timbre and isinstance(p, tuple)), (0, 27))
    n_total = max(1, int(round(dur * taxa)))
    n_cauda = n_total + int(CAUDA_S * taxa)
    rng = np.random.default_rng(7)

    # acordes: pequena defasagem de palhetada (grave -> aguda)
    por_t: dict = {}
    for n in notas:
        por_t.setdefault(round(n.t0, 4), []).append(n)
    eventos = []   # (amostra, ordem, tipo, dados)
    livre = 0
    for t0, grupo in por_t.items():
        grupo.sort(key=lambda n: -(n.corda or 0) if n.corda else n.altura)
        for k, n in enumerate(grupo):
            atraso = 0.006 * k if len(grupo) > 1 else 0.0
            ab = "P.M." in n.tecnica or "dead note" in n.tecnica or "palm" in n.tecnica.lower()
            if n.corda and 1 <= n.corda <= 6:
                ch = (CANAIS_ABAFADO if ab else CANAIS_CORDA)[n.corda - 1]
            else:
                ch = (CANAIS_ABAFADO if ab else CANAIS_CORDA)[livre % 6]
                livre += 1
            vel = n.vel
            if "hammer" in n.tecnica or "pull" in n.tecnica:
                vel = int(vel * 0.7)
            if "dead note" in n.tecnica:
                vel = min(127, int(vel * 1.1))
            vel = int(np.clip(vel + rng.integers(-6, 7), 20, 127))
            d = min(n.dur, 0.05) if "dead note" in n.tecnica else n.dur
            i0 = int(round((n.t0 + atraso) * taxa))
            i1 = int(round((n.t0 + d) * taxa))
            eventos.append((i0, 1, "on", (ch, n.altura, vel)))
            eventos.append((max(i1, i0 + 1), 0, "off", (ch, n.altura)))
            for i, s in _curva_bend(n, taxa):
                eventos.append((i, 2, "bend", (ch, s)))
    eventos.sort(key=lambda e: (e[0], e[1]))

    with _TRAVA:
        synth, sfid = _motor(taxa)
        for ch in range(16):
            synth.notes_off(ch)
            synth.sounds_off(ch)
        for ch in CANAIS_CORDA:
            synth.program_select(ch, sfid, preset[0], preset[1])
            synth.pitchbend_range(ch, FAIXA_BEND)
            synth.pitchbend(ch, 8192)
        for ch in CANAIS_ABAFADO:
            synth.program_select(ch, sfid, ABAFADO[0], ABAFADO[1])
            synth.pitchbend_range(ch, FAIXA_BEND)
            synth.pitchbend(ch, 8192)
        synth.generate(2048)                       # descarta resto de render anterior

        out = np.zeros((n_cauda, 2), np.float32)
        tocando: dict = {}                        # canal -> altura soando
        pos = 0

        def gerar_ate(alvo):
            nonlocal pos
            while pos < alvo:
                m = min(alvo - pos, 8192)
                bloco = np.frombuffer(synth.generate(m), dtype=np.float32).reshape(-1, 2)
                out[pos:pos + m] = bloco[:m]
                pos += m

        for i, _, tipo, dados in eventos:
            if i >= n_cauda:
                break
            gerar_ate(i)
            if tipo == "on":
                ch, alt, vel = dados
                if ch in tocando:                  # mesma corda: corta a anterior
                    synth.noteoff(ch, tocando[ch])
                synth.pitchbend(ch, 8192)
                synth.noteon(ch, alt, vel)
                tocando[ch] = alt
            elif tipo == "off":
                ch, alt = dados
                if tocando.get(ch) == alt:
                    synth.noteoff(ch, alt)
                    del tocando[ch]
            else:
                ch, s = dados
                synth.pitchbend(ch, int(np.clip(8192 + s / FAIXA_BEND * 8191, 0, 16383)))
        for ch, alt in list(tocando.items()):
            if n_total < n_cauda:
                gerar_ate(n_total)
            synth.noteoff(ch, alt)
        gerar_ate(n_cauda)
        for ch in range(16):
            synth.sounds_off(ch)

    corpo = out[:n_total].copy()
    if loop:
        resto = out[n_total:]
        while len(resto):
            m = min(len(resto), n_total)
            corpo[:m] += resto[:m]
            resto = resto[m:]
    return corpo


# ----------------------------------------------------------------------------
# Backend sintético (o de antes, agora em estéreo)
# ----------------------------------------------------------------------------
def nota_sintetica(f0: float, dur: float, taxa: int, vel: float, bend: float) -> np.ndarray:
    rel = 0.07
    n = int(min(dur + rel, 6.0) * taxa)
    if n <= 0:
        return np.zeros(0, np.float32)
    t = np.arange(n, dtype=np.float32) / taxa
    if bend:
        a, b = 0.2 * dur, 0.45 * dur
        semis = bend * np.clip((t - a) / max(b - a, 1e-3), 0, 1)
        fase = 2 * np.pi * np.cumsum(f0 * 2 ** (semis / 12)) / taxa
    else:
        fase = 2 * np.pi * f0 * t
    y = np.zeros(n, np.float32)
    for h in range(1, 11):
        if h * f0 > taxa * 0.45:
            break
        amp = abs(np.sin(np.pi * h * 0.21)) / h ** 0.9
        y += (amp * np.sin(h * fase) * np.exp(-t * (1.3 + 0.9 * h))).astype(np.float32)
    ataque = int(0.002 * taxa)
    if ataque:
        y[:ataque] *= np.linspace(0, 1, ataque, dtype=np.float32)
    k = int(dur * taxa)
    if k < n:
        y[k:] *= np.linspace(1, 0, n - k, dtype=np.float32) ** 2
    return y * vel


def _render_sintetico(notas: List[NotaAudio], dur: float, taxa: int, loop: bool) -> np.ndarray:
    n_total = max(1, int(round(dur * taxa)))
    mono = np.zeros(n_total, np.float32)
    for n in notas:
        d = min(n.dur, 0.03) if "dead note" in n.tecnica else n.dur
        sinal = nota_sintetica(440.0 * 2 ** ((n.altura - 69) / 12), d, taxa,
                               0.35 + 0.65 * n.vel / 127, n.bend)
        i0 = int(round(n.t0 * taxa))
        if i0 >= n_total or not len(sinal):
            continue
        fim = i0 + len(sinal)
        cabe = min(fim, n_total) - i0
        mono[i0:i0 + cabe] += sinal[:cabe]
        if loop and fim > n_total:
            resto = sinal[cabe:]
            while len(resto):
                m = min(len(resto), n_total)
                mono[:m] += resto[:m]
                resto = resto[m:]
    return np.repeat(mono[:, None], 2, axis=1)


# ----------------------------------------------------------------------------
# Entrada única
# ----------------------------------------------------------------------------
def sampler_disponivel() -> Tuple[bool, str]:
    try:
        from . import sampler_guitarra as sg
    except ImportError as e:
        return False, f"módulo do sampler: {e}"
    return sg.disponivel()


def melhor_timbre() -> str:
    if sampler_disponivel()[0]:
        return "real_clean"
    if soundfont_disponivel()[0]:
        return "clean"
    return "sintetico"


def _dobrar_cauda(buf: np.ndarray, n_total: int, loop: bool) -> np.ndarray:
    corpo = buf[:n_total].copy()
    if len(corpo) < n_total:
        corpo = np.concatenate([corpo, np.zeros((n_total - len(corpo), 2), np.float32)])
    if loop:
        resto = buf[n_total:]
        while len(resto):
            m = min(len(resto), n_total)
            corpo[:m] += resto[:m]
            resto = resto[m:]
    return corpo


def _render_sampler(notas: List[NotaAudio], dur: float, taxa: int, preset: str, loop: bool,
                    dobrar: bool, rapido: bool = False, cauda: float = 1.5) -> np.ndarray:
    from . import amp_guitarra as amp
    from . import sampler_guitarra as sg
    di = sg.render_di(notas, dur, taxa, dobrar=dobrar, cauda=cauda)
    saida = amp.processar(di, preset, taxa, rapido=rapido) if preset != "di" else di
    return _dobrar_cauda(saida, max(1, int(round(dur * taxa))), loop)


def render_notas(notas: List[NotaAudio], dur: float, taxa: int = 44100, timbre: str = "clean",
                 loop: bool = False, pico: float = 0.6, dobrar: bool = True, rapido: bool = False,
                 cauda: float = 1.5) -> Tuple[np.ndarray, str]:
    """-> (float32 (n, 2) normalizado para `pico`, backend usado: sampler | soundfont | sintetico).
    rapido/cauda: para tocar nota a nota em tempo real (amp sem oversampling, rabo curto)."""
    usado = "sintetico"
    buf = None
    alvo = next((p for i, _, p in TIMBRES if i == timbre), None)
    if isinstance(alvo, str) and alvo.startswith("amp:"):
        if sampler_disponivel()[0]:
            try:
                buf = _render_sampler(notas, dur, taxa, alvo[4:], loop, dobrar, rapido, cauda)
                usado = "sampler"
            except Exception as e:
                print("[sintetizador] sampler falhou:", e)
                buf = None
        if buf is None:                              # sem biblioteca: usa o parecido no SoundFont
            timbre = {"amp:clean": "clean", "amp:crunch": "overdrive", "amp:drive": "overdrive",
                      "amp:highgain": "distorcao", "amp:di": "clean"}[alvo]
    if buf is None and timbre != "sintetico" and soundfont_disponivel()[0]:
        try:
            buf = _render_soundfont(notas, dur, taxa, timbre, loop)
            usado = "soundfont"
        except Exception as e:                      # SoundFont corrompido etc.: cai no sintético
            print("[sintetizador] SoundFont falhou:", e)
            buf = None
    if buf is None:
        buf = _render_sintetico(notas, dur, taxa, loop)
    if pico is not None:
        m = float(np.abs(buf).max()) if buf.size else 0.0
        if m > 0:
            buf *= pico / m
    return buf, usado


# ----------------------------------------------------------------------------
# Instrumentos GM avulsos (baixo, voz, bateria) — usados pelo motor da tablatura
# ----------------------------------------------------------------------------
def render_gm(altura: int, dur: float, vel: int = 100, programa: int = 33, taxa: int = 44100,
              bateria: bool = False, bend: float = 0.0, cauda: float = 0.4) -> Optional[np.ndarray]:
    """Uma nota de qualquer instrumento GM pelo SoundFont. -> float32 (n, 2) ou None."""
    if not soundfont_disponivel()[0]:
        return None
    n_total = int((dur + cauda) * taxa)
    with _TRAVA:
        synth, sfid = _motor(taxa)
        for ch in range(16):
            synth.sounds_off(ch)
        ch = 9 if bateria else 0
        if bateria:
            synth.program_select(ch, sfid, 128, 0, True)
        else:
            synth.program_select(ch, sfid, 0, programa)
            synth.pitchbend_range(ch, FAIXA_BEND)
            synth.pitchbend(ch, 8192)
        synth.generate(1024)
        synth.noteon(ch, int(altura), int(np.clip(vel, 1, 127)))
        out = np.zeros((n_total, 2), np.float32)
        k_on = min(int(dur * taxa), n_total)
        pos = 0

        def gerar(ate):
            nonlocal pos
            while pos < ate:
                m = min(512, ate - pos)
                if bend and pos < k_on:
                    f = min(1.0, max(0.0, (pos / taxa - 0.2 * dur) / max(0.25 * dur, 1e-3)))
                    synth.pitchbend(ch, int(np.clip(8192 + bend * f / FAIXA_BEND * 8191, 0, 16383)))
                out[pos:pos + m] = np.frombuffer(synth.generate(m), dtype=np.float32).reshape(-1, 2)[:m]
                pos += m

        gerar(k_on)
        synth.noteoff(ch, int(altura))
        gerar(n_total)
        synth.sounds_off(ch)
    return out


# ----------------------------------------------------------------------------
# Nota avulsa com NÍVEL FIXO (motor da tablatura): nenhuma nota é normalizada
# sozinha, então todas saem no mesmo volume e com o mesmo tratamento
# ----------------------------------------------------------------------------
PICO_ALVO = 0.75
_GANHOS_FIXOS: dict = {}


def _ganho_calibrado(chave, gerar_referencia) -> float:
    if chave not in _GANHOS_FIXOS:
        ref = gerar_referencia()
        pico = float(np.abs(ref).max()) if ref is not None and ref.size else 0.0
        _GANHOS_FIXOS[chave] = (PICO_ALVO / pico) if pico > 1e-6 else 1.0
    return _GANHOS_FIXOS[chave]


ALVO_PERCEBIDO = 0.079      # ≈ -22 dB de volume percebido: o mesmo para todo timbre e toda nota


def _nivel_percebido(x: np.ndarray, taxa: int) -> float:
    from .amp_guitarra import nivel_percebido
    return nivel_percebido(x, taxa)


def _curva_vel(vel: float) -> float:
    v = max(1.0, min(127.0, float(vel))) / 127.0
    return 0.18 + 0.82 * v ** 1.6


def render_nota_fixa(nota: NotaAudio, dur: float, taxa: int = 44100, timbre: str = "real_clean") -> Tuple[np.ndarray, str]:
    """Uma nota da guitarra, sempre na melhor qualidade disponível e com o MESMO volume
    percebido para qualquer altura, corda, técnica, camada de sample ou timbre."""
    alvo = next((p for i, _, p in TIMBRES if i == timbre), None)
    if isinstance(alvo, str) and alvo.startswith("amp:") and sampler_disponivel()[0]:
        from . import amp_guitarra as amp
        from . import sampler_guitarra as sg
        di = sg.render_di([nota], dur, taxa, dobrar=True, cauda=0.0)
        preset = alvo[4:]
        out = di if preset == "di" else amp.processar(di, preset, taxa, pico_entrada=amp.PICO_ENTRADA_FIXO,
                                                      ganho_saida=1.0)
        usado = "sampler"
    elif timbre != "sintetico" and soundfont_disponivel()[0]:
        tb = timbre if isinstance(alvo, tuple) else "clean"
        out, usado = _render_soundfont([nota], dur, taxa, tb, False), "soundfont"
    else:
        out, usado = _render_sintetico([nota], dur, taxa, False), "sintetico"
    nivel = _nivel_percebido(out[: int(0.35 * taxa)], taxa)
    alvo_nota = ALVO_PERCEBIDO * _curva_vel(nota.vel) / _curva_vel(100)
    if nivel > 1e-9:
        out = out * np.float32(alvo_nota / nivel)
    return np.clip(out, -1, 1).astype(np.float32), usado


@functools.lru_cache(maxsize=2048)
def nivel_nota_timbre(timbre: str, altura: int, taxa: int) -> float:
    """Volume percebido de uma nota (intensidade 100) neste timbre, sem nenhum ajuste."""
    alvo = next((p for i, _, p in TIMBRES if i == timbre), None)
    corda = 6 if altura < 45 else 5 if altura < 50 else 4 if altura < 55 else 3 if altura < 59 else 2 if altura < 64 else 1
    n = NotaAudio(0.0, 0.6, int(altura), 100, corda=corda)
    if isinstance(alvo, str) and alvo.startswith("amp:") and sampler_disponivel()[0]:
        from . import amp_guitarra as amp
        return amp.nivel_nota(alvo[4:], int(altura), taxa)
    if timbre != "sintetico" and soundfont_disponivel()[0]:
        tb = timbre if isinstance(alvo, tuple) else "clean"
        out = _render_soundfont([n], 0.7, taxa, tb, False)
    else:
        out = _render_sintetico([n], 0.7, taxa, False)
    return _nivel_percebido(out[: int(0.35 * taxa)], taxa)


def ganho_por_altura(timbre: str, altura: int, taxa: int) -> float:
    """Ganho que põe a nota desta altura no volume alvo (limitado a ±12 dB)."""
    nivel = max(nivel_nota_timbre(timbre, int(altura), taxa), 1e-9)
    return float(min(ALVO_PERCEBIDO / nivel, 50.0))


def ganho_gm(programa: int, taxa: int, bateria: bool = False) -> float:
    """Nível fixo por instrumento GM (baixo, voz, bateria) medido numa nota de referência."""
    alt = 38 if bateria else (40 if programa in range(32, 40) else 60)
    return _ganho_calibrado(("gm", programa, bateria, taxa),
                            lambda: render_gm(alt, 0.6, 127, programa, taxa, bateria=bateria))
