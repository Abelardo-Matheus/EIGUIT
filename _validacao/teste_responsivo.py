# -*- coding: utf-8 -*-
"""
Suite do layout responsivo.

O arranjo de abertura vem do canvas de design em fracoes da tela. Aqui se
verifica que, em qualquer resolucao, todo bloco: cabe na area util, respeita o
tamanho minimo, nao fica com coordenada negativa e chega ao estado com as
mesmas medidas que o calculo prometeu.
"""
from harness import Contexto, Suite

import config.layout_padrao as layout
from config.ui_metrics import ALTURA_TOPBAR

s = Suite('teste_responsivo')

RESOLUCOES = [(1024, 600), (1280, 720), (1366, 768), (1600, 900),
              (1920, 1080), (2560, 1440), (3840, 2160)]


def nomes_batem():
    s.checar(set(layout.BLOCOS_REF) == set(layout.MINIMOS),
             'todo bloco do canvas precisa de um tamanho minimo')


def cabe_em_todas_as_resolucoes():
    for largura, altura in RESOLUCOES:
        viewport = max(600, altura - ALTURA_TOPBAR)
        calculado = layout.calcular(largura, viewport)
        s.checar(set(calculado) == set(layout.BLOCOS_REF),
                 f'{largura}x{altura}: faltou bloco no calculo')
        for nome, m in calculado.items():
            min_w, min_h = layout.MINIMOS[nome]
            s.checar(m['x'] >= 0 and m['y'] >= 0,
                     f'{nome} em {largura}x{altura}: coordenada negativa')
            s.checar(m['w'] >= min_w and m['h'] >= min_h,
                     f'{nome} em {largura}x{altura}: menor que o minimo')
            s.checar(m['x'] + m['w'] <= largura,
                     f'{nome} em {largura}x{altura}: passa da largura da tela')
            s.checar(m['y'] + m['h'] <= viewport or m['h'] >= viewport - 20,
                     f'{nome} em {largura}x{altura}: passa da altura util')


def estado_recebe_o_layout():
    for largura, altura in RESOLUCOES:
        ctx = Contexto(largura, altura)
        viewport = max(600, altura - ALTURA_TOPBAR)
        calculado = layout.calcular(largura, viewport)
        for nome, m in calculado.items():
            bloco = getattr(ctx.estado, nome, None)
            s.checar(bloco is not None, f'{nome} nao existe no estado')
            s.checar((bloco.x, bloco.y) == (m['x'], m['y']),
                     f'{nome} em {largura}x{altura}: posicao diferente do calculo')


def voltar_para_o_padrao():
    ctx = Contexto(1600, 900)
    ctx.estado.dragger_graus.x = 5000
    ctx.estado.dragger_capo.altura = 4
    layout.aplicar(ctx.estado)
    s.checar(ctx.estado.dragger_graus.x < 1600, 'o bloco voltou para dentro da tela')
    s.checar(ctx.estado.dragger_capo.altura >= layout.MINIMOS['dragger_capo'][1],
             'o bloco voltou ao tamanho minimo')


def barra_fica_fixa_no_rodape():
    """A barra de abas nao se move: rodape, largura cheia, fora do arrasto."""
    import core.controlador_eventos as controlador
    from ui.components.bottom_nav import MARGEM_BARRA, fixar_barra
    for largura, altura in RESOLUCOES:
        ctx = Contexto(largura, altura)
        viewport = max(600, altura - ALTURA_TOPBAR)
        barra = ctx.estado.dragger_painel_inferior
        # Mesmo empurrada para fora, o desenho a devolve para o rodape
        barra.x, barra.y, barra.largura = 900, 40, 300
        fixar_barra(ctx.estado, largura, viewport)
        s.checar(barra.x == layout.MARGEM_ESQUERDA,
                 f'{largura}x{altura}: a barra nao encostou na coluna')
        s.checar(barra.x + barra.largura <= largura - 1,
                 f'{largura}x{altura}: a barra passa da tela')
        s.checar(barra.y + barra.altura + MARGEM_BARRA <= viewport,
                 f'{largura}x{altura}: a barra passa do rodape')
        s.checar(barra not in controlador.obter_draggers_ativos(ctx.estado),
                 'a barra fixa nao pode entrar na lista de arrastaveis')


def tela_principal_fica_centrada():
    """Com os blocos guardados, braco e controles ficam no meio da area util."""
    for largura, altura in RESOLUCOES:
        viewport = max(600, altura - ALTURA_TOPBAR)
        calculado = layout.calcular(largura, viewport)
        util_x = layout.MARGEM_ESQUERDA
        util_w = largura - util_x - layout.MARGEM_DIREITA
        for nome in ('dragger_guitarra', 'dragger_controles_topo'):
            m = calculado[nome]
            folga_esq = m['x'] - util_x
            folga_dir = util_x + util_w - (m['x'] + m['w'])
            s.checar(abs(folga_esq - folga_dir) <= 2,
                     f'{nome} em {largura}x{altura}: fora do centro '
                     f'({folga_esq} x {folga_dir})')
        topo = calculado['dragger_controles_topo']
        braco = calculado['dragger_guitarra']
        barra = calculado['dragger_painel_inferior']
        s.checar(braco['y'] == topo['y'] + topo['h'] + layout.ESPACO_ENTRE_FIXOS,
                 'o braco fica logo abaixo dos controles do topo')
        acima = topo['y']
        abaixo = barra['y'] - (braco['y'] + braco['h'])
        s.checar(abs(acima - abaixo) <= 2 or acima <= layout.MARGEM_INFERIOR + 1,
                 f'o grupo nao ficou centrado na vertical ({acima} x {abaixo})')


def gaveta_de_baixo_cresce_com_a_tela():
    """A gaveta aberta cresce, mas nunca invade a barra nem sai pelo topo."""
    from ui.components.bottom_nav import (GAP_PAINEL, ALTURA_CAIXA_MIN,
                                          altura_caixa, fixar_barra)
    alturas = []
    for largura, altura in RESOLUCOES:
        ctx = Contexto(largura, altura)
        viewport = max(600, altura - ALTURA_TOPBAR)
        fixar_barra(ctx.estado, largura, viewport)
        caixa = altura_caixa(ctx.estado)
        barra = ctx.estado.dragger_painel_inferior
        topo_da_gaveta = barra.y - caixa - GAP_PAINEL
        s.checar(caixa >= ALTURA_CAIXA_MIN,
                 f'{largura}x{altura}: a gaveta encolheu para {caixa}')
        s.checar(topo_da_gaveta >= 0,
                 f'{largura}x{altura}: a gaveta sai pelo topo ({topo_da_gaveta})')
        s.checar(topo_da_gaveta + caixa <= barra.y,
                 f'{largura}x{altura}: a gaveta invade a barra')
        alturas.append((viewport, caixa))
    menor, maior = alturas[0], alturas[-1]
    s.checar(maior[1] > menor[1],
             f'a gaveta deveria crescer com a tela: {alturas}')


def clique_encontra_a_gaveta_desenhada():
    """A geometria do desenho e a do clique tem de ser a mesma."""
    from ui.components.bottom_nav import GAP_PAINEL, altura_caixa
    from ui import renderizador_ui
    import pygame
    for largura, altura in ((1920, 1080), (1366, 768)):
        ctx = Contexto(largura, altura)
        ctx.estado.secoes_inferiores[0]['expandido'] = True
        tela = pygame.Surface((largura, max(600, altura - ALTURA_TOPBAR)),
                              pygame.SRCALPHA)
        renderizador_ui.desenhar_workspace(
            tela, ctx.estado, ctx.configs, ctx.escalas, ctx.fontes,
            ctx.metronomo, ctx.processador, ctx.gravador, ctx.campo, ctx.jogos)
        desenhado = ctx.estado.secoes_inferiores[0].get('rect_painel')
        s.checar(desenhado is not None, 'a gaveta aberta nao guardou o retangulo')
        barra = ctx.estado.dragger_painel_inferior
        do_clique = pygame.Rect(barra.x, barra.y - altura_caixa(ctx.estado) - GAP_PAINEL,
                                barra.largura, altura_caixa(ctx.estado))
        s.checar(desenhado == do_clique,
                 f'{largura}x{altura}: desenho {desenhado} != clique {do_clique}')


s.teste('todo bloco do canvas tem tamanho minimo', nomes_batem)
s.teste('a barra de abas fica fixa no rodape', barra_fica_fixa_no_rodape)
s.teste('braco e controles ficam centrados', tela_principal_fica_centrada)
s.teste('a gaveta de baixo cresce com a tela', gaveta_de_baixo_cresce_com_a_tela)
s.teste('o clique encontra a gaveta desenhada', clique_encontra_a_gaveta_desenhada)
s.teste('o layout cabe em todas as resolucoes', cabe_em_todas_as_resolucoes)
s.teste('o estado recebe exatamente o layout calculado', estado_recebe_o_layout)
s.teste('voltar para o padrao conserta bloco perdido', voltar_para_o_padrao)
s.encerrar()
