# -*- coding: utf-8 -*-
"""
Barra superior fixa do EIGUIT Studio.

Da esquerda para a direita:
  marca | menus (Arquivo, Exibir, Perfil, Configuracoes, Ajuda)
  | contexto da tela atual (com Voltar quando ha uma tela aberta)
  | status da IA | medidor da entrada de audio | conta
  | tela cheia | tema | modo de edicao

Tudo que e clicavel e registrado em estado.botoes_cabecalho como
(rect, id_da_acao); o MenuSuperior trata o clique. A barra nunca passa pela
camera do workspace, entao o mouse usado aqui e sempre o real.
"""
import time

import pygame

from config.design_system import TEMA, ds
from config.ui_metrics import ALTURA_TOPBAR
from core.i18n import _t
from ui.components.notificacoes import desenhar_notificacoes

TAM_BTN = 28
ATRASO_DICA = 0.45

_fontes_extra = {}


def _fonte(tamanho, negrito=True, nome='Arial'):
    chave = (nome, tamanho, negrito)
    if chave not in _fontes_extra:
        _fontes_extra[chave] = pygame.font.SysFont(nome, tamanho, bold=negrito)
    return _fontes_extra[chave]


def _mouse_real(estado):
    pos = getattr(estado, 'pos_mouse_real', None)
    return pos if pos is not None else pygame.mouse.get_pos()


def _registrar(estado, rect, acao, dica=''):
    estado.botoes_cabecalho.append((pygame.Rect(rect), acao))
    if dica:
        estado._dicas_cabecalho.append((pygame.Rect(rect), dica))


# ---------------------------------------------------------------------------
# Pecas da barra
# ---------------------------------------------------------------------------

def _desenhar_marca(tela, fontes, largura_tela):
    """Logotipo + nome. Devolve onde a marca termina."""
    tam = 26
    rect_logo = pygame.Rect(ds.ESPACO_MD, (ALTURA_TOPBAR - tam) // 2, tam, tam)
    ds.gradiente_vertical(tela, rect_logo, TEMA.primaria_clara, TEMA.primaria, ds.RAIO_MD)
    # Tres "cordas" discretas atras da letra
    for i in range(3):
        y = rect_logo.y + 8 + i * 5
        pygame.draw.line(tela, ds.rgb(ds.misturar(TEMA.primaria_clara, (255, 255, 255), 0.35)),
                         (rect_logo.x + 4, y), (rect_logo.right - 5, y), 1)
    ds.texto_centralizado(tela, 'E', _fonte(16), rect_logo, TEMA.texto_sobre_cor)
    fim = rect_logo.right
    if largura_tela >= 1100:
        r1 = ds.texto_em(tela, 'EIGUIT', _fonte(15), (rect_logo.right + 9, ALTURA_TOPBAR // 2),
                         TEMA.texto, ancora='midleft')
        r2 = ds.texto_em(tela, 'Studio', _fonte(15, False), (r1.right + 5, ALTURA_TOPBAR // 2),
                         TEMA.texto_suave, ancora='midleft')
        fim = r2.right
    # Divisor vertical entre a marca e os menus
    x = fim + ds.ESPACO_MD
    pygame.draw.line(tela, ds.rgb(TEMA.borda), (x, 10), (x, ALTURA_TOPBAR - 10), 1)
    return x + 2


def _fundo_botao(tela, rect, hover, ativo=False):
    if ativo:
        pygame.draw.rect(tela, ds.rgb(TEMA.acento), rect, border_radius=ds.RAIO_MD)
        return TEMA.texto_sobre_cor
    if hover:
        ds.superficie_translucida(tela, rect, ds.misturar(TEMA.superficie_alt, TEMA.acento, 0.22),
                                  240, ds.RAIO_MD, ds.misturar(TEMA.borda, TEMA.acento, 0.6), 1)
        return TEMA.texto
    return TEMA.texto_suave


def _icone_tela_cheia(tela, rect, cor, cheia):
    """Quatro cantos: para fora = entrar em tela cheia, para dentro = sair."""
    cx, cy = rect.center
    d, t = 7, 4
    cor = ds.rgb(cor)
    for sx in (-1, 1):
        for sy in (-1, 1):
            canto = (cx + sx * d, cy + sy * d)
            if cheia:   # setas para dentro
                canto = (cx + sx * (d - t), cy + sy * (d - t))
                pygame.draw.line(tela, cor, canto, (canto[0] + sx * t, canto[1]), 2)
                pygame.draw.line(tela, cor, canto, (canto[0], canto[1] + sy * t), 2)
            else:
                pygame.draw.line(tela, cor, canto, (canto[0] - sx * t, canto[1]), 2)
                pygame.draw.line(tela, cor, canto, (canto[0], canto[1] - sy * t), 2)


def _icone_edicao(tela, rect, cor, ativo):
    cx, cy = rect.center
    cor = ds.rgb(cor)
    if ativo:
        # Cruz de movimento
        pygame.draw.line(tela, cor, (cx - 7, cy), (cx + 7, cy), 2)
        pygame.draw.line(tela, cor, (cx, cy - 7), (cx, cy + 7), 2)
        for dx, dy in ((-7, 0), (7, 0), (0, -7), (0, 7)):
            px, py = cx + dx, cy + dy
            if dx:
                pts = [(px, py), (px - (3 if dx > 0 else -3), py - 3), (px - (3 if dx > 0 else -3), py + 3)]
            else:
                pts = [(px, py), (px - 3, py - (3 if dy > 0 else -3)), (px + 3, py - (3 if dy > 0 else -3))]
            pygame.draw.polygon(tela, cor, pts)
    else:
        # Cadeado (layout travado)
        corpo = pygame.Rect(cx - 6, cy - 1, 12, 9)
        pygame.draw.rect(tela, cor, corpo, border_radius=2)
        pygame.draw.arc(tela, cor, pygame.Rect(cx - 4, cy - 8, 8, 12), 0, 3.1416, 2)


def _desenhar_botoes_sistema(tela, estado, x_direita, mouse):
    """Tela cheia, tema e modo de edicao. Devolve o novo x a esquerda."""
    import core.acoes_cabecalho as acoes
    y = (ALTURA_TOPBAR - TAM_BTN) // 2

    # Modo de edicao (o antigo "alfinete")
    rect = pygame.Rect(x_direita - TAM_BTN, y, TAM_BTN, TAM_BTN)
    ativo = bool(getattr(estado, 'drag_ativado', False))
    cor = _fundo_botao(tela, rect, rect.collidepoint(mouse), ativo)
    _icone_edicao(tela, rect, cor, ativo)
    estado.rect_btn_pin = rect
    _registrar(estado, rect, 'modo_edicao',
               (_t('Travar layout') if ativo else _t('Editar layout (arrastar blocos)')) + '  ·  F2')
    x_direita = rect.x - 6

    # Tema claro/escuro
    rect = pygame.Rect(x_direita - TAM_BTN, y, TAM_BTN, TAM_BTN)
    _fundo_botao(tela, rect, rect.collidepoint(mouse))
    proximo = 'claro' if TEMA.escuro else 'escuro'
    ds.icone_tema(tela, rect.center, proximo,
                  TEMA.aviso if proximo == 'claro' else TEMA.texto_suave, 7)
    estado.rect_btn_tema = rect
    _registrar(estado, rect, 'tema_escuro',
               (_t('Tema claro') if TEMA.escuro else _t('Tema escuro')) + '  ·  F3')
    x_direita = rect.x - 6

    # Tela cheia
    rect = pygame.Rect(x_direita - TAM_BTN, y, TAM_BTN, TAM_BTN)
    cor = _fundo_botao(tela, rect, rect.collidepoint(mouse))
    cheia = acoes.em_tela_cheia(estado)
    _icone_tela_cheia(tela, rect, cor, cheia)
    _registrar(estado, rect, 'tela_cheia',
               (_t('Sair da tela cheia') if cheia else _t('Tela cheia')) + '  ·  F11')
    x_direita = rect.x - ds.ESPACO_MD

    pygame.draw.line(tela, ds.rgb(TEMA.borda), (x_direita, 10), (x_direita, ALTURA_TOPBAR - 10), 1)
    return x_direita - ds.ESPACO_MD


def _nome_conta(estado):
    import core.acoes_cabecalho as acoes
    perfil = acoes.nome_perfil_atual(estado)
    email = getattr(estado, 'email_usuario', '') or ''
    usuario = email.split('@')[0] if email else _t('Convidado')
    return usuario, perfil


def _desenhar_conta(tela, estado, x_direita, mouse, compacto):
    usuario, perfil = _nome_conta(estado)
    fonte = _fonte(13)
    fonte_sub = _fonte(11, False)
    texto = usuario
    sub = perfil or _t('Perfil padrão')
    largura_texto = 0 if compacto else min(150, max(fonte.size(texto)[0], fonte_sub.size(sub)[0]))
    largura = 32 + (largura_texto + 8 if largura_texto else 0) + 20
    rect = pygame.Rect(x_direita - largura, (ALTURA_TOPBAR - 32) // 2, largura, 32)
    menu = getattr(estado, 'menu_superior', None)
    aberto = bool(menu and menu.menu_aberto == 'Perfil' and menu.ancora_dropdown is not None)
    hover = rect.collidepoint(mouse)
    if hover or aberto:
        ds.superficie_translucida(tela, rect, ds.misturar(TEMA.superficie_alt, TEMA.acento, 0.2),
                                  240, ds.RAIO_PILULA, ds.misturar(TEMA.borda, TEMA.acento, 0.6), 1)
    centro = (rect.x + 16, rect.centery)
    pygame.draw.circle(tela, ds.rgb(TEMA.primaria), centro, 12)
    pygame.draw.circle(tela, ds.rgb(TEMA.primaria_clara), centro, 12, 1)
    inicial = (usuario[:1] or '?').upper()
    ds.texto_em(tela, inicial, _fonte(13), centro, TEMA.texto_sobre_cor, ancora='center')
    if getattr(estado, 'usuario_id_logado', None):
        pygame.draw.circle(tela, ds.rgb(TEMA.superficie_topo), (centro[0] + 9, centro[1] + 9), 4)
        pygame.draw.circle(tela, ds.rgb(TEMA.verde), (centro[0] + 9, centro[1] + 9), 3)
    if largura_texto:
        ds.texto_em(tela, texto, fonte, (rect.x + 34, rect.centery - 7), TEMA.texto,
                    ancora='midleft', largura_max=largura_texto)
        ds.texto_em(tela, sub, fonte_sub, (rect.x + 34, rect.centery + 8), TEMA.texto_apagado,
                    ancora='midleft', largura_max=largura_texto)
    # Seta do menu
    sx, sy = rect.right - 11, rect.centery
    pygame.draw.polygon(tela, ds.rgb(TEMA.texto_suave), [(sx - 4, sy - 2), (sx + 4, sy - 2), (sx, sy + 3)])
    email = getattr(estado, 'email_usuario', '') or _t('Sem conta')
    _registrar(estado, rect, 'menu_conta', f"{email}" + (f"  ·  {_t('perfil')}: {perfil}" if perfil else ''))
    return rect.x - ds.ESPACO_SM


def _desenhar_medidor(tela, estado, x_direita, mouse):
    """Microfone + nota detectada + nivel de entrada. Clique abre a escolha da entrada."""
    motor = getattr(estado, 'motor_audio', None)
    ativo = bool(motor is not None and getattr(motor, 'ativo', False))
    largura = 104
    rect = pygame.Rect(x_direita - largura, (ALTURA_TOPBAR - 28) // 2, largura, 28)
    hover = rect.collidepoint(mouse)
    ds.superficie_translucida(tela, rect, ds.misturar(TEMA.superficie_alt, TEMA.acento, 0.18 if hover else 0.0),
                              200 if hover else 150, ds.RAIO_PILULA,
                              ds.misturar(TEMA.borda, TEMA.acento, 0.6) if hover else TEMA.borda, 1)
    # Microfone
    cor_mic = ds.rgb(TEMA.verde if ativo else TEMA.texto_apagado)
    mx, my = rect.x + 15, rect.centery
    pygame.draw.rect(tela, cor_mic, (mx - 3, my - 8, 6, 10), border_radius=3)
    pygame.draw.arc(tela, cor_mic, pygame.Rect(mx - 6, my - 6, 12, 11), 3.5, 5.95, 1)
    pygame.draw.line(tela, cor_mic, (mx, my + 4), (mx, my + 7), 1)
    pygame.draw.line(tela, cor_mic, (mx - 3, my + 7), (mx + 3, my + 7), 1)
    if not ativo:
        pygame.draw.line(tela, ds.rgb(TEMA.alerta), (mx - 7, my + 7), (mx + 7, my - 8), 2)
    # Nota
    nota = getattr(estado, 'nota_atual_detectada', '--') or '--'
    tem_nota = ativo and nota != '--'
    ds.texto_em(tela, nota if ativo else _t('off'), _fonte(13), (rect.x + 40, rect.centery),
                TEMA.texto if tem_nota else TEMA.texto_apagado, ancora='center')
    # Barras de nivel
    nivel = float(getattr(estado, 'nivel_entrada_db', -60.0) or -60.0) if ativo else -60.0
    acesas = int(round(max(0.0, min(1.0, (nivel + 60.0) / 54.0)) * 7))
    x = rect.x + 58
    for i in range(7):
        h = 5 + i * 2
        barra = pygame.Rect(x + i * 6, rect.centery + 8 - h, 4, h)
        if i < acesas:
            cor = TEMA.verde if i < 4 else (TEMA.aviso if i < 6 else TEMA.alerta)
        else:
            cor = ds.misturar(TEMA.borda, TEMA.superficie_topo, 0.2)
        pygame.draw.rect(tela, ds.rgb(cor), barra, border_radius=1)
    dica = (f"{_t('Entrada de áudio')}: {nivel:.0f} dBFS  ·  {_t('clique para trocar')}" if ativo
            else _t('Sem captura de áudio  ·  clique para escolher a entrada'))
    _registrar(estado, rect, 'audio', dica)
    return rect.x - ds.ESPACO_SM


def _desenhar_fps(tela, estado, x_direita):
    """Contador de quadros por segundo (Configuracoes > Desempenho)."""
    fps = getattr(estado, 'fps_real', 0) or 0
    alvo = getattr(estado, 'fps_alvo', 60) or 60
    cor = TEMA.verde if fps >= alvo * 0.9 else (TEMA.aviso if fps >= alvo * 0.6 else TEMA.alerta)
    texto = f'{fps:.0f} FPS'
    fonte = _fonte(12)
    largura = fonte.size('000 FPS')[0] + 16
    rect = pygame.Rect(x_direita - largura, (ALTURA_TOPBAR - 22) // 2, largura, 22)
    ds.superficie_translucida(tela, rect, cor, 40, ds.RAIO_PILULA, cor, 1)
    ds.texto_centralizado(tela, texto, fonte, rect, cor)
    _registrar(estado, rect, 'desempenho', f"{_t('Alvo')}: {alvo} FPS  ·  {_t('clique para ajustar o desempenho')}")
    return rect.x - ds.ESPACO_SM


def _desenhar_status_ia(tela, estado, x_direita):
    """Selo de status da transcricao por IA, quando ativa. Devolve o x livre."""
    cliente = getattr(estado, 'cliente_ia', None)
    if cliente is None or getattr(cliente, 'status', 'idle') == 'idle':
        return x_direita
    status = cliente.status
    if status == 'completed':
        msg, cor = _t('IA pronta'), TEMA.verde
    elif status == 'failed':
        msg, cor = f"{_t('IA: erro')} ({getattr(cliente, 'erro', '')})", TEMA.alerta
    else:
        msg, cor = f"{_t('IA')}: {str(status).upper()}", TEMA.aviso
    fonte = _fonte(12)
    largura = min(fonte.size(msg)[0] + 34, 260)
    rect = pygame.Rect(x_direita - largura, (ALTURA_TOPBAR - 26) // 2, largura, 26)
    if rect.x < 0:
        return x_direita
    ds.superficie_translucida(tela, rect, cor, 45, ds.RAIO_PILULA, cor, 1)
    # Ponto pulsante enquanto processa
    pulsa = ds.EFEITOS['animacoes'] and status not in ('completed', 'failed')
    raio = 3 + int(abs((time.time() * 2) % 2 - 1) * 2) if pulsa else 4
    pygame.draw.circle(tela, ds.rgb(cor), (rect.x + 13, rect.centery), raio)
    ds.texto_em(tela, msg, fonte, (rect.x + 23, rect.centery), cor, ancora='midleft',
                largura_max=largura - 30)
    return rect.x - ds.ESPACO_SM


def _desenhar_contexto(tela, estado, x_ini, x_fim, mouse):
    """Centro da barra: onde o usuario esta e o botao Voltar."""
    import core.acoes_cabecalho as acoes
    disponivel = x_fim - x_ini
    estado.rect_btn_voltar_global = pygame.Rect(-100, -100, 0, 0)
    if disponivel < 90:
        return
    texto, modificado = acoes.nome_contexto(estado)
    tela_aberta = acoes.ha_tela_aberta(estado)
    fonte = _fonte(13)
    fonte_tag = _fonte(11)
    larg_voltar = fonte.size(_t('Voltar'))[0] + 34 if tela_aberta else 0
    larg_tag = fonte_tag.size(_t('não salvo'))[0] + 16 if modificado else 0
    larg_texto = min(fonte.size(texto)[0], 360)
    largura = 30 + larg_texto + (larg_tag + 8 if larg_tag else 0) + 14 + (larg_voltar + 6 if larg_voltar else 0)
    if largura > disponivel:
        # Sem espaco: fica so o Voltar (se houver)
        if not tela_aberta or larg_voltar + 8 > disponivel:
            return
        larg_texto, larg_tag, largura = 0, 0, larg_voltar + 8
    x = x_ini + (disponivel - largura) // 2
    rect = pygame.Rect(x, (ALTURA_TOPBAR - 30) // 2, largura, 30)
    ds.superficie_translucida(tela, rect, TEMA.fundo_alt if TEMA.escuro else TEMA.superficie_alt,
                              170, ds.RAIO_PILULA, TEMA.borda, 1)
    cx = rect.x + 3
    if tela_aberta:
        r_voltar = pygame.Rect(cx, rect.y + 3, larg_voltar, rect.height - 6)
        hover = r_voltar.collidepoint(mouse)
        pygame.draw.rect(tela, ds.rgb(ds.clarear(TEMA.acento, 0.12) if hover else TEMA.acento),
                         r_voltar, border_radius=ds.RAIO_PILULA)
        ax, ay = r_voltar.x + 13, r_voltar.centery
        pygame.draw.lines(tela, ds.rgb(TEMA.texto_sobre_cor), False,
                          [(ax + 3, ay - 5), (ax - 2, ay), (ax + 3, ay + 5)], 2)
        ds.texto_em(tela, _t('Voltar'), fonte, (ax + 9, ay), TEMA.texto_sobre_cor, ancora='midleft')
        estado.rect_btn_voltar_global = r_voltar
        _registrar(estado, r_voltar, 'voltar', _t('Voltar ao workspace'))
        cx = r_voltar.right + 6
    if larg_texto:
        cor_ponto = TEMA.acento if tela_aberta else TEMA.verde
        pygame.draw.circle(tela, ds.rgb(cor_ponto), (cx + 12, rect.centery), 4)
        r_txt = ds.texto_em(tela, texto, fonte, (cx + 24, rect.centery), TEMA.texto,
                            ancora='midleft', largura_max=larg_texto)
        if larg_tag:
            tag = pygame.Rect(r_txt.right + 8, rect.centery - 9, larg_tag, 18)
            ds.superficie_translucida(tela, tag, TEMA.aviso, 50, ds.RAIO_PILULA, TEMA.aviso, 1)
            ds.texto_centralizado(tela, _t('não salvo'), fonte_tag, tag, TEMA.aviso)


def _desenhar_dica(tela, estado, mouse):
    """Dica do botao sob o mouse, depois de um pequeno atraso."""
    alvo = None
    for rect, texto in getattr(estado, '_dicas_cabecalho', []):
        if rect.collidepoint(mouse):
            alvo = (tuple(rect), texto)
            break
    agora = time.time()
    if alvo is None:
        estado._dica_alvo = None
        return
    if getattr(estado, '_dica_alvo', None) != alvo:
        estado._dica_alvo = alvo
        estado._dica_desde = agora
        return
    if agora - getattr(estado, '_dica_desde', agora) < ATRASO_DICA:
        return
    rect_alvo, texto = pygame.Rect(alvo[0]), alvo[1]
    fonte = _fonte(12, False)
    largura = fonte.size(texto)[0] + 20
    caixa = pygame.Rect(0, rect_alvo.bottom + 8, largura, 26)
    caixa.centerx = rect_alvo.centerx
    caixa.x = max(6, min(caixa.x, tela.get_width() - caixa.width - 6))
    ds.sombra(tela, caixa, ds.RAIO_MD, forca=100, deslocamento=2)
    pygame.draw.rect(tela, ds.rgb(TEMA.texto), caixa, border_radius=ds.RAIO_MD)
    ds.texto_centralizado(tela, texto, fonte, caixa, TEMA.superficie, largura_max=caixa.width - 8)


# ---------------------------------------------------------------------------
# Entrada principal
# ---------------------------------------------------------------------------

def desenhar_painel_superior(tela, estado, fontes, configs):
    """
    Como funciona: Pinta a barra, os menus e os controles globais, registra os
    alvos clicaveis e, por ultimo, desenha modais, dicas e avisos por cima de
    tudo (inclusive do workspace).
    Para que serve: Ponto fixo de navegacao e controle global da aplicacao.
    Onde e usada: main.py e renderizador_ui.desenhar_tudo, depois do conteudo.
    """
    import core.acoes_cabecalho as acoes
    largura_tela = tela.get_width()
    mouse = _mouse_real(estado)
    estado.botoes_cabecalho = []
    estado._dicas_cabecalho = []

    if configs is not None:
        TEMA.definir_acento(configs.get_cor_tema())

    # 1. Fundo
    rect_barra = pygame.Rect(0, 0, largura_tela, ALTURA_TOPBAR)
    ds.gradiente_vertical(tela, rect_barra, TEMA.superficie_topo,
                          ds.misturar(TEMA.superficie_topo, TEMA.fundo, 0.55))
    pygame.draw.line(tela, ds.rgb(ds.misturar(TEMA.borda, TEMA.acento, 0.35)),
                     (0, ALTURA_TOPBAR - 1), (largura_tela, ALTURA_TOPBAR - 1), 1)

    # 2. Marca
    x_menus = _desenhar_marca(tela, fontes, largura_tela)

    # 3. Lado direito (da direita para a esquerda)
    x = largura_tela - ds.ESPACO_MD
    x = _desenhar_botoes_sistema(tela, estado, x, mouse)
    x = _desenhar_conta(tela, estado, x, mouse, compacto=largura_tela < 1440)
    if largura_tela >= 1280:
        x = _desenhar_medidor(tela, estado, x, mouse)
    if (getattr(estado, 'desempenho', None) or {}).get('mostrar_fps'):
        x = _desenhar_fps(tela, estado, x)
    x_limite_direita = x

    # 4. Menus
    menu = getattr(estado, 'menu_superior', None)
    fonte_menu = fontes.get('pequena', fontes['ui'])
    fim_menus = x_menus
    if menu is not None:
        menu.offset_x = x_menus
        menu.largura_disponivel = largura_tela
        menu.fonte_menu = fonte_menu
        menu.recalcular_posicoes(largura_tela, fonte_menu)
        fim_menus = menu.largura_total_menu

    # 5. Status da IA e contexto no espaco do meio
    x_limite_direita = _desenhar_status_ia(tela, estado, x_limite_direita) \
        if x_limite_direita - fim_menus > 360 else x_limite_direita
    _desenhar_contexto(tela, estado, fim_menus + ds.ESPACO_LG, x_limite_direita - ds.ESPACO_SM, mouse)

    # 6. Titulos e dropdown dos menus (por cima do contexto)
    if menu is not None:
        menu.desenhar(tela, fonte_menu, estado, _fonte(12, False), fontes.get('titulo'))

    # 7. Captura de tela pedida no quadro anterior: sai sem modal, dica ou aviso
    acoes.executar_captura_se_pendente(estado, tela)

    # 8. Camadas por cima de tudo
    if menu is not None:
        fontes_modal = {'ui': _fonte(15, False), 'pequena': _fonte(13, False),
                        'titulo': _fonte(19), 'botao': _fonte(14)}
        menu.desenhar_sobreposicoes(tela, fontes, fontes_modal)
    if menu is None or not menu.ocupado:
        _desenhar_dica(tela, estado, mouse)
    desenhar_notificacoes(tela, estado, _fonte(13), ALTURA_TOPBAR)
