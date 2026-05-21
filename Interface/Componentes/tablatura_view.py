# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Componente de Visualização de Tablaturas Songsterr
# =============================================================================

import pygame
import os
from DragDrop.elemento_arrastavel import ElementoArrastavel
from Core.i18n import _t
from Modulos.leitor_midi import LeitorMIDI

class BlocoTablatura(ElementoArrastavel):
    def __init__(self, x, y, largura, altura, song_data):
        super().__init__(x, y, largura, altura)
        self.song_data = song_data
        self.titulo = song_data.get('title', 'Unknown')
        self.artista = song_data.get('artist', 'Unknown')
        self.song_id = song_data.get('songId')
        
        # Detalhes carregados dinamicamente
        self.detalhes = None
        self.carregando = False
        self.erro = False
        self.detalhes_carregados = False
        
        # Tracks e Dados Reais
        self.tracks = song_data.get('tracks', []) 
        self.track_ativa_idx = 0
        self.dados_tab_reais = {} # track_idx -> list of notes
        
        # Scroll Interno da Tab
        self.scroll_y_tab = 0
        self.altura_virtual_tab = 0
        
        # Cores Profissionais
        self.COR_FUNDO = (25, 25, 30)
        self.COR_BORDA = (60, 60, 70)
        self.COR_TEXTO = (240, 240, 240)
        self.COR_ACENTO = (0, 163, 255)
        self.COR_CABECALHO = (35, 35, 40)
        self.COR_LINHA = (60, 60, 65)

        # Suporte a MIDI Local
        self.caminho_midi_local = None

    def carregar_dados_completos(self, api_songsterr):
        """Dispara a busca de detalhes e download do MIDI (em thread)"""
        if self.carregando: return
        self.carregando = True
        
        import threading
        def thread_task():
            try:
                # Caso SEJA MIDI LOCAL (Adicionado via Drag-and-Drop ou Seleção)
                if self.caminho_midi_local and os.path.exists(self.caminho_midi_local):
                    leitor = LeitorMIDI(self.caminho_midi_local)
                    if leitor.ler():
                        # Cria uma track dummy baseada no MIDI (Afinação padrão EADGBE)
                        self.tracks = [{'instrument': 'Local MIDI', 'tuning': [64, 59, 55, 50, 45, 40], 'name': 'Track 1'}]
                        self.dados_tab_reais[0] = leitor.converter_para_tab([64, 59, 55, 50, 45, 40])
                        self.detalhes_carregados = True
                    else:
                        self.erro = True
                    self.carregando = False
                    return

                # Caso SEJA SONGSTERR
                # 1. Obtém metadados para pegar o revisionId atual
                res = api_songsterr.obter_detalhes_completos(self.song_id)
                if res:
                    self.detalhes = res
                    self.tracks = res.get('tracks', [])
                    revision_id = res.get('revisionId')
                    
                    if revision_id:
                        # 2. Baixa o MIDI automaticamente
                        caminho_midi = api_songsterr.baixar_midi(revision_id, self.song_id)
                        if caminho_midi:
                            # 3. Lê o MIDI
                            leitor = LeitorMIDI(caminho_midi)
                            if leitor.ler():
                                # Processa cada track baseada no tuning do Songsterr
                                for i, track in enumerate(self.tracks):
                                    tuning = track.get('tuning', [64, 59, 55, 50, 45, 40])
                                    self.dados_tab_reais[i] = leitor.converter_para_tab(tuning)
                                
                                self.detalhes_carregados = True
                            else:
                                print("Falha ao ler o binário do MIDI")
                                self.erro = True
                        else:
                            print("Falha ao baixar MIDI")
                            self.erro = True
                    else:
                        self.detalhes_carregados = True
                else:
                    self.erro = True
            except Exception as e:
                print(f"Erro no carregamento da tab: {e}")
                self.erro = True
            self.carregando = False
            
        threading.Thread(target=thread_task).start()

    def desenhar(self, tela, fontes):
        # 1. Fundo Principal
        rect_bg = pygame.Rect(self.x, self.y, self.largura, self.altura)
        pygame.draw.rect(tela, self.COR_FUNDO, rect_bg, border_radius=12)
        
        # 2. Cabeçalho Estilizado
        rect_header = pygame.Rect(self.x, self.y, self.largura, 45)
        pygame.draw.rect(tela, self.COR_CABECALHO, rect_header, border_radius=12)
        pygame.draw.rect(tela, self.COR_CABECALHO, (self.x, self.y + 12, self.largura, 33))
        
        txt_titulo = fontes['ui'].render(f"{self.titulo}", True, self.COR_TEXTO)
        tela.blit(txt_titulo, (self.x + 15, self.y + 12))
        
        txt_artista = fontes['pequena'].render(f"by {self.artista}", True, (180, 180, 180))
        tela.blit(txt_artista, (self.x + 15 + txt_titulo.get_width() + 10, self.y + 16))

        # 2.1 Botão Fechar (X)
        self.rect_fechar = pygame.Rect(self.x + self.largura - 35, self.y + 10, 25, 25)
        pygame.draw.rect(tela, (200, 60, 60), self.rect_fechar, border_radius=5)
        txt_x = fontes['ui'].render("X", True, (255, 255, 255))
        tela.blit(txt_x, (self.rect_fechar.centerx - txt_x.get_width()//2, self.rect_fechar.centery - txt_x.get_height()//2))
        
        # 3. ÁREA ÚTIL (Sidebar + Tab)
        y_conteudo = self.y + 55
        largura_sidebar = 160
        
        # Sidebar de Trilhas
        self._desenhar_sidebar(tela, self.x + 10, y_conteudo, largura_sidebar, fontes)

        # Visualizador de Tablatura (Com Clipping e Scroll)
        x_tab = self.x + largura_sidebar + 15
        largura_tab = self.largura - largura_sidebar - 30
        altura_tab = self.altura - 110
        
        rect_tab_view = pygame.Rect(x_tab, y_conteudo, largura_tab, altura_tab)
        
        if self.carregando:
             agora = pygame.time.get_ticks()
             pontos = "." * ((agora // 500) % 4)
             txt_l = fontes['ui'].render(_t("Acessando Songsterr") + pontos, True, (200, 200, 200))
             tela.blit(txt_l, (x_tab + 20, y_conteudo + 50))
        elif self.erro or not self.dados_tab_reais:
             txt_e = fontes['ui'].render(_t("Download Direto Restrito pelo Songsterr"), True, (255, 100, 100))
             tela.blit(txt_e, (x_tab + 20, y_conteudo + 50))
             
             txt_info = fontes['pequena'].render(_t("O site protege os arquivos MIDI. Use o botão abaixo para ver no navegador."), True, (180, 180, 180))
             tela.blit(txt_info, (x_tab + 20, y_conteudo + 80))
             
             # Desenha uma tablatura vazia/simulada apenas para manter a estética
             self._desenhar_visualizador_vazio(tela, x_tab, y_conteudo + 120, largura_tab, altura_tab - 120, fontes)
        else:
             original_clip = tela.get_clip()
             tela.set_clip(rect_tab_view)
             self._desenhar_visualizador_tab(tela, x_tab, y_conteudo, largura_tab, altura_tab, fontes)
             tela.set_clip(original_clip)
             
             if self.altura_virtual_tab > altura_tab:
                 self._desenhar_scrollbar(tela, rect_tab_view)

        # 4. Botões de Ação
        rect_site = pygame.Rect(x_tab, self.y + self.altura - 40, 160, 30)
        pygame.draw.rect(tela, (0, 80, 150), rect_site, border_radius=5)
        txt_s = fontes['pequena'].render(_t("Ver no Songsterr"), True, (255, 255, 255))
        tela.blit(txt_s, (rect_site.centerx - txt_s.get_width()//2, rect_site.centery - txt_s.get_height()//2))
        self.rect_btn_site = rect_site

        # 5. Borda Final e Gizmos
        pygame.draw.rect(tela, self.COR_BORDA, rect_bg, width=2, border_radius=12)
        
        pygame.draw.polygon(tela, (150, 150, 150), [
            (self.x + self.largura, self.y + self.altura - 15),
            (self.x + self.largura, self.y + self.altura),
            (self.x + self.largura - 15, self.y + self.altura)
        ])

    def _desenhar_sidebar(self, tela, x, y, largura, fontes):
        txt_tracks_tit = fontes['pequena'].render(_t("TRILHAS MIDI:"), True, self.COR_ACENTO)
        tela.blit(txt_tracks_tit, (x, y))
        
        max_trilhas = (self.altura - 120) // 25
        for i, track in enumerate(self.tracks[:max_trilhas]):
            y_item = y + 25 + (i * 25)
            cor_track = self.COR_ACENTO if i == self.track_ativa_idx else (140, 140, 145)
            
            nome_track = track.get('name', 'Track')
            if len(nome_track) > 18: nome_track = nome_track[:16] + ".."
            
            if i == self.track_ativa_idx:
                pygame.draw.rect(tela, (40, 45, 55), (x-5, y_item-2, largura, 22), border_radius=4)

            txt_t = fontes['pequena'].render(nome_track, True, cor_track)
            tela.blit(txt_t, (x, y_item))
            track['rect_clique'] = pygame.Rect(x, y_item, largura, 20)

    def _desenhar_visualizador_tab(self, tela, x, y, largura, altura_box, fontes):
        if self.track_ativa_idx not in self.dados_tab_reais:
            txt_msg = fontes['pequena'].render(_t("Processando notas..."), True, (150, 150, 150))
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
        if ticks_por_linha <= 0: ticks_por_linha = 1000
        
        max_tick = notas[-1]['tempo'] if notas else 0
        num_linhas = (max_tick // ticks_por_linha) + 1
        
        self.altura_virtual_tab = num_linhas * (altura_pauta + margem_pauta) + 50
        y_v = y - self.scroll_y_tab

        for l in range(num_linhas):
            y_pauta = y_v + (l * (altura_pauta + margem_pauta))
            if y_pauta + altura_pauta < y - 50 or y_pauta > y + altura_box + 50:
                continue

            for i in range(num_cordas):
                yl = y_pauta + (i * espacamento_cordas)
                pygame.draw.line(tela, self.COR_LINHA, (x + 35, yl), (x + largura - 5, yl), 1)

            pygame.draw.line(tela, (200, 200, 205), (x + 35, y_pauta), (x + 35, y_pauta + altura_pauta), 3)

            tempo_inicio_linha = l * ticks_por_linha
            tempo_fim_linha = (l + 1) * ticks_por_linha
            
            notas_linha = [n for n in notas if tempo_inicio_linha <= n['tempo'] < tempo_fim_linha]
            
            for n in notas_linha:
                nx = x + 45 + (n['tempo'] - tempo_inicio_linha) * escala_tempo
                ny = y_pauta + (n['string'] * espacamento_cordas)
                
                txt_val = fontes['pequena'].render(str(n['fret']), True, (255, 255, 255))
                pygame.draw.rect(tela, self.COR_FUNDO, (nx - 4, ny - 7, txt_val.get_width()+2, 14))
                tela.blit(txt_val, (nx - 2, ny - 8))

    def _desenhar_visualizador_vazio(self, tela, x, y, largura, altura_box, fontes):
        """Desenha uma pauta vazia estilizada para quando o download falha"""
        num_cordas = 6
        espacamento_cordas = 18
        altura_pauta = (num_cordas - 1) * espacamento_cordas
        margem_pauta = 60
        
        num_linhas_visiveis = (altura_box // (altura_pauta + margem_pauta)) + 1
        
        for l in range(num_linhas_visiveis):
            y_pauta = y + (l * (altura_pauta + margem_pauta))
            if y_pauta + altura_pauta > y + altura_box: break
            
            for i in range(num_cordas):
                yl = y_pauta + (i * espacamento_cordas)
                pygame.draw.line(tela, (50, 50, 55), (x + 35, yl), (x + largura - 5, yl), 1)
            
            pygame.draw.line(tela, (80, 80, 85), (x + 35, y_pauta), (x + 35, y_pauta + altura_pauta), 2)
            
            # Mensagem sutil no meio da primeira pauta
            if l == 0:
                txt_hint = fontes['pequena'].render(_t("Modo Visualização Web Recomendado"), True, (100, 100, 105))
                tela.blit(txt_hint, (x + largura//2 - txt_hint.get_width()//2, y_pauta + altura_pauta//2 - 10))

    def _desenhar_scrollbar(self, tela, rect_view):
        if self.altura_virtual_tab <= rect_view.height: return
        fator_altura = rect_view.height / self.altura_virtual_tab
        altura_alca = max(20, rect_view.height * fator_altura)
        y_alca = rect_view.y + (self.scroll_y_tab / self.altura_virtual_tab) * rect_view.height
        
        rect_track = pygame.Rect(rect_view.right - 8, rect_view.y, 6, rect_view.height)
        pygame.draw.rect(tela, (40, 40, 45), rect_track, border_radius=3)
        
        rect_alca = pygame.Rect(rect_view.right - 8, y_alca, 6, altura_alca)
        pygame.draw.rect(tela, (100, 100, 105), rect_alca, border_radius=3)

    def tratar_clique(self, pos):
        if hasattr(self, 'rect_fechar') and self.rect_fechar.collidepoint(pos):
            return "FECHAR"
            
        for i, track in enumerate(self.tracks):
            if track.get('rect_clique') and track['rect_clique'].collidepoint(pos):
                self.track_ativa_idx = i
                self.scroll_y_tab = 0
                return True

        if hasattr(self, 'rect_btn_site') and self.rect_btn_site.collidepoint(pos):
            if self.song_id:
                import webbrowser
                url = f"https://www.songsterr.com/a/wsa/song-tab-s{self.song_id}"
                webbrowser.open(url)
            return True
            
        return False

    def tratar_scroll(self, dy):
        if self.altura_virtual_tab > (self.altura - 110):
            self.scroll_y_tab -= dy * 40
            limite_max = self.altura_virtual_tab - (self.altura - 110)
            self.scroll_y_tab = max(0, min(self.scroll_y_tab, limite_max))
            return True
        return False
