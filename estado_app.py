import pygame

class EstadoGlobal:
    def __init__(self, largura_tela, altura_tela):
        self.indice_afinacao = 0
        self.tom_atual = 'C'
        self.freq_detectada = 0.0 
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
        self.Y_CAIXA = self.OFFSET_Y + self.ALTURA_BRACO + 80
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