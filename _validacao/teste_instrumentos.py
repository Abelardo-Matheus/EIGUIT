# -*- coding: utf-8 -*-
"""
Suite dos instrumentos e da afinacao.

Troca instrumento, numero de casas e afinacao, e verifica que o braco, as
medidas do estado e os blocos que dependem da afinacao acompanham a mudanca
sem desenhar nota fora do bloco do braco.
"""
import pygame

import harness
from harness import Contexto, Suite

from config.app_settings import lista_afinacoes
from ui.blocks.guitar_neck import desenhar_guitarra
import ui.components.blocos_extras as bx

s = Suite('teste_instrumentos')

INSTRUMENTOS = ['guitarra', 'baixo']


def afinacoes_bem_formadas():
    for afinacao in lista_afinacoes:
        s.checar(afinacao['nome'], 'afinacao sem nome')
        s.checar(len(afinacao['notas']) == 7,
                 f"{afinacao['nome']}: o braco espera sete cordas")
        for nota in afinacao['notas']:
            s.checar(nota in bx.NOTAS, f"{afinacao['nome']}: nota {nota} invalida")


def medidas_acompanham_o_braco():
    ctx = Contexto()
    for casas in (12, 18, 24):
        ctx.estado.NUM_CASAS = casas
        ctx.estado.atualizar_medidas()
        largura_casa = ctx.estado.LARGURA_BRACO / casas
        s.checar(abs(ctx.estado.ESPACO_CASAS - largura_casa) < 0.001,
                 f'{casas} casas: espacamento errado')
    for cordas in (6, 7):
        ctx.estado.NUM_CORDAS = cordas
        ctx.estado.atualizar_medidas()
        s.checar(ctx.estado.ESPACO_CORDAS > 0, f'{cordas} cordas: espacamento invalido')


def braco_desenha_por_instrumento(tema):
    ctx = Contexto(tema=tema)
    for instrumento in INSTRUMENTOS:
        ctx.estado.instrumento = instrumento
        for indice in range(len(lista_afinacoes)):
            ctx.estado.indice_afinacao = indice
            for casas in (12, 18, 24):
                ctx.estado.NUM_CASAS = casas
                ctx.estado.atualizar_medidas()
                desenhar_guitarra(ctx.tela, ctx.estado, ctx.configs, ctx.fontes,
                                  ctx.processador, ctx.campo)


def braco_pequeno_nao_vaza():
    """O braco encolhido nao pode pintar nota fora do proprio bloco.

    A faixa logo abaixo do braco e a unica excecao aceita: e onde ficam os
    numeros das casas, desenhados de proposito por fora da madeira.
    """
    ctx = Contexto()
    tela = pygame.Surface((900, 600), pygame.SRCALPHA)
    for largura, altura in [(300, 120), (520, 160), (800, 300)]:
        tela.fill((0, 0, 0, 0))
        rect = ctx.redimensionar_bloco('guitarra', largura, altura, 40, 40)
        ctx.estado.LARGURA_BRACO, ctx.estado.ALTURA_BRACO = largura, altura
        ctx.estado.atualizar_medidas()
        desenhar_guitarra(tela, ctx.estado, ctx.configs, ctx.fontes,
                          ctx.processador, ctx.campo)
        # Sombra do painel nas laterais e no topo, numeros das casas embaixo
        zona = pygame.Rect(rect.x - 20, rect.y - 20,
                           rect.width + 40, rect.height + 20 + 34)
        for y in range(0, 600, 2):
            for x in range(0, 900, 2):
                if zona.collidepoint(x, y):
                    continue
                s.checar(tela.get_at((x, y))[3] == 0,
                         f'braco {largura}x{altura} pintou em ({x}, {y})')


def bloco_de_cordas_segue_a_afinacao():
    ctx = Contexto()
    ctx.estado.blocos_guardados = set()      # tira o bloco do gaveteiro
    tela = pygame.Surface((600, 400), pygame.SRCALPHA)
    for indice, afinacao in enumerate(lista_afinacoes):
        ctx.estado.indice_afinacao = indice
        ctx.estado.instrumento = 'guitarra'
        ctx.redimensionar_bloco('cordas', 280, 150)
        bx.desenhar_bloco_cordas(tela, ctx.estado, ctx.fontes, ctx.configs, ctx.campo)
        notas = [n for _r, n in ctx.estado.rects_cordas]
        esperado = afinacao['notas'][:ctx.estado.NUM_CORDAS]
        s.checar(notas == esperado,
                 f"{afinacao['nome']}: bloco mostrou {notas}, esperado {esperado}")


def troca_de_instrumento_no_controlador():
    import core.controlador_eventos as controlador
    ctx = Contexto()
    antes = ctx.estado.indice_afinacao
    ctx.estado.indice_afinacao = (antes + 1) % len(lista_afinacoes)
    s.checar(ctx.estado.indice_afinacao != antes, 'a afinacao mudou')
    controlador.processar([], ctx.estado, ctx.configs, ctx.escalas,
                          ctx.metronomo, ctx.processador, ctx.gravador,
                          ctx.campo, ctx.jogos)


s.teste('afinacoes bem formadas', afinacoes_bem_formadas)
s.teste('medidas acompanham casas e cordas', medidas_acompanham_o_braco)
for _tema in harness.TEMAS:
    s.teste(f'[{_tema}] braco desenha em todo instrumento e afinacao',
            lambda t=_tema: braco_desenha_por_instrumento(t))
s.teste('braco encolhido nao pinta fora do bloco', braco_pequeno_nao_vaza)
s.teste('bloco de cordas segue a afinacao', bloco_de_cordas_segue_a_afinacao)
s.teste('controlador aceita a troca de afinacao', troca_de_instrumento_no_controlador)
s.encerrar()
