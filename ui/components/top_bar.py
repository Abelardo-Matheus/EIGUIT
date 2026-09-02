# -*- coding: utf-8 -*-
"""Barra superior fixa: marca, menus, status da IA e botoes de sistema."""
import pygame

from config.theme import *
from config.ui_metrics import *
from config.app_settings import *
from config.design_system import TEMA, ds
from core.i18n import _t


def _desenhar_marca(tela, fontes, altura_barra):
    """Logotipo compacto no canto esquerdo."""
    tam = 22
    y = (altura_barra - tam) // 2
    rect_logo = pygame.Rect(ds.ESPACO_MD, y, tam, tam)
    ds.gradiente_vertical(tela, rect_logo, TEMA.primaria_clara, TEMA.primaria,
                          ds.RAIO_MD)
    ds.texto_centralizado(tela, 'E', fontes['pequena'], rect_logo,
                          TEMA.texto_sobre_cor)
    ds.texto_em(tela, 'EIGUIT Studio', fontes['pequena'],
                (rect_logo.right + ds.ESPACO_SM, altura_barra // 2),
                TEMA.texto, ancora='midleft')
    return rect_logo.right + ds.ESPACO_SM + fontes['pequena'].size('EIGUIT Studio')[0]


def _desenhar_status_ia(tela, estado, fontes, x_limite, altura_barra):
    """Selo de status da transcricao por IA, quando ativa."""
    if not hasattr(estado, 'cliente_ia') or estado.cliente_ia.status == 'idle':
        return
    status = estado.cliente_ia.status
    if status == 'completed':
        msg, cor = (_t('IA pronta'), TEMA.verde)
    elif status == 'failed':
        msg, cor = (f"{_t('IA: erro')} ({estado.cliente_ia.erro})", TEMA.alerta)
    else:
        msg, cor = (f"{_t('IA')}: {status.upper()}", TEMA.aviso)

    fonte = fontes['pequena']
    largura = min(fonte.size(msg)[0] + ds.ESPACO_LG * 2, 320)
    altura = altura_barra - 12
    rect = pygame.Rect(x_limite - largura - ds.ESPACO_MD,
                       (altura_barra - altura) // 2, largura, altura)
    if rect.x < 0:
        return
    ds.superficie_translucida(tela, rect, cor, 45, ds.RAIO_PILULA, cor, 1)
    pygame.draw.circle(tela, ds.rgb(cor), (rect.x + ds.ESPACO_MD, rect.centery), 4)
    ds.texto_em(tela, msg, fonte, (rect.x + ds.ESPACO_MD + 10, rect.centery),
                cor, ancora='midleft', largura_max=largura - ds.ESPACO_XL - 10)


def _desenhar_botao_tema(tela, estado, rect):
    """Botao sol/lua que alterna o tema da interface em tempo real."""
    estado.rect_btn_tema = rect
    hover = rect.collidepoint(pygame.mouse.get_pos())
    fundo = ds.misturar(TEMA.superficie_alt, TEMA.acento, 0.35 if hover else 0.15)
    ds.superficie_translucida(tela, rect, fundo, 235, ds.RAIO_MD,
                              TEMA.acento if hover else TEMA.borda, 1)
    # Mostra o icone do modo que sera ativado ao clicar.
    proximo = 'claro' if TEMA.escuro else 'escuro'
    ds.icone_tema(tela, rect.center, proximo,
                  TEMA.aviso if proximo == 'claro' else TEMA.texto_suave, 7)


def _desenhar_botao_pin(tela, estado, rect, ativo):
    """Botao que liga/desliga o modo de edicao (arrastar e redimensionar)."""
    estado.rect_btn_pin = rect
    hover = rect.collidepoint(pygame.mouse.get_pos())
    if ativo:
        pygame.draw.rect(tela, ds.rgb(TEMA.acento), rect, border_radius=ds.RAIO_MD)
        cor_icone = TEMA.texto_sobre_cor
    else:
        fundo = ds.misturar(TEMA.superficie_alt, TEMA.acento, 0.25 if hover else 0.0)
        ds.superficie_translucida(tela, rect, fundo, 235, ds.RAIO_MD,
                                  TEMA.acento if hover else TEMA.borda, 1)
        cor_icone = TEMA.texto_suave

    cx, cy = rect.center
    cor_icone = ds.rgb(cor_icone)
    if ativo:
        # Cruz de movimento (modo edicao ligado)
        pygame.draw.line(tela, cor_icone, (cx - 7, cy), (cx + 7, cy), 2)
        pygame.draw.line(tela, cor_icone, (cx, cy - 7), (cx, cy + 7), 2)
        pygame.draw.circle(tela, cor_icone, (cx, cy), 3)
    else:
        # Alfinete (layout travado)
        pygame.draw.circle(tela, cor_icone, (cx, cy - 3), 4)
        pygame.draw.line(tela, cor_icone, (cx, cy + 1), (cx, cy + 7), 2)
        pygame.draw.line(tela, cor_icone, (cx - 5, cy + 1), (cx + 5, cy + 1), 2)


def _desenhar_botao_voltar(tela, estado, rect):
    """Botao global de voltar, visivel quando ha uma tela em primeiro plano."""
    estado.rect_btn_voltar_global = rect
    hover = rect.collidepoint(pygame.mouse.get_pos())
    cor = ds.clarear(TEMA.alerta, 0.15) if hover else TEMA.alerta
    pygame.draw.rect(tela, ds.rgb(cor), rect, border_radius=ds.RAIO_MD)
    cx, cy = rect.center
    pygame.draw.lines(tela, (255, 255, 255), False,
                      [(cx + 4, cy - 6), (cx - 4, cy), (cx + 4, cy + 6)], 2)


def desenhar_painel_superior(tela, estado, fontes, configs):
    """
    Como funciona: Renderiza a barra superior unificada com a marca, os menus,
    o status da IA e os botoes de sistema (tema, edicao e voltar).
    Para que serve: Ponto fixo de navegacao e controle global da aplicacao.
    Onde e usada: Chamada por main.py e por renderizador_ui.desenhar_tudo.
    """
    largura_tela = tela.get_width()
    altura_barra = ALTURA_TOPBAR

    # Mantem o acento do design system alinhado ao tema escolhido nas configs.
    if configs is not None:
        TEMA.definir_acento(configs.get_cor_tema())

    # 1. Fundo com gradiente sutil e linha de acento inferior
    rect_barra = pygame.Rect(0, 0, largura_tela, altura_barra)
    ds.gradiente_vertical(tela, rect_barra, TEMA.superficie_topo,
                          ds.misturar(TEMA.superficie_topo, TEMA.fundo, 0.6))
    pygame.draw.line(tela, ds.rgb(ds.misturar(TEMA.borda, TEMA.acento, 0.35)),
                     (0, altura_barra - 1), (largura_tela, altura_barra - 1), 1)

    # 2. Marca
    x_apos_marca = _desenhar_marca(tela, fontes, altura_barra)

    # 3. Menus (Arquivo, Perfil, ...)
    if hasattr(estado, 'menu_superior'):
        estado.menu_superior.desenhar(tela, fontes['ui'], estado)

    # 4. Botoes de sistema, montados da direita para a esquerda
    aba_aberta = (
        getattr(estado, 'tela_criacao_tab_ativa', False)
        or getattr(estado, 'tab_tela_cheia_ativa', False)
        or getattr(estado, 'tela_estudo_ativa', False)
        or getattr(estado, 'tela_jogo_ativa', False)
    )

    tam_btn = 28
    margem_y = (altura_barra - tam_btn) // 2
    x_direita = largura_tela - ds.ESPACO_MD - tam_btn

    if aba_aberta:
        _desenhar_botao_voltar(
            tela, estado, pygame.Rect(x_direita, margem_y, tam_btn, tam_btn))
        x_direita -= tam_btn + ds.ESPACO_SM
    elif hasattr(estado, 'rect_btn_voltar_global'):
        estado.rect_btn_voltar_global = pygame.Rect(-100, -100, 0, 0)

    _desenhar_botao_pin(
        tela, estado, pygame.Rect(x_direita, margem_y, tam_btn, tam_btn),
        estado.drag_ativado)
    x_direita -= tam_btn + ds.ESPACO_SM

    _desenhar_botao_tema(
        tela, estado, pygame.Rect(x_direita, margem_y, tam_btn, tam_btn))
    x_direita -= ds.ESPACO_SM

    # 5. Status da IA, encaixado no espaco livre entre menus e botoes
    if x_direita - x_apos_marca > 120:
        _desenhar_status_ia(tela, estado, fontes, x_direita, altura_barra)
