import pygame
from core.modulos.modulos_config import *

class MenuContexto:
    """
        Como funciona: Define a estrutura e estado do componente 'MenuContexto'.
        Para que serve: Atua como o modelo principal para instâncias de 'MenuContexto'.
        Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_menu_contexto'.
    """

    def __init__(self):
        """
            Como funciona: Inicializa os atributos e o estado inicial da instância.
            Para que serve: Prepara o objeto para ser utilizado no ciclo de vida da aplicação.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_menu_contexto'.
        """
        self.ativo = False
        self.x = 0
        self.y = 0
        self.opcoes = []
        self.rects = []
        self.alvo_atual = None
        self.tipo_alvo = ''
        self.largura = MENU_CONTEXTO_LARGURA
        self.altura_item = MENU_CONTEXTO_ALTURA_ITEM
        self.cor_fundo = MENU_CONTEXTO_COR_FUNDO
        self.cor_borda = MENU_CONTEXTO_COR_BORDA
        self.cor_hover = MENU_CONTEXTO_COR_HOVER
        self.cor_texto = MENU_CONTEXTO_COR_TEXTO
        self.item_hover = -1

    def abrir(self, pos_mouse, tipo_alvo, alvo_obj=None):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'abrir'.
            Para que serve: Realiza as tarefas fundamentais de 'abrir' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'abrir'.
        """
        self.ativo = True
        self.x, self.y = pos_mouse
        self.tipo_alvo = tipo_alvo
        self.alvo_atual = alvo_obj
        self.item_hover = -1
        if tipo_alvo == 'fundo_mesa':
            self.opcoes = ['Colar Bloco', 'Configurações da Mesa']
        else:
            self.opcoes = ['Configurações do Bloco', 'Duplicar Bloco (Cópia)', 'Nova Seção Vazia', 'Recortar', 'Apagar']
        self.rects.clear()
        y_atual = self.y
        for _ in self.opcoes:
            self.rects.append(pygame.Rect(self.x, y_atual, self.largura, self.altura_item))
            y_atual += self.altura_item

    def fechar(self):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'fechar'.
            Para que serve: Realiza as tarefas fundamentais de 'fechar' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'fechar'.
        """
        self.ativo = False
        self.opcoes.clear()
        self.rects.clear()
        self.alvo_atual = None

    def tratar_eventos(self, evento, pos_mouse_virtual, estado):
        """
            Como funciona: Verifica colisões e processa inputs do mouse/teclado.
            Para que serve: Mapeia ações do usuário para atualizações de estado.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_menu_contexto'.
        """
        if not self.ativo:
            return None
        if evento.type == pygame.MOUSEMOTION:
            self.item_hover = -1
            for i, rect in enumerate(self.rects):
                if rect.collidepoint(pos_mouse_virtual):
                    self.item_hover = i
            return 'CONSUMIU_EVENTO'
        if evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1:
                for i, rect in enumerate(self.rects):
                    if rect.collidepoint(pos_mouse_virtual):
                        acao_escolhida = self.opcoes[i]
                        alvo = self.alvo_atual
                        tipo = self.tipo_alvo
                        self.fechar()
                        return (acao_escolhida, alvo, tipo)
                self.fechar()
                return 'FECHOU_MENU'
            elif evento.button == 3:
                clicou_dentro = any((r.collidepoint(pos_mouse_virtual) for r in self.rects))
                if not clicou_dentro:
                    self.fechar()
        return None

    def desenhar(self, tela, fonte_ui):
        """
            Como funciona: Utiliza funções de renderização do Pygame para desenhar na tela.
            Para que serve: Apresenta o elemento visual 'desenhar' na interface gráfica.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_menu_contexto'.
        """
        if not self.ativo:
            return
        altura_total = len(self.opcoes) * self.altura_item
        rect_fundo = pygame.Rect(self.x, self.y, self.largura, altura_total)
        pygame.draw.rect(tela, (15, 15, 15), (self.x + 5, self.y + 5, self.largura, altura_total), border_radius=6)
        pygame.draw.rect(tela, self.cor_fundo, rect_fundo, border_radius=6)
        pygame.draw.rect(tela, self.cor_borda, rect_fundo, width=1, border_radius=6)
        for i, texto in enumerate(self.opcoes):
            rect_item = self.rects[i]
            if i == self.item_hover:
                cor_fundo_item = (200, 50, 50) if texto == 'Apagar' else self.cor_hover
                b_radius = 5 if len(self.opcoes) == 1 else 0
                if i == 0:
                    pygame.draw.rect(tela, cor_fundo_item, rect_item, border_top_left_radius=5, border_top_right_radius=5)
                elif i == len(self.opcoes) - 1:
                    pygame.draw.rect(tela, cor_fundo_item, rect_item, border_bottom_left_radius=5, border_bottom_right_radius=5)
                else:
                    pygame.draw.rect(tela, cor_fundo_item, rect_item)
            txt_surf = fonte_ui.render(texto, True, self.cor_texto)
            tela.blit(txt_surf, (rect_item.x + 15, rect_item.y + self.altura_item // 2 - txt_surf.get_height() // 2))
            if i < len(self.opcoes) - 1:
                pygame.draw.line(tela, (70, 70, 70), (rect_item.left + 8, rect_item.bottom), (rect_item.right - 8, rect_item.bottom))