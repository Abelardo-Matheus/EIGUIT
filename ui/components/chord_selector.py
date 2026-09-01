import pygame
from config.theme import *
from config.ui_metrics import *
from config.app_settings import *
from ui.components.config_componentes import CHORD_OFFSET_Y_INTERNO

def desenhar_acordes_arrastaveis(tela, estado, meu_campo_harmonico, fontes):
    """
        Como funciona: Utiliza funções de renderização do Pygame para desenhar na tela.
        Para que serve: Apresenta o elemento visual 'acordes arrastaveis' na interface gráfica.
        Onde é usada: Chamado a partir do módulo ou classe base de 'chord_selector'.
    """
    if not hasattr(estado, 'dragger_acordes'):
        return
    x_base = estado.dragger_acordes.x
    y_base = estado.dragger_acordes.y
    largura = estado.dragger_acordes.largura
    pygame.draw.rect(tela, (20, 20, 24), (x_base, y_base, largura, estado.ALTURA_ACORDES), border_radius=15)
    pygame.draw.rect(tela, COR_BORDA, (x_base, y_base, largura, estado.ALTURA_ACORDES), width=1, border_radius=15)
    meu_campo_harmonico.desenhar(tela, x_base, y_base + CHORD_OFFSET_Y_INTERNO, largura, fontes['titulo'], fontes['ui'], fontes['pequena'])
    if estado.drag_ativado:
        estado.dragger_acordes.desenhar_caixa_selecao(tela, margem=8)