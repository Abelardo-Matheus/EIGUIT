import pygame
import math
import core.modulos.escalas as escalas
from config.theme import *
from config.ui_metrics import *
from config.app_settings import *
from ui.components.config_componentes import CARDS_ESC_INTERNA, CARDS_TEXTO_OFFSET_Y
from config.design_system import TEMA, ds

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
        self.padding_y = 25
        self.estado = 'painel'
        self.casa_atual = 0
        self.last_w_braco = 0
        self.last_h_braco = 0
        self.espaco_casas = espaco_casas
        self.reconstruir_superficies(espaco_casas, espaco_cordas, altura_braco)
        self.rect_painel = self.imagem_painel.get_rect(topleft=(x_painel, y_painel))

    def reconstruir_superficies(self, espaco_casas, espaco_cordas, altura_braco, atualizar_painel=True):
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
        self.imagem_braco.fill(ds.rgb(TEMA.superficie))
        self._modo_tema_render = TEMA.modo
        
        # Cor de colorkey (não usamos branco pois as notas podem ser brancas)
        COR_CK = (1, 1, 1) 
        self.imagem_braco.set_colorkey(COR_CK)
        self.imagem_braco.fill(COR_CK)
        
        # Desenhar "Braço" do card (fundo escuro - Premium Dark)
        # Aumentamos o tamanho vertical (expansao_y) para tampar as bolinhas do braço da guitarra 
        expansao_y = 22
        rect_card = pygame.Rect(self.padding_x, self.padding_y - expansao_y, self.largura_real, self.altura_real + expansao_y * 2)
        pygame.draw.rect(self.imagem_braco, ds.rgb(TEMA.superficie_alt), rect_card, border_radius=12)
        pygame.draw.rect(self.imagem_braco, ds.rgb(TEMA.borda), rect_card, width=1, border_radius=12)
        
        # Desenhar Trastes
        for c in range(self.num_casas_desenho + 1):
            x_fret = self.padding_x + c * espaco_casas
            pygame.draw.line(self.imagem_braco, ds.rgb(TEMA.traste), (x_fret, self.padding_y), (x_fret, self.padding_y + self.altura_real), 1)
            
        # Desenhar Cordas
        for s in range(6):
            y_string = self.padding_y + self.altura_real - s * espaco_cordas
            pygame.draw.line(self.imagem_braco, ds.rgb(ds.escurecer(TEMA.corda, 0.35)), (self.padding_x, y_string), (self.padding_x + self.largura_real, y_string), 1)

        COR_DESTAQUE_TONICA = ds.rgb(TEMA.alerta)
        COR_NORMAL = self.cor_base
        raio = max(10, min(18, int(espaco_casas * 0.42)))
        
        # Smart Mapping para 6 cordas (trata inconsistências entre matrizes de 6 e 7 linhas)
        matriz_6_cordas = self.padrao
        if len(self.padrao) == 7:
            # Verifica se a primeira linha é redundante ou se a última é
            # Geralmente Row 0 == Row 5 (E strings) ou Row 1 == Row 6
            if self.padrao[0] == self.padrao[5]:
                # Row 0 a 5 são as 6 cordas (EADGBE)
                matriz_6_cordas = self.padrao[:6]
            elif self.padrao[1] == self.padrao[6]:
                # Row 1 a 6 são as 6 cordas
                matriz_6_cordas = self.padrao[1:7]
            else:
                # Fallback: assume as 6 primeiras
                matriz_6_cordas = self.padrao[:6]

        for corda in range(6):
            for casa_interna in range(self.num_casas_desenho):
                valor_matriz = matriz_6_cordas[corda][casa_interna]
                if valor_matriz in [1, 2]:
                    x_bolinha = self.padding_x + casa_interna * espaco_casas + espaco_casas / 2
                    y_bolinha = self.padding_y + self.altura_real - corda * espaco_cordas
                    
                    # Preenche o interior com a cor transparente (fura o fundo cinza)
                    pygame.draw.circle(self.imagem_braco, COR_CK, (int(x_bolinha), int(y_bolinha)), raio)
                    
                    cor_n = COR_DESTAQUE_TONICA if valor_matriz == 2 else COR_NORMAL
                    # Desenha apenas a borda (width=3), contornando o buraco transparente
                    pygame.draw.circle(self.imagem_braco, cor_n, (int(x_bolinha), int(y_bolinha)), raio, 3)

        if atualizar_painel:
            escala = CARDS_ESC_INTERNA
            w_painel = int(w_surf * escala)
            h_painel = int(h_surf * escala)
            self.imagem_painel = pygame.transform.scale(self.imagem_braco, (w_painel, h_painel))
            self.imagem_painel.set_colorkey(COR_CK)
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
                if self.estado != 'painel':
                    self.estado = 'painel'
                    self.ultimo_estado = 'painel'
            return True
        return False

    def atualizar_e_desenhar(self, tela, pos_mouse, rect_braco_colisao, fonte_pequena, nivel_alpha=255, estado=None):
        """
        Como funciona: Recalcula dimensões, estados e processa alterações temporais.
        Para que serve: Garante que os dados e a interface reflitam as últimas mudanças.
        Onde é usada: Chamado a partir do módulo ou classe base de 'ui_componentes'.
        """
        if estado is not None:
            self.num_casas_total = getattr(estado, 'NUM_CASAS', self.num_casas_total)

        # Reconstroi as superficies em cache quando o tema claro/escuro muda
        if getattr(self, '_modo_tema_render', None) != TEMA.modo:
            self.reconstruir_superficies(self.espaco_casas,
                                         self.altura_real / 6 if self.altura_real else 20,
                                         self.altura_real)
            self.escala_atual_painel = None
            
        scroll = getattr(self, 'scroll_offset', 0)
        if self.estado == 'painel':
            self.imagem_painel.set_alpha(nivel_alpha)
            y_desenho_rolado = self.rect_painel.y - scroll
            tela.blit(self.imagem_painel, (self.rect_painel.x, y_desenho_rolado))
            if self.nome != '':
                texto_nome = fonte_pequena.render(self.nome, True, ds.rgb(TEMA.texto))
                txt_x = self.rect_painel.centerx - texto_nome.get_width() / 2
                txt_y = y_desenho_rolado + CARDS_TEXTO_OFFSET_Y
                tela.blit(texto_nome, (txt_x, txt_y))
        elif self.estado in ['mouse', 'braco']:
            if rect_braco_colisao.width != self.last_w_braco or rect_braco_colisao.height != self.last_h_braco or getattr(self, 'ultimo_estado', 'painel') != self.estado:
                self.last_w_braco = rect_braco_colisao.width
                self.last_h_braco = rect_braco_colisao.height
                self.ultimo_estado = self.estado
                novo_espaco_casas = rect_braco_colisao.width / self.num_casas_total
                novo_espaco_cordas = rect_braco_colisao.height / 6
                self.reconstruir_superficies(novo_espaco_casas, novo_espaco_cordas, rect_braco_colisao.height, atualizar_painel=False)
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
                    pygame.draw.rect(tela, ds.rgb(TEMA.verde), self.rect_braco, 4, border_radius=ds.RAIO_MD)
                else:
                    self.rect_braco.center = pos_mouse
                    pygame.draw.rect(tela, ds.rgb(TEMA.alerta), self.rect_braco, 4, border_radius=ds.RAIO_MD)
            elif self.estado == 'braco':
                self.rect_braco.x = x_guit_real + self.casa_atual * self.espaco_casas - self.padding_x
                self.rect_braco.y = y_guit_real - self.padding_y
            tela.blit(self.imagem_braco, self.rect_braco.topleft)