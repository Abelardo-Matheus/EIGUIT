# -*- coding: utf-8 -*-
"""Widgets de audio: paleta de graus e painel de afinacao/processamento."""
import math

import pygame

from config.theme import *
from config.ui_metrics import *
from config.app_settings import *
from config.design_system import TEMA, ds
from core.i18n import _t

NOTAS_CROMATICAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# A partir destas medidas o painel abre no formato de tres colunas do canvas.
LARGURA_MIN_COMPLETO = 560
ALTURA_MIN_COMPLETO = 230

DB_MIN = -60.0
NOISE_GATE_MIN = -70.0
NOISE_GATE_MAX = -10.0


def _analisar_frequencia(freq):
    """Devolve (nome_nota, oitava, desvio_em_cents) para uma frequencia em Hz."""
    try:
        f = float(freq)
    except (TypeError, ValueError):
        return None, None, 0.0
    if f < 20.0:
        return None, None, 0.0
    valor = 12 * math.log2(f / 440.0)
    semitons = round(valor)
    cents = (valor - semitons) * 100.0
    nome = NOTAS_CROMATICAS[int((semitons + 9) % 12)]
    oitava = 4 + (semitons + 9) // 12
    return nome, int(oitava), cents


def _nome_afinacao(estado):
    try:
        return _t(lista_afinacoes[estado.indice_afinacao]['nome'])
    except (IndexError, KeyError, TypeError, AttributeError):
        return _t('Standard')


# ---------------------------------------------------------------------------
# PALETA DE GRAUS
# ---------------------------------------------------------------------------

def desenhar_painel_cores(tela, estado, fontes):
    """
        Como funciona: Desenha o seletor de cores dos graus (tonica, terca e quinta).
        Para que serve: Identificar visualmente os graus no braco.
        Onde e usada: Chamada pelo renderizador do workspace.
    """
    if not hasattr(estado, 'dragger_cores'):
        return

    d = estado.dragger_cores
    rect = pygame.Rect(d.x, d.y, d.largura, d.altura)
    y = ds.painel(tela, rect, _t('Cores (Graus)'), fontes['pequena'],
                  acento=TEMA.acento)

    itens = [
        (_t('Tonica (1)'), estado.indice_cor_tonica, 'rect_cor_tonica'),
        (_t('Terca (3)'), estado.indice_cor_terca, 'rect_cor_terca'),
        (_t('Quinta (5)'), estado.indice_cor_quinta, 'rect_cor_quinta'),
    ]

    disponivel = max(24, rect.bottom - y - ds.ESPACO_MD)
    altura_linha = min(38, disponivel // 3)
    tam_amostra = min(24, altura_linha - 6)

    for texto, indice, nome_rect in itens:
        linha = pygame.Rect(rect.x + ds.ESPACO_MD, y,
                            rect.width - ds.ESPACO_MD * 2, altura_linha)
        rect_cor = pygame.Rect(0, 0, tam_amostra, tam_amostra)
        rect_cor.midright = (linha.right, linha.centery)

        ds.texto_em(tela, texto, fontes['pequena'], (linha.x, linha.centery),
                    TEMA.texto_suave, ancora='midleft',
                    largura_max=linha.width - tam_amostra - ds.ESPACO_SM)
        ds.amostra_cor(tela, rect_cor,
                       CORES_TONICA[indice % len(CORES_TONICA)], False, ds.RAIO_SM)
        setattr(estado, nome_rect, rect_cor)
        y += altura_linha

    if estado.drag_ativado:
        d.desenhar_caixa_selecao(tela, margem=5)


# ---------------------------------------------------------------------------
# BLOCOS DO PAINEL DE AUDIO
# ---------------------------------------------------------------------------

def _coluna_afinador(tela, estado, fontes, rect, nota, oitava, cents, detectando):
    """Nota detectada, afinacao ativa, medidor de desvio e precisao."""
    y = rect.y

    rotulo = f'{nota}{oitava}' if (detectando and oitava is not None) else nota
    cor_nota = TEMA.verde if detectando else TEMA.texto_apagado
    ds.texto_em(tela, rotulo, fontes['titulo'], (rect.centerx, y), cor_nota,
                ancora='midtop' if False else 'midtop')
    y += fontes['titulo'].get_height() + 2

    ds.texto_em(tela, _nome_afinacao(estado), fontes['pequena'],
                (rect.centerx, y), TEMA.texto_apagado, ancora='midtop',
                largura_max=rect.width)
    y += fontes['pequena'].get_height() + ds.ESPACO_MD

    if detectando:
        try:
            hz = f'{float(estado.freq_detectada):.2f} Hz'
        except (TypeError, ValueError):
            hz = ''
    else:
        hz = _t('sem sinal')
    ds.texto_em(tela, hz, fontes['pequena'], (rect.centerx, y),
                TEMA.ciano if detectando else TEMA.texto_apagado, ancora='midtop')
    y += fontes['pequena'].get_height() + ds.ESPACO_MD

    rect_medidor = pygame.Rect(rect.x, y, rect.width, 8)
    if detectando:
        ds.medidor_desvio(tela, rect_medidor, cents, 50.0, fontes['pequena'])
    else:
        pygame.draw.rect(tela, ds.rgb(TEMA.trilho), rect_medidor, border_radius=4)
        pygame.draw.line(tela, ds.rgb(TEMA.borda),
                         (rect_medidor.centerx, rect_medidor.y - 3),
                         (rect_medidor.centerx, rect_medidor.bottom + 3), 2)
        ds.texto_em(tela, _t('Toque uma nota'), fontes['pequena'],
                    (rect_medidor.centerx, rect_medidor.bottom + ds.ESPACO_SM),
                    TEMA.texto_apagado, ancora='midtop')
    y = rect_medidor.bottom + ds.ESPACO_SM + fontes['pequena'].get_height() + ds.ESPACO_SM

    sessao = getattr(estado, 'sessao', None)
    if sessao is not None and y + fontes['pequena'].get_height() <= rect.bottom:
        ds.texto_em(tela, _t('Precisao'), fontes['pequena'], (rect.x, y),
                    TEMA.texto_apagado)
        ds.texto_em(tela, f'{sessao.precisao_recente}%', fontes['pequena'],
                    (rect.right, y), TEMA.verde, ancora='topright')


def _coluna_processador(tela, estado, fontes, rect):
    """Nivel de entrada, sensibilidade, portao de ruido e acoes."""
    pos_mouse = pygame.mouse.get_pos()
    y = rect.y
    fonte_p = fontes['pequena']
    passo = fonte_p.get_height() + ds.ESPACO_SM + ds.ALTURA_TRILHO + ds.ESPACO_LG

    # --- Nivel de entrada (somente leitura) --------------------------------
    nivel = float(getattr(estado, 'nivel_entrada_db', DB_MIN))
    pct_nivel = max(0.0, min(1.0, (nivel - DB_MIN) / (0.0 - DB_MIN)))
    ds.texto_em(tela, _t('Nivel de entrada'), fonte_p, (rect.x, y), TEMA.texto_suave)
    ds.texto_em(tela, f'{nivel:.0f} dB', fonte_p, (rect.right, y),
                TEMA.verde if nivel > estado.afinador_noise_gate else TEMA.texto_apagado,
                ancora='topright')
    y += fonte_p.get_height() + ds.ESPACO_SM
    barra_nivel = pygame.Rect(rect.x, y, rect.width, ds.ALTURA_TRILHO)
    cor_nivel = TEMA.alerta if nivel > -3 else (TEMA.aviso if nivel > -12 else TEMA.verde)
    ds.trilho(tela, barra_nivel, pct_nivel, cor_nivel)
    # marca do portao de ruido sobre a barra de nivel
    pct_gate = max(0.0, min(1.0, (estado.afinador_noise_gate - DB_MIN) / (0.0 - DB_MIN)))
    x_gate = barra_nivel.x + int(barra_nivel.width * pct_gate)
    pygame.draw.line(tela, ds.rgb(TEMA.texto), (x_gate, barra_nivel.y - 3),
                     (x_gate, barra_nivel.bottom + 3), 2)
    y += ds.ALTURA_TRILHO + ds.ESPACO_LG

    # --- Sensibilidade -----------------------------------------------------
    pct_sens = (estado.afinador_threshold - 0.1) / 0.7
    barra, alca = ds.slider(tela, pygame.Rect(rect.x, y + fonte_p.get_height() + ds.ESPACO_SM,
                                              rect.width, ds.ALTURA_TRILHO),
                            pct_sens, rotulo=_t('Sensibilidade'),
                            valor=f'{estado.afinador_threshold:.2f}', fonte=fonte_p)
    estado.rect_barra_threshold = barra
    estado.rect_alca_threshold = alca
    y += passo

    # --- Portao de ruido ---------------------------------------------------
    pct_ng = (estado.afinador_noise_gate - NOISE_GATE_MIN) / (NOISE_GATE_MAX - NOISE_GATE_MIN)
    barra_ng, alca_ng = ds.slider(tela, pygame.Rect(rect.x, y + fonte_p.get_height() + ds.ESPACO_SM,
                                                    rect.width, ds.ALTURA_TRILHO),
                                  pct_ng, rotulo=_t('Portao de ruido'),
                                  valor=f'{estado.afinador_noise_gate:.0f} dB',
                                  fonte=fonte_p)
    estado.rect_barra_noise_gate = barra_ng
    estado.rect_alca_noise_gate = alca_ng
    y += passo

    # --- Persistencia ------------------------------------------------------
    if y + passo <= rect.bottom + ds.ESPACO_LG:
        pct_pers = (estado.afinador_persistencia - 100) / 2900
        barra_p, alca_p = ds.slider(tela, pygame.Rect(rect.x, y + fonte_p.get_height() + ds.ESPACO_SM,
                                                      rect.width, ds.ALTURA_TRILHO),
                                    pct_pers, rotulo=_t('Persistencia'),
                                    valor=f'{estado.afinador_persistencia} ms',
                                    fonte=fonte_p)
        estado.rect_barra_persistencia = barra_p
        estado.rect_alca_persistencia = alca_p
        y += passo

    # --- Acoes -------------------------------------------------------------
    altura_btn = 28
    if y + altura_btn <= rect.bottom + ds.ESPACO_SM:
        largura_btn = (rect.width - ds.ESPACO_SM) // 2
        estado.rect_btn_calibrar = pygame.Rect(rect.x, y, largura_btn, altura_btn)
        estado.rect_btn_reset_audio = pygame.Rect(rect.x + largura_btn + ds.ESPACO_SM,
                                                  y, largura_btn, altura_btn)
        ds.botao(tela, estado.rect_btn_calibrar, _t('Calibrar'), fonte_p,
                 variante='suave',
                 hover=estado.rect_btn_calibrar.collidepoint(pos_mouse))
        ds.botao(tela, estado.rect_btn_reset_audio, _t('Resetar'), fonte_p,
                 variante='secundario',
                 hover=estado.rect_btn_reset_audio.collidepoint(pos_mouse))
    else:
        estado.rect_btn_calibrar = pygame.Rect(-100, -100, 0, 0)
        estado.rect_btn_reset_audio = pygame.Rect(-100, -100, 0, 0)


def _coluna_waveform(tela, estado, fontes, rect, motor_audio, detectando):
    """Forma de onda em tempo real a partir do buffer do microfone."""
    ds.superficie_translucida(tela, rect, TEMA.fundo, 170, ds.RAIO_MD, TEMA.borda, 1)

    amostras = None
    if motor_audio is not None:
        try:
            buffer = motor_audio.buffer
            passo = max(1, len(buffer) // max(2, rect.width // 3))
            amostras = [float(v) for v in buffer[::passo]]
        except Exception:
            amostras = None

    meio = rect.centery
    pygame.draw.line(tela, ds.rgb(TEMA.borda), (rect.x + 4, meio),
                     (rect.right - 4, meio), 1)

    if amostras and len(amostras) > 1:
        pico = max(1e-4, max(abs(v) for v in amostras))
        escala = (rect.height / 2 - 6) / max(pico, 0.05)
        largura_util = rect.width - 8
        pontos = [
            (rect.x + 4 + i * largura_util / (len(amostras) - 1),
             meio - max(-1.0, min(1.0, v)) * escala)
            for i, v in enumerate(amostras)
        ]
        pontos = [(x, max(rect.y + 2, min(rect.bottom - 2, y))) for x, y in pontos]
        cor = TEMA.ciano if detectando else TEMA.texto_apagado
        pygame.draw.lines(tela, ds.rgb(cor), False, pontos, 2)
    else:
        ds.texto_centralizado(tela, _t('Sem entrada'), fontes['pequena'], rect,
                              TEMA.texto_apagado)


def _seletor_cromatico(tela, estado, fontes, rect, nota, detectando):
    """Fileira de 12 notas para escolher a nota-alvo."""
    estado.rects_notas_selecao.clear()
    largura_celula = rect.width / 12
    for i, n in enumerate(NOTAS_CROMATICAS):
        rect_n = pygame.Rect(int(rect.x + i * largura_celula), rect.y,
                             max(12, int(largura_celula) - 2), rect.height)
        estado.rects_notas_selecao.append((rect_n, n))
        selecionada = estado.nota_selecionada_bloco == n
        tocando = detectando and n == nota
        if selecionada:
            pygame.draw.rect(tela, ds.rgb(TEMA.acento), rect_n,
                             border_radius=ds.RAIO_SM)
            cor_txt = TEMA.texto_sobre_cor
        elif tocando:
            ds.superficie_translucida(tela, rect_n, TEMA.verde, 70, ds.RAIO_SM,
                                      TEMA.verde, 1)
            cor_txt = TEMA.verde
        else:
            ds.superficie_translucida(tela, rect_n, TEMA.superficie_alt, 200,
                                      ds.RAIO_SM, TEMA.borda, 1)
            cor_txt = TEMA.texto_suave
        if fontes['pequena'].size(n)[0] < rect_n.width:
            ds.texto_centralizado(tela, n, fontes['pequena'], rect_n, cor_txt)


def desenhar_bloco_nota_atual(tela, estado, fontes, configs, motor_audio=None):
    """
        Como funciona: Em painel largo, mostra tres colunas (afinador,
        processamento de audio e forma de onda) mais o seletor cromatico. Em
        painel estreito, cai para um layout compacto de uma coluna.
        Para que serve: Afinacao, monitoramento de entrada e escolha da nota-alvo.
        Onde e usada: Chamada pelo renderizador do workspace.
    """
    if not hasattr(estado, 'dragger_nota_atual'):
        return
    if configs is not None:
        TEMA.definir_acento(configs.get_cor_tema())

    d = estado.dragger_nota_atual
    rect = pygame.Rect(d.x, d.y, d.largura, d.altura)
    ds.painel(tela, rect, None, None, acento=TEMA.acento)

    nota = estado.nota_atual_detectada
    detectando = nota != '--'
    _, oitava, cents = _analisar_frequencia(getattr(estado, 'freq_detectada', 0))

    pad = ds.ESPACO_LG
    interno = pygame.Rect(rect.x + pad, rect.y + ds.ESPACO_MD,
                          rect.width - pad * 2, rect.height - ds.ESPACO_MD * 2)

    completo = (rect.width >= LARGURA_MIN_COMPLETO
                and rect.height >= ALTURA_MIN_COMPLETO)

    if completo:
        altura_cromatico = 26
        sobra = interno.height - altura_cromatico - ds.ESPACO_MD
        altura_colunas = sobra if sobra > 120 else interno.height
        mostrar_cromatico = sobra > 120

        gap = ds.ESPACO_LG
        largura_col = (interno.width - gap * 2) // 3
        titulos = (_t('Afinador'), _t('Processamento'), _t('Forma de onda'))
        colunas = []
        for i in range(3):
            x = interno.x + i * (largura_col + gap)
            ds.rotulo_secao(tela, x, interno.y, titulos[i], fontes['pequena'],
                            TEMA.acento, largura_max=largura_col)
            colunas.append(pygame.Rect(
                x, interno.y + fontes['pequena'].get_height() + ds.ESPACO_SM,
                largura_col,
                altura_colunas - fontes['pequena'].get_height() - ds.ESPACO_SM))

        # separadores verticais
        for i in (1, 2):
            x_div = interno.x + i * (largura_col + gap) - gap // 2
            pygame.draw.line(tela, ds.rgb(TEMA.borda), (x_div, interno.y),
                             (x_div, colunas[0].bottom), 1)

        _coluna_afinador(tela, estado, fontes, colunas[0], nota, oitava, cents,
                         detectando)
        _coluna_processador(tela, estado, fontes, colunas[1])
        _coluna_waveform(tela, estado, fontes, colunas[2], motor_audio, detectando)

        if mostrar_cromatico:
            _seletor_cromatico(
                tela, estado, fontes,
                pygame.Rect(interno.x, interno.bottom - altura_cromatico,
                            interno.width, altura_cromatico), nota, detectando)
        else:
            estado.rects_notas_selecao.clear()
    else:
        _desenhar_compacto(tela, estado, fontes, interno, nota, oitava, cents,
                           detectando)

    if estado.drag_ativado:
        d.desenhar_caixa_selecao(tela, margem=8)


def _desenhar_compacto(tela, estado, fontes, interno, nota, oitava, cents, detectando):
    """Layout de uma coluna, usado quando o painel esta estreito."""
    x, largura = interno.x, interno.width
    y = interno.y

    rotulo = f'{nota}{oitava}' if (detectando and oitava is not None) else nota
    ds.texto_em(tela, rotulo, fontes['titulo'], (x, y),
                TEMA.verde if detectando else TEMA.texto_apagado)
    largura_nota = fontes['titulo'].size(rotulo)[0]
    if detectando:
        try:
            ds.texto_em(tela, f'{float(estado.freq_detectada):.1f} Hz',
                        fontes['pequena'],
                        (x + largura_nota + ds.ESPACO_SM,
                         y + fontes['titulo'].get_height() - ds.ESPACO_SM),
                        TEMA.texto_apagado)
        except (TypeError, ValueError):
            pass
    ds.texto_em(tela, _nome_afinacao(estado), fontes['pequena'],
                (interno.right, y + 2), TEMA.texto_apagado, ancora='topright',
                largura_max=largura // 2)
    y += fontes['titulo'].get_height() + ds.ESPACO_MD

    rect_medidor = pygame.Rect(x, y, largura, 8)
    if detectando:
        ds.medidor_desvio(tela, rect_medidor, cents, 50.0, fontes['pequena'])
    else:
        pygame.draw.rect(tela, ds.rgb(TEMA.trilho), rect_medidor, border_radius=4)
        pygame.draw.line(tela, ds.rgb(TEMA.borda),
                         (rect_medidor.centerx, rect_medidor.y - 3),
                         (rect_medidor.centerx, rect_medidor.bottom + 3), 2)
        ds.texto_em(tela, _t('Toque uma nota'), fontes['pequena'],
                    (rect_medidor.centerx, rect_medidor.bottom + ds.ESPACO_SM),
                    TEMA.texto_apagado, ancora='midtop')
    y += 8 + ds.ESPACO_SM + fontes['pequena'].get_height() + ds.ESPACO_MD

    altura_celula = min(26, max(18, int(largura / 12 * 1.15)))
    _seletor_cromatico(tela, estado, fontes,
                       pygame.Rect(x, y, largura, altura_celula), nota, detectando)
    y += altura_celula + ds.ESPACO_LG + fontes['pequena'].get_height()

    espaco = max(28, (interno.bottom - y) // 2)
    pct_pers = (estado.afinador_persistencia - 100) / 2900
    barra, alca = ds.slider(tela, pygame.Rect(x, y, largura, ds.ALTURA_TRILHO),
                            pct_pers, rotulo=_t('Persistencia'),
                            valor=f'{estado.afinador_persistencia} ms',
                            fonte=fontes['pequena'])
    estado.rect_barra_persistencia, estado.rect_alca_persistencia = barra, alca

    y += espaco
    pct_sens = (estado.afinador_threshold - 0.1) / 0.7
    barra_t, alca_t = ds.slider(tela, pygame.Rect(x, y, largura, ds.ALTURA_TRILHO),
                                pct_sens, rotulo=_t('Sensibilidade'),
                                valor=f'{estado.afinador_threshold:.2f}',
                                fonte=fontes['pequena'])
    estado.rect_barra_threshold, estado.rect_alca_threshold = barra_t, alca_t

    # Sem espaco para o portao de ruido e as acoes no modo compacto
    estado.rect_barra_noise_gate = pygame.Rect(-100, -100, 0, 0)
    estado.rect_alca_noise_gate = pygame.Rect(-100, -100, 0, 0)
    estado.rect_btn_calibrar = pygame.Rect(-100, -100, 0, 0)
    estado.rect_btn_reset_audio = pygame.Rect(-100, -100, 0, 0)
