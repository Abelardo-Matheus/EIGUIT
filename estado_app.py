# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# =============================================================================

import pygame
from DragDrop.elemento_arrastavel import ElementoArrastavel

class EstadoGlobal:
    def __init__(self, largura_tela, altura_tela):
        self.LARGURA_TELA = largura_tela
        self.ALTURA_TELA = altura_tela 
        
        self.drag_ativado = False 
        self.rect_btn_pin = pygame.Rect(0, 0, 40, 40) 
        self.tela_jogo_ativa = False
        self.solicitou_saida = False
        
        # Variáveis de Controle de Estudos
        self.tela_estudo_ativa = False
        self.estudo_ativo = ""
        self.botoes_estudo = {} # Guarda a posição de colisão dos botões gerados

        
        # Dados Musicais e IA
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

        # Geometria Base e Scroll (Atualizado para 5 abas)
        self.NUM_CORDAS = 7
        self.LARGURA_BRACO = max(800, largura_tela - 350) 
        self.ALTURA_BRACO = 300 
        self.scroll_y = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        self.max_scroll = {0: 600, 1: 0, 2: 400, 3: 500, 4: 500}
        
        self.atualizar_medidas()

        # Criação dos Elementos Arrastáveis (Draggers) Centralizados
        centro_x_braco = (largura_tela - self.LARGURA_BRACO) // 2

        self.dragger_guitarra = ElementoArrastavel(centro_x_braco, 100, self.LARGURA_BRACO, self.ALTURA_BRACO)
        
        self.LARGURA_ACORDES = 580 
        self.ALTURA_ACORDES = 110 
        centro_x_acordes = (largura_tela - self.LARGURA_ACORDES) // 2
        self.dragger_acordes = ElementoArrastavel(centro_x_acordes, self.dragger_guitarra.y + self.ALTURA_BRACO + 40, self.LARGURA_ACORDES, self.ALTURA_ACORDES)

        self.LARGURA_METRONOMO = 250
        self.ALTURA_METRONOMO = 80
        centro_x_metronomo = (largura_tela - self.LARGURA_METRONOMO) // 2
        self.dragger_metronomo = ElementoArrastavel(centro_x_metronomo, self.dragger_acordes.y + self.ALTURA_ACORDES + 40, self.LARGURA_METRONOMO, self.ALTURA_METRONOMO)

        largura_topo = 580
        centro_x_topo = (largura_tela - largura_topo) // 2
        self.dragger_controles_topo = ElementoArrastavel(centro_x_topo, 30, largura_topo, 40)
        
        y_inferior_inicial = altura_tela - 60 
        self.dragger_painel_inferior = ElementoArrastavel(centro_x_braco, y_inferior_inicial, self.LARGURA_BRACO, 40)
        self.Y_AREA_DESENHO = self.dragger_painel_inferior.y - 310 

        # Painéis Inferiores Expansíveis (5 Abas)
        self.secoes_inferiores = [
            {"titulo": "ESCALAS", "expandido": False, "conteudo": "escalas", "memoria_sub_aba": 0, "sub_abas": ["Maior", "Menor", "Penta", "Blues", "Modos"]},
            {"titulo": "ACORDES", "expandido": False, "conteudo": "acordes", "memoria_sub_aba": 0, "sub_abas": ["CAGED", "Tríades Maiores", "Tríades Menores"]},
            {"titulo": "ANÁLISE DE IA", "expandido": False, "conteudo": "analise_ia", "memoria_sub_aba": 0, "sub_abas": ["Afinador / IA", "Treino de Ritmo", "JOGOS"]},
            {"titulo": "ESTUDOS", "expandido": False, "conteudo": "estudos", "memoria_sub_aba": 0, "sub_abas": ["Notas", "Escalas", "Ritmo", "Acordes"]},
            {"titulo": "CONFIGURAÇÃO", "expandido": False, "conteudo": "configuracao", "memoria_sub_aba": 0, "sub_abas": ["Cores da Interface", "Configurações Globais"]}
        ]

    def atualizar_medidas(self):
        self.ESPACO_CORDAS = self.ALTURA_BRACO / (self.NUM_CORDAS - 1)
        self.ESPACO_CASAS = self.LARGURA_BRACO / self.NUM_CASAS
        
        if hasattr(self, 'dragger_guitarra'):
            self.dragger_guitarra.atualizar_dimensoes(self.LARGURA_BRACO, self.ALTURA_BRACO)