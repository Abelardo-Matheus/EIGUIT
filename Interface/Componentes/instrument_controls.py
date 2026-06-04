import pygame
from Core.constantes_ui import *
from Core.i18n import _t

def desenhar_controles_instrumento(tela, estado, fontes, configs):
    """
        Como funciona: Renderiza os controles de instrumento (Guitarra/Baixo), Afinação e Casas.
        Para que serve: Permitir ajustes rápidos no instrumento atual, agora localizado junto ao braço.
    """
    cor_tema = configs.get_cor_tema()
    
    # Usar o dragger que antes era da topbar, mas agora reposicionado para o instrumento
    if not hasattr(estado, 'dragger_controles_topo'):
        return
        
    alvo = estado.dragger_controles_topo
    dx, dy = alvo.x, alvo.y
    largura = alvo.largura
    
    # Fundo sutil para o painel de controles
    pygame.draw.rect(tela, (25, 25, 30), (dx, dy, largura, alvo.altura), border_radius=10)
    pygame.draw.rect(tela, (60, 60, 70), (dx, dy, largura, alvo.altura), width=1, border_radius=10)

    # Coluna 1: Casas
    x_casas = dx + 20
    btn_menos_casa = pygame.Rect(x_casas, dy + 5, 35, 30)
    btn_mais_casa = pygame.Rect(x_casas + 90, dy + 5, 35, 30)
    pygame.draw.rect(tela, cor_tema, btn_menos_casa, border_radius=6)
    tela.blit(fontes['ui'].render('-', True, BRANCO), (btn_menos_casa.centerx - 5, btn_menos_casa.centery - 12))
    
    txt_casas = fontes['pequena'].render(f"{estado.NUM_CASAS} C.", True, BRANCO)
    tela.blit(txt_casas, (btn_menos_casa.right + (btn_mais_casa.left - btn_menos_casa.right)//2 - txt_casas.get_width()//2, dy + 10))
    
    pygame.draw.rect(tela, cor_tema, btn_mais_casa, border_radius=6)
    tela.blit(fontes['ui'].render('+', True, BRANCO), (btn_mais_casa.centerx - 7, btn_mais_casa.centery - 12))
    
    estado.btn_menos_casa = btn_menos_casa
    estado.btn_mais_casa = btn_mais_casa

    # Coluna 2: Instrumento
    x_inst = x_casas + 150
    instrumento = getattr(estado, 'instrumento', 'guitarra')
    estado.btn_guit = pygame.Rect(x_inst, dy + 5, 80, 30)
    estado.btn_baixo = pygame.Rect(x_inst + 85, dy + 5, 80, 30)
    
    pygame.draw.rect(tela, cor_tema if instrumento == 'guitarra' else (50, 50, 55), estado.btn_guit, border_radius=6)
    txt_g = fontes['pequena'].render(_t('Guitarra'), True, BRANCO)
    tela.blit(txt_g, (estado.btn_guit.centerx - txt_g.get_width() // 2, estado.btn_guit.centery - txt_g.get_height() // 2))
    
    pygame.draw.rect(tela, cor_tema if instrumento == 'baixo' else (50, 50, 55), estado.btn_baixo, border_radius=6)
    txt_b = fontes['pequena'].render(_t('Baixo'), True, BRANCO)
    tela.blit(txt_b, (estado.btn_baixo.centerx - txt_b.get_width() // 2, estado.btn_baixo.centery - txt_b.get_height() // 2))

    # Coluna 3: Afinação
    x_af = x_inst + 190
    try:
        nome_afinacao = _t(lista_afinacoes[estado.indice_afinacao]['nome'])
    except:
        nome_afinacao = _t('Standard')
        
    estado.btn_menos_afinacao = pygame.Rect(x_af, dy + 5, 30, 30)
    estado.btn_mais_afinacao = pygame.Rect(largura + dx - 50, dy + 5, 30, 30)
    
    pygame.draw.rect(tela, cor_tema, estado.btn_menos_afinacao, border_radius=6)
    tela.blit(fontes['pequena'].render('<', True, BRANCO), (estado.btn_menos_afinacao.centerx - 5, estado.btn_menos_afinacao.centery - 10))
    
    pygame.draw.rect(tela, cor_tema, estado.btn_mais_afinacao, border_radius=6)
    tela.blit(fontes['pequena'].render('>', True, BRANCO), (estado.btn_mais_afinacao.centerx - 5, estado.btn_mais_afinacao.centery - 10))
    
    txt_af = fontes['pequena'].render(nome_afinacao, True, BRANCO)
    meio_setas = estado.btn_menos_afinacao.right + (estado.btn_mais_afinacao.left - estado.btn_menos_afinacao.right) // 2
    tela.blit(txt_af, (meio_setas - txt_af.get_width() // 2, dy + 10))

    if estado.drag_ativado:
        alvo.desenhar_caixa_selecao(tela, margem=5)
