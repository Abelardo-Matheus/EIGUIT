import pygame



class EstadoGlobal:
    def __init__(self, largura_tela, altura_tela):

        # ==========================================
        # DADOS DO CAMPO HARMÔNICO (NOVA ABA)
        # ==========================================
        self.notas_base = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.tonica_campo = 'C'  # Tônica padrão
        self.indice_escala_campo = 0
        
        # O "DNA" de todas as escalas possíveis (Modos Gregos)
        self.escalas_campo = [
            {"nome": "Maior (Jônio)", "int": [0, 2, 4, 5, 7, 9, 11], "romanos": ["I", "ii", "iii", "IV", "V", "vi", "vii°"], "qualidades": ["", "m", "m", "", "", "m", "dim"]},
            {"nome": "Menor (Eólio)", "int": [0, 2, 3, 5, 7, 8, 10], "romanos": ["i", "ii°", "III", "iv", "v", "VI", "VII"], "qualidades": ["m", "dim", "", "m", "m", "", ""]},
            {"nome": "Dórico", "int": [0, 2, 3, 5, 7, 9, 10], "romanos": ["i", "ii", "III", "IV", "v", "vi°", "VII"], "qualidades": ["m", "m", "", "", "m", "dim", ""]},
            {"nome": "Frígio", "int": [0, 1, 3, 5, 7, 8, 10], "romanos": ["i", "II", "III", "iv", "v°", "VI", "vii"], "qualidades": ["m", "", "", "m", "dim", "", "m"]},
            {"nome": "Lídio", "int": [0, 2, 4, 6, 7, 9, 11], "romanos": ["I", "II", "iii", "iv°", "V", "vi", "vii"], "qualidades": ["", "", "m", "dim", "", "m", "m"]},
            {"nome": "Mixolídio", "int": [0, 2, 4, 5, 7, 9, 10], "romanos": ["I", "ii", "iii°", "IV", "v", "vi", "VII"], "qualidades": ["", "m", "dim", "", "m", "m", ""]},
            {"nome": "Lócrio", "int": [0, 1, 3, 5, 6, 8, 10], "romanos": ["i°", "II", "iii", "iv", "V", "VI", "vii"], "qualidades": ["dim", "", "m", "m", "", "", "m"]},
        ]
        
        # Retângulos de colisão para as setinhas (salvamos aqui para o controlador de eventos achar)
        self.rect_tonica_esq = pygame.Rect(0,0,0,0)
        self.rect_tonica_dir = pygame.Rect(0,0,0,0)
        self.rect_escala_esq = pygame.Rect(0,0,0,0)
        self.rect_escala_dir = pygame.Rect(0,0,0,0)

        
        self.indice_afinacao = 0
        self.tom_atual = 'C'
        self.freq_detectada = 0.0 

        # --- CALIBRAÇÃO DO AFINADOR ---
        self.afinador_suavizacao = 5 # 1 (Nervoso/Rápido) a 10 (Lento/Estável)
        self.afinador_sensibilidade = 0.5 # 0.1 (Fácil de detectar) a 0.9 (Rigoroso)
        self.historico_freqs = [] # Guarda as últimas frequências para tirar a média

        self.indice_cor_tonica = 0  
        self.indice_cor_terca = 0   
        self.indice_cor_quinta = 0  
        self.dropdown_tom_aberto = False
        
        self.aba_atual = 0
        self.memoria_sub_abas = [0, 0, 0, 0] 
        self.NUM_CASAS = 18 
        self.solicitou_saida = False

        # --- GEOMETRIA E POSIÇÕES ---
        self.OFFSET_X = 100 
        self.OFFSET_Y = 90 
        self.NUM_CORDAS = 7
        self.LARGURA_BRACO = largura_tela - 350 
        self.ALTURA_BRACO = 300 
        
        self.X_PAINEL = largura_tela - 220
        self.Y_PAINEL = self.OFFSET_Y + 50
        
        # --- SCROLL DAS ESCALAS ---
        self.scroll_y = {0: 0, 1: 0, 2: 0, 3: 0}
        # Define o limite máximo que cada aba pode descer (Ajuste esses valores como quiser!)
        self.max_scroll = {0: 600, 1: 0, 2: 400, 3: 500}
        # === NOVA POSIÇÃO INDEPENDENTE PARA O CAMPO HARMÔNICO ===
        # Fica 60 pixels abaixo do braço da guitarra
        self.Y_CAMPO_HARMONICO = self.OFFSET_Y + self.ALTURA_BRACO + 70
        
        # A Caixa de baixo agora tem o próprio controle (aumente esse 250 se quiser ela mais pra baixo)
        self.Y_CAIXA = self.OFFSET_Y + self.ALTURA_BRACO + 250 
        self.ALTURA_CAIXA = altura_tela - self.Y_CAIXA - 50
        
        # --- MEMÓRIA DOS BOTÕES LATERAIS ---
        self.btn_up = pygame.Rect(self.X_PAINEL + 50, self.Y_PAINEL, 40, 40)
        self.btn_down = pygame.Rect(self.X_PAINEL + 50, self.Y_PAINEL + 60, 40, 40)
        self.rect_btn_tom = pygame.Rect(0, 0, 0, 0)
        self.rects_notas_dropdown = [] 
        self.rects_cores_tonica = []
        self.rects_cores_terca = []
        self.rects_cores_quinta = []
        
        self.atualizar_medidas()

    def atualizar_medidas(self):
        self.ESPACO_CORDAS = self.ALTURA_BRACO / (self.NUM_CORDAS - 1)
        self.ESPACO_CASAS = self.LARGURA_BRACO / self.NUM_CASAS
        self.rect_braco_colisao = pygame.Rect(self.OFFSET_X, self.OFFSET_Y, self.LARGURA_BRACO, self.ALTURA_BRACO)