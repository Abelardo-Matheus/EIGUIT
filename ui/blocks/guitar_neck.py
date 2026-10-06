# -*- coding: utf-8 -*-
"""Renderizacao do braco do instrumento: trastes, cordas, marcadores e notas."""
import pygame

import core.modulos.escalas as escalas
from config.theme import *
from config.ui_metrics import *
from config.app_settings import *
from config.design_system import TEMA, ds
from ui.components.utils import obter_grau
from core.modulos.escalas import equivalencia_notas
from ui.components.config_componentes import (
    GUITAR_RAIO_NOTA, GUITAR_ALPHA_NORMAL, GUITAR_ALPHA_INATIVO,
)

# Casas que recebem marcador de posicao (padrao de guitarra)
CASAS_MARCADAS = (3, 5, 7, 9, 15, 17, 19, 21)
CASAS_DUPLO_MARCADOR = (12, 24)


def _desenhar_base_braco(tela, rect, cor_madeira):
    """Madeira com gradiente e sombra projetada."""
    ds.sombra(tela, rect, raio=ds.RAIO_MD, forca=90, deslocamento=4)
    ds.gradiente_vertical(tela, rect, ds.clarear(cor_madeira, 0.16),
                          ds.escurecer(cor_madeira, 0.22), ds.RAIO_MD)
    pygame.draw.rect(tela, ds.rgb(ds.escurecer(cor_madeira, 0.45)), rect,
                     width=1, border_radius=ds.RAIO_MD)


def _desenhar_marcadores(tela, rect, num_casas, espaco_casas, cor):
    """Inlays de posicao no meio do braco."""
    for casa in range(1, num_casas + 1):
        x_centro = rect.x + casa * espaco_casas - espaco_casas / 2
        if casa in CASAS_DUPLO_MARCADOR:
            for deslocamento in (-rect.height * 0.22, rect.height * 0.22):
                pygame.draw.circle(tela, cor,
                                   (int(x_centro), int(rect.centery + deslocamento)),
                                   max(4, int(espaco_casas * 0.11)))
        elif casa in CASAS_MARCADAS:
            pygame.draw.circle(tela, cor, (int(x_centro), int(rect.centery)),
                               max(4, int(espaco_casas * 0.11)))


def desenhar_guitarra(tela, estado, configs, fontes, meu_processador,
                      meu_campo_harmonico, dragger_obj=None):
    """
        Como funciona: Desenha o braco completo (madeira, trastes, cordas,
        marcadores e numeracao) e sobrepoe as notas da escala, destacando
        tonica, terca, quinta e a nota captada pelo microfone.
        Para que serve: Visualizacao principal do estudo no instrumento.
        Onde e usada: Chamada pelo renderizador do workspace.
    """
    alvo = dragger_obj or getattr(estado, 'dragger_guitarra', None)
    if alvo is None:
        return

    if configs is not None:
        TEMA.definir_acento(configs.get_cor_tema())

    try:
        notas_abertas = lista_afinacoes[estado.indice_afinacao]['notas']
    except (IndexError, KeyError, TypeError):
        notas_abertas = ['E', 'A', 'D', 'G', 'B', 'E', 'B']

    cor_madeira = configs.get_cor_braco() if configs else TEMA.madeira
    instrumento = getattr(estado, 'instrumento', 'guitarra')
    num_cordas = 4 if instrumento == 'baixo' else estado.NUM_CORDAS

    altura = alvo.altura - 2 * estado.ESPACO_CORDAS if instrumento == 'baixo' else alvo.altura
    y_base = alvo.y + estado.ESPACO_CORDAS if instrumento == 'baixo' else alvo.y

    # Calha a esquerda da pestana, onde ficam as notas das cordas soltas.
    # Sem ela as bolinhas da casa 0 eram desenhadas fora do bloco.
    calha = int(max(26, min(44, alvo.largura * 0.028)))
    rect_braco = pygame.Rect(alvo.x + calha, y_base, alvo.largura - calha, altura)
    espaco_casas = rect_braco.width / estado.NUM_CASAS

    # --- Madeira e marcadores ---------------------------------------------
    _desenhar_base_braco(tela, rect_braco, cor_madeira)
    _desenhar_marcadores(tela, rect_braco, estado.NUM_CASAS, espaco_casas,
                         ds.com_alpha(ds.clarear(cor_madeira, 0.55), 200)[:3])

    # --- Realce das janelas dos acordes sobrepostos ------------------------
    # Lista unica: acordes ligados + previa do arrasto da paleta. O foco
    # (mouse sobre um chip ou cartao) deixa so aquele acorde em evidencia.
    from ui.components.paleta_acordes import acordes_para_desenhar
    acordes_braco, foco_acordes = acordes_para_desenhar(estado)
    etiquetas_usadas = []
    etiquetas_pendentes = []
    for indice_acorde, acorde in enumerate(acordes_braco):
        janela = acorde.get('janela')
        if not janela:
            continue
        cor_acorde = acorde.get('cor') or TEMA.acento
        apagado = bool(foco_acordes) and acorde.get('rotulo') not in foco_acordes
        # A janela cobre as CASAS ini..fim; a casa N ocupa a faixa (N-1, N)
        borda_esq = max(0, min(janela[0] - 1, estado.NUM_CASAS))
        borda_dir = max(0, min(janela[1], estado.NUM_CASAS))
        if borda_dir <= borda_esq:
            continue
        x_ini = rect_braco.x + borda_esq * espaco_casas
        largura_janela = (borda_dir - borda_esq) * espaco_casas
        realce = pygame.Surface((int(largura_janela), rect_braco.height),
                                pygame.SRCALPHA)
        realce.fill(ds.com_alpha(cor_acorde, 14 if apagado else 46))
        tela.blit(realce, (int(x_ini), rect_braco.y))
        pygame.draw.rect(tela, ds.rgb(ds.misturar(cor_acorde, TEMA.madeira, 0.6)
                                      if apagado else cor_acorde),
                         (int(x_ini), rect_braco.y, int(largura_janela),
                          rect_braco.height), 1 if apagado else 2,
                         border_radius=ds.RAIO_SM)

        etiqueta = str(acorde.get('rotulo', ''))
        fonte_etq = fontes['pequena']
        larg_etq = fonte_etq.size(etiqueta)[0] + ds.ESPACO_MD
        if etiqueta and larg_etq < largura_janela:
            # As etiquetas se empilham quando ha mais de um acorde na regiao
            rect_etq = pygame.Rect(int(x_ini) + 4, 0, larg_etq,
                                   fonte_etq.get_height() + 4)
            rect_etq.centery = rect_braco.y
            while rect_etq.collidelist(etiquetas_usadas) != -1:
                rect_etq.y += rect_etq.height + 2
            etiquetas_usadas.append(rect_etq.copy())
            # Desenhadas depois das notas, para nenhuma bolinha cobrir o nome
            etiquetas_pendentes.append((rect_etq, etiqueta, fonte_etq,
                                        cor_acorde, apagado))

    # --- Trastes e numeracao ----------------------------------------------
    # A numeracao some quando as casas ficam estreitas demais para o texto
    fonte_casas = fontes['pequena']
    mostrar_numeros = espaco_casas >= 16
    if mostrar_numeros and espaco_casas < 24:
        fonte_casas = fontes.get('micro') or fontes['pequena']
    cor_traste = ds.clarear(TEMA.traste, 0.1)
    for casa in range(estado.NUM_CASAS + 1):
        x = rect_braco.x + casa * espaco_casas
        if casa == 0:
            # Pestana: mais larga e clara
            pygame.draw.rect(tela, ds.rgb(ds.clarear(TEMA.corda, 0.35)),
                             (x - 2, rect_braco.y, 5, rect_braco.height))
        else:
            pygame.draw.line(tela, ds.rgb(cor_traste),
                             (x, rect_braco.y), (x, rect_braco.bottom), 2)
            if mostrar_numeros:
                x_num = x - espaco_casas / 2
                marcada = casa in CASAS_MARCADAS or casa in CASAS_DUPLO_MARCADOR
                ds.texto_em(tela, str(casa), fonte_casas,
                            (x_num, rect_braco.bottom + 9),
                            TEMA.acento if marcada else TEMA.texto_apagado,
                            ancora='midtop')

    # --- Contexto harmonico -----------------------------------------------
    modo_texto = configs.get_modo_texto() if configs else 'letras'
    cor_base_escala = configs.get_cor_notas() if configs else TEMA.texto
    tom_global = getattr(meu_campo_harmonico, 'tom',
                         getattr(meu_campo_harmonico, 'tonica', estado.tom_atual))
    estado.tom_atual = tom_global
    nome_escala = getattr(meu_campo_harmonico, 'tipo_escala',
                          getattr(meu_campo_harmonico, 'tipo', '')).lower()
    escala_menor = any(x in nome_escala for x in
                       ['menor', 'eolia', 'eólia', 'dorico', 'dórico',
                        'frigio', 'frígio', 'locrio', 'lócrio'])
    terca_global = escalas.obter_terca(tom_global, menor=escala_menor)
    quinta_global = escalas.obter_quinta(tom_global)

    acorde_ativo = meu_campo_harmonico.indice_acorde_selecionado != -1
    notas_acorde = meu_campo_harmonico.notas_acorde_selecionado
    tom_ref = notas_acorde[0] if acorde_ativo else tom_global
    nota_microfone = estado.nota_atual_detectada

    # --- Filtro de acordes (definido pelo painel da aba ACORDES) ----------
    filtro_acordes = bool(acordes_braco)

    acordes_cor = ([a for a in acordes_braco if a.get('rotulo') in foco_acordes]
                   if foco_acordes else acordes_braco)

    def _acordes_da_posicao(casa_atual, nome_nota):
        """[(grau, cor)] dos acordes que contem esta nota nesta casa."""
        achados = []
        # Acorde posto numa regiao manda nela; o do braco inteiro vem depois
        for item in sorted(acordes_cor, key=lambda a: not a.get('janela')):
            faixa = item.get('janela')
            if faixa and not (faixa[0] <= casa_atual <= faixa[1]):
                continue
            grau_item = (item.get('notas') or {}).get(nome_nota)
            if grau_item:
                achados.append((grau_item, item.get('cor') or TEMA.acento))
        return achados

    # --- Cordas e notas ----------------------------------------------------
    # As bolinhas acompanham o tamanho do bloco: nunca maiores que a casa
    # nem que o espaco entre cordas.
    escala_nota = configs.get_escala_nota() if configs else 1.0
    raio_base = int(min(espaco_casas * 0.42, estado.ESPACO_CORDAS * 0.46,
                        GUITAR_RAIO_NOTA) * escala_nota)
    raio_base = max(5, raio_base)
    mostrar_rotulo = raio_base >= 8

    for i in range(num_cordas):
        if instrumento == 'baixo':
            y = rect_braco.bottom - 15 - i * estado.ESPACO_CORDAS
        else:
            y = rect_braco.bottom - i * estado.ESPACO_CORDAS

        espessura = 1 + i // 3
        pygame.draw.line(tela, ds.rgb(ds.escurecer(TEMA.corda, 0.55)),
                         (rect_braco.x, y + 1), (rect_braco.right, y + 1), espessura)
        pygame.draw.line(tela, ds.rgb(TEMA.corda),
                         (rect_braco.x, y), (rect_braco.right, y), espessura)

        nota_aberta = notas_abertas[i if instrumento != 'baixo' else i + 2]

        for casa in range(estado.NUM_CASAS + 1):
            nota = escalas.obter_nota(nota_aberta, casa)
            no_acorde = True
            alpha, raio = GUITAR_ALPHA_NORMAL, raio_base

            if acorde_ativo and nota not in notas_acorde:
                no_acorde = False
                alpha, raio = GUITAR_ALPHA_INATIVO, max(6, int(raio_base * 0.75))

            # Filtro dos acordes sobrepostos no braco
            grau_acorde = cor_acorde_nota = None
            cores_extras = []
            if filtro_acordes:
                achados = _acordes_da_posicao(casa, nota)
                if achados:
                    grau_acorde, cor_acorde_nota = achados[0]
                    # Nota em comum: um anel por acorde a mais que tambem a tem
                    cores_extras = [cor for _g, cor in achados[1:4]]
                if grau_acorde is None:
                    no_acorde = False
                    alpha, raio = GUITAR_ALPHA_INATIVO, max(5, int(raio_base * 0.6))

            x_nota = (rect_braco.x - calha / 2 if casa == 0
                      else rect_braco.x + casa * espaco_casas - espaco_casas / 2)

            cor_fundo = cor_base_escala
            if grau_acorde is not None:
                cor_fundo = cor_acorde_nota
            elif no_acorde:
                ref_tonica = notas_acorde[0] if acorde_ativo else tom_global
                ref_terca = (notas_acorde[1] if acorde_ativo and len(notas_acorde) > 1
                             else terca_global)
                ref_quinta = (notas_acorde[2] if acorde_ativo and len(notas_acorde) > 2
                              else quinta_global)
                if nota == ref_tonica:
                    cor_fundo = CORES_TONICA[estado.indice_cor_tonica]
                elif nota == ref_terca:
                    cor_fundo = CORES_TONICA[estado.indice_cor_terca]
                elif nota == ref_quinta:
                    cor_fundo = CORES_TONICA[estado.indice_cor_quinta]

            tocando = bool(nota_microfone and equivalencia_notas(nota_microfone, nota))
            if tocando:
                cor_fundo = TEMA.aviso
                raio = int(raio_base * 1.25)
                alpha = GUITAR_ALPHA_NORMAL

            lado = (raio + 3 * len(cores_extras)) * 2 + 8
            s = pygame.Surface((lado, lado), pygame.SRCALPHA)
            centro = lado // 2

            if tocando:
                pygame.draw.circle(s, ds.com_alpha(TEMA.aviso, 90), (centro, centro),
                                   raio + 4)
            else:
                pygame.draw.circle(s, (0, 0, 0, alpha // 3), (centro, centro + 1), raio)

            pygame.draw.circle(s, (*ds.rgb(cor_fundo), alpha), (centro, centro), raio)
            cor_contorno = (255, 140, 0) if tocando else ds.escurecer(cor_fundo, 0.45)
            pygame.draw.circle(s, (*ds.rgb(cor_contorno), alpha), (centro, centro),
                               raio, 3 if tocando else 1)
            for k, cor_extra in enumerate(cores_extras):
                pygame.draw.circle(s, (*ds.rgb(cor_extra), alpha), (centro, centro),
                                   raio + 3 * (k + 1), 2)
            tela.blit(s, (int(x_nota - centro), int(y - centro)))

            if modo_texto != 'vazio' and mostrar_rotulo:
                if grau_acorde is not None:
                    rotulo = grau_acorde
                elif modo_texto == 'letras':
                    rotulo = nota
                else:
                    rotulo = obter_grau(tom_ref, nota)
                fonte = fontes['pequena' if raio < 15 else 'notas']
                surf = fonte.render(rotulo, True, ds.contraste_texto(cor_fundo))
                surf.set_alpha(alpha)
                tela.blit(surf, (x_nota - surf.get_width() / 2,
                                 y - surf.get_height() / 2))

    for rect_etq, etiqueta, fonte_etq, cor_acorde, apagado in etiquetas_pendentes:
        cor_fundo = ds.misturar(cor_acorde, TEMA.madeira, 0.55) if apagado else cor_acorde
        pygame.draw.rect(tela, ds.rgb(cor_fundo), rect_etq, border_radius=ds.RAIO_SM)
        ds.texto_centralizado(tela, etiqueta, fonte_etq, rect_etq,
                              ds.contraste_texto(cor_fundo))

    if estado.drag_ativado:
        alvo.desenhar_caixa_selecao(tela, margem=15)
