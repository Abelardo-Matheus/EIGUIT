# -*- coding: utf-8 -*-
"""
Blocos extras do workspace.

Widgets pequenos e independentes que ficam soltos na area de trabalho, cada um
resolvendo uma duvida que aparece o tempo todo no estudo:

- Quintas: as doze tonalidades no ciclo, com a relativa menor, a armadura e as
  vizinhas marcadas como IV e V. Clicar troca a tonalidade do programa inteiro.
- Notas tocadas: as ultimas notas captadas pelo microfone, o intervalo e a
  direcao entre elas, e a marca de quais estao fora da tonalidade em uso.
- Ideias: grava um trecho com um clique e lista as ultimas gravacoes salvas.
- Graus: o campo harmonico da tonalidade atual em sete botoes; clicar joga o
  acorde no braco.
- Referencia: um drone sustentado na nota escolhida, para afinar de ouvido e
  para improvisar por cima de um centro tonal.
- Cordas soltas: a afinacao em uso, marcando quais cordas pertencem a
  tonalidade; clicar solta o drone naquela nota.
- Capotraste: a forma que se toca para soar na tonalidade desejada.
- Progressoes: quatro giros classicos ja cifrados na tonalidade atual.

Duas regras valem para todos eles e estao concentradas em _moldura():

1. Nada e pintado fora do retangulo do bloco. O conteudo e desenhado com o
   recorte (clip) preso ao bloco, entao nenhum tamanho de janela faz um item
   vazar para cima do vizinho.
2. Os retangulos clicaveis sao guardados em estado.rects_* no momento do
   desenho e o tratamento de clique so consulta essa lista. Nenhuma geometria
   e recalculada no clique, entao o que se ve e exatamente o que se clica.
"""
import contextlib
import glob
import math
import os
import time

import pygame

from config.design_system import TEMA, ds
from core.i18n import _t

# ---------------------------------------------------------------------------
# DADOS MUSICAIS
# ---------------------------------------------------------------------------

NOTAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Ciclo das quintas: cada passo para a direita sobe uma quinta justa
CICLO = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#', 'F']
RELATIVAS = ['Am', 'Em', 'Bm', 'F#m', 'C#m', 'G#m', 'D#m', 'A#m',
             'Fm', 'Cm', 'Gm', 'Dm']
ARMADURAS = ['-', '1#', '2#', '3#', '4#', '5#', '6#', '7#',
             '4b', '3b', '2b', '1b']

NOMES_INTERVALOS = ['uni', '2m', '2M', '3m', '3M', '4J', 'trit',
                    '5J', '6m', '6M', '7m', '7M']

# Campo harmonico maior, usado quando nao ha um campo harmonico vivo por perto
CAMPO_MAIOR = [('I', ''), ('ii', 'm'), ('iii', 'm'), ('IV', ''),
               ('V', ''), ('vi', 'm'), ('vii', 'dim')]
GRAUS_ESCALA = [0, 2, 4, 5, 7, 9, 11]

# Sufixo de cifra -> chave em painel_acordes.TIPOS_ACORDE
TIPO_POR_SUFIXO = {'': 'maior', 'm': 'menor', 'dim': 'dim', 'aug': 'aum',
                   '7': '7', 'maj7': 'maj7', 'm7': 'm7', 'm7b5': 'm7b5'}

# Giros classicos, por grau do campo (0 = I)
PROGRESSOES_RAPIDAS = [
    {'nome': 'Pop', 'graus': [0, 4, 5, 3]},
    {'nome': 'Doo-wop', 'graus': [0, 5, 3, 4]},
    {'nome': 'ii - V - I', 'graus': [1, 4, 0]},
    {'nome': 'Epica', 'graus': [5, 3, 0, 4]},
]

CORES_PROGRESSAO = [(80, 170, 255), (255, 170, 70), (120, 220, 150), (235, 120, 190)]

MAX_CASA_CAPO = 7          # capotraste alem da setima casa ja nao e pratico
OITAVA_DRONE = 3           # oitava do drone: grave o bastante para nao cansar


# ---------------------------------------------------------------------------
# CALCULOS PUROS (sem pygame, faceis de testar)
# ---------------------------------------------------------------------------

def indice_no_ciclo(tonica):
    """Posicao da tonalidade no ciclo das quintas (0 = C)."""
    return CICLO.index(tonica) if tonica in CICLO else 0


def vizinhas_da_tonalidade(tonica):
    """(IV, V) da tonalidade: para onde a musica costuma andar."""
    i = indice_no_ciclo(tonica)
    return CICLO[(i - 1) % 12], CICLO[(i + 1) % 12]


def relativa_de(tonica):
    """A relativa menor da tonalidade maior dada."""
    return RELATIVAS[indice_no_ciclo(tonica)]


def armadura_de(tonica):
    """Quantos sustenidos ou bemois a tonalidade carrega."""
    return ARMADURAS[indice_no_ciclo(tonica)]


def intervalo_entre(nota_a, nota_b):
    """Nome curto do intervalo entre duas notas, subindo."""
    try:
        return NOMES_INTERVALOS[(NOTAS.index(nota_b) - NOTAS.index(nota_a)) % 12]
    except ValueError:
        return ''


def direcao_entre(nota_a, nota_b):
    """'^' quando a segunda nota subiu, 'v' quando desceu, '' se for a mesma."""
    try:
        passo = (NOTAS.index(nota_b) - NOTAS.index(nota_a)) % 12
    except ValueError:
        return ''
    if passo == 0:
        return ''
    return '^' if passo <= 6 else 'v'


def notas_da_tonalidade(tonica):
    """As sete notas da escala maior da tonica dada."""
    if tonica not in NOTAS:
        return []
    base = NOTAS.index(tonica)
    return [NOTAS[(base + passo) % 12] for passo in GRAUS_ESCALA]


def transpor(nota, semitons):
    """A nota deslocada em semitons, dando a volta nas doze."""
    if nota not in NOTAS:
        return nota
    return NOTAS[(NOTAS.index(nota) + semitons) % 12]


def forma_com_capo(tonica, casa):
    """Que forma se toca, com o capotraste na casa dada, para soar na tonica."""
    return transpor(tonica, -int(casa))


def frequencia_da_nota(nome, oitava=OITAVA_DRONE):
    """Frequencia em Hz pela afinacao igual, com La 4 em 440 Hz."""
    if nome not in NOTAS:
        return 0.0
    semitons = NOTAS.index(nome) - NOTAS.index('A') + (oitava - 4) * 12
    return 440.0 * (2.0 ** (semitons / 12.0))


def campo_da_tonalidade(tonica, campo=None):
    """
        Como funciona: Devolve [(algarismo, cifra, nota, chave_do_tipo)] dos
        sete graus, usando a escala escolhida no campo harmonico quando ele
        existe e o campo maior quando nao existe.
        Para que serve: Uma unica fonte para o bloco de graus e para as
        progressoes rapidas.
        Onde e usada: desenhar_bloco_graus, acordes_da_progressao.
    """
    if tonica not in NOTAS:
        tonica = 'C'
    base = NOTAS.index(tonica)
    intervalos = GRAUS_ESCALA
    romanos = [alg for alg, _suf in CAMPO_MAIOR]
    sufixos = [suf for _alg, suf in CAMPO_MAIOR]

    escalas = getattr(campo, 'escalas_campo', None) if campo else None
    if escalas:
        indice = getattr(campo, 'indice_escala_campo', 0) % len(escalas)
        escolhida = escalas[indice]
        intervalos = escolhida.get('int', GRAUS_ESCALA)
        romanos = escolhida.get('romanos', romanos)
        sufixos = [s.replace('°', 'dim') for s in escolhida.get('qualidades', sufixos)]

    graus = []
    for i in range(min(7, len(intervalos))):
        nota = NOTAS[(base + intervalos[i]) % 12]
        sufixo = sufixos[i] if i < len(sufixos) else ''
        algarismo = romanos[i] if i < len(romanos) else str(i + 1)
        tipo = TIPO_POR_SUFIXO.get(sufixo, 'maior')
        graus.append((algarismo, f'{nota}{sufixo}', nota, tipo))
    return graus


def acordes_da_progressao(tonica, indices, campo=None):
    """Os acordes de um giro, na tonalidade e no campo em uso."""
    campo_completo = campo_da_tonalidade(tonica, campo)
    if not campo_completo:
        return []
    return [campo_completo[i % len(campo_completo)] for i in indices]


# ---------------------------------------------------------------------------
# MOLDURA COMUM DOS BLOCOS
# ---------------------------------------------------------------------------

LARGURA_MINIMA = 60
ALTURA_MINIMA = 44


@contextlib.contextmanager
def _moldura(tela, estado, nome, titulo, fontes, configs=None):
    """
        Como funciona: Desenha o painel do bloco, prende o recorte da tela ao
        retangulo dele e devolve a area util de conteudo. Ao sair, devolve o
        recorte anterior e desenha a caixa de selecao quando o modo de arrastar
        esta ligado.
        Para que serve: Garantir, num lugar so, que nenhum bloco pinte fora dos
        proprios limites em qualquer tamanho de janela.
        Onde e usada: Todos os desenhar_bloco_* deste modulo.
    """
    d = getattr(estado, f'dragger_{nome}', None)
    if d is None:
        yield None
        return
    # Bloco guardado no gaveteiro nao aparece nem deixa alvo para tras
    from ui.components.gaveteiro import visivel as bloco_na_tela
    if not bloco_na_tela(estado, f'dragger_{nome}'):
        yield None
        return
    if configs is not None:
        TEMA.definir_acento(configs.get_cor_tema())

    rect = pygame.Rect(int(d.x), int(d.y), max(0, int(d.largura)), max(0, int(d.altura)))
    if rect.width < LARGURA_MINIMA or rect.height < ALTURA_MINIMA:
        # Pequeno demais ate para o titulo: desenha so a moldura, sem conteudo
        if rect.width > 8 and rect.height > 8:
            ds.painel(tela, rect, None, None, acento=TEMA.acento)
        yield None
        if getattr(estado, 'drag_ativado', False):
            d.desenhar_caixa_selecao(tela, margem=5)
        return

    y = ds.painel(tela, rect, titulo, fontes['pequena'], acento=TEMA.acento)
    area = pygame.Rect(rect.x + ds.ESPACO_MD, y,
                       max(0, rect.width - ds.ESPACO_MD * 2),
                       max(0, rect.bottom - ds.ESPACO_SM - y))

    recorte_anterior = tela.get_clip()
    tela.set_clip(rect.clip(tela.get_rect()))
    try:
        yield area if area.height >= 10 and area.width >= 20 else None
    finally:
        tela.set_clip(recorte_anterior)
        if getattr(estado, 'drag_ativado', False):
            d.desenhar_caixa_selecao(tela, margem=5)


def _grade(area, quantidade, largura_min, altura_min, gap=4,
           opcoes_colunas=(6, 4, 3, 2, 1), altura_max=34):
    """
        Como funciona: Procura o arranjo em colunas que faca os itens caberem
        na area com um tamanho ainda legivel, da mais colunas para menos.
        Para que serve: Os blocos mudam de formato conforme o tamanho em vez de
        espremer o conteudo ou deixa-lo transbordar.
        Onde e usada: Quintas, cordas soltas, capotraste e drone.
    """
    if quantidade <= 0 or area.width <= 0 or area.height <= 0:
        return []
    for colunas in opcoes_colunas:
        colunas = min(colunas, quantidade)
        linhas = math.ceil(quantidade / colunas)
        largura = (area.width - (colunas - 1) * gap) / colunas
        altura = (area.height - (linhas - 1) * gap) / linhas
        if largura < largura_min or altura < altura_min:
            continue
        altura = min(altura, altura_max)
        alt_total = altura * linhas + gap * (linhas - 1)
        topo = area.y + max(0, (area.height - alt_total) / 2)
        rects = []
        for i in range(quantidade):
            rects.append(pygame.Rect(
                int(area.x + (i % colunas) * (largura + gap)),
                int(topo + (i // colunas) * (altura + gap)),
                max(1, int(largura)), max(1, int(altura))))
        return rects
    return []


def _cabe(rect, area):
    """Verdadeiro quando o retangulo esta inteiro dentro da area util."""
    return area.contains(rect)


def _pilula(tela, rect, texto, fonte, ativo=False, cor_borda=None, cor_fundo=None):
    """
        Como funciona: Igual ao chip do design system, mas com a folga do texto
        medida em cima da largura real da pilula.
        Para que serve: Em bloco pequeno o chip padrao descarta o rotulo inteiro
        quando ele nao cabe na folga fixa; aqui 'D#' continua escrito.
        Onde e usada: Grades de tonalidades, notas, cordas e casas.
    """
    if ativo:
        pygame.draw.rect(tela, ds.rgb(TEMA.acento), rect,
                         border_radius=ds.RAIO_PILULA)
        cor_texto = TEMA.texto_sobre_cor
    else:
        ds.superficie_translucida(tela, rect, cor_fundo or TEMA.superficie_alt,
                                  220, ds.RAIO_PILULA,
                                  cor_borda or TEMA.borda, 1)
        cor_texto = TEMA.texto if cor_borda is not None else TEMA.texto_suave
    ds.texto_em(tela, texto, fonte, rect.center, cor_texto, ancora='center',
                largura_max=max(8, rect.width - 2))
    return rect


def _tonica_atual(estado, campo=None):
    """A tonalidade em uso, vinda do campo harmonico ou do proprio estado."""
    tonica = getattr(campo, 'tonica_campo', None) if campo else None
    if not tonica:
        tonica = getattr(estado, 'tom_atual', None) or getattr(
            estado, 'nota_selecionada_bloco', 'C')
    return tonica if tonica in NOTAS else 'C'


def _mouse_em(rect):
    """Hover seguro: fora do loop principal o mouse pode nem existir."""
    try:
        return rect.collidepoint(pygame.mouse.get_pos())
    except Exception:
        return False


# ---------------------------------------------------------------------------
# QUINTAS
# ---------------------------------------------------------------------------

def desenhar_bloco_circulo(tela, estado, fontes, configs=None, campo=None):
    """
        Como funciona: Mostra as doze tonalidades do ciclo das quintas. Quando
        ha espaco elas ficam em roda, com a tonalidade atual e a relativa menor
        no centro; quando o bloco encolhe, viram uma grade na mesma ordem do
        ciclo, que continua legivel. Em qualquer um dos dois, as vizinhas ficam
        marcadas em ciano, que sao o IV e o V, e o rodape escreve os dois com o
        nome e a armadura sempre que sobra altura para ele.
        Para que serve: Trocar de tonalidade e enxergar para onde ela anda.
        Onde e usada: Workspace, bloco arrastavel das quintas.
    """
    estado.rects_circulo = []
    fonte = fontes['pequena']
    with _moldura(tela, estado, 'circulo', _t('Quintas'), fontes, configs) as area:
        if area is None:
            return
        tonica = _tonica_atual(estado, campo)
        atual = indice_no_ciclo(tonica)
        quarta, quinta = vizinhas_da_tonalidade(tonica)
        alt_texto = fonte.get_height()

        def desenhar_em(area_itens):
            """Roda quando cabe, grade quando nao; False se nem a grade coube."""
            # O raio sai do tamanho da bolinha, e nao o contrario: assim as
            # doze cabem inteiras, sem nenhuma ser descartada na borda.
            largura_rotulo = fonte.size('C#')[0]
            tam = max((largura_rotulo + 2) // 2,
                      int(min(area_itens.width, area_itens.height) * 0.135))
            raio_x = area_itens.width / 2 - tam - 1
            raio_y = area_itens.height / 2 - tam - 1
            # A folga entre a roda e o centro precisa caber tonica e relativa
            if raio_y - tam >= alt_texto + 6 and raio_x - tam >= alt_texto:
                _circulo_em_roda(tela, estado, fonte, fontes, area_itens, atual,
                                 raio_x, raio_y, tam)
                return True
            return _circulo_em_grade(tela, estado, fonte, area_itens, atual,
                                     largura_rotulo)

        # O rodape so fica se as doze tonalidades continuarem cabendo sem ele
        altura_rodape = alt_texto + 2
        area_itens = pygame.Rect(area)
        com_rodape = area.height >= altura_rodape * 3
        if com_rodape:
            area_itens.height -= altura_rodape
        desenhou = desenhar_em(area_itens)
        if not desenhou and com_rodape:
            com_rodape = False
            desenhou = desenhar_em(area)

        if com_rodape:
            ds.texto_em(tela, f'IV {quarta}  ·  V {quinta}  ·  {armadura_de(tonica)}',
                        fonte, (area.centerx, area.bottom - altura_rodape + 1),
                        TEMA.texto_apagado, ancora='midtop', largura_max=area.width)
        elif not desenhou:
            ds.texto_em(tela, f'{tonica}   IV {quarta}   V {quinta}', fonte,
                        area.center, TEMA.acento, ancora='center',
                        largura_max=area.width)


def _circulo_em_roda(tela, estado, fonte, fontes, area, atual, raio_x, raio_y, tam):
    """As doze tonalidades em elipse, com a atual e a relativa no centro."""
    centro = (area.centerx, area.centery)
    for i, nome in enumerate(CICLO):
        angulo = -math.pi / 2 + i * math.tau / 12
        r = pygame.Rect(0, 0, tam * 2, tam * 2)
        r.center = (int(centro[0] + math.cos(angulo) * raio_x),
                    int(centro[1] + math.sin(angulo) * raio_y))
        if not _cabe(r, area):
            continue
        estado.rects_circulo.append((r, nome))
        passo = (i - atual) % 12
        if passo == 0:
            pygame.draw.circle(tela, ds.rgb(TEMA.acento), r.center, tam)
            cor = TEMA.texto_sobre_cor
        elif passo in (1, 11):
            pygame.draw.circle(tela, ds.rgb(ds.misturar(TEMA.superficie_alt,
                                                        TEMA.ciano, 0.45)),
                               r.center, tam)
            pygame.draw.circle(tela, ds.rgb(TEMA.ciano), r.center, tam, 2)
            cor = TEMA.texto
        else:
            pygame.draw.circle(tela, ds.rgb(TEMA.superficie_alt), r.center, tam)
            pygame.draw.circle(tela, ds.rgb(TEMA.borda), r.center, tam, 1)
            cor = TEMA.texto_apagado
        ds.texto_em(tela, nome, fonte, r.center, cor, ancora='center',
                    largura_max=tam * 2)

    largura_centro = int((raio_x - tam) * 2)
    fonte_centro = fontes['titulo'] if area.height > 150 else fonte
    alt = fonte_centro.get_height()
    ds.texto_em(tela, CICLO[atual], fonte_centro,
                (area.centerx, area.centery - alt // 2), TEMA.acento,
                ancora='center', largura_max=largura_centro)
    ds.texto_em(tela, RELATIVAS[atual], fonte,
                (area.centerx, area.centery + alt // 2 + 2), TEMA.texto_suave,
                ancora='center', largura_max=largura_centro)


def _circulo_em_grade(tela, estado, fonte, area, atual, largura_rotulo):
    """As doze tonalidades em grade, na ordem do ciclo, para blocos pequenos."""
    rects = _grade(area, 12, largura_rotulo + 2, fonte.get_height() + 2,
                   gap=3, opcoes_colunas=(6, 4, 3), altura_max=34)
    if not rects:
        return False
    for i, nome in enumerate(CICLO):
        r = rects[i]
        if not _cabe(r, area):
            continue
        estado.rects_circulo.append((r, nome))
        passo = (i - atual) % 12
        if passo == 0:
            _pilula(tela, r, nome, fonte, ativo=True)
        elif passo in (1, 11):
            _pilula(tela, r, nome, fonte, cor_borda=TEMA.ciano,
                    cor_fundo=ds.misturar(TEMA.superficie_alt, TEMA.ciano, 0.35))
        else:
            _pilula(tela, r, nome, fonte)
    return True


# ---------------------------------------------------------------------------
# NOTAS TOCADAS
# ---------------------------------------------------------------------------

MAX_HISTORICO = 12


def registrar_nota_historico(estado, nota):
    """
        Como funciona: Guarda a nota quando ela muda, mantendo as ultimas doze.
        O silencio ('--' ou vazio) conta como separador: se a mesma nota voltar
        depois de uma pausa, ela e registrada de novo, porque foi tocada de novo.
        Para que serve: Alimentar o bloco de notas tocadas.
        Onde e usada: Loop principal, a cada quadro.
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
    del historico[:-MAX_HISTORICO]


def resumo_historico(historico, tonica):
    """(total, fora_da_tonalidade) das notas guardadas."""
    da_escala = set(notas_da_tonalidade(tonica))
    if not da_escala:
        return len(historico), 0
    return len(historico), sum(1 for n in historico if n not in da_escala)


def desenhar_bloco_historico(tela, estado, fontes, configs=None, campo=None):
    """
        Como funciona: Enfileira as ultimas notas captadas, escreve o intervalo
        e a direcao entre cada par e pinta de vermelho as que nao pertencem a
        tonalidade em uso. O rodape conta quantas ficaram de fora.
        Para que serve: Conferir a frase que acabou de sair e treinar ouvido.
        Onde e usada: Workspace, bloco arrastavel de notas tocadas.
    """
    estado.rect_btn_limpar_historico = pygame.Rect(0, 0, 0, 0)
    fonte = fontes['pequena']
    with _moldura(tela, estado, 'historico', _t('Notas tocadas'),
                  fontes, configs) as area:
        if area is None:
            return
        historico = list(getattr(estado, 'historico_notas', []) or [])
        tonica = _tonica_atual(estado, campo)
        da_escala = set(notas_da_tonalidade(tonica))

        alt_texto = fonte.get_height()

        if not historico:
            ds.texto_em(tela, _t('Toque algo para comecar'), fonte,
                        (area.centerx, area.y + 2), TEMA.texto_apagado,
                        ancora='midtop', largura_max=area.width)
            return

        mostra_intervalos = area.height >= alt_texto * 2 + 14
        mostra_resumo = area.height >= alt_texto * 3 + 18
        reservado = (alt_texto + 2 if mostra_intervalos else 0) + \
                    (alt_texto + 2 if mostra_resumo else 0)
        alt_celula = min(44, area.height - reservado)

        if alt_celula < 14:
            # Sem altura para as celulas: uma linha de texto com as ultimas notas
            ds.texto_em(tela, ' '.join(historico[-6:]), fonte, area.center,
                        TEMA.texto, ancora='center', largura_max=area.width)
            return

        # Com o intervalo escrito embaixo, a celula precisa ser larga o
        # bastante para o rotulo nao encostar no do vizinho
        largura_intervalo = fonte.size('^3M')[0] + 6
        minimo = max(fonte.size('C#')[0] + 10,
                     largura_intervalo if mostra_intervalos else 0)
        gap = 4
        larg_celula = min(46, max(minimo, 24))
        cabem = max(1, int((area.width + gap) // (larg_celula + gap)))
        visiveis = historico[-cabem:]
        # Sobe as celulas de forma que o conjunto fique centrado na altura util
        topo = area.y + max(0, (area.height - reservado - alt_celula) // 2)

        for i, nota in enumerate(visiveis):
            celula = pygame.Rect(area.x + i * (larg_celula + gap), topo,
                                 larg_celula, alt_celula)
            if not _cabe(celula, area):
                break
            recente = i == len(visiveis) - 1
            de_fora = bool(da_escala) and nota not in da_escala
            if recente:
                fundo, borda, cor_texto = TEMA.acento, TEMA.acento, TEMA.texto_sobre_cor
            elif de_fora:
                fundo, borda, cor_texto = TEMA.superficie_alt, TEMA.alerta, TEMA.alerta
            else:
                fundo, borda, cor_texto = TEMA.superficie_alt, TEMA.borda, TEMA.texto
            ds.superficie_translucida(tela, celula, fundo, 225, ds.RAIO_SM, borda, 1)
            ds.texto_centralizado(tela, nota, fonte, celula, cor_texto)

            if mostra_intervalos and i > 0:
                anterior = visiveis[i - 1]
                rotulo = f'{direcao_entre(anterior, nota)}{intervalo_entre(anterior, nota)}'
                largura = min(fonte.size(rotulo)[0], larg_celula)
                centro_x = min(max(celula.x - gap // 2, area.x + largura // 2),
                               area.right - largura // 2)
                ds.texto_em(tela, rotulo, fonte, (centro_x, celula.bottom + 2),
                            TEMA.ciano, ancora='midtop', largura_max=largura)

        if mostra_resumo:
            total, fora = resumo_historico(historico, tonica)
            texto = f"{total} {_t('notas')}"
            if da_escala:
                texto += f"  ·  {fora} {_t('fora de')} {tonica}"
            # Botao de limpar no canto do rodape, dentro da area util
            largura_resumo = area.width
            limpar = pygame.Rect(area.right - 16, area.bottom - alt_texto, 16, alt_texto)
            if _cabe(limpar, area) and area.width > 70:
                estado.rect_btn_limpar_historico = limpar
                ds.texto_centralizado(tela, 'x', fonte, limpar, TEMA.texto_apagado)
                largura_resumo = area.width - 20
            ds.texto_em(tela, texto, fonte, (area.x, area.bottom - alt_texto),
                        TEMA.texto_apagado, largura_max=largura_resumo)


# ---------------------------------------------------------------------------
# IDEIAS: GRAVACAO RAPIDA
# ---------------------------------------------------------------------------

PASTA_IDEIAS = 'Ideias'


def ideias_salvas(limite=4):
    """As gravacoes mais recentes da pasta de ideias, da mais nova para a mais velha."""
    try:
        arquivos = glob.glob(os.path.join(PASTA_IDEIAS, '*.wav'))
        arquivos.sort(key=os.path.getmtime, reverse=True)
        return arquivos[:limite]
    except OSError:
        return []


def nome_curto_ideia(caminho):
    """O nome do arquivo sem o prefixo e sem a extensao."""
    return os.path.basename(caminho).replace('ideia_', '').replace('.wav', '')


def alternar_gravacao_ideia(estado, motor_audio):
    """
        Como funciona: Inicia a gravacao ou a encerra, salvando na pasta Ideias
        com a data e a hora no nome, e atualiza a lista de recentes.
        Para que serve: Acao do botao do bloco de ideias.
        Onde e usada: tratar_clique_blocos.
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


def desenhar_bloco_ideias(tela, estado, fontes, configs=None, motor_audio=None):
    """
        Como funciona: Um botao que comeca e termina a gravacao do que esta
        entrando e, abaixo dele, as ultimas gravacoes ja salvas. Enquanto grava,
        mostra o tempo decorrido com um ponto pulsando.
        Para que serve: Nao perder a frase que apareceu no meio do estudo.
        Onde e usada: Workspace, bloco arrastavel de ideias.
    """
    estado.rect_btn_gravar_ideia = pygame.Rect(0, 0, 0, 0)
    fonte = fontes['pequena']
    with _moldura(tela, estado, 'ideias', _t('Ideias'), fontes, configs) as area:
        if area is None:
            return
        gravando = bool(motor_audio is not None
                        and getattr(motor_audio, 'gravando', False))
        alt_texto = fonte.get_height()
        altura_btn = min(34, max(20, area.height - alt_texto - 4))
        botao = pygame.Rect(area.x, area.y, area.width, altura_btn)
        if not _cabe(botao, area):
            botao = pygame.Rect(area.x, area.y, area.width, area.height)
        estado.rect_btn_gravar_ideia = botao
        ds.botao(tela, botao,
                 _t('Parar e salvar') if gravando else _t('Gravar ideia'),
                 fonte, variante='perigo' if gravando else 'primario',
                 hover=_mouse_em(botao))

        y_texto = botao.bottom + 4
        if y_texto + alt_texto > area.bottom:
            return

        if gravando:
            inicio = getattr(estado, 'inicio_gravacao_ideia', time.time())
            decorrido = max(0, int(time.time() - inicio))
            pulso = 3 + int(2 * abs(math.sin(time.time() * 3)))
            pygame.draw.circle(tela, ds.rgb(TEMA.alerta),
                               (area.x + 6, y_texto + alt_texto // 2), pulso)
            ds.texto_em(tela, f'{decorrido // 60:02d}:{decorrido % 60:02d}  {_t("gravando")}',
                        fonte, (area.x + 16, y_texto), TEMA.alerta,
                        largura_max=area.width - 16)
            return

        recentes = getattr(estado, 'ideias_recentes', None)
        if recentes is None:
            recentes = ideias_salvas()
            estado.ideias_recentes = recentes

        if not recentes:
            ds.texto_em(tela, _t('Grava a entrada de audio'), fonte,
                        (area.x, y_texto), TEMA.texto_apagado,
                        largura_max=area.width)
            return

        for caminho in recentes:
            if y_texto + alt_texto > area.bottom:
                break
            pygame.draw.circle(tela, ds.rgb(TEMA.verde),
                               (area.x + 3, y_texto + alt_texto // 2), 3)
            ds.texto_em(tela, nome_curto_ideia(caminho), fonte,
                        (area.x + 12, y_texto), TEMA.texto_suave,
                        largura_max=area.width - 12)
            y_texto += alt_texto + 2


# ---------------------------------------------------------------------------
# GRAUS DO CAMPO HARMONICO
# ---------------------------------------------------------------------------

def _notas_do_acorde(nota, tipo):
    """Mapa {nota: grau} do acorde, reaproveitando o painel de acordes."""
    try:
        from ui.blocks.painel_acordes import notas_do_acorde
    except ImportError:
        return {}
    try:
        return notas_do_acorde(nota, tipo)
    except KeyError:
        return {}


def aplicar_grau(estado, tonica, indice, campo=None):
    """
        Como funciona: Joga no braco o acorde do grau escolhido, por cima dos
        que ja estavam fixados.
        Para que serve: Ouvir e ver o grau do campo harmonico sem sair do bloco.
        Onde e usada: tratar_clique_blocos.
    """
    graus = campo_da_tonalidade(tonica, campo)
    if not graus:
        return False
    algarismo, cifra, nota, tipo = graus[indice % len(graus)]
    notas = _notas_do_acorde(nota, tipo)
    if not notas:
        return False
    estado.grau_selecionado = indice
    estado.acordes_no_braco = list(getattr(estado, 'acordes_fixados', [])) + [
        {'rotulo': cifra, 'notas': notas, 'janela': None,
         'cor': CORES_PROGRESSAO[indice % len(CORES_PROGRESSAO)], 'fixado': False}]
    return True


def limpar_grau(estado):
    """Tira do braco o acorde posto pelo bloco de graus."""
    estado.grau_selecionado = -1
    estado.acordes_no_braco = list(getattr(estado, 'acordes_fixados', []))


def desenhar_bloco_graus(tela, estado, fontes, configs=None, campo=None):
    """
        Como funciona: Mostra os sete graus da tonalidade e da escala em uso,
        com o algarismo romano em cima e a cifra embaixo. Clicar num deles
        desenha o acorde no braco; clicar de novo tira.
        Para que serve: Ver o campo harmonico inteiro e experimentar acorde por
        acorde sem abrir a aba de acordes.
        Onde e usada: Workspace, bloco arrastavel de graus.
    """
    estado.rects_graus = []
    fonte = fontes['pequena']
    tonica = _tonica_atual(estado, campo)
    titulo = f"{_t('Graus')} · {tonica}"
    with _moldura(tela, estado, 'graus', titulo, fontes, configs) as area:
        if area is None:
            return
        graus = campo_da_tonalidade(tonica, campo)
        alt_texto = fonte.get_height()
        maior_cifra = max(fonte.size(c)[0] for _a, c, _n, _t2 in graus)
        maior_grau = max(fonte.size(a)[0] for a, _c, _n, _t2 in graus)

        # Primeiro tenta caber a cifra; se nao der, cabe pelo menos o
        # algarismo romano, que ja diz o grau e continua clicavel
        rects = _grade(area, len(graus), maior_cifra + 4, alt_texto + 4, gap=3,
                       opcoes_colunas=(7, 4, 3, 2), altura_max=alt_texto * 3)
        so_algarismo = False
        if not rects:
            rects = _grade(area, len(graus), maior_grau + 4, alt_texto + 2, gap=2,
                           opcoes_colunas=(7, 4), altura_max=alt_texto * 2)
            so_algarismo = True
        if not rects:
            ds.texto_em(tela, ' '.join(c for _a, c, _n, _t2 in graus), fonte,
                        area.center, TEMA.texto, ancora='center',
                        largura_max=area.width)
            return

        selecionado = getattr(estado, 'grau_selecionado', -1)
        for i, (algarismo, cifra, _nota, _tipo) in enumerate(graus):
            r = rects[i]
            if not _cabe(r, area):
                continue
            estado.rects_graus.append((r, i))
            ativo = i == selecionado
            ds.superficie_translucida(
                tela, r,
                ds.misturar(TEMA.superficie_alt, TEMA.acento, 0.30) if ativo
                else TEMA.superficie_alt, 225, ds.RAIO_SM,
                TEMA.acento if ativo else TEMA.borda, 1)
            if so_algarismo:
                ds.texto_em(tela, algarismo, fonte, r.center,
                            TEMA.acento if ativo else TEMA.texto,
                            ancora='center', largura_max=max(8, r.width - 2))
            elif r.height >= alt_texto * 2 + 2:
                ds.texto_em(tela, algarismo, fonte, (r.centerx, r.y + 1),
                            TEMA.texto_apagado, ancora='midtop',
                            largura_max=r.width - 2)
                ds.texto_em(tela, cifra, fonte, (r.centerx, r.bottom - 1),
                            TEMA.acento if ativo else TEMA.texto,
                            ancora='midbottom', largura_max=r.width - 2)
            else:
                ds.texto_em(tela, cifra, fonte, r.center,
                            TEMA.acento if ativo else TEMA.texto,
                            ancora='center', largura_max=max(8, r.width - 2))


# ---------------------------------------------------------------------------
# REFERENCIA: DRONE SUSTENTADO
# ---------------------------------------------------------------------------

_cache_drone = {}


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
        Como funciona: Liga ou desliga o drone; pedir uma nota diferente com
        ele ligado troca o som na hora. Sem motor de audio disponivel, apenas
        desliga e devolve False, sem quebrar.
        Para que serve: Acao dos botoes do bloco de referencia e das cordas.
        Onde e usada: tratar_clique_blocos.
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
        Como funciona: Doze notas para escolher a referencia e um botao que
        sustenta o som dela em loop, com a frequencia escrita embaixo.
        Para que serve: Afinar de ouvido e improvisar por cima de um centro
        tonal, que e como se treina modo e escala de verdade.
        Onde e usada: Workspace, bloco arrastavel de referencia.
    """
    estado.rects_drone = []
    estado.rect_btn_drone = pygame.Rect(0, 0, 0, 0)
    fonte = fontes['pequena']
    with _moldura(tela, estado, 'drone', _t('Referencia'), fontes, configs) as area:
        if area is None:
            return
        if not getattr(estado, 'drone_nota', None):
            estado.drone_nota = _tonica_atual(estado, campo)
        nota = estado.drone_nota
        ligado = bool(getattr(estado, 'drone_ativo', False))
        alt_texto = fonte.get_height()

        altura_btn = min(30, max(20, area.height // 3))
        area_notas = pygame.Rect(area.x, area.y, area.width,
                                 area.height - altura_btn - 4)
        rects = _grade(area_notas, 12, fonte.size('C#')[0] + 2, alt_texto + 2,
                       gap=3, opcoes_colunas=(6, 4, 3), altura_max=32)
        if rects:
            for i, nome in enumerate(NOTAS):
                if i >= len(rects):
                    break
                r = rects[i]
                if not _cabe(r, area_notas):
                    continue
                estado.rects_drone.append((r, nome))
                _pilula(tela, r, nome, fonte, ativo=(nome == nota))
        elif area_notas.height >= alt_texto + 2:
            # Sem espaco para as doze: um seletor de uma linha, com as setas
            # levando a nota anterior e a seguinte
            _drone_compacto(tela, estado, fonte, area_notas, nota)

        botao = pygame.Rect(area.x, area.bottom - altura_btn, area.width, altura_btn)

        if _cabe(botao, area):
            estado.rect_btn_drone = botao
            rotulo = f"{_t('Parar')} {nota}" if ligado else f"{_t('Soar')} {nota}"
            if ligado and botao.width > 90:
                rotulo += f'  {frequencia_da_nota(nota):.1f} Hz'
            ds.botao(tela, botao, rotulo, fonte,
                     variante='perigo' if ligado else 'primario',
                     hover=_mouse_em(botao))


def _drone_compacto(tela, estado, fonte, area, nota):
    """Seletor de uma linha: nota anterior, nota atual e nota seguinte."""
    indice = NOTAS.index(nota) if nota in NOTAS else 0
    largura_seta = max(18, min(30, area.width // 4))
    anterior = pygame.Rect(area.x, area.y, largura_seta, area.height)
    seguinte = pygame.Rect(area.right - largura_seta, area.y, largura_seta,
                           area.height)
    meio = pygame.Rect(anterior.right + 2, area.y,
                       max(1, seguinte.x - anterior.right - 4), area.height)
    if not (_cabe(anterior, area) and _cabe(seguinte, area)):
        return
    estado.rects_drone.append((anterior, NOTAS[(indice - 1) % 12]))
    estado.rects_drone.append((seguinte, NOTAS[(indice + 1) % 12]))
    _pilula(tela, anterior, '<', fonte)
    _pilula(tela, seguinte, '>', fonte)
    if meio.width > 8:
        _pilula(tela, meio, nota, fonte, ativo=True)



# ---------------------------------------------------------------------------
# CORDAS SOLTAS
# ---------------------------------------------------------------------------

def afinacao_atual(estado):
    """
        Como funciona: Devolve (nome, notas) da afinacao em uso, com a mesma
        contagem de cordas e o mesmo deslocamento do baixo que o braco usa.
        Para que serve: O bloco mostrar exatamente as cordas que estao
        desenhadas no braco.
        Onde e usada: desenhar_bloco_cordas.
    """
    try:
        from config.app_settings import lista_afinacoes
        afinacao = lista_afinacoes[getattr(estado, 'indice_afinacao', 0)
                                   % len(lista_afinacoes)]
        nome, notas = afinacao['nome'], list(afinacao['notas'])
    except Exception:
        nome, notas = 'Standard', ['B', 'E', 'A', 'D', 'G', 'B', 'E']

    instrumento = getattr(estado, 'instrumento', 'guitarra')
    num_cordas = 4 if instrumento == 'baixo' else int(getattr(estado, 'NUM_CORDAS', 6))
    deslocamento = 2 if instrumento == 'baixo' else 0
    escolhidas = notas[deslocamento:deslocamento + num_cordas]
    return nome, escolhidas or notas


def desenhar_bloco_cordas(tela, estado, fontes, configs=None, campo=None):
    """
        Como funciona: Lista as cordas soltas da afinacao em uso, da mais grave
        para a mais aguda, marcando quais pertencem a tonalidade atual. Clicar
        numa corda solta o drone naquela nota.
        Para que serve: Conferir a afinacao e ouvir a referencia de cada corda
        sem sair do braco.
        Onde e usada: Workspace, bloco arrastavel de cordas soltas.
    """
    estado.rects_cordas = []
    fonte = fontes['pequena']
    with _moldura(tela, estado, 'cordas', _t('Cordas soltas'), fontes, configs) as area:
        if area is None:
            return
        nome_afinacao, cordas = afinacao_atual(estado)
        tonica = _tonica_atual(estado, campo)
        da_escala = set(notas_da_tonalidade(tonica))
        nota_drone = getattr(estado, 'drone_nota', None)
        alt_texto = fonte.get_height()

        area_chips = pygame.Rect(area)
        if area.height >= alt_texto * 3:
            area_chips.height -= alt_texto + 2
            ds.texto_em(tela, f'{_t(nome_afinacao)}  ·  {len(cordas)} {_t("cordas")}',
                        fonte, (area.x, area.bottom - alt_texto),
                        TEMA.texto_apagado, largura_max=area.width)

        rects = _grade(area_chips, len(cordas), fonte.size('C#')[0] + 6,
                       alt_texto + 2, gap=3, opcoes_colunas=(7, 6, 4, 3),
                       altura_max=32)
        for i, nota in enumerate(cordas):
            if i >= len(rects):
                break
            r = rects[i]
            if not _cabe(r, area_chips):
                continue
            estado.rects_cordas.append((r, nota))
            if nota == nota_drone and getattr(estado, 'drone_ativo', False):
                _pilula(tela, r, nota, fonte, ativo=True)
            elif da_escala and nota in da_escala:
                _pilula(tela, r, nota, fonte, cor_borda=TEMA.verde,
                        cor_fundo=ds.misturar(TEMA.superficie_alt, TEMA.verde, 0.30))
            else:
                _pilula(tela, r, nota, fonte)


# ---------------------------------------------------------------------------
# CAPOTRASTE
# ---------------------------------------------------------------------------

def desenhar_bloco_capo(tela, estado, fontes, configs=None, campo=None):
    """
        Como funciona: Escolhida a casa do capotraste, mostra que forma se toca
        para a musica soar na tonalidade atual, e a relativa dessa forma.
        Para que serve: Tocar em tonalidade dificil usando forma facil, que e o
        uso real do capotraste no acompanhamento.
        Onde e usada: Workspace, bloco arrastavel do capotraste.
    """
    estado.rects_capo = []
    fonte = fontes['pequena']
    tonica = _tonica_atual(estado, campo)
    casa = int(getattr(estado, 'capo_casa', 0)) % (MAX_CASA_CAPO + 1)
    with _moldura(tela, estado, 'capo', _t('Capotraste'), fontes, configs) as area:
        if area is None:
            return
        alt_texto = fonte.get_height()
        forma = forma_com_capo(tonica, casa)

        area_chips = pygame.Rect(area)
        if area.height >= alt_texto * 3:
            area_chips.height -= alt_texto + 2
            if casa == 0:
                resumo = f'{_t("Sem capo")}  ·  {_t("forma")} {tonica}'
            else:
                resumo = f'{_t("Soa em")} {tonica}  ·  {_t("forma")} {forma}'
            ds.texto_em(tela, resumo, fonte, (area.centerx, area.bottom - alt_texto),
                        TEMA.texto_suave, ancora='midtop', largura_max=area.width)

        casas = list(range(MAX_CASA_CAPO + 1))
        rects = _grade(area_chips, len(casas), fonte.size('88')[0] + 6,
                       alt_texto + 2, gap=3, opcoes_colunas=(8, 4, 3),
                       altura_max=32)
        for i, numero in enumerate(casas):
            if i >= len(rects):
                break
            r = rects[i]
            if not _cabe(r, area_chips):
                continue
            estado.rects_capo.append((r, numero))
            _pilula(tela, r, str(numero), fonte, ativo=(numero == casa))


# ---------------------------------------------------------------------------
# PROGRESSOES RAPIDAS
# ---------------------------------------------------------------------------

def aplicar_progressao(estado, tonica, indices, campo=None):
    """
        Como funciona: Coloca todos os acordes do giro no braco, cada um com a
        sua cor, usando a mesma lista que o painel de acordes alimenta.
        Para que serve: Ver o giro inteiro desenhado de uma vez.
        Onde e usada: tratar_clique_blocos.
    """
    lista = []
    for i, (_alg, cifra, nota, tipo) in enumerate(
            acordes_da_progressao(tonica, indices, campo)):
        notas = _notas_do_acorde(nota, tipo)
        if not notas:
            return False
        lista.append({'rotulo': cifra, 'notas': notas, 'janela': None,
                      'cor': CORES_PROGRESSAO[i % len(CORES_PROGRESSAO)],
                      'fixado': True})
    if not lista:
        return False
    estado.acordes_fixados = list(lista)
    estado.acordes_no_braco = list(lista)
    return True


def limpar_progressao(estado):
    """Tira do braco os acordes do giro."""
    estado.progressao_ativa = -1
    estado.acordes_fixados = []
    estado.acordes_no_braco = []


def desenhar_bloco_progressoes(tela, estado, fontes, configs=None, campo=None):
    """
        Como funciona: Lista quatro giros classicos ja cifrados na tonalidade e
        no campo em uso; clicar num deles joga os acordes no braco e clicar de
        novo limpa.
        Para que serve: Sair do estudo solto e cair em algo que se toca.
        Onde e usada: Workspace, bloco arrastavel de progressoes.
    """
    estado.rects_progressoes = []
    fonte = fontes['pequena']
    tonica = _tonica_atual(estado, campo)
    with _moldura(tela, estado, 'progressoes', f"{_t('Progressoes')} · {tonica}",
                  fontes, configs) as area:
        if area is None:
            return
        alt_texto = fonte.get_height()
        # Cabendo os quatro giros, todos aparecem; se nao couberem, aparecem
        # os primeiros, em vez de o bloco ficar vazio
        quantas = len(PROGRESSOES_RAPIDAS)
        altura_minima = alt_texto + 4
        while quantas > 1 and (area.height - (quantas - 1) * 3) / quantas < altura_minima:
            quantas -= 1
        altura_linha = min(44, (area.height - (quantas - 1) * 3) / quantas)
        if altura_linha < altura_minima:
            ds.texto_em(tela, _t('Amplie o bloco'), fonte, area.center,
                        TEMA.texto_apagado, ancora='center', largura_max=area.width)
            return

        ativa = getattr(estado, 'progressao_ativa', -1)
        for i, giro in enumerate(PROGRESSOES_RAPIDAS[:quantas]):
            r = pygame.Rect(area.x, int(area.y + i * (altura_linha + 3)),
                            area.width, int(altura_linha))
            if not _cabe(r, area):
                break
            estado.rects_progressoes.append((r, i))
            selecionada = i == ativa
            ds.superficie_translucida(
                tela, r,
                ds.misturar(TEMA.superficie_alt, TEMA.acento, 0.28) if selecionada
                else TEMA.superficie_alt, 220, ds.RAIO_SM,
                TEMA.acento if selecionada else TEMA.borda, 1)

            duas_linhas = r.height >= alt_texto * 2 + 4
            ds.texto_em(tela, _t(giro['nome']), fonte,
                        (r.x + ds.ESPACO_SM, r.centery if not duas_linhas else r.y + 2),
                        TEMA.acento if selecionada else TEMA.texto_suave,
                        ancora='midleft' if not duas_linhas else 'topleft',
                        largura_max=r.width // 2 - ds.ESPACO_SM)

            cifras = acordes_da_progressao(tonica, giro['graus'], campo)
            x = r.right - ds.ESPACO_SM
            limite = r.x + r.width // 2
            for j in range(len(cifras) - 1, -1, -1):
                algarismo, cifra, _nota, _tipo = cifras[j]
                largura = max(fonte.size(cifra)[0], fonte.size(algarismo)[0])
                if x - largura < limite:
                    break
                cor = CORES_PROGRESSAO[j % len(CORES_PROGRESSAO)]
                if duas_linhas:
                    ds.texto_em(tela, cifra, fonte, (x, r.y + 2),
                                cor if selecionada else TEMA.texto, ancora='topright')
                    ds.texto_em(tela, algarismo, fonte, (x, r.bottom - 2),
                                TEMA.texto_apagado, ancora='bottomright')
                else:
                    ds.texto_em(tela, cifra, fonte, (x, r.centery),
                                cor if selecionada else TEMA.texto, ancora='midright')
                x -= largura + 8


# ---------------------------------------------------------------------------
# CLIQUE: SO OS RETANGULOS GUARDADOS NO DESENHO
# ---------------------------------------------------------------------------

def _achar(rects, pos):
    """O valor guardado junto do primeiro retangulo que contem o ponto."""
    for rect, valor in rects or []:
        if rect.width > 0 and rect.height > 0 and rect.collidepoint(pos):
            return valor
    return None


def tratar_clique_blocos(estado, pos, campo=None, motor_audio=None):
    """
        Como funciona: Testa o ponto clicado contra os retangulos que os blocos
        guardaram durante o desenho, na ordem dos blocos, e executa a acao do
        primeiro que acertar. Nenhuma geometria e recalculada aqui, entao o
        alvo do clique e exatamente o que foi desenhado.
        Para que serve: Um unico ponto de entrada para os cliques dos blocos
        extras, em vez de espalhar testes pelo controlador de eventos.
        Onde e usada: core/controlador_eventos.processar.

        Devolve o nome da acao executada, ou None quando o clique nao era de
        nenhum bloco. 'tonalidade' avisa o controlador para regerar as escalas.
    """
    # Quintas: troca a tonalidade do programa inteiro
    nota = _achar(getattr(estado, 'rects_circulo', []), pos)
    if nota is not None:
        estado.tom_atual = nota
        estado.nota_selecionada_bloco = nota
        if campo is not None:
            campo.tonica_campo = nota
            campo.tonica = nota
            if getattr(campo, 'indice_acorde_selecionado', -1) != -1:
                campo.calcular_notas_acorde_selecionado()
        return 'tonalidade'

    # Notas tocadas: limpar a lista
    limpar = getattr(estado, 'rect_btn_limpar_historico', None)
    if limpar is not None and limpar.width > 0 and limpar.collidepoint(pos):
        estado.historico_notas = []
        return 'historico'

    # Ideias: gravar ou parar e salvar
    gravar = getattr(estado, 'rect_btn_gravar_ideia', None)
    if gravar is not None and gravar.width > 0 and gravar.collidepoint(pos):
        alternar_gravacao_ideia(estado, motor_audio)
        return 'ideia'

    # Graus: joga o acorde do grau no braco, e o mesmo clique tira
    grau = _achar(getattr(estado, 'rects_graus', []), pos)
    if grau is not None:
        if getattr(estado, 'grau_selecionado', -1) == grau:
            limpar_grau(estado)
        else:
            aplicar_grau(estado, _tonica_atual(estado, campo), grau, campo)
        return 'grau'

    # Referencia: escolher a nota do drone
    nota_drone = _achar(getattr(estado, 'rects_drone', []), pos)
    if nota_drone is not None:
        if getattr(estado, 'drone_ativo', False):
            alternar_drone(estado, nota_drone)
        else:
            estado.drone_nota = nota_drone
        return 'drone'

    botao_drone = getattr(estado, 'rect_btn_drone', None)
    if botao_drone is not None and botao_drone.width > 0 and botao_drone.collidepoint(pos):
        alternar_drone(estado)
        return 'drone'

    # Cordas soltas: solta o drone na nota da corda
    corda = _achar(getattr(estado, 'rects_cordas', []), pos)
    if corda is not None:
        alternar_drone(estado, corda)
        return 'corda'

    # Capotraste: escolher a casa
    casa = _achar(getattr(estado, 'rects_capo', []), pos)
    if casa is not None:
        estado.capo_casa = 0 if getattr(estado, 'capo_casa', 0) == casa else casa
        return 'capo'

    # Progressoes: joga o giro inteiro no braco, e o mesmo clique limpa
    giro = _achar(getattr(estado, 'rects_progressoes', []), pos)
    if giro is not None:
        if getattr(estado, 'progressao_ativa', -1) == giro:
            limpar_progressao(estado)
        else:
            estado.progressao_ativa = giro
            aplicar_progressao(estado, _tonica_atual(estado, campo),
                               PROGRESSOES_RAPIDAS[giro]['graus'], campo)
        return 'progressao'

    return None


# ---------------------------------------------------------------------------
# REGISTRO DOS BLOCOS
# ---------------------------------------------------------------------------

# nome do dragger (sem o prefixo) -> funcao de desenho.
# A ordem e a mesma em que o workspace desenha e em que os cliques sao testados.
BLOCOS_EXTRAS = (
    ('circulo', desenhar_bloco_circulo),
    ('historico', desenhar_bloco_historico),
    ('ideias', desenhar_bloco_ideias),
    ('graus', desenhar_bloco_graus),
    ('drone', desenhar_bloco_drone),
    ('cordas', desenhar_bloco_cordas),
    ('capo', desenhar_bloco_capo),
    ('progressoes', desenhar_bloco_progressoes),
)


def desenhar_blocos_extras(tela, estado, fontes, configs=None, campo=None,
                           motor_audio=None):
    """
        Como funciona: Desenha todos os blocos extras na ordem do registro,
        entregando a cada um o que ele precisa.
        Para que serve: O renderizador chama uma linha so, e um bloco novo
        entra em cena apenas sendo registrado em BLOCOS_EXTRAS.
        Onde e usada: ui/renderizador_ui.desenhar_workspace.
    """
    for nome, desenhar in BLOCOS_EXTRAS:
        if nome == 'ideias':
            desenhar(tela, estado, fontes, configs, motor_audio)
        else:
            desenhar(tela, estado, fontes, configs, campo)
