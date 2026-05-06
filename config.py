# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 [SEU NOME]
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================

import pygame

class Configuracoes:
    def __init__(self, x_painel, y_painel):
        self.modos_texto = ['letras', 'graus', 'vazio']
        self.nomes_modos = ['C D E (Notas)', '1 2 3 (Graus)', 'Apenas Bolinha']
        self.indice_modo = 0

        # --- NOVO: FONTES DO SISTEMA ---
        # Escolha fontes que são nativas do Windows/Mac para evitar erros
        self.fontes_disponiveis = ['Arial', 'Verdana', 'Courier New', 'Consolas', 'Impact']
        self.indice_fonte = 0
        self.rects_fontes = []
        self.x = x_painel
        self.y = y_painel
        self.largura_maxima = 650 # Quando passar daqui, os itens descem para a próxima linha
        
        # --- ESTADOS DAS CONFIGURAÇÕES ---
        self.transparencia = 100 
        self.cor_braco = (80, 40, 15)  # Madeira padrão
        self.cor_notas = (255, 255, 255) # Branco padrão
        
        self.modos_texto = ['letras', 'graus', 'vazio']
        self.nomes_modos = ['C D E (Notas)', '1 2 3 (Graus)', 'Apenas Bolinha']
        self.indice_modo = 0

        # --- VARIÁVEIS DO SELETOR DE CORES (POP-UP) ---
        self.picker_aberto = False
        self.alvo_picker = None # Pode ser 'braco' ou 'notas'
        self.rect_picker = pygame.Rect(0, 0, 200, 150)
        self.surf_paleta = self.gerar_superficie_cores(self.rect_picker.width, self.rect_picker.height)

        # --- RETÂNGULOS DE COLISÃO (Atualizados dinamicamente pelo Flexbox) ---
        self.largura_slider = 200
        self.rect_barra_transp = pygame.Rect(0, 0, self.largura_slider, 10)
        self.rect_cursor_transp = pygame.Rect(0, 0, 15, 20)
        self.arrastando_transp = False

        self.rect_btn_cor_braco = pygame.Rect(0, 0, 50, 50)
        self.rect_btn_cor_notas = pygame.Rect(0, 0, 50, 50)
        self.rects_modos = []

        # Cores Básicas da UI
        self.BRANCO = (255, 255, 255)
        self.PRETO = (0, 0, 0)
        self.CINZA = (100, 100, 100)
        self.AZUL_DESTAQUE = (0, 120, 215)

    def gerar_superficie_cores(self, largura, altura):
        """Gera um espectro HSV de cores para o usuário clicar (O 'Color Picker')"""
        surf = pygame.Surface((largura, altura))
        for x in range(largura):
            for y in range(altura):
                matiz = int((x / largura) * 360) # Hue de 0 a 360
                brilho = int(100 - (y / altura) * 100) # Value de 100 a 0
                cor = pygame.Color(0)
                cor.hsva = (matiz, 100, brilho, 100) # (Hue, Saturation, Value, Alpha)
                surf.set_at((x, y), cor)
        return surf

    # --- GETTERS PARA O MAIN.PY ---
    def get_alpha(self): return int((self.transparencia / 100) * 255)
    def get_cor_braco(self): return self.cor_braco
    def get_cor_notas(self): return self.cor_notas
    def get_modo_texto(self): return self.modos_texto[self.indice_modo]

    # --- EVENTOS ---
    def tratar_clique(self, pos_mouse, aba_config_ativa):
        
        if not aba_config_ativa: return False
        # 4. Modos de Texto
        for i, rect in enumerate(self.rects_modos):
            if rect.collidepoint(pos_mouse):
                self.indice_modo = i
                return True

        # --- NOVO: Clique nas Fontes ---
        for i, rect in enumerate(self.rects_fontes):
            if rect.collidepoint(pos_mouse):
                self.indice_fonte = i
                return True
        # 1. Se o Seletor de Cores estiver aberto, ele bloqueia os outros cliques (Modal)
        if self.picker_aberto:
            if self.rect_picker.collidepoint(pos_mouse):
                # Pega a cor exata do pixel que o mouse clicou dentro da paleta
                x_rel = pos_mouse[0] - self.rect_picker.x
                y_rel = pos_mouse[1] - self.rect_picker.y
                cor_escolhida = self.surf_paleta.get_at((x_rel, y_rel))
                
                # Salva na variável correta e fecha o pop-up
                if self.alvo_picker == 'braco':
                    self.cor_braco = (cor_escolhida.r, cor_escolhida.g, cor_escolhida.b)
                elif self.alvo_picker == 'notas':
                    self.cor_notas = (cor_escolhida.r, cor_escolhida.g, cor_escolhida.b)
                
                self.picker_aberto = False
                return True
            else:
                # Se clicou fora do seletor, apenas fecha ele
                self.picker_aberto = False
                return True

        # 2. Cliques normais nas configurações
        if self.rect_cursor_transp.collidepoint(pos_mouse) or self.rect_barra_transp.collidepoint(pos_mouse):
            self.arrastando_transp = True
            return True

        if self.rect_btn_cor_braco.collidepoint(pos_mouse):
            self.picker_aberto = True
            self.alvo_picker = 'braco'
            # Posiciona o pop-up do lado do botão
            self.rect_picker.topleft = (self.rect_btn_cor_braco.right + 10, self.rect_btn_cor_braco.y)
            return True

        if self.rect_btn_cor_notas.collidepoint(pos_mouse):
            self.picker_aberto = True
            self.alvo_picker = 'notas'
            self.rect_picker.topleft = (self.rect_btn_cor_notas.right + 10, self.rect_btn_cor_notas.y)
            return True

        for i, rect in enumerate(self.rects_modos):
            if rect.collidepoint(pos_mouse):
                self.indice_modo = i
                return True
        
        return False
    
    def get_fonte(self): 
        return self.fontes_disponiveis[self.indice_fonte]    
    
    def processar_logica(self, pos_mouse):
        if self.arrastando_transp:
            if not pygame.mouse.get_pressed()[0]:
                self.arrastando_transp = False
            else:
                rel_x = max(0, min(self.largura_slider, pos_mouse[0] - self.rect_barra_transp.x))
                self.transparencia = int((rel_x / self.largura_slider) * 100)

    # --- DESENHO COM LÓGICA DE FLEXBOX ---
    # --- DESENHO COM LÓGICA DE FLEXBOX ---
    def desenhar(self, tela, fonte_titulo, fonte_ui, scroll_y=0):
        x_atual = self.x
        # 1. A MÁGICA DO SCROLL: O Y base agora subtrai a rolagem da tela!
        y_atual = self.y - scroll_y 
        altura_linha = 100 # Espaço que cada linha ocupa para baixo
        espacamento_x = 40  # Espaço entre um bloco e outro na mesma linha

        # Função auxiliar de Flexbox: Checa se cabe. Se não couber, quebra a linha!
        def quebrar_linha_se_precisar(largura_do_bloco):
            nonlocal x_atual, y_atual
            if x_atual + largura_do_bloco > self.x + self.largura_maxima:
                x_atual = self.x
                y_atual += altura_linha

        # BLOCO 1: Transparência (Largura aprox: 250px)
        largura_b1 = 250
        quebrar_linha_se_precisar(largura_b1)
        tela.blit(fonte_ui.render(f"Transparência: {self.transparencia}%", True, self.BRANCO), (x_atual, y_atual))
        
        self.rect_barra_transp.topleft = (x_atual, y_atual + 40)
        pygame.draw.rect(tela, self.CINZA, self.rect_barra_transp)
        pos_cursor_x = self.rect_barra_transp.x + (self.transparencia / 100) * self.largura_slider
        self.rect_cursor_transp.topleft = (pos_cursor_x - 7, self.rect_barra_transp.y - 5)
        pygame.draw.rect(tela, self.BRANCO, self.rect_cursor_transp)
        x_atual += largura_b1 + espacamento_x

        # BLOCO 2: Cor do Braço (Largura aprox: 150px)
        largura_b2 = 150
        quebrar_linha_se_precisar(largura_b2)
        tela.blit(fonte_ui.render("Cor do Braço:", True, self.BRANCO), (x_atual, y_atual))
        self.rect_btn_cor_braco.topleft = (x_atual, y_atual + 25)
        pygame.draw.rect(tela, self.cor_braco, self.rect_btn_cor_braco, border_radius=5)
        pygame.draw.rect(tela, self.BRANCO, self.rect_btn_cor_braco, 2, border_radius=5)
        x_atual += largura_b2 + espacamento_x

        # BLOCO 3: Cor das Notas (Largura aprox: 150px)
        largura_b3 = 150
        quebrar_linha_se_precisar(largura_b3)
        tela.blit(fonte_ui.render("Cor das Notas:", True, self.BRANCO), (x_atual, y_atual))
        self.rect_btn_cor_notas.topleft = (x_atual, y_atual + 25)
        pygame.draw.rect(tela, self.cor_notas, self.rect_btn_cor_notas, border_radius=5)
        pygame.draw.rect(tela, self.BRANCO, self.rect_btn_cor_notas, 2, border_radius=5)
        x_atual += largura_b3 + espacamento_x
        
        # BLOCO 4: Estilo do Texto (Largura aprox: 200px)
        largura_b4 = 200
        quebrar_linha_se_precisar(largura_b4) 
        tela.blit(fonte_ui.render("Texto nas Notas:", True, self.BRANCO), (x_atual, y_atual))
        self.rects_modos.clear()
        for i, nome in enumerate(self.nomes_modos):
            rect_botao = pygame.Rect(x_atual, y_atual + 25 + (i * 30), 180, 25)
            self.rects_modos.append(rect_botao)
            cor_fundo = self.AZUL_DESTAQUE if i == self.indice_modo else self.CINZA
            pygame.draw.rect(tela, cor_fundo, rect_botao, border_radius=5)
            tela.blit(fonte_ui.render(nome, True, self.BRANCO), (rect_botao.x + 10, rect_botao.y + 3))
            
        x_atual += largura_b4 + espacamento_x 

        # BLOCO 5: Escolha da Fonte (Largura aprox: 200px)
        largura_b5 = 200
        quebrar_linha_se_precisar(largura_b5)
        tela.blit(fonte_ui.render("Fonte do Sistema:", True, self.BRANCO), (x_atual, y_atual))
        self.rects_fontes.clear()
        
        for i, nome_fonte in enumerate(self.fontes_disponiveis):
            rect_botao = pygame.Rect(x_atual, y_atual + 25 + (i * 30), 180, 25)
            self.rects_fontes.append(rect_botao)
            
            cor_fundo = self.AZUL_DESTAQUE if i == self.indice_fonte else self.CINZA
            pygame.draw.rect(tela, cor_fundo, rect_botao, border_radius=5)
            
            # Escreve o nome da fonte no botão
            tela.blit(fonte_ui.render(nome_fonte, True, self.BRANCO), (rect_botao.x + 10, rect_botao.y + 3))
            
        x_atual += largura_b5 + espacamento_x

        # --- DESENHO DO POP-UP DO SELETOR DE CORES ---
        if self.picker_aberto:
            # Garante que o pop-up acompanhe o botão mesmo se rolarmos a tela com ele aberto
            if self.alvo_picker == 'braco':
                self.rect_picker.topleft = (self.rect_btn_cor_braco.right + 10, self.rect_btn_cor_braco.y)
            elif self.alvo_picker == 'notas':
                self.rect_picker.topleft = (self.rect_btn_cor_notas.right + 10, self.rect_btn_cor_notas.y)

            # Fundo preto para destacar o seletor
            fundo_picker = pygame.Rect(self.rect_picker.x - 5, self.rect_picker.y - 5, self.rect_picker.width + 10, self.rect_picker.height + 10)
            pygame.draw.rect(tela, self.PRETO, fundo_picker, border_radius=5)
            
            # Desenha o espectro HSV
            tela.blit(self.surf_paleta, self.rect_picker.topleft)
            pygame.draw.rect(tela, self.BRANCO, self.rect_picker, 2)