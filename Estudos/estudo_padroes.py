# -*- coding: utf-8 -*-
"""
Estudo de padroes melodicos e ritmicos.

Melodicos: uma escala e percorrida por uma sequencia (terças, quartas,
grupos de quatro, arpejos...). O estudo mostra a ordem das notas no
instrumento escolhido e avanca no andamento do metronomo.

Ritmicos: celulas ritmicas classicas desenhadas em notacao simplificada,
tocadas pelo metronomo e conferidas pelo ataque do instrumento.
"""
import time

import pygame

from config.design_system import TEMA, ds
from config.instrumentos import (ORDEM_INSTRUMENTOS, config_instrumento,
                                 desenhar_diagrama, nota_da_casa, NOTAS)
from core.i18n import _t
from core.modulos.detector_palhetadas import DetectorPalhetadas

# --- escalas usadas nos padroes melodicos ----------------------------------
ESCALAS = {
    'maior':        {'nome': 'Maior',            'int': [0, 2, 4, 5, 7, 9, 11]},
    'menor_nat':    {'nome': 'Menor natural',    'int': [0, 2, 3, 5, 7, 8, 10]},
    'menor_harm':   {'nome': 'Menor harmonica',  'int': [0, 2, 3, 5, 7, 8, 11]},
    'penta_maior':  {'nome': 'Pentatonica maior','int': [0, 2, 4, 7, 9]},
    'penta_menor':  {'nome': 'Pentatonica menor','int': [0, 3, 5, 7, 10]},
    'blues':        {'nome': 'Blues',            'int': [0, 3, 5, 6, 7, 10]},
    'dorico':       {'nome': 'Dorico',           'int': [0, 2, 3, 5, 7, 9, 10]},
    'mixolidio':    {'nome': 'Mixolidio',        'int': [0, 2, 4, 5, 7, 9, 10]},
}

# --- padroes melodicos: deslocamentos sobre os graus da escala -------------
PADROES_MELODICOS = [
    {'nome': 'Escala direta', 'passos': [0], 'salto': 1,
     'descricao': 'Sobe e desce grau a grau. Base de tudo.'},
    {'nome': 'Grupos de 3', 'passos': [0, 1, 2], 'salto': 1,
     'descricao': 'Tres notas por grau. Fluencia e articulacao.'},
    {'nome': 'Grupos de 4', 'passos': [0, 1, 2, 3], 'salto': 1,
     'descricao': 'Classico do estudo tecnico: 1-2-3-4, 2-3-4-5...'},
    {'nome': 'Tercas', 'passos': [0, 2], 'salto': 1,
     'descricao': 'Intervalo de terca. Abre o ouvido para harmonia.'},
    {'nome': 'Quartas', 'passos': [0, 3], 'salto': 1,
     'descricao': 'Som mais moderno, menos escalar.'},
    {'nome': 'Arpejo 1-3-5', 'passos': [0, 2, 4], 'salto': 1,
     'descricao': 'Triade sobre cada grau da escala.'},
    {'nome': 'Arpejo 1-3-5-7', 'passos': [0, 2, 4, 6], 'salto': 1,
     'descricao': 'Tetrade sobre cada grau. Vocabulario de jazz.'},
    {'nome': 'Escada 3-2-1', 'passos': [2, 1, 0], 'salto': 1,
     'descricao': 'Desce dentro do grupo enquanto sobe na escala.'},
    {'nome': 'Zigue-zague', 'passos': [0, 2, 1, 3], 'salto': 1,
     'descricao': 'Quebra a linearidade sem sair da escala.'},
    {'nome': 'Pedal na tonica', 'passos': [0, -99], 'salto': 1,
     'descricao': 'Alterna cada grau com a tonica. Cria tensao.'},
]

DIRECOES = ['Ascendente', 'Descendente', 'Alternado']

# --- celulas ritmicas -------------------------------------------------------
# duracao em fracao de tempo (1.0 = semínima), acentuada?
PADROES_RITMICOS = [
    {'nome': 'Seminimas', 'celula': [(1.0, True), (1.0, False), (1.0, False), (1.0, False)],
     'descricao': 'Um ataque por tempo. Comece por aqui.'},
    {'nome': 'Colcheias', 'celula': [(0.5, True), (0.5, False)] * 4,
     'descricao': 'Dois ataques por tempo, bem regulares.'},
    {'nome': 'Tercinas', 'celula': [(1/3, True), (1/3, False), (1/3, False)] * 2,
     'descricao': 'Tres por tempo. Base do shuffle e do blues.'},
    {'nome': 'Semicolcheias', 'celula': [(0.25, True)] + [(0.25, False)] * 3,
     'descricao': 'Quatro por tempo. Exige pulso firme.'},
    {'nome': 'Sincope', 'celula': [(0.5, True), (1.0, True), (0.5, False)],
     'descricao': 'O acento cai fora do tempo forte.'},
    {'nome': 'Galope', 'celula': [(0.5, True), (0.25, False), (0.25, False)],
     'descricao': 'Longa e duas curtas. Marca do rock e do metal.'},
    {'nome': 'Galope invertido', 'celula': [(0.25, True), (0.25, False), (0.5, False)],
     'descricao': 'O contrario do galope, mais nervoso.'},
    {'nome': '3+3+2', 'celula': [(0.75, True), (0.75, True), (0.5, True)],
     'descricao': 'Divisao latina, presente em quase toda musica popular.'},
    {'nome': 'Contratempo', 'celula': [(0.5, False), (0.5, True)] * 2,
     'descricao': 'So a segunda colcheia soa. Treina o silencio.'},
]

MODOS = ['Melodicos', 'Ritmicos']


def notas_da_escala(tonica, chave_escala):
    """Notas da escala, em ordem, comecando pela tonica."""
    escala = ESCALAS[chave_escala]
    base = NOTAS.index(tonica) if tonica in NOTAS else 0
    return [NOTAS[(base + i) % 12] for i in escala['int']]


def gerar_sequencia(tonica, chave_escala, padrao, direcao='Ascendente', voltas=1):
    """
        Como funciona: Aplica os deslocamentos do padrao sobre os graus da
        escala, gerando a ordem em que as notas devem ser tocadas.
        Para que serve: Transformar 'tercas em Do maior' numa lista concreta.
        Onde e usada: Estudo de padroes melodicos.
    """
    graus = notas_da_escala(tonica, chave_escala)
    n = len(graus)
    sequencia = []
    for inicio in range(n):
        for passo in padrao['passos']:
            indice = 0 if passo == -99 else (inicio + passo) % n
            sequencia.append((indice, graus[indice]))
    if direcao == 'Descendente':
        sequencia.reverse()
    elif direcao == 'Alternado':
        sequencia = sequencia + list(reversed(sequencia))
    return sequencia * max(1, voltas)


class EstudoPadroes:
    """
        Como funciona: Dois modos no mesmo painel. Em Melodicos, percorre uma
        sequencia gerada sobre a escala; em Ritmicos, roda a celula escolhida
        no metronomo e confere os ataques do instrumento.
        Para que serve: Estudo dirigido de tecnica e de tempo.
        Onde e usada: Aba Estudos, secao Padroes.
    """

    def __init__(self):
        self.modo = 0
        self.tonica = 'C'
        self.chave_escala = 'penta_menor'
        self.indice_padrao = 2
        self.indice_direcao = 0
        self.indice_ritmo = 1
        self.instrumento = 'guitarra'
        self.bpm = 70
        self.tocando = False

        self.sequencia = []
        self.posicao = 0
        self.ultimo_passo = 0.0
        self.inicio_ciclo = 0.0
        self.indice_celula = 0

        self.detector = DetectorPalhetadas()
        self.acertos = 0
        self.tentativas = 0
        self.desvios = []
        self.brilho = 0.0

        self.som_tick = None
        self.som_acento = None
        self._carregar_sons()

        self.rects_modo = []
        self.rects_padrao = []
        self.rects_tonica = []
        self.rects_escala = []
        self.rects_instrumento = []
        self.rect_direcao = pygame.Rect(0, 0, 0, 0)
        self.rect_play = pygame.Rect(0, 0, 0, 0)
        self.rect_bpm_menos = pygame.Rect(0, 0, 0, 0)
        self.rect_bpm_mais = pygame.Rect(0, 0, 0, 0)
        self._fontes = {}

    # ----------------------------------------------------------- recursos --
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

    # ------------------------------------------------------------ estado ---
    @property
    def padrao(self):
        return PADROES_MELODICOS[self.indice_padrao % len(PADROES_MELODICOS)]

    @property
    def ritmo(self):
        return PADROES_RITMICOS[self.indice_ritmo % len(PADROES_RITMICOS)]

    @property
    def duracao_celula(self):
        """Duracao total da celula ritmica, em segundos."""
        pulso = 60.0 / max(1, self.bpm)
        return sum(dur for dur, _ in self.ritmo['celula']) * pulso

    def preparar(self):
        """Regenera a sequencia melodica com os ajustes atuais."""
        self.sequencia = gerar_sequencia(
            self.tonica, self.chave_escala, self.padrao,
            DIRECOES[self.indice_direcao])
        self.posicao = 0

    def alternar_play(self):
        self.tocando = not self.tocando
        agora = time.time()
        self.ultimo_passo = agora
        self.inicio_ciclo = agora
        self.indice_celula = 0
        self.posicao = 0
        self.acertos = self.tentativas = 0
        self.desvios.clear()
        self.detector.reiniciar()
        if self.tocando and not self.sequencia:
            self.preparar()

    # ------------------------------------------------------------ logica ---
    def _avancar_melodico(self, agora):
        """Anda uma nota da sequencia a cada pulso."""
        if not self.sequencia:
            self.preparar()
        pulso = 60.0 / max(1, self.bpm)
        if agora - self.ultimo_passo >= pulso:
            self.ultimo_passo = agora
            self.posicao = (self.posicao + 1) % max(1, len(self.sequencia))
            self.brilho = 1.0
            som = self.som_acento if self.posicao == 0 and self.som_acento else self.som_tick
            if som:
                som.play()

    def _avancar_ritmico(self, agora, motor_audio):
        """Toca a celula e confere os ataques contra os tempos esperados."""
        celula = self.ritmo['celula']
        pulso = 60.0 / max(1, self.bpm)
        decorrido = agora - self.inicio_ciclo
        if decorrido >= self.duracao_celula:
            self.inicio_ciclo += self.duracao_celula
            self.indice_celula = 0
            decorrido = agora - self.inicio_ciclo

        # Instantes de cada ataque dentro da celula
        instantes, acumulado = [], 0.0
        for duracao, acentuada in celula:
            instantes.append((acumulado * pulso, acentuada))
            acumulado += duracao

        while (self.indice_celula < len(instantes)
               and decorrido >= instantes[self.indice_celula][0]):
            acentuada = instantes[self.indice_celula][1]
            som = self.som_acento if acentuada and self.som_acento else self.som_tick
            if som:
                som.play()
            self.brilho = 1.0
            self.indice_celula += 1

        if motor_audio is not None and hasattr(motor_audio, 'buffer'):
            try:
                if self.detector.processar_buffer(motor_audio.buffer, agora):
                    self.tentativas += 1
                    esperado = min((abs(decorrido - t) for t, _ in instantes),
                                   default=99)
                    self.desvios.append(esperado * 1000)
                    if esperado < 0.12:
                        self.acertos += 1
            except Exception:
                pass

    def atualizar(self, motor_audio=None):
        """Avanca o estudo conforme o modo escolhido."""
        if not self.tocando:
            return
        agora = time.time()
        self.brilho = max(0.0, self.brilho - 0.08)
        if MODOS[self.modo] == 'Melodicos':
            self._avancar_melodico(agora)
        else:
            self._avancar_ritmico(agora, motor_audio)

    # ------------------------------------------------------------ desenho --
    def _barra_ajustes(self, tela, rect, fontes):
        """Modo, tonica, escala/celula, instrumento, andamento e play."""
        pos_mouse = pygame.mouse.get_pos()
        fonte = self._fonte(12)
        y = rect.y

        # Modo
        self.rects_modo = []
        for i, nome in enumerate(MODOS):
            r = pygame.Rect(rect.x + i * 108, y, 100, 26)
            self.rects_modo.append(r)
            ds.chip(tela, r, _t(nome), fonte, ativo=i == self.modo)

        # Andamento e play, a direita
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
        # Tonica
        self.rects_tonica = []
        largura = min(34, (rect.width * 0.45 - 11 * 3) / 12)
        for i, nota in enumerate(NOTAS):
            r = pygame.Rect(int(rect.x + i * (largura + 3)), y, int(largura), 24)
            self.rects_tonica.append(r)
            ds.chip(tela, r, nota, self._fonte(11), ativo=nota == self.tonica)

        # Instrumento
        self.rects_instrumento = []
        x = rect.right
        for chave in reversed(ORDEM_INSTRUMENTOS):
            nome = config_instrumento(chave)['nome'].split(' (')[0]
            larg = fonte.size(nome)[0] + 16
            r = pygame.Rect(x - larg, y, larg, 24)
            if r.x < rect.x + rect.width * 0.5:
                break
            self.rects_instrumento.insert(0, (r, chave))
            ds.chip(tela, r, nome, self._fonte(11), ativo=chave == self.instrumento)
            x -= larg + 4
        return y + 30

    def _lista_lateral(self, tela, rect, fontes):
        """Escalas + padroes (melodico) ou celulas ritmicas."""
        self.rects_escala = []
        self.rects_padrao = []
        fonte = self._fonte(12)
        y = rect.y

        if MODOS[self.modo] == 'Melodicos':
            ds.rotulo_secao(tela, rect.x, y, _t('Escala'), fontes['pequena'],
                            TEMA.acento, largura_max=rect.width)
            y += fontes['pequena'].get_height() + 4
            chaves = list(ESCALAS)
            colunas = 2
            larg = (rect.width - 4) // colunas
            for i, chave in enumerate(chaves):
                r = pygame.Rect(rect.x + (i % colunas) * (larg + 4),
                                y + (i // colunas) * 26, larg, 22)
                self.rects_escala.append((r, chave))
                ds.chip(tela, r, _t(ESCALAS[chave]['nome']), self._fonte(11),
                        ativo=chave == self.chave_escala)
            y += ((len(chaves) + colunas - 1) // colunas) * 26 + 8

            ds.rotulo_secao(tela, rect.x, y, _t('Padrao'), fontes['pequena'],
                            TEMA.acento, largura_max=rect.width)
            y += fontes['pequena'].get_height() + 4
            lista = PADROES_MELODICOS
            selecionado = self.indice_padrao
        else:
            ds.rotulo_secao(tela, rect.x, y, _t('Celula ritmica'), fontes['pequena'],
                            TEMA.acento, largura_max=rect.width)
            y += fontes['pequena'].get_height() + 4
            lista = PADROES_RITMICOS
            selecionado = self.indice_ritmo

        altura_item = 24
        for i, item in enumerate(lista):
            if y + altura_item > rect.bottom:
                break
            r = pygame.Rect(rect.x, y, rect.width, altura_item)
            self.rects_padrao.append(r)
            ativo = i == selecionado % len(lista)
            if ativo:
                ds.superficie_translucida(
                    tela, r, ds.misturar(TEMA.superficie_alt, TEMA.acento, 0.3),
                    230, ds.RAIO_SM, TEMA.acento, 1)
            ds.texto_em(tela, _t(item['nome']), fonte,
                        (r.x + ds.ESPACO_SM, r.centery),
                        TEMA.texto if ativo else TEMA.texto_suave, ancora='midleft',
                        largura_max=r.width - ds.ESPACO_MD)
            y += altura_item + 2

    def _desenhar_melodico(self, tela, rect, fontes):
        """Diagrama do instrumento com a nota atual e a ordem da sequencia."""
        if not self.sequencia:
            self.preparar()
        atual = self.sequencia[self.posicao % len(self.sequencia)] if self.sequencia else None
        graus = notas_da_escala(self.tonica, self.chave_escala)

        destaques = {}
        cfg = config_instrumento(self.instrumento)
        alvo = atual[1] if atual else None
        if cfg['familia'] == 'corda':
            for i, solta in enumerate(cfg['cordas']):
                for casa in range(cfg['casas'] + 1):
                    nome = nota_da_casa(solta, casa)
                    if nome == alvo:
                        destaques[(i, casa)] = (TEMA.aviso, nome)
                    elif nome in graus:
                        cor = TEMA.acento if nome == self.tonica else TEMA.superficie_alt
                        destaques[(i, casa)] = (cor, nome)
        else:
            for i in range(cfg.get('num_oitavas', 2) * 12):
                nome = NOTAS[i % 12]
                if nome == alvo:
                    destaques[i] = (TEMA.aviso, nome)
                elif nome in graus:
                    destaques[i] = (TEMA.acento if nome == self.tonica
                                    else TEMA.superficie_alt, nome)

        altura_seq = 34
        rect_diagrama = pygame.Rect(rect.x, rect.y, rect.width,
                                    rect.height - altura_seq - ds.ESPACO_SM)
        desenhar_diagrama(tela, rect_diagrama, self.instrumento, destaques,
                          self._fonte(11))

        # Fita com a ordem das proximas notas
        fita = pygame.Rect(rect.x, rect.bottom - altura_seq, rect.width, altura_seq)
        ds.superficie_translucida(tela, fita, TEMA.superficie_alt, 200, ds.RAIO_SM,
                                  TEMA.borda, 1)
        if self.sequencia:
            visiveis = 14
            inicio = self.posicao
            largura = fita.width / visiveis
            for k in range(visiveis):
                indice = (inicio + k) % len(self.sequencia)
                _, nome = self.sequencia[indice]
                celula = pygame.Rect(int(fita.x + k * largura), fita.y + 4,
                                     int(largura) - 3, fita.height - 8)
                if k == 0:
                    ds.superficie_translucida(tela, celula, TEMA.aviso,
                                              int(120 + self.brilho * 100),
                                              ds.RAIO_SM, TEMA.aviso, 1)
                ds.texto_centralizado(tela, nome, self._fonte(12), celula,
                                      TEMA.aviso if k == 0 else TEMA.texto_suave)

    def _desenhar_ritmico(self, tela, rect, fontes):
        """Notacao simplificada da celula e placar de precisao."""
        celula = self.ritmo['celula']
        total = sum(d for d, _ in celula)

        pauta = pygame.Rect(rect.x, rect.y + 12, rect.width, 92)
        ds.superficie_translucida(tela, pauta, TEMA.superficie_alt, 200, ds.RAIO_MD,
                                  TEMA.borda, 1)
        y_linha = pauta.centery + 14
        pygame.draw.line(tela, ds.rgb(TEMA.borda),
                         (pauta.x + 16, y_linha), (pauta.right - 16, y_linha), 2)

        x = pauta.x + 24
        largura_util = pauta.width - 48
        for i, (duracao, acentuada) in enumerate(celula):
            largura = largura_util * (duracao / total)
            cx = x + largura / 2
            ativa = self.tocando and i == max(0, self.indice_celula - 1)
            cor = TEMA.aviso if ativa else (TEMA.acento if acentuada else TEMA.texto_apagado)
            raio = 9 if duracao >= 0.5 else 7
            pygame.draw.ellipse(tela, ds.rgb(cor),
                                (int(cx - raio - 2), int(y_linha - raio), raio * 2 + 4, raio * 2))
            pygame.draw.line(tela, ds.rgb(cor), (cx + raio, y_linha),
                             (cx + raio, y_linha - 30), 2)
            if duracao <= 0.5:   # colchete das figuras curtas
                pygame.draw.line(tela, ds.rgb(cor), (cx + raio, y_linha - 30),
                                 (cx + raio + 9, y_linha - 24), 2)
            if duracao <= 0.25:
                pygame.draw.line(tela, ds.rgb(cor), (cx + raio, y_linha - 24),
                                 (cx + raio + 9, y_linha - 18), 2)
            ds.texto_em(tela, f'{duracao:.2f}'.rstrip('0').rstrip('.'),
                        self._fonte(10), (cx, y_linha + 16), TEMA.texto_apagado,
                        ancora='midtop')
            x += largura

        ds.texto_em(tela, _t(self.ritmo['descricao']), self._fonte(12),
                    (rect.x, pauta.bottom + 10), TEMA.texto_suave,
                    largura_max=rect.width)

        if self.tentativas:
            precisao = int(self.acertos / self.tentativas * 100)
            medio = sum(self.desvios) / len(self.desvios) if self.desvios else 0
            ds.texto_em(tela, f"{_t('Precisao')}: {precisao}%   "
                              f"{_t('Desvio medio')}: {medio:.0f} ms",
                        self._fonte(13), (rect.x, pauta.bottom + 32), TEMA.verde)

    def desenhar(self, tela, estado, fontes, meio_x, meio_y, cam_x, cam_y,
                 motor_audio=None):
        """
            Como funciona: Barra de ajustes no topo, lista a esquerda e o
            conteudo do modo a direita.
            Para que serve: Tela do estudo de padroes.
            Onde e usada: Chamada pelo gerenciador de estudos.
        """
        self.atualizar(motor_audio)

        largura = getattr(estado, 'LARGURA_TELA', 1280)
        altura = getattr(estado, 'ALTURA_TELA', 720)
        area = pygame.Rect(int(cam_x + 40), int(cam_y + 56),
                           int(largura - 80), int(altura - 130))
        ds.painel(tela, area, None, None, acento=TEMA.acento, alpha=235)

        interno = area.inflate(-ds.ESPACO_XL * 2, -ds.ESPACO_XL * 2)
        y_conteudo = self._barra_ajustes(tela, interno, fontes)

        largura_lista = max(180, int(interno.width * 0.24))
        col_lista = pygame.Rect(interno.x, y_conteudo + ds.ESPACO_SM,
                                largura_lista, interno.bottom - y_conteudo - ds.ESPACO_SM)
        col_conteudo = pygame.Rect(col_lista.right + ds.ESPACO_LG, col_lista.y,
                                   interno.right - col_lista.right - ds.ESPACO_LG,
                                   col_lista.height)

        self._lista_lateral(tela, col_lista, fontes)
        if MODOS[self.modo] == 'Melodicos':
            self._desenhar_melodico(tela, col_conteudo, fontes)
        else:
            self._desenhar_ritmico(tela, col_conteudo, fontes)

    # ------------------------------------------------------------- clique --
    def tratar_cliques(self, pos, estado):
        """Trata todos os controles do estudo de padroes."""
        for i, r in enumerate(self.rects_modo):
            if r.collidepoint(pos):
                self.modo = i
                return True
        if self.rect_play.collidepoint(pos):
            self.alternar_play(); return True
        if self.rect_bpm_menos.collidepoint(pos):
            self.bpm = max(30, self.bpm - 5); return True
        if self.rect_bpm_mais.collidepoint(pos):
            self.bpm = min(240, self.bpm + 5); return True
        for i, r in enumerate(self.rects_tonica):
            if r.collidepoint(pos):
                self.tonica = NOTAS[i]; self.preparar(); return True
        for r, chave in self.rects_instrumento:
            if r.collidepoint(pos):
                self.instrumento = chave; return True
        for r, chave in self.rects_escala:
            if r.collidepoint(pos):
                self.chave_escala = chave; self.preparar(); return True
        for i, r in enumerate(self.rects_padrao):
            if r.collidepoint(pos):
                if MODOS[self.modo] == 'Melodicos':
                    self.indice_padrao = i; self.preparar()
                else:
                    self.indice_ritmo = i
                    self.inicio_ciclo = time.time(); self.indice_celula = 0
                return True
        return False
