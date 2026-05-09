# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================
# ui_componentes.py
import pygame
from constantes_ui import BRANCO

class DesenhoEscala:
    def __init__(self, x_painel, y_painel, espaco_casas, espaco_cordas, altura_braco, offset_x, num_casas_total, padrao, nome="", cor_base=(255, 255, 255)):
        self.nome = nome 
        self.aba = 0
        self.sub_aba = 0
        self.x_original = x_painel
        self.y_original = y_painel
        self.espaco_casas = espaco_casas
        # REMOVEMOS: O offset fixo não será mais a âncora principal. Usaremos a posição real em tempo de desenho.
        # self.offset_x = offset_x 
        self.num_casas_total = num_casas_total
        self.num_casas_desenho = len(padrao[0]) 
        
        self.padding_x = 5  
        self.padding_y = 20  
        raio = 18
        
        self.largura_real = espaco_casas * self.num_casas_desenho
        self.altura_real = altura_braco
        
        w_surf = int(self.largura_real + (self.padding_x * 2))
        h_surf = int(self.altura_real + (self.padding_y * 2))
        
        self.imagem_braco = pygame.Surface((w_surf, h_surf))
        self.imagem_braco.fill((0, 0, 0)) 
        
        COR_TRANSPARENTE = (255, 255, 255)
        self.imagem_braco.set_colorkey(COR_TRANSPARENTE)
        pygame.draw.rect(self.imagem_braco, (255, 255, 255), self.imagem_braco.get_rect(), 2)
        
        COR_DESTAQUE_TONICA = (255, 80, 80) 
        COR_NORMAL = cor_base 

        for corda in range(7):
            for casa_interna in range(self.num_casas_desenho):
                valor_matriz = padrao[corda][casa_interna]
                
                if valor_matriz in [1, 2]:
                    x_bolinha = self.padding_x + (casa_interna * espaco_casas) + (espaco_casas / 2)
                    y_bolinha = self.padding_y + self.altura_real - (corda * espaco_cordas)
                    
                    pygame.draw.circle(self.imagem_braco, COR_TRANSPARENTE, (int(x_bolinha), int(y_bolinha)), raio)
                    
                    if valor_matriz == 2:
                        pygame.draw.circle(self.imagem_braco, COR_DESTAQUE_TONICA, (int(x_bolinha), int(y_bolinha)), raio, 5)
                    else:
                        pygame.draw.circle(self.imagem_braco, COR_NORMAL, (int(x_bolinha), int(y_bolinha)), raio, 3)

        escala = 0.40
        w_painel = int(w_surf * escala)
        h_painel = int(h_surf * escala)
        
        self.imagem_painel = pygame.transform.scale(self.imagem_braco, (w_painel, h_painel))
        self.imagem_painel.set_colorkey(COR_TRANSPARENTE) 
        self.rect_painel = self.imagem_painel.get_rect(topleft=(x_painel, y_painel))
        self.rect_braco = self.imagem_braco.get_rect()
        self.estado = 'painel'

        # Variáveis novas para armazenar as coordenadas de rastreamento do arrasto
        self.casa_atual = 0

    def tratar_clique(self, pos_mouse, rect_braco_colisao):
        # 1. Pega o valor do scroll (se não existir, é 0)
        scroll = getattr(self, 'scroll_offset', 0)

        if self.estado == 'painel':
            rect_clique_rolado = self.rect_painel.copy()
            rect_clique_rolado.y -= scroll

            if rect_clique_rolado.collidepoint(pos_mouse):
                self.estado = 'mouse'
                return True
                
        elif self.estado == 'braco':
            if self.rect_braco.collidepoint(pos_mouse):
                self.estado = 'painel'
                return True
                
        elif self.estado == 'mouse':
            if rect_braco_colisao.collidepoint(pos_mouse):
                self.estado = 'braco'
            else:
                self.estado = 'painel'
            return True
            
        return False
    
    def atualizar_e_desenhar(self, tela, pos_mouse, rect_braco_colisao, fonte_pequena, nivel_alpha=255):
        self.imagem_painel.set_alpha(nivel_alpha)
        self.imagem_braco.set_alpha(nivel_alpha)

        # 2. Pega o valor do scroll na hora de desenhar
        scroll = getattr(self, 'scroll_offset', 0)
        
        if self.estado == 'painel':
            y_desenho_rolado = self.rect_painel.y - scroll
            tela.blit(self.imagem_painel, (self.rect_painel.x, y_desenho_rolado))
            
            if self.nome != "":
                texto_nome = fonte_pequena.render(self.nome, True, BRANCO)
                txt_x = self.rect_painel.centerx - (texto_nome.get_width() / 2)
                txt_y = y_desenho_rolado - 25 
                tela.blit(texto_nome, (txt_x, txt_y))
            
        elif self.estado == 'mouse' or self.estado == 'braco':
            
            # --- ATUALIZAÇÃO DINÂMICA DO BRAÇO ---
            # Agora a escala sempre sabe onde o braço de fato está!
            x_guit_real = rect_braco_colisao.x
            y_guit_real = rect_braco_colisao.y

            if self.estado == 'mouse':
                if rect_braco_colisao.collidepoint(pos_mouse):
                    # Calcula qual casa o mouse está apontando usando o 'x' real do braço arrastável
                    x_relativo = pos_mouse[0] - x_guit_real
                    self.casa_atual = int(x_relativo // self.espaco_casas)
                    self.casa_atual = max(0, min(self.casa_atual, self.num_casas_total - self.num_casas_desenho))
                    
                    self.rect_braco.x = x_guit_real + (self.casa_atual * self.espaco_casas) - self.padding_x
                    self.rect_braco.y = y_guit_real - self.padding_y
                    
                    pygame.draw.rect(tela, (0, 255, 0), self.rect_braco, 4)
                else:
                    self.rect_braco.center = pos_mouse
                    pygame.draw.rect(tela, (255, 0, 0), self.rect_braco, 4)

            elif self.estado == 'braco':
                # No estado braço, ele APENAS se reposiciona para seguir a guitarra
                self.rect_braco.x = x_guit_real + (self.casa_atual * self.espaco_casas) - self.padding_x
                self.rect_braco.y = y_guit_real - self.padding_y

            tela.blit(self.imagem_braco, self.rect_braco.topleft)