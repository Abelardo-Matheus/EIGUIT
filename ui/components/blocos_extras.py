# -*- coding: utf-8 -*-
"""
Blocos extras do workspace.

Cinco widgets pequenos que faltavam num estudio de musica:

- Circulo de quintas compacto: navegacao harmonica de relance. Clicar numa
  tonalidade muda o campo harmonico inteiro, e as vizinhas ficam marcadas
  como IV e V, que e para onde a musica costuma andar.
- Notas tocadas: as ultimas notas captadas, o intervalo entre elas e a marca
  de quais estao fora da tonalidade em uso.
- Ideias: grava um trecho curto com um clique e lista as ultimas gravacoes.
- Referencia: um drone sustentado na nota escolhida, para afinar de ouvido e
  para improvisar por cima.
- Progressoes: quatro giros classicos ja cifrados na tonalidade atual, com um
  clique para jogar todos os acordes no braco.
"""
import glob
import math
import os
import time

import pygame

from config.design_system import TEMA, ds
from core.i18n import _t

NOTAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
CICLO = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#', 'F']
RELATIVAS = ['Am', 'Em', 'Bm', 'F#m', 'C#m', 'G#m', 'D#m', 'A#m', 'Fm', 'Cm', 'Gm', 'Dm']
# Armadura de cada tonalidade do ciclo, na mesma ordem
ARMADURAS = ['-', '1#', '2#', '3#', '4#', '5#', '6#', '7#', '4b', '3b', '2b', '1b']

NOMES_INTERVALOS = ['uni', '2m', '2M', '3m', '3M', '4J', 'trit',
                    '5J', '6m', '6M', '7m', '7M']

# Campo harmonico maior: grau -> (algarismo, tipo de acorde)
CAMPO_MAIOR = [('I', 'maior'), ('ii', 'menor'), ('iii', 'menor'), ('IV', 'maior'),
               ('V', 'maior'), ('vi', 'menor'), ('vii', 'dim')]
GRAUS_ESCALA = [0, 2, 4, 5, 7, 9, 11]

# Giros classicos, por grau do campo maior
PROGRESSOES_RAPIDAS = [
    {'nome': 'Pop', 'graus': [0, 4, 5, 3]},
    {'nome': 'Doo-wop', 'graus': [0, 5, 3, 4]},
    {'nome': 'ii - V - I', 'graus': [1, 4, 0]},
    {'nome': 'Epica', 'graus': [5, 3, 0, 4]},
]

CORES_PROGRESSAO = [(80, 170, 255), (255, 170, 70), (120, 220, 150), (235, 120, 190)]


def intervalo_entre(nota_a, nota_b):
    """Nome curto do intervalo entre duas notas, subindo."""
    try:
        return NOMES_INTERVALOS[(NOTAS.index(nota_b) - NOTAS.index(nota_a)) % 12]
    except ValueError:
        return ''


def notas_da_tonalidade(tonica):
    """As sete notas da escala maior da tonica dada."""
    if tonica not in NOTAS:
        return []
    base = NOTAS.index(tonica)
    return [NOTAS[(base + passo) % 12] for passo in GRAUS_ESCALA]


def _tonica_atual(estado, campo=None):
    """A tonalidade em uso, vinda do campo harmonico ou do proprio estado."""
    tonica = getattr(campo, 'tonica_campo', None) if campo else None
    if not tonica:
        tonica = getattr(estado, 'nota_selecionada_bloco', 'C')
    return tonica if tonica in NOTAS else 'C'


# ---------------------------------------------------------------------------
# CIRCULO DE QUINTAS COMPACTO
# ---------------------------------------------------------------------------

def desenhar_bloco_circulo(tela, estado, fontes, configs=None, campo=None):
    """
        Como funciona: Desenha as doze tonalidades em circulo, marca a que
        esta em uso e rotula as vizinhas como IV e V.
        Para que serve: Trocar de tonalidade e enxergar para onde ela anda.
        Onde e usada: Workspace, bloco arrastavel do circulo.
    """
    if not hasattr(estado, 'dragger_circulo'):
        return
    if configs is not None:
        TEMA.definir_acento(configs.get_cor_tema())

    d = estado.dragger_circulo
    rect = pygame.Rect(d.x, d.y, d.largura, d.altura)
    y = ds.painel(tela, rect, _t('Quintas'), fontes['pequena'], acento=TEMA.acento)

    tonica = _tonica_atual(estado, campo)
    indice_atual = CICLO.index(tonica) if tonica in CICLO else 0

    altura_legenda = 18 if rect.bottom - y > 96 else 0
    area = pygame.Rect(rect.x, y, rect.width,
                       rect.bottom - y - ds.ESPACO_SM - altura_legenda)
    # Elipse em vez de circulo: o bloco e largo e baixo, e assim as doze
    # tonalidades ficam legiveis em vez de espremidas no meio.
    raio_x = area.width * 0.40
    raio_y = area.height * 0.42
    if min(raio_x, raio_y) < 24:
        estado.rects_circulo = []
        ds.texto_centralizado(tela, _t('Amplie o bloco'), fontes['pequena'], area,
                              TEMA.texto_apagado)
        if estado.drag_ativado:
            d.desenhar_caixa_selecao(tela, margem=5)
        return
    centro = (area.centerx, area.centery)
    tam = max(9, min(14, int(min(raio_x, raio_y) * 0.30)))

    estado.rects_circulo = []
    for i in range(12):
        angulo = -math.pi / 2 + i * math.tau / 12
        cx = centro[0] + math.cos(angulo) * raio_x
        cy = centro[1] + math.sin(angulo) * raio_y
        r = pygame.Rect(0, 0, tam * 2, tam * 2)
        r.center = (int(cx), int(cy))
        estado.rects_circulo.append((r, CICLO[i]))

        passo = (i - indice_atual) % 12
        if passo == 0:
            pygame.draw.circle(tela, ds.rgb(TEMA.acento), r.center, tam)
            cor = TEMA.texto_sobre_cor
        elif passo in (1, 11):
            pygame.draw.circle(tela, ds.rgb(ds.misturar(TEMA.superficie_alt,
                                                        TEMA.ciano, 0.5)),
                               r.center, tam)
            pygame.draw.circle(tela, ds.rgb(TEMA.ciano), r.center, tam, 2)
            cor = TEMA.texto
        else:
            pygame.draw.circle(tela, ds.rgb(TEMA.superficie_alt), r.center, tam)
            pygame.draw.circle(tela, ds.rgb(TEMA.borda), r.center, tam, 1)
            cor = TEMA.texto_apagado
        if tam >= 9:
            ds.texto_em(tela, CICLO[i], fontes['pequena'], r.center, cor,
                        ancora='center', largura_max=tam * 2)

    ds.texto_em(tela, tonica, fontes['titulo'], (centro[0], centro[1] - 8),
                TEMA.acento, ancora='center')
    ds.texto_em(tela, RELATIVAS[indice_atual], fontes['pequena'],
                (centro[0], centro[1] + 12), TEMA.texto_suave, ancora='center')

    # Vizinhas escritas por extenso: e para onde a musica costuma andar
    if altura_legenda:
        quarta = CICLO[(indice_atual - 1) % 12]
        quinta = CICLO[(indice_atual + 1) % 12]
        ds.texto_em(tela, f'IV {quarta}  ·  V {quinta}  ·  {ARMADURAS[indice_atual]}',
                    fontes['pequena'], (rect.centerx, rect.bottom - 18),
                    TEMA.texto_apagado, ancora='midtop',
                    largura_max=rect.width - ds.ESPACO_MD)

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


def desenhar_bloco_historico(tela, estado, fontes, configs=None, campo=None):
    """
        Como funciona: Mostra as ultimas notas captadas, o intervalo entre
        elas e marca em vermelho as que estao fora da tonalidade.
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

    tonica = _tonica_atual(estado, campo)
    da_escala = set(notas_da_tonalidade(tonica))

    pad = ds.ESPACO_MD
    largura_util = rect.width - pad * 2
    visiveis = historico[-8:]
    largura_nota = min(36, largura_util / max(1, len(visiveis)))
    espaco_livre = rect.bottom - y - 30
    altura_nota = min(30, max(18, espaco_livre - 16))

    x = rect.x + pad
    for i, nota in enumerate(visiveis):
        celula = pygame.Rect(int(x), int(y + 2), int(largura_nota) - 3, int(altura_nota))
        recente = i == len(visiveis) - 1
        de_fora = da_escala and nota not in da_escala
        if recente:
            fundo, borda, cor_texto = TEMA.acento, TEMA.acento, TEMA.texto_sobre_cor
        elif de_fora:
            fundo, borda, cor_texto = TEMA.superficie_alt, TEMA.alerta, TEMA.alerta
        else:
            fundo, borda, cor_texto = TEMA.superficie_alt, TEMA.borda, TEMA.texto
        ds.superficie_translucida(tela, celula, fundo, 220, ds.RAIO_SM, borda, 1)
        ds.texto_centralizado(tela, nota, fontes['pequena'], celula, cor_texto)

        if i > 0 and altura_nota + 18 <= espaco_livre:
            anterior = visiveis[i - 1]
            nome = intervalo_entre(anterior, nota)
            seta = ''
            try:
                subiu = (NOTAS.index(nota) - NOTAS.index(anterior)) % 12
                seta = '^' if 0 < subiu <= 6 else 'v'
            except ValueError:
                seta = ''
            ds.texto_em(tela, f'{seta}{nome}', fontes['pequena'],
                        (celula.x - 2, celula.bottom + 2), TEMA.ciano,
                        ancora='midtop')
        x += largura_nota

    if rect.bottom - (y + altura_nota) > 40:
        fora = sum(1 for n in historico if da_escala and n not in da_escala)
        resumo = f"{len(historico)} {_t('notas')}"
        if da_escala:
            resumo += f"  ·  {fora} {_t('fora de')} {tonica}"
        ds.texto_em(tela, resumo, fontes['pequena'],
                    (rect.x + pad, rect.bottom - 20), TEMA.texto_apagado,
                    largura_max=largura_util)

    if estado.drag_ativado:
        d.desenhar_caixa_selecao(tela, margem=5)


# ---------------------------------------------------------------------------
# IDEIAS: GRAVACAO RAPIDA
# ---------------------------------------------------------------------------

PASTA_IDEIAS = 'Ideias'


def ideias_salvas(limite=3):
    """As gravacoes mais recentes da pasta de ideias, da mais nova para a mais velha."""
    try:
        arquivos = glob.glob(os.path.join(PASTA_IDEIAS, '*.wav'))
        arquivos.sort(key=os.path.getmtime, reverse=True)
        return arquivos[:limite]
    except OSError:
        return []


def desenhar_bloco_ideias(tela, estado, fontes, configs=None, motor_audio=None):
    """
        Como funciona: Um botao que comeca e termina a gravacao do que esta
        entrando, e abaixo dele as ultimas gravacoes ja salvas.
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
    altura_btn = min(36, max(26, rect.bottom - y - 40))

    estado.rect_btn_gravar_ideia = pygame.Rect(
        rect.x + pad, y + 2, rect.width - pad * 2, altura_btn)
    ds.botao(tela, estado.rect_btn_gravar_ideia,
             _t('Parar e salvar') if gravando else _t('Gravar ideia'),
             fontes['pequena'], variante='perigo' if gravando else 'primario',
             hover=estado.rect_btn_gravar_ideia.collidepoint(pygame.mouse.get_pos()))

    y_texto = estado.rect_btn_gravar_ideia.bottom + 6
    if gravando:
        inicio = getattr(estado, 'inicio_gravacao_ideia', time.time())
        decorrido = int(time.time() - inicio)
        pulso = 4 + int(2 * abs(math.sin(time.time() * 3)))
        pygame.draw.circle(tela, ds.rgb(TEMA.alerta),
                           (rect.x + pad + 8, y_texto + 8), pulso)
        ds.texto_em(tela, f'{decorrido // 60:02d}:{decorrido % 60:02d}  {_t("gravando")}',
                    fontes['pequena'], (rect.x + pad + 20, y_texto),
                    TEMA.alerta, largura_max=rect.width - pad * 2 - 20)
        if estado.drag_ativado:
            d.desenhar_caixa_selecao(tela, margem=5)
        return

    recentes = getattr(estado, 'ideias_recentes', None)
    if recentes is None:
        recentes = ideias_salvas()
        estado.ideias_recentes = recentes

    if not recentes:
        ds.texto_em(tela, _t('Grava a entrada de audio'), fontes['pequena'],
                    (rect.x + pad, y_texto), TEMA.texto_apagado,
                    largura_max=rect.width - pad * 2)
    else:
        for caminho in recentes:
            if y_texto + 16 > rect.bottom - ds.ESPACO_SM:
                break
            nome = os.path.basename(caminho).replace('ideia_', '').replace('.wav', '')
            pygame.draw.circle(tela, ds.rgb(TEMA.verde), (rect.x + pad + 3, y_texto + 7), 3)
            ds.texto_em(tela, nome, fontes['pequena'], (rect.x + pad + 12, y_texto),
                        TEMA.texto_suave, largura_max=rect.width - pad * 2 - 12)
            y_texto += 17

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
        pasta = PASTA_IDEIAS
        try:
            os.makedirs(pasta, exist_ok=True)
        except OSError:
            pasta = '.'
        nome = time.strftime('ideia_%Y-%m-%d_%H-%M-%S.wav')
        caminho = motor_audio.parar_gravacao(os.path.join(pasta, nome))
        estado.ultima_ideia_salva = caminho or ''
        estado.ideias_recentes = ideias_salvas()
    else:
        motor_audio.iniciar_gravacao()
        estado.inicio_gravacao_ideia = time.time()
    return True


# ---------------------------------------------------------------------------
# REFERENCIA: DRONE SUSTENTADO
# ---------------------------------------------------------------------------

OITAVA_DRONE = 3          # oitava do drone, grave o bastante para nao cansar
_cache_drone = {}


def frequencia_da_nota(nome, oitava=OITAVA_DRONE):
    """Frequencia em Hz pela afinacao igual, com La 4 em 440 Hz."""
    if nome not in NOTAS:
        return 0.0
    semitons = NOTAS.index(nome) - NOTAS.index('A') + (oitava - 4) * 12
    return 440.0 * (2.0 ** (semitons / 12.0))


def _som_drone(nome):
    """Sintetiza um ciclo inteiro da nota, para o loop nao dar estalo."""
    if nome in _cache_drone:
        return _cache_drone[nome]
    try:
        import numpy as np
    except ImportError:
        return None
    info = pygame.mixer.get_init()
    if not info:
        return None
    taxa, _tamanho, canais = info
    freq = frequencia_da_nota(nome)
    if freq <= 0:
        return None

    # Comprimento arredondado para um numero inteiro de ciclos
    ciclos = max(1, int(round(freq)))
    n = max(64, int(round(taxa * ciclos / freq)))
    t = np.arange(n) / taxa
    onda = (np.sin(2 * np.pi * freq * t)
            + 0.35 * np.sin(4 * np.pi * freq * t)
            + 0.15 * np.sin(6 * np.pi * freq * t))
    onda = onda / max(1e-6, float(np.max(np.abs(onda)))) * 9000
    dados = onda.astype(np.int16)
    if canais > 1:
        dados = np.repeat(dados[:, None], canais, axis=1)
    try:
        som = pygame.mixer.Sound(np.ascontiguousarray(dados))
    except Exception:
        return None
    _cache_drone[nome] = som
    return som


def alternar_drone(estado, nota=None):
    """
        Como funciona: Liga ou desliga o drone; trocar de nota com ele ligado
        troca o som na hora.
        Para que serve: Acao dos botoes do bloco de referencia.
        Onde e usada: Chamada pelo controlador de eventos.
    """
    canal = getattr(estado, 'canal_drone', None)
    if canal is not None:
        try:
            canal.stop()
        except Exception:
            pass
    if nota is not None and nota != getattr(estado, 'drone_nota', None):
        estado.drone_nota = nota
        estado.drone_ativo = True
    else:
        estado.drone_ativo = not getattr(estado, 'drone_ativo', False)

    if not estado.drone_ativo:
        estado.canal_drone = None
        return True
    som = _som_drone(getattr(estado, 'drone_nota', 'C'))
    if som is None:
        estado.drone_ativo = False
        estado.canal_drone = None
        return False
    try:
        estado.canal_drone = som.play(loops=-1, fade_ms=120)
    except Exception:
        estado.drone_ativo = False
        estado.canal_drone = None
        return False
    return True


def desenhar_bloco_drone(tela, estado, fontes, configs=None, campo=None):
    """
        Como funciona: Escolhe a nota de referencia e sustenta o som dela em
        loop enquanto estiver ligado.
        Para que serve: Afinar de ouvido e improvisar por cima de um centro
        tonal, que e como se treina modo e escala de verdade.
        Onde e usada: Workspace, bloco arrastavel de referencia.
    """
    if not hasattr(estado, 'dragger_drone'):
        return
    if configs is not None:
        TEMA.definir_acento(configs.get_cor_tema())

    d = estado.dragger_drone
    rect = pygame.Rect(d.x, d.y, d.largura, d.altura)
    y = ds.painel(tela, rect, _t('Referencia'), fontes['pequena'], acento=TEMA.acento)

    if not getattr(estado, 'drone_nota', None):
        estado.drone_nota = _tonica_atual(estado, campo)
    nota = estado.drone_nota
    ligado = bool(getattr(estado, 'drone_ativo', False))
    pad = ds.ESPACO_MD
    largura_util = rect.width - pad * 2

    # Doze notas em duas fileiras
    estado.rects_drone = []
    colunas = 6
    largura_chip = max(18, (largura_util - (colunas - 1) * 4) // colunas)
    altura_chip = 22
    if rect.bottom - y < altura_chip * 2 + 50:
        altura_chip = max(16, (rect.bottom - y - 46) // 2)
    for i, nome in enumerate(NOTAS):
        cx = rect.x + pad + (i % colunas) * (largura_chip + 4)
        cy = y + 2 + (i // colunas) * (altura_chip + 4)
        r = pygame.Rect(cx, cy, largura_chip, altura_chip)
        if r.bottom > rect.bottom - 30:
            break
        estado.rects_drone.append((r, nome))
        ds.chip(tela, r, nome, fontes['pequena'], ativo=(nome == nota))

    y_botao = y + 2 + (altura_chip + 4) * 2 + 4
    altura_btn = min(32, max(22, rect.bottom - y_botao - ds.ESPACO_SM))
    estado.rect_btn_drone = pygame.Rect(rect.x + pad, y_botao, largura_util, altura_btn)
    rotulo = f"{_t('Parar')} {nota}" if ligado else f"{_t('Soar')} {nota}"
    ds.botao(tela, estado.rect_btn_drone, rotulo, fontes['pequena'],
             variante='perigo' if ligado else 'primario',
             hover=estado.rect_btn_drone.collidepoint(pygame.mouse.get_pos()))

    if ligado and estado.rect_btn_drone.bottom + 16 <= rect.bottom:
        ds.texto_em(tela, f'{frequencia_da_nota(nota):.1f} Hz', fontes['pequena'],
                    (rect.centerx, estado.rect_btn_drone.bottom + 3),
                    TEMA.texto_apagado, ancora='midtop')

    if estado.drag_ativado:
        d.desenhar_caixa_selecao(tela, margem=5)


# ---------------------------------------------------------------------------
# PROGRESSOES RAPIDAS
# ---------------------------------------------------------------------------

def acordes_da_progressao(tonica, graus):
    """(cifra, nota, tipo) de cada grau da progressao na tonalidade dada."""
    notas = notas_da_tonalidade(tonica)
    if not notas:
        return []
    saida = []
    for grau in graus:
        grau = grau % len(CAMPO_MAIOR)
        algarismo, tipo = CAMPO_MAIOR[grau]
        nota = notas[grau]
        sufixo = {'maior': '', 'menor': 'm', 'dim': 'dim'}[tipo]
        saida.append((f'{nota}{sufixo}', nota, tipo, algarismo))
    return saida


def aplicar_progressao(estado, tonica, graus):
    """
        Como funciona: Coloca todos os acordes da progressao no braco, cada um
        com a sua cor, usando a mesma lista que o painel de acordes alimenta.
        Para que serve: Ver o giro inteiro desenhado de uma vez.
        Onde e usada: Chamada pelo controlador de eventos.
    """
    try:
        from ui.blocks.painel_acordes import notas_do_acorde
    except ImportError:
        return False
    lista = []
    for i, (cifra, nota, tipo, _grau) in enumerate(acordes_da_progressao(tonica, graus)):
        lista.append({'rotulo': cifra, 'notas': notas_do_acorde(nota, tipo),
                      'janela': None, 'cor': CORES_PROGRESSAO[i % len(CORES_PROGRESSAO)],
                      'fixado': True})
    estado.acordes_fixados = list(lista)
    estado.acordes_no_braco = list(lista)
    return True


def desenhar_bloco_progressoes(tela, estado, fontes, configs=None, campo=None):
    """
        Como funciona: Lista quatro giros classicos ja cifrados na tonalidade
        atual; clicar num deles joga os acordes no braco.
        Para que serve: Sair do estudo solto e cair em algo que se toca.
        Onde e usada: Workspace, bloco arrastavel de progressoes.
    """
    if not hasattr(estado, 'dragger_progressoes'):
        return
    if configs is not None:
        TEMA.definir_acento(configs.get_cor_tema())

    d = estado.dragger_progressoes
    rect = pygame.Rect(d.x, d.y, d.largura, d.altura)
    tonica = _tonica_atual(estado, campo)
    y = ds.painel(tela, rect, f"{_t('Progressoes')} · {tonica}", fontes['pequena'],
                  acento=TEMA.acento)

    pad = ds.ESPACO_MD
    largura_util = rect.width - pad * 2
    espaco = rect.bottom - y - ds.ESPACO_SM
    altura_linha = max(28, min(42, espaco // max(1, len(PROGRESSOES_RAPIDAS))))
    ativa = getattr(estado, 'progressao_ativa', -1)

    estado.rects_progressoes = []
    linha_y = y + 2
    for i, prog in enumerate(PROGRESSOES_RAPIDAS):
        if linha_y + altura_linha > rect.bottom - 2:
            break
        r = pygame.Rect(rect.x + pad, linha_y, largura_util, altura_linha - 4)
        estado.rects_progressoes.append((r, i))
        selecionada = i == ativa
        ds.superficie_translucida(
            tela, r, ds.misturar(TEMA.superficie_alt, TEMA.acento, 0.28)
            if selecionada else TEMA.superficie_alt, 220, ds.RAIO_SM,
            TEMA.acento if selecionada else TEMA.borda, 1)

        ds.texto_em(tela, _t(prog['nome']), fontes['pequena'],
                    (r.x + ds.ESPACO_SM, r.y + 4),
                    TEMA.acento if selecionada else TEMA.texto_suave,
                    largura_max=r.width // 2)

        cifras = acordes_da_progressao(tonica, prog['graus'])
        x = r.right - ds.ESPACO_SM
        mostra_grau = altura_linha >= 34
        for j, (cifra, _n, _tp, grau) in enumerate(reversed(cifras)):
            indice = len(cifras) - 1 - j
            cor = CORES_PROGRESSAO[indice % len(CORES_PROGRESSAO)]
            largura_texto = max(fontes['pequena'].size(cifra)[0],
                                fontes['pequena'].size(grau)[0])
            if x - largura_texto < r.x + r.width // 2:
                break
            ds.texto_em(tela, cifra, fontes['pequena'], (x, r.y + 3),
                        cor if selecionada else TEMA.texto, ancora='topright')
            if mostra_grau:
                ds.texto_em(tela, grau, fontes['pequena'], (x, r.y + 18),
                            TEMA.texto_apagado, ancora='topright')
            x -= largura_texto + 10
        linha_y += altura_linha

    if estado.drag_ativado:
        d.desenhar_caixa_selecao(tela, margem=5)
