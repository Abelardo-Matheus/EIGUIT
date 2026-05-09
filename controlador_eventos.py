# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================

import pygame
import fabrica_escalas as fabrica_escalas
import gerenciador_interface as gerenciador_interface
from constantes_ui import *

# Removi o import do GerenciadorJogos daqui porque ele já virá instanciado do main.py via parâmetro.

# 1. CORREÇÃO: Adicionado 'meu_gerenciador_jogos' nos argumentos da função
def processar(eventos, estado, configs, dicionario_escalas, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico, meu_gerenciador_jogos):
    
    # =========================================================
    # --- TRAVA DE TELA CHEIA (JOGOS) ---
    # =========================================================
    if getattr(estado, 'tela_jogo_ativa', False):
        for evento in eventos:
            if evento.type == pygame.QUIT: 
                estado.solicitou_saida = True
                
            # ADICIONADO: Pressionar ESC para fechar o jogo
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                estado.tela_jogo_ativa = False
                meu_gerenciador_jogos.jogo_instancia = None # Limpa a memória do jogo
                
            # PASSANDO O GRAVADOR NO CLIQUE:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                meu_gerenciador_jogos.tratar_clique_tela_jogo(evento.pos, estado, meu_gravador)
        return
    
    pos_mouse = pygame.mouse.get_pos()
    
    for evento in eventos:
        if evento.type == pygame.QUIT: 
            estado.solicitou_saida = True

        # =========================================================
        # --- LÓGICA DO ALFINETE (LIGAR/DESLIGAR MODO ARRASTAR) ---
        # =========================================================
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if hasattr(estado, 'rect_btn_pin') and estado.rect_btn_pin.collidepoint(evento.pos):
                estado.drag_ativado = not estado.drag_ativado
                
                # Se desligou o drag, limpa o estado de "segurando" de todos os draggers
                if not estado.drag_ativado:
                    draggers = ['dragger_guitarra', 'dragger_acordes', 'dragger_controles_topo', 
                                'dragger_painel_inferior', 'dragger_metronomo']
                    for d in draggers:
                        if hasattr(estado, d): getattr(estado, d).arrastando = False
                continue 

        # =========================================================
        # --- DRAG & DROP: DETECÇÃO DE MOVIMENTO ---
        # =========================================================
        clicou_em_dragger = False

        if estado.drag_ativado:
            # Ordem de prioridade de clique (do menor/mais específico para o maior)
            if hasattr(estado, 'dragger_controles_topo') and estado.dragger_controles_topo.processar_eventos_mouse(evento, margem_clique=5): 
                clicou_em_dragger = True
            
            # --- ADICIONADO: Arraste do Metrônomo ---
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

        # Quando solta o mouse no modo drag, regenera os módulos para fixar as novas posições
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
            pos_mouse = pygame.mouse.get_pos()
            
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
            
            # --- CLIQUES NO CAMPO HARMÔNICO ---
            if hasattr(estado, 'dragger_acordes'):
                if meu_campo_harmonico.tratar_clique(evento.pos): pass 

            # --- CLIQUES NO MINI-METRÔNOMO (BOTOES E SLIDER) ---
            if meu_metronomo.tratar_clique(evento.pos, estado): 
                continue

            # --- CLIQUES NOS CONTROLES DO TOPO (CASAS / INSTRUMENTO) ---
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

            # --- CLIQUES NO CONTEÚDO DAS ÁREAS EXPANDIDAS ---
            for i, secao in enumerate(estado.secoes_inferiores):
                if secao["expandido"]:
                    dx_inf = estado.dragger_painel_inferior.x if hasattr(estado, 'dragger_painel_inferior') else 100
                    scroll_atual = estado.scroll_y.get(i, 0)
                    
                    if secao["conteudo"] in ["escalas", "acordes"]:
                        # 1. Pega a posição verdadeira do braço da guitarra!
                        pos_x_guit = estado.dragger_guitarra.x if hasattr(estado, 'dragger_guitarra') else 100
                        pos_y_guit = estado.dragger_guitarra.y if hasattr(estado, 'dragger_guitarra') else 90
                        altura_guit = estado.ALTURA_BRACO
                        
                        rect_braco_real = pygame.Rect(pos_x_guit, pos_y_guit, estado.LARGURA_BRACO, altura_guit)
                        
                        # 2. Manda o retângulo certo para a escala saber onde grudar
                        if gerenciador_interface.tratar_cliques_escalas(pos_mouse, i, secao["memoria_sub_aba"], dicionario_escalas, rect_braco_real, scroll_atual):
                            continue
                            
                    elif secao["conteudo"] == "analise_ia":
                        # 3. CORREÇÃO: Descobrir qual aba está aberta antes de checar os cliques
                        sub_aba_ia = secao["memoria_sub_aba"]
                        
                        if sub_aba_ia == 0:
                            btn_gravar_ia = pygame.Rect(dx_inf + 20, estado.Y_AREA_DESENHO + 50 - scroll_atual, 150, 40)
                            if meu_processador.tratar_clique(evento.pos, btn_gravar_ia, meu_gravador): continue
                            if meu_processador.tratar_clique_calibracao(evento.pos, estado, dx_inf, estado.Y_AREA_DESENHO - scroll_atual): continue
                        
                        # O ritmo (sub_aba_ia == 1) ainda não tem cliques
                        
                        elif sub_aba_ia == 2:
                            # 2. CORREÇÃO: Usando a instância e passando os argumentos certos
                            if meu_gerenciador_jogos.tratar_clique_aba(evento.pos, estado): continue

                    elif secao["conteudo"] == "configuracao":
                        configs.y = estado.Y_AREA_DESENHO + 20
                        meu_metronomo.y_config = estado.Y_AREA_DESENHO + 20
                        esta_na_config_cores = (secao["memoria_sub_aba"] == 0) 
                        cor_antiga = configs.indice_modo
                        
                        if configs.tratar_clique(evento.pos, esta_na_config_cores):
                            if configs.indice_modo != cor_antiga:
                                dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
                            continue
                        
                        if meu_metronomo.tratar_clique(evento.pos, estado, aba_config_aberta=True): 
                            continue