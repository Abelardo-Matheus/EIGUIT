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
        self.offset_x = offset_x
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

    def tratar_clique(self, pos_mouse, rect_braco_colisao):
        if self.estado == 'painel':
            if self.rect_painel.collidepoint(pos_mouse):
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
    
    # ATENÇÃO: Adicionamos fonte_pequena como parâmetro aqui para não depender do main.py!
    def atualizar_e_desenhar(self, tela, pos_mouse, rect_braco_colisao, fonte_pequena, nivel_alpha=255):
        self.imagem_painel.set_alpha(nivel_alpha)
        self.imagem_braco.set_alpha(nivel_alpha)
        if self.estado == 'painel':
            tela.blit(self.imagem_painel, self.rect_painel.topleft)
            
            if self.nome != "":
                texto_nome = fonte_pequena.render(self.nome, True, BRANCO)
                txt_x = self.rect_painel.centerx - (texto_nome.get_width() / 2)
                txt_y = self.rect_painel.top - 25 
                tela.blit(texto_nome, (txt_x, txt_y))
            
        elif self.estado == 'mouse' or self.estado == 'braco':
            if self.estado == 'mouse':
                if rect_braco_colisao.collidepoint(pos_mouse):
                    x_relativo = pos_mouse[0] - self.offset_x
                    casa_atual = int(x_relativo // self.espaco_casas)
                    casa_atual = max(0, min(casa_atual, self.num_casas_total - self.num_casas_desenho))
                    
                    self.rect_braco.x = self.offset_x + (casa_atual * self.espaco_casas) - self.padding_x
                    self.rect_braco.y = rect_braco_colisao.y - self.padding_y
                    
                    pygame.draw.rect(tela, (0, 255, 0), self.rect_braco, 4)
                else:
                    self.rect_braco.center = pos_mouse
                    pygame.draw.rect(tela, (255, 0, 0), self.rect_braco, 4)

            tela.blit(self.imagem_braco, self.rect_braco.topleft)