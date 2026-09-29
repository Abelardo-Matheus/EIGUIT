# -*- coding: utf-8 -*-
"""Testes do ESTUDOS > Tempo.  Rode:  python -m _validacao.teste_tempo"""
import os
import struct
import sys
import tempfile
from fractions import Fraction as F

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from Estudos import leitor_partitura as lp  # noqa: E402

PPQ = 480


def _vlq(v):
    b = [v & 0x7F]
    v >>= 7
    while v:
        b.insert(0, (v & 0x7F) | 0x80)
        v >>= 7
    return bytes(b)


def _trilha(eventos):
    eventos = sorted(eventos, key=lambda e: (e[0], e[1]))
    out, ult = b"", 0
    for t, _ord, dados in eventos:
        out += _vlq(t - ult) + dados
        ult = t
    out += b"\x00\xff\x2f\x00"
    return b"MTrk" + struct.pack(">I", len(out)) + out


def gerar_midi(caminho, jitter=0):
    import random
    rnd = random.Random(5)
    q = lambda x: int(round(x * PPQ))
    qh = lambda x: max(0, q(x) + (rnd.randint(-jitter, jitter) if jitter else 0))
    meta = [(0, 0, b"\xff\x03\x05Tempo"),
            (0, 0, b"\xff\x51\x03" + (600000).to_bytes(3, "big")),     # 100 BPM
            (0, 0, b"\xff\x58\x04\x04\x02\x18\x08"),                     # 4/4
            (q(12), 0, b"\xff\x58\x04\x03\x02\x18\x08"),                 # 3/4 no compasso 4
            (q(15), 0, b"\xff\x51\x03" + (750000).to_bytes(3, "big")),   # 80 BPM no compasso 5
            (q(15), 0, b"\xff\x58\x04\x04\x02\x18\x08")]
    notas = []   # (inicio_q, dur_q, pitch)
    # C1: 8 colcheias
    for i, p in enumerate([64, 67, 69, 67, 64, 62, 60, 62]):
        notas.append((F(i, 2), F(1, 2), p))
    # C2 t1: 4 semicolcheias
    b = F(4)
    for i, p in enumerate([64, 65, 67, 69]):
        notas.append((b + F(i, 4), F(1, 4), p))
    # C2 t2: tercina de colcheias
    for i, p in enumerate([72, 71, 69]):
        notas.append((b + 1 + F(i, 3), F(1, 3), p))
    # C2 t3: fusa + semicolcheia + 5 fusas
    offs = [F(0), F(1, 8), F(3, 8), F(4, 8), F(5, 8), F(6, 8), F(7, 8)]
    durs = [F(1, 8), F(1, 4)] + [F(1, 8)] * 5
    for o, d, p in zip(offs, durs, [76, 74, 72, 74, 76, 77, 76]):
        notas.append((b + 2 + o, d, p))
    # C2 t4: colcheia pontuada + semicolcheia
    notas += [(b + 3, F(3, 4), 69), (b + 3 + F(3, 4), F(1, 4), 67)]
    # C3 t1: septina
    b = F(8)
    for i, p in enumerate([64, 65, 67, 69, 71, 72, 74]):
        notas.append((b + F(i, 7), F(1, 7), p))
    # C3 t2: semínima com bend 1 tom ; t3-4: mínima em acorde (A5)
    notas.append((b + 1, F(1), 69))
    for p in (45, 52, 57):
        notas.append((b + 2, F(2), p))
    # C4 (3/4): semínima pontuada + colcheia + semínima
    b = F(12)
    notas += [(b, F(3, 2), 64), (b + F(3, 2), F(1, 2), 62), (b + 2, F(1), 60)]
    # C5 (4/4, 80 BPM): pausa no tempo 1 + 3 semínimas
    b = F(15)
    notas += [(b + 1, F(1), 55), (b + 2, F(1), 57), (b + 3, F(1), 59)]

    gtr = [(0, 0, b"\xff\x03\x08Guitarra"), (0, 1, b"\xc0\x1d")]
    for ini, dur, p in notas:
        a = qh(ini)
        gtr.append((a, 3, bytes([0x90, p, 96])))
        gtr.append((max(a + 10, qh(ini + dur) - (jitter * 3 if jitter else 0)), 2, bytes([0x80, p, 0])))
    # bend de +2 semitons (alcance padrão 2) na nota do C3 t2
    gtr.append((q(F(9)) + 120, 4, bytes([0xE0, 0x7F, 0x7F])))
    gtr.append((q(F(10)), 1, bytes([0xE0, 0x00, 0x40])))
    bat = [(q(F(i)), 3, bytes([0x99, 36, 100])) for i in range(19)] + \
          [(q(F(i)) + 60, 2, bytes([0x89, 36, 0])) for i in range(19)]

    cab = b"MThd" + struct.pack(">IHHH", 6, 1, 3, PPQ)
    with open(caminho, "wb") as f:
        f.write(cab + _trilha(meta) + _trilha(gtr) + _trilha(bat))


def testar():
    tmp = os.path.join(tempfile.gettempdir(), "teste_tempo.mid")
    gerar_midi(tmp)
    p = lp.ler_midi(tmp)
    erros = []

    def ok(cond, msg):
        if not cond:
            erros.append(msg)

    ok(p.faixas and "Guitarra" in p.faixas[p.faixa_idx], f"faixa padrão errada: {p.faixas}")
    ok(len(p.compassos) == 5, f"esperava 5 compassos, veio {len(p.compassos)}")
    ok([c.formula for c in p.compassos] == ["4/4", "4/4", "4/4", "3/4", "4/4"],
       f"fórmulas: {[c.formula for c in p.compassos]}")
    ok(p.bpm_inicial == 100 and p.compassos[4].bpm == 80, f"bpm: {p.mapa_bpm}")
    c1, c2, c3, c4, c5 = p.compassos
    ok(all(t.grade == 2 and t.descricao == "2 colcheias" for t in c1.tempos),
       f"C1: {[(t.grade, t.descricao) for t in c1.tempos]}")
    ok(c2.tempos[0].grade == 4 and c2.tempos[0].descricao == "4 semicolcheias", f"C2t1 {c2.tempos[0].descricao}")
    ok(c2.tempos[1].grade == 3 and c2.tempos[1].quialtera == "tercina", f"C2t2 {c2.tempos[1].grade}")
    ok(c2.tempos[1].grupos_quialtera and c2.tempos[1].grupos_quialtera[0][2] == 3,
       f"C2t2 grupo {c2.tempos[1].grupos_quialtera}")
    ok(c2.tempos[2].grade == 8 and c2.tempos[2].descricao == "fusa + semicolcheia + 5 fusas",
       f"C2t3 {c2.tempos[2].descricao}")
    ok(c2.tempos[2].celulas[2] == "—", f"C2t3 células {c2.tempos[2].celulas}")
    ok(c2.tempos[3].descricao == "colcheia pontuada + semicolcheia", f"C2t4 {c2.tempos[3].descricao}")
    ok(c3.tempos[0].grade == 7 and c3.tempos[0].quialtera == "septina", f"C3t1 {c3.tempos[0].grade}")
    ok(c3.tempos[0].grupos_quialtera and c3.tempos[0].grupos_quialtera[0][2] == 7,
       f"C3t1 grupo {c3.tempos[0].grupos_quialtera}")
    nota_bend = [n for n in p.notas if n.inicio == 9][0]
    ok(nota_bend.tecnica == "bend 1 tom", f"bend: {nota_bend.tecnica} {nota_bend.bend_semitons}")
    acorde = [n for n in p.notas if n.inicio == 10]
    ok(len(acorde) == 3 and len({n.corda for n in acorde}) == 3, "acorde sem cordas distintas")
    ok(c3.tempos[3].descricao == "continua", f"C3t4 {c3.tempos[3].descricao}")
    ok(c4.tempos[0].descricao == "semínima" and c4.tempos[1].descricao == "continua + colcheia",
       f"C4 {[t.descricao for t in c4.tempos]}")
    ok(c5.tempos[0].descricao.startswith("pausa"), f"C5t1 {c5.tempos[0].descricao}")
    for n in p.notas:
        ok(n.corda is not None and n.casa is not None and 0 <= n.casa <= 24, f"sem digitação: {n}")
        if n.corda:
            ok(p.afinacao[n.corda - 1] + n.casa == n.altura, f"digitação não bate: {n}")
    # tempo -> segundos
    ok(abs(p.segundos(F(15)) - 15 * 0.6) < 1e-9, "segundos() errado")
    ok(abs(p.segundos(F(16)) - (9 + 0.75)) < 1e-9, "segundos() após troca de BPM errado")
    ok(abs(float(p.q_de_segundos(9.75)) - 16) < 1e-4, "q_de_segundos() errado")

    # PDF (JSON simulado): soma que não fecha precisa virar alerta
    js = {"titulo": "t", "bpm": 90, "compassos": [
        {"numero": 1, "formula": "4/4", "eventos": [
            {"tempo": 1, "inicio": "0", "duracao": "1", "notas": [{"corda": 1, "casa": 5}]},
            {"tempo": 2, "inicio": "0", "duracao": "1/2", "notas": [{"corda": 2, "casa": 8}]},
            {"tempo": 2, "inicio": "1/2", "duracao": "1/2", "notas": [{"corda": 2, "casa": 8, "ligada_da_anterior": True}]},
            {"tempo": 3, "inicio": "0", "duracao": "1/3", "notas": [{"corda": 1, "casa": 12}]},
            {"tempo": 3, "inicio": "1/3", "duracao": "1/3", "notas": [{"corda": 1, "casa": 10}]},
            {"tempo": 3, "inicio": "2/3", "duracao": "1/3", "pausa": True, "notas": []},
            {"tempo": 4, "inicio": "0", "duracao": "1/2", "notas": [{"corda": 3, "casa": 7}]}]},
        {"numero": 2, "formula": "4/4", "eventos": [
            {"tempo": 1, "inicio": "0", "duracao": "4", "notas": [{"corda": 6, "casa": 0}]}]}]}
    pj = lp.partitura_de_json(js, "x.pdf")
    ok(pj.compassos[0].alertas and "3.5" in pj.compassos[0].alertas[-1], f"alerta de soma: {pj.compassos[0].alertas}")
    ok(not pj.compassos[1].alertas, f"C2 json não deveria alertar: {pj.compassos[1].alertas}")
    n28 = [n for n in pj.notas if n.corda == 2][0]
    ok(n28.duracao == 1, f"ligadura não somou: {n28.duracao}")
    ok(pj.compassos[0].tempos[2].quialtera == "tercina", "tercina do json")
    ok("pausa" in pj.compassos[0].tempos[3].descricao, f"pausa final: {pj.compassos[0].tempos[3].descricao}")

    # fluxo do PDF com a API simulada (lotes de páginas + continuação da numeração)
    try:
        from PIL import Image
        pdf = os.path.join(tempfile.gettempdir(), "teste_tempo.pdf")
        pgs = [Image.new("RGB", (200, 280), "white") for _ in range(3)]
        pgs[0].save(pdf, "PDF", save_all=True, append_images=pgs[1:])
        cache = os.path.splitext(pdf)[0] + ".tempo.json"
        if os.path.exists(cache):
            os.remove(cache)
        pedidos = []

        def falso(chave, modelo, b64, texto):
            pedidos.append(texto)
            n = 1 if len(pedidos) == 1 else 2
            return '```json\n' + __import__("json").dumps({"bpm": 72 if n == 1 else None, "compassos": [
                {"numero": n, "formula": "4/4", "eventos": [
                    {"tempo": 1, "inicio": "0", "duracao": "4", "notas": [{"corda": 5, "casa": 3}]}]}]}) + '\n```'
        orig = lp._chamar_claude
        lp._chamar_claude = falso
        try:
            pp = lp.ler_pdf(pdf, chave="x")
        finally:
            lp._chamar_claude = orig
        ok(len(pedidos) == 2 and "páginas 3 a 3" in pedidos[1] and "a partir do 2" in pedidos[1], f"lotes: {pedidos}")
        ok(len(pp.compassos) == 2 and pp.bpm_inicial == 72, "pdf simulado")
        ok(pp.notas[0].altura == 48, f"afinação/casa -> altura: {pp.notas[0].altura}")
        ok(os.path.exists(cache), "cache .tempo.json não foi salvo")
    except ImportError:
        pass

    # MIDI "tocado ao vivo": ataques fora da grade (±20 ticks) e notas mais curtas
    tmp_h = os.path.join(tempfile.gettempdir(), "teste_tempo_humano.mid")
    gerar_midi(tmp_h, jitter=20)
    ph = lp.ler_midi(tmp_h)
    ch = ph.compassos
    ok(any("humano" in a for a in ph.avisos), "MIDI humano deveria ser quantizado")
    ok([t.descricao for t in ch[0].tempos] == ["2 colcheias"] * 4, f"humano C1: {[t.descricao for t in ch[0].tempos]}")
    ok(ch[1].tempos[0].descricao == "4 semicolcheias", f"humano C2t1: {ch[1].tempos[0].descricao}")
    ok(ch[1].tempos[1].quialtera == "tercina", f"humano C2t2: {ch[1].tempos[1].descricao}")
    ok(ch[1].tempos[3].descricao == "colcheia pontuada + semicolcheia", f"humano C2t4: {ch[1].tempos[3].descricao}")
    ok(all(t.grade <= 12 for c in ch for t in c.tempos), "humano: sobrou grade estranha")

    md = lp.relatorio_markdown(p)
    ok("### Compasso 2" in md and "fusa + semicolcheia + 5 fusas" in md, "relatório")

    # áudio (sem pygame)
    try:
        from audio import motor_tempo as mt
        buf, dur = mt.renderizar(p, F(4), F(8), bpm=100, taxa=44100, canais=2)
        ok(abs(dur - 2.4) < 1e-6 and buf.shape == (int(round(2.4 * 44100)), 2), f"render {dur} {buf.shape}")
        ok(buf.max() > 1000, "render silencioso")
        buf2, dur2 = mt.renderizar(p, F(4), F(8), bpm=50, taxa=44100, canais=2)
        ok(abs(dur2 - 4.8) < 1e-6, f"render em 50 BPM: {dur2}")
        # sintetizador compartilhado
        from audio import sintetizador as sint
        ok_sf, motivo = sint.soundfont_disponivel()
        notas = [sint.NotaAudio(0.0, 0.5, 64, 100, corda=1), sint.NotaAudio(0.25, 0.5, 67, 100, corda=1),
                 sint.NotaAudio(0.6, 0.8, 69, 100, bend=2.0, tecnica="bend 1 tom", corda=2),
                 sint.NotaAudio(1.2, 0.2, 52, 100, tecnica="dead note", corda=5)]
        b_sin, u_sin = sint.render_notas(notas, 2.0, 44100, "sintetico")
        ok(u_sin == "sintetico" and b_sin.shape == (88200, 2) and b_sin.max() > 0.1, "backend sintético")
        if ok_sf:
            info = {}
            b, d = mt.renderizar(p, F(4), F(8), bpm=100, taxa=44100, canais=2, timbre="clean", info=info)
            ok(info.get("backend") == "soundfont" and b.shape == (int(round(2.4 * 44100)), 2) and b.max() > 1000,
               f"render SoundFont: {info} {b.shape}")
            b_sf, u_sf = sint.render_notas(notas, 2.0, 44100, "distorcao", loop=True)
            ok(u_sf == "soundfont" and b_sf.shape == (88200, 2), "render_notas SoundFont")
        else:
            print(f"(aviso) SoundFont não testado: {motivo}")
        ok_sm, motivo_sm = sint.sampler_disponivel()
        if ok_sm:
            import numpy as np
            for tb in ("real_clean", "real_highgain", "real_di"):
                b_sm, u_sm = sint.render_notas(notas, 2.0, 44100, tb, loop=True)
                ok(u_sm == "sampler" and b_sm.shape == (88200, 2) and not np.isnan(b_sm).any()
                   and abs(b_sm).max() > 0.3, f"sampler {tb}: {u_sm} {b_sm.shape}")
            # afinação: A4 pelo sampler DI deve dar ~440 Hz
            b_a, _ = sint.render_notas([sint.NotaAudio(0, 1.5, 69, 100, corda=1)], 1.6, 44100, "real_di", dobrar=False)
            x = b_a[8820:52920, 0] * np.hanning(44100)
            fr = np.fft.rfftfreq(1 << 18, 1 / 44100)
            sp = np.abs(np.fft.rfft(x, 1 << 18))
            m = (fr > 300) & (fr < 600)
            ok(abs(fr[m][sp[m].argmax()] - 440) < 4, "afinação do sampler")
            info = {}
            mt.renderizar(p, F(4), F(8), bpm=100, taxa=44100, canais=2, timbre="real_crunch", info=info)
            ok(info.get("backend") == "sampler", f"motor_tempo com sampler: {info}")
        else:
            print(f"(aviso) sampler não testado: {motivo_sm}")
    except ImportError as e:
        erros.append(f"motor de áudio: {e}")

    if erros:
        print("FALHAS:")
        for e in erros:
            print("  -", e)
        return False
    print(f"OK — {len(p.compassos)} compassos, {len(p.notas)} notas, todos os testes passaram.")
    return True


if __name__ == "__main__":
    sys.exit(0 if testar() else 1)
