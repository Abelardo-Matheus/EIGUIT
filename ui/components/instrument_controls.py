import pygame
from config.theme import *
from config.ui_metrics import *
from config.app_settings import *
from core.i18n import _t
from ui.components.btn_escala_guitarra import desenhar_botoes_escala

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
    altura = alvo.altura
    
    # Fundo sutil para o painel de controles
    pygame.draw.rect(tela, (25, 25, 30), (dx, dy, largura, altura), border_radius=10)
    pygame.draw.rect(tela, (60, 60, 70), (dx, dy, largura, altura), width=1, border_radius=10)

    # Cálculo de proporções
    terco = largura // 3
    margem_v = (altura - 30) // 2 # Centraliza botões verticalmente (altura padrão botão = 30)
    instrumento = getattr(estado, 'instrumento', 'guitarra')

    # Coluna 1: Casas (Delegado para componente atômico)
    desenhar_botoes_escala(tela, estado, fontes, configs, dx, dy, terco, margem_v)

    # Coluna 2: Instrumento (Centralizado no segundo terço)
    x_inst_centro = dx + terco + terco // 2
    btn_inst_w = min(80, (terco - 20) // 2)
    estado.btn_guit = pygame.Rect(x_inst_centro - btn_inst_w - 5, dy + margem_v, btn_inst_w, 30)
    estado.btn_baixo = pygame.Rect(x_inst_centro + 5, dy + margem_v, btn_inst_w, 30)
    
    pygame.draw.rect(tela, cor_tema if instrumento == 'guitarra' else (50, 50, 55), estado.btn_guit, border_radius=6)
    txt_g = fontes['pequena'].render(_t('Guit'), True, BRANCO) if btn_inst_w < 50 else fontes['pequena'].render(_t('Guitarra'), True, BRANCO)
    tela.blit(txt_g, (estado.btn_guit.centerx - txt_g.get_width() // 2, estado.btn_guit.centery - txt_g.get_height() // 2))
    
    pygame.draw.rect(tela, cor_tema if instrumento == 'baixo' else (50, 50, 55), estado.btn_baixo, border_radius=6)
    txt_b = fontes['pequena'].render(_t('Baixo'), True, BRANCO)
    tela.blit(txt_b, (estado.btn_baixo.centerx - txt_b.get_width() // 2, estado.btn_baixo.centery - txt_b.get_height() // 2))

    # Coluna 3: Afinação (Alinhada ao terceiro terço)
    x_af_inicio = dx + 2 * terco
    try:
        nome_afinacao = _t(lista_afinacoes[estado.indice_afinacao]['nome'])
    except:
        nome_afinacao = _t('Standard')
        
    estado.btn_menos_afinacao = pygame.Rect(x_af_inicio + 10, dy + margem_v, 30, 30)
    estado.btn_mais_afinacao = pygame.Rect(dx + largura - 40, dy + margem_v, 30, 30)
    
    pygame.draw.rect(tela, cor_tema, estado.btn_menos_afinacao, border_radius=6)
    tela.blit(fontes['pequena'].render('<', True, BRANCO), (estado.btn_menos_afinacao.centerx - 5, estado.btn_menos_afinacao.centery - 10))
    
    pygame.draw.rect(tela, cor_tema, estado.btn_mais_afinacao, border_radius=6)
    tela.blit(fontes['pequena'].render('>', True, BRANCO), (estado.btn_mais_afinacao.centerx - 5, estado.btn_mais_afinacao.centery - 10))
    
    txt_af = fontes['pequena'].render(nome_afinacao, True, BRANCO)
    if txt_af.get_width() > (estado.btn_mais_afinacao.left - estado.btn_menos_afinacao.right):
         txt_af = fontes['pequena'].render(nome_afinacao[:5] + "...", True, BRANCO)
         
    meio_setas = estado.btn_menos_afinacao.right + (estado.btn_mais_afinacao.left - estado.btn_menos_afinacao.right) // 2
    tela.blit(txt_af, (meio_setas - txt_af.get_width() // 2, dy + margem_v + 5))

    if estado.drag_ativado:
        alvo.desenhar_caixa_selecao(tela, margem=5)
