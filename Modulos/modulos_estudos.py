# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# =============================================================================

import pygame
import random
from Core.constantes_ui import *
import Estudos.estudo_notas as estudo_notas
import Estudos.estudo_escalas as estudo_escalas
import Estudos.estudo_acordes_pratico as estudo_acordes_pratico

# =============================================================================
# MÓDULO DE ACORDES (ACERTE O ACORDE)
# =============================================================================
class EstudoAcordes:
    def __init__(self):
        self.inicializado = False
        self.acertos = 0
        self.total = 0
        self.acorde_alvo = ""
        self.opcoes = []
        self.rects_opcoes = []
        self.estado_resposta = None
        self.feedback = ""
        self.cor_feedback = BRANCO
        
        # Dados para sorteio
        self.lista_acordes = ["C Maior", "A Maior", "G Maior", "E Maior", "D Maior", 
                             "C Menor", "A Menor", "E Menor", "C7", "A7", "G7", "E7", "D7"]
        
        # Mapeamento para shapes
        import Modulos.modulos_acordes as mod_acordes
        self.shapes = {
            "C Maior": mod_acordes.TRIADE_C_MAIOR,
            "A Maior": mod_acordes.TRIADE_A_MAIOR,
            "G Maior": mod_acordes.TRIADE_G_MAIOR,
            "E Maior": mod_acordes.TRIADE_E_MAIOR,
            "D Maior": mod_acordes.TRIADE_D_MAIOR,
            "C Menor": mod_acordes.TRIADE_C_MENOR,
            "A Menor": mod_acordes.TRIADE_A_MENOR,
            "E Menor": mod_acordes.TRIADE_E_MENOR,
            "C7": mod_acordes.C7, "A7": mod_acordes.A7, "G7": mod_acordes.G7, "E7": mod_acordes.E7, "D7": mod_acordes.D7
        }

    def inicializar_questao(self):
        self.acorde_alvo = random.choice(self.lista_acordes)
        self.opcoes = [self.acorde_alvo]
        while len(self.opcoes) < 4:
            falso = random.choice(self.lista_acordes)
            if falso not in self.opcoes:
                self.opcoes.append(falso)
        random.shuffle(self.opcoes)
        self.estado_resposta = None
        self.inicializado = True

    def desenhar(self, tela, estado, fontes, meio_x, meio_y, cam_x, cam_y):
        if not self.inicializado: self.inicializar_questao()
        
        txt_tit = fontes['titulo'].render(_t("Qual é este acorde?"), True, BRANCO)
        tela.blit(txt_tit, (meio_x - txt_tit.get_width()//2, cam_y + 100))
        
        shape = self.shapes[self.acorde_alvo]
        num_cordas = 7
        espaco_cordas = 30
        espaco_casas = 45
        altura_shape = (num_cordas - 1) * espaco_cordas
        largura_shape = (len(shape[0])) * espaco_casas
        
        x_shape = meio_x - largura_shape // 2
        y_shape = meio_y - 100
        
        pygame.draw.rect(tela, (50, 30, 20), (x_shape, y_shape, largura_shape, altura_shape), border_radius=5)
        for i in range(len(shape[0]) + 1):
            lx = x_shape + (i * espaco_casas)
            pygame.draw.line(tela, (150, 150, 150), (lx, y_shape), (lx, y_shape + altura_shape), 2)
        
        for i in range(num_cordas):
            ly = y_shape + (i * espaco_cordas)
            pygame.draw.line(tela, (200, 200, 200), (x_shape, ly), (x_shape + largura_shape, ly), 1)
            for casa_idx in range(len(shape[i])):
                val = shape[i][casa_idx]
                if val in [1, 2]:
                    bx = x_shape + (casa_idx * espaco_casas) + (espaco_casas // 2)
                    by = y_shape + altura_shape - (i * espaco_cordas) 
                    cor = (255, 100, 100) if val == 2 else BRANCO
                    pygame.draw.circle(tela, cor, (bx, by), 12)
                    pygame.draw.circle(tela, (0, 0, 0), (bx, by), 12, 2)

        y_btns = y_shape + altura_shape + 60
        self.rects_opcoes.clear()
        for i, op in enumerate(self.opcoes):
            col = i % 2
            lin = i // 2
            rx = meio_x - 210 + (col * 220)
            ry = y_btns + (lin * 60)
            rect = pygame.Rect(rx, ry, 200, 50)
            self.rects_opcoes.append((op, rect))
            
            cor_bg = (60, 60, 70)
            if self.estado_resposta == "conferido":
                if op == self.acorde_alvo: cor_bg = (50, 180, 50)
                elif op == self.resposta_usuario: cor_bg = (180, 50, 50)
                
            pygame.draw.rect(tela, cor_bg, rect, border_radius=8)
            pygame.draw.rect(tela, (150, 150, 150), rect, width=2, border_radius=8)
            txt_op = fontes['ui'].render(op, True, BRANCO)
            tela.blit(txt_op, (rect.centerx - txt_op.get_width()//2, rect.centery - txt_op.get_height()//2))

        if self.estado_resposta == "conferido":
            txt_feed = fontes['ui'].render(self.feedback, True, self.cor_feedback)
            tela.blit(txt_feed, (meio_x - txt_feed.get_width()//2, y_btns + 130))
            
            self.rect_btn_prox = pygame.Rect(meio_x - 75, y_btns + 170, 150, 40)
            pygame.draw.rect(tela, (0, 120, 215), self.rect_btn_prox, border_radius=8)
            txt_p = fontes['ui'].render("Próxima", True, BRANCO)
            tela.blit(txt_p, (self.rect_btn_prox.centerx - txt_p.get_width()//2, self.rect_btn_prox.centery - txt_p.get_height()//2))

    def tratar_cliques(self, pos, estado):
        if self.estado_resposta != "conferido":
            for op, rect in self.rects_opcoes:
                if rect.collidepoint(pos):
                    self.resposta_usuario = op
                    self.estado_resposta = "conferido"
                    if op == self.acorde_alvo:
                        self.acertos += 1
                        self.feedback = "Correto! Visão harmônica excelente."
                        self.cor_feedback = (100, 255, 100)
                    else:
                        self.feedback = f"Ops! Este era o {self.acorde_alvo}."
                        self.cor_feedback = (255, 100, 100)
                    return True
        else:
            if hasattr(self, 'rect_btn_prox') and self.rect_btn_prox.collidepoint(pos):
                self.inicializar_questao()
                return True
        return False

# =============================================================================
# GERENCIADOR DE ESTUDOS (ROTEADOR)
# =============================================================================
class GerenciadorEstudos:
    def __init__(self):
        self.rect_voltar = pygame.Rect(0, 0, 0, 0)
        self.modulo_notas = None
        self.modulo_escalas = None
        self.modulo_acordes = None
        self.modulo_acordes_pratico = None

    def desenhar_tela_estudo(self, tela, largura, altura, estado, fontes):
        tela.fill((20, 20, 25))

        cam_x = estado.camera.offset_x if hasattr(estado, 'camera') else 0
        cam_y = estado.camera.offset_y if hasattr(estado, 'camera') else 0
        w_monitor = getattr(estado, 'LARGURA_TELA', 1280)
        h_monitor = getattr(estado, 'ALTURA_TELA', 720)
        zoom = estado.camera.zoom if hasattr(estado, 'camera') else 1.0
        
        meio_x = cam_x + (w_monitor / 2) / zoom
        meio_y = cam_y + (h_monitor / 2) / zoom

        self.rect_voltar = pygame.Rect(cam_x + 20, cam_y + 20, 150, 40)
        pygame.draw.rect(tela, (200, 50, 50), self.rect_voltar, border_radius=5)
        txt_voltar = fontes['ui'].render(_t("<< Sair (ESC)"), True, (255, 255, 255))
        tela.blit(txt_voltar, (self.rect_voltar.centerx - txt_voltar.get_width()//2, self.rect_voltar.centery - txt_voltar.get_height()//2))

        titulo = f"{_t('Estudo')}: {_t(estado.estudo_ativo)}"
        txt_titulo = fontes['titulo'].render(titulo, True, (0, 160, 255))
        tela.blit(txt_titulo, (meio_x - txt_titulo.get_width() // 2, cam_y + 40))

        # =====================================================================
        # ROTEAMENTO DOS MÓDULOS DE ESTUDO
        # =====================================================================
        if estado.estudo_ativo in ["Notas", "Acerte a Nota", "Acerte o Som", "Acerte a Próxima"]:
            if self.modulo_notas is None: 
                self.modulo_notas = estudo_notas.AcerteANota()
                # Ajusta o modo inicial se o usuário veio de um botão específico
                if estado.estudo_ativo == "Acerte o Som": self.modulo_notas.modo_jogo = "ouvir"
                elif estado.estudo_ativo == "Notas": self.modulo_notas.modo_jogo = "adivinhar"
            
            self.modulo_notas.desenhar(tela, estado, fontes, meio_x, meio_y, cam_x, cam_y)
            
        elif estado.estudo_ativo in ["Escalas", "Acerte a Escala"]:
            if self.modulo_escalas is None: self.modulo_escalas = estudo_escalas.EstudoEscalas()
            self.modulo_escalas.desenhar(tela, estado, fontes, meio_x, meio_y, cam_x, cam_y)
            
        elif estado.estudo_ativo in ["Acordes", "Acerte o Acorde"]:
            if self.modulo_acordes is None: self.modulo_acordes = EstudoAcordes()
            self.modulo_acordes.desenhar(tela, estado, fontes, meio_x, meio_y, cam_x, cam_y)
            
        elif estado.estudo_ativo == "Prática de Acordes":
            if self.modulo_acordes_pratico is None: self.modulo_acordes_pratico = estudo_acordes_pratico.EstudoAcordesPratico()
            self.modulo_acordes_pratico.desenhar(tela, estado, fontes, meio_x, meio_y, cam_x, cam_y)

        else:
            txt_info = fontes['ui'].render("Módulo em desenvolvimento...", True, (150, 150, 150))
            tela.blit(txt_info, (meio_x - txt_info.get_width() // 2, meio_y))

    def _limpar_modulos(self):
        self.modulo_notas = None
        self.modulo_escalas = None
        self.modulo_acordes = None
        self.modulo_acordes_pratico = None

    def tratar_eventos(self, evento, pos_mouse, estado):
        cam_x = estado.camera.offset_x if hasattr(estado, 'camera') else 0
        cam_y = estado.camera.offset_y if hasattr(estado, 'camera') else 0
        zoom = estado.camera.zoom if hasattr(estado, 'camera') else 1.0
        pos_mouse_virtual = (cam_x + pos_mouse[0] / zoom, cam_y + pos_mouse[1] / zoom)

        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            estado.tela_estudo_ativa = False
            estado.estudo_ativo = ""
            self._limpar_modulos()
            return True

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.rect_voltar.collidepoint(pos_mouse_virtual):
                estado.tela_estudo_ativa = False
                estado.estudo_ativo = ""
                self._limpar_modulos()
                return True

            if estado.estudo_ativo in ["Notas", "Acerte a Nota", "Acerte o Som", "Acerte a Próxima"] and self.modulo_notas:
                if self.modulo_notas.tratar_cliques(pos_mouse_virtual, estado): return True
            elif estado.estudo_ativo in ["Escalas", "Acerte a Escala"] and self.modulo_escalas:
                if self.modulo_escalas.tratar_cliques(pos_mouse_virtual, estado): return True
            elif estado.estudo_ativo in ["Acordes", "Acerte o Acorde"] and self.modulo_acordes:
                if self.modulo_acordes.tratar_cliques(pos_mouse_virtual, estado): return True
            elif estado.estudo_ativo == "Prática de Acordes" and self.modulo_acordes_pratico:
                if self.modulo_acordes_pratico.tratar_cliques(pos_mouse_virtual, estado): return True
                        
        return False