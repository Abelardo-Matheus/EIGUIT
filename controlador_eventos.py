# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 [SEU NOME]
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================

import pygame
import fabrica_escalas as fabrica_escalas
import gerenciador_interface as gerenciador_interface
from constantes_ui import *

def processar(eventos, estado, configs, dicionario_escalas, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico):
    pos_mouse = pygame.mouse.get_pos()
    
    for evento in eventos:
        if evento.type == pygame.QUIT: 
            estado.solicitou_saida = True

        # ROLAGEM DO MOUSE (SCROLL)
        if evento.type == pygame.MOUSEWHEEL:
            aba = estado.aba_atual
            velocidade_scroll = 40
            
            # Só rola se aquela aba tiver um limite máximo definido
            if estado.max_scroll[aba] > 0:
                estado.scroll_y[aba] -= evento.y * velocidade_scroll
                # Trava para não subir pro infinito nem passar do limite
                estado.scroll_y[aba] = max(0, min(estado.scroll_y[aba], estado.max_scroll[aba]))

        if evento.type == pygame.KEYDOWN:
            meu_metronomo.tratar_teclado(evento)
            if evento.key == pygame.K_ESCAPE: 
                estado.solicitou_saida = True
                
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            pos_mouse = pygame.mouse.get_pos()
            
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if meu_campo_harmonico.tratar_clique(evento.pos):
                    pass # Se clicou no campo harmônico, já foi tratado!

            # --- LÓGICA DO CLIQUE DOS INSTRUMENTOS (Guitarra / Baixo) ---
            if hasattr(estado, 'btn_guit') and estado.btn_guit.collidepoint(evento.pos):
                estado.instrumento = 'guitarra'
                continue
                
            elif hasattr(estado, 'btn_baixo') and estado.btn_baixo.collidepoint(evento.pos):
                estado.instrumento = 'baixo'
                continue

            # --- IA: SUB-ABA 0 (AFINADOR) ---
            if estado.aba_atual == 2 and estado.memoria_sub_abas[2] == 0:
                btn_gravar_ia = pygame.Rect(estado.OFFSET_X + 20, estado.Y_CAIXA + 100, 150, 40)
                if meu_processador.tratar_clique(evento.pos, btn_gravar_ia, meu_gravador): 
                    continue
                
                if meu_processador.tratar_clique_calibracao(evento.pos, estado, estado.OFFSET_X, estado.Y_CAIXA):
                    continue

            # --- IA: SUB-ABA 1 (TREINO DE RITMO) ---
            # Aqui é onde a mágica acontece: liga o MIC e inicia a contagem
            if estado.aba_atual == 2 and estado.memoria_sub_abas[2] == 1:
                tempo_atual = pygame.time.get_ticks()
                if meu_processador.tratar_cliques_treino_ritmo(evento.pos, tempo_atual, meu_gravador, meu_metronomo):
                    continue
            
            # --- CONFIGURAÇÕES E METRÔNOMO ---
            esta_na_config_cores = (estado.aba_atual == 3 and estado.memoria_sub_abas[3] == 0)
            cor_antiga = configs.indice_modo
            if configs.tratar_clique(evento.pos, esta_na_config_cores):
                if configs.indice_modo != cor_antiga:
                    dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
                continue 

            esta_no_metronomo = (estado.aba_atual == 3 and estado.memoria_sub_abas[3] == 3)
            if meu_metronomo.tratar_clique(evento.pos, aba_config_aberta=esta_no_metronomo): 
                continue

            # --- BOTÕES DE QUANTIDADE DE CASAS ---
            btn_menos_casa = pygame.Rect(estado.OFFSET_X, 30, 40, 35)
            btn_mais_casa = pygame.Rect(estado.OFFSET_X + 160, 30, 40, 35)
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

            # --- ESCALAS E ARRASTAR BLOCOS ---
            if gerenciador_interface.tratar_cliques_escalas(evento.pos, estado.aba_atual, estado.memoria_sub_abas[estado.aba_atual], dicionario_escalas, estado.rect_braco_colisao, estado.scroll_y[estado.aba_atual]):
                continue
            
            # --- MENU LATERAL (TOM, CORES, AFINAÇÃO) ---
            clicou_lateral = False
            if estado.dropdown_tom_aberto:
                for item in estado.rects_notas_dropdown:
                    if item['rect'].collidepoint(evento.pos):
                        estado.tom_atual = item['nota']
                        estado.dropdown_tom_aberto = False
                        clicou_lateral = True
                        break

            if not clicou_lateral and estado.rect_btn_tom.collidepoint(evento.pos):
                estado.dropdown_tom_aberto = not estado.dropdown_tom_aberto
                clicou_lateral = True

            # Cores das notas
            for cat in [estado.rects_cores_tonica, estado.rects_cores_terca, estado.rects_cores_quinta]:
                for item in cat:
                    if item['rect'].collidepoint(evento.pos):
                        if cat == estado.rects_cores_tonica: estado.indice_cor_tonica = item['indice']
                        if cat == estado.rects_cores_terca: estado.indice_cor_terca = item['indice']
                        if cat == estado.rects_cores_quinta: estado.indice_cor_quinta = item['indice']
                        clicou_lateral = True

            # Setas de Afinação
            if estado.btn_up.collidepoint(evento.pos):
                estado.indice_afinacao = (estado.indice_afinacao - 1) % len(lista_afinacoes)
                dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
                clicou_lateral = True
            if estado.btn_down.collidepoint(evento.pos):
                estado.indice_afinacao = (estado.indice_afinacao + 1) % len(lista_afinacoes)
                dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
                clicou_lateral = True

            # --- NAVEGAÇÃO DE ABAS (INFERIOR) ---
            larg_aba = estado.LARGURA_BRACO / len(nomes_abas)
            for i in range(len(nomes_abas)):
                rect_aba = pygame.Rect(estado.OFFSET_X + (i*larg_aba), estado.Y_CAIXA - 40, larg_aba, 40)
                if rect_aba.collidepoint(evento.pos):
                    estado.aba_atual = i
                    continue
            
            largura_sub = (estado.LARGURA_BRACO - 40) / 5
            for j in range(len(nomes_sub_abas[estado.aba_atual])):
                x_sub = estado.OFFSET_X + 20 + (j * largura_sub)
                rect_sub = pygame.Rect(x_sub + 5, estado.Y_CAIXA + 15, largura_sub - 10, 35)
                if rect_sub.collidepoint(evento.pos):
                    estado.memoria_sub_abas[estado.aba_atual] = j