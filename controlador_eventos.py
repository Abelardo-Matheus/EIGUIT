import pygame
import gerenciador_interface
import fabrica_escalas
from constantes_ui import lista_afinacoes, nomes_abas, nomes_sub_abas

def processar(eventos, estado, configs, dicionario_escalas, meu_metronomo, meu_processador, meu_gravador):
    pos_mouse = pygame.mouse.get_pos()
    
    for evento in eventos:
        if evento.type == pygame.QUIT: 
            estado.solicitou_saida = True
            
        if evento.type == pygame.KEYDOWN:
            meu_metronomo.tratar_teclado(evento)
            if evento.key == pygame.K_ESCAPE: 
                estado.solicitou_saida = True
                
        if evento.type == pygame.MOUSEBUTTONDOWN:
            # IA
            if estado.aba_atual == 2 and estado.memoria_sub_abas[2] == 0:
                btn_gravar_ia = pygame.Rect(estado.OFFSET_X + 50, estado.Y_CAIXA + 110, 150, 40)
                
                # 1. Checa se clicou no botão de ligar o MIC ou nos Afinadores redondos
                if meu_processador.tratar_clique(evento.pos, btn_gravar_ia, meu_gravador): 
                    continue
                
                # 2. NOVO: Checa se clicou nos botões de + e - da calibração
                if meu_processador.tratar_clique_calibracao(evento.pos, estado, estado.OFFSET_X, estado.Y_CAIXA):
                    continue
            
            # Configurações e Metrônomo
            esta_na_config_cores = (estado.aba_atual == 3 and estado.memoria_sub_abas[3] == 0)
            cor_antiga = configs.indice_modo
            if configs.tratar_clique(evento.pos, esta_na_config_cores):
                if configs.indice_modo != cor_antiga:
                    dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
                continue 

            
            esta_no_metronomo = (estado.aba_atual == 3 and estado.memoria_sub_abas[3] == 3)
            # Ele sempre escuta o mouse, mas só ativa os botões de config se 'esta_no_metronomo' for True
            if meu_metronomo.tratar_clique(evento.pos, aba_config_aberta=esta_no_metronomo): 
                continue

            # Casas do Braço
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

            # Escalas (Arrastar Blocos)
            if gerenciador_interface.tratar_cliques_escalas(evento.pos, estado.aba_atual, estado.memoria_sub_abas[estado.aba_atual], dicionario_escalas, estado.rect_braco_colisao):
                continue
            
            # --- CLIQUES NO MENU LATERAL ---
            clicou_dropdown = False
            
            # 1. Dropdown do Tom
            if estado.dropdown_tom_aberto:
                for item in estado.rects_notas_dropdown:
                    if item['rect'].collidepoint(evento.pos):
                        estado.tom_atual = item['nota']
                        estado.dropdown_tom_aberto = False
                        clicou_dropdown = True
                        break

            if not clicou_dropdown and estado.rect_btn_tom.collidepoint(evento.pos):
                estado.dropdown_tom_aberto = not estado.dropdown_tom_aberto
                clicou_dropdown = True

            # 2. Cores da Tônica, Terça e Quinta
            for item in estado.rects_cores_tonica:
                if item['rect'].collidepoint(evento.pos):
                    estado.indice_cor_tonica = item['indice']
                    clicou_dropdown = True
            for item in estado.rects_cores_terca:
                if item['rect'].collidepoint(evento.pos):
                    estado.indice_cor_terca = item['indice']
                    clicou_dropdown = True
            for item in estado.rects_cores_quinta:
                if item['rect'].collidepoint(evento.pos):
                    estado.indice_cor_quinta = item['indice']
                    clicou_dropdown = True

            if not clicou_dropdown and estado.dropdown_tom_aberto:
                estado.dropdown_tom_aberto = False

            # 3. Setas da Afinação
            if estado.btn_up.collidepoint(evento.pos):
                estado.indice_afinacao = (estado.indice_afinacao - 1) % len(lista_afinacoes)
                dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))
            if estado.btn_down.collidepoint(evento.pos):
                estado.indice_afinacao = (estado.indice_afinacao + 1) % len(lista_afinacoes)
                dicionario_escalas.update(fabrica_escalas.gerar_modulos(estado, configs))

            # --- CLIQUES NAS ABAS INFERIORES ---
            larg_aba = estado.LARGURA_BRACO / len(nomes_abas)
            for i in range(len(nomes_abas)):
                if pygame.Rect(estado.OFFSET_X + (i*larg_aba), estado.Y_CAIXA - 40, larg_aba, 40).collidepoint(evento.pos):
                    estado.aba_atual = i
                    
            largura_sub = (estado.LARGURA_BRACO - 40) / 5
            for j in range(len(nomes_sub_abas[estado.aba_atual])):
                x_sub = estado.OFFSET_X + 20 + (j * largura_sub)
                if pygame.Rect(x_sub + 5, estado.Y_CAIXA + 15, largura_sub - 10, 35).collidepoint(evento.pos):
                    estado.memoria_sub_abas[estado.aba_atual] = j