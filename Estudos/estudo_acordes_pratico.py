# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# =============================================================================

import pygame
import random
from Core.constantes_ui import *
import Modulos.escalas as escalas
from Core.constantes_ui import lista_afinacoes

class EstudoAcordesPratico:
    def __init__(self):
        self.inicializado = False
        self.acertos = 0
        self.total = 0
        self.acorde_alvo = ""
        self.notas_alvo = []
        self.feedback = "Toque o acorde indicado..."
        self.cor_feedback = BRANCO
        self.tempo_feedback = 0
        self.acerto_detectado = False
        
        # Dados de acordes
        import Modulos.modulos_acordes as mod_acordes
        self.acordes_disponiveis = {
            "C Maior": {"notas": ["C", "E", "G"], "shape": mod_acordes.TRIADE_C_MAIOR},
            "A Maior": {"notas": ["A", "C#", "E"], "shape": mod_acordes.TRIADE_A_MAIOR},
            "G Maior": {"notas": ["G", "B", "D"], "shape": mod_acordes.TRIADE_G_MAIOR},
            "E Maior": {"notas": ["E", "G#", "B"], "shape": mod_acordes.TRIADE_E_MAIOR},
            "D Maior": {"notas": ["D", "F#", "A"], "shape": mod_acordes.TRIADE_D_MAIOR},
            "A Menor": {"notas": ["A", "C", "E"], "shape": mod_acordes.TRIADE_A_MENOR},
            "E Menor": {"notas": ["E", "G", "B"], "shape": mod_acordes.TRIADE_E_MENOR},
            "D Menor": {"notas": ["D", "F", "A"], "shape": [[0,0,1,0],[0,0,0,1],[1,0,0,0],[2,0,0,0],[0,0,1,0],[0,0,0,1],[0,0,1,0]]} # Dm simplificado
        }
        self.nomes_acordes = list(self.acordes_disponiveis.keys())

    def inicializar_questao(self, estado):
        self.acorde_alvo = random.choice(self.nomes_acordes)
        self.notas_alvo = self.acordes_disponiveis[self.acorde_alvo]["notas"]
        self.feedback = f"Toque {self.acorde_alvo}"
        self.cor_feedback = BRANCO
        self.acerto_detectado = False
        self.inicializado = True

    def desenhar(self, tela, estado, fontes, meio_x, meio_y, cam_x, cam_y):
        if not self.inicializado: self.inicializar_questao(estado)
        
        # Título e Feedback
        txt_tit = fontes['titulo'].render(f"Objetivo: Tocar o acorde {self.acorde_alvo}", True, (0, 160, 255))
        tela.blit(txt_tit, (meio_x - txt_tit.get_width()//2, cam_y + 100))
        
        cor_f = self.cor_feedback
        if self.acerto_detectado: cor_f = (100, 255, 100)
        txt_feed = fontes['titulo'].render(self.feedback, True, cor_f)
        tela.blit(txt_feed, (meio_x - txt_feed.get_width()//2, cam_y + 150))

        # Desenho do Shape do Acorde
        shape = self.acordes_disponiveis[self.acorde_alvo]["shape"]
        num_cordas = 7
        espaco_cordas = 35
        espaco_casas = 55
        altura_shape = (num_cordas - 1) * espaco_cordas
        largura_shape = 5 * espaco_casas
        
        x_shape = meio_x - largura_shape // 2
        y_shape = meio_y - 120
        
        # Madeira do braço (miniatura)
        pygame.draw.rect(tela, (60, 35, 25), (x_shape, y_shape, largura_shape, altura_shape), border_radius=5)
        
        # Trastes
        for i in range(6):
            lx = x_shape + (i * espaco_casas)
            pygame.draw.line(tela, (180, 180, 180), (lx, y_shape), (lx, y_shape + altura_shape), 2)
            
        # Cordas
        for i in range(num_cordas):
            ly = y_shape + (i * espaco_cordas)
            pygame.draw.line(tela, (200, 200, 200), (x_shape, ly), (x_shape + largura_shape, ly), 1)
            
            # Notas no shape
            if i < len(shape):
                for casa_idx, val in enumerate(shape[i]):
                    if val in [1, 2]:
                        bx = x_shape + (casa_idx * espaco_casas) + (espaco_casas // 2)
                        by = y_shape + altura_shape - (i * espaco_cordas)
                        cor_nota = (255, 100, 100) if val == 2 else BRANCO
                        pygame.draw.circle(tela, cor_nota, (int(bx), int(by)), 15)
                        pygame.draw.circle(tela, (0, 0, 0), (int(bx), int(by)), 15, 2)

        # Notas detectadas (Debug Visual)
        notas_atuais = getattr(estado, 'notas_detectadas_ia', [])
        if notas_atuais:
            txt_detect = fontes['pequena'].render(f"Detectado: {', '.join(notas_atuais)}", True, (200, 200, 200))
            tela.blit(txt_detect, (meio_x - txt_detect.get_width()//2, y_shape + altura_shape + 40))

        # Lógica de Verificação Automática (IA)
        if not self.acerto_detectado and notas_atuais:
            match_count = 0
            for n_alvo in self.notas_alvo:
                if any(escalas.equivalencia_notas(n_alvo, n_det) for n_det in notas_atuais):
                    match_count += 1
            
            # Se detectarmos pelo menos 2 das 3 notas (para ser mais tolerante com ruído)
            if match_count >= 2:
                self.acerto_detectado = True
                self.acertos += 1
                self.total += 1
                self.feedback = "MUITO BEM! Acorde detectado!"
                self.tempo_feedback = pygame.time.get_ticks() + 2000

        if self.acerto_detectado and pygame.time.get_ticks() > self.tempo_feedback:
            self.inicializar_questao(estado)

    def tratar_cliques(self, pos, estado):
        # Neste modo, o clique é apenas para pular caso o usuário queira
        return False
