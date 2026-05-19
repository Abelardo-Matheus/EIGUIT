# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# =============================================================================

import pygame
from Interface import fabrica_escalas
from Interface import gerenciador_interface
from Core.constantes_ui import *
import Modulos.modulo_menu_contexto as modulo_menu_contexto
import Modulos.modulo_menu_superior as modulo_menu_superior 

def processar(eventos, estado, configs, dicionario_escalas, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico, meu_gerenciador_jogos):
    
    # =========================================================================
    # 1. INICIALIZAÇÃO DE MENUS GLOBAIS
    # =========================================================================
    if not hasattr(estado, 'menu_contexto'):
        estado.menu_contexto = modulo_menu_contexto.MenuContexto()
    if not hasattr(estado, 'menu_superior'):
        estado.menu_superior = modulo_menu_superior.MenuSuperior()

    # =========================================================================
    # 2. TRAVAS DE SOBREPOSIÇÃO MÁXIMA (PERFIL, JOGOS E ESTUDOS)
    # =========================================================================
    if hasattr(estado, 'gerenciador_perfil') and estado.gerenciador_perfil.ativo:
        if estado.gerenciador_perfil.tratar_eventos(eventos, estado, configs, meu_campo_harmonico, meu_gravador):
            dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
            return 

    if getattr(estado, 'tela_jogo_ativa', False):
        for evento in eventos:
            if evento.type == pygame.QUIT: 
                estado.solicitou_saida = True
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                estado.tela_jogo_ativa = False
                meu_gerenciador_jogos.jogo_instancia = None 
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                meu_gerenciador_jogos.tratar_clique_tela_jogo(evento.pos, estado, meu_gravador)
        return

    # Trava Total da Tela de Estudos
    if getattr(estado, 'tela_estudo_ativa', False):
        for evento in eventos:
            if evento.type == pygame.QUIT: 
                estado.solicitou_saida = True
            if hasattr(estado, 'gerenciador_estudos'):
                estado.gerenciador_estudos.tratar_eventos(evento, pygame.mouse.get_pos(), estado)
        return
    
    pos_mouse = pygame.mouse.get_pos()

    # =========================================================================
    # 3. CÁLCULO DE Z-INDEX (PAINEL INFERIOR)
    # =========================================================================
    bloqueio_z_index = False
    dx_inf = estado.dragger_painel_inferior.x if hasattr(estado, 'dragger_painel_inferior') else 100
    dy_inf = estado.dragger_painel_inferior.y if hasattr(estado, 'dragger_painel_inferior') else estado.ALTURA_TELA - 50
    altura_caixa_total = 350
    largura_conteudo = estado.dragger_painel_inferior.largura if hasattr(estado, 'dragger_painel_inferior') else estado.LARGURA_BRACO

    for secao in estado.secoes_inferiores:
        if secao["expandido"]:
            y_conteudo = dy_inf - altura_caixa_total - 10
            rect_fundo_conteudo = pygame.Rect(dx_inf, y_conteudo, largura_conteudo, altura_caixa_total)
            if rect_fundo_conteudo.collidepoint(pos_mouse):
                bloqueio_z_index = True
            break
    
    # Lista unificada de draggers para evitar code smells
    def obter_draggers_ativos(estado):
        lista = []
        simples = ['dragger_controles_topo', 'dragger_cores', 'dragger_metronomo', 'dragger_acordes', 'dragger_painel_inferior', 'dragger_nota_atual']
        for d in simples:
            if hasattr(estado, d): lista.append(getattr(estado, d))
        if hasattr(estado, 'lista_guitarras'):
            lista.extend(reversed(estado.lista_guitarras))
        return lista

    # =========================================================================
    # 4. LOOP PRINCIPAL DE EVENTOS
    # =========================================================================
    for evento in eventos:
        if evento.type == pygame.QUIT: 
            estado.solicitou_saida = True

        # --- MENU SUPERIOR ---
        # ... (rest of the code below will be updated to use obter_draggers_ativos)

        # --- MENU SUPERIOR ---
        if estado.menu_superior.tratar_eventos(evento, pos_mouse, estado, configs, meu_campo_harmonico, meu_gravador):
            dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
            continue 

        # --- MENU DE CONTEXTO (CLIQUE DIREITO) ---
        if not hasattr(estado, 'lista_guitarras'):
            estado.lista_guitarras = [estado.dragger_guitarra] if hasattr(estado, 'dragger_guitarra') else []

        acao_contexto = estado.menu_contexto.tratar_eventos(evento, pos_mouse, estado)
        if acao_contexto == "CONSUMIU_EVENTO" or acao_contexto == "FECHOU_MENU":
            continue
        elif isinstance(acao_contexto, tuple):
            acao, alvo, tipo = acao_contexto
            print(f"[MENU] Ação: {acao} | Alvo: {tipo}")
            if tipo == "guitarra":
                if acao == "Apagar" and alvo in estado.lista_guitarras:
                    estado.lista_guitarras.remove(alvo)
                    if estado.dragger_guitarra == alvo:
                        estado.dragger_guitarra = estado.lista_guitarras[0] if estado.lista_guitarras else None
                elif acao in ["Duplicar Bloco (Cópia)", "Nova Seção Vazia"]:
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
                            estado.menu_contexto.abrir(pos_mouse, "guitarra", guit)
                            abriu_menu = True
                        else:
                            for lista_modulos in dicionario_escalas.values():
                                for modulo in lista_modulos:
                                    if modulo.estado != 'painel': modulo.estado = 'painel'
                        break 

            if not abriu_menu and hasattr(estado, 'dragger_acordes'):
                rect_acordes = pygame.Rect(estado.dragger_acordes.x, estado.dragger_acordes.y, estado.dragger_acordes.largura, estado.dragger_acordes.altura)
                if rect_acordes.collidepoint(pos_mouse) and estado.drag_ativado:
                    estado.menu_contexto.abrir(pos_mouse, "acordes", estado.dragger_acordes)
                    abriu_menu = True
                    
            if not abriu_menu:
                estado.menu_contexto.abrir(pos_mouse, "fundo_mesa")
            continue

        # --- SCROLL DO MOUSE ---
        if evento.type == pygame.MOUSEWHEEL:
            velocidade_scroll = 40
            for i, secao in enumerate(estado.secoes_inferiores):
                if secao["expandido"] and estado.max_scroll.get(i, 0) > 0:
                    estado.scroll_y[i] -= evento.y * velocidade_scroll
                    estado.scroll_y[i] = max(0, min(estado.scroll_y[i], estado.max_scroll[i]))

        # --- TECLADO ---
        if evento.type == pygame.KEYDOWN:
            meu_metronomo.tratar_teclado(evento)
            if evento.key == pygame.K_ESCAPE: estado.solicitou_saida = True

        # =====================================================================
        # DRAGGERS - MOVIMENTO (MOUSEMOTION) E SOLTAR (MOUSEBUTTONUP)
        # =====================================================================
        if estado.drag_ativado and evento.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP):
            for dragger in obter_draggers_ativos(estado):
                dragger.processar_eventos_mouse(evento)
                # Se for a guitarra redimensionando, sincroniza
                if hasattr(dragger, 'redimensionando') and evento.type == pygame.MOUSEMOTION and dragger.redimensionando:
                    estado.LARGURA_BRACO = dragger.largura
                    estado.ALTURA_BRACO = dragger.altura
                    estado.atualizar_medidas()
        
        # --- SOLTAR O CLIQUE ESQUERDO: Atualizar os dados das escalas de vez ---
        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1 and estado.drag_ativado:
            dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))

        # --- CLIQUE ESQUERDO DO MOUSE (INTERAÇÕES INICIAIS E DRAGGERS) ---
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            
            # Botão Alfinete
            if hasattr(estado, 'rect_btn_pin') and estado.rect_btn_pin.collidepoint(evento.pos):
                estado.drag_ativado = not estado.drag_ativado
                if not estado.drag_ativado:
                    for dragger in obter_draggers_ativos(estado): dragger.arrastando = False
                continue 

            # Detecção de Draggers (Saber se ele Clicou em cima de um bloco)
            clicou_em_dragger = False
            if estado.drag_ativado:
                for dragger in obter_draggers_ativos(estado):
                    # Guitarras têm margem maior
                    margem = 20 if hasattr(dragger, 'num_cordas') else 5
                    if dragger.processar_eventos_mouse(evento, margem_clique=margem):
                        clicou_em_dragger = True
                        if hasattr(dragger, 'redimensionando') and dragger.redimensionando:
                            estado.LARGURA_BRACO = dragger.largura
                            estado.ALTURA_BRACO = dragger.altura
                            estado.atualizar_medidas()
                        break
            
            # Se clicou num dragger para arrastar, ignora a UI embaixo
            if clicou_em_dragger:
                continue

            # Tabs Expansíveis (Cabeçalhos e Sub-abas)
            clicou_interface = False
            for i, secao in enumerate(estado.secoes_inferiores):
                if secao.get("rect_cabecalho") and secao["rect_cabecalho"].collidepoint(pos_mouse):
                    estado_anterior = secao["expandido"]
                    for s in estado.secoes_inferiores: s["expandido"] = False
                    secao["expandido"] = not estado_anterior
                    clicou_interface = True
                    break
                
                if secao["expandido"]:
                    for j in range(len(secao["sub_abas"])):
                        chave_rect = f"rect_sub_{j}"
                        if secao.get(chave_rect) and secao[chave_rect].collidepoint(pos_mouse):
                            secao["memoria_sub_aba"] = j
                            clicou_interface = True
                            break
            
            if clicou_interface: 
                continue 
            
            # CONTEÚDO DAS ÁREAS EXPANDIDAS
            clicou_conteudo = False
            for i, secao in enumerate(estado.secoes_inferiores):
                if secao["expandido"]:
                    scroll_atual = estado.scroll_y.get(i, 0)
                    
                    if secao["conteudo"] in ["escalas", "acordes"]:
                        pos_x_guit = estado.dragger_guitarra.x if hasattr(estado, 'dragger_guitarra') else 100
                        pos_y_guit = estado.dragger_guitarra.y if hasattr(estado, 'dragger_guitarra') else 90
                        rect_braco_real = pygame.Rect(pos_x_guit, pos_y_guit, estado.LARGURA_BRACO, estado.ALTURA_BRACO)
                        
                        if gerenciador_interface.tratar_cliques_escalas(pos_mouse, i, secao["memoria_sub_aba"], dicionario_escalas, rect_braco_real, scroll_atual):
                            clicou_conteudo = True
                            break
                            
                    elif secao["conteudo"] == "analise_ia":
                        sub_aba_ia = secao["memoria_sub_aba"]
                        if sub_aba_ia == 0:
                            if meu_processador.tratar_clique(evento.pos, meu_gravador):
                                clicou_conteudo = True; break
                        elif sub_aba_ia == 1:
                            if meu_gerenciador_jogos.tratar_clique_aba(evento.pos, estado):
                                clicou_conteudo = True; break
                    elif secao["conteudo"] == "configuracao":
                        configs.y = estado.Y_AREA_DESENHO + 20
                        configs.x = dx_inf + 20 
                        
                        meu_metronomo.y_config = estado.Y_AREA_DESENHO + 20
                        meu_metronomo.x = dx_inf + 20 
                        if hasattr(meu_metronomo, 'x_config'): meu_metronomo.x_config = dx_inf + 20
                        
                        esta_na_config_cores = (secao["memoria_sub_aba"] == 0) 
                        cor_antiga = configs.indice_modo
                        
                        if configs.tratar_clique(evento.pos, esta_na_config_cores):
                            if configs.indice_modo != cor_antiga: dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
                            clicou_conteudo = True; break
                        if meu_metronomo.tratar_clique(evento.pos, estado, aba_config_aberta=True): 
                            clicou_conteudo = True; break   

                    elif secao["conteudo"] == "estudos":
                        if hasattr(estado, 'botoes_estudo'):
                            for nome_estudo, rect_btn in estado.botoes_estudo.items():
                                if rect_btn.collidepoint(evento.pos):
                                    estado.tela_estudo_ativa = True
                                    estado.estudo_ativo = nome_estudo
                                    clicou_conteudo = True
                                    break
                            if clicou_conteudo: break

            if clicou_conteudo:
                continue

            if bloqueio_z_index: 
                continue 

            # Painel de Cores (Graus)
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
            
            # Bloco de Nota Atual e Seleção
            if hasattr(estado, 'rects_notas_selecao'):
                for rect_n, nota_n in estado.rects_notas_selecao:
                    if rect_n.collidepoint(evento.pos):
                        estado.nota_selecionada_bloco = nota_n
                        continue
                
                # Sliders de Calibração
                if hasattr(estado, 'rect_barra_persistencia') and estado.rect_barra_persistencia.collidepoint(evento.pos):
                    barra = estado.rect_barra_persistencia
                    rel_x = max(0, min(barra.width, evento.pos[0] - barra.x))
                    estado.afinador_persistencia = int(100 + (rel_x / barra.width) * 2900)
                    continue
                
                if hasattr(estado, 'rect_barra_threshold') and estado.rect_barra_threshold.collidepoint(evento.pos):
                    barra = estado.rect_barra_threshold
                    rel_x = max(0, min(barra.width, evento.pos[0] - barra.x))
                    estado.afinador_threshold = 0.1 + (rel_x / barra.width) * 0.7
                    continue

            # Campo Harmônico
            if hasattr(estado, 'dragger_acordes') and meu_campo_harmonico.tratar_clique(evento.pos): 
                estado.tom_atual = getattr(meu_campo_harmonico, 'tom', getattr(meu_campo_harmonico, 'tonica', estado.tom_atual))
                dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
                continue

            # Mini-Metrônomo
            if meu_metronomo.tratar_clique(evento.pos, estado): continue

            # Controles do Topo
            if hasattr(estado, 'btn_guit') and estado.btn_guit.collidepoint(evento.pos): estado.instrumento = 'guitarra'; continue
            if hasattr(estado, 'btn_baixo') and estado.btn_baixo.collidepoint(evento.pos): estado.instrumento = 'baixo'; continue

            if hasattr(estado, 'btn_menos_afinacao') and estado.btn_menos_afinacao.collidepoint(evento.pos):
                estado.indice_afinacao = (estado.indice_afinacao - 1) % len(lista_afinacoes)
                dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
                continue
            if hasattr(estado, 'btn_mais_afinacao') and estado.btn_mais_afinacao.collidepoint(evento.pos):
                estado.indice_afinacao = (estado.indice_afinacao + 1) % len(lista_afinacoes)
                dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
                continue