import pygame
import os
from DragDrop.elemento_arrastavel import ElementoArrastavel
from core.i18n import _t
from core.modulos.leitor_midi import LeitorMIDI

class BlocoTablatura(ElementoArrastavel):
    """
        Como funciona: Define a estrutura e estado do componente 'BlocoTablatura'.
        Para que serve: Atua como o modelo principal para instâncias de 'BlocoTablatura'.
        Onde é usada: Chamado a partir do módulo ou classe base de 'tablatura_view'.
    """

    def __init__(self, x, y, largura, altura, song_data):
        """
            Como funciona: Inicializa os atributos e o estado inicial da instância.
            Para que serve: Prepara o objeto para ser utilizado no ciclo de vida da aplicação.
            Onde é usada: Chamado a partir do módulo ou classe base de 'tablatura_view'.
        """
        super().__init__(x, y, largura, altura)
        self.song_data = song_data
        self.titulo = song_data.get('title', 'Unknown')
        self.artista = song_data.get('artist', 'Unknown')
        self.song_id = song_data.get('songId')
        self.detalhes = None
        self.carregando = False
        self.erro = False
        self.detalhes_carregados = False
        self.tracks = song_data.get('tracks', [])
        self.track_ativa_idx = 0
        self.dados_tab_reais = {}
        self.scroll_y_tab = 0
        self.altura_virtual_tab = 0
        self.COR_FUNDO = (25, 25, 30)
        self.COR_BORDA = (60, 60, 70)
        self.COR_TEXTO = (240, 240, 240)
        self.COR_ACENTO = (0, 163, 255)
        self.COR_CABECALHO = (35, 35, 40)
        self.COR_LINHA = (60, 60, 65)
        self.caminho_midi_local = None

    def carregar_dados_completos(self, api_songsterr):
        """
            Como funciona: Lê dados de disco, banco de dados ou estado salvo.
            Para que serve: Popula as estruturas em memória com as informações persistidas.
            Onde é usada: Chamado a partir do módulo ou classe base de 'tablatura_view'.
        """
        if self.carregando:
            return
        self.carregando = True
        import threading

        def thread_task():
            """
                Como funciona: Executa o fluxo lógico necessário para a operação 'thread task'.
                Para que serve: Realiza as tarefas fundamentais de 'thread task' dentro do contexto do módulo.
                Onde é usada: Utilizado internamente para gerenciar comportamentos de 'thread task'.
            """
            try:
                if self.caminho_midi_local and os.path.exists(self.caminho_midi_local):
                    leitor = LeitorMIDI(self.caminho_midi_local)
                    if leitor.ler():
                        self.tracks = [{'instrument': 'Local MIDI', 'tuning': [64, 59, 55, 50, 45, 40], 'name': 'Track 1'}]
                        self.dados_tab_reais[0] = leitor.converter_para_tab([64, 59, 55, 50, 45, 40])
                        self.detalhes_carregados = True
                    else:
                        self.erro = True
                    self.carregando = False
                    return
                res = api_songsterr.obter_detalhes_completos(self.song_id)
                if res:
                    self.detalhes = res
                    self.tracks = res.get('tracks', [])
                    revision_id = res.get('revisionId')
                    if revision_id:
                        caminho_midi = api_songsterr.baixar_midi(revision_id, self.song_id)
                        if caminho_midi:
                            leitor = LeitorMIDI(caminho_midi)
                            if leitor.ler():
                                for i, track in enumerate(self.tracks):
                                    tuning = track.get('tuning', [64, 59, 55, 50, 45, 40])
                                    self.dados_tab_reais[i] = leitor.converter_para_tab(tuning)
                                self.detalhes_carregados = True
                            else:
                                print('Falha ao ler o binário do MIDI')
                                self.erro = True
                        else:
                            print('Falha ao baixar MIDI')
                            self.erro = True
                    else:
                        self.detalhes_carregados = True
                else:
                    self.erro = True
            except Exception as e:
                print(f'Erro no carregamento da tab: {e}')
                self.erro = True
            self.carregando = False
        threading.Thread(target=thread_task).start()

    def desenhar(self, tela, fontes):
        """
            Como funciona: Utiliza funções de renderização do Pygame para desenhar na tela.
            Para que serve: Apresenta o elemento visual 'desenhar' na interface gráfica.
            Onde é usada: Chamado a partir do módulo ou classe base de 'tablatura_view'.
        """
        rect_bg = pygame.Rect(self.x, self.y, self.largura, self.altura)
        pygame.draw.rect(tela, self.COR_FUNDO, rect_bg, border_radius=12)
        rect_header = pygame.Rect(self.x, self.y, self.largura, 45)
        pygame.draw.rect(tela, self.COR_CABECALHO, rect_header, border_radius=12)
        pygame.draw.rect(tela, self.COR_CABECALHO, (self.x, self.y + 12, self.largura, 33))
        txt_titulo = fontes['ui'].render(f'{self.titulo}', True, self.COR_TEXTO)
        tela.blit(txt_titulo, (self.x + 15, self.y + 12))
        txt_artista = fontes['pequena'].render(f'by {self.artista}', True, (180, 180, 180))
        tela.blit(txt_artista, (self.x + 15 + txt_titulo.get_width() + 10, self.y + 16))
        self.rect_fechar = pygame.Rect(self.x + self.largura - 35, self.y + 10, 25, 25)
        pygame.draw.rect(tela, (200, 60, 60), self.rect_fechar, border_radius=5)
        txt_x = fontes['ui'].render('X', True, (255, 255, 255))
        tela.blit(txt_x, (self.rect_fechar.centerx - txt_x.get_width() // 2, self.rect_fechar.centery - txt_x.get_height() // 2))
        y_conteudo = self.y + 55
        largura_sidebar = 160
        self._desenhar_sidebar(tela, self.x + 10, y_conteudo, largura_sidebar, fontes)
        x_tab = self.x + largura_sidebar + 15
        largura_tab = self.largura - largura_sidebar - 30
        altura_tab = self.altura - 110
        rect_tab_view = pygame.Rect(x_tab, y_conteudo, largura_tab, altura_tab)
        if self.carregando:
            agora = pygame.time.get_ticks()
            pontos = '.' * (agora // 500 % 4)
            txt_l = fontes['ui'].render(_t('Acessando Songsterr') + pontos, True, (200, 200, 200))
            tela.blit(txt_l, (x_tab + 20, y_conteudo + 50))
        elif self.erro or not self.dados_tab_reais:
            txt_e = fontes['ui'].render(_t('Download Direto Restrito pelo Songsterr'), True, (255, 100, 100))
            tela.blit(txt_e, (x_tab + 20, y_conteudo + 50))
            txt_info = fontes['pequena'].render(_t('O site protege os arquivos MIDI. Use o botão abaixo para ver no navegador.'), True, (180, 180, 180))
            tela.blit(txt_info, (x_tab + 20, y_conteudo + 80))
            self._desenhar_visualizador_vazio(tela, x_tab, y_conteudo + 120, largura_tab, altura_tab - 120, fontes)
        else:
            original_clip = tela.get_clip()
            tela.set_clip(rect_tab_view)
            self._desenhar_visualizador_tab(tela, x_tab, y_conteudo, largura_tab, altura_tab, fontes)
            tela.set_clip(original_clip)
            if self.altura_virtual_tab > altura_tab:
                self._desenhar_scrollbar(tela, rect_tab_view)
        rect_site = pygame.Rect(x_tab, self.y + self.altura - 40, 160, 30)
        pygame.draw.rect(tela, (0, 80, 150), rect_site, border_radius=5)
        txt_s = fontes['pequena'].render(_t('Ver no Songsterr'), True, (255, 255, 255))
        tela.blit(txt_s, (rect_site.centerx - txt_s.get_width() // 2, rect_site.centery - txt_s.get_height() // 2))
        self.rect_btn_site = rect_site
        pygame.draw.rect(tela, self.COR_BORDA, rect_bg, width=2, border_radius=12)
        pygame.draw.polygon(tela, (150, 150, 150), [(self.x + self.largura, self.y + self.altura - 15), (self.x + self.largura, self.y + self.altura), (self.x + self.largura - 15, self.y + self.altura)])

    def _desenhar_sidebar(self, tela, x, y, largura, fontes):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação ' desenhar sidebar'.
            Para que serve: Realiza as tarefas fundamentais de ' desenhar sidebar' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de ' desenhar sidebar'.
        """
        txt_tracks_tit = fontes['pequena'].render(_t('TRILHAS MIDI:'), True, self.COR_ACENTO)
        tela.blit(txt_tracks_tit, (x, y))
        max_trilhas = (self.altura - 120) // 25
        for i, track in enumerate(self.tracks[:max_trilhas]):
            y_item = y + 25 + i * 25
            cor_track = self.COR_ACENTO if i == self.track_ativa_idx else (140, 140, 145)
            nome_track = track.get('name', 'Track')
            if len(nome_track) > 18:
                nome_track = nome_track[:16] + '..'
            if i == self.track_ativa_idx:
                pygame.draw.rect(tela, (40, 45, 55), (x - 5, y_item - 2, largura, 22), border_radius=4)
            txt_t = fontes['pequena'].render(nome_track, True, cor_track)
            tela.blit(txt_t, (x, y_item))
            track['rect_clique'] = pygame.Rect(x, y_item, largura, 20)

    def _desenhar_visualizador_tab(self, tela, x, y, largura, altura_box, fontes):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação ' desenhar visualizador tab'.
            Para que serve: Realiza as tarefas fundamentais de ' desenhar visualizador tab' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de ' desenhar visualizador tab'.
        """
        if self.track_ativa_idx not in self.dados_tab_reais:
            txt_msg = fontes['pequena'].render(_t('Processando notas...'), True, (150, 150, 150))
            tela.blit(txt_msg, (x + 20, y + 20))
            return
        notas = self.dados_tab_reais[self.track_ativa_idx]
        t = self.tracks[self.track_ativa_idx]
        num_cordas = len(t.get('tuning', [64, 59, 55, 50, 45, 40]))
        espacamento_cordas = 18
        altura_pauta = (num_cordas - 1) * espacamento_cordas
        margem_pauta = 60
        escala_tempo = 0.5
        ticks_por_linha = int((largura - 60) / escala_tempo)
        if ticks_por_linha <= 0:
            ticks_por_linha = 1000
        max_tick = notas[-1]['tempo'] if notas else 0
        num_linhas = max_tick // ticks_por_linha + 1
        self.altura_virtual_tab = num_linhas * (altura_pauta + margem_pauta) + 50
        y_v = y - self.scroll_y_tab
        for l in range(num_linhas):
            y_pauta = y_v + l * (altura_pauta + margem_pauta)
            if y_pauta + altura_pauta < y - 50 or y_pauta > y + altura_box + 50:
                continue
            for i in range(num_cordas):
                yl = y_pauta + i * espacamento_cordas
                pygame.draw.line(tela, self.COR_LINHA, (x + 35, yl), (x + largura - 5, yl), 1)
            pygame.draw.line(tela, (200, 200, 205), (x + 35, y_pauta), (x + 35, y_pauta + altura_pauta), 3)
            tempo_inicio_linha = l * ticks_por_linha
            tempo_fim_linha = (l + 1) * ticks_por_linha
            notas_linha = [n for n in notas if tempo_inicio_linha <= n['tempo'] < tempo_fim_linha]
            for n in notas_linha:
                nx = x + 45 + (n['tempo'] - tempo_inicio_linha) * escala_tempo
                ny = y_pauta + n['string'] * espacamento_cordas
                txt_val = fontes['pequena'].render(str(n['fret']), True, (255, 255, 255))
                pygame.draw.rect(tela, self.COR_FUNDO, (nx - 4, ny - 7, txt_val.get_width() + 2, 14))
                tela.blit(txt_val, (nx - 2, ny - 8))

    def _desenhar_visualizador_vazio(self, tela, x, y, largura, altura_box, fontes):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação ' desenhar visualizador vazio'.
            Para que serve: Realiza as tarefas fundamentais de ' desenhar visualizador vazio' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de ' desenhar visualizador vazio'.
        """
        num_cordas = 6
        espacamento_cordas = 18
        altura_pauta = (num_cordas - 1) * espacamento_cordas
        margem_pauta = 60
        num_linhas_visiveis = altura_box // (altura_pauta + margem_pauta) + 1
        for l in range(num_linhas_visiveis):
            y_pauta = y + l * (altura_pauta + margem_pauta)
            if y_pauta + altura_pauta > y + altura_box:
                break
            for i in range(num_cordas):
                yl = y_pauta + i * espacamento_cordas
                pygame.draw.line(tela, (50, 50, 55), (x + 35, yl), (x + largura - 5, yl), 1)
            pygame.draw.line(tela, (80, 80, 85), (x + 35, y_pauta), (x + 35, y_pauta + altura_pauta), 2)
            if l == 0:
                txt_hint = fontes['pequena'].render(_t('Modo Visualização Web Recomendado'), True, (100, 100, 105))
                tela.blit(txt_hint, (x + largura // 2 - txt_hint.get_width() // 2, y_pauta + altura_pauta // 2 - 10))

    def _desenhar_scrollbar(self, tela, rect_view):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação ' desenhar scrollbar'.
            Para que serve: Realiza as tarefas fundamentais de ' desenhar scrollbar' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de ' desenhar scrollbar'.
        """
        if self.altura_virtual_tab <= rect_view.height:
            return
        fator_altura = rect_view.height / self.altura_virtual_tab
        altura_alca = max(20, rect_view.height * fator_altura)
        y_alca = rect_view.y + self.scroll_y_tab / self.altura_virtual_tab * rect_view.height
        rect_track = pygame.Rect(rect_view.right - 8, rect_view.y, 6, rect_view.height)
        pygame.draw.rect(tela, (40, 40, 45), rect_track, border_radius=3)
        rect_alca = pygame.Rect(rect_view.right - 8, y_alca, 6, altura_alca)
        pygame.draw.rect(tela, (100, 100, 105), rect_alca, border_radius=3)

    def tratar_clique(self, pos):
        """
            Como funciona: Verifica colisões e processa inputs do mouse/teclado.
            Para que serve: Mapeia ações do usuário para atualizações de estado.
            Onde é usada: Chamado a partir do módulo ou classe base de 'tablatura_view'.
        """
        if hasattr(self, 'rect_fechar') and self.rect_fechar.collidepoint(pos):
            return 'FECHAR'
        for i, track in enumerate(self.tracks):
            if track.get('rect_clique') and track['rect_clique'].collidepoint(pos):
                self.track_ativa_idx = i
                self.scroll_y_tab = 0
                return True
        if hasattr(self, 'rect_btn_site') and self.rect_btn_site.collidepoint(pos):
            if self.song_id:
                import webbrowser
                url = f'https://www.songsterr.com/a/wsa/song-tab-s{self.song_id}'
                webbrowser.open(url)
            return True
        return False

    def tratar_scroll(self, dy):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'tratar scroll'.
            Para que serve: Realiza as tarefas fundamentais de 'tratar scroll' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'tratar scroll'.
        """
        if self.altura_virtual_tab > self.altura - 110:
            self.scroll_y_tab -= dy * 40
            limite_max = self.altura_virtual_tab - (self.altura - 110)
            self.scroll_y_tab = max(0, min(self.scroll_y_tab, limite_max))
            return True
        return False