# -*- coding: utf-8 -*-
"""
Previews do workspace e dos blocos extras.

Gera, nos dois temas, em _preview_design/:
- workspace_<tema>.png   : a tela inteira como o programa abre, com a coluna
                           das gavetas fechada e o resto guardado
- abas_escala_selecionada_<tema>.png : a gaveta translucida com uma forma
                           pousada no braco
- gaveteiro_<tema>.png   : a coluna aberta e alguns blocos ja na tela
- _z_ws_<tema>.png       : o workspace sem a barra superior, para olhar o miolo
- blocos_novos_<tema>.png: cada bloco extra nos tres tamanhos de teste
- ciclo_quintas_<tema>.png: o estudo do ciclo das quintas

Serve para conferir com o olho o que os testes so conseguem afirmar em numero.
"""
import os

import pygame

import harness
from harness import Contexto, montar_fontes

from config.design_system import TEMA, ds
from config.ui_metrics import ALTURA_TOPBAR
import ui.components.blocos_extras as bx
from ui import renderizador_ui
from ui.components import desenhar_painel_superior

SAIDA = os.path.join('_preview_design')
TAMANHOS = [(150, 120), (230, 150), (360, 200)]


def salvar(superficie, nome):
    os.makedirs(SAIDA, exist_ok=True)
    caminho = os.path.join(SAIDA, nome)
    pygame.image.save(superficie, caminho)
    print('  gerado', caminho)


def workspace(tema):
    ctx = Contexto(1920, 1080, tema)
    ctx.estado.historico_notas = ['C', 'D', 'F#', 'A', 'C', 'E', 'G', 'A#']
    ctx.estado.ideias_recentes = ['Ideias/ideia_2026-09-01_10-12-33.wav',
                                  'Ideias/ideia_2026-08-30_21-04-02.wav']
    ctx.estado.grau_selecionado = 4
    ctx.estado.capo_casa = 2
    bx.aplicar_grau(ctx.estado, 'C', 4, ctx.campo)

    tela = pygame.Surface((1920, 1080), pygame.SRCALPHA)
    ds.fundo_app(tela)
    viewport = tela.subsurface(pygame.Rect(0, ALTURA_TOPBAR, 1920,
                                           1080 - ALTURA_TOPBAR))
    renderizador_ui.desenhar_workspace(
        viewport, ctx.estado, ctx.configs, ctx.escalas, ctx.fontes,
        ctx.metronomo, ctx.processador, ctx.gravador, ctx.campo, ctx.jogos)
    salvar(viewport.copy(), f'_z_ws_{tema}.png')
    desenhar_painel_superior(tela, ctx.estado, ctx.fontes, ctx.configs)
    salvar(tela, f'workspace_{tema}.png')


def blocos(tema):
    ctx = Contexto(1920, 1080, tema)
    ctx.estado.blocos_guardados = set()
    ctx.estado.historico_notas = ['C', 'D', 'F#', 'A', 'C', 'E', 'G', 'A#']
    ctx.estado.ideias_recentes = ['Ideias/ideia_2026-09-01_10-12-33.wav',
                                  'Ideias/ideia_2026-08-30_21-04-02.wav']
    ctx.estado.grau_selecionado = 4
    ctx.estado.progressao_ativa = 0
    ctx.estado.capo_casa = 2
    ctx.estado.drone_nota = 'A'

    fonte_rotulo = montar_fontes(1.0)['ui']
    margem, gap = 24, 24
    largura_total = margem * 2 + sum(t[0] for t in TAMANHOS) + gap * (len(TAMANHOS) - 1)
    altura_linha = max(t[1] for t in TAMANHOS) + 34
    altura_total = margem * 2 + altura_linha * len(bx.BLOCOS_EXTRAS)

    tela = pygame.Surface((largura_total, altura_total), pygame.SRCALPHA)
    ds.fundo_app(tela)

    y = margem
    for nome, desenhar in bx.BLOCOS_EXTRAS:
        ds.texto_em(tela, nome.upper(), fonte_rotulo, (margem, y), TEMA.texto_suave)
        x = margem
        for largura, altura in TAMANHOS:
            ctx.redimensionar_bloco(nome, largura, altura, x, y + 22)
            if nome == 'ideias':
                desenhar(tela, ctx.estado, ctx.fontes, ctx.configs, None)
            else:
                desenhar(tela, ctx.estado, ctx.fontes, ctx.configs, ctx.campo)
            x += largura + gap
        y += altura_linha
    salvar(tela, f'blocos_novos_{tema}.png')


def abas_abertas(tema):
    """A gaveta de baixo aberta, para conferir o tamanho dela e do conteudo."""
    ctx = Contexto(1920, 1080, tema)
    for indice, nome in ((0, 'escalas'), (3, 'estudos')):
        for secao in ctx.estado.secoes_inferiores:
            secao['expandido'] = False
        ctx.estado.secoes_inferiores[indice]['expandido'] = True
        tela = pygame.Surface((1920, 1080), pygame.SRCALPHA)
        ds.fundo_app(tela)
        viewport = tela.subsurface(pygame.Rect(0, ALTURA_TOPBAR, 1920,
                                               1080 - ALTURA_TOPBAR))
        renderizador_ui.desenhar_workspace(
            viewport, ctx.estado, ctx.configs, ctx.escalas, ctx.fontes,
            ctx.metronomo, ctx.processador, ctx.gravador, ctx.campo, ctx.jogos)
        desenhar_painel_superior(tela, ctx.estado, ctx.fontes, ctx.configs)
        salvar(tela, f'abas_{nome}_{tema}.png')


def escala_selecionada(tema):
    """A gaveta de escalas aberta com uma forma ja pousada no braco.

    E a prova visual de que o braco continua a vista: a gaveta fica
    translucida e a forma e desenhada por cima dela.
    """
    ctx = Contexto(1920, 1080, tema)
    for secao in ctx.estado.secoes_inferiores:
        secao['expandido'] = False
    ctx.estado.secoes_inferiores[0]['expandido'] = True
    forma = ctx.escalas['maior'][0]
    forma.estado = 'braco'
    forma.casa_atual = 4

    tela = pygame.Surface((1920, 1080), pygame.SRCALPHA)
    ds.fundo_app(tela)
    viewport = tela.subsurface(pygame.Rect(0, ALTURA_TOPBAR, 1920,
                                           1080 - ALTURA_TOPBAR))
    renderizador_ui.desenhar_workspace(
        viewport, ctx.estado, ctx.configs, ctx.escalas, ctx.fontes,
        ctx.metronomo, ctx.processador, ctx.gravador, ctx.campo, ctx.jogos)
    desenhar_painel_superior(tela, ctx.estado, ctx.fontes, ctx.configs)
    salvar(tela, f'abas_escala_selecionada_{tema}.png')


def gaveteiro(tema):
    """A coluna aberta, com parte dos blocos ja fora da gaveta."""
    from ui.components import gaveteiro as gv
    ctx = Contexto(1920, 1080, tema)
    ctx.estado.historico_notas = ['C', 'D', 'F#', 'A', 'C', 'E', 'G', 'A#']
    for nome in ('dragger_circulo', 'dragger_graus', 'dragger_historico',
                 'dragger_progressoes'):
        gv.soltar(ctx.estado, nome)
    ctx.estado.mouse_workspace = (10, 400)
    for _ in range(40):
        gv.atualizar(ctx.estado, 1080 - ALTURA_TOPBAR)

    tela = pygame.Surface((1920, 1080), pygame.SRCALPHA)
    ds.fundo_app(tela)
    viewport = tela.subsurface(pygame.Rect(0, ALTURA_TOPBAR, 1920,
                                           1080 - ALTURA_TOPBAR))
    renderizador_ui.desenhar_workspace(
        viewport, ctx.estado, ctx.configs, ctx.escalas, ctx.fontes,
        ctx.metronomo, ctx.processador, ctx.gravador, ctx.campo, ctx.jogos)
    desenhar_painel_superior(tela, ctx.estado, ctx.fontes, ctx.configs)
    salvar(tela, f'gaveteiro_{tema}.png')


def ciclo(tema):
    import Estudos.estudo_ciclo_quintas as estudo_ciclo
    ctx = Contexto(1600, 900, tema)
    estudo = estudo_ciclo.EstudoCicloQuintas()
    tela = pygame.Surface((1600, 900), pygame.SRCALPHA)
    ds.fundo_app(tela)
    estudo.desenhar(tela, ctx.estado, ctx.fontes, 800, 450, 0, 0)
    salvar(tela, f'ciclo_quintas_{tema}.png')


if __name__ == '__main__':
    for tema in harness.TEMAS:
        print(f'[{tema}]')
        harness.definir_tema(tema)
        workspace(tema)
        abas_abertas(tema)
        escala_selecionada(tema)
        gaveteiro(tema)
        blocos(tema)
        ciclo(tema)
    print('preview2 concluido')
