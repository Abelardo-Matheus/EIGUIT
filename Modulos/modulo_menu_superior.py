# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# =============================================================================

import pygame
import webbrowser # Permite abrir links e emails nativamente

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
        
        # Controles dos Modais (Janelas Pop-up de Ajuda)
        self.modal_ideias_aberto = False
        self.modal_patrocine_aberto = False
        self.modal_motivacao_aberto = False

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
        # =====================================================================
        # LÓGICA DO MODAL "NOS ENVIE IDEIAS" (TRAVA DE EVENTOS)
        # =====================================================================
        if self.modal_ideias_aberto:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                self.modal_ideias_aberto = False
                return True
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if hasattr(self, 'rect_link_email') and self.rect_link_email.collidepoint(pos_mouse):
                    webbrowser.open('mailto:matheusabelardo12@gmail.com')
                elif hasattr(self, 'rect_link_github') and self.rect_link_github.collidepoint(pos_mouse):
                    webbrowser.open('https://github.com/Abelardo-Matheus/EIGUIT')
                elif hasattr(self, 'rect_fechar_ideias') and self.rect_fechar_ideias.collidepoint(pos_mouse):
                    self.modal_ideias_aberto = False
            return True

        # =====================================================================
        # LÓGICA DO MODAL "NOS PATROCINE" (TRAVA DE EVENTOS)
        # =====================================================================
        if self.modal_patrocine_aberto:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                self.modal_patrocine_aberto = False
                return True
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if hasattr(self, 'rect_fechar_patrocine') and self.rect_fechar_patrocine.collidepoint(pos_mouse):
                    self.modal_patrocine_aberto = False
            return True

        # =====================================================================
        # LÓGICA DO MODAL "MOTIVAÇÃO" (TRAVA DE EVENTOS)
        # =====================================================================
        if self.modal_motivacao_aberto:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                self.modal_motivacao_aberto = False
                return True
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if hasattr(self, 'rect_fechar_motivacao') and self.rect_fechar_motivacao.collidepoint(pos_mouse):
                    self.modal_motivacao_aberto = False
            return True

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
        
        if acao == "Sair": 
            estado.solicitou_saida = True
            
        elif acao == "Tela Cheia / Janela": 
            if not hasattr(estado, 'em_tela_cheia'): estado.em_tela_cheia = True 
            estado.em_tela_cheia = not estado.em_tela_cheia
            if estado.em_tela_cheia: tela_nova = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            else: tela_nova = pygame.display.set_mode((1280, 720))
            estado.LARGURA_TELA = tela_nova.get_width()
            estado.ALTURA_TELA = tela_nova.get_height()
            if hasattr(estado, 'gerenciador_perfil'): estado.gerenciador_perfil.restaurar_padrao(estado, configs, campo)
            
        elif acao == "Criar Novo Perfil":
            if hasattr(estado, 'gerenciador_perfil'): estado.gerenciador_perfil.abrir_modal_novo()
                
        elif acao == "Carregar Perfil":
            if hasattr(estado, 'gerenciador_perfil'): estado.gerenciador_perfil.abrir_modal_carregar()
                
        elif acao == "Deletar Perfil Atual":
            if hasattr(estado, 'gerenciador_perfil'): estado.gerenciador_perfil.deletar_perfil_atual()
                
        elif acao == "Voltar para o Padrão":
            if hasattr(estado, 'gerenciador_perfil'): estado.gerenciador_perfil.restaurar_padrao(estado, configs, campo)

        elif acao == "Imprimir":
            estado.solicitou_impressao = True
            
        elif acao == "Nos Envie Ideias":
            self.modal_ideias_aberto = True
            
        elif acao == "Nos Patrocine":
            self.modal_patrocine_aberto = True
            
        elif acao == "Motivação":
            self.modal_motivacao_aberto = True

    # =========================================================================
    # MODAL 1: NOS ENVIE IDEIAS (TEXTO HUMANIZADO E CENTRALIZADO)
    # =========================================================================
    def desenhar_modal_ideias(self, tela, fonte_ui):
        overlay = pygame.Surface((tela.get_width(), tela.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        tela.blit(overlay, (0, 0))

        largura_modal = 680
        altura_modal = 360
        cx = tela.get_width() // 2 - largura_modal // 2
        cy = tela.get_height() // 2 - altura_modal // 2
        rect_modal = pygame.Rect(cx, cy, largura_modal, altura_modal)
        centro_x_modal = cx + (largura_modal // 2)

        pygame.draw.rect(tela, (30, 30, 30), rect_modal, border_radius=10)
        pygame.draw.rect(tela, (100, 100, 100), rect_modal, width=2, border_radius=10)

        tit = fonte_ui.render("Colabore com o Ecossistema Open-Source", True, self.BRANCO)
        tela.blit(tit, (centro_x_modal - tit.get_width() // 2, cy + 30))

        txt1 = fonte_ui.render("Grandes ferramentas não nascem no isolamento; elas ganham vida através", True, (200, 200, 200))
        txt2 = fonte_ui.render("do diálogo direto com quem as utiliza. Se você vislumbrou um recurso,", True, (200, 200, 200))
        txt3 = fonte_ui.render("identificou falhas ou quer sugerir refinamentos técnicos, sua visão é crucial.", True, (200, 200, 200))
        txt4 = fonte_ui.render("O EIGUIT pertence à comunidade, e Pull Requests são muito bem-vindos.", True, (200, 200, 200))
        
        tela.blit(txt1, (centro_x_modal - txt1.get_width() // 2, cy + 85))
        tela.blit(txt2, (centro_x_modal - txt2.get_width() // 2, cy + 115))
        tela.blit(txt3, (centro_x_modal - txt3.get_width() // 2, cy + 145))
        tela.blit(txt4, (centro_x_modal - txt4.get_width() // 2, cy + 175))

        # Bloco Email Centralizado
        lbl_email = fonte_ui.render("Compartilhe suas ideias: ", True, (200, 200, 200))
        lnk_email = fonte_ui.render("matheusabelardo12@gmail.com", True, (0, 160, 255))
        largura_total_email = lbl_email.get_width() + lnk_email.get_width()
        start_x_email = centro_x_modal - (largura_total_email // 2)
        tela.blit(lbl_email, (start_x_email, cy + 220))
        self.rect_link_email = tela.blit(lnk_email, (start_x_email + lbl_email.get_width(), cy + 220))
        pygame.draw.line(tela, (0, 160, 255), (self.rect_link_email.left, self.rect_link_email.bottom - 2), (self.rect_link_email.right, self.rect_link_email.bottom - 2))

        # Bloco GitHub Centralizado
        lbl_git = fonte_ui.render("Repositório Oficial (Contribuições): ", True, (200, 200, 200))
        lnk_git = fonte_ui.render("github.com/Abelardo-Matheus/EIGUIT", True, (0, 160, 255))
        largura_total_git = lbl_git.get_width() + lnk_git.get_width()
        start_x_git = centro_x_modal - (largura_total_git // 2)
        tela.blit(lbl_git, (start_x_git, cy + 255))
        self.rect_link_github = tela.blit(lnk_git, (start_x_git + lbl_git.get_width(), cy + 255))
        pygame.draw.line(tela, (0, 160, 255), (self.rect_link_github.left, self.rect_link_github.bottom - 2), (self.rect_link_github.right, self.rect_link_github.bottom - 2))

        self.rect_fechar_ideias = pygame.Rect(centro_x_modal - 60, cy + 305, 120, 35)
        pygame.draw.rect(tela, (200, 50, 50), self.rect_fechar_ideias, border_radius=5)
        txt_fechar = fonte_ui.render("Voltar", True, self.BRANCO)
        tela.blit(txt_fechar, (self.rect_fechar_ideias.centerx - txt_fechar.get_width()//2, self.rect_fechar_ideias.centery - txt_fechar.get_height()//2))

    # =========================================================================
    # MODAL 2: NOS PATROCINE (TEXTO HUMANIZADO E CENTRALIZADO)
    # =========================================================================
    def desenhar_modal_patrocine(self, tela, fonte_ui):
        overlay = pygame.Surface((tela.get_width(), tela.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        tela.blit(overlay, (0, 0))

        largura_modal = 800
        altura_modal = 360
        cx = tela.get_width() // 2 - largura_modal // 2
        cy = tela.get_height() // 2 - altura_modal // 2
        rect_modal = pygame.Rect(cx, cy, largura_modal, altura_modal)
        centro_x_modal = cx + (largura_modal // 2)

        pygame.draw.rect(tela, (30, 30, 30), rect_modal, border_radius=10)
        pygame.draw.rect(tela, (100, 100, 100), rect_modal, width=2, border_radius=10)

        tit = fonte_ui.render("Apoie o Desenvolvimento do Projeto", True, self.BRANCO)
        tela.blit(tit, (centro_x_modal - tit.get_width() // 2, cy + 30))

        l1 = fonte_ui.render("Manter uma plataforma de código aberto exige dedicação, estudo e infraestrutura.", True, (200, 200, 200))
        l2 = fonte_ui.render("Se o Guitar Studio IA trouxe clareza ou impulsionou sua rotina de estudos,", True, (200, 200, 200))
        l3 = fonte_ui.render("saiba que seu incentivo é o que viabiliza a evolução contínua do sistema.", True, (200, 200, 200))
        l4 = fonte_ui.render("Por enquanto, o suporte ao projeto é centralizado de forma direta via PIX.", True, (200, 200, 200))
        
        tela.blit(l1, (centro_x_modal - l1.get_width() // 2, cy + 85))
        tela.blit(l2, (centro_x_modal - l2.get_width() // 2, cy + 115))
        tela.blit(l3, (centro_x_modal - l3.get_width() // 2, cy + 145))
        tela.blit(l4, (centro_x_modal - l4.get_width() // 2, cy + 175))

        # Bloco PIX Centralizado
        lbl_pix = fonte_ui.render("Chave PIX / Celular: ", True, (200, 200, 200))
        val_pix = fonte_ui.render("31983410907", True, (255, 215, 0)) 
        largura_bloco_pix = lbl_pix.get_width() + val_pix.get_width()
        start_x_pix = centro_x_modal - (largura_bloco_pix // 2)
        tela.blit(lbl_pix, (start_x_pix, cy + 220))
        tela.blit(val_pix, (start_x_pix + lbl_pix.get_width(), cy + 220))

        l5 = fonte_ui.render("Este número também é meu canal direto no WhatsApp pessoal.", True, (200, 200, 200))
        l6 = fonte_ui.render("Sinta-se à vontade para mandar feedbacks, dúvidas ou apenas conversar sobre música!", True, (150, 150, 150))
        
        tela.blit(l5, (centro_x_modal - l5.get_width() // 2, cy + 255))
        tela.blit(l6, (centro_x_modal - l6.get_width() // 2, cy + 280))

        self.rect_fechar_patrocine = pygame.Rect(centro_x_modal - 60, cy + 315, 120, 35)
        pygame.draw.rect(tela, (200, 50, 50), self.rect_fechar_patrocine, border_radius=5)
        txt_fechar = fonte_ui.render("Voltar", True, self.BRANCO)
        tela.blit(txt_fechar, (self.rect_fechar_patrocine.centerx - txt_fechar.get_width()//2, self.rect_fechar_patrocine.centery - txt_fechar.get_height()//2))

    # =========================================================================
    # MODAL 3: MOTIVAÇÃO (NARRATIVA REBUSCADA E 100% AUTÊNTICA/HUMANA)
    # =========================================================================
    def desenhar_modal_motivacao(self, tela, fonte_ui):
        overlay = pygame.Surface((tela.get_width(), tela.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        tela.blit(overlay, (0, 0))

        # Caixa ligeiramente maior para acomodar a narrativa sem espremer
        largura_modal = 850
        altura_modal = 400
        cx = tela.get_width() // 2 - largura_modal // 2
        cy = tela.get_height() // 2 - altura_modal // 2
        rect_modal = pygame.Rect(cx, cy, largura_modal, altura_modal)
        centro_x_modal = cx + (largura_modal // 2)

        pygame.draw.rect(tela, (30, 30, 30), rect_modal, border_radius=10)
        pygame.draw.rect(tela, (100, 100, 100), rect_modal, width=2, border_radius=10)

        tit = fonte_ui.render("A Gênese do Guitar Studio IA", True, self.BRANCO)
        tela.blit(tit, (centro_x_modal - tit.get_width() // 2, cy + 30))

        m1 = fonte_ui.render("O EIGUIT nasceu de uma profunda inquietação pessoal. Diante dos labirintos", True, (200, 200, 200))
        m2 = fonte_ui.render("teóricos e da fragmentação de materiais que frequentemente frustram o estudo", True, (200, 200, 200))
        m3 = fonte_ui.render("da guitarra, idealizei este projeto, inicialmente, como um utilitário de uso restrito", True, (200, 200, 200))
        m4 = fonte_ui.render("— um porto seguro para mapear escalas e visualizar intervalos de forma ágil.", True, (200, 200, 200))
        m5 = fonte_ui.render("Contudo, à medida que as linhas de código se fundiam com as necessidades musicais,", True, (200, 200, 200))
        m6 = fonte_ui.render("o software expandiu-se a ponto de se tornar um ambiente completo de prática.", True, (200, 200, 200))
        m7 = fonte_ui.render("Compreendi, então, que reter essa ferramenta seria privar outros músicos do mesmo amparo.", True, (200, 200, 200))
        m8 = fonte_ui.render("É uma honra abrir este ecossistema para que novos entusiastas aprimorem sua técnica", True, (200, 200, 200))
        m9 = fonte_ui.render("através de uma metodologia visual, simples e unificada.", True, (200, 200, 200))

        tela.blit(m1, (centro_x_modal - m1.get_width() // 2, cy + 85))
        tela.blit(m2, (centro_x_modal - m2.get_width() // 2, cy + 110))
        tela.blit(m3, (centro_x_modal - m3.get_width() // 2, cy + 135))
        tela.blit(m4, (centro_x_modal - m4.get_width() // 2, cy + 160))
        tela.blit(m5, (centro_x_modal - m5.get_width() // 2, cy + 190))
        tela.blit(m6, (centro_x_modal - m6.get_width() // 2, cy + 215))
        tela.blit(m7, (centro_x_modal - m7.get_width() // 2, cy + 240))
        tela.blit(m8, (centro_x_modal - m8.get_width() // 2, cy + 275))
        tela.blit(m9, (centro_x_modal - m9.get_width() // 2, cy + 300))

        self.rect_fechar_motivacao = pygame.Rect(centro_x_modal - 60, cy + 335, 120, 35)
        pygame.draw.rect(tela, (200, 50, 50), self.rect_fechar_motivacao, border_radius=5)
        txt_fechar = fonte_ui.render("Voltar", True, self.BRANCO)
        tela.blit(txt_fechar, (self.rect_fechar_motivacao.centerx - txt_fechar.get_width()//2, self.rect_fechar_motivacao.centery - txt_fechar.get_height()//2))

    def desenhar(self, tela, fonte_ui):
        self.BRANCO = (255, 255, 255) # Preserva o escopo para os modais subordinados
        
        # Desenhando Barra Base
        pygame.draw.rect(tela, self.cor_barra, (0, 0, self.largura_total_menu, self.altura_barra))
        pygame.draw.line(tela, self.cor_borda, (0, self.altura_barra), (self.largura_total_menu, self.altura_barra))
        pygame.draw.line(tela, self.cor_borda, (self.largura_total_menu, 0), (self.largura_total_menu, self.altura_barra))

        # Desenhando Menus Principais
        for menu, rect in self.rects_principais.items():
            cor_fundo = self.cor_hover if self.item_hover == menu or self.menu_aberto == menu else self.cor_barra
            pygame.draw.rect(tela, cor_fundo, rect)
            txt = fonte_ui.render(menu, True, self.cor_texto)
            tela.blit(txt, (rect.x + (rect.width//2 - txt.get_width()//2), rect.y + 4))

        # Desenhando Dropdowns
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
                
        # Invocação das janelas modais com prioridade de sobreposição
        if self.modal_ideias_aberto:
            self.desenhar_modal_ideias(tela, fonte_ui)
            
        if self.modal_patrocine_aberto:
            self.desenhar_modal_patrocine(tela, fonte_ui)
            
        if self.modal_motivacao_aberto:
            self.desenhar_modal_motivacao(tela, fonte_ui)