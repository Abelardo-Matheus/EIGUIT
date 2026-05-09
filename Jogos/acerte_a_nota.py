import pygame
import os
import sys
import random
import math
import time

class AcerteANota:
    def __init__(self):
        # --- CORES ---
        self.VERMELHO = (200, 50, 50)
        self.VERDE = (50, 200, 50)
        self.AMARELO = (255, 255, 50)
        self.BRANCO = (255, 255, 255)
        self.AZUL_INTERFACE = (0, 120, 215)
        self.ROXO = (150, 50, 200)

        # --- NOTAS MUSICAIS ---
        self.notas_naturais = ["C", "D", "E", "F", "G", "A", "B"]
        self.notas_sustenidos = ["C#", "D#", "F#", "G#", "A#"]
        self.notas_bemois = ["Db", "Eb", "Gb", "Ab", "Bb"]
        
        self.notas_calibracao = ["C", "D", "E", "F", "G", "A", "B"]
        self.status_notas = [0] * 7  
        self.indice_atual = 0
        self.status_notas[0] = 1 
        
        self.calibrado = False
        self.em_calibracao = False
        self.jogo_iniciado = False 
        
        # --- PRECISÃO DO MICROFONE ---
        self.nota_atual_mic = ""
        self.nota_perfeita_mic = "" # Só preenche se a afinação em Hz for quase cravada
        self.desvio_afinacao = 0.0  # Diz se tá mais grave (< 0) ou mais agudo (> 0)
        self.nivel_volume = 0.0 
        self.y_indicador_anim = None 
        
        # --- VARIÁVEIS DO JOGO ---
        self.dificuldades = ["FÁCIL", "MÉDIA", "DIFÍCIL", "IMPOSSÍVEL"]
        self.idx_dificuldade = 0
        self.velocidade = 50 
        
        self.pontuacao = 0
        self.notas_na_tela = [] 
        self.particulas = [] 
        self.ultimo_spawn = time.time()
        
        # Retângulos de Interface
        self.btn_calibrar = pygame.Rect(0, 0, 320, 60)
        self.btn_play = pygame.Rect(0, 0, 320, 60)
        self.btn_disp_esq, self.btn_disp_dir = pygame.Rect(0, 0, 40, 40), pygame.Rect(0, 0, 40, 40)
        self.btn_dif_esq, self.btn_dif_dir = pygame.Rect(0, 0, 30, 40), pygame.Rect(0, 0, 30, 40)
        self.btn_vel_esq, self.btn_vel_dir = pygame.Rect(0, 0, 30, 40), pygame.Rect(0, 0, 30, 40)

        # Mapeamento de Dispositivos
        self.lista_dispositivos = []
        try:
            import sounddevice as sd
            for i, dev in enumerate(sd.query_devices()):
                if dev['max_input_channels'] > 0:
                    self.lista_dispositivos.append({'id': i, 'name': dev['name']})
        except: pass
        
        try:
            pasta_raiz = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable)) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.fundo = pygame.image.load(os.path.join(pasta_raiz, "fundo_jogo.png")).convert_alpha()
        except: self.fundo = None
            
        self.tam_anterior = (0, 0)
        self.fundo_render = None

    def equivalencia_notas(self, nota1, nota2):
        """Verifica se duas notas são a mesma, incluindo sustenidos e bemóis"""
        if nota1 == nota2: return True
        enarmonicas = {"C#": "Db", "Db": "C#", "D#": "Eb", "Eb": "D#", "F#": "Gb", "Gb": "F#", "G#": "Ab", "Ab": "G#", "A#": "Bb", "Bb": "A#"}
        return enarmonicas.get(nota1) == nota2 or enarmonicas.get(nota2) == nota1

    def gerar_faiscas(self, x, y):
        """Cria uma explosão de partículas no local do acerto"""
        for _ in range(20):
            angulo = random.uniform(0, math.pi * 2)
            velocidade = random.uniform(2, 8)
            self.particulas.append({
                'x': x, 'y': y,
                'vx': math.cos(angulo) * velocidade,
                'vy': math.sin(angulo) * velocidade,
                'vida': 1.0 
            })

    def atualizar_audio(self, freq_detectada):
        """NOVO: Exige precisão de Hz (afinação). Calcula o erro em Cents."""
        try:
            f = float(freq_detectada)
            if f < 20.0:
                self.nota_atual_mic = ""; self.nota_perfeita_mic = ""
                self.nivel_volume = max(0.0, self.nivel_volume - 0.1)
                return

            valor_exato = 12 * math.log2(f / 440.0)
            semitons_de_A4 = round(valor_exato)
            self.desvio_afinacao = valor_exato - semitons_de_A4 # Erro da afinação (-0.5 a +0.5)
            
            indice_nota = (semitons_de_A4 + 9) % 12
            notas_str = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            nota_encontrada = notas_str[int(indice_nota)]
            
            self.nota_atual_mic = nota_encontrada
            self.nivel_volume = min(1.0, 0.7 + random.uniform(0.0, 0.3))
            
            # MAGIA: Exige que a afinação não fuja nem 15 cents para cima ou para baixo!
            # Se você errar a casa ou pressionar forte demais, ele capta o desvio e não estoura.
            if abs(self.desvio_afinacao) <= 0.15:
                self.nota_perfeita_mic = nota_encontrada
            else:
                self.nota_perfeita_mic = ""
                
        except:
            self.nota_atual_mic = ""; self.nota_perfeita_mic = ""
            self.nivel_volume = max(0.0, self.nivel_volume - 0.1)

        # Lógica de Calibração (Agora exige estar cravado)
        if self.nota_perfeita_mic and self.em_calibracao and not self.calibrado and not self.jogo_iniciado:
            if self.nota_perfeita_mic == self.notas_calibracao[self.indice_atual]:
                self.status_notas[self.indice_atual] = 2 
                self.indice_atual += 1
                if self.indice_atual < len(self.notas_calibracao): self.status_notas[self.indice_atual] = 1 
                else: self.calibrado = True 

    def gerar_notas_jogo(self, largura):
        agora = time.time()
        intervalo_spawn = 5.0 - ((self.velocidade / 100.0) * 3.5) 
        
        if agora - self.ultimo_spawn > intervalo_spawn:
            self.ultimo_spawn = agora
            
            dif = self.dificuldades[self.idx_dificuldade]
            qnt_notas = 1
            pool_notas = self.notas_naturais[:]
            tem_sustain = False
            
            if dif == "MÉDIA":
                pool_notas += self.notas_sustenidos
                qnt_notas = random.choice([1, 1, 2])
                tem_sustain = random.random() > 0.8
            elif dif == "DIFÍCIL":
                pool_notas += self.notas_sustenidos
                qnt_notas = random.choice([1, 2, 2, 3, 4])
                tem_sustain = random.random() > 0.6
            elif dif == "IMPOSSÍVEL":
                pool_notas += self.notas_sustenidos + self.notas_bemois
                qnt_notas = random.choice([2, 3, 4, 5])
                tem_sustain = random.random() > 0.4
                
            margem = 150
            posicoes_x = list(range(margem, largura - margem - 100, 80))
            random.shuffle(posicoes_x)
            
            escadinha = dif in ["DIFÍCIL", "IMPOSSÍVEL"] and random.random() > 0.5
            
            for i in range(qnt_notas):
                nota_sorteada = random.choice(pool_notas)
                x = posicoes_x[i]
                y = -50 - (i * 60 if escadinha else 0)
                tamanho_sus = random.randint(100, 300) if tem_sustain and i == 0 else 0
                
                self.notas_na_tela.append({
                    'nota': nota_sorteada, 'x': x, 'y': y,
                    'sustain': tamanho_sus, 'sendo_tocada': False, 'tempo_sustain': 0
                })

    def desenhar(self, tela, largura, altura, meu_gravador=None):
        if self.fundo:
            if self.tam_anterior != (largura, altura):
                self.fundo_render = pygame.transform.smoothscale(self.fundo, (largura, altura))
                self.tam_anterior = (largura, altura)
            tela.blit(self.fundo_render, (0, 0))
        else:
            tela.fill((30, 30, 30))

        fonte_tit = pygame.font.SysFont("Arial", 40, bold=True)
        fonte_ui = pygame.font.SysFont("Arial", 25, bold=True)
        fonte_peq = pygame.font.SysFont("Arial", 18, bold=True)

        txt_tit = fonte_tit.render("ACERTE A NOTA", True, self.BRANCO)
        tela.blit(txt_tit, (largura//2 - txt_tit.get_width()//2, 50))

        y_centro = altura // 2
        y_indicador_original = y_centro - 160
        y_indicador_jogo_ativo = altura - 60 
        
        if self.y_indicador_anim is None: self.y_indicador_anim = y_indicador_original
        alvo_y = y_indicador_jogo_ativo if self.jogo_iniciado else y_indicador_original
        self.y_indicador_anim += (alvo_y - self.y_indicador_anim) * 0.08

        linha_vermelha_y = altura - 150
        
        if self.jogo_iniciado:
            # --- FAÍSCAS ---
            particulas_vivas = []
            for p in self.particulas:
                p['x'] += p['vx']; p['y'] += p['vy']; p['vy'] += 0.2; p['vida'] -= 0.03
                if p['vida'] > 0:
                    tamanho = max(1, int(6 * p['vida']))
                    pygame.draw.circle(tela, (255, int(255 * p['vida']), 0), (int(p['x']), int(p['y'])), tamanho)
                    particulas_vivas.append(p)
            self.particulas = particulas_vivas

            # --- RÉGUA E PONTOS ---
            txt_pontos = fonte_tit.render(f"PONTOS: {self.pontuacao}", True, self.AMARELO)
            tela.blit(txt_pontos, (largura - txt_pontos.get_width() - 30, 40))
            
            x_regua = largura - 80
            pygame.draw.line(tela, self.BRANCO, (x_regua, 100), (x_regua, altura - 50), 4)
            pygame.draw.line(tela, self.VERMELHO, (x_regua - 10, linha_vermelha_y), (x_regua + 10, linha_vermelha_y), 6)
            
            tela.blit(fonte_peq.render("10", True, self.VERDE), (x_regua + 15, 100))
            tela.blit(fonte_peq.render("5", True, self.AMARELO), (x_regua + 15, (linha_vermelha_y + 100)//2))
            tela.blit(fonte_peq.render("1", True, self.VERMELHO), (x_regua + 15, linha_vermelha_y - 20))
            tela.blit(fonte_peq.render("-2", True, (100,100,100)), (x_regua + 15, linha_vermelha_y + 30))
            tela.blit(fonte_peq.render("-5", True, (100,100,100)), (x_regua + 15, altura - 70))

            pygame.draw.line(tela, self.VERMELHO, (0, linha_vermelha_y), (largura - 100, linha_vermelha_y), 3)

            # --- LÓGICA DAS BOLINHAS (QUALQUER LUGAR DA TELA) ---
            self.gerar_notas_jogo(largura)
            vel_queda = 1.0 + (self.velocidade / 50.0) 
            
            notas_para_remover = []
            nota_hit_neste_frame = False 
            
            for i, n in enumerate(self.notas_na_tela):
                if not n['sendo_tocada']: n['y'] += vel_queda
                
                if n['sustain'] > 0:
                    cor_sus = self.AMARELO if n['sendo_tocada'] else self.ROXO
                    h_sus = n['sustain'] - n['tempo_sustain']
                    pygame.draw.rect(tela, cor_sus, (n['x'] - 10, n['y'] - h_sus, 20, h_sus), border_radius=10)
                
                cor_bola = self.VERDE if n['sendo_tocada'] else self.AZUL_INTERFACE
                pygame.draw.circle(tela, cor_bola, (n['x'], n['y']), 35)
                pygame.draw.circle(tela, self.BRANCO, (n['x'], n['y']), 35, 2)
                txt_n = fonte_ui.render(n['nota'], True, self.BRANCO)
                tela.blit(txt_n, (n['x'] - txt_n.get_width()//2, n['y'] - txt_n.get_height()//2))

                # Zona livre de acertos - Se está na tela e ainda não sumiu lá embaixo
                distancia = linha_vermelha_y - n['y']
                
                if distancia > -50: # -50 permite acertar só até o limitezinho da linha antes de perder
                    
                    # Exige o NOTA_PERFEITA_MIC para evitar slides
                    if not nota_hit_neste_frame and self.nota_perfeita_mic and self.equivalencia_notas(self.nota_perfeita_mic, n['nota']):
                        n['sendo_tocada'] = True
                        nota_hit_neste_frame = True 

                        if not n.get('ponto_computado', False):
                            if distancia >= 0:
                                # Mais no alto = mais próximo de 10. Pertinho da linha vermelha = próximo a 1
                                pontos = int((distancia / linha_vermelha_y) * 9) + 1
                                self.pontuacao += min(10, max(1, pontos))
                            else:
                                # Passou um tiquinho da linha
                                self.pontuacao -= 2
                                
                            n['ponto_computado'] = True
                            self.gerar_faiscas(n['x'], n['y'])

                        if n['sustain'] > 0:
                            n['tempo_sustain'] += vel_queda * 2 
                            self.gerar_faiscas(n['x'], n['y']) 
                            if n['tempo_sustain'] >= n['sustain']:
                                self.pontuacao += 5 
                                notas_para_remover.append(i)
                        else:
                            notas_para_remover.append(i)
                            
                    else:
                        n['sendo_tocada'] = False 

                if n['y'] - n['sustain'] > altura:
                    self.pontuacao -= 5
                    if i not in notas_para_remover: notas_para_remover.append(i)

            for i in sorted(notas_para_remover, reverse=True): self.notas_na_tela.pop(i)

        # =========================================================
        # INDICADOR DO MICROFONE (COM FEEDBACK DE AFINAÇÃO!)
        # =========================================================
        x_indicador = largura // 2
        
        # Decide a cor da borda do microfone
        cor_mic_borda = self.BRANCO
        if self.nota_atual_mic:
            if self.nota_perfeita_mic: cor_mic_borda = self.VERDE  # Afinação perfeita!
            elif self.desvio_afinacao < 0: cor_mic_borda = self.AMARELO # Flopou (Grave)
            else: cor_mic_borda = self.VERMELHO # Pressionou muito forte (Agudo)

        pygame.draw.circle(tela, (60, 60, 60), (x_indicador, self.y_indicador_anim), 28)
        pygame.draw.circle(tela, cor_mic_borda, (x_indicador, self.y_indicador_anim), 28, 3)
        
        if self.nota_atual_mic:
            txt_mic = fonte_ui.render(self.nota_atual_mic, True, self.BRANCO)
            tela.blit(txt_mic, (x_indicador - txt_mic.get_width()//2, self.y_indicador_anim - txt_mic.get_height()//2))
        else:
            txt_mic = fonte_peq.render("...", True, (150, 150, 150))
            tela.blit(txt_mic, (x_indicador - txt_mic.get_width()//2, self.y_indicador_anim - txt_mic.get_height()//2))

        w_vol = 15; h_vol = 50; x_vol = x_indicador + 40; y_vol = self.y_indicador_anim - (h_vol // 2) 
        pygame.draw.rect(tela, (40, 40, 40), (x_vol, y_vol, w_vol, h_vol), border_radius=3)
        alt_p = int(h_vol * self.nivel_volume)
        pygame.draw.rect(tela, self.VERDE, pygame.Rect(x_vol, y_vol + h_vol - alt_p, w_vol, alt_p), border_radius=3)
        pygame.draw.rect(tela, self.BRANCO, (x_vol, y_vol, w_vol, h_vol), 1, border_radius=3)

        # INTERFACE INICIAL
        if not self.jogo_iniciado:
            if meu_gravador:
                x_sel = largura // 2 - 180; y_sel = y_centro + 50
                pygame.draw.rect(tela, (40, 40, 40), (x_sel, y_sel, 360, 40), border_radius=5)
                pygame.draw.rect(tela, (150, 150, 150), (x_sel, y_sel, 360, 40), 2, border_radius=5)
                
                self.btn_disp_esq.topleft = (x_sel, y_sel); self.btn_disp_dir.topleft = (x_sel + 320, y_sel)
                pygame.draw.rect(tela, self.AZUL_INTERFACE, self.btn_disp_esq, border_radius=5)
                pygame.draw.rect(tela, self.AZUL_INTERFACE, self.btn_disp_dir, border_radius=5)
                
                txt_esq = fonte_peq.render("<", True, self.BRANCO); txt_dir = fonte_peq.render(">", True, self.BRANCO)
                tela.blit(txt_esq, (self.btn_disp_esq.centerx - txt_esq.get_width()//2, self.btn_disp_esq.centery - txt_esq.get_height()//2))
                tela.blit(txt_dir, (self.btn_disp_dir.centerx - txt_dir.get_width()//2, self.btn_disp_dir.centery - txt_dir.get_height()//2))
                
                nome_disp = f"ID: {getattr(meu_gravador, 'device_id', 0)}"
                for d in self.lista_dispositivos:
                    if d['id'] == getattr(meu_gravador, 'device_id', 0): nome_disp = d['name']; break
                if len(nome_disp) > 28: nome_disp = nome_disp[:25] + "..."
                txt_nome = fonte_peq.render(nome_disp, True, self.BRANCO)
                tela.blit(txt_nome, (largura//2 - txt_nome.get_width()//2, y_sel + 20 - txt_nome.get_height()//2))

                x_dif = largura // 2 - 180; y_dif = y_sel + 50
                pygame.draw.rect(tela, (40, 40, 40), (x_dif, y_dif, 175, 40), border_radius=5)
                pygame.draw.rect(tela, (150, 150, 150), (x_dif, y_dif, 175, 40), 2, border_radius=5)
                self.btn_dif_esq.topleft = (x_dif, y_dif); self.btn_dif_dir.topleft = (x_dif + 145, y_dif)
                pygame.draw.rect(tela, self.AZUL_INTERFACE, self.btn_dif_esq, border_radius=5)
                pygame.draw.rect(tela, self.AZUL_INTERFACE, self.btn_dif_dir, border_radius=5)
                tela.blit(txt_esq, (self.btn_dif_esq.centerx - txt_esq.get_width()//2, self.btn_dif_esq.centery - txt_esq.get_height()//2))
                tela.blit(txt_dir, (self.btn_dif_dir.centerx - txt_dir.get_width()//2, self.btn_dif_dir.centery - txt_dir.get_height()//2))
                txt_dif = fonte_peq.render(self.dificuldades[self.idx_dificuldade], True, self.BRANCO)
                tela.blit(txt_dif, (x_dif + 87 - txt_dif.get_width()//2, y_dif + 20 - txt_dif.get_height()//2))

                x_vel = largura // 2 + 5; y_vel = y_sel + 50
                pygame.draw.rect(tela, (40, 40, 40), (x_vel, y_vel, 175, 40), border_radius=5)
                pygame.draw.rect(tela, (150, 150, 150), (x_vel, y_vel, 175, 40), 2, border_radius=5)
                self.btn_vel_esq.topleft = (x_vel, y_vel); self.btn_vel_dir.topleft = (x_vel + 145, y_vel)
                pygame.draw.rect(tela, self.AZUL_INTERFACE, self.btn_vel_esq, border_radius=5)
                pygame.draw.rect(tela, self.AZUL_INTERFACE, self.btn_vel_dir, border_radius=5)
                tela.blit(txt_esq, (self.btn_vel_esq.centerx - txt_esq.get_width()//2, self.btn_vel_esq.centery - txt_esq.get_height()//2))
                tela.blit(txt_dir, (self.btn_vel_dir.centerx - txt_dir.get_width()//2, self.btn_vel_dir.centery - txt_dir.get_height()//2))
                txt_vel = fonte_peq.render(f"Vel: {self.velocidade}", True, self.BRANCO)
                tela.blit(txt_vel, (x_vel + 87 - txt_vel.get_width()//2, y_vel + 20 - txt_vel.get_height()//2))

            if not self.em_calibracao:
                self.btn_calibrar.center = (largura // 2, y_centro - 20)
                pygame.draw.rect(tela, self.AZUL_INTERFACE, self.btn_calibrar, border_radius=10)
                pygame.draw.rect(tela, self.BRANCO, self.btn_calibrar, 2, border_radius=10) 
                txt = fonte_ui.render("INICIAR CALIBRAÇÃO", True, self.BRANCO)
                tela.blit(txt, (self.btn_calibrar.centerx - txt.get_width()//2, self.btn_calibrar.centery - txt.get_height()//2))

            else:
                sub_msg = "Toque a nota em destaque (CRAVE A AFINAÇÃO!)" if not self.calibrado else "Calibração concluída!"
                txt_msg = fonte_ui.render(sub_msg, True, self.AMARELO if not self.calibrado else self.VERDE)
                tela.blit(txt_msg, (largura//2 - txt_msg.get_width()//2, y_centro - 90))

                espacamento = 100; x_ini = largura // 2 - ((len(self.notas_calibracao) - 1) * espacamento) // 2
                for i, nota in enumerate(self.notas_calibracao):
                    cor = self.VERMELHO
                    if self.status_notas[i] == 1: cor = self.AMARELO
                    elif self.status_notas[i] == 2: cor = self.VERDE
                    pygame.draw.circle(tela, self.BRANCO, (x_ini + i * espacamento, y_centro - 20), 35, 2)
                    pygame.draw.circle(tela, cor, (x_ini + i * espacamento, y_centro - 20), 32)
                    txt_n = fonte_ui.render(nota, True, (0,0,0) if cor == self.AMARELO else self.BRANCO)
                    tela.blit(txt_n, (x_ini + i * espacamento - txt_n.get_width()//2, y_centro - 20 - txt_n.get_height()//2))

                self.btn_play.center = (largura // 2, altura - 80)
                cor_play = self.VERDE if self.calibrado else (70, 70, 70)
                pygame.draw.rect(tela, cor_play, self.btn_play, border_radius=10)
                if self.calibrado: pygame.draw.rect(tela, self.BRANCO, self.btn_play, 2, border_radius=10)
                txt_p = fonte_ui.render("COMEÇAR JOGO", True, self.BRANCO if self.calibrado else (150, 150, 150))
                tela.blit(txt_p, (self.btn_play.centerx - txt_p.get_width()//2, self.btn_play.centery - txt_p.get_height()//2))

    def tratar_clique(self, pos_mouse, meu_gravador=None):
        if self.jogo_iniciado: return False 

        if meu_gravador:
            if self.btn_disp_esq.collidepoint(pos_mouse): self._alterar_dispositivo(-1, meu_gravador); return True
            if self.btn_disp_dir.collidepoint(pos_mouse): self._alterar_dispositivo(1, meu_gravador); return True
            if self.btn_dif_esq.collidepoint(pos_mouse): self.idx_dificuldade = (self.idx_dificuldade - 1) % len(self.dificuldades); return True
            if self.btn_dif_dir.collidepoint(pos_mouse): self.idx_dificuldade = (self.idx_dificuldade + 1) % len(self.dificuldades); return True
            if self.btn_vel_esq.collidepoint(pos_mouse): self.velocidade = max(1, self.velocidade - 5); return True
            if self.btn_vel_dir.collidepoint(pos_mouse): self.velocidade = min(100, self.velocidade + 5); return True

        if not self.em_calibracao and self.btn_calibrar.collidepoint(pos_mouse):
            self.em_calibracao = True; return True
        
        if self.em_calibracao and self.calibrado and self.btn_play.collidepoint(pos_mouse):
            self.jogo_iniciado = True; self.ultimo_spawn = time.time(); return True
            
        return False

    def _alterar_dispositivo(self, direcao, meu_gravador):
        if not self.lista_dispositivos: return 
        id_atual = getattr(meu_gravador, 'device_id', 0)
        idx_atual = next((i for i, d in enumerate(self.lista_dispositivos) if d['id'] == id_atual), 0)
        novo_id = self.lista_dispositivos[(idx_atual + direcao) % len(self.lista_dispositivos)]['id']
        meu_gravador.device_id = novo_id
        if hasattr(meu_gravador, 'mudar_dispositivo'):
            try: meu_gravador.mudar_dispositivo(novo_id)
            except:
                try: meu_gravador.mudar_dispositivo()
                except: pass