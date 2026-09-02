# -*- coding: utf-8 -*-
"""
Sistema de Design do EIGUIT Studio.

Ponto unico de verdade para toda a aparencia do programa: paletas (escuro/claro),
espacamentos, raios, tipografia e os componentes de desenho reutilizaveis.

Como usar em um renderizador:

    from config.design_system import TEMA, ds

    ds.painel(tela, rect, titulo='Metronomo', fonte=fontes['pequena'])
    ds.botao(tela, rect_btn, 'PLAY', fontes['ui'], variante='primario')

TEMA e um objeto vivo: trocar o modo com TEMA.alternar() reflete imediatamente
em todos os modulos que leem TEMA.<token>, sem reiniciar o programa.
"""
import json
import os

import pygame

# ---------------------------------------------------------------------------
# PALETAS
# ---------------------------------------------------------------------------

PALETA_ESCURA = {
    'fundo': (10, 14, 39),
    'fundo_alt': (26, 31, 58),
    'superficie': (20, 26, 48),
    'superficie_alt': (28, 35, 60),
    'superficie_topo': (14, 18, 36),
    'borda': (44, 54, 82),
    'borda_forte': (0, 120, 215),
    'texto': (255, 255, 255),
    'texto_suave': (170, 178, 196),
    'texto_apagado': (128, 136, 154),
    'texto_sobre_cor': (255, 255, 255),
    'primaria': (0, 120, 215),
    'primaria_clara': (0, 212, 255),
    'primaria_escura': (0, 84, 156),
    'ciano': (0, 212, 255),
    'verde': (78, 205, 196),
    'alerta': (255, 107, 107),
    'aviso': (255, 217, 61),
    'roxo': (155, 122, 255),
    'madeira': (58, 34, 20),
    'corda': (150, 156, 172),
    'traste': (92, 100, 120),
    'trilho': (44, 54, 82),
    'sombra': (0, 0, 0),
    'overlay': (6, 9, 26),
}

PALETA_CLARA = {
    'fundo': (240, 243, 250),
    'fundo_alt': (255, 255, 255),
    'superficie': (255, 255, 255),
    'superficie_alt': (238, 242, 249),
    'superficie_topo': (255, 255, 255),
    'borda': (206, 215, 230),
    'borda_forte': (0, 120, 215),
    'texto': (16, 24, 45),
    'texto_suave': (85, 97, 122),
    'texto_apagado': (132, 146, 171),
    'texto_sobre_cor': (255, 255, 255),
    'primaria': (0, 110, 200),
    'primaria_clara': (0, 146, 184),
    'primaria_escura': (0, 78, 145),
    'ciano': (0, 146, 184),
    'verde': (21, 156, 146),
    'alerta': (214, 69, 69),
    'aviso': (183, 121, 31),
    'roxo': (118, 84, 214),
    'madeira': (176, 132, 92),
    'corda': (120, 128, 146),
    'traste': (168, 176, 192),
    'trilho': (216, 223, 235),
    'sombra': (120, 132, 158),
    'overlay': (226, 232, 242),
}

# ---------------------------------------------------------------------------
# ESCALAS (espacamento, raio, tipografia)
# ---------------------------------------------------------------------------

ESPACO_XS = 4
ESPACO_SM = 8
ESPACO_MD = 12
ESPACO_LG = 16
ESPACO_XL = 24

RAIO_SM = 4
RAIO_MD = 6
RAIO_LG = 10
RAIO_XL = 15
RAIO_PILULA = 999

ALTURA_CONTROLE = 32
ALTURA_CONTROLE_SM = 26
ALTURA_TRILHO = 6

ARQUIVO_PREFS = 'config_eiguit.json'


def _raiz_projeto():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class _Tema:
    """Estado vivo do tema. Ler TEMA.<token> sempre devolve a cor do modo atual."""

    MODOS = ('escuro', 'claro')

    def __init__(self):
        self.modo = 'escuro'
        self._paleta = PALETA_ESCURA
        # Cor de destaque escolhida pelo usuario nas Configuracoes.
        # Quando None, usa a primaria da paleta.
        self.acento_usuario = None
        self.carregar()

    # -- acesso aos tokens --------------------------------------------------
    def __getattr__(self, nome):
        paleta = self.__dict__.get('_paleta') or PALETA_ESCURA
        if nome in paleta:
            return paleta[nome]
        raise AttributeError(nome)

    @property
    def acento(self):
        """Cor de destaque efetiva (respeita o tema de cores do usuario)."""
        return self.acento_usuario or self._paleta['primaria']

    @property
    def escuro(self):
        return self.modo == 'escuro'

    def definir_acento(self, cor):
        self.acento_usuario = tuple(cor[:3]) if cor else None

    # -- troca de modo ------------------------------------------------------
    def definir_modo(self, modo):
        if modo not in self.MODOS:
            return
        self.modo = modo
        self._paleta = PALETA_ESCURA if modo == 'escuro' else PALETA_CLARA
        self.salvar()

    def alternar(self):
        self.definir_modo('claro' if self.modo == 'escuro' else 'escuro')
        return self.modo

    # -- persistencia -------------------------------------------------------
    def _caminho_prefs(self):
        return os.path.join(_raiz_projeto(), ARQUIVO_PREFS)

    def carregar(self):
        try:
            with open(self._caminho_prefs(), 'r', encoding='utf-8') as arq:
                dados = json.load(arq)
            modo = dados.get('tema_interface', 'escuro')
            if modo in self.MODOS:
                self.modo = modo
                self._paleta = PALETA_ESCURA if modo == 'escuro' else PALETA_CLARA
        except Exception:
            pass

    def salvar(self):
        caminho = self._caminho_prefs()
        dados = {}
        try:
            with open(caminho, 'r', encoding='utf-8') as arq:
                dados = json.load(arq)
        except Exception:
            dados = {}
        dados['tema_interface'] = self.modo
        try:
            with open(caminho, 'w', encoding='utf-8') as arq:
                json.dump(dados, arq, ensure_ascii=False)
        except Exception:
            pass


TEMA = _Tema()


# ---------------------------------------------------------------------------
# UTILIDADES DE COR
# ---------------------------------------------------------------------------

def rgb(cor):
    """Normaliza qualquer cor para uma tupla RGB de 3 canais."""
    return (int(cor[0]), int(cor[1]), int(cor[2]))


def com_alpha(cor, a):
    return (int(cor[0]), int(cor[1]), int(cor[2]), max(0, min(255, int(a))))


def misturar(cor_a, cor_b, t):
    """Interpola linearmente entre duas cores. t=0 -> cor_a, t=1 -> cor_b."""
    t = max(0.0, min(1.0, t))
    return (
        int(cor_a[0] + (cor_b[0] - cor_a[0]) * t),
        int(cor_a[1] + (cor_b[1] - cor_a[1]) * t),
        int(cor_a[2] + (cor_b[2] - cor_a[2]) * t),
    )


def clarear(cor, q=0.2):
    return misturar(rgb(cor), (255, 255, 255), q)


def escurecer(cor, q=0.2):
    return misturar(rgb(cor), (0, 0, 0), q)


def contraste_texto(cor_fundo):
    """Escolhe preto ou branco conforme a luminancia do fundo."""
    lum = (0.299 * cor_fundo[0] + 0.587 * cor_fundo[1] + 0.114 * cor_fundo[2]) / 255
    return (15, 20, 35) if lum > 0.62 else (255, 255, 255)


# ---------------------------------------------------------------------------
# PRIMITIVAS DE DESENHO
# ---------------------------------------------------------------------------

def gradiente_vertical(tela, rect, cor_topo, cor_base, raio=0):
    """Preenche um retangulo com gradiente vertical suave."""
    rect = pygame.Rect(rect)
    if rect.height <= 0 or rect.width <= 0:
        return
    superficie = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    passos = max(1, min(rect.height, 96))
    altura_passo = rect.height / passos
    for i in range(passos):
        cor = misturar(cor_topo, cor_base, i / max(1, passos - 1))
        pygame.draw.rect(
            superficie, cor,
            (0, int(i * altura_passo), rect.width, int(altura_passo) + 1)
        )
    if raio:
        mascara = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(mascara, (255, 255, 255, 255),
                         (0, 0, rect.width, rect.height), border_radius=raio)
        superficie.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    tela.blit(superficie, rect.topleft)


def sombra(tela, rect, raio=RAIO_XL, forca=70, deslocamento=3, expansao=2):
    """Sombra suave sob um painel. No tema claro fica mais discreta."""
    rect = pygame.Rect(rect)
    forca = forca if TEMA.escuro else int(forca * 0.45)
    camadas = 3
    for i in range(camadas, 0, -1):
        alpha = int(forca / (i * 1.9))
        r = rect.inflate(expansao * i * 2, expansao * i * 2)
        r.y += deslocamento
        superficie = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        pygame.draw.rect(superficie, com_alpha(TEMA.sombra, alpha),
                         (0, 0, r.width, r.height), border_radius=raio + i * 2)
        tela.blit(superficie, r.topleft)


def superficie_translucida(tela, rect, cor, alpha=235, raio=RAIO_XL,
                           cor_borda=None, largura_borda=1):
    """Retangulo arredondado semitransparente (o painel base do design)."""
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return rect
    superficie = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(superficie, com_alpha(cor, alpha),
                     (0, 0, rect.width, rect.height), border_radius=raio)
    if cor_borda is not None and largura_borda > 0:
        pygame.draw.rect(superficie, com_alpha(cor_borda, min(255, alpha + 40)),
                         (0, 0, rect.width, rect.height),
                         width=largura_borda, border_radius=raio)
    tela.blit(superficie, rect.topleft)
    return rect


def truncar(texto, fonte, largura_max, sufixo='...'):
    """Corta o texto para caber na largura, adicionando reticencias."""
    if largura_max <= 0 or fonte.size(texto)[0] <= largura_max:
        return texto
    corte = texto
    while corte and fonte.size(corte + sufixo)[0] > largura_max:
        corte = corte[:-1]
    return (corte + sufixo) if corte else ''


def texto_em(tela, texto, fonte, pos, cor=None, ancora='topleft', largura_max=None):
    """Renderiza texto com ancoragem e truncamento opcional."""
    cor = cor if cor is not None else TEMA.texto
    if largura_max:
        texto = truncar(texto, fonte, largura_max)
    surf = fonte.render(texto, True, rgb(cor))
    rect = surf.get_rect(**{ancora: pos})
    tela.blit(surf, rect.topleft)
    return rect


def texto_centralizado(tela, texto, fonte, rect, cor=None, largura_max=None):
    rect = pygame.Rect(rect)
    return texto_em(tela, texto, fonte, rect.center, cor, 'center',
                    largura_max if largura_max is not None else rect.width - 8)


def divisor(tela, x, y, largura, cor=None):
    pygame.draw.line(tela, rgb(cor or TEMA.borda), (x, y), (x + largura, y), 1)


# ---------------------------------------------------------------------------
# COMPONENTES
# ---------------------------------------------------------------------------

def painel(tela, rect, titulo=None, fonte=None, raio=RAIO_XL, acento=None,
           alpha=235, com_sombra=True, elevado=False, cor_fundo=None):
    """
    Painel padrao do EIGUIT: fundo translucido, borda sutil, faixa de acento no
    topo e titulo opcional em caixa alta. Devolve o Y onde o conteudo comeca.
    """
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return rect.y
    if com_sombra:
        sombra(tela, rect, raio)
    base = cor_fundo or (TEMA.superficie_alt if elevado else TEMA.superficie)
    superficie_translucida(tela, rect, base, alpha, raio, TEMA.borda, 1)

    if acento:
        faixa = pygame.Surface((rect.width, 3), pygame.SRCALPHA)
        pygame.draw.rect(faixa, com_alpha(acento, 210), (0, 0, rect.width, 3),
                         border_top_left_radius=raio, border_top_right_radius=raio)
        tela.blit(faixa, (rect.x, rect.y))

    y_conteudo = rect.y + ESPACO_MD
    if titulo and fonte:
        texto_em(tela, titulo.upper(), fonte,
                 (rect.x + ESPACO_LG, rect.y + ESPACO_MD),
                 acento or TEMA.acento, largura_max=rect.width - ESPACO_XL)
        y_conteudo = rect.y + ESPACO_MD + fonte.get_height() + ESPACO_SM
    return y_conteudo


def rotulo_secao(tela, x, y, texto, fonte, cor=None, largura_max=None):
    """Titulo pequeno em caixa alta usado para separar blocos."""
    return texto_em(tela, texto.upper(), fonte, (x, y),
                    cor or TEMA.acento, largura_max=largura_max)


def botao(tela, rect, texto, fonte, variante='primario', ativo=False,
          hover=False, habilitado=True, raio=RAIO_MD, cor=None, icone=None):
    """
    Botao consistente do design system.

    variantes: 'primario', 'secundario', 'fantasma', 'perigo', 'sucesso', 'suave'
    """
    rect = pygame.Rect(rect)
    acento = cor or TEMA.acento

    mapa = {
        'primario': (acento, TEMA.texto_sobre_cor, None),
        'secundario': (TEMA.superficie_alt, TEMA.texto, TEMA.borda),
        'fantasma': (None, acento, acento),
        'perigo': (TEMA.alerta, (255, 255, 255), None),
        'sucesso': (TEMA.verde, contraste_texto(TEMA.verde), None),
        'suave': (misturar(TEMA.superficie, acento, 0.18), acento, misturar(TEMA.borda, acento, 0.4)),
    }
    fundo, cor_texto, cor_borda = mapa.get(variante, mapa['primario'])

    if ativo and variante in ('secundario', 'fantasma', 'suave'):
        fundo, cor_texto, cor_borda = acento, TEMA.texto_sobre_cor, None
    if hover and fundo is not None:
        fundo = clarear(fundo, 0.12)
    if not habilitado:
        fundo = TEMA.superficie_alt if fundo is not None else None
        cor_texto = TEMA.texto_apagado
        cor_borda = TEMA.borda

    if fundo is not None:
        pygame.draw.rect(tela, rgb(fundo), rect, border_radius=raio)
    if cor_borda is not None:
        pygame.draw.rect(tela, rgb(cor_borda), rect, width=1, border_radius=raio)

    conteudo = texto
    if icone:
        conteudo = f'{icone} {texto}'.strip()
    if conteudo:
        texto_centralizado(tela, conteudo, fonte, rect, cor_texto)
    return rect


def chip(tela, rect, texto, fonte, ativo=False, cor=None):
    """Pilula de selecao (sub-abas, modos, filtros)."""
    rect = pygame.Rect(rect)
    acento = cor or TEMA.acento
    if ativo:
        pygame.draw.rect(tela, rgb(acento), rect, border_radius=RAIO_PILULA)
        cor_txt = TEMA.texto_sobre_cor
    else:
        superficie_translucida(tela, rect, TEMA.superficie_alt, 220,
                               RAIO_PILULA, TEMA.borda, 1)
        cor_txt = TEMA.texto_suave
    texto_centralizado(tela, texto, fonte, rect, cor_txt)
    return rect


def selo(tela, pos, texto, fonte, cor=None, ancora='topleft'):
    """Etiqueta compacta com fundo tingido (ex.: 'Root: C')."""
    acento = cor or TEMA.acento
    largura = fonte.size(texto)[0] + ESPACO_MD * 2
    altura = fonte.get_height() + ESPACO_XS * 2
    rect = pygame.Rect(0, 0, largura, altura)
    setattr(rect, ancora, pos)
    superficie_translucida(tela, rect, acento, 60, RAIO_SM, acento, 1)
    texto_centralizado(tela, texto, fonte, rect, acento)
    return rect


def trilho(tela, rect, pct, cor=None, raio=None, cor_trilho=None):
    """Barra de progresso / preenchimento de slider."""
    rect = pygame.Rect(rect)
    raio = rect.height // 2 if raio is None else raio
    pct = max(0.0, min(1.0, pct))
    pygame.draw.rect(tela, rgb(cor_trilho or TEMA.trilho), rect, border_radius=raio)
    largura = int(rect.width * pct)
    if largura > 0:
        rect_cheio = pygame.Rect(rect.x, rect.y, max(raio * 2, largura), rect.height)
        gradiente_vertical(tela, rect_cheio, clarear(cor or TEMA.acento, 0.25),
                           cor or TEMA.acento, raio)
    return rect


def slider(tela, rect_barra, pct, cor=None, rotulo=None, valor=None,
           fonte=None, raio_alca=8):
    """
    Slider completo: rotulo + valor a direita, trilho preenchido e alca.
    Devolve (rect_barra, rect_alca) para o tratamento de clique.
    """
    rect_barra = pygame.Rect(rect_barra)
    acento = cor or TEMA.acento
    if fonte and (rotulo or valor is not None):
        y_texto = rect_barra.y - fonte.get_height() - ESPACO_SM
        if rotulo:
            texto_em(tela, rotulo, fonte, (rect_barra.x, y_texto), TEMA.texto_suave)
        if valor is not None:
            texto_em(tela, str(valor), fonte, (rect_barra.right, y_texto),
                     acento, ancora='topright')
    trilho(tela, rect_barra, pct, acento)

    pct = max(0.0, min(1.0, pct))
    cx = rect_barra.x + int(rect_barra.width * pct)
    cy = rect_barra.centery
    pygame.draw.circle(tela, rgb(TEMA.texto_sobre_cor if TEMA.escuro else (255, 255, 255)),
                       (cx, cy), raio_alca)
    pygame.draw.circle(tela, rgb(acento), (cx, cy), raio_alca, 3)
    rect_alca = pygame.Rect(cx - raio_alca, cy - raio_alca, raio_alca * 2, raio_alca * 2)
    return rect_barra, rect_alca


def interruptor(tela, rect, ligado, cor=None):
    """Toggle switch (usado no modo claro/escuro e em opcoes booleanas)."""
    rect = pygame.Rect(rect)
    acento = cor or TEMA.acento
    raio = rect.height // 2
    fundo = acento if ligado else TEMA.trilho
    pygame.draw.rect(tela, rgb(fundo), rect, border_radius=raio)
    if not ligado:
        pygame.draw.rect(tela, rgb(TEMA.borda), rect, width=1, border_radius=raio)
    cxr = raio - 2
    cx = (rect.right - raio) if ligado else (rect.x + raio)
    pygame.draw.circle(tela, (255, 255, 255), (cx, rect.centery), cxr)
    return rect


def caixa_valor(tela, rect, valor, legenda=None, fonte_valor=None,
                fonte_legenda=None, cor=None, raio=RAIO_LG):
    """Bloco de leitura grande (nota detectada, BPM, precisao)."""
    rect = pygame.Rect(rect)
    acento = cor or TEMA.acento
    superficie_translucida(tela, rect, misturar(TEMA.superficie, acento, 0.12),
                           220, raio, acento, 2)
    if legenda and fonte_legenda:
        alt_legenda = fonte_legenda.get_height()
        texto_em(tela, str(valor), fonte_valor,
                 (rect.centerx, rect.centery - alt_legenda // 2),
                 acento, ancora='center', largura_max=rect.width - ESPACO_MD)
        texto_em(tela, legenda, fonte_legenda,
                 (rect.centerx, rect.bottom - ESPACO_SM - alt_legenda // 2),
                 TEMA.texto_suave, ancora='center', largura_max=rect.width - ESPACO_SM)
    else:
        texto_centralizado(tela, str(valor), fonte_valor, rect, acento)
    return rect


def caixa_texto(tela, rect, texto, fonte, focado=False, placeholder='',
                cor=None, raio=RAIO_MD):
    """Campo de entrada de texto."""
    rect = pygame.Rect(rect)
    acento = cor or TEMA.acento
    superficie_translucida(tela, rect, TEMA.superficie_alt, 240, raio,
                           acento if focado else TEMA.borda, 2 if focado else 1)
    mostrar = texto if texto else placeholder
    cor_txt = TEMA.texto if texto else TEMA.texto_apagado
    if mostrar:
        texto_em(tela, mostrar, fonte, (rect.x + ESPACO_MD, rect.centery),
                 cor_txt, ancora='midleft', largura_max=rect.width - ESPACO_XL)
    if focado and (pygame.time.get_ticks() // 500) % 2 == 0:
        x_cursor = rect.x + ESPACO_MD + fonte.size(texto)[0] + 2
        if x_cursor < rect.right - ESPACO_SM:
            pygame.draw.line(tela, rgb(acento), (x_cursor, rect.y + 6),
                             (x_cursor, rect.bottom - 6), 2)
    return rect


def medidor_desvio(tela, rect, desvio, limite=50.0, fonte=None, cor=None):
    """
    Medidor de afinacao com zero no centro.
    desvio em cents (negativo = grave, positivo = agudo).
    """
    rect = pygame.Rect(rect)
    acento = cor or TEMA.acento
    proporcao = max(-1.0, min(1.0, desvio / limite))
    afinado = abs(desvio) <= 5
    cor_estado = TEMA.verde if afinado else (TEMA.aviso if abs(desvio) <= 20 else TEMA.alerta)

    pygame.draw.rect(tela, rgb(TEMA.trilho), rect, border_radius=rect.height // 2)
    centro = rect.centerx
    largura_barra = int(abs(proporcao) * (rect.width / 2))
    if largura_barra > 2:
        x = centro if proporcao > 0 else centro - largura_barra
        pygame.draw.rect(tela, rgb(cor_estado), (x, rect.y, largura_barra, rect.height),
                         border_radius=rect.height // 2)
    pygame.draw.line(tela, rgb(TEMA.texto), (centro, rect.y - 3),
                     (centro, rect.bottom + 3), 2)
    if fonte:
        sinal = '+' if desvio > 0 else ''
        texto_em(tela, f'{sinal}{desvio:.0f} cents', fonte,
                 (rect.centerx, rect.bottom + ESPACO_SM + fonte.get_height() // 2),
                 cor_estado, ancora='center')
    return cor_estado


def barra_rolagem(tela, x, y, altura, pct_visivel, pct_scroll, largura=8):
    """Scrollbar arredondada."""
    if pct_visivel >= 1.0:
        return
    pygame.draw.rect(tela, rgb(TEMA.trilho), (x, y, largura, altura),
                     border_radius=largura // 2)
    alt_alca = max(30, int(altura * pct_visivel))
    y_alca = y + int((altura - alt_alca) * max(0.0, min(1.0, pct_scroll)))
    pygame.draw.rect(tela, rgb(misturar(TEMA.borda, TEMA.acento, 0.5)),
                     (x, y_alca, largura, alt_alca), border_radius=largura // 2)


def icone_tema(tela, centro, modo, cor=None, tamanho=8):
    """Desenha o icone sol (tema claro) ou lua (tema escuro)."""
    cor = rgb(cor or TEMA.texto)
    cx, cy = int(centro[0]), int(centro[1])
    if modo == 'escuro':
        pygame.draw.circle(tela, cor, (cx, cy), tamanho)
        # recorta a lua deslocando um circulo do fundo
        pygame.draw.circle(tela, rgb(TEMA.superficie_topo),
                           (cx + tamanho // 2, cy - tamanho // 2), tamanho)
    else:
        pygame.draw.circle(tela, cor, (cx, cy), tamanho - 3)
        for i in range(8):
            import math
            ang = i * math.pi / 4
            x1 = cx + int(math.cos(ang) * (tamanho - 1))
            y1 = cy + int(math.sin(ang) * (tamanho - 1))
            x2 = cx + int(math.cos(ang) * (tamanho + 3))
            y2 = cy + int(math.sin(ang) * (tamanho + 3))
            pygame.draw.line(tela, cor, (x1, y1), (x2, y2), 2)


def fundo_app(tela, rect=None):
    """Fundo geral da aplicacao com gradiente vertical."""
    rect = pygame.Rect(rect) if rect else tela.get_rect()
    gradiente_vertical(tela, rect, TEMA.fundo, TEMA.fundo_alt)


def caixa_selecao(tela, rect, marcado, cor=None, raio=RAIO_SM):
    """Checkbox do design system."""
    rect = pygame.Rect(rect)
    acento = cor or TEMA.acento
    if marcado:
        pygame.draw.rect(tela, rgb(acento), rect, border_radius=raio)
        cx, cy = rect.center
        pygame.draw.lines(tela, (255, 255, 255), False, [
            (cx - 6, cy), (cx - 2, cy + 4), (cx + 6, cy - 5)], 3)
    else:
        superficie_translucida(tela, rect, TEMA.superficie_alt, 230, raio,
                               TEMA.borda, 2)
    return rect


def amostra_cor(tela, rect, cor, selecionado=False, raio=RAIO_MD):
    """Quadrado de cor clicavel (paletas e color pickers)."""
    rect = pygame.Rect(rect)
    pygame.draw.rect(tela, rgb(cor), rect, border_radius=raio)
    borda = TEMA.acento if selecionado else TEMA.borda
    pygame.draw.rect(tela, rgb(borda), rect, width=3 if selecionado else 1,
                     border_radius=raio)
    return rect


def cartao_vazio(tela, rect, mensagem, fonte, icone=''):
    """Estado vazio padronizado (listas sem resultado)."""
    rect = pygame.Rect(rect)
    superficie_translucida(tela, rect, TEMA.superficie_alt, 120, RAIO_LG,
                           TEMA.borda, 1)
    texto_centralizado(tela, f'{icone} {mensagem}'.strip(), fonte, rect,
                       TEMA.texto_apagado)
    return rect


import sys as _sys
ds = _sys.modules[__name__]
