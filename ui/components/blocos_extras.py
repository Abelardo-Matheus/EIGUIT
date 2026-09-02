# -*- coding: utf-8 -*-
"""
Blocos extras do workspace.

Tres widgets pequenos que faltavam num estudio de musica:

- Circulo de quintas compacto: navegacao harmonica de relance. Clicar numa
  tonalidade muda o campo harmonico inteiro.
- Historico de notas: as ultimas notas captadas e o intervalo entre elas.
  Serve para conferir o que voce acabou de tocar e treinar ouvido.
- Ideias: grava um trecho curto com um clique, para nao perder a frase que
  apareceu no meio do estudo.
"""
import math
import os
import time

import pygame

from config.design_system import TEMA, ds
from core.i18n import _t

NOTAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
CICLO = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#', 'F']
RELATIVAS = ['Am', 'Em', 'Bm', 'F#m', 'C#m', 'G#m', 'D#m', 'A#m', 'Fm', 'Cm', 'Gm', 'Dm']

NOMES_INTERVALOS = ['uni', '2m', '2M', '3m', '3M', '4J', 'trit',
                    '5J', '6m', '6M', '7m', '7M']


def intervalo_entre(nota_a, nota_b):
    """Nome curto do intervalo entre duas notas, subindo."""
    try:
        return NOMES_INTERVALOS[(NOTAS.index(nota_b) - NOTAS.index(nota_a)) % 12]
    except ValueError:
        return ''


# ---------------------------------------------------------------------------
# CIRCULO DE QUINTAS COMPACTO
# ---------------------------------------------------------------------------

def desenhar_bloco_circulo(tela, estado, fontes, configs=None, campo=None):
    """
        Como funciona: Desenha as doze tonalidades em circulo e marca a que
        esta em uso, junto com as duas vizinhas.
        Para que serve: Trocar de tonalidade sem abrir nenhuma aba.
        Onde e usada: Workspace, bloco arrastavel do circulo.
    """
    if not hasattr(estado, 'dragger_circulo'):
        return
    if configs is not None:
        TEMA.definir_acento(configs.get_cor_tema())

    d = estado.dragger_circulo
    rect = pygame.Rect(d.x, d.y, d.largura, d.altura)
    y = ds.painel(tela, rect, _t('Circulo de quintas'), fontes['pequena'],
                  acento=TEMA.acento)

    tonica = getattr(campo, 'tonica_campo', 'C') if campo else 'C'
    indice_atual = CICLO.index(tonica) if tonica in CICLO else 0

    area = pygame.Rect(rect.x, y, rect.width, rect.bottom - y - ds.ESPACO_SM)
    raio = min(area.width, area.height) * 0.38
    if raio < 26:
        estado.rects_circulo = []
        ds.texto_centralizado(tela, _t('Amplie o bloco'), fontes['pequena'], area,
                              TEMA.texto_apagado)
        return
    centro = (area.centerx, area.centery)
    tam = max(9, int(raio * 0.24))

    estado.rects_circulo = []
    for i in range(12):
        angulo = -math.pi / 2 + i * math.tau / 12
        cx = centro[0] + math.cos(angulo) * raio
        cy = centro[1] + math.sin(angulo) * raio
        r = pygame.Rect(0, 0, tam * 2, tam * 2)
        r.center = (int(cx), int(cy))
        estado.rects_circulo.append((r, CICLO[i]))

        selecionada = i == indice_atual
        vizinha = (i - indice_atual) % 12 in (1, 11)
        if selecionada:
            pygame.draw.circle(tela, ds.rgb(TEMA.acento), r.center, tam)
            cor = TEMA.texto_sobre_cor
        elif vizinha:
            pygame.draw.circle(tela, ds.rgb(ds.misturar(TEMA.superficie_alt,
                                                        TEMA.ciano, 0.45)),
                               r.center, tam)
            cor = TEMA.texto
        else:
            pygame.draw.circle(tela, ds.rgb(TEMA.superficie_alt), r.center, tam)
            pygame.draw.circle(tela, ds.rgb(TEMA.borda), r.center, tam, 1)
            cor = TEMA.texto_apagado
        if tam >= 11:
            ds.texto_em(tela, CICLO[i], fontes['pequena'], r.center, cor, ancora='center')

    ds.texto_em(tela, tonica, fontes['titulo'], (centro[0], centro[1] - 8),
                TEMA.acento, ancora='center')
    ds.texto_em(tela, RELATIVAS[indice_atual], fontes['pequena'],
                (centro[0], centro[1] + 12), TEMA.texto_apagado, ancora='center')

    if estado.drag_ativado:
        d.desenhar_caixa_selecao(tela, margem=5)


# ---------------------------------------------------------------------------
# HISTORICO DE NOTAS
# ---------------------------------------------------------------------------

def registrar_nota_historico(estado, nota):
    """Guarda a nota quando ela muda, mantendo as ultimas doze.

    O silencio ('--' ou vazio) conta como separador: se a mesma nota voltar
    depois de uma pausa ela e registrada de novo, porque foi tocada de novo.
    """
    anterior = getattr(estado, 'ultima_nota_historico', None)
    estado.ultima_nota_historico = nota if nota else '--'
    if not nota or nota == '--':
        return
    historico = getattr(estado, 'historico_notas', None)
    if historico is None:
        historico = []
        estado.historico_notas = historico
    if anterior == nota:
        return
    historico.append(nota)
    del historico[:-12]


def desenhar_bloco_historico(tela, estado, fontes, configs=None):
    """
        Como funciona: Mostra as ultimas notas captadas e, entre elas, o
        intervalo que as separa.
        Para que serve: Conferir a frase que acabou de sair e treinar ouvido.
        Onde e usada: Workspace, bloco arrastavel de historico.
    """
    if not hasattr(estado, 'dragger_historico'):
        return
    if configs is not None:
        TEMA.definir_acento(configs.get_cor_tema())

    d = estado.dragger_historico
    rect = pygame.Rect(d.x, d.y, d.largura, d.altura)
    y = ds.painel(tela, rect, _t('Notas tocadas'), fontes['pequena'],
                  acento=TEMA.acento)

    historico = getattr(estado, 'historico_notas', [])
    estado.rect_btn_limpar_historico = pygame.Rect(
        rect.right - ds.ESPACO_MD - 18, rect.y + ds.ESPACO_MD, 18, 18)
    if historico:
        ds.texto_centralizado(tela, 'x', fontes['pequena'],
                              estado.rect_btn_limpar_historico, TEMA.texto_apagado)

    if not historico:
        ds.texto_em(tela, _t('Toque algo para comecar'), fontes['pequena'],
                    (rect.centerx, y + ds.ESPACO_MD), TEMA.texto_apagado,
                    ancora='midtop', largura_max=rect.width - ds.ESPACO_LG)
        if estado.drag_ativado:
            d.desenhar_caixa_selecao(tela, margem=5)
        return

    pad = ds.ESPACO_MD
    largura_util = rect.width - pad * 2
    visiveis = historico[-8:]
    largura_nota = min(34, largura_util / max(1, len(visiveis)))
    altura_nota = min(28, max(18, rect.bottom - y - 34))

    x = rect.x + pad
    for i, nota in enumerate(visiveis):
        celula = pygame.Rect(int(x), int(y + 2), int(largura_nota) - 3, int(altura_nota))
        recente = i == len(visiveis) - 1
        ds.superficie_translucida(
            tela, celula, TEMA.acento if recente else TEMA.superficie_alt,
            220, ds.RAIO_SM, TEMA.acento if recente else TEMA.borda, 1)
        ds.texto_centralizado(tela, nota, fontes['pequena'], celula,
                              TEMA.texto_sobre_cor if recente else TEMA.texto)
        if i > 0:
            nome = intervalo_entre(visiveis[i - 1], nota)
            ds.texto_em(tela, nome, fontes['pequena'],
                        (celula.x - 2, celula.bottom + 2), TEMA.ciano,
                        ancora='midtop')
        x += largura_nota

    if rect.bottom - (y + altura_nota) > 34:
        ds.texto_em(tela, f"{_t('Ultimas')} {len(historico)} {_t('notas')}",
                    fontes['pequena'], (rect.x + pad, rect.bottom - 20),
                    TEMA.texto_apagado)

    if estado.drag_ativado:
        d.desenhar_caixa_selecao(tela, margem=5)


# ---------------------------------------------------------------------------
# IDEIAS: GRAVACAO RAPIDA
# ---------------------------------------------------------------------------

def desenhar_bloco_ideias(tela, estado, fontes, configs=None, motor_audio=None):
    """
        Como funciona: Um botao que comeca e termina a gravacao do que esta
        entrando, salvando o arquivo na pasta Ideias.
        Para que serve: Nao perder a frase que apareceu no meio do estudo.
        Onde e usada: Workspace, bloco arrastavel de ideias.
    """
    if not hasattr(estado, 'dragger_ideias'):
        return
    if configs is not None:
        TEMA.definir_acento(configs.get_cor_tema())

    d = estado.dragger_ideias
    rect = pygame.Rect(d.x, d.y, d.largura, d.altura)
    y = ds.painel(tela, rect, _t('Ideias'), fontes['pequena'], acento=TEMA.acento)

    gravando = bool(motor_audio is not None and getattr(motor_audio, 'gravando', False))
    pad = ds.ESPACO_MD
    altura_btn = min(38, max(26, rect.bottom - y - 34))

    estado.rect_btn_gravar_ideia = pygame.Rect(
        rect.x + pad, y + 2, rect.width - pad * 2, altura_btn)
    ds.botao(tela, estado.rect_btn_gravar_ideia,
             _t('Parar e salvar') if gravando else _t('Gravar ideia'),
             fontes['pequena'], variante='perigo' if gravando else 'primario',
             hover=estado.rect_btn_gravar_ideia.collidepoint(pygame.mouse.get_pos()))

    if gravando:
        inicio = getattr(estado, 'inicio_gravacao_ideia', time.time())
        decorrido = int(time.time() - inicio)
        pygame.draw.circle(tela, ds.rgb(TEMA.alerta),
                           (rect.x + pad + 8, estado.rect_btn_gravar_ideia.bottom + 14), 5)
        ds.texto_em(tela, f'{decorrido // 60:02d}:{decorrido % 60:02d}',
                    fontes['pequena'], (rect.x + pad + 20,
                                        estado.rect_btn_gravar_ideia.bottom + 6),
                    TEMA.alerta)
    else:
        ultima = getattr(estado, 'ultima_ideia_salva', '')
        texto = (f"{_t('Ultima')}: {os.path.basename(ultima)}" if ultima
                 else _t('Grava a entrada de audio'))
        ds.texto_em(tela, texto, fontes['pequena'],
                    (rect.x + pad, estado.rect_btn_gravar_ideia.bottom + 6),
                    TEMA.texto_apagado, largura_max=rect.width - pad * 2)

    if estado.drag_ativado:
        d.desenhar_caixa_selecao(tela, margem=5)


def alternar_gravacao_ideia(estado, motor_audio):
    """
        Como funciona: Inicia a gravacao ou a encerra, salvando na pasta
        Ideias com a data e a hora no nome.
        Para que serve: Acao do botao do bloco de ideias.
        Onde e usada: Chamada pelo controlador de eventos.
    """
    if motor_audio is None:
        return False
    if getattr(motor_audio, 'gravando', False):
        pasta = 'Ideias'
        try:
            os.makedirs(pasta, exist_ok=True)
        except OSError:
            pasta = '.'
        nome = time.strftime('ideia_%Y-%m-%d_%H-%M-%S.wav')
        caminho = motor_audio.parar_gravacao(os.path.join(pasta, nome))
        estado.ultima_ideia_salva = caminho or ''
    else:
        motor_audio.iniciar_gravacao()
        estado.inicio_gravacao_ideia = time.time()
    return True
