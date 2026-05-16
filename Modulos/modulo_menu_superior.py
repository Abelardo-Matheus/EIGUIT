# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# =============================================================================

import pygame

class MenuSuperior:
    def __init__(self):
        self.altura_barra = 25
        self.cor_barra = (35, 35, 35)        
        self.cor_texto = (230, 230, 230)     
        self.cor_hover = (0, 120, 215)       
        self.cor_dropdown = (45, 45, 45)     
        self.cor_borda = (80, 80, 80)        

        self.menu_aberto = None
        self.item_hover = None
        self.sub_item_hover = None

        self.estrutura = {
            "Perfil": ["Criar Novo Perfil", "Carregar Perfil", "Deletar Perfil Atual", "Voltar para o Padrão", "Imprimir", "Sair"],
            "Configurações": ["Áudio", "Tamanho da Tela", "Tela Cheia / Janela"],
            "Ajuda": ["Suporte", "Nos Patrocine", "Motivação", "Nos Envie Ideias"]
        }

        self.rects_principais = {}
        self.rects_dropdown = []
        
        self.largura_item = 130 
        self.largura_dropdown = 220

        x_atual = 0
        for menu in self.estrutura.keys():
            self.rects_principais[menu] = pygame.Rect(x_atual, 0, self.largura_item, self.altura_barra)
            x_atual += self.largura_item
            
        self.largura_total_menu = x_atual

    def tratar_eventos(self, evento, pos_mouse, estado, configs=None, campo=None, gravador=None):
        consumiu_clique = False

        if evento.type == pygame.MOUSEMOTION:
            self.item_hover = None
            self.sub_item_hover = None
            for menu, rect in self.rects_principais.items():
                if rect.collidepoint(pos_mouse): self.item_hover = menu
            if self.menu_aberto:
                for i, (texto, rect) in enumerate(self.rects_dropdown):
                    if rect.collidepoint(pos_mouse): self.sub_item_hover = i

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            clicou_no_menu = False
            for menu, rect in self.rects_principais.items():
                if rect.collidepoint(pos_mouse):
                    if self.menu_aberto == menu: self.menu_aberto = None
                    else: self.menu_aberto = menu
                    clicou_no_menu = True
                    break

            if self.menu_aberto and not clicou_no_menu:
                for i, (texto, rect) in enumerate(self.rects_dropdown):
                    if rect.collidepoint(pos_mouse):
                        self.executar_acao(texto, estado, configs, campo, gravador)
                        self.menu_aberto = None
                        clicou_no_menu = True
                        break

            if self.menu_aberto and not clicou_no_menu:
                self.menu_aberto = None
                consumiu_clique = True

            if clicou_no_menu: consumiu_clique = True

        return consumiu_clique

    def executar_acao(self, acao, estado, configs, campo, gravador):
        print(f"[MENU SUPERIOR] Ação Acionada: {acao}")
        
        if acao == "Sair": estado.solicitou_saida = True
        elif acao == "Tela Cheia / Janela": pygame.display.toggle_fullscreen()
            
        elif acao == "Criar Novo Perfil":
            if hasattr(estado, 'gerenciador_perfil'): estado.gerenciador_perfil.abrir_modal_novo()
                
        elif acao == "Carregar Perfil":
            if hasattr(estado, 'gerenciador_perfil'): estado.gerenciador_perfil.abrir_modal_carregar()
                
        elif acao == "Deletar Perfil Atual":
            if hasattr(estado, 'gerenciador_perfil'): estado.gerenciador_perfil.deletar_perfil_atual()
                
        elif acao == "Voltar para o Padrão":
            if hasattr(estado, 'gerenciador_perfil'): estado.gerenciador_perfil.restaurar_padrao(estado, configs, campo)

    def desenhar(self, tela, fonte_ui):
        pygame.draw.rect(tela, self.cor_barra, (0, 0, self.largura_total_menu, self.altura_barra))
        pygame.draw.line(tela, self.cor_borda, (0, self.altura_barra), (self.largura_total_menu, self.altura_barra))
        pygame.draw.line(tela, self.cor_borda, (self.largura_total_menu, 0), (self.largura_total_menu, self.altura_barra))

        for menu, rect in self.rects_principais.items():
            cor_fundo = self.cor_hover if self.item_hover == menu or self.menu_aberto == menu else self.cor_barra
            pygame.draw.rect(tela, cor_fundo, rect)
            txt = fonte_ui.render(menu, True, self.cor_texto)
            tela.blit(txt, (rect.x + (rect.width//2 - txt.get_width()//2), rect.y + 4))

        if self.menu_aberto:
            itens_sub = self.estrutura[self.menu_aberto]
            rect_pai = self.rects_principais[self.menu_aberto]
            altura_item = 35
            altura_total_dd = len(itens_sub) * altura_item
            rect_bg_dd = pygame.Rect(rect_pai.x, self.altura_barra, self.largura_dropdown, altura_total_dd)
            
            pygame.draw.rect(tela, self.cor_dropdown, rect_bg_dd)
            pygame.draw.rect(tela, self.cor_borda, rect_bg_dd, 1)

            self.rects_dropdown.clear()
            y_atual = self.altura_barra
            for i, texto in enumerate(itens_sub):
                rect_item = pygame.Rect(rect_pai.x, y_atual, self.largura_dropdown, altura_item)
                self.rects_dropdown.append((texto, rect_item))
                cor_fundo_item = self.cor_hover if self.sub_item_hover == i else self.cor_dropdown
                pygame.draw.rect(tela, cor_fundo_item, rect_item)
                txt_sub = fonte_ui.render(texto, True, self.cor_texto)
                tela.blit(txt_sub, (rect_item.x + 15, rect_item.y + 8))
                y_atual += altura_item