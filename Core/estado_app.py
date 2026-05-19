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
        
        # Sessão do Usuário
        self.usuario_id_logado = None
        self.email_usuario = ""
        
        self.drag_ativado = False 
        self.rect_btn_pin = pygame.Rect(0, 0, 40, 40) 
        self.tela_jogo_ativa = False
        self.solicitou_saida = False
        self.idioma = 'pt' # Idioma da interface
        
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
        self.afinador_persistencia = 1000 # Milissegundos para a nota ficar na tela
        self.afinador_threshold = 0.3 # Limiar de detecção (mais baixo = mais sensível)
        self.tempo_ultima_nota = 0
        self.historico_freqs = [] 
        self.indice_cor_tonica = 0  
        self.indice_cor_terca = 0   
        self.indice_cor_quinta = 0  
        self.dropdown_tom_aberto = False
        self.NUM_CASAS = 18 

        # Geometria Base e Scroll (Layout Profissional Centralizado)
        self.NUM_CORDAS = 7
        self.LARGURA_BRACO = max(800, largura_tela - 400) 
        self.ALTURA_BRACO = 280 
        self.scroll_y = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        self.max_scroll = {0: 1000, 1: 800, 2: 400, 3: 500, 4: 500}
        
        self.atualizar_medidas()

        # Posicionamento Estratégico (Layout Dashboard Profissional)
        centro_x_global = largura_tela // 2
        
        # 1. Controles Superiores (Docked Top - Centralizado)
        largura_topo = 620
        self.dragger_controles_topo = ElementoArrastavel(centro_x_global - (largura_topo // 2), 40, largura_topo, 40)

        # 2. Braço da Guitarra (Foco Central)
        # Deixamos um espaço maior no topo para "respirar"
        self.dragger_guitarra = ElementoArrastavel(centro_x_global - (self.LARGURA_BRACO // 2), 120, self.LARGURA_BRACO, self.ALTURA_BRACO)
        
        # 3. Painel de Acordes (Abaixo do Braço - Alinhado)
        self.LARGURA_ACORDES = 620 
        self.ALTURA_ACORDES = 120 
        self.dragger_acordes = ElementoArrastavel(centro_x_global - (self.LARGURA_ACORDES // 2), self.dragger_guitarra.y + self.ALTURA_BRACO + 40, self.LARGURA_ACORDES, self.ALTURA_ACORDES)

        # 4. Nota Atual e Visual Feedback (Sidebar Esquerda)
        self.LARGURA_BLOCO_NOTA = 280
        self.ALTURA_BLOCO_NOTA = 220
        # Posicionado à esquerda do braço para não poluir o centro
        self.dragger_nota_atual = ElementoArrastavel(30, 120, self.LARGURA_BLOCO_NOTA, self.ALTURA_BLOCO_NOTA)

        # 5. Metrônomo (Sidebar Direita ou Abaixo dos Acordes)
        self.LARGURA_METRONOMO = 240
        self.ALTURA_METRONOMO = 100
        # Colocamos ao lado dos acordes para economizar espaço vertical
        x_metronomo = self.dragger_acordes.x + self.LARGURA_ACORDES + 30
        if x_metronomo + self.LARGURA_METRONOMO > largura_tela: # Se não couber, coloca embaixo
             x_metronomo = centro_x_global - (self.LARGURA_METRONOMO // 2)
             y_metronomo = self.dragger_acordes.y + self.ALTURA_ACORDES + 30
        else:
             y_metronomo = self.dragger_acordes.y + (self.ALTURA_ACORDES // 2) - (self.ALTURA_METRONOMO // 2)
        
        self.dragger_metronomo = ElementoArrastavel(x_metronomo, y_metronomo, self.LARGURA_METRONOMO, self.ALTURA_METRONOMO)

        # 6. Painel de Cores (Canto Inferior Esquerdo)
        # Inicializamos aqui para garantir persistência de posição
        self.dragger_cores = ElementoArrastavel(30, altura_tela - 220, 180, 150)

        # 7. Painel Inferior de Ferramentas (Fixed Bottom - Docked)
        y_inferior_inicial = altura_tela - 65 
        self.dragger_painel_inferior = ElementoArrastavel(centro_x_global - (self.LARGURA_BRACO // 2), y_inferior_inicial, self.LARGURA_BRACO, 45)
        self.Y_AREA_DESENHO = self.dragger_painel_inferior.y - 310 
        
        self.nota_atual_detectada = "--" 
        self.nota_selecionada_bloco = "C"
        self.rects_notas_selecao = [] 
        self.instrumento = 'guitarra'

        # Painéis Inferiores Expansíveis (5 Abas)
        # Mantemos as chaves em PT para que o tradutor dinâmico as reconheça sempre
        self.secoes_inferiores = [
            {"titulo": "ESCALAS", "expandido": False, "conteudo": "escalas", "memoria_sub_aba": 0, "sub_abas": ["Maior", "Menor", "Penta Maior", "Penta Menor", "Blues", "Modos", "Harmônica", "Melodica", "Exóticas"]},
            {"titulo": "ACORDES", "expandido": False, "conteudo": "acordes", "memoria_sub_aba": 0, "sub_abas": ["CAGED", "Tríades Maiores", "Tríades Menores", "Sétimas", "Power Chords"]},
            {"titulo": "ANÁLISE DE IA", "expandido": False, "conteudo": "analise_ia", "memoria_sub_aba": 0, "sub_abas": ["Afinador / IA", "JOGOS"]},
            {"titulo": "ESTUDOS", "expandido": False, "conteudo": "estudos", "memoria_sub_aba": 0, "sub_abas": ["Notas", "Escalas", "Ritmo", "Acordes"]},
            {"titulo": "CONFIGURAÇÃO", "expandido": False, "conteudo": "configuracao", "memoria_sub_aba": 0, "sub_abas": ["Cores da Interface", "Configurações Globais"]}
        ]

    def atualizar_medidas(self):
        self.ESPACO_CORDAS = self.ALTURA_BRACO / (self.NUM_CORDAS - 1)
        self.ESPACO_CASAS = self.LARGURA_BRACO / self.NUM_CASAS
        
        if hasattr(self, 'dragger_guitarra'):
            self.dragger_guitarra.atualizar_dimensoes(self.LARGURA_BRACO, self.ALTURA_BRACO)