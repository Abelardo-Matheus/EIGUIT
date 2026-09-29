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
s.teste('motor da tablatura: modos, instrumentos e botao de som', motor_tablatura)
s.teste('celula da grade lida igual ao player', celula_lida_igual_ao_player)
for _tema in harness.TEMAS:
    for _l, _a in ((1920, 1080), (1600, 900), (1280, 720)):
        s.teste(f'[{_tema}] interface {_l}x{_a}', lambda l=_l, a=_a, t=_tema: interface(l, a, t))
s.encerrar()
