# -*- coding: utf-8 -*-
"""
Gaveteiro lateral do workspace.

A tela principal fica com o braco e a barra de abas. Todo o resto mora numa
coluna estreita na borda esquerda, uma gaveta por bloco. Passando o mouse a
coluna se abre e mostra o nome de cada gaveta; clicando, o bloco sai para a
tela ou volta para dentro; arrastando a gaveta, o bloco sai ja preso ao mouse
e pode ser largado onde se quiser. Largar um bloco em cima da coluna guarda
ele de volta.

Tudo comeca guardado, entao o estudo abre limpo: so o instrumento e as abas.

As duas regras dos blocos valem aqui tambem: o desenho e recortado na coluna,
e os retangulos das gavetas sao guardados no desenho e so consultados no
clique.
"""
import pygame

from config.design_system import TEMA, ds
from core.i18n import _t

# Largura da coluna fechada e aberta, em pixels
LARGURA_FECHADO = 40
LARGURA_ABERTO = 216

# Quanto a abertura anda por quadro (0 a 1)
PASSO_ABERTURA = 0.18

ALTURA_GAVETA = 34
ALTURA_GAVETA_MIN = 22
ESPACO_GAVETA = 4
MARGEM_ARRASTO = 6      # pixels de mouse antes de virar arrasto de verdade

# Ordem das gavetas na coluna: bloco -> nome que aparece
GAVETAS = (
    ('dragger_circulo', 'Quintas'),
    ('dragger_graus', 'Graus'),
    ('dragger_acordes', 'Campo harmonico'),
    ('dragger_progressoes', 'Progressoes'),
    ('dragger_historico', 'Notas tocadas'),
    ('dragger_nota_atual', 'Nota atual'),
    ('dragger_drone', 'Referencia'),
    ('dragger_cordas', 'Cordas soltas'),
    ('dragger_capo', 'Capotraste'),
    ('dragger_metronomo', 'Metronomo'),
    ('dragger_ideias', 'Ideias'),
    ('dragger_sessao', 'Sessao'),
    ('dragger_cores', 'Cores'),
)

NOMES = tuple(nome for nome, _rotulo in GAVETAS)
ROTULOS = dict(GAVETAS)


# ---------------------------------------------------------------------------
# ESTADO
# ---------------------------------------------------------------------------

def preparar(estado):
    """
        Como funciona: Garante os campos do gaveteiro no estado global, com
        todos os blocos guardados na primeira vez.
        Para que serve: O programa abrir com a tela limpa e o resto na coluna.
        Onde e usada: EstadoGlobal.__init__ e ao carregar um perfil antigo.
    """
    if not hasattr(estado, 'blocos_guardados') or estado.blocos_guardados is None:
        estado.blocos_guardados = set(NOMES)
    estado.gaveteiro_abertura = getattr(estado, 'gaveteiro_abertura', 0.0)
    estado.rects_gavetas = getattr(estado, 'rects_gavetas', [])
    estado.rect_gaveteiro = getattr(estado, 'rect_gaveteiro',
                                    pygame.Rect(0, 0, LARGURA_FECHADO, 0))
    estado.gaveta_pressionada = getattr(estado, 'gaveta_pressionada', None)
    # Longe da coluna: sem isso ela abriria sozinha no primeiro quadro
    estado.mouse_workspace = getattr(estado, 'mouse_workspace', (-9999, -9999))
    return estado.blocos_guardados


def visivel(estado, nome):
    """Verdadeiro quando o bloco esta na tela, e nao guardado na coluna."""
    if nome not in NOMES:
        return True
    guardados = getattr(estado, 'blocos_guardados', None)
    if guardados is None:
        return True
    return nome not in guardados


def largura_atual(estado):
    """Largura da coluna neste quadro, entre fechada e aberta."""
    abertura = max(0.0, min(1.0, getattr(estado, 'gaveteiro_abertura', 0.0)))
    return int(LARGURA_FECHADO + (LARGURA_ABERTO - LARGURA_FECHADO) * abertura)


def guardar(estado, nome):
    """
        Como funciona: Devolve o bloco para a coluna, sem mexer na posicao
        dele, para sair de novo no mesmo lugar.
        Para que serve: Limpar a tela sem perder o arranjo.
        Onde e usada: Clique na gaveta e bloco largado sobre a coluna.
    """
    preparar(estado)
    if nome in NOMES:
        estado.blocos_guardados.add(nome)
        bloco = getattr(estado, nome, None)
        if bloco is not None:
            bloco.arrastando = False
            bloco.redimensionando = False
    return True


def _ocupado(estado, ignorar):
    """Retangulos que ja estao na tela: os fixos e os blocos que sairam."""
    from config.layout_padrao import MARGEM_ESQUERDA
    rects = []
    fixos = ('dragger_guitarra', 'dragger_controles_topo',
             'dragger_painel_inferior')
    for nome in fixos + NOMES:
        if nome == ignorar or (nome in NOMES and not visivel(estado, nome)):
            continue
        bloco = getattr(estado, nome, None)
        if bloco is None:
            continue
        rects.append(pygame.Rect(bloco.x, bloco.y, bloco.largura, bloco.altura))
    return rects


def _sobreposicao(rect, ocupados):
    """Area total que o retangulo cobre do que ja esta na tela."""
    total = 0
    for outro in ocupados:
        corte = rect.clip(outro)
        total += corte.width * corte.height
    return total


def _lugar_livre(estado, nome, bloco):
    """
        Como funciona: Fica com o lugar de sempre do bloco se ele estiver
        livre; se estiver ocupado, varre a area util de cima para baixo e
        devolve o primeiro canto onde o bloco nao encosta em nada.
        Para que serve: Clicar na gaveta poe o bloco num lugar que da para ver,
        em vez de empilhar tudo por cima do braco.
        Onde e usada: soltar(), quando nao veio posicao do arrasto.
    """
    from config.layout_padrao import MARGEM_ESQUERDA, MARGEM_DIREITA
    from config.ui_metrics import ALTURA_TOPBAR
    largura = int(getattr(estado, 'LARGURA_TELA', 1920))
    altura = int(getattr(estado, 'ALTURA_TELA', 1080)) - ALTURA_TOPBAR
    barra = getattr(estado, 'dragger_painel_inferior', None)
    limite_y = getattr(barra, 'y', altura) - ESPACO_GAVETA

    ocupados = _ocupado(estado, nome)
    atual = pygame.Rect(bloco.x, bloco.y, bloco.largura, bloco.altura)
    if (atual.x >= LARGURA_FECHADO and atual.right <= largura - MARGEM_DIREITA
            and atual.bottom <= limite_y
            and not any(atual.colliderect(r) for r in ocupados)):
        return atual.x, atual.y

    # Com a tela cheia pode nao haver canto livre; entao fica o que menos
    # cobre o que ja esta na tela
    passo = 24
    melhor, menor_sobra = (atual.x, atual.y), _sobreposicao(atual, ocupados)
    # Primeira volta longe da coluna aberta, para o bloco nao nascer escondido
    # atras dela; a segunda aceita a faixa que so a coluna fechada ocupa
    for inicio in (LARGURA_ABERTO + ds.ESPACO_SM, MARGEM_ESQUERDA):
        direita = largura - MARGEM_DIREITA - bloco.largura
        if inicio > direita:
            continue
        for y in range(ds.ESPACO_SM,
                       max(ds.ESPACO_SM + 1, limite_y - bloco.altura), passo):
            for x in range(inicio, max(inicio + 1, direita), passo):
                tentativa = pygame.Rect(x, y, bloco.largura, bloco.altura)
                sobra = _sobreposicao(tentativa, ocupados)
                if sobra == 0:
                    return x, y
                if sobra < menor_sobra:
                    melhor, menor_sobra = (x, y), sobra
    return melhor


def soltar(estado, nome, pos=None):
    """
        Como funciona: Tira o bloco da coluna. Sem posicao, ele volta para
        onde estava; com posicao, aparece centrado ali, longe da coluna.
        Para que serve: Por o bloco na tela por clique ou por arrasto.
        Onde e usada: Clique e arrasto da gaveta.
    """
    preparar(estado)
    if nome not in NOMES:
        return False
    estado.blocos_guardados.discard(nome)
    bloco = getattr(estado, nome, None)
    if bloco is None:
        return False
    if pos is not None:
        bloco.x = int(pos[0] - bloco.largura // 2)
        bloco.y = int(pos[1] - 12)
    else:
        bloco.x, bloco.y = _lugar_livre(estado, nome, bloco)
    limite = LARGURA_FECHADO + ds.ESPACO_SM
    bloco.x = max(limite, int(bloco.x))
    bloco.y = max(0, int(bloco.y))
    if hasattr(bloco, 'rect_caixa'):
        bloco.rect_caixa.update(bloco.x, bloco.y, bloco.largura, bloco.altura)
    return True


def alternar(estado, nome, pos=None):
    """Guarda o bloco que esta na tela, ou solta o que esta guardado."""
    if visivel(estado, nome):
        return guardar(estado, nome)
    return soltar(estado, nome, pos)


# ---------------------------------------------------------------------------
# DESENHO
# ---------------------------------------------------------------------------

def atualizar(estado, altura_viewport):
    """
        Como funciona: Aproxima a abertura da coluna do alvo, que e aberta
        enquanto o mouse esta em cima dela ou arrastando uma gaveta.
        Para que serve: A coluna abrir e fechar sozinha, sem clique.
        Onde e usada: Inicio do desenho do gaveteiro, a cada quadro.
    """
    preparar(estado)
    rect = pygame.Rect(0, 0, largura_atual(estado), max(0, altura_viewport))
    x_mouse, y_mouse = getattr(estado, 'mouse_workspace', (0, 0))
    perto = (0 <= y_mouse <= altura_viewport
             and x_mouse <= max(rect.width, LARGURA_FECHADO) + 12)
    alvo = 1.0 if (perto or estado.gaveta_pressionada) else 0.0
    atual = getattr(estado, 'gaveteiro_abertura', 0.0)
    estado.gaveteiro_abertura = atual + (alvo - atual) * PASSO_ABERTURA
    if abs(estado.gaveteiro_abertura - alvo) < 0.01:
        estado.gaveteiro_abertura = alvo
    return estado.gaveteiro_abertura


def desenhar(tela, estado, fontes, configs=None):
    """
        Como funciona: Desenha a coluna e uma gaveta por bloco, marcando as
        que estao na tela. Guarda os retangulos para o clique e recorta o
        desenho na propria coluna.
        Para que serve: Ponto unico para tirar e guardar bloco.
        Onde e usada: ui/renderizador_ui.desenhar_workspace, por cima de tudo.
    """
    preparar(estado)
    if configs is not None:
        TEMA.definir_acento(configs.get_cor_tema())

    largura_tela, altura_tela = tela.get_size()
    atualizar(estado, altura_tela)
    estado.rects_gavetas = []

    fonte = fontes['pequena']
    alt_texto = fonte.get_height()
    largura = largura_atual(estado)
    aberto = largura > LARGURA_FECHADO + 20

    margem = ds.ESPACO_SM
    topo = margem
    altura_util = max(0, altura_tela - margem * 2)
    rect = pygame.Rect(0, topo, largura, altura_util)
    estado.rect_gaveteiro = pygame.Rect(0, 0, max(largura, LARGURA_FECHADO),
                                        altura_tela)
    if rect.height < 60 or rect.width < 16:
        return

    ds.sombra(tela, rect, ds.RAIO_LG)
    ds.superficie_translucida(tela, rect, TEMA.superficie, 242, ds.RAIO_LG,
                              TEMA.borda, 1)
    faixa = pygame.Rect(rect.x, rect.y, 3, rect.height)
    ds.superficie_translucida(tela, faixa, TEMA.acento, 210, 0)

    recorte_anterior = tela.get_clip()
    tela.set_clip(rect.clip(tela.get_rect()))
    try:
        y = rect.y + ds.ESPACO_SM
        if aberto:
            ds.texto_em(tela, _t('Blocos').upper(), fonte,
                        (rect.x + ds.ESPACO_MD, y), TEMA.acento,
                        largura_max=rect.width - ds.ESPACO_LG)
            y += alt_texto + ds.ESPACO_SM
        else:
            for i in range(3):
                pygame.draw.circle(tela, ds.rgb(TEMA.texto_apagado),
                                   (rect.centerx, y + 4 + i * 6), 2)
            y += 24

        espaco = rect.bottom - y - ds.ESPACO_SM
        altura_gaveta = min(ALTURA_GAVETA,
                            (espaco - ESPACO_GAVETA * (len(GAVETAS) - 1))
                            / max(1, len(GAVETAS)))
        altura_gaveta = int(max(ALTURA_GAVETA_MIN, altura_gaveta))

        for nome, rotulo in GAVETAS:
            linha = pygame.Rect(rect.x + 5, int(y), rect.width - 10, altura_gaveta)
            if linha.bottom > rect.bottom - 2:
                break
            estado.rects_gavetas.append((linha, nome))
            _desenhar_gaveta(tela, estado, fonte, linha, nome, rotulo, aberto)
            y += altura_gaveta + ESPACO_GAVETA
    finally:
        tela.set_clip(recorte_anterior)


def _desenhar_gaveta(tela, estado, fonte, rect, nome, rotulo, aberto):
    """Uma gaveta: marca do bloco, nome quando aberto e puxador."""
    na_tela = visivel(estado, nome)
    x_mouse, y_mouse = getattr(estado, 'mouse_workspace', (0, 0))
    hover = rect.collidepoint(x_mouse, y_mouse)

    if na_tela:
        fundo = ds.misturar(TEMA.superficie_alt, TEMA.acento, 0.32)
        borda = TEMA.acento
        cor_texto = TEMA.texto
    else:
        fundo = ds.misturar(TEMA.superficie_alt, TEMA.superficie, 0.4)
        borda = TEMA.borda
        cor_texto = TEMA.texto_suave
    if hover:
        fundo = ds.clarear(fundo, 0.10)
    ds.superficie_translucida(tela, rect, fundo, 235, ds.RAIO_SM, borda, 1)

    marca = pygame.Rect(rect.x + 4, rect.y + 4, rect.height - 8, rect.height - 8)
    inicial = _t(rotulo)[:1].upper()
    if na_tela:
        pygame.draw.rect(tela, ds.rgb(TEMA.acento), marca,
                         border_radius=ds.RAIO_SM)
        ds.texto_em(tela, inicial, fonte, marca.center, TEMA.texto_sobre_cor,
                    ancora='center', largura_max=marca.width)
    else:
        pygame.draw.rect(tela, ds.rgb(TEMA.borda), marca, width=1,
                         border_radius=ds.RAIO_SM)
        ds.texto_em(tela, inicial, fonte, marca.center, TEMA.texto_apagado,
                    ancora='center', largura_max=marca.width)

    if aberto:
        largura_texto = rect.right - marca.right - ds.ESPACO_MD - 10
        if largura_texto > 20:
            ds.texto_em(tela, _t(rotulo), fonte,
                        (marca.right + ds.ESPACO_SM, rect.centery), cor_texto,
                        ancora='midleft', largura_max=largura_texto)
        # Puxador: duas linhas curtas na borda direita
        for i in range(2):
            x = rect.right - 9 + i * 3
            pygame.draw.line(tela, ds.rgb(TEMA.texto_apagado),
                             (x, rect.centery - 5), (x, rect.centery + 5), 1)


# ---------------------------------------------------------------------------
# EVENTOS
# ---------------------------------------------------------------------------

def _tela_cheia_aberta(estado):
    """Verdadeiro quando um estudo, jogo ou editor tomou a tela inteira."""
    for atributo in ('tela_estudo_ativa', 'tela_jogo_ativa',
                     'tela_criacao_tab_ativa', 'tab_tela_cheia_ativa'):
        if getattr(estado, atributo, False):
            return True
    perfil = getattr(estado, 'gerenciador_perfil', None)
    return bool(getattr(perfil, 'ativo', False))


def _gaveta_em(estado, pos):
    for rect, nome in getattr(estado, 'rects_gavetas', []):
        if rect.collidepoint(pos):
            return nome
    return None


def sobre_a_coluna(estado, rect_bloco):
    """Verdadeiro quando o bloco esta por cima da coluna, na hora de largar."""
    coluna = getattr(estado, 'rect_gaveteiro', None)
    if coluna is None:
        return False
    zona = pygame.Rect(0, coluna.y, max(coluna.width, LARGURA_FECHADO) + 16,
                       coluna.height)
    return zona.colliderect(rect_bloco) and rect_bloco.x < zona.right


def tratar_evento(estado, evento):
    """
        Como funciona: Cuida do mouse do gaveteiro. Ao apertar numa gaveta, o
        bloco guardado ja sai para a tela; mexendo o mouse, ele passa a ser
        arrastado; soltando, se ele ficou por cima da coluna, volta para
        dentro. Apertar a gaveta de um bloco que ja esta na tela guarda ele.
        Para que serve: Um lugar so para tirar, mover e guardar bloco.
        Onde e usada: core/controlador_eventos.processar, antes dos draggers.

        Devolve True quando consumiu o evento.
    """
    preparar(estado)
    if _tela_cheia_aberta(estado):
        # Com estudo, jogo ou editor abertos o workspace nem e desenhado:
        # os retangulos guardados sao de outro momento e nao valem mais
        estado.gaveta_pressionada = None
        return False

    if evento.type == pygame.MOUSEMOTION:
        estado.mouse_workspace = evento.pos
        pressionada = estado.gaveta_pressionada
        if not pressionada:
            return False
        nome, inicio = pressionada
        bloco = getattr(estado, nome, None)
        if bloco is None:
            return False
        distancia = abs(evento.pos[0] - inicio[0]) + abs(evento.pos[1] - inicio[1])
        if distancia < MARGEM_ARRASTO:
            return True
        # Passou a ser arrasto: o bloco gruda no mouse
        if not bloco.arrastando:
            bloco.x = int(evento.pos[0] - bloco.largura // 2)
            bloco.y = int(evento.pos[1] - 12)
            bloco.mouse_inicio_x = evento.pos[0] - bloco.x
            bloco.mouse_inicio_y = evento.pos[1] - bloco.y
            bloco.arrastando = True
        else:
            bloco.x = int(evento.pos[0] - bloco.mouse_inicio_x)
            bloco.y = int(evento.pos[1] - bloco.mouse_inicio_y)
        if hasattr(bloco, 'rect_caixa'):
            bloco.rect_caixa.update(bloco.x, bloco.y, bloco.largura, bloco.altura)
        return True

    if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
        estado.mouse_workspace = evento.pos
        nome = _gaveta_em(estado, evento.pos)
        if nome is None:
            # Clique no corpo da coluna nao pode atravessar para o bloco de tras
            coluna = getattr(estado, 'rect_gaveteiro', None)
            if coluna is not None and pygame.Rect(
                    0, coluna.y, largura_atual(estado), coluna.height
            ).collidepoint(evento.pos):
                return True
            return False
        if visivel(estado, nome):
            guardar(estado, nome)
            return True
        soltar(estado, nome)
        estado.gaveta_pressionada = (nome, evento.pos)
        return True

    if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
        pressionada = estado.gaveta_pressionada
        estado.gaveta_pressionada = None
        guardou = False
        for nome in NOMES:
            if not visivel(estado, nome):
                continue
            bloco = getattr(estado, nome, None)
            if bloco is None or not bloco.arrastando:
                continue
            rect_bloco = pygame.Rect(bloco.x, bloco.y, bloco.largura, bloco.altura)
            if sobre_a_coluna(estado, rect_bloco):
                guardar(estado, nome)
                guardou = True
        if pressionada:
            nome, _inicio = pressionada
            bloco = getattr(estado, nome, None)
            if bloco is not None:
                bloco.arrastando = False
            return True
        return guardou

    return False


# Nomes publicos usados pelo resto do programa
desenhar_gaveteiro = desenhar
guardar_bloco = guardar
soltar_bloco = soltar
alternar_bloco = alternar
bloco_visivel = visivel
tratar_evento_gaveteiro = tratar_evento
