# -*- coding: utf-8 -*-
"""
Prepara uma biblioteca SFZ de guitarra para o sampler do EIGUIT:
converte os samples para FLAC mono 16-bit (≈ 1/3 do tamanho), reescreve o .sfz
e cria o instrumento.json.

Uso (Emilyguitar, CC0 — https://github.com/sfzinstruments/karoryfer.emilyguitar):
    git clone --depth 1 https://github.com/sfzinstruments/karoryfer.emilyguitar
    python -m audio.preparar_biblioteca karoryfer.emilyguitar assets/audio/guitarra_di
"""
import json
import os
import re
import shutil
import sys

import numpy as np
import soundfile as sf


def preparar(origem: str, destino: str, sfz: str = "emily_basic.sfz") -> None:
    os.makedirs(destino, exist_ok=True)
    with open(os.path.join(origem, sfz), encoding="utf-8", errors="ignore") as f:
        texto = f.read()
    amostras = sorted(set(re.findall(r"sample=([^\r\n]+?\.wav)", texto)))
    total_in = total_out = 0
    for rel in amostras:
        src = os.path.join(origem, rel.replace("\\", "/"))
        dst = os.path.join(destino, os.path.splitext(rel.replace("\\", "/"))[0] + ".flac")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        x, fs = sf.read(src, dtype="float32", always_2d=True)
        x = x.mean(axis=1)
        # corta silêncio final e faz fade curto
        ult = np.nonzero(np.abs(x) > 10 ** (-70 / 20))[0]
        if len(ult):
            x = x[: ult[-1] + 1]
        f = min(len(x), int(0.02 * fs))
        if f:
            x[-f:] *= np.linspace(1, 0, f)
        sf.write(dst, x, fs, subtype="PCM_16", format="FLAC")
        total_in += os.path.getsize(src)
        total_out += os.path.getsize(dst)
    texto = re.sub(r"(sample=[^\r\n]+?)\.wav", r"\1.flac", texto)
    with open(os.path.join(destino, "guitarra.sfz"), "w", encoding="utf-8") as f:
        f.write(texto)
    cfg = {"nome": "Emilyguitar (Karoryfer, CC0) — Epiphone, captação direta",
           "sfz": "guitarra.sfz", "teclas_abafadas": [91, 92, 93, 94, 95], "teclas_ruido": [90, 96]}
    with open(os.path.join(destino, "instrumento.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=1)
    for doc in ("LICENSE", "readme.txt"):
        if os.path.exists(os.path.join(origem, doc)):
            shutil.copyfile(os.path.join(origem, doc), os.path.join(destino, doc))
    print(f"{len(amostras)} samples: {total_in / 1e6:.0f} MB -> {total_out / 1e6:.0f} MB em {destino}")


if __name__ == "__main__":
    preparar(sys.argv[1], sys.argv[2], *(sys.argv[3:4]))
