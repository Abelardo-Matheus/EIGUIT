import pygame
from Modulos.modulo_dados_tab import GerenciadorDadosTablatura
from Modulos.modulo_synth_guitarra import SintetizadorGuitarra

class RenderizadorCriadorTablatura:
    def __init__(self, tela, largura, altura):
        self.tela = tela
        self.largura = largura
        self.altura = altura
        
        self.dados = GerenciadorDadosTablatura()
        self.synth = SintetizadorGuitarra()
        
        # Cores
        self.COR_FUNDO = (30, 30, 30)
        self.COR_LINHA = (100, 100, 100)
        self.COR_TEXTO = (200, 200, 200)
        self.COR_CURSOR = (255, 255, 0, 100)
        self.COR_ATALHO = (0, 255, 255)

        # Configurações de Grade
        self.margem_esquerda = 50
        self.espacamento_cordas = 40
        self.espacamento_tempos = 40
        self.inicio_y = 150
        
        # Estado da UI
        self.scroll_x = 0
        self.cursor_pos = [0, 0] # [corda, tempo]
        self.campo_focado = None # "nome" ou "bpm"
        
        self.fonte = pygame.font.SysFont("Arial", 20)
        self.fonte_pequena = pygame.font.SysFont("Arial", 16)
        self.fonte_titulo = pygame.font.SysFont("Arial", 24, bold=True)

    def renderizar(self):
        self.tela.fill(self.COR_FUNDO)
        
        # Desenha as 6 linhas (cordas)
        nomes_cordas = ["e", "B", "G", "D", "A", "E"]
        for i in range(6):
            y = self.inicio_y + i * self.espacamento_cordas
            pygame.draw.line(self.tela, self.COR_LINHA, (self.margem_esquerda, y), (self.largura, y), 2)
            
            # Nome da corda
            txt = self.fonte.render(nomes_cordas[i], True, self.COR_TEXTO)
            self.tela.blit(txt, (10, y - 10))

        # Calcula quais colunas (tempos) estão visíveis (Culling)
        primeiro_tempo = int(self.scroll_x / self.espacamento_tempos)
        num_visiveis = int((self.largura - self.margem_esquerda) / self.espacamento_tempos) + 1
        ultimo_tempo = min(primeiro_tempo + num_visiveis, len(self.dados.grade[0]))

        # Desenha as notas e colunas verticais
        for t in range(primeiro_tempo, ultimo_tempo):
            x = self.margem_esquerda + t * self.espacamento_tempos - self.scroll_x
            
            # Linha vertical de tempo
            if t % 4 == 0: # Marcação de tempo forte
                pygame.draw.line(self.tela, (60, 60, 60), (x, self.inicio_y - 20), (x, self.inicio_y + 5 * self.espacamento_cordas + 20), 1)

            for c in range(6):
                y = self.inicio_y + c * self.espacamento_cordas
                valor = self.dados.grade[c][t]
                
                if valor != "-":
                    # Desenha a nota (fundo circular para legibilidade)
                    pygame.draw.circle(self.tela, (50, 50, 50), (x, y), 14)
                    pygame.draw.circle(self.tela, self.COR_ATALHO, (x, y), 14, 1)
                    txt_nota = self.fonte_pequena.render(valor, True, self.COR_ATALHO)
                    self.tela.blit(txt_nota, (x - txt_nota.get_width()//2, y - txt_nota.get_height()//2))

        # Desenha Cursor de Edição
        cursor_x = self.margem_esquerda + self.cursor_pos[1] * self.espacamento_tempos - self.scroll_x
        cursor_y = self.inicio_y + self.cursor_pos[0] * self.espacamento_cordas
        if self.margem_esquerda <= cursor_x <= self.largura:
            s = pygame.Surface((self.espacamento_tempos, self.espacamento_cordas), pygame.SRCALPHA)
            s.fill((255, 255, 0, 80))
            self.tela.blit(s, (cursor_x - self.espacamento_tempos//2, cursor_y - self.espacamento_cordas//2))

        # Barra de Status/Ferramentas
        self._desenhar_painel_superior()

    def _desenhar_painel_superior(self):
        # Cabeçalho Fundo
        pygame.draw.rect(self.tela, (40, 40, 45), (0, 0, self.largura, 120))
        pygame.draw.line(self.tela, (80, 80, 85), (0, 120), (self.largura, 120), 2)

        # 1. Campo Nome da Música
        lbl_nome = self.fonte_pequena.render("MÚSICA:", True, (150, 150, 150))
        self.tela.blit(lbl_nome, (20, 20))
        self.rect_nome = pygame.Rect(20, 40, 300, 35)
        cor_borda_nome = (0, 255, 255) if self.campo_focado == "nome" else (100, 100, 100)
        pygame.draw.rect(self.tela, (30, 30, 35), self.rect_nome, border_radius=5)
        pygame.draw.rect(self.tela, cor_borda_nome, self.rect_nome, 1, border_radius=5)
        txt_nome = self.fonte.render(self.dados.nome_musica, True, (255, 255, 255))
        self.tela.blit(txt_nome, (30, 45))

        # 2. Campo BPM
        lbl_bpm = self.fonte_pequena.render("BPM:", True, (150, 150, 150))
        self.tela.blit(lbl_bpm, (340, 20))
        self.rect_bpm = pygame.Rect(340, 40, 80, 35)
        cor_borda_bpm = (0, 255, 255) if self.campo_focado == "bpm" else (100, 100, 100)
        pygame.draw.rect(self.tela, (30, 30, 35), self.rect_bpm, border_radius=5)
        pygame.draw.rect(self.tela, cor_borda_bpm, self.rect_bpm, 1, border_radius=5)
        txt_bpm = self.fonte.render(str(self.dados.bpm), True, (255, 255, 255))
        self.tela.blit(txt_bpm, (350, 45))

        # 3. Botão Salvar
        self.rect_salvar = pygame.Rect(440, 40, 120, 35)
        pygame.draw.rect(self.tela, (46, 204, 113), self.rect_salvar, border_radius=5)
        txt_salvar = self.fonte.render("SALVAR", True, (255, 255, 255))
        self.tela.blit(txt_salvar, (self.rect_salvar.centerx - txt_salvar.get_width()//2, self.rect_salvar.centery - txt_salvar.get_height()//2))

        # 4. Botão Limpar
        self.rect_limpar = pygame.Rect(570, 40, 120, 35)
        pygame.draw.rect(self.tela, (231, 76, 60), self.rect_limpar, border_radius=5)
        txt_limpar = self.fonte.render("LIMPAR", True, (255, 255, 255))
        self.tela.blit(txt_limpar, (self.rect_limpar.centerx - txt_limpar.get_width()//2, self.rect_limpar.centery - txt_limpar.get_height()//2))
        
        instrucoes = self.fonte_pequena.render("Setas: Mover | Números: Inserir | b: Bend | s: Slide | Espaço: Play/Stop", True, (150, 150, 150))
        self.tela.blit(instrucoes, (20, 90))
        
        if self.dados.playing:
            play_txt = self.fonte.render("REPRODUZINDO...", True, (0, 255, 0))
            self.tela.blit(play_txt, (self.largura - 200, 40))

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

            elif self.campo_focado == "bpm":
                if evento.key == pygame.K_BACKSPACE:
                    s_bpm = str(self.dados.bpm)[:-1]
                    self.dados.bpm = int(s_bpm) if s_bpm else 0
                elif evento.key == pygame.K_RETURN or evento.key == pygame.K_ESCAPE:
                    self.campo_focado = None
                    self.dados.bpm = max(10, min(300, self.dados.bpm))
                elif evento.unicode.isdigit():
                    self.dados.bpm = int(str(self.dados.bpm) + evento.unicode)
                return

            if evento.key == pygame.K_SPACE:
                if self.dados.playing:
                    self.dados.stop()
                else:
                    self.dados.play(self.synth.tocar_nota)
            
            elif evento.key == pygame.K_RIGHT:
                self.cursor_pos[1] += 1
                if self.cursor_pos[1] >= len(self.dados.grade[0]):
                    # Expande a grade se necessário
                    for c in range(6): self.dados.grade[c].append("-")
                self._ajustar_scroll()
            elif evento.key == pygame.K_LEFT:
                self.cursor_pos[1] = max(0, self.cursor_pos[1] - 1)
                self._ajustar_scroll()
            elif evento.key == pygame.K_UP:
                self.cursor_pos[0] = max(0, self.cursor_pos[0] - 1)
            elif evento.key == pygame.K_DOWN:
                self.cursor_pos[0] = min(5, self.cursor_pos[0] + 1)
            
            elif pygame.K_0 <= evento.key <= pygame.K_9:
                num = str(evento.key - pygame.K_0)
                # Se já houver um número, concatena ou substitui (lógica simples aqui)
                atual = self.dados.grade[self.cursor_pos[0]][self.cursor_pos[1]]
                if atual == "-" or not atual.replace('bs/\\hp', '').isdigit():
                    self.dados.adicionar_nota(self.cursor_pos[0], self.cursor_pos[1], num)
                else:
                    novo_val = atual + num
                    if int(novo_val.strip('bs/\\hp')) <= 24:
                        self.dados.adicionar_nota(self.cursor_pos[0], self.cursor_pos[1], novo_val)
                # Toca a nota ao inserir
                self.synth.tocar_nota(self.cursor_pos[0]+1, int(self.dados.grade[self.cursor_pos[0]][self.cursor_pos[1]].strip('bs/\\hp')))

            elif evento.key == pygame.K_BACKSPACE:
                self.dados.remover_nota(self.cursor_pos[0], self.cursor_pos[1])
            
            elif evento.key == pygame.K_b:
                self._adicionar_tecnica("b")
            elif evento.key == pygame.K_s:
                self._adicionar_tecnica("/")

        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 4: # Scroll Up
                self.scroll_x = max(0, self.scroll_x - 40)
            elif evento.button == 5: # Scroll Down
                self.scroll_x += 40
            elif evento.button == 1: # Clique Esquerdo
                # Verificar clique nos campos de texto
                if self.rect_nome.collidepoint(evento.pos):
                    self.campo_focado = "nome"
                elif self.rect_bpm.collidepoint(evento.pos):
                    self.campo_focado = "bpm"
                elif self.rect_salvar.collidepoint(evento.pos):
                    self._salvar_no_banco(estado)
                elif self.rect_limpar.collidepoint(evento.pos):
                    self.dados.limpar_tablatura()
                else:
                    self.campo_focado = None
                    # Seleciona célula pelo clique
                    mouse_x, mouse_y = evento.pos
                    t = int((mouse_x - self.margem_esquerda + self.scroll_x) / self.espacamento_tempos)
                    c = int((mouse_y - self.inicio_y + self.espacamento_cordas//2) / self.espacamento_cordas)
                    if 0 <= c < 6 and 0 <= t < len(self.dados.grade[0]):
                        self.cursor_pos = [c, t]

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

    def _ajustar_scroll(self):
        # Garante que o cursor esteja sempre visível
        cursor_x_tela = self.margem_esquerda + self.cursor_pos[1] * self.espacamento_tempos - self.scroll_x
        if cursor_x_tela > self.largura - 100:
            self.scroll_x += self.espacamento_tempos
        elif cursor_x_tela < self.margem_esquerda + 100:
            self.scroll_x = max(0, self.scroll_x - self.espacamento_tempos)

    def _adicionar_tecnica(self, char):
        atual = self.dados.grade[self.cursor_pos[0]][self.cursor_pos[1]]
        if atual != "-" and char not in atual:
            self.dados.adicionar_nota(self.cursor_pos[0], self.cursor_pos[1], atual + char)

    def _ajustar_scroll(self):
        # Garante que o cursor esteja sempre visível
        cursor_x_tela = self.margem_esquerda + self.cursor_pos[1] * self.espacamento_tempos - self.scroll_x
        if cursor_x_tela > self.largura - 100:
            self.scroll_x += self.espacamento_tempos
        elif cursor_x_tela < self.margem_esquerda + 100:
            self.scroll_x = max(0, self.scroll_x - self.espacamento_tempos)

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
