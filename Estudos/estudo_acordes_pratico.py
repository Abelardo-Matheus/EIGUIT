import pygame
import random
from config.theme import *
from config.ui_metrics import *
from config.app_settings import *
import core.modulos.escalas as escalas
from config.app_settings import lista_afinacoes

class EstudoAcordesPratico:
    """
        Como funciona: Define a estrutura e estado do componente 'EstudoAcordesPratico'.
        Para que serve: Controla a lógica e interação da tela de estudo prático.
        Onde é usada: Chamado a partir do módulo ou classe base de 'estudo_acordes_pratico'.
    """

    def __init__(self):
        """
            Como funciona: Inicializa os atributos e o estado inicial da instância.
            Para que serve: Prepara o objeto para ser utilizado no ciclo de vida da aplicação.
            Onde é usada: Chamado a partir do módulo ou classe base de 'estudo_acordes_pratico'.
        """
        self.inicializado = False
        self.acertos = 0
        self.total = 0
        self.acorde_alvo = ''
        self.notas_alvo = []
        self.feedback = 'Toque o acorde indicado...'
        self.cor_feedback = BRANCO
        self.tempo_feedback = 0
        self.acerto_detectado = False
        import core.modulos.modulos_acordes as mod_acordes
        self.acordes_disponiveis = {'C Maior': {'notas': ['C', 'E', 'G'], 'shape': mod_acordes.TRIADE_C_MAIOR}, 'A Maior': {'notas': ['A', 'C#', 'E'], 'shape': mod_acordes.TRIADE_A_MAIOR}, 'G Maior': {'notas': ['G', 'B', 'D'], 'shape': mod_acordes.TRIADE_G_MAIOR}, 'E Maior': {'notas': ['E', 'G#', 'B'], 'shape': mod_acordes.TRIADE_E_MAIOR}, 'D Maior': {'notas': ['D', 'F#', 'A'], 'shape': mod_acordes.TRIADE_D_MAIOR}, 'A Menor': {'notas': ['A', 'C', 'E'], 'shape': mod_acordes.TRIADE_A_MENOR}, 'E Menor': {'notas': ['E', 'G', 'B'], 'shape': mod_acordes.TRIADE_E_MENOR}, 'D Menor': {'notas': ['D', 'F', 'A'], 'shape': [[0, 0, 1, 0], [0, 0, 0, 1], [1, 0, 0, 0], [2, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [0, 0, 1, 0]]}}
        self.nomes_acordes = list(self.acordes_disponiveis.keys())

    def inicializar_questao(self, estado):
        """
            Como funciona: Prepara variáveis e limpa dados de sessões anteriores.
            Para que serve: Configura o ambiente necessário para início de uma nova tarefa.
            Onde é usada: Chamado a partir do módulo ou classe base de 'estudo_acordes_pratico'.
        """
        self.acorde_alvo = random.choice(self.nomes_acordes)
        self.notas_alvo = self.acordes_disponiveis[self.acorde_alvo]['notas']
        self.feedback = f'Toque {self.acorde_alvo}'
        self.cor_feedback = BRANCO
        self.acerto_detectado = False
        self.inicializado = True

    def desenhar(self, tela, estado, fontes, meio_x, meio_y, cam_x, cam_y):
        """
            Como funciona: Utiliza funções de renderização do Pygame para desenhar na tela.
            Para que serve: Apresenta o elemento visual 'desenhar' na interface gráfica.
            Onde é usada: Chamado a partir do módulo ou classe base de 'estudo_acordes_pratico'.
        """
        if not self.inicializado:
            self.inicializar_questao(estado)
        txt_tit = fontes['titulo'].render(f'Objetivo: Tocar o acorde {self.acorde_alvo}', True, (0, 160, 255))
        tela.blit(txt_tit, (meio_x - txt_tit.get_width() // 2, cam_y + 100))
        cor_f = self.cor_feedback
        if self.acerto_detectado:
            cor_f = (100, 255, 100)
        txt_feed = fontes['titulo'].render(self.feedback, True, cor_f)
        tela.blit(txt_feed, (meio_x - txt_feed.get_width() // 2, cam_y + 150))
        shape = self.acordes_disponiveis[self.acorde_alvo]['shape']
        num_cordas = 7
        espaco_cordas = 35
        espaco_casas = 55
        altura_shape = (num_cordas - 1) * espaco_cordas
        largura_shape = 5 * espaco_casas
        x_shape = meio_x - largura_shape // 2
        y_shape = meio_y - 120
        pygame.draw.rect(tela, (60, 35, 25), (x_shape, y_shape, largura_shape, altura_shape), border_radius=5)
        for i in range(6):
            lx = x_shape + i * espaco_casas
            pygame.draw.line(tela, (180, 180, 180), (lx, y_shape), (lx, y_shape + altura_shape), 2)
        for i in range(num_cordas):
            ly = y_shape + i * espaco_cordas
            pygame.draw.line(tela, (200, 200, 200), (x_shape, ly), (x_shape + largura_shape, ly), 1)
            if i < len(shape):
                for casa_idx, val in enumerate(shape[i]):
                    if val in [1, 2]:
                        bx = x_shape + casa_idx * espaco_casas + espaco_casas // 2
                        by = y_shape + altura_shape - i * espaco_cordas
                        cor_nota = (255, 100, 100) if val == 2 else BRANCO
                        pygame.draw.circle(tela, cor_nota, (int(bx), int(by)), 15)
                        pygame.draw.circle(tela, (0, 0, 0), (int(bx), int(by)), 15, 2)
        notas_atuais = getattr(estado, 'notas_detectadas_ia', [])
        if notas_atuais:
            txt_detect = fontes['pequena'].render(f"Detectado: {', '.join(notas_atuais)}", True, (200, 200, 200))
            tela.blit(txt_detect, (meio_x - txt_detect.get_width() // 2, y_shape + altura_shape + 40))
        if not self.acerto_detectado and notas_atuais:
            match_count = 0
            for n_alvo in self.notas_alvo:
                if any((escalas.equivalencia_notas(n_alvo, n_det) for n_det in notas_atuais)):
                    match_count += 1
            if match_count >= 2:
                self.acerto_detectado = True
                self.acertos += 1
                self.total += 1
                self.feedback = 'MUITO BEM! Acorde detectado!'
                self.tempo_feedback = pygame.time.get_ticks() + 2000
        if self.acerto_detectado and pygame.time.get_ticks() > self.tempo_feedback:
            self.inicializar_questao(estado)

    def tratar_cliques(self, pos, estado):
        """
            Como funciona: Verifica colisões e processa inputs do mouse/teclado.
            Para que serve: Mapeia ações do usuário para atualizações de estado.
            Onde é usada: Chamado a partir do módulo ou classe base de 'estudo_acordes_pratico'.
        """
        return False