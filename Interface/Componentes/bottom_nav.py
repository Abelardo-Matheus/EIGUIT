import pygame
from Core.constantes_ui import *
from Core.i18n import _t
from Interface.Componentes.config_componentes import BOTTOM_ALTURA_CAIXA, BOTTOM_OFFSET_AREA_DESENHO, BOTTOM_OFFSET_CLIPPING_Y, BOTTOM_ALTURA_UTIL_DIFF, BOTTOM_MARGIN_X, CONFIG_OFFSET_Y_INTERNO, ESTUDOS_OFFSET_Y_INTERNO, ESTUDOS_DESC_OFFSET_X, BOTTOM_SUBABA_Y_OFFSET, BOTTOM_SUBABA_ALTURA, BOTTOM_SUBABA_MARGIN_X

def quebrar_texto(texto, fonte, max_largura):
    """
        Como funciona: Executa o fluxo lógico necessário para a operação 'quebrar texto'.
        Para que serve: Realiza as tarefas fundamentais de 'quebrar texto' dentro do contexto do módulo.
        Onde é usada: Utilizado internamente para gerenciar comportamentos de 'quebrar texto'.
    """
    palavras = texto.split(' ')
    linhas = []
    linha_atual = ''
    for palavra in palavras:
        teste_linha = linha_atual + palavra + ' '
        if fonte.size(teste_linha)[0] < max_largura:
            linha_atual = teste_linha
        else:
            linhas.append(linha_atual)
            linha_atual = palavra + ' '
    linhas.append(linha_atual)
    return linhas

def _desenhar_aba_ia(tela, dx, y_start, estado, fontes, meu_processador, meu_gravador, meu_gerenciador_jogos, memoria_sub_aba, configs):
    """
        Como funciona: Executa o fluxo lógico necessário para a operação ' desenhar aba ia'.
        Para que serve: Realiza as tarefas fundamentais de ' desenhar aba ia' dentro do contexto do módulo.
        Onde é usada: Utilizado internamente para gerenciar comportamentos de ' desenhar aba ia'.
    """
    cor_tema = configs.get_cor_tema()
    if memoria_sub_aba == 0:
        try:
            notas_abertas = lista_afinacoes[estado.indice_afinacao]['notas']
        except:
            notas_abertas = ['E', 'A', 'D', 'G', 'B', 'E', 'B']
        meu_processador.desenhar_aba_ia(tela, dx, y_start, meu_gravador, fontes['ui'], fontes['titulo'], notas_abertas, estado)
    elif memoria_sub_aba == 1:
        meu_gerenciador_jogos.desenhar_aba_jogos(tela, dx, y_start, fontes['ui'])

def _desenhar_aba_configuracao(tela, dx, y_start, largura_conteudo, estado, fontes, configs, meu_metronomo, memoria_sub_aba, scroll_y):
    """
        Como funciona: Executa o fluxo lógico necessário para a operação ' desenhar aba configuracao'.
        Para que serve: Realiza as tarefas fundamentais de ' desenhar aba configuracao' dentro do contexto do módulo.
        Onde é usada: Utilizado internamente para gerenciar comportamentos de ' desenhar aba configuracao'.
    """
    if memoria_sub_aba == 0:
        configs.y = y_start + CONFIG_OFFSET_Y_INTERNO
        configs.x = dx + BOTTOM_MARGIN_X
        configs.desenhar(tela, fontes, 0, largura_max=largura_conteudo)
    else:
        meu_metronomo.y = y_start + CONFIG_OFFSET_Y_INTERNO
        meu_metronomo.x = dx + BOTTOM_MARGIN_X
        if hasattr(meu_metronomo, 'x_config'):
            meu_metronomo.x_config = dx + BOTTOM_MARGIN_X
        meu_metronomo.desenhar_config(tela, fontes['ui'], 0)

def _desenhar_aba_estudos(tela, dx, y_start, largura_conteudo, estado, fontes, memoria_sub_aba, configs):
    """
        Como funciona: Executa o fluxo lógico necessário para a operação ' desenhar aba estudos'.
        Para que serve: Realiza as tarefas fundamentais de ' desenhar aba estudos' dentro do contexto do módulo.
        Onde é usada: Utilizado internamente para gerenciar comportamentos de ' desenhar aba estudos'.
    """
    cor_tema = configs.get_cor_tema()
    BRANCO = (255, 255, 255)
    estado.botoes_estudo.clear()
    largura_texto_max = largura_conteudo - 240
    if memoria_sub_aba == 0:
        textos = [(_t('Acerte a Nota'), _t('Treine seu mapeamento visual: Descubra qual nota está escondida em uma casa específica do braço.')), (_t('Acerte o Som'), _t('Treinamento de percepção absoluta: Escute a frequência gerada e identifique a nota pelo som.')), (_t('Acerte a Próxima'), _t('Domine os intervalos calculando saltos de distância (Uníssono, 2ª, 3ª, 4ª, 5ª, 6ª e 7ª).'))]
        y_btn = y_start + ESTUDOS_OFFSET_Y_INTERNO
        for titulo_btn, descricao in textos:
            rect_btn = pygame.Rect(dx + BOTTOM_MARGIN_X, y_btn, 170, 45)
            pygame.draw.rect(tela, cor_tema, rect_btn, border_radius=6)
            txt_btn = fontes['ui'].render(titulo_btn, True, BRANCO)
            tela.blit(txt_btn, (rect_btn.centerx - txt_btn.get_width() // 2, rect_btn.centery - txt_btn.get_height() // 2))
            estado.botoes_estudo[titulo_btn] = rect_btn
            linhas = quebrar_texto(descricao, fontes['pequena'], largura_texto_max)
            y_linha = rect_btn.y + 2
            for linha in linhas:
                txt_l = fontes['pequena'].render(linha, True, (200, 200, 200))
                tela.blit(txt_l, (dx + ESTUDOS_DESC_OFFSET_X, y_linha))
                y_linha += 18
            y_btn += 65
    elif memoria_sub_aba == 1:
        textos_escalas = [(_t('Acerte a Escala'), _t('Pratique shapes e digitações: Encontre todas as notas que pertencem à escala solicitada.'))]
        y_btn = y_start + ESTUDOS_OFFSET_Y_INTERNO
        for titulo_btn, descricao in textos_escalas:
            rect_btn = pygame.Rect(dx + BOTTOM_MARGIN_X, y_btn, 170, 45)
            pygame.draw.rect(tela, cor_tema, rect_btn, border_radius=6)
            txt_btn = fontes['ui'].render(titulo_btn, True, BRANCO)
            tela.blit(txt_btn, (rect_btn.centerx - txt_btn.get_width() // 2, rect_btn.centery - txt_btn.get_height() // 2))
            estado.botoes_estudo[titulo_btn] = rect_btn
            linhas = quebrar_texto(descricao, fontes['pequena'], largura_texto_max)
            y_linha = rect_btn.y + 2
            for linha in linhas:
                txt_l = fontes['pequena'].render(linha, True, (200, 200, 200))
                tela.blit(txt_l, (dx + ESTUDOS_DESC_OFFSET_X, y_linha))
                y_linha += 18
            y_btn += 65
    elif memoria_sub_aba == 2:
        textos_acordes = [(_t('Prática de Acordes'), _t('IA Real-Time: Toque o acorde completo em sua guitarra e a IA validará se as notas estão certas.'))]
        y_btn = y_start + ESTUDOS_OFFSET_Y_INTERNO
        for titulo_btn, descricao in textos_acordes:
            rect_btn = pygame.Rect(dx + BOTTOM_MARGIN_X, y_btn, 170, 45)
            pygame.draw.rect(tela, cor_tema, rect_btn, border_radius=6)
            txt_btn = fontes['ui'].render(titulo_btn, True, BRANCO)
            tela.blit(txt_btn, (rect_btn.centerx - txt_btn.get_width() // 2, rect_btn.centery - txt_btn.get_height() // 2))
            estado.botoes_estudo[titulo_btn] = rect_btn
            linhas = quebrar_texto(descricao, fontes['pequena'], largura_texto_max)
            y_linha = rect_btn.y + 2
            for linha in linhas:
                txt_l = fontes['pequena'].render(linha, True, (200, 200, 200))
                tela.blit(txt_l, (dx + ESTUDOS_DESC_OFFSET_X, y_linha))
                y_linha += 18
            y_btn += 65
    elif memoria_sub_aba == 3:
        textos_teoria = [(_t('Ciclo de Quintas'), _t('Domine a harmonia: Entenda as relações entre tonalidades, armaduras de clave e progressões quartais/quintais.'))]
        y_btn = y_start + ESTUDOS_OFFSET_Y_INTERNO
        for titulo_btn, descricao in textos_teoria:
            rect_btn = pygame.Rect(dx + BOTTOM_MARGIN_X, y_btn, 170, 45)
            pygame.draw.rect(tela, cor_tema, rect_btn, border_radius=6)
            txt_btn = fontes['ui'].render(titulo_btn, True, BRANCO)
            tela.blit(txt_btn, (rect_btn.centerx - txt_btn.get_width() // 2, rect_btn.centery - txt_btn.get_height() // 2))
            estado.botoes_estudo[titulo_btn] = rect_btn
            linhas = quebrar_texto(descricao, fontes['pequena'], largura_texto_max)
            y_linha = rect_btn.y + 2
            for linha in linhas:
                txt_l = fontes['pequena'].render(linha, True, (200, 200, 200))
                tela.blit(txt_l, (dx + ESTUDOS_DESC_OFFSET_X, y_linha))
                y_linha += 18
            y_btn += 65

def _desenhar_aba_musicas(tela, dx, y_start, largura_conteudo, estado, fontes, memoria_sub_aba, configs):
    """
        Como funciona: Executa o fluxo lógico necessário para a operação ' desenhar aba musicas'.
        Para que serve: Realiza as tarefas fundamentais de ' desenhar aba musicas' dentro do contexto do módulo.
        Onde é usada: Utilizado internamente para gerenciar comportamentos de ' desenhar aba musicas'.
    """
    cor_tema = configs.get_cor_tema()
    if memoria_sub_aba == 0:
        y_nav_interna = y_start + 10
        largura_nav = 360
        rect_nav = pygame.Rect(dx + 20, y_nav_interna, largura_nav, 30)
        pygame.draw.rect(tela, (40, 40, 45), rect_nav, border_radius=15)
        rect_aba_busca = pygame.Rect(dx + 20, y_nav_interna, 110, 30)
        rect_aba_favs = pygame.Rect(dx + 130, y_nav_interna, 110, 30)
        rect_aba_locais = pygame.Rect(dx + 240, y_nav_interna, 130, 30)
        estado.rect_aba_songsterr_busca = rect_aba_busca
        estado.rect_aba_songsterr_favs = rect_aba_favs
        estado.rect_aba_songsterr_locais = rect_aba_locais
        if estado.sub_memoria_musicas == 0:
            pygame.draw.rect(tela, cor_tema, rect_aba_busca, border_radius=15)
        elif estado.sub_memoria_musicas == 1:
            pygame.draw.rect(tela, cor_tema, rect_aba_favs, border_radius=15)
        else:
            pygame.draw.rect(tela, cor_tema, rect_aba_locais, border_radius=15)
        txt_b = fontes['pequena'].render(_t('Busca'), True, (255, 255, 255))
        tela.blit(txt_b, (rect_aba_busca.centerx - txt_b.get_width() // 2, rect_aba_busca.centery - txt_b.get_height() // 2))
        txt_f = fontes['pequena'].render(_t('Favoritas'), True, (255, 255, 255))
        tela.blit(txt_f, (rect_aba_favs.centerx - txt_f.get_width() // 2, rect_aba_favs.centery - txt_f.get_height() // 2))
        txt_l = fontes['pequena'].render(_t('Minhas Músicas'), True, (255, 255, 255))
        tela.blit(txt_l, (rect_aba_locais.centerx - txt_l.get_width() // 2, rect_aba_locais.centery - txt_l.get_height() // 2))
        if estado.sub_memoria_musicas == 0:
            rect_busca = pygame.Rect(dx + 20, y_start + 50, largura_conteudo - 150, 30)
            cor_borda_busca = cor_tema if getattr(estado, 'songsterr_search_active', False) else (100, 100, 100)
            pygame.draw.rect(tela, (50, 50, 50), rect_busca, border_radius=5)
            pygame.draw.rect(tela, cor_borda_busca, rect_busca, width=2 if getattr(estado, 'songsterr_search_active', False) else 1, border_radius=5)
            estado.rect_busca_songsterr = rect_busca
            query_display = estado.query_songsterr if estado.query_songsterr else _t('Clique para digitar...')
            cor_query = (255, 255, 255) if estado.query_songsterr else (150, 150, 150)
            txt_query = fontes['pequena'].render(query_display, True, cor_query)
            tela.blit(txt_query, (rect_busca.x + 10, rect_busca.y + 7))
            rect_btn_busca = pygame.Rect(rect_busca.right + 10, rect_busca.y, 100, 30)
            cor_btn = cor_tema
            pygame.draw.rect(tela, cor_btn, rect_btn_busca, border_radius=5)
            txt_btn = fontes['pequena'].render(_t('Buscar'), True, (255, 255, 255))
            tela.blit(txt_btn, (rect_btn_busca.centerx - txt_btn.get_width() // 2, rect_btn_busca.centery - txt_btn.get_height() // 2))
            estado.rect_btn_songsterr = rect_btn_busca
            y_lista = rect_busca.bottom + 15
            if estado.songsterr.carregando:
                txt_load = fontes['pequena'].render(_t('Carregando...'), True, (200, 200, 200))
                tela.blit(txt_load, (dx + 20, y_lista))
            elif not estado.resultados_songsterr:
                txt_vazio = fontes['pequena'].render(_t('Nenhum resultado. Digite e clique em Buscar.'), True, (150, 150, 150))
                tela.blit(txt_vazio, (dx + 20, y_lista))
            else:
                estado.rects_resultados_songsterr = []
                for i, song in enumerate(estado.resultados_songsterr[:5]):
                    y_item = y_lista + i * 45
                    rect_item = pygame.Rect(dx + 20, y_item, largura_conteudo - 80, 40)
                    pygame.draw.rect(tela, (35, 35, 35), rect_item, border_radius=5)
                    estado.rects_resultados_songsterr.append((rect_item, song))
                    title = song.get('title', 'Unknown')
                    artist = song.get('artist', 'Unknown')
                    txt_song = fontes['pequena'].render(f'{title} - {artist}', True, (255, 255, 255))
                    tela.blit(txt_song, (rect_item.x + 10, rect_item.y + 12))
                    rect_estrela = pygame.Rect(rect_item.right + 10, y_item, 40, 40)
                    is_fav = any((f.get('songId') == song.get('songId') for f in estado.favoritos_songsterr))
                    cor_estrela = (255, 215, 0) if is_fav else (100, 100, 100)
                    pygame.draw.rect(tela, (30, 30, 30), rect_estrela, border_radius=5)
                    txt_estrela = fontes['titulo'].render('★' if is_fav else '☆', True, cor_estrela)
                    tela.blit(txt_estrela, (rect_estrela.centerx - txt_estrela.get_width() // 2, rect_estrela.centery - txt_estrela.get_height() // 2))
                    if not hasattr(estado, 'rects_favoritos_click'):
                        estado.rects_favoritos_click = []
                    estado.rects_favoritos_click.append((rect_estrela, song))
        elif estado.sub_memoria_musicas == 1:
            y_lista = y_start + 50
            if not estado.favoritos_songsterr:
                txt_vazio = fontes['pequena'].render(_t('Você ainda não salvou nenhuma música.'), True, (150, 150, 150))
                tela.blit(txt_vazio, (dx + 20, y_lista))
            else:
                estado.rects_resultados_songsterr = []
                estado.rects_favoritos_click = []
                for i, song in enumerate(estado.favoritos_songsterr):
                    y_item = y_lista + i * 45
                    rect_item = pygame.Rect(dx + 20, y_item, largura_conteudo - 80, 40)
                    pygame.draw.rect(tela, (35, 35, 35), rect_item, border_radius=5)
                    pygame.draw.rect(tela, (255, 215, 0), rect_item, width=1, border_radius=5)
                    estado.rects_resultados_songsterr.append((rect_item, song))
                    title = song.get('title', 'Unknown')
                    artist = song.get('artist', 'Unknown')
                    txt_song = fontes['pequena'].render(f'★ {title} - {artist}', True, (255, 215, 0))
                    tela.blit(txt_song, (rect_item.x + 10, rect_item.y + 12))
                    rect_estrela = pygame.Rect(rect_item.right + 10, y_item, 40, 40)
                    pygame.draw.rect(tela, (30, 30, 30), rect_estrela, border_radius=5)
                    txt_estrela = fontes['titulo'].render('★', True, (255, 215, 0))
                    tela.blit(txt_estrela, (rect_estrela.centerx - txt_estrela.get_width() // 2, rect_estrela.centery - txt_estrela.get_height() // 2))
                    estado.rects_favoritos_click.append((rect_estrela, song))
        else:
            y_lista = y_start + 50
            rect_add = pygame.Rect(dx + 20, y_lista, 200, 35)
            pygame.draw.rect(tela, cor_tema, rect_add, border_radius=8)
            txt_add = fontes['pequena'].render(_t('+ Selecionar MIDI'), True, (255, 255, 255))
            tela.blit(txt_add, (rect_add.centerx - txt_add.get_width() // 2, rect_add.centery - txt_add.get_height() // 2))
            estado.rect_btn_add_midi = rect_add
            txt_hint = fontes['pequena'].render(_t('(Ou arraste o arquivo .mid para aqui)'), True, (150, 150, 150))
            tela.blit(txt_hint, (rect_add.right + 15, rect_add.y + 8))
            y_lista += 50
            if not estado.musicas_locais:
                txt_vazio = fontes['pequena'].render(_t('Nenhum MIDI local adicionado.'), True, (120, 120, 120))
                tela.blit(txt_vazio, (dx + 20, y_lista))
            else:
                estado.rects_musicas_locais = []
                for i, song in enumerate(estado.musicas_locais):
                    y_item = y_lista + i * 45
                    rect_item = pygame.Rect(dx + 20, y_item, largura_conteudo - 40, 40)
                    pygame.draw.rect(tela, (40, 45, 55), rect_item, border_radius=5)
                    estado.rects_musicas_locais.append((rect_item, song))
                    name = song.get('title', 'Arquivo MIDI')
                    txt_song = fontes['pequena'].render(f'📄 {name}', True, (220, 220, 220))
                    tela.blit(txt_song, (rect_item.x + 10, rect_item.y + 12))
    elif memoria_sub_aba == 1:
        txt = fontes['titulo'].render(_t('Minhas Músicas (Em Breve)'), True, (180, 180, 180))
        tela.blit(txt, (dx + largura_conteudo // 2 - txt.get_width() // 2, y_start + 100))

def desenhar_secoes_inferiores_expansiveis(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_gerenciador_jogos):
    """
        Como funciona: Utiliza funções de renderização do Pygame para desenhar na tela.
        Para que serve: Apresenta o elemento visual 'secoes inferiores expansiveis' na interface gráfica.
        Onde é usada: Chamado a partir do módulo ou classe base de 'bottom_nav'.
    """
    alpha_atual = configs.get_alpha() if configs else 255
    cor_tema = configs.get_cor_tema()
    dx = estado.dragger_painel_inferior.x if hasattr(estado, 'dragger_painel_inferior') else 100
    dy = estado.dragger_painel_inferior.y if hasattr(estado, 'dragger_painel_inferior') else estado.ALTURA_TELA - 50
    altura_caixa_total = BOTTOM_ALTURA_CAIXA
    largura_conteudo = estado.dragger_painel_inferior.largura if hasattr(estado, 'dragger_painel_inferior') else estado.LARGURA_BRACO
    espacamento = 8
    num_secoes = len(estado.secoes_inferiores)
    largura_botao = (largura_conteudo - espacamento * (num_secoes - 1)) / num_secoes
    pos_x_guit = estado.dragger_guitarra.x if hasattr(estado, 'dragger_guitarra') else 100
    pos_y_guit = estado.dragger_guitarra.y if hasattr(estado, 'dragger_guitarra') else 90
    instrumento = getattr(estado, 'instrumento', 'guitarra')
    offset_y_guit = pos_y_guit + estado.ESPACO_CORDAS if instrumento == 'baixo' else pos_y_guit
    altura_guit_atual = estado.ALTURA_BRACO - 2 * estado.ESPACO_CORDAS if instrumento == 'baixo' else estado.ALTURA_BRACO
    rect_braco_real = pygame.Rect(pos_x_guit, offset_y_guit, estado.LARGURA_BRACO, altura_guit_atual)
    tela.set_clip(None)
    for chave_escala, lista_modulos_gerais in dicionario_escalas.items():
        for modulo in lista_modulos_gerais:
            if modulo.estado != 'painel':
                modulo.x_braco = pos_x_guit
                modulo.y_braco = offset_y_guit
                modulo.atualizar_e_desenhar(tela, pygame.mouse.get_pos(), rect_braco_real, fontes['pequena'], alpha_atual)
    num_secoes = len(estado.secoes_inferiores)
    espacamento_entre_botoes = 8
    largura_total_util = largura_conteudo - espacamento_entre_botoes * (num_secoes - 1)
    largura_botao_fluida = largura_total_util / num_secoes
    for i, secao in enumerate(estado.secoes_inferiores):
        x_botao = dx + i * (largura_botao_fluida + espacamento_entre_botoes)
        rect_cabecalho = pygame.Rect(x_botao, dy, largura_botao_fluida, 45)
        secao['rect_cabecalho'] = rect_cabecalho
        cor_fundo = cor_tema if secao['expandido'] else (40, 40, 40)
        pygame.draw.rect(tela, cor_fundo, rect_cabecalho, border_radius=RADIUS_PADRAO)
        if not secao['expandido']:
            pygame.draw.rect(tela, COR_BORDA, rect_cabecalho, width=1, border_radius=RADIUS_PADRAO)
        txt_traduzido = _t(secao['titulo'])
        txt = fontes['pequena'].render(txt_traduzido, True, BRANCO)
        tela.blit(txt, (rect_cabecalho.centerx - txt.get_width() // 2, rect_cabecalho.centery - txt.get_height() // 2))
        if secao['expandido']:
            y_conteudo = dy - altura_caixa_total - 15
            rect_fundo_conteudo = pygame.Rect(dx, y_conteudo, largura_conteudo, altura_caixa_total)
            pygame.draw.rect(tela, (25, 25, 25), rect_fundo_conteudo, border_radius=RADIUS_PADRAO)
            pygame.draw.rect(tela, COR_BORDA, rect_fundo_conteudo, width=2, border_radius=RADIUS_PADRAO)
            y_sub_abas = y_conteudo + BOTTOM_SUBABA_Y_OFFSET
            altura_sub = BOTTOM_SUBABA_ALTURA
            if secao['sub_abas']:
                largura_sub = (largura_conteudo - BOTTOM_SUBABA_MARGIN_X) / len(secao['sub_abas'])
                for j, nome_sub in enumerate(secao['sub_abas']):
                    rect_sub = pygame.Rect(dx + BOTTOM_MARGIN_X + j * largura_sub, y_sub_abas, largura_sub - 5, altura_sub)
                    secao[f'rect_sub_{j}'] = rect_sub
                    cor_sub = cor_tema if secao['memoria_sub_aba'] == j else (40, 40, 40)
                    pygame.draw.rect(tela, cor_sub, rect_sub, border_radius=6)
                    txt_sub_trad = _t(nome_sub)
                    txt_sub = fontes['pequena'].render(txt_sub_trad, True, BRANCO)
                    tela.blit(txt_sub, (rect_sub.centerx - txt_sub.get_width() // 2, rect_sub.centery - txt_sub.get_height() // 2))
            y_area_desenho = y_conteudo + BOTTOM_OFFSET_AREA_DESENHO
            altura_util = altura_caixa_total - BOTTOM_ALTURA_UTIL_DIFF
            rect_clipping = pygame.Rect(dx + 5, y_area_desenho + BOTTOM_OFFSET_CLIPPING_Y, largura_conteudo - 10, altura_util - BOTTOM_OFFSET_CLIPPING_Y)
            tela.set_clip(rect_clipping)
            scroll_atual = estado.scroll_y.get(i, 0)
            y_start = y_area_desenho - scroll_atual
            if secao['conteudo'] in ['escalas', 'acordes']:
                chaves = []
                if secao['conteudo'] == 'escalas':
                    chaves = ['maior', 'menor', 'penta_maior', 'penta_menor', 'blues', 'modos', 'harmonica', 'melodica', 'exoticas']
                elif secao['conteudo'] == 'acordes':
                    chaves = ['caged', 'triades_maior', 'triades_menor', 'setimas', 'power']
                if secao['memoria_sub_aba'] < len(chaves):
                    chave_atual = chaves[secao['memoria_sub_aba']]
                    lista_ativa = dicionario_escalas.get(chave_atual, [])
                    altura_total_conteudo = 0
                    for modulo in lista_ativa:
                        if modulo.estado == 'painel':
                            y_rel = getattr(modulo, 'y_relativo', 0)
                            altura_total_conteudo = max(altura_total_conteudo, y_rel + 150)
                    estado.max_scroll[i] = max(0, altura_total_conteudo - altura_util + 50)
                    for modulo in lista_ativa:
                        if modulo.estado == 'painel':
                            x_rel = getattr(modulo, 'x_original_relativo', 0)
                            if not hasattr(modulo, 'x_original_relativo'):
                                modulo.x_original_relativo = modulo.rect_painel.x - (estado.dragger_painel_inferior.x if hasattr(estado, 'dragger_painel_inferior') else 100)
                                x_rel = modulo.x_original_relativo
                            modulo.rect_painel.x = dx + x_rel
                            y_rel = getattr(modulo, 'y_relativo', 0)
                            modulo.rect_painel.y = y_start + 10 + y_rel
                            modulo.scroll_offset = 0
                            modulo.atualizar_e_desenhar(tela, pygame.mouse.get_pos(), rect_braco_real, fontes['pequena'], alpha_atual)
                    tela.set_clip(rect_clipping)
            elif secao['conteudo'] == 'analise_ia':
                estado.max_scroll[i] = 200 if secao['memoria_sub_aba'] == 0 else 0
                _desenhar_aba_ia(tela, dx, y_start, estado, fontes, meu_processador, meu_gravador, meu_gerenciador_jogos, secao['memoria_sub_aba'], configs)
            elif secao['conteudo'] == 'configuracao':
                num_blocos = 7 if secao['memoria_sub_aba'] == 0 else 1
                esp = 15
                altura_bloco = 185
                largura_util_nav = largura_conteudo - 40
                largura_bloco = (largura_util_nav - 3 * esp) // 4
                num_linhas = (num_blocos + 3) // 4
                altura_total_config = num_linhas * (altura_bloco + esp) + 20
                estado.max_scroll[i] = max(0, altura_total_config - altura_util + 20)
                _desenhar_aba_configuracao(tela, dx, y_start, largura_conteudo, estado, fontes, configs, meu_metronomo, secao['memoria_sub_aba'], scroll_atual)
            elif secao['conteudo'] == 'estudos':
                num_itens = 3 if secao['memoria_sub_aba'] == 0 else 1
                altura_total_estudos = num_itens * 65 + 40
                estado.max_scroll[i] = max(0, altura_total_estudos - altura_util)
                _desenhar_aba_estudos(tela, dx, y_start, largura_conteudo, estado, fontes, secao['memoria_sub_aba'], configs)
            elif secao['conteudo'] == 'musicas':
                num_musicas = len(estado.resultados_songsterr) if secao['memoria_sub_aba'] == 0 else len(estado.musicas_locais)
                altura_total_musicas = num_musicas * 45 + 150
                estado.max_scroll[i] = max(0, altura_total_musicas - altura_util)
                _desenhar_aba_musicas(tela, dx, y_start, largura_conteudo, estado, fontes, secao['memoria_sub_aba'], configs)
            tela.set_clip(None)
            if estado.max_scroll.get(i, 0) > 0:
                x_scroll = dx + largura_conteudo - 12
                tamanho_alca = max(30, altura_util * (altura_util / (altura_util + estado.max_scroll[i])))
                y_alca = y_area_desenho + scroll_atual / estado.max_scroll[i] * (altura_util - tamanho_alca)
                pygame.draw.rect(tela, (45, 45, 45), (x_scroll, y_area_desenho, 8, altura_util), border_radius=4)
                pygame.draw.rect(tela, (120, 120, 120), (x_scroll, y_alca, 8, tamanho_alca), border_radius=4)
    if estado.drag_ativado and hasattr(estado, 'dragger_painel_inferior'):
        estado.dragger_painel_inferior.desenhar_caixa_selecao(tela, margem=8)