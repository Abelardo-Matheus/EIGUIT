# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 [SEU NOME]
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================
import pygame
import Modulos.escalas as escalas
import gerenciador_interface
from constantes_ui import *

def obter_grau(tonica, nota):
    """Calcula o intervalo musical entre a tônica e a nota atual."""
    todas_notas = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    graus = ['1', 'b2', '2', 'b3', '3', '4', 'b5', '5', 'b6', '6', 'b7', '7']
    
    try:
        idx_tonica = todas_notas.index(tonica)
        idx_nota = todas_notas.index(nota)
        distancia = (idx_nota - idx_tonica) % 12
        return graus[distancia]
    except ValueError:
        return ""


    # Agora usa sua própria variável independente!
    y_base = estado.Y_CAMPO_HARMONICO
    x_centro = tela.get_width() // 2
    
    # Cores
    COR_FUNDO = (40, 40, 40)
    COR_BORDA = (100, 100, 100)
    COR_TEXTO = (255, 255, 255)
    AZUL_BOTAO = (0, 120, 215)
    
    # Pega os dados da escala atual
    escala_atual = estado.escalas_campo[estado.indice_escala_campo]
    idx_tonica = estado.notas_base.index(estado.tonica_campo)
    
    # --- DESENHAR OS 7 BLOCOS ---
    largura_bloco = 70
    altura_bloco = 60
    espacamento = 15
    largura_total = (7 * largura_bloco) + (6 * espacamento)
    x_inicial = x_centro - (largura_total // 2)
    
    for i in range(7):
        x_bloco = x_inicial + i * (largura_bloco + espacamento)
        
        # Calcula a nota correta somando o intervalo da escala
        idx_nota = (idx_tonica + escala_atual["int"][i]) % 12
        nota_acorde = estado.notas_base[idx_nota]
        nome_acorde = nota_acorde + escala_atual["qualidades"][i]
        
        # 1. Desenha o Algarismo Romano em cima
        romano = escala_atual["romanos"][i]
        txt_romano = fonte_pequena.render(romano, True, COR_BORDA)
        tela.blit(txt_romano, (x_bloco + (largura_bloco//2) - (txt_romano.get_width()//2), y_base - 25))
        
        # 2. Desenha o Bloco
        rect_bloco = pygame.Rect(x_bloco, y_base, largura_bloco, altura_bloco)
        pygame.draw.rect(tela, COR_FUNDO, rect_bloco, border_radius=8)
        pygame.draw.rect(tela, COR_BORDA, rect_bloco, width=2, border_radius=8)
        
        # 3. Desenha o Acorde dentro do bloco
        txt_acorde = fonte_titulo.render(nome_acorde, True, COR_TEXTO)
        tela.blit(txt_acorde, (x_bloco + (largura_bloco//2) - (txt_acorde.get_width()//2), y_base + 15))

    # --- DESENHAR OS CONTROLES (Setinhas em baixo) ---
    y_controles = y_base + altura_bloco + 20
    
    # Controle da Tônica (Ex: < C >)
    estado.rect_tonica_esq = pygame.Rect(x_centro - 200, y_controles, 30, 30)
    estado.rect_tonica_dir = pygame.Rect(x_centro - 100, y_controles, 30, 30)
    pygame.draw.rect(tela, AZUL_BOTAO, estado.rect_tonica_esq, border_radius=5)
    pygame.draw.rect(tela, AZUL_BOTAO, estado.rect_tonica_dir, border_radius=5)
    tela.blit(fonte_titulo.render("<", True, COR_TEXTO), (estado.rect_tonica_esq.x + 8, estado.rect_tonica_esq.y + 2))
    tela.blit(fonte_titulo.render(">", True, COR_TEXTO), (estado.rect_tonica_dir.x + 8, estado.rect_tonica_dir.y + 2))
    
    txt_tonica = fonte_titulo.render(estado.tonica_campo, True, COR_TEXTO)
    tela.blit(txt_tonica, (x_centro - 150 - (txt_tonica.get_width()//2), y_controles + 5))

    # Controle da Escala (Ex: < Maior (Jônio) >)
    estado.rect_escala_esq = pygame.Rect(x_centro + 10, y_controles, 30, 30)
    estado.rect_escala_dir = pygame.Rect(x_centro + 240, y_controles, 30, 30)
    pygame.draw.rect(tela, AZUL_BOTAO, estado.rect_escala_esq, border_radius=5)
    pygame.draw.rect(tela, AZUL_BOTAO, estado.rect_escala_dir, border_radius=5)
    tela.blit(fonte_titulo.render("<", True, COR_TEXTO), (estado.rect_escala_esq.x + 8, estado.rect_escala_esq.y + 2))
    tela.blit(fonte_titulo.render(">", True, COR_TEXTO), (estado.rect_escala_dir.x + 8, estado.rect_escala_dir.y + 2))
    
    txt_escala = fonte_ui.render(escala_atual["nome"], True, COR_TEXTO)
    tela.blit(txt_escala, (x_centro + 140 - (txt_escala.get_width()//2), y_controles + 5))

def desenhar_painel_superior(tela, estado, fontes):
    btn_menos_casa = pygame.Rect(estado.OFFSET_X, 30, 40, 35)
    btn_mais_casa = pygame.Rect(estado.OFFSET_X + 160, 30, 40, 35)
    
    pygame.draw.rect(tela, AZUL_BOTAO, btn_menos_casa, border_radius=5)
    tela.blit(fontes['titulo'].render("-", True, BRANCO), (btn_menos_casa.centerx - 5, btn_menos_casa.centery - 15))
    
    txt_casas = fontes['titulo'].render(f"Casas: {estado.NUM_CASAS}", True, BRANCO)
    tela.blit(txt_casas, (estado.OFFSET_X + 50, 35))
    
    pygame.draw.rect(tela, AZUL_BOTAO, btn_mais_casa, border_radius=5)
    tela.blit(fontes['titulo'].render("+", True, BRANCO), (btn_mais_casa.centerx - 7, btn_mais_casa.centery - 15))

    instrumento = getattr(estado, 'instrumento', 'guitarra')

    estado.btn_guit = pygame.Rect(estado.OFFSET_X + 250, 30, 110, 35)
    estado.btn_baixo = pygame.Rect(estado.OFFSET_X + 370, 30, 110, 35)

    cor_guit = AZUL_BOTAO if instrumento == 'guitarra' else (70, 70, 70)
    cor_baixo = AZUL_BOTAO if instrumento == 'baixo' else (70, 70, 70)

    pygame.draw.rect(tela, cor_guit, estado.btn_guit, border_radius=5)
    txt_g = fontes['ui'].render("Guitarra", True, BRANCO)
    tela.blit(txt_g, (estado.btn_guit.centerx - txt_g.get_width()//2, estado.btn_guit.centery - txt_g.get_height()//2))

    pygame.draw.rect(tela, cor_baixo, estado.btn_baixo, border_radius=5)
    txt_b = fontes['ui'].render("Baixo", True, BRANCO)
    tela.blit(txt_b, (estado.btn_baixo.centerx - txt_b.get_width()//2, estado.btn_baixo.centery - txt_b.get_height()//2))


def desenhar_guitarra(tela, estado, configs, fontes, meu_processador, meu_campo_harmonico):
    notas_abertas = lista_afinacoes[estado.indice_afinacao]["notas"]
    cor_madeira = configs.get_cor_braco() if configs else (80, 40, 15)
    
    instrumento = getattr(estado, 'instrumento', 'guitarra')
    num_cordas_desenho = 4 if instrumento == 'baixo' else estado.NUM_CORDAS
    
    if instrumento == 'baixo':
        altura_braco_atual = estado.ALTURA_BRACO - (2 * estado.ESPACO_CORDAS)
        offset_y_atual = estado.OFFSET_Y + estado.ESPACO_CORDAS
    else:
        altura_braco_atual = estado.ALTURA_BRACO
        offset_y_atual = estado.OFFSET_Y

    # 1. Madeira e Trastes
    pygame.draw.rect(tela, cor_madeira, (estado.OFFSET_X, offset_y_atual, estado.LARGURA_BRACO, altura_braco_atual))

    for casa in range(estado.NUM_CASAS + 1):
        x = estado.OFFSET_X + (casa * estado.ESPACO_CASAS)
        pygame.draw.line(tela, (150, 150, 150), (x, offset_y_atual), (x, offset_y_atual + altura_braco_atual), 2)
    
    modo_texto = configs.get_modo_texto() if configs else 'letras'
    cor_base_escala = configs.get_cor_notas() if configs else (255, 255, 255)
    
    # 3. Cordas
    for i in range(num_cordas_desenho):
        y = (offset_y_atual + altura_braco_atual - (i * estado.ESPACO_CORDAS)) if instrumento != 'baixo' else (offset_y_atual + altura_braco_atual - 15 - (i * estado.ESPACO_CORDAS))
        pygame.draw.line(tela, (200, 200, 200), (estado.OFFSET_X, y), (estado.OFFSET_X + estado.LARGURA_BRACO, y), 1)
        
        nota_aberta_atual = notas_abertas[i if instrumento != 'baixo' else i + 2]

        # 4. Loop de Notas
        for casa in range(estado.NUM_CASAS + 1):
            nota_calculada = escalas.obter_nota(nota_aberta_atual, casa)
            
            # --- NOVA LÓGICA DE TRANSPARÊNCIA ---
            esta_no_acorde = True
            alpha_nota = 255 # Opaco (normal)
            raio_atual = 18

            # Se houver um acorde selecionado, checamos se a nota atual faz parte dele
            if meu_campo_harmonico.indice_acorde_selecionado != -1:
                if nota_calculada not in meu_campo_harmonico.notas_acorde_selecionado:
                    esta_no_acorde = False
                    alpha_nota = 90  # Fica bem transparente
                    raio_atual = 14  # Diminui um pouco o tamanho para dar profundidade

            x_nota = estado.OFFSET_X - 40 if casa == 0 else estado.OFFSET_X + (casa * estado.ESPACO_CASAS) - (estado.ESPACO_CASAS / 2)

            # Define a cor base
            cor_fundo = cor_base_escala 
            if meu_campo_harmonico.indice_acorde_selecionado != -1 and esta_no_acorde:
                if nota_calculada == meu_campo_harmonico.notas_acorde_selecionado[0]: cor_fundo = CORES_TONICA[estado.indice_cor_tonica]
                elif nota_calculada == meu_campo_harmonico.notas_acorde_selecionado[1]: cor_fundo = CORES_TONICA[estado.indice_cor_terca]
                elif nota_calculada == meu_campo_harmonico.notas_acorde_selecionado[2]: cor_fundo = CORES_TONICA[estado.indice_cor_quinta]
            else:
                if nota_calculada == estado.tom_atual: cor_fundo = CORES_TONICA[estado.indice_cor_tonica]
                elif nota_calculada == escalas.obter_terca(estado.tom_atual): cor_fundo = CORES_TONICA[estado.indice_cor_terca]
                elif nota_calculada == escalas.obter_quinta(estado.tom_atual): cor_fundo = CORES_TONICA[estado.indice_cor_quinta]

            # --- RENDERIZAÇÃO COM SUPORTE A ALPHA ---
            # No Pygame, para desenhar círculos transparentes, usamos uma Surface temporária
            s = pygame.Surface((raio_atual*2, raio_atual*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*cor_fundo, alpha_nota), (raio_atual, raio_atual), raio_atual)
            pygame.draw.circle(s, (0, 0, 0, alpha_nota), (raio_atual, raio_atual), raio_atual, 2) # Borda
            tela.blit(s, (int(x_nota - raio_atual), int(y - raio_atual)))

            # Texto da nota (também com transparência)
            if modo_texto != 'vazio':
                tom_ref = meu_campo_harmonico.notas_acorde_selecionado[0] if meu_campo_harmonico.indice_acorde_selecionado != -1 else estado.tom_atual
                texto_str = nota_calculada if modo_texto == 'letras' else obter_grau(tom_ref, nota_calculada)
                
                txt_surf = fontes['notas'].render(texto_str, True, (0, 0, 0))
                txt_surf.set_alpha(alpha_nota) # Aplica a mesma transparência no texto
                tela.blit(txt_surf, (x_nota - (txt_surf.get_width()/2), y - (txt_surf.get_height()/2)))

def desenhar_painel_lateral(tela, estado, fontes):
    info = lista_afinacoes[estado.indice_afinacao]["nome"]
    tela.blit(fontes['ui'].render(f"Afinação: {info}", True, BRANCO), (estado.X_PAINEL, estado.Y_PAINEL - 40))
    
    pygame.draw.rect(tela, AZUL_BOTAO, estado.btn_up, border_radius=5)
    tela.blit(fontes['ui'].render("^", True, BRANCO), (estado.btn_up.centerx - 5, estado.btn_up.centery - 10))
    pygame.draw.rect(tela, AZUL_BOTAO, estado.btn_down, border_radius=5)
    tela.blit(fontes['ui'].render("v", True, BRANCO), (estado.btn_down.centerx - 5, estado.btn_down.centery - 10))

    y_base_cores = estado.Y_PAINEL + 120
    categorias = [
        {"nome": "Tônica", "indice": estado.indice_cor_tonica, "lista": estado.rects_cores_tonica},
        {"nome": "Terça",  "indice": estado.indice_cor_terca,  "lista": estado.rects_cores_terca},
        {"nome": "Quinta", "indice": estado.indice_cor_quinta, "lista": estado.rects_cores_quinta}
    ]

    for j, cat in enumerate(categorias):
        y_linha = y_base_cores + (j * 40)
        tela.blit(fontes['ui'].render(cat["nome"] + ":", True, BRANCO), (estado.X_PAINEL, y_linha))
        cat["lista"].clear()
        for i, cor in enumerate(CORES_TONICA):
            bx, by, raio = estado.X_PAINEL + 75 + (i * 24), y_linha + 10, 10
            pygame.draw.circle(tela, cor, (bx, by), raio)
            if i == cat["indice"]: pygame.draw.circle(tela, BRANCO, (bx, by), raio + 3, 2)
            else: pygame.draw.circle(tela, PRETO, (bx, by), raio, 1)
            cat["lista"].append({'rect': pygame.Rect(bx-raio, by-raio, raio*2, raio*2), 'indice': i})

    y_tom_base = y_base_cores + 130
    tela.blit(fontes['ui'].render("Tom:", True, BRANCO), (estado.X_PAINEL, y_tom_base))

    cx, cy = estado.X_PAINEL + 75, y_tom_base + 10
    pygame.draw.circle(tela, BRANCO, (cx, cy), 18)
    pygame.draw.circle(tela, PRETO, (cx, cy), 18, 2)
    txt_tom = fontes['notas'].render(estado.tom_atual, True, PRETO)
    tela.blit(txt_tom, (cx - txt_tom.get_width()//2, cy - txt_tom.get_height()//2))

    estado.rect_btn_tom = pygame.Rect(cx - 18, cy - 18, 36, 36)

    estado.rects_notas_dropdown.clear()
    if estado.dropdown_tom_aberto:
        pygame.draw.rect(tela, (50, 50, 50), (cx - 20, cy + 25, 140, 180), border_radius=8)
        for i, nota in enumerate(escalas.NOTAS):
            nx, ny = cx + ((i % 3) * 45), cy + 45 + ((i // 3) * 40)
            pygame.draw.circle(tela, BRANCO, (nx, ny), 18)
            pygame.draw.circle(tela, PRETO, (nx, ny), 18, 2)
            tn = fontes['notas'].render(nota, True, PRETO)
            tela.blit(tn, (nx - tn.get_width()//2, ny - tn.get_height()//2))
            estado.rects_notas_dropdown.append({'rect': pygame.Rect(nx-18, ny-18, 36, 36), 'nota': nota})

def desenhar_painel_inferior(tela, estado, fontes):
    caixa_principal = pygame.Rect(estado.OFFSET_X, estado.Y_CAIXA, estado.LARGURA_BRACO, estado.ALTURA_CAIXA)
    pygame.draw.rect(tela, COR_PAINEL, caixa_principal, border_radius=10)

    largura_aba = estado.LARGURA_BRACO / len(nomes_abas)
    for i, nome in enumerate(nomes_abas):
        x_aba, y_aba = estado.OFFSET_X + (i * largura_aba), estado.Y_CAIXA - 40
        rect_aba = pygame.Rect(x_aba, y_aba, largura_aba, 40)
        cor_fundo = COR_ABA_ATIVA if i == estado.aba_atual else COR_ABA_INATIVA
        cor_texto = BRANCO if i == estado.aba_atual else COR_TEXTO_INATIVO
        
        pygame.draw.rect(tela, cor_fundo, rect_aba, border_top_left_radius=10, border_top_right_radius=10)
        txt = fontes['ui'].render(nome, True, cor_texto)
        tela.blit(txt, (rect_aba.centerx - (txt.get_width()/2), y_aba + 10))

    margem_interna = 20
    largura_sub = (estado.LARGURA_BRACO - (margem_interna * 2)) / 5 
    sub_selecionada = estado.memoria_sub_abas[estado.aba_atual]

    for j, nome_sub in enumerate(nomes_sub_abas[estado.aba_atual]):
        x_sub = estado.OFFSET_X + margem_interna + (j * largura_sub)
        rect_sub = pygame.Rect(x_sub + 5, estado.Y_CAIXA + 15, largura_sub - 10, 35)
        
        cor_fundo_sub = COR_SUB_ATIVA if j == sub_selecionada else COR_SUB_INATIVA
        cor_texto_sub = BRANCO if j == sub_selecionada else COR_TEXTO_INATIVO
        
        pygame.draw.rect(tela, cor_fundo_sub, rect_sub, border_radius=6)
        txt_sub = fontes['pequena'].render(nome_sub, True, cor_texto_sub)
        tela.blit(txt_sub, (rect_sub.centerx - (txt_sub.get_width()/2), rect_sub.centery - (txt_sub.get_height()/2)))


def desenhar_tudo(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico):
    tela.fill(FUNDO_ESCURO)
    
    desenhar_guitarra(tela, estado, configs, fontes, meu_processador, meu_campo_harmonico)
    desenhar_painel_superior(tela, estado, fontes)
    desenhar_painel_lateral(tela, estado, fontes)
    desenhar_painel_inferior(tela, estado, fontes) 
    
    alpha_atual = configs.get_alpha() if configs else 255
    
    # ========================================================
    # --- DESENHAR O CAMPO HARMÔNICO ---
    # ========================================================
    meu_campo_harmonico.desenhar(tela, estado.Y_CAMPO_HARMONICO, fontes['titulo'], fontes['ui'], fontes['pequena'])

    # ========================================================
    # 1. LIGAR A MÁSCARA (CLIPPING) PARA TODA A CAIXA
    # ========================================================
    y_corte = estado.Y_CAIXA + 60
    altura_corte = estado.ALTURA_CAIXA - 60
    rect_corte = pygame.Rect(estado.OFFSET_X, y_corte, estado.LARGURA_BRACO, altura_corte)
    
    tela.set_clip(rect_corte)
    
    # Pega o scroll exato da aba que estamos olhando agora
    scroll_atual = estado.scroll_y[estado.aba_atual]
    
    # --- ABA 0: ESCALAS ---
    if estado.aba_atual == 0:
        gerenciador_interface.desenhar_escalas_ativas(
            tela, pygame.mouse.get_pos(), estado.aba_atual, estado.memoria_sub_abas[0], 
            dicionario_escalas, estado.rect_braco_colisao, alpha_atual, fontes['pequena'],
            scroll_atual # Passando o scroll!
        )
        
    # --- ABA 2: ANÁLISE DE IA ---
    if estado.aba_atual == 2 and estado.memoria_sub_abas[2] == 0:
        # A Mágica aqui: Subtraímos o scroll direto no Y da criação do botão e da aba!
        y_botao_ia = (estado.Y_CAIXA + 100) - scroll_atual
        btn_gravar_ia = pygame.Rect(estado.OFFSET_X + 20, y_botao_ia, 150, 40)
        notas_abertas_atual = lista_afinacoes[estado.indice_afinacao]["notas"]
        
        y_base_ia = (estado.Y_CAIXA + 50) - scroll_atual
        
        meu_processador.desenhar_aba_ia(
            tela, estado.OFFSET_X, y_base_ia, btn_gravar_ia, 
            meu_gravador, fontes['ui'], fontes['titulo'], notas_abertas_atual, estado 
        )
        
    if estado.aba_atual == 2 and estado.memoria_sub_abas[2] == 1:
        y_base_ritmo = estado.Y_CAIXA - scroll_atual
        meu_processador.desenhar_aba_treino_ritmo(tela, estado.OFFSET_X, y_base_ritmo, fontes['ui'], fontes['titulo'])

    # --- ABA 3: CONFIGURAÇÕES E METRÔNOMO ---
    if estado.aba_atual == 3 and estado.memoria_sub_abas[3] == 0: 
        # Passando o scroll como argumento novo
        configs.desenhar(tela, fontes['titulo'], fontes['ui'], scroll_atual)
        
    if estado.aba_atual == 3 and estado.memoria_sub_abas[3] == 3: 
        # Passando o scroll como argumento novo
        meu_metronomo.desenhar_config(tela, fontes['ui'], scroll_atual)

    # ========================================================
    # 2. DESLIGAR A MÁSCARA
    # ========================================================
    tela.set_clip(None)

    # ========================================================
    # 3. DESENHAR A BARRA DE ROLAGEM DINÂMICA
    # ========================================================
    if estado.max_scroll[estado.aba_atual] > 0:
        x_scroll = estado.OFFSET_X + estado.LARGURA_BRACO - 15
        tamanho_alca = max(30, altura_corte * (altura_corte / (altura_corte + estado.max_scroll[estado.aba_atual])))
        
        progresso = scroll_atual / estado.max_scroll[estado.aba_atual]
        y_alca = y_corte + (progresso * (altura_corte - tamanho_alca))
        
        pygame.draw.rect(tela, (60, 60, 60), (x_scroll, y_corte, 10, altura_corte), border_radius=5)
        pygame.draw.rect(tela, (150, 150, 150), (x_scroll, y_alca, 10, tamanho_alca), border_radius=5)
   
    
    meu_metronomo.desenhar_mini_metronomo(tela, tela.get_width(), tela.get_height(), fontes['ui'])