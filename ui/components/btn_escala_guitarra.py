# -*- coding: utf-8 -*-
"""Controle atomico do numero de casas visiveis no braco."""
import pygame

from config.theme import *
from config.ui_metrics import *
from config.app_settings import *
from config.design_system import TEMA, ds
from core.i18n import _t


def desenhar_botoes_escala(tela, estado, fontes, configs, dx, dy, terco, margem_v):
    """
    Como funciona: Desenha o stepper de casas (- / valor / +) dentro da coluna
    reservada nos controles de instrumento.
    Para que serve: Ajustar rapidamente quantas casas do braco ficam visiveis.
    Onde e usada: Chamada por desenhar_controles_instrumento.
    """
    largura_col = terco - ds.ESPACO_MD * 2
    x = dx + ds.ESPACO_MD
    y_rotulo = dy + ds.ESPACO_SM
    y_ctrl = dy + margem_v

    ds.rotulo_secao(tela, x, y_rotulo, _t('Casas'), fontes['pequena'],
                    TEMA.texto_apagado, largura_max=largura_col)

    tam_btn = min(30, max(24, largura_col // 4))
    btn_menos = pygame.Rect(x, y_ctrl, tam_btn, ALTURA_BOTAO)
    btn_mais = pygame.Rect(x + largura_col - tam_btn, y_ctrl, tam_btn, ALTURA_BOTAO)

    ds.botao(tela, btn_menos, '-', fontes['ui'], variante='secundario',
             hover=btn_menos.collidepoint(pygame.mouse.get_pos()))
    ds.botao(tela, btn_mais, '+', fontes['ui'], variante='secundario',
             hover=btn_mais.collidepoint(pygame.mouse.get_pos()))

    rect_valor = pygame.Rect(btn_menos.right, y_ctrl,
                             btn_mais.left - btn_menos.right, ALTURA_BOTAO)
    ds.texto_centralizado(tela, str(estado.NUM_CASAS), fontes['ui'],
                          rect_valor, TEMA.texto)

    estado.btn_menos_casa = btn_menos
    estado.btn_mais_casa = btn_mais
