import pygame
import threading
import requests
import time
from tkinter import filedialog, Tk
from core.modulos.modulo_dados_tab import GerenciadorDadosTablatura
from audio.tab_synth import MotorAudioDual

# --- CONSTANTES DE ESTILO (Premium Dark Studio) ---
COR_FUNDO = (15, 18, 22)
COR_LINHA_AGUDA = (70, 70, 80)
COR_LINHA_GRAVE = (100, 100, 115)
COR_TEXTO = (230, 230, 240)
COR_CURSOR_OUTLINE = (0, 255, 255)
COR_CURSOR_FILL = (0, 255, 255, 30)
COR_PLAYHEAD = (255, 90, 90)
COR_NOTA_NORMAL = (40, 140, 255)
COR_NOTA_TECNICA = (255, 150, 0)

FUNDO_CONTROLES = (20, 24, 30)
BOTAO_NORMAL = (35, 40, 48)
BOTAO_HOVER = (50, 55, 65)
VERMELHO_DANGER = (220, 53, 69)
VERDE_SUCCESS = (32, 201, 151)
AZUL_LINK = (13, 110, 253)
BRANCO = (255, 255, 255)

class RenderizadorCriadorTablatura:
    def __init__(self, tela, largura, altura):
        self.tela = tela
        self.largura = largura
        self.altura = altura
        
        self.dados = GerenciadorDadosTablatura()
        self.synth = MotorAudioDual(modo="sintetico")
        
        # Cores legadas
        self.COR_FUNDO = COR_FUNDO
        self.COR_LINHA = COR_LINHA_AGUDA
        self.COR_TEXTO = COR_TEXTO
        self.COR_CURSOR = COR_CURSOR_FILL
        self.COR_PLAYHEAD = COR_PLAYHEAD
        self.COR_SELECAO = (52, 152, 219, 80)

        # Configurações de Grade Modernas
        self.margem_esquerda = 50
        self.espacamento_cordas = 18
        self.espacamento_tempos = 32
        self.inicio_y = 120 
        self.espacamento_linhas = 150 

        # UI State
        self.scroll_y = 0
        self.cursor_pos = [0, 0] # [corda, tempo]
        self.campo_focado = None
        self.status_ia = ""
        self.processando_ia = False
        self.instrumento_selecionado = "Guitarra" # Mantendo dict
        self.pos_mouse = (0, 0)
        
        # Fontes Modernas
        self.fonte_mini = pygame.font.SysFont("Segoe UI", 12, bold=True)
        self.fonte_normal = pygame.font.SysFont("Segoe UI", 14, bold=True)
        self.fonte_ui = pygame.font.SysFont("Segoe UI", 14)
        self.fonte_titulo = pygame.font.SysFont("Segoe UI", 18, bold=True)

    def renderizar(self, estado=None):
        self.largura = self.tela.get_width()
        self.altura = self.tela.get_height()
        if estado: self.pos_mouse = getattr(estado, 'pos_mouse_real', pygame.mouse.get_pos())
        
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
            espessura = 1 if i < 3 else 2
            cor_linha = COR_LINHA_AGUDA if i < 3 else COR_LINHA_GRAVE
            pygame.draw.line(self.tela, cor_linha, (self.margem_esquerda, y), (self.margem_esquerda + largura_sistema, y), espessura)
            txt = self.fonte_mini.render(n, True, (130, 130, 140))
            self.tela.blit(txt, (20, y - txt.get_height()//2))

        for t in range(inicio_t, inicio_t + self.colunas_por_linha):
            rel_t = t - inicio_t
            x = self.margem_esquerda + rel_t * self.espacamento_tempos
            
            if t % 16 == 0:
                pygame.draw.line(self.tela, (90, 90, 105), (x, base_y - 8), (x, base_y + 5 * self.espacamento_cordas + 8), 2)
            
            if self.cursor_pos[1] == t: 
                self._desenhar_cursor(x, base_y)
            
            if self.dados.cursor_tempo == t: 
                pygame.draw.polygon(self.tela, COR_PLAYHEAD, [(x - 6, base_y - 12), (x + 6, base_y - 12), (x, base_y - 4)])
                pygame.draw.line(self.tela, COR_PLAYHEAD, (x, base_y - 4), (x, base_y + 5 * self.espacamento_cordas + 10), 2)
            
            if t < len(self.dados.grade[0]):
                for c in range(6):
                    valor = self.dados.grade[c][t]
                    if valor != "-":
                        y_nota = base_y + c * self.espacamento_cordas
                        is_tecnica = any(tec in valor for tec in "bs/\\hp~")
                        cor_fundo_nota = COR_NOTA_TECNICA if is_tecnica else COR_NOTA_NORMAL
                        
                        largura_box = 20 + (len(valor)-1)*6
                        rect_nota = pygame.Rect(x - largura_box//2, y_nota - 9, largura_box, 18)
                        pygame.draw.rect(self.tela, cor_fundo_nota, rect_nota, border_radius=4)
                        
                        txt_n = self.fonte_normal.render(valor, True, BRANCO)
                        self.tela.blit(txt_n, (x - txt_n.get_width()//2, y_nota - txt_n.get_height()//2))

    def _desenhar_botao_adicionar(self, num_sistemas):
        base_y = self.inicio_y + (num_sistemas * self.espacamento_linhas) - self.scroll_y
        if base_y + 50 < 100 or base_y > self.altura: return
        centro_x = self.margem_esquerda + (self.colunas_por_linha * self.espacamento_tempos) // 2
        self.rect_add_sistema = pygame.Rect(centro_x - 24, base_y, 48, 48)
        is_hover = self.rect_add_sistema.collidepoint(self.pos_mouse)
        cor = AZUL_LINK if is_hover else (60, 60, 75)
        
        pygame.draw.circle(self.tela, (30, 30, 38), self.rect_add_sistema.center, 24)
        pygame.draw.circle(self.tela, cor, self.rect_add_sistema.center, 24, 2)
        txt = self.fonte_titulo.render("+", True, cor)
        self.tela.blit(txt, (self.rect_add_sistema.centerx - txt.get_width()//2, self.rect_add_sistema.centery - txt.get_height()//2 - 2))

    def _desenhar_cursor(self, x, base_y):
        y = base_y + self.cursor_pos[0] * self.espacamento_cordas
        rect = pygame.Rect(x - self.espacamento_tempos // 2 + 2, y - self.espacamento_cordas // 2, self.espacamento_tempos - 4, self.espacamento_cordas)
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        s.fill(COR_CURSOR_FILL)
        self.tela.blit(s, rect.topleft)
        pygame.draw.rect(self.tela, COR_CURSOR_OUTLINE, rect, 2, border_radius=4)

    def _desenhar_toolbar(self):
        pygame.draw.rect(self.tela, (10, 12, 15), (0, 95, self.largura, 10))
        pygame.draw.rect(self.tela, FUNDO_CONTROLES, (0, 0, self.largura, 95))
        pygame.draw.line(self.tela, (40, 45, 55), (0, 95), (self.largura, 95), 1)
        
        txt_proj = self.fonte_titulo.render(f"TAB: {self.dados.nome_musica}", True, BRANCO)
        self.tela.blit(txt_proj, (30, 20))
        
        self.rect_play = pygame.Rect(30, 50, 40, 36)
        self.rect_stop = pygame.Rect(80, 50, 40, 36)
        
        hover_play = self.rect_play.collidepoint(self.pos_mouse)
        cor_play = VERDE_SUCCESS if not self.dados.playing else (241, 196, 15)
        if hover_play: cor_play = (min(255, cor_play[0]+30), min(255, cor_play[1]+30), min(255, cor_play[2]+30))
        pygame.draw.rect(self.tela, cor_play, self.rect_play, border_radius=8)
        sym = "▶" if not self.dados.playing else "⏸"
        t_sym = self.fonte_titulo.render(sym, True, BRANCO)
        self.tela.blit(t_sym, (self.rect_play.centerx - t_sym.get_width()//2, self.rect_play.centery - t_sym.get_height()//2))
        
        hover_stop = self.rect_stop.collidepoint(self.pos_mouse)
        cor_stop = (255, 100, 100) if hover_stop else VERMELHO_DANGER
        pygame.draw.rect(self.tela, cor_stop, self.rect_stop, border_radius=8)
        pygame.draw.rect(self.tela, BRANCO, (self.rect_stop.centerx - 6, self.rect_stop.centery - 6, 12, 12), border_radius=2)
        
        # --- Seleção de Instrumento ---
        self.rect_btn_instrumentos = []
        insts = [("🎸", "Guitarra"), ("🎸_", "Baixo"), ("🥁", "Bateria"), ("🎤", "Voz")]
        base_x_inst = 250
        for i, (icon, key) in enumerate(insts):
            rect = pygame.Rect(base_x_inst + i * 50, 15, 45, 36)
            self.rect_btn_instrumentos.append((rect, key))
            is_hover = rect.collidepoint(self.pos_mouse)
            cor = AZUL_LINK if self.instrumento_selecionado == key else (BOTAO_HOVER if is_hover else BOTAO_NORMAL)
            pygame.draw.rect(self.tela, cor, rect, border_radius=8)
            txt = self.fonte_titulo.render(icon, True, BRANCO)
            self.tela.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

        self.rect_ai = pygame.Rect(500, 15, 140, 36)
        cor_ai = (120, 100, 255) if self.rect_ai.collidepoint(self.pos_mouse) else (100, 80, 255)
        pygame.draw.rect(self.tela, cor_ai, self.rect_ai, border_radius=18)
        txt_ai = self.fonte_ui.render("✨ Transcrever", True, BRANCO)
        self.tela.blit(txt_ai, (self.rect_ai.centerx - txt_ai.get_width()//2, self.rect_ai.centery - txt_ai.get_height()//2))

        self.rect_import = pygame.Rect(650, 15, 120, 36)
        cor_imp = (60, 220, 130) if self.rect_import.collidepoint(self.pos_mouse) else VERDE_SUCCESS
        pygame.draw.rect(self.tela, cor_imp, self.rect_import, border_radius=18)
        txt_imp = self.fonte_ui.render("📁 Importar", True, BRANCO)
        self.tela.blit(txt_imp, (self.rect_import.centerx - txt_imp.get_width()//2, self.rect_import.centery - txt_imp.get_height()//2))

        self.rect_save = pygame.Rect(780, 15, 120, 36)
        cor_save = (30, 140, 255) if self.rect_save.collidepoint(self.pos_mouse) else (0, 120, 215)
        pygame.draw.rect(self.tela, cor_save, self.rect_save, border_radius=18)
        txt_save = self.fonte_ui.render("💾 Salvar", True, BRANCO)
        self.tela.blit(txt_save, (self.rect_save.centerx - txt_save.get_width()//2, self.rect_save.centery - txt_save.get_height()//2))

        # --- Toggle Dual-Engine ---
        self.rect_toggle_audio = pygame.Rect(self.largura - 460, 15, 180, 36)
        cor_toggle = (50, 150, 255) if self.synth.modo == "realista" else (100, 100, 120)
        pygame.draw.rect(self.tela, cor_toggle, self.rect_toggle_audio, border_radius=18)
        txt_modo = "Modo de Som: Realista" if self.synth.modo == "realista" else "Modo de Som: Sintético"
        txt_t = self.fonte_ui.render(txt_modo, True, BRANCO)
        self.tela.blit(txt_t, (self.rect_toggle_audio.centerx - txt_t.get_width()//2, self.rect_toggle_audio.centery - txt_t.get_height()//2))

    def _desenhar_status_ia(self):
        if self.status_ia:
            rect = pygame.Rect(self.largura - 260, 20, 240, 36)
            pygame.draw.rect(self.tela, (35, 40, 45), rect, border_radius=8)
            pygame.draw.rect(self.tela, (255, 200, 0), rect, 1, border_radius=8)
            txt = self.fonte_ui.render(self.status_ia, True, (255, 200, 0))
            self.tela.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

    def _desenhar_scrollbar(self, num_sistemas):
        total_h = num_sistemas * self.espacamento_linhas + self.inicio_y
        if total_h > self.altura:
            razao = (self.altura - 110) / total_h
            barra_h = max(30, (self.altura - 110) * razao)
            barra_y = 110 + (self.scroll_y / total_h) * (self.altura - 110)
            pygame.draw.rect(self.tela, (25, 25, 30), (self.largura - 12, 110, 8, self.altura - 110))
            pygame.draw.rect(self.tela, (90, 95, 110), (self.largura - 12, barra_y, 8, barra_h), border_radius=4)

    def _salvar_projeto(self, estado):
        if not estado or not hasattr(estado, 'db') or not estado.usuario_id_logado:
            print("[UI] Erro: Usuário não logado ou Banco de Dados indisponível.")
            return

        import json
        dados_json = json.dumps({
            "bpm": self.dados.bpm,
            "grade": self.dados.grade,
            "nome": self.dados.nome_musica
        })
        
        sucesso = estado.db.salvar_projeto(estado.usuario_id_logado, self.dados.nome_musica, "tablatura", dados_json)
        if sucesso:
            print(f"[UI] Projeto '{self.dados.nome_musica}' salvo com sucesso!")
            self.status_ia = "✅ PROJETO SALVO"
        else:
            print("[UI] Erro ao salvar projeto no banco.")
            self.status_ia = "❌ ERRO AO SALVAR"

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
        if evento.type == pygame.MOUSEWHEEL: 
            self.scroll_y = max(0, self.scroll_y - evento.y * 40)
            return True
        elif evento.type == pygame.KEYDOWN:
            if self.campo_focado: return False
            if evento.key == pygame.K_RIGHT: 
                self.cursor_pos[1] += 1
                self.dados._garantir_capacidade(self.cursor_pos[1])
                return True
            elif evento.key == pygame.K_LEFT: 
                self.cursor_pos[1] = max(0, self.cursor_pos[1] - 1)
                return True
            elif evento.key == pygame.K_UP: 
                self.cursor_pos[0] = max(0, self.cursor_pos[0] - 1)
                return True
            elif evento.key == pygame.K_DOWN: 
                self.cursor_pos[0] = min(5, self.cursor_pos[0] + 1)
                return True
            elif pygame.K_0 <= evento.key <= pygame.K_9:
                num = str(evento.key - pygame.K_0)
                atual = self.dados.grade[self.cursor_pos[0]][self.cursor_pos[1]]
                novo = num if atual == "-" or any(c.isalpha() for c in atual) else (atual + num)[:2]
                self.dados.adicionar_nota(self.cursor_pos[0], self.cursor_pos[1], novo)
                self.synth.reproduzir_nota(self.cursor_pos[0]+1, int(novo))
                self.cursor_pos[1] += 1
                self.dados._garantir_capacidade(self.cursor_pos[1])
                return True
            elif evento.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                self.dados.remover_nota(self.cursor_pos[0], self.cursor_pos[1])
                if evento.key == pygame.K_BACKSPACE: 
                    self.cursor_pos[1] = max(0, self.cursor_pos[1] - 1)
                return True
            elif evento.key == pygame.K_SPACE:
                if self.dados.playing: self.dados.stop()
                else: self.dados.play(self.synth.reproduzir_nota)
                return True
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1:
                if evento.pos[1] < 110:
                    for rect, key in self.rect_btn_instrumentos:
                        if rect.collidepoint(evento.pos): 
                            self.instrumento_selecionado = key
                            self.dados.alternar_instrumento(key)
                            self.synth.alternar_instrumento_synth(key)
                            return True
                    if hasattr(self, 'rect_toggle_audio') and self.rect_toggle_audio.collidepoint(evento.pos):
                        novo_modo = "realista" if self.synth.modo == "sintetico" else "sintetico"
                        self.synth.alternar_modo(novo_modo)
                        return True
                    if self.rect_play.collidepoint(evento.pos):
                        if self.dados.playing: self.dados.stop()
                        else: self.dados.play(self.synth.reproduzir_nota)
                        return True
                    elif self.rect_stop.collidepoint(evento.pos): 
                        self.dados.stop()
                        return True
                    elif self.rect_ai.collidepoint(evento.pos) or self.rect_import.collidepoint(evento.pos):
                        self._iniciar_transcricao_ia(estado)
                        return True
                    elif self.rect_save.collidepoint(evento.pos):
                        self._salvar_projeto(estado)
                        return True
                    return True
                else:
                    if hasattr(self, 'rect_add_sistema') and self.rect_add_sistema.collidepoint(evento.pos):
                        self.dados._garantir_capacidade(len(self.dados.grade[0]) + self.colunas_por_linha)
                        return True
                    t, c = self._obter_coord_clique(evento.pos[0], evento.pos[1])
                    if t is not None: 
                        self.cursor_pos = [c, t]
                        self.dados._garantir_capacidade(t)
                        return True
        return False

    def _obter_coord_clique(self, mx, my):
        if my < 110: return None, None
        y_rel = my + self.scroll_y - self.inicio_y
        idx_sistema = int(y_rel // self.espacamento_linhas)
        y_dentro = y_rel % self.espacamento_linhas
        if y_dentro < -10 or y_dentro > 6 * self.espacamento_cordas + 10: return None, None
        c = max(0, min(5, int((y_dentro + (self.espacamento_cordas//2)) // self.espacamento_cordas)))
        if mx < self.margem_esquerda or mx > self.margem_esquerda + self.colunas_por_linha * self.espacamento_tempos: return None, None
        t_rel = int((mx - self.margem_esquerda + (self.espacamento_tempos//2)) // self.espacamento_tempos)
        return idx_sistema * self.colunas_por_linha + t_rel, c
