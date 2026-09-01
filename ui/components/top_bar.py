import pygame
from config.theme import *
from config.ui_metrics import *
from config.app_settings import *
from core.i18n import _t
from ui.components.config_componentes import TOPBAR_MIN_LARGURA, TOPBAR_PIN_OFFSET_X, TOPBAR_PIN_Y, TOPBAR_PIN_TAMANHO

def desenhar_painel_superior(tela, estado, fontes, configs):
    """
        Como funciona: Renderiza a barra superior unificada, integrando os menus (Arquivo, Perfil, etc)
        e os botões de sistema (Pin, Sair).
    """
    largura_tela_real = tela.get_width()
    altura_barra = 40
    
    # 1. Desenhar Fundo da Barra (Clean Dark)
    pygame.draw.rect(tela, (15, 15, 18), (0, 0, largura_tela_real, altura_barra))
    # Removemos a linha dura inferior para criar um aspecto mais limpo e contínuo

    # 2. Desenhar Menus (Arquivo, Perfil, etc)
    if hasattr(estado, 'menu_superior'):
        # Passamos a largura disponível descontando os botões de sistema na direita (~120px)
        estado.menu_superior.desenhar(tela, fontes['ui'], estado)

    # 3. Desenhar Botões de Sistema (Pin / Sair)
    cor_tema = configs.get_cor_tema()
    aba_aberta = (
        getattr(estado, 'tela_criacao_tab_ativa', False) or 
        getattr(estado, 'tab_tela_cheia_ativa', False) or 
        getattr(estado, 'tela_estudo_ativa', False) or 
        getattr(estado, 'tela_jogo_ativa', False)
    )

    tam_btn = 30
    margem_y = (altura_barra - tam_btn) // 2
    
    # Botão PIN (Edit Mode)
    offset_pin = 10 if not aba_aberta else (tam_btn + 20)
    estado.rect_btn_pin = pygame.Rect(largura_tela_real - tam_btn - offset_pin, margem_y, tam_btn, tam_btn)
    
    cor_pin_bg = cor_tema if estado.drag_ativado else (30, 30, 35)
    pygame.draw.rect(tela, cor_pin_bg, estado.rect_btn_pin, border_radius=8)
    
    cx, cy = estado.rect_btn_pin.center
    if estado.drag_ativado:
        pygame.draw.circle(tela, BRANCO, (cx, cy), 3)
        pygame.draw.line(tela, BRANCO, (cx - 8, cy), (cx + 8, cy), 2)
        pygame.draw.line(tela, BRANCO, (cx, cy - 8), (cx, cy + 8), 2)
    else:
        pygame.draw.circle(tela, (200, 200, 200), (cx, cy - 3), 4)
        pygame.draw.line(tela, BRANCO, (cx - 4, cy + 2), (cx + 4, cy + 2), 2)

    # Botão SAIR Global
    if aba_aberta:
        estado.rect_btn_voltar_global = pygame.Rect(largura_tela_real - tam_btn - 10, margem_y, tam_btn, tam_btn)
        pygame.draw.rect(tela, (255, 60, 80), estado.rect_btn_voltar_global, border_radius=8)
        # Seta ( < )
        cx_v, cy_v = estado.rect_btn_voltar_global.center
        pts = [(cx_v + 4, cy_v - 7), (cx_v - 4, cy_v), (cx_v + 4, cy_v + 7)]
        pygame.draw.lines(tela, BRANCO, False, pts, 2)

    # 4. Status da IA de Transcrição
    if hasattr(estado, 'cliente_ia') and estado.cliente_ia.status != "idle":
        status = estado.cliente_ia.status
        msg = f"IA: {status.upper()}"
        cor_msg = (255, 200, 0) # Amarelo para processando

        if status == "completed":
            msg = "IA: PRONTA ✅"
            cor_msg = (46, 204, 113) # Verde
        elif status == "failed":
            msg = f"IA: ERRO ❌ ({estado.cliente_ia.erro})"
            cor_msg = (231, 76, 60) # Vermelho

        txt_ia = fontes['ui'].render(msg, True, cor_msg)
        # Posiciona à esquerda dos botões de sistema
        x_pos = largura_tela_real - tam_btn - offset_pin - txt_ia.get_width() - 30
        tela.blit(txt_ia, (x_pos, margem_y + 5))