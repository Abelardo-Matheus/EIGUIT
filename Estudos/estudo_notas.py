# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# =============================================================================

import pygame
import random
import math
import array
import os
import sys
import Modulos.escalas as escalas
from Core.constantes_ui import lista_afinacoes

class AcerteANota:
    def __init__(self):
        # Controles Gerais
        self.modo_jogo = "adivinhar" # "adivinhar", "mapear", "ouvir"
        self.casas_estudo = 12 
        self.acertos = 0
        self.total = 0
        self.feedback = ""
        self.cor_feedback = (255, 255, 255)
        self.tempo_feedback = 0
        self.inicializado = False

        # Variáveis do Modo "Adivinhar"
        self.corda_alvo = 0
        self.casa_alvo = 0
        self.nota_correta = ""
        self.rects_notas = {}

        # Variáveis do Modo "Mapear"
        self.nota_alvo_mapear = ""
        self.posicoes_corretas = set()
        self.posicoes_encontradas = set()

        # Variáveis do Modo "Ouvir" (Ear Training)
        self.timbre = "sintetizado" # "sintetizado" ou "piano"
        self.frequencias = {
            "C": 261.63, "C#": 277.18, "Db": 277.18, "D": 293.66, "D#": 311.13, 
            "Eb": 311.13, "E": 329.63, "F": 349.23, "F#": 369.99, "Gb": 369.99, 
            "G": 392.00, "G#": 415.30, "Ab": 415.30, "A": 440.00, "A#": 466.16, 
            "Bb": 466.16, "B": 493.88
        }
        self.sons_sintetizados = {}
        self.sons_piano = {}
        self.rect_btn_tocar = pygame.Rect(0, 0, 120, 120)
        self.rect_btn_timbre = pygame.Rect(0, 0, 150, 35)

        # Áreas de Clique (Geometria Dinâmica)
        self.rect_btn_menos = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_mais = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_adivinhar = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_mapear = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_ouvir = pygame.Rect(0, 0, 0, 0)

        self.x_braco = 0
        self.y_braco = 0
        self.largura_braco = 0
        self.altura_braco = 0
        self.espaco_casas = 0
        self.espaco_cordas = 0
        self.num_cordas = 6

        self._carregar_sons()

    def _carregar_sons(self):
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=1)

        notas = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        for n in notas:
            # Síntese Matemática (Python nativo)
            if n in self.frequencias:
                self.sons_sintetizados[n] = self._gerar_amostra(self.frequencias[n])

            # Piano (Busca na pasta Audios)
            try:
                # Ajusta caminho para raiz/Audios
                base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                caminho = os.path.join(base, "Audios", f"{n}.wav")
                if os.path.exists(caminho):
                    self.sons_piano[n] = pygame.mixer.Sound(caminho)
            except: pass

    def _gerar_amostra(self, freq, duracao=1.2):
        sample_rate = 44100
        n_samples = int(sample_rate * duracao)
        buf = array.array('h', [0] * n_samples)
        for i in range(n_samples):
            t = float(i) / sample_rate
            envelope = math.exp(-3.0 * t) # Fade out suave
            v = int(envelope * 16384 * math.sin(2.0 * math.pi * freq * t))
            buf[i] = v
        return pygame.mixer.Sound(buf)

    def inicializar_questao(self, estado):
        try: notas_abertas = lista_afinacoes[estado.indice_afinacao]["notas"]
        except: notas_abertas = ['E', 'A', 'D', 'G', 'B', 'E', 'B']

        instrumento = getattr(estado, 'instrumento', 'guitarra')
        self.num_cordas = 4 if instrumento == 'baixo' else estado.NUM_CORDAS
        notas_botoes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

        if self.modo_jogo == "adivinhar":
            self.corda_alvo = random.randint(0, self.num_cordas - 1)
            self.casa_alvo = random.randint(1, self.casas_estudo) 
            nota_aberta_atual = notas_abertas[self.corda_alvo if instrumento != 'baixo' else self.corda_alvo + 2]
            self.nota_correta = escalas.obter_nota(nota_aberta_atual, self.casa_alvo)

        elif self.modo_jogo == "mapear":
            self.nota_alvo_mapear = random.choice(notas_botoes)
            self.posicoes_corretas.clear()
            self.posicoes_encontradas.clear()
            for c in range(self.num_cordas):
                nota_aberta = notas_abertas[c if instrumento != 'baixo' else c + 2]
                for casa in range(1, self.casas_estudo + 1):
                    n_calc = escalas.obter_nota(nota_aberta, casa)
                    if n_calc == self.nota_alvo_mapear or (self.nota_alvo_mapear == 'C#' and n_calc == 'Db') or (self.nota_alvo_mapear == 'Db' and n_calc == 'C#'):
                        self.posicoes_corretas.add((c, casa))

        elif self.modo_jogo == "ouvir":
            self.nota_correta = random.choice(notas_botoes)
            self.tocar_nota_atual()

        self.inicializado = True

    def tocar_nota_atual(self):
        if self.modo_jogo == "ouvir":
            bib = self.sons_piano if self.timbre == "piano" and self.nota_correta in self.sons_piano else self.sons_sintetizados
            if self.nota_correta in bib:
                bib[self.nota_correta].play()

    def desenhar(self, tela, estado, fontes, meio_x, meio_y, cam_x, cam_y):
        if not self.inicializado:
            self.inicializar_questao(estado)

        # =====================================================================
        # 1. SELETOR DE MODOS DE JOGO (Topo)
        # =====================================================================
        largura_seletor = 400
        self.rect_btn_adivinhar = pygame.Rect(meio_x - 200, cam_y + 90, 125, 35)
        self.rect_btn_mapear = pygame.Rect(meio_x - 65, cam_y + 90, 125, 35)
        self.rect_btn_ouvir = pygame.Rect(meio_x + 70, cam_y + 90, 125, 35)

        for btn, modo, txt in [(self.rect_btn_adivinhar, "adivinhar", "Visual"), 
                               (self.rect_btn_mapear, "mapear", "Mapear"), 
                               (self.rect_btn_ouvir, "ouvir", "Ouvir (Som)")]:
            cor = (0, 160, 255) if self.modo_jogo == modo else (60, 60, 60)
            pygame.draw.rect(tela, cor, btn, border_radius=5)
            t_surf = fontes['pequena'].render(txt, True, (255, 255, 255))
            tela.blit(t_surf, (btn.centerx - t_surf.get_width()//2, btn.centery - t_surf.get_height()//2))

        # =====================================================================
        # 2. DESENHO DO BRAÇO OU ÁREA DE SOM
        # =====================================================================
        if self.modo_jogo != "ouvir":
            self.largura_braco = max(700, min(1000, 40 * self.casas_estudo)) 
            self.altura_braco = 300
            self.x_braco = meio_x - self.largura_braco // 2
            self.y_braco = meio_y - 250
            self.espaco_cordas = self.altura_braco / (self.num_cordas - 1) if self.num_cordas > 1 else self.altura_braco
            self.espaco_casas = self.largura_braco / self.casas_estudo

            pygame.draw.rect(tela, (45, 40, 45), (self.x_braco, self.y_braco, self.largura_braco, self.altura_braco), border_radius=4)
            for casa in range(self.casas_estudo + 1):
                x_traste = self.x_braco + (casa * self.espaco_casas)
                pygame.draw.line(tela, (160, 160, 160), (x_traste, self.y_braco), (x_traste, self.y_braco + self.altura_braco), 2)
                if casa > 0:
                    xc = x_traste - (self.espaco_casas / 2)
                    if casa in [3, 5, 7, 9, 12, 15, 17, 19, 21, 24]:
                        pygame.draw.circle(tela, (130, 130, 130), (int(xc), int(self.y_braco + self.altura_braco / 2)), 6)
                    txt_c = fontes['pequena'].render(str(casa), True, (150, 150, 150))
                    tela.blit(txt_c, (xc - txt_c.get_width()//2, self.y_braco + self.altura_braco + 8))
            for i in range(self.num_cordas):
                y_corda = self.y_braco + self.altura_braco - (i * self.espaco_cordas)
                pygame.draw.line(tela, (220, 220, 220), (self.x_braco, y_corda), (self.x_braco + self.largura_braco, y_corda), 1)

        # =====================================================================
        # 3. INTERFACE POR MODO
        # =====================================================================
        y_botoes = meio_y + 130
        notas_botoes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

        if self.modo_jogo == "adivinhar":
            x_alvo = self.x_braco + (self.casa_alvo * self.espaco_casas) - (self.espaco_casas / 2)
            y_alvo = self.y_braco + self.altura_braco - (self.corda_alvo * self.espaco_cordas)
            pygame.draw.circle(tela, (0, 120, 215), (int(x_alvo), int(y_alvo)), 14)
            pygame.draw.circle(tela, (255, 255, 255), (int(x_alvo), int(y_alvo)), 14, 2)

        elif self.modo_jogo == "mapear":
            for (corda, casa) in self.posicoes_encontradas:
                x_enc = self.x_braco + (casa * self.espaco_casas) - (self.espaco_casas / 2)
                y_enc = self.y_braco + self.altura_braco - (corda * self.espaco_cordas)
                pygame.draw.circle(tela, (50, 220, 50), (int(x_enc), int(y_enc)), 14)

            rect_alvo = pygame.Rect(meio_x - 50, y_botoes - 40, 100, 100)
            pygame.draw.rect(tela, (0, 120, 215), rect_alvo, border_radius=10)
            txt_g = fontes['titulo'].render(self.nota_alvo_mapear, True, (255, 255, 255))
            tela.blit(txt_g, (rect_alvo.centerx - txt_g.get_width()//2, rect_alvo.centery - txt_g.get_height()//2))

        elif self.modo_jogo == "ouvir":
            # Botão de Tocar Som
            self.rect_btn_tocar.center = (meio_x, meio_y - 100)
            pygame.draw.circle(tela, (0, 120, 215), self.rect_btn_tocar.center, 60)
            pygame.draw.circle(tela, (255, 255, 255), self.rect_btn_tocar.center, 60, 3)
            # Ícone Play
            cx, cy = self.rect_btn_tocar.center
            pygame.draw.polygon(tela, (255, 255, 255), [(cx-15, cy-20), (cx+25, cy), (cx-15, cy+20)])

            # Seletor de Timbre
            self.rect_btn_timbre.center = (meio_x, meio_y + 20)
            pygame.draw.rect(tela, (80, 80, 80), self.rect_btn_timbre, border_radius=5)
            txt_timb = fontes['pequena'].render(f"Timbre: {self.timbre.capitalize()}", True, (255, 255, 255))
            tela.blit(txt_timb, (self.rect_btn_timbre.centerx - txt_timb.get_width()//2, self.rect_btn_timbre.centery - txt_timb.get_height()//2))

        # BOTÕES DE RESPOSTA (Compartilhados entre Visual e Ouvir)
        if self.modo_jogo in ["adivinhar", "ouvir"]:
            self.rects_notas.clear()
            largura_btn = 65
            x_start = meio_x - ((12 * largura_btn) + (11 * 10)) // 2
            for idx, nota in enumerate(notas_botoes):
                rect = pygame.Rect(x_start + (idx * (largura_btn + 10)), y_botoes + 100, largura_btn, 45)
                self.rects_notas[nota] = rect
                pygame.draw.rect(tela, (60, 60, 65), rect, border_radius=6)
                t_n = fontes['ui'].render(nota, True, (255, 255, 255))
                tela.blit(t_n, (rect.centerx - t_n.get_width()//2, rect.centery - t_n.get_height()//2))

        # Feedback e Controle
        if self.feedback and pygame.time.get_ticks() < self.tempo_feedback:
            txt_f = fontes['titulo'].render(self.feedback, True, self.cor_feedback)
            tela.blit(txt_f, (meio_x - txt_f.get_width()//2, meio_y + 50))

    def tratar_cliques(self, pos, estado):
        if self.rect_btn_adivinhar.collidepoint(pos):
            self.modo_jogo = "adivinhar"; self.inicializar_questao(estado); return True
        if self.rect_btn_mapear.collidepoint(pos):
            self.modo_jogo = "mapear"; self.inicializar_questao(estado); return True
        if self.rect_btn_ouvir.collidepoint(pos):
            self.modo_jogo = "ouvir"; self.inicializar_questao(estado); return True

        if self.modo_jogo == "ouvir":
            if self.rect_btn_tocar.collidepoint(pos): self.tocar_nota_atual(); return True
            if self.rect_btn_timbre.collidepoint(pos):
                self.timbre = "piano" if self.timbre == "sintetizado" else "sintetizado"
                return True

        if self.modo_jogo in ["adivinhar", "ouvir"]:
            for nota, rect in self.rects_notas.items():
                if rect.collidepoint(pos):
                    self.verificar_resposta(nota, estado); return True

        elif self.modo_jogo == "mapear":
            rect_braco = pygame.Rect(self.x_braco, self.y_braco, self.largura_braco, self.altura_braco)
            if rect_braco.collidepoint(pos):
                rel_x = pos[0] - self.x_braco
                casa = int(rel_x / self.espaco_casas) + 1
                rel_y = pos[1] - self.y_braco
                corda = round((self.altura_braco - rel_y) / self.espaco_cordas)
                if 0 <= corda < self.num_cordas: self.verificar_clique_mapeamento(corda, casa, estado); return True

        return False

    def verificar_resposta(self, nota, estado):
        self.total += 1
        if nota == self.nota_correta or (self.nota_correta == "Db" and nota == "C#") or (self.nota_correta == "C#" and nota == "Db"):
            self.feedback = "Acertou!"; self.cor_feedback = (100, 255, 100); self.acertos += 1
        else: self.feedback = f"Errado! Era {self.nota_correta}"; self.cor_feedback = (255, 100, 100)
        self.tempo_feedback = pygame.time.get_ticks() + 1500
        self.inicializar_questao(estado)

    def verificar_clique_mapeamento(self, corda, casa, estado):
        if (corda, casa) in self.posicoes_corretas:
            if (corda, casa) not in self.posicoes_encontradas:
                self.posicoes_encontradas.add((corda, casa))
                if len(self.posicoes_encontradas) == len(self.posicoes_corretas):
                    self.feedback = "Excelente!"; self.cor_feedback = (100, 255, 100); self.acertos += 1
                    self.tempo_feedback = pygame.time.get_ticks() + 1500; self.inicializar_questao(estado)
        else:
            self.feedback = "Ops! Nota errada."; self.cor_feedback = (255, 100, 100)
            self.tempo_feedback = pygame.time.get_ticks() + 1500