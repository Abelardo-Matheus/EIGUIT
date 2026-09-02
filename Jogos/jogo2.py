# -*- coding: utf-8 -*-
"""
Jogo de ritmo.

As figuras descem numa pista alinhada ao pulso escolhido. O acerto e medido
pelo ATAQUE do instrumento (nao pelo sustain), o que torna a leitura honesta:
segurar uma nota nao acumula pontos.

O que o jogo devolve nao e so um placar. Cada acerto guarda a distancia em
milissegundos ate o tempo exato, e o medidor da direita mostra essa nuvem de
desvios: e ali que se ve se voce adianta ou atrasa, que e a informacao que
faz alguem melhorar de verdade.
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

# (rotulo, tolerancia em segundos, pontos)
GRAUS_ACERTO = [
    ('Perfeito', 0.045, 20),
    ('Bom', 0.090, 12),
    ('Ok', 0.150, 6),
]
TOLERANCIA_MAXIMA = GRAUS_ACERTO[-1][1]

# Atalhos de configuracao: (rotulo, bpm, subdivisao, compasso)
PRESETS = [
    ('Iniciante', 60, 1, 4),
    ('Pratica', 90, 2, 4),
    ('Desafio', 120, 4, 4),
]

JANELA_MEDIDOR_MS = 150.0      # escala do medidor de precisao
MAX_MARCAS_MEDIDOR = 28        # quantos desvios recentes aparecem no medidor


def cor_do_grau(rotulo):
    """Verde, ciano e amarelo para Perfeito, Bom e Ok."""
    return {'Perfeito': TEMA.verde, 'Bom': TEMA.ciano}.get(rotulo, TEMA.aviso)


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
        self.mostrar_resultado = False
        self.resultado = None

        self.bpm = 80
        self.subdivisao = 1
        self.compasso = 4
        self.metronomo_on = True

        self.pontuacao = 0
        self.sequencia = 0
        self.melhor_sequencia = 0
        self.contagem_graus = {rotulo: 0 for rotulo, _, _ in GRAUS_ACERTO}
        self.perdidas = 0
        self.desvios_ms = []        # positivo = atrasado, negativo = adiantado

        self.notas = []
        self.indice_batida = 0
        self.tempo_inicio = 0.0
        self.primeira_valida = 0.0
        self.proxima_batida = 0.0
        self.batida_metronomo = 0

        self.detector = DetectorPalhetadas()
        self.som_tick = None
        self.som_acento = None

        self.mensagem = ''
        self.cor_mensagem = None
        self.mensagem_ate = 0.0
        self.brilho_linha = 0.0
        self.pulso_visual = 0.0

        # Geometria, recalculada a cada quadro em _layout
        self.largura_pista = 320
        self.y_linha = 0
        self.rect_pista = pygame.Rect(0, 0, 0, 0)
        self.rect_esq = pygame.Rect(0, 0, 0, 0)
        self.rect_dir = pygame.Rect(0, 0, 0, 0)

        self.btn_start = pygame.Rect(0, 0, 300, 50)
        self.btn_menos_bpm = pygame.Rect(0, 0, 32, 32)
        self.btn_mais_bpm = pygame.Rect(0, 0, 32, 32)
        self.btn_menos_ritmo = pygame.Rect(0, 0, 32, 32)
        self.btn_mais_ritmo = pygame.Rect(0, 0, 32, 32)
        self.btn_menos_compasso = pygame.Rect(0, 0, 32, 32)
        self.btn_mais_compasso = pygame.Rect(0, 0, 32, 32)
        self.btn_metronomo = pygame.Rect(0, 0, 26, 26)
        self.btn_parar = pygame.Rect(0, 0, 120, 34)
        self.btn_metronomo_jogo = pygame.Rect(0, 0, 0, 0)
        self.btn_de_novo = pygame.Rect(0, 0, 0, 0)
        self.btn_ajustes = pygame.Rect(0, 0, 0, 0)
        self.rects_preset = []

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
            for atributo, arquivo in (('som_tick', 'tick.wav'),
                                      ('som_acento', 'tick_high.wav')):
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

    @property
    def figuras_por_compasso(self):
        return SUBDIVISOES[self.subdivisao][1] * max(1, self.compasso)

    def inicializar(self, largura, altura):
        """Calcula a geometria e marca o layout como pronto."""
        self._layout(largura, altura)
        self.inicializado = True

    def _layout(self, largura, altura):
        """Tres colunas: placar, pista e medidor de precisao."""
        margem = 24
        col_esq = 250 if largura >= 1100 else 0
        col_dir = 300 if largura >= 1280 else 0
        topo = margem
        alt = max(120, altura - margem * 2)

        self.rect_esq = pygame.Rect(margem, topo, col_esq, alt)
        self.rect_dir = pygame.Rect(largura - margem - col_dir, topo, col_dir, alt)

        limite_esq = self.rect_esq.right + 32 if col_esq else margem
        limite_dir = self.rect_dir.left - 32 if col_dir else largura - margem
        disponivel = max(180, limite_dir - limite_esq)
        self.largura_pista = int(min(420, disponivel))
        centro = (limite_esq + limite_dir) // 2
        self.rect_pista = pygame.Rect(centro - self.largura_pista // 2, topo,
                                      self.largura_pista, alt)
        self.y_linha = self.rect_pista.bottom - int(alt * 0.18)

    def aplicar_preset(self, indice):
        """Carrega um dos atalhos de configuracao."""
        if 0 <= indice < len(PRESETS):
            _rot, bpm, sub, comp = PRESETS[indice]
            self.bpm, self.subdivisao, self.compasso = bpm, sub, comp

    def preset_ativo(self):
        for i, (_r, bpm, sub, comp) in enumerate(PRESETS):
            if (bpm, sub, comp) == (self.bpm, self.subdivisao, self.compasso):
                return i
        return -1

    # ------------------------------------------------------------- partida --
    def iniciar_jogo(self):
        """Comeca a partida com uma contagem de preparacao."""
        self.jogo_iniciado = True
        self.mostrar_resultado = False
        self.resultado = None
        self.pontuacao = 0
        self.sequencia = 0
        self.melhor_sequencia = 0
        self.perdidas = 0
        self.desvios_ms.clear()
        self.contagem_graus = {rotulo: 0 for rotulo, _, _ in GRAUS_ACERTO}
        self.notas.clear()
        self.detector.reiniciar()

        agora = time.time()
        self.tempo_inicio = agora
        # A primeira figura valida so chega apos a contagem de preparacao
        self.primeira_valida = agora + self.intervalo_batida * self.CONTAGEM_INICIAL
        self.proxima_batida = self.primeira_valida
        self.indice_batida = 0
        self.batida_metronomo = 0
        self.mensagem = ''

    def parar_jogo(self):
        """Encerra a partida e guarda o resumo para a tela de resultado."""
        if self.jogo_iniciado:
            self.resultado = self.resumo()
            self.mostrar_resultado = self.resultado['tentativas'] > 0
        self.jogo_iniciado = False
        self.notas.clear()

    def resumo(self):
        """Numeros da partida, usados na tela de resultado."""
        acertos = sum(self.contagem_graus.values())
        tentativas = acertos + self.perdidas
        medio = (sum(self.desvios_ms) / len(self.desvios_ms)) if self.desvios_ms else 0.0
        espalhamento = 0.0
        if len(self.desvios_ms) > 1:
            espalhamento = (sum((d - medio) ** 2 for d in self.desvios_ms)
                            / (len(self.desvios_ms) - 1)) ** 0.5
        return {
            'pontuacao': self.pontuacao,
            'acertos': acertos,
            'tentativas': tentativas,
            'precisao': (acertos / tentativas * 100.0) if tentativas else 0.0,
            'desvio_medio': medio,
            'espalhamento': espalhamento,
            'melhor_sequencia': self.melhor_sequencia,
            'graus': dict(self.contagem_graus),
            'perdidas': self.perdidas,
            'bpm': self.bpm,
            'subdivisao': SUBDIVISOES[self.subdivisao][0],
            'compasso': self.compasso,
        }

    def tendencia(self, medio=None):
        """Texto curto dizendo se o aluno adianta ou atrasa."""
        if medio is None:
            if not self.desvios_ms:
                return '', TEMA.texto_apagado
            medio = sum(self.desvios_ms) / len(self.desvios_ms)
        if abs(medio) <= 12:
            return _t('no tempo'), TEMA.verde
        if medio > 0:
            return _t('atrasando'), TEMA.aviso
        return _t('adiantando'), TEMA.ciano

    # ------------------------------------------------------------- logica --
    def _avisar(self, texto, cor):
        self.mensagem = texto
        self.cor_mensagem = cor
        self.mensagem_ate = time.time() + 0.55

    def _agendar(self, agora, mult_vel):
        """Cria as figuras com antecedencia suficiente para caberem na tela."""
        velocidade = self.VELOCIDADE_BASE * mult_vel
        altura_visivel = max(120, self.y_linha - self.rect_pista.y) + 80
        tempo_queda = altura_visivel / velocidade
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
        pulso = 60.0 / max(1, self.bpm)
        decorrido = agora - self.tempo_inicio
        batida = int(decorrido / pulso)
        if batida > self.batida_metronomo:
            self.batida_metronomo = batida
            self.pulso_visual = 1.0
            if not self.metronomo_on:
                return
            acento = (batida % max(1, self.compasso)) == 0
            som = self.som_acento if (acento and self.som_acento) else self.som_tick
            if som:
                try:
                    som.play()
                except Exception:
                    pass

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
                nota['grau'] = rotulo
                nota['brilho'] = 1.0
                self.sequencia += 1
                self.melhor_sequencia = max(self.melhor_sequencia, self.sequencia)
                self.contagem_graus[rotulo] += 1
                # positivo = atrasado (tocou depois do tempo)
                self.desvios_ms.append((agora - nota['alvo']) * 1000.0)
                self.pontuacao += pontos + self.sequencia // 5
                self.brilho_linha = 1.0
                self._avisar(_t(rotulo), cor_do_grau(rotulo))
                return

    def registrar_ataque_manual(self):
        """Ataque vindo do teclado, para quem esta sem instrumento ligado."""
        if self.jogo_iniciado:
            self._registrar_ataque(time.time())

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
        self.pulso_visual = max(0.0, self.pulso_visual - 0.08)

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
    def _figura(self, tela, cx, cy, escala, cor, cor_borda, bandeirolas=0,
                preenchida=True):
        """Cabeca de nota inclinada com haste e bandeirolas, como na pauta."""
        largura = int(28 * escala)
        altura = int(20 * escala)
        cabeca = pygame.Surface((largura + 6, altura + 6), pygame.SRCALPHA)
        if preenchida:
            pygame.draw.ellipse(cabeca, ds.rgb(cor), (3, 3, largura, altura))
        else:
            pygame.draw.ellipse(cabeca, ds.rgb(cor), (3, 3, largura, altura), 3)
        pygame.draw.ellipse(cabeca, ds.rgb(cor_borda), (3, 3, largura, altura), 2)
        cabeca = pygame.transform.rotate(cabeca, 20)
        tela.blit(cabeca, (int(cx - cabeca.get_width() / 2),
                           int(cy - cabeca.get_height() / 2)))

        haste_x = int(cx + largura * 0.45)
        topo = int(cy - 42 * escala)
        pygame.draw.line(tela, ds.rgb(cor_borda), (haste_x, int(cy)),
                         (haste_x, topo), max(2, int(2 * escala)))
        for i in range(bandeirolas):
            y = topo + i * int(9 * escala)
            pygame.draw.line(tela, ds.rgb(cor_borda), (haste_x, y),
                             (haste_x + int(13 * escala), y + int(12 * escala)),
                             max(2, int(2 * escala)))

    def _desenhar_pista(self, tela, mult_vel):
        """Pista, janelas de tolerancia, compassos e linha de acerto."""
        pista = self.rect_pista
        ds.painel(tela, pista, None, None, acento=TEMA.acento, alpha=210)
        velocidade = self.VELOCIDADE_BASE * mult_vel
        agora = time.time()

        tela.set_clip(pista.inflate(-4, -4))

        # Janelas de tolerancia: marcadas nas bordas, para o centro ficar limpo
        for rotulo, tolerancia, _pt in GRAUS_ACERTO:
            meia = max(2, int(tolerancia * velocidade))
            cor = cor_do_grau(rotulo)
            for y in (self.y_linha - meia, self.y_linha + meia):
                for x in (pista.x + 6, pista.right - 20):
                    pygame.draw.rect(tela, ds.rgb(cor), (x, int(y) - 1, 14, 3),
                                     border_radius=2)
        # Brilho suave so na janela do Perfeito
        meia = max(2, int(GRAUS_ACERTO[0][1] * velocidade))
        ds.superficie_translucida(tela, pygame.Rect(pista.x + 6, self.y_linha - meia,
                                                    pista.width - 12, meia * 2),
                                  TEMA.verde, 34, ds.RAIO_SM, None, 0)

        # Grade do compasso: uma linha por pulso, mais forte no tempo 1
        if self.jogo_iniciado:
            pulso = 60.0 / max(1, self.bpm)
            base = self.tempo_inicio + int((agora - self.tempo_inicio) / pulso) * pulso
            for i in range(-1, 14):
                t = base + i * pulso
                y = self.y_linha - (t - agora) * velocidade
                if not (pista.y - 20 < y < pista.bottom):
                    continue
                batida = int(round((t - self.tempo_inicio) / pulso))
                forte = (batida % max(1, self.compasso)) == 0
                cor = TEMA.borda if forte else ds.misturar(TEMA.borda, TEMA.fundo, 0.55)
                pygame.draw.line(tela, ds.rgb(cor), (pista.x + 8, y),
                                 (pista.right - 8, y), 2 if forte else 1)
                if forte and y < self.y_linha - 10:
                    numero = batida // max(1, self.compasso) + 1
                    ds.texto_em(tela, str(numero), self._fonte(11),
                                (pista.x + 12, y - 14), TEMA.texto_apagado)

        # Linha de acerto
        brilho = int(40 + self.brilho_linha * 120)
        faixa = pygame.Surface((pista.width - 12, 8), pygame.SRCALPHA)
        faixa.fill(ds.com_alpha(TEMA.acento, brilho))
        tela.blit(faixa, (pista.x + 6, self.y_linha - 4))
        pygame.draw.line(tela, ds.rgb(TEMA.acento), (pista.x + 6, self.y_linha),
                         (pista.right - 6, self.y_linha), 3)
        self.brilho_linha = max(0.0, self.brilho_linha - 0.06)
        tela.set_clip(None)

    def _desenhar_figuras(self, tela, mult_vel):
        """Cada figura como nota escrita, maior no tempo forte do compasso."""
        agora = time.time()
        velocidade = self.VELOCIDADE_BASE * mult_vel
        divisoes = SUBDIVISOES[self.subdivisao][1]
        bandeirolas = {1: 0, 2: 1, 3: 1, 4: 2}[self.subdivisao]
        cx = self.rect_pista.centerx
        pista = self.rect_pista

        tela.set_clip(pista.inflate(-4, -4))
        for nota in self.notas:
            y = self.y_linha - (nota['alvo'] - agora) * velocidade
            if y < pista.y - 40 or y > pista.bottom + 40:
                continue
            no_compasso = (nota['indice'] % self.figuras_por_compasso) == 0
            no_pulso = (nota['indice'] % divisoes) == 0
            escala = 1.25 if no_compasso else (1.0 if no_pulso else 0.78)

            if nota.get('perdida'):
                cor, borda = TEMA.trilho, TEMA.alerta
            elif nota['resolvida']:
                cor = borda = cor_do_grau(nota.get('grau', 'Ok'))
            elif no_compasso:
                cor, borda = TEMA.acento, TEMA.texto
            elif no_pulso:
                cor, borda = TEMA.ciano, TEMA.texto_suave
            else:
                cor, borda = TEMA.superficie_alt, TEMA.ciano

            if nota['brilho'] > 0:
                raio = int(30 * escala)
                halo = pygame.Surface((raio * 4, raio * 4), pygame.SRCALPHA)
                pygame.draw.circle(halo, ds.com_alpha(cor, int(120 * nota['brilho'])),
                                   (raio * 2, raio * 2), int(raio * 1.6))
                tela.blit(halo, (cx - raio * 2, int(y) - raio * 2))

            self._figura(tela, cx, y, escala, cor, borda,
                         bandeirolas=0 if no_pulso else bandeirolas,
                         preenchida=not nota.get('perdida'))
            if no_compasso and not nota['resolvida']:
                ds.texto_em(tela, '1', self._fonte(13), (cx - 22 * escala, y),
                            TEMA.acento, ancora='center')
        tela.set_clip(None)

        # Aviso do ultimo acerto, ao lado da linha e nunca por cima dela
        if self.mensagem and time.time() < self.mensagem_ate:
            ds.texto_em(tela, self.mensagem, self._fonte(26),
                        (self.rect_pista.centerx, self.rect_pista.bottom - 22),
                        self.cor_mensagem or TEMA.texto, ancora='center')

    def _contagem_regressiva(self, tela):
        """Numero grande enquanto a contagem de preparacao nao termina."""
        restante = self.primeira_valida - time.time()
        if restante <= 0:
            return
        faltam = int(restante / max(1e-3, self.intervalo_batida)) + 1
        centro = (self.rect_pista.centerx, self.rect_pista.y + self.rect_pista.height // 3)
        ds.texto_em(tela, str(min(faltam, self.CONTAGEM_INICIAL)), self._fonte(72),
                    centro, TEMA.acento, ancora='center')
        ds.texto_em(tela, _t('Prepare-se'), self._fonte(15),
                    (centro[0], centro[1] + 52), TEMA.texto_suave, ancora='center')

    def _barra_graus(self, tela, rect):
        """Distribuicao dos acertos como barra empilhada, com legenda."""
        total = sum(self.contagem_graus.values()) + self.perdidas
        barra = pygame.Rect(rect.x, rect.y, rect.width, 10)
        pygame.draw.rect(tela, ds.rgb(TEMA.trilho), barra, border_radius=5)
        if total:
            x = barra.x
            partes = [(cor_do_grau(r), self.contagem_graus[r])
                      for r, _t_, _p in GRAUS_ACERTO]
            partes.append((TEMA.alerta, self.perdidas))
            for cor, quantos in partes:
                largura = int(barra.width * quantos / total)
                if largura > 0:
                    pygame.draw.rect(tela, ds.rgb(cor),
                                     (x, barra.y, largura, barra.height),
                                     border_radius=5)
                    x += largura

        y = barra.bottom + ds.ESPACO_MD
        itens = [(r, self.contagem_graus[r], cor_do_grau(r))
                 for r, _t_, _p in GRAUS_ACERTO]
        itens.append(('Passou', self.perdidas, TEMA.alerta))
        for rotulo, quantos, cor in itens:
            pygame.draw.circle(tela, ds.rgb(cor), (rect.x + 5, y + 7), 4)
            ds.texto_em(tela, _t(rotulo), self._fonte(12), (rect.x + 16, y),
                        TEMA.texto_suave)
            ds.texto_em(tela, str(quantos), self._fonte(12),
                        (rect.right, y), TEMA.texto, ancora='topright')
            y += 19
        return y

    def _desenhar_placar(self, tela):
        """Coluna da esquerda: pontos, sequencia e distribuicao."""
        if self.rect_esq.width <= 0:
            return
        topo = self.rect_esq.y + max(0, (self.rect_esq.height - 452) // 2)
        painel = pygame.Rect(self.rect_esq.x, topo, self.rect_esq.width, 158)
        ds.painel(tela, painel, None, None, acento=TEMA.acento, alpha=230)
        ds.texto_em(tela, str(self.pontuacao), self._fonte(34),
                    (painel.centerx, painel.y + 12), TEMA.aviso, ancora='midtop')
        ds.texto_em(tela, _t('pontos'), self._fonte(11),
                    (painel.centerx, painel.y + 50), TEMA.texto_apagado, ancora='midtop')

        y = painel.y + 78
        for rotulo, valor, cor in (
                (_t('Sequencia'), str(self.sequencia), TEMA.verde),
                (_t('Melhor'), str(self.melhor_sequencia), TEMA.ciano),
                (_t('Acertos'), f'{sum(self.contagem_graus.values())}', TEMA.texto)):
            ds.texto_em(tela, rotulo, self._fonte(12),
                        (painel.x + ds.ESPACO_LG, y), TEMA.texto_apagado)
            ds.texto_em(tela, valor, self._fonte(13),
                        (painel.right - ds.ESPACO_LG, y), cor, ancora='topright')
            y += 21

        resumo = pygame.Rect(self.rect_esq.x, painel.bottom + 14,
                             self.rect_esq.width, 132)
        ds.painel(tela, resumo, _t('Acertos'), self._fonte(12), acento=TEMA.borda,
                  alpha=214)
        self._barra_graus(tela, pygame.Rect(resumo.x + ds.ESPACO_LG, resumo.y + 40,
                                            resumo.width - ds.ESPACO_LG * 2, 80))

        # Legenda das figuras: ajuda a ler a pista de relance
        legenda = pygame.Rect(self.rect_esq.x, resumo.bottom + 14,
                              self.rect_esq.width, 134)
        ds.painel(tela, legenda, _t('Figuras'), self._fonte(12), acento=TEMA.borda,
                  alpha=214)
        bandeirolas = {1: 0, 2: 1, 3: 1, 4: 2}[self.subdivisao]
        itens = [(1.0, TEMA.acento, TEMA.texto, 0, _t('Tempo 1 do compasso')),
                 (0.8, TEMA.ciano, TEMA.texto_suave, 0, _t('Pulso')),
                 (0.62, TEMA.superficie_alt, TEMA.ciano, bandeirolas,
                  _t(SUBDIVISOES[self.subdivisao][0]))]
        y = legenda.y + 58
        for escala, cor, borda, flags, rotulo in itens:
            self._figura(tela, legenda.x + ds.ESPACO_XL + 6, y + 6, escala * 0.55,
                         cor, borda, bandeirolas=flags)
            ds.texto_em(tela, rotulo, self._fonte(12),
                        (legenda.x + ds.ESPACO_XL + 30, y), TEMA.texto_suave,
                        largura_max=legenda.width - 56)
            y += 26

    def _medidor_precisao(self, tela, rect):
        """Nuvem dos ultimos desvios: adiantado a esquerda, atrasado a direita."""
        centro = rect.centerx
        meia = rect.width / 2.0

        for rotulo, tolerancia, _p in reversed(GRAUS_ACERTO):
            largura = min(meia, tolerancia * 1000.0 / JANELA_MEDIDOR_MS * meia)
            faixa = pygame.Rect(int(centro - largura), rect.y,
                                int(largura * 2), rect.height)
            ds.superficie_translucida(tela, faixa, cor_do_grau(rotulo), 40,
                                      ds.RAIO_SM, None, 0)
        pygame.draw.rect(tela, ds.rgb(TEMA.borda), rect, 1, border_radius=ds.RAIO_SM)
        pygame.draw.line(tela, ds.rgb(TEMA.texto), (centro, rect.y - 3),
                         (centro, rect.bottom + 3), 2)

        recentes = self.desvios_ms[-MAX_MARCAS_MEDIDOR:]
        for i, desvio in enumerate(recentes):
            pct = max(-1.0, min(1.0, desvio / JANELA_MEDIDOR_MS))
            x = int(centro + pct * meia)
            alpha = int(70 + 185 * (i + 1) / max(1, len(recentes)))
            marca = pygame.Surface((3, rect.height - 8), pygame.SRCALPHA)
            marca.fill(ds.com_alpha(TEMA.texto, alpha))
            tela.blit(marca, (x - 1, rect.y + 4))

        if self.desvios_ms:
            medio = sum(self.desvios_ms) / len(self.desvios_ms)
            pct = max(-1.0, min(1.0, medio / JANELA_MEDIDOR_MS))
            x = int(centro + pct * meia)
            texto, cor = self.tendencia(medio)
            pygame.draw.polygon(tela, ds.rgb(cor),
                                [(x, rect.bottom + 2), (x - 6, rect.bottom + 12),
                                 (x + 6, rect.bottom + 12)])
            ds.texto_em(tela, f'{medio:+.0f} ms  ·  {texto}', self._fonte(13),
                        (rect.centerx, rect.bottom + 20), cor, ancora='midtop')
        else:
            ds.texto_em(tela, _t('Toque para medir'), self._fonte(12),
                        (rect.centerx, rect.bottom + 20), TEMA.texto_apagado,
                        ancora='midtop')

        ds.texto_em(tela, _t('adiantado'), self._fonte(10), (rect.x, rect.y - 16),
                    TEMA.ciano)
        ds.texto_em(tela, _t('atrasado'), self._fonte(10),
                    (rect.right, rect.y - 16), TEMA.aviso, ancora='topright')

    def _desenhar_lateral(self, tela):
        """Coluna da direita: compasso, precisao e controles da partida."""
        if self.rect_dir.width <= 0:
            self.btn_parar.topleft = (self.rect_pista.right + 12, self.rect_pista.y)
            ds.botao(tela, self.btn_parar, _t('Encerrar'), self._fonte(13),
                     variante='secundario')
            return

        col = self.rect_dir
        topo = col.y + max(0, (col.height - 404) // 2)
        pulso = pygame.Rect(col.x, topo, col.width, 118)
        ds.painel(tela, pulso, _t('Compasso'), self._fonte(12), acento=TEMA.acento,
                  alpha=230)
        batida_atual = self.batida_metronomo % max(1, self.compasso)
        n = max(1, self.compasso)
        raio = min(16, (pulso.width - ds.ESPACO_LG * 2) // (n * 2 + 2))
        passo = (pulso.width - ds.ESPACO_LG * 2 - raio * 2) / max(1, n - 1) if n > 1 else 0
        cy = pulso.y + 74
        for i in range(n):
            cx = int(pulso.x + ds.ESPACO_LG + raio + i * passo)
            ativo = self.jogo_iniciado and i == batida_atual
            cor = TEMA.acento if i == 0 else TEMA.ciano
            if ativo:
                pygame.draw.circle(tela, ds.rgb(cor), (cx, cy),
                                   int(raio * (1 + 0.25 * self.pulso_visual)))
                ds.texto_em(tela, str(i + 1), self._fonte(12), (cx, cy),
                            ds.contraste_texto(cor), ancora='center')
            else:
                pygame.draw.circle(tela, ds.rgb(TEMA.trilho), (cx, cy), raio)
                pygame.draw.circle(tela, ds.rgb(cor), (cx, cy), raio, 2)
                ds.texto_em(tela, str(i + 1), self._fonte(12), (cx, cy),
                            TEMA.texto_suave, ancora='center')
        ds.texto_em(tela, f'{self.bpm} BPM  ·  {_t(SUBDIVISOES[self.subdivisao][0])}',
                    self._fonte(12), (pulso.centerx, pulso.y + 34),
                    TEMA.texto_suave, ancora='midtop')

        medidor = pygame.Rect(col.x, pulso.bottom + 14, col.width, 150)
        ds.painel(tela, medidor, _t('Precisao'), self._fonte(12), acento=TEMA.borda,
                  alpha=220)
        self._medidor_precisao(tela, pygame.Rect(medidor.x + ds.ESPACO_LG,
                                                 medidor.y + 66,
                                                 medidor.width - ds.ESPACO_LG * 2, 40))

        controles = pygame.Rect(col.x, medidor.bottom + 14, col.width, 108)
        ds.painel(tela, controles, None, None, acento=None, alpha=214)
        self.btn_metronomo_jogo = pygame.Rect(controles.x + ds.ESPACO_LG,
                                              controles.y + ds.ESPACO_LG, 26, 26)
        ds.caixa_selecao(tela, self.btn_metronomo_jogo, self.metronomo_on)
        ds.texto_em(tela, _t('Clique do metronomo'), self._fonte(13),
                    (self.btn_metronomo_jogo.right + ds.ESPACO_MD,
                     self.btn_metronomo_jogo.centery), TEMA.texto_suave,
                    ancora='midleft', largura_max=controles.width - 70)
        self.btn_parar = pygame.Rect(controles.x + ds.ESPACO_LG,
                                     controles.bottom - 46,
                                     controles.width - ds.ESPACO_LG * 2, 34)
        ds.botao(tela, self.btn_parar, _t('Encerrar'), self._fonte(14),
                 variante='secundario',
                 hover=self.btn_parar.collidepoint(pygame.mouse.get_pos()))

    def _desenhar_ajustes(self, tela, largura, altura):
        """Tela inicial: atalhos, andamento, subdivisao e compasso."""
        painel = pygame.Rect(0, 0, min(560, largura - 80), min(430, altura - 60))
        painel.center = (largura // 2, altura // 2)
        ds.painel(tela, painel, None, None, acento=TEMA.acento)
        pos_mouse = pygame.mouse.get_pos()

        ds.texto_em(tela, _t('Jogo de Ritmo'), self._fonte(30),
                    (painel.centerx, painel.y + 20), TEMA.texto, ancora='midtop')
        ds.texto_em(tela, _t('Toque no tempo exato de cada figura'), self._fonte(14),
                    (painel.centerx, painel.y + 56), TEMA.texto_apagado, ancora='midtop')

        x = painel.x + ds.ESPACO_XL
        largura_linha = painel.width - ds.ESPACO_XL * 2

        # Atalhos de configuracao
        self.rects_preset = []
        ativo = self.preset_ativo()
        largura_chip = (largura_linha - ds.ESPACO_SM * (len(PRESETS) - 1)) // len(PRESETS)
        for i, (rotulo, _b, _s, _c) in enumerate(PRESETS):
            r = pygame.Rect(x + i * (largura_chip + ds.ESPACO_SM), painel.y + 88,
                            largura_chip, 30)
            ds.chip(tela, r, _t(rotulo), self._fonte(13), ativo=(i == ativo))
            self.rects_preset.append(r)

        y = painel.y + 134

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
            return y_atual + 44

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

        ds.texto_em(tela, _t('Toque no instrumento ou use a barra de espaco'),
                    self._fonte(12), (painel.centerx, painel.bottom - 78),
                    TEMA.texto_apagado, ancora='midtop',
                    largura_max=largura_linha)

        self.btn_start.size = (largura_linha, 46)
        self.btn_start.topleft = (x, painel.bottom - 60)
        ds.botao(tela, self.btn_start, _t('Comecar'), self._fonte(20),
                 variante='primario', hover=self.btn_start.collidepoint(pos_mouse))

    def _desenhar_resultado(self, tela, largura, altura):
        """Resumo da partida, com precisao, tendencia e distribuicao."""
        r = self.resultado or self.resumo()
        painel = pygame.Rect(0, 0, min(560, largura - 80), min(430, altura - 60))
        painel.center = (largura // 2, altura // 2)
        ds.painel(tela, painel, None, None, acento=TEMA.acento)
        pos_mouse = pygame.mouse.get_pos()

        ds.texto_em(tela, _t('Fim da partida'), self._fonte(26),
                    (painel.centerx, painel.y + 18), TEMA.texto, ancora='midtop')
        ds.texto_em(tela, f"{r['bpm']} BPM  ·  {_t(r['subdivisao'])}  ·  {r['compasso']}/4",
                    self._fonte(13), (painel.centerx, painel.y + 52),
                    TEMA.texto_apagado, ancora='midtop')

        largura_caixa = (painel.width - ds.ESPACO_XL * 2 - ds.ESPACO_MD * 2) // 3
        texto_tend, cor_tend = self.tendencia(r['desvio_medio'])
        caixas = [
            (f"{r['precisao']:.0f}%", _t('precisao'), TEMA.verde),
            (f"{r['desvio_medio']:+.0f} ms", texto_tend or _t('desvio'), cor_tend),
            (str(r['melhor_sequencia']), _t('melhor sequencia'), TEMA.ciano),
        ]
        for i, (valor, legenda, cor) in enumerate(caixas):
            caixa = pygame.Rect(painel.x + ds.ESPACO_XL + i * (largura_caixa + ds.ESPACO_MD),
                                painel.y + 84, largura_caixa, 76)
            ds.caixa_valor(tela, caixa, valor, legenda, self._fonte(22),
                           self._fonte(11), cor=cor)

        ds.texto_em(tela, f"{r['acertos']} {_t('de')} {r['tentativas']} {_t('figuras')}",
                    self._fonte(13), (painel.centerx, painel.y + 172),
                    TEMA.texto_suave, ancora='midtop')
        if r['espalhamento']:
            ds.texto_em(tela, f"{_t('Constancia')}: ±{r['espalhamento']:.0f} ms",
                        self._fonte(12), (painel.centerx, painel.y + 194),
                        TEMA.texto_apagado, ancora='midtop')

        self._barra_graus(tela, pygame.Rect(painel.x + ds.ESPACO_XL, painel.y + 224,
                                            painel.width - ds.ESPACO_XL * 2, 80))

        largura_botao = (painel.width - ds.ESPACO_XL * 2 - ds.ESPACO_MD) // 2
        self.btn_de_novo = pygame.Rect(painel.x + ds.ESPACO_XL, painel.bottom - 58,
                                       largura_botao, 42)
        self.btn_ajustes = pygame.Rect(self.btn_de_novo.right + ds.ESPACO_MD,
                                       self.btn_de_novo.y, largura_botao, 42)
        ds.botao(tela, self.btn_de_novo, _t('Jogar de novo'), self._fonte(15),
                 variante='primario', hover=self.btn_de_novo.collidepoint(pos_mouse))
        ds.botao(tela, self.btn_ajustes, _t('Ajustes'), self._fonte(15),
                 variante='secundario', hover=self.btn_ajustes.collidepoint(pos_mouse))

    def desenhar(self, tela, largura, altura, estado, meu_gravador=None, configs=None):
        """
            Como funciona: Atualiza a logica e desenha pista, figuras e placar.
            Para que serve: Loop visual do jogo de ritmo.
            Onde e usada: Chamada pelo gerenciador de jogos.
        """
        self._layout(largura, altura)
        self.inicializado = True
        if configs is not None:
            TEMA.definir_acento(configs.get_cor_tema())

        self.atualizar(estado, meu_gravador, configs)
        ds.fundo_app(tela, pygame.Rect(0, 0, largura, altura))

        if not self.jogo_iniciado:
            if self.mostrar_resultado:
                self._desenhar_resultado(tela, largura, altura)
            else:
                self._desenhar_ajustes(tela, largura, altura)
            return

        mult_vel = configs.get_vel_jogo() if configs else 1.0
        self._desenhar_pista(tela, mult_vel)
        self._desenhar_figuras(tela, mult_vel)
        self._desenhar_placar(tela)
        self._desenhar_lateral(tela)
        self._contagem_regressiva(tela)

    # ------------------------------------------------------------ entrada --
    def tratar_tecla(self, evento):
        """
            Como funciona: Barra de espaco vale como ataque e P encerra.
            Para que serve: Jogar mesmo sem instrumento ligado na entrada.
            Onde e usada: Chamada pelo gerenciador de jogos.
        """
        if evento.type != pygame.KEYDOWN:
            return False
        if evento.key == pygame.K_SPACE:
            if self.jogo_iniciado:
                self.registrar_ataque_manual()
            elif self.mostrar_resultado:
                self.iniciar_jogo()
            else:
                self.iniciar_jogo()
            return True
        if evento.key == pygame.K_p and self.jogo_iniciado:
            self.parar_jogo()
            return True
        return False

    def tratar_clique(self, pos, meu_gravador=None):
        """
            Como funciona: Trata os controles da tela inicial, do jogo e do
            resultado.
            Para que serve: Ajustar o exercicio, jogar e rever a partida.
            Onde e usada: Chamada pelo gerenciador de jogos.
        """
        if self.jogo_iniciado:
            if self.btn_parar.collidepoint(pos):
                self.parar_jogo(); return True
            if self.btn_metronomo_jogo.collidepoint(pos):
                self.metronomo_on = not self.metronomo_on; return True
            return False

        if self.mostrar_resultado:
            if self.btn_de_novo.collidepoint(pos):
                self.iniciar_jogo(); return True
            if self.btn_ajustes.collidepoint(pos):
                self.mostrar_resultado = False; return True
            return False

        for i, r in enumerate(self.rects_preset):
            if r.collidepoint(pos):
                self.aplicar_preset(i); return True
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
