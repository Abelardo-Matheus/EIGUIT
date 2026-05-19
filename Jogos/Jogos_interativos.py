import pygame
import os
import sys
# Importamos os jogos
from Jogos.acerte_a_nota import AcerteANota
from Jogos.jogo2 import RhythmHero

class GerenciadorJogos:
    def __init__(self):
        self.jogos = [
            {"nome": "Acerte a Nota", "id": "acerte_a_nota"},
            {"nome": "Rhythm Hero", "id": "jogo2"},
            {"nome": "Em breve...", "id": "jogo3"},
            {"nome": "Em breve...", "id": "jogo4"}
        ]
        
        # Botões do Menu (Box)
        self.botoes_menu = []
        self.btn_voltar = pygame.Rect(20, 20, 50, 40)
        
        # Estado do jogo atual
        self.jogo_instancia = None
        self.jogo_id_ativo = None

    def desenhar_aba_jogos(self, tela, x_base, y_base, fonte_ui):
        """Desenha a lista de 4 jogos dentro da box azul"""
        self.botoes_menu.clear()
        largura_btn = 180
        altura_btn = 40
        espacamento = 15
        
        for i, jogo in enumerate(self.jogos):
            # Organiza em 2 colunas
            col = i % 2
            lin = i // 2
            x = x_base + 20 + (col * (largura_btn + espacamento))
            y = y_base + 40 + (lin * (altura_btn + espacamento))
            
            rect = pygame.Rect(x, y, largura_btn, altura_btn)
            self.botoes_menu.append((rect, jogo["id"]))
            
            # Cor diferenciada se o jogo estiver "Em breve..."
            cor_bg = (0, 120, 215) if jogo["id"] in ["acerte_a_nota", "jogo2"] else (80, 80, 80)
            pygame.draw.rect(tela, cor_bg, rect, border_radius=5)
            
            txt = fonte_ui.render(jogo["nome"], True, (255, 255, 255))
            tela.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

    def desenhar_tela_jogo(self, tela, largura_tela, altura_tela, estado, meu_gravador=None, configs=None):
        """Gerencia qual tela de jogo desenhar"""
        if self.jogo_instancia:
            # Repassa o estado, gravador e configurações para o jogo específico
            # Checa se o jogo aceita configs (como o Rhythm Hero)
            import inspect
            sig = inspect.signature(self.jogo_instancia.desenhar)
            params = sig.parameters
            
            kwargs = {}
            if 'meu_gravador' in params: kwargs['meu_gravador'] = meu_gravador
            if 'configs' in params: kwargs['configs'] = configs
            
            # Passamos o estado como primeiro argumento posicional após tela, largura, altura
            self.jogo_instancia.desenhar(tela, largura_tela, altura_tela, estado, **kwargs)
        
        # Botão Voltar Universal
        pygame.draw.rect(tela, (200, 50, 50), self.btn_voltar, border_radius=5)
        cx, cy = self.btn_voltar.center
        pygame.draw.polygon(tela, (255, 255, 255), [(cx-10, cy), (cx+5, cy-10), (cx+5, cy+10)])


    def tratar_clique_tela_jogo(self, pos_mouse, estado, meu_gravador=None):
        """Gerencia os cliques enquanto a tela cheia do jogo está aberta"""
        if self.btn_voltar.collidepoint(pos_mouse):
            estado.tela_jogo_ativa = False
            self.jogo_instancia = None
            return True
            
        # Repassa o clique e o gravador para o jogo atual!
        if self.jogo_instancia and hasattr(self.jogo_instancia, 'tratar_clique'):
            return self.jogo_instancia.tratar_clique(pos_mouse, meu_gravador)
            
        return False

    def tratar_clique_aba(self, pos_mouse, estado):
        """Detecta qual jogo foi escolhido no menu"""
        for rect, jogo_id in self.botoes_menu:
            if rect.collidepoint(pos_mouse):
                self.jogo_id_ativo = jogo_id
                # Inicializa o jogo escolhido
                if jogo_id == "acerte_a_nota":
                    self.jogo_instancia = AcerteANota()
                elif jogo_id == "jogo2":
                    self.jogo_instancia = RhythmHero()
                else:
                    self.jogo_instancia = None # Outros jogos em branco por enquanto
                
                if self.jogo_instancia:
                    estado.tela_jogo_ativa = True
                    return True
        return False

    