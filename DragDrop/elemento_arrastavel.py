import pygame

class ElementoArrastavel:
    def __init__(self, x_inicial, y_inicial, largura, altura):
        self.x = x_inicial
        self.y = y_inicial
        self.largura = largura
        self.altura = altura
        
        self.arrastando = False
        self.redimensionando = False
        self.canto_ativo = None # Guarda em qual quadradinho você clicou ('TL', 'TR', 'BL', 'BR')
        
        self.mouse_inicio_x = 0
        self.mouse_inicio_y = 0
        
        self.tamanho_minimo = 80 # Não deixa a janela sumir ou ficar negativa
        self.rect_caixa = pygame.Rect(self.x, self.y, self.largura, self.altura)

    def atualizar_dimensoes(self, w, h):
        self.largura = w
        self.altura = h
        self.rect_caixa.size = (w, h)

    def obter_cantos(self, margem=0):
        """Calcula os 4 quadradinhos nos cantos exatos da caixa"""
        r = pygame.Rect(self.x - margem, self.y - margem, self.largura + margem*2, self.altura + margem*2)
        s = 14 # Tamanho do quadradinho de redimensionamento
        offset = s // 2
        
        return {
            'TL': pygame.Rect(r.left - offset, r.top - offset, s, s),       # Top-Left (Cima-Esq)
            'TR': pygame.Rect(r.right - offset, r.top - offset, s, s),      # Top-Right (Cima-Dir)
            'BL': pygame.Rect(r.left - offset, r.bottom - offset, s, s),    # Bottom-Left (Baixo-Esq)
            'BR': pygame.Rect(r.right - offset, r.bottom - offset, s, s)    # Bottom-Right (Baixo-Dir)
        }

    def processar_eventos_mouse(self, evento, margem_clique=0):
        if not hasattr(evento, 'pos'):
            return False
            
        pos_mouse = evento.pos
        cantos = self.obter_cantos(margem_clique)
        rect_total = pygame.Rect(self.x - margem_clique, self.y - margem_clique, self.largura + margem_clique*2, self.altura + margem_clique*2)

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            # 1. Checa a colisão com os quadradinhos PRIMEIRO!
            for nome, rect_canto in cantos.items():
                if rect_canto.collidepoint(pos_mouse):
                    self.redimensionando = True
                    self.canto_ativo = nome
                    self.mouse_inicio_x = pos_mouse[0]
                    self.mouse_inicio_y = pos_mouse[1]
                    return True
                    
            # 2. Se não clicou nos cantos, checa o corpo para Arrastar
            if rect_total.collidepoint(pos_mouse):
                self.arrastando = True
                self.mouse_inicio_x = pos_mouse[0] - self.x
                self.mouse_inicio_y = pos_mouse[1] - self.y
                return True

        elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            self.arrastando = False
            self.redimensionando = False
            self.canto_ativo = None

        elif evento.type == pygame.MOUSEMOTION:
            if self.redimensionando:
                dx = pos_mouse[0] - self.mouse_inicio_x
                dy = pos_mouse[1] - self.mouse_inicio_y
                
                nova_largura = self.largura
                nova_altura = self.altura
                novo_x = self.x
                novo_y = self.y

                # Lógica matemática pesada para empurrar os cantos certos
                if self.canto_ativo == 'TL':
                    nova_largura -= dx
                    nova_altura -= dy
                    novo_x += dx
                    novo_y += dy
                elif self.canto_ativo == 'TR':
                    nova_largura += dx
                    nova_altura -= dy
                    novo_y += dy
                elif self.canto_ativo == 'BL':
                    nova_largura -= dx
                    nova_altura += dy
                    novo_x += dx
                elif self.canto_ativo == 'BR':
                    nova_largura += dx
                    nova_altura += dy

                # Aplica as medidas apenas se a caixa não bugar
                if nova_largura >= self.tamanho_minimo:
                    self.largura = nova_largura
                    self.x = novo_x
                    self.mouse_inicio_x = pos_mouse[0]
                if nova_altura >= self.tamanho_minimo:
                    self.altura = nova_altura
                    self.y = novo_y
                    self.mouse_inicio_y = pos_mouse[1]

                self.rect_caixa = pygame.Rect(self.x, self.y, self.largura, self.altura)
                return True

            elif self.arrastando:
                self.x = pos_mouse[0] - self.mouse_inicio_x
                self.y = pos_mouse[1] - self.mouse_inicio_y
                self.rect_caixa = pygame.Rect(self.x, self.y, self.largura, self.altura)
                return True

        return False

    def desenhar_caixa_selecao(self, tela, margem=0):
        # A caixa muda de cor se você estiver arrastando vs redimensionando
        rect_total = pygame.Rect(self.x - margem, self.y - margem, self.largura + margem*2, self.altura + margem*2)
        cor_caixa = (0, 255, 255) if self.redimensionando else ((0, 255, 0) if self.arrastando else (255, 255, 0))
        
        pygame.draw.rect(tela, cor_caixa, rect_total, width=2, border_radius=5)
        
        # Desenha os quadradinhos 
        cantos = self.obter_cantos(margem)
        for nome, rect_canto in cantos.items():
            cor_canto = (255, 100, 100) if self.canto_ativo == nome else (255, 255, 255)
            pygame.draw.rect(tela, cor_canto, rect_canto)
            pygame.draw.rect(tela, (0, 0, 0), rect_canto, width=1) # Borda do quadradinho