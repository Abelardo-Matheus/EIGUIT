# -*- coding: utf-8 -*-
"""
Biblioteca de partituras do Estudo de Tempo (cache local, separado por conta).

Toda partitura aberta (MIDI ou PDF) fica guardada já analisada. Da próxima vez
basta escolher na lista: abre na hora, sem ler o MIDI de novo e sem gastar
outra leitura de PDF pela IA.

Onde fica:  %APPDATA%\\EIGUIT\\biblioteca\\usuario_<id>\\<id da partitura>\\
    original.mid / original.pdf   cópia do arquivo (reprocessa se o formato mudar)
    original.tempo.json           leitura do PDF pela IA (quando for PDF)
    partitura.pkl                 a análise pronta (compassos, tempos, digitação)
    meta.json                     título, fonte, compassos, BPM, datas
"""
from __future__ import annotations

import hashlib
import json
import os
import pickle
import shutil
import time
from typing import List, Optional

try:
    from . import leitor_partitura as lp
except ImportError:                                   # rodando fora do pacote
    from Estudos import leitor_partitura as lp        # type: ignore

VERSAO_CACHE = 3          # suba quando a análise mudar: o cache antigo é refeito sozinho


def pasta_raiz() -> str:
    base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "EIGUIT", "biblioteca")


def _id_arquivo(caminho: str) -> str:
    h = hashlib.sha1()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()[:16]


class Biblioteca:
    def __init__(self, usuario=None, raiz: Optional[str] = None):
        self.usuario = usuario
        nome = f"usuario_{usuario}" if usuario not in (None, "", 0) else "local"
        self.pasta = os.path.join(raiz or pasta_raiz(), nome)
        os.makedirs(self.pasta, exist_ok=True)

    # ------------------------------------------------------------ consulta
    def listar(self) -> List[dict]:
        itens = []
        for nome in os.listdir(self.pasta):
            meta = os.path.join(self.pasta, nome, "meta.json")
            if os.path.exists(meta):
                try:
                    with open(meta, encoding="utf-8") as f:
                        itens.append(json.load(f))
                except (OSError, ValueError):
                    continue
        return sorted(itens, key=lambda m: m.get("usado", 0), reverse=True)

    # ------------------------------------------------------------ gravação
    def salvar(self, p: lp.Partitura, caminho_origem: Optional[str] = None) -> Optional[str]:
        """Guarda (ou atualiza) a partitura. Devolve o id."""
        origem = caminho_origem or p.arquivo
        if not origem or not os.path.exists(origem):
            return None
        pid = _id_arquivo(origem)
        pasta = os.path.join(self.pasta, pid)
        os.makedirs(pasta, exist_ok=True)
        ext = os.path.splitext(origem)[1].lower() or ".mid"
        destino = os.path.join(pasta, "original" + ext)
        if os.path.abspath(origem) != os.path.abspath(destino):
            shutil.copy2(origem, destino)
            leitura_pdf = os.path.splitext(origem)[0] + ".tempo.json"
            if ext == ".pdf" and os.path.exists(leitura_pdf):
                shutil.copy2(leitura_pdf, os.path.join(pasta, "original.tempo.json"))
        p.arquivo = destino                      # trocar de faixa relê daqui
        copia = lp.Partitura(**{k: getattr(p, k) for k in p.__dataclass_fields__})
        copia._dados_midi = None                 # dados crus do MIDI não precisam ir para o disco
        with open(os.path.join(pasta, "partitura.pkl"), "wb") as f:
            pickle.dump({"versao": VERSAO_CACHE, "partitura": copia}, f, protocol=pickle.HIGHEST_PROTOCOL)
        agora = time.time()
        meta_antiga = self._meta(pid) or {}
        meta = {
            "id": pid, "titulo": p.titulo or os.path.basename(origem), "fonte": p.fonte, "ext": ext,
            "compassos": len(p.compassos), "notas": len(p.notas), "bpm": p.bpm_inicial,
            "faixa": p.faixa_idx, "faixa_nome": p.faixas[p.faixa_idx] if p.faixas else "",
            "nome_arquivo": os.path.basename(origem) if caminho_origem else meta_antiga.get("nome_arquivo", ""),
            "criado": meta_antiga.get("criado", agora), "usado": agora,
        }
        with open(os.path.join(pasta, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
        return pid

    def _meta(self, pid: str) -> Optional[dict]:
        try:
            with open(os.path.join(self.pasta, pid, "meta.json"), encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return None

    # ------------------------------------------------------------ leitura
    def abrir(self, pid: str) -> lp.Partitura:
        pasta = os.path.join(self.pasta, pid)
        meta = self._meta(pid) or {}
        p = None
        try:
            with open(os.path.join(pasta, "partitura.pkl"), "rb") as f:
                pacote = pickle.load(f)
            if pacote.get("versao") == VERSAO_CACHE:
                p = pacote["partitura"]
        except Exception:
            p = None
        if p is None:                                        # cache antigo: refaz do original
            original = os.path.join(pasta, "original" + meta.get("ext", ".mid"))
            if meta.get("ext", ".mid") in (".mid", ".midi", ".kar"):
                p = lp.ler_midi(original, faixa=meta.get("faixa"))
            else:
                p = lp.carregar(original)
            self.salvar(p, original)
        p.arquivo = os.path.join(pasta, "original" + meta.get("ext", ".mid"))
        meta["usado"] = time.time()
        try:
            with open(os.path.join(pasta, "meta.json"), "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=1)
        except OSError:
            pass
        return p

    def remover(self, pid: str) -> None:
        shutil.rmtree(os.path.join(self.pasta, pid), ignore_errors=True)

    # ------------------------------------------------------------ preferências da tela
    @staticmethod
    def ler_preferencias() -> dict:
        try:
            with open(os.path.join(pasta_raiz(), "preferencias_tempo.json"), encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    @staticmethod
    def gravar_preferencias(prefs: dict) -> None:
        try:
            os.makedirs(pasta_raiz(), exist_ok=True)
            with open(os.path.join(pasta_raiz(), "preferencias_tempo.json"), "w", encoding="utf-8") as f:
                json.dump(prefs, f)
        except OSError:
            pass
