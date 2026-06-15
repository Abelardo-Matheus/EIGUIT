import pygame
from Core.constantes_ui import *
from Core.i18n import _t
from Interface.Componentes.config_componentes import SIDEBAR_NOTA_OFFSET_X, SIDEBAR_NOTA_OFFSET_Y, SIDEBAR_LABEL_OFFSET_Y, SIDEBAR_GRID_NOTAS_Y, SIDEBAR_SLIDER_OFFSET_Y, SIDEBAR_SLIDER_ALTURA_PROX

def desenhar_painel_cores(tela, estado, fontes):
    """
        Como funciona: Utiliza funções de renderização do Pygame para desenhar na tela.
        Para que serve: Apresenta o elemento visual 'painel cores' na interface gráfica.
        Onde é usada: Chamado a partir do módulo ou classe base de 'audio_sidebar'.
    """
    if not hasattr(estado, 'dragger_cores'):
        return
    x_base = estado.dragger_cores.x
    y_base = estado.dragger_cores.y
    largura = estado.dragger_cores.largura
    altura = estado.dragger_cores.altura
    
    pygame.draw.rect(tela, FUNDO_PAINEL, (x_base, y_base, largura, altura), border_radius=RADIUS_PADRAO)
    pygame.draw.rect(tela, COR_BORDA, (x_base, y_base, largura, altura), width=1, border_radius=RADIUS_PADRAO)
    
    txt_tit = fontes['pequena'].render(_t('Cores (Graus)'), True, BRANCO)
    tela.blit(txt_tit, (x_base + largura // 2 - txt_tit.get_width() // 2, y_base + 12))
    
    itens = [(_t('Tônica (1)'), estado.indice_cor_tonica, 'rect_cor_tonica'), (_t('Terça (3)'), estado.indice_cor_terca, 'rect_cor_terca'), (_t('Quinta (5)'), estado.indice_cor_quinta, 'rect_cor_quinta')]
    
    espacamento_v = (altura - 50) // 3
    y_item = y_base + 45
    
    for texto, indice_cor, nome_rect in itens:
        txt = fontes['pequena'].render(texto, True, BRANCO)
        if txt.get_width() > largura - 60:
             txt = fontes['pequena'].render(texto[:5] + ".", True, BRANCO)
             
        tela.blit(txt, (x_base + 10, y_item + (espacamento_v - 25) // 2))
        
        rect_cor = pygame.Rect(x_base + largura - 40, y_item + (espacamento_v - 25) // 2, 25, 25)
        cor_atual = CORES_TONICA[indice_cor % len(CORES_TONICA)]
        pygame.draw.rect(tela, cor_atual, rect_cor, border_radius=5)
        pygame.draw.rect(tela, BRANCO, rect_cor, width=2, border_radius=5)
        setattr(estado, nome_rect, rect_cor)
        y_item += espacamento_v
        
    if estado.drag_ativado:
        estado.dragger_cores.desenhar_caixa_selecao(tela, margem=5)

def desenhar_bloco_nota_atual(tela, estado, fontes, configs):
    """
        Como funciona: Utiliza funções de renderização do Pygame para desenhar na tela.
        Para que serve: Apresenta o elemento visual 'bloco nota atual' na interface gráfica.
        Onde é usada: Chamado a partir do módulo ou classe base de 'audio_sidebar'.
    """
    if not hasattr(estado, 'dragger_nota_atual'):
        return
    cor_tema = configs.get_cor_tema()
    x_base = estado.dragger_nota_atual.x
    y_base = estado.dragger_nota_atual.y
    largura = estado.dragger_nota_atual.largura
    altura = estado.dragger_nota_atual.altura
    
    pygame.draw.rect(tela, FUNDO_PAINEL, (x_base, y_base, largura, altura), border_radius=RADIUS_PADRAO)
    pygame.draw.rect(tela, COR_BORDA, (x_base, y_base, largura, altura), width=1, border_radius=RADIUS_PADRAO)
    
    nota_microfone = estado.nota_atual_detectada
    cor_nota_grande = VERDE_SUCCESS if nota_microfone != '--' else (100, 100, 100)
    
    # Cabeçalho adaptável
    txt_nota = fontes['titulo'].render(nota_microfone, True, cor_nota_grande)
    tela.blit(txt_nota, (x_base + 20, y_base + 15))
    
    txt_label = fontes['pequena'].render(_t('Entrada de Áudio'), True, (150, 150, 150))
    tela.blit(txt_label, (x_base + 20, y_base + 45))
    
    # Seleção de notas adaptável
    y_selecao = y_base + 75
    margem_h = 20
    espacamento = (largura - margem_h * 2) / 12
    estado.rects_notas_selecao.clear()
    notas_base = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    for i, n in enumerate(notas_base):
        rect_n = pygame.Rect(x_base + margem_h + i * espacamento, y_selecao, espacamento - 2, 30)
        estado.rects_notas_selecao.append((rect_n, n))
        cor_bg = cor_tema if estado.nota_selecionada_bloco == n else (40, 40, 40)
        pygame.draw.rect(tela, cor_bg, rect_n, border_radius=5)
        if estado.nota_selecionada_bloco != n:
            pygame.draw.rect(tela, COR_BORDA, rect_n, width=1, border_radius=5)
        
        fonte_n = fontes['pequena'] if espacamento > 20 else fontes['pequena'] # Poderia ser menor se necessário
        txt_n = fonte_n.render(n, True, BRANCO)
        if txt_n.get_width() < rect_n.width:
            tela.blit(txt_n, (rect_n.centerx - txt_n.get_width() // 2, rect_n.centery - txt_n.get_height() // 2))

    # Sliders adaptáveis
    altura_util_sliders = altura - (y_selecao - y_base) - 40
    espacamento_slider = altura_util_sliders // 2
    
    y_ctrl = y_selecao + 40
    # Slider 1: Persistência
    txt_pers = fontes['pequena'].render(f"{_t('Pers')}: {estado.afinador_persistencia}ms", True, (180, 180, 180))
    tela.blit(txt_pers, (x_base + 20, y_ctrl))
    
    barra_pers = pygame.Rect(x_base + 20, y_ctrl + 20, largura - 40, 6)
    pygame.draw.rect(tela, (40, 40, 40), barra_pers, border_radius=3)
    pct_pers = (estado.afinador_persistencia - 100) / 2900
    pos_alca = barra_pers.x + pct_pers * barra_pers.width
    estado.rect_alca_persistencia = pygame.Rect(pos_alca - 7, barra_pers.y - 5, 14, 16)
    pygame.draw.rect(tela, cor_tema, estado.rect_alca_persistencia, border_radius=4)
    estado.rect_barra_persistencia = barra_pers
    
    y_ctrl += espacamento_slider
    # Slider 2: Sensibilidade
    txt_thresh = fontes['pequena'].render(f"{_t('Sens')}: {estado.afinador_threshold:.2f}", True, (180, 180, 180))
    tela.blit(txt_thresh, (x_base + 20, y_ctrl))
    
    barra_thresh = pygame.Rect(x_base + 20, y_ctrl + 20, largura - 40, 6)
    pygame.draw.rect(tela, (40, 40, 40), barra_thresh, border_radius=3)
    pct_thresh = (estado.afinador_threshold - 0.1) / 0.7
    pos_alca_t = barra_thresh.x + pct_thresh * barra_thresh.width
    estado.rect_alca_threshold = pygame.Rect(pos_alca_t - 7, barra_thresh.y - 5, 14, 16)
    pygame.draw.rect(tela, cor_tema, estado.rect_alca_threshold, border_radius=4)
    estado.rect_barra_threshold = barra_thresh
    
    if estado.drag_ativado:
        estado.dragger_nota_atual.desenhar_caixa_selecao(tela, margem=8)