# -*- coding: utf-8 -*-
"""Widgets de audio: paleta de graus e bloco de afinacao/entrada de microfone."""
import math

import pygame

from config.theme import *
from config.ui_metrics import *
from config.app_settings import *
from config.design_system import TEMA, ds
from core.i18n import _t

NOTAS_CROMATICAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


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


def desenhar_painel_cores(tela, estado, fontes):
    """
    Como funciona: Desenha o seletor de cores dos graus (tonica, terca e quinta).
    Para que serve: Permite identificar visualmente os graus no braco.
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

        ds.texto_em(tela, texto, fontes['pequena'],
                    (linha.x, linha.centery), TEMA.texto_suave,
                    ancora='midleft',
                    largura_max=linha.width - tam_amostra - ds.ESPACO_SM)
        ds.amostra_cor(tela, rect_cor,
                       CORES_TONICA[indice % len(CORES_TONICA)], False, ds.RAIO_SM)
        setattr(estado, nome_rect, rect_cor)
        y += altura_linha

    if estado.drag_ativado:
        d.desenhar_caixa_selecao(tela, margem=5)


def desenhar_bloco_nota_atual(tela, estado, fontes, configs):
    """
    Como funciona: Mostra a nota captada pelo microfone, o desvio de afinacao em
    cents, o seletor cromatico de nota-alvo e os ajustes do afinador.
    Para que serve: Painel principal de afinacao e monitoramento de entrada.
    Onde e usada: Chamada pelo renderizador do workspace.
    """
    if not hasattr(estado, 'dragger_nota_atual'):
        return

    d = estado.dragger_nota_atual
    rect = pygame.Rect(d.x, d.y, d.largura, d.altura)
    ds.painel(tela, rect, None, None, acento=TEMA.acento)

    nota = estado.nota_atual_detectada
    detectando = nota != '--'
    nome_freq, oitava, cents = _analisar_frequencia(getattr(estado, 'freq_detectada', 0))

    pad = ds.ESPACO_LG
    x = rect.x + pad
    largura_util = rect.width - pad * 2
    y = rect.y + ds.ESPACO_MD

    # --- Cabecalho: nota grande + frequencia ------------------------------
    cor_nota = TEMA.verde if detectando else TEMA.texto_apagado
    rotulo = f'{nota}{oitava}' if (detectando and oitava is not None) else nota
    ds.texto_em(tela, rotulo, fontes['titulo'], (x, y), cor_nota)

    largura_nota = fontes['titulo'].size(rotulo)[0]
    if detectando:
        try:
            hz = f'{float(estado.freq_detectada):.1f} Hz'
        except (TypeError, ValueError):
            hz = ''
        if hz:
            ds.texto_em(tela, hz, fontes['pequena'],
                        (x + largura_nota + ds.ESPACO_SM,
                         y + fontes['titulo'].get_height() - ds.ESPACO_SM),
                        TEMA.texto_apagado)

    # Indicador de sinal vivo no canto direito
    ds.texto_em(tela, _t('Entrada de Audio'), fontes['pequena'],
                (rect.right - pad, y + 2), TEMA.texto_apagado, ancora='topright',
                largura_max=largura_util // 2)
    pygame.draw.circle(tela, ds.rgb(TEMA.verde if detectando else TEMA.trilho),
                       (rect.right - pad - 2, y + fontes['pequena'].get_height() + 10), 4)

    y += fontes['titulo'].get_height() + ds.ESPACO_MD

    # --- Medidor de afinacao ----------------------------------------------
    rect_medidor = pygame.Rect(x, y, largura_util, 8)
    if detectando:
        ds.medidor_desvio(tela, rect_medidor, cents, 50.0, fontes['pequena'])
    else:
        pygame.draw.rect(tela, ds.rgb(TEMA.trilho), rect_medidor,
                         border_radius=4)
        pygame.draw.line(tela, ds.rgb(TEMA.borda),
                         (rect_medidor.centerx, rect_medidor.y - 3),
                         (rect_medidor.centerx, rect_medidor.bottom + 3), 2)
        ds.texto_em(tela, _t('Toque uma nota'), fontes['pequena'],
                    (rect_medidor.centerx,
                     rect_medidor.bottom + ds.ESPACO_SM + fontes['pequena'].get_height() // 2),
                    TEMA.texto_apagado, ancora='center')
    y += 8 + ds.ESPACO_SM + fontes['pequena'].get_height() + ds.ESPACO_MD

    # --- Seletor cromatico -------------------------------------------------
    estado.rects_notas_selecao.clear()
    largura_celula = largura_util / 12
    altura_celula = min(28, max(20, int(largura_celula * 1.15)))
    for i, n in enumerate(NOTAS_CROMATICAS):
        rect_n = pygame.Rect(int(x + i * largura_celula), y,
                             int(largura_celula) - 2, altura_celula)
        estado.rects_notas_selecao.append((rect_n, n))
        selecionada = estado.nota_selecionada_bloco == n
        tocando = detectando and n == nota
        if selecionada:
            pygame.draw.rect(tela, ds.rgb(TEMA.acento), rect_n,
                             border_radius=ds.RAIO_SM)
            cor_txt = TEMA.texto_sobre_cor
        elif tocando:
            ds.superficie_translucida(tela, rect_n, TEMA.verde, 70,
                                      ds.RAIO_SM, TEMA.verde, 1)
            cor_txt = TEMA.verde
        else:
            ds.superficie_translucida(tela, rect_n, TEMA.superficie_alt, 200,
                                      ds.RAIO_SM, TEMA.borda, 1)
            cor_txt = TEMA.texto_suave
        if fontes['pequena'].size(n)[0] < rect_n.width:
            ds.texto_centralizado(tela, n, fontes['pequena'], rect_n, cor_txt)
    y += altura_celula + ds.ESPACO_LG + fontes['pequena'].get_height()

    # --- Ajustes do afinador ----------------------------------------------
    espaco_restante = rect.bottom - y - ds.ESPACO_MD
    passo = max(28, espaco_restante // 2)

    pct_pers = (estado.afinador_persistencia - 100) / 2900
    barra, alca = ds.slider(
        tela, pygame.Rect(x, y, largura_util, ALTURA_TRILHO), pct_pers,
        rotulo=_t('Persistencia'), valor=f'{estado.afinador_persistencia} ms',
        fonte=fontes['pequena'])
    estado.rect_barra_persistencia = barra
    estado.rect_alca_persistencia = alca

    y += passo
    pct_sens = (estado.afinador_threshold - 0.1) / 0.7
    barra_t, alca_t = ds.slider(
        tela, pygame.Rect(x, y, largura_util, ALTURA_TRILHO), pct_sens,
        rotulo=_t('Sensibilidade'), valor=f'{estado.afinador_threshold:.2f}',
        fonte=fontes['pequena'])
    estado.rect_barra_threshold = barra_t
    estado.rect_alca_threshold = alca_t

    if estado.drag_ativado:
        d.desenhar_caixa_selecao(tela, margem=8)
