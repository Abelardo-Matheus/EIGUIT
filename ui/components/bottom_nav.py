# -*- coding: utf-8 -*-
"""Barra inferior expansivel: Escalas, Acordes, Estudos, Musicas, IA e Config."""
import pygame

from config.theme import *
from config.ui_metrics import *
from config.app_settings import *
from config.design_system import TEMA, ds
from ui.blocks.painel_acordes import painel_da_sub_aba
from core.i18n import _t
from ui.components.config_componentes import (
    BOTTOM_MARGIN_X, CONFIG_OFFSET_Y_INTERNO, ESTUDOS_OFFSET_Y_INTERNO,
    ESTUDOS_DESC_OFFSET_X, BOTTOM_OFFSET_AREA_DESENHO,
)

GAP_PAINEL = 10

# A gaveta aberta ocupa uma fatia do viewport, entre um piso e um teto. O
# controlador de eventos chama altura_caixa() para achar exatamente a mesma
# geometria na hora de tratar clique e scroll.
FRACAO_CAIXA = 0.62
ALTURA_CAIXA_MIN = 280
ALTURA_CAIXA_MAX = 760

# Medidas base do conteudo, para a caixa de 280. Crescem junto com a gaveta.
ALTURA_SUB_ABA_BASE = 30
ALTURA_ITEM_LISTA_BASE = 44
ESCALA_MINIATURA_BASE = 0.28
FATOR_MAXIMO = 1.7

# Tamanho de uma miniatura de escala em escala 1.0, e o respiro entre elas
MINIATURA_W = 535
MINIATURA_H = 321
MINIATURA_GAP_X = 178
MINIATURA_GAP_Y = 285

# Medidas deste quadro, atualizadas no inicio do desenho e lidas pelas funcoes
# de cada aba logo em seguida.
ALTURA_SUB_ABA = ALTURA_SUB_ABA_BASE
ALTURA_ITEM_LISTA = ALTURA_ITEM_LISTA_BASE

# Barra fixa no rodape: altura e respiro ate a borda
ALTURA_BARRA = 40
MARGEM_BARRA = 10


def altura_caixa(estado):
    """
        Como funciona: Da a altura da gaveta aberta a partir da altura do
        viewport, presa entre o piso e o teto e limitada pelo espaco que existe
        acima da barra.
        Para que serve: A gaveta abrir grande em tela grande, sem nunca passar
        por cima da barra de abas nem sair da tela.
        Onde e usada: Desenho da barra inferior e o teste de clique e scroll no
        controlador de eventos, que precisam da mesma geometria.
    """
    from config.ui_metrics import ALTURA_TOPBAR
    viewport = max(320, int(getattr(estado, 'ALTURA_TELA', 1080)) - ALTURA_TOPBAR)
    barra = getattr(estado, 'dragger_painel_inferior', None)
    espaco = getattr(barra, 'y', viewport) - GAP_PAINEL - MARGEM_BARRA
    alvo = min(viewport * FRACAO_CAIXA, ALTURA_CAIXA_MAX)
    return int(max(ALTURA_CAIXA_MIN, min(alvo, max(ALTURA_CAIXA_MIN, espaco))))


def _atualizar_medidas(altura):
    """Cresce o conteudo da gaveta na mesma proporcao em que ela cresceu."""
    global ALTURA_SUB_ABA, ALTURA_ITEM_LISTA
    fator = min(FATOR_MAXIMO, max(1.0, altura / ALTURA_CAIXA_MIN))
    ALTURA_SUB_ABA = int(ALTURA_SUB_ABA_BASE * fator)
    ALTURA_ITEM_LISTA = int(ALTURA_ITEM_LISTA_BASE * fator)
    return fator


def arranjo_miniaturas(quantidade, largura, altura, escala_maxima=1.1):
    """
        Como funciona: Testa cada quantidade de colunas possivel e ve ate onde
        as miniaturas podem crescer naquela grade, na largura e na altura.
        Fica com a maior escala e, entre arranjos parecidos, com o que usa
        menos linhas.
        Para que serve: A gaveta grande mostrar as formas grandes e cheias,
        em vez de miniaturas pequenas com meia gaveta vazia.
        Onde e usada: Aba ESCALAS.

        Devolve (escala, colunas).
    """
    quantidade = max(1, quantidade)
    largura_util = max(120, largura - 40)
    altura_util = max(80, altura - 45)

    melhor = (ESCALA_MINIATURA_BASE, quantidade)
    for colunas in range(1, quantidade + 1):
        linhas = -(-quantidade // colunas)
        por_largura = largura_util / (colunas * MINIATURA_W
                                      + (colunas - 1) * MINIATURA_GAP_X)
        por_altura = altura_util / (linhas * MINIATURA_H
                                    + (linhas - 1) * MINIATURA_GAP_Y)
        escala = min(por_largura, por_altura, escala_maxima)
        if escala > melhor[0] * 1.02:
            melhor = (escala, colunas)
        elif escala > melhor[0] * 0.98 and linhas < -(-quantidade // melhor[1]):
            melhor = (max(escala, melhor[0]), colunas)
    return round(max(melhor[0], ESCALA_MINIATURA_BASE), 3), melhor[1]


def fixar_barra(estado, largura_tela, altura_viewport):
    """
        Como funciona: Prende a barra de abas no rodape, com a largura toda
        menos a faixa da coluna do gaveteiro.
        Para que serve: A barra e o unico movel da tela que nao se move: e a
        referencia de onde a gaveta abre.
        Onde e usada: Inicio do desenho da barra inferior, a cada quadro.
    """
    from config.layout_padrao import MARGEM_ESQUERDA, MARGEM_DIREITA
    barra = getattr(estado, 'dragger_painel_inferior', None)
    if barra is None:
        return None
    barra.arrastando = False
    barra.redimensionando = False
    barra.x = MARGEM_ESQUERDA
    barra.largura = max(240, largura_tela - MARGEM_ESQUERDA - MARGEM_DIREITA)
    barra.altura = max(32, min(ALTURA_BARRA, barra.altura))
    barra.y = max(0, altura_viewport - barra.altura - MARGEM_BARRA)
    if hasattr(barra, 'rect_caixa'):
        barra.rect_caixa.update(barra.x, barra.y, barra.largura, barra.altura)
    # Mesma conta do estado inicial, para os paineis de escala continuarem
    # sendo montados na altura certa
    from ui.components.config_componentes import BOTTOM_Y_AREA_DESENHO_OFFSET
    estado.Y_AREA_DESENHO = barra.y - BOTTOM_Y_AREA_DESENHO_OFFSET
    return barra


def quebrar_texto(texto, fonte, max_largura):
    """
        Como funciona: Quebra um texto em linhas que caibam na largura dada.
        Para que serve: Descricoes multilinha nos cartoes de estudo.
        Onde e usada: Aba de Estudos e listas com texto longo.
    """
    palavras = texto.split(' ')
    linhas = []
    linha_atual = ''
    for palavra in palavras:
        teste = linha_atual + palavra + ' '
        if fonte.size(teste)[0] < max_largura:
            linha_atual = teste
        else:
            if linha_atual:
                linhas.append(linha_atual)
            linha_atual = palavra + ' '
    linhas.append(linha_atual)
    return linhas


def _cartao_acao(tela, rect, titulo, descricao, fontes, largura_texto, x_desc):
    """Botao de acao a esquerda com descricao explicativa a direita."""
    ds.botao(tela, rect, titulo, fontes['ui'], variante='primario',
             hover=rect.collidepoint(pygame.mouse.get_pos()))
    altura_linha = fontes['pequena'].get_height() + 3
    linhas = quebrar_texto(descricao, fontes['pequena'], largura_texto)
    # Descricao centrada na altura do botao, que cresce junto com a gaveta
    y = rect.centery - (len(linhas) * altura_linha) // 2
    for linha in linhas:
        ds.texto_em(tela, linha, fontes['pequena'], (x_desc, y), TEMA.texto_suave)
        y += altura_linha


def _desenhar_aba_ia(tela, dx, y_start, estado, fontes, meu_processador,
                     meu_gravador, meu_gerenciador_jogos, memoria_sub_aba, configs):
    """Sub-abas de Analise de IA (afinador avancado e jogos)."""
    if memoria_sub_aba == 0:
        try:
            notas_abertas = lista_afinacoes[estado.indice_afinacao]['notas']
        except (IndexError, KeyError, TypeError):
            notas_abertas = ['E', 'A', 'D', 'G', 'B', 'E', 'B']
        meu_processador.desenhar_aba_ia(tela, dx, y_start, meu_gravador,
                                        fontes['ui'], fontes['titulo'],
                                        notas_abertas, estado)
    elif memoria_sub_aba == 1:
        meu_gerenciador_jogos.desenhar_aba_jogos(tela, dx, y_start, fontes['ui'])


def _desenhar_aba_configuracao(tela, dx, y_start, largura_conteudo, estado,
                               fontes, configs, meu_metronomo, memoria_sub_aba,
                               scroll_y):
    """Sub-abas de Configuracoes (aparencia e metronomo)."""
    if memoria_sub_aba == 0:
        configs.y = y_start + CONFIG_OFFSET_Y_INTERNO
        configs.x = dx + BOTTOM_MARGIN_X
        configs.desenhar(tela, fontes, 0, largura_max=largura_conteudo)
    else:
        meu_metronomo.y = y_start + CONFIG_OFFSET_Y_INTERNO
        meu_metronomo.x = dx + BOTTOM_MARGIN_X
        if hasattr(meu_metronomo, 'x_config'):
            meu_metronomo.x_config = dx + BOTTOM_MARGIN_X
        meu_metronomo.desenhar_config(tela, fontes['ui'], 0, configs)


def _desenhar_aba_estudos(tela, dx, y_start, largura_conteudo, estado, fontes,
                          memoria_sub_aba, configs, altura_util=None):
    """Cartoes de exercicio, um por modalidade de estudo."""
    estado.botoes_estudo.clear()
    fator = ALTURA_ITEM_LISTA / ALTURA_ITEM_LISTA_BASE
    largura_botao = int(178 * fator)
    x_desc = dx + BOTTOM_MARGIN_X + largura_botao + ds.ESPACO_XL
    largura_texto = largura_conteudo - (x_desc - dx) - BOTTOM_MARGIN_X

    grupos = {
        0: [
            (_t('Acerte a Nota'), _t('Treine seu mapeamento visual: descubra qual nota esta escondida em uma casa especifica do braco.')),
            (_t('Acerte o Som'), _t('Treinamento de percepcao absoluta: escute a frequencia gerada e identifique a nota pelo som.')),
            (_t('Acerte a Proxima'), _t('Domine os intervalos calculando saltos de distancia (unissono, 2a, 3a, 4a, 5a, 6a e 7a).')),
        ],
        1: [(_t('Acerte a Escala'), _t('Pratique shapes e digitacoes: encontre todas as notas que pertencem a escala solicitada.'))],
        2: [(_t('Pratica de Acordes'), _t('IA em tempo real: toque o acorde completo e a IA valida se as notas estao certas.'))],
        3: [(_t('Ciclo de Quintas'), _t('Domine a harmonia: relacoes entre tonalidades, armaduras de clave e progressoes quartais.'))],
        4: [
            (_t('Padrões'), _t('Padroes melodicos sobre a escala (tercas, quartas, grupos de quatro, arpejos) e celulas ritmicas classicas, no andamento que voce escolher.')),
        ],
        5: [
            (_t('Improvisação'), _t('Progressao rodando, notas alvo de cada acorde, escala que serve, notas a evitar e vocabulario de frases.')),
        ],
    }

    itens = grupos.get(memoria_sub_aba, [])
    altura_item = int(52 * fator)
    # Os cartoes se espalham pela altura da gaveta em vez de se amontoarem
    # no topo, com um respiro maximo para nao ficarem soltos demais
    if altura_util:
        folga = (altura_util - len(itens) * altura_item) / (len(itens) + 1)
        espacamento = int(min(52, max(18, folga)))
    else:
        espacamento = int(22 * fator)
    y = y_start + ESTUDOS_OFFSET_Y_INTERNO + espacamento

    for titulo, descricao in itens:
        rect = pygame.Rect(dx + BOTTOM_MARGIN_X, y, largura_botao, altura_item)
        _cartao_acao(tela, rect, titulo, descricao, fontes, largura_texto, x_desc)
        estado.botoes_estudo[titulo] = rect
        y += altura_item + espacamento
    # Altura real dos cartoes, para so haver rolagem quando faltar espaco
    return y - y_start


def _linha_musica(tela, rect, titulo, subtitulo, fontes, favorita=False):
    """Item de lista para resultados de busca e favoritos."""
    hover = rect.collidepoint(pygame.mouse.get_pos())
    ds.superficie_translucida(
        tela, rect,
        ds.misturar(TEMA.superficie_alt, TEMA.acento, 0.18 if hover else 0.0),
        225, ds.RAIO_MD,
        TEMA.aviso if favorita else TEMA.borda, 1)
    ds.texto_em(tela, titulo, fontes['pequena'],
                (rect.x + ds.ESPACO_MD, rect.centery), TEMA.texto,
                ancora='midleft', largura_max=rect.width - ds.ESPACO_XL)
    if subtitulo:
        ds.texto_em(tela, subtitulo, fontes['pequena'],
                    (rect.right - ds.ESPACO_MD, rect.centery), TEMA.texto_apagado,
                    ancora='midright', largura_max=rect.width // 3)


def _desenhar_aba_musicas(tela, dx, y_start, largura_conteudo, estado, fontes,
                          memoria_sub_aba, configs):
    """Busca no Songsterr, favoritos e arquivos MIDI locais."""
    if memoria_sub_aba == 0:
        # Navegacao interna em pilulas
        y_nav = y_start + ds.ESPACO_SM
        larguras = [110, 110, 140]
        rotulos = [_t('Busca'), _t('Favoritas'), _t('Minhas Musicas')]
        x = dx + BOTTOM_MARGIN_X
        rects_nav = []
        for i, (larg, rot) in enumerate(zip(larguras, rotulos)):
            r = pygame.Rect(x, y_nav, larg, 30)
            ds.chip(tela, r, rot, fontes['pequena'],
                    ativo=estado.sub_memoria_musicas == i)
            rects_nav.append(r)
            x += larg + ds.ESPACO_SM
        (estado.rect_aba_songsterr_busca,
         estado.rect_aba_songsterr_favs,
         estado.rect_aba_songsterr_locais) = rects_nav

        y_conteudo = y_nav + 30 + ds.ESPACO_MD

        if estado.sub_memoria_musicas == 0:
            # Campo de busca + botao
            largura_btn = 100
            rect_busca = pygame.Rect(dx + BOTTOM_MARGIN_X, y_conteudo,
                                     largura_conteudo - BOTTOM_MARGIN_X * 2 - largura_btn - ds.ESPACO_SM,
                                     32)
            estado.rect_busca_songsterr = rect_busca
            ds.caixa_texto(tela, rect_busca, estado.query_songsterr, fontes['pequena'],
                           focado=getattr(estado, 'songsterr_search_active', False),
                           placeholder=_t('Clique para digitar...'))
            rect_btn = pygame.Rect(rect_busca.right + ds.ESPACO_SM, y_conteudo,
                                   largura_btn, 32)
            estado.rect_btn_songsterr = rect_btn
            ds.botao(tela, rect_btn, _t('Buscar'), fontes['pequena'],
                     hover=rect_btn.collidepoint(pygame.mouse.get_pos()))

            y_lista = rect_busca.bottom + ds.ESPACO_MD
            largura_lista = largura_conteudo - BOTTOM_MARGIN_X * 2 - 48

            if estado.songsterr.carregando:
                ds.texto_em(tela, _t('Carregando...'), fontes['pequena'],
                            (dx + BOTTOM_MARGIN_X, y_lista), TEMA.acento)
            elif not estado.resultados_songsterr:
                ds.cartao_vazio(tela,
                                pygame.Rect(dx + BOTTOM_MARGIN_X, y_lista,
                                            largura_conteudo - BOTTOM_MARGIN_X * 2, 56),
                                _t('Nenhum resultado. Digite e clique em Buscar.'),
                                fontes['pequena'])
            else:
                estado.rects_resultados_songsterr = []
                estado.rects_favoritos_click = []
                for i, song in enumerate(estado.resultados_songsterr[:5]):
                    y_item = y_lista + i * (ALTURA_ITEM_LISTA + 4)
                    rect_item = pygame.Rect(dx + BOTTOM_MARGIN_X, y_item,
                                            largura_lista, ALTURA_ITEM_LISTA)
                    estado.rects_resultados_songsterr.append((rect_item, song))
                    _linha_musica(tela, rect_item, song.get('title', 'Unknown'),
                                  song.get('artist', ''), fontes)

                    favorita = any(f.get('songId') == song.get('songId')
                                   for f in estado.favoritos_songsterr)
                    rect_estrela = pygame.Rect(rect_item.right + ds.ESPACO_SM,
                                               y_item, ALTURA_ITEM_LISTA,
                                               ALTURA_ITEM_LISTA)
                    ds.superficie_translucida(tela, rect_estrela,
                                              TEMA.superficie_alt, 220, ds.RAIO_MD,
                                              TEMA.aviso if favorita else TEMA.borda, 1)
                    ds.texto_centralizado(tela, '*' if favorita else 'o',
                                          fontes['titulo'], rect_estrela,
                                          TEMA.aviso if favorita else TEMA.texto_apagado)
                    estado.rects_favoritos_click.append((rect_estrela, song))

        elif estado.sub_memoria_musicas == 1:
            y_lista = y_conteudo
            if not estado.favoritos_songsterr:
                ds.cartao_vazio(tela,
                                pygame.Rect(dx + BOTTOM_MARGIN_X, y_lista,
                                            largura_conteudo - BOTTOM_MARGIN_X * 2, 56),
                                _t('Voce ainda nao salvou nenhuma musica.'),
                                fontes['pequena'])
            else:
                estado.rects_resultados_songsterr = []
                estado.rects_favoritos_click = []
                largura_lista = largura_conteudo - BOTTOM_MARGIN_X * 2 - 48
                for i, song in enumerate(estado.favoritos_songsterr):
                    y_item = y_lista + i * (ALTURA_ITEM_LISTA + 4)
                    rect_item = pygame.Rect(dx + BOTTOM_MARGIN_X, y_item,
                                            largura_lista, ALTURA_ITEM_LISTA)
                    estado.rects_resultados_songsterr.append((rect_item, song))
                    _linha_musica(tela, rect_item, song.get('title', 'Unknown'),
                                  song.get('artist', ''), fontes, favorita=True)
                    rect_estrela = pygame.Rect(rect_item.right + ds.ESPACO_SM,
                                               y_item, ALTURA_ITEM_LISTA,
                                               ALTURA_ITEM_LISTA)
                    ds.superficie_translucida(tela, rect_estrela, TEMA.superficie_alt,
                                              220, ds.RAIO_MD, TEMA.aviso, 1)
                    ds.texto_centralizado(tela, '*', fontes['titulo'], rect_estrela,
                                          TEMA.aviso)
                    estado.rects_favoritos_click.append((rect_estrela, song))

        else:
            y_lista = y_conteudo
            rect_add = pygame.Rect(dx + BOTTOM_MARGIN_X, y_lista, 200, 34)
            estado.rect_btn_add_midi = rect_add
            ds.botao(tela, rect_add, _t('Selecionar MIDI'), fontes['pequena'],
                     icone='+', hover=rect_add.collidepoint(pygame.mouse.get_pos()))
            ds.texto_em(tela, _t('(ou arraste um arquivo .mid para ca)'),
                        fontes['pequena'],
                        (rect_add.right + ds.ESPACO_MD, rect_add.centery),
                        TEMA.texto_apagado, ancora='midleft')

            y_lista += 48
            if not estado.musicas_locais:
                ds.cartao_vazio(tela,
                                pygame.Rect(dx + BOTTOM_MARGIN_X, y_lista,
                                            largura_conteudo - BOTTOM_MARGIN_X * 2, 56),
                                _t('Nenhum MIDI local adicionado.'), fontes['pequena'])
            else:
                estado.rects_musicas_locais = []
                for i, song in enumerate(estado.musicas_locais):
                    y_item = y_lista + i * (ALTURA_ITEM_LISTA + 4)
                    rect_item = pygame.Rect(dx + BOTTOM_MARGIN_X, y_item,
                                            largura_conteudo - BOTTOM_MARGIN_X * 2,
                                            ALTURA_ITEM_LISTA)
                    estado.rects_musicas_locais.append((rect_item, song))
                    _linha_musica(tela, rect_item, song.get('title', 'Arquivo MIDI'),
                                  'MIDI', fontes)

    elif memoria_sub_aba == 1:
        ds.cartao_vazio(tela,
                        pygame.Rect(dx + BOTTOM_MARGIN_X, y_start + 60,
                                    largura_conteudo - BOTTOM_MARGIN_X * 2, 70),
                        _t('Minhas Musicas (em breve)'), fontes['ui'])

    elif memoria_sub_aba == 2:
        ds.texto_em(tela, _t('Area de Musica'), fontes['titulo'],
                    (dx + largura_conteudo // 2, y_start + 40), TEMA.texto,
                    ancora='center')
        ds.texto_em(tela, _t('Criacao Musical'), fontes['pequena'],
                    (dx + largura_conteudo // 2, y_start + 68), TEMA.texto_suave,
                    ancora='center')
        rect_btn = pygame.Rect(dx + largura_conteudo // 2 - 100, y_start + 96, 200, 40)
        estado.rect_btn_criar_tablatura = rect_btn
        ds.botao(tela, rect_btn, _t('Criar Tablatura'), fontes['ui'],
                 hover=rect_btn.collidepoint(pygame.mouse.get_pos()))


def desenhar_secoes_inferiores_expansiveis(tela, estado, configs, dicionario_escalas,
                                           fontes, meu_metronomo, meu_processador,
                                           meu_gravador, meu_gerenciador_jogos):
    """
        Como funciona: Desenha a fileira de botoes-pilula e, quando uma secao
        esta expandida, o painel com sub-abas, conteudo rolavel e scrollbar.
        Para que serve: Navegacao principal entre os modulos do estudio.
        Onde e usada: Chamada pelo renderizador do workspace.
    """
    if not hasattr(estado, 'dragger_painel_inferior'):
        return

    if configs is not None:
        TEMA.definir_acento(configs.get_cor_tema())

    # O filtro do braco so vale enquanto a aba CAGED estiver aberta
    acordes_visivel = any(sec.get('expandido') and sec['conteudo'] == 'acordes'
                          for sec in estado.secoes_inferiores)
    if not acordes_visivel:
        # Fora da aba, so os acordes fixados continuam no braco
        estado.acordes_no_braco = list(getattr(estado, 'acordes_fixados', []))

    alpha_atual = configs.get_alpha() if configs else 255
    # A barra e fixa no rodape e a gaveta cresce com a tela
    fixar_barra(estado, tela.get_width(), tela.get_height())
    ALTURA_CAIXA = altura_caixa(estado)
    _atualizar_medidas(ALTURA_CAIXA)
    dragger = estado.dragger_painel_inferior
    dx, dy = dragger.x, dragger.y
    largura_conteudo = dragger.largura
    altura_dragger = dragger.altura
    pos_mouse = pygame.mouse.get_pos()

    # Braco de referencia para os shapes que saem do painel
    pos_x_guit = getattr(getattr(estado, 'dragger_guitarra', None), 'x', 100)
    pos_y_guit = getattr(getattr(estado, 'dragger_guitarra', None), 'y', 90)
    instrumento = getattr(estado, 'instrumento', 'guitarra')
    offset_y_guit = pos_y_guit + estado.ESPACO_CORDAS if instrumento == 'baixo' else pos_y_guit
    altura_guit = (estado.ALTURA_BRACO - 2 * estado.ESPACO_CORDAS
                   if instrumento == 'baixo' else estado.ALTURA_BRACO)
    rect_braco_real = pygame.Rect(pos_x_guit, offset_y_guit,
                                  estado.LARGURA_BRACO, altura_guit)

    tela.set_clip(None)
    for lista_modulos in dicionario_escalas.values():
        for modulo in lista_modulos:
            if modulo.estado != 'painel':
                modulo.x_braco = pos_x_guit
                modulo.y_braco = offset_y_guit
                modulo.atualizar_e_desenhar(tela, pos_mouse, rect_braco_real,
                                            fontes['pequena'], alpha_atual,
                                            estado=estado)

    # --- Fileira de botoes principais -------------------------------------
    num_secoes = len(estado.secoes_inferiores)
    gap = ds.ESPACO_SM
    largura_botao = (largura_conteudo - gap * (num_secoes - 1)) / num_secoes

    for i, secao in enumerate(estado.secoes_inferiores):
        x_botao = dx + i * (largura_botao + gap)
        rect_cabecalho = pygame.Rect(x_botao, dy, largura_botao, altura_dragger)
        secao['rect_cabecalho'] = rect_cabecalho

        ds.chip(tela, rect_cabecalho, _t(secao['titulo']), fontes['pequena'],
                ativo=secao['expandido'])

        if not secao['expandido']:
            continue

        # --- Painel expandido ---------------------------------------------
        y_conteudo = dy - ALTURA_CAIXA - GAP_PAINEL
        rect_painel = pygame.Rect(dx, y_conteudo, largura_conteudo, ALTURA_CAIXA)
        # Guardado para o teste de clique conferir que a geometria bate
        secao['rect_painel'] = rect_painel
        ds.painel(tela, rect_painel, None, None, acento=TEMA.acento, alpha=255)

        # Sub-abas
        y_sub = y_conteudo + GAP_PAINEL
        altura_sub = ALTURA_SUB_ABA
        if secao['sub_abas']:
            num_sub = len(secao['sub_abas'])
            espaco_total = largura_conteudo - BOTTOM_MARGIN_X * 2
            largura_sub = (espaco_total - (num_sub - 1) * ds.ESPACO_XS) / num_sub
            for j, nome_sub in enumerate(secao['sub_abas']):
                rect_sub = pygame.Rect(dx + BOTTOM_MARGIN_X + j * (largura_sub + ds.ESPACO_XS),
                                       y_sub, largura_sub, altura_sub)
                secao[f'rect_sub_{j}'] = rect_sub
                ds.chip(tela, rect_sub, _t(nome_sub), fontes['pequena'],
                        ativo=secao['memoria_sub_aba'] == j)

        # Area rolavel. y_area fica exatamente em
        # y_conteudo + BOTTOM_OFFSET_AREA_DESENHO, o mesmo ponto que o
        # controlador de eventos assume ao tratar cliques e scroll.
        y_area = y_conteudo + BOTTOM_OFFSET_AREA_DESENHO
        altura_util = ALTURA_CAIXA - BOTTOM_OFFSET_AREA_DESENHO - ds.ESPACO_MD
        rect_clip = pygame.Rect(dx + ds.ESPACO_XS, y_area,
                                largura_conteudo - ds.ESPACO_SM, altura_util)

        tela.set_clip(rect_clip)
        scroll_atual = estado.scroll_y.get(i, 0)
        y_start = y_area - scroll_atual

        if secao['conteudo'] == 'acordes':
            # Todas as sub-abas de acordes usam o mesmo painel de braco
            painel_da_sub_aba(secao['memoria_sub_aba']).desenhar(
                tela,
                pygame.Rect(rect_clip.x + BOTTOM_MARGIN_X, y_area,
                            rect_clip.width - BOTTOM_MARGIN_X * 2, altura_util),
                fontes, estado.campo_harmonico_ref, estado)
            estado.max_scroll[i] = 0

        elif secao['conteudo'] == 'escalas':
            chaves = ['maior', 'menor', 'penta_maior', 'penta_menor', 'blues',
                      'modos', 'harmonica', 'melodica', 'exoticas']
            if secao['memoria_sub_aba'] < len(chaves):
                lista_ativa = dicionario_escalas.get(chaves[secao['memoria_sub_aba']], [])
                altura_total = 0
                # A maior escala em que as formas ainda cabem todas de uma vez
                quantas = sum(1 for m in lista_ativa if m.estado == 'painel')
                escala_compacta, colunas = arranjo_miniaturas(
                    quantas, largura_conteudo, altura_util)
                largura_bloco = int(MINIATURA_W * escala_compacta)
                altura_bloco = int(MINIATURA_H * escala_compacta)
                esp_x = int(MINIATURA_GAP_X * escala_compacta)
                esp_y = int(MINIATURA_GAP_Y * escala_compacta)
                largura_grade = colunas * largura_bloco + (colunas - 1) * esp_x
                offset_x = (largura_conteudo - largura_grade) // 2

                for idx, modulo in enumerate(lista_ativa):
                    if modulo.estado != 'painel':
                        continue
                    if getattr(modulo, 'escala_atual_painel', None) != escala_compacta:
                        surf_orig = getattr(modulo, 'imagem_braco', modulo.imagem_painel)
                        modulo.imagem_painel = pygame.transform.scale(
                            surf_orig,
                            (int(surf_orig.get_width() * escala_compacta),
                             int(surf_orig.get_height() * escala_compacta)))
                        modulo.escala_atual_painel = escala_compacta
                        modulo.rect_painel = modulo.imagem_painel.get_rect()

                    col, lin = idx % colunas, idx // colunas
                    modulo.rect_painel.x = dx + offset_x + col * (largura_bloco + esp_x)
                    modulo.rect_painel.y = y_start + 45 + lin * (altura_bloco + esp_y)
                    # Altura real do conteudo: sem respiro sobrando na ultima
                    # linha, para nao inventar rolagem em gaveta que ja mostra
                    # tudo
                    altura_total = max(altura_total,
                                       45 + (lin + 1) * altura_bloco + lin * esp_y)
                    modulo.atualizar_e_desenhar(tela, pos_mouse, rect_braco_real,
                                                fontes['pequena'], alpha_atual,
                                                estado=estado)

                estado.max_scroll[i] = max(0, altura_total - altura_util)

        elif secao['conteudo'] == 'analise_ia':
            _desenhar_aba_ia(tela, dx, y_start, estado, fontes, meu_processador,
                             meu_gravador, meu_gerenciador_jogos,
                             secao['memoria_sub_aba'], configs)
        elif secao['conteudo'] == 'configuracao':
            _desenhar_aba_configuracao(tela, dx, y_start, largura_conteudo, estado,
                                       fontes, configs, meu_metronomo,
                                       secao['memoria_sub_aba'], scroll_atual)
        elif secao['conteudo'] == 'estudos':
            alto = _desenhar_aba_estudos(tela, dx, y_start, largura_conteudo,
                                         estado, fontes, secao['memoria_sub_aba'],
                                         configs, altura_util)
            estado.max_scroll[i] = max(0, alto - altura_util)
        elif secao['conteudo'] == 'musicas':
            _desenhar_aba_musicas(tela, dx, y_start, largura_conteudo, estado,
                                  fontes, secao['memoria_sub_aba'], configs)

        tela.set_clip(None)

        # Scrollbar
        max_scroll = estado.max_scroll.get(i, 0)
        if max_scroll > 0:
            ds.barra_rolagem(tela, dx + largura_conteudo - 14, y_area, altura_util,
                             altura_util / (altura_util + max_scroll),
                             scroll_atual / max_scroll)

    if estado.drag_ativado:
        dragger.desenhar_caixa_selecao(tela, margem=8)
