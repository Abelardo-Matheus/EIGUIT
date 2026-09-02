# -*- coding: utf-8 -*-
"""
Suite dos acordes.

Confere a teoria (quais notas cada acorde tem, qual a cifra, quais os shapes
CAGED) e depois desenha o painel de acordes e o campo harmonico nos dois temas.
"""
import pygame

import harness
from harness import Contexto, Suite

from ui.blocks.painel_acordes import (FAMILIAS, MAX_FIXADOS, SHAPES,
                                      TIPOS_ACORDE, nome_do_acorde,
                                      notas_do_acorde, semitons)

s = Suite('teste_acordes')

ESPERADOS = {
    ('C', 'maior'): {'C': 'R', 'E': '3', 'G': '5'},
    ('A', 'menor'): {'A': 'R', 'C': 'b3', 'E': '5'},
    ('B', 'dim'): {'B': 'R', 'D': 'b3', 'F': 'b5'},
    ('G', '7'): {'G': 'R', 'B': '3', 'D': '5', 'F': 'b7'},
    ('C', 'maj7'): {'C': 'R', 'E': '3', 'G': '5', 'B': '7'},
    ('E', 'power'): {'E': 'R', 'B': '5'},
}


def notas_certas():
    for (tonica, tipo), esperado in ESPERADOS.items():
        obtido = notas_do_acorde(tonica, tipo)
        s.checar(obtido == esperado,
                 f'{tonica}{tipo}: esperado {esperado}, veio {obtido}')


def cifras_certas():
    s.checar(nome_do_acorde('C', 'maior') == 'C', 'C maior')
    s.checar(nome_do_acorde('A', 'menor') == 'Am', 'A menor')
    s.checar(nome_do_acorde('G', '7') == 'G7', 'G com setima')
    s.checar(nome_do_acorde('E', 'power') == 'E5', 'power chord de E')


def distancias():
    s.checar(semitons('C', 'G') == 7, 'C -> G sao sete semitons')
    s.checar(semitons('G', 'C') == 5, 'G -> C sao cinco semitons')
    s.checar(semitons('C', 'C') == 0, 'a mesma nota da zero')


def todos_os_tipos_sao_coerentes():
    for chave, tipo in TIPOS_ACORDE.items():
        s.checar(len(tipo['int']) == len(tipo['graus']),
                 f'{chave}: intervalos e graus com tamanhos diferentes')
        s.checar(tipo['int'][0] == 0, f'{chave}: nao comeca na tonica')
        notas = notas_do_acorde('C', chave)
        s.checar('C' in notas, f'{chave}: perdeu a tonica')


def familias_apontam_para_tipos_existentes():
    for nome, familia in FAMILIAS.items():
        for chave in familia['tipos']:
            s.checar(chave in TIPOS_ACORDE, f'{nome} aponta para {chave}, que nao existe')


def shapes_caged():
    s.checar(len(SHAPES) == 5, 'CAGED tem cinco shapes')
    s.checar([f['nome'] for f in SHAPES] == ['C', 'A', 'G', 'E', 'D'],
             'a ordem dos shapes e C A G E D')
    for shape in SHAPES:
        graus = {g for _c, _casa, g in shape['notas']}
        s.checar('R' in graus and '3' in graus and '5' in graus,
                 f"shape {shape['nome']} nao tem triade completa")
        s.checar(0 <= shape['corda_tonica'] <= 5,
                 f"shape {shape['nome']} com corda invalida")


def campo_harmonico_desenha(tema):
    ctx = Contexto(tema=tema)
    for indice in range(len(ctx.campo.escalas_campo)):
        ctx.campo.indice_escala_campo = indice
        ctx.campo.tipo_escala = ctx.campo.escalas_campo[indice]['nome']
        notas = ctx.campo.notas_da_escala()
        s.checar(len(notas) == 7, f'escala {indice} sem sete notas')
        for altura in (132, 96, 60):
            ctx.campo.desenhar(ctx.tela, 40, 40, 900, ctx.fontes['titulo'],
                               ctx.fontes['ui'], ctx.fontes['pequena'], altura)
        s.checar(ctx.campo.rects_acordes_campo, 'o campo nao guardou os acordes')
        rect = ctx.campo.rects_acordes_campo[0]
        alvo = rect[0] if isinstance(rect, (tuple, list)) else rect
        ctx.campo.tratar_clique(alvo.center)


def painel_de_acordes_desenha(tema):
    from ui.blocks.painel_acordes import PainelAcordes
    ctx = Contexto(tema=tema)
    painel = PainelAcordes()
    rect = pygame.Rect(40, 40, 900, 400)
    for familia in FAMILIAS:
        painel.familia = familia
        painel.desenhar(ctx.tela, rect, ctx.fontes, ctx.campo, ctx.estado)


s.teste('notas de cada acorde', notas_certas)
s.teste('cifras', cifras_certas)
s.teste('distancia entre notas', distancias)
s.teste('todos os tipos de acorde sao coerentes', todos_os_tipos_sao_coerentes)
s.teste('familias apontam para tipos existentes', familias_apontam_para_tipos_existentes)
s.teste('shapes CAGED', shapes_caged)
s.checar(MAX_FIXADOS >= 2, 'da para fixar pelo menos dois acordes')
for _tema in harness.TEMAS:
    s.teste(f'[{_tema}] campo harmonico desenha e responde ao clique',
            lambda t=_tema: campo_harmonico_desenha(t))
    s.teste(f'[{_tema}] painel de acordes desenha todas as familias',
            lambda t=_tema: painel_de_acordes_desenha(t))
s.encerrar()
