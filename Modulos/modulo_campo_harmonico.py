# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================

import pygame

class CampoHarmonico:
    def __init__(self):
        self.notas_base = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.tonica_campo = 'C'  # Tônica padrão
        self.indice_escala_campo = 0
        
        self.rects_acordes_campo = [] 
        self.indice_acorde_selecionado = -1 
        self.notas_acorde_selecionado = [] 

        self.escalas_campo = [
            {"nome": "Maior (Jônio)", "int": [0, 2, 4, 5, 7, 9, 11], "romanos": ["I", "ii", "iii", "IV", "V", "vi", "vii°"], "qualidades": ["", "m", "m", "", "", "m", "dim"]},
            {"nome": "Menor (Eólio)", "int": [0, 2, 3, 5, 7, 8, 10], "romanos": ["i", "ii°", "III", "iv", "v", "VI", "VII"], "qualidades": ["m", "dim", "", "m", "m", "", ""]},
            {"nome": "Dórico", "int": [0, 2, 3, 5, 7, 9, 10], "romanos": ["i", "ii", "III", "IV", "v", "vi°", "VII"], "qualidades": ["m", "m", "", "", "m", "dim", ""]},
            {"nome": "Frígio", "int": [0, 1, 3, 5, 7, 8, 10], "romanos": ["i", "II", "III", "iv", "v°", "VI", "vii"], "qualidades": ["m", "", "", "m", "dim", "", "m"]},
            {"nome": "Lídio", "int": [0, 2, 4, 6, 7, 9, 11], "romanos": ["I", "II", "iii", "iv°", "V", "vi", "vii"], "qualidades": ["", "", "m", "dim", "", "m", "m"]},
            {"nome": "Mixolídio", "int": [0, 2, 4, 5, 7, 9, 10], "romanos": ["I", "ii", "iii°", "IV", "v", "vi", "VII"], "qualidades": ["", "m", "dim", "", "m", "m", ""]},
            {"nome": "Lócrio", "int": [0, 1, 3, 5, 6, 8, 10], "romanos": ["i°", "II", "iii", "iv", "V", "VI", "vii"], "qualidades": ["dim", "", "m", "m", "", "", "m"]},
        ]
        
        self.rect_tonica_esq = pygame.Rect(0,0,0,0)
        self.rect_tonica_dir = pygame.Rect(0,0,0,0)
        self.rect_escala_esq = pygame.Rect(0,0,0,0)
        self.rect_escala_dir = pygame.Rect(0,0,0,0)

    def calcular_notas_acorde_selecionado(self):
        escala_atual = self.escalas_campo[self.indice_escala_campo]
        idx_tonica_escala = self.notas_base.index(self.tonica_campo)

        idx_raiz_acorde = (idx_tonica_escala + escala_atual["int"][self.indice_acorde_selecionado]) % 12
        qualidade = escala_atual["qualidades"][self.indice_acorde_selecionado]

        if qualidade == "": 
            idx_terca = (idx_raiz_acorde + 4) % 12
            idx_quinta = (idx_raiz_acorde + 7) % 12
        elif qualidade == "m": 
            idx_terca = (idx_raiz_acorde + 3) % 12
            idx_quinta = (idx_raiz_acorde + 7) % 12
        elif qualidade == "dim": 
            idx_terca = (idx_raiz_acorde + 3) % 12
            idx_quinta = (idx_raiz_acorde + 6) % 12

        self.notas_acorde_selecionado = [
            self.notas_base[idx_raiz_acorde],
            self.notas_base[idx_terca],
            self.notas_base[idx_quinta]
        ]

    # --- AGORA A FUNÇÃO RECEBE X_BASE E LARGURA_DRAGGER ---
    def desenhar(self, tela, x_base, y_base, largura_dragger, fonte_titulo, fonte_ui, fonte_pequena):
        x_centro = x_base + (largura_dragger // 2)
        
        COR_FUNDO = (40, 40, 40)
        COR_BORDA = (100, 100, 100)
        COR_TEXTO = (255, 255, 255)
        AZUL_BOTAO = (0, 120, 215)
        
        escala_atual = self.escalas_campo[self.indice_escala_campo]
        idx_tonica = self.notas_base.index(self.tonica_campo)
        
        largura_bloco = 70
        altura_bloco = 60
        espacamento = 15
        largura_total = (7 * largura_bloco) + (6 * espacamento)
        x_inicial = x_centro - (largura_total // 2)
        
        self.rects_acordes_campo.clear()

        for i in range(7):
            x_bloco = x_inicial + i * (largura_bloco + espacamento)
            
            idx_nota = (idx_tonica + escala_atual["int"][i]) % 12
            nota_acorde = self.notas_base[idx_nota]
            nome_acorde = nota_acorde + escala_atual["qualidades"][i]
            
            romano = escala_atual["romanos"][i]
            txt_romano = fonte_pequena.render(romano, True, COR_BORDA)
            tela.blit(txt_romano, (x_bloco + (largura_bloco//2) - (txt_romano.get_width()//2), y_base - 25))
            
            rect_bloco = pygame.Rect(x_bloco, y_base, largura_bloco, altura_bloco)
            self.rects_acordes_campo.append(rect_bloco)
            
            if self.indice_acorde_selecionado == i:
                pygame.draw.rect(tela, AZUL_BOTAO, rect_bloco, border_radius=8)
                pygame.draw.rect(tela, COR_TEXTO, rect_bloco, width=2, border_radius=8) 
            else:
                pygame.draw.rect(tela, COR_FUNDO, rect_bloco, border_radius=8)
                pygame.draw.rect(tela, COR_BORDA, rect_bloco, width=2, border_radius=8)
            
            txt_acorde = fonte_titulo.render(nome_acorde, True, COR_TEXTO)
            tela.blit(txt_acorde, (x_bloco + (largura_bloco//2) - (txt_acorde.get_width()//2), y_base + 15))

        y_controles = y_base + altura_bloco + 20
        
        self.rect_tonica_esq = pygame.Rect(x_centro - 200, y_controles, 30, 30)
        self.rect_tonica_dir = pygame.Rect(x_centro - 100, y_controles, 30, 30)
        pygame.draw.rect(tela, AZUL_BOTAO, self.rect_tonica_esq, border_radius=5)
        pygame.draw.rect(tela, AZUL_BOTAO, self.rect_tonica_dir, border_radius=5)
        tela.blit(fonte_titulo.render("<", True, COR_TEXTO), (self.rect_tonica_esq.x + 8, self.rect_tonica_esq.y + 2))
        tela.blit(fonte_titulo.render(">", True, COR_TEXTO), (self.rect_tonica_dir.x + 8, self.rect_tonica_dir.y + 2))
        
        txt_tonica = fonte_titulo.render(self.tonica_campo, True, COR_TEXTO)
        tela.blit(txt_tonica, (x_centro - 150 - (txt_tonica.get_width()//2), y_controles + 5))

        self.rect_escala_esq = pygame.Rect(x_centro + 10, y_controles, 30, 30)
        self.rect_escala_dir = pygame.Rect(x_centro + 240, y_controles, 30, 30)
        pygame.draw.rect(tela, AZUL_BOTAO, self.rect_escala_esq, border_radius=5)
        pygame.draw.rect(tela, AZUL_BOTAO, self.rect_escala_dir, border_radius=5)
        tela.blit(fonte_titulo.render("<", True, COR_TEXTO), (self.rect_escala_esq.x + 8, self.rect_escala_esq.y + 2))
        tela.blit(fonte_titulo.render(">", True, COR_TEXTO), (self.rect_escala_dir.x + 8, self.rect_escala_dir.y + 2))
        
        txt_escala = fonte_ui.render(escala_atual["nome"], True, COR_TEXTO)
        tela.blit(txt_escala, (x_centro + 140 - (txt_escala.get_width()//2), y_controles + 5))

    def tratar_clique(self, pos_mouse):
        for i, rect in enumerate(self.rects_acordes_campo):
            if rect.collidepoint(pos_mouse):
                if self.indice_acorde_selecionado == i:
                    self.indice_acorde_selecionado = -1 
                    self.notas_acorde_selecionado = []
                else:
                    self.indice_acorde_selecionado = i
                    self.calcular_notas_acorde_selecionado()
                return True

        if self.rect_tonica_esq.collidepoint(pos_mouse):
            idx = self.notas_base.index(self.tonica_campo)
            self.tonica_campo = self.notas_base[(idx - 1) % 12]
            self.indice_acorde_selecionado = -1
            return True
            
        elif self.rect_tonica_dir.collidepoint(pos_mouse):
            idx = self.notas_base.index(self.tonica_campo)
            self.tonica_campo = self.notas_base[(idx + 1) % 12]
            self.indice_acorde_selecionado = -1
            return True
            
        elif self.rect_escala_esq.collidepoint(pos_mouse):
            self.indice_escala_campo = (self.indice_escala_campo - 1) % len(self.escalas_campo)
            self.indice_acorde_selecionado = -1
            return True
            
        elif self.rect_escala_dir.collidepoint(pos_mouse):
            self.indice_escala_campo = (self.indice_escala_campo + 1) % len(self.escalas_campo)
            self.indice_acorde_selecionado = -1
            return True

        return False