# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# =============================================================================

import pygame

class MenuContexto:
    def __init__(self):
        self.ativo = False
        self.x = 0
        self.y = 0
        self.opcoes = []
        self.rects = []
        
        # Referências do que foi clicado
        self.alvo_atual = None  # O objeto em si (ex: a instância da guitarra)
        self.tipo_alvo = ""     # String identificadora (ex: "guitarra", "fundo")

        # Estilo visual moderno e escuro
        self.largura = 200
        self.altura_item = 35
        self.cor_fundo = (40, 40, 40)
        self.cor_borda = (90, 90, 90)
        self.cor_hover = (0, 120, 215)
        self.cor_texto = (240, 240, 240)
        
        self.item_hover = -1

    def abrir(self, pos_mouse, tipo_alvo, alvo_obj=None):
        self.ativo = True
        self.x, self.y = pos_mouse
        self.tipo_alvo = tipo_alvo
        self.alvo_atual = alvo_obj
        self.item_hover = -1

        # =====================================================================
        # OPÇÕES DINÂMICAS: Define o que aparece baseado em ONDE você clicou
        # =====================================================================
        if tipo_alvo == "fundo_mesa":
            self.opcoes = ["Colar Bloco", "Configurações da Mesa"]
        else:
            # Menu completo para blocos (Guitarra, Metrônomo, etc)
            self.opcoes = [
                "Configurações do Bloco", 
                "Duplicar Bloco (Cópia)", 
                "Nova Seção Vazia", 
                "Recortar", 
                "Apagar"
            ]

        self.rects.clear()
        y_atual = self.y
        for _ in self.opcoes:
            self.rects.append(pygame.Rect(self.x, y_atual, self.largura, self.altura_item))
            y_atual += self.altura_item

    def fechar(self):
        self.ativo = False
        self.opcoes.clear()
        self.rects.clear()
        self.alvo_atual = None

    def tratar_eventos(self, evento, pos_mouse_virtual, estado):
        """Monitora as ações do menu. Deve rodar antes do resto da tela."""
        if not self.ativo:
            return None

        if evento.type == pygame.MOUSEMOTION:
            self.item_hover = -1
            for i, rect in enumerate(self.rects):
                if rect.collidepoint(pos_mouse_virtual):
                    self.item_hover = i
            return "CONSUMIU_EVENTO" 

        if evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1: # Clique Esquerdo
                for i, rect in enumerate(self.rects):
                    if rect.collidepoint(pos_mouse_virtual):
                        acao_escolhida = self.opcoes[i]
                        alvo = self.alvo_atual
                        tipo = self.tipo_alvo
                        self.fechar()
                        return (acao_escolhida, alvo, tipo) # Dispara a ação!
                
                self.fechar() # Clicou fora, fecha o menu
                return "FECHOU_MENU"
                
            elif evento.button == 3: # Clique Direito em outro lugar
                clicou_dentro = any(r.collidepoint(pos_mouse_virtual) for r in self.rects)
                if not clicou_dentro:
                    self.fechar() # Apenas fecha para poder reabrir na nova posição

        return None

    def desenhar(self, tela, fonte_ui):
        if not self.ativo:
            return

        altura_total = len(self.opcoes) * self.altura_item
        rect_fundo = pygame.Rect(self.x, self.y, self.largura, altura_total)
        
        # Sombra
        pygame.draw.rect(tela, (15, 15, 15), (self.x + 5, self.y + 5, self.largura, altura_total), border_radius=6)
        
        # Fundo e Borda
        pygame.draw.rect(tela, self.cor_fundo, rect_fundo, border_radius=6)
        pygame.draw.rect(tela, self.cor_borda, rect_fundo, width=1, border_radius=6)

        for i, texto in enumerate(self.opcoes):
            rect_item = self.rects[i]
            
            if i == self.item_hover:
                cor_fundo_item = (200, 50, 50) if texto == "Apagar" else self.cor_hover
                b_radius = 5 if len(self.opcoes) == 1 else 0
                if i == 0: pygame.draw.rect(tela, cor_fundo_item, rect_item, border_top_left_radius=5, border_top_right_radius=5)
                elif i == len(self.opcoes) - 1: pygame.draw.rect(tela, cor_fundo_item, rect_item, border_bottom_left_radius=5, border_bottom_right_radius=5)
                else: pygame.draw.rect(tela, cor_fundo_item, rect_item)

            txt_surf = fonte_ui.render(texto, True, self.cor_texto)
            tela.blit(txt_surf, (rect_item.x + 15, rect_item.y + (self.altura_item // 2) - (txt_surf.get_height() // 2)))
            
            # Linha separadora
            if i < len(self.opcoes) - 1:
                pygame.draw.line(tela, (70, 70, 70), (rect_item.left + 8, rect_item.bottom), (rect_item.right - 8, rect_item.bottom))