# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================

import pygame
import os
import sys 

class Metronomo:
    def __init__(self, x_painel, y_painel):
        self.x = x_painel
        self.y = y_painel
        
        # Estados Principais
        self.bpm = 100
        self.ativado = True  
        self.tocando = False
        self.compasso = 4    
        self.tempo_atual = 0 
        
        self.ultimo_tick = 0
        self.foco_input = False 
        self.bpm_texto = str(self.bpm)
        
        # Cores e Visual
        self.BRANCO = (255, 255, 255)
        self.CINZA = (100, 100, 100)
        self.FUNDO_INPUT = (60, 60, 60)
        
        # Paleta de cores para o usuário escolher clicando
        self.paleta_cores = [
            (255, 50, 50),   # Vermelho
            (50, 255, 50),   # Verde
            (50, 150, 255),  # Azul
            (255, 255, 50),  # Amarelo
            (255, 150, 50),  # Laranja
            (200, 50, 255)   # Roxo
        ]
        
        # Cor padrão: Batida 1 é Vermelha (índice 0), resto é Verde (índice 1)
        # Suporta até 8 batidas no compasso
        self.indices_cores = [0] + [1] * 7 
        
        # --- Definição de Retângulos Estáticos (Configurações) ---
        self.rect_checkbox = pygame.Rect(self.x, self.y, 25, 25)
        self.btn_mais_batida = pygame.Rect(self.x + 100, self.y + 40, 30, 30)
        self.btn_menos_batida = pygame.Rect(self.x + 140, self.y + 40, 30, 30)
        self.rects_cores_config = [] # Preenchido no momento de desenhar
        
        # --- Definição de Retângulos Dinâmicos (Mini-Metrônomo) ---
        # Eles iniciam em 0, mas se atualizam sozinhos buscando o tamanho da tela
        self.slider_largura = 120
        self.btn_play = pygame.Rect(0, 0, 55, 30)
        self.rect_slider_barra = pygame.Rect(0, 0, self.slider_largura, 10)
        self.rect_cursor = pygame.Rect(0, 0, 15, 20)
        self.rect_input = pygame.Rect(0, 0, 50, 30)
        self.arrastando_slider = False

        # --- ÁUDIO À PROVA DE PYINSTALLER ---
        try:
                # --- CAMINHO COMPATÍVEL COM --ONEFILE ---
            if getattr(sys, 'frozen', False):
                # Se for o .exe (inclusive no modo --onefile)
                # O PyInstaller extrai os arquivos para sys._MEIPASS
                pasta_raiz = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            else:
                # Se for rodando via Python
                pasta_modulos = os.path.dirname(os.path.abspath(__file__))
                pasta_raiz = os.path.dirname(pasta_modulos)

            caminho_tick = os.path.join(pasta_raiz, "tick.wav")
            caminho_tick_high = os.path.join(pasta_raiz, "tick_high.wav")
            
            # Carrega
            self.som_acento = pygame.mixer.Sound(caminho_tick_high) 
            self.som_tick = pygame.mixer.Sound(caminho_tick)
            
        except Exception as e:
            print(f"❌ ERRO CRÍTICO DE ÁUDIO: {e}")
            self.som_tick = None
            self.som_acento = None

    def tocar_som(self):
        """Força o metrônomo a tocar um bip e piscar a bolinha visual (Usado pelo Maestro da IA)"""
        self.ultimo_tick = pygame.time.get_ticks()
        
        # Toca o som (com ou sem acento dependendo do tempo do compasso)
        if self.som_tick:
            if self.tempo_atual == 0 and self.som_acento:
                self.som_acento.play()
            else:
                self.som_tick.play()
                
        # Avança a bolinha visual para a próxima batida
        self.tempo_atual = (self.tempo_atual + 1) % self.compasso
        
    def atualizar_ancoras_ui(self):
        """Atualiza a posição dos controles do mini-metrônomo para o canto da tela"""
        tela = pygame.display.get_surface()
        if tela:
            largura, altura = tela.get_size()
            margem_x = largura - 250
            margem_y = altura - 50
            
            self.btn_play.topleft = (margem_x, margem_y)
            self.rect_slider_barra.topleft = (margem_x + 60, margem_y + 10)
            self.rect_cursor.y = margem_y + 5
            self.rect_input.topleft = (margem_x + 190, margem_y)

    def tratar_clique(self, pos_mouse, aba_config_aberta=False):
        
        # --- SÓ FUNCIONA SE ESTIVER NA ABA DE CONFIGURAÇÕES ---
        if aba_config_aberta:
            # 1. Toggle Ativar/Desativar
            if self.rect_checkbox.collidepoint(pos_mouse):
                self.ativado = not self.ativado
                return True

            # 2. Compasso
            if self.btn_mais_batida.collidepoint(pos_mouse):
                self.compasso = min(8, self.compasso + 1)
                return True
            if self.btn_menos_batida.collidepoint(pos_mouse):
                self.compasso = max(2, self.compasso - 1)
                return True

            # 3. Trocar Cor da Bolinha
            for i, rect in enumerate(self.rects_cores_config):
                if rect.collidepoint(pos_mouse) and i < self.compasso:
                    self.indices_cores[i] = (self.indices_cores[i] + 1) % len(self.paleta_cores)
                    return True

        # --- FUNCIONA EM QUALQUER LUGAR (MINI-METRÔNOMO) ---
        if self.ativado:
            # 4. Play/Pause
            if self.btn_play.collidepoint(pos_mouse):
                self.tocando = not self.tocando
                if self.tocando:
                    self.ultimo_tick = pygame.time.get_ticks()
                    self.tempo_atual = 0 
                    
                    # Toca a primeira nota imediatamente e no volume máximo!
                    if self.som_tick:
                        if self.som_acento:
                            self.som_acento.play()
                        else:
                            self.som_tick.play()
                return True

            # 5. Foco no Input de Texto
            if self.rect_input.collidepoint(pos_mouse):
                self.foco_input = True
                self.bpm_texto = "" 
                return True
            else:
                self.foco_input = False

            # 6. Iniciar Arraste do Slider
            if self.rect_cursor.collidepoint(pos_mouse) or self.rect_slider_barra.collidepoint(pos_mouse):
                self.arrastando_slider = True
                return True

        return False

    def tratar_teclado(self, evento):
        # Se o usuário estiver focado no campo de texto digitando o BPM
        if self.foco_input:
            if evento.key == pygame.K_RETURN:
                self.foco_input = False
                try:
                    novo_bpm = int(self.bpm_texto)
                    self.bpm = max(40, min(260, novo_bpm))
                except: pass
                self.bpm_texto = str(self.bpm)
            elif evento.key == pygame.K_BACKSPACE:
                self.bpm_texto = self.bpm_texto[:-1]
            else:
                if evento.unicode.isdigit() and len(self.bpm_texto) < 3:
                    self.bpm_texto += evento.unicode
        
        # --- NOVO: SE NÃO ESTIVER DIGITANDO, ESCUTA A BARRA DE ESPAÇO ---
        else:
            if evento.key == pygame.K_SPACE and self.ativado:
                self.tocando = not self.tocando
                if self.tocando:
                    self.ultimo_tick = pygame.time.get_ticks()
                    self.tempo_atual = 0 
                    
                    # Toca a primeira nota imediatamente
                    if self.som_tick:
                        if self.som_acento:
                            self.som_acento.play()
                        else:
                            self.som_tick.play()

    def processar_logica(self, pos_mouse):
        self.atualizar_ancoras_ui()

        # Lógica do Slider
        if self.arrastando_slider:
            if not pygame.mouse.get_pressed()[0]:
                self.arrastando_slider = False
            else:
                rel_x = max(0, min(self.slider_largura, pos_mouse[0] - self.rect_slider_barra.x))
                porcentagem = rel_x / self.slider_largura
                self.bpm = int(40 + (porcentagem * (260 - 40)))
                self.bpm_texto = str(self.bpm)

        # Lógica do Tempo (Ticks)
        if self.ativado and self.tocando:
            tempo_ms = pygame.time.get_ticks()
            intervalo = 60000 / self.bpm
            if tempo_ms - self.ultimo_tick >= intervalo:
                self.ultimo_tick = tempo_ms
                self.tempo_atual = (self.tempo_atual + 1) % self.compasso
                
                if self.som_tick:
                    if self.tempo_atual == 0 and self.som_acento:
                        self.som_acento.play()
                    else:
                        self.som_tick.play()

    # Altere a assinatura para receber scroll_y
    def desenhar_config(self, tela, fonte_ui, scroll_y=0):
        """Desenha APENAS configurações estáticas na aba"""
        
        # 1. Aplica o scroll no Y base
        y_rolado = self.y - scroll_y
        
        # Checkbox (Atualizando a posição do Rect com o novo Y)
        self.rect_checkbox.y = y_rolado
        pygame.draw.rect(tela, self.CINZA, self.rect_checkbox, 2)
        if self.ativado:
            cor_ativa = self.paleta_cores[1] 
            pygame.draw.line(tela, cor_ativa, (self.x+5, y_rolado+12), (self.x+10, y_rolado+20), 3)
            pygame.draw.line(tela, cor_ativa, (self.x+10, y_rolado+20), (self.x+20, y_rolado+5), 3)
        tela.blit(fonte_ui.render("Ativar Metrônomo", True, self.BRANCO), (self.x + 35, y_rolado))

        # Compasso
        y_compasso = y_rolado + 45
        tela.blit(fonte_ui.render(f"Batidas: {self.compasso}", True, self.BRANCO), (self.x, y_compasso))
        
        # Atualiza o Y dos botões
        self.btn_mais_batida.y = y_rolado + 40
        self.btn_menos_batida.y = y_rolado + 40
        
        pygame.draw.rect(tela, (50, 50, 50), self.btn_mais_batida)
        pygame.draw.rect(tela, (50, 50, 50), self.btn_menos_batida)
        tela.blit(fonte_ui.render("+", True, self.BRANCO), (self.btn_mais_batida.x+8, self.btn_mais_batida.y+2))
        tela.blit(fonte_ui.render("-", True, self.BRANCO), (self.btn_menos_batida.x+10, self.btn_menos_batida.y+2))

        # Seleção de Cores das Bolinhas
        y_cores = y_rolado + 100
        tela.blit(fonte_ui.render("Cores (Clique para mudar):", True, self.BRANCO), (self.x, y_cores))
        
        self.rects_cores_config.clear()
        for i in range(self.compasso):
            cx = self.x + 250 + (i * 30)
            cy = y_cores + 10
            cor_atual = self.paleta_cores[self.indices_cores[i]]
            
            pygame.draw.circle(tela, cor_atual, (cx, cy), 12)
            pygame.draw.circle(tela, self.BRANCO, (cx, cy), 12, 2)
            
            # Salva o rect para a colisão no tratar_clique (Já com o Y rolado!)
            self.rects_cores_config.append(pygame.Rect(cx-12, cy-12, 24, 24))

    def desenhar_mini_metronomo(self, tela, largura_tela, altura_tela, fonte_ui):
        """Desenha o metrônomo funcional no canto da tela com Play, Slider e Animação"""
        if not self.ativado: return

        # --- LINHA DE CIMA: AS BOLINHAS ANIMADAS ---
        margem = 30
        raio_base = 12
        espacamento = 40
        x_inicio = largura_tela - (self.compasso * espacamento) - margem
        y_bolinhas = altura_tela - 90

        tempo_decorrido = pygame.time.get_ticks() - self.ultimo_tick

        for i in range(self.compasso):
            cor_escolhida = self.paleta_cores[self.indices_cores[i]]
            cx = x_inicio + (i * espacamento)
            
            # Lógica de Animação (Cresce e murcha)
            raio_atual = raio_base
            if i == self.tempo_atual and self.tocando:
                # O raio ganha um bônus que diminui de 8 até 0 ao longo de 200ms
                bonus = max(0, 8 - (tempo_decorrido / 25))
                raio_atual += bonus
                pygame.draw.circle(tela, cor_escolhida, (int(cx), y_bolinhas), int(raio_atual))
            else:
                # Se não for o tempo atual, fica escurecido
                cor_escura = (max(0, cor_escolhida[0]-150), max(0, cor_escolhida[1]-150), max(0, cor_escolhida[2]-150))
                pygame.draw.circle(tela, cor_escura, (int(cx), y_bolinhas), raio_atual)

            pygame.draw.circle(tela, (200, 200, 200), (int(cx), y_bolinhas), int(raio_atual), 2)

        # --- LINHA DE BAIXO: CONTROLES ---
        # Botão Play
        cor_play = (200, 50, 50) if self.tocando else (50, 200, 50)
        pygame.draw.rect(tela, cor_play, self.btn_play, border_radius=5)
        icone = "STOP" if self.tocando else "PLAY"
        txt_play = fonte_ui.render(icone, True, self.BRANCO)
        tela.blit(txt_play, (self.btn_play.centerx - txt_play.get_width()//2, self.btn_play.centery - txt_play.get_height()//2))

        # Slider
        pygame.draw.rect(tela, self.CINZA, self.rect_slider_barra)
        pos_x = self.rect_slider_barra.x + ((self.bpm - 40) / (260 - 40)) * self.slider_largura
        self.rect_cursor.x = pos_x - 7
        pygame.draw.rect(tela, self.BRANCO, self.rect_cursor)

        # Input Texto
        cor_borda = self.paleta_cores[1] if self.foco_input else self.CINZA
        pygame.draw.rect(tela, self.FUNDO_INPUT, self.rect_input)
        pygame.draw.rect(tela, cor_borda, self.rect_input, 2)
        txt_bpm = fonte_ui.render(self.bpm_texto, True, self.BRANCO)
        tela.blit(txt_bpm, (self.rect_input.x + 5, self.rect_input.y + 5))