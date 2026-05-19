# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# =============================================================================

import pygame
import random
import time
import math

class RhythmHero:
    def __init__(self):
        self.inicializado = False
        self.jogo_iniciado = False
        self.pontuacao = 0
        self.streak = 0
        self.bpm = 80
        self.subdivisao = 1 # 1=Semínima, 2=Colcheia, 3=Tercina, 4=Semicolcheia
        self.nomes_ritmos = {1: "Semínima", 2: "Colcheia", 3: "Tercina", 4: "Semicolcheia"}
        
        self.ultima_batida = 0
        self.proxima_batida = 0
        
        self.notas_caindo = [] 
        self.tempo_inicio = 0
        
        # Geometria
        self.largura_pista = 250
        self.y_linha_hit = 0
        
        # Botões Interface
        self.btn_start = pygame.Rect(0, 0, 300, 60)
        self.btn_menos_bpm = pygame.Rect(0, 0, 40, 40)
        self.btn_mais_bpm = pygame.Rect(0, 0, 40, 40)
        self.btn_menos_ritmo = pygame.Rect(0, 0, 40, 40)
        self.btn_mais_ritmo = pygame.Rect(0, 0, 40, 40)
        
        # Feedback
        self.feedback_msg = ""
        self.feedback_cor = (255, 255, 255)
        self.feedback_timer = 0

    def inicializar(self, largura, altura):
        self.y_linha_hit = altura - 150
        self.btn_start.center = (largura // 2, altura // 2 + 100)
        
        # Posicionamento dos seletores
        y_seletores = altura // 2 - 50
        self.btn_menos_bpm.topleft = (largura // 2 - 180, y_seletores)
        self.btn_mais_bpm.topleft = (largura // 2 - 60, y_seletores)
        
        self.btn_menos_ritmo.topleft = (largura // 2 + 60, y_seletores)
        self.btn_mais_ritmo.topleft = (largura // 2 + 180, y_seletores)
        
        self.inicializado = True

    def iniciar_jogo(self):
        self.jogo_iniciado = True
        self.pontuacao = 0
        self.streak = 0
        self.tempo_inicio = time.time()
        self.ultima_batida = self.tempo_inicio
        
        # Velocidade fixa para visualização
        velocidade = 400 
        tempo_queda = (self.y_linha_hit + 50) / velocidade
        
        # O intervalo entre notas agora depende da subdivisão
        # BPM 80 = 0.75s por batida. Se subdivisão=2, intervalo=0.375s
        intervalo_notas = (60.0 / self.bpm) / self.subdivisao
        self.proxima_batida = self.tempo_inicio + tempo_queda + intervalo_notas
        self.notas_caindo.clear()

    def atualizar(self, estado, meu_gravador, configs=None):
        if not self.jogo_iniciado: return
        
        agora = time.time()
        mult_vel = configs.get_vel_jogo() if configs else 1.0
        
        velocidade = 400 * mult_vel
        tempo_queda = (self.y_linha_hit + 50) / velocidade
        intervalo_notas = ((60.0 / self.bpm) / self.subdivisao) / mult_vel
        
        # Gerar nova nota antecipadamente
        if agora >= self.proxima_batida - tempo_queda:
            self.notas_caindo.append({
                "tempo_alvo": self.proxima_batida,
                "hit": False
            })
            self.proxima_batida += intervalo_notas

        # Mover notas
        for nota in self.notas_caindo:
            tempo_restante = nota["tempo_alvo"] - agora
            nota["y"] = self.y_linha_hit - (tempo_restante * velocidade)

        # Detectar batida (Usa a nota detectada pelo motor global ou volume)
        detectou_som = False
        if estado.nota_atual_detectada != "--":
            detectou_som = True
        elif meu_gravador and hasattr(meu_gravador, 'volume_atual'):
            # Se a nota falhar, usamos um volume residual bem baixo como backup
            if meu_gravador.volume_atual > 0.02: 
                detectou_som = True

        if detectou_som:
            for nota in self.notas_caindo:
                if not nota["hit"]:
                    distancia = abs(nota["y"] - self.y_linha_hit)
                    if distancia < 50: 
                        nota["hit"] = True
                        self.pontuacao += 10 + (self.streak // 5)
                        self.streak += 1
                        self.mostrar_feedback("BOA!", (100, 255, 100))
                        break

        # Remover notas passadas
        for nota in self.notas_caindo[:]:
            if nota["y"] > self.y_linha_hit + 60:
                if not nota["hit"]:
                    self.streak = 0
                    self.mostrar_feedback("ERROU!", (255, 50, 50))
                self.notas_caindo.remove(nota)

    def mostrar_feedback(self, msg, cor):
        self.feedback_msg = msg
        self.feedback_cor = cor
        self.feedback_timer = time.time() + 0.4

    def desenhar(self, tela, largura, altura, estado, meu_gravador=None, configs=None):
        if not self.inicializado:
            self.inicializar(largura, altura)
        
        self.atualizar(estado, meu_gravador, configs)
        
        tela.fill((15, 15, 25))
        
        x_pista = largura // 2 - self.largura_pista // 2
        pygame.draw.rect(tela, (25, 25, 35), (x_pista, 0, self.largura_pista, altura))
        pygame.draw.line(tela, (0, 160, 255), (x_pista, 0), (x_pista, altura), 2)
        pygame.draw.line(tela, (0, 160, 255), (x_pista + self.largura_pista, 0), (x_pista + self.largura_pista, altura), 2)
        pygame.draw.line(tela, (255, 255, 255), (x_pista, self.y_linha_hit), (x_pista + self.largura_pista, self.y_linha_hit), 4)
        
        f_tit = pygame.font.SysFont("Arial", 45, bold=True)
        f_ui = pygame.font.SysFont("Arial", 25, bold=True)
        f_p = pygame.font.SysFont("Arial", 18, bold=True)

        if not self.jogo_iniciado:
            # Menu Inicial com Configurações
            txt_t = f_tit.render("RHYTHM HERO", True, (255, 255, 255))
            tela.blit(txt_t, (largura//2 - txt_t.get_width()//2, altura//2 - 200))
            
            # --- Configuração BPM ---
            tela.blit(f_p.render("BPM (Andamento)", True, (150, 150, 150)), (self.btn_menos_bpm.x, self.btn_menos_bpm.y - 25))
            pygame.draw.rect(tela, (0, 120, 215), self.btn_menos_bpm, border_radius=5)
            pygame.draw.rect(tela, (0, 120, 215), self.btn_mais_bpm, border_radius=5)
            tela.blit(f_ui.render("-", True, (255, 255, 255)), (self.btn_menos_bpm.centerx - 5, self.btn_menos_bpm.centery - 15))
            tela.blit(f_ui.render("+", True, (255, 255, 255)), (self.btn_mais_bpm.centerx - 7, self.btn_mais_bpm.centery - 15))
            txt_bpm = f_ui.render(str(self.bpm), True, (255, 255, 255))
            tela.blit(txt_bpm, (self.btn_menos_bpm.right + 25, self.btn_menos_bpm.y + 5))

            # --- Configuração Ritmo ---
            tela.blit(f_p.render("Subdivisão", True, (150, 150, 150)), (self.btn_menos_ritmo.x, self.btn_menos_ritmo.y - 25))
            pygame.draw.rect(tela, (0, 120, 215), self.btn_menos_ritmo, border_radius=5)
            pygame.draw.rect(tela, (0, 120, 215), self.btn_mais_ritmo, border_radius=5)
            tela.blit(f_ui.render("<", True, (255, 255, 255)), (self.btn_menos_ritmo.centerx - 7, self.btn_menos_ritmo.centery - 15))
            tela.blit(f_ui.render(">", True, (255, 255, 255)), (self.btn_mais_ritmo.centerx - 7, self.btn_mais_ritmo.centery - 15))
            txt_rit = f_ui.render(self.nomes_ritmos[self.subdivisao], True, (255, 255, 255))
            tela.blit(txt_rit, (self.btn_menos_ritmo.right + 15, self.btn_menos_ritmo.y + 5))

            # Botão Iniciar
            pygame.draw.rect(tela, (0, 200, 100), self.btn_start, border_radius=12)
            txt_b = f_ui.render("INICIAR JOGO", True, (255, 255, 255))
            tela.blit(txt_b, (self.btn_start.centerx - txt_b.get_width()//2, self.btn_start.centery - txt_b.get_height()//2))
            
            txt_i = f_ui.render("Palhete sua guitarra no tempo das notas!", True, (150, 150, 150))
            tela.blit(txt_i, (largura//2 - txt_i.get_width()//2, self.btn_start.bottom + 40))
        else:
            # Notas e HUD
            for nota in self.notas_caindo:
                if not nota["hit"]:
                    pygame.draw.circle(tela, (0, 200, 255), (largura // 2, int(nota["y"])), 30)
                    pygame.draw.circle(tela, (255, 255, 255), (largura // 2, int(nota["y"])), 30, 3)

            f_hud = pygame.font.SysFont("Arial", 35, bold=True)
            tela.blit(f_hud.render(f"PONTOS: {self.pontuacao}", True, (255, 255, 255)), (50, 50))
            tela.blit(f_hud.render(f"STREAK: {self.streak}", True, (255, 255, 0)), (50, 100))
            tela.blit(f_ui.render(f"{self.bpm} BPM | {self.nomes_ritmos[self.subdivisao]}", True, (150, 150, 150)), (50, 150))
            
            if time.time() < self.feedback_timer:
                txt_f = f_hud.render(self.feedback_msg, True, self.feedback_cor)
                tela.blit(txt_f, (largura // 2 - txt_f.get_width() // 2, self.y_linha_hit - 120))

    def tratar_clique(self, pos, meu_gravador=None):
        if not self.jogo_iniciado:
            if self.btn_menos_bpm.collidepoint(pos):
                self.bpm = max(40, self.bpm - 5)
                return True
            if self.btn_mais_bpm.collidepoint(pos):
                self.bpm = min(240, self.bpm + 5)
                return True
            if self.btn_menos_ritmo.collidepoint(pos):
                self.subdivisao = max(1, self.subdivisao - 1)
                return True
            if self.btn_mais_ritmo.collidepoint(pos):
                self.subdivisao = min(4, self.subdivisao + 1)
                return True
            if self.btn_start.collidepoint(pos):
                self.iniciar_jogo()
                return True
        return False
