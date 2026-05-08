# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================
import pygame
import Modulos.escalas as escalas
import gerenciador_interface
from constantes_ui import *

def obter_grau(tonica, nota):
    todas_notas = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    graus = ['1', 'b2', '2', 'b3', '3', '4', 'b5', '5', 'b6', '6', 'b7', '7']
    try:
        return graus[(todas_notas.index(nota) - todas_notas.index(tonica)) % 12]
    except ValueError: return ""

def desenhar_painel_superior(tela, estado, fontes):
    dx = estado.dragger_controles_topo.x if hasattr(estado, 'dragger_controles_topo') else 100
    dy = estado.dragger_controles_topo.y if hasattr(estado, 'dragger_controles_topo') else 30
    
    # BOTÃO ALFINETE (Lado Superior Direito)
    estado.rect_btn_pin = pygame.Rect(tela.get_width() - 60, 20, 40, 40)
    cor_pin_bg = (0, 160, 255) if estado.drag_ativado else (80, 80, 80)
    pygame.draw.rect(tela, cor_pin_bg, estado.rect_btn_pin, border_radius=8)
    pygame.draw.rect(tela, BRANCO, estado.rect_btn_pin, width=2, border_radius=8)
    
    cx, cy = estado.rect_btn_pin.center
    if estado.drag_ativado:
        pygame.draw.circle(tela, BRANCO, (cx, cy), 4)
        pygame.draw.line(tela, BRANCO, (cx-10, cy), (cx+10, cy), 2)
        pygame.draw.line(tela, BRANCO, (cx, cy-10), (cx, cy+10), 2)
    else:
        pygame.draw.circle(tela, (255, 100, 100), (cx, cy - 4), 6) 
        pygame.draw.line(tela, BRANCO, (cx - 6, cy + 2), (cx + 6, cy + 2), 2) 
        pygame.draw.line(tela, BRANCO, (cx, cy + 2), (cx, cy + 12), 2) 

    # BOTÕES TOP
    btn_menos_casa = pygame.Rect(dx, dy, 40, 35)
    btn_mais_casa = pygame.Rect(dx + 160, dy, 40, 35)
    
    pygame.draw.rect(tela, (0, 120, 215), btn_menos_casa, border_radius=5)
    tela.blit(fontes['titulo'].render("-", True, BRANCO), (btn_menos_casa.centerx - 5, btn_menos_casa.centery - 15))
    tela.blit(fontes['titulo'].render(f"Casas: {estado.NUM_CASAS}", True, BRANCO), (dx + 50, dy + 5))
    pygame.draw.rect(tela, (0, 120, 215), btn_mais_casa, border_radius=5)
    tela.blit(fontes['titulo'].render("+", True, BRANCO), (btn_mais_casa.centerx - 7, btn_mais_casa.centery - 15))

    instrumento = getattr(estado, 'instrumento', 'guitarra')
    estado.btn_guit = pygame.Rect(dx + 250, dy, 110, 35)
    estado.btn_baixo = pygame.Rect(dx + 370, dy, 110, 35)

    pygame.draw.rect(tela, (0, 120, 215) if instrumento == 'guitarra' else (70, 70, 70), estado.btn_guit, border_radius=5)
    txt_g = fontes['ui'].render("Guitarra", True, BRANCO)
    tela.blit(txt_g, (estado.btn_guit.centerx - txt_g.get_width()//2, estado.btn_guit.centery - txt_g.get_height()//2))

    pygame.draw.rect(tela, (0, 120, 215) if instrumento == 'baixo' else (70, 70, 70), estado.btn_baixo, border_radius=5)
    txt_b = fontes['ui'].render("Baixo", True, BRANCO)
    tela.blit(txt_b, (estado.btn_baixo.centerx - txt_b.get_width()//2, estado.btn_baixo.centery - txt_b.get_height()//2))

    if estado.drag_ativado and hasattr(estado, 'dragger_controles_topo'):
        estado.dragger_controles_topo.desenhar_caixa_selecao(tela, margem=5)

def desenhar_guitarra(tela, estado, configs, fontes, meu_processador, meu_campo_harmonico):
    try: notas_abertas = lista_afinacoes[estado.indice_afinacao]["notas"]
    except: notas_abertas = ['E', 'A', 'D', 'G', 'B', 'E', 'B']

    cor_madeira = configs.get_cor_braco() if configs else (80, 40, 15)
    instrumento = getattr(estado, 'instrumento', 'guitarra')
    num_cordas_desenho = 4 if instrumento == 'baixo' else estado.NUM_CORDAS
    
    pos_x_base = estado.dragger_guitarra.x if hasattr(estado, 'dragger_guitarra') else 100
    pos_y_base = estado.dragger_guitarra.y if hasattr(estado, 'dragger_guitarra') else 90

    altura_braco_atual = estado.ALTURA_BRACO - (2 * estado.ESPACO_CORDAS) if instrumento == 'baixo' else estado.ALTURA_BRACO
    offset_y_atual = pos_y_base + estado.ESPACO_CORDAS if instrumento == 'baixo' else pos_y_base

    pygame.draw.rect(tela, cor_madeira, (pos_x_base, offset_y_atual, estado.LARGURA_BRACO, altura_braco_atual))

    for casa in range(estado.NUM_CASAS + 1):
        x = pos_x_base + (casa * estado.ESPACO_CASAS)
        pygame.draw.line(tela, (150, 150, 150), (x, offset_y_atual), (x, offset_y_atual + altura_braco_atual), 2)
    
    modo_texto = configs.get_modo_texto() if configs else 'letras'
    cor_base_escala = configs.get_cor_notas() if configs else (255, 255, 255)
    
    for i in range(num_cordas_desenho):
        y = (offset_y_atual + altura_braco_atual - (i * estado.ESPACO_CORDAS)) if instrumento != 'baixo' else (offset_y_atual + altura_braco_atual - 15 - (i * estado.ESPACO_CORDAS))
        pygame.draw.line(tela, (200, 200, 200), (pos_x_base, y), (pos_x_base + estado.LARGURA_BRACO, y), 1)
        nota_aberta_atual = notas_abertas[i if instrumento != 'baixo' else i + 2]

        for casa in range(estado.NUM_CASAS + 1):
            nota_calculada = escalas.obter_nota(nota_aberta_atual, casa)
            
            esta_no_acorde = True
            alpha_nota, raio_atual = 255, 18

            if meu_campo_harmonico.indice_acorde_selecionado != -1:
                if nota_calculada not in meu_campo_harmonico.notas_acorde_selecionado:
                    esta_no_acorde = False
                    alpha_nota, raio_atual = 90, 14  

            x_nota = pos_x_base - 40 if casa == 0 else pos_x_base + (casa * estado.ESPACO_CASAS) - (estado.ESPACO_CASAS / 2)
            cor_fundo = cor_base_escala 

            if meu_campo_harmonico.indice_acorde_selecionado != -1 and esta_no_acorde:
                if nota_calculada == meu_campo_harmonico.notas_acorde_selecionado[0]: cor_fundo = CORES_TONICA[estado.indice_cor_tonica]
                elif nota_calculada == meu_campo_harmonico.notas_acorde_selecionado[1]: cor_fundo = CORES_TONICA[estado.indice_cor_terca]
                elif nota_calculada == meu_campo_harmonico.notas_acorde_selecionado[2]: cor_fundo = CORES_TONICA[estado.indice_cor_quinta]
            else:
                if nota_calculada == estado.tom_atual: cor_fundo = CORES_TONICA[estado.indice_cor_tonica]
                elif nota_calculada == escalas.obter_terca(estado.tom_atual): cor_fundo = CORES_TONICA[estado.indice_cor_terca]
                elif nota_calculada == escalas.obter_quinta(estado.tom_atual): cor_fundo = CORES_TONICA[estado.indice_cor_quinta]

            s = pygame.Surface((raio_atual*2, raio_atual*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*cor_fundo, alpha_nota), (raio_atual, raio_atual), raio_atual)
            pygame.draw.circle(s, (0, 0, 0, alpha_nota), (raio_atual, raio_atual), raio_atual, 2) 
            tela.blit(s, (int(x_nota - raio_atual), int(y - raio_atual)))

            if modo_texto != 'vazio':
                tom_ref = meu_campo_harmonico.notas_acorde_selecionado[0] if meu_campo_harmonico.indice_acorde_selecionado != -1 else estado.tom_atual
                texto_str = nota_calculada if modo_texto == 'letras' else obter_grau(tom_ref, nota_calculada)
                txt_surf = fontes['notas'].render(texto_str, True, (0, 0, 0))
                txt_surf.set_alpha(alpha_nota) 
                tela.blit(txt_surf, (x_nota - (txt_surf.get_width()/2), y - (txt_surf.get_height()/2)))
    
    if estado.drag_ativado and hasattr(estado, 'dragger_guitarra'):
        estado.dragger_guitarra.desenhar_caixa_selecao(tela, margem=20)


def desenhar_acordes_arrastaveis(tela, estado, meu_campo_harmonico, fontes):
    if not hasattr(estado, 'dragger_acordes'): return

    x_base = estado.dragger_acordes.x
    y_base = estado.dragger_acordes.y
    largura = estado.dragger_acordes.largura

    # Renderiza apenas os acordes sem fundo amarelo. Passamos x_base e largura para centralizar!
    meu_campo_harmonico.desenhar(tela, x_base, y_base + 10, largura, fontes['titulo'], fontes['ui'], fontes['pequena'])

    # SÓ DESENHA A BORDA SE O MODO DRAG ESTIVER ATIVADO
    if estado.drag_ativado:
        estado.dragger_acordes.desenhar_caixa_selecao(tela, margem=5)


def desenhar_secoes_inferiores_expansiveis(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador):
    alpha_atual = configs.get_alpha() if configs else 255
    AZUL_BOTAO = (0, 120, 215)
    AZUL_CLARO = (0, 160, 255)
    
    dx = estado.dragger_painel_inferior.x if hasattr(estado, 'dragger_painel_inferior') else 100
    dy = estado.dragger_painel_inferior.y if hasattr(estado, 'dragger_painel_inferior') else estado.ALTURA_TELA - 50
    
    # Padronizamos a área de desenho para todos
    altura_caixa_total = 350
    largura_conteudo = estado.LARGURA_BRACO
    largura_botao = (largura_conteudo - 30) / 4 
    espacamento = 10
    
    for i, secao in enumerate(estado.secoes_inferiores):
        x_botao = dx + (i * (largura_botao + espacamento))
        rect_cabecalho = pygame.Rect(x_botao, dy, largura_botao, 40)
        secao["rect_cabecalho"] = rect_cabecalho 
        
        cor_fundo = AZUL_CLARO if secao["expandido"] else AZUL_BOTAO
        pygame.draw.rect(tela, cor_fundo, rect_cabecalho, border_radius=8)
        
        txt = fontes['ui'].render(secao["titulo"], True, BRANCO)
        tela.blit(txt, (rect_cabecalho.centerx - txt.get_width()//2, rect_cabecalho.centery - txt.get_height()//2))

        if secao["expandido"]:
            # A caixa abre para CIMA do botão
            y_conteudo = dy - altura_caixa_total - 10 
            
            rect_fundo_conteudo = pygame.Rect(dx, y_conteudo, largura_conteudo, altura_caixa_total)
            pygame.draw.rect(tela, COR_PAINEL, rect_fundo_conteudo, border_radius=8)
            pygame.draw.rect(tela, (100, 100, 100), rect_fundo_conteudo, width=2, border_radius=8)

            # --- SUB-ABAS (ALTURA FIXA: 30px + 10px margem = 40px) ---
            y_sub_abas = y_conteudo + 10
            altura_sub = 30
            if secao["sub_abas"]:
                largura_sub = (largura_conteudo - 40) / len(secao["sub_abas"])
                for j, nome_sub in enumerate(secao["sub_abas"]):
                    rect_sub = pygame.Rect(dx + 20 + (j * largura_sub), y_sub_abas, largura_sub - 5, altura_sub)
                    secao[f"rect_sub_{j}"] = rect_sub 
                    cor_sub = AZUL_CLARO if secao["memoria_sub_aba"] == j else (60, 60, 60)
                    pygame.draw.rect(tela, cor_sub, rect_sub, border_radius=5)
                    txt_sub = fontes['pequena'].render(nome_sub, True, BRANCO)
                    tela.blit(txt_sub, (rect_sub.centerx - txt_sub.get_width()//2, rect_sub.centery - txt_sub.get_height()//2))

            # --- ÁREA ÚTIL DE CONTEÚDO (Onde o desenho começa de fato) ---
            # Definimos que o conteúdo começa EXATAMENTE 50 pixels abaixo do topo da caixa (10 margem + 30 subaba + 10 margem)
            y_area_desenho = y_conteudo + 50
            altura_util = altura_caixa_total - 60 # Descontando as abas e margem inferior
            
            rect_clipping = pygame.Rect(dx, y_area_desenho, largura_conteudo, altura_util)
            tela.set_clip(rect_clipping)
            scroll_atual = estado.scroll_y.get(i, 0)
            
            # Ponto de referência Y para todos os desenhos (Unificado!)
            y_start = y_area_desenho - scroll_atual

            if secao["conteudo"] in ["escalas", "acordes"]:
                gerenciador_interface.desenhar_escalas_ativas(
                    tela, pygame.mouse.get_pos(), i, secao["memoria_sub_aba"], 
                    dicionario_escalas, rect_clipping, alpha_atual, fontes['pequena'], scroll_atual
                )

            elif secao["conteudo"] == "analise_ia":
                if secao["memoria_sub_aba"] == 0:
                    btn_gravar_ia = pygame.Rect(dx + 20, y_start + 40, 150, 40)
                    try: notas_abertas = lista_afinacoes[estado.indice_afinacao]["notas"]
                    except: notas_abertas = ['E', 'A', 'D', 'G', 'B', 'E', 'B']
                    
                    meu_processador.desenhar_aba_ia(tela, dx, y_start, btn_gravar_ia, meu_gravador, fontes['ui'], fontes['titulo'], notas_abertas, estado)
                else:
                    meu_processador.desenhar_aba_treino_ritmo(tela, dx, y_start, fontes['ui'], fontes['titulo'])

            elif secao["conteudo"] == "configuracao":
                if secao["memoria_sub_aba"] == 0:
                    configs.y = y_start + 10 # Pequeno ajuste para não colar no topo
                    configs.desenhar(tela, fontes['titulo'], fontes['ui'], 0) # Scroll já tratado no y_start
                else:
                    meu_metronomo.y = y_start + 10
                    meu_metronomo.desenhar_config(tela, fontes['ui'], 0) # Scroll já tratado no y_start

            tela.set_clip(None)

            # Scrollbar
            if estado.max_scroll.get(i, 0) > 0:
                x_scroll = dx + largura_conteudo - 15
                tamanho_alca = max(30, altura_util * (altura_util / (altura_util + estado.max_scroll[i])))
                y_alca = y_area_desenho + (scroll_atual / estado.max_scroll[i]) * (altura_util - tamanho_alca)
                pygame.draw.rect(tela, (60, 60, 60), (x_scroll, y_area_desenho, 10, altura_util), border_radius=5)
                pygame.draw.rect(tela, (150, 150, 150), (x_scroll, y_alca, 10, tamanho_alca), border_radius=5)

    if estado.drag_ativado and hasattr(estado, 'dragger_painel_inferior'):
        estado.dragger_painel_inferior.desenhar_caixa_selecao(tela, margem=5)

def desenhar_tudo(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico):
    tela.fill(FUNDO_ESCURO)
    
    desenhar_painel_superior(tela, estado, fontes)
    desenhar_guitarra(tela, estado, configs, fontes, meu_processador, meu_campo_harmonico)
    desenhar_acordes_arrastaveis(tela, estado, meu_campo_harmonico, fontes)
    meu_metronomo.desenhar_mini_metronomo(tela, estado, fontes['ui'])
    desenhar_secoes_inferiores_expansiveis(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador)
    
    