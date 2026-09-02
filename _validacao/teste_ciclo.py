# -*- coding: utf-8 -*-
"""
Suite do ciclo das quintas.

Cobre as duas pontas do mesmo assunto: o estudo do Ciclo de Quintas (roda,
construtor de sequencias e desafio) e o bloco Quintas do workspace. As duas
telas tem de concordar sobre vizinhanca, relativa e armadura.
"""
import pygame

import harness
from harness import Contexto, Suite

import Estudos.estudo_ciclo_quintas as estudo_ciclo
import ui.components.blocos_extras as bx

s = Suite('teste_ciclo')


def montar(tema='escuro', aba=0):
    ctx = Contexto(tema=tema)
    estudo = estudo_ciclo.EstudoCicloQuintas()
    estudo.aba = aba
    estudo.desenhar(ctx.tela, ctx.estado, ctx.fontes, ctx.largura // 2,
                    ctx.altura // 2, 0, 0)
    return ctx, estudo


def roda_tem_doze_posicoes():
    _ctx, estudo = montar(aba=0)
    s.checar(len(estudo.rects_roda) == 12,
             f'a roda tem {len(estudo.rects_roda)} posicoes')
    # Os alvos sao quadrados em volta de bolinhas numa roda: encostar nos
    # cantos e normal, o que nao pode e um alvo cobrir o centro do vizinho.
    for i, a in enumerate(estudo.rects_roda):
        for j, b in enumerate(estudo.rects_roda):
            if i == j:
                continue
            s.checar(not a.collidepoint(b.center),
                     f'o alvo {i} cobre o centro do alvo {j}')


def clicar_na_roda_troca_a_tonalidade():
    ctx, estudo = montar(aba=0)
    alvo = estudo.rects_roda[3]
    s.checar(estudo.tratar_cliques(alvo.center, ctx.estado), 'clique na roda')
    s.checar(estudo.indice_tonalidade == 3, 'a tonalidade seguiu o clique')


def sentido_e_tonalidade_alternam():
    ctx, estudo = montar(aba=0)
    estudo.tratar_cliques(estudo.rect_sentido.center, ctx.estado)
    s.checar(estudo.sentido == 'quartas', 'o sentido virou quartas')
    estudo.tratar_cliques(estudo.rect_tonal.center, ctx.estado)
    s.checar(estudo.tonal == 'menor', 'a tonalidade virou menor')


def construtor_de_sequencias():
    ctx, estudo = montar(aba=1)
    s.checar(estudo.rects_graus, 'a aba de sequencias mostra os graus')
    for rect in estudo.rects_graus[:3]:
        estudo.tratar_cliques(rect.center, ctx.estado)
    s.checar(len(estudo.sequencia_atual) == 3,
             f'a sequencia ficou com {len(estudo.sequencia_atual)} graus')
    estudo.desenhar(ctx.tela, ctx.estado, ctx.fontes, 640, 360, 0, 0)
    estudo.tratar_cliques(estudo.rect_btn_limpar.center, ctx.estado)
    s.checar(estudo.sequencia_atual == [], 'o botao limpar esvaziou a sequencia')


def sequencia_tem_teto():
    ctx, estudo = montar(aba=1)
    for _ in range(40):
        estudo.tratar_cliques(estudo.rects_graus[0].center, ctx.estado)
    s.checar(len(estudo.sequencia_atual) <= 16,
             f'a sequencia passou do teto: {len(estudo.sequencia_atual)}')


def desafio_conta_acertos():
    ctx, estudo = montar(aba=2)
    s.checar(estudo.rects_opcoes, 'o desafio mostra as opcoes')
    s.checar(estudo.resposta_correta in estudo.opcoes,
             'a resposta certa esta entre as opcoes')
    for _ in range(4):
        certo = estudo.resposta_correta
        indice = estudo.opcoes.index(certo)
        estudo.tratar_cliques(estudo.rects_opcoes[indice].center, ctx.estado)
        estudo.desenhar(ctx.tela, ctx.estado, ctx.fontes, 640, 360, 0, 0)
    s.checar(estudo.acertos == estudo.total == 4,
             f'placar: {estudo.acertos}/{estudo.total}')


def bloco_e_estudo_concordam():
    """A ordem do ciclo do bloco tem de bater com a teoria: quinta a quinta."""
    for i, tonalidade in enumerate(bx.CICLO):
        proxima = bx.CICLO[(i + 1) % 12]
        s.checar(bx.intervalo_entre(tonalidade, proxima) == '5J',
                 f'{tonalidade} -> {proxima} nao e quinta justa')
        quarta, quinta = bx.vizinhas_da_tonalidade(tonalidade)
        s.checar(quinta == proxima, f'V de {tonalidade} deveria ser {proxima}')
        s.checar(bx.intervalo_entre(tonalidade, quarta) == '4J',
                 f'IV de {tonalidade} nao e quarta justa')


def relativa_e_a_sexta_menor_grau():
    """A relativa menor mora no sexto grau da tonalidade maior."""
    for tonalidade in bx.CICLO:
        sexto = bx.notas_da_tonalidade(tonalidade)[5]
        s.checar(bx.relativa_de(tonalidade) == f'{sexto}m',
                 f'relativa de {tonalidade}: {bx.relativa_de(tonalidade)} != {sexto}m')


def armaduras_sobem_de_um_em_um():
    esperado = ['-'] + [f'{n}#' for n in range(1, 8)] + ['4b', '3b', '2b', '1b']
    s.checar(bx.ARMADURAS == esperado, f'armaduras fora de ordem: {bx.ARMADURAS}')


for _tema in harness.TEMAS:
    for _aba in (0, 1, 2):
        s.teste(f'[{_tema}] o estudo desenha a aba {_aba}',
                lambda t=_tema, a=_aba: montar(t, a))

s.teste('a roda tem doze posicoes sem sobreposicao', roda_tem_doze_posicoes)
s.teste('clicar na roda troca a tonalidade', clicar_na_roda_troca_a_tonalidade)
s.teste('sentido e tonalidade alternam', sentido_e_tonalidade_alternam)
s.teste('construtor de sequencias monta e limpa', construtor_de_sequencias)
s.teste('a sequencia tem teto', sequencia_tem_teto)
s.teste('o desafio conta os acertos', desafio_conta_acertos)
s.teste('o ciclo do bloco anda de quinta em quinta', bloco_e_estudo_concordam)
s.teste('a relativa e o sexto grau', relativa_e_a_sexta_menor_grau)
s.teste('as armaduras seguem o ciclo', armaduras_sobem_de_um_em_um)
s.encerrar()
