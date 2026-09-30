# -*- coding: utf-8 -*-
"""
Importa uma tablatura do Songsterr para o Estudo de Tempo, pelo nome da música.

Caminho: busca (o mesmo SongsterrAPI da aba MÚSICAS) -> escolhe a música ->
escolhe a faixa (guitarra, baixo...) -> baixa o JSON da faixa, que é o mesmo que
o site usa para desenhar: corda, casa, ritmo (com quiálteras), técnicas e
afinação exatos. Não precisa adivinhar digitação como no MIDI.

Se o JSON não vier, cai no MIDI da música (SongsterrAPI.baixar_midi).
Uso pessoal de estudo: o conteúdo pertence ao Songsterr e aos autores.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from typing import List, Optional

CDN = "https://dqsljvtekg760.cloudfront.net"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


def _api():
    from core.modulos.modulo_songsterr import SongsterrAPI
    return SongsterrAPI()


def _baixar_json(url: str, referer: str = "https://www.songsterr.com/") -> Optional[dict]:
    try:
        import requests
        r = requests.get(url, headers={"User-Agent": UA, "Referer": referer}, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    try:                                              # mesmo plano B do SongsterrAPI
        res = subprocess.run(["curl.exe" if os.name == "nt" else "curl", "-L", "-s", "-A", UA,
                              "-H", f"Referer: {referer}", url],
                             capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=20)
        if res.stdout.strip().startswith(("{", "[")):
            return json.loads(res.stdout)
    except Exception:
        pass
    return None


def buscar(texto: str) -> List[dict]:
    """-> [{id, titulo, artista}]"""
    saida = []
    for item in _api().buscar_musicas(texto) or []:
        sid = item.get("songId") or item.get("id")
        if sid:
            saida.append({"id": sid, "titulo": item.get("title", "?"), "artista": item.get("artist", "")})
    return saida


def faixas(song_id) -> tuple:
    """-> (meta, [{indice, nome, instrumento, afinacao, cordas}])"""
    meta = _api().obter_detalhes_completos(song_id) or {}
    lista = []
    for i, t in enumerate(meta.get("tracks") or []):
        lista.append({
            "indice": i, "partId": t.get("partId", i),
            "nome": t.get("name") or t.get("title") or f"Faixa {i + 1}",
            "instrumento": t.get("instrument") or "",
            "afinacao": t.get("tuning") or [],
            "percussao": bool(t.get("isDrums") or "drum" in str(t.get("instrument", "")).lower()),
        })
    return meta, lista


def _nome_arquivo(meta: dict, faixa: dict) -> str:
    base = f"{meta.get('artist', '')} - {meta.get('title', '')} ({faixa.get('nome', '')})"
    base = re.sub(r'[\\/:*?"<>|]+', "", base).strip(" -") or "songsterr"
    pasta = os.path.join(tempfile.gettempdir(), "EIGUIT_songsterr")
    os.makedirs(pasta, exist_ok=True)
    return os.path.join(pasta, base)


def baixar_faixa(meta: dict, faixa: dict) -> str:
    """Baixa a faixa e devolve um caminho que o leitor abre (.songsterr.json ou .mid)."""
    song_id = meta.get("songId")
    rev = meta.get("revisionId")
    imagem = meta.get("image")
    referer = f"https://www.songsterr.com/a/wsa/song-tab-s{song_id}"
    parte = None
    if song_id and rev and imagem is not None:
        parte = _baixar_json(f"{CDN}/{song_id}/{rev}/{imagem}/{faixa['partId']}.json", referer)
    if parte and parte.get("measures"):
        caminho = _nome_arquivo(meta, faixa) + ".songsterr.json"
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump({"meta": {k: meta.get(k) for k in ("songId", "revisionId", "artist", "title")},
                       "parte": parte}, f)
        return caminho
    # plano B: MIDI da música inteira (a digitação volta a ser sugerida)
    midi = _api().baixar_midi(rev, song_id) if rev else None
    if midi:
        return midi
    raise RuntimeError("Não consegui baixar essa faixa do Songsterr (sem internet ou o site mudou).")
