import pygame
import math
import Modulos.escalas as escalas
from Core.constantes_ui import *
from Interface.Componentes.config_componentes import CARDS_ESC_INTERNA, CARDS_TEXTO_OFFSET_Y

class DesenhoEscala:
    """
        Como funciona: Define a estrutura e estado do componente 'DesenhoEscala'.
        Para que serve: Atua como o modelo principal para instâncias de 'DesenhoEscala'.
        Onde é usada: Chamado a partir do módulo ou classe base de 'ui_componentes'.
    """

    def __init__(self, x_painel, y_painel, espaco_casas, espaco_cordas, altura_braco, offset_x, num_casas_total, padrao, nome='', cor_base=(255, 255, 255)):
        """
            Como funciona: Inicializa os atributos e o estado inicial da instância.
            Para que serve: Prepara o objeto para ser utilizado no ciclo de vida da aplicação.
            Onde é usada: Chamado a partir do módulo ou classe base de 'ui_componentes'.
        """
        self.nome = nome
        self.aba = 0
        self.sub_aba = 0
        self.x_original = x_painel
        self.y_original = y_painel
        self.y_relativo = 0
        self.num_casas_total = num_casas_total
        self.padrao = padrao
        self.cor_base = cor_base
        self.num_casas_desenho = len(padrao[0])
        self.padding_x = 5
        self.padding_y = 20
        self.estado = 'painel'
        self.casa_atual = 0
        self.last_w_braco = 0
        self.last_h_braco = 0
        self.espaco_casas = espaco_casas
        self.reconstruir_superficies(espaco_casas, espaco_cordas, altura_braco)
        self.rect_painel = self.imagem_painel.get_rect(topleft=(x_painel, y_painel))

    def reconstruir_superficies(self, espaco_casas, espaco_cordas, altura_braco):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'reconstruir superficies'.
            Para que serve: Realiza as tarefas fundamentais de 'reconstruir superficies' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'reconstruir superficies'.
        """
        self.espaco_casas = espaco_casas
        self.largura_real = espaco_casas * self.num_casas_desenho
        self.altura_real = altura_braco
        w_surf = int(self.largura_real + self.padding_x * 2)
        h_surf = int(self.altura_real + self.padding_y * 2)
        self.imagem_braco = pygame.Surface((w_surf, h_surf))
        self.imagem_braco.fill((0, 0, 0))
        COR_TRANSPARENTE = (255, 255, 255)
        self.imagem_braco.set_colorkey(COR_TRANSPARENTE)
        pygame.draw.rect(self.imagem_braco, (255, 255, 255), self.imagem_braco.get_rect(), 2)
        COR_DESTAQUE_TONICA = (255, 80, 80)
        COR_NORMAL = self.cor_base
        raio = max(10, min(18, int(espaco_casas * 0.42)))
        for corda in range(7):
            for casa_interna in range(self.num_casas_desenho):
                valor_matriz = self.padrao[corda][casa_interna]
                if valor_matriz in [1, 2]:
                    x_bolinha = self.padding_x + casa_interna * espaco_casas + espaco_casas / 2
                    y_bolinha = self.padding_y + self.altura_real - corda * espaco_cordas
                    pygame.draw.circle(self.imagem_braco, COR_TRANSPARENTE, (int(x_bolinha), int(y_bolinha)), raio)
                    if valor_matriz == 2:
                        pygame.draw.circle(self.imagem_braco, COR_DESTAQUE_TONICA, (int(x_bolinha), int(y_bolinha)), raio, max(2, int(raio // 3.5)))
                    else:
                        pygame.draw.circle(self.imagem_braco, COR_NORMAL, (int(x_bolinha), int(y_bolinha)), raio, max(1, int(raio // 5)))
        escala = CARDS_ESC_INTERNA
        w_painel = int(w_surf * escala)
        h_painel = int(h_surf * escala)
        self.imagem_painel = pygame.transform.scale(self.imagem_braco, (w_painel, h_painel))
        self.imagem_painel.set_colorkey(COR_TRANSPARENTE)
        self.rect_braco = self.imagem_braco.get_rect()

    def tratar_clique(self, pos_mouse, rect_braco_colisao):
        """
            Como funciona: Verifica colisões e processa inputs do mouse/teclado.
            Para que serve: Mapeia ações do usuário para atualizações de estado.
            Onde é usada: Chamado a partir do módulo ou classe base de 'ui_componentes'.
        """
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
        """
            Como funciona: Recalcula dimensões, estados e processa alterações temporais.
            Para que serve: Garante que os dados e a interface reflitam as últimas mudanças.
            Onde é usada: Chamado a partir do módulo ou classe base de 'ui_componentes'.
        """
        scroll = getattr(self, 'scroll_offset', 0)
        if self.estado == 'painel':
            self.imagem_painel.set_alpha(nivel_alpha)
            y_desenho_rolado = self.rect_painel.y - scroll
            tela.blit(self.imagem_painel, (self.rect_painel.x, y_desenho_rolado))
            if self.nome != '':
                texto_nome = fonte_pequena.render(self.nome, True, BRANCO)
                txt_x = self.rect_painel.centerx - texto_nome.get_width() / 2
                txt_y = y_desenho_rolado + CARDS_TEXTO_OFFSET_Y
                tela.blit(texto_nome, (txt_x, txt_y))
        elif self.estado in ['mouse', 'braco']:
            if rect_braco_colisao.width != self.last_w_braco or rect_braco_colisao.height != self.last_h_braco:
                self.last_w_braco = rect_braco_colisao.width
                self.last_h_braco = rect_braco_colisao.height
                novo_espaco_casas = rect_braco_colisao.width / self.num_casas_total
                novo_espaco_cordas = rect_braco_colisao.height / 6
                self.reconstruir_superficies(novo_espaco_casas, novo_espaco_cordas, rect_braco_colisao.height)
            self.imagem_braco.set_alpha(nivel_alpha)
            x_guit_real = rect_braco_colisao.x
            y_guit_real = rect_braco_colisao.y
            if self.estado == 'mouse':
                if rect_braco_colisao.collidepoint(pos_mouse):
                    x_relativo = pos_mouse[0] - x_guit_real
                    self.casa_atual = int(x_relativo // self.espaco_casas)
                    self.casa_atual = max(0, min(self.casa_atual, self.num_casas_total - self.num_casas_desenho))
                    self.rect_braco.x = x_guit_real + self.casa_atual * self.espaco_casas - self.padding_x
                    self.rect_braco.y = y_guit_real - self.padding_y
                    pygame.draw.rect(tela, (0, 255, 0), self.rect_braco, 4)
                else:
                    self.rect_braco.center = pos_mouse
                    pygame.draw.rect(tela, (255, 0, 0), self.rect_braco, 4)
            elif self.estado == 'braco':
                self.rect_braco.x = x_guit_real + self.casa_atual * self.espaco_casas - self.padding_x
                self.rect_braco.y = y_guit_real - self.padding_y
            tela.blit(self.imagem_braco, self.rect_braco.topleft)