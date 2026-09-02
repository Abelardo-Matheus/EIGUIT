# -*- coding: utf-8 -*-
"""Widget de sessao: precisao, duracao e notas tocadas."""
import pygame

from config.theme import *
from config.ui_metrics import *
from config.design_system import TEMA, ds
from core.i18n import _t


def desenhar_painel_sessao(tela, estado, fontes, configs=None):
    """
        Como funciona: Le os contadores de estado.sessao e apresenta precisao,
        duracao e total de notas, com uma barra de progresso da precisao.
        Para que serve: Retorno objetivo sobre a pratica em andamento.
        Onde e usada: Chamada pelo renderizador do workspace.
    """
    if not hasattr(estado, 'dragger_sessao'):
        return
    sessao = getattr(estado, 'sessao', None)
    if configs is not None:
        TEMA.definir_acento(configs.get_cor_tema())

    d = estado.dragger_sessao
    rect = pygame.Rect(d.x, d.y, d.largura, d.altura)
    y = ds.painel(tela, rect, _t('Sessao'), fontes['pequena'], acento=TEMA.acento)

    precisao = sessao.precisao_recente if sessao else 0
    duracao = sessao.duracao_texto if sessao else '00:00'
    notas = sessao.notas_tocadas if sessao else 0
    pausada = bool(sessao and sessao.pausada)

    pad = ds.ESPACO_LG
    x = rect.x + pad
    largura = rect.width - pad * 2

    # Cor da precisao muda conforme o desempenho
    if precisao >= 80:
        cor_precisao = TEMA.verde
    elif precisao >= 50:
        cor_precisao = TEMA.aviso
    else:
        cor_precisao = TEMA.alerta
    if notas == 0:
        cor_precisao = TEMA.texto_apagado

    linhas = [
        (_t('Precisao'), f'{precisao}%', cor_precisao),
        (_t('Duracao'), duracao, TEMA.ciano if not pausada else TEMA.texto_apagado),
        (_t('Notas'), str(notas), TEMA.texto),
    ]

    espaco = max(20, (rect.bottom - ds.ESPACO_LG - y) // (len(linhas) + 1))
    for rotulo, valor, cor in linhas:
        ds.texto_em(tela, rotulo, fontes['pequena'], (x, y), TEMA.texto_suave,
                    largura_max=largura // 2)
        ds.texto_em(tela, valor, fontes['ui'], (rect.right - pad, y - 2), cor,
                    ancora='topright', largura_max=largura // 2)
        y += espaco

    # Barra de precisao
    if y + ds.ALTURA_TRILHO <= rect.bottom - ds.ESPACO_MD:
        ds.trilho(tela, pygame.Rect(x, y, largura, ds.ALTURA_TRILHO),
                  precisao / 100 if notas else 0.0, cor_precisao)

    # Botao de pausa/retomada no canto do cabecalho
    tam = 18
    estado.rect_btn_sessao_pausa = pygame.Rect(
        rect.right - pad - tam, rect.y + ds.ESPACO_MD, tam, tam)
    cor_btn = TEMA.acento if not pausada else TEMA.aviso
    bx, by = estado.rect_btn_sessao_pausa.center
    if pausada:
        pygame.draw.polygon(tela, ds.rgb(cor_btn),
                            [(bx - 4, by - 6), (bx + 6, by), (bx - 4, by + 6)])
    else:
        pygame.draw.rect(tela, ds.rgb(cor_btn), (bx - 5, by - 6, 4, 12))
        pygame.draw.rect(tela, ds.rgb(cor_btn), (bx + 1, by - 6, 4, 12))

    if estado.drag_ativado:
        d.desenhar_caixa_selecao(tela, margem=5)
