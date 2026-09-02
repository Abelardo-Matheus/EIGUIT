# -*- coding: utf-8 -*-
"""
Auditoria de interface do EIGUIT.

Tres verificacoes, nos dois temas:

1. Contraste: os pares de cor que a interface usa de verdade (texto sobre
   painel, texto sobre acento, marcas de alerta e de acerto) precisam passar
   no contraste minimo da WCAG para o tamanho em que sao usados.
2. Alvos da barra superior: todo botao clicavel do topo tem de caber dentro da
   barra, ter tamanho de alvo aceitavel e nao se sobrepor a outro.
3. Regioes vazias: cada bloco do layout padrao e auditado no quadro real. Um
   bloco que so desenha a moldura, sem conteudo dentro, e erro. Todo bloco
   novo entra aqui automaticamente, porque a lista sai do layout padrao.

Uso: python3 auditoria.py    (silencioso quando esta tudo limpo)
"""
import sys

import pygame

import harness
from harness import Contexto, Suite

from config.design_system import TEMA, PALETA_CLARA, PALETA_ESCURA
from config.ui_metrics import ALTURA_TOPBAR
import config.layout_padrao as layout
from ui import renderizador_ui
from ui.components import desenhar_painel_superior

LARGURA, ALTURA = 1920, 1080

# (frente, fundo, minimo, descricao). 4.5 para texto corrido, 3.0 para texto
# grande, para elemento de interface e para marca colorida.
PARES = [
    ('texto', 'superficie', 4.5, 'texto sobre painel'),
    ('texto', 'superficie_alt', 4.5, 'texto sobre painel elevado'),
    ('texto_suave', 'superficie', 4.5, 'texto secundario sobre painel'),
    ('texto_apagado', 'superficie', 3.0, 'texto apagado sobre painel'),
    ('texto_sobre_cor', 'primaria', 3.0, 'texto sobre botao primario'),
    ('alerta', 'superficie_alt', 3.0, 'nota fora da tonalidade'),
    ('verde', 'superficie_alt', 3.0, 'corda dentro da tonalidade'),
    ('ciano', 'superficie_alt', 3.0, 'intervalo e vizinhas do ciclo'),
    ('acento_padrao', 'superficie', 3.0, 'titulo do painel'),
    ('borda', 'superficie', 1.3, 'borda do painel'),
]

ALVO_MINIMO = 20        # menor lado aceitavel de um alvo de clique, em pixels


def _luminancia(cor):
    canais = []
    for c in cor[:3]:
        c = c / 255.0
        canais.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = canais
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(frente, fundo):
    a, b = _luminancia(frente), _luminancia(fundo)
    claro, escuro = max(a, b), min(a, b)
    return (claro + 0.05) / (escuro + 0.05)


s = Suite('auditoria')


def auditar_contraste(tema):
    paleta = PALETA_ESCURA if tema == 'escuro' else PALETA_CLARA
    problemas = []
    for nome_frente, nome_fundo, minimo, descricao in PARES:
        frente = paleta['primaria'] if nome_frente == 'acento_padrao' else paleta[nome_frente]
        fundo = paleta[nome_fundo]
        razao = contraste(frente, fundo)
        if razao < minimo:
            problemas.append(f'{descricao}: {razao:.2f} < {minimo}')
    s.checar(not problemas, 'contraste insuficiente -> ' + '; '.join(problemas))


def _quadro(tema, com_blocos_na_tela=True):
    """Desenha um quadro completo e devolve (contexto, tela)."""
    ctx = Contexto(LARGURA, ALTURA, tema)
    if com_blocos_na_tela:
        # A auditoria de regiao so faz sentido com os blocos fora da gaveta
        ctx.estado.blocos_guardados = set()
    ctx.estado.historico_notas = ['C', 'D', 'F#', 'A', 'C', 'E', 'G', 'A#']
    ctx.estado.ideias_recentes = ['Ideias/ideia_2026-09-01_10-12-33.wav']
    ctx.estado.grau_selecionado = 4
    ctx.estado.progressao_ativa = 0
    ctx.estado.capo_casa = 2
    tela = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    from config.design_system import ds
    ds.fundo_app(tela)
    viewport = tela.subsurface(pygame.Rect(0, ALTURA_TOPBAR, LARGURA,
                                           ALTURA - ALTURA_TOPBAR))
    renderizador_ui.desenhar_workspace(
        viewport, ctx.estado, ctx.configs, ctx.escalas, ctx.fontes,
        ctx.metronomo, ctx.processador, ctx.gravador, ctx.campo, ctx.jogos)
    desenhar_painel_superior(tela, ctx.estado, ctx.fontes, ctx.configs)
    return ctx, tela


def auditar_gavetas(tema):
    """As gavetas sao alvo de clique como qualquer outro: tamanho e limites."""
    from ui.components import gaveteiro as gv
    ctx, _tela = _quadro(tema, com_blocos_na_tela=False)
    ctx.estado.mouse_workspace = (8, 300)
    for _ in range(40):
        gv.atualizar(ctx.estado, ALTURA - ALTURA_TOPBAR)
    tela = pygame.Surface((LARGURA, ALTURA - ALTURA_TOPBAR), pygame.SRCALPHA)
    gv.desenhar(tela, ctx.estado, ctx.fontes, ctx.configs)

    problemas = []
    s.checar(ctx.estado.rects_gavetas, 'o gaveteiro nao desenhou gaveta nenhuma')
    coluna = pygame.Rect(0, 0, gv.largura_atual(ctx.estado), ALTURA - ALTURA_TOPBAR)
    for rect, nome in ctx.estado.rects_gavetas:
        if not coluna.contains(rect):
            problemas.append(f'{nome} sai da coluna')
        if rect.height < ALVO_MINIMO:
            problemas.append(f'{nome} baixa demais ({rect.height}px)')
    s.checar(not problemas, 'gavetas -> ' + '; '.join(problemas))


def auditar_alvos_topo(tema):
    ctx, _tela = _quadro(tema)
    barra = pygame.Rect(0, 0, LARGURA, ALTURA_TOPBAR)
    alvos = []
    for nome in ('rect_btn_tema', 'rect_btn_pin', 'rect_btn_voltar_global'):
        r = getattr(ctx.estado, nome, None)
        if r is not None and r.width > 0 and r.x >= 0:
            alvos.append((nome, pygame.Rect(r)))
    menu = getattr(ctx.estado, 'menu_superior', None)
    for nome, r in getattr(menu, 'rects_principais', {}).items():
        alvos.append((f'menu {nome}', pygame.Rect(r)))

    s.checar(alvos, 'a barra superior nao registrou nenhum alvo clicavel')
    problemas = []
    for nome, r in alvos:
        if not barra.contains(r):
            problemas.append(f'{nome} sai da barra ({r})')
        if min(r.width, r.height) < ALVO_MINIMO:
            problemas.append(f'{nome} pequeno demais ({r.width}x{r.height})')
    for i, (nome_a, a) in enumerate(alvos):
        for nome_b, b in alvos[i + 1:]:
            if a.colliderect(b):
                problemas.append(f'{nome_a} e {nome_b} se sobrepoem')
    s.checar(not problemas, 'alvos da barra superior -> ' + '; '.join(problemas))


def _fracao_de_conteudo(tela, rect):
    """Quanto do bloco nao e a cor de fundo dominante dele."""
    contagem = {}
    passo = 2
    total = 0
    for y in range(rect.y + 4, rect.bottom - 4, passo):
        for x in range(rect.x + 4, rect.right - 4, passo):
            cor = tela.get_at((x, y))[:3]
            contagem[cor] = contagem.get(cor, 0) + 1
            total += 1
    if not total:
        return 0.0
    dominante = max(contagem.values())
    return 1.0 - dominante / total


def auditar_regioes(tema):
    ctx, tela = _quadro(tema)
    problemas = []
    from ui.components import gaveteiro as gv
    coluna = pygame.Rect(0, ALTURA_TOPBAR, gv.largura_atual(ctx.estado),
                         ALTURA - ALTURA_TOPBAR)
    if _fracao_de_conteudo(tela, coluna) < 0.02:
        problemas.append('a coluna do gaveteiro ficou vazia')
    for nome in sorted(layout.BLOCOS_REF):
        bloco = getattr(ctx.estado, nome, None)
        if bloco is None:
            problemas.append(f'{nome} nao existe no estado')
            continue
        rect = pygame.Rect(bloco.x, bloco.y + ALTURA_TOPBAR,
                           bloco.largura, bloco.altura)
        rect = rect.clip(pygame.Rect(0, 0, LARGURA, ALTURA))
        if rect.width < 12 or rect.height < 12:
            problemas.append(f'{nome} ficou sem area visivel')
            continue
        # A parte coberta pela coluna nao conta: ali quem manda e o gaveteiro
        if rect.right <= coluna.right:
            continue
        rect = pygame.Rect(max(rect.x, coluna.right), rect.y,
                           rect.right - max(rect.x, coluna.right), rect.height)
        fracao = _fracao_de_conteudo(tela, rect)
        if fracao < 0.02:
            problemas.append(f'{nome} vazio ({fracao * 100:.1f}% de conteudo)')
    s.checar(not problemas, 'regioes vazias -> ' + '; '.join(problemas))


if __name__ == '__main__':
    for _tema in harness.TEMAS:
        s.teste(f'[{_tema}] contraste das cores em uso',
                lambda t=_tema: auditar_contraste(t))
        s.teste(f'[{_tema}] alvos clicaveis da barra superior',
                lambda t=_tema: auditar_alvos_topo(t))
        s.teste(f'[{_tema}] nenhuma regiao do layout fica vazia',
                lambda t=_tema: auditar_regioes(t))
        s.teste(f'[{_tema}] alvos das gavetas laterais',
                lambda t=_tema: auditar_gavetas(t))

    s.encerrar()
