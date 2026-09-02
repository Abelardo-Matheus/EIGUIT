# -*- coding: utf-8 -*-
"""
Smoke geral: sobe o programa inteiro sem janela e desenha o workspace completo
em varias resolucoes e nos dois temas, com e sem modo de arrastar ligado.
Depois passa uma leva de eventos sinteticos pelo controlador. Serve para pegar
quebra de import, assinatura trocada e explosao no primeiro quadro.
"""
import pygame

import harness
from harness import Contexto, Suite
from ui import renderizador_ui

s = Suite('smoke2')

RESOLUCOES = [(1280, 720), (1600, 900), (1920, 1080), (2560, 1440)]


def desenhar_uma_vez(largura, altura, tema, arrastando, blocos_na_tela=False):
    ctx = Contexto(largura, altura, tema)
    ctx.estado.drag_ativado = arrastando
    if blocos_na_tela:
        # Mesmo quadro, agora com tudo fora do gaveteiro
        ctx.estado.blocos_guardados = set()
    renderizador_ui.desenhar_workspace(
        ctx.tela, ctx.estado, ctx.configs, ctx.escalas, ctx.fontes,
        ctx.metronomo, ctx.processador, ctx.gravador, ctx.campo, ctx.jogos)
    renderizador_ui.desenhar_ui_fixa(
        ctx.tela, ctx.estado, ctx.fontes, ctx.gravador, ctx.configs, ctx.jogos,
        ctx.campo)
    from ui.components import desenhar_painel_superior
    desenhar_painel_superior(ctx.tela, ctx.estado, ctx.fontes, ctx.configs)
    return ctx


for _tema in harness.TEMAS:
    for _res in RESOLUCOES:
        for _arrasto in (False, True):
            s.teste(f'[{_tema}] workspace {_res[0]}x{_res[1]} arrasto={_arrasto}',
                    lambda t=_tema, r=_res, a=_arrasto: desenhar_uma_vez(r[0], r[1], t, a))
    for _res in RESOLUCOES:
        s.teste(f'[{_tema}] workspace {_res[0]}x{_res[1]} com todos os blocos na tela',
                lambda t=_tema, r=_res: desenhar_uma_vez(r[0], r[1], t, False, True))


def eventos_sinteticos():
    import core.controlador_eventos as controlador
    ctx = Contexto()
    ctx.estado.blocos_guardados = set()
    eventos = []
    for x, y in [(10, 10), (400, 300), (900, 600), (1500, 900)]:
        for tipo in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            eventos.append(pygame.event.Event(tipo, {'pos': (x, y), 'button': 1}))
        eventos.append(pygame.event.Event(pygame.MOUSEMOTION,
                                          {'pos': (x, y), 'rel': (1, 1),
                                           'buttons': (0, 0, 0)}))
    for tecla in (pygame.K_SPACE, pygame.K_LEFT, pygame.K_RIGHT):
        eventos.append(pygame.event.Event(pygame.KEYDOWN,
                                          {'key': tecla, 'unicode': '', 'mod': 0}))
    controlador.processar(eventos, ctx.estado, ctx.configs, ctx.escalas,
                          ctx.metronomo, ctx.processador, ctx.gravador,
                          ctx.campo, ctx.jogos)


def sem_captura_de_audio():
    """Sem PortAudio o motor sobe degradado; o loop tem de seguir mesmo assim."""
    from audio.global_audio import GlobalAudioEngine
    ctx = Contexto()
    motor = GlobalAudioEngine()
    motor.atualizar_analise_ia(ctx.estado.afinador_threshold,
                               gate_db=ctx.estado.afinador_noise_gate)
    ctx.estado.freq_detectada = motor.freq_detectada
    ctx.processador.processar_logica_continua(motor, ctx.estado)
    renderizador_ui.desenhar_workspace(
        ctx.tela, ctx.estado, ctx.configs, ctx.escalas, ctx.fontes,
        ctx.metronomo, ctx.processador, motor, ctx.campo, ctx.jogos)


s.teste('eventos sinteticos passam pelo controlador', eventos_sinteticos)
s.teste('workspace roda com o motor de audio sem captura', sem_captura_de_audio)
s.encerrar()
