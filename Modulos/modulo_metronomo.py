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
        
        self.paleta_cores = [
            (255, 50, 50),   # Vermelho
            (50, 255, 50),   # Verde
            (50, 150, 255),  # Azul
            (255, 255, 50),  # Amarelo
            (255, 150, 50),  # Laranja
            (200, 50, 255)   # Roxo
        ]
        
        self.indices_cores = [0] + [1] * 7 
        
        # --- Definição de Retângulos ---
        self.slider_largura = 150 # Tamanho compacto para centralizar melhor
        self.btn_play = pygame.Rect(0, 0, 55, 30)
        self.rect_slider_barra = pygame.Rect(0, 0, self.slider_largura, 10)
        self.rect_cursor = pygame.Rect(0, 0, 15, 20)
        self.rect_input = pygame.Rect(0, 0, 50, 30)
        self.arrastando_slider = False

        self.rect_checkbox = pygame.Rect(self.x, self.y, 25, 25)
        self.btn_mais_batida = pygame.Rect(self.x + 100, self.y + 40, 30, 30)
        self.btn_menos_batida = pygame.Rect(self.x + 140, self.y + 40, 30, 30)
        self.rects_cores_config = []

        # --- ÁUDIO ---
        try:
            if getattr(sys, 'frozen', False):
                pasta_raiz = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            else:
                pasta_modulos = os.path.dirname(os.path.abspath(__file__))
                pasta_raiz = os.path.dirname(pasta_modulos)

            caminho_tick = os.path.join(pasta_raiz, "tick.wav")
            caminho_tick_high = os.path.join(pasta_raiz, "tick_high.wav")
            
            self.som_acento = pygame.mixer.Sound(caminho_tick_high) 
            self.som_tick = pygame.mixer.Sound(caminho_tick)
            
        except Exception as e:
            print(f"❌ ERRO ÁUDIO: {e}")
            self.som_tick = self.som_acento = None

    def tratar_clique(self, pos_mouse, estado, aba_config_aberta=False):
        if aba_config_aberta:
            if self.rect_checkbox.collidepoint(pos_mouse):
                self.ativado = not self.ativado
                return True
            if self.btn_mais_batida.collidepoint(pos_mouse):
                self.compasso = min(8, self.compasso + 1)
                return True
            if self.btn_menos_batida.collidepoint(pos_mouse):
                self.compasso = max(2, self.compasso - 1)
                return True
            for i, rect in enumerate(self.rects_cores_config):
                if rect.collidepoint(pos_mouse) and i < self.compasso:
                    self.indices_cores[i] = (self.indices_cores[i] + 1) % len(self.paleta_cores)
                    return True

        if self.ativado:
            # Sincroniza posições para detecção de clique centralizada
            dx = estado.dragger_metronomo.x
            dy = estado.dragger_metronomo.y
            largura_total_ui = 55 + 10 + self.slider_largura + 10 + 50
            x_start = dx + (estado.dragger_metronomo.largura - largura_total_ui) // 2
            y_ctrl = dy + 45
            
            self.btn_play.topleft = (x_start, y_ctrl)
            self.rect_slider_barra.topleft = (x_start + 65, y_ctrl + 10)
            self.rect_input.topleft = (x_start + 65 + self.slider_largura + 10, y_ctrl)

            if self.btn_play.collidepoint(pos_mouse):
                self.tocando = not self.tocando
                if self.tocando:
                    self.ultimo_tick, self.tempo_atual = pygame.time.get_ticks(), 0
                    if self.som_tick: (self.som_acento if self.som_acento else self.som_tick).play()
                return True

            if self.rect_input.collidepoint(pos_mouse):
                self.foco_input, self.bpm_texto = True, ""
                return True
            else: self.foco_input = False

            pos_x_cursor = self.rect_slider_barra.x + ((self.bpm - 40) / (300 - 40)) * self.slider_largura
            cursor_temp = pygame.Rect(pos_x_cursor - 7, y_ctrl + 5, 15, 20)
            if cursor_temp.collidepoint(pos_mouse) or self.rect_slider_barra.collidepoint(pos_mouse):
                self.arrastando_slider = True
                return True
        return False

    def tratar_teclado(self, evento):
        if self.foco_input:
            if evento.key == pygame.K_RETURN:
                self.foco_input = False
                try: self.bpm = max(40, min(300, int(self.bpm_texto)))
                except: pass
                self.bpm_texto = str(self.bpm)
            elif evento.key == pygame.K_BACKSPACE: self.bpm_texto = self.bpm_texto[:-1]
            elif evento.unicode.isdigit() and len(self.bpm_texto) < 3: self.bpm_texto += evento.unicode
        elif evento.key == pygame.K_SPACE and self.ativado:
            self.tocando = not self.tocando
            if self.tocando: 
                self.ultimo_tick, self.tempo_atual = pygame.time.get_ticks(), 0
                if self.som_tick: (self.som_acento if self.som_acento else self.som_tick).play()

    def processar_logica(self, pos_mouse, estado):
        if self.arrastando_slider:
            if not pygame.mouse.get_pressed()[0]: self.arrastando_slider = False
            else:
                dx = estado.dragger_metronomo.x
                largura_total_ui = 55 + 10 + self.slider_largura + 10 + 50
                x_barra = dx + (estado.dragger_metronomo.largura - largura_total_ui) // 2 + 65
                rel_x = max(0, min(self.slider_largura, pos_mouse[0] - x_barra))
                self.bpm = int(40 + ((rel_x / self.slider_largura) * (300 - 40)))
                self.bpm_texto = str(self.bpm)

        if self.ativado and self.tocando:
            tempo_ms = pygame.time.get_ticks()
            if tempo_ms - self.ultimo_tick >= (60000 / self.bpm):
                self.ultimo_tick = tempo_ms
                self.tempo_atual = (self.tempo_atual + 1) % self.compasso
                if self.som_tick: (self.som_acento if self.tempo_atual == 0 and self.som_acento else self.som_tick).play()

    def desenhar_config(self, tela, fonte_ui, scroll_y=0):
        y_rolado = self.y - scroll_y
        self.rect_checkbox.y = y_rolado
        pygame.draw.rect(tela, self.CINZA, self.rect_checkbox, 2)
        if self.ativado:
            pygame.draw.line(tela, self.paleta_cores[1], (self.x+5, y_rolado+12), (self.x+10, y_rolado+20), 3)
            pygame.draw.line(tela, self.paleta_cores[1], (self.x+10, y_rolado+20), (self.x+20, y_rolado+5), 3)
        tela.blit(fonte_ui.render("Ativar Metrônomo", True, self.BRANCO), (self.x + 35, y_rolado))
        
        y_compasso = y_rolado + 45
        self.btn_mais_batida.y = self.btn_menos_batida.y = y_rolado + 40
        pygame.draw.rect(tela, (50, 50, 50), self.btn_mais_batida)
        pygame.draw.rect(tela, (50, 50, 50), self.btn_menos_batida)
        tela.blit(fonte_ui.render(f"Batidas: {self.compasso}", True, self.BRANCO), (self.x, y_compasso))
        tela.blit(fonte_ui.render("+", True, self.BRANCO), (self.btn_mais_batida.x+8, self.btn_mais_batida.y+2))
        tela.blit(fonte_ui.render("-", True, self.BRANCO), (self.btn_menos_batida.x+10, self.btn_menos_batida.y+2))

        y_cores = y_rolado + 100
        tela.blit(fonte_ui.render("Cores (Clique):", True, self.BRANCO), (self.x, y_cores))
        self.rects_cores_config.clear()
        for i in range(self.compasso):
            cx, cy = self.x + 200 + (i * 35), y_cores + 12
            pygame.draw.circle(tela, self.paleta_cores[self.indices_cores[i]], (cx, cy), 12)
            pygame.draw.circle(tela, self.BRANCO, (cx, cy), 12, 2)
            self.rects_cores_config.append(pygame.Rect(cx-12, cy-12, 24, 24))

    def desenhar_mini_metronomo(self, tela, estado, fonte_ui):
        if not self.ativado: return
        dx, dy = estado.dragger_metronomo.x, estado.dragger_metronomo.y
        largura = estado.dragger_metronomo.largura
        
        # Centralização das bolinhas
        espacamento = 35
        x_inicio = dx + (largura // 2) - ((self.compasso - 1) * espacamento // 2)
        tempo_decorrido = pygame.time.get_ticks() - self.ultimo_tick

        for i in range(self.compasso):
            cor = self.paleta_cores[self.indices_cores[i]]
            cx, cy = x_inicio + (i * espacamento), dy + 15
            raio = 10 + (max(0, 6 - (tempo_decorrido / 30)) if i == self.tempo_atual and self.tocando else 0)
            if not (i == self.tempo_atual and self.tocando):
                cor = (max(0, cor[0]-150), max(0, cor[1]-150), max(0, cor[2]-150))
            pygame.draw.circle(tela, cor, (int(cx), int(cy)), int(raio))
            pygame.draw.circle(tela, (200, 200, 200), (int(cx), int(cy)), int(raio), 2)

        # Centralização dos Controles
        largura_total_ui = 55 + 10 + self.slider_largura + 10 + 50
        x_start = dx + (largura - largura_total_ui) // 2
        y_ctrl = dy + 45

        # Play
        pygame.draw.rect(tela, ((200,50,50) if self.tocando else (50,200,50)), (x_start, y_ctrl, 55, 30), border_radius=5)
        txt = fonte_ui.render("STOP" if self.tocando else "PLAY", True, self.BRANCO)
        tela.blit(txt, (x_start + 27 - txt.get_width()//2, y_ctrl + 15 - txt.get_height()//2))

        # Slider
        bar_rect = (x_start + 65, y_ctrl + 10, self.slider_largura, 10)
        pygame.draw.rect(tela, self.CINZA, bar_rect)
        cursor_x = bar_rect[0] + ((self.bpm - 40) / (300 - 40)) * self.slider_largura
        pygame.draw.rect(tela, self.BRANCO, (cursor_x - 7, y_ctrl + 5, 15, 20))

        # Input
        in_rect = (x_start + 65 + self.slider_largura + 10, y_ctrl, 50, 30)
        pygame.draw.rect(tela, self.FUNDO_INPUT, in_rect)
        pygame.draw.rect(tela, (self.paleta_cores[1] if self.foco_input else self.CINZA), in_rect, 2)
        txt_bpm = fonte_ui.render(self.bpm_texto, True, self.BRANCO)
        tela.blit(txt_bpm, (in_rect[0] + 5, in_rect[1] + 5))

        if estado.drag_ativado: estado.dragger_metronomo.desenhar_caixa_selecao(tela, margem=5)