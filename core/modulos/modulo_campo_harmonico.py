import pygame
from core.modulos.modulos_config import *

class CampoHarmonico:
    """
        Como funciona: Define a estrutura e estado do componente 'CampoHarmonico'.
        Para que serve: Atua como o modelo principal para instâncias de 'CampoHarmonico'.
        Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_campo_harmonico'.
    """

    def __init__(self):
        """
            Como funciona: Inicializa os atributos e o estado inicial da instância.
            Para que serve: Prepara o objeto para ser utilizado no ciclo de vida da aplicação.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_campo_harmonico'.
        """
        self.notas_base = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.tonica_campo = 'C'
        self.indice_escala_campo = 0
        self.tonica = 'C'
        self.tipo_escala = 'Maior (Jônio)'
        self.rects_acordes_campo = []
        self.indice_acorde_selecionado = -1
        self.notas_acorde_selecionado = []
        self.escalas_campo = [{'nome': 'Maior (Jônio)', 'int': [0, 2, 4, 5, 7, 9, 11], 'romanos': ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°'], 'qualidades': ['', 'm', 'm', '', '', 'm', 'dim']}, {'nome': 'Menor (Eólio)', 'int': [0, 2, 3, 5, 7, 8, 10], 'romanos': ['i', 'ii°', 'III', 'iv', 'v', 'VI', 'VII'], 'qualidades': ['m', 'dim', '', 'm', 'm', '', '']}, {'nome': 'Dórico', 'int': [0, 2, 3, 5, 7, 9, 10], 'romanos': ['i', 'ii', 'III', 'IV', 'v', 'vi°', 'VII'], 'qualidades': ['m', 'm', '', '', 'm', 'dim', '']}, {'nome': 'Frígio', 'int': [0, 1, 3, 5, 7, 8, 10], 'romanos': ['i', 'II', 'III', 'iv', 'v°', 'VI', 'vii'], 'qualidades': ['m', '', '', 'm', 'dim', '', 'm']}, {'nome': 'Lídio', 'int': [0, 2, 4, 6, 7, 9, 11], 'romanos': ['I', 'II', 'iii', 'iv°', 'V', 'vi', 'vii'], 'qualidades': ['', '', 'm', 'dim', '', 'm', 'm']}, {'nome': 'Mixolídio', 'int': [0, 2, 4, 5, 7, 9, 10], 'romanos': ['I', 'ii', 'iii°', 'IV', 'v', 'vi', 'VII'], 'qualidades': ['', 'm', 'dim', '', 'm', 'm', '']}, {'nome': 'Lócrio', 'int': [0, 1, 3, 5, 6, 8, 10], 'romanos': ['i°', 'II', 'iii', 'iv', 'V', 'VI', 'vii'], 'qualidades': ['dim', '', 'm', 'm', '', '', 'm']}]
        self.rect_tonica_esq = pygame.Rect(0, 0, 0, 0)
        self.rect_tonica_dir = pygame.Rect(0, 0, 0, 0)
        self.rect_escala_esq = pygame.Rect(0, 0, 0, 0)
        self.rect_escala_dir = pygame.Rect(0, 0, 0, 0)

    def notas_da_escala(self):
        """
            Como funciona: Devolve as sete notas da tonalidade ativa.
            Para que serve: Saber se uma nota tocada pertence ao contexto atual.
            Onde e usada: Rastreamento de precisao da sessao de estudo.
        """
        escala = self.escalas_campo[self.indice_escala_campo]
        idx = self.notas_base.index(self.tonica_campo)
        return [self.notas_base[(idx + i) % 12] for i in escala['int']]

    def calcular_notas_acorde_selecionado(self):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'calcular notas acorde selecionado'.
            Para que serve: Realiza as tarefas fundamentais de 'calcular notas acorde selecionado' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'calcular notas acorde selecionado'.
        """
        escala_atual = self.escalas_campo[self.indice_escala_campo]
        idx_tonica_escala = self.notas_base.index(self.tonica_campo)
        idx_raiz_acorde = (idx_tonica_escala + escala_atual['int'][self.indice_acorde_selecionado]) % 12
        qualidade = escala_atual['qualidades'][self.indice_acorde_selecionado]
        if qualidade == '':
            idx_terca = (idx_raiz_acorde + 4) % 12
            idx_quinta = (idx_raiz_acorde + 7) % 12
        elif qualidade == 'm':
            idx_terca = (idx_raiz_acorde + 3) % 12
            idx_quinta = (idx_raiz_acorde + 7) % 12
        elif qualidade == 'dim':
            idx_terca = (idx_raiz_acorde + 3) % 12
            idx_quinta = (idx_raiz_acorde + 6) % 12
        self.notas_acorde_selecionado = [self.notas_base[idx_raiz_acorde], self.notas_base[idx_terca], self.notas_base[idx_quinta]]

    def desenhar(self, tela, x_base, y_base, largura_dragger, fonte_titulo, fonte_ui, fonte_pequena):
        """
            Como funciona: Renderiza os sete graus da tonalidade como cartoes
            selecionaveis, com o algarismo romano acima e os controles de tonica
            e escala logo abaixo.
            Para que serve: Navegar pelo campo harmonico e filtrar o braco.
            Onde e usada: Chamado pelo painel de acordes do workspace.
        """
        from config.design_system import TEMA, ds

        escala_atual = self.escalas_campo[self.indice_escala_campo]
        idx_tonica = self.notas_base.index(self.tonica_campo)
        x_centro = x_base + largura_dragger // 2

        # --- Cartoes dos sete graus ---------------------------------------
        largura_bloco = min(88, max(48, (largura_dragger - 120) // 7))
        altura_bloco = 58
        espacamento = max(6, (largura_dragger - 7 * largura_bloco) // 9)
        largura_total = 7 * largura_bloco + 6 * espacamento
        x_inicial = x_centro - largura_total // 2

        self.rects_acordes_campo.clear()
        for i in range(7):
            x_bloco = x_inicial + i * (largura_bloco + espacamento)
            idx_nota = (idx_tonica + escala_atual['int'][i]) % 12
            nome_acorde = self.notas_base[idx_nota] + escala_atual['qualidades'][i]
            romano = escala_atual['romanos'][i]
            selecionado = self.indice_acorde_selecionado == i

            ds.texto_em(tela, romano, fonte_pequena,
                        (x_bloco + largura_bloco // 2, y_base - 12),
                        TEMA.acento if selecionado else TEMA.texto_apagado,
                        ancora='center')

            rect_bloco = pygame.Rect(x_bloco, y_base, largura_bloco, altura_bloco)
            self.rects_acordes_campo.append(rect_bloco)

            if selecionado:
                ds.gradiente_vertical(tela, rect_bloco,
                                      ds.clarear(TEMA.acento, 0.18),
                                      TEMA.acento, ds.RAIO_LG)
                pygame.draw.rect(tela, ds.rgb(TEMA.texto), rect_bloco,
                                 width=2, border_radius=ds.RAIO_LG)
                cor_txt = TEMA.texto_sobre_cor
            else:
                ds.superficie_translucida(tela, rect_bloco, TEMA.superficie_alt,
                                          235, ds.RAIO_LG, TEMA.borda, 1)
                cor_txt = TEMA.texto

            fonte_acorde = fonte_titulo
            if fonte_acorde.size(nome_acorde)[0] > largura_bloco - 10:
                fonte_acorde = fonte_ui
            ds.texto_centralizado(tela, nome_acorde, fonte_acorde, rect_bloco,
                                  cor_txt)

        # --- Controles de tonica e escala ---------------------------------
        y_controles = y_base + altura_bloco + ds.ESPACO_LG
        metade = largura_dragger // 2
        tam_seta = 28
        altura_ctrl = 30

        def _stepper(x_centro_ctrl, largura_campo, valor, rotulo, fonte_valor):
            largura_campo = max(70, largura_campo)
            rect_esq = pygame.Rect(x_centro_ctrl - largura_campo // 2 - tam_seta,
                                   y_controles, tam_seta, altura_ctrl)
            rect_dir = pygame.Rect(x_centro_ctrl + largura_campo // 2,
                                   y_controles, tam_seta, altura_ctrl)
            ds.texto_em(tela, rotulo, fonte_pequena,
                        (x_centro_ctrl, y_controles - 12),
                        TEMA.texto_apagado, ancora='center')
            ds.botao(tela, rect_esq, '<', fonte_pequena, variante='secundario')
            ds.botao(tela, rect_dir, '>', fonte_pequena, variante='secundario')
            rect_valor = pygame.Rect(rect_esq.right, y_controles,
                                     rect_dir.left - rect_esq.right, altura_ctrl)
            ds.texto_centralizado(tela, valor, fonte_valor, rect_valor, TEMA.texto)
            return rect_esq, rect_dir

        from core.i18n import _t
        self.rect_tonica_esq, self.rect_tonica_dir = _stepper(
            x_base + metade // 2, 60, self.tonica_campo, _t('Tonica'), fonte_titulo)

        fonte_escala = fonte_ui if fonte_ui.size(escala_atual['nome'])[0] <= 150 else fonte_pequena
        self.rect_escala_esq, self.rect_escala_dir = _stepper(
            x_base + metade + metade // 2, min(170, metade - 80),
            escala_atual['nome'], _t('Escala'), fonte_escala)

    def tratar_clique(self, pos_mouse):
        """
            Como funciona: Verifica colisões e processa inputs do mouse/teclado.
            Para que serve: Mapeia ações do usuário para atualizações de estado.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_campo_harmonico'.
        """
        for i, rect in enumerate(self.rects_acordes_campo):
            if rect.collidepoint(pos_mouse):
                if self.indice_acorde_selecionado == i:
                    self.indice_acorde_selecionado = -1
                    self.notas_acorde_selecionado = []
                else:
                    self.indice_acorde_selecionado = i
                    self.calcular_notas_acorde_selecionado()
                return True
        if self.rect_tonica_esq.collidepoint(pos_mouse):
            idx = self.notas_base.index(self.tonica_campo)
            self.tonica_campo = self.notas_base[(idx - 1) % 12]
            self.tonica = self.tonica_campo
            self.indice_acorde_selecionado = -1
            return True
        elif self.rect_tonica_dir.collidepoint(pos_mouse):
            idx = self.notas_base.index(self.tonica_campo)
            self.tonica_campo = self.notas_base[(idx + 1) % 12]
            self.tonica = self.tonica_campo
            self.indice_acorde_selecionado = -1
            return True
        elif self.rect_escala_esq.collidepoint(pos_mouse):
            self.indice_escala_campo = (self.indice_escala_campo - 1) % len(self.escalas_campo)
            self.tipo_escala = self.escalas_campo[self.indice_escala_campo]['nome']
            self.indice_acorde_selecionado = -1
            return True
        elif self.rect_escala_dir.collidepoint(pos_mouse):
            self.indice_escala_campo = (self.indice_escala_campo + 1) % len(self.escalas_campo)
            self.tipo_escala = self.escalas_campo[self.indice_escala_campo]['nome']
            self.indice_acorde_selecionado = -1
            return True
        return False