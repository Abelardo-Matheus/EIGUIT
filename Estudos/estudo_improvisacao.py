# -*- coding: utf-8 -*-
"""
Estudo de improvisacao.

A ideia central: improvisar bem e menos sobre "qual escala cabe" e mais sobre
"em que nota eu chego". O painel roda uma progressao no andamento escolhido e,
a cada acorde, mostra no instrumento:

- as notas ALVO (do acorde), que resolvem;
- as notas da ESCALA que servem de passagem;
- as notas a EVITAR em tempo forte, com o motivo.

Alem disso oferece guias de fraseado, celulas de vocabulario e modos de
pratica que mudam o foco do exercicio.
"""
import time

import pygame

from config.design_system import TEMA, ds
from config.instrumentos import (ORDEM_INSTRUMENTOS, config_instrumento,
                                 desenhar_diagrama, nota_da_casa, NOTAS)
from core.i18n import _t

# --- acordes -----------------------------------------------------------------
TIPOS = {
    'maior': {'sufixo': '', 'int': [0, 4, 7], 'graus': ['1', '3', '5']},
    'menor': {'sufixo': 'm', 'int': [0, 3, 7], 'graus': ['1', 'b3', '5']},
    '7':     {'sufixo': '7', 'int': [0, 4, 7, 10], 'graus': ['1', '3', '5', 'b7']},
    'maj7':  {'sufixo': 'maj7', 'int': [0, 4, 7, 11], 'graus': ['1', '3', '5', '7']},
    'm7':    {'sufixo': 'm7', 'int': [0, 3, 7, 10], 'graus': ['1', 'b3', '5', 'b7']},
    'm7b5':  {'sufixo': 'm7b5', 'int': [0, 3, 6, 10], 'graus': ['1', 'b3', 'b5', 'b7']},
}

# --- escalas que servem sobre cada tipo de acorde -----------------------------
ESCALA_POR_TIPO = {
    'maior': {'nome': 'Jonio', 'int': [0, 2, 4, 5, 7, 9, 11], 'evitar': [5]},
    'menor': {'nome': 'Eolio', 'int': [0, 2, 3, 5, 7, 8, 10], 'evitar': [8]},
    '7':     {'nome': 'Mixolidio', 'int': [0, 2, 4, 5, 7, 9, 10], 'evitar': [5]},
    'maj7':  {'nome': 'Jonio', 'int': [0, 2, 4, 5, 7, 9, 11], 'evitar': [5]},
    'm7':    {'nome': 'Dorico', 'int': [0, 2, 3, 5, 7, 9, 10], 'evitar': []},
    'm7b5':  {'nome': 'Locrio', 'int': [0, 1, 3, 5, 6, 8, 10], 'evitar': [1]},
}

MOTIVO_EVITAR = {
    5: 'A quarta justa briga com a terca maior. Use de passagem, nunca parada.',
    8: 'A sexta menor pesa sobre o acorde. Resolva rapido para a quinta.',
    1: 'A segunda menor e muito tensa. Serve como aproximacao cromatica.',
}

# --- progressoes --------------------------------------------------------------
# (grau em semitons a partir da tonica, tipo, compassos)
PROGRESSOES = [
    {'nome': 'I - V - vi - IV', 'compasso': 4,
     'acordes': [(0, 'maior', 1), (7, 'maior', 1), (9, 'menor', 1), (5, 'maior', 1)],
     'descricao': 'A progressao mais comum da musica popular.'},
    {'nome': 'ii - V - I', 'compasso': 4,
     'acordes': [(2, 'm7', 1), (7, '7', 1), (0, 'maj7', 2)],
     'descricao': 'Celula central do jazz. Treine a resolucao no I.'},
    {'nome': 'Blues em 12 compassos', 'compasso': 4,
     'acordes': [(0, '7', 4), (5, '7', 2), (0, '7', 2),
                 (7, '7', 1), (5, '7', 1), (0, '7', 1), (7, '7', 1)],
     'descricao': 'Forma classica. Toda a nota tensa se resolve no proximo acorde.'},
    {'nome': 'i - VI - III - VII', 'compasso': 4,
     'acordes': [(0, 'menor', 1), (8, 'maior', 1), (3, 'maior', 1), (10, 'maior', 1)],
     'descricao': 'Menor natural, som epico e melancolico.'},
    {'nome': 'Vamp dorico i - IV', 'compasso': 4,
     'acordes': [(0, 'm7', 2), (5, '7', 2)],
     'descricao': 'Dois acordes so. Espaco de sobra para trabalhar fraseado.'},
    {'nome': 'ii - V menor', 'compasso': 4,
     'acordes': [(2, 'm7b5', 1), (7, '7', 1), (0, 'menor', 2)],
     'descricao': 'Cadencia menor. O m7b5 pede cuidado com a nota a evitar.'},
]

# --- modos de pratica ---------------------------------------------------------
MODOS_PRATICA = [
    {'nome': 'Notas alvo',
     'dica': 'Toque poucas notas e chegue no 3 ou no 7 de cada acorde no tempo 1.'},
    {'nome': 'Escala',
     'dica': 'Percorra a escala do acorde sem parar nas notas a evitar.'},
    {'nome': 'Cromatismo',
     'dica': 'Aproxime cada nota alvo por um semitom abaixo antes de resolver.'},
    {'nome': 'Pergunta e resposta',
     'dica': 'Frase de dois compassos e responda com outra parecida, terminando diferente.'},
    {'nome': 'So ritmo',
     'dica': 'Use uma nota so e varie o ritmo. Improviso e ritmo antes de altura.'},
]

# --- vocabulario: celulas em graus -------------------------------------------
VOCABULARIO = [
    {'nome': 'Aproximacao cromatica', 'graus': ['b3', '3', '5'],
     'dica': 'Chega na terca por baixo. Serve em qualquer acorde maior.'},
    {'nome': 'Envelope', 'graus': ['9', '7', '1'],
     'dica': 'Cerca a tonica por cima e por baixo antes de resolver.'},
    {'nome': 'Arpejo descendente', 'graus': ['b7', '5', '3', '1'],
     'dica': 'Deixa claro qual e o acorde. Bom para comecar frase.'},
    {'nome': 'Blues box', 'graus': ['1', 'b3', '4', 'b5', '5'],
     'dica': 'A b5 e de passagem: nunca pare nela.'},
    {'nome': 'Motivo de tres', 'graus': ['5', '6', '1'],
     'dica': 'Repita o mesmo desenho em outro grau para criar sequencia.'},
]


def nome_do_acorde(tonica, semitom, tipo):
    """Cifra do acorde que fica a tantos semitons da tonalidade."""
    idx = (NOTAS.index(tonica) + semitom) % 12 if tonica in NOTAS else 0
    return f"{NOTAS[idx]}{TIPOS[tipo]['sufixo']}"


def notas_do_acorde(tonica, semitom, tipo):
    """{nota: grau} das notas do acorde."""
    raiz = (NOTAS.index(tonica) + semitom) % 12 if tonica in NOTAS else 0
    info = TIPOS[tipo]
    return {NOTAS[(raiz + i) % 12]: g for i, g in zip(info['int'], info['graus'])}


def notas_da_escala(tonica, semitom, tipo):
    """({nota: grau}, [notas a evitar]) da escala que serve sobre o acorde."""
    raiz = (NOTAS.index(tonica) + semitom) % 12 if tonica in NOTAS else 0
    escala = ESCALA_POR_TIPO[tipo]
    graus_nome = ['1', 'b2', '2', 'b3', '3', '4', 'b5', '5', 'b6', '6', 'b7', '7']
    mapa = {NOTAS[(raiz + i) % 12]: graus_nome[i] for i in escala['int']}
    evitar = [NOTAS[(raiz + i) % 12] for i in escala['evitar']]
    return mapa, evitar


class EstudoImprovisacao:
    """
        Como funciona: Roda uma progressao no andamento escolhido e, para o
        acorde do momento, destaca no instrumento as notas alvo, as de
        passagem e as que devem ser evitadas em tempo forte.
        Para que serve: Sair do 'decorei a escala' e chegar no fraseado.
        Onde e usada: Aba Estudos, secao Improvisacao.
    """

    def __init__(self):
        self.tonica = 'A'
        self.indice_progressao = 2      # blues
        self.indice_modo = 0
        self.instrumento = 'guitarra'
        self.bpm = 80
        self.tocando = False

        self.indice_acorde = 0
        self.inicio_compasso = 0.0
        self.brilho = 0.0

        self.som_tick = None
        self.som_acento = None
        self._carregar_sons()

        self.rects_tonica = []
        self.rects_progressao = []
        self.rects_modo = []
        self.rects_instrumento = []
        self.rects_acordes = []
        self.rect_play = pygame.Rect(0, 0, 0, 0)
        self.rect_bpm_menos = pygame.Rect(0, 0, 0, 0)
        self.rect_bpm_mais = pygame.Rect(0, 0, 0, 0)
        self._fontes = {}

    def _fonte(self, tamanho):
        if tamanho not in self._fontes:
            self._fontes[tamanho] = pygame.font.SysFont('Arial', tamanho, bold=True)
        return self._fontes[tamanho]

    def _carregar_sons(self):
        import os, sys
        try:
            raiz = (os.path.dirname(sys.executable) if getattr(sys, 'frozen', False)
                    else os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            pasta = os.path.join(raiz, 'assets', 'audio')
            for atributo, arquivo in (('som_tick', 'tick.wav'), ('som_acento', 'tick_high.wav')):
                caminho = os.path.join(pasta, arquivo)
                if os.path.exists(caminho):
                    setattr(self, atributo, pygame.mixer.Sound(caminho))
        except Exception:
            pass

    # ------------------------------------------------------------- estado --
    @property
    def progressao(self):
        return PROGRESSOES[self.indice_progressao % len(PROGRESSOES)]

    @property
    def modo_pratica(self):
        return MODOS_PRATICA[self.indice_modo % len(MODOS_PRATICA)]

    @property
    def acorde_atual(self):
        acordes = self.progressao['acordes']
        return acordes[self.indice_acorde % len(acordes)]

    def duracao_acorde(self, acorde):
        """Segundos que o acorde dura, conforme compassos e andamento."""
        pulso = 60.0 / max(1, self.bpm)
        return acorde[2] * self.progressao['compasso'] * pulso

    def alternar_play(self):
        self.tocando = not self.tocando
        self.indice_acorde = 0
        self.inicio_compasso = time.time()

    def atualizar(self):
        """Avanca a progressao e marca o pulso."""
        if not self.tocando:
            return
        agora = time.time()
        self.brilho = max(0.0, self.brilho - 0.05)
        duracao = self.duracao_acorde(self.acorde_atual)
        if agora - self.inicio_compasso >= duracao:
            self.inicio_compasso += duracao
            self.indice_acorde = (self.indice_acorde + 1) % len(self.progressao['acordes'])
            self.brilho = 1.0
            if self.som_acento:
                self.som_acento.play()

    # ------------------------------------------------------------ desenho --
    def _barra(self, tela, rect, fontes):
        """Tonalidade, andamento, play e instrumento."""
        pos_mouse = pygame.mouse.get_pos()
        fonte = self._fonte(12)
        y = rect.y

        self.rects_tonica = []
        largura = min(32, (rect.width * 0.42 - 33) / 12)
        for i, nota in enumerate(NOTAS):
            r = pygame.Rect(int(rect.x + i * (largura + 3)), y, int(largura), 26)
            self.rects_tonica.append(r)
            ds.chip(tela, r, nota, self._fonte(11), ativo=nota == self.tonica)

        self.rect_play = pygame.Rect(rect.right - 92, y, 92, 26)
        ds.botao(tela, self.rect_play, _t('Parar') if self.tocando else _t('Tocar'),
                 fonte, variante='perigo' if self.tocando else 'primario',
                 hover=self.rect_play.collidepoint(pos_mouse))
        self.rect_bpm_mais = pygame.Rect(self.rect_play.x - 34, y, 30, 26)
        self.rect_bpm_menos = pygame.Rect(self.rect_play.x - 150, y, 30, 26)
        ds.botao(tela, self.rect_bpm_menos, '-', fonte, variante='secundario')
        ds.botao(tela, self.rect_bpm_mais, '+', fonte, variante='secundario')
        ds.texto_centralizado(
            tela, f'{self.bpm} BPM', fonte,
            pygame.Rect(self.rect_bpm_menos.right, y,
                        self.rect_bpm_mais.left - self.rect_bpm_menos.right, 26),
            TEMA.texto)

        y += 32
        self.rects_instrumento = []
        x = rect.right
        for chave in reversed(ORDEM_INSTRUMENTOS):
            nome = config_instrumento(chave)['nome'].split(' (')[0]
            larg = fonte.size(nome)[0] + 16
            r = pygame.Rect(x - larg, y, larg, 24)
            if r.x < rect.x + rect.width * 0.45:
                break
            self.rects_instrumento.insert(0, (r, chave))
            ds.chip(tela, r, nome, self._fonte(11), ativo=chave == self.instrumento)
            x -= larg + 4

        self.rects_modo = []
        for i, modo in enumerate(MODOS_PRATICA):
            larg = fonte.size(_t(modo['nome']))[0] + 16
            r = pygame.Rect(rect.x + sum(fonte.size(_t(m['nome']))[0] + 20
                                         for m in MODOS_PRATICA[:i]), y, larg, 24)
            if r.right > rect.x + rect.width * 0.45:
                break
            self.rects_modo.append(r)
            ds.chip(tela, r, _t(modo['nome']), self._fonte(11), ativo=i == self.indice_modo)
        return y + 30

    def _grade(self, tela, rect, fontes):
        """Sequencia de acordes, com destaque no que esta soando."""
        acordes = self.progressao['acordes']
        total_compassos = sum(a[2] for a in acordes)
        self.rects_acordes = []
        x = rect.x
        for i, acorde in enumerate(acordes):
            largura = rect.width * (acorde[2] / total_compassos)
            celula = pygame.Rect(int(x), rect.y, int(largura) - 3, rect.height)
            self.rects_acordes.append(celula)
            ativo = self.tocando and i == self.indice_acorde % len(acordes)
            if ativo:
                ds.gradiente_vertical(tela, celula, ds.clarear(TEMA.acento, 0.2),
                                      TEMA.acento, ds.RAIO_MD)
                cor_txt = TEMA.texto_sobre_cor
            else:
                ds.superficie_translucida(tela, celula, TEMA.superficie_alt, 220,
                                          ds.RAIO_MD, TEMA.borda, 1)
                cor_txt = TEMA.texto
            ds.texto_centralizado(tela, nome_do_acorde(self.tonica, acorde[0], acorde[1]),
                                  self._fonte(16), celula, cor_txt)
            x += largura

        # Barra de progresso dentro do acorde atual
        if self.tocando and self.rects_acordes:
            atual = self.rects_acordes[self.indice_acorde % len(self.rects_acordes)]
            fracao = min(1.0, (time.time() - self.inicio_compasso)
                         / max(0.1, self.duracao_acorde(self.acorde_atual)))
            pygame.draw.rect(tela, ds.rgb(TEMA.aviso),
                             (atual.x, atual.bottom - 3, int(atual.width * fracao), 3))

    def _diagrama(self, tela, rect, fontes):
        """Instrumento com alvos, escala e notas a evitar."""
        semitom, tipo, _ = self.acorde_atual
        alvos = notas_do_acorde(self.tonica, semitom, tipo)
        escala, evitar = notas_da_escala(self.tonica, semitom, tipo)

        cfg = config_instrumento(self.instrumento)
        destaques = {}

        def classificar(nome):
            if nome in alvos:
                cor = TEMA.acento if alvos[nome] == '1' else TEMA.verde
                return cor, alvos[nome]
            if nome in evitar:
                return TEMA.alerta, escala.get(nome, '')
            if nome in escala:
                return ds.misturar(TEMA.superficie_alt, TEMA.ciano, 0.5), escala[nome]
            return None

        if cfg['familia'] == 'corda':
            for i, solta in enumerate(cfg['cordas']):
                for casa in range(cfg['casas'] + 1):
                    dados = classificar(nota_da_casa(solta, casa))
                    if dados:
                        destaques[(i, casa)] = dados
        else:
            for i in range(cfg.get('num_oitavas', 2) * 12):
                dados = classificar(NOTAS[i % 12])
                if dados:
                    destaques[i] = dados

        desenhar_diagrama(tela, rect, self.instrumento, destaques, self._fonte(11))

    def _guia(self, tela, rect, fontes):
        """Coluna com o que fazer sobre o acorde do momento."""
        semitom, tipo, _ = self.acorde_atual
        alvos = notas_do_acorde(self.tonica, semitom, tipo)
        escala, evitar = notas_da_escala(self.tonica, semitom, tipo)
        info_escala = ESCALA_POR_TIPO[tipo]

        ds.superficie_translucida(tela, rect, TEMA.superficie_alt, 225, ds.RAIO_MD,
                                  TEMA.borda, 1)
        pad = ds.ESPACO_MD
        y = rect.y + ds.ESPACO_SM
        larg = rect.width - pad * 2

        def bloco(rotulo, valor, cor, y_atual):
            ds.texto_em(tela, rotulo, self._fonte(11), (rect.x + pad, y_atual),
                        TEMA.texto_apagado, largura_max=larg)
            y_atual += self._fonte(11).get_height() + 1
            ds.texto_em(tela, valor, self._fonte(13), (rect.x + pad, y_atual), cor,
                        largura_max=larg)
            return y_atual + self._fonte(13).get_height() + 8

        y = bloco(_t('Acorde agora'), nome_do_acorde(self.tonica, semitom, tipo),
                  TEMA.acento, y)
        y = bloco(_t('Notas alvo'), ' '.join(f'{n}({g})' for n, g in alvos.items()),
                  TEMA.verde, y)
        y = bloco(_t('Escala'), f"{_t(info_escala['nome'])}: {' '.join(escala.keys())}",
                  TEMA.ciano, y)
        if evitar:
            y = bloco(_t('Evitar em tempo forte'), ' '.join(evitar), TEMA.alerta, y)
            motivo = MOTIVO_EVITAR.get(info_escala['evitar'][0], '')
            if motivo and y < rect.bottom - 30:
                for linha in _quebrar(_t(motivo), self._fonte(11), larg):
                    ds.texto_em(tela, linha, self._fonte(11), (rect.x + pad, y),
                                TEMA.texto_apagado)
                    y += 14
                y += 6
        if y < rect.bottom - 40:
            y = bloco(_t('Foco do exercicio'), _t(self.modo_pratica['nome']),
                      TEMA.aviso, y)
            for linha in _quebrar(_t(self.modo_pratica['dica']), self._fonte(11), larg):
                if y > rect.bottom - 16:
                    break
                ds.texto_em(tela, linha, self._fonte(11), (rect.x + pad, y),
                            TEMA.texto_suave)
                y += 14

    def _vocabulario(self, tela, rect, fontes):
        """Celulas melodicas curtas, escritas em graus."""
        ds.rotulo_secao(tela, rect.x, rect.y, _t('Vocabulario'), fontes['pequena'],
                        TEMA.acento, largura_max=rect.width)
        y = rect.y + fontes['pequena'].get_height() + 4
        for item in VOCABULARIO:
            if y + 30 > rect.bottom:
                break
            ds.texto_em(tela, _t(item['nome']), self._fonte(12), (rect.x, y),
                        TEMA.texto, largura_max=rect.width)
            ds.texto_em(tela, ' - '.join(item['graus']), self._fonte(12),
                        (rect.right, y), TEMA.ciano, ancora='topright')
            y += 16
            ds.texto_em(tela, _t(item['dica']), self._fonte(10), (rect.x, y),
                        TEMA.texto_apagado, largura_max=rect.width)
            y += 18

    def desenhar(self, tela, estado, fontes, meio_x, meio_y, cam_x, cam_y,
                 motor_audio=None):
        """
            Como funciona: Barra de ajustes, grade da progressao, diagrama do
            instrumento e as colunas de guia e vocabulario.
            Para que serve: Tela do estudo de improvisacao.
            Onde e usada: Chamada pelo gerenciador de estudos.
        """
        self.atualizar()
        largura = getattr(estado, 'LARGURA_TELA', 1280)
        altura = getattr(estado, 'ALTURA_TELA', 720)
        area = pygame.Rect(int(cam_x + 40), int(cam_y + 56),
                           int(largura - 80), int(altura - 130))
        ds.painel(tela, area, None, None, acento=TEMA.acento, alpha=235)
        interno = area.inflate(-ds.ESPACO_XL * 2, -ds.ESPACO_XL * 2)

        y = self._barra(tela, interno, fontes)

        # Progressoes disponiveis, em coluna estreita a esquerda
        largura_lista = max(170, int(interno.width * 0.2))
        col_lista = pygame.Rect(interno.x, y + ds.ESPACO_SM, largura_lista,
                                interno.bottom - y - ds.ESPACO_SM)
        ds.rotulo_secao(tela, col_lista.x, col_lista.y, _t('Progressao'),
                        fontes['pequena'], TEMA.acento, largura_max=col_lista.width)
        y_lista = col_lista.y + fontes['pequena'].get_height() + 4
        self.rects_progressao = []
        for i, prog in enumerate(PROGRESSOES):
            if y_lista + 26 > col_lista.bottom:
                break
            r = pygame.Rect(col_lista.x, y_lista, col_lista.width, 24)
            self.rects_progressao.append(r)
            ds.chip(tela, r, _t(prog['nome']), self._fonte(11),
                    ativo=i == self.indice_progressao)
            y_lista += 27
        if y_lista + 40 < col_lista.bottom:
            self._vocabulario(tela, pygame.Rect(col_lista.x, y_lista + 8,
                                                col_lista.width,
                                                col_lista.bottom - y_lista - 8), fontes)

        # Coluna central e guia a direita
        largura_guia = max(200, int(interno.width * 0.24))
        col_centro = pygame.Rect(col_lista.right + ds.ESPACO_LG, col_lista.y,
                                 interno.width - largura_lista - largura_guia - ds.ESPACO_LG * 2,
                                 col_lista.height)
        col_guia = pygame.Rect(col_centro.right + ds.ESPACO_LG, col_lista.y,
                               largura_guia, col_lista.height)

        altura_grade = 52
        self._grade(tela, pygame.Rect(col_centro.x, col_centro.y,
                                      col_centro.width, altura_grade), fontes)
        ds.texto_em(tela, _t(self.progressao['descricao']), self._fonte(11),
                    (col_centro.x, col_centro.y + altura_grade + 6),
                    TEMA.texto_apagado, largura_max=col_centro.width)
        y_diagrama = col_centro.y + altura_grade + 26
        self._diagrama(tela, pygame.Rect(col_centro.x, y_diagrama, col_centro.width,
                                         col_centro.bottom - y_diagrama), fontes)
        self._guia(tela, col_guia, fontes)

    # ------------------------------------------------------------- clique --
    def tratar_cliques(self, pos, estado):
        """Trata os controles do estudo de improvisacao."""
        if self.rect_play.collidepoint(pos):
            self.alternar_play(); return True
        if self.rect_bpm_menos.collidepoint(pos):
            self.bpm = max(40, self.bpm - 5); return True
        if self.rect_bpm_mais.collidepoint(pos):
            self.bpm = min(240, self.bpm + 5); return True
        for i, r in enumerate(self.rects_tonica):
            if r.collidepoint(pos):
                self.tonica = NOTAS[i]; return True
        for i, r in enumerate(self.rects_progressao):
            if r.collidepoint(pos):
                self.indice_progressao = i
                self.indice_acorde = 0
                self.inicio_compasso = time.time()
                return True
        for i, r in enumerate(self.rects_modo):
            if r.collidepoint(pos):
                self.indice_modo = i; return True
        for r, chave in self.rects_instrumento:
            if r.collidepoint(pos):
                self.instrumento = chave; return True
        for i, r in enumerate(self.rects_acordes):
            if r.collidepoint(pos):
                self.indice_acorde = i
                self.inicio_compasso = time.time()
                return True
        return False


def _quebrar(texto, fonte, largura_max):
    """Quebra o texto em linhas que cabem na largura."""
    palavras, linhas, atual = texto.split(' '), [], ''
    for palavra in palavras:
        teste = f'{atual} {palavra}'.strip()
        if fonte.size(teste)[0] <= largura_max:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas
