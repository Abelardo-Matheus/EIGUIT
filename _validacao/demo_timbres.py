# -*- coding: utf-8 -*-
"""Gera _validacao/previews/demo_timbres.wav: o mesmo riff + solo em cada timbre,
separados por 1 s de silêncio (ordem impressa no terminal).
Rode:  python -m _validacao.demo_timbres"""
import os
import sys
import time
import wave

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from audio import sintetizador as sint  # noqa: E402

AFIN = [64, 59, 55, 50, 45, 40]
BPM = 112
Q = 60 / BPM          # semínima em segundos


def nota(t_q, dur_q, corda, casa, vel=100, tec="", bend=0.0):
    return sint.NotaAudio(t_q * Q, dur_q * Q, AFIN[corda - 1] + casa, vel, bend, tec, corda)


def riff_e_solo():
    n = []
    t = 0.0
    # 2 compassos de riff: palhetada abafada na 6ª solta + power chords
    for rep in range(2):
        for k in range(4):
            n.append(nota(t + k * 0.5, 0.5, 6, 0, 105, "P.M."))
        for casa, (a, b) in ((0, (2, 2)), (3, (5, 5))):
            for c, f in ((6, casa), (5, casa + a), (4, casa + b)):
                n.append(nota(t + 2, 1.0 if casa == 0 else 0.5, c, f, 112))
        for c, f in ((6, 5), (5, 7), (4, 7)):
            n.append(nota(t + 3.5, 0.5, c, f, 112))
        t += 4
    # 2 compassos de solo
    n += [nota(t, 1, 2, 15, 110, "bend 1 tom", 2.0), nota(t + 1, 0.5, 2, 15, 95, "bend 1 tom release", 2.0),
          nota(t + 1.5, 0.5, 2, 12, 100), nota(t + 2, 0.25, 1, 12, 105), nota(t + 2.25, 0.25, 1, 15, 90, "hammer"),
          nota(t + 2.5, 0.25, 1, 12, 90, "pull"), nota(t + 2.75, 0.25, 2, 15, 100),
          nota(t + 3, 0.5, 2, 12, 100), nota(t + 3.5, 0.5, 3, 14, 100)]
    t += 4
    n += [nota(t, 0.5, 3, 12, 100), nota(t + 0.5, 0.5, 3, 14, 95, "slide"), nota(t + 1, 0.25, 2, 12, 100),
          nota(t + 1.25, 0.25, 2, 13, 85, "hammer"), nota(t + 1.5, 0.5, 3, 14, 100),
          nota(t + 2, 2, 2, 12, 110, "vibrato")]
    return n, (t + 4) * Q


def main():
    notas, dur = riff_e_solo()
    ordem = ["sintetico", "clean", "distorcao", "real_clean", "real_crunch", "real_drive", "real_highgain"]
    partes = []
    for tb in ordem:
        t = time.time()
        buf, usado = sint.render_notas(notas, dur, 44100, tb)
        print(f"{sint.nome_timbre(tb):18s} backend={usado:9s} {time.time() - t:.2f}s")
        partes += [buf, np.zeros((44100, 2), np.float32)]
    x = (np.clip(np.concatenate(partes), -1, 1) * 32000).astype(np.int16)
    os.makedirs(os.path.join(os.path.dirname(__file__), "previews"), exist_ok=True)
    alvo = os.path.join(os.path.dirname(__file__), "previews", "demo_timbres.wav")
    with wave.open(alvo, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(x.tobytes())
    print("->", alvo, f"({len(x) / 44100:.1f} s; cada trecho {dur:.1f} s + 1 s de pausa)")


if __name__ == "__main__":
    main()
