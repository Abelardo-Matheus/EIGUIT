# -*- coding: utf-8 -*-
"""Painel arrastavel que hospeda o campo harmonico."""
import pygame

from config.theme import *
from config.ui_metrics import *
from config.app_settings import *
from config.design_system import TEMA, ds
from ui.components.config_componentes import CHORD_OFFSET_Y_INTERNO


def desenhar_acordes_arrastaveis(tela, estado, meu_campo_harmonico, fontes):
    """
    Como funciona: Desenha o painel de fundo e delega o conteudo ao
    CampoHarmonico.
    Para que serve: Exibir os sete graus da tonalidade de forma arrastavel.
    Onde e usada: Chamada pelo renderizador do workspace.
    """
    if not hasattr(estado, 'dragger_acordes'):
        return

    d = estado.dragger_acordes
    rect = pygame.Rect(d.x, d.y, d.largura, estado.ALTURA_ACORDES)
    ds.painel(tela, rect, None, None, acento=TEMA.acento)

    meu_campo_harmonico.desenhar(
        tela, rect.x, rect.y + CHORD_OFFSET_Y_INTERNO, rect.width,
        fontes['titulo'], fontes['ui'], fontes['pequena'])

    if estado.drag_ativado:
        d.desenhar_caixa_selecao(tela, margem=8)
