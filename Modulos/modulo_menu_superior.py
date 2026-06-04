import pygame
import webbrowser
import Modulos.modulo_suporte as modulo_suporte
from Core.i18n import _t
from Modulos.modulos_config import *

class MenuSuperior:
    """
        Como funciona: Define a estrutura e estado do componente 'MenuSuperior'.
        Para que serve: Atua como o modelo principal para instâncias de 'MenuSuperior'.
        Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_menu_superior'.
    """

    def __init__(self):
        """
            Como funciona: Inicializa os atributos e o estado inicial da instância.
            Para que serve: Prepara o objeto para ser utilizado no ciclo de vida da aplicação.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_menu_superior'.
        """
        self.altura_barra = MENU_SUPERIOR_ALTURA_BARRA
        self.cor_barra = MENU_SUPERIOR_COR_BARRA
        self.cor_texto = MENU_SUPERIOR_COR_TEXTO
        self.cor_hover = MENU_SUPERIOR_COR_HOVER
        self.cor_dropdown = MENU_SUPERIOR_COR_DROPDOWN
        self.cor_borda = MENU_SUPERIOR_COR_BORDA
        self.BRANCO = MENU_SUPERIOR_BRANCO
        self.menu_aberto = None
        self.item_hover = None
        self.sub_item_hover = None
        self.modal_ideias_aberto = False
        self.modal_patrocine_aberto = False
        self.modal_motivacao_aberto = False
        self.gerenciador_suporte = modulo_suporte.TutorialSuporte()
        self.ordem_menus = ['Arquivo', 'Perfil', 'Configurações', 'Ajuda']
        self.estrutura = {'Arquivo': ['Novo', 'Abrir', 'Salvar', 'Exportar'], 'Perfil': ['Minha Conta (Cloud)', 'Deslogar (Trocar Conta)', 'Criar Novo Perfil', 'Carregar Perfil', 'Deletar Perfil Atual', 'Voltar para o Padrão', 'Imprimir', 'Sair'], 'Configurações': ['Áudio', 'Tamanho da Tela', 'Tela Cheia / Janela'], 'Ajuda': ['Suporte', 'Nos Patrocine', 'Motivação', 'Nos Envie Ideias']}
        self.rects_principais = {}
        self.rects_dropdown = []
        self.largura_dropdown = 220

    def recalcular_posicoes(self, largura_total=0):
        """
            Como funciona: Define posições fixas e compactas para os menus superiores.
        """
        largura_item = 120
        x_atual = 10
        self.rects_principais.clear()
        for menu in self.ordem_menus:
            self.rects_principais[menu] = pygame.Rect(x_atual, 0, largura_item, self.altura_barra)
            x_atual += largura_item
        self.largura_total_menu = x_atual

    def tratar_eventos(self, evento, pos_mouse, estado, configs=None, campo=None, gravador=None):
        """
            Como funciona: Verifica colisões e processa inputs do mouse/teclado.
        """
        self.recalcular_posicoes()
        if self.gerenciador_suporte.aberto:
            if self.gerenciador_suporte.tratar_eventos([evento], pos_mouse):
                return True
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
        if self.modal_patrocine_aberto:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                self.modal_patrocine_aberto = False
                return True
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if hasattr(self, 'rect_fechar_patrocine') and self.rect_fechar_patrocine.collidepoint(pos_mouse):
                    self.modal_patrocine_aberto = False
            return True
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
                if rect.collidepoint(pos_mouse):
                    self.item_hover = menu
            if self.menu_aberto:
                for i, (texto, rect) in enumerate(self.rects_dropdown):
                    if rect.collidepoint(pos_mouse):
                        self.sub_item_hover = i
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            clicou_no_menu = False
            for menu, rect in self.rects_principais.items():
                if rect.collidepoint(pos_mouse):
                    if self.menu_aberto == menu:
                        self.menu_aberto = None
                    else:
                        self.menu_aberto = menu
                    clicou_no_menu = True
                    break
            if self.menu_aberto and (not clicou_no_menu):
                for i, (texto, rect) in enumerate(self.rects_dropdown):
                    if rect.collidepoint(pos_mouse):
                        self.executar_acao(texto, estado, configs, campo, gravador)
                        self.menu_aberto = None
                        clicou_no_menu = True
                        break
            if self.menu_aberto and (not clicou_no_menu):
                self.menu_aberto = None
                consumiu_clique = True
            if clicou_no_menu:
                consumiu_clique = True
        return consumiu_clique

    def executar_acao(self, acao, estado, configs, campo, gravador):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'executar acao'.
            Para que serve: Realiza as tarefas fundamentais de 'executar acao' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'executar acao'.
        """
        if acao == 'Sair':
            estado.solicitou_saida = True
        elif acao == 'Tela Cheia / Janela':
            if not hasattr(estado, 'em_tela_cheia'):
                estado.em_tela_cheia = True
            estado.em_tela_cheia = not estado.em_tela_cheia
            if estado.em_tela_cheia:
                tela_nova = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            else:
                tela_nova = pygame.display.set_mode((1280, 720))
            estado.LARGURA_TELA = tela_nova.get_width()
            estado.ALTURA_TELA = tela_nova.get_height()
            if hasattr(estado, 'gerenciador_perfil'):
                estado.gerenciador_perfil.restaurar_padrao(estado, configs, campo)
        elif acao == 'Minha Conta (Cloud)':
            if hasattr(estado, 'gerenciador_perfil'):
                estado.gerenciador_perfil.abrir_modal_conta(estado)
        elif acao == 'Deslogar (Trocar Conta)':
            import os
            if os.path.exists('sessao_cache.json'):
                try:
                    os.remove('sessao_cache.json')
                except:
                    pass
            estado.solicitou_saida = True
        elif acao == 'Criar Novo Perfil':
            if hasattr(estado, 'gerenciador_perfil'):
                estado.gerenciador_perfil.abrir_modal_novo()
        elif acao == 'Carregar Perfil':
            if hasattr(estado, 'gerenciador_perfil'):
                estado.gerenciador_perfil.abrir_modal_carregar()
        elif acao == 'Deletar Perfil Atual':
            if hasattr(estado, 'gerenciador_perfil'):
                estado.gerenciador_perfil.deletar_perfil_atual()
        elif acao == 'Voltar para o Padrão':
            if hasattr(estado, 'gerenciador_perfil'):
                estado.gerenciador_perfil.restaurar_padrao(estado, configs, campo)
        elif acao == 'Imprimir':
            estado.solicitou_impressao = True
        elif acao == 'Nos Envie Ideias':
            self.modal_ideias_aberto = True
        elif acao == 'Nos Patrocine':
            self.modal_patrocine_aberto = True
        elif acao == 'Motivação':
            self.modal_motivacao_aberto = True
        elif acao == 'Suporte':
            self.gerenciador_suporte.aberto = True

    def calcular_centro_camera(self, estado, tela, largura_obj, altura_obj):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'calcular centro camera'.
            Para que serve: Realiza as tarefas fundamentais de 'calcular centro camera' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'calcular centro camera'.
        """
        tela_real = pygame.display.get_surface()
        w_real = tela_real.get_width() if tela_real else 1280
        h_real = tela_real.get_height() if tela_real else 720
        if estado and hasattr(estado, 'camera'):
            zoom = estado.camera.zoom
            meio_x_virtual = estado.camera.offset_x + w_real / 2 / zoom
            meio_y_virtual = estado.camera.offset_y + h_real / 2 / zoom
            cx = meio_x_virtual - largura_obj / 2
            cy = meio_y_virtual - altura_obj / 2
            return (int(cx), int(cy))
        return (w_real // 2 - largura_obj // 2, h_real // 2 - altura_obj // 2)

    def desenhar_modal_ideias(self, tela, fonte_ui, estado):
        """
            Como funciona: Utiliza funções de renderização do Pygame para desenhar na tela.
            Para que serve: Apresenta o elemento visual 'modal ideias' na interface gráfica.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_menu_superior'.
        """
        overlay = pygame.Surface((tela.get_width(), tela.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        tela.blit(overlay, (0, 0))
        largura_modal = 680
        altura_modal = 360
        cx, cy = self.calcular_centro_camera(estado, tela, largura_modal, altura_modal)
        rect_modal = pygame.Rect(cx, cy, largura_modal, altura_modal)
        centro_x_modal = cx + largura_modal // 2
        pygame.draw.rect(tela, (30, 30, 30), rect_modal, border_radius=10)
        pygame.draw.rect(tela, (100, 100, 100), rect_modal, width=2, border_radius=10)
        tit = fonte_ui.render(_t('Colabore com o Ecossistema Open-Source'), True, self.BRANCO)
        tela.blit(tit, (centro_x_modal - tit.get_width() // 2, cy + 30))
        lines = [_t('Grandes ferramentas não nascem no isolamento; elas ganham vida através'), _t('do diálogo direto com quem as utiliza. Se você vislumbrou um recurso,'), _t('identificou falhas ou quer sugerir refinamentos técnicos, sua visão é crucial.'), _t('O EIGUIT pertence à comunidade, e Pull Requests são muito bem-vindos.')]
        for i, line in enumerate(lines):
            txt = fonte_ui.render(line, True, (200, 200, 200))
            tela.blit(txt, (centro_x_modal - txt.get_width() // 2, cy + 85 + i * 30))
        lbl_email = fonte_ui.render(_t('Compartilhe suas ideias: '), True, (200, 200, 200))
        lnk_email = fonte_ui.render('matheusabelardo12@gmail.com', True, (0, 160, 255))
        start_x_email = centro_x_modal - (lbl_email.get_width() + lnk_email.get_width()) // 2
        tela.blit(lbl_email, (start_x_email, cy + 220))
        self.rect_link_email = tela.blit(lnk_email, (start_x_email + lbl_email.get_width(), cy + 220))
        pygame.draw.line(tela, (0, 160, 255), (self.rect_link_email.left, self.rect_link_email.bottom - 2), (self.rect_link_email.right, self.rect_link_email.bottom - 2))
        lbl_git = fonte_ui.render(_t('Repositório Oficial (Contribuições): '), True, (200, 200, 200))
        lnk_git = fonte_ui.render('github.com/Abelardo-Matheus/EIGUIT', True, (0, 160, 255))
        start_x_git = centro_x_modal - (lbl_git.get_width() + lnk_git.get_width()) // 2
        tela.blit(lbl_git, (start_x_git, cy + 255))
        self.rect_link_github = tela.blit(lnk_git, (start_x_git + lbl_git.get_width(), cy + 255))
        pygame.draw.line(tela, (0, 160, 255), (self.rect_link_github.left, self.rect_link_github.bottom - 2), (self.rect_link_github.right, self.rect_link_github.bottom - 2))
        self.rect_fechar_ideias = pygame.Rect(centro_x_modal - 60, cy + 305, 120, 35)
        pygame.draw.rect(tela, (200, 50, 50), self.rect_fechar_ideias, border_radius=5)
        txt_fechar = fonte_ui.render(_t('Voltar'), True, self.BRANCO)
        tela.blit(txt_fechar, (self.rect_fechar_ideias.centerx - txt_fechar.get_width() // 2, self.rect_fechar_ideias.centery - txt_fechar.get_height() // 2))

    def desenhar_modal_patrocine(self, tela, fonte_ui, estado=None):
        """
            Como funciona: Utiliza funções de renderização do Pygame para desenhar na tela.
            Para que serve: Apresenta o elemento visual 'modal patrocine' na interface gráfica.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_menu_superior'.
        """
        overlay = pygame.Surface((tela.get_width(), tela.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        tela.blit(overlay, (0, 0))
        largura_modal = 800
        altura_modal = 360
        cx, cy = self.calcular_centro_camera(estado, tela, largura_modal, altura_modal)
        rect_modal = pygame.Rect(cx, cy, largura_modal, altura_modal)
        centro_x_modal = cx + largura_modal // 2
        pygame.draw.rect(tela, (30, 30, 30), rect_modal, border_radius=10)
        pygame.draw.rect(tela, (100, 100, 100), rect_modal, width=2, border_radius=10)
        tit = fonte_ui.render(_t('Apoie o Desenvolvimento do Projeto'), True, self.BRANCO)
        tela.blit(tit, (centro_x_modal - tit.get_width() // 2, cy + 30))
        lines = [_t('Manter uma plataforma de código aberto exige dedicação, estudo e infraestrutura.'), _t('Se o Guitar Studio IA trouxe clareza ou impulsionou sua rotina de estudos,'), _t('saiba que seu incentivo é o que viabiliza a evolução contínua do sistema.'), _t('Por enquanto, o suporte ao projeto é centralizado de forma direta via PIX.')]
        for i, line in enumerate(lines):
            txt = fonte_ui.render(line, True, (200, 200, 200))
            tela.blit(txt, (centro_x_modal - txt.get_width() // 2, cy + 85 + i * 30))
        lbl_pix = fonte_ui.render(_t('Chave PIX / Celular: '), True, (200, 200, 200))
        val_pix = fonte_ui.render('31983410907', True, (255, 215, 0))
        start_x_pix = centro_x_modal - (lbl_pix.get_width() + val_pix.get_width()) // 2
        tela.blit(lbl_pix, (start_x_pix, cy + 220))
        tela.blit(val_pix, (start_x_pix + lbl_pix.get_width(), cy + 220))
        extra1 = fonte_ui.render(_t('Este número também é meu canal direto no WhatsApp pessoal.'), True, (200, 200, 200))
        extra2 = fonte_ui.render(_t('Sinta-se à vontade para mandar feedbacks, dúvidas ou apenas conversar sobre música!'), True, (150, 150, 150))
        tela.blit(extra1, (centro_x_modal - extra1.get_width() // 2, cy + 255))
        tela.blit(extra2, (centro_x_modal - extra2.get_width() // 2, cy + 280))
        self.rect_fechar_patrocine = pygame.Rect(centro_x_modal - 60, cy + 315, 120, 35)
        pygame.draw.rect(tela, (200, 50, 50), self.rect_fechar_patrocine, border_radius=5)
        txt_fechar = fonte_ui.render(_t('Voltar'), True, self.BRANCO)
        tela.blit(txt_fechar, (self.rect_fechar_patrocine.centerx - txt_fechar.get_width() // 2, self.rect_fechar_patrocine.centery - txt_fechar.get_height() // 2))

    def desenhar_modal_motivacao(self, tela, fonte_ui, estado=None):
        """
            Como funciona: Utiliza funções de renderização do Pygame para desenhar na tela.
            Para que serve: Apresenta o elemento visual 'modal motivacao' na interface gráfica.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_menu_superior'.
        """
        overlay = pygame.Surface((tela.get_width(), tela.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        tela.blit(overlay, (0, 0))
        largura_modal = 850
        altura_modal = 400
        cx, cy = self.calcular_centro_camera(estado, tela, largura_modal, altura_modal)
        rect_modal = pygame.Rect(cx, cy, largura_modal, altura_modal)
        centro_x_modal = cx + largura_modal // 2
        pygame.draw.rect(tela, (30, 30, 30), rect_modal, border_radius=10)
        pygame.draw.rect(tela, (100, 100, 100), rect_modal, width=2, border_radius=10)
        tit = fonte_ui.render(_t('A Gênese do Guitar Studio IA'), True, self.BRANCO)
        tela.blit(tit, (centro_x_modal - tit.get_width() // 2, cy + 30))
        lines = [_t('O EIGUIT nasceu de uma profunda inquietação pessoal. Diante dos labirintos'), _t('teóricos e da fragmentação de materiais que frequentemente frustram o estudo'), _t('da guitarra, idealizei este projeto, inicialmente, como um utilitário de uso restrito'), _t('— um porto seguro para mapear escalas e visualizar intervalos de forma ágil.'), _t('Contudo, à medida que as linhas de código se fundiam com as necessidades musicais,'), _t('o software expandiu-se a ponto de se tornar um ambiente completo de prática.'), _t('Compreendi, então, que reter essa ferramenta seria privar outros músicos do mesmo amparo.'), _t('É uma honra abrir este ecossistema para que novos entusiastas aprimorem sua técnica'), _t('através de uma metodologia visual, simples e unificada.')]
        for i, line in enumerate(lines):
            txt = fonte_ui.render(line, True, (200, 200, 200))
            tela.blit(txt, (centro_x_modal - txt.get_width() // 2, cy + 85 + i * 25))
        self.rect_fechar_motivacao = pygame.Rect(centro_x_modal - 60, cy + 345, 120, 35)
        pygame.draw.rect(tela, (200, 50, 50), self.rect_fechar_motivacao, border_radius=5)
        txt_fechar = fonte_ui.render(_t('Voltar'), True, self.BRANCO)
        tela.blit(txt_fechar, (self.rect_fechar_motivacao.centerx - txt_fechar.get_width() // 2, self.rect_fechar_motivacao.centery - txt_fechar.get_height() // 2))

    def desenhar(self, tela, fonte_ui, estado=None):
        """
            Como funciona: Utiliza funções de renderização do Pygame para desenhar na tela.
            Para que serve: Apresenta o elemento visual 'desenhar' na interface gráfica.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_menu_superior'.
        """
        pygame.draw.rect(tela, self.cor_barra, (0, 0, self.largura_total_menu, self.altura_barra))
        pygame.draw.line(tela, self.cor_borda, (0, self.altura_barra), (self.largura_total_menu, self.altura_barra))
        for menu_chave, rect in self.rects_principais.items():
            titulo_exibir = _t(menu_chave)
            cor_fundo = self.cor_hover if self.item_hover == menu_chave or self.menu_aberto == menu_chave else self.cor_barra
            pygame.draw.rect(tela, cor_fundo, rect)
            txt = fonte_ui.render(titulo_exibir, True, self.cor_texto)
            tela.blit(txt, (rect.x + (rect.width // 2 - txt.get_width() // 2), rect.y + 4))
        if self.menu_aberto:
            itens_sub = self.estrutura[self.menu_aberto]
            rect_pai = self.rects_principais[self.menu_aberto]
            altura_item = 35
            rect_bg_dd = pygame.Rect(rect_pai.x, self.altura_barra, self.largura_dropdown, len(itens_sub) * altura_item)
            pygame.draw.rect(tela, self.cor_dropdown, rect_bg_dd)
            pygame.draw.rect(tela, self.cor_borda, rect_bg_dd, 1)
            self.rects_dropdown.clear()
            for i, texto_chave in enumerate(itens_sub):
                rect_item = pygame.Rect(rect_pai.x, self.altura_barra + i * altura_item, self.largura_dropdown, altura_item)
                self.rects_dropdown.append((texto_chave, rect_item))
                if self.sub_item_hover == i:
                    pygame.draw.rect(tela, self.cor_hover, rect_item)
                texto_exibir = _t(texto_chave)
                txt_sub = fonte_ui.render(texto_exibir, True, self.cor_texto)
                tela.blit(txt_sub, (rect_item.x + 15, rect_item.y + 8))
        if self.modal_ideias_aberto:
            self.desenhar_modal_ideias(tela, fonte_ui, estado)
        elif self.modal_patrocine_aberto:
            self.desenhar_modal_patrocine(tela, fonte_ui, estado)
        elif self.modal_motivacao_aberto:
            self.desenhar_modal_motivacao(tela, fonte_ui, estado)
        elif self.gerenciador_suporte.aberto:
            self.gerenciador_suporte.desenhar(tela, fonte_ui, pygame.font.SysFont(None, 24, bold=True), estado)