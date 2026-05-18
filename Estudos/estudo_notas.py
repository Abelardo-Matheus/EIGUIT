# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# =============================================================================

import pygame
import random
import math
import Modulos.escalas as escalas
from constantes_ui import lista_afinacoes

class AcerteANota:
    def __init__(self):
        # Controles Gerais
        self.modo_jogo = "adivinhar" # Pode ser "adivinhar" ou "mapear"
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

        # Áreas de Clique (Geometria Dinâmica)
        self.rect_btn_menos = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_mais = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_adivinhar = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_mapear = pygame.Rect(0, 0, 0, 0)
        
        self.x_braco = 0
        self.y_braco = 0
        self.largura_braco = 0
        self.altura_braco = 0
        self.espaco_casas = 0
        self.espaco_cordas = 0
        self.num_cordas = 6

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
            
            # Varre todo o braço visível para encontrar todas as ocorrências da nota sorteada
            for c in range(self.num_cordas):
                nota_aberta = notas_abertas[c if instrumento != 'baixo' else c + 2]
                for casa in range(1, self.casas_estudo + 1):
                    n_calc = escalas.obter_nota(nota_aberta, casa)
                    # Equivalência harmônica para evitar injustiças
                    if n_calc == self.nota_alvo_mapear or (self.nota_alvo_mapear == 'C#' and n_calc == 'Db') or (self.nota_alvo_mapear == 'Db' and n_calc == 'C#'):
                        self.posicoes_corretas.add((c, casa))

        self.inicializado = True

    def desenhar(self, tela, estado, fontes, meio_x, meio_y, cam_x, cam_y):
        if not self.inicializado:
            self.inicializar_questao(estado)

        # =====================================================================
        # 1. SELETOR DE MODOS DE JOGO (Topo)
        # =====================================================================
        self.rect_btn_adivinhar = pygame.Rect(meio_x - 130, cam_y + 90, 120, 35)
        self.rect_btn_mapear = pygame.Rect(meio_x + 10, cam_y + 90, 120, 35)

        cor_adiv = (0, 160, 255) if self.modo_jogo == "adivinhar" else (60, 60, 60)
        cor_map = (0, 160, 255) if self.modo_jogo == "mapear" else (60, 60, 60)

        pygame.draw.rect(tela, cor_adiv, self.rect_btn_adivinhar, border_radius=5)
        pygame.draw.rect(tela, cor_map, self.rect_btn_mapear, border_radius=5)

        txt_adiv = fontes['pequena'].render("Modo Adivinhar", True, (255, 255, 255))
        txt_map = fontes['pequena'].render("Modo Mapear", True, (255, 255, 255))

        tela.blit(txt_adiv, (self.rect_btn_adivinhar.centerx - txt_adiv.get_width()//2, self.rect_btn_adivinhar.centery - txt_adiv.get_height()//2))
        tela.blit(txt_map, (self.rect_btn_mapear.centerx - txt_map.get_width()//2, self.rect_btn_mapear.centery - txt_map.get_height()//2))

        # =====================================================================
        # 2. DESENHO DO BRAÇO CEGO (Tamanho dinâmico)
        # =====================================================================
        self.largura_braco = max(1200, min(1000, 40 * self.casas_estudo)) 
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
                x_centro = x_traste - (self.espaco_casas / 2)
                
                # INLAYS (Bolinhas de Marcação)
                if casa in [3, 5, 7, 9, 15, 17, 19, 21]:
                    pygame.draw.circle(tela, (130, 130, 130), (int(x_centro), int(self.y_braco + self.altura_braco / 2)), 6)
                elif casa in [12, 24]:
                    pygame.draw.circle(tela, (130, 130, 130), (int(x_centro), int(self.y_braco + self.altura_braco / 3)), 6)
                    pygame.draw.circle(tela, (130, 130, 130), (int(x_centro), int(self.y_braco + self.altura_braco * 2 / 3)), 6)

                txt_c = fontes['pequena'].render(str(casa), True, (150, 150, 150))
                tela.blit(txt_c, (x_centro - txt_c.get_width()//2, self.y_braco + self.altura_braco + 8))

        for i in range(self.num_cordas):
            y_corda = self.y_braco + self.altura_braco - (i * self.espaco_cordas)
            pygame.draw.line(tela, (220, 220, 220), (self.x_braco, y_corda), (self.x_braco + self.largura_braco, y_corda), 1 + (i // 3))

        # =====================================================================
        # 3. LÓGICA VISUAL DOS MODOS DE JOGO
        # =====================================================================
        y_botoes = meio_y + 130

        if self.modo_jogo == "adivinhar":
            # DESTACA A NOTA ALVO (Bolinha Piscante)
            x_alvo = self.x_braco + (self.casa_alvo * self.espaco_casas) - (self.espaco_casas / 2)
            y_alvo = self.y_braco + self.altura_braco - (self.corda_alvo * self.espaco_cordas)

            raio_pulso = 16 + int(math.sin(pygame.time.get_ticks() * 0.01) * 3)
            s_pulso = pygame.Surface((raio_pulso*2, raio_pulso*2), pygame.SRCALPHA)
            pygame.draw.circle(s_pulso, (0, 160, 255, 80), (raio_pulso, raio_pulso), raio_pulso)
            tela.blit(s_pulso, (int(x_alvo - raio_pulso), int(y_alvo - raio_pulso)))

            pygame.draw.circle(tela, (0, 120, 215), (int(x_alvo), int(y_alvo)), 14)
            pygame.draw.circle(tela, (255, 255, 255), (int(x_alvo), int(y_alvo)), 14, width=2)

            # DESENHA OS 12 BOTÕES DE ESCOLHA
            notas_botoes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            self.rects_notas.clear()
            largura_btn = 65
            x_botoes_start = meio_x - ((12 * largura_btn) + (11 * 10)) // 2

            for idx, nota in enumerate(notas_botoes):
                x_btn = x_botoes_start + (idx * (largura_btn + 10))
                rect_btn = pygame.Rect(x_btn, y_botoes, largura_btn, 45)
                self.rects_notas[nota] = rect_btn

                cor_base = (40, 40, 45) if '#' in nota else (60, 60, 65)
                pygame.draw.rect(tela, cor_base, rect_btn, border_radius=6)
                pygame.draw.rect(tela, (120, 120, 130), rect_btn, width=1, border_radius=6)

                txt_n = fontes['ui'].render(nota, True, (255, 255, 255))
                tela.blit(txt_n, (rect_btn.centerx - txt_n.get_width()//2, rect_btn.centery - txt_n.get_height()//2))

        elif self.modo_jogo == "mapear":
            # PINTA AS BOLINHAS JÁ ENCONTRADAS (Verdes)
            for (corda, casa) in self.posicoes_encontradas:
                x_enc = self.x_braco + (casa * self.espaco_casas) - (self.espaco_casas / 2)
                y_enc = self.y_braco + self.altura_braco - (corda * self.espaco_cordas)
                pygame.draw.circle(tela, (50, 220, 50), (int(x_enc), int(y_enc)), 14)
                pygame.draw.circle(tela, (255, 255, 255), (int(x_enc), int(y_enc)), 14, width=2)

            # DESENHA O QUADRADO GIGANTE DA NOTA ALVO EMBAIXO
            rect_alvo = pygame.Rect(meio_x - 50, y_botoes, 100, 100)
            pygame.draw.rect(tela, (0, 120, 215), rect_alvo, border_radius=10)
            pygame.draw.rect(tela, (255, 255, 255), rect_alvo, width=3, border_radius=10)
            
            # Use a fonte UI mas com escala maior se possível, ou usa a titulo
            txt_gigante = fontes['titulo'].render(self.nota_alvo_mapear, True, (255, 255, 255))
            # Gambiarra rápida para texto gigante: renderizar titulo e dar scale (ou só centralizar a titulo)
            tela.blit(txt_gigante, (rect_alvo.centerx - txt_gigante.get_width()//2, rect_alvo.centery - txt_gigante.get_height()//2))

            # Texto de Progresso
            progresso = f"Faltam: {len(self.posicoes_corretas) - len(self.posicoes_encontradas)}"
            txt_prog = fontes['pequena'].render(progresso, True, (200, 200, 200))
            tela.blit(txt_prog, (meio_x - txt_prog.get_width()//2, y_botoes + 115))

        # =====================================================================
        # 4. PLACAR E CONTROLE DE CASAS E FEEDBACK
        # =====================================================================
        txt_placar = fontes['ui'].render(f"Rodadas Vencidas: {self.acertos}", True, (200, 200, 200))
        tela.blit(txt_placar, (meio_x - txt_placar.get_width()//2, self.y_braco - 40))

        # Botões de Controle de Casas (Canto superior direito)
        x_controles = cam_x + getattr(estado, 'LARGURA_TELA', 1280) - 200
        y_controles = cam_y + 20
        
        txt_casas_info = fontes['pequena'].render(f"Treinando em {self.casas_estudo} casas", True, (150, 150, 150))
        tela.blit(txt_casas_info, (x_controles, y_controles))

        self.rect_btn_menos = pygame.Rect(x_controles, y_controles + 25, 35, 30)
        self.rect_btn_mais = pygame.Rect(x_controles + 125, y_controles + 25, 35, 30)
        
        pygame.draw.rect(tela, (0, 120, 215), self.rect_btn_menos, border_radius=4)
        tela.blit(fontes['titulo'].render("-", True, (255, 255, 255)), (self.rect_btn_menos.centerx - 5, self.rect_btn_menos.centery - 12))
        
        pygame.draw.rect(tela, (0, 120, 215), self.rect_btn_mais, border_radius=4)
        tela.blit(fontes['titulo'].render("+", True, (255, 255, 255)), (self.rect_btn_mais.centerx - 7, self.rect_btn_mais.centery - 12))

        # Feedback
        if self.feedback and pygame.time.get_ticks() < self.tempo_feedback:
            txt_feed = fontes['titulo'].render(self.feedback, True, self.cor_feedback)
            tela.blit(txt_feed, (meio_x - txt_feed.get_width()//2, self.y_braco + self.altura_braco + 40))
        else:
            self.feedback = ""

    def tratar_cliques(self, pos_mouse_virtual, estado):
        """Nova função para interceptar os cliques no painel e na guitarra"""
        
        # 1. Troca de Modos
        if self.rect_btn_adivinhar.collidepoint(pos_mouse_virtual) and self.modo_jogo != "adivinhar":
            self.modo_jogo = "adivinhar"
            self.acertos = 0
            self.inicializar_questao(estado)
            return True
            
        if self.rect_btn_mapear.collidepoint(pos_mouse_virtual) and self.modo_jogo != "mapear":
            self.modo_jogo = "mapear"
            self.acertos = 0
            self.inicializar_questao(estado)
            return True

        # 2. Controles do Tamanho do Braço
        if self.rect_btn_menos.collidepoint(pos_mouse_virtual) and self.casas_estudo > 5:
            self.casas_estudo -= 1
            self.inicializar_questao(estado) 
            return True
        if self.rect_btn_mais.collidepoint(pos_mouse_virtual) and self.casas_estudo < 24:
            self.casas_estudo += 1
            self.inicializar_questao(estado)
            return True

        # =====================================================================
        # 3. INTERAÇÕES DE JOGO 
        # =====================================================================
        if self.modo_jogo == "adivinhar":
            # VERIFICA O CLIQUE NOS 12 BOTÕES DE NOTA
            for nota, rect_btn in self.rects_notas.items():
                if rect_btn.collidepoint(pos_mouse_virtual):
                    self.verificar_resposta(nota, estado)
                    return True

        elif self.modo_jogo == "mapear":
            # Verifica se o clique foi DENTRO da área do braço da guitarra
            rect_braco = pygame.Rect(self.x_braco, self.y_braco, self.largura_braco, self.altura_braco)
            if rect_braco.collidepoint(pos_mouse_virtual):
                
                # CÁLCULO MATEMÁTICO: Descobre onde o cara clicou!
                rel_x = pos_mouse_virtual[0] - self.x_braco
                casa_clicada = int(rel_x / self.espaco_casas) + 1
                if casa_clicada > self.casas_estudo: casa_clicada = self.casas_estudo

                rel_y = pos_mouse_virtual[1] - self.y_braco
                dist_do_chao = self.altura_braco - rel_y
                corda_clicada = round(dist_do_chao / self.espaco_cordas)

                if 0 <= corda_clicada < self.num_cordas and 1 <= casa_clicada <= self.casas_estudo:
                    self.verificar_clique_mapeamento(corda_clicada, casa_clicada, estado)
                    return True

        return False
    
    def verificar_resposta(self, nota_clicada, estado):
        """Usado APENAS no Modo Adivinhar"""
        self.total += 1
        if nota_clicada == self.nota_correta or (self.nota_correta == "Db" and nota_clicada == "C#"):
            self.feedback = "Acertou! Perfeito."
            self.cor_feedback = (100, 255, 100)
            self.acertos += 1
        else:
            self.feedback = f"Errado! Era a nota {self.nota_correta}"
            self.cor_feedback = (255, 100, 100)

        self.tempo_feedback = pygame.time.get_ticks() + 1500
        self.inicializar_questao(estado)

    def verificar_clique_mapeamento(self, corda, casa, estado):
        """Usado APENAS no Modo Mapear"""
        if (corda, casa) in self.posicoes_corretas:
            # Acertou a nota!
            if (corda, casa) not in self.posicoes_encontradas:
                self.posicoes_encontradas.add((corda, casa))
                
                # Se achou todas as notas daquele braço, ele ganha a rodada!
                if len(self.posicoes_encontradas) == len(self.posicoes_corretas):
                    self.feedback = "Excelente! Mapeamento concluído."
                    self.cor_feedback = (100, 255, 100)
                    self.acertos += 1
                    self.tempo_feedback = pygame.time.get_ticks() + 1500
                    self.inicializar_questao(estado)
        else:
            # Clicou em uma casa errada. Calcula qual nota ele tocou para dar a bronca:
            try: notas_abertas = lista_afinacoes[estado.indice_afinacao]["notas"]
            except: notas_abertas = ['E', 'A', 'D', 'G', 'B', 'E', 'B']
            instrumento = getattr(estado, 'instrumento', 'guitarra')
            nota_aberta = notas_abertas[corda if instrumento != 'baixo' else corda + 2]
            nota_errada = escalas.obter_nota(nota_aberta, casa)

            self.feedback = f"Ops! Você tocou um {nota_errada}."
            self.cor_feedback = (255, 100, 100)
            self.tempo_feedback = pygame.time.get_ticks() + 1500