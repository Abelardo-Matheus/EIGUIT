# -*- coding: utf-8 -*-
"""
Suite dos estudos.

Abre cada estudo pelo gerenciador, desenha varios quadros nos dois temas e
manda cliques e teclas, inclusive ESC. Nenhum estudo pode depender de
microfone para pelo menos aparecer na tela.
"""
import pygame

import harness
from harness import Contexto, Suite

import core.modulos.modulos_estudos as modulo_estudos

s = Suite('teste_estudos_novos')

ESTUDOS = ['Notas', 'Acerte o Som', 'Escalas', 'Acordes', 'Prática de Acordes',
           'Padrões', 'Improvisação', 'Ciclo de Quintas', 'Pedais de Efeito',
           'Modulo Inexistente']


def rodar_estudo(nome, tema):
    ctx = Contexto(tema=tema)
    gerenciador = modulo_estudos.GerenciadorEstudos()
    ctx.estado.tela_estudo_ativa = True
    ctx.estado.estudo_ativo = nome
    for _ in range(3):
        gerenciador.desenhar_tela_estudo(ctx.tela, ctx.largura, ctx.altura,
                                         ctx.estado, ctx.fontes)
    for pos in [(ctx.largura // 2, ctx.altura // 2), (100, 100),
                (ctx.largura - 60, ctx.altura - 60)]:
        gerenciador.tratar_eventos(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': pos, 'button': 1}),
            pos, ctx.estado)
    gerenciador.desenhar_tela_estudo(ctx.tela, ctx.largura, ctx.altura,
                                     ctx.estado, ctx.fontes)


def esc_fecha_o_estudo():
    ctx = Contexto()
    gerenciador = modulo_estudos.GerenciadorEstudos()
    ctx.estado.tela_estudo_ativa = True
    ctx.estado.estudo_ativo = 'Notas'
    gerenciador.desenhar_tela_estudo(ctx.tela, ctx.largura, ctx.altura,
                                     ctx.estado, ctx.fontes)
    gerenciador.tratar_eventos(
        pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_ESCAPE,
                                            'unicode': '', 'mod': 0}),
        (0, 0), ctx.estado)
    s.checar(ctx.estado.tela_estudo_ativa is False, 'ESC fechou a tela de estudo')
    s.checar(ctx.estado.estudo_ativo == '', 'e limpou o estudo ativo')
    s.checar(gerenciador.modulo_notas is None, 'e soltou o modulo carregado')


def sub_abas_de_estudo_existem():
    ctx = Contexto()
    secao = [s_ for s_ in ctx.estado.secoes_inferiores if s_['conteudo'] == 'estudos'][0]
    s.checar(secao['sub_abas'], 'a aba ESTUDOS precisa de sub-abas')
    for nome in secao['sub_abas']:
        s.checar(isinstance(nome, str) and nome, f'sub-aba invalida: {nome!r}')


for _tema in harness.TEMAS:
    for _estudo in ESTUDOS:
        s.teste(f'[{_tema}] estudo {_estudo}',
                lambda e=_estudo, t=_tema: rodar_estudo(e, t))

s.teste('ESC fecha o estudo e solta o modulo', esc_fecha_o_estudo)
s.teste('a aba ESTUDOS lista as sub-abas', sub_abas_de_estudo_existem)
s.encerrar()
