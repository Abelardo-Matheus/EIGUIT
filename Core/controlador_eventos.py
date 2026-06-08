import pygame
from Interface import fabrica_escalas
from Interface import gerenciador_interface
from Core.constantes_ui import *
import Modulos.modulo_menu_contexto as modulo_menu_contexto
import Modulos.modulo_menu_superior as modulo_menu_superior
from Interface.Componentes.tablatura_view import BlocoTablatura
from Interface.Componentes.config_componentes import BOTTOM_OFFSET_AREA_DESENHO

def obter_draggers_ativos(estado):
    """
        Como funciona: Acessa e formata dados internos ou de configuração.
        Para que serve: Retorna as informações solicitadas sobre 'draggers ativos'.
        Onde é usada: Chamado a partir do módulo ou classe base de 'controlador_eventos'.
    """
    lista = []
    simples = ['dragger_controles_topo', 'dragger_cores', 'dragger_metronomo', 'dragger_acordes', 'dragger_painel_inferior', 'dragger_nota_atual']
    for d in simples:
        if hasattr(estado, d):
            lista.append(getattr(estado, d))
    if hasattr(estado, 'lista_guitarras'):
        lista.extend(reversed(estado.lista_guitarras))
    if hasattr(estado, 'lista_tabs'):
        lista.extend(reversed(estado.lista_tabs))
    return lista

def processar(eventos, estado, configs, dicionario_escalas, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico, meu_gerenciador_jogos):
    """
        Como funciona: Itera sobre a fila de eventos do Pygame, tratando entradas de teclado, mouse e gestos de câmera.
    """
    if not hasattr(estado, 'menu_contexto'):
        estado.menu_contexto = modulo_menu_contexto.MenuContexto()
    if not hasattr(estado, 'menu_superior'):
        estado.menu_superior = modulo_menu_superior.MenuSuperior()
    
    pos_mouse = pygame.mouse.get_pos()
    pos_real = getattr(estado, 'pos_mouse_real', pos_mouse)

    # 1. PRIORIDADE MÁXIMA: BARRA SUPERIOR E MENUS DE SISTEMA
    # Isso garante que Pin, Arquivo, Perfil, etc funcionem SEMPRE.
    for evento in eventos:
        if evento.type == pygame.QUIT:
            estado.solicitou_saida = True
            
        # Tratar Menu Superior
        if estado.menu_superior.tratar_eventos(evento, pos_real, estado, configs, meu_campo_harmonico, meu_gravador):
            dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
            return # Bloqueia propagação

        # Tratar Botão PIN (Edit Mode)
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if hasattr(estado, 'rect_btn_pin') and estado.rect_btn_pin.collidepoint(pos_real):
                estado.drag_ativado = not estado.drag_ativado
                if not estado.drag_ativado:
                    for dragger in obter_draggers_ativos(estado):
                        dragger.arrastando = False
                return # Bloqueia propagação

    # 2. TELAS EM DESTAQUE (Estudo / Jogo)
    if hasattr(estado, 'gerenciador_perfil') and estado.gerenciador_perfil.ativo:
        if estado.gerenciador_perfil.tratar_eventos(eventos, estado, configs, meu_campo_harmonico, meu_gravador):
            dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
            return
            
    if getattr(estado, 'tela_jogo_ativa', False):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                estado.tela_jogo_ativa = False
                meu_gerenciador_jogos.jogo_instancia = None
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                meu_gerenciador_jogos.tratar_clique_tela_jogo(evento.pos, estado, meu_gravador)
        return

    if getattr(estado, 'tela_estudo_ativa', False):
        for evento in eventos:
            if hasattr(estado, 'gerenciador_estudos'):
                estado.gerenciador_estudos.tratar_eventos(evento, pygame.mouse.get_pos(), estado)
        return

    if getattr(estado, 'tela_criacao_tab_ativa', False):
        import Interface.renderizador_ui as render_ui
        from Interface.renderizador_tablatura import RenderizadorTablatura
        if render_ui.render_tab is None:
            render_ui.render_tab = RenderizadorTablatura()
        render_tab = render_ui.render_tab
        
        import re
        for evento in eventos:
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1: # Clique Esquerdo
                    if hasattr(estado, 'rect_voltar_criacao') and estado.rect_voltar_criacao.collidepoint(evento.pos):
                        estado.tela_criacao_tab_ativa = False
                    elif hasattr(estado, 'rect_tab_play') and estado.rect_tab_play.collidepoint(evento.pos):
                        estado.tab_reproduzindo = not estado.tab_reproduzindo
                        if estado.tab_reproduzindo:
                            estado.tempo_ultimo_tick = pygame.time.get_ticks()
                    elif hasattr(estado, 'rect_bpm_mais') and estado.rect_bpm_mais.collidepoint(evento.pos):
                        estado.tab_bpm = min(300, estado.tab_bpm + 5)
                    elif hasattr(estado, 'rect_bpm_menos') and estado.rect_bpm_menos.collidepoint(evento.pos):
                        estado.tab_bpm = max(10, estado.tab_bpm - 5)
                    elif hasattr(estado, 'rect_tab_salvar') and estado.rect_tab_salvar.collidepoint(evento.pos):
                        from BD.gerenciador_remoto_db import GerenciadorDB
                        import json
                        db = GerenciadorDB()
                        dados_json = json.dumps({'dados': estado.tab_dados, 'duracoes': getattr(estado, 'tab_duracoes', [])})
                        if estado.usuario_id_logado:
                            success = db.salvar_projeto(estado.usuario_id_logado, estado.tab_nome, 'tablatura', dados_json)
                            print(f"[TAB] Salvo no banco de dados: {success}")
                    
                    # Clicar em técnicas na barra de ferramentas
                    clicou_ferramenta = False
                    if render_tab and hasattr(render_tab, 'rects_tecnicas'):
                        for rect, cmd in render_tab.rects_tecnicas:
                            if rect.collidepoint(evento.pos):
                                col, corda = estado.tab_cursor_col, estado.tab_cursor_corda
                                nota_atual = str(estado.tab_dados[col][corda])
                                
                                if cmd == 'del':
                                    estado.tab_dados[col][corda] = '-'
                                elif cmd == '+':
                                    estado.tab_duracoes[col] = min(16, estado.tab_duracoes[col] + 1)
                                elif cmd == '-':
                                    estado.tab_duracoes[col] = max(1, estado.tab_duracoes[col] - 1)
                                elif nota_atual != '-':
                                    # Aplicar técnica (b, /, h, p)
                                    match = re.match(r"(\d+)(.*)", nota_atual)
                                    if match:
                                        estado.tab_dados[col][corda] = match.group(1) + cmd
                                
                                clicou_ferramenta = True
                                break

                    if not clicou_ferramenta:
                        # Clicar em acordes do campo harmônico
                        clicou_acorde = False
                        if render_tab and hasattr(render_tab, 'rects_campo_harmonico'):
                            for rect, nome_acorde in render_tab.rects_campo_harmonico:
                                if rect.collidepoint(evento.pos):
                                    # Simplificação: Insere as notas da tríade na vertical
                                    print(f"[TAB] Inserindo acorde: {nome_acorde}")
                                    # Para o exemplo, vamos colocar uma tríade de C (Power chord placeholder)
                                    # Em uma implementação real, mapearíamos o nome_acorde para casas reais
                                    estado.tab_dados[estado.tab_cursor_col] = ['-', '-', '-', '5', '5', '3']
                                    clicou_acorde = True
                                    break
                        
                        if not clicou_acorde:
                            for (col, corda), rect in render_tab.rects_clique.items():
                                if rect.collidepoint(evento.pos):
                                    estado.tab_cursor_col = col
                                    estado.tab_cursor_corda = corda
                                    break
                elif evento.button == 3: # Clique Direito: Move o Play
                    for (col, corda), rect in render_tab.rects_clique.items():
                        if rect.collidepoint(evento.pos):
                            estado.tab_coluna_atual = col
                            estado.tab_cursor_col = col # Move o cursor também para clareza
                            estado.tab_cursor_corda = corda
                            break
            
            if evento.type == pygame.MOUSEWHEEL:
                # Scroll Vertical no novo layout wrap
                estado.tab_scroll_y = max(0, getattr(estado, 'tab_scroll_y', 0) - evento.y * 50)

            if evento.type == pygame.KEYDOWN:
                if not hasattr(estado, 'tab_duracoes'):
                    estado.tab_duracoes = [1 for _ in range(len(estado.tab_dados))]
                    
                if evento.key == pygame.K_ESCAPE:
                    estado.tela_criacao_tab_ativa = False
                elif evento.key in [pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS]:
                    estado.tab_duracoes[estado.tab_cursor_col] = min(16, estado.tab_duracoes[estado.tab_cursor_col] + 1)
                elif evento.key in [pygame.K_MINUS, pygame.K_KP_MINUS]:
                    estado.tab_duracoes[estado.tab_cursor_col] = max(1, estado.tab_duracoes[estado.tab_cursor_col] - 1)
                elif evento.key == pygame.K_SPACE:
                    estado.tab_reproduzindo = not estado.tab_reproduzindo
                    if estado.tab_reproduzindo:
                        estado.tempo_ultimo_tick = pygame.time.get_ticks()
                elif evento.key == pygame.K_RIGHT:
                    estado.tab_cursor_col += 1
                elif evento.key == pygame.K_LEFT:
                    estado.tab_cursor_col = max(0, estado.tab_cursor_col - 1)
                elif evento.key == pygame.K_UP:
                    estado.tab_cursor_corda = max(0, estado.tab_cursor_corda - 1)
                elif evento.key == pygame.K_DOWN:
                    estado.tab_cursor_corda = min(5, estado.tab_cursor_corda + 1)
                elif pygame.K_0 <= evento.key <= pygame.K_9:
                    num = str(evento.key - pygame.K_0)
                    atual = estado.tab_dados[estado.tab_cursor_col][estado.tab_cursor_corda]
                    if atual == '-':
                        estado.tab_dados[estado.tab_cursor_col][estado.tab_cursor_corda] = num
                    else:
                        match = re.match(r"(\d+)(.*)", str(atual))
                        if match:
                            nova_casa = match.group(1) + num
                            if int(nova_casa) <= 24:
                                estado.tab_dados[estado.tab_cursor_col][estado.tab_cursor_corda] = nova_casa + match.group(2)
                elif evento.key == pygame.K_BACKSPACE:
                    estado.tab_dados[estado.tab_cursor_col][estado.tab_cursor_corda] = '-'
                elif evento.unicode.lower() in ['b', '/', 'h', 'p']:
                    atual = estado.tab_dados[estado.tab_cursor_col][estado.tab_cursor_corda]
                    if atual != '-':
                        match = re.match(r"(\d+)(.*)", str(atual))
                        if match:
                            estado.tab_dados[estado.tab_cursor_col][estado.tab_cursor_corda] = match.group(1) + evento.unicode.lower()
        return

    if getattr(estado, 'tab_tela_cheia_ativa', False):
        for evento in eventos:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if hasattr(estado, 'rect_voltar_tab') and estado.rect_voltar_tab.collidepoint(evento.pos):
                    estado.tab_tela_cheia_ativa = False
            if evento.type == pygame.MOUSEWHEEL and hasattr(estado, 'tab_focada'):
                estado.tab_focada.tratar_scroll(evento.y)
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                estado.tab_tela_cheia_ativa = False
        return

    # 3. WORKSPACE (Mesa de Trabalho)
    bloqueio_z_index = False
    dx_inf = estado.dragger_painel_inferior.x if hasattr(estado, 'dragger_painel_inferior') else 100
    dy_inf = estado.dragger_painel_inferior.y if hasattr(estado, 'dragger_painel_inferior') else estado.ALTURA_TELA - 50
    altura_caixa_total = 350
    largura_conteudo = estado.dragger_painel_inferior.largura if hasattr(estado, 'dragger_painel_inferior') else estado.LARGURA_BRACO
    for secao in estado.secoes_inferiores:
        if secao['expandido']:
            y_conteudo = dy_inf - altura_caixa_total - 10
            rect_fundo_conteudo = pygame.Rect(dx_inf, y_conteudo, largura_conteudo, altura_caixa_total)
            if rect_fundo_conteudo.collidepoint(pos_mouse):
                bloqueio_z_index = True
            break

    for evento in eventos:
        if evento.type == pygame.QUIT:
            estado.solicitou_saida = True
        if estado.menu_superior.tratar_eventos(evento, pos_real, estado, configs, meu_campo_harmonico, meu_gravador):
            dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
            continue
        if not hasattr(estado, 'lista_guitarras'):
            estado.lista_guitarras = [estado.dragger_guitarra] if hasattr(estado, 'dragger_guitarra') else []
        acao_contexto = estado.menu_contexto.tratar_eventos(evento, pos_mouse, estado)
        if acao_contexto == 'CONSUMIU_EVENTO' or acao_contexto == 'FECHOU_MENU':
            continue
        elif isinstance(acao_contexto, tuple):
            acao, alvo, tipo = acao_contexto
            print(f'[MENU] Ação: {acao} | Alvo: {tipo}')
            if tipo == 'guitarra':
                if acao == 'Apagar' and alvo in estado.lista_guitarras:
                    estado.lista_guitarras.remove(alvo)
                    if estado.dragger_guitarra == alvo:
                        estado.dragger_guitarra = estado.lista_guitarras[0] if estado.lista_guitarras else None
                elif acao in ['Duplicar Bloco (Cópia)', 'Nova Seção Vazia']:
                    import copy
                    novo_dragger = copy.copy(alvo)
                    novo_dragger.y += 180
                    estado.lista_guitarras.append(novo_dragger)
            continue
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 3:
            abriu_menu = False
            if hasattr(estado, 'lista_guitarras'):
                for guit in reversed(estado.lista_guitarras):
                    rect_guit = pygame.Rect(guit.x, guit.y, guit.largura, guit.altura)
                    if rect_guit.collidepoint(pos_mouse):
                        if estado.drag_ativado:
                            estado.menu_contexto.abrir(pos_mouse, 'guitarra', guit)
                            abriu_menu = True
                        else:
                            for lista_modulos in dicionario_escalas.values():
                                for modulo in lista_modulos:
                                    if modulo.estado != 'painel':
                                        modulo.estado = 'painel'
                        break
            if not abriu_menu and hasattr(estado, 'dragger_acordes'):
                rect_acordes = pygame.Rect(estado.dragger_acordes.x, estado.dragger_acordes.y, estado.dragger_acordes.largura, estado.dragger_acordes.altura)
                if rect_acordes.collidepoint(pos_mouse) and estado.drag_ativado:
                    estado.menu_contexto.abrir(pos_mouse, 'acordes', estado.dragger_acordes)
                    abriu_menu = True
            if not abriu_menu:
                estado.menu_contexto.abrir(pos_mouse, 'fundo_mesa')
            continue
        if evento.type == pygame.MOUSEWHEEL:
            velocidade_scroll = 40
            consumiu_scroll = False
            if hasattr(estado, 'lista_tabs'):
                for tab in reversed(estado.lista_tabs):
                    rect_tab = pygame.Rect(tab.x, tab.y, tab.largura, tab.altura)
                    if rect_tab.collidepoint(pos_mouse):
                        if tab.tratar_scroll(evento.y):
                            consumiu_scroll = True
                            break
            if not consumiu_scroll:
                for i, secao in enumerate(estado.secoes_inferiores):
                    if secao.get('expandido') and secao['conteudo'] in ['escalas', 'acordes', 'configuracao', 'estudos', 'musicas']:
                        y_topo = dy_inf - altura_caixa_total - 10
                        rect_area = pygame.Rect(dx_inf, y_topo, largura_conteudo, altura_caixa_total)
                        if rect_area.collidepoint(pos_mouse):
                            estado.scroll_y.setdefault(i, 0)
                            max_val = estado.max_scroll.get(i, 0)
                            estado.scroll_y[i] -= evento.y * velocidade_scroll
                            estado.scroll_y[i] = max(0, min(estado.scroll_y[i], max_val))
                            break
        if evento.type == pygame.KEYDOWN:
            if getattr(estado, 'songsterr_search_active', False):
                if evento.key == pygame.K_BACKSPACE:
                    estado.query_songsterr = estado.query_songsterr[:-1]
                elif evento.key == pygame.K_RETURN:
                    import threading

                    def thread_busca():
                        """
                            Como funciona: Executa o fluxo lógico necessário para a operação 'thread busca'.
                            Para que serve: Realiza as tarefas fundamentais de 'thread busca' dentro do contexto do módulo.
                            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'thread busca'.
                        """
                        estado.resultados_songsterr = estado.songsterr.buscar_musicas(estado.query_songsterr)
                    threading.Thread(target=thread_busca).start()
                elif len(evento.unicode) > 0 and evento.unicode.isprintable():
                    estado.query_songsterr += evento.unicode
                continue
            meu_metronomo.tratar_teclado(evento)
            if evento.key == pygame.K_ESCAPE:
                estado.solicitou_saida = True
        if evento.type == pygame.DROPFILE:
            caminho_arquivo = evento.file
            if caminho_arquivo.lower().endswith(('.mid', '.midi')):
                import shutil
                import os
                nome_arquivo = os.path.basename(caminho_arquivo)
                destino = os.path.join('Audios/Midis', nome_arquivo)
                try:
                    shutil.copy(caminho_arquivo, destino)
                    nova_musica = {'songId': f'local_{nome_arquivo}', 'title': nome_arquivo.replace('.mid', '').replace('.midi', ''), 'artist': 'Arquivo Local', 'local_path': destino}
                    if not any((m['local_path'] == destino for m in estado.musicas_locais)):
                        estado.musicas_locais.append(nova_musica)
                    nova_tab = BlocoTablatura(200, 200, 700, 450, nova_musica)
                    nova_tab.caminho_midi_local = destino
                    nova_tab.carregar_dados_completos(estado.songsterr)
                    estado.lista_tabs.append(nova_tab)
                    print(f'[DROP] MIDI Adicionado: {nome_arquivo}')
                except Exception as e:
                    print(f'[DROP] Erro ao copiar MIDI: {e}')
        if evento.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            # Prioridade para drag and drop global
            draggers = obter_draggers_ativos(estado)
            clicou_em_dragger = False
            
            # Processar eventos de mouse para todos os draggers
            for dragger in draggers:
                is_fixo = dragger in [getattr(estado, 'dragger_painel_inferior', None)]
                
                # Se for fixo, usa pos_real, senão usa pos_mouse (virtual)
                pos_ref = pos_real if is_fixo else evento.pos
                pode_interagir = estado.drag_ativado or isinstance(dragger, BlocoTablatura)
                
                if pode_interagir:
                    evt_dict = evento.dict.copy()
                    evt_dict['pos'] = pos_ref
                    evento_dragger = pygame.event.Event(evento.type, evt_dict)
                    
                    margem = 20 if (hasattr(dragger, 'num_cordas') or dragger == getattr(estado, 'dragger_guitarra', None)) else 5
                    if dragger.processar_eventos_mouse(evento_dragger, margem_clique=margem):
                        clicou_em_dragger = True
                        
                        # Atualizar lógica de redimensionamento específica para guitarra
                        is_guitarra = hasattr(dragger, 'num_cordas') or dragger == getattr(estado, 'dragger_guitarra', None)
                        if is_guitarra and hasattr(dragger, 'redimensionando') and dragger.redimensionando:
                            estado.LARGURA_BRACO = dragger.largura
                            estado.ALTURA_BRACO = dragger.altura
                            estado.atualizar_medidas()
                        break
            
            if clicou_em_dragger:
                continue

        if evento.type == pygame.MOUSEBUTTONUP:
            # Garantir limpeza de estados de drag
            for dragger in obter_draggers_ativos(estado):
                dragger.arrastando = False
                dragger.redimensionando = False
            
            if evento.button == 1 and estado.drag_ativado:
                 dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if hasattr(estado, 'rect_btn_pin') and estado.rect_btn_pin.collidepoint(pos_real):
                estado.drag_ativado = not estado.drag_ativado
                if not estado.drag_ativado:
                    for dragger in obter_draggers_ativos(estado):
                        dragger.arrastando = False
                continue
            
            # Cliques nos novos botões de controle de instrumento (usam evento.pos virtual)
            if hasattr(estado, 'btn_guit') and estado.btn_guit.collidepoint(evento.pos):
                estado.instrumento = 'guitarra'
                continue
            if hasattr(estado, 'btn_baixo') and estado.btn_baixo.collidepoint(evento.pos):
                estado.instrumento = 'baixo'
                continue
            if hasattr(estado, 'btn_menos_casa') and estado.btn_menos_casa.collidepoint(evento.pos):
                estado.NUM_CASAS = max(1, estado.NUM_CASAS - 1)
                estado.atualizar_medidas()
                continue
            if hasattr(estado, 'btn_mais_casa') and estado.btn_mais_casa.collidepoint(evento.pos):
                estado.NUM_CASAS = min(36, estado.NUM_CASAS + 1)
                estado.atualizar_medidas()
                continue
            if hasattr(estado, 'btn_menos_afinacao') and estado.btn_menos_afinacao.collidepoint(evento.pos):
                estado.indice_afinacao = (estado.indice_afinacao - 1) % len(lista_afinacoes)
                dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
                continue
            if hasattr(estado, 'btn_mais_afinacao') and estado.btn_mais_afinacao.collidepoint(evento.pos):
                estado.indice_afinacao = (estado.indice_afinacao + 1) % len(lista_afinacoes)
                dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
                continue
            clicou_conteudo = False
            tab_para_fechar = None
            if hasattr(estado, 'lista_tabs'):
                for tab in reversed(estado.lista_tabs):
                    acao = tab.tratar_clique(evento.pos)
                    if acao == 'FECHAR':
                        tab_para_fechar = tab
                        clicou_conteudo = True
                        break
                    elif acao == 'TELA_CHEIA':
                        estado.tab_tela_cheia_ativa = True
                        estado.tab_focada = tab
                        clicou_conteudo = True
                        break
                    elif acao:
                        clicou_conteudo = True
                        break
            if tab_para_fechar:
                estado.lista_tabs.remove(tab_para_fechar)
            if clicou_conteudo:
                continue
            clicou_em_dragger = False
            for dragger in obter_draggers_ativos(estado):
                is_fixo = dragger == getattr(estado, 'dragger_controles_topo', None)
                pos_clique = pos_real if is_fixo else evento.pos
                pode_arrastar = estado.drag_ativado or isinstance(dragger, BlocoTablatura)
                if pode_arrastar:
                    margem = 20 if hasattr(dragger, 'num_cordas') else 5
                    evt_dict = evento.dict.copy()
                    evt_dict['pos'] = pos_clique
                    evento_clique = pygame.event.Event(evento.type, evt_dict)
                    if dragger.processar_eventos_mouse(evento_clique, margem_clique=margem):
                        clicou_em_dragger = True
                        is_guitarra = hasattr(dragger, 'num_cordas') or dragger == getattr(estado, 'dragger_guitarra', None)
                        if is_guitarra and hasattr(dragger, 'redimensionando') and dragger.redimensionando:
                            estado.LARGURA_BRACO = dragger.largura
                            estado.ALTURA_BRACO = dragger.altura
                            estado.atualizar_medidas()
                        break
            if clicou_em_dragger:
                continue
            clicou_interface = False
            for i, secao in enumerate(estado.secoes_inferiores):
                if secao.get('rect_cabecalho') and secao['rect_cabecalho'].collidepoint(evento.pos):
                    estado_anterior = secao['expandido']
                    for s in estado.secoes_inferiores:
                        s['expandido'] = False
                    secao['expandido'] = not estado_anterior
                    clicou_interface = True
                    break
                if secao['expandido']:
                    if secao['conteudo'] == 'musicas' and secao['memoria_sub_aba'] == 2:
                        if hasattr(estado, 'rect_btn_criar_tablatura') and estado.rect_btn_criar_tablatura.collidepoint(evento.pos):
                            estado.tela_criacao_tab_ativa = True
                            clicou_interface = True
                            break
                    for j in range(len(secao['sub_abas'])):

                        chave_rect = f'rect_sub_{j}'
                        if secao.get(chave_rect) and secao[chave_rect].collidepoint(evento.pos):
                            secao['memoria_sub_aba'] = j
                            clicou_interface = True
                            break
                    if clicou_interface:
                        break
            if clicou_interface:
                continue
            clicou_conteudo = False
            for i, secao in enumerate(estado.secoes_inferiores):
                if secao['expandido']:
                    y_conteudo = dy_inf - altura_caixa_total - 10
                    rect_fundo_conteudo = pygame.Rect(dx_inf, y_conteudo, largura_conteudo, altura_caixa_total)
                    if rect_fundo_conteudo.collidepoint(evento.pos):
                        clicou_conteudo = True
                    scroll_atual = estado.scroll_y.get(i, 0)
                    y_start = y_conteudo + BOTTOM_OFFSET_AREA_DESENHO - scroll_atual
                    if secao['conteudo'] in ['escalas', 'acordes']:
                        pos_x_guit = estado.dragger_guitarra.x if hasattr(estado, 'dragger_guitarra') else 100
                        pos_y_guit = estado.dragger_guitarra.y if hasattr(estado, 'dragger_guitarra') else 90
                        rect_braco_real = pygame.Rect(pos_x_guit, pos_y_guit, estado.LARGURA_BRACO, estado.ALTURA_BRACO)
                        if gerenciador_interface.tratar_cliques_escalas(evento.pos, i, secao['memoria_sub_aba'], dicionario_escalas, rect_braco_real, scroll_atual):
                            clicou_conteudo = True
                            break
                    elif secao['conteudo'] == 'analise_ia':
                        sub_aba_ia = secao['memoria_sub_aba']
                        if sub_aba_ia == 0:
                            if meu_processador.tratar_clique(evento.pos, meu_gravador):
                                clicou_conteudo = True
                                break
                        elif sub_aba_ia == 1:
                            if meu_gerenciador_jogos.tratar_clique_aba(evento.pos, estado):
                                clicou_conteudo = True
                                break
                    elif secao['conteudo'] == 'configuracao':
                        configs.y = y_start
                        configs.x = dx_inf + 20
                        meu_metronomo.y = y_start
                        meu_metronomo.x = dx_inf + 20
                        if hasattr(meu_metronomo, 'x_config'):
                            meu_metronomo.x_config = dx_inf + 20
                        esta_na_config_cores = secao['memoria_sub_aba'] == 0
                        cor_antiga = configs.indice_modo
                        if configs.tratar_clique(evento.pos, esta_na_config_cores):
                            if configs.indice_modo != cor_antiga:
                                dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
                            clicou_conteudo = True
                            break
                        if meu_metronomo.tratar_clique(evento.pos, estado, aba_config_aberta=True):
                            clicou_conteudo = True
                            break
                    elif secao['conteudo'] == 'estudos':
                        if hasattr(estado, 'botoes_estudo'):
                            for nome_estudo, rect_btn in estado.botoes_estudo.items():
                                if rect_btn.collidepoint(evento.pos):
                                    estado.tela_estudo_ativa = True
                                    estado.estudo_ativo = nome_estudo
                                    clicou_conteudo = True
                                    break
                            if clicou_conteudo:
                                break
                    elif secao['conteudo'] == 'musicas':
                        if hasattr(estado, 'rect_aba_songsterr_busca') and estado.rect_aba_songsterr_busca.collidepoint(evento.pos):
                            estado.sub_memoria_musicas = 0
                            clicou_conteudo = True
                        elif hasattr(estado, 'rect_aba_songsterr_favs') and estado.rect_aba_songsterr_favs.collidepoint(evento.pos):
                            estado.sub_memoria_musicas = 1
                            clicou_conteudo = True
                        elif hasattr(estado, 'rect_aba_songsterr_locais') and estado.rect_aba_songsterr_locais.collidepoint(evento.pos):
                            estado.sub_memoria_musicas = 2
                            clicou_conteudo = True
                        if not clicou_conteudo and estado.sub_memoria_musicas == 0:
                            if hasattr(estado, 'rect_busca_songsterr') and estado.rect_busca_songsterr.collidepoint(evento.pos):
                                estado.songsterr_search_active = True
                                clicou_conteudo = True
                            else:
                                estado.songsterr_search_active = False
                            if hasattr(estado, 'rect_btn_songsterr') and estado.rect_btn_songsterr.collidepoint(evento.pos):
                                import threading

                                def thread_busca():
                                    """
                                        Como funciona: Executa o fluxo lógico necessário para a operação 'thread busca'.
                                        Para que serve: Realiza as tarefas fundamentais de 'thread busca' dentro do contexto do módulo.
                                        Onde é usada: Utilizado internamente para gerenciar comportamentos de 'thread busca'.
                                    """
                                    estado.resultados_songsterr = estado.songsterr.buscar_musicas(estado.query_songsterr)
                                threading.Thread(target=thread_busca).start()
                                clicou_conteudo = True
                        elif not clicou_conteudo and estado.sub_memoria_musicas == 2:
                            if hasattr(estado, 'rect_btn_add_midi') and estado.rect_btn_add_midi.collidepoint(evento.pos):
                                import tkinter as tk
                                from tkinter import filedialog
                                root = tk.Tk()
                                root.withdraw()
                                root.attributes('-topmost', True)
                                caminho = filedialog.askopenfilename(filetypes=[('MIDI files', '*.mid *.midi')])
                                root.destroy()
                                if caminho:
                                    import shutil
                                    import os
                                    nome_arquivo = os.path.basename(caminho)
                                    destino = os.path.join('Audios/Midis', nome_arquivo)
                                    try:
                                        if not os.path.exists('Audios/Midis'):
                                            os.makedirs('Audios/Midis')
                                        shutil.copy(caminho, destino)
                                        nova_musica = {'songId': f'local_{nome_arquivo}', 'title': nome_arquivo.replace('.mid', '').replace('.midi', ''), 'artist': 'Arquivo Local', 'local_path': destino}
                                        if not any((m['local_path'] == destino for m in estado.musicas_locais)):
                                            estado.musicas_locais.append(nova_musica)
                                        nova_tab = BlocoTablatura(200, 200, 700, 450, nova_musica)
                                        nova_tab.caminho_midi_local = destino
                                        nova_tab.carregar_dados_completos(estado.songsterr)
                                        estado.lista_tabs.append(nova_tab)
                                        clicou_conteudo = True
                                    except Exception as e:
                                        print(f'[UI] Erro ao selecionar MIDI: {e}')
                            if hasattr(estado, 'rects_musicas_locais'):
                                for rect_item, song_data in estado.rects_musicas_locais:
                                    if rect_item.collidepoint(evento.pos):
                                        nova_tab = BlocoTablatura(200, 200, 700, 450, song_data)
                                        nova_tab.caminho_midi_local = song_data.get('local_path')
                                        nova_tab.carregar_dados_completos(estado.songsterr)
                                        estado.lista_tabs.append(nova_tab)
                                        clicou_conteudo = True
                                        break
                        if not clicou_conteudo and hasattr(estado, 'rects_resultados_songsterr'):
                            for rect_res, song_data in estado.rects_resultados_songsterr:
                                if rect_res.collidepoint(evento.pos):
                                    nova_tab = BlocoTablatura(200, 200, 700, 450, song_data)
                                    nova_tab.favoritos_ref = estado.favoritos_songsterr
                                    nova_tab.carregar_dados_completos(estado.songsterr)
                                    estado.lista_tabs.append(nova_tab)
                                    clicou_conteudo = True
                                    break
                        if hasattr(estado, 'rects_favoritos_click'):
                            for rect_star, song_data in estado.rects_favoritos_click:
                                if rect_star.collidepoint(evento.pos):
                                    song_id = song_data.get('songId')
                                    song_idx = -1
                                    for idx, f in enumerate(estado.favoritos_songsterr):
                                        if f.get('songId') == song_id:
                                            song_idx = idx
                                            break
                                    from BD.gerenciador_remoto_db import GerenciadorDB
                                    db = GerenciadorDB()
                                    if song_idx >= 0:
                                        estado.favoritos_songsterr.pop(song_idx)
                                        if estado.usuario_id_logado:
                                            db.remover_favorito(estado.usuario_id_logado, song_id)
                                    else:
                                        novo_fav = {'songId': song_id, 'title': song_data.get('title'), 'artist': song_data.get('artist')}
                                        estado.favoritos_songsterr.append(novo_fav)
                                        if estado.usuario_id_logado:
                                            db.adicionar_favorito(estado.usuario_id_logado, song_id, novo_fav['title'], novo_fav['artist'])
                                    clicou_conteudo = True
                                    break
                        if clicou_conteudo:
                            break
            if clicou_conteudo:
                continue
            for tab in estado.lista_tabs[:]:
                acao = tab.tratar_clique(evento.pos)
                if acao == 'TELA_CHEIA':
                    estado.tab_tela_cheia_ativa = True
                    estado.tab_focada = tab
                    bloqueio_z_index = True
                    break
                elif acao:
                    bloqueio_z_index = True
                    break
            if bloqueio_z_index:
                continue
            from Core.constantes_ui import CORES_TONICA
            if hasattr(estado, 'rect_cor_tonica') and estado.rect_cor_tonica.collidepoint(evento.pos):
                estado.indice_cor_tonica = (estado.indice_cor_tonica + 1) % len(CORES_TONICA)
                continue
            elif hasattr(estado, 'rect_cor_terca') and estado.rect_cor_terca.collidepoint(evento.pos):
                estado.indice_cor_terca = (estado.indice_cor_terca + 1) % len(CORES_TONICA)
                continue
            elif hasattr(estado, 'rect_cor_quinta') and estado.rect_cor_quinta.collidepoint(evento.pos):
                estado.indice_cor_quinta = (estado.indice_cor_quinta + 1) % len(CORES_TONICA)
                continue
            if hasattr(estado, 'rects_notas_selecao'):
                for rect_n, nota_n in estado.rects_notas_selecao:
                    if rect_n.collidepoint(evento.pos):
                        estado.nota_selecionada_bloco = nota_n
                        continue
                if hasattr(estado, 'rect_barra_persistencia') and estado.rect_barra_persistencia.collidepoint(evento.pos):
                    barra = estado.rect_barra_persistencia
                    rel_x = max(0, min(barra.width, evento.pos[0] - barra.x))
                    estado.afinador_persistencia = int(100 + rel_x / barra.width * 2900)
                    continue
                if hasattr(estado, 'rect_barra_threshold') and estado.rect_barra_threshold.collidepoint(evento.pos):
                    barra = estado.rect_barra_threshold
                    rel_x = max(0, min(barra.width, evento.pos[0] - barra.x))
                    estado.afinador_threshold = 0.1 + rel_x / barra.width * 0.7
                    continue
            if hasattr(estado, 'dragger_acordes') and meu_campo_harmonico.tratar_clique(evento.pos):
                estado.tom_atual = getattr(meu_campo_harmonico, 'tom', getattr(meu_campo_harmonico, 'tonica', estado.tom_atual))
                dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
                continue
            if meu_metronomo.tratar_clique(evento.pos, estado):
                continue
