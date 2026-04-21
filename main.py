import pygame
import sys
import escalas 
import modulos_penta 

# Inicialização
pygame.init()

tela = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
LARGURA, ALTURA = tela.get_size()
pygame.display.set_caption("Guitar Studio IA - Tela Cheia")

# Cores
FUNDO_ESCURO = (30, 30, 30)
COR_CORDA = (180, 180, 180)
COR_TRASTE = (140, 140, 140)
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
MADEIRA = (80, 40, 15)
AZUL_BOTAO = (0, 120, 215)

CORES_TONICA = [
    BRANCO, (255, 80, 80), (80, 255, 80), 
    (255, 200, 50), (50, 200, 255), (200, 100, 255)
]

COR_PAINEL = (45, 45, 45)
COR_ABA_ATIVA = (65, 65, 65)
COR_ABA_INATIVA = (35, 35, 35)
COR_SUB_ATIVA = (100, 100, 100)
COR_SUB_INATIVA = (55, 55, 55)
COR_TEXTO_INATIVO = (150, 150, 150)

# Fontes
fonte_ui = pygame.font.SysFont("Arial", 18, bold=True)
fonte_pequena = pygame.font.SysFont("Arial", 15, bold=True)
fonte_titulo = pygame.font.SysFont("Arial", 22, bold=True)
fonte_notas_pequena = pygame.font.SysFont("Arial", 20, bold=True) 

# --- BANCO DE DADOS DE AFINAÇÕES ---
lista_afinacoes = [
    {"nome": "Standard B", "notas": ["B", "E", "A", "D", "G", "B", "E"]},
    {"nome": "Drop A",     "notas": ["A", "E", "A", "D", "G", "B", "E"]},
    {"nome": "Standard A", "notas": ["A", "D", "G", "C", "F", "A", "D"]},
    {"nome": "All 4ths",   "notas": ["B", "E", "A", "D", "G", "C", "F"]}
]
indice_afinacao = 0

tom_atual = 'C'
indice_cor_tonica = 0
dropdown_tom_aberto = False

# --- MEDIDAS DINÂMICAS DO BRAÇO ---
# NOVO: Desci o braço para o Y=90 para caber o menu superior
OFFSET_X = 100 
OFFSET_Y = 90 
NUM_CORDAS = 7

# NOVO: Variável global que começa em 18 casas
NUM_CASAS = 18 

LARGURA_BRACO = LARGURA - 350 
ALTURA_BRACO = 300 
ESPACO_CORDAS = ALTURA_BRACO / (NUM_CORDAS - 1)
ESPACO_CASAS = LARGURA_BRACO / NUM_CASAS

rect_braco_colisao = pygame.Rect(OFFSET_X, OFFSET_Y, LARGURA_BRACO, ALTURA_BRACO)

# --- BOTÕES DO MENU SUPERIOR (NOVO) ---
btn_menos_casa = pygame.Rect(OFFSET_X, 30, 40, 35)
btn_mais_casa = pygame.Rect(OFFSET_X + 160, 30, 40, 35)

# --- LÓGICA DE INTERFACE LATERAL ---
X_PAINEL = LARGURA - 220
Y_PAINEL = OFFSET_Y + 50
btn_up = pygame.Rect(X_PAINEL + 50, Y_PAINEL, 40, 40)
btn_down = pygame.Rect(X_PAINEL + 50, Y_PAINEL + 60, 40, 40)

rect_btn_tom = pygame.Rect(0, 0, 0, 0)
rects_notas_dropdown = [] 
rects_cores = []          

# Lógica das Abas
Y_CAIXA = OFFSET_Y + ALTURA_BRACO + 80
ALTURA_CAIXA = ALTURA - Y_CAIXA - 50 
nomes_abas = ["Escalas", "Acordes", "Análise de IA", "Configurações"]
aba_atual = 0
rects_abas = []

nomes_sub_abas = [
    ["Maior", "Menor", "Pentatônica", "Blues", "Modos Gregos"],
    ["Tríades", "Tétrades", "Inversões", "Diminutos", "Suspensos"],
    ["Ouvir Solo", "Sugerir Acorde", "Gerar Backing", "Timbre", "Chat"],
    ["Cores", "Sons", "MIDI", "Metrônomo", "Exportar Projeto"]
]
memoria_sub_abas = [0, 0, 0, 0] 
rects_sub_abas = []

# --- INICIALIZAÇÃO DINÂMICA DAS ESCALAS ---
lista_modulos_penta = []

def recriar_modulos_escala():
    """NOVO: Recalcula o tamanho dos blocos pretos de acordo com o nº de casas"""
    global lista_modulos_penta, ESPACO_CASAS
    
    # Atualiza a matemática do espaçamento da casa
    ESPACO_CASAS = LARGURA_BRACO / NUM_CASAS
    
    lista_modulos_penta.clear() # Limpa os módulos antigos da memória
    
    offset_inicial_x = OFFSET_X + 20     
    distancia_entre_shapes = 150         
    offset_y_painel = Y_CAIXA + 130      

    # Cria os módulos novinhos em folha com o novo tamanho (ESPACO_CASAS)
    for indice, padrao in enumerate(modulos_penta.TODOS_OS_SHAPES):
        x_pos = offset_inicial_x + (indice * distancia_entre_shapes)
        novo_modulo = modulos_penta.DesenhoEscala(
            x_painel=x_pos, 
            y_painel=offset_y_painel, 
            espaco_casas=ESPACO_CASAS, 
            espaco_cordas=ESPACO_CORDAS, 
            altura_braco=ALTURA_BRACO,
            offset_x=OFFSET_X,
            num_casas_total=NUM_CASAS,
            padrao=padrao
        )
        lista_modulos_penta.append(novo_modulo)

# Chama a função pela primeira vez para carregar o programa
recriar_modulos_escala()

def desenhar_painel_superior():
    """NOVO: Desenha os botões de mudar o número de casas"""
    # Fundo do botão -
    pygame.draw.rect(tela, AZUL_BOTAO, btn_menos_casa, border_radius=5)
    tela.blit(fonte_titulo.render("-", True, BRANCO), (btn_menos_casa.centerx - 5, btn_menos_casa.centery - 15))
    
    # Texto do meio
    txt_casas = fonte_titulo.render(f"Casas: {NUM_CASAS}", True, BRANCO)
    tela.blit(txt_casas, (OFFSET_X + 50, 35))
    
    # Fundo do botão +
    pygame.draw.rect(tela, AZUL_BOTAO, btn_mais_casa, border_radius=5)
    tela.blit(fonte_titulo.render("+", True, BRANCO), (btn_mais_casa.centerx - 7, btn_mais_casa.centery - 15))


def desenhar_guitarra():
    tela.fill(FUNDO_ESCURO)
    notas_abertas = lista_afinacoes[indice_afinacao]["notas"]

    pygame.draw.rect(tela, MADEIRA, (OFFSET_X, OFFSET_Y, LARGURA_BRACO, ALTURA_BRACO))

    # Desenha as casas baseado na variável global NUM_CASAS
    for casa in range(NUM_CASAS + 1):
        x = OFFSET_X + (casa * ESPACO_CASAS)
        pygame.draw.line(tela, COR_TRASTE, (x, OFFSET_Y), (x, OFFSET_Y + ALTURA_BRACO), 2)
        if casa > 0:
            num = fonte_ui.render(str(casa), True, (150, 150, 150))
            tela.blit(num, (x - (ESPACO_CASAS/2) - 5, OFFSET_Y + ALTURA_BRACO + 15))

    for i in range(NUM_CORDAS):
        y = OFFSET_Y + ALTURA_BRACO - (i * ESPACO_CORDAS)
        espessura = 1 + ((NUM_CORDAS - 1 - i) * 0.7)
        pygame.draw.line(tela, COR_CORDA, (OFFSET_X, y), (OFFSET_X + LARGURA_BRACO, y), int(espessura))
        
        nota_aberta_atual = notas_abertas[i]
        raio_circulo = 18 

        for casa in range(NUM_CASAS + 1):
            nota_calculada = escalas.obter_nota(nota_aberta_atual, casa)
            
            if casa == 0:
                x_nota = OFFSET_X - 40 
            else:
                x_nota = OFFSET_X + (casa * ESPACO_CASAS) - (ESPACO_CASAS / 2)

            if nota_calculada == tom_atual:
                cor_fundo = CORES_TONICA[indice_cor_tonica]
            else:
                cor_fundo = BRANCO

            pygame.draw.circle(tela, cor_fundo, (int(x_nota), int(y)), raio_circulo)
            pygame.draw.circle(tela, PRETO, (int(x_nota), int(y)), raio_circulo, 2)
            
            txt_nota = fonte_notas_pequena.render(nota_calculada, True, PRETO)
            txt_x = x_nota - (txt_nota.get_width() / 2)
            txt_y = y - (txt_nota.get_height() / 2)
            tela.blit(txt_nota, (txt_x, txt_y))

def desenhar_painel_lateral():
    global rect_btn_tom, rects_notas_dropdown, rects_cores

    info = lista_afinacoes[indice_afinacao]["nome"]
    tela.blit(fonte_ui.render(f"Afinação: {info}", True, BRANCO), (X_PAINEL, Y_PAINEL - 40))

    pygame.draw.rect(tela, AZUL_BOTAO, btn_up, border_radius=5)
    tela.blit(fonte_ui.render("^", True, BRANCO), (btn_up.centerx - 5, btn_up.centery - 10))
    pygame.draw.rect(tela, AZUL_BOTAO, btn_down, border_radius=5)
    tela.blit(fonte_ui.render("v", True, BRANCO), (btn_down.centerx - 5, btn_down.centery - 10))

    y_cor_base = Y_PAINEL + 150
    tela.blit(fonte_ui.render("Tônica:", True, BRANCO), (X_PAINEL, y_cor_base))
    
    rects_cores.clear()
    for i, cor in enumerate(CORES_TONICA):
        bx = X_PAINEL + 75 + (i * 24) 
        by = y_cor_base + 10
        raio_cor = 10
        
        pygame.draw.circle(tela, cor, (bx, by), raio_cor)
        if i == indice_cor_tonica:
            pygame.draw.circle(tela, BRANCO, (bx, by), raio_cor + 3, 2) 
        else:
            pygame.draw.circle(tela, PRETO, (bx, by), raio_cor, 1)

        rects_cores.append({'rect': pygame.Rect(bx - raio_cor, by - raio_cor, raio_cor*2, raio_cor*2), 'indice': i})

    y_tom_base = y_cor_base + 50
    tela.blit(fonte_ui.render("Tom:", True, BRANCO), (X_PAINEL, y_tom_base))

    cx, cy = X_PAINEL + 75, y_tom_base + 10
    pygame.draw.circle(tela, BRANCO, (cx, cy), 18)
    pygame.draw.circle(tela, PRETO, (cx, cy), 18, 2)
    txt_tom = fonte_notas_pequena.render(tom_atual, True, PRETO)
    tela.blit(txt_tom, (cx - txt_tom.get_width()//2, cy - txt_tom.get_height()//2))

    rect_btn_tom = pygame.Rect(cx - 18, cy - 18, 36, 36)

    rects_notas_dropdown.clear()
    if dropdown_tom_aberto:
        pygame.draw.rect(tela, (50, 50, 50), (cx - 20, cy + 25, 140, 180), border_radius=8)
        
        for i, nota in enumerate(escalas.NOTAS):
            coluna = i % 3
            linha = i // 3
            nx = cx + (coluna * 45)
            ny = cy + 45 + (linha * 40)

            pygame.draw.circle(tela, BRANCO, (nx, ny), 18)
            pygame.draw.circle(tela, PRETO, (nx, ny), 18, 2)
            tn = fonte_notas_pequena.render(nota, True, PRETO)
            tela.blit(tn, (nx - tn.get_width()//2, ny - tn.get_height()//2))

            rects_notas_dropdown.append({'rect': pygame.Rect(nx-18, ny-18, 36, 36), 'nota': nota})

def desenhar_painel_inferior():
    global rects_abas, rects_sub_abas
    rects_abas.clear()
    rects_sub_abas.clear()
    
    caixa_principal = pygame.Rect(OFFSET_X, Y_CAIXA, LARGURA_BRACO, ALTURA_CAIXA)
    pygame.draw.rect(tela, COR_PAINEL, caixa_principal, border_radius=10)

    altura_aba = 40
    largura_aba = LARGURA_BRACO / len(nomes_abas)

    for i, nome in enumerate(nomes_abas):
        x_aba = OFFSET_X + (i * largura_aba)
        y_aba = Y_CAIXA - altura_aba 
        
        rect_aba = pygame.Rect(x_aba, y_aba, largura_aba, altura_aba)
        rects_abas.append(rect_aba) 
        
        cor_fundo = COR_ABA_ATIVA if i == aba_atual else COR_ABA_INATIVA
        cor_texto = BRANCO if i == aba_atual else COR_TEXTO_INATIVO
        
        pygame.draw.rect(tela, cor_fundo, rect_aba, border_top_left_radius=10, border_top_right_radius=10)
        txt = fonte_ui.render(nome, True, cor_texto)
        tela.blit(txt, (x_aba + (largura_aba/2) - (txt.get_width()/2), y_aba + 10))

    margem_interna = 20
    largura_util = LARGURA_BRACO - (margem_interna * 2)
    largura_sub = largura_util / 5 
    altura_sub = 35
    y_sub = Y_CAIXA + 15 

    lista_subs_atual = nomes_sub_abas[aba_atual]
    sub_selecionada = memoria_sub_abas[aba_atual]

    for j, nome_sub in enumerate(lista_subs_atual):
        x_sub = OFFSET_X + margem_interna + (j * largura_sub)
        
        rect_sub = pygame.Rect(x_sub + 5, y_sub, largura_sub - 10, altura_sub)
        rects_sub_abas.append(rect_sub)
        
        cor_fundo_sub = COR_SUB_ATIVA if j == sub_selecionada else COR_SUB_INATIVA
        cor_texto_sub = BRANCO if j == sub_selecionada else COR_TEXTO_INATIVO
        
        pygame.draw.rect(tela, cor_fundo_sub, rect_sub, border_radius=6)
        txt_sub = fonte_pequena.render(nome_sub, True, cor_texto_sub)
        tela.blit(txt_sub, (rect_sub.centerx - (txt_sub.get_width()/2), rect_sub.centery - (txt_sub.get_height()/2)))

def main():
    global indice_afinacao, aba_atual, memoria_sub_abas
    global tom_atual, indice_cor_tonica, dropdown_tom_aberto, NUM_CASAS

    rodando = True
    
    while rodando:
        pos_mouse = pygame.mouse.get_pos()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    rodando = False

            if evento.type == pygame.MOUSEBUTTONDOWN:
                clicou_em_algo_do_dropdown = False

                # --- NOVO: LÓGICA DE MAIS OU MENOS CASAS ---
                if btn_menos_casa.collidepoint(evento.pos):
                    if NUM_CASAS > 12: # Limite mínimo: 12 casas
                        NUM_CASAS -= 1
                        recriar_modulos_escala()
                        continue
                
                if btn_mais_casa.collidepoint(evento.pos):
                    if NUM_CASAS < 24: # Limite máximo: 24 casas
                        NUM_CASAS += 1
                        recriar_modulos_escala()
                        continue

                # 1. LÓGICA DOS MÓDULOS DA PENTATÔNICA
                if aba_atual == 0 and memoria_sub_abas[0] == 2:
                    clicou_num_modulo = False
                    
                    for modulo in lista_modulos_penta:
                        if modulo.tratar_clique(evento.pos, rect_braco_colisao):
                            clicou_num_modulo = True
                            break 
                    
                    if clicou_num_modulo:
                        continue 

                # 2. Dropdown Tom
                if dropdown_tom_aberto:
                    for item in rects_notas_dropdown:
                        if item['rect'].collidepoint(evento.pos):
                            tom_atual = item['nota']       
                            dropdown_tom_aberto = False    
                            clicou_em_algo_do_dropdown = True
                            break

                # 3. Botão Tom
                if not clicou_em_algo_do_dropdown and rect_btn_tom.collidepoint(evento.pos):
                    dropdown_tom_aberto = not dropdown_tom_aberto
                    clicou_em_algo_do_dropdown = True

                if not clicou_em_algo_do_dropdown and dropdown_tom_aberto:
                    dropdown_tom_aberto = False

                # 4. Cores Tônica
                for item in rects_cores:
                    if item['rect'].collidepoint(evento.pos):
                        indice_cor_tonica = item['indice']

                # 5. Afinação
                if btn_up.collidepoint(evento.pos):
                    indice_afinacao = (indice_afinacao - 1) % len(lista_afinacoes)
                    recriar_modulos_escala() # Garante que os modulos recalculem caso a afinação mude o grid (opcional, mas seguro)
                if btn_down.collidepoint(evento.pos):
                    indice_afinacao = (indice_afinacao + 1) % len(lista_afinacoes)
                    recriar_modulos_escala()
                
                # 6 e 7. Abas
                for i, rect in enumerate(rects_abas):
                    if rect.collidepoint(evento.pos):
                        aba_atual = i
                for j, rect in enumerate(rects_sub_abas):
                    if rect.collidepoint(evento.pos):
                        memoria_sub_abas[aba_atual] = j

        # --- RENDERIZAÇÃO ---
        desenhar_guitarra()
        desenhar_painel_superior() # Desenha os botões de +- casas
        desenhar_painel_inferior()
        
        if aba_atual == 0 and memoria_sub_abas[0] == 2:
            for modulo in lista_modulos_penta:
                modulo.atualizar_e_desenhar(tela, pos_mouse, rect_braco_colisao)
            
        desenhar_painel_lateral() 
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()