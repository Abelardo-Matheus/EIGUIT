import pygame
import threading
import requests
import time
from tkinter import filedialog, Tk
from Modulos.modulo_dados_tab import GerenciadorDadosTablatura
from Modulos.modulo_synth_guitarra import SintetizadorGuitarra

# --- CONSTANTES DE ESTILO ---
VERMELHO_DANGER = (231, 76, 60)
VERDE_SUCCESS = (46, 204, 113)
AZUL_LINK = (52, 152, 219)
FUNDO_CONTROLES = (22, 22, 28)
BRANCO = (255, 255, 255)

class RenderizadorCriadorTablatura:
    def __init__(self, tela, largura, altura):
        self.tela = tela
        self.largura = largura
        self.altura = altura
        
        self.dados = GerenciadorDadosTablatura()
        self.synth = SintetizadorGuitarra()
        
        # Cores
        self.COR_FUNDO = (15, 15, 18)
        self.COR_LINHA = (50, 50, 55)
        self.COR_TEXTO = (200, 200, 205)
        self.COR_CURSOR = (0, 255, 255, 60)
        self.COR_PLAYHEAD = (255, 80, 80)
        self.COR_SELECAO = (52, 152, 219, 80)

        # Configurações de Grade
        self.margem_esquerda = 50
        self.espacamento_cordas = 16
        self.espacamento_tempos = 24
        self.inicio_y = 140 # Aumentado para não ficar sob a toolbar
        self.espacamento_linhas = 135 # Espaço entre sistemas (6 cordas)

        
        # UI State
        self.scroll_y = 0
        self.cursor_pos = [0, 0] # [corda, tempo]
        self.campo_focado = None
        self.ultimo_clique_tempo = 0
        self.modo_selecao = False
        
        # Fontes
        self.fonte_mini = pygame.font.SysFont("Consolas", 11)
        self.fonte_normal = pygame.font.SysFont("Consolas", 14, bold=True)
        self.fonte_ui = pygame.font.SysFont("Arial", 13)
        self.fonte_titulo = pygame.font.SysFont("Arial", 16, bold=True)

    def renderizar(self):
        # Atualiza dimensões caso a janela tenha mudado
        self.largura = self.tela.get_width()
        self.altura = self.tela.get_height()

        # 1. Background
        self.tela.fill(self.COR_FUNDO)
        
        # 2. Calcular layout dinâmico
        margem_direita = 40
        largura_disponivel = self.largura - self.margem_esquerda - margem_direita
        self.colunas_por_linha = max(8, largura_disponivel // self.espacamento_tempos)
        self.colunas_por_linha = (self.colunas_por_linha // 4) * 4
        
        # 3. Desenhar Sistemas de Tablatura
        num_colunas_total = len(self.dados.grade[0])
        num_sistemas_existentes = (num_colunas_total + self.colunas_por_linha - 1) // self.colunas_por_linha
        
        # Sempre mostrar pelo menos 4 sistemas (mesmo que vazios)
        num_sistemas_a_exibir = max(4, num_sistemas_existentes)
        
        # Define área útil para a tablatura (abaixo da toolbar)
        area_tab = pygame.Rect(0, 135, self.largura, self.altura - 135)
        self.tela.set_clip(area_tab)
        
        for s_idx in range(num_sistemas_a_exibir):
            self._desenhar_sistema(s_idx)
            
        # Botão "+" para adicionar mais sistemas ao final
        self._desenhar_botao_adicionar(num_sistemas_a_exibir)
            
        self.tela.set_clip(None)
        
        # 4. Desenhar Controles Fixos (Topo)
        self._desenhar_status_ia()
        self._desenhar_toolbar()
        
        # 5. Desenhar Scrollbar se necessário
        self._desenhar_scrollbar(num_sistemas_a_exibir + 1)

    def _desenhar_sistema(self, idx):
        base_y = self.inicio_y + (idx * self.espacamento_linhas) - self.scroll_y
        
        # Culling (não desenha o que está fora da tela)
        if base_y + self.espacamento_linhas < 50 or base_y > self.altura:
            return
            
        inicio_t = idx * self.colunas_por_linha
        fim_t = min(inicio_t + self.colunas_por_linha, len(self.dados.grade[0]))
        largura_sistema = self.colunas_por_linha * self.espacamento_tempos
        
        # Nomes das Cordas
        nomes = ["e", "B", "G", "D", "A", "E"]
        for i, n in enumerate(nomes):
            y = base_y + i * self.espacamento_cordas
            pygame.draw.line(self.tela, self.COR_LINHA, (self.margem_esquerda, y), (self.margem_esquerda + largura_sistema, y), 1)
            txt = self.fonte_mini.render(n, True, (80, 80, 90))
            self.tela.blit(txt, (20, y - 6))
            
        # Linhas de Divisão de Tempo e Notas
        for t in range(inicio_t, inicio_t + self.colunas_por_linha):
            rel_t = t - inicio_t
            x = self.margem_esquerda + rel_t * self.espacamento_tempos
            
            # Divisórias
            if t % 16 == 0: # Compasso
                pygame.draw.line(self.tela, (100, 100, 110), (x, base_y - 5), (x, base_y + 5 * self.espacamento_cordas + 5), 2)
                num_comp = (t // 16) + 1
                txt_comp = self.fonte_mini.render(str(num_comp), True, (120, 120, 130))
                self.tela.blit(txt_comp, (x + 4, base_y - 18))
            elif t % 4 == 0: # Batida
                pygame.draw.line(self.tela, (45, 45, 50), (x, base_y), (x, base_y + 5 * self.espacamento_cordas), 1)

            # Cursor e Playhead
            if self.cursor_pos[1] == t:
                self._desenhar_cursor(x, base_y)
            if self.dados.cursor_tempo == t:
                pygame.draw.line(self.tela, self.COR_PLAYHEAD, (x, base_y - 10), (x, base_y + 5 * self.espacamento_cordas + 10), 2)

            # Notas (apenas se o tempo existir nos dados)
            if t < len(self.dados.grade[0]):
                for c in range(6):
                    valor = self.dados.grade[c][t]
                    if valor != "-":
                        y_nota = base_y + c * self.espacamento_cordas
                        pygame.draw.rect(self.tela, self.COR_FUNDO, (x - 7, y_nota - 7, 14, 14))
                        
                        cor_n = self.COR_TEXTO
                        if any(tec in valor for tec in "bs/\\hp~"):
                            cor_n = AZUL_LINK
                            
                        txt_n = self.fonte_normal.render(valor, True, cor_n)
                        self.tela.blit(txt_n, (x - txt_n.get_width()//2, y_nota - txt_n.get_height()//2))

    def _desenhar_botao_adicionar(self, num_sistemas):
        base_y = self.inicio_y + (num_sistemas * self.espacamento_linhas) - self.scroll_y
        if base_y + 50 < 100 or base_y > self.altura:
            return
            
        centro_x = self.margem_esquerda + (self.colunas_por_linha * self.espacamento_tempos) // 2
        self.rect_add_sistema = pygame.Rect(centro_x - 20, base_y, 40, 40)
        
        # Desenha círculo com "+"
        pygame.draw.circle(self.tela, (40, 40, 50), self.rect_add_sistema.center, 20)
        pygame.draw.circle(self.tela, AZUL_LINK, self.rect_add_sistema.center, 20, 2)
        
        txt_plus = self.fonte_titulo.render("+", True, AZUL_LINK)
        self.tela.blit(txt_plus, (self.rect_add_sistema.centerx - txt_plus.get_width()//2, self.rect_add_sistema.centery - txt_plus.get_height()//2 - 2))
        
        txt_hint = self.fonte_mini.render("Adicionar Sistema", True, (100, 100, 110))
        self.tela.blit(txt_hint, (self.rect_add_sistema.centerx - txt_hint.get_width()//2, self.rect_add_sistema.bottom + 5))

    def _desenhar_cursor(self, x, base_y):
        y = base_y + self.cursor_pos[0] * self.espacamento_cordas
        rect = pygame.Rect(x - self.espacamento_tempos // 2, y - self.espacamento_cordas // 2, self.espacamento_tempos, self.espacamento_cordas)
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        s.fill(self.COR_CURSOR)
        self.tela.blit(s, rect.topleft)
        pygame.draw.rect(self.tela, (0, 255, 255), rect, 1, border_radius=2)

    def _desenhar_toolbar(self):
        # Background do Painel Superior (Compacto)
        pygame.draw.rect(self.tela, FUNDO_CONTROLES, (0, 0, self.largura, 100))
        pygame.draw.line(self.tela, (60, 60, 70), (0, 100), (self.largura, 100), 2)
        
        # 1. Informações Básicas
        txt_proj = self.fonte_titulo.render(f"TAB: {self.dados.nome_musica}", True, BRANCO)
        self.tela.blit(txt_proj, (20, 15))
        
        self.rect_play = pygame.Rect(20, 50, 36, 36)
        self.rect_stop = pygame.Rect(65, 50, 36, 36)
        
        # Play/Pause
        pygame.draw.rect(self.tela, VERDE_SUCCESS if not self.dados.playing else (241, 196, 15), self.rect_play, border_radius=6)
        sym = ">" if not self.dados.playing else "||"
        t_sym = self.fonte_titulo.render(sym, True, BRANCO)
        self.tela.blit(t_sym, (self.rect_play.centerx - t_sym.get_width()//2, self.rect_play.centery - t_sym.get_height()//2))
        
        # Stop
        pygame.draw.rect(self.tela, VERMELHO_DANGER, self.rect_stop, border_radius=6)
        pygame.draw.rect(self.tela, BRANCO, (self.rect_stop.centerx - 5, self.rect_stop.centery - 5, 10, 10))
        
        # BPM
        self.rect_bpm = pygame.Rect(115, 50, 100, 36)
        pygame.draw.rect(self.tela, (40, 40, 50), self.rect_bpm, border_radius=6)
        txt_bpm = self.fonte_ui.render(f"BPM: {self.dados.bpm}", True, AZUL_LINK)
        self.tela.blit(txt_bpm, (self.rect_bpm.centerx - txt_bpm.get_width()//2, self.rect_bpm.centery - txt_bpm.get_height()//2))
        
        # 3. Botão Transcrição IA e Importar
        self.rect_ai = pygame.Rect(225, 10, 140, 30)
        pygame.draw.rect(self.tela, AZUL_LINK if not hasattr(self, 'processando_ia') else (100, 100, 100), self.rect_ai, border_radius=15)
        txt_ai = self.fonte_ui.render("✨ Transcrição IA", True, BRANCO)
        self.tela.blit(txt_ai, (self.rect_ai.centerx - txt_ai.get_width()//2, self.rect_ai.centery - txt_ai.get_height()//2))

        self.rect_import = pygame.Rect(375, 10, 140, 30)
        pygame.draw.rect(self.tela, (46, 204, 113), self.rect_import, border_radius=15)
        txt_imp = self.fonte_ui.render("📁 Importar MP3", True, BRANCO)
        self.tela.blit(txt_imp, (self.rect_import.centerx - txt_imp.get_width()//2, self.rect_import.centery - txt_imp.get_height()//2))

        # 2. Técnicas (Atalhos Visuais - Segunda Coluna)
        tecnicas = [("B", "Bend"), ("S", "Slide"), ("H", "Hammer"), ("P", "Pull"), ("V", "Vibrato")]
        for i, (key, label) in enumerate(tecnicas):
            rect = pygame.Rect(230 + i * 75, 50, 70, 36)
            pygame.draw.rect(self.tela, (35, 35, 45), rect, border_radius=6)
            txt_k = self.fonte_normal.render(key, True, AZUL_LINK)
            txt_l = self.fonte_mini.render(label, True, (150, 150, 160))
            self.tela.blit(txt_k, (rect.x + 6, rect.centery - 7))
            self.tela.blit(txt_l, (rect.x + 22, rect.centery - 5))

    def _desenhar_scrollbar(self, num_sistemas):
        total_h = num_sistemas * self.espacamento_linhas + self.inicio_y
        if total_h > self.altura:
            razao = (self.altura - 100) / total_h
            barra_h = max(20, (self.altura - 100) * razao)
            barra_y = 100 + (self.scroll_y / total_h) * (self.altura - 100)
            pygame.draw.rect(self.tela, (30, 30, 35), (self.largura - 10, 100, 6, self.altura - 100))
            pygame.draw.rect(self.tela, (100, 100, 110), (self.largura - 10, barra_y, 6, barra_h), border_radius=3)

    def tratar_evento(self, evento, estado=None):
        if evento.type == pygame.DROPFILE:
            caminho = evento.file
            if caminho.lower().endswith(('.mp3', '.wav', '.ogg')):
                self.processando_ia = True
                self.status_ia = "Arquivo solto: Enviando..."
                threading.Thread(target=self._processar_ia, args=(caminho,), daemon=True).start()
            return True

        if evento.type == pygame.MOUSEWHEEL:
            self.scroll_y = max(0, self.scroll_y - evento.y * 40)
            return True
            
        elif evento.type == pygame.KEYDOWN:
            if self.campo_focado: return False
            
            # Navegação
            consumiu = False
            if evento.key == pygame.K_RIGHT: 
                self.cursor_pos[1] += 1
                self.dados._garantir_capacidade(self.cursor_pos[1])
                consumiu = True
            elif evento.key == pygame.K_LEFT: 
                self.cursor_pos[1] = max(0, self.cursor_pos[1] - 1)
                consumiu = True
            elif evento.key == pygame.K_UP: 
                self.cursor_pos[0] = max(0, self.cursor_pos[0] - 1)
                consumiu = True
            elif evento.key == pygame.K_DOWN: 
                self.cursor_pos[0] = min(5, self.cursor_pos[0] + 1)
                consumiu = True
            
            # Edição de Notas
            elif pygame.K_0 <= evento.key <= pygame.K_9:
                num = str(evento.key - pygame.K_0)
                atual = self.dados.grade[self.cursor_pos[0]][self.cursor_pos[1]]
                if atual == "-" or any(c.isalpha() for c in atual): novo = num
                else: novo = (atual + num)[:2] # Max 2 dígitos
                self.dados.adicionar_nota(self.cursor_pos[0], self.cursor_pos[1], novo)
                self.synth.tocar_nota(self.cursor_pos[0]+1, int(novo))
                self.cursor_pos[1] += 1 # Auto-advance
                self.dados._garantir_capacidade(self.cursor_pos[1])
                consumiu = True
                
            elif evento.key == pygame.K_BACKSPACE or evento.key == pygame.K_DELETE:
                self.dados.remover_nota(self.cursor_pos[0], self.cursor_pos[1])
                if evento.key == pygame.K_BACKSPACE:
                    self.cursor_pos[1] = max(0, self.cursor_pos[1] - 1)
                consumiu = True
                
            # Técnicas
            elif evento.key == pygame.K_b: self._toggle_tecnica("b"); consumiu = True
            elif evento.key == pygame.K_s: self._toggle_tecnica("/"); consumiu = True
            elif evento.key == pygame.K_h: self._toggle_tecnica("h"); consumiu = True
            elif evento.key == pygame.K_p: self._toggle_tecnica("p"); consumiu = True
            elif evento.key == pygame.K_v: self._toggle_tecnica("~"); consumiu = True
            elif evento.key == pygame.K_x: self.dados.adicionar_nota(self.cursor_pos[0], self.cursor_pos[1], "x"); consumiu = True
            
            # Playback
            elif evento.key == pygame.K_SPACE:
                if self.dados.playing: self.dados.stop()
                else: self.dados.play(self.synth.tocar_nota)
                consumiu = True
                
            return consumiu

        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1:
                # Prioridade: Toolbar (área fixa)
                if evento.pos[1] < 100:
                    if self.rect_play.collidepoint(evento.pos):
                        if self.dados.playing: self.dados.stop()
                        else: self.dados.play(self.synth.tocar_nota)
                        return True
                    elif self.rect_stop.collidepoint(evento.pos):
                        self.dados.stop()
                        return True
                    elif hasattr(self, 'rect_ai') and self.rect_ai.collidepoint(evento.pos):
                        self._iniciar_transcricao_ia()
                        return True
                    elif hasattr(self, 'rect_import') and self.rect_import.collidepoint(evento.pos):
                        self._iniciar_transcricao_ia()
                        return True
                    # Se clicar na toolbar mas não nos botões, consumimos para não clicar no que está atrás
                    return True
                else:
                    # Verificar botão "+"
                    if hasattr(self, 'rect_add_sistema') and self.rect_add_sistema.collidepoint(evento.pos):
                        proximo_tempo = len(self.dados.grade[0]) + self.colunas_por_linha
                        self.dados._garantir_capacidade(proximo_tempo)
                        return True

                    # Clique na grade (considerando scroll)
                    t, c = self._obter_coord_clique(evento.pos[0], evento.pos[1])
                    if t is not None:
                        self.cursor_pos = [c, t]
                        self.dados._garantir_capacidade(t)
                        return True
        return False

    def _obter_coord_clique(self, mx, my):
        # 1. Ignorar cliques na toolbar
        if my < 100: return None, None
        
        # 2. Ajustar Y pelo scroll e offset inicial
        y_rel = my + self.scroll_y - self.inicio_y
        
        # 3. Identificar o sistema
        idx_sistema = int(y_rel // self.espacamento_linhas)
        y_dentro_sistema = y_rel % self.espacamento_linhas
        
        # 4. Verificar se o clique foi nas cordas (evitar espaço entre sistemas)
        altura_tab = 6 * self.espacamento_cordas
        if y_dentro_sistema < -10 or y_dentro_sistema > altura_tab + 10:
            return None, None
            
        # 5. Mapear Corda e Tempo
        c = max(0, min(5, int((y_dentro_sistema + (self.espacamento_cordas//2)) // self.espacamento_cordas)))
        
        # Tempo relativo ao sistema
        largura_sistema = self.colunas_por_linha * self.espacamento_tempos
        if mx < self.margem_esquerda or mx > self.margem_esquerda + largura_sistema:
            return None, None
            
        t_rel = int((mx - self.margem_esquerda + (self.espacamento_tempos//2)) // self.espacamento_tempos)
        
        if 0 <= t_rel < self.colunas_por_linha:
            t_absoluto = idx_sistema * self.colunas_por_linha + t_rel
            if t_absoluto >= 0:
                return t_absoluto, c
                
        return None, None

    def _toggle_tecnica(self, char):
        atual = self.dados.grade[self.cursor_pos[0]][self.cursor_pos[1]]
        if atual == "-": return
        if char in atual:
            self.dados.adicionar_nota(self.cursor_pos[0], self.cursor_pos[1], atual.replace(char, ""))
        else:
            self.dados.adicionar_nota(self.cursor_pos[0], self.cursor_pos[1], atual + char)

    def _iniciar_transcricao_ia(self):
        if hasattr(self, 'processando_ia') and self.processando_ia:
            return

        # Abrir seletor de arquivo (em thread para não travar o Pygame)
        def selecionar_e_enviar():
            root = Tk()
            root.withdraw()
            caminho_arquivo = filedialog.askopenfilename(
                title="Selecionar Áudio para Transcrição",
                filetypes=[("Arquivos de Áudio", "*.wav *.mp3 *.ogg")]
            )
            root.destroy()

            if caminho_arquivo:
                self.processando_ia = True
                self.status_ia = "Enviando arquivo..."
                threading.Thread(target=self._processar_ia, args=(caminho_arquivo,), daemon=True).start()

        threading.Thread(target=selecionar_e_enviar, daemon=True).start()

    def _processar_ia(self, caminho_arquivo):
        try:
            url_base = "http://localhost:8000"
            
            # 1. Upload
            self.status_ia = "Processando IA..."
            with open(caminho_arquivo, 'rb') as f:
                r = requests.post(f"{url_base}/transcribe", files={'file': f})
            
            if r.status_code != 200:
                self.status_ia = "Erro no Upload"
                time.sleep(3)
                self.processando_ia = False
                return

            task_id = r.json().get("task_id")
            
            # 2. Polling de Status
            while True:
                r_status = requests.get(f"{url_base}/status/{task_id}")
                dados = r_status.json()
                
                if dados['status'] == 'completed':
                    self.status_ia = "Mapeando notas..."
                    self.dados.preencher_da_ia(dados['result']['notes'])
                    self.status_ia = "Concluído!"
                    time.sleep(2)
                    break
                elif dados['status'] == 'failed':
                    self.status_ia = "IA falhou."
                    break
                
                time.sleep(2) # Espera 2 segundos antes de checar de novo

        except Exception as e:
            print(f"Erro na Transcrição IA: {e}")
            self.status_ia = "Erro de Conexão"
        
        self.processando_ia = False
        if hasattr(self, 'status_ia') and self.status_ia == "Concluído!":
            time.sleep(1)
            delattr(self, 'status_ia')

    # Adicionar no final do renderizar() antes do toolbar
    def _desenhar_status_ia(self):
        if hasattr(self, 'status_ia'):
            rect_status = pygame.Rect(self.largura - 210, 15, 200, 30)
            pygame.draw.rect(self.tela, (40, 40, 50), rect_status, border_radius=6)
            txt = self.fonte_ui.render(self.status_ia, True, (255, 200, 0))
            self.tela.blit(txt, (rect_status.centerx - txt.get_width()//2, rect_status.centery - txt.get_height()//2))
