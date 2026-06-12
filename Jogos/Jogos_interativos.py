import pygame
import os
import sys
from Jogos.acerte_a_nota import AcerteANota
from Jogos.jogo2 import RhythmHero

class GerenciadorJogos:
    """
        Como funciona: Mantém instâncias ativas e delega tarefas aos submódulos de 'GerenciadorJogos'.
        Para que serve: Orquestra recursos e o ciclo de vida do módulo.
        Onde é usada: Chamado a partir do módulo ou classe base de 'Jogos_interativos'.
    """

    def __init__(self):
        """
            Como funciona: Inicializa os atributos e o estado inicial da instância.
            Para que serve: Prepara o objeto para ser utilizado no ciclo de vida da aplicação.
            Onde é usada: Chamado a partir do módulo ou classe base de 'Jogos_interativos'.
        """
        self.jogos = [{'nome': 'Acerte a Nota', 'id': 'acerte_a_nota'}, {'nome': 'Rhythm Hero', 'id': 'jogo2'}, {'nome': 'Em breve...', 'id': 'jogo3'}, {'nome': 'Em breve...', 'id': 'jogo4'}]
        self.botoes_menu = []
        self.btn_voltar = pygame.Rect(20, 20, 50, 40)
        self.jogo_instancia = None
        self.jogo_id_ativo = None

    def desenhar_aba_jogos(self, tela, x_base, y_base, fonte_ui):
        """
            Como funciona: Utiliza funções de renderização do Pygame para desenhar na tela.
            Para que serve: Apresenta o elemento visual 'aba jogos' na interface gráfica.
            Onde é usada: Chamado a partir do módulo ou classe base de 'Jogos_interativos'.
        """
        self.botoes_menu.clear()
        largura_btn = 180
        altura_btn = 40
        espacamento = 15
        for i, jogo in enumerate(self.jogos):
            col = i % 2
            lin = i // 2
            x = x_base + 20 + col * (largura_btn + espacamento)
            y = y_base + 40 + lin * (altura_btn + espacamento)
            rect = pygame.Rect(x, y, largura_btn, altura_btn)
            self.botoes_menu.append((rect, jogo['id']))
            cor_bg = (0, 120, 215) if jogo['id'] in ['acerte_a_nota', 'jogo2'] else (80, 80, 80)
            pygame.draw.rect(tela, cor_bg, rect, border_radius=5)
            txt = fonte_ui.render(jogo['nome'], True, (255, 255, 255))
            tela.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

    def desenhar_tela_jogo(self, tela, largura_tela, altura_tela, estado, meu_gravador=None, configs=None):
        """
            Como funciona: Utiliza funções de renderização do Pygame para desenhar na tela.
            Para que serve: Apresenta o elemento visual 'tela jogo' na interface gráfica.
            Onde é usada: Chamado a partir do módulo ou classe base de 'Jogos_interativos'.
        """
        if self.jogo_instancia:
            import inspect
            sig = inspect.signature(self.jogo_instancia.desenhar)
            params = sig.parameters
            kwargs = {}
            if 'meu_gravador' in params:
                kwargs['meu_gravador'] = meu_gravador
            if 'configs' in params:
                kwargs['configs'] = configs
            self.jogo_instancia.desenhar(tela, largura_tela, altura_tela, estado, **kwargs)
        
        # Botão voltar agora é global na Top Bar.

    def tratar_clique_tela_jogo(self, pos_mouse, estado, meu_gravador=None):
        """
            Como funciona: Verifica colisões e processa inputs do mouse/teclado.
            Para que serve: Mapeia ações do usuário para atualizações de estado.
            Onde é usada: Chamado a partir do módulo ou classe base de 'Jogos_interativos'.
        """
        if self.jogo_instancia and hasattr(self.jogo_instancia, 'tratar_clique'):
            return self.jogo_instancia.tratar_clique(pos_mouse, meu_gravador)
        return False

    def tratar_clique_aba(self, pos_mouse, estado):
        """
            Como funciona: Verifica colisões e processa inputs do mouse/teclado.
            Para que serve: Mapeia ações do usuário para atualizações de estado.
            Onde é usada: Chamado a partir do módulo ou classe base de 'Jogos_interativos'.
        """
        for rect, jogo_id in self.botoes_menu:
            if rect.collidepoint(pos_mouse):
                self.jogo_id_ativo = jogo_id
                if jogo_id == 'acerte_a_nota':
                    self.jogo_instancia = AcerteANota()
                elif jogo_id == 'jogo2':
                    self.jogo_instancia = RhythmHero()
                else:
                    self.jogo_instancia = None
                if self.jogo_instancia:
                    estado.tela_jogo_ativa = True
                    return True
        return False