# -*- coding: utf-8 -*-
"""
Jogo Acerte a Nota.

As notas descem sobre uma pauta de cinco linhas, desenhadas como figuras
musicais (cabeca, haste e acidente quando houver). Ao cruzar a faixa de
acerto, a nota captada pelo microfone precisa bater com a figura. Nos niveis
mais altos tambem e exigido um ataque no tempo certo, entao vale a precisao
ritmica e nao so a altura.
"""
import math
import os
import random
import sys
import time

import numpy as np
import pygame

from config.design_system import TEMA, ds
from core.i18n import _t
from core.modulos.escalas import equivalencia_notas
from core.modulos.detector_palhetadas import DetectorPalhetadas

NOTAS_NATURAIS = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
NOTAS_SUSTENIDOS = ['C#', 'D#', 'F#', 'G#', 'A#']
NOTAS_BEMOIS = ['Db', 'Eb', 'Gb', 'Ab', 'Bb']

FREQUENCIAS = {
    'C': 261.63, 'C#': 277.18, 'Db': 277.18, 'D': 293.66, 'D#': 311.13,
    'Eb': 311.13, 'E': 329.63, 'F': 349.23, 'F#': 369.99, 'Gb': 369.99,
    'G': 392.0, 'G#': 415.30, 'Ab': 415.30, 'A': 440.0, 'A#': 466.16,
    'Bb': 466.16, 'B': 493.88,
}

# nome, notas extras no sorteio, quantas por leva, exige ataque no tempo
DIFICULDADES = [
    {'nome': 'Facil', 'extras': [], 'quantidade': (1, 1), 'exige_ataque': False},
    {'nome': 'Media', 'extras': NOTAS_SUSTENIDOS, 'quantidade': (1, 2), 'exige_ataque': False},
    {'nome': 'Dificil', 'extras': NOTAS_SUSTENIDOS, 'quantidade': (2, 3), 'exige_ataque': True},
    {'nome': 'Impossivel', 'extras': NOTAS_SUSTENIDOS + NOTAS_BEMOIS,
     'quantidade': (3, 5), 'exige_ataque': True},
]

MODOS_AUDIO = ['Desligado', 'Voz (nome)', 'Som (nota)']

# Graus da pauta: cada nota natural ocupa uma linha ou um espaco
GRAU_NA_PAUTA = {'C': 0, 'D': 1, 'E': 2, 'F': 3, 'G': 4, 'A': 5, 'B': 6}


class AcerteANota:
    """
        Como funciona: Faz descer figuras musicais sobre uma pauta e compara a
        nota captada com a figura que cruza a faixa de acerto.
        Para que serve: Treinar o reconhecimento das notas no instrumento.
        Onde e usada: Instanciada pelo gerenciador de jogos.
    """

    ALTURA_FAIXA_ACERTO = 74
    JANELA_ATAQUE = 0.25          # segundos de tolerancia para o ataque
    RAIO_CABECA = 17

    def __init__(self):
        self.detector = DetectorPalhetadas()

        # --- estado de jogo -------------------------------------------------
        self.jogo_iniciado = False
        self.pontuacao = 0
        self.sequencia = 0
        self.melhor_sequencia = 0
        self.acertos = 0
        self.erros = 0
        self.notas_na_tela = []
        self.particulas = []
        self.ultimo_spawn = 0.0

        # --- ajustes --------------------------------------------------------
        self.idx_dificuldade = 0
        self.velocidade = 50
        self.idx_audio = 0
        self.metronomo_on = True
        self.idx_dispositivo = 0

        # --- leitura de audio ------------------------------------------------
        self.nota_ouvida = ''
        self.nivel_volume = 0.0
        self.houve_ataque = False
        self.instante_ataque = 0.0

        # --- retorno visual ---------------------------------------------------
        self.mensagem = ''
        self.cor_mensagem = None
        self.mensagem_ate = 0.0
        self.brilho_faixa = 0.0

        # --- audio de apoio ---------------------------------------------------
        self.fila_audio = []
        self.duracao_permitida = 0.0
        self.tempo_inicio_fala = 0.0
        self.ultimo_tick_ms = 0
        self.som_tick = None
        self.som_acento = None
        self.sons_vozes = {}
        self.sons_sintetizados = {}
        self.canal_voz = None

        # --- retangulos de interacao -------------------------------------------
        self.btn_play = pygame.Rect(0, 0, 300, 52)
        self.btn_dif_esq = pygame.Rect(0, 0, 32, 32)
        self.btn_dif_dir = pygame.Rect(0, 0, 32, 32)
        self.btn_vel_esq = pygame.Rect(0, 0, 32, 32)
        self.btn_vel_dir = pygame.Rect(0, 0, 32, 32)
        self.btn_aud_esq = pygame.Rect(0, 0, 32, 32)
        self.btn_aud_dir = pygame.Rect(0, 0, 32, 32)
        self.btn_disp_esq = pygame.Rect(0, 0, 32, 32)
        self.btn_disp_dir = pygame.Rect(0, 0, 32, 32)
        self.btn_metronomo = pygame.Rect(0, 0, 26, 26)
        self.lista_dispositivos = []

        self._fontes = {}
        self._carregar_recursos()

    # ------------------------------------------------------------- recursos
    def _fonte(self, tamanho, negrito=True):
        chave = (tamanho, negrito)
        if chave not in self._fontes:
            self._fontes[chave] = pygame.font.SysFont('Arial', tamanho, bold=negrito)
        return self._fontes[chave]

    def _pasta_raiz(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _gerar_amostra(self, freq, duracao=0.9, sample_rate=44100):
        """Sintetiza a nota com decaimento, de forma vetorizada."""
        n = int(sample_rate * duracao)
        t = np.arange(n) / sample_rate
        envelope = np.clip(np.linspace(1.0, 0.0, n) * 1.4, 0.0, 1.0)
        onda = (np.sin(2 * np.pi * freq * t)
                + 0.35 * np.sin(4 * np.pi * freq * t)
                + 0.15 * np.sin(6 * np.pi * freq * t))
        onda = onda / np.max(np.abs(onda)) * envelope * 16384
        return pygame.mixer.Sound(onda.astype(np.int16))

    def _carregar_recursos(self):
        """Carrega vozes, sintetiza notas e prepara o metronomo."""
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=1)
            except pygame.error:
                return
        try:
            pygame.mixer.set_num_channels(32)
            self.canal_voz = pygame.mixer.Channel(0)
        except pygame.error:
            self.canal_voz = None

        pasta = os.path.join(self._pasta_raiz(), 'assets', 'audio')
        for nome in NOTAS_NATURAIS + NOTAS_SUSTENIDOS + NOTAS_BEMOIS:
            caminho = os.path.join(pasta, f'{nome}.wav')
            if os.path.exists(caminho):
                try:
                    self.sons_vozes[nome] = pygame.mixer.Sound(caminho)
                except pygame.error:
                    pass
            if nome in FREQUENCIAS:
                try:
                    self.sons_sintetizados[nome] = self._gerar_amostra(FREQUENCIAS[nome])
                except (pygame.error, ValueError):
                    pass

        for atributo, arquivo in (('som_tick', 'tick.wav'), ('som_acento', 'tick_high.wav')):
            caminho = os.path.join(pasta, arquivo)
            if os.path.exists(caminho):
                try:
                    setattr(self, atributo, pygame.mixer.Sound(caminho))
                except pygame.error:
                    pass

        try:
            import sounddevice as sd
            self.lista_dispositivos = [
                {'id': i, 'name': d['name']}
                for i, d in enumerate(sd.query_devices())
                if d['max_input_channels'] > 0]
        except Exception:
            self.lista_dispositivos = []

    # ---------------------------------------------------------- ajustes ---
    @property
    def dificuldade(self):
        return DIFICULDADES[self.idx_dificuldade]

    def reiniciar_partida(self):
        """Zera a partida, mantendo os ajustes escolhidos."""
        self.pontuacao = 0
        self.sequencia = 0
        self.acertos = 0
        self.erros = 0
        self.notas_na_tela.clear()
        self.particulas.clear()
        self.fila_audio.clear()
        self.detector.reiniciar()
        self.ultimo_spawn = time.time()
        self.mensagem = ''

    # ------------------------------------------------------------- audio --
    def _ler_audio(self, estado, motor_audio):
        """Atualiza nota ouvida, nivel e ataque a partir do motor de audio."""
        self.nota_ouvida = getattr(estado, 'nota_atual_detectada', '--')
        if self.nota_ouvida == '--':
            self.nota_ouvida = ''

        self.houve_ataque = False
        if motor_audio is not None and hasattr(motor_audio, 'buffer'):
            try:
                if self.detector.processar_buffer(motor_audio.buffer):
                    self.houve_ataque = True
                    self.instante_ataque = time.time()
            except Exception:
                pass

        alvo = 1.0 if self.nota_ouvida else 0.0
        self.nivel_volume += (alvo - self.nivel_volume) * 0.25

    def _tocar_fila(self):
        """Fala ou toca a proxima nota da fila, respeitando a dificuldade."""
        if MODOS_AUDIO[self.idx_audio] == 'Desligado' or not self.fila_audio:
            return
        if self.canal_voz is None:
            self.fila_audio.clear()
            return

        agora = time.time()
        fator = max(0.35, 1.0 - self.idx_dificuldade * 0.12 - self.velocidade / 400.0)
        if not self.canal_voz.get_busy():
            nota = self.fila_audio.pop(0)
            biblioteca = (self.sons_vozes if MODOS_AUDIO[self.idx_audio] == 'Voz (nome)'
                          else self.sons_sintetizados)
            som = biblioteca.get(nota)
            if som:
                self.duracao_permitida = som.get_length() * fator
                self.tempo_inicio_fala = agora
                self.canal_voz.play(som)
        elif agora - self.tempo_inicio_fala >= self.duracao_permitida:
            self.canal_voz.stop()

    def _pulsar_metronomo(self, mult_vel):
        """Toca o clique no andamento correspondente a velocidade escolhida."""
        if not (self.jogo_iniciado and self.metronomo_on and self.som_tick):
            return
        bpm = 60 + self.velocidade * 1.2 * mult_vel
        intervalo = 60000 / max(1.0, bpm)
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tick_ms >= intervalo:
            self.ultimo_tick_ms = agora
            self.som_tick.play()

    # ------------------------------------------------------------ logica --
    def _sortear_notas(self, largura, mult_vel):
        """Cria novas figuras no topo conforme a dificuldade."""
        agora = time.time()
        intervalo = max(0.45, (4.6 - self.velocidade / 100.0 * 3.4) / max(0.2, mult_vel))
        if agora - self.ultimo_spawn < intervalo:
            return
        self.ultimo_spawn = agora

        dif = self.dificuldade
        pool = NOTAS_NATURAIS + dif['extras']
        minimo, maximo = dif['quantidade']
        colunas = max(1, (largura - 260) // 150)

        usadas = set()
        for _ in range(random.randint(minimo, maximo)):
            nota = random.choice(pool)
            coluna = random.randrange(colunas)
            if coluna in usadas:
                coluna = (coluna + 1) % colunas
            usadas.add(coluna)
            if MODOS_AUDIO[self.idx_audio] != 'Desligado':
                self.fila_audio.append(nota)
            self.notas_na_tela.append({
                'nota': nota,
                'x': 150 + coluna * 150 + random.randint(-12, 12),
                'y': -40.0,
                'resolvida': False,
                'brilho': 0.0,
            })

    def _faiscas(self, x, y, cor):
        for _ in range(16):
            angulo = random.uniform(0, math.tau)
            velocidade = random.uniform(1.5, 6.0)
            self.particulas.append({
                'x': x, 'y': y,
                'vx': math.cos(angulo) * velocidade,
                'vy': math.sin(angulo) * velocidade,
                'vida': 1.0, 'cor': cor})

    def _avisar(self, texto, cor):
        self.mensagem = texto
        self.cor_mensagem = cor
        self.mensagem_ate = time.time() + 0.9

    def _resolver_notas(self, y_faixa, mult_vel, altura):
        """Move as figuras e decide acerto ou erro ao cruzar a faixa."""
        agora = time.time()
        exige_ataque = self.dificuldade['exige_ataque']
        topo = y_faixa - self.ALTURA_FAIXA_ACERTO / 2
        base = y_faixa + self.ALTURA_FAIXA_ACERTO / 2

        for nota in self.notas_na_tela[:]:
            nota['y'] += (1.1 + self.velocidade / 45.0) * mult_vel
            nota['brilho'] = max(0.0, nota['brilho'] - 0.06)

            if nota['resolvida']:
                if nota['y'] > altura + 60:
                    self.notas_na_tela.remove(nota)
                continue

            na_faixa = topo <= nota['y'] <= base
            if na_faixa and self.nota_ouvida and equivalencia_notas(self.nota_ouvida,
                                                                    nota['nota']):
                no_tempo = (not exige_ataque
                            or (agora - self.instante_ataque) <= self.JANELA_ATAQUE)
                if no_tempo:
                    nota['resolvida'] = True
                    nota['brilho'] = 1.0
                    self.sequencia += 1
                    self.melhor_sequencia = max(self.melhor_sequencia, self.sequencia)
                    self.acertos += 1
                    bonus = 1 + self.sequencia // 5
                    self.pontuacao += 10 * bonus
                    self.brilho_faixa = 1.0
                    self._faiscas(nota['x'], nota['y'], TEMA.verde)
                    self._avisar(_t('Acertou') + (f'  x{bonus}' if bonus > 1 else ''),
                                 TEMA.verde)
                    continue

            if nota['y'] > base:
                self.notas_na_tela.remove(nota)
                self.sequencia = 0
                self.erros += 1
                self._avisar(_t('Passou'), TEMA.alerta)

    # ------------------------------------------------------------ desenho --
    def _desenhar_pauta(self, tela, rect, y_faixa):
        """Cinco linhas da pauta e a faixa de acerto."""
        espaco = 26
        y_centro = rect.y + rect.height * 0.34
        for i in range(-2, 3):
            y = y_centro + i * espaco
            pygame.draw.line(tela, ds.rgb(ds.misturar(TEMA.borda, TEMA.fundo, 0.35)),
                             (rect.x + 40, y), (rect.right - 40, y), 1)

        # Faixa de acerto: onde a figura precisa ser tocada
        altura = self.ALTURA_FAIXA_ACERTO
        faixa = pygame.Rect(rect.x, y_faixa - altura // 2, rect.width, altura)
        intensidade = int(26 + self.brilho_faixa * 90)
        superficie = pygame.Surface((faixa.width, faixa.height), pygame.SRCALPHA)
        superficie.fill(ds.com_alpha(TEMA.acento, intensidade))
        tela.blit(superficie, faixa.topleft)
        pygame.draw.line(tela, ds.rgb(TEMA.acento),
                         (faixa.x, faixa.centery), (faixa.right, faixa.centery), 3)
        self.brilho_faixa = max(0.0, self.brilho_faixa - 0.05)

    def _desenhar_figura(self, tela, nota, fonte):
        """Uma figura musical: acidente, cabeca inclinada, haste e nome."""
        x, y = int(nota['x']), int(nota['y'])
        nome = nota['nota']
        natural = nome[0]
        acidente = nome[1:] if len(nome) > 1 else ''

        if nota['resolvida']:
            cor = TEMA.verde
        elif acidente:
            cor = TEMA.roxo if acidente == 'b' else TEMA.ciano
        else:
            cor = TEMA.acento

        raio = self.RAIO_CABECA
        if nota['brilho'] > 0:
            halo = pygame.Surface((raio * 6, raio * 6), pygame.SRCALPHA)
            pygame.draw.circle(halo, ds.com_alpha(cor, int(120 * nota['brilho'])),
                               (raio * 3, raio * 3), int(raio * 2.2))
            tela.blit(halo, (x - raio * 3, y - raio * 3))

        # Haste, do lado direito da cabeca
        pygame.draw.line(tela, ds.rgb(cor), (x + raio - 2, y),
                         (x + raio - 2, y - raio * 3), 3)

        # Cabeca: elipse levemente inclinada, como na notacao
        cabeca = pygame.Surface((raio * 2 + 6, raio * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(cabeca, ds.rgb(cor), (0, 0, raio * 2 + 6, raio * 2))
        cabeca = pygame.transform.rotate(cabeca, 18)
        tela.blit(cabeca, (x - cabeca.get_width() // 2, y - cabeca.get_height() // 2))

        ds.texto_em(tela, natural, fonte, (x, y), ds.contraste_texto(cor),
                    ancora='center')
        if acidente:
            simbolo = '#' if acidente == '#' else 'b'
            ds.texto_em(tela, simbolo, self._fonte(17),
                        (x - raio - 8, y - 2), cor, ancora='center')

    def _desenhar_hud(self, tela, rect, fonte_ui, fonte_p):
        """Placar, sequencia e precisao no alto da tela."""
        total = self.acertos + self.erros
        precisao = int(self.acertos / total * 100) if total else 0

        cartao = pygame.Rect(rect.right - 250, rect.y + 16, 234, 92)
        ds.painel(tela, cartao, None, None, acento=TEMA.acento, alpha=225)
        ds.texto_em(tela, str(self.pontuacao), self._fonte(30),
                    (cartao.centerx, cartao.y + 8), TEMA.aviso, ancora='midtop')
        ds.texto_em(tela, _t('pontos'), fonte_p,
                    (cartao.centerx, cartao.y + 42), TEMA.texto_apagado, ancora='midtop')
        ds.texto_em(tela, f"{_t('Sequencia')}: {self.sequencia}", fonte_p,
                    (cartao.x + ds.ESPACO_MD, cartao.bottom - 22), TEMA.verde)
        ds.texto_em(tela, f'{precisao}%', fonte_p,
                    (cartao.right - ds.ESPACO_MD, cartao.bottom - 22),
                    TEMA.texto_suave, ancora='topright')

        # Nota ouvida agora
        chip = pygame.Rect(rect.x + 20, rect.y + 16, 150, 54)
        ds.painel(tela, chip, None, None,
                  acento=TEMA.verde if self.nota_ouvida else TEMA.borda, alpha=225)
        ds.texto_em(tela, self.nota_ouvida or '--', self._fonte(24),
                    (chip.centerx, chip.centery - 6),
                    TEMA.verde if self.nota_ouvida else TEMA.texto_apagado,
                    ancora='center')
        ds.texto_em(tela, _t('ouvindo'), self._fonte(11),
                    (chip.centerx, chip.bottom - 14), TEMA.texto_apagado, ancora='center')

        if self.mensagem and time.time() < self.mensagem_ate:
            ds.texto_em(tela, self.mensagem, self._fonte(26),
                        (rect.centerx, rect.y + 30), self.cor_mensagem or TEMA.texto,
                        ancora='midtop')

    def _desenhar_ajustes(self, tela, rect, fonte_ui, fonte_p):
        """Tela inicial: escolha de dificuldade, velocidade, audio e entrada."""
        largura = min(520, rect.width - 80)
        altura = 380
        painel = pygame.Rect(0, 0, largura, altura)
        painel.center = rect.center
        ds.painel(tela, painel, None, None, acento=TEMA.acento)

        ds.texto_em(tela, _t('Acerte a Nota'), self._fonte(30),
                    (painel.centerx, painel.y + 22), TEMA.texto, ancora='midtop')
        ds.texto_em(tela, _t('Toque a nota que cruzar a linha'), fonte_p,
                    (painel.centerx, painel.y + 60), TEMA.texto_apagado, ancora='midtop')

        x = painel.x + ds.ESPACO_XL
        largura_linha = painel.width - ds.ESPACO_XL * 2
        y = painel.y + 96
        pos_mouse = pygame.mouse.get_pos()

        def linha(rotulo, valor, esq, dir_, y_atual):
            ds.texto_em(tela, rotulo, fonte_p, (x, y_atual + 8), TEMA.texto_suave,
                        largura_max=largura_linha // 3)
            esq.topleft = (x + largura_linha - 210, y_atual)
            esq.size = (32, 32)
            dir_.topleft = (x + largura_linha - 32, y_atual)
            dir_.size = (32, 32)
            ds.botao(tela, esq, '<', fonte_p, variante='secundario',
                     hover=esq.collidepoint(pos_mouse))
            ds.botao(tela, dir_, '>', fonte_p, variante='secundario',
                     hover=dir_.collidepoint(pos_mouse))
            ds.texto_centralizado(
                tela, valor, fonte_p,
                pygame.Rect(esq.right, y_atual, dir_.left - esq.right, 32), TEMA.texto)
            return y_atual + 44

        y = linha(_t('Dificuldade'), _t(self.dificuldade['nome']),
                  self.btn_dif_esq, self.btn_dif_dir, y)
        y = linha(_t('Velocidade'), f'{self.velocidade}',
                  self.btn_vel_esq, self.btn_vel_dir, y)
        y = linha(_t('Guia de audio'), _t(MODOS_AUDIO[self.idx_audio]),
                  self.btn_aud_esq, self.btn_aud_dir, y)

        nome_disp = _t('Padrao do sistema')
        if self.lista_dispositivos:
            idx = self.idx_dispositivo % len(self.lista_dispositivos)
            nome_disp = self.lista_dispositivos[idx]['name'][:22]
        y = linha(_t('Entrada'), nome_disp, self.btn_disp_esq, self.btn_disp_dir, y)

        self.btn_metronomo.topleft = (x, y + 2)
        ds.caixa_selecao(tela, self.btn_metronomo, self.metronomo_on)
        ds.texto_em(tela, _t('Clique do metronomo'), fonte_p,
                    (self.btn_metronomo.right + ds.ESPACO_MD, self.btn_metronomo.centery),
                    TEMA.texto_suave, ancora='midleft')

        self.btn_play.size = (largura_linha, 48)
        self.btn_play.topleft = (x, painel.bottom - 66)
        ds.botao(tela, self.btn_play, _t('Comecar'), self._fonte(20),
                 variante='primario', hover=self.btn_play.collidepoint(pos_mouse))

    def desenhar(self, tela, largura, altura, estado, meu_gravador=None, configs=None):
        """
            Como funciona: Atualiza audio e fisica das figuras e desenha a cena.
            Para que serve: Loop visual do jogo.
            Onde e usada: Chamada pelo gerenciador de jogos a cada quadro.
        """
        if configs is not None:
            TEMA.definir_acento(configs.get_cor_tema())
        mult_vel = configs.get_vel_jogo() if configs else 1.0
        particulas_on = configs.get_particulas() if configs else True

        self._ler_audio(estado, meu_gravador)
        self._tocar_fila()
        self._pulsar_metronomo(mult_vel)

        rect = pygame.Rect(0, 0, largura, altura)
        ds.fundo_app(tela, rect)

        fonte_ui = self._fonte(20)
        fonte_p = self._fonte(14)

        if not self.jogo_iniciado:
            self._desenhar_ajustes(tela, rect, fonte_ui, fonte_p)
            return

        y_faixa = altura - 150
        self._desenhar_pauta(tela, rect, y_faixa)
        self._sortear_notas(largura, mult_vel)
        self._resolver_notas(y_faixa, mult_vel, altura)

        if particulas_on:
            for p in self.particulas[:]:
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['vy'] += 0.22
                p['vida'] -= 0.035
                if p['vida'] <= 0:
                    self.particulas.remove(p)
                    continue
                pygame.draw.circle(tela, ds.rgb(p['cor']),
                                   (int(p['x']), int(p['y'])),
                                   max(1, int(5 * p['vida'])))
        else:
            self.particulas.clear()

        fonte_nota = self._fonte(18)
        for nota in self.notas_na_tela:
            self._desenhar_figura(tela, nota, fonte_nota)

        self._desenhar_hud(tela, rect, fonte_ui, fonte_p)

        # Medidor de entrada rente ao rodape
        largura_medidor = min(320, largura // 3)
        barra = pygame.Rect(rect.centerx - largura_medidor // 2, altura - 42,
                            largura_medidor, ds.ALTURA_TRILHO)
        ds.trilho(tela, barra, self.nivel_volume,
                  TEMA.verde if self.nota_ouvida else TEMA.trilho)

    # ------------------------------------------------------------- clique --
    def tratar_clique(self, pos_mouse, meu_gravador=None):
        """
            Como funciona: Testa os controles da tela de ajustes.
            Para que serve: Trocar dificuldade, velocidade, audio, entrada e
            iniciar a partida.
            Onde e usada: Chamada pelo gerenciador de jogos.
        """
        if self.jogo_iniciado:
            return False

        if self.btn_play.collidepoint(pos_mouse):
            self.reiniciar_partida()
            self.jogo_iniciado = True
            return True
        if self.btn_metronomo.collidepoint(pos_mouse):
            self.metronomo_on = not self.metronomo_on
            return True

        if self.btn_dif_esq.collidepoint(pos_mouse):
            self.idx_dificuldade = (self.idx_dificuldade - 1) % len(DIFICULDADES)
            return True
        if self.btn_dif_dir.collidepoint(pos_mouse):
            self.idx_dificuldade = (self.idx_dificuldade + 1) % len(DIFICULDADES)
            return True

        if self.btn_vel_esq.collidepoint(pos_mouse):
            self.velocidade = max(10, self.velocidade - 10)
            return True
        if self.btn_vel_dir.collidepoint(pos_mouse):
            self.velocidade = min(100, self.velocidade + 10)
            return True

        if self.btn_aud_esq.collidepoint(pos_mouse):
            self.idx_audio = (self.idx_audio - 1) % len(MODOS_AUDIO)
            return True
        if self.btn_aud_dir.collidepoint(pos_mouse):
            self.idx_audio = (self.idx_audio + 1) % len(MODOS_AUDIO)
            return True

        if self.lista_dispositivos and (self.btn_disp_esq.collidepoint(pos_mouse)
                                        or self.btn_disp_dir.collidepoint(pos_mouse)):
            passo = -1 if self.btn_disp_esq.collidepoint(pos_mouse) else 1
            self.idx_dispositivo = (self.idx_dispositivo + passo) % len(self.lista_dispositivos)
            novo_id = self.lista_dispositivos[self.idx_dispositivo]['id']
            if meu_gravador is not None and hasattr(meu_gravador, 'mudar_dispositivo'):
                try:
                    meu_gravador.mudar_dispositivo(novo_id)
                except Exception as e:
                    print(f'[ACERTE A NOTA] Nao foi possivel trocar a entrada: {e}')
            return True
        return False
