# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Componente: TopBar
# =============================================================================

import pygame
from Core.constantes_ui import *
from Core.i18n import _t
from Interface.Componentes.config_componentes import (
    TOPBAR_MIN_LARGURA, TOPBAR_PIN_OFFSET_X, TOPBAR_PIN_Y, TOPBAR_PIN_TAMANHO
)

def desenhar_painel_superior(tela, estado, fontes):
    if hasattr(estado, 'dragger_controles_topo') and estado.dragger_controles_topo.largura < TOPBAR_MIN_LARGURA:
        estado.dragger_controles_topo.largura = TOPBAR_MIN_LARGURA
        
    dx = estado.dragger_controles_topo.x if hasattr(estado, 'dragger_controles_topo') else 100
    dy = estado.dragger_controles_topo.y if hasattr(estado, 'dragger_controles_topo') else 30
    largura_caixa = estado.dragger_controles_topo.largura if hasattr(estado, 'dragger_controles_topo') else TOPBAR_MIN_LARGURA
    
    largura_tela_real = getattr(estado, 'LARGURA_TELA', 1280)
    estado.rect_btn_pin = pygame.Rect(largura_tela_real - TOPBAR_PIN_OFFSET_X, TOPBAR_PIN_Y, TOPBAR_PIN_TAMANHO, TOPBAR_PIN_TAMANHO)
    cor_pin_bg = AZUL_PRIMARIO if estado.drag_ativado else (45, 45, 45)
    pygame.draw.rect(tela, cor_pin_bg, estado.rect_btn_pin, border_radius=10)
    pygame.draw.rect(tela, COR_BORDA, estado.rect_btn_pin, width=1, border_radius=10)
    
    cx, cy = estado.rect_btn_pin.center
    if estado.drag_ativado:
        pygame.draw.circle(tela, BRANCO, (cx, cy), 5)
        pygame.draw.line(tela, BRANCO, (cx-12, cy), (cx+12, cy), 3)
        pygame.draw.line(tela, BRANCO, (cx, cy-12), (cx, cy+12), 3)
    else:
        pygame.draw.circle(tela, (200, 200, 200), (cx, cy - 4), 6) 
        pygame.draw.line(tela, BRANCO, (cx - 6, cy + 2), (cx + 6, cy + 2), 2) 
        pygame.draw.line(tela, BRANCO, (cx, cy + 2), (cx, cy + 12), 2) 

    centro_col1 = dx + (largura_caixa / 6)
    centro_col2 = dx + (largura_caixa / 2)
    centro_col3 = dx + (largura_caixa * 5 / 6)
    
    # Bloco 1: Casas
    x_casas_inicio = centro_col1 - 95 
    btn_menos_casa = pygame.Rect(x_casas_inicio, dy, 40, 35)
    btn_mais_casa = pygame.Rect(x_casas_inicio + 150, dy, 40, 35)
    
    pygame.draw.rect(tela, AZUL_PRIMARIO, btn_menos_casa, border_radius=6)
    tela.blit(fontes['titulo'].render("-", True, BRANCO), (btn_menos_casa.centerx - 5, btn_menos_casa.centery - 15))
    
    txt_casas = fontes['pequena'].render(f"{_t('Casas')}: {estado.NUM_CASAS}", True, BRANCO)
    meio_casas = btn_menos_casa.right + ((btn_mais_casa.left - btn_menos_casa.right) // 2)
    tela.blit(txt_casas, (meio_casas - txt_casas.get_width()//2, dy + 5))
    
    pygame.draw.rect(tela, AZUL_PRIMARIO, btn_mais_casa, border_radius=6)
    tela.blit(fontes['titulo'].render("+", True, BRANCO), (btn_mais_casa.centerx - 7, btn_mais_casa.centery - 15))

    # Bloco 2: Instrumento
    instrumento = getattr(estado, 'instrumento', 'guitarra')
    x_inst_inicio = centro_col2 - 105
    estado.btn_guit = pygame.Rect(x_inst_inicio, dy, 100, 35)
    estado.btn_baixo = pygame.Rect(x_inst_inicio + 110, dy, 100, 35)

    pygame.draw.rect(tela, AZUL_PRIMARIO if instrumento == 'guitarra' else (60, 60, 60), estado.btn_guit, border_radius=6)
    txt_g = fontes['pequena'].render(_t("Guitarra"), True, BRANCO)
    tela.blit(txt_g, (estado.btn_guit.centerx - txt_g.get_width()//2, estado.btn_guit.centery - txt_g.get_height()//2))

    pygame.draw.rect(tela, AZUL_PRIMARIO if instrumento == 'baixo' else (60, 60, 60), estado.btn_baixo, border_radius=6)
    txt_b = fontes['pequena'].render(_t("Baixo"), True, BRANCO)
    tela.blit(txt_b, (estado.btn_baixo.centerx - txt_b.get_width()//2, estado.btn_baixo.centery - txt_b.get_height()//2))

    # Bloco 3: Afinação
    try: nome_afinacao = _t(lista_afinacoes[estado.indice_afinacao]["nome"])
    except: nome_afinacao = _t("Standard")

    x_af_inicio = centro_col3 - 75
    estado.btn_menos_afinacao = pygame.Rect(x_af_inicio, dy, 35, 35)
    estado.btn_mais_afinacao = pygame.Rect(x_af_inicio + 115, dy, 35, 35)

    pygame.draw.rect(tela, AZUL_PRIMARIO, estado.btn_menos_afinacao, border_radius=6)
    tela.blit(fontes['titulo'].render("<", True, BRANCO), (estado.btn_menos_afinacao.centerx - 7, estado.btn_menos_afinacao.centery - 15))

    pygame.draw.rect(tela, AZUL_PRIMARIO, estado.btn_mais_afinacao, border_radius=6)
    tela.blit(fontes['titulo'].render(">", True, BRANCO), (estado.btn_mais_afinacao.centerx - 7, estado.btn_mais_afinacao.centery - 15))

    txt_af = fontes['pequena'].render(nome_afinacao, True, BRANCO)
    meio_setas = estado.btn_menos_afinacao.right + ((estado.btn_mais_afinacao.left - estado.btn_menos_afinacao.right) // 2)
    tela.blit(txt_af, (meio_setas - (txt_af.get_width() // 2), dy + 8))

    if estado.drag_ativado and hasattr(estado, 'dragger_controles_topo'):
        estado.dragger_controles_topo.desenhar_caixa_selecao(tela, margem=10)
