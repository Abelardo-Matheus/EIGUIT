# -*- coding: utf-8 -*-
"""
Jogo de ritmo.

As figuras descem numa pista alinhadas ao pulso escolhido. O acerto e medido
pelo ATAQUE do instrumento (nao pelo sustain), o que torna a leitura honesta:
segurar uma nota nao acumula pontos. Cada acerto recebe uma nota de precisao
conforme a distancia em milissegundos ate o tempo exato.
"""
import time

import pygame

from config.design_system import TEMA, ds
from core.i18n import _t
from core.modulos.detector_palhetadas import DetectorPalhetadas

SUBDIVISOES = {
    1: ('Seminima', 1),
    2: ('Colcheia', 2),
    3: ('Tercina', 3),
    4: ('Semicolcheia', 4),
}

# (rotulo, tolerancia em segundos, pontos, cor)
GRAUS_ACERTO = [
    ('Perfeito', 0.045, 20),
    ('Bom', 0.090, 12),
    ('Ok', 0.150, 6),
]
TOLERANCIA_MAXIMA = GRAUS_ACERTO[-1][1]


class RhythmHero:
    """
        Como funciona: Agenda batidas a partir do relogio, desenha a pista e
        compara cada ataque detectado com o tempo exato da figura mais proxima.
        Para que serve: Treinar precisao ritmica com o proprio instrumento.
        Onde e usada: Instanciada pelo gerenciador de jogos.
    """

    VELOCIDADE_BASE = 420.0     # pixels por segundo de queda
    CONTAGEM_INICIAL = 4        # batidas de preparacao antes de valer ponto

    def __init__(self):
        self.inicializado = False
        self.jogo_iniciado = False

        self.bpm = 80
        self.subdivisao = 1
        self.compasso = 4
        self.metronomo_on = True

        self.pontuacao = 0
        self.sequencia = 0
        self.melhor_sequencia = 0
        self.contagem_graus = {rotulo: 0 for rotulo, _, _ in GRAUS_ACERTO}
        self.perdidas = 0
        self.desvios_ms = []

        self.notas = []
        self.indice_batida = 0
        self.tempo_inicio = 0.0
        self.proxima_batida = 0.0
        self.batida_metronomo = 0

        self.detector = DetectorPalhetadas()
        self.som_tick = None
        self.som_acento = None

        self.mensagem = ''
        self.cor_mensagem = None
        self.mensagem_ate = 0.0
        self.brilho_linha = 0.0

        self.largura_pista = 280
        self.y_linha = 0

        self.btn_start = pygame.Rect(0, 0, 300, 50)
        self.btn_menos_bpm = pygame.Rect(0, 0, 32, 32)
        self.btn_mais_bpm = pygame.Rect(0, 0, 32, 32)
        self.btn_menos_ritmo = pygame.Rect(0, 0, 32, 32)
        self.btn_mais_ritmo = pygame.Rect(0, 0, 32, 32)
        self.btn_menos_compasso = pygame.Rect(0, 0, 32, 32)
        self.btn_mais_compasso = pygame.Rect(0, 0, 32, 32)
        self.btn_metronomo = pygame.Rect(0, 0, 26, 26)
        self.btn_parar = pygame.Rect(0, 0, 120, 34)

        self._fontes = {}
        self._carregar_sons()

    # ----------------------------------------------------------- recursos --
    def _fonte(self, tamanho, negrito=True):
        chave = (tamanho, negrito)
        if chave not in self._fontes:
            self._fontes[chave] = pygame.font.SysFont('Arial', tamanho, bold=negrito)
        return self._fontes[chave]

    def _carregar_sons(self):
        import os, sys
        try:
            if getattr(sys, 'frozen', False):
                raiz = os.path.dirname(sys.executable)
            else:
                raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            pasta = os.path.join(raiz, 'assets', 'audio')
            for atributo, arquivo in (('som_tick', 'tick.wav'), ('som_acento', 'tick_high.wav')):
                caminho = os.path.join(pasta, arquivo)
                if os.path.exists(caminho):
                    setattr(self, atributo, pygame.mixer.Sound(caminho))
        except Exception:
            pass

    # ------------------------------------------------------------ ajustes --
    @property
    def intervalo_batida(self):
        """Segundos entre duas figuras, ja considerando a subdivisao."""
        return 60.0 / max(1, self.bpm) / SUBDIVISOES[self.subdivisao][1]

    def inicializar(self, largura, altura):
        """Posiciona a linha de acerto e marca o layout como pronto."""
        self.y_linha = int(altura * 0.72)
        self.inicializado = True

    def iniciar_jogo(self):
        """Comeca a partida com uma contagem de preparacao."""
        self.jogo_iniciado = True
        self.pontuacao = 0
        self.sequencia = 0
        self.perdidas = 0
        self.desvios_ms.clear()
        self.contagem_graus = {rotulo: 0 for rotulo, _, _ in GRAUS_ACERTO}
        self.notas.clear()
        self.detector.reiniciar()

        agora = time.time()
        self.tempo_inicio = agora
        # A primeira figura valida so chega apos a contagem de preparacao
        self.proxima_batida = agora + self.intervalo_batida * self.CONTAGEM_INICIAL
        self.indice_batida = 0
        self.batida_metronomo = 0

    def parar_jogo(self):
        self.jogo_iniciado = False
        self.notas.clear()

    # ------------------------------------------------------------- logica --
    def _avisar(self, texto, cor):
        self.mensagem = texto
        self.cor_mensagem = cor
        self.mensagem_ate = time.time() + 0.5

    def _agendar(self, agora, mult_vel):
        """Cria as figuras com antecedencia suficiente para caberem na tela."""
        velocidade = self.VELOCIDADE_BASE * mult_vel
        tempo_queda = (self.y_linha + 60) / velocidade
        while self.proxima_batida - agora <= tempo_queda:
            self.notas.append({
                'alvo': self.proxima_batida,
                'indice': self.indice_batida,
                'resolvida': False,
                'brilho': 0.0,
            })
            self.proxima_batida += self.intervalo_batida
            self.indice_batida += 1

    def _tocar_metronomo(self, agora):
        """Clique no pulso, com acento no primeiro tempo do compasso."""
        if not self.metronomo_on:
            return
        pulso = 60.0 / max(1, self.bpm)
        decorrido = agora - self.tempo_inicio
        batida = int(decorrido / pulso)
        if batida > self.batida_metronomo:
            self.batida_metronomo = batida
            acento = (batida % max(1, self.compasso)) == 0
            som = self.som_acento if (acento and self.som_acento) else self.som_tick
            if som:
                som.play()

    def _registrar_ataque(self, agora):
        """Casa o ataque com a figura mais proxima e pontua pela precisao."""
        candidatas = [n for n in self.notas if not n['resolvida']]
        if not candidatas:
            return
        nota = min(candidatas, key=lambda n: abs(n['alvo'] - agora))
        desvio = abs(nota['alvo'] - agora)
        if desvio > TOLERANCIA_MAXIMA:
            return

        for rotulo, tolerancia, pontos in GRAUS_ACERTO:
            if desvio <= tolerancia:
                nota['resolvida'] = True
                nota['brilho'] = 1.0
                self.sequencia += 1
                self.melhor_sequencia = max(self.melhor_sequencia, self.sequencia)
                self.contagem_graus[rotulo] += 1
                self.desvios_ms.append((nota['alvo'] - agora) * 1000.0)
                self.pontuacao += pontos + self.sequencia // 5
                self.brilho_linha = 1.0
                cor = (TEMA.verde if rotulo == 'Perfeito'
                       else TEMA.ciano if rotulo == 'Bom' else TEMA.aviso)
                self._avisar(_t(rotulo), cor)
                return

    def atualizar(self, estado, meu_gravador, configs=None):
        """
            Como funciona: Agenda figuras, toca o metronomo, escuta ataques e
            descarta as figuras que passaram da tolerancia.
            Para que serve: Nucleo do jogo, independente do desenho.
            Onde e usada: Chamada por desenhar a cada quadro.
        """
        if not self.jogo_iniciado:
            return
        agora = time.time()
        mult_vel = configs.get_vel_jogo() if configs else 1.0

        self._agendar(agora, mult_vel)
        self._tocar_metronomo(agora)

        if meu_gravador is not None and hasattr(meu_gravador, 'buffer'):
            try:
                if self.detector.processar_buffer(meu_gravador.buffer, agora):
                    self._registrar_ataque(agora)
            except Exception:
                pass

        for nota in self.notas[:]:
            nota['brilho'] = max(0.0, nota['brilho'] - 0.07)
            if not nota['resolvida'] and agora - nota['alvo'] > TOLERANCIA_MAXIMA:
                nota['resolvida'] = True
                nota['perdida'] = True
                self.perdidas += 1
                self.sequencia = 0
                self._avisar(_t('Passou'), TEMA.alerta)
            if agora - nota['alvo'] > 1.0:
                self.notas.remove(nota)

    # ------------------------------------------------------------ desenho --
    def _desenhar_pista(self, tela, largura, altura, mult_vel):
        """Pista, marcas de pulso e linha de acerto."""
        x_pista = largura // 2 - self.largura_pista // 2
        pista = pygame.Rect(x_pista, 0, self.largura_pista, altura)
        ds.superficie_translucida(tela, pista, TEMA.superficie, 150, 0, None, 0)
        for x in (x_pista, x_pista + self.largura_pista):
            pygame.draw.line(tela, ds.rgb(ds.misturar(TEMA.borda, TEMA.acento, 0.4)),
                             (x, 0), (x, altura), 2)

        # Marcas de pulso: ajudam a ler o andamento mesmo sem figura na tela
        velocidade = self.VELOCIDADE_BASE * mult_vel
        if self.jogo_iniciado:
            pulso = 60.0 / max(1, self.bpm)
            agora = time.time()
            proximo = self.tempo_inicio + (int((agora - self.tempo_inicio) / pulso) + 1) * pulso
            for i in range(6):
                t = proximo + i * pulso
                y = self.y_linha - (t - agora) * velocidade
                if 0 < y < self.y_linha:
                    pygame.draw.line(tela, ds.rgb(ds.misturar(TEMA.borda, TEMA.fundo, 0.4)),
                                     (x_pista + 12, y), (x_pista + self.largura_pista - 12, y), 1)

        # Linha de acerto
        brilho = int(30 + self.brilho_linha * 110)
        faixa = pygame.Surface((self.largura_pista, 46), pygame.SRCALPHA)
        faixa.fill(ds.com_alpha(TEMA.acento, brilho))
        tela.blit(faixa, (x_pista, self.y_linha - 23))
        pygame.draw.line(tela, ds.rgb(TEMA.acento),
                         (x_pista, self.y_linha), (x_pista + self.largura_pista, self.y_linha), 4)
        self.brilho_linha = max(0.0, self.brilho_linha - 0.06)
        return x_pista

    def _desenhar_figuras(self, tela, largura, mult_vel):
        """Cada figura como cabeca de nota, com acento no primeiro tempo."""
        agora = time.time()
        velocidade = self.VELOCIDADE_BASE * mult_vel
        divisoes = SUBDIVISOES[self.subdivisao][1]
        cx = largura // 2

        for nota in self.notas:
            y = self.y_linha - (nota['alvo'] - agora) * velocidade
            if y < -60:
                continue
            no_tempo_forte = (nota['indice'] % (divisoes * max(1, self.compasso))) == 0
            raio = 22 if no_tempo_forte else 16

            if nota.get('perdida'):
                cor, borda = TEMA.trilho, TEMA.alerta
            elif nota['resolvida']:
                cor, borda = TEMA.verde, TEMA.verde
            else:
                cor, borda = (TEMA.acento if no_tempo_forte else TEMA.ciano), TEMA.texto

            if nota['brilho'] > 0:
                halo = pygame.Surface((raio * 6, raio * 6), pygame.SRCALPHA)
                pygame.draw.circle(halo, ds.com_alpha(cor, int(130 * nota['brilho'])),
                                   (raio * 3, raio * 3), int(raio * 2.1))
                tela.blit(halo, (cx - raio * 3, int(y) - raio * 3))

            pygame.draw.circle(tela, ds.rgb(cor), (cx, int(y)), raio)
            pygame.draw.circle(tela, ds.rgb(borda), (cx, int(y)), raio, 2)
            if no_tempo_forte and not nota['resolvida']:
                ds.texto_em(tela, '1', self._fonte(15), (cx, int(y)),
                            ds.contraste_texto(cor), ancora='center')

    def _desenhar_hud(self, tela, largura, altura):
        """Placar, precisao media e distribuicao dos acertos."""
        painel = pygame.Rect(24, 24, 250, 150)
        ds.painel(tela, painel, None, None, acento=TEMA.acento, alpha=228)
        ds.texto_em(tela, str(self.pontuacao), self._fonte(30),
                    (painel.centerx, painel.y + 10), TEMA.aviso, ancora='midtop')
        ds.texto_em(tela, _t('pontos'), self._fonte(12),
                    (painel.centerx, painel.y + 44), TEMA.texto_apagado, ancora='midtop')

        y = painel.y + 68
        linhas = [(f"{_t('Sequencia')}", str(self.sequencia), TEMA.verde)]
        if self.desvios_ms:
            medio = sum(self.desvios_ms) / len(self.desvios_ms)
            sinal = '+' if medio > 0 else ''
            adianto = _t('adiantado') if medio > 0 else _t('atrasado')
            linhas.append((_t('Desvio medio'), f'{sinal}{medio:.0f} ms', TEMA.ciano))
            linhas.append(('', adianto, TEMA.texto_apagado))
        for rotulo, valor, cor in linhas:
            if rotulo:
                ds.texto_em(tela, rotulo, self._fonte(12), (painel.x + ds.ESPACO_MD, y),
                            TEMA.texto_apagado)
            ds.texto_em(tela, valor, self._fonte(13),
                        (painel.right - ds.ESPACO_MD, y), cor, ancora='topright')
            y += 20

        # Distribuicao dos acertos
        resumo = pygame.Rect(24, painel.bottom + 12, 250, 96)
        ds.painel(tela, resumo, None, None, acento=TEMA.borda, alpha=210)
        y = resumo.y + ds.ESPACO_MD
        cores = {'Perfeito': TEMA.verde, 'Bom': TEMA.ciano, 'Ok': TEMA.aviso}
        for rotulo, _tol, _pt in GRAUS_ACERTO:
            ds.texto_em(tela, _t(rotulo), self._fonte(12),
                        (resumo.x + ds.ESPACO_MD, y), cores[rotulo])
            ds.texto_em(tela, str(self.contagem_graus[rotulo]), self._fonte(12),
                        (resumo.right - ds.ESPACO_MD, y), TEMA.texto, ancora='topright')
            y += 19
        ds.texto_em(tela, _t('Passou'), self._fonte(12),
                    (resumo.x + ds.ESPACO_MD, y), TEMA.alerta)
        ds.texto_em(tela, str(self.perdidas), self._fonte(12),
                    (resumo.right - ds.ESPACO_MD, y), TEMA.texto, ancora='topright')

        # Andamento em uso
        ds.texto_em(tela, f'{self.bpm} BPM  ·  {_t(SUBDIVISOES[self.subdivisao][0])}'
                          f'  ·  {self.compasso}/4',
                    self._fonte(14), (largura // 2, 24), TEMA.texto_suave, ancora='midtop')

        self.btn_parar.topleft = (largura - 144, 24)
        ds.botao(tela, self.btn_parar, _t('Encerrar'), self._fonte(13),
                 variante='secundario',
                 hover=self.btn_parar.collidepoint(pygame.mouse.get_pos()))

        if self.mensagem and time.time() < self.mensagem_ate:
            ds.texto_em(tela, self.mensagem, self._fonte(30),
                        (largura // 2, self.y_linha - 90),
                        self.cor_mensagem or TEMA.texto, ancora='center')

        # Contagem de preparacao
        restante = self.proxima_batida - time.time()
        if restante > 0 and not any(n['resolvida'] for n in self.notas) and self.pontuacao == 0:
            faltam = int(restante / max(1e-3, self.intervalo_batida)) + 1
            if faltam <= self.CONTAGEM_INICIAL:
                ds.texto_em(tela, str(faltam), self._fonte(64),
                            (largura // 2, altura // 2), TEMA.acento, ancora='center')

    def _desenhar_ajustes(self, tela, largura, altura):
        """Tela inicial com andamento, subdivisao e compasso."""
        painel = pygame.Rect(0, 0, min(520, largura - 80), 350)
        painel.center = (largura // 2, altura // 2)
        ds.painel(tela, painel, None, None, acento=TEMA.acento)
        pos_mouse = pygame.mouse.get_pos()

        ds.texto_em(tela, _t('Jogo de Ritmo'), self._fonte(30),
                    (painel.centerx, painel.y + 22), TEMA.texto, ancora='midtop')
        ds.texto_em(tela, _t('Toque no tempo exato de cada figura'), self._fonte(14),
                    (painel.centerx, painel.y + 60), TEMA.texto_apagado, ancora='midtop')

        x = painel.x + ds.ESPACO_XL
        largura_linha = painel.width - ds.ESPACO_XL * 2
        y = painel.y + 100

        def linha(rotulo, valor, esq, dir_, y_atual):
            ds.texto_em(tela, rotulo, self._fonte(14), (x, y_atual + 8),
                        TEMA.texto_suave, largura_max=largura_linha // 3)
            esq.topleft = (x + largura_linha - 210, y_atual); esq.size = (32, 32)
            dir_.topleft = (x + largura_linha - 32, y_atual); dir_.size = (32, 32)
            ds.botao(tela, esq, '<', self._fonte(14), variante='secundario',
                     hover=esq.collidepoint(pos_mouse))
            ds.botao(tela, dir_, '>', self._fonte(14), variante='secundario',
                     hover=dir_.collidepoint(pos_mouse))
            ds.texto_centralizado(
                tela, valor, self._fonte(14),
                pygame.Rect(esq.right, y_atual, dir_.left - esq.right, 32), TEMA.texto)
            return y_atual + 46

        y = linha(_t('Andamento'), f'{self.bpm} BPM',
                  self.btn_menos_bpm, self.btn_mais_bpm, y)
        y = linha(_t('Subdivisao'), _t(SUBDIVISOES[self.subdivisao][0]),
                  self.btn_menos_ritmo, self.btn_mais_ritmo, y)
        y = linha(_t('Compasso'), f'{self.compasso}/4',
                  self.btn_menos_compasso, self.btn_mais_compasso, y)

        self.btn_metronomo.topleft = (x, y + 2)
        ds.caixa_selecao(tela, self.btn_metronomo, self.metronomo_on)
        ds.texto_em(tela, _t('Clique do metronomo'), self._fonte(14),
                    (self.btn_metronomo.right + ds.ESPACO_MD, self.btn_metronomo.centery),
                    TEMA.texto_suave, ancora='midleft')

        self.btn_start.size = (largura_linha, 48)
        self.btn_start.topleft = (x, painel.bottom - 66)
        ds.botao(tela, self.btn_start, _t('Comecar'), self._fonte(20),
                 variante='primario', hover=self.btn_start.collidepoint(pos_mouse))

    def desenhar(self, tela, largura, altura, estado, meu_gravador=None, configs=None):
        """
            Como funciona: Atualiza a logica e desenha pista, figuras e placar.
            Para que serve: Loop visual do jogo de ritmo.
            Onde e usada: Chamada pelo gerenciador de jogos.
        """
        if not self.inicializado or self.y_linha == 0:
            self.inicializar(largura, altura)
        if configs is not None:
            TEMA.definir_acento(configs.get_cor_tema())

        self.atualizar(estado, meu_gravador, configs)
        ds.fundo_app(tela, pygame.Rect(0, 0, largura, altura))

        if not self.jogo_iniciado:
            self._desenhar_ajustes(tela, largura, altura)
            return

        mult_vel = configs.get_vel_jogo() if configs else 1.0
        self._desenhar_pista(tela, largura, altura, mult_vel)
        self._desenhar_figuras(tela, largura, mult_vel)
        self._desenhar_hud(tela, largura, altura)

    # ------------------------------------------------------------- clique --
    def tratar_clique(self, pos, meu_gravador=None):
        """
            Como funciona: Trata os controles da tela inicial e o encerrar.
            Para que serve: Ajustar o exercicio e comecar ou parar a partida.
            Onde e usada: Chamada pelo gerenciador de jogos.
        """
        if self.jogo_iniciado:
            if self.btn_parar.collidepoint(pos):
                self.parar_jogo()
                return True
            return False

        if self.btn_menos_bpm.collidepoint(pos):
            self.bpm = max(40, self.bpm - 5); return True
        if self.btn_mais_bpm.collidepoint(pos):
            self.bpm = min(240, self.bpm + 5); return True
        if self.btn_menos_ritmo.collidepoint(pos):
            self.subdivisao = max(1, self.subdivisao - 1); return True
        if self.btn_mais_ritmo.collidepoint(pos):
            self.subdivisao = min(4, self.subdivisao + 1); return True
        if self.btn_menos_compasso.collidepoint(pos):
            self.compasso = max(2, self.compasso - 1); return True
        if self.btn_mais_compasso.collidepoint(pos):
            self.compasso = min(8, self.compasso + 1); return True
        if self.btn_metronomo.collidepoint(pos):
            self.metronomo_on = not self.metronomo_on; return True
        if self.btn_start.collidepoint(pos):
            self.iniciar_jogo(); return True
        return False
