import pygame
from Core.constantes_ui import *
from Core.i18n import _t
from Interface.Componentes.config_componentes import TOPBAR_MIN_LARGURA, TOPBAR_PIN_OFFSET_X, TOPBAR_PIN_Y, TOPBAR_PIN_TAMANHO

def desenhar_painel_superior(tela, estado, fontes, configs):
    """
        Como funciona: Renderiza apenas a barra superior mínima com o Pin (Edit Mode).
        Para que serve: Garantir que o controle global de layout esteja sempre acessível.
    """
    cor_tema = configs.get_cor_tema()
    largura_tela_real = getattr(estado, 'LARGURA_TELA', 1280)
    
    # Botão PIN (Edit Mode) - Topo Direita
    estado.rect_btn_pin = pygame.Rect(largura_tela_real - TOPBAR_PIN_OFFSET_X - 10, TOPBAR_PIN_Y, TOPBAR_PIN_TAMANHO, TOPBAR_PIN_TAMANHO)
    cor_pin_bg = cor_tema if estado.drag_ativado else (45, 45, 45)
    pygame.draw.rect(tela, cor_pin_bg, estado.rect_btn_pin, border_radius=10)
    pygame.draw.rect(tela, COR_BORDA, estado.rect_btn_pin, width=1, border_radius=10)
    
    cx, cy = estado.rect_btn_pin.center
    if estado.drag_ativado:
        # Ícone de "+" ou Pin ativo
        pygame.draw.circle(tela, BRANCO, (cx, cy), 5)
        pygame.draw.line(tela, BRANCO, (cx - 12, cy), (cx + 12, cy), 3)
        pygame.draw.line(tela, BRANCO, (cx, cy - 12), (cx, cy + 12), 3)
    else:
        # Ícone de Cadeado ou Pin inativo
        pygame.draw.circle(tela, (200, 200, 200), (cx, cy - 4), 6)
        pygame.draw.line(tela, BRANCO, (cx - 6, cy + 2), (cx + 6, cy + 2), 2)
        pygame.draw.line(tela, BRANCO, (cx, cy + 2), (cx, cy + 12), 2)