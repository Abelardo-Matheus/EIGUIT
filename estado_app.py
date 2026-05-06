# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 [SEU NOME]
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================
import pygame



class EstadoGlobal:
    def __init__(self, largura_tela, altura_tela):

        # ==========================================
        # DADOS DO CAMPO HARMÔNICO (NOVA ABA)
        # ==========================================
        self.notas_base = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.tonica_campo = 'C'  # Tônica padrão
        self.indice_escala_campo = 0
        
        

        
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
    
    def calcular_notas_acorde_selecionado(self):
        """Descobre a Tônica, Terça e Quinta do acorde que o usuário clicou."""
        escala_atual = self.escalas_campo[self.indice_escala_campo]
        idx_tonica_escala = self.notas_base.index(self.tonica_campo)

        # 1. Acha a raiz do acorde clicado
        idx_raiz_acorde = (idx_tonica_escala + escala_atual["int"][self.indice_acorde_selecionado]) % 12
        qualidade = escala_atual["qualidades"][self.indice_acorde_selecionado]

        # 2. Calcula os intervalos baseados na qualidade (Maior, Menor, Diminuto)
        if qualidade == "": # Acorde Maior
            idx_terca = (idx_raiz_acorde + 4) % 12
            idx_quinta = (idx_raiz_acorde + 7) % 12
        elif qualidade == "m": # Acorde Menor
            idx_terca = (idx_raiz_acorde + 3) % 12
            idx_quinta = (idx_raiz_acorde + 7) % 12
        elif qualidade == "dim": # Acorde Diminuto
            idx_terca = (idx_raiz_acorde + 3) % 12
            idx_quinta = (idx_raiz_acorde + 6) % 12

        # 3. Salva a tríade exata
        self.notas_acorde_selecionado = [
            self.notas_base[idx_raiz_acorde],
            self.notas_base[idx_terca],
            self.notas_base[idx_quinta]
        ]