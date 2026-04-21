import pygame

class DesenhoEscala:
    def __init__(self, x_painel, y_painel, num_casas_desenho, espaco_casas, espaco_cordas, altura_braco, offset_x, num_casas_total, padrao):
        self.x_original = x_painel
        self.y_original = y_painel
        
        # Variáveis de Grid
        self.espaco_casas = espaco_casas
        self.offset_x = offset_x
        self.num_casas_total = num_casas_total
        self.num_casas_desenho = num_casas_desenho
        
        self.largura = espaco_casas * num_casas_desenho
        self.altura = altura_braco
        
        # 1. Cria o "Fundo" da caixa (Translúcido)
        self.imagem = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        self.imagem.fill((0, 150, 255, 60)) # Azul bem suave
        pygame.draw.rect(self.imagem, (255, 255, 255), self.imagem.get_rect(), 2) # Borda da caixa
        
        # 2. Desenha as bolinhas direto na imagem baseando-se na Matriz (padrao)
        raio = 14
        for corda in range(7):
            for casa_interna in range(num_casas_desenho):
                if padrao[corda][casa_interna] == 1:
                    # Calcula o centro exato da casa dentro do desenho
                    x_bolinha = (casa_interna * espaco_casas) + (espaco_casas / 2)
                    # Calcula a altura exata da corda
                    y_bolinha = self.altura - (corda * espaco_cordas)
                    
                    pygame.draw.circle(self.imagem, (255, 255, 255), (int(x_bolinha), int(y_bolinha)), raio)
                    pygame.draw.circle(self.imagem, (0, 0, 0), (int(x_bolinha), int(y_bolinha)), raio, 2)
        
        self.rect = self.imagem.get_rect(topleft=(x_painel, y_painel))
        self.estado = 'painel' # 'painel', 'mouse', 'braco'

    def tratar_clique(self, pos_mouse, rect_braco):
        if self.estado == 'painel':
            if self.rect.collidepoint(pos_mouse):
                self.estado = 'mouse'
                return True

        elif self.estado == 'braco':
            if self.rect.collidepoint(pos_mouse):
                self.estado = 'painel'
                self.rect.topleft = (self.x_original, self.y_original)
                return True

        elif self.estado == 'mouse':
            if rect_braco.collidepoint(pos_mouse):
                self.estado = 'braco'
                # O snapping visual no atualizar_e_desenhar já garante a posição exata
            else:
                self.estado = 'painel'
                self.rect.topleft = (self.x_original, self.y_original)
            return True
            
        return False

    def atualizar_e_desenhar(self, tela, pos_mouse, rect_braco):
        if self.estado == 'mouse':
            if rect_braco.collidepoint(pos_mouse):
                # --- LÓGICA DE SNAPPING (GRADE) ---
                x_relativo = pos_mouse[0] - self.offset_x
                casa_atual = int(x_relativo // self.espaco_casas)
                
                # Impede que a caixa saia pelo final do braço
                casa_atual = max(0, min(casa_atual, self.num_casas_total - self.num_casas_desenho))
                
                # Trava a posição X exatamente na linha da casa
                self.rect.x = self.offset_x + (casa_atual * self.espaco_casas)
                # Trava a posição Y exatamente no braço
                self.rect.y = rect_braco.y
                
                # Feedback visual de sucesso (Verde)
                pygame.draw.rect(tela, (0, 255, 0), self.rect, 4)
            else:
                # Segue o mouse livremente
                self.rect.center = pos_mouse
                pygame.draw.rect(tela, (255, 0, 0), self.rect, 4) # Vermelho (Fora do braço)

        tela.blit(self.imagem, self.rect.topleft)