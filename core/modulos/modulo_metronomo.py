# -*- coding: utf-8 -*-
"""Metronomo do EIGUIT Studio: widget compacto no workspace e painel completo."""
import os
import sys

import pygame

from core.modulos.modulos_config import *
from core.i18n import _t
from config.design_system import TEMA, ds

BPM_MIN = 40
BPM_MAX = 300
PRESETS_BPM = [60, 80, 100, 120, 140, 180]


class Metronomo:
    """
        Como funciona: Mantem o estado de tempo (BPM, compasso, batida atual) e
        dispara os sons de tick e acento.
        Para que serve: Referencia ritmica para estudo e gravacao.
        Onde e usada: Instanciado em main.py e desenhado pelo workspace.
    """

    def __init__(self, x_painel, y_painel):
        """
            Como funciona: Inicializa estado, retangulos de interacao e sons.
            Para que serve: Preparar o metronomo para o ciclo de vida do app.
            Onde e usada: Chamado a partir de main.py.
        """
        self.x = x_painel
        self.y = y_painel
        self.x_config = x_painel
        self.bpm = 100
        self.ativado = True
        self.tocando = False
        self.compasso = 4
        self.tempo_atual = 0
        self.ultimo_tick = 0
        self.foco_input = False
        self.bpm_texto = str(self.bpm)

        self.BRANCO = METRONOMO_BRANCO
        self.CINZA = METRONOMO_CINZA
        self.FUNDO_INPUT = METRONOMO_FUNDO_INPUT

        self.paleta_cores = [
            (255, 107, 107), (78, 205, 196), (0, 212, 255),
            (255, 217, 61), (255, 149, 61), (155, 122, 255),
        ]
        self.indices_cores = [0] + [1] * 7

        self.slider_largura = METRONOMO_SLIDER_LARGURA
        self.btn_play = pygame.Rect(0, 0, 55, 30)
        self.rect_slider_barra = pygame.Rect(0, 0, self.slider_largura, ds.ALTURA_TRILHO)
        self.rect_alca = pygame.Rect(0, 0, 16, 16)
        self.rect_input = pygame.Rect(0, 0, 52, 30)
        self.arrastando_slider = False

        self.rect_checkbox = pygame.Rect(self.x, self.y, 24, 24)
        self.btn_mais_batida = pygame.Rect(0, 0, 30, 30)
        self.btn_menos_batida = pygame.Rect(0, 0, 30, 30)
        self.rects_cores_config = []
        self.rects_presets = []

        self.som_tick = None
        self.som_acento = None
        self._carregar_sons()

    # ------------------------------------------------------------------ sons
    def _carregar_sons(self):
        """Carrega tick.wav e tick_high.wav de assets/audio, se existirem."""
        try:
            if getattr(sys, 'frozen', False):
                pasta_raiz = os.path.dirname(sys.executable)
            else:
                pasta_modulos = os.path.dirname(os.path.abspath(__file__))
                pasta_raiz = os.path.dirname(os.path.dirname(pasta_modulos))
            pasta_audios = os.path.join(pasta_raiz, 'assets', 'audio')
            caminho_tick = os.path.join(pasta_audios, 'tick.wav')
            caminho_acento = os.path.join(pasta_audios, 'tick_high.wav')
            if os.path.exists(caminho_tick):
                self.som_tick = pygame.mixer.Sound(caminho_tick)
            else:
                print(f'Aviso: som do metronomo nao encontrado em: {caminho_tick}')
            if os.path.exists(caminho_acento):
                self.som_acento = pygame.mixer.Sound(caminho_acento)
            else:
                print(f'Aviso: som de acento nao encontrado em: {caminho_acento}')
        except Exception as e:
            print(f'Aviso: erro ao carregar sons do metronomo: {e}')

    def _tocar_batida(self, acentuada):
        som = self.som_acento if (acentuada and self.som_acento) else self.som_tick
        if som:
            som.play()

    def _iniciar(self):
        self.tocando = True
        self.ultimo_tick = pygame.time.get_ticks()
        self.tempo_atual = 0
        self._tocar_batida(True)

    def definir_bpm(self, valor):
        self.bpm = max(BPM_MIN, min(BPM_MAX, int(valor)))
        self.bpm_texto = str(self.bpm)

    # --------------------------------------------------------------- eventos
    def tratar_clique(self, pos_mouse, estado, aba_config_aberta=False):
        """
            Como funciona: Testa colisao com os retangulos calculados no ultimo
            desenho, o que mantem clique e visual sempre alinhados.
            Para que serve: Traduzir cliques em mudancas de estado.
            Onde e usada: Chamado pelo controlador de eventos.
        """
        if aba_config_aberta:
            if self.rect_checkbox.collidepoint(pos_mouse):
                self.ativado = not self.ativado
                return True
            if self.btn_mais_batida.collidepoint(pos_mouse):
                self.compasso = min(8, self.compasso + 1)
                return True
            if self.btn_menos_batida.collidepoint(pos_mouse):
                self.compasso = max(2, self.compasso - 1)
                return True
            for i, rect in enumerate(self.rects_presets):
                if rect.collidepoint(pos_mouse):
                    self.definir_bpm(PRESETS_BPM[i])
                    return True
            for i, rect in enumerate(self.rects_cores_config):
                if rect.collidepoint(pos_mouse) and i < self.compasso:
                    self.indices_cores[i] = (self.indices_cores[i] + 1) % len(self.paleta_cores)
                    return True

        if not self.ativado:
            return False

        if self.btn_play.collidepoint(pos_mouse):
            if self.tocando:
                self.tocando = False
            else:
                self._iniciar()
            return True

        if self.rect_input.collidepoint(pos_mouse):
            self.foco_input = True
            self.bpm_texto = ''
            return True
        self.foco_input = False

        if (self.rect_alca.collidepoint(pos_mouse)
                or self.rect_slider_barra.inflate(0, 14).collidepoint(pos_mouse)):
            self.arrastando_slider = True
            self._atualizar_bpm_por_mouse(pos_mouse)
            return True
        return False

    def tratar_teclado(self, evento):
        """
            Como funciona: Trata digitacao no campo de BPM e o atalho de espaco.
            Para que serve: Controle rapido do metronomo pelo teclado.
            Onde e usada: Chamado pelo controlador de eventos.
        """
        if self.foco_input:
            if evento.key == pygame.K_RETURN:
                self.foco_input = False
                try:
                    self.definir_bpm(int(self.bpm_texto))
                except ValueError:
                    self.bpm_texto = str(self.bpm)
            elif evento.key == pygame.K_ESCAPE:
                self.foco_input = False
                self.bpm_texto = str(self.bpm)
            elif evento.key == pygame.K_BACKSPACE:
                self.bpm_texto = self.bpm_texto[:-1]
            elif evento.unicode.isdigit() and len(self.bpm_texto) < 3:
                self.bpm_texto += evento.unicode
        elif evento.key == pygame.K_SPACE and self.ativado:
            if self.tocando:
                self.tocando = False
            else:
                self._iniciar()

    def _atualizar_bpm_por_mouse(self, pos_mouse):
        barra = self.rect_slider_barra
        if barra.width <= 0:
            return
        rel = max(0, min(barra.width, pos_mouse[0] - barra.x))
        self.definir_bpm(BPM_MIN + rel / barra.width * (BPM_MAX - BPM_MIN))

    def processar_logica(self, pos_mouse, estado):
        """
            Como funciona: Atualiza o arrasto do slider e dispara as batidas.
            Para que serve: Manter o pulso ritmico em tempo real.
            Onde e usada: Chamado a cada quadro por main.py.
        """
        if self.arrastando_slider:
            if not pygame.mouse.get_pressed()[0]:
                self.arrastando_slider = False
            else:
                self._atualizar_bpm_por_mouse(pos_mouse)

        if self.ativado and self.tocando:
            agora = pygame.time.get_ticks()
            if agora - self.ultimo_tick >= 60000 / self.bpm:
                self.ultimo_tick = agora
                self.tempo_atual = (self.tempo_atual + 1) % self.compasso
                self._tocar_batida(self.tempo_atual == 0)

    # -------------------------------------------------------------- desenhos
    def _desenhar_batidas(self, tela, centro_x, centro_y, largura_disponivel):
        """Circulos que pulsam a cada batida do compasso."""
        espacamento = min(34, max(18, largura_disponivel // max(1, self.compasso)))
        x_inicio = centro_x - (self.compasso - 1) * espacamento // 2
        decorrido = pygame.time.get_ticks() - self.ultimo_tick

        for i in range(self.compasso):
            cor = self.paleta_cores[self.indices_cores[i] % len(self.paleta_cores)]
            ativa = (i == self.tempo_atual and self.tocando)
            cx = x_inicio + i * espacamento
            raio = 9 + (max(0, 6 - decorrido / 30) if ativa else 0)

            if ativa:
                halo = pygame.Surface((int(raio * 4), int(raio * 4)), pygame.SRCALPHA)
                pygame.draw.circle(halo, ds.com_alpha(cor, 70),
                                   (int(raio * 2), int(raio * 2)), int(raio * 1.9))
                tela.blit(halo, (cx - raio * 2, centro_y - raio * 2))
                pygame.draw.circle(tela, ds.rgb(cor), (int(cx), int(centro_y)), int(raio))
            else:
                base = ds.misturar(TEMA.superficie_alt, cor, 0.35)
                pygame.draw.circle(tela, ds.rgb(base), (int(cx), int(centro_y)), int(raio))
                pygame.draw.circle(tela, ds.rgb(ds.misturar(TEMA.borda, cor, 0.5)),
                                   (int(cx), int(centro_y)), int(raio), 1)

    def desenhar_mini_metronomo(self, tela, estado, fonte_ui, configs=None):
        """
            Como funciona: Widget compacto com batidas, play/stop, slider de BPM
            e campo numerico editavel.
            Para que serve: Controle do tempo sem sair do workspace.
            Onde e usada: Chamado por desenhar_controles_playback.
        """
        if not self.ativado:
            return
        if configs is not None:
            TEMA.definir_acento(configs.get_cor_tema())

        dragger = estado.dragger_metronomo
        rect = pygame.Rect(dragger.x, dragger.y, dragger.largura, dragger.altura)
        ds.painel(tela, rect, None, None, acento=TEMA.acento)

        pad = ds.ESPACO_MD
        # Cabecalho: rotulo e BPM atual
        ds.texto_em(tela, _t('Metronomo').upper(), fonte_ui,
                    (rect.x + pad, rect.y + ds.ESPACO_SM), TEMA.acento,
                    largura_max=rect.width // 2)
        ds.texto_em(tela, f'{self.bpm} BPM', fonte_ui,
                    (rect.right - pad, rect.y + ds.ESPACO_SM), TEMA.texto_suave,
                    ancora='topright')

        y_batidas = rect.y + ds.ESPACO_SM + fonte_ui.get_height() + 16
        self._desenhar_batidas(tela, rect.centerx, y_batidas, rect.width - pad * 2)

        # Linha de controles
        altura_btn = 30
        y_ctrl = min(rect.bottom - altura_btn - ds.ESPACO_MD, y_batidas + 24)
        largura_play = 56
        largura_input = 50
        gap = ds.ESPACO_SM

        self.btn_play = pygame.Rect(rect.x + pad, y_ctrl, largura_play, altura_btn)
        self.rect_input = pygame.Rect(rect.right - pad - largura_input, y_ctrl,
                                      largura_input, altura_btn)

        ds.botao(tela, self.btn_play, _t('STOP') if self.tocando else _t('PLAY'),
                 fonte_ui, variante='perigo' if self.tocando else 'primario',
                 hover=self.btn_play.collidepoint(pygame.mouse.get_pos()))

        largura_slider = max(40, self.rect_input.left - self.btn_play.right - gap * 2)
        self.slider_largura = largura_slider
        barra = pygame.Rect(self.btn_play.right + gap,
                            y_ctrl + altura_btn // 2 - ds.ALTURA_TRILHO // 2,
                            largura_slider, ds.ALTURA_TRILHO)
        pct = (self.bpm - BPM_MIN) / (BPM_MAX - BPM_MIN)
        self.rect_slider_barra, self.rect_alca = ds.slider(tela, barra, pct)

        ds.caixa_texto(tela, self.rect_input, self.bpm_texto, fonte_ui,
                       focado=self.foco_input)

        if estado.drag_ativado:
            dragger.desenhar_caixa_selecao(tela, margem=5)

    def desenhar_config(self, tela, fonte_ui, scroll_y=0, configs=None):
        """
            Como funciona: Painel completo de ajustes: ativar, compasso,
            atalhos de BPM e cores de cada batida.
            Para que serve: Configuracao detalhada do metronomo.
            Onde e usada: Aba Configuracoes > Metronomo.
        """
        if configs is not None:
            TEMA.definir_acento(configs.get_cor_tema())

        x = self.x
        y = self.y - scroll_y
        # Linha 1: ativar
        self.rect_checkbox = pygame.Rect(x, y, 24, 24)
        ds.caixa_selecao(tela, self.rect_checkbox, self.ativado)
        ds.texto_em(tela, _t('Ativar Metronomo'), fonte_ui,
                    (self.rect_checkbox.right + ds.ESPACO_MD,
                     self.rect_checkbox.centery), TEMA.texto, ancora='midleft')

        # Linha 2: compasso
        y += 46
        ds.rotulo_secao(tela, x, y, _t('Batidas por compasso'), fonte_ui,
                        TEMA.texto_apagado)
        y += fonte_ui.get_height() + ds.ESPACO_SM
        self.btn_menos_batida = pygame.Rect(x, y, 30, 30)
        self.btn_mais_batida = pygame.Rect(x + 76, y, 30, 30)
        ds.botao(tela, self.btn_menos_batida, '-', fonte_ui, variante='secundario')
        ds.botao(tela, self.btn_mais_batida, '+', fonte_ui, variante='secundario')
        ds.texto_centralizado(tela, f'{self.compasso}/4', fonte_ui,
                              pygame.Rect(self.btn_menos_batida.right, y,
                                          self.btn_mais_batida.left - self.btn_menos_batida.right,
                                          30), TEMA.texto)

        # Linha 3: presets de BPM
        y += 48
        ds.rotulo_secao(tela, x, y, _t('Tempos rapidos'), fonte_ui,
                        TEMA.texto_apagado)
        y += fonte_ui.get_height() + ds.ESPACO_SM
        self.rects_presets = []
        largura_chip = 52
        for i, valor in enumerate(PRESETS_BPM):
            rect_chip = pygame.Rect(x + i * (largura_chip + ds.ESPACO_SM), y,
                                    largura_chip, 28)
            self.rects_presets.append(rect_chip)
            ds.chip(tela, rect_chip, str(valor), fonte_ui, ativo=self.bpm == valor)

        # Linha 4: cores das batidas
        y += 48
        ds.rotulo_secao(tela, x, y, _t('Cores das batidas (clique para trocar)'),
                        fonte_ui, TEMA.texto_apagado)
        y += fonte_ui.get_height() + ds.ESPACO_MD
        self.rects_cores_config.clear()
        for i in range(self.compasso):
            cx = x + 16 + i * 38
            cor = self.paleta_cores[self.indices_cores[i] % len(self.paleta_cores)]
            pygame.draw.circle(tela, ds.rgb(cor), (cx, y + 12), 13)
            pygame.draw.circle(tela, ds.rgb(TEMA.texto if i == 0 else TEMA.borda),
                               (cx, y + 12), 13, 2)
            if i == 0:
                ds.texto_em(tela, '1', fonte_ui, (cx, y + 12),
                            ds.contraste_texto(cor), ancora='center')
            self.rects_cores_config.append(pygame.Rect(cx - 13, y - 1, 26, 26))
