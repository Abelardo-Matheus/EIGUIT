# -*- coding: utf-8 -*-
"""
Cursor do ESTUDOS > Tempo x som que sai da placa (sem placa de som: canal simulado).

Reproduz o defeito antigo: tocando em pedaços, a linha do tempo avançava 3 s a cada
quadro em que o pedaço não cabia na fila, e o cursor pulava para o lugar errado / para
o fim com a música ainda tocando. Também testa quadros engasgados (render em 2º plano).

    python3 _validacao/teste_cursor_tempo.py
"""
import os
import random
import sys
import types

import numpy as np

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, RAIZ)
TAXA = 44100


class _Relogio:
    t = 100.0

    def perf_counter(self):
        return self.t


class _Som:
    def __init__(self, arr):
        self.n = len(arr)


class _Canal:
    """Canal do pygame simulado: toca um som e o da fila emenda sem buraco."""

    def __init__(self, rel):
        self.rel, self.cur, self.q, self.fim, self.ini, self.consumido = rel, None, None, 0.0, 0.0, 0.0

    def _andar(self):
        while self.cur is not None and self.rel.t >= self.fim:
            self.consumido += self.cur.n / TAXA
            if self.q is not None:
                self.cur, self.q = self.q, None
                self.ini, self.fim = self.fim, self.fim + self.cur.n / TAXA
            else:
                self.cur = None

    def verdade(self):
        self._andar()
        return self.consumido + ((self.rel.t - self.ini) if self.cur is not None else 0.0)

    def play(self, som):
        self.cur, self.q, self.ini, self.fim = som, None, self.rel.t, self.rel.t + som.n / TAXA

    def queue(self, som):
        self._andar()
        if self.cur is None:
            self.play(som)
        else:
            self.q = som

    def get_queue(self):
        self._andar()
        return self.q

    def get_busy(self):
        self._andar()
        return self.cur is not None

    def stop(self):
        self.cur = self.q = None

    def set_volume(self, v):
        pass


def rodar(loop, engasgo, render_lento, dur=40.0, semente=3):
    from audio import motor_tempo as mt
    rel = _Relogio()
    mt_time = mt.time
    mt.time = types.SimpleNamespace(perf_counter=rel.perf_counter)
    pg_antigo = sys.modules.get("pygame")
    pg = types.ModuleType("pygame")
    pg.sndarray = types.SimpleNamespace(make_sound=_Som)
    sys.modules["pygame"] = pg
    try:
        r = mt.Reprodutor()
        canal = _Canal(rel)
        r.canal, r._garantir, r.latencia = canal, (lambda: None), 0.0
        r.formato = staticmethod(lambda: (TAXA, 2))
        pronto = {"ate": 0}

        def obter(i0, i1):
            if render_lento and i1 > pronto["ate"]:
                return None
            return np.zeros((i1 - i0, 2), np.int16)

        rng = random.Random(semente)
        r.tocar_em_pedacos(obter, int(dur * TAXA), loop, 0.0)
        ini, erros = rel.t, []
        while rel.t - ini < dur + 5:
            rel.t += 1 / 60 + (rng.uniform(0.1, 0.5) if rng.random() < engasgo else 0.0)
            pronto["ate"] = int((rel.t - ini) * 0.9 * TAXA) + 3 * TAXA      # render mais lento que o tempo real
            if not r.atualizar():
                break
            e = r.posicao() - canal.verdade()
            if loop:
                e = (e + dur / 2) % dur - dur / 2
            erros.append(abs(e))
        return max(erros)
    finally:
        mt.time = mt_time
        if pg_antigo is not None:
            sys.modules["pygame"] = pg_antigo
        else:
            sys.modules.pop("pygame", None)


def main():
    falhas = 0
    for loop in (False, True):
        for engasgo in (0.0, 0.05):
            for lento in (False, True):
                erro = rodar(loop, engasgo, lento)
                # num quadro engasgado o cursor só pode errar o próprio engasgo (≤ 0,5 s)
                limite = 0.02 if not engasgo else 0.55
                ok = erro <= limite
                falhas += not ok
                print(f"  {'ok  ' if ok else 'FALHA'}  loop={loop!s:5} engasgos={engasgo:.2f} render_lento={lento!s:5} "
                      f"erro máx do cursor {erro * 1000:.0f} ms")
    print(f"\n[teste_cursor_tempo] {'todos passaram' if not falhas else f'{falhas} falha(s)'}")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
