import pygame
from DragDrop.elemento_arrastavel import ElementoArrastavel
from ui.components.config_componentes import LARGURA_TOOLBAR_PADRAO, LARGURA_INFERIOR_PADRAO, TOPBAR_Y_INICIAL, TOPBAR_ALTURA, GUITAR_Y_INICIAL, GUITAR_ALTURA_BRACO, CHORD_ALTURA, CHORD_OFFSET_Y_BRACO, SIDEBAR_NOTA_LARGURA, SIDEBAR_NOTA_ALTURA, SIDEBAR_NOTA_OFFSET_X, SIDEBAR_NOTA_OFFSET_Y_BOTTOM, METRO_LARGURA, METRO_ALTURA, METRO_OFFSET_X, METRO_OFFSET_Y_ESTUDO, CORES_LARGURA, CORES_ALTURA, CORES_OFFSET_X, CORES_OFFSET_Y_BOTTOM, BOTTOM_Y_OFFSET_TELA, BOTTOM_Y_AREA_DESENHO_OFFSET
from core.modulos.modulo_songsterr import SongsterrAPI
from core.modulos.modulo_timbre import BuscaTimbre

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
        # --- Pesquisa de Timbre (sub-aba "Timbre" de MÚSICAS) ---
        self.timbre = BuscaTimbre()
        self.query_timbre = ''
        self.timbre_busca_ativa = False
        self.resultados_timbre = None
        self.rect_busca_timbre = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_timbre = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_timbre_copiar_prompt = pygame.Rect(0, 0, 0, 0)
        self.rects_timbre_pessoas = []
        self.rects_timbre_sites = []
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
        # Portao de ruido em dB: abaixo disso a entrada e ignorada visualmente
        self.afinador_noise_gate = -45.0
        self.nivel_entrada_db = -60.0
        # Slider do painel de audio em arrasto ('threshold', 'noise_gate', ...)
        self.slider_audio_ativo = None
        self.tempo_ultima_nota = 0
        self.historico_freqs = []
        # Cores distintas por padrao: branco, vermelho e verde-agua
        self.indice_cor_tonica = 0
        self.indice_cor_terca = 1
        self.indice_cor_quinta = 2
        # Acordes desenhados sobre o braco principal.
        # acordes_fixados: escolhidos com o botao Fixar, ficam ate serem tirados.
        # acordes_no_braco: os fixados mais a selecao atual do painel.
        self.acordes_fixados = []
        self.acordes_no_braco = []
        self.dropdown_tom_aberto = False
        self.NUM_CASAS = 18
        self.NUM_CORDAS = 7
        self.LARGURA_BRACO = 1713 
        self.ALTURA_BRACO = 393
        self.scroll_y = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        self.max_scroll = {0: 1000, 1: 800, 2: 400, 3: 500, 4: 500}
        
        # Medidas de referência (Extraídas do Setup_Centralizado)
        self.LARGURA_ACORDES = 620
        self.ALTURA_ACORDES = 120
        self.LARGURA_BLOCO_NOTA = 280
        self.ALTURA_BLOCO_NOTA = 220
        self.LARGURA_METRONOMO = 276
        self.ALTURA_METRONOMO = 104
        self.LARGURA_SESSAO = 240
        self.ALTURA_SESSAO = 150
        
        from config.ui_metrics import ALTURA_TOPBAR
        from config.layout_padrao import calcular as calcular_layout_padrao

        alt_viewport = max(600, self.ALTURA_TELA - ALTURA_TOPBAR)

        # Layout de abertura derivado do canvas de design, proporcional a tela.
        layout = calcular_layout_padrao(self.LARGURA_TELA, alt_viewport)

        def _bloco(nome):
            m = layout[nome]
            return ElementoArrastavel(m['x'], m['y'], m['w'], m['h'])

        # O braco define as medidas de casas e cordas, entao vem primeiro
        medidas_braco = layout['dragger_guitarra']
        self.LARGURA_BRACO = medidas_braco['w']
        self.ALTURA_BRACO = medidas_braco['h']
        self.ALTURA_ACORDES = layout['dragger_acordes']['h']

        self.dragger_controles_topo = _bloco('dragger_controles_topo')
        self.dragger_guitarra = _bloco('dragger_guitarra')
        self.dragger_painel_inferior = _bloco('dragger_painel_inferior')
        self.dragger_acordes = _bloco('dragger_acordes')
        self.dragger_metronomo = _bloco('dragger_metronomo')
        self.dragger_cores = _bloco('dragger_cores')
        self.dragger_nota_atual = _bloco('dragger_nota_atual')
        self.dragger_sessao = _bloco('dragger_sessao')
        self.dragger_circulo = _bloco('dragger_circulo')
        self.dragger_historico = _bloco('dragger_historico')
        self.dragger_ideias = _bloco('dragger_ideias')
        self.dragger_drone = _bloco('dragger_drone')
        self.dragger_progressoes = _bloco('dragger_progressoes')
        self.dragger_graus = _bloco('dragger_graus')
        self.dragger_cordas = _bloco('dragger_cordas')
        self.dragger_capo = _bloco('dragger_capo')

        self.atualizar_medidas()

        self.Y_AREA_DESENHO = self.dragger_painel_inferior.y - BOTTOM_Y_AREA_DESENHO_OFFSET
        self.nota_atual_detectada = '--'
        # Preenchido por main.py com a instancia de SessaoEstudo
        self.sessao = None
        # Ultimas notas captadas, usadas pelo bloco de historico
        self.historico_notas = []
        self.ultima_nota_historico = '--'
        self.ideias_recentes = None
        # Drone de referencia
        self.drone_nota = 'C'
        self.drone_ativo = False
        self.canal_drone = None
        self.rects_drone = []
        self.rect_btn_drone = pygame.Rect(0, 0, 0, 0)
        self.rects_circulo = []
        self.rect_btn_limpar_historico = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_gravar_ideia = pygame.Rect(0, 0, 0, 0)
        self.inicio_gravacao_ideia = 0.0
        # Progressoes rapidas
        self.progressao_ativa = -1
        self.rects_progressoes = []
        self.ultima_ideia_salva = ''
        # Graus do campo harmonico desenhados no braco pelo bloco de graus
        self.grau_selecionado = -1
        self.rects_graus = []
        # Cordas soltas da afinacao em uso
        self.rects_cordas = []
        # Capotraste: casa escolhida, 0 = sem capo
        self.capo_casa = 0
        self.rects_capo = []
        # Gaveteiro lateral: todos os blocos comecam guardados na coluna
        from ui.components.gaveteiro import preparar as preparar_gaveteiro
        preparar_gaveteiro(self)
        self.nota_selecionada_bloco = 'C'
        self.rects_notas_selecao = []
        self.instrumento = 'guitarra'
        self.secoes_inferiores = [{'titulo': 'ESCALAS', 'expandido': False, 'conteudo': 'escalas', 'memoria_sub_aba': 0, 'sub_abas': ['Maior', 'Menor', 'Penta Maior', 'Penta Menor', 'Blues', 'Modos', 'Harmônica', 'Melodica', 'Exóticas']}, {'titulo': 'ACORDES', 'expandido': False, 'conteudo': 'acordes', 'memoria_sub_aba': 0, 'sub_abas': ['CAGED', 'Tríades Maiores', 'Tríades Menores', 'Sétimas', 'Power Chords']}, {'titulo': 'ANÁLISE DE IA', 'expandido': False, 'conteudo': 'analise_ia', 'memoria_sub_aba': 0, 'sub_abas': ['Afinador / IA', 'JOGOS']}, {'titulo': 'ESTUDOS', 'expandido': False, 'conteudo': 'estudos', 'memoria_sub_aba': 0, 'sub_abas': ['Notas', 'Escalas', 'Acordes', 'Teoria', 'Padrões', 'Improvisação', 'Aulas', 'Pedais', 'Tempo']}, {'titulo': 'MÚSICAS', 'expandido': False, 'conteudo': 'musicas', 'memoria_sub_aba': 0, 'sub_abas': ['Songster', 'Minhas Músicas', 'Criação Musical', 'Timbre']}, {'titulo': 'CONFIGURAÇÃO', 'expandido': False, 'conteudo': 'configuracao', 'memoria_sub_aba': 0, 'sub_abas': ['Cores da Interface', 'Configurações Globais']}]
        
        # --- Criador de Tablaturas ---
        from core.modulos.modulo_dados_tab import GerenciadorDadosTablatura
        self.tela_criacao_tab_ativa = False
        self.tab_nome = "Nova Música"
        self.tab_bpm = 120
        self.tab_reproduzindo = False
        self.tab_coluna_atual = 0
        self.tab_dados_gerenciador = GerenciadorDadosTablatura(self.tab_bpm)
        self.tab_cursor_col = 0
        self.tab_cursor_corda = 0
        self.tab_scroll_x = 0
        self.tempo_ultimo_tick = 0
        self.guias_x = []
        self.guias_y = []
        
        # --- IA de Transcrição ---
        from core.modulos.modulo_ia_transcricao import ClienteTranscricaoIA
        self.cliente_ia = ClienteTranscricaoIA()
        self.ia_ligada = False

    def adicionar_coluna_ia(self, notas_json):
        """Preenche os dados da tablatura vindo da IA usando o gerenciador."""
        self.tab_dados_gerenciador.preencher_da_ia(notas_json)

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