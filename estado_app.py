# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================
import pygame
from DragDrop.elemento_arrastavel import ElementoArrastavel

class EstadoGlobal:
    def __init__(self, largura_tela, altura_tela):

        self.ALTURA_TELA = altura_tela 
        
        # ==========================================
        # MODO DE EDIÇÃO (NOVO BOTÃO ALFINETE)
        # ==========================================
        self.drag_ativado = False 
        self.rect_btn_pin = pygame.Rect(0, 0, 40, 40) 

        # Controle de tela cheia para jogos
        self.tela_jogo_ativa = False

        # ==========================================
        # DADOS MUSICAIS E IA
        # ==========================================
        self.notas_base = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.tonica_campo = 'C'  
        self.indice_escala_campo = 0
        self.indice_afinacao = 0
        self.tom_atual = 'C'
        self.freq_detectada = ""
        self.afinador_suavizacao = 5 
        self.afinador_sensibilidade = 0.5 
        self.historico_freqs = [] 
        self.indice_cor_tonica = 0  
        self.indice_cor_terca = 0   
        self.indice_cor_quinta = 0  
        self.dropdown_tom_aberto = False
        self.NUM_CASAS = 18 
        self.solicitou_saida = False

        # --- GEOMETRIA BASE ---
        self.NUM_CORDAS = 7
        self.LARGURA_BRACO = largura_tela - 350 
        self.ALTURA_BRACO = 300 
        self.scroll_y = {0: 0, 1: 0, 2: 0, 3: 0}
        self.max_scroll = {0: 600, 1: 0, 2: 400, 3: 500}
        
        self.atualizar_medidas()

        # ==========================================
        # 1. CRIAR OS DRAGGERS INDEPENDENTES (ORDEM IMPORTA!)
        # ==========================================
        centro_x_braco = (largura_tela - self.LARGURA_BRACO) // 2

        # Guitarra
        self.dragger_guitarra = ElementoArrastavel(x_inicial=centro_x_braco, y_inicial=100, largura=self.LARGURA_BRACO, altura=self.ALTURA_BRACO)
        
        # Acordes (Criado antes do metrônomo para evitar o erro de atributo)
        self.LARGURA_ACORDES = 580 
        self.ALTURA_ACORDES = 110 
        centro_x_acordes = (largura_tela - self.LARGURA_ACORDES) // 2
        self.dragger_acordes = ElementoArrastavel(x_inicial=centro_x_acordes, y_inicial=480, largura=self.LARGURA_ACORDES, altura=self.ALTURA_ACORDES)

        # Metrônomo (Agora ele pode usar self.dragger_acordes.y com segurança)
        self.LARGURA_METRONOMO = 250
        self.ALTURA_METRONOMO = 80
        centro_x_metronomo = (largura_tela - self.LARGURA_METRONOMO) // 2
        y_inicial_metronomo = self.dragger_acordes.y + self.ALTURA_ACORDES + 90
        self.dragger_metronomo = ElementoArrastavel(x_inicial=centro_x_metronomo, y_inicial=y_inicial_metronomo, largura=self.LARGURA_METRONOMO, altura=self.ALTURA_METRONOMO)

        # Controles Topo
        largura_topo = 780
        centro_x_topo = (largura_tela - largura_topo) // 2
        self.dragger_controles_topo = ElementoArrastavel(x_inicial=centro_x_topo, y_inicial=30, largura=largura_topo, altura=40)
        
        # Painel Inferior
        y_inferior_inicial = altura_tela - 60 
        self.dragger_painel_inferior = ElementoArrastavel(x_inicial=centro_x_braco, y_inicial=y_inferior_inicial, largura=self.LARGURA_BRACO, altura=40)

        # Define a área de desenho do conteúdo baseada na posição do painel inferior
        self.Y_AREA_DESENHO = self.dragger_painel_inferior.y - 350 + 40 

        # ==========================================
        # 2. PAINÉIS INFERIORES EXPANSÍVEIS
        # ==========================================
        self.secoes_inferiores = [
            {
                "titulo": "ESCALAS", "expandido": False, "conteudo": "escalas", "memoria_sub_aba": 0,
                "sub_abas": ["Maior", "Menor", "Penta", "Blues", "Modos"]
            },
            {
                "titulo": "ACORDES", "expandido": False, "conteudo": "acordes", "memoria_sub_aba": 0,
                "sub_abas": ["CAGED", "Tríades Maiores", "Tríades Menores"]
            },
            {
                "titulo": "ANÁLISE DE IA", "expandido": False, "conteudo": "analise_ia", "memoria_sub_aba": 0,
                "sub_abas": ["Afinador / IA", "Treino de Ritmo", "JOGOS"] # <--- Adicionado JOGOS
            },
            {
                "titulo": "CONFIGURAÇÃO", "expandido": False, "conteudo": "configuracao", "memoria_sub_aba": 0,
                "sub_abas": ["Cores da Interface", "Configurações Globais"]
            }
        ]

    def atualizar_medidas(self):
        self.ESPACO_CORDAS = self.ALTURA_BRACO / (self.NUM_CORDAS - 1)
        self.ESPACO_CASAS = self.LARGURA_BRACO / self.NUM_CASAS
        
        if hasattr(self, 'dragger_guitarra'):
            self.dragger_guitarra.atualizar_dimensoes(self.LARGURA_BRACO, self.ALTURA_BRACO)