import pygame
from Core.i18n import _t

class Configuracoes:
    """
        Como funciona: Define a estrutura e estado do componente 'Configuracoes'.
        Para que serve: Atua como o modelo principal para instâncias de 'Configuracoes'.
        Onde é usada: Chamado a partir do módulo ou classe base de 'config'.
    """

    def __init__(self, x_painel, y_painel):
        """
            Como funciona: Inicializa os atributos e o estado inicial da instância.
            Para que serve: Prepara o objeto para ser utilizado no ciclo de vida da aplicação.
            Onde é usada: Chamado a partir do módulo ou classe base de 'config'.
        """
        self.x = x_painel
        self.y = y_painel
        self.largura_maxima = 650
        self.transparencia = 100
        self.cor_braco = (80, 40, 15)
        self.cor_notas = (255, 255, 255)
        self.modos_texto = ['letras', 'graus', 'vazio']
        self.nomes_modos = ['C D E (Notas)', '1 2 3 (Graus)', 'Apenas Bolinha']
        self.indice_modo = 0
        self.fontes_disponiveis = ['Arial', 'Verdana', 'Courier New', 'Consolas', 'Impact']
        self.indice_fonte = 0
        self.rects_fontes = []
        self.idiomas = [{'nome': 'Português', 'code': 'pt'}, {'nome': 'English', 'code': 'en'}, {'nome': 'Español', 'code': 'es'}, {'nome': 'Français', 'code': 'fr'}, {'nome': 'Deutsch', 'code': 'de'}]
        self.indice_idioma = 0
        self.rect_btn_idioma_esq = pygame.Rect(0, 0, 30, 30)
        self.rect_btn_idioma_dir = pygame.Rect(0, 0, 30, 30)
        self.temas = ['Azul', 'Vermelho', 'Verde', 'Roxo', 'Laranja']
        self.cores_temas = [(0, 120, 215), (200, 50, 50), (50, 180, 50), (150, 50, 200), (230, 100, 0)]
        self.indice_tema = 0
        self.AZUL_DESTAQUE = self.cores_temas[0]
        self.velocidade_jogo = 1.0
        self.volume_fx = 80
        self.particulas_habilitadas = True
        self.tamanho_notas = 1.0
        self.picker_aberto = False
        self.alvo_picker = None
        self.rect_picker = pygame.Rect(0, 0, 200, 150)
        self.surf_paleta = self.gerar_superficie_cores(self.rect_picker.width, self.rect_picker.height)
        self.largura_slider = 200
        self.rect_barra_transp = pygame.Rect(0, 0, self.largura_slider, 10)
        self.rect_cursor_transp = pygame.Rect(0, 0, 15, 20)
        self.arrastando_transp = False
        self.rect_barra_vol_fx = pygame.Rect(0, 0, self.largura_slider, 10)
        self.rect_cursor_vol_fx = pygame.Rect(0, 0, 15, 20)
        self.arrastando_vol_fx = False
        self.rect_btn_cor_braco = pygame.Rect(0, 0, 50, 50)
        self.rect_btn_cor_notas = pygame.Rect(0, 0, 50, 50)
        self.rects_modos = []
        self.rect_btn_particulas = pygame.Rect(0, 0, 30, 30)
        self.rect_btn_vel_menos = pygame.Rect(0, 0, 35, 30)
        self.rect_btn_vel_mais = pygame.Rect(0, 0, 35, 30)
        self.rect_btn_tema_esq = pygame.Rect(0, 0, 30, 30)
        self.rect_btn_tema_dir = pygame.Rect(0, 0, 30, 30)
        self.rect_btn_nota_menos = pygame.Rect(0, 0, 30, 30)
        self.rect_btn_nota_mais = pygame.Rect(0, 0, 30, 30)
        self.BRANCO = (255, 255, 255)
        self.PRETO = (0, 0, 0)
        self.CINZA = (100, 100, 100)

    def gerar_superficie_cores(self, largura, altura):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'gerar superficie cores'.
            Para que serve: Realiza as tarefas fundamentais de 'gerar superficie cores' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'gerar superficie cores'.
        """
        surf = pygame.Surface((largura, altura))
        for x in range(largura):
            for y in range(altura):
                matiz = int(x / largura * 360)
                brilho = int(100 - y / altura * 100)
                cor = pygame.Color(0)
                cor.hsva = (matiz, 100, brilho, 100)
                surf.set_at((x, y), cor)
        return surf

    def get_alpha(self):
        """
            Como funciona: Acessa e formata dados internos ou de configuração.
            Para que serve: Retorna as informações solicitadas sobre 'alpha'.
            Onde é usada: Chamado a partir do módulo ou classe base de 'config'.
        """
        return int(self.transparencia / 100 * 255)

    def get_cor_braco(self):
        """
            Como funciona: Acessa e formata dados internos ou de configuração.
            Para que serve: Retorna as informações solicitadas sobre 'cor braco'.
            Onde é usada: Chamado a partir do módulo ou classe base de 'config'.
        """
        return self.cor_braco

    def get_cor_notas(self):
        """
            Como funciona: Acessa e formata dados internos ou de configuração.
            Para que serve: Retorna as informações solicitadas sobre 'cor notas'.
            Onde é usada: Chamado a partir do módulo ou classe base de 'config'.
        """
        return self.cor_notas

    def get_modo_texto(self):
        """
            Como funciona: Acessa e formata dados internos ou de configuração.
            Para que serve: Retorna as informações solicitadas sobre 'modo texto'.
            Onde é usada: Chamado a partir do módulo ou classe base de 'config'.
        """
        return self.modos_texto[self.indice_modo]

    def get_fonte(self):
        """
            Como funciona: Acessa e formata dados internos ou de configuração.
            Para que serve: Retorna as informações solicitadas sobre 'fonte'.
            Onde é usada: Chamado a partir do módulo ou classe base de 'config'.
        """
        return self.fontes_disponiveis[self.indice_fonte]

    def get_vel_jogo(self):
        """
            Como funciona: Acessa e formata dados internos ou de configuração.
            Para que serve: Retorna as informações solicitadas sobre 'vel jogo'.
            Onde é usada: Chamado a partir do módulo ou classe base de 'config'.
        """
        return self.velocidade_jogo

    def get_vol_fx(self):
        """
            Como funciona: Acessa e formata dados internos ou de configuração.
            Para que serve: Retorna as informações solicitadas sobre 'vol fx'.
            Onde é usada: Chamado a partir do módulo ou classe base de 'config'.
        """
        return self.volume_fx / 100.0

    def get_particulas(self):
        """
            Como funciona: Acessa e formata dados internos ou de configuração.
            Para que serve: Retorna as informações solicitadas sobre 'particulas'.
            Onde é usada: Chamado a partir do módulo ou classe base de 'config'.
        """
        return self.particulas_habilitadas

    def get_cor_tema(self):
        """
            Como funciona: Acessa e formata dados internos ou de configuração.
            Para que serve: Retorna as informações solicitadas sobre 'cor tema'.
            Onde é usada: Chamado a partir do módulo ou classe base de 'config'.
        """
        cor = self.cores_temas[self.indice_tema]
        self.AZUL_DESTAQUE = cor
        return cor

    def get_escala_nota(self):
        """
            Como funciona: Acessa e formata dados internos ou de configuração.
            Para que serve: Retorna as informações solicitadas sobre 'escala nota'.
            Onde é usada: Chamado a partir do módulo ou classe base de 'config'.
        """
        return self.tamanho_notas

    def tratar_clique(self, pos_mouse, aba_config_ativa):
        """
            Como funciona: Verifica colisões e processa inputs do mouse/teclado.
            Para que serve: Mapeia ações do usuário para atualizações de estado.
            Onde é usada: Chamado a partir do módulo ou classe base de 'config'.
        """
        if not aba_config_ativa:
            return False
        if self.picker_aberto:
            if self.rect_picker.collidepoint(pos_mouse):
                x_rel, y_rel = (pos_mouse[0] - self.rect_picker.x, pos_mouse[1] - self.rect_picker.y)
                cor = self.surf_paleta.get_at((x_rel, y_rel))
                if self.alvo_picker == 'braco':
                    self.cor_braco = (cor.r, cor.g, cor.b)
                elif self.alvo_picker == 'notas':
                    self.cor_notas = (cor.r, cor.g, cor.b)
            self.picker_aberto = False
            return True
        if self.rect_cursor_transp.collidepoint(pos_mouse) or self.rect_barra_transp.collidepoint(pos_mouse):
            self.arrastando_transp = True
            return True
        if self.rect_cursor_vol_fx.collidepoint(pos_mouse) or self.rect_barra_vol_fx.collidepoint(pos_mouse):
            self.arrastando_vol_fx = True
            return True
        if self.rect_btn_cor_braco.collidepoint(pos_mouse):
            self.picker_aberto = True
            self.alvo_picker = 'braco'
            self.rect_picker.topleft = (pos_mouse[0] - 100, pos_mouse[1] - 160)
            return True
        if self.rect_btn_cor_notas.collidepoint(pos_mouse):
            self.picker_aberto = True
            self.alvo_picker = 'notas'
            self.rect_picker.topleft = (pos_mouse[0] - 100, pos_mouse[1] - 160)
            return True
        if self.rect_btn_particulas.collidepoint(pos_mouse):
            self.particulas_habilitadas = not self.particulas_habilitadas
            return True
        if self.rect_btn_vel_menos.collidepoint(pos_mouse):
            self.velocidade_jogo = round(max(0.5, self.velocidade_jogo - 0.1), 1)
            return True
        if self.rect_btn_vel_mais.collidepoint(pos_mouse):
            self.velocidade_jogo = round(min(3.0, self.velocidade_jogo + 0.1), 1)
            return True
        if self.rect_btn_tema_esq.collidepoint(pos_mouse):
            self.indice_tema = (self.indice_tema - 1) % len(self.temas)
            self.AZUL_DESTAQUE = self.cores_temas[self.indice_tema]
            return True
        if self.rect_btn_tema_dir.collidepoint(pos_mouse):
            self.indice_tema = (self.indice_tema + 1) % len(self.temas)
            self.AZUL_DESTAQUE = self.cores_temas[self.indice_tema]
            return True
        if self.rect_btn_nota_menos.collidepoint(pos_mouse):
            self.tamanho_notas = round(max(0.5, self.tamanho_notas - 0.1), 1)
            return True
        if self.rect_btn_nota_mais.collidepoint(pos_mouse):
            self.tamanho_notas = round(min(1.5, self.tamanho_notas + 0.1), 1)
            return True
        if self.rect_btn_idioma_esq.collidepoint(pos_mouse):
            self.indice_idioma = (self.indice_idioma - 1) % len(self.idiomas)
            codigo = self.idiomas[self.indice_idioma]['code']
            from Core.i18n import sistema_traducao
            sistema_traducao.atualizar_configuracao(codigo)
            return True
        if self.rect_btn_idioma_dir.collidepoint(pos_mouse):
            self.indice_idioma = (self.indice_idioma + 1) % len(self.idiomas)
            codigo = self.idiomas[self.indice_idioma]['code']
            from Core.i18n import sistema_traducao
            sistema_traducao.atualizar_configuracao(codigo)
            return True
        for i, r in enumerate(self.rects_modos):
            if r.collidepoint(pos_mouse):
                self.indice_modo = i
                return True
        for i, r in enumerate(self.rects_fontes):
            if r.collidepoint(pos_mouse):
                self.indice_fonte = i
                return True
        return False

    def processar_logica(self, pos_mouse):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'processar logica'.
            Para que serve: Realiza as tarefas fundamentais de 'processar logica' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'processar logica'.
        """
        if self.arrastando_transp:
            if not pygame.mouse.get_pressed()[0]:
                self.arrastando_transp = False
            else:
                rel_x = max(0, min(self.largura_slider, pos_mouse[0] - self.rect_barra_transp.x))
                self.transparencia = int(rel_x / self.largura_slider * 100)
        if self.arrastando_vol_fx:
            if not pygame.mouse.get_pressed()[0]:
                self.arrastando_vol_fx = False
            else:
                rel_x = max(0, min(self.largura_slider, pos_mouse[0] - self.rect_barra_vol_fx.x))
                self.volume_fx = int(rel_x / self.largura_slider * 100)

    def desenhar(self, tela, fontes, scroll_y=0, largura_max=1200):
        """
            Como funciona: Utiliza funções de renderização do Pygame para desenhar na tela.
            Para que serve: Apresenta o elemento visual 'desenhar' na interface gráfica.
            Onde é usada: Chamado a partir do módulo ou classe base de 'config'.
        """
        fonte_titulo = fontes['titulo']
        fonte_ui = fontes['ui']
        largura_util = largura_max - 40
        x_start, y_start = (self.x, self.y - scroll_y + 15)
        esp = 15
        altura_bloco = 185
        
        # Cálculo dinâmico de colunas baseado na largura
        min_largura_bloco = 220
        num_colunas = max(1, largura_util // (min_largura_bloco + esp))
        largura_bloco = (largura_util - (num_colunas - 1) * esp) // num_colunas
        
        x_atual, y_atual = (x_start, y_start)

        def avancar_posicao(x, y):
            """
                Como funciona: Executa o fluxo lógico necessário para a operação 'avancar posicao'.
            """
            x += largura_bloco + esp
            if x + largura_bloco > x_start + largura_util + 5:
                x = x_start
                y += altura_bloco + esp
            return (x, y)

        def container(x, y, titulo):
            """
                Como funciona: Desenha o fundo de cada bloco de configuração.
            """
            rect = pygame.Rect(x, y, largura_bloco, altura_bloco)
            pygame.draw.rect(tela, (35, 35, 45), rect, border_radius=12)
            pygame.draw.rect(tela, (80, 80, 100), rect, width=2, border_radius=12)
            
            txt_t = fonte_ui.render(_t(titulo), True, self.AZUL_DESTAQUE)
            if txt_t.get_width() > largura_bloco - 20:
                 txt_t = fontes['pequena'].render(_t(titulo), True, self.AZUL_DESTAQUE)
            tela.blit(txt_t, (x + 15, y + 10))
            return y + 45
        y_int = container(x_atual, y_atual, 'Ajustes de Áudio')
        tela.blit(fonte_ui.render(f"{_t('Transparência')}: {self.transparencia}%", True, self.BRANCO), (x_atual + 15, y_int))
        self.rect_barra_transp.topleft = (x_atual + 15, y_int + 25)
        pygame.draw.rect(tela, self.CINZA, self.rect_barra_transp, border_radius=5)
        px = self.rect_barra_transp.x + self.transparencia / 100 * self.largura_slider
        self.rect_cursor_transp.topleft = (px - 7, self.rect_barra_transp.y - 5)
        pygame.draw.rect(tela, self.BRANCO, self.rect_cursor_transp, border_radius=3)
        y_int += 65
        tela.blit(fonte_ui.render(f"{_t('Volume FX')}: {self.volume_fx}%", True, self.BRANCO), (x_atual + 15, y_int))
        self.rect_barra_vol_fx.topleft = (x_atual + 15, y_int + 25)
        pygame.draw.rect(tela, self.CINZA, self.rect_barra_vol_fx, border_radius=5)
        pxv = self.rect_barra_vol_fx.x + self.volume_fx / 100 * self.largura_slider
        self.rect_cursor_vol_fx.topleft = (pxv - 7, self.rect_barra_vol_fx.y - 5)
        pygame.draw.rect(tela, self.BRANCO, self.rect_cursor_vol_fx, border_radius=3)
        x_atual, y_atual = avancar_posicao(x_atual, y_atual)
        y_int = container(x_atual, y_atual, 'Cores do Instrumento')
        self.rect_btn_cor_braco.topleft = (x_atual + 20, y_int + 5)
        pygame.draw.rect(tela, self.cor_braco, self.rect_btn_cor_braco, border_radius=8)
        pygame.draw.rect(tela, self.BRANCO, self.rect_btn_cor_braco, 2, border_radius=8)
        tela.blit(fonte_ui.render(_t('Cor Madeira'), True, self.BRANCO), (self.rect_btn_cor_braco.right + 15, y_int + 15))
        self.rect_btn_cor_notas.topleft = (x_atual + 20, y_int + 70)
        pygame.draw.rect(tela, self.cor_notas, self.rect_btn_cor_notas, border_radius=8)
        pygame.draw.rect(tela, self.BRANCO, self.rect_btn_cor_notas, 2, border_radius=8)
        tela.blit(fonte_ui.render(_t('Cor Notas'), True, self.BRANCO), (self.rect_btn_cor_notas.right + 15, y_int + 80))
        x_atual, y_atual = avancar_posicao(x_atual, y_atual)
        y_int = container(x_atual, y_atual, 'Performance e Jogos')
        self.rect_btn_particulas.topleft = (x_atual + 15, y_int)
        pygame.draw.rect(tela, (60, 60, 60), self.rect_btn_particulas, border_radius=5)
        if self.particulas_habilitadas:
            pygame.draw.rect(tela, self.AZUL_DESTAQUE, self.rect_btn_particulas.inflate(-10, -10), border_radius=3)
        pygame.draw.rect(tela, self.BRANCO, self.rect_btn_particulas, 2, border_radius=5)
        tela.blit(fonte_ui.render(_t('Efeitos de Partículas'), True, self.BRANCO), (self.rect_btn_particulas.right + 10, y_int + 2))
        y_int += 50
        tela.blit(fonte_ui.render(f"{_t('Velocidade Jogos')}: {self.velocidade_jogo}x", True, self.BRANCO), (x_atual + 15, y_int))
        self.rect_btn_vel_menos.topleft = (x_atual + 15, y_int + 30)
        self.rect_btn_vel_mais.topleft = (x_atual + 110, y_int + 30)
        pygame.draw.rect(tela, self.AZUL_DESTAQUE, self.rect_btn_vel_menos, border_radius=5)
        pygame.draw.rect(tela, self.AZUL_DESTAQUE, self.rect_btn_vel_mais, border_radius=5)
        tela.blit(fonte_titulo.render('-', True, self.BRANCO), (self.rect_btn_vel_menos.centerx - 5, self.rect_btn_vel_menos.centery - 15))
        tela.blit(fonte_titulo.render('+', True, self.BRANCO), (self.rect_btn_vel_mais.centerx - 7, self.rect_btn_vel_mais.centery - 15))
        x_atual, y_atual = avancar_posicao(x_atual, y_atual)
        y_int = container(x_atual, y_atual, 'Temas e Aparência')
        tela.blit(fonte_ui.render(_t('Tema de Cores:'), True, self.BRANCO), (x_atual + 15, y_int))
        self.rect_btn_tema_esq.topleft = (x_atual + 15, y_int + 30)
        self.rect_btn_tema_dir.topleft = (x_atual + 180, y_int + 30)
        pygame.draw.rect(tela, self.AZUL_DESTAQUE, self.rect_btn_tema_esq, border_radius=5)
        pygame.draw.rect(tela, self.AZUL_DESTAQUE, self.rect_btn_tema_dir, border_radius=5)
        tela.blit(fonte_ui.render('<', True, self.BRANCO), (self.rect_btn_tema_esq.centerx - 5, self.rect_btn_tema_esq.centery - 10))
        tela.blit(fonte_ui.render('>', True, self.BRANCO), (self.rect_btn_tema_dir.centerx - 5, self.rect_btn_tema_dir.centery - 10))
        txt_t = fonte_ui.render(_t(self.temas[self.indice_tema]), True, self.BRANCO)
        tela.blit(txt_t, (x_atual + 100 - txt_t.get_width() // 2, y_int + 35))
        y_int += 75
        tela.blit(fonte_ui.render(f"{_t('Escala Notas')}: {self.tamanho_notas}x", True, self.BRANCO), (x_atual + 15, y_int))
        self.rect_btn_nota_menos.topleft = (x_atual + 15, y_int + 30)
        self.rect_btn_nota_mais.topleft = (x_atual + 110, y_int + 30)
        pygame.draw.rect(tela, self.AZUL_DESTAQUE, self.rect_btn_nota_menos, border_radius=5)
        pygame.draw.rect(tela, self.AZUL_DESTAQUE, self.rect_btn_nota_mais, border_radius=5)
        tela.blit(fonte_titulo.render('-', True, self.BRANCO), (self.rect_btn_nota_menos.centerx - 5, self.rect_btn_nota_menos.centery - 15))
        tela.blit(fonte_titulo.render('+', True, self.BRANCO), (self.rect_btn_nota_mais.centerx - 7, self.rect_btn_nota_mais.centery - 15))
        x_atual, y_atual = avancar_posicao(x_atual, y_atual)
        y_int = container(x_atual, y_atual, 'Estilo de Notas')
        self.rects_modos.clear()
        for i, n in enumerate(self.nomes_modos):
            r = pygame.Rect(x_atual + 15, y_int + i * 35, 220, 28)
            self.rects_modos.append(r)
            pygame.draw.rect(tela, self.AZUL_DESTAQUE if i == self.indice_modo else (60, 60, 60), r, border_radius=5)
            tela.blit(fonte_ui.render(_t(n), True, self.BRANCO), (r.x + 10, r.y + 3))
        x_atual, y_atual = avancar_posicao(x_atual, y_atual)
        y_int = container(x_atual, y_atual, 'Fontes do Sistema')
        self.rects_fontes.clear()
        for i, f in enumerate(self.fontes_disponiveis):
            r = pygame.Rect(x_atual + 15, y_int + i * 25, 180, 22)
            self.rects_fontes.append(r)
            pygame.draw.rect(tela, self.AZUL_DESTAQUE if i == self.indice_fonte else (60, 60, 60), r, border_radius=5)
            tela.blit(fonte_ui.render(f, True, self.BRANCO), (r.x + 10, r.y + 1))
        x_atual, y_atual = avancar_posicao(x_atual, y_atual)
        y_int = container(x_atual, y_atual, 'Idioma da Interface')
        self.rect_btn_idioma_esq.topleft = (x_atual + 15, y_int + 15)
        self.rect_btn_idioma_dir.topleft = (x_atual + 180, y_int + 15)
        pygame.draw.rect(tela, self.AZUL_DESTAQUE, self.rect_btn_idioma_esq, border_radius=5)
        pygame.draw.rect(tela, self.AZUL_DESTAQUE, self.rect_btn_idioma_dir, border_radius=5)
        tela.blit(fonte_ui.render('<', True, self.BRANCO), (self.rect_btn_idioma_esq.centerx - 5, self.rect_btn_idioma_esq.centery - 10))
        tela.blit(fonte_ui.render('>', True, self.BRANCO), (self.rect_btn_idioma_dir.centerx - 5, self.rect_btn_idioma_dir.centery - 10))
        txt_id = fonte_ui.render(_t(self.idiomas[self.indice_idioma]['nome']), True, self.BRANCO)
        tela.blit(txt_id, (x_atual + 100 - txt_id.get_width() // 2, y_int + 20))
        lbl_info = fontes['pequena'].render(_t('(API Translation + Cache)'), True, self.CINZA)
        tela.blit(lbl_info, (x_atual + 15, y_int + 55))
        if self.picker_aberto:
            fp = pygame.Rect(self.rect_picker.x - 5, self.rect_picker.y - 5, self.rect_picker.width + 10, self.rect_picker.height + 10)
            pygame.draw.rect(tela, self.PRETO, fp, border_radius=5)
            tela.blit(self.surf_paleta, self.rect_picker.topleft)
            pygame.draw.rect(tela, self.BRANCO, self.rect_picker, 2)