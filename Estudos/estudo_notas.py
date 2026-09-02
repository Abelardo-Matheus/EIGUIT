# -*- coding: utf-8 -*-
"""
Estudo de notas no instrumento.

Tres modos:

- Adivinhar: o estudo aponta uma posicao e voce diz que nota e.
- Mapear: o estudo pede uma nota e voce acha todas as posicoes dela.
- Ouvir: o estudo toca uma nota e voce a identifica de ouvido.

Funciona em qualquer instrumento do modelo compartilhado: guitarra de 6 e 7
cordas, baixo de 4 e 5, ukulele, cavaquinho e teclado.
"""
import os
import random

import numpy as np
import pygame

from config.design_system import TEMA, ds
from config.instrumentos import (ORDEM_INSTRUMENTOS, config_instrumento,
                                 desenhar_diagrama, nota_da_casa, NOTAS)
from core.i18n import _t

MODOS = [('adivinhar', 'Adivinhar'), ('mapear', 'Mapear'), ('ouvir', 'Ouvir')]

FREQUENCIAS = {
    'C': 261.63, 'C#': 277.18, 'D': 293.66, 'D#': 311.13, 'E': 329.63,
    'F': 349.23, 'F#': 369.99, 'G': 392.0, 'G#': 415.30, 'A': 440.0,
    'A#': 466.16, 'B': 493.88,
}


class AcerteANota:
    """
        Como funciona: Sorteia posicoes ou notas no instrumento escolhido e
        confere a resposta, mostrando o resultado no proprio diagrama.
        Para que serve: Aprender onde cada nota mora em cada instrumento.
        Onde e usada: Aba Estudos, secao Notas.
    """

    def __init__(self):
        self.modo_jogo = 'adivinhar'
        self.instrumento = 'guitarra'
        self.casas_estudo = 12
        self.timbre = 'sintetizado'

        self.acertos = 0
        self.total = 0
        self.feedback = ''
        self.cor_feedback = None
        self.tempo_feedback = 0
        self.inicializado = False

        # modo adivinhar / ouvir
        self.corda_alvo = 0
        self.casa_alvo = 0
        self.tecla_alvo = 0
        self.nota_correta = ''
        # modo mapear
        self.nota_alvo_mapear = ''
        self.posicoes_corretas = set()
        self.posicoes_encontradas = set()

        self.sons_sintetizados = {}
        self.sons_piano = {}

        self.rects_notas = {}
        self.rects_modo = []
        self.rects_instrumento = []
        self.rects_posicoes = []
        self.rect_btn_tocar = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_timbre = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_menos = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_mais = pygame.Rect(0, 0, 0, 0)

        self._fontes = {}
        self._carregar_sons()

    # ----------------------------------------------------------- recursos --
    def _fonte(self, tamanho):
        if tamanho not in self._fontes:
            self._fontes[tamanho] = pygame.font.SysFont('Arial', tamanho, bold=True)
        return self._fontes[tamanho]

    def _gerar_amostra(self, freq, duracao=1.2, sample_rate=44100):
        """Sintetiza a nota com decaimento exponencial, de forma vetorizada."""
        n = int(sample_rate * duracao)
        t = np.arange(n) / sample_rate
        envelope = np.exp(-3.0 * t)
        onda = (np.sin(2 * np.pi * freq * t)
                + 0.3 * np.sin(4 * np.pi * freq * t)) * envelope
        onda = onda / max(1e-6, np.max(np.abs(onda))) * 16384 * envelope
        return pygame.mixer.Sound(onda.astype(np.int16))

    def _carregar_sons(self):
        """Sintetiza as doze notas e carrega amostras de piano, se houver."""
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=1)
            except pygame.error:
                return
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for nome in NOTAS:
            if nome in FREQUENCIAS:
                try:
                    self.sons_sintetizados[nome] = self._gerar_amostra(FREQUENCIAS[nome])
                except (pygame.error, ValueError):
                    pass
            for pasta in ('Audios', os.path.join('assets', 'audio')):
                caminho = os.path.join(base, pasta, f'{nome}.wav')
                if os.path.exists(caminho):
                    try:
                        self.sons_piano[nome] = pygame.mixer.Sound(caminho)
                    except pygame.error:
                        pass
                    break

    # -------------------------------------------------------------- logica --
    @property
    def config(self):
        return config_instrumento(self.instrumento)

    @property
    def de_corda(self):
        return self.config['familia'] == 'corda'

    def _casas_disponiveis(self):
        return min(self.casas_estudo, self.config.get('casas', 12))

    def inicializar_questao(self, estado=None):
        """
            Como funciona: Sorteia a proxima pergunta conforme o modo e o
            instrumento escolhidos.
            Para que serve: Encadear as perguntas do estudo.
            Onde e usada: Ao abrir, ao trocar de ajuste e apos cada resposta.
        """
        self.rects_notas.clear()
        if self.modo_jogo == 'adivinhar':
            if self.de_corda:
                cordas = self.config['cordas']
                self.corda_alvo = random.randrange(len(cordas))
                self.casa_alvo = random.randint(0, self._casas_disponiveis())
                self.nota_correta = nota_da_casa(cordas[self.corda_alvo], self.casa_alvo)
            else:
                total = self.config.get('num_oitavas', 2) * 12
                self.tecla_alvo = random.randrange(total)
                self.nota_correta = NOTAS[self.tecla_alvo % 12]

        elif self.modo_jogo == 'mapear':
            self.nota_alvo_mapear = random.choice(NOTAS)
            self.posicoes_corretas.clear()
            self.posicoes_encontradas.clear()
            if self.de_corda:
                for c, solta in enumerate(self.config['cordas']):
                    for casa in range(self._casas_disponiveis() + 1):
                        if nota_da_casa(solta, casa) == self.nota_alvo_mapear:
                            self.posicoes_corretas.add((c, casa))
            else:
                for i in range(self.config.get('num_oitavas', 2) * 12):
                    if NOTAS[i % 12] == self.nota_alvo_mapear:
                        self.posicoes_corretas.add(i)

        elif self.modo_jogo == 'ouvir':
            self.nota_correta = random.choice(NOTAS)
            self.tocar_nota_atual()

        self.inicializado = True

    def tocar_nota_atual(self):
        """Toca a nota da pergunta, no timbre escolhido."""
        biblioteca = (self.sons_piano if self.timbre == 'piano'
                      and self.nota_correta in self.sons_piano
                      else self.sons_sintetizados)
        som = biblioteca.get(self.nota_correta)
        if som:
            som.play()

    def _avisar(self, texto, cor):
        self.feedback = texto
        self.cor_feedback = cor
        self.tempo_feedback = pygame.time.get_ticks() + 1500

    def verificar_resposta(self, nota, estado=None):
        """Confere a nota respondida nos modos adivinhar e ouvir."""
        self.total += 1
        if nota == self.nota_correta:
            self.acertos += 1
            self._avisar(_t('Acertou!'), TEMA.verde)
        else:
            self._avisar(f"{_t('Era')} {self.nota_correta}", TEMA.alerta)
        self.inicializar_questao(estado)

    def verificar_clique_mapeamento(self, posicao, estado=None):
        """Confere um clique no modo mapear."""
        if posicao in self.posicoes_corretas:
            if posicao not in self.posicoes_encontradas:
                self.posicoes_encontradas.add(posicao)
                if len(self.posicoes_encontradas) == len(self.posicoes_corretas):
                    self.acertos += 1
                    self.total += 1
                    self._avisar(_t('Achou todas!'), TEMA.verde)
                    self.inicializar_questao(estado)
        else:
            self._avisar(_t('Essa nao e a nota'), TEMA.alerta)

    # ------------------------------------------------------------ desenho --
    def _barra(self, tela, rect, fontes):
        """Modo, instrumento, casas e placar."""
        pos_mouse = pygame.mouse.get_pos()
        fonte = self._fonte(12)
        y = rect.y

        self.rects_modo = []
        x = rect.x
        for chave, rotulo in MODOS:
            larg = fonte.size(_t(rotulo))[0] + 22
            r = pygame.Rect(x, y, larg, 26)
            self.rects_modo.append((r, chave))
            ds.chip(tela, r, _t(rotulo), fonte, ativo=chave == self.modo_jogo)
            x += larg + 5

        # Placar a direita
        precisao = int(self.acertos / self.total * 100) if self.total else 0
        ds.texto_em(tela, f"{self.acertos}/{self.total}  ·  {precisao}%",
                    self._fonte(14), (rect.right, y + 5),
                    TEMA.verde if precisao >= 70 else TEMA.texto_suave,
                    ancora='topright')

        y += 32
        self.rects_instrumento = []
        x = rect.x
        for chave in ORDEM_INSTRUMENTOS:
            nome = config_instrumento(chave)['nome'].split(' (')[0]
            sufixo = config_instrumento(chave)['nome']
            rotulo = nome if '(' not in sufixo else sufixo.replace('cordas', 'c.')
            larg = self._fonte(11).size(rotulo)[0] + 16
            r = pygame.Rect(x, y, larg, 24)
            if r.right > rect.right - 150:
                break
            self.rects_instrumento.append((r, chave))
            ds.chip(tela, r, rotulo, self._fonte(11), ativo=chave == self.instrumento)
            x += larg + 4

        if self.de_corda:
            self.rect_btn_mais = pygame.Rect(rect.right - 30, y, 30, 24)
            self.rect_btn_menos = pygame.Rect(rect.right - 118, y, 30, 24)
            ds.botao(tela, self.rect_btn_menos, '-', fonte, variante='secundario',
                     hover=self.rect_btn_menos.collidepoint(pos_mouse))
            ds.botao(tela, self.rect_btn_mais, '+', fonte, variante='secundario',
                     hover=self.rect_btn_mais.collidepoint(pos_mouse))
            ds.texto_centralizado(
                tela, f'{self._casas_disponiveis()} {_t("casas")}', self._fonte(11),
                pygame.Rect(self.rect_btn_menos.right, y,
                            self.rect_btn_mais.left - self.rect_btn_menos.right, 24),
                TEMA.texto)
        else:
            self.rect_btn_menos = pygame.Rect(-100, -100, 0, 0)
            self.rect_btn_mais = pygame.Rect(-100, -100, 0, 0)
        return y + 30

    def _destaques(self):
        """O que fica marcado no diagrama, conforme o modo."""
        destaques = {}
        if self.modo_jogo == 'adivinhar':
            chave = (self.corda_alvo, self.casa_alvo) if self.de_corda else self.tecla_alvo
            destaques[chave] = (TEMA.aviso, '?')
        elif self.modo_jogo == 'mapear':
            for pos in self.posicoes_encontradas:
                destaques[pos] = (TEMA.verde, self.nota_alvo_mapear)
        return destaques

    def _pergunta(self, tela, rect, fontes):
        """Enunciado da pergunta e, no modo ouvir, o botao de tocar."""
        pos_mouse = pygame.mouse.get_pos()
        if self.modo_jogo == 'adivinhar':
            if self.de_corda:
                corda = self.config['cordas'][self.corda_alvo]
                texto = (f"{_t('Corda')} {corda} · "
                         f"{_t('casa')} {self.casa_alvo}" if self.casa_alvo
                         else f"{_t('Corda solta')} {corda}")
            else:
                texto = _t('Qual e a tecla marcada?')
            ds.texto_em(tela, texto, self._fonte(18), (rect.centerx, rect.y),
                        TEMA.texto, ancora='midtop')
            self.rect_btn_tocar = pygame.Rect(-100, -100, 0, 0)

        elif self.modo_jogo == 'mapear':
            achadas = len(self.posicoes_encontradas)
            total = len(self.posicoes_corretas)
            ds.texto_em(tela, f"{_t('Ache todas as posicoes de')} {self.nota_alvo_mapear}",
                        self._fonte(18), (rect.centerx, rect.y), TEMA.texto,
                        ancora='midtop')
            ds.texto_em(tela, f'{achadas} / {total}', self._fonte(14),
                        (rect.centerx, rect.y + 24),
                        TEMA.verde if achadas == total else TEMA.texto_suave,
                        ancora='midtop')
            self.rect_btn_tocar = pygame.Rect(-100, -100, 0, 0)

        else:  # ouvir
            self.rect_btn_tocar = pygame.Rect(rect.centerx - 70, rect.y, 140, 38)
            ds.botao(tela, self.rect_btn_tocar, _t('Tocar de novo'), self._fonte(14),
                     variante='primario',
                     hover=self.rect_btn_tocar.collidepoint(pos_mouse))
            self.rect_btn_timbre = pygame.Rect(self.rect_btn_tocar.right + 8, rect.y,
                                               110, 38)
            ds.botao(tela, self.rect_btn_timbre,
                     _t('Piano') if self.timbre == 'piano' else _t('Sintetizado'),
                     self._fonte(12), variante='secundario',
                     hover=self.rect_btn_timbre.collidepoint(pos_mouse))

    def _teclado_resposta(self, tela, rect, fontes):
        """Fileira com as doze notas para responder."""
        self.rects_notas.clear()
        largura = (rect.width - 11 * 4) / 12
        for i, nota in enumerate(NOTAS):
            r = pygame.Rect(int(rect.x + i * (largura + 4)), rect.y,
                            int(largura), rect.height)
            self.rects_notas[nota] = r
            acidente = len(nota) > 1
            ds.botao(tela, r, nota, self._fonte(14),
                     variante='secundario' if acidente else 'suave')

    def desenhar(self, tela, estado, fontes, meio_x, meio_y, cam_x, cam_y,
                 motor_audio=None):
        """
            Como funciona: Barra de ajustes, enunciado, diagrama do instrumento
            e as doze notas de resposta.
            Para que serve: Tela do estudo de notas.
            Onde e usada: Chamada pelo gerenciador de estudos.
        """
        if not self.inicializado:
            self.inicializar_questao(estado)

        largura = getattr(estado, 'LARGURA_TELA', 1280)
        altura = getattr(estado, 'ALTURA_TELA', 720)
        area = pygame.Rect(int(cam_x + 40), int(cam_y + 56),
                           int(largura - 80), int(altura - 130))
        ds.painel(tela, area, None, None, acento=TEMA.acento, alpha=235)
        interno = area.inflate(-ds.ESPACO_XL * 2, -ds.ESPACO_XL * 2)

        y = self._barra(tela, interno, fontes)

        altura_pergunta = 46
        self._pergunta(tela, pygame.Rect(interno.x, y + ds.ESPACO_SM,
                                         interno.width, altura_pergunta), fontes)
        y += altura_pergunta + ds.ESPACO_MD

        altura_respostas = 44 if self.modo_jogo != 'mapear' else 0
        rect_diagrama = pygame.Rect(
            interno.x, y, interno.width,
            interno.bottom - y - altura_respostas - ds.ESPACO_LG * 2)
        if rect_diagrama.height > 60:
            self.rects_posicoes = []
            desenhar_diagrama(tela, rect_diagrama, self.instrumento,
                              self._destaques(), self._fonte(11),
                              self.rects_posicoes,
                              casas_visiveis=self._casas_disponiveis()
                              if self.de_corda else None)

        if altura_respostas:
            self._teclado_resposta(
                tela, pygame.Rect(interno.x, interno.bottom - altura_respostas,
                                  interno.width, altura_respostas), fontes)
        else:
            self.rects_notas.clear()

        if self.feedback and pygame.time.get_ticks() < self.tempo_feedback:
            ds.texto_em(tela, self.feedback, self._fonte(22),
                        (interno.centerx, rect_diagrama.y - 4),
                        self.cor_feedback or TEMA.texto, ancora='midbottom')

    # ------------------------------------------------------------- clique --
    def tratar_cliques(self, pos, estado=None):
        """Trata modo, instrumento, casas, respostas e cliques no diagrama."""
        for r, chave in self.rects_modo:
            if r.collidepoint(pos):
                self.modo_jogo = chave
                self.inicializar_questao(estado)
                return True
        for r, chave in self.rects_instrumento:
            if r.collidepoint(pos):
                self.instrumento = chave
                self.inicializar_questao(estado)
                return True
        if self.rect_btn_menos.collidepoint(pos):
            self.casas_estudo = max(5, self.casas_estudo - 1)
            self.inicializar_questao(estado)
            return True
        if self.rect_btn_mais.collidepoint(pos):
            self.casas_estudo = min(self.config.get('casas', 12), self.casas_estudo + 1)
            self.inicializar_questao(estado)
            return True
        if self.rect_btn_tocar.collidepoint(pos):
            self.tocar_nota_atual()
            return True
        if self.rect_btn_timbre.collidepoint(pos):
            self.timbre = 'piano' if self.timbre == 'sintetizado' else 'sintetizado'
            return True

        for nota, r in self.rects_notas.items():
            if r.collidepoint(pos):
                self.verificar_resposta(nota, estado)
                return True

        if self.modo_jogo == 'mapear':
            for r, posicao in self.rects_posicoes:
                if r.collidepoint(pos):
                    self.verificar_clique_mapeamento(posicao, estado)
                    return True
        return False
