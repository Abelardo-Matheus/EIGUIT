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


def desenhar_guitarra(tela, estado, configs, fontes, meu_processador):
    notas_abertas = lista_afinacoes[estado.indice_afinacao]["notas"]
    cor_madeira = configs.get_cor_braco() if configs else MADEIRA
    
    # ========================================================
    # --- MATEMÁTICA DINÂMICA: GUITARRA VS BAIXO ---
    # ========================================================
    instrumento = getattr(estado, 'instrumento', 'guitarra')
    num_cordas_desenho = 4 if instrumento == 'baixo' else estado.NUM_CORDAS
    
    # Se for baixo, a madeira "emagrece" o equivalente a 2 cordas e desce um pouco para centralizar
    if instrumento == 'baixo':
        altura_braco_atual = estado.ALTURA_BRACO - (2 * estado.ESPACO_CORDAS)
        offset_y_atual = estado.OFFSET_Y + estado.ESPACO_CORDAS
    else:
        altura_braco_atual = estado.ALTURA_BRACO
        offset_y_atual = estado.OFFSET_Y

    # 1. Desenha a madeira ajustada
    pygame.draw.rect(tela, cor_madeira, (estado.OFFSET_X, offset_y_atual, estado.LARGURA_BRACO, altura_braco_atual))

    # 2. Desenha os Trastes usando a nova altura
    for casa in range(estado.NUM_CASAS + 1):
        x = estado.OFFSET_X + (casa * estado.ESPACO_CASAS)
        pygame.draw.line(tela, COR_TRASTE, (x, offset_y_atual), (x, offset_y_atual + altura_braco_atual), 2)
        if casa > 0:
            num = fontes['ui'].render(str(casa), True, (150, 150, 150))
            tela.blit(num, (x - (estado.ESPACO_CASAS/2) - 5, offset_y_atual + altura_braco_atual + 15))
    
    modo_texto = configs.get_modo_texto() if configs else 'letras'
    cor_base_escala = configs.get_cor_notas() if configs else BRANCO
    
    # 3. Desenha as Cordas
    for i in range(num_cordas_desenho):
        
        if instrumento == 'baixo':
            espessura = 2 + ((num_cordas_desenho - 1 - i) * 1.5) 
            # Calcula o padding para as 4 cordas ficarem perfeitamente no meio da madeira fina
            padding = (altura_braco_atual - ((num_cordas_desenho - 1) * estado.ESPACO_CORDAS)) / 2
            y = offset_y_atual + altura_braco_atual - padding - (i * estado.ESPACO_CORDAS)
            
            # Pula as 2 cordas mais agudas da afinação da guitarra (E e B)
            indice_nota = i + 2 
        else:
            espessura = 1 + ((estado.NUM_CORDAS - 1 - i) * 0.7)
            y = estado.OFFSET_Y + estado.ALTURA_BRACO - (i * estado.ESPACO_CORDAS)
            indice_nota = i

        pygame.draw.line(tela, COR_CORDA, (estado.OFFSET_X, y), (estado.OFFSET_X + estado.LARGURA_BRACO, y), int(espessura))
        
        nota_aberta_atual = notas_abertas[indice_nota]

        # 4. Desenha as Notas (Bolinhas)
        for casa in range(estado.NUM_CASAS + 1):
            nota_calculada = escalas.obter_nota(nota_aberta_atual, casa)
            cor_fundo = cor_base_escala 
            raio_atual = 18 
            
            x_nota = estado.OFFSET_X - 40 if casa == 0 else estado.OFFSET_X + (casa * estado.ESPACO_CASAS) - (estado.ESPACO_CASAS / 2)

            if nota_calculada == estado.tom_atual: cor_fundo = CORES_TONICA[estado.indice_cor_tonica]
            elif nota_calculada == escalas.obter_terca(estado.tom_atual): cor_fundo = CORES_TONICA[estado.indice_cor_terca]
            elif nota_calculada == escalas.obter_quinta(estado.tom_atual): cor_fundo = CORES_TONICA[estado.indice_cor_quinta]

            # Frequência da IA mapeada para o índice correto da corda
            if estado.freq_detectada > 0 and len(meu_processador.freqs_referencia) > indice_nota:
                freq_aberta = meu_processador.freqs_referencia[indice_nota]
                freq_desta_casa = freq_aberta * (2 ** (casa / 12.0))
                margem = freq_desta_casa * 0.03
                
                if abs(estado.freq_detectada - freq_desta_casa) < margem:
                    cor_fundo = (255, 255, 0) 
                    raio_atual = 26 

            pygame.draw.circle(tela, cor_fundo, (int(x_nota), int(y)), raio_atual)
            pygame.draw.circle(tela, PRETO, (int(x_nota), int(y)), raio_atual, 2)
            
            if modo_texto != 'vazio':
                texto_str = nota_calculada if modo_texto == 'letras' else obter_grau(estado.tom_atual, nota_calculada)
                txt_nota = fontes['notas'].render(texto_str, True, PRETO)
                tela.blit(txt_nota, (x_nota - (txt_nota.get_width()/2), y - (txt_nota.get_height()/2)))

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

def desenhar_tudo(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador):
    tela.fill(FUNDO_ESCURO)
    
    desenhar_guitarra(tela, estado, configs, fontes, meu_processador) 
    desenhar_painel_superior(tela, estado, fontes)
    desenhar_painel_lateral(tela, estado, fontes)
    desenhar_painel_inferior(tela, estado, fontes) 
    
    alpha_atual = configs.get_alpha() if configs else 255
    gerenciador_interface.desenhar_escalas_ativas(
        tela, pygame.mouse.get_pos(), estado.aba_atual, estado.memoria_sub_abas[estado.aba_atual], 
        dicionario_escalas, estado.rect_braco_colisao, alpha_atual, fontes['pequena'] 
    )
        
    if estado.aba_atual == 3 and estado.memoria_sub_abas[3] == 0: configs.desenhar(tela, fontes['titulo'], fontes['ui'])
    if estado.aba_atual == 3 and estado.memoria_sub_abas[3] == 3: meu_metronomo.desenhar_config(tela, fontes['ui'])
    if estado.aba_atual == 2 and estado.memoria_sub_abas[2] == 0:
        btn_gravar_ia = pygame.Rect(estado.OFFSET_X + 20, estado.Y_CAIXA + 100, 150, 40)
        
        notas_abertas_atual = lista_afinacoes[estado.indice_afinacao]["notas"]
        
        meu_processador.desenhar_aba_ia(
            tela, estado.OFFSET_X, estado.Y_CAIXA+50, btn_gravar_ia, 
            meu_gravador, fontes['ui'], fontes['titulo'], notas_abertas_atual, estado 
        )
    # ==========================================
    # --- NOVO: Sub-Aba 1 (Treino de Ritmo) ---
    # ==========================================
    if estado.aba_atual == 2 and estado.memoria_sub_abas[2] == 1:
        meu_processador.desenhar_aba_treino_ritmo(tela, estado.OFFSET_X, estado.Y_CAIXA, fontes['ui'], fontes['titulo'])
        
    meu_metronomo.desenhar_mini_metronomo(tela, tela.get_width(), tela.get_height(), fontes['ui'])