# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# =============================================================================

import pygame
import fabrica_escalas as fabrica_escalas
import gerenciador_interface as gerenciador_interface
from constantes_ui import *

# IMPORTANTE: Carrega o Menu Superior para o cérebro do programa
import Modulos.modulo_menu_superior as modulo_menu_superior 

def processar(eventos, estado, configs, dicionario_escalas, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico, meu_gerenciador_jogos):
    
    # =========================================================================
    # 1. TRAVA DO MODAL DE PERFIS: Engole os eventos se a janelinha estiver aberta
    # AGORA PASSAMOS TODAS AS CONFIGS PRA ELE PODER SALVAR/CARREGAR
    # =========================================================================
    if hasattr(estado, 'gerenciador_perfil') and estado.gerenciador_perfil.ativo:
        if estado.gerenciador_perfil.tratar_eventos(eventos, estado, configs, meu_campo_harmonico, meu_gravador):
            # Força o recálculo das escalas se houver mudança de tom/casas ao carregar perfil
            dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
            return 

    # 2. Cria o menu globalmente na memória se ele ainda não existir
    if not hasattr(estado, 'menu_superior'):
        estado.menu_superior = modulo_menu_superior.MenuSuperior()

    # 3. TRAVA DE TELA CHEIA (JOGOS)
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
    
    pos_mouse = pygame.mouse.get_pos()

    # 4. CÁLCULO DE Z-INDEX (Bloqueia cliques vazados para as janelas de baixo)
    bloqueio_z_index = False
    dx_inf = estado.dragger_painel_inferior.x if hasattr(estado, 'dragger_painel_inferior') else 100
    dy_inf = estado.dragger_painel_inferior.y if hasattr(estado, 'dragger_painel_inferior') else estado.ALTURA_TELA - 50
    altura_caixa_total = 350
    
    # =========================================================================
    # CORREÇÃO DA ZONA DE CLIQUE PARA O NOVO TAMANHO
    # =========================================================================
    largura_conteudo = estado.dragger_painel_inferior.largura if hasattr(estado, 'dragger_painel_inferior') else estado.LARGURA_BRACO

    for secao in estado.secoes_inferiores:
        if secao["expandido"]:
            y_conteudo = dy_inf - altura_caixa_total - 10
            rect_fundo_conteudo = pygame.Rect(dx_inf, y_conteudo, largura_conteudo, altura_caixa_total)
            if rect_fundo_conteudo.collidepoint(pos_mouse):
                bloqueio_z_index = True
            break
    
    for evento in eventos:
        if evento.type == pygame.QUIT: 
            estado.solicitou_saida = True

        # =========================================================
        # --- AVALIA O MENU SUPERIOR ANTES DE TUDO! ---
        # =========================================================
        # Envia os parâmetros completos para ele acionar as funções de perfil
        if estado.menu_superior.tratar_eventos(evento, pos_mouse, estado, configs, meu_campo_harmonico, meu_gravador):
            dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
            continue 

        # =========================================================
        # --- REMOVER ESCALA COM BOTÃO DIREITO DO MOUSE ---
        # =========================================================
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 3:
            dx_guit = estado.dragger_guitarra.x if hasattr(estado, 'dragger_guitarra') else 100
            dy_guit = estado.dragger_guitarra.y if hasattr(estado, 'dragger_guitarra') else 90
            rect_guit = pygame.Rect(dx_guit, dy_guit, estado.LARGURA_BRACO, estado.ALTURA_BRACO)
            
            if rect_guit.collidepoint(pos_mouse):
                for lista_modulos in dicionario_escalas.values():
                    for modulo in lista_modulos:
                        if modulo.estado != 'painel':
                            modulo.estado = 'painel'
            continue

        # =========================================================
        # --- LÓGICA DO ALFINETE (LIGAR/DESLIGAR MODO ARRASTAR) ---
        # =========================================================
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if hasattr(estado, 'rect_btn_pin') and estado.rect_btn_pin.collidepoint(evento.pos):
                estado.drag_ativado = not estado.drag_ativado
                
                if not estado.drag_ativado:
                    draggers = ['dragger_guitarra', 'dragger_acordes', 'dragger_controles_topo', 
                                'dragger_painel_inferior', 'dragger_metronomo', 'dragger_cores'] 
                    for d in draggers:
                        if hasattr(estado, d): getattr(estado, d).arrastando = False
                continue 

        # =========================================================
        # --- DRAG & DROP: DETECÇÃO DE MOVIMENTO ---
        # =========================================================
        clicou_em_dragger = False

        # ... código existente (onde ele testa se clicou nos draggers)...
        
        if estado.drag_ativado:
            if hasattr(estado, 'dragger_controles_topo') and estado.dragger_controles_topo.processar_eventos_mouse(evento, margem_clique=5): 
                clicou_em_dragger = True

            if not clicou_em_dragger and hasattr(estado, 'dragger_cores'):
                if estado.dragger_cores.processar_eventos_mouse(evento, margem_clique=5):
                    clicou_em_dragger = True
                
            if not clicou_em_dragger and hasattr(estado, 'dragger_metronomo'):
                if estado.dragger_metronomo.processar_eventos_mouse(evento, margem_clique=5):
                    clicou_em_dragger = True

            if not clicou_em_dragger and hasattr(estado, 'dragger_guitarra'):
                if estado.dragger_guitarra.processar_eventos_mouse(evento, margem_clique=20):
                    clicou_em_dragger = True

            if not clicou_em_dragger and hasattr(estado, 'dragger_acordes'):
                if estado.dragger_acordes.processar_eventos_mouse(evento, margem_clique=10):
                    clicou_em_dragger = True

            if not clicou_em_dragger and hasattr(estado, 'dragger_painel_inferior'):
                if estado.dragger_painel_inferior.processar_eventos_mouse(evento, margem_clique=5):
                    clicou_em_dragger = True

            # =========================================================================
            # NOVO: SINCRONIZA O TAMANHO DO BRAÇO QUANDO REDIMENSIONADO
            # =========================================================================
            if hasattr(estado, 'dragger_guitarra') and estado.dragger_guitarra.redimensionando:
                # Ao redimensionar a caixa, repassamos a nova largura/altura pro estado e mandamos recalcular
                estado.LARGURA_BRACO = estado.dragger_guitarra.largura
                estado.ALTURA_BRACO = estado.dragger_guitarra.altura
                estado.atualizar_medidas()
            # =========================================================================

        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1 and estado.drag_ativado:
            dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))

        # =========================================================
        # --- ROLAGEM E ATALHOS ---
        # =========================================================
        if evento.type == pygame.MOUSEWHEEL:
            velocidade_scroll = 40
            for i, secao in enumerate(estado.secoes_inferiores):
                if secao["expandido"] and estado.max_scroll.get(i, 0) > 0:
                    estado.scroll_y[i] -= evento.y * velocidade_scroll
                    estado.scroll_y[i] = max(0, min(estado.scroll_y[i], estado.max_scroll[i]))

        if evento.type == pygame.KEYDOWN:
            meu_metronomo.tratar_teclado(evento)
            if evento.key == pygame.K_ESCAPE: estado.solicitou_saida = True
                
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            
            # --- CLIQUES NA INTERFACE DE ABAS (EXPANDIR/RECOLHER) ---
            if not clicou_em_dragger:
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
                                
                if clicou_interface: continue 
            
            # --- CLIQUES NO CONTEÚDO DAS ÁREAS EXPANDIDAS (Acontece por cima de tudo) ---
            for i, secao in enumerate(estado.secoes_inferiores):
                if secao["expandido"]:
                    scroll_atual = estado.scroll_y.get(i, 0)
                    
                    if secao["conteudo"] in ["escalas", "acordes"]:
                        pos_x_guit = estado.dragger_guitarra.x if hasattr(estado, 'dragger_guitarra') else 100
                        pos_y_guit = estado.dragger_guitarra.y if hasattr(estado, 'dragger_guitarra') else 90
                        rect_braco_real = pygame.Rect(pos_x_guit, pos_y_guit, estado.LARGURA_BRACO, estado.ALTURA_BRACO)
                        
                        if gerenciador_interface.tratar_cliques_escalas(pos_mouse, i, secao["memoria_sub_aba"], dicionario_escalas, rect_braco_real, scroll_atual):
                            continue
                            
                    elif secao["conteudo"] == "analise_ia":
                        sub_aba_ia = secao["memoria_sub_aba"]
                        if sub_aba_ia == 0:
                            btn_gravar_ia = pygame.Rect(dx_inf + 20, estado.Y_AREA_DESENHO + 50 - scroll_atual, 150, 40)
                            if meu_processador.tratar_clique(evento.pos, btn_gravar_ia, meu_gravador): continue
                            if meu_processador.tratar_clique_calibracao(evento.pos, estado, dx_inf, estado.Y_AREA_DESENHO - scroll_atual): continue
                        elif sub_aba_ia == 1:
                            tempo_atual = pygame.time.get_ticks()
                            if hasattr(meu_processador, 'tratar_clique_ritmo'):
                                if meu_processador.tratar_clique_ritmo(evento.pos, tempo_atual, meu_metronomo, estado): 
                                    continue
                        elif sub_aba_ia == 2:
                            if meu_gerenciador_jogos.tratar_clique_aba(evento.pos, estado): continue

                    elif secao["conteudo"] == "configuracao":
                        configs.y = estado.Y_AREA_DESENHO + 20
                        meu_metronomo.y_config = estado.Y_AREA_DESENHO + 20
                        esta_na_config_cores = (secao["memoria_sub_aba"] == 0) 
                        cor_antiga = configs.indice_modo
                        if configs.tratar_clique(evento.pos, esta_na_config_cores):
                            if configs.indice_modo != cor_antiga: dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
                            continue
                        if meu_metronomo.tratar_clique(evento.pos, estado, aba_config_aberta=True): continue

            # APLICA A TRAVA DE CLIQUE AQUI
            if bloqueio_z_index:
                continue 

            # --- CLIQUES NO PAINEL DE CORES (GRAUS) ---
            from constantes_ui import CORES_TONICA
            if hasattr(estado, 'rect_cor_tonica') and estado.rect_cor_tonica.collidepoint(evento.pos):
                estado.indice_cor_tonica = (estado.indice_cor_tonica + 1) % len(CORES_TONICA)
                continue
            elif hasattr(estado, 'rect_cor_terca') and estado.rect_cor_terca.collidepoint(evento.pos):
                estado.indice_cor_terca = (estado.indice_cor_terca + 1) % len(CORES_TONICA)
                continue
            elif hasattr(estado, 'rect_cor_quinta') and estado.rect_cor_quinta.collidepoint(evento.pos):
                estado.indice_cor_quinta = (estado.indice_cor_quinta + 1) % len(CORES_TONICA)
                continue
            
            # --- CLIQUES NO CAMPO HARMÔNICO ---
            if hasattr(estado, 'dragger_acordes'):
                if meu_campo_harmonico.tratar_clique(evento.pos): 
                    tom_global = getattr(meu_campo_harmonico, 'tom', getattr(meu_campo_harmonico, 'tonica', estado.tom_atual))
                    estado.tom_atual = tom_global
                    dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
                    continue

            # --- CLIQUES NO MINI-METRÔNOMO ---
            if meu_metronomo.tratar_clique(evento.pos, estado): continue

            # --- CLIQUES NOS CONTROLES DO TOPO ---
            dx_topo = estado.dragger_controles_topo.x if hasattr(estado, 'dragger_controles_topo') else 100
            dy_topo = estado.dragger_controles_topo.y if hasattr(estado, 'dragger_controles_topo') else 30

            btn_guit_mock = pygame.Rect(dx_topo + 250, dy_topo, 110, 35)
            btn_baixo_mock = pygame.Rect(dx_topo + 370, dy_topo, 110, 35)

            if btn_guit_mock.collidepoint(evento.pos):
                estado.instrumento = 'guitarra'
                continue
            elif btn_baixo_mock.collidepoint(evento.pos):
                estado.instrumento = 'baixo'
                continue

            btn_menos_casa = pygame.Rect(dx_topo, dy_topo, 40, 35)
            btn_mais_casa = pygame.Rect(dx_topo + 160, dy_topo, 40, 35)
            
            if btn_menos_casa.collidepoint(evento.pos) and estado.NUM_CASAS > 12:
                estado.NUM_CASAS -= 1
                estado.atualizar_medidas()
                dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
                continue
            if btn_mais_casa.collidepoint(evento.pos) and estado.NUM_CASAS < 24:
                estado.NUM_CASAS += 1
                estado.atualizar_medidas()
                dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
                continue
            
            if hasattr(estado, 'btn_menos_afinacao') and estado.btn_menos_afinacao.collidepoint(evento.pos):
                from constantes_ui import lista_afinacoes
                estado.indice_afinacao = (estado.indice_afinacao - 1) % len(lista_afinacoes)
                dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
                continue
            if hasattr(estado, 'btn_mais_afinacao') and estado.btn_mais_afinacao.collidepoint(evento.pos):
                from constantes_ui import lista_afinacoes
                estado.indice_afinacao = (estado.indice_afinacao + 1) % len(lista_afinacoes)
                dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
                continue