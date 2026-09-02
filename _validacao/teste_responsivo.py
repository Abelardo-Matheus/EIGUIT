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


s.teste('todo bloco do canvas tem tamanho minimo', nomes_batem)
s.teste('o layout cabe em todas as resolucoes', cabe_em_todas_as_resolucoes)
s.teste('o estado recebe exatamente o layout calculado', estado_recebe_o_layout)
s.teste('voltar para o padrao conserta bloco perdido', voltar_para_o_padrao)
s.encerrar()
