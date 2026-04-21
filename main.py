import pygame
import sys
import escalas 
import modulos_penta 
import modulos_escala_maior
import modulos_escala_menor
import gerenciador_interface # Importe o novo mestre de cerimônias
import modulos_teoria_avancada as teoria
import modulos_acordes as acordes
import modulo_metronomo

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
indice_cor_tonica = 0  # Vermelho (CORES_TONICA[1])
indice_cor_terca = 0   # Verde (CORES_TONICA[2])
indice_cor_quinta = 0  # Azul (CORES_TONICA[4])
dropdown_tom_aberto = False
rects_cores_tonica = []
rects_cores_terca = []
rects_cores_quinta = []
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
meu_metronomo = modulo_metronomo.Metronomo(OFFSET_X + 50, Y_CAIXA + 80)
nomes_sub_abas = [
    ["Maior", "Menor", "Pentatônica", "Blues", "Modos Gregos"],
    ["Tríades", "Tétrades", "Inversões", "Diminutos", "Suspensos"],
    ["Ouvir Solo", "Sugerir Acorde", "Gerar Backing", "Timbre", "Chat"],
    ["Cores", "Sons", "MIDI", "Metrônomo", "Exportar Projeto"]
]
memoria_sub_abas = [0, 0, 0, 0] 
rects_sub_abas = []
lista_modulos_maior = []
# --- INICIALIZAÇÃO DINÂMICA DAS ESCALAS ---
lista_modulos_penta = []

# --- INICIALIZAÇÃO DINÂMICA DAS ESCALAS ---
lista_modulos_penta = []
lista_modulos_maior = []
lista_modulos_menor = []
lista_modulos_penta = []
lista_modulos_blues = []
lista_modulos_modos = []

# --- LISTAS GLOBAIS DE ACORDES ---
lista_modulos_triades_maior = []
lista_modulos_triades_menor = []

# MUDAMOS DE "def DesenhoEscala():" PARA "class DesenhoEscala:"
class DesenhoEscala:
    # NOVO: Adicionei 'nome=""' no final dos parâmetros
    def __init__(self, x_painel, y_painel, espaco_casas, espaco_cordas, altura_braco, offset_x, num_casas_total, padrao, nome=""):
        self.x_original = x_painel
        self.y_original = y_painel
        self.nome = nome # Salva o nome para usar depois
        
        self.espaco_casas = espaco_casas
        self.offset_x = offset_x
        self.num_casas_total = num_casas_total
        self.num_casas_desenho = len(padrao[0]) 
        
        self.padding_x = 5  
        self.padding_y = 20  
        raio = 18
        
        self.largura_real = espaco_casas * self.num_casas_desenho
        self.altura_real = altura_braco
        
        w_surf = int(self.largura_real + (self.padding_x * 2))
        h_surf = int(self.altura_real + (self.padding_y * 2))
        
        self.imagem_braco = pygame.Surface((w_surf, h_surf))
        self.imagem_braco.fill((0, 0, 0)) 
        self.imagem_braco.set_alpha(255) 
        
        COR_TRANSPARENTE = (255, 255, 255)
        self.imagem_braco.set_colorkey(COR_TRANSPARENTE)
        pygame.draw.rect(self.imagem_braco, (255, 255, 255), self.imagem_braco.get_rect(), 2)
        
        # Definimos uma cor fixa de destaque para a tônica dentro da miniatura
        COR_DESTAQUE_TONICA = (255, 80, 80) # Vermelho claro
        COR_NORMAL = (255, 255, 255)        # Branco

        for corda in range(7):
            for casa_interna in range(self.num_casas_desenho):
                valor_matriz = padrao[corda][casa_interna]
                
                # Se for 1 (Nota Normal) ou 2 (Tônica)
                if valor_matriz in [1, 2]:
                    x_bolinha = self.padding_x + (casa_interna * espaco_casas) + (espaco_casas / 2)
                    y_bolinha = self.padding_y + self.altura_real - (corda * espaco_cordas)
                    
                    # Desenha o "fundo" transparente que não apaga o braço
                    pygame.draw.circle(self.imagem_braco, COR_TRANSPARENTE, (int(x_bolinha), int(y_bolinha)), raio)
                    
                    # Desenha a borda da bolinha
                    # Se for a tônica (valor 2), a borda fica vermelha e mais grossa
                    if valor_matriz == 2:
                        pygame.draw.circle(self.imagem_braco, COR_DESTAQUE_TONICA, (int(x_bolinha), int(y_bolinha)), raio, 5)
                    else:
                        pygame.draw.circle(self.imagem_braco, COR_NORMAL, (int(x_bolinha), int(y_bolinha)), raio, 3)

        escala = 0.40
        w_painel = int(w_surf * escala)
        h_painel = int(h_surf * escala)
        
        self.imagem_painel = pygame.transform.scale(self.imagem_braco, (w_painel, h_painel))
        self.imagem_painel.set_colorkey(COR_TRANSPARENTE) 
        self.rect_painel = self.imagem_painel.get_rect(topleft=(x_painel, y_painel))
        self.rect_braco = self.imagem_braco.get_rect()
        self.estado = 'painel' 

    # (O tratar_clique continua igualzinho)
    def tratar_clique(self, pos_mouse, rect_braco_colisao):
        if self.estado == 'painel':
            if self.rect_painel.collidepoint(pos_mouse):
                self.estado = 'mouse'
                return True
        elif self.estado == 'braco':
            if self.rect_braco.collidepoint(pos_mouse):
                self.estado = 'painel'
                return True
        elif self.estado == 'mouse':
            if rect_braco_colisao.collidepoint(pos_mouse):
                self.estado = 'braco'
            else:
                self.estado = 'painel'
            return True
        return False

    def atualizar_e_desenhar(self, tela, pos_mouse, rect_braco_colisao):
        if self.estado == 'painel':
            tela.blit(self.imagem_painel, self.rect_painel.topleft)
            
            # --- NOVO: DESENHA O NOME EM CIMA DA MINIATURA ---
            if self.nome != "":
                # Cria o texto usando a sua fonte branca
                texto_nome = fonte_pequena.render(self.nome, True, BRANCO)
                # Calcula o meio exato do bloco para centralizar o texto
                txt_x = self.rect_painel.centerx - (texto_nome.get_width() / 2)
                # Coloca o texto 25 pixels acima do bloco
                txt_y = self.rect_painel.top - 25 
                tela.blit(texto_nome, (txt_x, txt_y))
            
        elif self.estado == 'mouse' or self.estado == 'braco':
            if self.estado == 'mouse':
                if rect_braco_colisao.collidepoint(pos_mouse):
                    x_relativo = pos_mouse[0] - self.offset_x
                    casa_atual = int(x_relativo // self.espaco_casas)
                    casa_atual = max(0, min(casa_atual, self.num_casas_total - self.num_casas_desenho))
                    
                    self.rect_braco.x = self.offset_x + (casa_atual * self.espaco_casas) - self.padding_x
                    self.rect_braco.y = rect_braco_colisao.y - self.padding_y
                    
                    pygame.draw.rect(tela, (0, 255, 0), self.rect_braco, 4)
                else:
                    self.rect_braco.center = pos_mouse
                    pygame.draw.rect(tela, (255, 0, 0), self.rect_braco, 4)

            tela.blit(self.imagem_braco, self.rect_braco.topleft)

def recriar_modulos_escala():
    global lista_modulos_penta, lista_modulos_maior, lista_modulos_menor
    global lista_modulos_modos, lista_modulos_triades_maior, lista_modulos_triades_menor, lista_modulos_blues
    global ESPACO_CASAS
    
    
    ESPACO_CASAS = LARGURA_BRACO / NUM_CASAS
    
    # Limpeza de todas as listas
    listas_para_limpar = [
        lista_modulos_penta, 
        lista_modulos_maior, 
        lista_modulos_menor,
        lista_modulos_modos, 
        lista_modulos_triades_maior, # Atualizado
        lista_modulos_triades_menor, # Novo
        lista_modulos_blues
    ]

    for lista in listas_para_limpar:
        lista.clear()
    
    offset_inicial_x = OFFSET_X + 20     
    offset_y_painel = Y_CAIXA + 150 
    espaco_entre_imagens = 30 
    
    # Nomes para exibir em cima dos desenhos
    nomes_caged = ["Forma C", "Forma A", "Forma G", "Forma E", "Forma D"]
    nomes_shapes = ["Shape 1", "Shape 2", "Shape 3", "Shape 4", "Shape 5", "Completo"]
    nomes_modos = ["Jônico", "Dórico", "Frígio", "Lídio", "Mixolídio", "Eólio", "Lócrio"]
    nomes_acordes = ["Maior", "Menor", "Aumentado", "Diminuto", "Sus2", "Sus4"]

    

    # --- FUNÇÃO AUXILIAR INTERNA PARA EVITAR REPETIÇÃO (DRY) ---
    def carregar_categoria(lista_destino, matrizes, nomes):
        nonlocal offset_inicial_x, offset_y_painel, espaco_entre_imagens
        pos_x = offset_inicial_x
        for i, padrao in enumerate(matrizes):
            nome_label = nomes[i] if i < len(nomes) else f"Shape {i+1}"
            modulo = DesenhoEscala(
                x_painel=pos_x, y_painel=offset_y_painel, espaco_casas=ESPACO_CASAS,
                espaco_cordas=ESPACO_CORDAS, altura_braco=ALTURA_BRACO, offset_x=OFFSET_X,
                num_casas_total=NUM_CASAS, padrao=padrao, nome=nome_label
            )
            lista_destino.append(modulo)
            pos_x += modulo.imagem_painel.get_width() + espaco_entre_imagens

    # --- CARREGAMENTO DAS CATEGORIAS ---
    nomes_caged = ["Forma C", "Forma A", "Forma G", "Forma E", "Forma D"]
    # 1. Pentatônica
    carregar_categoria(lista_modulos_penta, modulos_penta.TODOS_OS_SHAPES, nomes_shapes)

    # 2. Escala Maior
    carregar_categoria(lista_modulos_maior, modulos_escala_maior.TODOS_OS_SHAPES, nomes_shapes)
        
    # 3. Escala Menor
    carregar_categoria(lista_modulos_menor, modulos_escala_menor.TODOS_OS_SHAPES, nomes_shapes)

    # 4. Blues (Penta + Blue Note)
    carregar_categoria(lista_modulos_blues, teoria.TODOS_OS_SHAPES_BLUES, nomes_shapes)

    # 5. Modos Gregos (7 Shapes ou 3 notas por corda)
    carregar_categoria(lista_modulos_modos, teoria.TODOS_OS_MODOS, nomes_modos)

    # Acordes Maiores (Aba 1, Sub-aba 0)
    carregar_categoria(lista_modulos_triades_maior, acordes.TODOS_AS_TRIADES_MAIORES, ["C Major", "A Major", "G Major", "E Major", "D Major"])

    # Acordes Menores (Aba 1, Sub-aba 1) - Você precisará criar a 'lista_modulos_triades_menor'
    carregar_categoria(lista_modulos_triades_menor, acordes.TODOS_AS_TRIADES_MENORES, ["C Minor", "A Minor", "G Minor", "E Minor", "D Minor"])
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
            cor_fundo = BRANCO
            if casa == 0:
                x_nota = OFFSET_X - 40 
            else:
                x_nota = OFFSET_X + (casa * ESPACO_CASAS) - (ESPACO_CASAS / 2)

            if nota_calculada == tom_atual:
                cor_fundo = CORES_TONICA[indice_cor_tonica]
            elif nota_calculada == escalas.obter_terca(tom_atual): # Você precisará criar essa função
                cor_fundo = CORES_TONICA[indice_cor_terca]
            elif nota_calculada == escalas.obter_quinta(tom_atual): # E essa também
                cor_fundo = CORES_TONICA[indice_cor_quinta]

            pygame.draw.circle(tela, cor_fundo, (int(x_nota), int(y)), raio_circulo)
            pygame.draw.circle(tela, PRETO, (int(x_nota), int(y)), raio_circulo, 2)
            
            txt_nota = fonte_notas_pequena.render(nota_calculada, True, PRETO)
            txt_x = x_nota - (txt_nota.get_width() / 2)
            txt_y = y - (txt_nota.get_height() / 2)
            tela.blit(txt_nota, (txt_x, txt_y))

def desenhar_painel_lateral():
    global rect_btn_tom, rects_notas_dropdown
    global rects_cores_tonica, rects_cores_terca, rects_cores_quinta

    # 1. Afinação (Igual)
    info = lista_afinacoes[indice_afinacao]["nome"]
    tela.blit(fonte_ui.render(f"Afinação: {info}", True, BRANCO), (X_PAINEL, Y_PAINEL - 40))
    pygame.draw.rect(tela, AZUL_BOTAO, btn_up, border_radius=5)
    tela.blit(fonte_ui.render("^", True, BRANCO), (btn_up.centerx - 5, btn_up.centery - 10))
    pygame.draw.rect(tela, AZUL_BOTAO, btn_down, border_radius=5)
    tela.blit(fonte_ui.render("v", True, BRANCO), (btn_down.centerx - 5, btn_down.centery - 10))

    # --- SELEÇÃO DE CORES (TÔNICA, TERÇA, QUINTA) ---
    y_base_cores = Y_PAINEL + 120
    categorias = [
        {"nome": "Tônica", "indice": indice_cor_tonica, "lista": rects_cores_tonica},
        {"nome": "Terça",  "indice": indice_cor_terca,  "lista": rects_cores_terca},
        {"nome": "Quinta", "indice": indice_cor_quinta, "lista": rects_cores_quinta}
    ]

    for j, cat in enumerate(categorias):
        y_linha = y_base_cores + (j * 40)
        tela.blit(fonte_ui.render(cat["nome"] + ":", True, BRANCO), (X_PAINEL, y_linha))
        
        cat["lista"].clear()
        for i, cor in enumerate(CORES_TONICA):
            bx = X_PAINEL + 75 + (i * 24)
            by = y_linha + 10
            raio = 10
            
            pygame.draw.circle(tela, cor, (bx, by), raio)
            if i == cat["indice"]:
                pygame.draw.circle(tela, BRANCO, (bx, by), raio + 3, 2)
            else:
                pygame.draw.circle(tela, PRETO, (bx, by), raio, 1)

            cat["lista"].append({'rect': pygame.Rect(bx-raio, by-raio, raio*2, raio*2), 'indice': i})

    # 2. Seleção de Tom (Desci um pouco para não bater nas cores)
    y_tom_base = y_base_cores + 130
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
    # Adicionamos as novas variáveis de cor como globais aqui!
    global indice_afinacao, aba_atual, memoria_sub_abas
    global tom_atual, indice_cor_tonica, indice_cor_terca, indice_cor_quinta
    global dropdown_tom_aberto, NUM_CASAS

    dicionario_escalas = {
        'maior': lista_modulos_maior,
        'menor': lista_modulos_menor,
        'penta': lista_modulos_penta,
        'blues': lista_modulos_blues,
        'modos': lista_modulos_modos, 
        'triades_maior': lista_modulos_triades_maior,
        'triades_menor': lista_modulos_triades_menor,
    }

    rodando = True
    
    while rodando:
        
        pos_mouse = pygame.mouse.get_pos()
        meu_metronomo.processar_logica(pos_mouse)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            
            if evento.type == pygame.KEYDOWN:
                meu_metronomo.tratar_teclado(evento)
                if evento.key == pygame.K_ESCAPE:
                    rodando = False

            if evento.type == pygame.MOUSEBUTTONDOWN:
                clicou_em_algo_do_dropdown = False
                esta_na_config = (aba_atual == 3 and memoria_sub_abas[3] == 3)
                if meu_metronomo.tratar_clique(evento.pos, esta_na_config):
                    continue # Se o clique foi no metrônomo, não faz mais nada neste frame
                # 1. Lógica de Casas
                if btn_menos_casa.collidepoint(evento.pos):
                    if NUM_CASAS > 12:
                        NUM_CASAS -= 1
                        recriar_modulos_escala()
                        continue
                if aba_atual == 3 and memoria_sub_abas[3] == 3:
                    if meu_metronomo.tratar_clique(evento.pos):
                        continue
                if btn_mais_casa.collidepoint(evento.pos):
                    if NUM_CASAS < 24:
                        NUM_CASAS += 1
                        recriar_modulos_escala()
                        continue

                # 2. Gerenciador de Escalas/Acordes (Arrastar)
                if gerenciador_interface.tratar_cliques_escalas(
                    evento.pos, aba_atual, memoria_sub_abas[aba_atual], 
                    dicionario_escalas, rect_braco_colisao
                ):
                    continue

                # 3. Dropdown de Tom
                if dropdown_tom_aberto:
                    for item in rects_notas_dropdown:
                        if item['rect'].collidepoint(evento.pos):
                            tom_atual = item['nota']       
                            dropdown_tom_aberto = False    
                            clicou_em_algo_do_dropdown = True
                            break

                if not clicou_em_algo_do_dropdown and rect_btn_tom.collidepoint(evento.pos):
                    dropdown_tom_aberto = not dropdown_tom_aberto
                    clicou_em_algo_do_dropdown = True

                # --- 4. SELEÇÃO DE CORES (CORRIGIDO) ---
                # Verifica Tônica
                for item in rects_cores_tonica:
                    if item['rect'].collidepoint(evento.pos):
                        indice_cor_tonica = item['indice']
                        clicou_em_algo_do_dropdown = True

                # Verifica Terça
                for item in rects_cores_terca:
                    if item['rect'].collidepoint(evento.pos):
                        indice_cor_terca = item['indice']
                        clicou_em_algo_do_dropdown = True

                # Verifica Quinta
                for item in rects_cores_quinta:
                    if item['rect'].collidepoint(evento.pos):
                        indice_cor_quinta = item['indice']
                        clicou_em_algo_do_dropdown = True

                if not clicou_em_algo_do_dropdown and dropdown_tom_aberto:
                    dropdown_tom_aberto = False

                # 5. Afinação
                if btn_up.collidepoint(evento.pos):
                    indice_afinacao = (indice_afinacao - 1) % len(lista_afinacoes)
                    recriar_modulos_escala() 
                if btn_down.collidepoint(evento.pos):
                    indice_afinacao = (indice_afinacao + 1) % len(lista_afinacoes)
                    recriar_modulos_escala()
                
                # 6. Abas
                for i, rect in enumerate(rects_abas):
                    if rect.collidepoint(evento.pos):
                        aba_atual = i
                for j, rect in enumerate(rects_sub_abas):
                    if rect.collidepoint(evento.pos):
                        memoria_sub_abas[aba_atual] = j

        
        # Renderização
        desenhar_guitarra()
        desenhar_painel_superior() 
        desenhar_painel_inferior()
        
        # 1. Desenha as Escalas e Acordes apenas nas abas corretas (0 e 1)
        if aba_atual in [0, 1]:
            gerenciador_interface.desenhar_escalas_ativas(
                tela, pos_mouse, aba_atual, memoria_sub_abas[aba_atual], 
                dicionario_escalas, rect_braco_colisao
            )
            
        # 2. Desenha a interface do Metrônomo (Slider, botões, input) na Aba de Configurações
        if aba_atual == 3 and memoria_sub_abas[3] == 3:
            # É ESSA FUNÇÃO QUE FALTAVA PARA DESENHAR OS BOTÕES:
            meu_metronomo.desenhar_config(tela, fonte_ui)
        
        meu_metronomo.desenhar_mini_metronomo(tela, LARGURA, ALTURA, fonte_ui)
        
        # 4. Painel Lateral sempre no topo
        desenhar_painel_lateral() 
        
        
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()