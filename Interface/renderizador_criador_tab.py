import pygame
from Modulos.modulo_dados_tab import GerenciadorDadosTablatura
from Modulos.modulo_synth_guitarra import SintetizadorGuitarra

# --- CONSTANTES DE LAYOUT PARA EVITAR SOBREPOSIÇÃO ---
# Menu Superior Global: Y=0 a Y=40
# Top Bar / Drag Handle Global: Y=75 a Y=115
GLOBAL_OFFSET_Y = 125 # Tudo deve começar APÓS isso

class RenderizadorCriadorTablatura:
    def __init__(self, tela, largura, altura):
        self.tela = tela
        self.largura = largura
        self.altura = altura
        
        self.dados = GerenciadorDadosTablatura()
        self.synth = SintetizadorGuitarra()
        
        # Cores
        self.COR_FUNDO = (20, 20, 22)
        self.COR_LINHA = (65, 65, 70)
        self.COR_TEXTO = (180, 180, 185)
        self.COR_CURSOR = (0, 255, 255, 80)
        self.COR_ATALHO = (0, 255, 255)

        # Configurações de Grade
        self.margem_esquerda = 60
        self.espacamento_cordas = 26
        self.espacamento_tempos = 32
        self.inicio_y = 300 # Empurrado para baixo para dar espaço aos novos controles
        self.espacamento_linhas = 200
        
        # Layout Dinâmico
        self.colunas_por_compasso = 16 
        self.colunas_por_linha = 64
        
        # Estado da UI
        self.scroll_y = 0
        self.cursor_pos = [0, 0] # [corda, tempo]
        self.campo_focado = None # "nome" ou "bpm"
        self.arrastando_playhead = False
        
        self.fonte = pygame.font.SysFont("Arial", 16)
        self.fonte_pequena = pygame.font.SysFont("Arial", 12)
        self.fonte_titulo = pygame.font.SysFont("Arial", 18, bold=True)
        self.fonte_bold = pygame.font.SysFont("Arial", 14, bold=True)

    def renderizar(self):
        # Recalcula colunas por linha dinamicamente baseado na largura da tela
        largura_util = self.largura - self.margem_esquerda - 60
        self.colunas_por_linha = max(16, (largura_util // self.espacamento_tempos))
        # Arredonda para o compasso mais próximo (16 colunas)
        self.colunas_por_linha = (self.colunas_por_linha // 16) * 16
        if self.colunas_por_linha == 0: self.colunas_por_linha = 16

        self._verificar_autoscroll()
        self.tela.fill(self.COR_FUNDO)
        
        # 1. Desenha o Grid de Tablatura com Quebra de Linha Dinâmica
        area_limite_y = 180 # Onde a tab começa a aparecer
        num_colunas_total = len(self.dados.grade[0])
        num_linhas_tab = (num_colunas_total + self.colunas_por_linha - 1) // self.colunas_por_linha
        
        nomes_cordas = ["e", "B", "G", "D", "A", "E"]
        
        for linha_idx in range(num_linhas_tab):
            # Base Y para esta linha de tablatura (6 cordas)
            base_y = self.inicio_y + (linha_idx * self.espacamento_linhas) - self.scroll_y
            
            # Culling Vertical: Só desenha se estiver visível na tela
            if base_y + self.espacamento_linhas < area_limite_y or base_y > self.altura:
                continue
                
            # Desenha as 6 cordas da linha
            for i in range(6):
                y = base_y + i * self.espacamento_cordas
                pygame.draw.line(self.tela, self.COR_LINHA, (self.margem_esquerda, y), (self.margem_esquerda + self.colunas_por_linha * self.espacamento_tempos, y), 1)
                
                # Nome da corda (apenas no início da linha)
                txt = self.fonte_pequena.render(nomes_cordas[i], True, (120, 120, 120))
                self.tela.blit(txt, (20, y - 8))

            # Desenha Notas e Compassos para esta linha
            inicio_col = linha_idx * self.colunas_por_linha
            fim_col = min(inicio_col + self.colunas_por_linha, num_colunas_total)
            
            for t in range(inicio_col, fim_col):
                rel_t = t - inicio_col
                x = self.margem_esquerda + rel_t * self.espacamento_tempos
                
                # Divisórias de Compasso
                if t % self.colunas_por_compasso == 0:
                    pygame.draw.line(self.tela, (100, 100, 105), (x, base_y - 10), (x, base_y + 5 * self.espacamento_cordas + 10), 2)
                elif t % 4 == 0:
                    pygame.draw.line(self.tela, (60, 60, 65), (x, base_y), (x, base_y + 5 * self.espacamento_cordas), 1)

                # Notas
                for c in range(6):
                    y = base_y + c * self.espacamento_cordas
                    valor = self.dados.grade[c][t]
                    
                    if valor != "-":
                        pygame.draw.circle(self.tela, (35, 35, 40), (x, y), 11)
                        txt_nota = self.fonte_pequena.render(valor, True, self.COR_ATALHO)
                        self.tela.blit(txt_nota, (x - txt_nota.get_width()//2, y - txt_nota.get_height()//2))

                # Cursor de Edição
                if self.cursor_pos[1] == t:
                    cursor_y = base_y + self.cursor_pos[0] * self.espacamento_cordas
                    s = pygame.Surface((self.espacamento_tempos, self.espacamento_cordas), pygame.SRCALPHA)
                    s.fill((0, 255, 255, 40))
                    self.tela.blit(s, (x - self.espacamento_tempos//2, cursor_y - self.espacamento_cordas//2))
                    pygame.draw.rect(self.tela, (0, 255, 255), (x - self.espacamento_tempos//2, cursor_y - self.espacamento_cordas//2, self.espacamento_tempos, self.espacamento_cordas), 1, border_radius=3)

                # Cursor de Playback (Playhead)
                if self.dados.cursor_tempo == t:
                    pygame.draw.line(self.tela, (255, 80, 80), (x, base_y - 15), (x, base_y + 5 * self.espacamento_cordas + 15), 2)

        # 2. Desenha a Barra de Scroll Vertical
        self._desenhar_scrollbar(num_linhas_tab)
        
        # 3. Painel Superior
        self._desenhar_painel_superior()

    def _desenhar_scrollbar(self, num_linhas):
        total_h = num_linhas * self.espacamento_linhas + self.inicio_y
        if total_h > self.altura:
            razao = self.altura / (total_h + 400)
            barra_h = self.altura * razao
            barra_y = (self.scroll_y / (total_h + 400)) * self.altura
            pygame.draw.rect(self.tela, (40, 40, 45), (self.largura - 12, 0, 8, self.altura))
            pygame.draw.rect(self.tela, (80, 80, 90), (self.largura - 12, barra_y, 8, barra_h), border_radius=4)

    def _desenhar_painel_superior(self):
        # --- ZONA SEGURA SUPERIOR (Y=45 a 70) ---
        # Fica entre o Menu (Y=40) e o Drag Handle (Y=75)
        pygame.draw.rect(self.tela, (25, 25, 30), (0, 45, self.largura, 30))
        pygame.draw.line(self.tela, (50, 50, 55), (0, 75), (self.largura, 75), 1)

        # Nome da Música (Zona Superior)
        self.rect_nome = pygame.Rect(10, 48, 180, 24)
        pygame.draw.rect(self.tela, (15, 15, 20), self.rect_nome, border_radius=4)
        txt_nome = self.fonte_pequena.render(self.dados.nome_musica[:20], True, (255, 255, 255))
        self.tela.blit(txt_nome, (18, 52))

        # Botões de Ação (Zona Superior - Direita)
        # Afastado do Botão PIN (que fica no extremo topo direito)
        self.rect_salvar = pygame.Rect(self.largura - 240, 48, 90, 24)
        pygame.draw.rect(self.tela, (52, 152, 219), self.rect_salvar, border_radius=4)
        ts = self.fonte_pequena.render("SALVAR", True, (255, 255, 255))
        self.tela.blit(ts, (self.rect_salvar.centerx - ts.get_width()//2, self.rect_salvar.centery - ts.get_height()//2))

        self.rect_limpar = pygame.Rect(self.largura - 140, 48, 90, 24)
        pygame.draw.rect(self.tela, (149, 165, 166), self.rect_limpar, border_radius=4)
        tl = self.fonte_pequena.render("LIMPAR", True, (255, 255, 255))
        self.tela.blit(tl, (self.rect_limpar.centerx - tl.get_width()//2, self.rect_limpar.centery - tl.get_height()//2))


        # --- ZONA SEGURA INFERIOR (Y=120 a 200) ---
        # Fica abaixo do Drag Handle (Y=115)
        pygame.draw.rect(self.tela, (22, 22, 28), (0, 120, self.largura, 80))
        pygame.draw.line(self.tela, (60, 60, 65), (0, 200), (self.largura, 200), 2)

        # 2. Reprodução (Centro Inferior)
        cx = self.largura // 2
        self.rect_play = pygame.Rect(cx - 100, 135, 50, 50)
        self.rect_stop = pygame.Rect(cx - 40, 135, 50, 50)
        
        pygame.draw.circle(self.tela, (46, 204, 113) if not self.dados.playing else (241, 196, 15), self.rect_play.center, 25)
        txt_p = "II" if self.dados.playing else ">"
        t_play = self.fonte_titulo.render(txt_p, True, (255, 255, 255))
        self.tela.blit(t_play, (self.rect_play.centerx - t_play.get_width()//2, self.rect_play.centery - t_play.get_height()//2))

        pygame.draw.circle(self.tela, (VERMELHO_DANGER if 'VERMELHO_DANGER' in locals() else (231, 76, 60)), self.rect_stop.center, 25)
        pygame.draw.rect(self.tela, (255, 255, 255), (self.rect_stop.centerx - 8, self.rect_stop.centery - 8, 16, 16))

        # 3. Técnicas (Lado Esquerdo Inferior)
        tecnicas = [("B", "b"), ("S", "/"), ("H", "h"), ("P", "p")]
        self.btns_tecnicas = {}
        for i, (label, char) in enumerate(tecnicas):
            rect = pygame.Rect(20 + i * 50, 135, 45, 45)
            pygame.draw.rect(self.tela, (50, 50, 60), rect, border_radius=8)
            pygame.draw.rect(self.tela, (100, 100, 110), rect, 1, border_radius=8)
            txt = self.fonte_bold.render(label, True, (255, 255, 255))
            self.tela.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))
            self.btns_tecnicas[char] = rect

        # 4. BPM (Direita Inferior)
        self.rect_bpm_menos = pygame.Rect(self.largura - 160, 142, 35, 35)
        self.rect_bpm = pygame.Rect(self.largura - 120, 142, 60, 35)
        self.rect_bpm_mais = pygame.Rect(self.largura - 55, 142, 35, 35)
        
        for r, t in [(self.rect_bpm_mais, "+"), (self.rect_bpm_menos, "-")]:
            pygame.draw.rect(self.tela, (60, 60, 70), r, border_radius=5)
            txt = self.fonte.render(t, True, (255, 255, 255))
            self.tela.blit(txt, (r.centerx - txt.get_width()//2, r.centery - txt.get_height()//2))
        
        pygame.draw.rect(self.tela, (15, 15, 20), self.rect_bpm, border_radius=5)
        t_bpm = self.fonte_bold.render(str(self.dados.bpm), True, (0, 255, 255))
        self.tela.blit(t_bpm, (self.rect_bpm.centerx - t_bpm.get_width()//2, self.rect_bpm.centery - t_bpm.get_height()//2))

    def tratar_evento(self, evento, estado=None):
        if evento.type == pygame.KEYDOWN:
            if self.campo_focado == "nome":
                if evento.key == pygame.K_BACKSPACE:
                    self.dados.nome_musica = self.dados.nome_musica[:-1]
                elif evento.key == pygame.K_RETURN or evento.key == pygame.K_ESCAPE:
                    self.campo_focado = None
                elif len(evento.unicode) > 0 and evento.unicode.isprintable():
                    self.dados.nome_musica += evento.unicode
                return

            if evento.key == pygame.K_SPACE:
                if self.dados.playing: self.dados.stop()
                else: self.dados.play(self.synth.tocar_nota)
            elif evento.key == pygame.K_DELETE or evento.key == pygame.K_BACKSPACE:
                self.dados.remover_nota(self.cursor_pos[0], self.cursor_pos[1])
            elif evento.key == pygame.K_RIGHT:
                self.cursor_pos[1] += 1
                if self.cursor_pos[1] >= len(self.dados.grade[0]):
                    for c in range(6): self.dados.grade[c].append("-")
            elif evento.key == pygame.K_LEFT:
                self.cursor_pos[1] = max(0, self.cursor_pos[1] - 1)
            elif evento.key == pygame.K_UP:
                self.cursor_pos[0] = max(0, self.cursor_pos[0] - 1)
            elif evento.key == pygame.K_DOWN:
                self.cursor_pos[0] = min(5, self.cursor_pos[0] + 1)
            elif evento.key == pygame.K_b: self._adicionar_tecnica("b")
            elif evento.key == pygame.K_s or evento.key == 47: self._adicionar_tecnica("/") # "/" key
            elif evento.key == pygame.K_h: self._adicionar_tecnica("h")
            elif evento.key == pygame.K_p: self._adicionar_tecnica("p")
            elif pygame.K_0 <= evento.key <= pygame.K_9:
                num = str(evento.key - pygame.K_0)
                atual = self.dados.grade[self.cursor_pos[0]][self.cursor_pos[1]]
                val_limpo = atual.strip("bs/\\hp")
                if val_limpo == "-" or len(val_limpo) >= 2: novo = num
                else: novo = val_limpo + num
                self.dados.adicionar_nota(self.cursor_pos[0], self.cursor_pos[1], novo)
                self.synth.tocar_nota(self.cursor_pos[0]+1, int(novo))

        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 4: # Scroll Up
                self.scroll_y = max(0, self.scroll_y - 60)
            elif evento.button == 5: # Scroll Down
                self.scroll_y += 60
            
            elif evento.button == 1: # Clique Esquerdo
                mouse_x, mouse_y = evento.pos
                
                # Botões do Painel Superior
                if self.rect_play.collidepoint(evento.pos):
                    if self.dados.playing: self.dados.stop()
                    else: self.dados.play(self.synth.tocar_nota)
                elif self.rect_stop.collidepoint(evento.pos):
                    self.dados.stop()
                    self.dados.cursor_tempo = 0
                elif self.rect_bpm_mais.collidepoint(evento.pos):
                    self.dados.bpm = min(300, self.dados.bpm + 5)
                elif self.rect_bpm_menos.collidepoint(evento.pos):
                    self.dados.bpm = max(10, self.dados.bpm - 5)
                elif self.rect_salvar.collidepoint(evento.pos):
                    self._salvar_no_banco(estado)
                elif self.rect_limpar.collidepoint(evento.pos):
                    self.dados.limpar_tablatura()
                elif self.rect_nome.collidepoint(evento.pos):
                    self.campo_focado = "nome"
                
                # Botões de Técnica
                else:
                    clicou_tec = False
                    for char, rect in self.btns_tecnicas.items():
                        if rect.collidepoint(evento.pos):
                            self._adicionar_tecnica(char)
                            clicou_tec = True
                            break
                    
                    if not clicou_tec:
                        # Clique na Tablatura (Seleção e Playhead)
                        if mouse_y > 180: # Ajustado para o novo limite da tab
                            t_click, c_click = self._obter_coord_clique(mouse_x, mouse_y)
                            if t_click is not None:
                                self.cursor_pos = [c_click, t_click]
                                if abs(t_click - self.dados.cursor_tempo) < 2:
                                    self.arrastando_playhead = True
            
            elif evento.button == 3: # Clique Direito: Pula Playhead direto
                mouse_x, mouse_y = evento.pos
                t_click, _ = self._obter_coord_clique(mouse_x, mouse_y)
                if t_click is not None:
                    self.dados.cursor_tempo = t_click

        elif evento.type == pygame.MOUSEBUTTONUP:
            if evento.button == 1:
                self.arrastando_playhead = False

        elif evento.type == pygame.MOUSEMOTION:
            if self.arrastando_playhead:
                t_drag, _ = self._obter_coord_clique(evento.pos[0], evento.pos[1])
                if t_drag is not None:
                    self.dados.cursor_tempo = t_drag

    def _obter_coord_clique(self, mx, my):
        y_efetivo = my + self.scroll_y - self.inicio_y
        linha_idx = int(y_efetivo / self.espacamento_linhas)
        rel_y = y_efetivo % self.espacamento_linhas
        
        # Margem de segurança para não clicar fora das cordas
        if rel_y < -20 or rel_y > 6 * self.espacamento_cordas + 20:
            return None, None
            
        c = max(0, min(5, int((rel_y + self.espacamento_cordas//2) / self.espacamento_cordas)))
        rel_t = int((mx - self.margem_esquerda + self.espacamento_tempos//2) / self.espacamento_tempos)
        
        if 0 <= rel_t < self.colunas_por_linha:
            t = linha_idx * self.colunas_por_linha + rel_t
            if 0 <= t < len(self.dados.grade[0]):
                return t, c
        return None, None

    def _salvar_no_banco(self, estado):
        """Salva a tablatura atual no banco de dados remoto."""
        if not estado or not getattr(estado, 'usuario_id_logado', None):
            print("[TAB] Erro: Usuário não logado. Não é possível salvar no perfil.")
            return

        from BD.gerenciador_remoto_db import GerenciadorDB
        import json
        
        db = GerenciadorDB()
        dados_json = json.dumps({
            "bpm": self.dados.bpm,
            "grade": self.dados.grade
        })
        
        sucesso = db.salvar_projeto(
            usuario_id=estado.usuario_id_logado,
            nome=self.dados.nome_musica,
            tipo="tablatura",
            dados_json=dados_json
        )
        
        if sucesso:
            print(f"[TAB] Música '{self.dados.nome_musica}' salva com sucesso no perfil!")
        else:
            print("[TAB] Erro ao salvar música no banco de dados.")

    def _adicionar_tecnica(self, char):
        atual = self.dados.grade[self.cursor_pos[0]][self.cursor_pos[1]]
        if atual != "-" and char not in atual:
            self.dados.adicionar_nota(self.cursor_pos[0], self.cursor_pos[1], atual + char)

    def _verificar_autoscroll(self):
        """Garante que o playhead esteja visível durante a reprodução."""
        if not self.dados.playing:
            return
            
        t = self.dados.cursor_tempo
        linha_idx = t // self.colunas_por_linha
        base_y = self.inicio_y + (linha_idx * self.espacamento_linhas) - self.scroll_y
        
        if base_y > self.altura - 100:
            self.scroll_y += self.espacamento_linhas
        elif base_y < 120:
            self.scroll_y = max(0, self.scroll_y - self.espacamento_linhas)

if __name__ == "__main__":
    pygame.init()
    largura, altura = 1000, 600
    tela = pygame.display.set_mode((largura, altura))
    pygame.display.set_caption("Guitar Studio - Criador de Tablaturas")
    
    renderizador = RenderizadorCriadorTablatura(tela, largura, altura)
    clock = pygame.time.Clock()
    
    executando = True
    while executando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                executando = False
            renderizador.tratar_evento(evento)
            
        renderizador.renderizar()
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
