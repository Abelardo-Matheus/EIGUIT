import pygame

class ElementoArrastavel:
    """
        Como funciona: Define a estrutura e estado do componente 'ElementoArrastavel'.
        Para que serve: Atua como o modelo principal para instâncias de 'ElementoArrastavel'.
        Onde é usada: Chamado a partir do módulo ou classe base de 'elemento_arrastavel'.
    """

    def __init__(self, x_inicial, y_inicial, largura, altura):
        """
            Como funciona: Inicializa os atributos e o estado inicial da instância.
            Para que serve: Prepara o objeto para ser utilizado no ciclo de vida da aplicação.
            Onde é usada: Chamado a partir do módulo ou classe base de 'elemento_arrastavel'.
        """
        self.x = x_inicial
        self.y = y_inicial
        self.largura = largura
        self.altura = altura
        self.arrastando = False
        self.redimensionando = False
        self.canto_ativo = None
        self.mouse_inicio_x = 0
        self.mouse_inicio_y = 0
        self.tamanho_minimo = 80
        self.rect_caixa = pygame.Rect(self.x, self.y, self.largura, self.altura)

    def atualizar_dimensoes(self, w, h):
        """
            Como funciona: Recalcula dimensões, estados e processa alterações temporais.
            Para que serve: Garante que os dados e a interface reflitam as últimas mudanças.
            Onde é usada: Chamado a partir do módulo ou classe base de 'elemento_arrastavel'.
        """
        self.largura = w
        self.altura = h
        self.rect_caixa.size = (w, h)

    def obter_cantos(self, margem=0):
        """
            Como funciona: Acessa e formata dados internos ou de configuração.
            Para que serve: Retorna as informações solicitadas sobre 'cantos'.
            Onde é usada: Chamado a partir do módulo ou classe base de 'elemento_arrastavel'.
        """
        r = pygame.Rect(self.x - margem, self.y - margem, self.largura + margem * 2, self.altura + margem * 2)
        s = 14
        offset = s // 2
        return {'TL': pygame.Rect(r.left - offset, r.top - offset, s, s), 'TR': pygame.Rect(r.right - offset, r.top - offset, s, s), 'BL': pygame.Rect(r.left - offset, r.bottom - offset, s, s), 'BR': pygame.Rect(r.right - offset, r.bottom - offset, s, s)}

    def processar_eventos_mouse(self, evento, margem_clique=0):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'processar eventos mouse'.
            Para que serve: Realiza as tarefas fundamentais de 'processar eventos mouse' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'processar eventos mouse'.
        """
        if not hasattr(evento, 'pos'):
            return False
        pos_mouse = evento.pos
        cantos = self.obter_cantos(margem_clique)
        rect_total = pygame.Rect(self.x - margem_clique, self.y - margem_clique, self.largura + margem_clique * 2, self.altura + margem_clique * 2)
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for nome, rect_canto in cantos.items():
                if rect_canto.collidepoint(pos_mouse):
                    self.redimensionando = True
                    self.canto_ativo = nome
                    self.mouse_inicio_x = pos_mouse[0]
                    self.mouse_inicio_y = pos_mouse[1]
                    return True
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
                
                # Armazenar estado anterior para rollback se necessário
                antigo_x, antigo_y = self.x, self.y
                antiga_w, antiga_h = self.largura, self.altura
                
                if 'T' in self.canto_ativo:
                    self.altura -= dy
                    self.y += dy
                if 'B' in self.canto_ativo:
                    self.altura += dy
                if 'L' in self.canto_ativo:
                    self.largura -= dx
                    self.x += dx
                if 'R' in self.canto_ativo:
                    self.largura += dx
                
                # Validar tamanho mínimo e limites de tela (opcional)
                if self.largura < self.tamanho_minimo:
                    self.largura = antiga_w
                    self.x = antigo_x
                else:
                    self.mouse_inicio_x = pos_mouse[0]
                    
                if self.altura < 30: # Altura mínima para botões
                    self.altura = antiga_h
                    self.y = antigo_y
                else:
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
        """
            Como funciona: Utiliza funções de renderização do Pygame para desenhar na tela.
            Para que serve: Apresenta o elemento visual 'caixa selecao' na interface gráfica.
            Onde é usada: Chamado a partir do módulo ou classe base de 'elemento_arrastavel'.
        """
        AZUL_SOFT = (0, 163, 255)
        VERDE_SOFT = (46, 204, 113)
        BRANCO = (255, 255, 255)
        rect_total = pygame.Rect(self.x - margem, self.y - margem, self.largura + margem * 2, self.altura + margem * 2)
        cor_caixa = AZUL_SOFT if self.redimensionando or self.arrastando else (150, 150, 150)
        largura_linha = 2 if self.redimensionando or self.arrastando else 1
        pygame.draw.rect(tela, cor_caixa, rect_total, width=largura_linha, border_radius=6)
        cantos = self.obter_cantos(margem)
        for nome, rect_canto in cantos.items():
            pygame.draw.circle(tela, BRANCO, rect_canto.center, 5)
            pygame.draw.circle(tela, cor_caixa, rect_canto.center, 5, width=2)
            if self.canto_ativo == nome:
                pygame.draw.circle(tela, AZUL_SOFT, rect_canto.center, 3)