# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# =============================================================================

import pygame

class TutorialSuporte:
    def __init__(self):
        self.aberto = False
        self.aba_ativa = 0
        self.scroll_y = 0
        self.max_scroll = 0
        
        self.BRANCO = (255, 255, 255)
        self.CINZA = (150, 150, 150)
        self.AZUL = (0, 120, 215)
        self.AZUL_CLARO = (0, 160, 255)

        self.abas = ["Escalas", "Configurações", "Metrônomo", "Acordes", "Análise IA"]
        
        # Dicionário com os tutoriais. Cada item é uma seção do scroll.
        self.conteudo = {
            0: [ # Escalas
                {"titulo": "Sistema Drag & Drop", "texto": "Para utilizar as escalas, ative o ícone do 'Alfinete' (canto superior direito). Com o modo de edição ativado, clique e arraste qualquer escala do painel inferior diretamente para o braço da guitarra."},
                {"titulo": "Sobreposição Dinâmica", "texto": "Você pode soltar a escala em qualquer parte do braço. O EIGUIT recalcula automaticamente as notas baseando-se na afinação atual e no tom selecionado."},
                {"titulo": "Removendo Escalas", "texto": "Errou a posição ou quer limpar a tela? Basta clicar com o Botão Direito do mouse sobre o braço da guitarra para devolver todas as escalas de volta ao painel de origem."}
            ],
            1: [ # Configurações
                {"titulo": "Personalização Visual", "texto": "Acesse a aba de configurações para alterar as cores do braço da guitarra e das notas. Use o seletor de cores integrado para encontrar o tom exato que mais agrada sua visão durante os estudos."},
                {"titulo": "Modos de Visualização", "texto": "Você pode alternar o texto exibido dentro das bolinhas. Escolha entre 'Notas' (C, D, E), 'Graus' (1, 2, 3) para estudar intervalos, ou oculte o texto para focar apenas nos padrões visuais (shapes)."},
                {"titulo": "Ajuste de Transparência", "texto": "Utilize o controle deslizante de Alpha (Transparência) para mesclar a visualização das escalas com a madeira da guitarra, criando uma interface menos agressiva aos olhos."}
            ],
            2: [ # Metrônomo
                {"titulo": "Controle de Tempo (BPM)", "texto": "O metrônomo é o coração do seu estudo rítmico. Ajuste a velocidade usando os botões de + e - ou clique na barra deslizante. A faixa vai de 40 a 240 Batidas Por Minuto."},
                {"titulo": "Assinatura de Compasso", "texto": "Ajuste os tempos por compasso clicando nos números centrais (ex: 4/4, 3/4). O primeiro tempo (cabeça do compasso) sempre emitirá um som diferenciado para guiá-lo."},
                {"titulo": "Controles Flutuantes", "texto": "Mantenha o mini-metrônomo onde for mais conveniente na tela. Ele continuará tocando em segundo plano mesmo enquanto você interage com outras janelas."}
            ],
            3: [ # Acordes
                {"titulo": "O Campo Harmônico", "texto": "A janela de acordes arrastáveis exibe o campo harmônico completo da tônica escolhida. Clique em qualquer acorde para destacá-lo imediatamente no braço da guitarra."},
                {"titulo": "Destaque de Graus", "texto": "Ao clicar em um acorde, o EIGUIT pinta automaticamente as Tônicas, Terças e Quintas (Tríade) específicas daquele acorde, ajudando na visualização de arpejos ao longo do braço."},
                {"titulo": "Mudança Global de Tom", "texto": "Ao alterar a tônica ou o tipo de escala no módulo do Campo Harmônico, todo o sistema (incluindo as escalas do painel inferior) se adapta instantaneamente para o novo tom."}
            ],
            4: [ # Análise IA
                {"titulo": "Afinador e Detecção", "texto": "Conecte seu microfone nas configurações de áudio. O sistema analisará a frequência da sua guitarra em tempo real, indicando na tela exatamente qual nota está sendo tocada."},
                {"titulo": "Treinamento Rítmico", "texto": "Use a IA para avaliar sua precisão. O EIGUIT escuta suas palhetadas e cruza as informações com o BPM do metrônomo, indicando se você está adiantando ou atrasando o tempo."},
                {"titulo": "Gamificação (Jogos)", "texto": "Aprenda brincando. Acesse a aba de jogos para desafios interativos onde você precisa acertar as notas no tempo correto, ganhando pontos e elevando seu nível prático."}
            ]
        }

    def quebrar_texto(self, texto, fonte, max_largura):
        """Função auxiliar para fazer o Word Wrap (Quebra de linha) do Pygame"""
        palavras = texto.split(' ')
        linhas = []
        linha_atual = ""
        for palavra in palavras:
            teste_linha = linha_atual + palavra + " "
            if fonte.size(teste_linha)[0] < max_largura:
                linha_atual = teste_linha
            else:
                linhas.append(linha_atual)
                linha_atual = palavra + " "
        linhas.append(linha_atual)
        return linhas

    def tratar_eventos(self, eventos, pos_mouse):
        if not self.aberto: return False

        for evento in eventos:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                self.aberto = False
                return True
                
            if evento.type == pygame.MOUSEWHEEL:
                velocidade = 30
                self.scroll_y -= evento.y * velocidade
                self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))
                return True
                
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                # Fechar
                if hasattr(self, 'rect_fechar') and self.rect_fechar.collidepoint(pos_mouse):
                    self.aberto = False
                    
                # Mudar de Aba
                if hasattr(self, 'rects_abas'):
                    for i, rect in enumerate(self.rects_abas):
                        if rect.collidepoint(pos_mouse):
                            self.aba_ativa = i
                            self.scroll_y = 0 # Reseta o scroll ao mudar de aba
                            break
            return True # Engole o clique para não passar pra guitarra
        return False
    
    def calcular_centro_camera(self, estado, tela, largura_obj, altura_obj):
        if estado and hasattr(estado, 'camera'):
            w_monitor = getattr(estado, 'LARGURA_TELA', 1280)
            h_monitor = getattr(estado, 'ALTURA_TELA', 720)
            zoom = estado.camera.zoom
            cx = estado.camera.offset_x + (w_monitor / 2) / zoom - (largura_obj / 2)
            cy = estado.camera.offset_y + (h_monitor / 2) / zoom - (altura_obj / 2)
            return int(cx), int(cy)
        return tela.get_width() // 2 - largura_obj // 2, tela.get_height() // 2 - altura_obj // 2

    def desenhar(self, tela, fonte_ui, fonte_titulo, estado=None): 
        if not self.aberto: return

        overlay = pygame.Surface((tela.get_width(), tela.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        tela.blit(overlay, (0, 0))

        largura_modal = 850
        altura_modal = 550
        # === A NOVA MATEMÁTICA ===
        cx, cy = self.calcular_centro_camera(estado, tela, largura_modal, altura_modal)
        
        rect_modal = pygame.Rect(cx, cy, largura_modal, altura_modal)
        # Desenha a Janela
        pygame.draw.rect(tela, (30, 30, 30), rect_modal, border_radius=10)
        pygame.draw.rect(tela, (100, 100, 100), rect_modal, width=2, border_radius=10)

        # =========================================================
        # CABEÇALHO E ABAS
        # =========================================================
        tit = fonte_titulo.render("Central de Suporte & Tutoriais", True, self.BRANCO)
        tela.blit(tit, (cx + 20, cy + 20))

        self.rects_abas = []
        largura_aba = (largura_modal - 40) / len(self.abas)
        y_abas = cy + 60
        
        for i, nome_aba in enumerate(self.abas):
            rect_aba = pygame.Rect(cx + 20 + (i * largura_aba), y_abas, largura_aba - 5, 35)
            self.rects_abas.append(rect_aba)
            
            cor_fundo = self.AZUL_CLARO if self.aba_ativa == i else (60, 60, 60)
            pygame.draw.rect(tela, cor_fundo, rect_aba, border_radius=5)
            
            txt_aba = fonte_ui.render(nome_aba, True, self.BRANCO)
            tela.blit(txt_aba, (rect_aba.centerx - txt_aba.get_width()//2, rect_aba.centery - txt_aba.get_height()//2))

        # =========================================================
        # ÁREA DE SCROLL (CONTEÚDO)
        # =========================================================
        y_conteudo = y_abas + 45
        altura_conteudo = altura_modal - 120
        rect_clipping = pygame.Rect(cx + 20, y_conteudo, largura_modal - 40, altura_conteudo)
        
        pygame.draw.rect(tela, (20, 20, 20), rect_clipping, border_radius=5)
        tela.set_clip(rect_clipping) # Corta tudo que passar dessa caixa!

        y_item = y_conteudo + 20 - self.scroll_y
        itens_atuais = self.conteudo.get(self.aba_ativa, [])
        
        # --- MATEMÁTICA DE MARGENS CORRIGIDA ---
        margem_esq = 40
        margem_dir = 60 # Adiciona um respiro robusto na direita para não colar na scrollbar
        espacamento_meio = 30
        
        largura_imagem = 280
        altura_imagem = 160
        
        # A largura do texto agora respeita as margens dos dois lados
        largura_texto_max = largura_modal - margem_esq - margem_dir - largura_imagem - espacamento_meio

        for i, item in enumerate(itens_atuais):
            # Lógica Zigue-Zague (Par = Img na Esquerda / Ímpar = Img na Direita)
            img_na_esquerda = (i % 2 == 0)
            
            if img_na_esquerda:
                x_img = cx + margem_esq
                x_texto = x_img + largura_imagem + espacamento_meio
            else:
                x_texto = cx + margem_esq
                x_img = x_texto + largura_texto_max + espacamento_meio

            # 1. Desenha Placeholder da Imagem
            rect_img = pygame.Rect(x_img, y_item, largura_imagem, altura_imagem)
            pygame.draw.rect(tela, (50, 50, 50), rect_img, border_radius=8)
            pygame.draw.rect(tela, self.CINZA, rect_img, width=2, border_radius=8)
            
            txt_img = fonte_ui.render("Imagem Ilustrativa", True, (100, 100, 100))
            tela.blit(txt_img, (rect_img.centerx - txt_img.get_width()//2, rect_img.centery - txt_img.get_height()//2))

            # 2. Renderiza o Título do Bloco
            txt_titulo = fonte_titulo.render(item["titulo"], True, self.AZUL_CLARO)
            tela.blit(txt_titulo, (x_texto, y_item))

            # 3. Renderiza o Texto descritivo com Quebra de Linha Automática
            linhas = self.quebrar_texto(item["texto"], fonte_ui, largura_texto_max)
            y_linha = y_item + 35
            for linha in linhas:
                txt_linha = fonte_ui.render(linha, True, (200, 200, 200))
                tela.blit(txt_linha, (x_texto, y_linha))
                y_linha += 22

            # O próximo item desce o suficiente para caber a imagem e o espaçamento
            y_item += altura_imagem + 40 

        # Atualiza o limite máximo de scroll para esta aba
        altura_total_renderizada = (y_item + self.scroll_y) - y_conteudo
        self.max_scroll = max(0, altura_total_renderizada - altura_conteudo)

        tela.set_clip(None) # Libera o corte da tela

        # =========================================================
        # SCROLLBAR (Barra de Rolagem Direita)
        # =========================================================
        if self.max_scroll > 0:
            x_bar = cx + largura_modal - 15
            tamanho_alca = max(40, altura_conteudo * (altura_conteudo / (altura_conteudo + self.max_scroll)))
            y_alca = y_conteudo + (self.scroll_y / self.max_scroll) * (altura_conteudo - tamanho_alca)
            
            pygame.draw.rect(tela, (50, 50, 50), (x_bar, y_conteudo, 8, altura_conteudo), border_radius=4)
            pygame.draw.rect(tela, self.CINZA, (x_bar, y_alca, 8, tamanho_alca), border_radius=4)

        # =========================================================
        # BOTÃO FECHAR
        # =========================================================
        self.rect_fechar = pygame.Rect(cx + largura_modal - 140, cy + 20, 120, 30)
        pygame.draw.rect(tela, (200, 50, 50), self.rect_fechar, border_radius=5)
        txt_fechar = fonte_ui.render("Fechar X", True, self.BRANCO)
        tela.blit(txt_fechar, (self.rect_fechar.centerx - txt_fechar.get_width()//2, self.rect_fechar.centery - txt_fechar.get_height()//2))