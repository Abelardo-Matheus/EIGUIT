# -*- coding: utf-8 -*-
"""
Modelo de instrumentos do EIGUIT Studio.

Cada instrumento descreve como suas notas ficam dispostas: cordas e casas nos
instrumentos de braco, teclas brancas e pretas no teclado. Um mesmo diagrama
serve para estudos, jogos e visualizacoes, bastando dizer quais notas
destacar e com que cor.
"""
import pygame

from config.design_system import TEMA, ds

NOTAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
TECLAS_BRANCAS = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
# Posicao da tecla preta entre duas brancas (indice da branca a esquerda)
PRETAS_DEPOIS_DE = {0: 'C#', 1: 'D#', 3: 'F#', 4: 'G#', 5: 'A#'}

INSTRUMENTOS = {
    'guitarra': {
        'nome': 'Guitarra (6 cordas)', 'familia': 'corda', 'tipo_audio': 'guitarra',
        'cordas': ['E', 'A', 'D', 'G', 'B', 'E'], 'casas': 15,
        'oitavas': [2, 2, 3, 3, 3, 4],
    },
    'guitarra7': {
        'nome': 'Guitarra (7 cordas)', 'familia': 'corda', 'tipo_audio': 'guitarra7',
        'cordas': ['B', 'E', 'A', 'D', 'G', 'B', 'E'], 'casas': 15,
        'oitavas': [1, 2, 2, 3, 3, 3, 4],
    },
    'baixo': {
        'nome': 'Baixo (4 cordas)', 'familia': 'corda', 'tipo_audio': 'baixo',
        'cordas': ['E', 'A', 'D', 'G'], 'casas': 15,
        'oitavas': [1, 1, 2, 2],
    },
    'baixo5': {
        'nome': 'Baixo (5 cordas)', 'familia': 'corda', 'tipo_audio': 'baixo',
        'cordas': ['B', 'E', 'A', 'D', 'G'], 'casas': 15,
        'oitavas': [0, 1, 1, 2, 2],
    },
    'ukulele': {
        'nome': 'Ukulele', 'familia': 'corda', 'tipo_audio': 'ukulele',
        'cordas': ['G', 'C', 'E', 'A'], 'casas': 12,
        'oitavas': [4, 4, 4, 4],
    },
    'cavaquinho': {
        'nome': 'Cavaquinho', 'familia': 'corda', 'tipo_audio': 'ukulele',
        'cordas': ['D', 'G', 'B', 'D'], 'casas': 12,
        'oitavas': [4, 4, 4, 5],
    },
    'teclado': {
        'nome': 'Teclado', 'familia': 'tecla', 'tipo_audio': 'teclado',
        'oitava_inicial': 3, 'num_oitavas': 2,
    },
}

ORDEM_INSTRUMENTOS = ['guitarra', 'guitarra7', 'baixo', 'baixo5',
                      'ukulele', 'cavaquinho', 'teclado']


def config_instrumento(chave):
    """Devolve a definicao do instrumento, caindo na guitarra se nao existir."""
    return INSTRUMENTOS.get(chave, INSTRUMENTOS['guitarra'])


def nota_da_casa(corda_solta, casa):
    """Nome da nota na casa indicada de uma corda solta."""
    try:
        return NOTAS[(NOTAS.index(corda_solta) + casa) % 12]
    except ValueError:
        return corda_solta


def posicoes_da_nota(chave, nota_alvo):
    """
    Todas as posicoes onde a nota aparece no instrumento.
    Instrumentos de corda devolvem (corda, casa); teclado devolve (indice_tecla,).
    """
    cfg = config_instrumento(chave)
    achados = []
    if cfg['familia'] == 'corda':
        for i, solta in enumerate(cfg['cordas']):
            for casa in range(cfg['casas'] + 1):
                if nota_da_casa(solta, casa) == nota_alvo:
                    achados.append((i, casa))
    else:
        total = cfg['num_oitavas'] * 12
        for i in range(total):
            if NOTAS[i % 12] == nota_alvo:
                achados.append((i,))
    return achados


# ---------------------------------------------------------------------------
# DIAGRAMAS
# ---------------------------------------------------------------------------

def _desenhar_braco(tela, rect, cfg, destaques, fonte, mostrar_casas=True,
                    rects_saida=None, casa_inicial=0, casas_visiveis=None):
    """Diagrama de instrumento de corda. destaques: {(corda, casa): (cor, rotulo)}."""
    cordas = cfg['cordas']
    n_cordas = len(cordas)
    total_casas = casas_visiveis or cfg['casas']
    altura_num = 15 if mostrar_casas and rect.height >= 90 else 0

    area = pygame.Rect(rect.x + 26, rect.y + 8,
                       rect.width - 34, rect.height - 16 - altura_num)
    if area.width < 60 or area.height < 40:
        return

    ds.gradiente_vertical(tela, area, ds.clarear(TEMA.madeira, 0.14),
                          ds.escurecer(TEMA.madeira, 0.2), ds.RAIO_SM)

    largura_casa = area.width / total_casas
    espaco_corda = area.height / max(1, n_cordas - 1)

    for c in range(total_casas + 1):
        x = area.x + c * largura_casa
        if casa_inicial == 0 and c == 0:
            pygame.draw.rect(tela, ds.rgb(ds.clarear(TEMA.corda, 0.4)),
                             (x - 2, area.y, 4, area.height))
        else:
            pygame.draw.line(tela, ds.rgb(TEMA.traste), (x, area.y),
                             (x, area.bottom), 1)
        if c < total_casas and altura_num:
            numero = casa_inicial + c + 1
            marcada = numero in (3, 5, 7, 9, 12, 15, 17, 19, 21, 24)
            ds.texto_em(tela, str(numero), fonte,
                        (x + largura_casa / 2, area.bottom + 3),
                        TEMA.acento if marcada else TEMA.texto_apagado,
                        ancora='midtop')

    for i in range(n_cordas):
        y = area.bottom - i * espaco_corda
        pygame.draw.line(tela, ds.rgb(TEMA.corda), (area.x, y), (area.right, y),
                         1 + i // 3)
        ds.texto_em(tela, cordas[i], fonte, (rect.x + 12, y), TEMA.texto_apagado,
                    ancora='center')

    raio = max(6, min(16, int(min(largura_casa, espaco_corda) * 0.4)))
    for (corda, casa), dados in (destaques or {}).items():
        if not (0 <= corda < n_cordas):
            continue
        casa_rel = casa - casa_inicial
        if not (0 <= casa_rel <= total_casas):
            continue
        cor, rotulo = dados if isinstance(dados, (tuple, list)) else (dados, '')
        cx = (area.x - largura_casa * 0.5 if casa_rel == 0
              else area.x + casa_rel * largura_casa - largura_casa / 2)
        cy = area.bottom - corda * espaco_corda
        pygame.draw.circle(tela, ds.rgb(cor), (int(cx), int(cy)), raio)
        pygame.draw.circle(tela, ds.rgb(ds.escurecer(cor, 0.45)),
                           (int(cx), int(cy)), raio, 1)
        if rotulo and raio >= 9:
            ds.texto_em(tela, str(rotulo), fonte, (int(cx), int(cy)),
                        ds.contraste_texto(cor), ancora='center')
        if rects_saida is not None:
            rects_saida.append((pygame.Rect(int(cx - raio), int(cy - raio),
                                            raio * 2, raio * 2), (corda, casa)))


def _desenhar_teclado(tela, rect, cfg, destaques, fonte, rects_saida=None):
    """Diagrama de teclado. destaques: {indice_tecla: (cor, rotulo)}."""
    num_oitavas = cfg.get('num_oitavas', 2)
    total_brancas = 7 * num_oitavas
    largura_branca = rect.width / total_brancas
    altura_branca = rect.height
    altura_preta = altura_branca * 0.62
    largura_preta = largura_branca * 0.62

    # Teclas brancas primeiro
    indices_brancas = []
    for oitava in range(num_oitavas):
        for i, nome in enumerate(TECLAS_BRANCAS):
            indice_cromatico = oitava * 12 + NOTAS.index(nome)
            indices_brancas.append(indice_cromatico)
            x = rect.x + (oitava * 7 + i) * largura_branca
            tecla = pygame.Rect(int(x), rect.y, int(largura_branca) - 1, int(altura_branca))
            dados = (destaques or {}).get(indice_cromatico)
            cor_base = (240, 240, 245) if TEMA.escuro else (252, 252, 255)
            pygame.draw.rect(tela, cor_base, tecla, border_bottom_left_radius=4,
                             border_bottom_right_radius=4)
            pygame.draw.rect(tela, ds.rgb(TEMA.borda), tecla, 1,
                             border_bottom_left_radius=4, border_bottom_right_radius=4)
            if dados:
                cor, rotulo = dados if isinstance(dados, (tuple, list)) else (dados, '')
                marca = pygame.Rect(tecla.x + 3, tecla.bottom - int(altura_branca * 0.34),
                                    tecla.width - 6, int(altura_branca * 0.3))
                pygame.draw.rect(tela, ds.rgb(cor), marca, border_radius=4)
                if rotulo:
                    ds.texto_em(tela, str(rotulo), fonte, marca.center,
                                ds.contraste_texto(cor), ancora='center')
            else:
                ds.texto_em(tela, nome, fonte,
                            (tecla.centerx, tecla.bottom - 12), (120, 125, 140),
                            ancora='center')
            if rects_saida is not None:
                rects_saida.append((tecla, indice_cromatico))

    # Teclas pretas por cima
    for oitava in range(num_oitavas):
        for i, nome in PRETAS_DEPOIS_DE.items():
            indice_cromatico = oitava * 12 + NOTAS.index(nome)
            x = rect.x + (oitava * 7 + i + 1) * largura_branca - largura_preta / 2
            tecla = pygame.Rect(int(x), rect.y, int(largura_preta), int(altura_preta))
            dados = (destaques or {}).get(indice_cromatico)
            pygame.draw.rect(tela, (24, 26, 34), tecla,
                             border_bottom_left_radius=3, border_bottom_right_radius=3)
            if dados:
                cor, rotulo = dados if isinstance(dados, (tuple, list)) else (dados, '')
                marca = pygame.Rect(tecla.x + 2, tecla.bottom - int(altura_preta * 0.36),
                                    tecla.width - 4, int(altura_preta * 0.3))
                pygame.draw.rect(tela, ds.rgb(cor), marca, border_radius=3)
                if rotulo:
                    ds.texto_em(tela, str(rotulo), fonte, marca.center,
                                ds.contraste_texto(cor), ancora='center')
            if rects_saida is not None:
                rects_saida.append((tecla, indice_cromatico))


def desenhar_diagrama(tela, rect, chave, destaques=None, fonte=None,
                      rects_saida=None, mostrar_casas=True, casa_inicial=0,
                      casas_visiveis=None):
    """
        Como funciona: Escolhe entre braco e teclado conforme o instrumento e
        desenha as notas destacadas.
        Para que serve: Um so diagrama serve a todos os estudos e jogos.
        Onde e usada: Estudos de notas, padroes e improvisacao.
    """
    cfg = config_instrumento(chave)
    fonte = fonte or pygame.font.SysFont('Arial', 12, bold=True)
    if rects_saida is not None:
        rects_saida.clear()
    if cfg['familia'] == 'corda':
        _desenhar_braco(tela, rect, cfg, destaques, fonte, mostrar_casas,
                        rects_saida, casa_inicial, casas_visiveis)
    else:
        _desenhar_teclado(tela, rect, cfg, destaques, fonte, rects_saida)


def destaques_por_nota(chave, mapa_notas, cores_por_grau=None):
    """
    Converte {nota: grau} nas posicoes do instrumento, prontas para o diagrama.
    """
    cores = cores_por_grau or {}
    destaques = {}
    cfg = config_instrumento(chave)
    if cfg['familia'] == 'corda':
        for i, solta in enumerate(cfg['cordas']):
            for casa in range(cfg['casas'] + 1):
                nome = nota_da_casa(solta, casa)
                grau = mapa_notas.get(nome)
                if grau:
                    destaques[(i, casa)] = (cores.get(grau, TEMA.acento), grau)
    else:
        for i in range(cfg.get('num_oitavas', 2) * 12):
            nome = NOTAS[i % 12]
            grau = mapa_notas.get(nome)
            if grau:
                destaques[i] = (cores.get(grau, TEMA.acento), grau)
    return destaques
