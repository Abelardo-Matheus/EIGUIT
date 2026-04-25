import librosa
import numpy as np
import pygame

class ProcessadorAudio:
    def __init__(self, taxa_amostragem=48000):
        self.sr = taxa_amostragem
        
        # Agora as listas nascem vazias e se adaptam à afinação do usuário
        self.nomes_exibicao = []
        self.ordem_cordas = []
        self.freqs_referencia = []
        
        self.nota_detectada = "Microfone Desligado"
        self.freq_atual = 0.0
        self.corda_selecionada = None 
        
        self.ultimo_tempo_analise = 0
        self.intervalo_analise = 100 
        
        self.lista_dispositivos = []
        self.indice_dispositivo = 0
        self.carregou_dispositivos = False
        
        self.rect_seta_esq = pygame.Rect(0, 0, 30, 30)
        self.rect_seta_dir = pygame.Rect(0, 0, 30, 30)
        self.rects_cordas = []
        
        self.AZUL_BOTAO = (0, 120, 215)
        self.VERDE = (0, 255, 100)
        self.VERMELHO = (255, 50, 50)
        self.BRANCO = (255, 255, 255)
        self.CINZA = (150, 150, 150)
        self.FUNDO_ESCURO = (40, 40, 40)

    def atualizar_afinacao(self, notas_abertas):
        """Lê a lista de notas e calcula automaticamente as oitavas e frequências (Hz)"""
        if self.nomes_exibicao == notas_abertas: 
            return # Só recalcula se a afinação do painel mudou!

        self.nomes_exibicao = notas_abertas
        self.ordem_cordas = []
        self.freqs_referencia = []
        
        # Algoritmo Inteligente de Oitavas: Se a nota passar por Dó (C), a oitava sobe
        notas_escala = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        oitava_atual = 1 # A 7ª corda de uma guitarra geralmente fica na oitava 1
        
        if len(notas_abertas) > 0:
            ultimo_idx = notas_escala.index(notas_abertas[0])
            for nota in notas_abertas:
                idx = notas_escala.index(nota)
                if idx < ultimo_idx: 
                    oitava_atual += 1
                ultimo_idx = idx
                
                nome_completo = f"{nota}{oitava_atual}"
                self.ordem_cordas.append(nome_completo)
                
                # Usa o librosa para pegar a frequência matemática exata da nota!
                freq = float(librosa.note_to_hz(nome_completo))
                self.freqs_referencia.append(freq)
        
        # Reseta o afinador caso o usuário troque de afinação enquanto afina
        self.corda_selecionada = None 
    
    def extrair_nota_dominante(self, audio_array):
        if audio_array is None or len(audio_array) == 0: return ""
        if audio_array.ndim > 1: audio_array = np.mean(audio_array, axis=1)
        chroma = librosa.feature.chroma_stft(y=audio_array, sr=self.sr)
        notas = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        return notas[np.argmax(np.mean(chroma, axis=1))]
    
    def extrair_pitch_exato(self, audio_array, tolerancia):
        if audio_array is None or len(audio_array) == 0: return 0.0
        
        # Filtro de Volume (Noise Gate): Ignora som se for muito baixo
        if np.max(np.abs(audio_array)) < 0.01:
            return 0.0

        # O yin() do librosa aceita um parâmetro de tolerância (trough_threshold)
        # Menor = Mais rigoroso (ignora harmônicos), Maior = Mais fácil
        f0 = librosa.yin(audio_array, fmin=60, fmax=400, sr=self.sr, trough_threshold=tolerancia)
        
        f0_valido = f0[f0 > 0]
        if len(f0_valido) > 0:
            # Pega a mediana em vez da média, elimina picos malucos (outliers)
            return np.median(f0_valido) 
        return 0.0

    def processar_logica_continua(self, gravador, estado):
        if not gravador.gravando:
            self.nota_detectada = "Microfone Desligado"
            self.freq_atual = 0.0
            estado.freq_detectada = 0.0
            estado.historico_freqs.clear() # Limpa o histórico se desligar
            return

        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.ultimo_tempo_analise > self.intervalo_analise:
            self.ultimo_tempo_analise = tempo_atual
            
            audio_cru = gravador.obter_array_para_ia()
            if audio_cru is not None:
                # Usa a tolerância do Estado
                freq_crua = self.extrair_pitch_exato(audio_cru, estado.afinador_sensibilidade)
                
                # --- SISTEMA DE SUAVIZAÇÃO (MÉDIA MÓVEL) ---
                if freq_crua > 0:
                    estado.historico_freqs.append(freq_crua)
                    # Mantém o histórico no tamanho da suavização escolhida
                    if len(estado.historico_freqs) > estado.afinador_suavizacao:
                        estado.historico_freqs.pop(0)
                        
                    # A frequência exata é a média do histórico
                    freq_exata = sum(estado.historico_freqs) / len(estado.historico_freqs)
                else:
                    estado.historico_freqs.clear()
                    freq_exata = 0.0
                
                estado.freq_detectada = freq_exata
                
                if self.corda_selecionada is not None:
                    self.freq_atual = freq_exata
                    self.nota_detectada = f"Frequência: {self.freq_atual:.2f} Hz"
                else:
                    if freq_crua > 0:
                        nota = self.extrair_nota_dominante(audio_cru)
                        self.nota_detectada = f"Nota no Braço: {nota}"
                    self.freq_atual = freq_exata
            else:
                self.nota_detectada = "Aguardando som..."
                self.freq_atual = 0.0
                estado.freq_detectada = 0.0
                estado.historico_freqs.clear()

    # --- NOVO: FUNÇÃO PARA CLICAR NOS CONTROLES ---
    def tratar_clique_calibracao(self, pos_mouse, estado, offset_x, y_caixa):
        # Mesmas coordenadas que usamos para desenhar os botões
        x_calib = offset_x +530
        y_suav = y_caixa + 65  
        y_sens = y_caixa + 115 
        
        # --- Botões de Suavização (- e +) ---
        r_menos_suav = pygame.Rect(x_calib + 220, y_suav, 30, 30)
        r_mais_suav = pygame.Rect(x_calib + 300, y_suav, 30, 30)
        
        if r_menos_suav.collidepoint(pos_mouse):
            estado.afinador_suavizacao = max(1, estado.afinador_suavizacao - 1)
            return True
        if r_mais_suav.collidepoint(pos_mouse):
            estado.afinador_suavizacao = min(20, estado.afinador_suavizacao + 1)
            return True
            
        # --- Botões de Sensibilidade (- e +) ---
        r_menos_sens = pygame.Rect(x_calib + 220, y_sens, 30, 30)
        r_mais_sens = pygame.Rect(x_calib + 300, y_sens, 30, 30)
        
        if r_menos_sens.collidepoint(pos_mouse):
            # Usamos round() porque o Python as vezes faz 0.5 - 0.1 = 0.3999999
            estado.afinador_sensibilidade = round(max(0.1, estado.afinador_sensibilidade - 0.1), 1)
            return True
        if r_mais_sens.collidepoint(pos_mouse):
            estado.afinador_sensibilidade = round(min(0.9, estado.afinador_sensibilidade + 0.1), 1)
            return True
            
        return False

    def tratar_clique(self, pos_mouse, rect_botao, gravador):
        if rect_botao.collidepoint(pos_mouse):
            gravador.alternar_microfone()
            return True
            
        if len(self.lista_dispositivos) > 0:
            if self.rect_seta_esq.collidepoint(pos_mouse):
                self.indice_dispositivo = (self.indice_dispositivo - 1) % len(self.lista_dispositivos)
                gravador.mudar_dispositivo(self.lista_dispositivos[self.indice_dispositivo]['id'])
                return True
            if self.rect_seta_dir.collidepoint(pos_mouse):
                self.indice_dispositivo = (self.indice_dispositivo + 1) % len(self.lista_dispositivos)
                gravador.mudar_dispositivo(self.lista_dispositivos[self.indice_dispositivo]['id'])
                return True

        for i, rect in enumerate(self.rects_cordas):
            if rect.collidepoint(pos_mouse):
                self.corda_selecionada = None if self.corda_selecionada == i else i
                return True
        return False

    def desenhar_aba_ia(self, tela, offset_x, y_caixa, rect_botao, gravador, fonte_ui, fonte_titulo, notas_abertas, estado):
        # --- ATUALIZA A AFINAÇÃO DINAMICAMENTE AQUI ---
        self.atualizar_afinacao(notas_abertas)

        if not self.carregou_dispositivos:
            self.lista_dispositivos = gravador.obter_lista_entradas()
            for i, disp in enumerate(self.lista_dispositivos):
                if disp['id'] == gravador.device_id:
                    self.indice_dispositivo = i
                    break
            self.carregou_dispositivos = True

        # Título da Sessão
        txt = fonte_titulo.render("Detecção em Tempo Real", True, self.BRANCO)
        tela.blit(txt, (offset_x + 20, y_caixa + 20))

        # ==========================================================
        # --- SETOR: PAINEL DE CALIBRAÇÃO (No lado direito) ---
        # ==========================================================
        x_calib = offset_x + 450
        distancia_x = 300  # Aumente isso se quiser afastar ainda mais os botões do texto!
        
        y_suav = y_caixa + 20
        tela.blit(fonte_ui.render("Estabilidade da Agulha:", True, self.CINZA), (x_calib+90, y_suav + 5))
        
        # Botões Suavização
        r_menos_suav = pygame.Rect(x_calib + distancia_x, y_suav, 30, 30)
        r_mais_suav = pygame.Rect(x_calib + distancia_x + 80, y_suav, 30, 30)
        pygame.draw.rect(tela, self.AZUL_BOTAO, r_menos_suav, border_radius=5)
        pygame.draw.rect(tela, self.AZUL_BOTAO, r_mais_suav, border_radius=5)
        tela.blit(fonte_ui.render("-", True, self.BRANCO), (r_menos_suav.centerx - 5, r_menos_suav.centery - 10))
        tela.blit(fonte_ui.render("+", True, self.BRANCO), (r_mais_suav.centerx - 5, r_mais_suav.centery - 10))
        
        # Valor Suavização
        txt_suav = fonte_titulo.render(str(estado.afinador_suavizacao), True, self.BRANCO)
        tela.blit(txt_suav, (x_calib + distancia_x + 45, y_suav + 5))

        y_sens = y_caixa + 70
        tela.blit(fonte_ui.render("Rigor da Frequência:", True, self.CINZA), (x_calib+90, y_sens + 5))
        
        # Botões Sensibilidade
        r_menos_sens = pygame.Rect(x_calib + distancia_x, y_sens, 30, 30)
        r_mais_sens = pygame.Rect(x_calib + distancia_x + 80, y_sens, 30, 30)
        pygame.draw.rect(tela, self.AZUL_BOTAO, r_menos_sens, border_radius=5)
        pygame.draw.rect(tela, self.AZUL_BOTAO, r_mais_sens, border_radius=5)
        tela.blit(fonte_ui.render("-", True, self.BRANCO), (r_menos_sens.centerx - 5, r_menos_sens.centery - 10))
        tela.blit(fonte_ui.render("+", True, self.BRANCO), (r_mais_sens.centerx - 5, r_mais_sens.centery - 10))
        
        # Valor Sensibilidade
        txt_sens = fonte_titulo.render(f"{estado.afinador_sensibilidade:.1f}", True, self.BRANCO)
        tela.blit(txt_sens, (x_calib + distancia_x + 40, y_sens + 5))
        # ==========================================================

        # --- SETOR: BOTÃO LIGAR MIC E NOTA DETECTADA ---
        cor_btn = self.VERMELHO if gravador.gravando else self.AZUL_BOTAO
        pygame.draw.rect(tela, cor_btn, rect_botao, border_radius=8)
        lbl = fonte_ui.render("MIC ABERTO" if gravador.gravando else "LIGAR MIC", True, self.BRANCO)
        tela.blit(lbl, (rect_botao.centerx - lbl.get_width()//2, rect_botao.centery - lbl.get_height()//2))

        cor_res = self.VERDE if gravador.gravando and "Aguardando" not in self.nota_detectada else self.CINZA
        txt_res = fonte_titulo.render(self.nota_detectada, True, cor_res)
        tela.blit(txt_res, (rect_botao.right + 20, rect_botao.y + 8))

        # --- SETOR: SELETOR DE MICROFONE ---
        y_seletor = rect_botao.bottom + 15
        tela.blit(fonte_ui.render("Microfone:", True, self.BRANCO), (offset_x + 20, y_seletor + 5))
        
        x_botoes = offset_x + 120
        self.rect_seta_esq.topleft = (x_botoes, y_seletor)
        
        largura_caixa = 250
        pygame.draw.rect(tela, self.FUNDO_ESCURO, (self.rect_seta_esq.right + 5, y_seletor, largura_caixa, 30), border_radius=5)
        
        if len(self.lista_dispositivos) > 0:
            nome_disp = self.lista_dispositivos[self.indice_dispositivo]['nome']
            if len(nome_disp) > 25: nome_disp = nome_disp[:22] + "..."
        else:
            nome_disp = "Nenhum detectado"
            
        txt_disp = fonte_ui.render(nome_disp, True, self.BRANCO)
        tela.blit(txt_disp, (self.rect_seta_esq.right + 15, y_seletor + 5))
        
        self.rect_seta_dir.topleft = (self.rect_seta_esq.right + 5 + largura_caixa + 5, y_seletor)

        pygame.draw.rect(tela, self.CINZA, self.rect_seta_esq, border_radius=5)
        pygame.draw.rect(tela, self.CINZA, self.rect_seta_dir, border_radius=5)
        tela.blit(fonte_ui.render("<", True, self.BRANCO), (self.rect_seta_esq.x + 8, self.rect_seta_esq.y + 4))
        tela.blit(fonte_ui.render(">", True, self.BRANCO), (self.rect_seta_dir.x + 8, self.rect_seta_dir.y + 4))

        # --- SETOR: BOLINHAS DO AFINADOR ---
        y_afinador_base = y_seletor + 45
        tela.blit(fonte_ui.render("Afinador (Clique para focar na corda):", True, self.BRANCO), (offset_x + 20, y_afinador_base))
        
        self.rects_cordas.clear()
        y_cordas = y_afinador_base + 40
        espacamento = 50
        
        for i, nome in enumerate(self.nomes_exibicao):
            cx = offset_x + 40 + (i * espacamento)
            raio = 18
            cor = self.VERDE if self.corda_selecionada == i else (60, 60, 60)
            
            circ = pygame.draw.circle(tela, cor, (cx, y_cordas), raio)
            pygame.draw.circle(tela, self.BRANCO, (cx, y_cordas), raio, 2)
            
            txt_n = fonte_ui.render(nome, True, self.BRANCO)
            tela.blit(txt_n, (cx - txt_n.get_width()//2, y_cordas - txt_n.get_height()//2))
            self.rects_cordas.append(circ)

        # --- SETOR: AGULHA DO AFINADOR ---
        if self.corda_selecionada is not None and gravador.gravando:
            nome_nota = self.ordem_cordas[self.corda_selecionada]
            freq_alvo = self.freqs_referencia[self.corda_selecionada]
            
            x_agulha_base = offset_x + 20
            y_agulha = y_cordas + 65
            largura_barra = 350
            
            pygame.draw.line(tela, (100, 100, 100), (x_agulha_base, y_agulha), (x_agulha_base + largura_barra, y_agulha), 4)
            pygame.draw.circle(tela, self.VERDE, (x_agulha_base + largura_barra//2, y_agulha), 6) 
            
            tela.blit(fonte_ui.render("Flat (-)", True, self.CINZA), (x_agulha_base, y_agulha + 15))
            tela.blit(fonte_ui.render("Sharp (+)", True, self.CINZA), (x_agulha_base + largura_barra - 60, y_agulha + 15))

            if self.freq_atual > 0:
                cents = 1200 * np.log2(self.freq_atual / freq_alvo)
                desvio_x = (cents / 50) * (largura_barra // 2)
                desvio_x = max(-largura_barra//2, min(largura_barra//2, desvio_x)) 
                
                cor_agulha = self.VERDE if abs(cents) < 5 else self.VERMELHO
                pos_agulha = x_agulha_base + largura_barra//2 + desvio_x
                
                pygame.draw.line(tela, cor_agulha, (pos_agulha, y_agulha - 30), (pos_agulha, y_agulha + 30), 4)
                
                txt_status = "AFINADO!" if abs(cents) < 5 else ("APERTAR" if cents < 0 else "FROUXAR")
                lbl_st = fonte_ui.render(f"{txt_status} ({cents:.1f} cents)", True, cor_agulha)
                tela.blit(lbl_st, (x_agulha_base + largura_barra//2 - lbl_st.get_width()//2, y_agulha - 45))
            
            tela.blit(fonte_ui.render(f"Alvo: {nome_nota} ({freq_alvo:.2f}Hz)", True, self.BRANCO), (x_agulha_base + largura_barra + 30, y_agulha - 10))