# -*- coding: utf-8 -*-
"""
Painel CAGED: os cinco shapes maiores, posicionados na tonalidade ativa.

Cada shape guarda as posicoes relativas (corda, casa, grau) e a corda onde fica
a tonica. A casa base e calculada a partir da tonica escolhida no campo
harmonico, entao o mini-braco mostra o shape no lugar certo do instrumento.
"""
import pygame

from config.design_system import TEMA, ds
from core.i18n import _t

NOTAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
# Afinacao padrao de referencia, da corda mais grave para a mais aguda
CORDAS_SOLTAS = ['E', 'A', 'D', 'G', 'B', 'E']

GRAU_TONICA, GRAU_TERCA, GRAU_QUINTA = 'R', '3', '5'

# (corda 0=Mi grave .. 5=Mi agudo, casa relativa, grau)
SHAPES = [
    {
        'nome': 'C', 'corda_tonica': 1, 'casa_tonica': 3,
        'descricao': 'Tonica na quinta corda, dedilhado aberto',
        'dificuldade': 'Iniciante',
        'notas': [(1, 3, GRAU_TONICA), (2, 2, GRAU_QUINTA), (3, 0, GRAU_TONICA),
                  (4, 1, GRAU_TERCA), (5, 0, GRAU_QUINTA)],
    },
    {
        'nome': 'A', 'corda_tonica': 1, 'casa_tonica': 0,
        'descricao': 'Pestana com tonica na quinta corda',
        'dificuldade': 'Intermediario',
        'notas': [(1, 0, GRAU_TONICA), (2, 2, GRAU_QUINTA), (3, 2, GRAU_TONICA),
                  (4, 2, GRAU_TERCA), (5, 0, GRAU_QUINTA)],
    },
    {
        'nome': 'G', 'corda_tonica': 0, 'casa_tonica': 3,
        'descricao': 'Tonica na sexta corda, extensao larga',
        'dificuldade': 'Avancado',
        'notas': [(0, 3, GRAU_TONICA), (1, 2, GRAU_QUINTA), (2, 0, GRAU_TONICA),
                  (3, 0, GRAU_TERCA), (4, 0, GRAU_QUINTA), (5, 3, GRAU_TONICA)],
    },
    {
        'nome': 'E', 'corda_tonica': 0, 'casa_tonica': 0,
        'descricao': 'Pestana com tonica na sexta corda',
        'dificuldade': 'Iniciante',
        'notas': [(0, 0, GRAU_TONICA), (1, 2, GRAU_QUINTA), (2, 2, GRAU_TONICA),
                  (3, 1, GRAU_TERCA), (4, 0, GRAU_QUINTA), (5, 0, GRAU_TONICA)],
    },
    {
        'nome': 'D', 'corda_tonica': 2, 'casa_tonica': 0,
        'descricao': 'Tonica na quarta corda, tres primeiras cordas',
        'dificuldade': 'Intermediario',
        'notas': [(2, 0, GRAU_TONICA), (3, 2, GRAU_QUINTA), (4, 3, GRAU_TONICA),
                  (5, 2, GRAU_TERCA)],
    },
]


def _semitons(de, para):
    """Distancia em semitons entre duas notas, de 0 a 11."""
    try:
        return (NOTAS.index(para) - NOTAS.index(de)) % 12
    except ValueError:
        return 0


class PainelCAGED:
    """
        Como funciona: Mantem o shape selecionado e desenha a lista de shapes,
        o mini-braco do shape ativo, a informacao do acorde e os sete modos.
        Para que serve: Estudar o sistema CAGED na tonalidade em uso.
        Onde e usada: Aba inferior ACORDES > CAGED.
    """

    def __init__(self):
        self.indice = 3  # shape de E, o mais comum para comecar
        self.rects_shapes = []
        self.rects_modos = []
        self._cache_fontes = {}

    # ------------------------------------------------------------- calculos
    def _fonte(self, tamanho):
        if tamanho not in self._cache_fontes:
            self._cache_fontes[tamanho] = pygame.font.SysFont('Arial', tamanho, bold=True)
        return self._cache_fontes[tamanho]

    def shape_atual(self):
        return SHAPES[self.indice % len(SHAPES)]

    def casa_base(self, tonica, shape=None):
        """Primeira casa do shape para a tonica informada."""
        shape = shape or self.shape_atual()
        corda_solta = CORDAS_SOLTAS[shape['corda_tonica']]
        casa_da_tonica = _semitons(corda_solta, tonica)
        base = casa_da_tonica - shape['casa_tonica']
        return base + 12 if base < 0 else base

    def notas_do_acorde(self, tonica):
        """Devolve (tonica, terca maior, quinta justa) da tonalidade."""
        idx = NOTAS.index(tonica) if tonica in NOTAS else 0
        return [NOTAS[idx], NOTAS[(idx + 4) % 12], NOTAS[(idx + 7) % 12]]

    def _cor_grau(self, grau):
        return {GRAU_TONICA: TEMA.acento, GRAU_TERCA: TEMA.verde,
                GRAU_QUINTA: TEMA.ciano}.get(grau, TEMA.texto_suave)

    # -------------------------------------------------------------- desenho
    def _desenhar_lista(self, tela, rect, fontes, tonica):
        """Coluna esquerda: os cinco shapes como cartoes selecionaveis."""
        ds.rotulo_secao(tela, rect.x, rect.y, _t('Shapes CAGED'), fontes['pequena'],
                        TEMA.acento, largura_max=rect.width)
        y = rect.y + fontes['pequena'].get_height() + ds.ESPACO_SM

        self.rects_shapes = []
        altura = max(46, (rect.bottom - y - ds.ESPACO_SM * 4) // len(SHAPES))
        for i, shape in enumerate(SHAPES):
            card = pygame.Rect(rect.x, y, rect.width, altura)
            self.rects_shapes.append(card)
            ativo = i == self.indice
            base = self.casa_base(tonica, shape)

            if ativo:
                ds.superficie_translucida(tela, card,
                                          ds.misturar(TEMA.superficie_alt, TEMA.acento, 0.28),
                                          235, ds.RAIO_MD, TEMA.acento, 1)
            else:
                ds.superficie_translucida(tela, card, TEMA.superficie_alt, 200,
                                          ds.RAIO_MD, TEMA.borda, 1)
            pygame.draw.rect(tela, ds.rgb(TEMA.acento if ativo else TEMA.borda),
                             (card.x, card.y + 4, 3, card.height - 8),
                             border_radius=2)

            titulo = f"{_t('Shape')} {shape['nome']}  -  {_t('casa')} {base}"
            ds.texto_em(tela, titulo, fontes['pequena'],
                        (card.x + ds.ESPACO_MD, card.y + ds.ESPACO_SM),
                        TEMA.texto if ativo else TEMA.texto_suave,
                        largura_max=card.width - ds.ESPACO_LG)
            if altura >= 42:
                ds.texto_em(tela, _t(shape['descricao']), self._fonte(11),
                            (card.x + ds.ESPACO_MD,
                             card.y + ds.ESPACO_SM + fontes['pequena'].get_height() + 2),
                            TEMA.texto_apagado, largura_max=card.width - ds.ESPACO_LG)
            y += altura + ds.ESPACO_SM

    def _desenhar_braco(self, tela, rect, fontes, tonica):
        """Mini-braco com o shape ativo desenhado casa a casa."""
        shape = self.shape_atual()
        base = self.casa_base(tonica, shape)
        casas_shape = max(c for _, c, _ in shape['notas']) + 1
        num_casas = max(5, casas_shape + 1)

        ds.superficie_translucida(tela, rect, TEMA.fundo, 170, ds.RAIO_MD,
                                  TEMA.borda, 1)

        margem = ds.ESPACO_LG
        area = pygame.Rect(rect.x + margem, rect.y + margem,
                           rect.width - margem * 2, rect.height - margem * 2 - 14)
        if area.width < 40 or area.height < 40:
            return

        largura_casa = area.width / num_casas
        altura_corda = area.height / 5

        # trastes
        for c in range(num_casas + 1):
            x = area.x + c * largura_casa
            largura_linha = 3 if (base == 0 and c == 0) else 1
            pygame.draw.line(tela, ds.rgb(TEMA.traste), (x, area.y),
                             (x, area.bottom), largura_linha)
            if c < num_casas:
                ds.texto_em(tela, str(base + c), self._fonte(10),
                            (x + largura_casa / 2, area.bottom + 3),
                            TEMA.texto_apagado, ancora='midtop')

        # cordas
        for i in range(6):
            y = area.y + i * altura_corda
            pygame.draw.line(tela, ds.rgb(TEMA.corda), (area.x, y),
                             (area.right, y), 1 + (5 - i) // 3)

        # notas do shape (corda 0 = grave, desenhada embaixo)
        raio = int(min(largura_casa, altura_corda) * 0.38)
        raio = max(7, min(15, raio))
        for corda, casa_rel, grau in shape['notas']:
            cx = area.x + casa_rel * largura_casa + largura_casa / 2
            cy = area.y + (5 - corda) * altura_corda
            cor = self._cor_grau(grau)
            pygame.draw.circle(tela, ds.rgb(cor), (int(cx), int(cy)), raio)
            pygame.draw.circle(tela, ds.rgb(ds.escurecer(cor, 0.4)),
                               (int(cx), int(cy)), raio, 1)
            ds.texto_em(tela, grau, self._fonte(max(9, raio)),
                        (int(cx), int(cy)), ds.contraste_texto(cor), ancora='center')

    def _desenhar_info(self, tela, rect, fontes, tonica):
        """Bloco com nome, notas, intervalos e dificuldade do shape ativo."""
        shape = self.shape_atual()
        notas = self.notas_do_acorde(tonica)
        ds.superficie_translucida(tela, rect,
                                  ds.misturar(TEMA.superficie, TEMA.acento, 0.10),
                                  225, ds.RAIO_MD, TEMA.acento, 1)

        pad = ds.ESPACO_MD
        y = rect.y + ds.ESPACO_SM
        linhas = [
            (_t('Acorde'), f'{tonica} {_t("Maior")}'),
            (_t('Notas'), ' - '.join(notas)),
            (_t('Intervalos'), f'{_t("Tonica")} - {_t("Terca maior")} - {_t("Quinta justa")}'),
            (_t('Dificuldade'), _t(shape['dificuldade'])),
            (_t('Casa inicial'), str(self.casa_base(tonica))),
        ]
        passo = max(14, (rect.height - ds.ESPACO_SM * 2) // len(linhas))
        for rotulo, valor in linhas:
            if y + passo > rect.bottom:
                break
            ds.texto_em(tela, rotulo, self._fonte(11), (rect.x + pad, y),
                        TEMA.texto_apagado, largura_max=rect.width // 2)
            ds.texto_em(tela, valor, self._fonte(12), (rect.right - pad, y),
                        TEMA.texto, ancora='topright',
                        largura_max=rect.width * 2 // 3)
            y += passo

    def _desenhar_modos(self, tela, rect, fontes, campo_harmonico):
        """Fileira com os sete modos gregos do campo harmonico."""
        self.rects_modos = []
        escalas = campo_harmonico.escalas_campo
        gap = ds.ESPACO_XS
        largura = (rect.width - gap * (len(escalas) - 1)) / len(escalas)
        for i, escala in enumerate(escalas):
            r = pygame.Rect(int(rect.x + i * (largura + gap)), rect.y,
                            int(largura), rect.height)
            self.rects_modos.append(r)
            ds.chip(tela, r, _t(escala['nome']), self._fonte(11),
                    ativo=campo_harmonico.indice_escala_campo == i)

    def desenhar(self, tela, rect, fontes, campo_harmonico):
        """
            Como funciona: Divide a area em coluna de shapes a esquerda e
            braco + informacoes a direita, com os modos numa faixa embaixo.
            Para que serve: Tela principal de estudo do sistema CAGED.
            Onde e usada: Chamada pelo painel inferior na aba ACORDES > CAGED.
        """
        tonica = getattr(campo_harmonico, 'tonica_campo', 'C')

        altura_modos = 26
        area = pygame.Rect(rect.x, rect.y, rect.width,
                           rect.height - altura_modos - ds.ESPACO_MD)

        largura_esq = max(180, int(area.width * 0.34))
        col_esq = pygame.Rect(area.x, area.y, largura_esq, area.height)
        col_dir = pygame.Rect(area.x + largura_esq + ds.ESPACO_LG, area.y,
                              area.width - largura_esq - ds.ESPACO_LG, area.height)

        self._desenhar_lista(tela, col_esq, fontes, tonica)

        ds.rotulo_secao(tela, col_dir.x, col_dir.y,
                        f"{_t('Shape')} {self.shape_atual()['nome']} - {tonica}",
                        fontes['pequena'], TEMA.acento, largura_max=col_dir.width)
        y_dir = col_dir.y + fontes['pequena'].get_height() + ds.ESPACO_SM

        altura_info = min(96, max(70, int(col_dir.height * 0.38)))
        rect_braco = pygame.Rect(col_dir.x, y_dir, col_dir.width,
                                 col_dir.bottom - y_dir - altura_info - ds.ESPACO_SM)
        if rect_braco.height > 60:
            self._desenhar_braco(tela, rect_braco, fontes, tonica)
            rect_info = pygame.Rect(col_dir.x, rect_braco.bottom + ds.ESPACO_SM,
                                    col_dir.width, altura_info)
        else:
            rect_info = pygame.Rect(col_dir.x, y_dir, col_dir.width,
                                    col_dir.bottom - y_dir)
        self._desenhar_info(tela, rect_info, fontes, tonica)

        self._desenhar_modos(
            tela, pygame.Rect(rect.x, rect.bottom - altura_modos, rect.width,
                              altura_modos), fontes, campo_harmonico)

    # --------------------------------------------------------------- clique
    def tratar_clique(self, pos, campo_harmonico):
        """
            Como funciona: Testa os cartoes de shape e os botoes de modo.
            Para que serve: Trocar o shape estudado e o modo do campo harmonico.
            Onde e usada: Chamada pelo controlador de eventos.
        """
        for i, rect in enumerate(self.rects_shapes):
            if rect.collidepoint(pos):
                self.indice = i
                return True
        for i, rect in enumerate(self.rects_modos):
            if rect.collidepoint(pos):
                campo_harmonico.indice_escala_campo = i
                campo_harmonico.tipo_escala = campo_harmonico.escalas_campo[i]['nome']
                if campo_harmonico.indice_acorde_selecionado != -1:
                    campo_harmonico.calcular_notas_acorde_selecionado()
                return True
        return False


# Instancia unica compartilhada entre o renderizador e o controlador de eventos
painel_caged = PainelCAGED()
