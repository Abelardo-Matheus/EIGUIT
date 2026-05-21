# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Componente: ChordSelector
# =============================================================================

import pygame
from Core.constantes_ui import *
from Interface.Componentes.config_componentes import CHORD_OFFSET_Y_INTERNO

def desenhar_acordes_arrastaveis(tela, estado, meu_campo_harmonico, fontes):
    if not hasattr(estado, 'dragger_acordes'): return
    x_base = estado.dragger_acordes.x
    y_base = estado.dragger_acordes.y
    largura = estado.dragger_acordes.largura

    # Fundo moderno para o campo harmônico
    pygame.draw.rect(tela, FUNDO_PAINEL, (x_base, y_base, largura, estado.ALTURA_ACORDES), border_radius=RADIUS_PADRAO)
    pygame.draw.rect(tela, COR_BORDA, (x_base, y_base, largura, estado.ALTURA_ACORDES), width=1, border_radius=RADIUS_PADRAO)

    meu_campo_harmonico.desenhar(tela, x_base, y_base + CHORD_OFFSET_Y_INTERNO, largura, fontes['titulo'], fontes['ui'], fontes['pequena'])

    if estado.drag_ativado:
        estado.dragger_acordes.desenhar_caixa_selecao(tela, margem=8)
