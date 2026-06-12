import pygame
from Core.constantes_ui import *
from Core.i18n import _t
from Interface.Componentes.config_componentes import TOPBAR_MIN_LARGURA, TOPBAR_PIN_OFFSET_X, TOPBAR_PIN_Y, TOPBAR_PIN_TAMANHO

def desenhar_painel_superior(tela, estado, fontes, configs):
    """
        Como funciona: Renderiza apenas a barra superior mínima com o Pin (Edit Mode) e o botão Voltar (Sair).
        Para que serve: Garantir que o controle global de layout esteja sempre acessível.
    """
    cor_tema = configs.get_cor_tema()
    largura_tela_real = getattr(estado, 'LARGURA_TELA', 1280)
    
    # Determinar se há alguma "aba" / tela sobreposta aberta
    aba_aberta = (
        getattr(estado, 'tela_criacao_tab_ativa', False) or 
        getattr(estado, 'tab_tela_cheia_ativa', False) or 
        getattr(estado, 'tela_estudo_ativa', False) or 
        getattr(estado, 'tela_jogo_ativa', False)
    )
    
    # Botão PIN (Edit Mode)
    # Se a aba estiver aberta, o PIN divide o canto direito com o botão de SAIR
    offset_pin = 20 if not aba_aberta else (TOPBAR_PIN_TAMANHO + 30)
    estado.rect_btn_pin = pygame.Rect(largura_tela_real - TOPBAR_PIN_TAMANHO - offset_pin, TOPBAR_PIN_Y, TOPBAR_PIN_TAMANHO, TOPBAR_PIN_TAMANHO)
    
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

    # Botão Universal SAIR/VOLTAR (Só aparece se houver aba aberta)
    if aba_aberta:
        estado.rect_btn_voltar_global = pygame.Rect(largura_tela_real - TOPBAR_PIN_TAMANHO - 20, TOPBAR_PIN_Y, TOPBAR_PIN_TAMANHO, TOPBAR_PIN_TAMANHO)
        
        # Fundo vermelho/escuro para destacar a ação de Sair
        pygame.draw.rect(tela, (231, 76, 60), estado.rect_btn_voltar_global, border_radius=10)
        pygame.draw.rect(tela, (255, 255, 255, 50), estado.rect_btn_voltar_global, width=1, border_radius=10)
        
        # Ícone de Seta Minimalista ( < )
        cx_v, cy_v = estado.rect_btn_voltar_global.center
        pontos_seta = [(cx_v + 6, cy_v - 10), (cx_v - 6, cy_v), (cx_v + 6, cy_v + 10)]
        pygame.draw.lines(tela, (255, 255, 255), False, pontos_seta, 3)