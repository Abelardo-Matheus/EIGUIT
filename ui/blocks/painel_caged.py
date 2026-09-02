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

    # Quantas casas o shape ocupa no braco
    LARGURA_JANELA = 4

    def __init__(self):
        self.indice = 3  # shape de E, o mais comum para comecar
        self.rects_shapes = []
        self.rects_modos = []
        self.rect_btn_projetar = pygame.Rect(0, 0, 0, 0)
        self.mostrar_no_braco = True
        self._cache_fontes = {}

    def aplicar_no_estado(self, estado, campo_harmonico):
        """
            Como funciona: Publica no estado a janela de casas do shape ativo e
            as notas do acorde com seus graus, para o braco principal filtrar.
            Para que serve: Ver o shape CAGED direto no instrumento.
            Onde e usada: Ao desenhar o painel e a cada clique nele.
        """
        tonica = getattr(campo_harmonico, 'tonica_campo', 'C')
        base = self.casa_base(tonica)
        notas = self.notas_do_acorde(tonica)
        estado.caged_janela = (base, base + self.LARGURA_JANELA)
        estado.caged_notas = {notas[0]: GRAU_TONICA, notas[1]: GRAU_TERCA,
                              notas[2]: GRAU_QUINTA}
        estado.caged_shape = self.shape_atual()['nome']
        estado.caged_ativo = self.mostrar_no_braco

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
        disponivel = max(20, rect.bottom - y)
        altura = max(20, (disponivel - ds.ESPACO_SM * (len(SHAPES) - 1)) // len(SHAPES))
        altura = min(altura, 58)
        for i, shape in enumerate(SHAPES):
            if y + altura > rect.bottom:
                break
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
            if altura >= 40 and card.bottom - card.y > fontes['pequena'].get_height() + 18:
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

        margem_x, margem_y = ds.ESPACO_MD, ds.ESPACO_SM
        altura_num = 13 if rect.height >= 74 else 0
        area = pygame.Rect(rect.x + margem_x, rect.y + margem_y,
                           rect.width - margem_x * 2,
                           rect.height - margem_y * 2 - altura_num)
        if area.width < 40 or area.height < 26:
            ds.texto_centralizado(tela, _t('Amplie o painel para ver o shape'),
                                  self._fonte(11), rect, TEMA.texto_apagado)
            return

        largura_casa = area.width / num_casas
        altura_corda = area.height / 5

        # trastes
        for c in range(num_casas + 1):
            x = area.x + c * largura_casa
            largura_linha = 3 if (base == 0 and c == 0) else 1
            pygame.draw.line(tela, ds.rgb(TEMA.traste), (x, area.y),
                             (x, area.bottom), largura_linha)
            if c < num_casas and altura_num:
                ds.texto_em(tela, str(base + c), self._fonte(10),
                            (x + largura_casa / 2, area.bottom + 2),
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

    def _desenhar_info(self, tela, rect, fontes, tonica, empilhado=False):
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
                # Coluna estreita: rotulo acima, valor embaixo
                ds.texto_em(tela, rotulo, self._fonte(11), (rect.x + pad, y),
                            TEMA.texto_apagado, largura_max=rect.width - pad * 2)
                ds.texto_em(tela, valor, self._fonte(12),
                            (rect.x + pad, y + alt_rotulo + 1), TEMA.texto,
                            largura_max=rect.width - pad * 2)
            else:
                ds.texto_em(tela, rotulo, self._fonte(11), (rect.x + pad, y),
                            TEMA.texto_apagado, largura_max=rect.width // 2)
                ds.texto_em(tela, valor, self._fonte(12), (rect.right - pad, y),
                            TEMA.texto, ancora='topright',
                            largura_max=rect.width * 2 // 3)
            y += passo

    def _desenhar_modos(self, tela, rect, fontes, campo_harmonico):
        """Fileira com os sete modos gregos e o botao de projecao no braco."""
        self.rects_modos = []
        escalas = campo_harmonico.escalas_campo

        # Botao que liga/desliga o shape no braco principal
        largura_btn = min(180, max(120, int(rect.width * 0.2)))
        self.rect_btn_projetar = pygame.Rect(rect.right - largura_btn, rect.y,
                                             largura_btn, rect.height)
        ds.botao(tela, self.rect_btn_projetar,
                 _t('No braco: ligado') if self.mostrar_no_braco
                 else _t('No braco: desligado'),
                 self._fonte(11),
                 variante='primario' if self.mostrar_no_braco else 'secundario',
                 hover=self.rect_btn_projetar.collidepoint(pygame.mouse.get_pos()))

        rect = pygame.Rect(rect.x, rect.y,
                           rect.width - largura_btn - ds.ESPACO_SM, rect.height)
        gap = ds.ESPACO_XS
        largura = (rect.width - gap * (len(escalas) - 1)) / len(escalas)
        for i, escala in enumerate(escalas):
            r = pygame.Rect(int(rect.x + i * (largura + gap)), rect.y,
                            int(largura), rect.height)
            self.rects_modos.append(r)
            ds.chip(tela, r, _t(escala['nome']), self._fonte(11),
                    ativo=campo_harmonico.indice_escala_campo == i)

    estado_ref = None

    def desenhar(self, tela, rect, fontes, campo_harmonico, estado=None):
        """
            Como funciona: Divide a area em tres colunas (shapes, braco do shape
            e informacao do acorde) com uma faixa de modos embaixo. Em painel
            estreito a coluna de informacao sai e o braco ocupa o lugar dela.
            Para que serve: Tela principal de estudo do sistema CAGED.
            Onde e usada: Chamada pelo painel inferior na aba ACORDES > CAGED.
        """
        if estado is not None:
            self.estado_ref = estado
        tonica = getattr(campo_harmonico, 'tonica_campo', 'C')

        altura_modos = 26
        area = pygame.Rect(rect.x, rect.y, rect.width,
                           rect.height - altura_modos - ds.ESPACO_SM)

        # Tres colunas: lista | braco | informacao
        tem_info = area.width >= 760
        largura_lista = max(170, int(area.width * (0.26 if tem_info else 0.34)))
        largura_info = int(area.width * 0.24) if tem_info else 0
        gap = ds.ESPACO_LG
        largura_braco = area.width - largura_lista - largura_info - gap * (2 if tem_info else 1)

        col_lista = pygame.Rect(area.x, area.y, largura_lista, area.height)
        col_braco = pygame.Rect(col_lista.right + gap, area.y, largura_braco, area.height)
        col_info = pygame.Rect(col_braco.right + gap, area.y, largura_info, area.height)

        self._desenhar_lista(tela, col_lista, fontes, tonica)

        # --- Coluna do braco ------------------------------------------------
        ds.rotulo_secao(tela, col_braco.x, col_braco.y,
                        f"{_t('Shape')} {self.shape_atual()['nome']} - {tonica}",
                        fontes['pequena'], TEMA.acento, largura_max=col_braco.width)
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
            self._desenhar_braco(tela, rect_braco, fontes, tonica)

        # --- Coluna de informacao -------------------------------------------
        if col_info.width > 60 and col_info.height > 20:
            if tem_info:
                ds.rotulo_secao(tela, col_info.x, col_info.y, _t('Acorde'),
                                fontes['pequena'], TEMA.acento,
                                largura_max=col_info.width)
                col_info = pygame.Rect(
                    col_info.x, col_info.y + fontes['pequena'].get_height() + ds.ESPACO_SM,
                    col_info.width, col_info.height - fontes['pequena'].get_height() - ds.ESPACO_SM)
            self._desenhar_info(tela, col_info, fontes, tonica, empilhado=tem_info)

        self._desenhar_modos(
            tela, pygame.Rect(rect.x, rect.bottom - altura_modos, rect.width,
                              altura_modos), fontes, campo_harmonico)

        # Mantem o braco principal em sincronia com o shape mostrado aqui
        if self.estado_ref is not None:
            self.aplicar_no_estado(self.estado_ref, campo_harmonico)

    # --------------------------------------------------------------- clique
    def tratar_clique(self, pos, campo_harmonico):
        """
            Como funciona: Testa os cartoes de shape e os botoes de modo.
            Para que serve: Trocar o shape estudado e o modo do campo harmonico.
            Onde e usada: Chamada pelo controlador de eventos.
        """
        if self.rect_btn_projetar.collidepoint(pos):
            self.mostrar_no_braco = not self.mostrar_no_braco
            if self.estado_ref is not None:
                self.aplicar_no_estado(self.estado_ref, campo_harmonico)
            return True

        for i, rect in enumerate(self.rects_shapes):
            if rect.collidepoint(pos):
                self.indice = i
                if self.estado_ref is not None:
                    self.aplicar_no_estado(self.estado_ref, campo_harmonico)
                return True
        for i, rect in enumerate(self.rects_modos):
            if rect.collidepoint(pos):
                campo_harmonico.indice_escala_campo = i
                campo_harmonico.tipo_escala = campo_harmonico.escalas_campo[i]['nome']
                if campo_harmonico.indice_acorde_selecionado != -1:
                    campo_harmonico.calcular_notas_acorde_selecionado()
                if self.estado_ref is not None:
                    self.aplicar_no_estado(self.estado_ref, campo_harmonico)
                return True
        return False


# Instancia unica compartilhada entre o renderizador e o controlador de eventos
painel_caged = PainelCAGED()
