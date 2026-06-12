import pygame
from DragDrop.elemento_arrastavel import ElementoArrastavel
from Interface.Componentes.config_componentes import LARGURA_TOOLBAR_PADRAO, LARGURA_INFERIOR_PADRAO, TOPBAR_Y_INICIAL, TOPBAR_ALTURA, GUITAR_Y_INICIAL, GUITAR_ALTURA_BRACO, CHORD_ALTURA, CHORD_OFFSET_Y_BRACO, SIDEBAR_NOTA_LARGURA, SIDEBAR_NOTA_ALTURA, SIDEBAR_NOTA_OFFSET_X, SIDEBAR_NOTA_OFFSET_Y_BOTTOM, METRO_LARGURA, METRO_ALTURA, METRO_OFFSET_X, METRO_OFFSET_Y_ESTUDO, CORES_LARGURA, CORES_ALTURA, CORES_OFFSET_X, CORES_OFFSET_Y_BOTTOM, BOTTOM_Y_OFFSET_TELA, BOTTOM_Y_AREA_DESENHO_OFFSET
from Modulos.modulo_songsterr import SongsterrAPI

class EstadoGlobal:
    """
        Como funciona: Armazena variáveis de controle, configurações de interface, resultados de busca e estados de componentes arrastáveis.
        Para que serve: Atuar como a 'Fonte da Verdade' (Single Source of Truth) para todo o estado da aplicação.
        Onde é usada: Instanciado no início do main.py e passado para quase todos os módulos de interface e lógica.
    """

    def __init__(self, largura_tela, altura_tela):
        """
            Como funciona: Inicializa os atributos e o estado inicial da instância.
            Para que serve: Prepara o objeto para ser utilizado no ciclo de vida da aplicação.
            Onde é usada: Chamado a partir do módulo ou classe base de 'estado_app'.
        """
        self.LARGURA_TELA = largura_tela
        self.ALTURA_TELA = altura_tela
        self.songsterr = SongsterrAPI()
        self.query_songsterr = ''
        self.resultados_songsterr = []
        self.songsterr_search_active = False
        self.lista_tabs = []
        self.favoritos_songsterr = []
        self.musicas_locais = []
        self.sub_memoria_musicas = 0
        self.rect_btn_add_midi = pygame.Rect(0, 0, 0, 0)
        self.usuario_id_logado = None
        self.email_usuario = ''
        self.drag_ativado = False
        self.rect_btn_pin = pygame.Rect(0, 0, 40, 40)
        self.tela_jogo_ativa = False
        self.solicitou_saida = False
        self.idioma = 'pt'
        self.tela_estudo_ativa = False
        self.estudo_ativo = ''
        self.botoes_estudo = {}
        self.notas_base = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.tonica_campo = 'C'
        self.indice_escala_campo = 0
        self.indice_afinacao = 0
        self.tom_atual = 'C'
        self.freq_detectada = ''
        self.afinador_suavizacao = 5
        self.afinador_sensibilidade = 0.5
        self.afinador_persistencia = 1000
        self.afinador_threshold = 0.3
        self.tempo_ultima_nota = 0
        self.historico_freqs = []
        self.indice_cor_tonica = 0
        self.indice_cor_terca = 0
        self.indice_cor_quinta = 0
        self.dropdown_tom_aberto = False
        self.NUM_CASAS = 18
        self.NUM_CORDAS = 7
        self.LARGURA_BRACO = 1000 # Fixado para bater com o padrão de 18 casas visual
        self.ALTURA_BRACO = GUITAR_ALTURA_BRACO
        self.scroll_y = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        self.max_scroll = {0: 1000, 1: 800, 2: 400, 3: 500, 4: 500}
        
        # --- Novos padrões centralizados e organizados (Sincronizados com modulo_perfil) ---
        gap_horizontal = 50
        largura_total_pequenos = 240 + 180 + 280 + (gap_horizontal * 2)
        x_inicio_pequenos = (largura_tela - largura_total_pequenos) // 2
        
        # Medidas de referência
        self.LARGURA_ACORDES = 620
        self.ALTURA_ACORDES = CHORD_ALTURA
        self.LARGURA_BLOCO_NOTA = SIDEBAR_NOTA_LARGURA
        self.ALTURA_BLOCO_NOTA = SIDEBAR_NOTA_ALTURA
        self.LARGURA_METRONOMO = METRO_LARGURA
        self.ALTURA_METRONOMO = METRO_ALTURA
        
        # Grandes
        self.dragger_controles_topo = ElementoArrastavel((largura_tela - 700) // 2, 20, 700, TOPBAR_ALTURA)
        self.dragger_guitarra = ElementoArrastavel((largura_tela - 1000) // 2, 80, self.LARGURA_BRACO, self.ALTURA_BRACO)
        self.dragger_acordes = ElementoArrastavel((largura_tela - 620) // 2, 380, self.LARGURA_ACORDES, self.ALTURA_ACORDES)
        self.dragger_painel_inferior = ElementoArrastavel((largura_tela - 1200) // 2, altura_tela - 85, 1200, 45)
        
        # Pequenos
        self.dragger_metronomo = ElementoArrastavel(x_inicio_pequenos, 520, self.LARGURA_METRONOMO, self.ALTURA_METRONOMO)
        self.dragger_cores = ElementoArrastavel(x_inicio_pequenos + 240 + gap_horizontal, 520, 180, 150)
        self.dragger_nota_atual = ElementoArrastavel(x_inicio_pequenos + 240 + 180 + (gap_horizontal * 2), 520, self.LARGURA_BLOCO_NOTA, self.ALTURA_BLOCO_NOTA)

        self.atualizar_medidas()

        self.Y_AREA_DESENHO = self.dragger_painel_inferior.y - BOTTOM_Y_AREA_DESENHO_OFFSET
        self.nota_atual_detectada = '--'
        self.nota_selecionada_bloco = 'C'
        self.rects_notas_selecao = []
        self.instrumento = 'guitarra'
        self.secoes_inferiores = [{'titulo': 'ESCALAS', 'expandido': False, 'conteudo': 'escalas', 'memoria_sub_aba': 0, 'sub_abas': ['Maior', 'Menor', 'Penta Maior', 'Penta Menor', 'Blues', 'Modos', 'Harmônica', 'Melodica', 'Exóticas']}, {'titulo': 'ACORDES', 'expandido': False, 'conteudo': 'acordes', 'memoria_sub_aba': 0, 'sub_abas': ['CAGED', 'Tríades Maiores', 'Tríades Menores', 'Sétimas', 'Power Chords']}, {'titulo': 'ANÁLISE DE IA', 'expandido': False, 'conteudo': 'analise_ia', 'memoria_sub_aba': 0, 'sub_abas': ['Afinador / IA', 'JOGOS']}, {'titulo': 'ESTUDOS', 'expandido': False, 'conteudo': 'estudos', 'memoria_sub_aba': 0, 'sub_abas': ['Notas', 'Escalas', 'Acordes', 'Teoria']}, {'titulo': 'MÚSICAS', 'expandido': False, 'conteudo': 'musicas', 'memoria_sub_aba': 0, 'sub_abas': ['Songster', 'Minhas Músicas', 'Criação Musical']}, {'titulo': 'CONFIGURAÇÃO', 'expandido': False, 'conteudo': 'configuracao', 'memoria_sub_aba': 0, 'sub_abas': ['Cores da Interface', 'Configurações Globais']}]
        
        # --- Criador de Tablaturas ---
        self.tela_criacao_tab_ativa = False
        self.tab_nome = "Nova Música"
        self.tab_bpm = 120
        self.tab_reproduzindo = False
        self.tab_coluna_atual = 0
        self.tab_dados = [['-' for _ in range(6)] for _ in range(100)] # 100 colunas iniciais
        self.tab_cursor_col = 0
        self.tab_cursor_corda = 0
        self.tab_scroll_x = 0
        self.tempo_ultimo_tick = 0
        self.guias_x = []
        self.guias_y = []

    def atualizar_medidas(self):
        """
            Como funciona: Recalcula dimensões, estados e processa alterações temporais.
            Para que serve: Garante que os dados e a interface reflitam as últimas mudanças.
            Onde é usada: Chamado a partir do módulo ou classe base de 'estado_app'.
        """
        self.ESPACO_CORDAS = self.ALTURA_BRACO / (self.NUM_CORDAS - 1)
        self.ESPACO_CASAS = self.LARGURA_BRACO / self.NUM_CASAS
        if hasattr(self, 'dragger_guitarra'):
            self.dragger_guitarra.atualizar_dimensoes(self.LARGURA_BRACO, self.ALTURA_BRACO)