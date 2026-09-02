import pygame
from core.i18n import _t

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
        self.rect_btn_modo_tema = pygame.Rect(0, 0, 56, 28)
        self.rects_cores_temas = []
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
        if self.rect_btn_modo_tema.collidepoint(pos_mouse):
            from config.design_system import TEMA
            import config.theme as _tema_legado
            TEMA.alternar()
            _tema_legado.sincronizar_tema()
            return True
        for i, r in enumerate(self.rects_cores_temas):
            if r.collidepoint(pos_mouse):
                self.indice_tema = i
                self.AZUL_DESTAQUE = self.cores_temas[i]
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
            from core.i18n import sistema_traducao
            sistema_traducao.atualizar_configuracao(codigo)
            return True
        if self.rect_btn_idioma_dir.collidepoint(pos_mouse):
            self.indice_idioma = (self.indice_idioma + 1) % len(self.idiomas)
            codigo = self.idiomas[self.indice_idioma]['code']
            from core.i18n import sistema_traducao
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
            Como funciona: Monta uma grade responsiva de cartoes, cada um com um
            grupo de ajustes, usando os componentes do design system.
            Para que serve: Painel de Configuracoes > Cores/Aparencia.
            Onde e usada: Chamado pela aba inferior de Configuracoes.
        """
        from config.design_system import TEMA, ds

        TEMA.definir_acento(self.get_cor_tema())
        fonte_titulo = fontes['titulo']
        fonte_ui = fontes['ui']
        fonte_p = fontes['pequena']
        pos_mouse = pygame.mouse.get_pos()

        largura_util = largura_max - 40
        esp = ds.ESPACO_LG
        altura_bloco = 190
        min_largura = 235
        colunas = max(1, largura_util // (min_largura + esp))
        largura_bloco = (largura_util - (colunas - 1) * esp) // colunas

        x_inicial = self.x
        x_atual = x_inicial
        y_atual = self.y - scroll_y + ds.ESPACO_MD

        def novo_cartao(titulo):
            """Desenha o cartao e devolve (x_conteudo, y_conteudo, largura_interna)."""
            nonlocal x_atual, y_atual
            rect = pygame.Rect(x_atual, y_atual, largura_bloco, altura_bloco)
            y_conteudo = ds.painel(tela, rect, _t(titulo), fonte_p,
                                   acento=self.AZUL_DESTAQUE)
            info = (rect.x + ds.ESPACO_LG, y_conteudo + ds.ESPACO_XS,
                    largura_bloco - ds.ESPACO_LG * 2)
            x_atual += largura_bloco + esp
            if x_atual + largura_bloco > x_inicial + largura_util + 5:
                x_atual = x_inicial
                y_atual += altura_bloco + esp
            return info

        def stepper(x, y, largura, rotulo, valor, rect_menos, rect_mais):
            """Rotulo + [-] valor [+] reaproveitado por varios ajustes."""
            ds.texto_em(tela, rotulo, fonte_p, (x, y), TEMA.texto_suave,
                        largura_max=largura)
            y_btn = y + fonte_p.get_height() + ds.ESPACO_SM
            rect_menos.topleft = (x, y_btn)
            rect_menos.size = (30, 30)
            rect_mais.topleft = (x + largura - 30, y_btn)
            rect_mais.size = (30, 30)
            ds.botao(tela, rect_menos, '-', fonte_ui, variante='secundario',
                     hover=rect_menos.collidepoint(pos_mouse))
            ds.botao(tela, rect_mais, '+', fonte_ui, variante='secundario',
                     hover=rect_mais.collidepoint(pos_mouse))
            ds.texto_centralizado(
                tela, str(valor), fonte_ui,
                pygame.Rect(rect_menos.right, y_btn,
                            rect_mais.left - rect_menos.right, 30), TEMA.texto)
            return y_btn + 30 + ds.ESPACO_MD

        def seletor(x, y, largura, rotulo, valor, rect_esq, rect_dir):
            """Rotulo + [<] valor [>] para listas circulares."""
            ds.texto_em(tela, rotulo, fonte_p, (x, y), TEMA.texto_suave,
                        largura_max=largura)
            y_btn = y + fonte_p.get_height() + ds.ESPACO_SM
            rect_esq.topleft = (x, y_btn)
            rect_esq.size = (30, 30)
            rect_dir.topleft = (x + largura - 30, y_btn)
            rect_dir.size = (30, 30)
            ds.botao(tela, rect_esq, '<', fonte_p, variante='secundario',
                     hover=rect_esq.collidepoint(pos_mouse))
            ds.botao(tela, rect_dir, '>', fonte_p, variante='secundario',
                     hover=rect_dir.collidepoint(pos_mouse))
            ds.texto_centralizado(
                tela, valor, fonte_ui,
                pygame.Rect(rect_esq.right, y_btn,
                            rect_dir.left - rect_esq.right, 30), TEMA.texto)
            return y_btn + 30 + ds.ESPACO_MD

        # ---------------------------------------------------- 1. Audio -----
        x, y, larg = novo_cartao('Audio e Interface')
        y += fonte_p.get_height() + ds.ESPACO_SM
        self.rect_barra_transp = pygame.Rect(x, y, larg, ds.ALTURA_TRILHO)
        self.largura_slider = larg
        _, self.rect_cursor_transp = ds.slider(
            tela, self.rect_barra_transp, self.transparencia / 100,
            rotulo=_t('Transparencia'), valor=f'{self.transparencia}%', fonte=fonte_p)

        y += 52 + fonte_p.get_height()
        self.rect_barra_vol_fx = pygame.Rect(x, y, larg, ds.ALTURA_TRILHO)
        _, self.rect_cursor_vol_fx = ds.slider(
            tela, self.rect_barra_vol_fx, self.volume_fx / 100,
            rotulo=_t('Volume FX'), valor=f'{self.volume_fx}%', fonte=fonte_p)

        # ------------------------------------------ 2. Cores do braco ------
        x, y, larg = novo_cartao('Cores do Instrumento')
        self.rect_btn_cor_braco = pygame.Rect(x, y, 46, 46)
        ds.amostra_cor(tela, self.rect_btn_cor_braco, self.cor_braco)
        ds.texto_em(tela, _t('Cor da Madeira'), fonte_p,
                    (self.rect_btn_cor_braco.right + ds.ESPACO_MD,
                     self.rect_btn_cor_braco.centery), TEMA.texto_suave,
                    ancora='midleft', largura_max=larg - 60)

        y += 46 + ds.ESPACO_MD
        self.rect_btn_cor_notas = pygame.Rect(x, y, 46, 46)
        ds.amostra_cor(tela, self.rect_btn_cor_notas, self.cor_notas)
        ds.texto_em(tela, _t('Cor das Notas'), fonte_p,
                    (self.rect_btn_cor_notas.right + ds.ESPACO_MD,
                     self.rect_btn_cor_notas.centery), TEMA.texto_suave,
                    ancora='midleft', largura_max=larg - 60)

        # ----------------------------------------- 3. Tema da interface ----
        x, y, larg = novo_cartao('Tema da Interface')
        ds.texto_em(tela, _t('Modo claro / escuro'), fonte_p, (x, y),
                    TEMA.texto_suave, largura_max=larg)
        y += fonte_p.get_height() + ds.ESPACO_MD

        self.rect_btn_modo_tema = pygame.Rect(x, y, 56, 28)
        ds.interruptor(tela, self.rect_btn_modo_tema, not TEMA.escuro)
        rotulo_modo = _t('Claro') if not TEMA.escuro else _t('Escuro')
        ds.icone_tema(tela, (self.rect_btn_modo_tema.right + 22,
                             self.rect_btn_modo_tema.centery),
                      TEMA.modo, TEMA.aviso if not TEMA.escuro else TEMA.texto_suave, 7)
        ds.texto_em(tela, rotulo_modo, fonte_ui,
                    (self.rect_btn_modo_tema.right + 42,
                     self.rect_btn_modo_tema.centery), TEMA.texto, ancora='midleft')

        y += 28 + ds.ESPACO_MD
        ds.texto_em(tela, _t('Tambem disponivel na barra superior'), fonte_p,
                    (x, y), TEMA.texto_apagado, largura_max=larg)

        # ------------------------------------- 4. Performance e jogos ------
        x, y, larg = novo_cartao('Performance e Jogos')
        self.rect_btn_particulas = pygame.Rect(x, y, 26, 26)
        ds.caixa_selecao(tela, self.rect_btn_particulas, self.particulas_habilitadas)
        ds.texto_em(tela, _t('Efeitos de Particulas'), fonte_p,
                    (self.rect_btn_particulas.right + ds.ESPACO_MD,
                     self.rect_btn_particulas.centery), TEMA.texto_suave,
                    ancora='midleft', largura_max=larg - 40)
        y += 26 + ds.ESPACO_LG
        stepper(x, y, larg, _t('Velocidade dos Jogos'), f'{self.velocidade_jogo}x',
                self.rect_btn_vel_menos, self.rect_btn_vel_mais)

        # --------------------------------------- 5. Cor de destaque --------
        x, y, larg = novo_cartao('Cor de Destaque')
        y = seletor(x, y, larg, _t('Tema de cores'), _t(self.temas[self.indice_tema]),
                    self.rect_btn_tema_esq, self.rect_btn_tema_dir)
        largura_amostra = (larg - (len(self.cores_temas) - 1) * ds.ESPACO_SM) // len(self.cores_temas)
        self.rects_cores_temas = []
        for i, cor in enumerate(self.cores_temas):
            rect_c = pygame.Rect(x + i * (largura_amostra + ds.ESPACO_SM), y,
                                 largura_amostra, 22)
            self.rects_cores_temas.append(rect_c)
            ds.amostra_cor(tela, rect_c, cor, selecionado=i == self.indice_tema,
                           raio=ds.RAIO_SM)

        # ------------------------------------------ 6. Escala das notas ----
        x, y, larg = novo_cartao('Tamanho das Notas')
        stepper(x, y, larg, _t('Escala das bolinhas'), f'{self.tamanho_notas}x',
                self.rect_btn_nota_menos, self.rect_btn_nota_mais)

        # -------------------------------------------- 7. Estilo de notas ---
        x, y, larg = novo_cartao('Estilo das Notas')
        self.rects_modos.clear()
        for i, nome in enumerate(self.nomes_modos):
            r = pygame.Rect(x, y + i * 34, larg, 28)
            self.rects_modos.append(r)
            ds.chip(tela, r, _t(nome), fonte_p, ativo=i == self.indice_modo)

        # -------------------------------------------------- 8. Fontes ------
        x, y, larg = novo_cartao('Fonte da Interface')
        self.rects_fontes.clear()
        for i, nome in enumerate(self.fontes_disponiveis):
            r = pygame.Rect(x, y + i * 25, larg, 22)
            self.rects_fontes.append(r)
            ds.chip(tela, r, nome, fonte_p, ativo=i == self.indice_fonte)

        # -------------------------------------------------- 9. Idioma ------
        x, y, larg = novo_cartao('Idioma da Interface')
        y = seletor(x, y, larg, _t('Idioma'),
                    _t(self.idiomas[self.indice_idioma]['nome']),
                    self.rect_btn_idioma_esq, self.rect_btn_idioma_dir)
        ds.texto_em(tela, _t('(API de traducao + cache local)'), fonte_p, (x, y),
                    TEMA.texto_apagado, largura_max=larg)

        # ---------------------------------------------- Color picker -------
        if self.picker_aberto:
            moldura = self.rect_picker.inflate(12, 12)
            ds.sombra(tela, moldura, ds.RAIO_LG)
            ds.superficie_translucida(tela, moldura, TEMA.superficie, 250,
                                      ds.RAIO_LG, TEMA.acento, 2)
            tela.blit(self.surf_paleta, self.rect_picker.topleft)
