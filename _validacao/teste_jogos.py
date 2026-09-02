# -*- coding: utf-8 -*-
"""
Suite dos jogos.

Abre cada jogo pelo mesmo caminho da interface (clique no botao da aba), pede
alguns quadros e manda cliques e teclas. Sem microfone: os jogos precisam
continuar de pe e aceitar o teclado como entrada.
"""
import pygame

import harness
from harness import Contexto, Suite

s = Suite('teste_jogos')


def abrir_pelo_menu(ctx, id_jogo):
    tela = ctx.tela
    ctx.jogos.desenhar_aba_jogos(tela, 0, 0, ctx.fontes['ui'])
    s.checar(ctx.jogos.botoes_menu, 'a aba listou os jogos')
    for rect, identificador in ctx.jogos.botoes_menu:
        if identificador == id_jogo:
            ctx.jogos.tratar_clique_aba(rect.center, ctx.estado)
            return True
    return False


def jogar(id_jogo, tema):
    ctx = Contexto(tema=tema)
    s.checar(abrir_pelo_menu(ctx, id_jogo), f'{id_jogo} nao abriu pelo menu')
    s.checar(ctx.estado.tela_jogo_ativa, 'a tela de jogo ficou ativa')
    for _ in range(5):
        if hasattr(ctx.jogos.jogo_instancia, 'atualizar'):
            ctx.jogos.jogo_instancia.atualizar(ctx.estado, None, ctx.configs)
        ctx.jogos.desenhar_tela_jogo(ctx.tela, ctx.largura, ctx.altura,
                                     ctx.estado, None, ctx.configs)
    ctx.jogos.tratar_clique_tela_jogo((ctx.largura // 2, ctx.altura // 2),
                                      ctx.estado, None)
    for tecla in (pygame.K_SPACE, pygame.K_1, pygame.K_ESCAPE):
        ctx.jogos.tratar_tecla(pygame.event.Event(
            pygame.KEYDOWN, {'key': tecla, 'unicode': '', 'mod': 0}), ctx.estado)
    ctx.jogos.desenhar_tela_jogo(ctx.tela, ctx.largura, ctx.altura,
                                 ctx.estado, None, ctx.configs)


def aba_sem_jogo_escolhido():
    ctx = Contexto()
    ctx.jogos.desenhar_tela_jogo(ctx.tela, ctx.largura, ctx.altura,
                                 ctx.estado, None, ctx.configs)


def jogo_em_desenvolvimento_nao_abre():
    ctx = Contexto()
    ctx.jogos.desenhar_aba_jogos(ctx.tela, 0, 0, ctx.fontes['ui'])
    rect, _id = ctx.jogos.botoes_menu[2]
    ctx.jogos.tratar_clique_aba(rect.center, ctx.estado)
    s.checar(ctx.jogos.jogo_instancia is None,
             'jogo em desenvolvimento nao deve instanciar nada')


for _tema in harness.TEMAS:
    for _jogo in ('acerte_a_nota', 'jogo2'):
        s.teste(f'[{_tema}] {_jogo}: abre, roda quadros e aceita entrada',
                lambda j=_jogo, t=_tema: jogar(j, t))

s.teste('tela de jogo sem jogo escolhido nao quebra', aba_sem_jogo_escolhido)
s.teste('jogo em desenvolvimento nao abre', jogo_em_desenvolvimento_nao_abre)
s.encerrar()
