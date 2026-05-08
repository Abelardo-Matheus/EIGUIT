# =============================================================================
# GUITAR STUDIO IA - Módulo Universal de Drag & Drop
# =============================================================================
import pygame

class ElementoArrastavel:
    def __init__(self, x_inicial, y_inicial, largura, altura):
        self.x = x_inicial
        self.y = y_inicial
        self.largura = largura
        self.altura = altura
        
        # Estados do elemento
        self.selecionado = False
        self.arrastando = False
        
        # Variáveis auxiliares para o clique perfeito
        self.offset_mouse_x = 0
        self.offset_mouse_y = 0

    def atualizar_dimensoes(self, largura, altura):
        """Atualiza a área de clique caso o elemento mude de tamanho dinamicamente."""
        self.largura = largura
        self.altura = altura

    def processar_eventos_mouse(self, evento, margem_clique=0):
        """
        Lida com os eventos de mouse. 
        Retorna True se o clique foi neste elemento, evitando clicar em vários ao mesmo tempo.
        """
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            # Cria um retângulo invisível representando a área de clique
            rect_area = pygame.Rect(self.x - margem_clique, self.y - margem_clique, 
                                    self.largura + (margem_clique * 2), self.altura + (margem_clique * 2))
            
            if rect_area.collidepoint(evento.pos):
                self.selecionado = True
                self.arrastando = True
                self.offset_mouse_x = evento.pos[0] - self.x
                self.offset_mouse_y = evento.pos[1] - self.y
                return True # Informa que este elemento foi o alvo do clique
            else:
                self.selecionado = False
                
        elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            self.arrastando = False
            
        elif evento.type == pygame.MOUSEMOTION:
            if self.arrastando:
                self.x = evento.pos[0] - self.offset_mouse_x
                self.y = evento.pos[1] - self.offset_mouse_y
                
        return False

    def desenhar_caixa_selecao(self, tela, margem=0):
        """Desenha a borda branca de seleção apenas se o elemento estiver selecionado."""
        if self.selecionado:
            rect_selecao = pygame.Rect(self.x - margem, self.y - margem, 
                                       self.largura + (margem * 2), self.altura + (margem * 2))
            
            # Borda branca da seleção
            pygame.draw.rect(tela, (255, 255, 255), rect_selecao, width=2, border_radius=8)
            
            # Alças de transformação (quadradinhos nos cantos)
            t_alca = 6
            alcas = [
                (rect_selecao.left - t_alca//2, rect_selecao.top - t_alca//2),     # Canto Sup Esq
                (rect_selecao.right - t_alca//2, rect_selecao.top - t_alca//2),    # Canto Sup Dir
                (rect_selecao.left - t_alca//2, rect_selecao.bottom - t_alca//2),  # Canto Inf Esq
                (rect_selecao.right - t_alca//2, rect_selecao.bottom - t_alca//2)  # Canto Inf Dir
            ]
            
            for pos_x, pos_y in alcas:
                pygame.draw.rect(tela, (255, 255, 255), (pos_x, pos_y, t_alca, t_alca))