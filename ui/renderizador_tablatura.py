import pygame
from config.theme import *
from config.ui_metrics import *
from config.app_settings import *
from audio.tab_synth import MotorAudioDual
import re

from core.modulos.modulo_dados_tab import GerenciadorDadosTablatura

class RenderizadorTablatura:
    """
    Renderizador responsável por desenhar a grade da tablatura, o cursor e processar a reprodução.
    Utiliza GerenciadorDadosTablatura para lógica de dados.
    """
    def __init__(self):
        self.synth = MotorAudioDual(modo="sintetico")
        self.dados = GerenciadorDadosTablatura()
        self.largura_coluna = 60
        self.altura_linha = 20
        self.espaco_entre_sistemas = 220 
        self.margem_esquerda = 80
        self.margem_topo = 220
        self.rects_clique = {} 
        self.rects_campo_harmonico = [] 
        self.rects_tecnicas = []

    def sincronizar_com_estado(self, estado):
        """Sincroniza os dados do gerenciador com o estado global."""
        if hasattr(estado, 'tab_dados_gerenciador'):
            self.dados = estado.tab_dados_gerenciador
        self.dados.bpm = estado.tab_bpm
        
        # Se o estado tiver dados novos (ex: carregados de DB), atualiza o gerenciador
        if hasattr(estado, 'tab_dados_importados'):
            self.dados.grade = estado.tab_dados_importados
            del estado.tab_dados_importados

    def desenhar_grade(self, tela, estado, fontes, largura_tela, altura_tela):
        self.sincronizar_com_estado(estado)
        self.rects_clique = {}
        largura_maxima = largura_tela - self.margem_esquerda - 60
        scroll_y = getattr(estado, 'tab_scroll_y', 0)
        
        # Ajuste dinâmico de cordas por instrumento
        nomes_cordas = ['E', 'B', 'G', 'D', 'A', 'E']
        if self.dados.instrumento_atual == "Baixo":
            nomes_cordas = ['G', 'D', 'A', 'E']
        
        num_cordas = len(nomes_cordas)
        num_cols = len(self.dados.grade[0])
        x_acumulado = 0
        linha_atual = 0
        self.posicoes_colunas = {} 

        # Resolução visual
        RESOLUCAO_VISUAL = 4
        
        # Clip para não desenhar em cima dos menus
        rect_clip = pygame.Rect(0, self.margem_topo - 10, largura_tela, altura_tela - self.margem_topo + 10)
        tela.set_clip(rect_clip)
        
        for col_idx in range(num_cols):
            largura_da_coluna = self.largura_coluna / 2
            
            if x_acumulado + largura_da_coluna > largura_maxima and col_idx > 0:
                linha_atual += 1
                x_acumulado = 0
            
            x = self.margem_esquerda + x_acumulado
            y_base = self.margem_topo + linha_atual * self.espaco_entre_sistemas - scroll_y
            self.posicoes_colunas[col_idx] = (x, y_base, largura_da_coluna)

            # Evita processar linhas muito acima ou muito abaixo da tela (otimização)
            visivel = (y_base + self.espaco_entre_sistemas > self.margem_topo - 50 and y_base < altura_tela)

            if visivel:
                if x_acumulado == 0:
                    for i, nome in enumerate(nomes_cordas):
                        y_corda = y_base + i * self.altura_linha
                        # Pula desenho da corda se estiver na área do menu (reforço extra ao set_clip)
                        if y_corda < self.margem_topo - 20:
                            continue
                        txt = fontes['ui'].render(nome, True, (150, 150, 150))
                        tela.blit(txt, (self.margem_esquerda - 40, y_corda - 8))
                        pygame.draw.line(tela, (50, 50, 55), (self.margem_esquerda - 10, y_corda), (largura_tela - 30, y_corda), 1)

                # Desenhar linha divisória do compasso (a cada 4 tempos)
                if col_idx % 4 == 0:
                    y_inicio_compasso = y_base
                    y_fim_compasso = y_base + (num_cordas - 1) * self.altura_linha
                    # Evita desenhar linhas verticais que sobem para o menu
                    if y_inicio_compasso >= self.margem_topo - 10:
                        pygame.draw.line(tela, (120, 120, 130), (x - 8, y_inicio_compasso), (x - 8, y_fim_compasso), 2)
                        
                        # Número do compasso
                        num_compasso = (col_idx // 4) + 1
                        txt_comp = fontes['pequena'].render(str(num_compasso), True, (120, 120, 130))
                        tela.blit(txt_comp, (x - 4, y_inicio_compasso - 20))

                # Notas
                for corda_idx in range(num_cordas):
                    y_corda = y_base + corda_idx * self.altura_linha
                    if y_corda < self.margem_topo - 20:
                        continue
                        
                    celula = self.dados.grade[corda_idx][col_idx]
                    
                    rect_clique = pygame.Rect(x - 12, y_corda - 10, 24, 20)
                    self.rects_clique[(col_idx, corda_idx)] = rect_clique

                    # Cursor de edição com brilho
                    if estado.tab_cursor_col == col_idx and estado.tab_cursor_corda == corda_idx:
                        pygame.draw.rect(tela, (100, 200, 255), rect_clique, 2, border_radius=4)

                    if celula != '-':
                        # Parse da célula (ex: "12v100d4~")
                        match = re.match(r"(\d+)", str(celula))
                        if match:
                            casa = match.group(1)
                            
                            # Efeitos visuais baseados em metadados
                            vibrato = '~' in str(celula)
                            vol_match = re.search(r"v(\d+)", str(celula))
                            volume = int(vol_match.group(1)) if vol_match else 100
                            
                            # Cor baseada no volume (dinâmica visual)
                            cor_nota = (min(255, 150 + volume), min(255, 150 + volume), min(255, 150 + volume))
                            
                            # Fundo da nota circular para visual moderno
                            pygame.draw.circle(tela, (30, 30, 35), (x, y_corda), 10)
                            if vibrato:
                                # Desenhar onda de vibrato
                                pts = [(x-10+i, y_corda+8+np.sin(i*0.5)*3) for i in range(20)]
                                pygame.draw.lines(tela, (0, 255, 150), False, pts, 1)

                            txt_n = fontes['pequena'].render(casa, True, cor_nota)
                            tela.blit(txt_n, (x - txt_n.get_width() // 2, y_corda - txt_n.get_height() // 2))
                            
                            # Linha de duração estilizada
                            if 'd' in str(celula):
                                d_match = re.search(r"d(\d+)", str(celula))
                                if d_match:
                                    dur = int(d_match.group(1))
                                    # Gradiente de duração
                                    rect_dur = pygame.Rect(x + 10, y_corda - 1, dur * largura_da_coluna - 15, 3)
                                    pygame.draw.rect(tela, AZUL_PRIMARIO, rect_dur, border_radius=2)


                # Cursor de Playback
                if estado.tab_reproduzindo and estado.tab_coluna_atual == col_idx:
                    pygame.draw.rect(tela, (255, 215, 0), (x - 1, y_base - 5, 2, 5 * self.altura_linha + 10))

            x_acumulado += largura_da_coluna

        # Botão "+ ADICIONAR LINHA" ao final
        y_add = self.margem_topo + (linha_atual + 1) * self.espaco_entre_sistemas - scroll_y
        if y_add > self.margem_topo - 40 and y_add < altura_tela:
            estado.rect_tab_add_linha = pygame.Rect(self.margem_esquerda, y_add, 200, 40)
            pygame.draw.rect(tela, (60, 60, 75), estado.rect_tab_add_linha, border_radius=5)
            txt_add = fontes['pequena'].render("+ ADICIONAR LINHA", True, BRANCO)
            tela.blit(txt_add, (estado.rect_tab_add_linha.centerx - txt_add.get_width() // 2, estado.rect_tab_add_linha.centery - txt_add.get_height() // 2))
        else:
            if hasattr(estado, 'rect_tab_add_linha'):
                del estado.rect_tab_add_linha

        # Restaura a área de desenho normal
        tela.set_clip(None)

    def processar_reproducao(self, estado):
        if not estado.tab_reproduzindo: return
        
        agora = pygame.time.get_ticks()
        
        # Sincroniza BPM
        self.dados.bpm = estado.tab_bpm
        # 1 coluna = 1 batida (semínima)
        ms_por_beat = 60000 / max(1, estado.tab_bpm)
        ms_por_coluna = ms_por_beat

        if not hasattr(estado, 'tempo_proximo_tick'):
            # Acabou de dar play. Toca a coluna inicial IMEDIATAMENTE e agenda a próxima.
            self._tocar_notas_da_coluna(estado, ms_por_coluna)
            estado.tempo_proximo_tick = agora + ms_por_coluna
            return
            
        if agora >= estado.tempo_proximo_tick:
            # Só avança a coluna atual visualmente quando o tempo da anterior terminar
            estado.tab_coluna_atual += 1
            
            if estado.tab_coluna_atual < len(self.dados.grade[0]):
                self._tocar_notas_da_coluna(estado, ms_por_coluna)
                # Adiciona o tempo para manter o metrônomo perfeito (não usa "agora" para evitar drift)
                estado.tempo_proximo_tick += ms_por_coluna
            else:
                estado.tab_reproduzindo = False
                estado.tab_coluna_atual = 0
                del estado.tempo_proximo_tick

    def _tocar_notas_da_coluna(self, estado, ms_por_coluna):
        """Função auxiliar para disparar os sons de uma coluna."""
        num_cordas = len(self.dados.grade)
        for corda_idx in range(num_cordas):
            celula = self.dados.grade[corda_idx][estado.tab_coluna_atual]
            if celula != '-':
                # Tocar nota com fidelidade máxima
                match = re.match(r"(\d+)", str(celula))
                if match:
                    casa = int(match.group(1))
                    
                    # Extração de Fidelidade (Expressão)
                    vol_match = re.search(r"v(\d+)", str(celula))
                    volume = int(vol_match.group(1)) if vol_match else 100
                    
                    dur_cols = 1
                    d_match = re.search(r"d(\d+)", str(celula))
                    if d_match: dur_cols = int(d_match.group(1))
                    
                    tecnica = ""
                    if 'b' in str(celula): tecnica += 'b'
                    if '/' in str(celula): tecnica += '/'
                    if '~' in str(celula): tecnica += '~'
                    
                    dur_seg = (dur_cols * ms_por_coluna / 1000.0) * 1.5 # Sustain estendido para realismo
                    self.synth.reproduzir_nota(corda_idx + 1, casa, tecnica, duracao=dur_seg, volume=volume)


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
        Interface completa do criador com seletor de instrumentos.
        """
        self.sincronizar_com_estado(estado)
        tela.fill(FUNDO_ESCURO)
        
        # Título
        txt_titulo = fontes['titulo'].render(f"Criador de Tablaturas: {estado.tab_nome}", True, BRANCO)
        tela.blit(txt_titulo, (20, 20))

        # --- NOVO: Seletor de Instrumentos (Trilhas) ---
        x_inst = 20
        y_inst = 160
        self.rects_instrumentos = {}
        for nome in self.dados.trilhas.keys():
            cor_bg = (60, 60, 70) if nome != self.dados.instrumento_atual else AZUL_PRIMARIO
            
            # Define o ícone baseado no nome do instrumento
            icone = "🎸"
            nome_lower = nome.lower()
            if "baixo" in nome_lower: icone = "🎸"
            elif "bateria" in nome_lower or "drum" in nome_lower: icone = "🥁"
            elif "teclado" in nome_lower or "piano" in nome_lower: icone = "🎹"
            elif "voz" in nome_lower or "vocal" in nome_lower: icone = "🎤"
            
            texto_nome = nome.upper()
            
            # Tenta utilizar a fonte nativa de emojis do Windows para evitar os quadrados brancos
            try:
                fonte_emoji = pygame.font.SysFont("segoe ui emoji", 16)
                surf_icone = fonte_emoji.render(icone, True, BRANCO)
            except:
                surf_icone = fontes['pequena'].render(icone, True, BRANCO)

            surf_texto = fontes['pequena'].render(texto_nome, True, BRANCO)
            
            largura_total = surf_icone.get_width() + 5 + surf_texto.get_width()
            largura_btn = max(100, largura_total + 30)
            
            rect = pygame.Rect(x_inst, y_inst, largura_btn, 30)
            pygame.draw.rect(tela, cor_bg, rect, border_radius=5)
            
            x_base = rect.centerx - largura_total // 2
            tela.blit(surf_icone, (x_base, rect.centery - surf_icone.get_height() // 2))
            tela.blit(surf_texto, (x_base + surf_icone.get_width() + 5, rect.centery - surf_texto.get_height() // 2))
            
            self.rects_instrumentos[nome] = rect
            x_inst += largura_btn + 10
        
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

        # Novo: Botão Exportar TXT (Notas)
        estado.rect_tab_export_txt = pygame.Rect(400, y_ctrl, 130, 30)
        pygame.draw.rect(tela, (39, 174, 96), estado.rect_tab_export_txt, border_radius=5)
        txt_export = fontes['pequena'].render("📄 Exportar TXT", True, BRANCO)
        tela.blit(txt_export, (estado.rect_tab_export_txt.x + 10, y_ctrl + 7))

        # NOVO: Botão de Ligar/Desligar IA
        estado.rect_tab_toggle_ia = pygame.Rect(540, y_ctrl, 100, 30)
        cor_toggle_ia = (46, 204, 113) if getattr(estado, 'ia_ligada', False) else (231, 76, 60)
        pygame.draw.rect(tela, cor_toggle_ia, estado.rect_tab_toggle_ia, border_radius=5)
        txt_toggle = fontes['pequena'].render("IA ON" if getattr(estado, 'ia_ligada', False) else "IA OFF", True, BRANCO)
        tela.blit(txt_toggle, (estado.rect_tab_toggle_ia.centerx - txt_toggle.get_width() // 2, y_ctrl + 7))

        # 4. IA Transcrição (Movida um pouco para a direita)
        estado.rect_tab_ia = pygame.Rect(650, y_ctrl, 150, 30)
        cor_btn_ia = (100, 80, 255) if getattr(estado, 'ia_ligada', False) else (100, 100, 100)
        pygame.draw.rect(tela, cor_btn_ia, estado.rect_tab_ia, border_radius=5)
        txt_ia = fontes['pequena'].render("✨ Transcrever Áudio", True, BRANCO if getattr(estado, 'ia_ligada', False) else (180, 180, 180))
        tela.blit(txt_ia, (estado.rect_tab_ia.centerx - txt_ia.get_width() // 2, y_ctrl + 7))

        # 5. Botão de Gravação Direta (Movido)
        estado.rect_tab_rec = pygame.Rect(810, y_ctrl, 140, 30)
        esta_gravando = getattr(estado, 'tab_gravando', False)
        
        if getattr(estado, 'ia_ligada', False):
            cor_rec = (231, 76, 60) if esta_gravando else (60, 60, 65)
            cor_txt_rec = BRANCO
        else:
            cor_rec = (60, 60, 60)
            cor_txt_rec = (180, 180, 180)
            
        pygame.draw.rect(tela, cor_rec, estado.rect_tab_rec, border_radius=5)
        txt_rec = fontes['pequena'].render("🛑 PARAR" if esta_gravando else "🎤 GRAVAR", True, cor_txt_rec)
        tela.blit(txt_rec, (estado.rect_tab_rec.centerx - txt_rec.get_width() // 2, y_ctrl + 7))

        # NOVO: Botão Toggle Audio (Dual-Engine)
        estado.rect_tab_toggle_audio = pygame.Rect(960, y_ctrl, 140, 30)
        cor_toggle_audio = (50, 150, 255) if self.synth.modo == "realista" else (100, 100, 120)
        pygame.draw.rect(tela, cor_toggle_audio, estado.rect_tab_toggle_audio, border_radius=5)
        txt_modo = "Som: Realista" if self.synth.modo == "realista" else "Som: Sintético"
        txt_t_audio = fontes['pequena'].render(txt_modo, True, BRANCO)
        tela.blit(txt_t_audio, (estado.rect_tab_toggle_audio.centerx - txt_t_audio.get_width() // 2, y_ctrl + 7))

        # Status da IA
        if hasattr(estado, 'cliente_ia') and estado.cliente_ia.status != 'idle' and getattr(estado, 'ia_ligada', False):
            cor_status = (255, 215, 0)
            status_texto = f"IA: {estado.cliente_ia.status.upper()}"
            if estado.cliente_ia.status == 'failed':
                cor_status = (231, 76, 60)
                status_texto = f"IA: ERRO ({estado.cliente_ia.erro})"
            elif estado.cliente_ia.status == 'completed':
                cor_status = (46, 204, 113)
                status_texto = "IA: CONCLUÍDO!"
            
            txt_st = fontes['pequena'].render(status_texto, True, cor_status)
            tela.blit(txt_st, (715, y_ctrl + 7))

        # Grade
        self.desenhar_grade(tela, estado, fontes, largura, altura)
        
        # Processar áudio
        self.processar_reproducao(estado)
        
        # Instruções
        txt_help = fontes['pequena'].render("Setas: Mover | Números: Casa | +/-: Duração | b: Bend | /: Slide | Direito: Mover Play", True, (150, 150, 150))
        tela.blit(txt_help, (20, altura - 40))

    def tratar_evento(self, evento, estado, motor_audio=None):
        """
        Trata eventos de clique e teclado para editar a tablatura.
        """
        if evento.type == pygame.MOUSEWHEEL:
            estado.tab_scroll_y = max(0, getattr(estado, 'tab_scroll_y', 0) - evento.y * 30)
            return True

        if evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1:
                # Tratar botão adicionar linha
                if hasattr(estado, 'rect_tab_add_linha') and estado.rect_tab_add_linha.collidepoint(evento.pos):
                    self.dados.adicionar_colunas(64)
                    return True

                # Ignorar cliques na grade se estiverem fora da área de clipping (acima do menu)
                if evento.pos[1] > self.margem_topo - 10:
                    # 1. Cliques na Grade
                    for (col, corda), rect in self.rects_clique.items():
                        if rect.collidepoint(evento.pos):
                            estado.tab_cursor_col = col
                            estado.tab_cursor_corda = corda
                            return True
                
                # 2. Cliques em Controles (BPM, Play, Salvar)
                if hasattr(estado, 'rect_bpm_menos') and estado.rect_bpm_menos.collidepoint(evento.pos):
                    estado.tab_bpm = max(1, estado.tab_bpm - 5); return True
                if hasattr(estado, 'rect_bpm_mais') and estado.rect_bpm_mais.collidepoint(evento.pos):
                    estado.tab_bpm += 5; return True
                if hasattr(estado, 'rect_tab_play') and estado.rect_tab_play.collidepoint(evento.pos):
                    estado.tab_reproduzindo = not estado.tab_reproduzindo
                    if estado.tab_reproduzindo:
                        estado.tab_coluna_atual = 0
                        estado.tempo_proximo_tick = pygame.time.get_ticks()
                    return True
                if hasattr(estado, 'rect_tab_salvar') and estado.rect_tab_salvar.collidepoint(evento.pos):
                    self.salvar_no_db(estado); return True
                if hasattr(estado, 'rect_tab_export_txt') and estado.rect_tab_export_txt.collidepoint(evento.pos):
                    self._exportar_para_txt(estado); return True
                
                # Lógica do Botão Toggle IA
                if hasattr(estado, 'rect_tab_toggle_ia') and estado.rect_tab_toggle_ia.collidepoint(evento.pos):
                    if not getattr(estado, 'ia_ligada', False):
                        print("[IA] Iniciando serviços de IA manualmente...")
                        from core.modulos.gerenciador_servicos_ia import iniciar_servicos_ia
                        iniciar_servicos_ia()
                        estado.ia_ligada = True
                    else:
                        print("[IA] Desligando integração com a IA (serviço backend pode continuar rodando).")
                        estado.ia_ligada = False
                    return True

                if hasattr(estado, 'rect_tab_ia') and estado.rect_tab_ia.collidepoint(evento.pos):
                    if getattr(estado, 'ia_ligada', False):
                        self._iniciar_transcricao_ia(estado)
                    return True
                if hasattr(estado, 'rect_tab_rec') and estado.rect_tab_rec.collidepoint(evento.pos):
                    if getattr(estado, 'ia_ligada', False) or getattr(estado, 'tab_gravando', False):
                        self._alternar_gravacao(estado, motor_audio)
                    return True
                if hasattr(estado, 'rect_tab_toggle_audio') and estado.rect_tab_toggle_audio.collidepoint(evento.pos):
                    novo_modo = "realista" if self.synth.modo == "sintetico" else "sintetico"
                    self.synth.alternar_modo(novo_modo)
                    return True

                # 3. Cliques em Seletor de Instrumentos
                for nome, rect in self.rects_instrumentos.items():
                    if rect.collidepoint(evento.pos):
                        self.dados.alternar_instrumento(nome)
                        self.synth.alternar_instrumento_synth(nome)
                        return True

                # 4. Cliques em Técnicas
                for rect, cmd in self.rects_tecnicas:
                    if rect.collidepoint(evento.pos):
                        self.aplicar_tecnica(estado, cmd); return True

                # 4. Cliques no Campo Harmônico
                for rect, nome_acorde in self.rects_campo_harmonico:
                    if rect.collidepoint(evento.pos):
                        print(f"Inserindo acorde {nome_acorde}") # Futura implementação de acordes
                        return True

            elif evento.button == 3: # Clique direito move o playhead
                for col in range(len(self.dados.grade[0])):
                    if col in self.posicoes_colunas:
                        x, y, w = self.posicoes_colunas[col]
                        if x <= evento.pos[0] <= x + w:
                            estado.tab_coluna_atual = col
                            return True

        elif evento.type == pygame.KEYDOWN:
            # Movimentação do Cursor
            if evento.key == pygame.K_RIGHT:
                estado.tab_cursor_col = min(len(self.dados.grade[0]) - 1, estado.tab_cursor_col + 1); return True
            if evento.key == pygame.K_LEFT:
                estado.tab_cursor_col = max(0, estado.tab_cursor_col - 1); return True
            if evento.key == pygame.K_UP:
                estado.tab_cursor_corda = max(0, estado.tab_cursor_corda - 1); return True
            if evento.key == pygame.K_DOWN:
                estado.tab_cursor_corda = min(5, estado.tab_cursor_corda + 1); return True
            
            # Edição de Notas
            if pygame.K_0 <= evento.key <= pygame.K_9:
                num = str(evento.key - pygame.K_0)
                atual = self.dados.grade[estado.tab_cursor_corda][estado.tab_cursor_col]
                if atual == '-' or not atual[0].isdigit():
                    self.dados.adicionar_nota(estado.tab_cursor_corda, estado.tab_cursor_col, num)
                else:
                    # Parse para adicionar dígitos extras (ex: 1 -> 12)
                    match = re.match(r"(\d+)", str(atual))
                    num_base = match.group(1) if match else ""
                    nova_casa = (num_base + num)[:2]
                    self.dados.grade[estado.tab_cursor_corda][estado.tab_cursor_col] = str(nova_casa) + (atual[len(num_base):] if match else "")
                
                # Tocar nota
                try:
                    match = re.match(r"(\d+)", str(self.dados.grade[estado.tab_cursor_corda][estado.tab_cursor_col]))
                    if match: self.synth.reproduzir_nota(estado.tab_cursor_corda + 1, int(match.group(1)))
                except: pass
                return True

            if evento.key == pygame.K_BACKSPACE or evento.key == pygame.K_DELETE:
                self.dados.grade[estado.tab_cursor_corda][estado.tab_cursor_col] = '-'
                return True

            # Atalhos de Técnicas
            if evento.key == pygame.K_b: self.aplicar_tecnica(estado, 'b'); return True
            if evento.key == pygame.K_s: self.aplicar_tecnica(estado, '/'); return True
            if evento.key == pygame.K_h: self.aplicar_tecnica(estado, 'h'); return True
            if evento.key == pygame.K_p: self.aplicar_tecnica(estado, 'p'); return True

        return False

    def aplicar_tecnica(self, estado, cmd):
        col, corda = estado.tab_cursor_col, estado.tab_cursor_corda
        atual = self.dados.grade[corda][col]
        
        if cmd in ('b', '/', 'h', 'p'):
            if atual != '-' and atual[0].isdigit():
                match = re.match(r"(\d+)", str(atual))
                if match:
                    self.dados.grade[corda][col] = match.group(1) + cmd
        elif cmd == '+':
            # Aumentar duração (d2 -> d3, etc)
            match = re.search(r"d(\d+)", str(atual))
            if match:
                nova_dur = int(match.group(1)) + 1
                self.dados.grade[corda][col] = re.sub(r"d\d+", f"d{nova_dur}", str(atual))
            elif atual != '-':
                self.dados.grade[corda][col] = str(atual) + "d2"
        elif cmd == '-':
            match = re.search(r"d(\d+)", str(atual))
            if match:
                nova_dur = max(1, int(match.group(1)) - 1)
                self.dados.grade[corda][col] = re.sub(r"d\d+", f"d{nova_dur}", str(atual))
        elif cmd == 'del':
            self.dados.grade[corda][col] = '-'

    def salvar_no_db(self, estado):
        if not hasattr(estado, 'db') or not estado.usuario_id_logado:
            print("[DB] Usuário não logado ou BD offline.")
            return
            
        import json
        json_str = json.dumps({
            "bpm": self.dados.bpm,
            "grade": self.dados.grade
        })
        
        sucesso = estado.db.salvar_projeto(estado.usuario_id_logado, estado.tab_nome, "tablatura", json_str)
        if sucesso:
            print(f"[DB] Tablaturas '{estado.tab_nome}' salva com sucesso!")
        else:
            print("[DB] Erro ao salvar no banco.")

    def _iniciar_transcricao_ia(self, estado):
        """
        Abre o seletor de arquivos e inicia a transcrição via IA.
        """
        if not hasattr(estado, 'cliente_ia'):
            return
            
        if estado.cliente_ia.status not in ('idle', 'completed', 'failed'):
            return # Já está processando

        try:
            import tkinter as tk
            from tkinter import filedialog
            
            # Criar root apenas se necessário e esconder
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            
            # Abrir diálogo
            caminho = filedialog.askopenfilename(
                parent=root,
                title="Selecionar Áudio para Transcrição",
                filetypes=[("Áudio", "*.wav *.mp3 *.ogg")]
            )
            
            # Destruição segura
            root.destroy()
            
            if caminho:
                print(f"[IA] Arquivo selecionado: {caminho}")
                estado.cliente_ia.transcrever_arquivo(caminho, estado, instrumento="other")
                
        except Exception as e:
            print(f"[UI ERROR] Falha ao abrir seletor de arquivos: {e}")
            try: root.destroy()
            except: pass

    def _alternar_gravacao(self, estado, motor_audio=None):
        """
        Inicia ou para a gravação direta do microfone.
        """
        if not motor_audio:
            print("[UI] Erro: Motor de áudio não disponível para gravação.")
            return

        if not getattr(estado, 'tab_gravando', False):
            # Iniciar
            motor_audio.iniciar_gravacao()
            estado.tab_gravando = True
        else:
            # Parar e enviar
            import uuid
            import os
            nome_arquivo = f"rec_{uuid.uuid4().hex[:8]}.wav"
            caminho = motor_audio.parar_gravacao(output_path=nome_arquivo)
            estado.tab_gravando = False
            
            if caminho and os.path.exists(caminho):
                print(f"[IA] Gravação finalizada. Enviando {caminho}...")
                estado.cliente_ia.transcrever_arquivo(caminho, estado, instrumento="other")

    def _exportar_para_txt(self, estado):
        """
        Abre diálogo para salvar as notas da tablatura em arquivo TXT.
        """
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            
            caminho = filedialog.asksaveasfilename(
                parent=root,
                title="Salvar Notas como TXT",
                defaultextension=".txt",
                initialfile=f"{estado.tab_nome}_notas.txt",
                filetypes=[("Arquivo de Texto", "*.txt")]
            )
            
            root.destroy()
            
            if caminho:
                sucesso = self.dados.exportar_notas_txt(caminho)
                if sucesso:
                    print(f"[UI] Notas exportadas para {caminho}")
                else:
                    print("[UI] Falha ao exportar notas.")
                    
        except Exception as e:
            print(f"[UI ERROR] Falha na exportação TXT: {e}")


