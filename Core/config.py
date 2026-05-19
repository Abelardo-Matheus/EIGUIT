# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================

import pygame

class Configuracoes:
    def __init__(self, x_painel, y_painel):
        self.x = x_painel
        self.y = y_painel
        self.largura_maxima = 650
        
        # --- ESTADOS DAS CONFIGURAÇÕES ---
        self.transparencia = 100 
        self.cor_braco = (80, 40, 15)
        self.cor_notas = (255, 255, 255)
        
        self.modos_texto = ['letras', 'graus', 'vazio']
        self.nomes_modos = ['C D E (Notas)', '1 2 3 (Graus)', 'Apenas Bolinha']
        self.indice_modo = 0

        self.fontes_disponiveis = ['Arial', 'Verdana', 'Courier New', 'Consolas', 'Impact']
        self.indice_fonte = 0
        self.rects_fontes = []

        # --- TRADUÇÃO ---
        self.idiomas = [
            {'nome': 'Português', 'code': 'pt'},
            {'nome': 'English', 'code': 'en'},
            {'nome': 'Español', 'code': 'es'},
            {'nome': 'Français', 'code': 'fr'},
            {'nome': 'Deutsch', 'code': 'de'}
        ]
        self.indice_idioma = 0
        self.rect_btn_idioma_esq = pygame.Rect(0, 0, 30, 30)
        self.rect_btn_idioma_dir = pygame.Rect(0, 0, 30, 30)

        # --- NOVAS CONFIGURAÇÕES (VISUAL E TEMAS) ---
        self.temas = ['Azul', 'Vermelho', 'Verde', 'Roxo', 'Laranja']
        self.cores_temas = [(0, 120, 215), (200, 50, 50), (50, 180, 50), (150, 50, 200), (230, 100, 0)]
        self.indice_tema = 0
        self.AZUL_DESTAQUE = self.cores_temas[0]
        
        self.velocidade_jogo = 1.0
        self.volume_fx = 80
        self.particulas_habilitadas = True
        self.tamanho_notas = 1.0
        
        # --- VARIÁVEIS DO SELETOR DE CORES ---
        self.picker_aberto = False
        self.alvo_picker = None
        self.rect_picker = pygame.Rect(0, 0, 200, 150)
        self.surf_paleta = self.gerar_superficie_cores(self.rect_picker.width, self.rect_picker.height)

        # --- RETÂNGULOS DE COLISÃO ---
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
        self.rect_btn_nota_menos = pygame.Rect(0, 0, 30, 30)
        self.rect_btn_nota_mais = pygame.Rect(0, 0, 30, 30)

        # Cores Básicas
        self.BRANCO = (255, 255, 255)
        self.PRETO = (0, 0, 0)
        self.CINZA = (100, 100, 100)

    def gerar_superficie_cores(self, largura, altura):
        surf = pygame.Surface((largura, altura))
        for x in range(largura):
            for y in range(altura):
                matiz = int((x / largura) * 360)
                brilho = int(100 - (y / altura) * 100)
                cor = pygame.Color(0)
                cor.hsva = (matiz, 100, brilho, 100)
                surf.set_at((x, y), cor)
        return surf

    def get_alpha(self): return int((self.transparencia / 100) * 255)
    def get_cor_braco(self): return self.cor_braco
    def get_cor_notas(self): return self.cor_notas
    def get_modo_texto(self): return self.modos_texto[self.indice_modo]
    def get_fonte(self): return self.fontes_disponiveis[self.indice_fonte]    
    def get_vel_jogo(self): return self.velocidade_jogo
    def get_vol_fx(self): return self.volume_fx / 100.0
    def get_particulas(self): return self.particulas_habilitadas
    def get_cor_tema(self): return self.cores_temas[self.indice_tema]
    def get_escala_nota(self): return self.tamanho_notas

    def tratar_clique(self, pos_mouse, aba_config_ativa):
        if not aba_config_ativa: return False
        if self.picker_aberto:
            if self.rect_picker.collidepoint(pos_mouse):
                x_rel, y_rel = pos_mouse[0] - self.rect_picker.x, pos_mouse[1] - self.rect_picker.y
                cor = self.surf_paleta.get_at((x_rel, y_rel))
                if self.alvo_picker == 'braco': self.cor_braco = (cor.r, cor.g, cor.b)
                elif self.alvo_picker == 'notas': self.cor_notas = (cor.r, cor.g, cor.b)
            self.picker_aberto = False; return True

        if self.rect_cursor_transp.collidepoint(pos_mouse) or self.rect_barra_transp.collidepoint(pos_mouse):
            self.arrastando_transp = True; return True
        if self.rect_cursor_vol_fx.collidepoint(pos_mouse) or self.rect_barra_vol_fx.collidepoint(pos_mouse):
            self.arrastando_vol_fx = True; return True
        if self.rect_btn_cor_braco.collidepoint(pos_mouse):
            self.picker_aberto = True; self.alvo_picker = 'braco'; self.rect_picker.topleft = (pos_mouse[0]-100, pos_mouse[1]-160); return True
        if self.rect_btn_cor_notas.collidepoint(pos_mouse):
            self.picker_aberto = True; self.alvo_picker = 'notas'; self.rect_picker.topleft = (pos_mouse[0]-100, pos_mouse[1]-160); return True
        if self.rect_btn_particulas.collidepoint(pos_mouse):
            self.particulas_habilitadas = not self.particulas_habilitadas; return True
        if self.rect_btn_vel_menos.collidepoint(pos_mouse): self.velocidade_jogo = round(max(0.5, self.velocidade_jogo - 0.1), 1); return True
        if self.rect_btn_vel_mais.collidepoint(pos_mouse): self.velocidade_jogo = round(min(3.0, self.velocidade_jogo + 0.1), 1); return True
        if self.rect_btn_tema_esq.collidepoint(pos_mouse): self.indice_tema = (self.indice_tema - 1) % len(self.temas); self.AZUL_DESTAQUE = self.cores_temas[self.indice_tema]; return True
        if self.rect_btn_tema_dir.collidepoint(pos_mouse): self.indice_tema = (self.indice_tema + 1) % len(self.temas); self.AZUL_DESTAQUE = self.cores_temas[self.indice_tema]; return True
        if self.rect_btn_nota_menos.collidepoint(pos_mouse): self.tamanho_notas = round(max(0.5, self.tamanho_notas - 0.1), 1); return True
        if self.rect_btn_nota_mais.collidepoint(pos_mouse): self.tamanho_notas = round(min(1.5, self.tamanho_notas + 0.1), 1); return True
        
        # Cliques no Idioma
        if self.rect_btn_idioma_esq.collidepoint(pos_mouse):
            self.indice_idioma = (self.indice_idioma - 1) % len(self.idiomas)
            codigo = self.idiomas[self.indice_idioma]['code']
            from Core.i18n import sistema_traducao
            sistema_traducao.atualizar_configuracao(codigo)
            return True
        if self.rect_btn_idioma_dir.collidepoint(pos_mouse):
            self.indice_idioma = (self.indice_idioma + 1) % len(self.idiomas)
            codigo = self.idiomas[self.indice_idioma]['code']
            from Core.i18n import sistema_traducao
            sistema_traducao.atualizar_configuracao(codigo)
            return True

        for i, r in enumerate(self.rects_modos):
            if r.collidepoint(pos_mouse): self.indice_modo = i; return True
        for i, r in enumerate(self.rects_fontes):
            if r.collidepoint(pos_mouse): self.indice_fonte = i; return True
        return False
    
    def processar_logica(self, pos_mouse):
        if self.arrastando_transp:
            if not pygame.mouse.get_pressed()[0]: self.arrastando_transp = False
            else:
                rel_x = max(0, min(self.largura_slider, pos_mouse[0] - self.rect_barra_transp.x))
                self.transparencia = int((rel_x / self.largura_slider) * 100)
        if self.arrastando_vol_fx:
            if not pygame.mouse.get_pressed()[0]: self.arrastando_vol_fx = False
            else:
                rel_x = max(0, min(self.largura_slider, pos_mouse[0] - self.rect_barra_vol_fx.x))
                self.volume_fx = int((rel_x / self.largura_slider) * 100)

    def desenhar(self, tela, fontes, scroll_y=0):
        # Desempacota do dicionário para manter compatibilidade com o código abaixo
        fonte_titulo = fontes['titulo']
        fonte_ui = fontes['ui']
        
        x_atual, y_atual = self.x, self.y - scroll_y 
        altura_bloco, largura_bloco, esp = 180, 310, 20

        def container(x, y, titulo):
            rect = pygame.Rect(x, y, largura_bloco, altura_bloco)
            pygame.draw.rect(tela, (35, 35, 45), rect, border_radius=12)
            pygame.draw.rect(tela, (80, 80, 100), rect, width=2, border_radius=12)
            tela.blit(fonte_ui.render(_t(titulo), True, self.AZUL_DESTAQUE), (x + 15, y + 10))
            return y + 45

        # Bloco 1
        y_int = container(x_atual, y_atual, "Ajustes de Áudio")
        tela.blit(fonte_ui.render(f"{_t('Transparência')}: {self.transparencia}%", True, self.BRANCO), (x_atual + 15, y_int))
        self.rect_barra_transp.topleft = (x_atual + 15, y_int + 25)
        pygame.draw.rect(tela, self.CINZA, self.rect_barra_transp, border_radius=5)
        px = self.rect_barra_transp.x + (self.transparencia / 100) * self.largura_slider
        self.rect_cursor_transp.topleft = (px - 7, self.rect_barra_transp.y - 5)
        pygame.draw.rect(tela, self.BRANCO, self.rect_cursor_transp, border_radius=3)
        y_int += 65
        tela.blit(fonte_ui.render(f"{_t('Volume FX')}: {self.volume_fx}%", True, self.BRANCO), (x_atual + 15, y_int))
        self.rect_barra_vol_fx.topleft = (x_atual + 15, y_int + 25)
        pygame.draw.rect(tela, self.CINZA, self.rect_barra_vol_fx, border_radius=5)
        pxv = self.rect_barra_vol_fx.x + (self.volume_fx / 100) * self.largura_slider
        self.rect_cursor_vol_fx.topleft = (pxv - 7, self.rect_barra_vol_fx.y - 5)
        pygame.draw.rect(tela, self.BRANCO, self.rect_cursor_vol_fx, border_radius=3)

        # Bloco 2
        x_c2 = x_atual + largura_bloco + esp
        y_int = container(x_c2, y_atual, "Cores do Instrumento")
        self.rect_btn_cor_braco.topleft = (x_c2 + 20, y_int + 5)
        pygame.draw.rect(tela, self.cor_braco, self.rect_btn_cor_braco, border_radius=8)
        pygame.draw.rect(tela, self.BRANCO, self.rect_btn_cor_braco, 2, border_radius=8)
        tela.blit(fonte_ui.render(_t("Cor Madeira"), True, self.BRANCO), (self.rect_btn_cor_braco.right + 15, y_int + 15))
        self.rect_btn_cor_notas.topleft = (x_c2 + 20, y_int + 70)
        pygame.draw.rect(tela, self.cor_notas, self.rect_btn_cor_notas, border_radius=8)
        pygame.draw.rect(tela, self.BRANCO, self.rect_btn_cor_notas, 2, border_radius=8)
        tela.blit(fonte_ui.render(_t("Cor Notas"), True, self.BRANCO), (self.rect_btn_cor_notas.right + 15, y_int + 80))

        # Bloco 3
        y_l2 = y_atual + altura_bloco + esp
        y_int = container(x_atual, y_l2, "Performance e Jogos")
        self.rect_btn_particulas.topleft = (x_atual + 15, y_int)
        pygame.draw.rect(tela, (60, 60, 60), self.rect_btn_particulas, border_radius=5)
        if self.particulas_habilitadas: pygame.draw.rect(tela, self.AZUL_DESTAQUE, self.rect_btn_particulas.inflate(-10, -10), border_radius=3)
        pygame.draw.rect(tela, self.BRANCO, self.rect_btn_particulas, 2, border_radius=5)
        tela.blit(fonte_ui.render(_t("Efeitos de Partículas"), True, self.BRANCO), (self.rect_btn_particulas.right + 10, y_int + 2))
        y_int += 50
        tela.blit(fonte_ui.render(f"{_t('Velocidade Jogos')}: {self.velocidade_jogo}x", True, self.BRANCO), (x_atual + 15, y_int))
        self.rect_btn_vel_menos.topleft = (x_atual + 15, y_int + 30); self.rect_btn_vel_mais.topleft = (x_atual + 110, y_int + 30)
        pygame.draw.rect(tela, self.AZUL_DESTAQUE, self.rect_btn_vel_menos, border_radius=5); pygame.draw.rect(tela, self.AZUL_DESTAQUE, self.rect_btn_vel_mais, border_radius=5)
        tela.blit(fonte_titulo.render("-", True, self.BRANCO), (self.rect_btn_vel_menos.centerx-5, self.rect_btn_vel_menos.centery-15))
        tela.blit(fonte_titulo.render("+", True, self.BRANCO), (self.rect_btn_vel_mais.centerx-7, self.rect_btn_vel_mais.centery-15))

        # Bloco 4
        y_int = container(x_c2, y_l2, "Temas e Aparência")
        tela.blit(fonte_ui.render(_t("Tema de Cores:"), True, self.BRANCO), (x_c2 + 15, y_int))
        self.rect_btn_tema_esq.topleft = (x_c2 + 15, y_int + 30); self.rect_btn_tema_dir.topleft = (x_c2 + 180, y_int + 30)
        pygame.draw.rect(tela, self.AZUL_DESTAQUE, self.rect_btn_tema_esq, border_radius=5); pygame.draw.rect(tela, self.AZUL_DESTAQUE, self.rect_btn_tema_dir, border_radius=5)
        tela.blit(fonte_ui.render("<", True, self.BRANCO), (self.rect_btn_tema_esq.centerx-5, self.rect_btn_tema_esq.centery-10))
        tela.blit(fonte_ui.render(">", True, self.BRANCO), (self.rect_btn_tema_dir.centerx-5, self.rect_btn_tema_dir.centery-10))
        txt_t = fonte_ui.render(_t(self.temas[self.indice_tema]), True, self.BRANCO)
        tela.blit(txt_t, (x_c2 + 100 - txt_t.get_width()//2, y_int + 35))
        y_int += 75
        tela.blit(fonte_ui.render(f"{_t('Escala Notas')}: {self.tamanho_notas}x", True, self.BRANCO), (x_c2 + 15, y_int))
        self.rect_btn_nota_menos.topleft = (x_c2 + 15, y_int + 30); self.rect_btn_nota_mais.topleft = (x_c2 + 110, y_int + 30)
        pygame.draw.rect(tela, self.AZUL_DESTAQUE, self.rect_btn_nota_menos, border_radius=5); pygame.draw.rect(tela, self.AZUL_DESTAQUE, self.rect_btn_nota_mais, border_radius=5)
        tela.blit(fonte_titulo.render("-", True, self.BRANCO), (self.rect_btn_nota_menos.centerx-5, self.rect_btn_nota_menos.centery-15))
        tela.blit(fonte_titulo.render("+", True, self.BRANCO), (self.rect_btn_nota_mais.centerx-7, self.rect_btn_nota_mais.centery-15))

        # Bloco 5 e 6
        y_l3 = y_l2 + altura_bloco + esp
        y_int = container(x_atual, y_l3, "Estilo de Notas")
        self.rects_modos.clear()
        for i, n in enumerate(self.nomes_modos):
            r = pygame.Rect(x_atual + 15, y_int + (i * 35), 220, 28)
            self.rects_modos.append(r); pygame.draw.rect(tela, self.AZUL_DESTAQUE if i == self.indice_modo else (60, 60, 60), r, border_radius=5)
            tela.blit(fonte_ui.render(_t(n), True, self.BRANCO), (r.x + 10, r.y + 3))

        y_int = container(x_c2, y_l3, "Fontes do Sistema")
        self.rects_fontes.clear()
        for i, f in enumerate(self.fontes_disponiveis):
            r = pygame.Rect(x_c2 + 15, y_int + (i * 25), 180, 22)
            self.rects_fontes.append(r); pygame.draw.rect(tela, self.AZUL_DESTAQUE if i == self.indice_fonte else (60, 60, 60), r, border_radius=5)
            tela.blit(fonte_ui.render(f, True, self.BRANCO), (r.x + 10, r.y + 1))

        # Bloco 7: Idioma
        y_l4 = y_l3 + altura_bloco + esp
        y_int = container(x_atual, y_l4, "Idioma da Interface")
        self.rect_btn_idioma_esq.topleft = (x_atual + 15, y_int + 15)
        self.rect_btn_idioma_dir.topleft = (x_atual + 180, y_int + 15)
        pygame.draw.rect(tela, self.AZUL_DESTAQUE, self.rect_btn_idioma_esq, border_radius=5)
        pygame.draw.rect(tela, self.AZUL_DESTAQUE, self.rect_btn_idioma_dir, border_radius=5)
        tela.blit(fonte_ui.render("<", True, self.BRANCO), (self.rect_btn_idioma_esq.centerx-5, self.rect_btn_idioma_esq.centery-10))
        tela.blit(fonte_ui.render(">", True, self.BRANCO), (self.rect_btn_idioma_dir.centerx-5, self.rect_btn_idioma_dir.centery-10))
        
        txt_id = fonte_ui.render(_t(self.idiomas[self.indice_idioma]['nome']), True, self.BRANCO)
        tela.blit(txt_id, (x_atual + 100 - txt_id.get_width()//2, y_int + 20))
        
        lbl_info = fontes['pequena'].render(_t("(API Translation + Cache)"), True, self.CINZA)
        tela.blit(lbl_info, (x_atual + 15, y_int + 55))

        if self.picker_aberto:
            fp = pygame.Rect(self.rect_picker.x-5, self.rect_picker.y-5, self.rect_picker.width+10, self.rect_picker.height+10)
            pygame.draw.rect(tela, self.PRETO, fp, border_radius=5)
            tela.blit(self.surf_paleta, self.rect_picker.topleft)
            pygame.draw.rect(tela, self.BRANCO, self.rect_picker, 2)
