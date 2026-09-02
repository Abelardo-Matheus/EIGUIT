# -*- coding: utf-8 -*-
"""
Painel de acordes no braco.

Duas leituras do mesmo assunto:

- Familia CAGED: os cinco shapes maiores, cada um numa janela de casas
  calculada para a tonica escolhida.
- Demais familias (triades, setimas, power chords): todas as posicoes do
  acorde no braco inteiro, sem janela.

Qualquer acorde pode ser FIXADO no braco. Os fixados ficam desenhados por
cima do braco principal, cada um com sua cor, o que permite comparar duas
sonoridades na mesma regiao.
"""
import pygame

from config.design_system import TEMA, ds
from core.i18n import _t

NOTAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
CORDAS_SOLTAS = ['E', 'A', 'D', 'G', 'B', 'E']

# Tipos de acorde: intervalos em semitons a partir da tonica e o grau de cada um
TIPOS_ACORDE = {
    'maior':  {'nome': 'Maior',         'sufixo': '',     'int': [0, 4, 7],        'graus': ['R', '3', '5']},
    'menor':  {'nome': 'Menor',         'sufixo': 'm',    'int': [0, 3, 7],        'graus': ['R', 'b3', '5']},
    'dim':    {'nome': 'Diminuto',      'sufixo': 'dim',  'int': [0, 3, 6],        'graus': ['R', 'b3', 'b5']},
    'aum':    {'nome': 'Aumentado',     'sufixo': 'aug',  'int': [0, 4, 8],        'graus': ['R', '3', '#5']},
    'sus2':   {'nome': 'Suspenso 2',    'sufixo': 'sus2', 'int': [0, 2, 7],        'graus': ['R', '2', '5']},
    'sus4':   {'nome': 'Suspenso 4',    'sufixo': 'sus4', 'int': [0, 5, 7],        'graus': ['R', '4', '5']},
    '6':      {'nome': 'Sexta',         'sufixo': '6',    'int': [0, 4, 7, 9],     'graus': ['R', '3', '5', '6']},
    'm6':     {'nome': 'Menor com 6',   'sufixo': 'm6',   'int': [0, 3, 7, 9],     'graus': ['R', 'b3', '5', '6']},
    '7':      {'nome': 'Dominante 7',   'sufixo': '7',    'int': [0, 4, 7, 10],    'graus': ['R', '3', '5', 'b7']},
    'maj7':   {'nome': 'Maior 7',       'sufixo': 'maj7', 'int': [0, 4, 7, 11],    'graus': ['R', '3', '5', '7']},
    'm7':     {'nome': 'Menor 7',       'sufixo': 'm7',   'int': [0, 3, 7, 10],    'graus': ['R', 'b3', '5', 'b7']},
    'm7b5':   {'nome': 'Meio diminuto', 'sufixo': 'm7b5', 'int': [0, 3, 6, 10],    'graus': ['R', 'b3', 'b5', 'b7']},
    'dim7':   {'nome': 'Diminuto 7',    'sufixo': 'dim7', 'int': [0, 3, 6, 9],     'graus': ['R', 'b3', 'b5', 'bb7']},
    '9':      {'nome': 'Nona',          'sufixo': '9',    'int': [0, 4, 7, 10, 2], 'graus': ['R', '3', '5', 'b7', '9']},
    'power':  {'nome': 'Power chord',   'sufixo': '5',    'int': [0, 7],           'graus': ['R', '5']},
    'power8': {'nome': 'Power + oitava','sufixo': '5(8)', 'int': [0, 7],           'graus': ['R', '5']},
}

# Cada sub-aba de ACORDES aponta para uma familia
FAMILIAS = {
    'caged': {'nome': 'CAGED', 'tipos': ['maior'], 'usa_shapes': True},
    'triades_maior': {'nome': 'Triades maiores',
                      'tipos': ['maior', 'sus2', 'sus4', 'aum', '6'], 'usa_shapes': False},
    'triades_menor': {'nome': 'Triades menores',
                      'tipos': ['menor', 'dim', 'm6'], 'usa_shapes': False},
    'setimas': {'nome': 'Setimas',
                'tipos': ['7', 'maj7', 'm7', 'm7b5', 'dim7', '9'], 'usa_shapes': False},
    'power': {'nome': 'Power chords', 'tipos': ['power', 'power8'], 'usa_shapes': False},
}

# Shapes CAGED maiores: (corda 0=Mi grave .. 5=Mi agudo, casa relativa, grau)
SHAPES = [
    {'nome': 'C', 'corda_tonica': 1, 'casa_tonica': 3,
     'descricao': 'Tonica na quinta corda, dedilhado aberto', 'dificuldade': 'Iniciante',
     'notas': [(1, 3, 'R'), (2, 2, '5'), (3, 0, 'R'), (4, 1, '3'), (5, 0, '5')]},
    {'nome': 'A', 'corda_tonica': 1, 'casa_tonica': 0,
     'descricao': 'Pestana com tonica na quinta corda', 'dificuldade': 'Intermediario',
     'notas': [(1, 0, 'R'), (2, 2, '5'), (3, 2, 'R'), (4, 2, '3'), (5, 0, '5')]},
    {'nome': 'G', 'corda_tonica': 0, 'casa_tonica': 3,
     'descricao': 'Tonica na sexta corda, extensao larga', 'dificuldade': 'Avancado',
     'notas': [(0, 3, 'R'), (1, 2, '5'), (2, 0, 'R'), (3, 0, '3'), (4, 0, '5'), (5, 3, 'R')]},
    {'nome': 'E', 'corda_tonica': 0, 'casa_tonica': 0,
     'descricao': 'Pestana com tonica na sexta corda', 'dificuldade': 'Iniciante',
     'notas': [(0, 0, 'R'), (1, 2, '5'), (2, 2, 'R'), (3, 1, '3'), (4, 0, '5'), (5, 0, 'R')]},
    {'nome': 'D', 'corda_tonica': 2, 'casa_tonica': 0,
     'descricao': 'Tonica na quarta corda, cordas agudas', 'dificuldade': 'Intermediario',
     'notas': [(2, 0, 'R'), (3, 2, '5'), (4, 3, 'R'), (5, 2, '3')]},
]

# Cores usadas quando varios acordes ficam fixados ao mesmo tempo
CORES_FIXADOS = [
    (0, 120, 215), (255, 107, 107), (78, 205, 196),
    (255, 217, 61), (155, 122, 255), (0, 212, 255),
]
MAX_FIXADOS = 4


def semitons(de, para):
    """Distancia em semitons entre duas notas, de 0 a 11."""
    try:
        return (NOTAS.index(para) - NOTAS.index(de)) % 12
    except ValueError:
        return 0


def notas_do_acorde(tonica, chave_tipo):
    """Devolve {nome_da_nota: grau} para o acorde pedido."""
    tipo = TIPOS_ACORDE[chave_tipo]
    idx = NOTAS.index(tonica) if tonica in NOTAS else 0
    mapa = {}
    for intervalo, grau in zip(tipo['int'], tipo['graus']):
        mapa.setdefault(NOTAS[(idx + intervalo) % 12], grau)
    return mapa


def nome_do_acorde(tonica, chave_tipo):
    """Cifra do acorde, por exemplo C, Am7, G5."""
    return f"{tonica}{TIPOS_ACORDE[chave_tipo]['sufixo']}"


class PainelAcordes:
    """
        Como funciona: Mostra os acordes de uma familia, deixa escolher a
        tonica entre as doze notas e projeta o resultado no braco principal,
        com a opcao de fixar varios acordes ao mesmo tempo.
        Para que serve: Estudar formas de acorde no braco inteiro.
        Onde e usada: Sub-abas da aba ACORDES.
    """

    LARGURA_JANELA = 4   # casas cobertas por um shape CAGED

    def __init__(self, familia='caged'):
        self.familia = familia
        self.indice_shape = 3          # shape de E
        self.indice_tipo = 0
        self.tonica = 'C'
        self.mostrar_no_braco = True

        self.rects_itens = []
        self.rects_tonicas = []
        self.rects_fixados = []
        self.rect_btn_projetar = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_fixar = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_limpar = pygame.Rect(0, 0, 0, 0)

        self.estado_ref = None
        self._cache_fontes = {}

    # ------------------------------------------------------------ auxiliares
    def _fonte(self, tamanho):
        if tamanho not in self._cache_fontes:
            self._cache_fontes[tamanho] = pygame.font.SysFont('Arial', tamanho, bold=True)
        return self._cache_fontes[tamanho]

    @property
    def config_familia(self):
        return FAMILIAS.get(self.familia, FAMILIAS['caged'])

    @property
    def usa_shapes(self):
        return self.config_familia['usa_shapes']

    @property
    def tipo_atual(self):
        tipos = self.config_familia['tipos']
        return tipos[self.indice_tipo % len(tipos)]

    def shape_atual(self):
        return SHAPES[self.indice_shape % len(SHAPES)]

    def casa_base(self, tonica=None, shape=None):
        """Primeira casa do shape CAGED para a tonica informada."""
        tonica = tonica or self.tonica
        shape = shape or self.shape_atual()
        casa = semitons(CORDAS_SOLTAS[shape['corda_tonica']], tonica)
        base = casa - shape['casa_tonica']
        return base + 12 if base < 0 else base

    def _cor_grau(self, grau):
        if grau == 'R':
            return TEMA.acento
        if grau in ('3', 'b3'):
            return TEMA.verde
        if grau in ('5', 'b5', '#5'):
            return TEMA.ciano
        return TEMA.aviso

    # ----------------------------------------------------- estado do braco
    def _descricao_atual(self):
        """Monta o dicionario que o braco principal usa para filtrar."""
        tipo = self.tipo_atual
        janela = None
        rotulo = nome_do_acorde(self.tonica, tipo)
        if self.usa_shapes:
            base = self.casa_base()
            janela = (base, base + self.LARGURA_JANELA)
            rotulo = f"{rotulo} ({self.shape_atual()['nome']})"
        return {'rotulo': rotulo, 'notas': notas_do_acorde(self.tonica, tipo),
                'janela': janela, 'cor': tuple(TEMA.acento), 'fixado': False}

    def aplicar_no_estado(self, estado=None):
        """
            Como funciona: Publica no estado a lista de acordes desenhados no
            braco: os fixados mais a selecao atual, quando projetada.
            Para que serve: O braco principal so le essa lista.
            Onde e usada: A cada desenho e a cada clique do painel.
        """
        estado = estado or self.estado_ref
        if estado is None:
            return
        fixados = list(getattr(estado, 'acordes_fixados', []))
        lista = list(fixados)
        if self.mostrar_no_braco:
            atual = self._descricao_atual()
            if not any(f['rotulo'] == atual['rotulo'] for f in fixados):
                lista.append(atual)
        estado.acordes_no_braco = lista

    def fixar_atual(self, estado=None):
        """Guarda o acorde atual para continuar aparecendo no braco."""
        estado = estado or self.estado_ref
        if estado is None:
            return False
        fixados = getattr(estado, 'acordes_fixados', None)
        if fixados is None:
            fixados = []
            estado.acordes_fixados = fixados
        atual = self._descricao_atual()
        if any(f['rotulo'] == atual['rotulo'] for f in fixados):
            return False
        if len(fixados) >= MAX_FIXADOS:
            fixados.pop(0)
        atual['fixado'] = True
        atual['cor'] = CORES_FIXADOS[len(fixados) % len(CORES_FIXADOS)]
        fixados.append(atual)
        self.aplicar_no_estado(estado)
        return True

    def limpar_fixados(self, estado=None):
        """Tira todos os acordes fixados do braco."""
        estado = estado or self.estado_ref
        if estado is not None:
            estado.acordes_fixados = []
            self.aplicar_no_estado(estado)

    # ---------------------------------------------------------- desenho ---
    def _desenhar_lista(self, tela, rect, fontes):
        """Coluna esquerda: shapes CAGED ou tipos de acorde da familia."""
        titulo = _t('Shapes CAGED') if self.usa_shapes else _t('Tipos de acorde')
        ds.rotulo_secao(tela, rect.x, rect.y, titulo, fontes['pequena'],
                        TEMA.acento, largura_max=rect.width)
        y = rect.y + fontes['pequena'].get_height() + ds.ESPACO_SM

        if self.usa_shapes:
            itens = [(s['nome'], f"{_t('casa')} {self.casa_base(shape=s)}",
                      _t(s['descricao'])) for s in SHAPES]
            selecionado = self.indice_shape % len(SHAPES)
        else:
            tipos = self.config_familia['tipos']
            itens = [(nome_do_acorde(self.tonica, t), _t(TIPOS_ACORDE[t]['nome']),
                      ' · '.join(TIPOS_ACORDE[t]['graus'])) for t in tipos]
            selecionado = self.indice_tipo % len(tipos)

        self.rects_itens = []
        disponivel = max(20, rect.bottom - y)
        altura = max(20, (disponivel - ds.ESPACO_SM * (len(itens) - 1)) // max(1, len(itens)))
        altura = min(altura, 56)

        for i, (titulo_item, subtitulo, detalhe) in enumerate(itens):
            if y + altura > rect.bottom:
                break
            card = pygame.Rect(rect.x, y, rect.width, altura)
            self.rects_itens.append(card)
            ativo = i == selecionado
            if ativo:
                ds.superficie_translucida(
                    tela, card, ds.misturar(TEMA.superficie_alt, TEMA.acento, 0.28),
                    235, ds.RAIO_MD, TEMA.acento, 1)
            else:
                ds.superficie_translucida(tela, card, TEMA.superficie_alt, 200,
                                          ds.RAIO_MD, TEMA.borda, 1)
            pygame.draw.rect(tela, ds.rgb(TEMA.acento if ativo else TEMA.borda),
                             (card.x, card.y + 4, 3, card.height - 8), border_radius=2)
            ds.texto_em(tela, f'{titulo_item}  -  {subtitulo}', fontes['pequena'],
                        (card.x + ds.ESPACO_MD, card.y + ds.ESPACO_SM),
                        TEMA.texto if ativo else TEMA.texto_suave,
                        largura_max=card.width - ds.ESPACO_LG)
            if altura >= 40:
                ds.texto_em(tela, detalhe, self._fonte(11),
                            (card.x + ds.ESPACO_MD,
                             card.y + ds.ESPACO_SM + fontes['pequena'].get_height() + 2),
                            TEMA.texto_apagado, largura_max=card.width - ds.ESPACO_LG)
            y += altura + ds.ESPACO_SM

    def _posicoes_no_braco(self):
        """(corda, casa, grau) do que sera desenhado no mini-braco."""
        if self.usa_shapes:
            shape = self.shape_atual()
            num_casas = max(5, max(c for _, c, _ in shape['notas']) + 2)
            return self.casa_base(), num_casas, list(shape['notas'])

        num_casas = 13
        mapa = notas_do_acorde(self.tonica, self.tipo_atual)
        posicoes = []
        for corda in range(6):
            solta = CORDAS_SOLTAS[corda]
            for casa in range(num_casas):
                nome = NOTAS[(NOTAS.index(solta) + casa) % 12]
                grau = mapa.get(nome)
                if grau:
                    posicoes.append((corda, casa, grau))
        return 0, num_casas, posicoes

    def _desenhar_braco(self, tela, rect, fontes):
        """Mini-braco: shape CAGED ou o acorde inteiro ao longo das casas."""
        ds.superficie_translucida(tela, rect, TEMA.fundo, 170, ds.RAIO_MD, TEMA.borda, 1)
        margem_x, margem_y = ds.ESPACO_MD, ds.ESPACO_SM
        altura_num = 13 if rect.height >= 74 else 0
        area = pygame.Rect(rect.x + margem_x, rect.y + margem_y,
                           rect.width - margem_x * 2,
                           rect.height - margem_y * 2 - altura_num)
        if area.width < 40 or area.height < 26:
            ds.texto_centralizado(tela, _t('Amplie o painel'), self._fonte(11),
                                  rect, TEMA.texto_apagado)
            return

        base, num_casas, posicoes = self._posicoes_no_braco()
        largura_casa = area.width / num_casas
        altura_corda = area.height / 5

        for c in range(num_casas + 1):
            x = area.x + c * largura_casa
            pygame.draw.line(tela, ds.rgb(TEMA.traste), (x, area.y), (x, area.bottom),
                             3 if (base == 0 and c == 0) else 1)
            if c < num_casas and altura_num:
                ds.texto_em(tela, str(base + c), self._fonte(10),
                            (x + largura_casa / 2, area.bottom + 2),
                            TEMA.texto_apagado, ancora='midtop')

        for i in range(6):
            y = area.y + i * altura_corda
            pygame.draw.line(tela, ds.rgb(TEMA.corda), (area.x, y), (area.right, y),
                             1 + (5 - i) // 3)

        raio = max(6, min(15, int(min(largura_casa, altura_corda) * 0.38)))
        for corda, casa, grau in posicoes:
            cx = area.x + casa * largura_casa + largura_casa / 2
            cy = area.y + (5 - corda) * altura_corda
            cor = self._cor_grau(grau)
            pygame.draw.circle(tela, ds.rgb(cor), (int(cx), int(cy)), raio)
            pygame.draw.circle(tela, ds.rgb(ds.escurecer(cor, 0.4)),
                               (int(cx), int(cy)), raio, 1)
            if raio >= 9:
                ds.texto_em(tela, grau, self._fonte(max(9, raio - 1)),
                            (int(cx), int(cy)), ds.contraste_texto(cor), ancora='center')

    def _desenhar_info(self, tela, rect, fontes, empilhado=False):
        """Nome, notas, graus e, no CAGED, a casa inicial."""
        tipo = TIPOS_ACORDE[self.tipo_atual]
        mapa = notas_do_acorde(self.tonica, self.tipo_atual)
        ds.superficie_translucida(tela, rect,
                                  ds.misturar(TEMA.superficie, TEMA.acento, 0.10),
                                  225, ds.RAIO_MD, TEMA.acento, 1)
        pad = ds.ESPACO_MD
        y = rect.y + ds.ESPACO_SM

        linhas = [
            (_t('Acorde'), f'{nome_do_acorde(self.tonica, self.tipo_atual)}'),
            (_t('Tipo'), _t(tipo['nome'])),
            (_t('Notas'), ' - '.join(mapa.keys())),
            (_t('Graus'), ' - '.join(tipo['graus'])),
        ]
        if self.usa_shapes:
            linhas.append((_t('Casa inicial'), str(self.casa_base())))
            linhas.append((_t('Dificuldade'), _t(self.shape_atual()['dificuldade'])))

        alt_rotulo = self._fonte(11).get_height()
        alt_valor = self._fonte(12).get_height()
        altura_linha = (alt_rotulo + alt_valor + 3) if empilhado else (alt_valor + 2)
        cabem = max(1, (rect.height - ds.ESPACO_SM) // altura_linha)
        linhas = linhas[:cabem]
        passo = max(altura_linha, (rect.height - ds.ESPACO_SM) // len(linhas))

        for rotulo, valor in linhas:
            if y + altura_linha > rect.bottom + 2:
                break
            if empilhado:
                ds.texto_em(tela, rotulo, self._fonte(11), (rect.x + pad, y),
                            TEMA.texto_apagado, largura_max=rect.width - pad * 2)
                ds.texto_em(tela, valor, self._fonte(12), (rect.x + pad, y + alt_rotulo + 1),
                            TEMA.texto, largura_max=rect.width - pad * 2)
            else:
                ds.texto_em(tela, rotulo, self._fonte(11), (rect.x + pad, y),
                            TEMA.texto_apagado, largura_max=rect.width // 2)
                ds.texto_em(tela, valor, self._fonte(12), (rect.right - pad, y),
                            TEMA.texto, ancora='topright', largura_max=rect.width * 2 // 3)
            y += passo

    def _desenhar_barra(self, tela, rect, fontes, estado):
        """Tonicas, botoes de projetar/fixar/limpar e a lista de fixados."""
        pos_mouse = pygame.mouse.get_pos()
        altura = rect.height

        largura_btn = min(112, max(78, int(rect.width * 0.11)))
        x_dir = rect.right
        self.rect_btn_limpar = pygame.Rect(x_dir - largura_btn, rect.y, largura_btn, altura)
        x_dir -= largura_btn + ds.ESPACO_XS
        self.rect_btn_fixar = pygame.Rect(x_dir - largura_btn, rect.y, largura_btn, altura)
        x_dir -= largura_btn + ds.ESPACO_XS
        self.rect_btn_projetar = pygame.Rect(x_dir - largura_btn, rect.y, largura_btn, altura)
        x_dir -= largura_btn + ds.ESPACO_SM

        ds.botao(tela, self.rect_btn_projetar,
                 _t('No braco') if self.mostrar_no_braco else _t('Oculto'),
                 self._fonte(11),
                 variante='primario' if self.mostrar_no_braco else 'secundario',
                 hover=self.rect_btn_projetar.collidepoint(pos_mouse))
        ds.botao(tela, self.rect_btn_fixar, _t('Fixar'), self._fonte(11),
                 variante='suave', hover=self.rect_btn_fixar.collidepoint(pos_mouse))

        fixados = getattr(estado, 'acordes_fixados', []) if estado else []
        ds.botao(tela, self.rect_btn_limpar, _t('Limpar'), self._fonte(11),
                 variante='secundario', habilitado=bool(fixados),
                 hover=self.rect_btn_limpar.collidepoint(pos_mouse))

        # Chips dos acordes fixados: clicar remove
        self.rects_fixados = []
        if fixados:
            largura_chip = min(96, max(58, int(rect.width * 0.09)))
            for i, fixo in enumerate(fixados):
                chip = pygame.Rect(x_dir - largura_chip, rect.y, largura_chip, altura)
                if chip.x < rect.x:
                    break
                self.rects_fixados.append((chip, i))
                ds.superficie_translucida(tela, chip, fixo['cor'], 90, ds.RAIO_PILULA,
                                          fixo['cor'], 1)
                ds.texto_centralizado(tela, fixo['rotulo'].split(' (')[0],
                                      self._fonte(11), chip, fixo['cor'])
                x_dir -= largura_chip + ds.ESPACO_XS

        # Seletor de tonica: as doze notas
        largura_disponivel = max(60, x_dir - rect.x - ds.ESPACO_SM)
        self.rects_tonicas = []
        largura_nota = (largura_disponivel - ds.ESPACO_XS * 11) / 12
        if largura_nota >= 15:
            for i, nota in enumerate(NOTAS):
                r = pygame.Rect(int(rect.x + i * (largura_nota + ds.ESPACO_XS)), rect.y,
                                max(14, int(largura_nota)), altura)
                self.rects_tonicas.append(r)
                ds.chip(tela, r, nota, self._fonte(11), ativo=nota == self.tonica)

    def desenhar(self, tela, rect, fontes, campo_harmonico=None, estado=None):
        """
            Como funciona: Tres colunas (lista, braco e informacao) com a barra
            de tonicas e acoes embaixo.
            Para que serve: Tela de estudo de acordes no braco.
            Onde e usada: Sub-abas da aba ACORDES do painel inferior.
        """
        if estado is not None:
            self.estado_ref = estado

        altura_barra = 26
        area = pygame.Rect(rect.x, rect.y, rect.width,
                           rect.height - altura_barra - ds.ESPACO_SM)

        tem_info = area.width >= 760
        largura_lista = max(170, int(area.width * (0.26 if tem_info else 0.34)))
        largura_info = int(area.width * 0.24) if tem_info else 0
        gap = ds.ESPACO_LG
        largura_braco = area.width - largura_lista - largura_info - gap * (2 if tem_info else 1)

        col_lista = pygame.Rect(area.x, area.y, largura_lista, area.height)
        col_braco = pygame.Rect(col_lista.right + gap, area.y, largura_braco, area.height)
        col_info = pygame.Rect(col_braco.right + gap, area.y, largura_info, area.height)

        self._desenhar_lista(tela, col_lista, fontes)

        titulo = nome_do_acorde(self.tonica, self.tipo_atual)
        if self.usa_shapes:
            titulo = f"{_t('Shape')} {self.shape_atual()['nome']} - {titulo}"
        ds.rotulo_secao(tela, col_braco.x, col_braco.y, titulo, fontes['pequena'],
                        TEMA.acento, largura_max=col_braco.width)
        y_braco = col_braco.y + fontes['pequena'].get_height() + ds.ESPACO_SM

        if tem_info:
            rect_braco = pygame.Rect(col_braco.x, y_braco, col_braco.width,
                                     col_braco.bottom - y_braco)
        else:
            alt_linha = self._fonte(12).get_height() + 2
            altura_info = min(alt_linha * 3 + ds.ESPACO_SM,
                              max(alt_linha * 2, int(col_braco.height * 0.34)))
            rect_braco = pygame.Rect(col_braco.x, y_braco, col_braco.width,
                                     col_braco.bottom - y_braco - altura_info - ds.ESPACO_SM)
            col_info = pygame.Rect(col_braco.x, rect_braco.bottom + ds.ESPACO_SM,
                                   col_braco.width, altura_info)

        if rect_braco.height >= 40:
            self._desenhar_braco(tela, rect_braco, fontes)

        if col_info.width > 60 and col_info.height > 20:
            if tem_info:
                ds.rotulo_secao(tela, col_info.x, col_info.y, _t('Acorde'),
                                fontes['pequena'], TEMA.acento, largura_max=col_info.width)
                col_info = pygame.Rect(
                    col_info.x, col_info.y + fontes['pequena'].get_height() + ds.ESPACO_SM,
                    col_info.width,
                    col_info.height - fontes['pequena'].get_height() - ds.ESPACO_SM)
            self._desenhar_info(tela, col_info, fontes, empilhado=tem_info)

        self._desenhar_barra(
            tela, pygame.Rect(rect.x, rect.bottom - altura_barra, rect.width, altura_barra),
            fontes, estado)

        self.aplicar_no_estado(estado)

    # ------------------------------------------------------------- clique --
    def tratar_clique(self, pos, campo_harmonico=None, estado=None):
        """
            Como funciona: Testa botoes, chips de fixados, tonicas e itens.
            Para que serve: Toda a interacao do painel de acordes.
            Onde e usada: Chamada pelo controlador de eventos.
        """
        estado = estado or self.estado_ref

        if self.rect_btn_projetar.collidepoint(pos):
            self.mostrar_no_braco = not self.mostrar_no_braco
            self.aplicar_no_estado(estado)
            return True
        if self.rect_btn_fixar.collidepoint(pos):
            self.fixar_atual(estado)
            return True
        if self.rect_btn_limpar.collidepoint(pos):
            self.limpar_fixados(estado)
            return True

        for chip, indice in self.rects_fixados:
            if chip.collidepoint(pos):
                fixados = getattr(estado, 'acordes_fixados', [])
                if 0 <= indice < len(fixados):
                    fixados.pop(indice)
                    self.aplicar_no_estado(estado)
                return True

        for i, r in enumerate(self.rects_tonicas):
            if r.collidepoint(pos):
                self.tonica = NOTAS[i]
                self.aplicar_no_estado(estado)
                return True

        for i, r in enumerate(self.rects_itens):
            if r.collidepoint(pos):
                if self.usa_shapes:
                    self.indice_shape = i
                else:
                    self.indice_tipo = i
                self.aplicar_no_estado(estado)
                return True
        return False


# Uma instancia por sub-aba de ACORDES, na ordem em que elas aparecem
PAINEIS = [
    PainelAcordes('caged'),
    PainelAcordes('triades_maior'),
    PainelAcordes('triades_menor'),
    PainelAcordes('setimas'),
    PainelAcordes('power'),
]


def painel_da_sub_aba(indice):
    """Devolve o painel correspondente a sub-aba de ACORDES."""
    return PAINEIS[indice] if 0 <= indice < len(PAINEIS) else PAINEIS[0]
