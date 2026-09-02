# -*- coding: utf-8 -*-
"""
Suite do estudo de notas.

E o estudo mais usado e o que tem mais estado interno: modo, instrumento,
numero de casas e o sorteio da questao. Aqui se joga uma partida inteira por
codigo, respondendo certo e errado, e se confere o placar e os alvos clicaveis.
"""
import pygame

import harness
from harness import Contexto, Suite

import Estudos.estudo_notas as estudo_notas

s = Suite('teste_estudo_notas')


def montar(tema='escuro', modo='adivinhar'):
    ctx = Contexto(tema=tema)
    estudo = estudo_notas.AcerteANota()
    estudo.modo_jogo = modo
    estudo.inicializar_questao(ctx.estado)
    estudo.desenhar(ctx.tela, ctx.estado, ctx.fontes, 0, 0, 0, 0)
    return ctx, estudo


def questao_sorteada_e_valida():
    ctx, estudo = montar()
    s.checar(estudo.nota_correta, 'o estudo sorteou uma nota')
    s.checar(estudo.nota_correta in ctx.estado.notas_base,
             f'nota invalida: {estudo.nota_correta}')
    s.checar(0 <= estudo.casa_alvo <= estudo.casas_estudo,
             f'casa fora do braco: {estudo.casa_alvo}')


def resposta_certa_e_errada_contam():
    ctx, estudo = montar()
    estudo.acertos = estudo.total = 0
    for tentativa in range(4):
        certa = estudo.nota_correta
        errada = [n for n in ctx.estado.notas_base if n != certa][0]
        escolha = certa if tentativa % 2 == 0 else errada
        alvo = estudo.rects_notas.get(escolha)
        s.checar(alvo is not None, f'a nota {escolha} nao tem alvo na tela')
        estudo.tratar_cliques(alvo.center, ctx.estado)
        estudo.desenhar(ctx.tela, ctx.estado, ctx.fontes, 0, 0, 0, 0)
    s.checar(estudo.total == 4, f'o estudo contou {estudo.total} respostas')
    s.checar(estudo.acertos == 2, f'o estudo contou {estudo.acertos} acertos')


def alvos_das_notas_nao_se_sobrepoem():
    _ctx, estudo = montar()
    rects = list(estudo.rects_notas.values())
    s.checar(len(rects) == 12, f'o teclado de resposta tem {len(rects)} notas')
    for i, a in enumerate(rects):
        for b in rects[i + 1:]:
            s.checar(not a.colliderect(b), f'alvos sobrepostos: {a} e {b}')


def trocar_modo_e_instrumento():
    ctx, estudo = montar()
    for rect, chave in estudo.rects_modo:
        estudo.tratar_cliques(rect.center, ctx.estado)
        s.checar(estudo.modo_jogo == chave, f'o modo nao virou {chave}')
        estudo.desenhar(ctx.tela, ctx.estado, ctx.fontes, 0, 0, 0, 0)
    for rect, chave in estudo.rects_instrumento:
        estudo.tratar_cliques(rect.center, ctx.estado)
        s.checar(estudo.instrumento == chave, f'o instrumento nao virou {chave}')
        estudo.desenhar(ctx.tela, ctx.estado, ctx.fontes, 0, 0, 0, 0)


def numero_de_casas_tem_limite():
    ctx, estudo = montar()
    for _ in range(30):
        estudo.tratar_cliques(estudo.rect_btn_mais.center, ctx.estado)
    s.checar(estudo.casas_estudo <= 24, f'casas demais: {estudo.casas_estudo}')
    for _ in range(30):
        estudo.tratar_cliques(estudo.rect_btn_menos.center, ctx.estado)
    s.checar(estudo.casas_estudo >= 1, f'casas de menos: {estudo.casas_estudo}')


def modo_mapear_sem_teclado_de_resposta():
    ctx, estudo = montar(modo='mapear')
    s.checar(estudo.rects_notas == {}, 'no modo mapear nao ha teclado de resposta')
    s.checar(estudo.rects_posicoes, 'o modo mapear precisa do diagrama clicavel')


def desenha_nos_dois_temas():
    for tema in harness.TEMAS:
        for modo in ('adivinhar', 'ouvir', 'mapear'):
            montar(tema, modo)


s.teste('a questao sorteada e valida', questao_sorteada_e_valida)
s.teste('respostas certas e erradas contam no placar', resposta_certa_e_errada_contam)
s.teste('os alvos das doze notas nao se sobrepoem', alvos_das_notas_nao_se_sobrepoem)
s.teste('trocar modo e instrumento', trocar_modo_e_instrumento)
s.teste('numero de casas tem limite', numero_de_casas_tem_limite)
s.teste('modo mapear usa o diagrama, nao o teclado', modo_mapear_sem_teclado_de_resposta)
s.teste('desenha nos dois temas e em todo modo', desenha_nos_dois_temas)
s.encerrar()
