import pygame
import escalas
import gerenciador_interface
from constantes_ui import *

def desenhar_painel_superior(tela, estado, fontes):
    btn_menos_casa = pygame.Rect(estado.OFFSET_X, 30, 40, 35)
    btn_mais_casa = pygame.Rect(estado.OFFSET_X + 160, 30, 40, 35)
    
    pygame.draw.rect(tela, AZUL_BOTAO, btn_menos_casa, border_radius=5)
    tela.blit(fontes['titulo'].render("-", True, BRANCO), (btn_menos_casa.centerx - 5, btn_menos_casa.centery - 15))
    
    txt_casas = fontes['titulo'].render(f"Casas: {estado.NUM_CASAS}", True, BRANCO)
    tela.blit(txt_casas, (estado.OFFSET_X + 50, 35))
    
    pygame.draw.rect(tela, AZUL_BOTAO, btn_mais_casa, border_radius=5)
    tela.blit(fontes['titulo'].render("+", True, BRANCO), (btn_mais_casa.centerx - 7, btn_mais_casa.centery - 15))

def desenhar_guitarra(tela, estado, configs, fontes):
    notas_abertas = lista_afinacoes[estado.indice_afinacao]["notas"]
    cor_madeira = configs.get_cor_braco() if configs else MADEIRA
    pygame.draw.rect(tela, cor_madeira, (estado.OFFSET_X, estado.OFFSET_Y, estado.LARGURA_BRACO, estado.ALTURA_BRACO))

    for casa in range(estado.NUM_CASAS + 1):
        x = estado.OFFSET_X + (casa * estado.ESPACO_CASAS)
        pygame.draw.line(tela, COR_TRASTE, (x, estado.OFFSET_Y), (x, estado.OFFSET_Y + estado.ALTURA_BRACO), 2)
        if casa > 0:
            num = fontes['ui'].render(str(casa), True, (150, 150, 150))
            tela.blit(num, (x - (estado.ESPACO_CASAS/2) - 5, estado.OFFSET_Y + estado.ALTURA_BRACO + 15))

    modo_texto = configs.get_modo_texto() if configs else 'letras'
    cor_base_escala = configs.get_cor_notas() if configs else BRANCO

    def obter_grau(tonica, nota_alvo):
        try:
            dist = (escalas.NOTAS.index(nota_alvo) - escalas.NOTAS.index(tonica)) % 12
            return {0:"1", 1:"b2", 2:"2", 3:"m3", 4:"3", 5:"4", 6:"b5", 7:"5", 8:"b6", 9:"6", 10:"b7", 11:"7"}[dist]
        except: return ""

    for i in range(estado.NUM_CORDAS):
        y = estado.OFFSET_Y + estado.ALTURA_BRACO - (i * estado.ESPACO_CORDAS)
        espessura = 1 + ((estado.NUM_CORDAS - 1 - i) * 0.7)
        pygame.draw.line(tela, COR_CORDA, (estado.OFFSET_X, y), (estado.OFFSET_X + estado.LARGURA_BRACO, y), int(espessura))
        
        nota_aberta_atual = notas_abertas[i]
        raio_circulo = 18 

        for casa in range(estado.NUM_CASAS + 1):
            nota_calculada = escalas.obter_nota(nota_aberta_atual, casa)
            cor_fundo = cor_base_escala 
            
            x_nota = estado.OFFSET_X - 40 if casa == 0 else estado.OFFSET_X + (casa * estado.ESPACO_CASAS) - (estado.ESPACO_CASAS / 2)

            if nota_calculada == estado.tom_atual: cor_fundo = CORES_TONICA[estado.indice_cor_tonica]
            elif nota_calculada == escalas.obter_terca(estado.tom_atual): cor_fundo = CORES_TONICA[estado.indice_cor_terca]
            elif nota_calculada == escalas.obter_quinta(estado.tom_atual): cor_fundo = CORES_TONICA[estado.indice_cor_quinta]

            pygame.draw.circle(tela, cor_fundo, (int(x_nota), int(y)), raio_circulo)
            pygame.draw.circle(tela, PRETO, (int(x_nota), int(y)), raio_circulo, 2)
            
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
    
    desenhar_guitarra(tela, estado, configs, fontes)
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
        btn_gravar_ia = pygame.Rect(estado.OFFSET_X + 50, estado.Y_CAIXA + 80, 150, 40)
        notas_abertas_atual = lista_afinacoes[estado.indice_afinacao]["notas"]
        
        meu_processador.desenhar_aba_ia(
            tela, estado.OFFSET_X, estado.Y_CAIXA, btn_gravar_ia, 
            meu_gravador, fontes['ui'], fontes['titulo'], notas_abertas_atual
        )
        
    meu_metronomo.desenhar_mini_metronomo(tela, tela.get_width(), tela.get_height(), fontes['ui'])