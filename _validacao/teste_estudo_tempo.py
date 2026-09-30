# -*- coding: utf-8 -*-
"""
Suite do Estudo de Tempo e do som profissional da tablatura.

Estudo de Tempo: abre pelo gerenciador de estudos (cartao e sub-aba), carrega
um MIDI de teste, separa os compassos em tempos certos, seleciona compasso com
clique, toca em loop com metronomo, ESC para o audio. Tela em tres resolucoes
e nos dois temas.

Motor da tablatura (audio/tab_synth.py): os tres modos tocam os quatro
instrumentos, o botao de som percorre os timbres, a celula da grade e lida do
mesmo jeito que o GerenciadorDadosTablatura le, e o play da grade manda a
duracao em segundos.
"""
import os
import tempfile
import time
from fractions import Fraction

# a suite nunca mexe na biblioteca de verdade do usuario
os.environ['APPDATA'] = tempfile.mkdtemp(prefix='eiguit_teste_bib_')

import pygame

import harness
from harness import Contexto, Suite

import core.modulos.modulos_estudos as modulo_estudos
from Estudos import leitor_partitura as lp
from audio import sintetizador as sint

s = Suite('teste_estudo_tempo')

MIDI = os.path.join(tempfile.gettempdir(), 'eiguit_teste_tempo.mid')


def _gerar_midi():
    import teste_leitor_tempo
    teste_leitor_tempo.gerar_midi(MIDI)


# ------------------------------------------------------------ leitura --
def leitura_do_midi():
    _gerar_midi()
    p = lp.carregar(MIDI)
    s.checar([c.formula for c in p.compassos] == ['4/4', '4/4', '4/4', '3/4', '4/4'], 'formulas erradas')
    t = p.compassos[1].tempos
    s.checar(t[1].quialtera == 'tercina' and t[2].descricao == 'fusa + semicolcheia + 5 fusas',
             f'tempos do compasso 2: {[x.descricao for x in t]}')
    s.checar(p.bpm_inicial == 100, 'bpm da partitura nao lido')


# ------------------------------------------------------------ interface --
def _abrir(ctx, nome='Estudo de Tempo'):
    ger = modulo_estudos.GerenciadorEstudos()
    ctx.estado.tela_estudo_ativa = True
    ctx.estado.estudo_ativo = nome
    ger.desenhar_tela_estudo(ctx.tela, ctx.largura, ctx.altura, ctx.estado, ctx.fontes)
    return ger, ger.modulo_tempo


def _quadro(ger, ctx):
    ger.desenhar_tela_estudo(ctx.tela, ctx.largura, ctx.altura, ctx.estado, ctx.fontes)


def interface(largura, altura, tema):
    ctx = Contexto(largura, altura, tema)
    ger, m = _abrir(ctx)
    s.checar(m is not None, 'o gerenciador nao abriu o Estudo de Tempo')
    m._aplicar_partitura(lp.carregar(MIDI))
    s.checar(m.bpm == 100, 'o metronomo nao foi para o BPM da partitura')
    _quadro(ger, ctx)
    s.checar(m.diag is not None and len(m.diag.sistemas) >= 1, 'a partitura nao foi desenhada')

    # clique no 2o compasso seleciona ele
    _, vista, _ = m._areas()
    si, k = m.diag.onde[1]
    cl = m.diag.sistemas[si]['comps'][k]
    pos = (int(vista.x + 12 + cl['x'] + cl['w'] / 2),
           int(vista.y + 14 - m.scroll + m.diag.sistemas[si]['y'] + m.diag.head + 30))
    ger.tratar_eventos(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': pos, 'button': 1}), pos, ctx.estado)
    ger.tratar_eventos(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': pos, 'button': 1}), pos, ctx.estado)
    s.checar(m.sel == (1, 1), f'clique no compasso 2 nao selecionou (sel={m.sel})')

    # espaco toca o trecho em loop
    ger.tratar_eventos(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_SPACE, 'unicode': ' ', 'mod': 0}),
                       (0, 0), ctx.estado)
    limite = time.time() + 20
    while time.time() < limite and not m.rep.tocando:
        _quadro(ger, ctx)
        time.sleep(0.02)
    s.checar(m.rep.tocando, 'o play nao comecou')
    s.checar(m._atual[1] > 2.3 and m._atual[1] < 2.5, 'o loop nao tem a duracao de 1 compasso a 100 BPM')
    _quadro(ger, ctx)

    reprodutor = m.rep
    ger.tratar_eventos(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_ESCAPE, 'unicode': '', 'mod': 0}),
                       (0, 0), ctx.estado)
    s.checar(ger.modulo_tempo is None, 'ESC nao soltou o modulo de tempo')
    s.checar(reprodutor.tocando is False, 'ESC nao parou o audio')


def sub_aba_e_cartao():
    ctx = Contexto()
    secao = [x for x in ctx.estado.secoes_inferiores if x['conteudo'] == 'estudos'][0]
    s.checar('Tempo' in secao['sub_abas'], 'sub-aba Tempo nao esta em ESTUDOS')
    from ui.components import bottom_nav
    ctx.estado.botoes_estudo = {}
    bottom_nav._desenhar_aba_estudos(ctx.tela, 0, 0, 1200, ctx.estado, ctx.fontes,
                                     secao['sub_abas'].index('Tempo'), ctx.configs)
    s.checar('Estudo de Tempo' in ctx.estado.botoes_estudo, 'cartao Estudo de Tempo nao apareceu')
    s.checar('Estudo de Tempo' in modulo_estudos.NOMES_TEMPO, 'nome do cartao nao abre o estudo')


def biblioteca_da_conta():
    ctx = Contexto(1600, 900)
    ctx.estado.usuario_id_logado = 42
    ger, m = _abrir(ctx)
    m.abrir(MIDI)
    limite = time.time() + 20
    while time.time() < limite and not m.p:
        _quadro(ger, ctx)
        time.sleep(0.02)
    s.checar(m.p is not None, 'o MIDI nao abriu')
    s.checar(len(m._itens_bib) == 1 and m._id_atual, 'o MIDI aberto nao foi guardado na biblioteca')
    s.checar('usuario_42' in m.bib.pasta, 'a biblioteca nao e separada por conta')
    # outra conta nao ve a partitura
    ctx2 = Contexto(1600, 900)
    ctx2.estado.usuario_id_logado = 7
    ger2, m2 = _abrir(ctx2)
    s.checar(len(m2._itens_bib) == 0, 'a biblioteca de uma conta apareceu em outra')
    # mesma conta, estudo novo (programa reaberto): lista aparece e abre com um clique
    ctx3 = Contexto(1600, 900)
    ctx3.estado.usuario_id_logado = 42
    ger3, m3 = _abrir(ctx3)
    _quadro(ger3, ctx3)
    s.checar(len(m3._itens_bib) == 1 and m3._rects_bib, 'a lista da biblioteca nao apareceu')
    r = [r for r, acao, _ in m3._rects_bib if acao == 'abrir'][0]
    ger3.tratar_eventos(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': r.center, 'button': 1}),
                        r.center, ctx3.estado)
    limite = time.time() + 10
    while time.time() < limite and not m3.p:
        _quadro(ger3, ctx3)
        time.sleep(0.01)
    s.checar(m3.p is not None and len(m3.p.compassos) == 5, 'nao abriu pela biblioteca')
    s.checar(m3.p.compassos[1].tempos[2].descricao == 'fusa + semicolcheia + 5 fusas',
             'a partitura da biblioteca voltou diferente')
    # remover
    rx = [r for r, acao, _ in m3._rects_bib if acao == 'remover'] if m3._rects_bib else []
    m3.remover_da_biblioteca(m3._itens_bib[0]['id'])
    s.checar(len(m3._itens_bib) == 0, 'remover da biblioteca nao funcionou')


def zoom_e_papel():
    ctx = Contexto(1600, 900)
    ger, m = _abrir(ctx)
    m._aplicar_partitura(lp.carregar(MIDI))
    _quadro(ger, ctx)
    h1 = m.diag.alt_sist
    m.mudar_zoom(+0.45)
    _quadro(ger, ctx)
    s.checar(m.diag.alt_sist > h1, 'o zoom nao aumentou a tablatura')
    m.alternar_papel()
    _quadro(ger, ctx)
    m.alternar_papel()


def audio_pronto_e_gaveta():
    ctx = Contexto(1600, 900)
    ger, m = _abrir(ctx)
    m._aplicar_partitura(lp.carregar(MIDI))
    # play logo depois de abrir: espera o audio (com %) e toca sozinho
    m.sel = (0, 0)
    m.play_pause()
    limite = time.time() + 60
    while time.time() < limite and not m.rep.tocando:
        _quadro(ger, ctx)
        time.sleep(0.02)
    s.checar(m.rep.tocando, 'o play dado logo ao abrir nao tocou quando o audio ficou pronto')
    m.parar()
    limite = time.time() + 60
    while time.time() < limite and not m.audio_pronto():
        _quadro(ger, ctx)
        time.sleep(0.02)
    s.checar(m.audio_pronto(), 'o audio da musica inteira nao ficou pronto')
    m.sel = (1, 1)
    t = time.perf_counter()
    m.play_pause()
    _quadro(ger, ctx)
    s.checar(m.rep.tocando and time.perf_counter() - t < 0.5, 'com o audio pronto o play deveria ser imediato')
    m.parar()
    # quadros leves: as linhas ficam prontas em cache
    for _ in range(3):
        _quadro(ger, ctx)
    t = time.perf_counter()
    for _ in range(20):
        _quadro(ger, ctx)
    s.checar((time.perf_counter() - t) / 20 < 0.05, 'desenhar um quadro deveria levar menos de 50 ms')
    # gaveta de sons
    m.alternar_gaveta()
    _quadro(ger, ctx)
    alvo = [r for r, tid in m._rects_gaveta if tid == 'sintetico'][0]
    ger.tratar_eventos(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': alvo.center, 'button': 1}),
                       alvo.center, ctx.estado)
    s.checar(m.timbre == 'sintetico' and not m.gaveta_som, 'a gaveta nao trocou o som')
    v0 = m.rep.volume
    m.mudar_volume(-0.2)
    s.checar(abs(m.rep.volume - max(0.0, v0 - 0.2)) < 1e-6, 'botao de volume do estudo nao mudou o volume')
    m.mudar_volume(+0.2)


def musica_longa_toca_em_pedacos():
    """Play sem selecao numa musica longa, logo ao abrir: comeca antes do audio inteiro ficar pronto."""
    import struct
    import teste_leitor_tempo as tl
    cam = os.path.join(tempfile.gettempdir(), 'eiguit_longa.mid')
    ev = [(0, 0, b"\xff\x51\x03" + (500000).to_bytes(3, "big")), (0, 0, b"\xff\x58\x04\x04\x02\x18\x08")]
    tr = [(0, 0, b"\xff\x03\x08Guitarra")]
    for k in range(60 * 8):                                    # 60 compassos de colcheias (2 min)
        alt = (40, 45, 47, 52, 55, 57, 59, 64)[k % 8]
        tr += [(k * 240, 3, bytes([0x90, alt, 100])), (k * 240 + 200, 2, bytes([0x80, alt, 0]))]
    with open(cam, 'wb') as f:
        f.write(b"MThd" + struct.pack(">IHHH", 6, 1, 2, 480) + tl._trilha(ev) + tl._trilha(tr))
    ctx = Contexto(1600, 900)
    ger, m = _abrir(ctx)
    m.timbre = 'real_clean' if __import__('audio.sintetizador', fromlist=['x']).sampler_disponivel()[0] else 'sintetico'
    m._aplicar_partitura(lp.carregar(cam))
    m.sel = None
    m.play_pause()
    limite = time.time() + 60
    while time.time() < limite and not m.rep.tocando:
        _quadro(ger, ctx)
        time.sleep(0.02)
    s.checar(m.rep.tocando, 'o play sem selecao nao comecou')
    if m.timbre != 'sintetico':
        s.checar(not m.audio_pronto(), 'deveria ter comecado antes do audio inteiro ficar pronto')
    q_ini = m.posicao_q()
    t = time.time()
    while time.time() - t < 1.5:
        _quadro(ger, ctx)
        time.sleep(0.02)
    s.checar(m.posicao_q() > q_ini, 'o cursor nao andou tocando em pedacos')
    m.parar()
    # trocar o som no meio do preparo e dar play: nao pode cair num render pesado em paralelo
    outro = 'real_crunch' if m.timbre == 'real_clean' else 'sintetico'
    m.escolher_timbre(outro)
    m.play_pause()
    limite = time.time() + 60
    while time.time() < limite and not m.rep.tocando:
        _quadro(ger, ctx)
        s.checar(m._render_thread is None or not m._render_thread.is_alive(),
                 'o play gerou um segundo audio em paralelo (era o que travava no 0%)')
        time.sleep(0.02)
    s.checar(m.rep.tocando and m._atual[2][-1] == outro, 'depois de trocar o som o play nao tocou')
    m.parar()


def volume_igual_para_todas_as_notas():
    """Todas as alturas no mesmo volume (antes: ate 9 dB de diferenca entre notas)."""
    import numpy as np
    from audio import amp_guitarra as amp, motor_tempo as mt, sintetizador as sint
    T = 44100
    p = lp.Partitura(titulo='niveis')
    p.mapa_bpm = [(Fraction(0), 120.0)]
    q, notas = Fraction(0), []
    for corda in range(1, 7):
        for casa in (0, 5, 12):
            notas.append(lp.Nota(q, Fraction(1), p.afinacao[corda - 1] + casa, corda, casa, '', 100))
            q += 2
    p.notas = notas
    p.eventos = lp._agrupar_eventos(notas)
    p.compassos = lp._montar_compassos([], q, p)
    lp.analisar(p)
    timbres = ['sintetico'] + (['real_clean', 'real_highgain'] if sint.sampler_disponivel()[0] else [])
    for tb in timbres:
        buf = mt.renderizar_guitarra_completa(p, 120, T, tb)
        niveis = [20 * np.log10(amp.nivel_percebido(buf[i * T:i * T + int(0.35 * T)], T)) for i in range(len(notas))]
        s.checar(max(niveis) - min(niveis) < 3.0, f'{tb}: {max(niveis) - min(niveis):.1f} dB entre notas')
    # motor da tablatura (nota a nota)
    from audio.tab_synth import MotorAudioDual
    m = MotorAudioDual()
    niveis = [20 * np.log10(amp.nivel_percebido(m._render_array(m._chave(c, k, '', 0.5, 100, False))[:int(0.35 * T)], T))
              for c in (1, 3, 6) for k in (0, 7, 15)]
    s.checar(max(niveis) - min(niveis) < 1.5, f'tablatura: {max(niveis) - min(niveis):.1f} dB entre notas')
    # volume geral
    v0 = m.volume_mestre
    from ui.components.gaveta_som import GavetaSom
    g = GavetaSom()
    g.aberta = True
    g.desenhar(pygame.display.get_surface() or pygame.Surface((800, 600)), pygame.Rect(10, 10, 120, 30),
               pygame.font.SysFont(None, 18), m)
    r = [r for r, c in g._itens if c == 'vol-'][0]
    g.tratar_clique(r.center, pygame.Rect(10, 10, 120, 30), m)
    s.checar(abs(m.volume_mestre - max(0.0, v0 - 0.1)) < 1e-6 and g.aberta, 'o volume da gaveta nao mudou')
    m.definir_volume(v0)


def songsterr_simulado():
    import json as _json
    from Estudos import importar_songsterr as imp
    parte = {"name": "Lead", "tuning": [64, 59, 55, 50, 45, 40], "automations": {"tempo": [{"measure": 0, "bpm": 100}]},
             "measures": [{"signature": [4, 4], "voices": [{"beats": [
                 {"duration": [1, 4], "notes": [{"string": 2, "fret": 5}]}] * 4}]}] * 2}
    orig = (imp.buscar, imp.faixas, imp.baixar_faixa)
    alvo = os.path.join(tempfile.gettempdir(), 'Banda - Teste (Lead).songsterr.json')
    imp.buscar = lambda t: [{'id': 1, 'titulo': 'Teste', 'artista': 'Banda'}]
    imp.faixas = lambda i: ({'songId': 1, 'revisionId': 2, 'artist': 'Banda', 'title': 'Teste', 'image': 'x'},
                            [{'indice': 0, 'partId': 0, 'nome': 'Lead', 'instrumento': 'Guitar',
                              'afinacao': [64, 59, 55, 50, 45, 40], 'percussao': False}])

    def baixar(meta, faixa):
        with open(alvo, 'w', encoding='utf-8') as f:
            _json.dump({'meta': meta, 'parte': parte}, f)
        return alvo
    imp.baixar_faixa = baixar
    try:
        ctx = Contexto(1600, 900)
        ger, m = _abrir(ctx)
        m.abrir_songsterr()
        for ch in 'teste':
            ger.tratar_eventos(pygame.event.Event(pygame.KEYDOWN, {'key': 0, 'unicode': ch, 'mod': 0}), (0, 0), ctx.estado)
        s.checar(m.songsterr['texto'] == 'teste', 'digitacao na busca do Songsterr')
        ger.tratar_eventos(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RETURN, 'unicode': '\r', 'mod': 0}),
                           (0, 0), ctx.estado)
        for fase in ('musica', 'faixa'):
            limite = time.time() + 5
            while time.time() < limite and not [r for r, a, _ in m.songsterr['rects'] if a == fase]:
                _quadro(ger, ctx)
                time.sleep(0.02)
            r = [r for r, a, _ in m.songsterr['rects'] if a == fase][0]
            ger.tratar_eventos(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': r.center, 'button': 1}),
                               r.center, ctx.estado)
            _quadro(ger, ctx)
        limite = time.time() + 10
        while time.time() < limite and not (m.p and m.p.fonte == 'songsterr'):
            _quadro(ger, ctx)
            time.sleep(0.02)
        s.checar(m.p is not None and m.p.fonte == 'songsterr' and not m.p.digitacao_sugerida,
                 'a faixa do Songsterr nao abriu')
    finally:
        imp.buscar, imp.faixas, imp.baixar_faixa = orig


def impressao():
    from Estudos import estudo_tempo
    alvo = os.path.join(tempfile.gettempdir(), 'eiguit_tab_teste.pdf')
    n = estudo_tempo.exportar_pdf(lp.carregar(MIDI), alvo)
    s.checar(n >= 1 and os.path.getsize(alvo) > 10000, 'PDF da tablatura nao foi gerado')


# ------------------------------------------------------ motor da tablatura --
def motor_tablatura():
    from audio.tab_synth import MotorAudioDual
    m = MotorAudioDual()
    disp = m.modos_disponiveis()
    s.checar('sintetico' in disp, 'modo sintetico sumiu')
    if sint.sampler_disponivel()[0]:
        s.checar(m.modo == 'profissional', 'o motor deveria comecar no modo profissional')
    for modo in disp:
        m.alternar_modo(modo)
        for inst in ('Guitarra', 'Baixo', 'Voz', 'Bateria'):
            m.alternar_instrumento_synth(inst)
            m.reproduzir_nota(3, 5, 'b', 0.3, 100)
            s.checar(m.canais_cordas[2].get_busy(), f'{modo}/{inst}: nenhuma nota tocando')
        m.alternar_instrumento_synth('Guitarra')
    # o botao percorre todos os sons e volta ao comeco
    vistos = set()
    for _ in range(12):
        vistos.add(m.proximo_som())
    s.checar(len(vistos) >= len(disp), f'o botao de som nao percorre os modos: {vistos}')


def celula_lida_igual_ao_player():
    from audio.tab_synth import MotorAudioDual
    import core.modulos.modulo_dados_tab as dados_tab
    recebido = []
    g = dados_tab.GerenciadorDadosTablatura(bpm=120)
    g.on_note_trigger = lambda *a: recebido.append(a)
    for celula in ('12', '5b', '7hd2v80', '3/~', '0p', '12bd3'):
        recebido.clear()
        g._processar_e_tocar(1, celula)
        casa, tec, cols, vol = MotorAudioDual.ler_celula(celula)
        c, casa_g, tec_g, dur_g, vol_g = recebido[0]
        s.checar((casa, tec, vol) == (casa_g, tec_g, vol_g), f'{celula}: {(casa, tec, vol)} != {(casa_g, tec_g, vol_g)}')
        s.checar(abs(dur_g - cols * 0.125 * 1.5) < 1e-9, f'{celula}: duracao deveria vir em segundos ({dur_g})')


s.teste('leitura ritmica do MIDI', leitura_do_midi)
s.teste('sub-aba Tempo e cartao em ESTUDOS', sub_aba_e_cartao)
s.teste('impressao da tablatura em PDF', impressao)
s.teste('biblioteca de partituras por conta', biblioteca_da_conta)
s.teste('zoom e papel claro', zoom_e_papel)
s.teste('audio da musica pronto, play imediato e gaveta de sons', audio_pronto_e_gaveta)
s.teste('importar do Songsterr pela busca (rede simulada)', songsterr_simulado)
s.teste('musica longa: play logo ao abrir toca em pedacos', musica_longa_toca_em_pedacos)
s.teste('mesmo volume para todas as notas e volume geral', volume_igual_para_todas_as_notas)
s.teste('motor da tablatura: modos, instrumentos e botao de som', motor_tablatura)
s.teste('celula da grade lida igual ao player', celula_lida_igual_ao_player)
for _tema in harness.TEMAS:
    for _l, _a in ((1920, 1080), (1600, 900), (1280, 720)):
        s.teste(f'[{_tema}] interface {_l}x{_a}', lambda l=_l, a=_a, t=_tema: interface(l, a, t))
s.encerrar()
