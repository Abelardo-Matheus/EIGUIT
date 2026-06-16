import pygame
import os
import subprocess
import cv2
from PIL import Image as PILImage
from core.i18n import _t
from core.modulos.modulos_config import *

class TutorialSuporte:
    """
        Gerencia o modal de suporte e tutoriais com sistema de abas e scroll.
    """

    def __init__(self):
        self.aberto = False
        self.aba_ativa = 0
        self.scroll_y = 0
        self.max_scroll = 0
        self.arrastando_scroll = False
        
        self.BRANCO = SUPORTE_BRANCO
        self.CINZA = SUPORTE_CINZA
        self.AZUL = SUPORTE_AZUL
        self.AZUL_CLARO = SUPORTE_AZUL_CLARO
        
        self.abas = ['Escalas', 'Configurações', 'Metrônomo', 'Acordes', 'Vídeos']
        self.conteudo = {
            0: [
                {'titulo': 'Sistema Drag & Drop', 'texto': "Para utilizar as escalas, ative o ícone do 'Alfinete' (canto superior direito). Com o modo de edição ativado, clique e arraste qualquer escala do painel inferior diretamente para o braço da guitarra.", 'thumb': 'assets/images/Thumbnails/Escalas/drag_drop.png'}, 
                {'titulo': 'Sobreposição Dinâmica', 'texto': 'Você pode soltar a escala em qualquer parte do braço. O EIGUIT recalcula automaticamente as notas baseando-se na afinação atual e no tom selecionado.', 'thumb': 'assets/images/Thumbnails/Escalas/sobreposicao.png'}, 
                {'titulo': 'Removendo Escalas', 'texto': 'Errou a posição ou quer limpar a tela? Basta clicar com o Botão Direito do mouse sobre o braço da guitarra para devolver todas as escalas de volta ao painel de origem.', 'thumb': 'assets/images/Thumbnails/Escalas/remover.png'}
            ], 
            1: [
                {'titulo': 'Personalização Visual', 'texto': 'Acesse a aba de configurações para alterar as cores do braço da guitarra e das notas. Use o seletor de cores integrado para encontrar o tom exato que mais agrada sua visão durante os estudos.', 'thumb': 'assets/images/Thumbnails/Configuracoes/visual.png'}, 
                {'titulo': 'Modos de Visualização', 'texto': "Você pode alternar o texto exibido dentro das bolinhas. Escolha entre 'Notas' (C, D, E), 'Graus' (1, 2, 3) para estudar intervalos, ou oculte o texto para focar apenas nos padrões visuais (shapes).", 'thumb': 'assets/images/Thumbnails/Configuracoes/modos.png'}, 
                {'titulo': 'Ajuste de Transparência', 'texto': 'Utilize o controle deslizante de Alpha (Transparência) para mesclar a visualização das escalas com a madeira da guitarra, criando uma interface menos agressiva aos olhos.', 'thumb': 'assets/images/Thumbnails/Configuracoes/transparencia.png'}
            ], 
            2: [
                {'titulo': 'Controle de Tempo (BPM)', 'texto': 'O metrônomo é o coração do seu estudo rítmico. Ajuste a velocidade usando os botões de + e - ou clique na barra deslizante. A faixa vai de 40 a 240 Batidas Por Minuto.', 'thumb': 'assets/images/Thumbnails/Metronomo/bpm.png'}, 
                {'titulo': 'Assinatura de Compasso', 'texto': 'Ajuste os tempos por compasso clicando nos números centrais (ex: 4/4, 3/4). O primeiro tempo (cabeça do compasso) sempre emitirá um som diferenciado para guiá-lo.', 'thumb': 'assets/images/Thumbnails/Metronomo/compasso.png'}
            ],
            3: [
                {'titulo': 'Busca de Acordes', 'texto': 'Utilize o painel de acordes para encontrar qualquer variação. Digite o nome da nota e o tipo (Maior, Menor, 7M, etc).', 'thumb': 'assets/images/Thumbnails/Acordes/busca.png'}, 
                {'titulo': 'Visualização no Braço', 'texto': 'Ao clicar em um acorde, ele é desenhado no braço da guitarra, mostrando as casas e dedos recomendados.', 'thumb': 'assets/images/Thumbnails/Acordes/braco.png'}
            ],
            4: [] # Aba de Vídeos
        }
        self.rects_videos = {}
        self.thumbnails_cache = {} # Cache para superfícies de miniaturas
        self.images_cache = {} # Cache para imagens estáticas e GIFs
        self.rect_barra_scroll = pygame.Rect(0,0,0,0)
        self._carregar_videos_automacao()

    def _obter_imagem_tutorial(self, path):
        """Carrega imagem estática ou frame de GIF animado."""
        if not path: return None
        
        # Se for vídeo, pega o primeiro frame como antes
        if path.endswith('.mp4'):
            return self._obter_thumbnail_video(path)
            
        # Se for GIF, trata animação
        if path.lower().endswith('.gif'):
            return self._processar_gif(path)
            
        # Imagem normal (PNG, JPG, etc)
        if path in self.images_cache:
            return self.images_cache[path]
            
        try:
            # Tenta encontrar o arquivo com diferentes extensões se necessário
            caminho_real = path
            if not os.path.exists(path):
                for ext in ['.png', '.jpg', '.gif', '.webp']:
                    teste = os.path.splitext(path)[0] + ext
                    if os.path.exists(teste):
                        caminho_real = teste
                        break
            
            if os.path.exists(caminho_real):
                if caminho_real.lower().endswith('.gif'):
                    return self._processar_gif(caminho_real)
                
                img = pygame.image.load(caminho_real).convert_alpha()
                img = pygame.transform.smoothscale(img, (280, 160))
                self.images_cache[path] = img
                return img
        except Exception as e:
            print(f"[ERRO] Falha ao carregar imagem tutorial {path}: {e}")
        return None

    def _processar_gif(self, path):
        """Lógica para carregar frames de GIF e retornar o frame atual baseado no tempo."""
        agora = pygame.time.get_ticks()
        
        if path not in self.images_cache:
            try:
                img_pil = PILImage.open(path)
                frames = []
                durations = []
                try:
                    while True:
                        # Converte frame para RGBA e Pygame Surface
                        frame_pil = img_pil.convert('RGBA')
                        frame_data = frame_pil.tobytes()
                        frame_size = frame_pil.size
                        frame_surf = pygame.image.fromstring(frame_data, frame_size, 'RGBA')
                        frame_surf = pygame.transform.smoothscale(frame_surf, (280, 160))
                        frames.append(frame_surf)
                        durations.append(img_pil.info.get('duration', 100)) # Default 100ms
                        img_pil.seek(img_pil.tell() + 1)
                except EOFError:
                    pass
                
                self.images_cache[path] = {
                    'frames': frames,
                    'durations': durations,
                    'total_time': sum(durations),
                    'start_time': agora
                }
            except Exception as e:
                print(f"[ERRO] Falha ao processar GIF {path}: {e}")
                return None

        # Calcula qual frame mostrar agora
        data = self.images_cache[path]
        tempo_decorrido = (agora - data['start_time']) % data['total_time']
        acumulado = 0
        for i, d in enumerate(data['durations']):
            acumulado += d
            if tempo_decorrido < acumulado:
                return data['frames'][i]
        
        return data['frames'][0]

    def _obter_thumbnail_video(self, video_path):
        """Extrai o primeiro frame do vídeo e converte em Pygame Surface."""
        if video_path in self.thumbnails_cache:
            return self.thumbnails_cache[video_path]

        try:
            cap = cv2.VideoCapture(video_path)
            ret, frame = cap.read()
            cap.release()

            if ret:
                # Converte de BGR (OpenCV) para RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Redimensiona para o tamanho da miniatura (280x160)
                frame = cv2.resize(frame, (280, 160))
                # Rotaciona e inverte pois o OpenCV usa formato diferente do Pygame
                frame = frame.swapaxes(0, 1)
                surf = pygame.surfarray.make_surface(frame)
                self.thumbnails_cache[video_path] = surf
                return surf
        except Exception as e:
            print(f"[ERRO] Falha ao gerar thumbnail para {video_path}: {e}")
        
        return None

    def _carregar_videos_automacao(self):
        path_videos = "automacao_tutoriais/videos_exportados"
        if os.path.exists(path_videos):
            videos = [f for f in os.listdir(path_videos) if f.endswith('.mp4')]
            self.conteudo[4] = []
            for v in videos:
                nome_formatado = v.replace('.mp4', '').replace('_', ' ').title()
                path_full = os.path.join(path_videos, v)
                self.conteudo[4].append({
                    'titulo': nome_formatado,
                    'texto': 'Assista ao tutorial em vídeo para entender melhor como utilizar esta funcionalidade.',
                    'path': path_full,
                    'tipo': 'video'
                })

    def quebrar_texto(self, texto, fonte, max_largura):
        palavras = texto.split(' ')
        linhas = []
        linha_atual = ''
        for palavra in palavras:
            teste_linha = linha_atual + palavra + ' '
            if fonte.size(teste_linha)[0] < max_largura:
                linha_atual = teste_linha
            else:
                linhas.append(linha_atual)
                linha_atual = palavra + ' '
        linhas.append(linha_atual)
        return linhas

    def _reproduzir_video(self, path):
        try:
            from core.modulos.modulo_video_aula import abrir_player_video_async
            # Extrai o título do caminho do arquivo
            titulo = os.path.basename(path).replace('.mp4', '').replace('_', ' ').title()
            abrir_player_video_async(path, titulo=f"Tutorial: {titulo}")
        except (ImportError, Exception) as e:
            print(f"[AVISO] Falha ao abrir player interno ({e}). Usando player do sistema.")
            self._reproduzir_video_externo(path)

    def _reproduzir_video_externo(self, path):
        try:
            if os.name == 'nt':
                os.startfile(path)
            else:
                subprocess.call(['open', path])
        except:
            pass

    def tratar_eventos(self, eventos, pos_mouse):
        if not self.aberto:
            return False
            
        for evento in eventos:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                self.aberto = False
                return True
                
            # Scroll via Roda do Mouse (Moderno)
            if evento.type == pygame.MOUSEWHEEL:
                velocidade = 100
                self.scroll_y -= evento.y * velocidade
                self._limitar_scroll()
                continue
                
            if evento.type == pygame.MOUSEBUTTONDOWN:
                # Scroll via Roda do Mouse (Legado/Clássico)
                if evento.button == 4: # Roda para cima
                    self.scroll_y -= 60
                    self._limitar_scroll()
                    continue
                if evento.button == 5: # Roda para baixo
                    self.scroll_y += 60
                    self._limitar_scroll()
                    continue

                if evento.button == 1:
                    # Clique na Barra de Scroll
                    if self.max_scroll > 0 and self.rect_barra_scroll.collidepoint(pos_mouse):
                        self.arrastando_scroll = True
                        self._atualizar_scroll_por_clique(pos_mouse)
                        return True

                    if hasattr(self, 'rect_fechar') and self.rect_fechar.collidepoint(pos_mouse):
                        self.aberto = False
                        return True
                        
                    if hasattr(self, 'rects_abas'):
                        for i, rect in enumerate(self.rects_abas):
                            if rect.collidepoint(pos_mouse):
                                if self.aba_ativa != i:
                                    self.aba_ativa = i
                                    self._recalcular_limites_scroll()
                                if i == 4: self._carregar_videos_automacao()
                                return True
                                
                    for path, r_vid in self.rects_videos.items():
                        if r_vid.collidepoint(pos_mouse):
                            self._reproduzir_video(path)
                            return True
            
            if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
                self.arrastando_scroll = False

            if evento.type == pygame.MOUSEMOTION and self.arrastando_scroll:
                self._atualizar_scroll_por_clique(pos_mouse)
                return True

        return True

    def _atualizar_scroll_por_clique(self, pos_mouse):
        if self.rect_barra_scroll.height > 0:
            rel_y = pos_mouse[1] - self.rect_barra_scroll.top
            percent = max(0, min(1, rel_y / self.rect_barra_scroll.height))
            self.scroll_y = percent * self.max_scroll
            self._limitar_scroll()

    def _limitar_scroll(self):
        self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))

    def _recalcular_limites_scroll(self):
        # Simula o layout para saber a altura total
        altura_conteudo_visivel = 550 - 120 # altura_modal - 120
        itens_atuais = self.conteudo.get(self.aba_ativa, [])
        altura_total_conteudo = 20 # Margem inicial
        largura_imagem, altura_imagem = (280, 160)
        for item in itens_atuais:
            altura_total_conteudo += altura_imagem + 40
        self.max_scroll = max(0, altura_total_conteudo - altura_conteudo_visivel)
        self._limitar_scroll()

    def calcular_centro_camera(self, estado, tela, largura_obj, altura_obj):
        largura_real = tela.get_width()
        altura_real = tela.get_height()
        return (largura_real // 2 - largura_obj // 2, altura_real // 2 - altura_obj // 2)

    def desenhar(self, tela, fonte_ui, fonte_titulo, estado=None):
        if not self.aberto:
            return
            
        overlay = pygame.Surface((tela.get_width(), tela.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        tela.blit(overlay, (0, 0))
        
        largura_modal, altura_modal = 850, 550
        cx, cy = self.calcular_centro_camera(estado, tela, largura_modal, altura_modal)
        rect_modal = pygame.Rect(cx, cy, largura_modal, altura_modal)
        
        pygame.draw.rect(tela, (30, 30, 30), rect_modal, border_radius=10)
        pygame.draw.rect(tela, (100, 100, 100), rect_modal, width=2, border_radius=10)
        
        # Cabeçalho
        tit = fonte_titulo.render(_t('Central de Suporte & Tutoriais'), True, self.BRANCO)
        tela.blit(tit, (cx + 20, cy + 20))
        
        # Abas
        self.rects_abas = []
        largura_aba = (largura_modal - 40) / len(self.abas)
        y_abas = cy + 60
        for i, nome_aba in enumerate(self.abas):
            rect_aba = pygame.Rect(cx + 20 + i * largura_aba, y_abas, largura_aba - 5, 35)
            self.rects_abas.append(rect_aba)
            cor_fundo = self.AZUL_CLARO if self.aba_ativa == i else (60, 60, 60)
            pygame.draw.rect(tela, cor_fundo, rect_aba, border_radius=5)
            txt_aba = fonte_ui.render(_t(nome_aba), True, self.BRANCO)
            tela.blit(txt_aba, (rect_aba.centerx - txt_aba.get_width() // 2, rect_aba.centery - txt_aba.get_height() // 2))
            
        # Área de Conteúdo (Clipping)
        y_conteudo, altura_conteudo = y_abas + 45, altura_modal - 120
        rect_clipping = pygame.Rect(cx + 20, y_conteudo, largura_modal - 40, altura_conteudo)
        pygame.draw.rect(tela, (20, 20, 20), rect_clipping, border_radius=5)
        
        # --- CÁLCULO DE MAX_SCROLL DINÂMICO ---
        itens_atuais = self.conteudo.get(self.aba_ativa, [])
        altura_total_conteudo = 20 # Margem inicial
        largura_imagem, altura_imagem = (280, 160)
        for item in itens_atuais:
            altura_total_conteudo += altura_imagem + 40
        self.max_scroll = max(0, altura_total_conteudo - altura_conteudo)
        self._limitar_scroll()
        # --------------------------------------

        tela.set_clip(rect_clipping)
        y_item = y_conteudo + 20 - self.scroll_y
        margem_esq, margem_dir, espacamento_meio = (40, 60, 30)
        largura_texto_max = largura_modal - margem_esq - margem_dir - largura_imagem - espacamento_meio
        self.rects_videos.clear()
        
        for i, item in enumerate(itens_atuais):
            img_na_esquerda = i % 2 == 0
            x_img = cx + margem_esq if img_na_esquerda else cx + margem_esq + largura_texto_max + espacamento_meio
            x_texto = cx + margem_esq + largura_imagem + espacamento_meio if img_na_esquerda else cx + margem_esq
            
            rect_img = pygame.Rect(x_img, y_item, largura_imagem, altura_imagem)
            pygame.draw.rect(tela, (40, 40, 45), rect_img, border_radius=8)
            
            # --- RENDERIZAÇÃO DA MINIATURA (VÍDEO OU IMAGEM) ---
            thumb = None
            if item.get('tipo') == 'video':
                thumb = self._obter_thumbnail_video(item['path'])
            elif 'thumb' in item:
                thumb = self._obter_imagem_tutorial(item['thumb'])
                
            if thumb:
                tela.blit(thumb, rect_img)
            
            if item.get('tipo') == 'video':
                self.rects_videos[item['path']] = rect_img
                # Overlay de Play
                pygame.draw.circle(tela, (0, 0, 0, 120), rect_img.center, 30)
                pygame.draw.circle(tela, self.BRANCO, rect_img.center, 30, width=2)
                p1, p2, p3 = (rect_img.centerx - 10, rect_img.centery - 15), (rect_img.centerx - 10, rect_img.centery + 15), (rect_img.centerx + 15, rect_img.centery)
                pygame.draw.polygon(tela, self.BRANCO, [p1, p2, p3])
            
            pygame.draw.rect(tela, self.AZUL if item.get('tipo') == 'video' else self.CINZA, rect_img, width=2, border_radius=8)
            
            txt_titulo = fonte_titulo.render(_t(item['titulo']), True, self.AZUL_CLARO)
            tela.blit(txt_titulo, (x_texto, y_item))
            
            linhas = self.quebrar_texto(_t(item['texto']), fonte_ui, largura_texto_max)
            y_linha = y_item + 35
            for linha in linhas:
                txt_linha = fonte_ui.render(linha, True, (200, 200, 200))
                tela.blit(txt_linha, (x_texto, y_linha))
                y_linha += 22
            
            y_item += altura_imagem + 40
            
        tela.set_clip(None)
        
        # Barra de Scroll Lateral
        if self.max_scroll > 0:
            x_bar = cx + largura_modal - 15
            self.rect_barra_scroll = pygame.Rect(x_bar, y_conteudo, 8, altura_conteudo)
            pygame.draw.rect(tela, (50, 50, 50), self.rect_barra_scroll, border_radius=4)
            
            tamanho_alca = max(40, altura_conteudo * (altura_conteudo / (altura_conteudo + self.max_scroll)))
            y_alca = y_conteudo + (self.scroll_y / self.max_scroll) * (altura_conteudo - tamanho_alca)
            pygame.draw.rect(tela, self.CINZA if not self.arrastando_scroll else self.AZUL_CLARO, (x_bar, y_alca, 8, tamanho_alca), border_radius=4)
            
        # Botão Fechar
        self.rect_fechar = pygame.Rect(cx + largura_modal - 140, cy + 20, 120, 30)
        pygame.draw.rect(tela, (200, 50, 50), self.rect_fechar, border_radius=5)
        txt_fechar = fonte_ui.render(_t('Fechar X'), True, self.BRANCO)
        tela.blit(txt_fechar, (self.rect_fechar.centerx - txt_fechar.get_width() // 2, self.rect_fechar.centery - txt_fechar.get_height() // 2))
