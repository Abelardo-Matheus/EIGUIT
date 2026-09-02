# -*- coding: utf-8 -*-
"""Barra de controles do instrumento: casas, tipo de instrumento e afinacao."""
import pygame

from config.theme import *
from config.ui_metrics import *
from config.app_settings import *
from config.design_system import TEMA, ds
from core.i18n import _t
from ui.components.btn_escala_guitarra import desenhar_botoes_escala


def desenhar_controles_instrumento(tela, estado, fontes, configs):
    """
    Como funciona: Renderiza tres grupos rotulados (Casas, Instrumento e
    Afinacao) dentro do painel arrastavel de controles.
    Para que serve: Concentrar os ajustes rapidos do braco em um so lugar.
    Onde e usada: Chamada pelo renderizador do workspace.
    """
    if not hasattr(estado, 'dragger_controles_topo'):
        return

    alvo = estado.dragger_controles_topo
    rect = pygame.Rect(alvo.x, alvo.y, alvo.largura, alvo.altura)
    ds.painel(tela, rect, None, None, acento=TEMA.acento)

    pos_mouse = pygame.mouse.get_pos()
    terco = rect.width // 3
    margem_v = max(ds.ESPACO_LG + 6, (rect.height - ALTURA_BOTAO) // 2 + 6)
    instrumento = getattr(estado, 'instrumento', 'guitarra')

    # --- Coluna 1: numero de casas ----------------------------------------
    desenhar_botoes_escala(tela, estado, fontes, configs, rect.x, rect.y,
                           terco, margem_v)

    # --- Divisores verticais ----------------------------------------------
    for i in (1, 2):
        x_div = rect.x + terco * i
        pygame.draw.line(tela, ds.rgb(TEMA.borda),
                         (x_div, rect.y + ds.ESPACO_MD),
                         (x_div, rect.bottom - ds.ESPACO_MD), 1)

    # --- Coluna 2: instrumento --------------------------------------------
    x_col = rect.x + terco + ds.ESPACO_MD
    largura_col = terco - ds.ESPACO_MD * 2
    ds.rotulo_secao(tela, x_col, rect.y + ds.ESPACO_SM, _t('Instrumento'),
                    fontes['pequena'], TEMA.texto_apagado, largura_max=largura_col)

    largura_btn = (largura_col - ds.ESPACO_SM) // 2
    estado.btn_guit = pygame.Rect(x_col, rect.y + margem_v, largura_btn, ALTURA_BOTAO)
    estado.btn_baixo = pygame.Rect(estado.btn_guit.right + ds.ESPACO_SM,
                                   rect.y + margem_v, largura_btn, ALTURA_BOTAO)

    texto_guit = _t('Guitarra') if largura_btn >= 66 else _t('Guit')
    ds.botao(tela, estado.btn_guit, texto_guit, fontes['pequena'],
             variante='secundario', ativo=instrumento == 'guitarra',
             hover=estado.btn_guit.collidepoint(pos_mouse))
    ds.botao(tela, estado.btn_baixo, _t('Baixo'), fontes['pequena'],
             variante='secundario', ativo=instrumento == 'baixo',
             hover=estado.btn_baixo.collidepoint(pos_mouse))

    # --- Coluna 3: afinacao -----------------------------------------------
    x_col = rect.x + terco * 2 + ds.ESPACO_MD
    largura_col = rect.width - (terco * 2) - ds.ESPACO_MD * 2
    ds.rotulo_secao(tela, x_col, rect.y + ds.ESPACO_SM, _t('Afinacao'),
                    fontes['pequena'], TEMA.texto_apagado, largura_max=largura_col)

    try:
        nome_afinacao = _t(lista_afinacoes[estado.indice_afinacao]['nome'])
    except (IndexError, KeyError, TypeError):
        nome_afinacao = _t('Standard')

    tam_seta = 28
    estado.btn_menos_afinacao = pygame.Rect(x_col, rect.y + margem_v,
                                            tam_seta, ALTURA_BOTAO)
    estado.btn_mais_afinacao = pygame.Rect(x_col + largura_col - tam_seta,
                                           rect.y + margem_v, tam_seta, ALTURA_BOTAO)

    ds.botao(tela, estado.btn_menos_afinacao, '<', fontes['pequena'],
             variante='secundario',
             hover=estado.btn_menos_afinacao.collidepoint(pos_mouse))
    ds.botao(tela, estado.btn_mais_afinacao, '>', fontes['pequena'],
             variante='secundario',
             hover=estado.btn_mais_afinacao.collidepoint(pos_mouse))

    rect_nome = pygame.Rect(estado.btn_menos_afinacao.right + ds.ESPACO_XS,
                            rect.y + margem_v,
                            estado.btn_mais_afinacao.left - estado.btn_menos_afinacao.right - ds.ESPACO_SM,
                            ALTURA_BOTAO)
    ds.texto_centralizado(tela, nome_afinacao, fontes['pequena'], rect_nome,
                          TEMA.texto)

    if estado.drag_ativado:
        alvo.desenhar_caixa_selecao(tela, margem=5)
