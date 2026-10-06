# -*- coding: utf-8 -*-
"""
Avisos curtos (toasts) que aparecem logo abaixo da barra superior.

Qualquer parte do programa pode chamar notificar(estado, 'texto') para dar
retorno ao usuario sem depender do console: perfil salvo, captura feita,
erro ao abrir arquivo e assim por diante.
"""
import time

import pygame

from config.design_system import TEMA, ds

DURACAO_PADRAO = 3.0
MAXIMO_NA_TELA = 4
_ICONES = {'info': 'i', 'erro': '!', 'aviso': '!'}


def notificar(estado, texto, tipo='info', duracao=DURACAO_PADRAO):
    """Empilha um aviso. tipo: 'info', 'sucesso', 'aviso' ou 'erro'."""
    if estado is None:
        print(f'[AVISO] {texto}')
        return
    fila = getattr(estado, 'notificacoes', None)
    if fila is None:
        fila = []
        estado.notificacoes = fila
    agora = time.time()
    # Mesmo texto repetido so renova o tempo, nao empilha de novo
    for aviso in fila:
        if aviso['texto'] == texto:
            aviso['ate'] = agora + duracao
            return
    fila.append({'texto': texto, 'tipo': tipo, 'inicio': agora,
                 'ate': agora + duracao})
    del fila[:-MAXIMO_NA_TELA]
    print(f'[{tipo.upper()}] {texto}')


def _cor(tipo):
    return {'sucesso': TEMA.verde, 'erro': TEMA.alerta,
            'aviso': TEMA.aviso}.get(tipo, TEMA.acento)


def desenhar_notificacoes(tela, estado, fonte, y_topo):
    """Desenha os avisos ativos no canto superior direito."""
    fila = getattr(estado, 'notificacoes', None)
    if not fila:
        return
    agora = time.time()
    fila[:] = [a for a in fila if a['ate'] > agora]
    largura_tela = tela.get_width()
    y = y_topo + ds.ESPACO_SM
    for aviso in fila:
        cor = _cor(aviso['tipo'])
        largura = min(460, fonte.size(aviso['texto'])[0] + 64)
        rect = pygame.Rect(largura_tela - largura - ds.ESPACO_LG, y, largura, 38)
        # Entra deslizando e sai sumindo
        entrada = min(1.0, (agora - aviso['inicio']) / 0.18) if ds.EFEITOS['animacoes'] else 1.0
        rect.x += int((1.0 - entrada) * 40)
        restante = aviso['ate'] - agora
        alpha = int(250 * max(0.0, min(1.0, restante / 0.35)))
        ds.sombra(tela, rect, ds.RAIO_LG, forca=90, deslocamento=3)
        ds.superficie_translucida(tela, rect, TEMA.superficie_alt, alpha,
                                  ds.RAIO_LG, ds.misturar(TEMA.borda, cor, 0.5), 1)
        pygame.draw.rect(tela, ds.rgb(cor), (rect.x, rect.y + 8, 3, rect.height - 16),
                         border_radius=2)
        centro = (rect.x + 22, rect.centery)
        pygame.draw.circle(tela, ds.rgb(cor), centro, 9)
        if aviso['tipo'] == 'sucesso':
            cx, cy = centro
            pygame.draw.lines(tela, ds.rgb(TEMA.texto_sobre_cor), False,
                              [(cx - 4, cy), (cx - 1, cy + 3), (cx + 4, cy - 3)], 2)
        else:
            ds.texto_em(tela, _ICONES.get(aviso['tipo'], 'i'), fonte, centro,
                        TEMA.texto_sobre_cor, ancora='center')
        ds.texto_em(tela, aviso['texto'], fonte, (rect.x + 40, rect.centery),
                    TEMA.texto, ancora='midleft', largura_max=rect.width - 52)
        y += rect.height + ds.ESPACO_SM
