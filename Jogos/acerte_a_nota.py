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
        self.nota_perfeita_mic = "" 
        self.desvio_afinacao = 0.0  
        self.nivel_volume = 0.0 
        self.y_indicador_anim = None 
        
        # --- VARIÁVEIS DO JOGO ---
        self.dificuldades = ["FÁCIL", "MÉDIA", "DIFÍCIL", "IMPOSSÍVEL"]
        self.idx_dificuldade = 0
        self.velocidade = 50 

        # --- SELETOR DE ÁUDIO E FILA ---
        self.modos_audio = ["DESLIGADO", "VOZ (NOME)", "SOM (NOTA)"]
        self.idx_audio = 0
        self.fila_audio = [] 
        self.tempo_inicio_fala = 0
        self.duracao_permitida = 0
        
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
        self.btn_aud_esq, self.btn_aud_dir = pygame.Rect(0, 0, 30, 40), pygame.Rect(0, 0, 30, 40)

        # Mapeamento de Dispositivos
        self.lista_dispositivos = []
        try:
            import sounddevice as sd
            for i, dev in enumerate(sd.query_devices()):
                if dev['max_input_channels'] > 0:
                    self.lista_dispositivos.append({'id': i, 'name': dev['name']})
        except: pass
        
        # --- ASSETS ---
        try:
            if getattr(sys, 'frozen', False):
                pasta_jogos = os.path.dirname(sys.executable)
                pasta_raiz = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            else:
                pasta_jogos = os.path.dirname(os.path.abspath(__file__))
                pasta_raiz = os.path.dirname(pasta_jogos)

            self.fundo = pygame.image.load(os.path.join(pasta_raiz, "fundo_jogo.png")).convert_alpha()
            self.pasta_audios = os.path.join(pasta_jogos, "Audios")
        except:
            self.fundo = None
            self.pasta_audios = ""
            
        self.tam_anterior = (0, 0)
        self.fundo_render = None

        # --- SISTEMA DE SOM ---
        self.sons_notas = {}
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        self.canal_voz = pygame.mixer.Channel(0)
        pygame.mixer.set_num_channels(64) 
            
        todas_as_notas = self.notas_naturais + self.notas_sustenidos + self.notas_bemois
        for n in todas_as_notas:
            caminho_wav = os.path.join(self.pasta_audios, f"{n}.wav")
            if os.path.exists(caminho_wav):
                try:
                    self.sons_notas[n] = pygame.mixer.Sound(caminho_wav)
                    self.sons_notas[n].set_volume(0.8) 
                except: pass

    def equivalencia_notas(self, nota1, nota2):
        if nota1 == nota2: return True
        enarmonicas = {"C#": "Db", "Db": "C#", "D#": "Eb", "Eb": "D#", "F#": "Gb", "Gb": "F#", "G#": "Ab", "Ab": "G#", "A#": "Bb", "Bb": "A#"}
        return enarmonicas.get(nota1) == nota2 or enarmonicas.get(nota2) == nota1

    def gerar_faiscas(self, x, y):
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
        try:
            f = float(freq_detectada)
            if f < 20.0:
                self.nota_atual_mic = ""; self.nota_perfeita_mic = ""
                self.nivel_volume = max(0.0, self.nivel_volume - 0.1)
                return
            valor_exato = 12 * math.log2(f / 440.0)
            semitons_de_A4 = round(valor_exato)
            self.desvio_afinacao = valor_exato - semitons_de_A4 
            indice_nota = (semitons_de_A4 + 9) % 12
            notas_str = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            nota_encontrada = notas_str[int(indice_nota)]
            self.nota_atual_mic = nota_encontrada
            self.nivel_volume = min(1.0, 0.7 + random.uniform(0.0, 0.3))
            if abs(self.desvio_afinacao) <= 0.15: self.nota_perfeita_mic = nota_encontrada
            else: self.nota_perfeita_mic = ""
        except:
            self.nota_atual_mic = ""; self.nota_perfeita_mic = ""
            self.nivel_volume = max(0.0, self.nivel_volume - 0.1)

        if self.nota_perfeita_mic and self.em_calibracao and not self.calibrado and not self.jogo_iniciado:
            if self.nota_perfeita_mic == self.notas_calibracao[self.indice_atual]:
                self.status_notas[self.indice_atual] = 2 
                self.indice_atual += 1
                if self.indice_atual < len(self.notas_calibracao): self.status_notas[self.indice_atual] = 1 
                else: self.calibrado = True

    def atualizar_fila_voz(self):
        if self.modos_audio[self.idx_audio] == "DESLIGADO" or not self.fila_audio:
            return

        tempo_atual = time.time()
        fator_aceleracao = 1.0 - (self.idx_dificuldade * 0.12) - (self.velocidade / 400.0)
        fator_aceleracao = max(0.35, fator_aceleracao)

        if not self.canal_voz.get_busy():
            proxima_nota = self.fila_audio.pop(0)
            if proxima_nota in self.sons_notas:
                som = self.sons_notas[proxima_nota]
                self.duracao_permitida = som.get_length() * fator_aceleracao
                self.tempo_inicio_fala = tempo_atual
                self.canal_voz.play(som)
        else:
            if tempo_atual - self.tempo_inicio_fala >= self.duracao_permitida:
                self.canal_voz.stop()

    def gerar_notas_jogo(self, largura):
        agora = time.time()
        intervalo_spawn = 5.0 - ((self.velocidade / 100.0) * 3.5) 
        if agora - self.ultimo_spawn > intervalo_spawn:
            self.ultimo_spawn = agora
            dif = self.dificuldades[self.idx_dificuldade]
            pool = self.notas_naturais[:]
            qnt = 1
            if dif != "FÁCIL": pool += self.notas_sustenidos
            if dif == "MÉDIA": qnt = random.choice([1, 2])
            if dif == "DIFÍCIL": qnt = random.randint(2, 3)
            if dif == "IMPOSSÍVEL": pool += self.notas_bemois; qnt = random.randint(3, 5)
            
            for _ in range(qnt):
                nota_sorteada = random.choice(pool)
                if self.modos_audio[self.idx_audio] != "DESLIGADO":
                    self.fila_audio.append(nota_sorteada)
                
                self.notas_na_tela.append({
                    'nota': nota_sorteada, 'x': random.randint(150, largura-250), 'y': -50,
                    'sustain': 0, 'sendo_tocada': False, 'ponto_computado': False
                })

    def desenhar(self, tela, largura, altura, meu_gravador=None):
        self.atualizar_fila_voz()

        if self.fundo:
            if self.tam_anterior != (largura, altura):
                self.fundo_render = pygame.transform.smoothscale(self.fundo, (largura, altura))
                self.tam_anterior = (largura, altura)
            tela.blit(self.fundo_render, (0, 0))
        else: tela.fill((30, 30, 30))

        fonte_tit = pygame.font.SysFont("Arial", 40, bold=True)
        fonte_ui = pygame.font.SysFont("Arial", 25, bold=True)
        fonte_peq = pygame.font.SysFont("Arial", 18, bold=True)
        linha_vermelha_y = altura - 150
        y_centro = altura // 2

        if self.y_indicador_anim is None: self.y_indicador_anim = y_centro - 160
        alvo_y = altura - 60 if self.jogo_iniciado else y_centro - 160
        self.y_indicador_anim += (alvo_y - self.y_indicador_anim) * 0.08

        if self.jogo_iniciado:
            # --- RÉGUA E PONTOS ---
            txt_pontos = fonte_tit.render(f"PONTOS: {self.pontuacao}", True, self.AMARELO)
            tela.blit(txt_pontos, (largura - txt_pontos.get_width() - 30, 40))
            pygame.draw.line(tela, self.VERMELHO, (0, linha_vermelha_y), (largura - 100, linha_vermelha_y), 3)

            x_regua = largura - 80
            pygame.draw.line(tela, self.BRANCO, (x_regua, 100), (x_regua, altura - 50), 4)
            tela.blit(fonte_peq.render("10", True, self.VERDE), (x_regua + 15, 100))
            tela.blit(fonte_peq.render("1", True, self.VERMELHO), (x_regua + 15, linha_vermelha_y - 20))

            # --- LÓGICA DAS NOTAS ---
            self.gerar_notas_jogo(largura)
            for p in self.particulas[:]:
                p['x'] += p['vx']; p['y'] += p['vy']; p['vy'] += 0.2; p['vida'] -= 0.03
                if p['vida'] > 0:
                    pygame.draw.circle(tela, (255, int(255 * p['vida']), 0), (int(p['x']), int(p['y'])), max(1, int(6 * p['vida'])))
                else: self.particulas.remove(p)

            for i, n in enumerate(self.notas_na_tela[:]):
                n['y'] += 1.0 + (self.velocidade / 50.0)
                pygame.draw.circle(tela, self.AZUL_INTERFACE, (n['x'], int(n['y'])), 35)
                pygame.draw.circle(tela, self.BRANCO, (n['x'], int(n['y'])), 35, 2)
                txt_n = fonte_ui.render(n['nota'], True, self.BRANCO)
                tela.blit(txt_n, (n['x'] - txt_n.get_width()//2, int(n['y']) - txt_n.get_height()//2))

                distancia = linha_vermelha_y - n['y']
                if distancia > -50:
                    if self.nota_perfeita_mic and self.equivalencia_notas(self.nota_perfeita_mic, n['nota']):
                        if not n['ponto_computado']:
                            pontos = int((distancia / linha_vermelha_y) * 9) + 1 if distancia >= 0 else -2
                            self.pontuacao += min(10, max(-2, pontos))
                            n['ponto_computado'] = True
                        self.gerar_faiscas(n['x'], n['y'])
                        self.notas_na_tela.remove(n)
                if n['y'] > altura:
                    self.pontuacao -= 5
                    self.notas_na_tela.remove(n)

        # --- INTERFACE INICIAL ---
        if not self.jogo_iniciado:
            if not self.em_calibracao:
                txt_tit = fonte_tit.render("ACERTE A NOTA", True, self.BRANCO)
                tela.blit(txt_tit, (largura//2 - txt_tit.get_width()//2, 50))
                
                x_sel = largura // 2 - 270
                y_sel = y_centro + 50
                self._desenhar_botao_seletor(tela, x_sel, y_sel, f"{self.dificuldades[self.idx_dificuldade]}", self.btn_dif_esq, self.btn_dif_dir)
                self._desenhar_botao_seletor(tela, x_sel + 185, y_sel, f"{self.modos_audio[self.idx_audio]}", self.btn_aud_esq, self.btn_aud_dir)
                self._desenhar_botao_seletor(tela, x_sel + 370, y_sel, f"Vel: {self.velocidade}", self.btn_vel_esq, self.btn_vel_dir)

                self.btn_calibrar.center = (largura // 2, y_centro - 20)
                pygame.draw.rect(tela, self.AZUL_INTERFACE, self.btn_calibrar, border_radius=10)
                txt_c = fonte_ui.render("INICIAR CALIBRAÇÃO", True, self.BRANCO)
                tela.blit(txt_c, (self.btn_calibrar.centerx - txt_c.get_width()//2, self.btn_calibrar.centery - txt_c.get_height()//2))

                self.btn_play.center = (largura // 2, altura - 100)
                pygame.draw.rect(tela, self.VERDE, self.btn_play, border_radius=10)
                txt_p = fonte_ui.render("COMEÇAR JOGO", True, self.BRANCO)
                tela.blit(txt_p, (self.btn_play.centerx - txt_p.get_width()//2, self.btn_play.centery - txt_p.get_height()//2))
            else:
                # TELA DE CALIBRAÇÃO
                msg = "Toque a nota amarela" if not self.calibrado else "Calibração Concluída!"
                txt_m = fonte_ui.render(msg, True, self.AMARELO if not self.calibrado else self.VERDE)
                tela.blit(txt_m, (largura//2 - txt_m.get_width()//2, y_centro - 100))
                esp = 100; x_i = largura//2 - (3*esp)
                for i, n in enumerate(self.notas_calibracao):
                    cor = self.VERDE if self.status_notas[i] == 2 else (self.AMARELO if self.status_notas[i] == 1 else self.VERMELHO)
                    pygame.draw.circle(tela, cor, (x_i + i*esp, y_centro), 35)
                    pygame.draw.circle(tela, self.BRANCO, (x_i + i*esp, y_centro), 35, 2)
                    txt_n = fonte_peq.render(n, True, self.BRANCO)
                    tela.blit(txt_n, (x_i + i*esp - txt_n.get_width()//2, y_centro - txt_n.get_height()//2))
                
                self.btn_play.center = (largura // 2, altura - 80)
                pygame.draw.rect(tela, self.VERDE, self.btn_play, border_radius=10)
                txt_v = fonte_ui.render("VOLTAR" if self.calibrado else "CANCELAR", True, self.BRANCO)
                tela.blit(txt_v, (self.btn_play.centerx - txt_v.get_width()//2, self.btn_play.centery - txt_v.get_height()//2))

        # --- INDICADOR MIC E BARRA DE VOLUME (RECUPERADA) ---
        cor_b = self.VERDE if self.nota_perfeita_mic else (self.AMARELO if self.nota_atual_mic else self.BRANCO)
        x_mic = largura // 2
        y_mic = int(self.y_indicador_anim)
        pygame.draw.circle(tela, (60, 60, 60), (x_mic, y_mic), 28)
        pygame.draw.circle(tela, cor_b, (x_mic, y_mic), 28, 3)
        if self.nota_atual_mic:
            txt_m = fonte_ui.render(self.nota_atual_mic, True, self.BRANCO)
            tela.blit(txt_m, (x_mic - txt_m.get_width()//2, y_mic - txt_m.get_height()//2))
            
        # RETÂNGULO DO VOLUME
        w_vol = 15; h_vol = 50; x_vol = x_mic + 40; y_vol = y_mic - (h_vol // 2) 
        pygame.draw.rect(tela, (40, 40, 40), (x_vol, y_vol, w_vol, h_vol), border_radius=3)
        alt_p = int(h_vol * self.nivel_volume)
        pygame.draw.rect(tela, self.VERDE, pygame.Rect(x_vol, y_vol + h_vol - alt_p, w_vol, alt_p), border_radius=3)
        pygame.draw.rect(tela, self.BRANCO, (x_vol, y_vol, w_vol, h_vol), 1, border_radius=3)

    def _desenhar_botao_seletor(self, tela, x, y, texto, b_esq, b_dir):
        pygame.draw.rect(tela, (40, 40, 40), (x, y, 175, 40), border_radius=5)
        b_esq.topleft = (x, y); b_dir.topleft = (x + 145, y)
        pygame.draw.rect(tela, self.AZUL_INTERFACE, b_esq, border_radius=5)
        pygame.draw.rect(tela, self.AZUL_INTERFACE, b_dir, border_radius=5)
        f = pygame.font.SysFont("Arial", 16, bold=True)
        t = f.render(texto, True, self.BRANCO)
        tela.blit(t, (x + 87 - t.get_width()//2, y + 10))
        tela.blit(f.render("<", True, self.BRANCO), (b_esq.centerx-5, b_esq.centery-10))
        tela.blit(f.render(">", True, self.BRANCO), (b_dir.centerx-5, b_dir.centery-10))

    def tratar_clique(self, pos_mouse, meu_gravador=None):
        if self.jogo_iniciado: return False 
        if not self.em_calibracao:
            if self.btn_dif_esq.collidepoint(pos_mouse): self.idx_dificuldade = (self.idx_dificuldade - 1) % 4; return True
            if self.btn_dif_dir.collidepoint(pos_mouse): self.idx_dificuldade = (self.idx_dificuldade + 1) % 4; return True
            if self.btn_aud_esq.collidepoint(pos_mouse): self.idx_audio = (self.idx_audio - 1) % 3; return True
            if self.btn_aud_dir.collidepoint(pos_mouse): self.idx_audio = (self.idx_audio + 1) % 3; return True
            if self.btn_vel_esq.collidepoint(pos_mouse): self.velocidade = max(1, self.velocidade - 5); return True
            if self.btn_vel_dir.collidepoint(pos_mouse): self.velocidade = min(100, self.velocidade + 5); return True
            if self.btn_calibrar.collidepoint(pos_mouse): self.em_calibracao = True; return True
        if self.btn_play.collidepoint(pos_mouse):
            if self.em_calibracao: self.em_calibracao = False
            else: self.jogo_iniciado = True; self.ultimo_spawn = time.time()
            return True
        return False

    def _alterar_dispositivo(self, direcao, meu_gravador):
        if not self.lista_dispositivos: return 
        id_atual = getattr(meu_gravador, 'device_id', 0)
        idx_atual = next((i for i, d in enumerate(self.lista_dispositivos) if d['id'] == id_atual), 0)
        novo_id = self.lista_dispositivos[(idx_atual + direcao) % len(self.lista_dispositivos)]['id']
        meu_gravador.device_id = novo_id
        if hasattr(meu_gravador, 'mudar_dispositivo'):
            try: meu_gravador.mudar_dispositivo(novo_id)
            except: pass