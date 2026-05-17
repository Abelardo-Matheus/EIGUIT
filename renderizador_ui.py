# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================
import pygame
import math 
import Modulos.escalas as escalas
import gerenciador_interface
from constantes_ui import *
from Jogos.Jogos_interativos import GerenciadorJogos

def obter_grau(tonica, nota):
    todas_notas = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    graus = ['1', 'b2', '2', 'b3', '3', '4', 'b5', '5', 'b6', '6', 'b7', '7']
    try:
        return graus[(todas_notas.index(nota) - todas_notas.index(tonica)) % 12]
    except ValueError: return ""

def equivalencia_notas(nota1, nota2):
    if nota1 == nota2: return True
    enarmonicas = {"C#": "Db", "Db": "C#", "D#": "Eb", "Eb": "D#", "F#": "Gb", "Gb": "F#", "G#": "Ab", "Ab": "G#", "A#": "Bb", "Bb": "A#"}
    return enarmonicas.get(nota1) == nota2 or enarmonicas.get(nota2) == nota1

def desenhar_painel_superior(tela, estado, fontes):
    # =========================================================================
    # ALINHAMENTO CENTRALIZADO: Ignora o 'dragger' e usa o centro real da tela
    # =========================================================================
    largura_tela = tela.get_width()
    centro_x = largura_tela // 2
    
    # O painel todo tem mais ou menos 640 pixels de largura (dos botões de casas até as setas de afinação)
    largura_bloco_controles = 640
    dx = centro_x - (largura_bloco_controles // 2)
    dy = estado.dragger_controles_topo.y if hasattr(estado, 'dragger_controles_topo') else 30
    
    # Botão de Pin (Modo de Edição) continua encostado na direita
    estado.rect_btn_pin = pygame.Rect(largura_tela - 60, 20, 40, 40)
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

    # --- BLOCO 1: Casas ---
    btn_menos_casa = pygame.Rect(dx, dy, 40, 35)
    btn_mais_casa = pygame.Rect(dx + 160, dy, 40, 35)
    
    pygame.draw.rect(tela, (0, 120, 215), btn_menos_casa, border_radius=5)
    tela.blit(fontes['titulo'].render("-", True, BRANCO), (btn_menos_casa.centerx - 5, btn_menos_casa.centery - 15))
    tela.blit(fontes['titulo'].render(f"Casas: {estado.NUM_CASAS}", True, BRANCO), (dx + 50, dy + 5))
    pygame.draw.rect(tela, (0, 120, 215), btn_mais_casa, border_radius=5)
    tela.blit(fontes['titulo'].render("+", True, BRANCO), (btn_mais_casa.centerx - 7, btn_mais_casa.centery - 15))

    # --- BLOCO 2: Instrumento ---
    instrumento = getattr(estado, 'instrumento', 'guitarra')
    estado.btn_guit = pygame.Rect(dx + 220, dy, 100, 35)
    estado.btn_baixo = pygame.Rect(dx + 330, dy, 100, 35)

    pygame.draw.rect(tela, (0, 120, 215) if instrumento == 'guitarra' else (70, 70, 70), estado.btn_guit, border_radius=5)
    txt_g = fontes['ui'].render("Guitarra", True, BRANCO)
    tela.blit(txt_g, (estado.btn_guit.centerx - txt_g.get_width()//2, estado.btn_guit.centery - txt_g.get_height()//2))

    pygame.draw.rect(tela, (0, 120, 215) if instrumento == 'baixo' else (70, 70, 70), estado.btn_baixo, border_radius=5)
    txt_b = fontes['ui'].render("Baixo", True, BRANCO)
    tela.blit(txt_b, (estado.btn_baixo.centerx - txt_b.get_width()//2, estado.btn_baixo.centery - txt_b.get_height()//2))

    # --- BLOCO 3: Afinação ---
    try: nome_afinacao = lista_afinacoes[estado.indice_afinacao]["nome"]
    except: nome_afinacao = "Standard"

    x_af = dx + 450 
    estado.btn_menos_afinacao = pygame.Rect(x_af, dy, 35, 35)
    estado.btn_mais_afinacao = pygame.Rect(x_af + 150, dy, 35, 35)

    pygame.draw.rect(tela, (0, 120, 215), estado.btn_menos_afinacao, border_radius=5)
    tela.blit(fontes['titulo'].render("<", True, BRANCO), (estado.btn_menos_afinacao.centerx - 7, estado.btn_menos_afinacao.centery - 15))

    pygame.draw.rect(tela, (0, 120, 215), estado.btn_mais_afinacao, border_radius=5)
    tela.blit(fontes['titulo'].render(">", True, BRANCO), (estado.btn_mais_afinacao.centerx - 7, estado.btn_mais_afinacao.centery - 15))

    txt_af = fontes['ui'].render(nome_afinacao, True, BRANCO)
    # Centraliza o nome da afinação entre as duas setas
    meio_setas = x_af + 35 + ((150 - 35) // 2)
    tela.blit(txt_af, (meio_setas - (txt_af.get_width() // 2), dy + 8))

    # Desenha a caixa de seleção do arrastador do topo (se aplicável)
    if estado.drag_ativado and hasattr(estado, 'dragger_controles_topo'):
        # Atualiza as posições do dragger para acompanharem o visual forçado
        estado.dragger_controles_topo.x = dx
        estado.dragger_controles_topo.largura = largura_bloco_controles + 40
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
        
        if casa > 0:
            x_centro_casa = x - (estado.ESPACO_CASAS / 2) 
            txt_casa = fontes['pequena'].render(str(casa), True, (200, 200, 200)) 
            tela.blit(txt_casa, (x_centro_casa - txt_casa.get_width()//2, offset_y_atual + altura_braco_atual + 20))
            
    modo_texto = configs.get_modo_texto() if configs else 'letras'
    cor_base_escala = configs.get_cor_notas() if configs else (255, 255, 255)
    
    tom_global = getattr(meu_campo_harmonico, 'tom', getattr(meu_campo_harmonico, 'tonica', estado.tom_atual))
    estado.tom_atual = tom_global 
    
    nome_escala = getattr(meu_campo_harmonico, 'tipo_escala', getattr(meu_campo_harmonico, 'tipo', '')).lower()
    escala_menor = any(x in nome_escala for x in ['menor', 'eólia', 'dórico', 'frígio', 'lócrio'])

    freq_mic = getattr(estado, 'freq_detectada', 0.0)
    nota_microfone = ""
    try:
        f = float(freq_mic)
        if f >= 20.0:
            valor_exato = 12 * math.log2(f / 440.0)
            semitons = round(valor_exato)
            desvio = valor_exato - semitons
            if abs(desvio) <= 0.30: 
                indice_nota = (semitons + 9) % 12
                notas_str = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                nota_microfone = notas_str[int(indice_nota)]
    except: pass
        
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

            # =========================================================================
            # LÓGICA DE CORES DINÂMICA: FOCA NO ACORDE (SE EXISTIR) OU NO TOM GLOBAL
            # =========================================================================
            if meu_campo_harmonico.indice_acorde_selecionado != -1:
                # SE UM ACORDE ESPECÍFICO ESTIVER CLICADO: Pinta a Tônica, Terça e Quinta dele
                if esta_no_acorde:
                    if nota_calculada == meu_campo_harmonico.notas_acorde_selecionado[0]: 
                        cor_fundo = CORES_TONICA[estado.indice_cor_tonica]
                    elif len(meu_campo_harmonico.notas_acorde_selecionado) > 1 and nota_calculada == meu_campo_harmonico.notas_acorde_selecionado[1]: 
                        cor_fundo = CORES_TONICA[estado.indice_cor_terca]
                    elif len(meu_campo_harmonico.notas_acorde_selecionado) > 2 and nota_calculada == meu_campo_harmonico.notas_acorde_selecionado[2]: 
                        cor_fundo = CORES_TONICA[estado.indice_cor_quinta]
            else:
                # SE NENHUM ACORDE ESTIVER CLICADO: Pinta a escala do Tom Global
                if nota_calculada == tom_global: 
                    cor_fundo = CORES_TONICA[estado.indice_cor_tonica]
                elif nota_calculada == escalas.obter_terca(tom_global, menor=escala_menor): 
                    cor_fundo = CORES_TONICA[estado.indice_cor_terca]
                elif nota_calculada == escalas.obter_quinta(tom_global): 
                    cor_fundo = CORES_TONICA[estado.indice_cor_quinta]
            # =========================================================================

            tocando_agora = False
            if nota_microfone and equivalencia_notas(nota_microfone, nota_calculada):
                cor_fundo = (255, 255, 0) 
                raio_atual = 22
                alpha_nota = 255
                tocando_agora = True

            s = pygame.Surface((raio_atual*2, raio_atual*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*cor_fundo, alpha_nota), (raio_atual, raio_atual), raio_atual)
            
            if tocando_agora:
                pygame.draw.circle(s, (255, 100, 0), (raio_atual, raio_atual), raio_atual, 3) 
            else:
                pygame.draw.circle(s, (0, 0, 0, alpha_nota), (raio_atual, raio_atual), raio_atual, 2) 
            
            tela.blit(s, (int(x_nota - raio_atual), int(y - raio_atual)))

            if modo_texto != 'vazio':
                # O número do grau (1, 3, 5) agora também acompanha o Acorde se ele estiver clicado!
                tom_ref = meu_campo_harmonico.notas_acorde_selecionado[0] if meu_campo_harmonico.indice_acorde_selecionado != -1 else tom_global
                texto_str = nota_calculada if modo_texto == 'letras' else obter_grau(tom_ref, nota_calculada)
                txt_surf = fontes['notas'].render(texto_str, True, (0, 0, 0))
                txt_surf.set_alpha(alpha_nota) 
                tela.blit(txt_surf, (x_nota - (txt_surf.get_width()/2), y - (txt_surf.get_height()/2)))
    
    if estado.drag_ativado and hasattr(estado, 'dragger_guitarra'):
        estado.dragger_guitarra.desenhar_caixa_selecao(tela, margem=20)

def desenhar_painel_cores(tela, estado, fontes):
    if not hasattr(estado, 'dragger_cores'):
        if hasattr(estado, 'dragger_acordes'):
            DraggerClass = type(estado.dragger_acordes)
            
            altura_painel = 150
            margem_fundo = 20
            y_inicial = tela.get_height() - altura_painel - margem_fundo - 100
            
            estado.dragger_cores = DraggerClass(20, y_inicial, 160, altura_painel)
        else:
            return

    x_base = estado.dragger_cores.x
    y_base = estado.dragger_cores.y
    largura = estado.dragger_cores.largura
    altura = estado.dragger_cores.altura

    pygame.draw.rect(tela, (40, 40, 40), (x_base, y_base, largura, altura), border_radius=8)
    pygame.draw.rect(tela, (150, 150, 150), (x_base, y_base, largura, altura), width=2, border_radius=8)

    txt_tit = fontes['ui'].render("Cores (Graus)", True, BRANCO)
    tela.blit(txt_tit, (x_base + largura//2 - txt_tit.get_width()//2, y_base + 10))

    itens = [
        ("Tônica (1)", estado.indice_cor_tonica, 'rect_cor_tonica'),
        ("Terça (3)", estado.indice_cor_terca, 'rect_cor_terca'),
        ("Quinta (5)", estado.indice_cor_quinta, 'rect_cor_quinta')
    ]

    y_item = y_base + 45
    for texto, indice_cor, nome_rect in itens:
        txt = fontes['pequena'].render(texto, True, BRANCO)
        tela.blit(txt, (x_base + 10, y_item + 5))
        
        rect_cor = pygame.Rect(x_base + largura - 40, y_item, 25, 25)
        cor_atual = CORES_TONICA[indice_cor % len(CORES_TONICA)]
        
        pygame.draw.rect(tela, cor_atual, rect_cor, border_radius=5)
        pygame.draw.rect(tela, BRANCO, rect_cor, width=2, border_radius=5)
        
        setattr(estado, nome_rect, rect_cor)
        y_item += 35

    if estado.drag_ativado:
        estado.dragger_cores.desenhar_caixa_selecao(tela, margem=5)

def desenhar_acordes_arrastaveis(tela, estado, meu_campo_harmonico, fontes):
    if not hasattr(estado, 'dragger_acordes'): return

    x_base = estado.dragger_acordes.x
    y_base = estado.dragger_acordes.y
    largura = estado.dragger_acordes.largura

    meu_campo_harmonico.desenhar(tela, x_base, y_base + 10, largura, fontes['titulo'], fontes['ui'], fontes['pequena'])

    if estado.drag_ativado:
        estado.dragger_acordes.desenhar_caixa_selecao(tela, margem=5)

def desenhar_secoes_inferiores_expansiveis(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_gerenciador_jogos):
    alpha_atual = configs.get_alpha() if configs else 255
    AZUL_BOTAO = (0, 120, 215)
    AZUL_CLARO = (0, 160, 255)
    
    dx = estado.dragger_painel_inferior.x if hasattr(estado, 'dragger_painel_inferior') else 100
    dy = estado.dragger_painel_inferior.y if hasattr(estado, 'dragger_painel_inferior') else estado.ALTURA_TELA - 50
    
    altura_caixa_total = 350
    largura_conteudo = estado.LARGURA_BRACO
    largura_botao = (largura_conteudo - 30) / 4 
    espacamento = 10
    
    pos_x_guit = estado.dragger_guitarra.x if hasattr(estado, 'dragger_guitarra') else 100
    pos_y_guit = estado.dragger_guitarra.y if hasattr(estado, 'dragger_guitarra') else 90
    instrumento = getattr(estado, 'instrumento', 'guitarra')
    offset_y_guit = pos_y_guit + estado.ESPACO_CORDAS if instrumento == 'baixo' else pos_y_guit
    altura_guit_atual = estado.ALTURA_BRACO - (2 * estado.ESPACO_CORDAS) if instrumento == 'baixo' else estado.ALTURA_BRACO
    rect_braco_real = pygame.Rect(pos_x_guit, offset_y_guit, estado.LARGURA_BRACO, altura_guit_atual)
    
    tela.set_clip(None) 
    for chave_escala, lista_modulos_gerais in dicionario_escalas.items():
        for modulo in lista_modulos_gerais:
            if modulo.estado != 'painel': 
                modulo.x_braco = pos_x_guit
                modulo.y_braco = offset_y_guit
                modulo.atualizar_e_desenhar(tela, pygame.mouse.get_pos(), rect_braco_real, fontes['pequena'], alpha_atual)
    
    for i, secao in enumerate(estado.secoes_inferiores):
        x_botao = dx + (i * (largura_botao + espacamento))
        rect_cabecalho = pygame.Rect(x_botao, dy, largura_botao, 40)
        secao["rect_cabecalho"] = rect_cabecalho 
        
        cor_fundo = AZUL_CLARO if secao["expandido"] else AZUL_BOTAO
        pygame.draw.rect(tela, cor_fundo, rect_cabecalho, border_radius=8)
        
        txt = fontes['ui'].render(secao["titulo"], True, BRANCO)
        tela.blit(txt, (rect_cabecalho.centerx - txt.get_width()//2, rect_cabecalho.centery - txt.get_height()//2))

        if secao["expandido"]:
            y_conteudo = dy - altura_caixa_total - 10 
            rect_fundo_conteudo = pygame.Rect(dx, y_conteudo, largura_conteudo, altura_caixa_total)
            pygame.draw.rect(tela, COR_PAINEL, rect_fundo_conteudo, border_radius=8)
            pygame.draw.rect(tela, (100, 100, 100), rect_fundo_conteudo, width=2, border_radius=8)

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

            y_area_desenho = y_conteudo + 50
            altura_util = altura_caixa_total - 60 
            
            rect_clipping = pygame.Rect(dx, y_area_desenho, largura_conteudo, altura_util)
            tela.set_clip(rect_clipping)
            scroll_atual = estado.scroll_y.get(i, 0)
            y_start = y_area_desenho - scroll_atual

            if secao["conteudo"] in ["escalas", "acordes"]:
                chaves = []
                if secao["conteudo"] == "escalas":
                    chaves = ['maior', 'menor', 'penta', 'blues', 'modos']
                elif secao["conteudo"] == "acordes":
                    chaves = ['caged', 'triades_maior', 'triades_menor']
                
                if secao["memoria_sub_aba"] < len(chaves):
                    chave_atual = chaves[secao["memoria_sub_aba"]]
                    lista_ativa = dicionario_escalas.get(chave_atual, [])
                    
                    for modulo in lista_ativa:
                        if modulo.estado == 'painel':
                            modulo.x_braco = pos_x_guit
                            modulo.y_braco = offset_y_guit
                            modulo.y_painel = y_start + 20 
                            modulo.scroll_offset = 0 
                            modulo.atualizar_e_desenhar(tela, pygame.mouse.get_pos(), rect_braco_real, fontes['pequena'], alpha_atual)
                    
                    tela.set_clip(rect_clipping)

            elif secao["conteudo"] == "analise_ia":
                if secao["memoria_sub_aba"] == 0:
                    btn_gravar_ia = pygame.Rect(dx + 20, y_start + 40, 150, 40)
                    try: notas_abertas = lista_afinacoes[estado.indice_afinacao]["notas"]
                    except: notas_abertas = ['E', 'A', 'D', 'G', 'B', 'E', 'B']
                    meu_processador.desenhar_aba_ia(tela, dx, y_start, btn_gravar_ia, meu_gravador, fontes['ui'], fontes['titulo'], notas_abertas, estado)
                elif secao["memoria_sub_aba"] == 1:
                     meu_processador.desenhar_aba_treino_ritmo(tela, dx, y_start, fontes['ui'], fontes['titulo'])
                elif secao["memoria_sub_aba"] == 2:
                    meu_gerenciador_jogos.desenhar_aba_jogos(tela, dx, y_start, fontes['ui'])
                
            elif secao["conteudo"] == "configuracao":
                if secao["memoria_sub_aba"] == 0:
                    configs.y = y_start + 10 
                    configs.desenhar(tela, fontes['titulo'], fontes['ui'], 0) 
                else:
                    meu_metronomo.y = y_start + 10
                    meu_metronomo.desenhar_config(tela, fontes['ui'], 0) 

            tela.set_clip(None)

            if estado.max_scroll.get(i, 0) > 0:
                x_scroll = dx + largura_conteudo - 15
                tamanho_alca = max(30, altura_util * (altura_util / (altura_util + estado.max_scroll[i])))
                y_alca = y_area_desenho + (scroll_atual / estado.max_scroll[i]) * (altura_util - tamanho_alca)
                pygame.draw.rect(tela, (60, 60, 60), (x_scroll, y_area_desenho, 10, altura_util), border_radius=5)
                pygame.draw.rect(tela, (150, 150, 150), (x_scroll, y_alca, 10, tamanho_alca), border_radius=5)

    if estado.drag_ativado and hasattr(estado, 'dragger_painel_inferior'):
        estado.dragger_painel_inferior.desenhar_caixa_selecao(tela, margem=5)

def desenhar_tudo(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico, meu_gerenciador_jogos):
    tela.fill(FUNDO_ESCURO)
    desenhar_painel_superior(tela, estado, fontes)
    desenhar_guitarra(tela, estado, configs, fontes, meu_processador, meu_campo_harmonico)
    desenhar_acordes_arrastaveis(tela, estado, meu_campo_harmonico, fontes)
    desenhar_painel_cores(tela, estado, fontes)
    meu_metronomo.desenhar_mini_metronomo(tela, estado, fontes['ui'])
    desenhar_secoes_inferiores_expansiveis(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador,meu_gerenciador_jogos)
    
    if estado.tela_jogo_ativa: 
        meu_gerenciador_jogos.desenhar_tela_jogo(tela, tela.get_width(), tela.get_height(), meu_gravador)

    if hasattr(estado, 'menu_superior'):
        estado.menu_superior.desenhar(tela, fontes['ui'])
    if hasattr(estado, 'gerenciador_perfil'):
        estado.gerenciador_perfil.desenhar(tela, fontes['titulo'], fontes['ui'])

    # =========================================================================
    # LÓGICA DO FOTÓGRAFO: Tira a foto DEPOIS que o menu já sumiu da tela!
    # =========================================================================
    if getattr(estado, 'solicitou_impressao', False):
        import os
        try:
            tela_w, tela_h = tela.get_size()
            
            x_guit = estado.dragger_guitarra.x if hasattr(estado, 'dragger_guitarra') else 100
            y_guit = estado.dragger_guitarra.y if hasattr(estado, 'dragger_guitarra') else 100
            largura = estado.LARGURA_BRACO
            altura = estado.ALTURA_BRACO
            
            x_captura = max(0, x_guit - 80)
            y_captura = max(0, y_guit - 80)
            
            largura_captura = min(tela_w - x_captura, largura + 160)
            altura_captura = min(tela_h - y_captura, altura + 160)
            
            rect_captura = pygame.Rect(x_captura, y_captura, largura_captura, altura_captura)
            imagem_recortada = tela.subsurface(rect_captura)
            
            caminho_imagem = os.path.join(os.getcwd(), "impressao_eiguit.png")
            pygame.image.save(imagem_recortada, caminho_imagem)
            
            if os.name == 'nt':
                os.startfile(caminho_imagem, "print")
                print(f"[IMPRESSÃO] Imagem salva e enviada para o Windows: {caminho_imagem}")
                
        except Exception as e:
            print(f"[ERRO IMPRESSÃO] Não foi possível gerar a impressão: {e}")
            
        # Reseta o pedido para não ficar tirando print infinito
        estado.solicitou_impressao = False