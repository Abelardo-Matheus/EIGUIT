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
        # Cor principal editavel por hexadecimal / RGB
        self.cor_customizada = None
        self.hex_texto = '0078D7'
        self.hex_foco = False
        self.rect_campo_hex = pygame.Rect(0, 0, 0, 0)
        self.rects_rgb = []
        self.slider_rgb_ativo = None
        self.rects_presets_tema = []
        self.rects_acentos = []
        self.rect_btn_aplicar = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_resetar = pygame.Rect(0, 0, 0, 0)
        # Tamanho da fonte da interface: 0=Pequena, 1=Normal, 2=Grande
        self.tamanhos_fonte = ['Pequena', 'Normal', 'Grande']
        self.escalas_fonte = [0.85, 1.0, 1.2]
        self.indice_tamanho_fonte = 1
        self.rects_tamanho_fonte = []
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
        cor = self.cor_customizada or self.cores_temas[self.indice_tema]
        self.AZUL_DESTAQUE = cor
        return cor

    def get_escala_fonte(self):
        """
            Como funciona: Devolve o multiplicador do tamanho das fontes da UI.
            Para que serve: Permitir interface pequena, normal ou grande.
            Onde e usada: main.py reconstroi as fontes quando isto muda.
        """
        return self.escalas_fonte[self.indice_tamanho_fonte]

    def definir_cor_principal(self, cor):
        """Aplica uma cor de destaque personalizada e sincroniza o campo hex."""
        cor = (max(0, min(255, int(cor[0]))),
               max(0, min(255, int(cor[1]))),
               max(0, min(255, int(cor[2]))))
        self.cor_customizada = cor
        self.AZUL_DESTAQUE = cor
        self.hex_texto = '%02X%02X%02X' % cor
        return cor

    def aplicar_hex(self, texto=None):
        """
            Como funciona: Converte o texto do campo hexadecimal em RGB.
            Para que serve: Digitar a cor exata da marca.
            Onde e usada: Ao confirmar o campo hex com Enter.
        """
        bruto = (texto if texto is not None else self.hex_texto).strip().lstrip('#')
        if len(bruto) == 3:
            bruto = ''.join(c * 2 for c in bruto)
        if len(bruto) != 6:
            self.hex_texto = '%02X%02X%02X' % tuple(self.get_cor_tema())
            return False
        try:
            valor = int(bruto, 16)
        except ValueError:
            self.hex_texto = '%02X%02X%02X' % tuple(self.get_cor_tema())
            return False
        self.definir_cor_principal(((valor >> 16) & 255, (valor >> 8) & 255, valor & 255))
        return True

    def resetar_aparencia(self):
        """Volta cores, transparencia e tamanhos aos valores de fabrica."""
        self.cor_customizada = None
        self.indice_tema = 0
        self.AZUL_DESTAQUE = self.cores_temas[0]
        self.hex_texto = '%02X%02X%02X' % tuple(self.cores_temas[0])
        self.transparencia = 100
        self.volume_fx = 80
        self.cor_braco = (80, 40, 15)
        self.cor_notas = (255, 255, 255)
        self.indice_tamanho_fonte = 1
        self.tamanho_notas = 1.0

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
        for rect, modo, cor in self.rects_presets_tema:
            if rect.collidepoint(pos_mouse):
                from config.design_system import TEMA
                import config.theme as _tema_legado
                TEMA.definir_modo(modo)
                _tema_legado.sincronizar_tema()
                self.definir_cor_principal(cor)
                return True

        if self.rect_campo_hex.collidepoint(pos_mouse):
            self.hex_foco = True
            return True
        self.hex_foco = False

        for barra, canal in self.rects_rgb:
            if barra.inflate(6, 16).collidepoint(pos_mouse):
                rel = max(0, min(barra.width, pos_mouse[0] - barra.x)) / barra.width
                cor = list(self.get_cor_tema())
                cor[canal] = round(rel * 255)
                self.definir_cor_principal(cor)
                self.slider_rgb_ativo = canal
                return True

        for rect, cor in self.rects_acentos:
            if rect.collidepoint(pos_mouse):
                self.definir_cor_principal(cor)
                return True

        for i, rect in enumerate(self.rects_tamanho_fonte):
            if rect.collidepoint(pos_mouse):
                self.indice_tamanho_fonte = i
                return True

        if self.rect_btn_aplicar.collidepoint(pos_mouse):
            self.aplicar_hex()
            return True
        if self.rect_btn_resetar.collidepoint(pos_mouse):
            self.resetar_aparencia()
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

    def tratar_teclado(self, evento):
        """
            Como funciona: Digitacao do campo hexadecimal da cor principal.
            Para que serve: Definir a cor exata por codigo.
            Onde e usada: Chamado pelo controlador de eventos quando ha foco.
        """
        if not self.hex_foco:
            return False
        if evento.key == pygame.K_RETURN:
            self.aplicar_hex()
            self.hex_foco = False
        elif evento.key == pygame.K_ESCAPE:
            self.hex_texto = '%02X%02X%02X' % tuple(self.get_cor_tema())
            self.hex_foco = False
        elif evento.key == pygame.K_BACKSPACE:
            self.hex_texto = self.hex_texto[:-1]
        elif evento.unicode and evento.unicode.upper() in '0123456789ABCDEF':
            if len(self.hex_texto) < 6:
                self.hex_texto += evento.unicode.upper()
                if len(self.hex_texto) == 6:
                    self.aplicar_hex()
        return True

    def processar_logica(self, pos_mouse):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'processar logica'.
            Para que serve: Realiza as tarefas fundamentais de 'processar logica' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'processar logica'.
        """
        if self.slider_rgb_ativo is not None:
            if not pygame.mouse.get_pressed()[0]:
                self.slider_rgb_ativo = None
            else:
                for barra, canal in self.rects_rgb:
                    if canal == self.slider_rgb_ativo and barra.width:
                        rel = max(0, min(barra.width, pos_mouse[0] - barra.x)) / barra.width
                        cor = list(self.get_cor_tema())
                        cor[canal] = round(rel * 255)
                        self.definir_cor_principal(cor)
                        break

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
            Como funciona: Monta uma grade responsiva de cartoes seguindo o
            canvas de design: presets de tema, cor principal com hexadecimal e
            RGB, acentos rotulados, cores do instrumento, tamanhos e idioma.
            Para que serve: Painel de Configuracoes > Cores da Interface.
            Onde e usada: Chamado pela aba inferior de Configuracoes.
        """
        from config.design_system import TEMA, ds, PALETA_ESCURA, PALETA_CLARA

        TEMA.definir_acento(self.get_cor_tema())
        fonte_ui, fonte_p = fontes['ui'], fontes['pequena']
        pos_mouse = pygame.mouse.get_pos()

        largura_util = largura_max - 40
        esp = ds.ESPACO_LG
        altura_bloco = 190
        colunas = max(1, largura_util // (235 + esp))
        largura_bloco = (largura_util - (colunas - 1) * esp) // colunas

        x_inicial = self.x
        x_atual, y_atual = x_inicial, self.y - scroll_y + ds.ESPACO_MD

        def novo_cartao(titulo):
            nonlocal x_atual, y_atual
            rect = pygame.Rect(x_atual, y_atual, largura_bloco, altura_bloco)
            y_conteudo = ds.painel(tela, rect, _t(titulo), fonte_p,
                                   acento=self.AZUL_DESTAQUE)
            info = (rect.x + ds.ESPACO_LG, y_conteudo + ds.ESPACO_XS,
                    largura_bloco - ds.ESPACO_LG * 2, rect.bottom)
            x_atual += largura_bloco + esp
            if x_atual + largura_bloco > x_inicial + largura_util + 5:
                x_atual = x_inicial
                y_atual += altura_bloco + esp
            return info

        def stepper(x, y, largura, rotulo, valor, rect_menos, rect_mais):
            ds.texto_em(tela, rotulo, fonte_p, (x, y), TEMA.texto_suave,
                        largura_max=largura)
            y_btn = y + fonte_p.get_height() + ds.ESPACO_SM
            rect_menos.topleft, rect_menos.size = (x, y_btn), (30, 30)
            rect_mais.topleft, rect_mais.size = (x + largura - 30, y_btn), (30, 30)
            ds.botao(tela, rect_menos, '-', fonte_ui, variante='secundario',
                     hover=rect_menos.collidepoint(pos_mouse))
            ds.botao(tela, rect_mais, '+', fonte_ui, variante='secundario',
                     hover=rect_mais.collidepoint(pos_mouse))
            ds.texto_centralizado(tela, str(valor), fonte_ui,
                                  pygame.Rect(rect_menos.right, y_btn,
                                              rect_mais.left - rect_menos.right, 30),
                                  TEMA.texto)
            return y_btn + 30 + ds.ESPACO_MD

        def seletor(x, y, largura, rotulo, valor, rect_esq, rect_dir):
            ds.texto_em(tela, rotulo, fonte_p, (x, y), TEMA.texto_suave,
                        largura_max=largura)
            y_btn = y + fonte_p.get_height() + ds.ESPACO_SM
            rect_esq.topleft, rect_esq.size = (x, y_btn), (30, 30)
            rect_dir.topleft, rect_dir.size = (x + largura - 30, y_btn), (30, 30)
            ds.botao(tela, rect_esq, '<', fonte_p, variante='secundario',
                     hover=rect_esq.collidepoint(pos_mouse))
            ds.botao(tela, rect_dir, '>', fonte_p, variante='secundario',
                     hover=rect_dir.collidepoint(pos_mouse))
            ds.texto_centralizado(tela, valor, fonte_ui,
                                  pygame.Rect(rect_esq.right, y_btn,
                                              rect_dir.left - rect_esq.right, 30),
                                  TEMA.texto)
            return y_btn + 30 + ds.ESPACO_MD

        # ------------------------------------------- 1. Presets de tema -----
        x, y, larg, fundo = novo_cartao('Presets de Tema')
        presets = [
            (_t('Azul Escuro'), 'escuro', (10, 14, 39), (0, 120, 215)),
            (_t('Roxo'), 'escuro', (26, 15, 46), (155, 122, 255)),
            (_t('Ciano'), 'escuro', (10, 21, 21), (0, 212, 255)),
            (_t('Claro'), 'claro', (240, 243, 250), (0, 110, 200)),
        ]
        self.rects_presets_tema = []
        gap = ds.ESPACO_SM
        largura_p = (larg - gap) // 2
        altura_p = 52
        for i, (nome, modo, c1, c2) in enumerate(presets):
            col, lin = i % 2, i // 2
            r = pygame.Rect(x + col * (largura_p + gap), y + lin * (altura_p + gap),
                            largura_p, altura_p)
            self.rects_presets_tema.append((r, modo, c2))
            ativo = (TEMA.modo == modo and tuple(self.get_cor_tema()) == c2)
            ds.gradiente_vertical(tela, r, c1, c2, ds.RAIO_MD)
            pygame.draw.rect(tela, ds.rgb(TEMA.texto if ativo else TEMA.borda), r,
                             width=2 if ativo else 1, border_radius=ds.RAIO_MD)
            ds.texto_em(tela, nome, fonte_p, (r.x + ds.ESPACO_SM, r.centery),
                        ds.contraste_texto(c1), ancora='midleft',
                        largura_max=r.width - ds.ESPACO_MD)

        # ------------------------------------------- 2. Cor principal -------
        x, y, larg, fundo = novo_cartao('Cor Principal')
        cor_atual = tuple(self.get_cor_tema())
        amostra = pygame.Rect(x, y, 56, 56)
        ds.amostra_cor(tela, amostra, cor_atual, True, ds.RAIO_MD)

        x_campo = amostra.right + ds.ESPACO_MD
        largura_campo = larg - 56 - ds.ESPACO_MD
        ds.texto_em(tela, _t('Hexadecimal'), fonte_p, (x_campo, y),
                    TEMA.texto_apagado, largura_max=largura_campo)
        self.rect_campo_hex = pygame.Rect(x_campo, y + fonte_p.get_height() + 2,
                                          largura_campo, 28)
        ds.caixa_texto(tela, self.rect_campo_hex, f'#{self.hex_texto}', fonte_p,
                       focado=self.hex_foco, placeholder='#0078D7')

        y_rgb = amostra.bottom + ds.ESPACO_MD
        self.rects_rgb = []
        canais = [('R', cor_atual[0], TEMA.alerta), ('G', cor_atual[1], TEMA.verde),
                  ('B', cor_atual[2], TEMA.ciano)]
        largura_canal = (larg - ds.ESPACO_SM * 2) // 3
        for i, (nome, valor, cor_canal) in enumerate(canais):
            xc = x + i * (largura_canal + ds.ESPACO_SM)
            ds.texto_em(tela, f'{nome} {valor}', fonte_p, (xc, y_rgb),
                        TEMA.texto_apagado)
            barra = pygame.Rect(xc, y_rgb + fonte_p.get_height() + ds.ESPACO_XS,
                                largura_canal, ds.ALTURA_TRILHO)
            ds.trilho(tela, barra, valor / 255, cor_canal)
            self.rects_rgb.append((barra, i))

        # ------------------------------------------- 3. Cores de acento -----
        x, y, larg, fundo = novo_cartao('Cores de Acento')
        paleta = PALETA_ESCURA if TEMA.escuro else PALETA_CLARA
        acentos = [
            (_t('Primaria'), paleta['primaria']), (_t('Ciano'), paleta['ciano']),
            (_t('Verde'), paleta['verde']), (_t('Alerta'), paleta['alerta']),
            (_t('Aviso'), paleta['aviso']),
        ]
        self.rects_acentos = []
        largura_a = (larg - ds.ESPACO_SM * (len(acentos) - 1)) // len(acentos)
        for i, (nome, cor) in enumerate(acentos):
            r = pygame.Rect(x + i * (largura_a + ds.ESPACO_SM), y, largura_a, 44)
            self.rects_acentos.append((r, tuple(cor)))
            ds.amostra_cor(tela, r, cor, tuple(cor) == cor_atual, ds.RAIO_SM)
            ds.texto_em(tela, nome, fonte_p, (r.centerx, r.bottom + ds.ESPACO_XS),
                        TEMA.texto_apagado, ancora='midtop', largura_max=largura_a + 6)

        # ------------------------------------------- 4. Instrumento ---------
        x, y, larg, fundo = novo_cartao('Cores do Instrumento')
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

        # ------------------------------------------- 5. Tema da interface ---
        x, y, larg, fundo = novo_cartao('Tema da Interface')
        ds.texto_em(tela, _t('Modo claro / escuro'), fonte_p, (x, y),
                    TEMA.texto_suave, largura_max=larg)
        y += fonte_p.get_height() + ds.ESPACO_MD
        self.rect_btn_modo_tema = pygame.Rect(x, y, 56, 28)
        ds.interruptor(tela, self.rect_btn_modo_tema, not TEMA.escuro)
        ds.icone_tema(tela, (self.rect_btn_modo_tema.right + 22,
                             self.rect_btn_modo_tema.centery), TEMA.modo,
                      TEMA.aviso if not TEMA.escuro else TEMA.texto_suave, 7)
        ds.texto_em(tela, _t('Claro') if not TEMA.escuro else _t('Escuro'), fonte_ui,
                    (self.rect_btn_modo_tema.right + 42,
                     self.rect_btn_modo_tema.centery), TEMA.texto, ancora='midleft')
        y += 28 + ds.ESPACO_MD
        ds.texto_em(tela, _t('Tambem disponivel na barra superior'), fonte_p,
                    (x, y), TEMA.texto_apagado, largura_max=larg)

        # ------------------------------------------- 6. Transparencia -------
        x, y, larg, fundo = novo_cartao('Audio e Interface')
        y += fonte_p.get_height() + ds.ESPACO_SM
        self.largura_slider = larg
        self.rect_barra_transp = pygame.Rect(x, y, larg, ds.ALTURA_TRILHO)
        _, self.rect_cursor_transp = ds.slider(
            tela, self.rect_barra_transp, self.transparencia / 100,
            rotulo=_t('Transparencia'), valor=f'{self.transparencia}%', fonte=fonte_p)
        y += 52 + fonte_p.get_height()
        self.rect_barra_vol_fx = pygame.Rect(x, y, larg, ds.ALTURA_TRILHO)
        _, self.rect_cursor_vol_fx = ds.slider(
            tela, self.rect_barra_vol_fx, self.volume_fx / 100,
            rotulo=_t('Volume FX'), valor=f'{self.volume_fx}%', fonte=fonte_p)

        # ------------------------------------------- 7. Tamanhos ------------
        x, y, larg, fundo = novo_cartao('Tamanhos')
        ds.texto_em(tela, _t('Fonte da interface'), fonte_p, (x, y),
                    TEMA.texto_suave, largura_max=larg)
        y += fonte_p.get_height() + ds.ESPACO_SM
        self.rects_tamanho_fonte = []
        largura_t = (larg - ds.ESPACO_SM * 2) // 3
        for i, nome in enumerate(self.tamanhos_fonte):
            r = pygame.Rect(x + i * (largura_t + ds.ESPACO_SM), y, largura_t, 28)
            self.rects_tamanho_fonte.append(r)
            ds.chip(tela, r, _t(nome), fonte_p, ativo=i == self.indice_tamanho_fonte)
        y += 28 + ds.ESPACO_MD
        stepper(x, y, larg, _t('Escala das notas'), f'{self.tamanho_notas}x',
                self.rect_btn_nota_menos, self.rect_btn_nota_mais)

        # ------------------------------------------- 8. Estilo de notas -----
        x, y, larg, fundo = novo_cartao('Estilo das Notas')
        self.rects_modos.clear()
        for i, nome in enumerate(self.nomes_modos):
            r = pygame.Rect(x, y + i * 34, larg, 28)
            self.rects_modos.append(r)
            ds.chip(tela, r, _t(nome), fonte_p, ativo=i == self.indice_modo)

        # ------------------------------------------- 9. Fonte ---------------
        x, y, larg, fundo = novo_cartao('Fonte da Interface')
        self.rects_fontes.clear()
        for i, nome in enumerate(self.fontes_disponiveis):
            r = pygame.Rect(x, y + i * 25, larg, 22)
            self.rects_fontes.append(r)
            ds.chip(tela, r, nome, fonte_p, ativo=i == self.indice_fonte)

        # ------------------------------------------- 10. Performance --------
        x, y, larg, fundo = novo_cartao('Performance e Jogos')
        self.rect_btn_particulas = pygame.Rect(x, y, 26, 26)
        ds.caixa_selecao(tela, self.rect_btn_particulas, self.particulas_habilitadas)
        ds.texto_em(tela, _t('Efeitos de Particulas'), fonte_p,
                    (self.rect_btn_particulas.right + ds.ESPACO_MD,
                     self.rect_btn_particulas.centery), TEMA.texto_suave,
                    ancora='midleft', largura_max=larg - 40)
        y += 26 + ds.ESPACO_LG
        stepper(x, y, larg, _t('Velocidade dos Jogos'), f'{self.velocidade_jogo}x',
                self.rect_btn_vel_menos, self.rect_btn_vel_mais)

        # ------------------------------------------- 11. Idioma -------------
        x, y, larg, fundo = novo_cartao('Idioma da Interface')
        y = seletor(x, y, larg, _t('Idioma'),
                    _t(self.idiomas[self.indice_idioma]['nome']),
                    self.rect_btn_idioma_esq, self.rect_btn_idioma_dir)
        ds.texto_em(tela, _t('(API de traducao + cache local)'), fonte_p, (x, y),
                    TEMA.texto_apagado, largura_max=larg)

        # ------------------------------------------- 12. Acoes --------------
        x, y, larg, fundo = novo_cartao('Acoes')
        largura_btn = (larg - ds.ESPACO_SM) // 2
        self.rect_btn_aplicar = pygame.Rect(x, y, largura_btn, 34)
        self.rect_btn_resetar = pygame.Rect(x + largura_btn + ds.ESPACO_SM, y,
                                            largura_btn, 34)
        ds.botao(tela, self.rect_btn_aplicar, _t('Aplicar'), fonte_p,
                 variante='primario',
                 hover=self.rect_btn_aplicar.collidepoint(pos_mouse))
        ds.botao(tela, self.rect_btn_resetar, _t('Resetar'), fonte_p,
                 variante='secundario',
                 hover=self.rect_btn_resetar.collidepoint(pos_mouse))
        ds.texto_em(tela, _t('Resetar volta cores, tamanhos e transparencia ao padrao.'),
                    fonte_p, (x, y + 34 + ds.ESPACO_MD), TEMA.texto_apagado,
                    largura_max=larg)

        # ------------------------------------------- Color picker -----------
        if self.picker_aberto:
            moldura = self.rect_picker.inflate(12, 12)
            ds.sombra(tela, moldura, ds.RAIO_LG)
            ds.superficie_translucida(tela, moldura, TEMA.superficie, 250,
                                      ds.RAIO_LG, TEMA.acento, 2)
            tela.blit(self.surf_paleta, self.rect_picker.topleft)
