import pygame
import threading
import requests
import time
from tkinter import filedialog, Tk
from core.modulos.modulo_dados_tab import GerenciadorDadosTablatura
from core.modulos.modulo_synth_guitarra import SintetizadorGuitarra

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
        self.inicio_y = 110 
        self.espacamento_linhas = 135 

        # UI State
        self.scroll_y = 0
        self.cursor_pos = [0, 0] # [corda, tempo]
        self.campo_focado = None
        self.status_ia = ""
        self.processando_ia = False
        self.instrumento_selecionado = "other" # other, bass, drums, vocals
        
        # Fontes
        self.fonte_mini = pygame.font.SysFont("Consolas", 11)
        self.fonte_normal = pygame.font.SysFont("Consolas", 14, bold=True)
        self.fonte_ui = pygame.font.SysFont("Arial", 13)
        self.fonte_titulo = pygame.font.SysFont("Arial", 16, bold=True)

    def renderizar(self, estado=None):
        self.largura = self.tela.get_width()
        self.altura = self.tela.get_height()
        
        if estado and hasattr(estado, 'cliente_ia'):
            self.processando_ia = estado.cliente_ia.status not in ("idle", "completed", "failed")
            if self.processando_ia:
                self.status_ia = f"IA: {estado.cliente_ia.status.upper()}..."
            elif estado.cliente_ia.status == "completed":
                self.status_ia = "✅ TRANSCRIÇÃO CONCLUÍDA"
            elif estado.cliente_ia.status == "failed":
                self.status_ia = f"❌ ERRO: {estado.cliente_ia.erro}"
            else:
                self.status_ia = ""

        self.tela.fill(self.COR_FUNDO)
        margem_direita = 40
        largura_disponivel = self.largura - self.margem_esquerda - margem_direita
        self.colunas_por_linha = max(8, largura_disponivel // self.espacamento_tempos)
        self.colunas_por_linha = (self.colunas_por_linha // 4) * 4
        
        num_colunas_total = len(self.dados.grade[0])
        num_sistemas_a_exibir = max(4, (num_colunas_total + self.colunas_por_linha - 1) // self.colunas_por_linha)
        
        area_tab = pygame.Rect(0, 135, self.largura, self.altura - 135)
        self.tela.set_clip(area_tab)
        for s_idx in range(num_sistemas_a_exibir):
            self._desenhar_sistema(s_idx)
        self._desenhar_botao_adicionar(num_sistemas_a_exibir)
        self.tela.set_clip(None)
        
        self._desenhar_status_ia()
        self._desenhar_toolbar()
        self._desenhar_scrollbar(num_sistemas_a_exibir + 1)

    def _desenhar_sistema(self, idx):
        base_y = self.inicio_y + (idx * self.espacamento_linhas) - self.scroll_y
        if base_y + self.espacamento_linhas < 50 or base_y > self.altura: return
        inicio_t = idx * self.colunas_por_linha
        largura_sistema = self.colunas_por_linha * self.espacamento_tempos
        nomes = ["e", "B", "G", "D", "A", "E"]
        for i, n in enumerate(nomes):
            y = base_y + i * self.espacamento_cordas
            pygame.draw.line(self.tela, self.COR_LINHA, (self.margem_esquerda, y), (self.margem_esquerda + largura_sistema, y), 1)
            txt = self.fonte_mini.render(n, True, (80, 80, 90)); self.tela.blit(txt, (20, y - 6))
        for t in range(inicio_t, inicio_t + self.colunas_por_linha):
            rel_t = t - inicio_t; x = self.margem_esquerda + rel_t * self.espacamento_tempos
            if t % 16 == 0:
                pygame.draw.line(self.tela, (100, 100, 110), (x, base_y - 5), (x, base_y + 5 * self.espacamento_cordas + 5), 2)
            if self.cursor_pos[1] == t: self._desenhar_cursor(x, base_y)
            if self.dados.cursor_tempo == t: pygame.draw.line(self.tela, self.COR_PLAYHEAD, (x, base_y - 10), (x, base_y + 5 * self.espacamento_cordas + 10), 2)
            if t < len(self.dados.grade[0]):
                for c in range(6):
                    valor = self.dados.grade[c][t]
                    if valor != "-":
                        y_nota = base_y + c * self.espacamento_cordas
                        pygame.draw.rect(self.tela, self.COR_FUNDO, (x - 7, y_nota - 7, 14, 14))
                        cor_n = AZUL_LINK if any(tec in valor for tec in "bs/\\hp~") else self.COR_TEXTO
                        txt_n = self.fonte_normal.render(valor, True, cor_n); self.tela.blit(txt_n, (x - txt_n.get_width()//2, y_nota - txt_n.get_height()//2))

    def _desenhar_botao_adicionar(self, num_sistemas):
        base_y = self.inicio_y + (num_sistemas * self.espacamento_linhas) - self.scroll_y
        if base_y + 50 < 100 or base_y > self.altura: return
        centro_x = self.margem_esquerda + (self.colunas_por_linha * self.espacamento_tempos) // 2
        self.rect_add_sistema = pygame.Rect(centro_x - 20, base_y, 40, 40)
        pygame.draw.circle(self.tela, (40, 40, 50), self.rect_add_sistema.center, 20)
        pygame.draw.circle(self.tela, AZUL_LINK, self.rect_add_sistema.center, 20, 2)
        txt = self.fonte_titulo.render("+", True, AZUL_LINK); self.tela.blit(txt, (self.rect_add_sistema.centerx - txt.get_width()//2, self.rect_add_sistema.centery - txt.get_height()//2 - 2))

    def _desenhar_cursor(self, x, base_y):
        y = base_y + self.cursor_pos[0] * self.espacamento_cordas
        rect = pygame.Rect(x - self.espacamento_tempos // 2, y - self.espacamento_cordas // 2, self.espacamento_tempos, self.espacamento_cordas)
        s = pygame.Surface(rect.size, pygame.SRCALPHA); s.fill(self.COR_CURSOR); self.tela.blit(s, rect.topleft)
        pygame.draw.rect(self.tela, (0, 255, 255), rect, 1, border_radius=2)

    def _desenhar_toolbar(self):
        pygame.draw.rect(self.tela, FUNDO_CONTROLES, (0, 0, self.largura, 100))
        pygame.draw.line(self.tela, (60, 60, 70), (0, 100), (self.largura, 100), 2)
        txt_proj = self.fonte_titulo.render(f"TAB: {self.dados.nome_musica}", True, BRANCO); self.tela.blit(txt_proj, (20, 15))
        self.rect_play = pygame.Rect(20, 50, 36, 36); self.rect_stop = pygame.Rect(65, 50, 36, 36)
        pygame.draw.rect(self.tela, VERDE_SUCCESS if not self.dados.playing else (241, 196, 15), self.rect_play, border_radius=6)
        sym = ">" if not self.dados.playing else "||"; t_sym = self.fonte_titulo.render(sym, True, BRANCO); self.tela.blit(t_sym, (self.rect_play.centerx - t_sym.get_width()//2, self.rect_play.centery - t_sym.get_height()//2))
        pygame.draw.rect(self.tela, VERMELHO_DANGER, self.rect_stop, border_radius=6)
        pygame.draw.rect(self.tela, BRANCO, (self.rect_stop.centerx - 5, self.rect_stop.centery - 5, 10, 10))
        
        # --- Seleção de Instrumento ---
        self.rect_btn_instrumentos = []
        insts = [("🎸", "other"), ("🎸_", "bass"), ("🥁", "drums"), ("🎤", "vocals")]
        for i, (icon, key) in enumerate(insts):
            rect = pygame.Rect(225 + i * 45, 10, 40, 30); self.rect_btn_instrumentos.append((rect, key))
            cor = AZUL_LINK if self.instrumento_selecionado == key else (45, 45, 55)
            pygame.draw.rect(self.tela, cor, rect, border_radius=6)
            txt = self.fonte_titulo.render(icon, True, BRANCO); self.tela.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

        self.rect_ai = pygame.Rect(410, 10, 120, 30)
        pygame.draw.rect(self.tela, (100, 80, 255), self.rect_ai, border_radius=15)
        txt_ai = self.fonte_ui.render("✨ Transcrever", True, BRANCO); self.tela.blit(txt_ai, (self.rect_ai.centerx - txt_ai.get_width()//2, self.rect_ai.centery - txt_ai.get_height()//2))

        self.rect_import = pygame.Rect(540, 10, 120, 30)
        pygame.draw.rect(self.tela, (46, 204, 113), self.rect_import, border_radius=15)
        txt_imp = self.fonte_ui.render("📁 Importar", True, BRANCO); self.tela.blit(txt_imp, (self.rect_import.centerx - txt_imp.get_width()//2, self.rect_import.centery - txt_imp.get_height()//2))

    def _desenhar_status_ia(self):
        if self.status_ia:
            rect = pygame.Rect(self.largura - 250, 15, 230, 30); pygame.draw.rect(self.tela, (40, 40, 50), rect, border_radius=6)
            txt = self.fonte_ui.render(self.status_ia, True, (255, 200, 0)); self.tela.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

    def _desenhar_scrollbar(self, num_sistemas):
        total_h = num_sistemas * self.espacamento_linhas + self.inicio_y
        if total_h > self.altura:
            razao = (self.altura - 100) / total_h; barra_h = max(20, (self.altura - 100) * razao); barra_y = 100 + (self.scroll_y / total_h) * (self.altura - 100)
            pygame.draw.rect(self.tela, (30, 30, 35), (self.largura - 10, 100, 6, self.altura - 100))
            pygame.draw.rect(self.tela, (100, 100, 110), (self.largura - 10, barra_y, 6, barra_h), border_radius=3)

    def _iniciar_transcricao_ia(self, estado=None):
        if self.processando_ia: return
        
        # Abrir o diálogo na Main Thread (onde o Pygame processa os eventos)
        try:
            root = Tk()
            root.withdraw()
            root.attributes("-topmost", True) # Garante que a janela apareça na frente
            caminho = filedialog.askopenfilename(title="Selecionar Áudio", filetypes=[("Áudio", "*.wav *.mp3 *.ogg")])
            root.destroy()
            
            if caminho and estado and hasattr(estado, 'cliente_ia'):
                estado.cliente_ia.transcrever_arquivo(caminho, estado, instrumento=self.instrumento_selecionado)
        except Exception as e:
            print(f"[UI ERROR] Falha ao abrir seletor de arquivos: {e}")

    def tratar_evento(self, evento, estado=None):
        if evento.type == pygame.MOUSEWHEEL: self.scroll_y = max(0, self.scroll_y - evento.y * 40); return True
        elif evento.type == pygame.KEYDOWN:
            if self.campo_focado: return False
            if evento.key == pygame.K_RIGHT: self.cursor_pos[1] += 1; self.dados._garantir_capacidade(self.cursor_pos[1]); return True
            elif evento.key == pygame.K_LEFT: self.cursor_pos[1] = max(0, self.cursor_pos[1] - 1); return True
            elif evento.key == pygame.K_UP: self.cursor_pos[0] = max(0, self.cursor_pos[0] - 1); return True
            elif evento.key == pygame.K_DOWN: self.cursor_pos[0] = min(5, self.cursor_pos[0] + 1); return True
            elif pygame.K_0 <= evento.key <= pygame.K_9:
                num = str(evento.key - pygame.K_0); atual = self.dados.grade[self.cursor_pos[0]][self.cursor_pos[1]]
                novo = num if atual == "-" or any(c.isalpha() for c in atual) else (atual + num)[:2]
                self.dados.adicionar_nota(self.cursor_pos[0], self.cursor_pos[1], novo); self.synth.tocar_nota(self.cursor_pos[0]+1, int(novo))
                self.cursor_pos[1] += 1; self.dados._garantir_capacidade(self.cursor_pos[1]); return True
            elif evento.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                self.dados.remover_nota(self.cursor_pos[0], self.cursor_pos[1])
                if evento.key == pygame.K_BACKSPACE: self.cursor_pos[1] = max(0, self.cursor_pos[1] - 1)
                return True
            elif evento.key == pygame.K_SPACE:
                if self.dados.playing: self.dados.stop()
                else: self.dados.play(self.synth.tocar_nota)
                return True
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1:
                if evento.pos[1] < 100:
                    for rect, key in self.rect_btn_instrumentos:
                        if rect.collidepoint(evento.pos): self.instrumento_selecionado = key; return True
                    if self.rect_play.collidepoint(evento.pos):
                        if self.dados.playing: self.dados.stop()
                        else: self.dados.play(self.synth.tocar_nota)
                        return True
                    elif self.rect_stop.collidepoint(evento.pos): self.dados.stop(); return True
                    elif self.rect_ai.collidepoint(evento.pos) or self.rect_import.collidepoint(evento.pos):
                        self._iniciar_transcricao_ia(estado); return True
                    return True
                else:
                    if hasattr(self, 'rect_add_sistema') and self.rect_add_sistema.collidepoint(evento.pos):
                        self.dados._garantir_capacidade(len(self.dados.grade[0]) + self.colunas_por_linha); return True
                    t, c = self._obter_coord_clique(evento.pos[0], evento.pos[1])
                    if t is not None: self.cursor_pos = [c, t]; self.dados._garantir_capacidade(t); return True
        return False

    def _obter_coord_clique(self, mx, my):
        if my < 100: return None, None
        y_rel = my + self.scroll_y - self.inicio_y; idx_sistema = int(y_rel // self.espacamento_linhas); y_dentro = y_rel % self.espacamento_linhas
        if y_dentro < -10 or y_dentro > 6 * self.espacamento_cordas + 10: return None, None
        c = max(0, min(5, int((y_dentro + (self.espacamento_cordas//2)) // self.espacamento_cordas)))
        if mx < self.margem_esquerda or mx > self.margem_esquerda + self.colunas_por_linha * self.espacamento_tempos: return None, None
        t_rel = int((mx - self.margem_esquerda + (self.espacamento_tempos//2)) // self.espacamento_tempos)
        return idx_sistema * self.colunas_por_linha + t_rel, c
