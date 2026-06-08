import pygame
from Core.constantes_ui import *
from Modulos.modulo_synth import SintetizadorTablatura
import re

class RenderizadorTablatura:
    """
    Renderizador responsável por desenhar a grade da tablatura, o cursor e processar a reprodução.
    """
    def __init__(self):
        self.synth = SintetizadorTablatura()
        self.largura_coluna = 40
        self.altura_linha = 20
        self.espaco_entre_sistemas = 220 # Aumentado para caber o campo harmônico se necessário
        self.margem_esquerda = 80
        self.margem_topo = 180
        self.rects_clique = {} # (col, corda) -> Rect
        self.rects_campo_harmonico = [] # List of (rect, nome_acorde)
        self.rects_tecnicas = []

    def desenhar_grade(self, tela, estado, fontes, largura_tela, altura_tela):
        """
        Desenha a grade com larguras dinâmicas baseadas na duração das notas.
        Garante que o cursor (barra amarela) ande em velocidade constante.
        """
        self.rects_clique = {}
        largura_maxima = largura_tela - self.margem_esquerda - 60
        
        scroll_y = getattr(estado, 'tab_scroll_y', 0)
        nomes_cordas = ['E', 'B', 'G', 'D', 'A', 'E']
        
        if not hasattr(estado, 'tab_duracoes'):
            estado.tab_duracoes = [1 for _ in range(len(estado.tab_dados))]

        x_acumulado = 0
        linha_atual = 0
        
        # Mapeamento para saber onde cada coluna foi parar (para o Play e Clique)
        self.posicoes_colunas = {} 

        for col_idx in range(len(estado.tab_dados)):
            duracao = estado.tab_duracoes[col_idx]
            largura_da_coluna = self.largura_coluna * duracao
            
            # Verificar se cabe na linha atual
            if x_acumulado + largura_da_coluna > largura_maxima and col_idx > 0:
                linha_atual += 1
                x_acumulado = 0
            
            x = self.margem_esquerda + x_acumulado
            y_base = self.margem_topo + linha_atual * self.espaco_entre_sistemas - scroll_y
            
            self.posicoes_colunas[col_idx] = (x, y_base, largura_da_coluna)

            # Otimização: Só desenha se estiver visível
            visivel = (y_base + self.espaco_entre_sistemas > 0 and y_base < altura_tela)

            if visivel:
                # Desenhar estrutura básica no início da linha
                if x_acumulado == 0:
                    for i, nome in enumerate(nomes_cordas):
                        y_corda = y_base + i * self.altura_linha
                        txt = fontes['ui'].render(nome, True, (150, 150, 150))
                        tela.blit(txt, (self.margem_esquerda - 40, y_corda - 8))
                        pygame.draw.line(tela, (60, 60, 65), (self.margem_esquerda - 10, y_corda), (largura_tela - 30, y_corda), 1)
                    pygame.draw.line(tela, (100, 100, 105), (self.margem_esquerda - 10, y_base), (self.margem_esquerda - 10, y_base + 5 * self.altura_linha), 2)

                # Divisória de compasso simplificada (a cada 4 tempos base)
                # (Nota: isso pode ficar desalinhado se houver muitas durações quebradas, mas serve como guia)
                pygame.draw.line(tela, (50, 50, 55), (x, y_base - 5), (x, y_base + 5 * self.altura_linha + 5), 1)

                # Desenhar notas e cursor
                for corda_idx in range(6):
                    y_corda = y_base + corda_idx * self.altura_linha
                    nota = estado.tab_dados[col_idx][corda_idx]
                    
                    rect_clique = pygame.Rect(x - 15, y_corda - 10, 30, 20)
                    self.rects_clique[(col_idx, corda_idx)] = rect_clique

                    if estado.tab_cursor_col == col_idx and estado.tab_cursor_corda == corda_idx:
                        pygame.draw.rect(tela, AZUL_PRIMARIO, rect_clique, 1, border_radius=3)

                    if nota != '-':
                        pygame.draw.rect(tela, FUNDO_ESCURO, (x - 10, y_corda - 9, 20, 18))
                        txt_n = fontes['pequena'].render(str(nota), True, BRANCO)
                        tela.blit(txt_n, (x - txt_n.get_width() // 2, y_corda - txt_n.get_height() // 2))
                        
                        if duracao > 1:
                            pygame.draw.line(tela, AZUL_PRIMARIO, (x + 12, y_corda), (x + largura_da_coluna - 5, y_corda), 2)

                # Playback Suave (Barra Amarela)
                if estado.tab_reproduzindo and estado.tab_coluna_atual - 1 == col_idx:
                    progresso = getattr(estado, 'tab_progresso_coluna', 0.0)
                    offset_x = progresso * largura_da_coluna
                    pygame.draw.rect(tela, (255, 215, 0), (x + offset_x - 2, y_base - 5, 4, 5 * self.altura_linha + 10))

            x_acumulado += largura_da_coluna

    def processar_reproducao(self, estado):
        if not estado.tab_reproduzindo: 
            return
            
        agora = pygame.time.get_ticks()
        
        if not hasattr(estado, 'tab_espera_atual'): estado.tab_espera_atual = 0
        if not hasattr(estado, 'tab_duracoes'): estado.tab_duracoes = [1 for _ in range(len(estado.tab_dados))]
        
        # Calcular progresso dentro da nota atual para animação suave
        tempo_passado = agora - estado.tempo_ultimo_tick
        if estado.tab_espera_atual > 0:
            estado.tab_progresso_coluna = min(1.0, tempo_passado / estado.tab_espera_atual)
        else:
            estado.tab_progresso_coluna = 0.0

        if tempo_passado >= estado.tab_espera_atual:
            if estado.tab_coluna_atual < len(estado.tab_dados):
                ms_por_batida = 60000 / max(1, estado.tab_bpm)
                ms_por_coluna = ms_por_batida / 4
                dur_mult = estado.tab_duracoes[estado.tab_coluna_atual]
                
                espera_ms = ms_por_coluna * dur_mult
                dur_seg = (espera_ms / 1000.0) * 0.9
                
                coluna = estado.tab_dados[estado.tab_coluna_atual]
                for i, nota in enumerate(coluna):
                    if nota != '-':
                        match = re.match(r"(\d+)(.*)", str(nota))
                        if match:
                            try: self.synth.reproduzir_nota(i + 1, int(match.group(1)), match.group(2), duracao=dur_seg)
                            except: pass
                
                estado.tab_espera_atual = espera_ms
                estado.tempo_ultimo_tick = agora
                estado.tab_coluna_atual += 1
                estado.tab_progresso_coluna = 0.0
            else:
                estado.tab_reproduzindo = False
                estado.tab_coluna_atual = 0
                estado.tab_espera_atual = 0
                estado.tab_progresso_coluna = 0.0

    def desenhar_campo_tab(self, tela, x, y, largura, estado, fontes, meu_campo_harmonico):
        """
        Desenha os botões do campo harmônico para inserção rápida com tamanhos dinâmicos.
        """
        self.rects_campo_harmonico = []
        if not meu_campo_harmonico: return

        txt_ch = fontes['pequena'].render(f"Campo de {meu_campo_harmonico.tonica_campo} {meu_campo_harmonico.tipo_escala}:", True, (180, 180, 180))
        tela.blit(txt_ch, (x, y - 25))

        escala_atual = meu_campo_harmonico.escalas_campo[meu_campo_harmonico.indice_escala_campo]
        idx_tonica = meu_campo_harmonico.notas_base.index(meu_campo_harmonico.tonica_campo)
        
        x_atual = x
        for i in range(7):
            idx_nota = (idx_tonica + escala_atual['int'][i]) % 12
            nota_acorde = meu_campo_harmonico.notas_base[idx_nota]
            nome_acorde = nota_acorde + escala_atual['qualidades'][i]
            
            # Calcular largura baseada no texto
            largura_texto = fontes['pequena'].size(nome_acorde)[0]
            largura_btn = largura_texto + 30 # Padding
            
            rect = pygame.Rect(x_atual, y, largura_btn, 30)
            pygame.draw.rect(tela, (40, 40, 45), rect, border_radius=5)
            pygame.draw.rect(tela, (80, 80, 85), rect, width=1, border_radius=5)
            
            txt = fontes['pequena'].render(nome_acorde, True, BRANCO)
            tela.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))
            self.rects_campo_harmonico.append((rect, nome_acorde))
            x_atual += largura_btn + 10

    def desenhar_toolbar_tecnicas(self, tela, x, y, estado, fontes):
        """
        Desenha botões para aplicar técnicas e duração com tamanhos dinâmicos.
        """
        self.rects_tecnicas = []
        tecnicas = [
            {'label': 'BEND (b)', 'cmd': 'b', 'cor': (255, 100, 0)},
            {'label': 'SLIDE (/)', 'cmd': '/', 'cor': (0, 200, 200)},
            {'label': 'HAMMER (h)', 'cmd': 'h', 'cor': (100, 255, 100)},
            {'label': 'PULL-OFF (p)', 'cmd': 'p', 'cor': (200, 100, 255)},
            {'label': 'DUR +', 'cmd': '+', 'cor': (0, 163, 255)},
            {'label': 'DUR -', 'cmd': '-', 'cor': (0, 163, 255)},
            {'label': 'LIMPAR', 'cmd': 'del', 'cor': (200, 50, 50)}
        ]
        
        x_atual = x
        for tec in tecnicas:
            # Calcular largura baseada no texto
            largura_texto = fontes['pequena'].size(tec['label'])[0]
            largura_btn = largura_texto + 30 # Padding
            
            rect = pygame.Rect(x_atual, y, largura_btn, 35)
            pygame.draw.rect(tela, (45, 45, 50), rect, border_radius=5)
            pygame.draw.rect(tela, tec['cor'], rect, width=2, border_radius=5)
            
            txt = fontes['pequena'].render(tec['label'], True, BRANCO)
            tela.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))
            self.rects_tecnicas.append((rect, tec['cmd']))
            x_atual += largura_btn + 10

    def desenhar_interface_tab(self, tela, estado, fontes, largura, altura, configs, meu_campo_harmonico=None):
        """
        Interface completa do criador.
        """
        tela.fill(FUNDO_ESCURO)
        
        # Título e Controles Globais
        txt_titulo = fontes['titulo'].render(f"Criador de Tablaturas: {estado.tab_nome}", True, BRANCO)
        tela.blit(txt_titulo, (20, 20))
        
        # 1. Barra de Campo Harmônico
        y_campo = 60
        self.desenhar_campo_tab(tela, 360, y_campo + 10, 500, estado, fontes, meu_campo_harmonico)
        
        # 2. Barra de Técnicas
        y_toolbar = 115
        self.desenhar_toolbar_tecnicas(tela, 20, y_toolbar, estado, fontes)
        
        # 3. Inputs de Controle (BPM e Play)
        y_ctrl = 60
        # Botões de ajuste de BPM
        estado.rect_bpm_menos = pygame.Rect(20, y_ctrl, 30, 30)
        estado.rect_bpm_mais = pygame.Rect(120, y_ctrl, 30, 30)
        pygame.draw.rect(tela, (60, 60, 65), estado.rect_bpm_menos, border_radius=5)
        pygame.draw.rect(tela, (60, 60, 65), estado.rect_bpm_mais, border_radius=5)
        
        tela.blit(fontes['ui'].render("-", True, BRANCO), (estado.rect_bpm_menos.x + 10, estado.rect_bpm_menos.y + 2))
        tela.blit(fontes['ui'].render("+", True, BRANCO), (estado.rect_bpm_mais.x + 8, estado.rect_bpm_mais.y + 2))
        
        txt_bpm = fontes['pequena'].render(f"{estado.tab_bpm} BPM", True, BRANCO)
        tela.blit(txt_bpm, (60, y_ctrl + 7))

        estado.rect_tab_play = pygame.Rect(170, y_ctrl, 80, 30)
        cor_play = (46, 204, 113) if not estado.tab_reproduzindo else (231, 76, 60)
        pygame.draw.rect(tela, cor_play, estado.rect_tab_play, border_radius=5)
        txt_play = fontes['pequena'].render("STOP" if estado.tab_reproduzindo else "PLAY", True, BRANCO)
        tela.blit(txt_play, (estado.rect_tab_play.centerx - txt_play.get_width() // 2, y_ctrl + 7))

        estado.rect_tab_salvar = pygame.Rect(270, y_ctrl, 120, 30)
        pygame.draw.rect(tela, (0, 120, 215), estado.rect_tab_salvar, border_radius=5)
        txt_save = fontes['pequena'].render("Salvar Projeto", True, BRANCO)
        tela.blit(txt_save, (280, y_ctrl + 7))

        # Grade
        self.desenhar_grade(tela, estado, fontes, largura, altura)
        
        # Processar áudio
        self.processar_reproducao(estado)
        
        # Instruções
        txt_help = fontes['pequena'].render("Setas: Mover | Números: Casa | +/-: Duração | b: Bend | /: Slide | Direito: Mover Play", True, (150, 150, 150))
        tela.blit(txt_help, (20, altura - 40))
