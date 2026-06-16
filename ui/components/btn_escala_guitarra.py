import pygame
from config.theme import *
from config.ui_metrics import *
from config.app_settings import *

def desenhar_botoes_escala(tela, estado, fontes, configs, dx, dy, terco, margem_v):
    """
    Componente atômico: Responsável apenas pela renderização dos botões de escala (casas da guitarra).
    """
    cor_tema = configs.get_cor_tema()
    
    x_casas = dx + 10
    btn_w = min(35, terco // 4)
    btn_menos_casa = pygame.Rect(x_casas, dy + margem_v, btn_w, 30)
    btn_mais_casa = pygame.Rect(dx + terco - btn_w - 10, dy + margem_v, btn_w, 30)
    
    pygame.draw.rect(tela, cor_tema, btn_menos_casa, border_radius=6)
    tela.blit(fontes['ui'].render('-', True, BRANCO), (btn_menos_casa.centerx - 5, btn_menos_casa.centery - 12))
    
    txt_casas = fontes['pequena'].render(f"{estado.NUM_CASAS} C.", True, BRANCO)
    tela.blit(txt_casas, (btn_menos_casa.right + (btn_mais_casa.left - btn_menos_casa.right)//2 - txt_casas.get_width()//2, dy + margem_v + 5))
    
    pygame.draw.rect(tela, cor_tema, btn_mais_casa, border_radius=6)
    tela.blit(fontes['ui'].render('+', True, BRANCO), (btn_mais_casa.centerx - 7, btn_mais_casa.centery - 12))
    
    # Atualiza o estado global para que o controlador de eventos responda ao clique
    estado.btn_menos_casa = btn_menos_casa
    estado.btn_mais_casa = btn_mais_casa
