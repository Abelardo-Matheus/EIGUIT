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


def tela_principal_fica_no_topo():
    """Braco e controles: centrados na horizontal, encostados no topo."""
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
        s.checar(topo['y'] == layout.MARGEM_TOPO,
                 f'os controles em {largura}x{altura} deviam encostar no topo '
                 f"(y={topo['y']})")
        s.checar(braco['y'] + braco['h'] < barra['y'],
                 f'o braco em {largura}x{altura} invade a barra de abas')


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


def barra_e_coluna_ficam_na_tela_na_mesa_virtual():
    """
    O workspace e desenhado numa mesa virtual de 4000x3000 e a camera mostra
    so um pedaco dela. Quem se prende ao rodape tem de usar o tamanho da tela,
    e nao o da superficie, senao vai parar fora do monitor.
    """
    import pygame
    from ui import renderizador_ui
    from ui.components import gaveteiro as gv
    for largura, altura in ((1920, 1080), (1366, 768)):
        ctx = Contexto(largura, altura)
        ctx.estado.secoes_inferiores[0]['expandido'] = True
        mesa = pygame.Surface((4000, 3000), pygame.SRCALPHA)
        renderizador_ui.desenhar_workspace(
            mesa, ctx.estado, ctx.configs, ctx.escalas, ctx.fontes,
            ctx.metronomo, ctx.processador, ctx.gravador, ctx.campo, ctx.jogos)
        viewport = pygame.Rect(0, 0, largura, max(600, altura - ALTURA_TOPBAR))

        barra = ctx.estado.dragger_painel_inferior
        rect_barra = pygame.Rect(barra.x, barra.y, barra.largura, barra.altura)
        s.checar(viewport.contains(rect_barra),
                 f'{largura}x{altura}: a barra caiu fora da tela em {rect_barra}')

        secao = ctx.estado.secoes_inferiores[0]
        cabecalho = secao.get('rect_cabecalho')
        s.checar(cabecalho is not None and viewport.contains(cabecalho),
                 f'{largura}x{altura}: a aba nao foi desenhada dentro da tela')
        painel = secao.get('rect_painel')
        s.checar(painel is not None and viewport.contains(painel),
                 f'{largura}x{altura}: a gaveta aberta caiu fora da tela')

        coluna = ctx.estado.rect_gaveteiro
        s.checar(viewport.contains(coluna),
                 f'{largura}x{altura}: a coluna caiu fora da tela em {coluna}')
        s.checar(len(ctx.estado.rects_gavetas) == len(gv.GAVETAS),
                 f'{largura}x{altura}: gavetas de menos na mesa virtual')


def gaveta_apaga_com_forma_selecionada():
    """
    Escolher uma forma de escala nao pode esconder o braco: a gaveta aberta
    fica translucida e a forma passa a ser desenhada por cima dela.
    """
    import pygame
    from ui import renderizador_ui
    from ui.components import bottom_nav

    ctx = Contexto(1920, 1080)
    ctx.estado.secoes_inferiores[0]['expandido'] = True
    viewport = max(600, 1080 - ALTURA_TOPBAR)

    def quadro():
        tela = pygame.Surface((1920, viewport))
        renderizador_ui.desenhar_workspace(
            tela, ctx.estado, ctx.configs, ctx.escalas, ctx.fontes,
            ctx.metronomo, ctx.processador, ctx.gravador, ctx.campo, ctx.jogos)
        return tela

    s.checar(not bottom_nav.forma_em_uso(ctx.escalas),
             'nenhuma forma deveria comecar fora do painel')
    fechada = quadro()

    forma = ctx.escalas['maior'][0]
    forma.estado = 'braco'
    s.checar(bottom_nav.forma_em_uso(ctx.escalas),
             'a forma no braco tem de contar como selecionada')
    aberta = quadro()

    # A gaveta ocupa o rodape do viewport; com a forma na mao ela tem de mudar
    painel = ctx.estado.secoes_inferiores[0]['rect_painel']
    amostra = [(painel.x + painel.width // 3, painel.y + painel.height // 2),
               (painel.centerx, painel.y + 6)]
    mudou = sum(1 for p in amostra if fechada.get_at(p) != aberta.get_at(p))
    s.checar(mudou == len(amostra),
             'a gaveta continuou opaca com a forma selecionada')

    forma.estado = 'painel'


s.teste('todo bloco do canvas tem tamanho minimo', nomes_batem)
s.teste('a gaveta apaga quando ha forma selecionada',
        gaveta_apaga_com_forma_selecionada)
s.teste('barra e coluna ficam na tela mesmo na mesa virtual',
        barra_e_coluna_ficam_na_tela_na_mesa_virtual)
s.teste('a barra de abas fica fixa no rodape', barra_fica_fixa_no_rodape)
s.teste('braco e controles ficam no topo', tela_principal_fica_no_topo)
s.teste('a gaveta de baixo cresce com a tela', gaveta_de_baixo_cresce_com_a_tela)
s.teste('o clique encontra a gaveta desenhada', clique_encontra_a_gaveta_desenhada)
s.teste('o layout cabe em todas as resolucoes', cabe_em_todas_as_resolucoes)
s.teste('o estado recebe exatamente o layout calculado', estado_recebe_o_layout)
s.teste('voltar para o padrao conserta bloco perdido', voltar_para_o_padrao)
s.encerrar()
