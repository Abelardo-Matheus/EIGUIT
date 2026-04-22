import librosa
import numpy as np
import pygame

class ProcessadorAudio:
    def __init__(self, taxa_amostragem=48000):
        self.sr = taxa_amostragem
        
        self.freqs_referencia = {
            'B': 61.74, 'E': 82.41, 'A': 110.00, 'D': 146.83, 
            'G': 196.00, 'B2': 246.94, 'E2': 329.63
        }
        self.ordem_cordas = ['B', 'E', 'A', 'D', 'G', 'B2', 'E2']
        self.nomes_exibicao = ['B', 'E', 'A', 'D', 'G', 'B', 'E']
        
        self.nota_detectada = "Microfone Desligado"
        self.freq_atual = 0.0
        self.corda_selecionada = None 
        
        self.ultimo_tempo_analise = 0
        self.intervalo_analise = 100 
        
        # --- NOVAS VARIÁVEIS DO SELETOR DE DISPOSITIVOS ---
        self.lista_dispositivos = []
        self.indice_dispositivo = 0
        self.carregou_dispositivos = False
        
        # Retângulos das setinhas < e >
        self.rect_seta_esq = pygame.Rect(0, 0, 30, 30)
        self.rect_seta_dir = pygame.Rect(0, 0, 30, 30)
        self.rects_cordas = []
        
        # Cores
        self.AZUL_BOTAO = (0, 120, 215)
        self.VERDE = (0, 255, 100)
        self.VERMELHO = (255, 50, 50)
        self.BRANCO = (255, 255, 255)
        self.CINZA = (150, 150, 150)
        self.FUNDO_ESCURO = (40, 40, 40)

    def extrair_pitch_exato(self, audio_array):
        if audio_array is None or len(audio_array) == 0: return 0.0
        f0 = librosa.yin(audio_array, fmin=50, fmax=500, sr=self.sr)
        f0_valido = f0[f0 > 0]
        return np.mean(f0_valido) if len(f0_valido) > 0 else 0.0

    def extrair_nota_dominante(self, audio_array):
        if audio_array is None or len(audio_array) == 0: return ""
        if audio_array.ndim > 1: audio_array = np.mean(audio_array, axis=1)
        chroma = librosa.feature.chroma_stft(y=audio_array, sr=self.sr)
        notas = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        return notas[np.argmax(np.mean(chroma, axis=1))]

    def processar_logica_continua(self, gravador):
        if not gravador.gravando:
            self.nota_detectada = "Microfone Desligado"
            self.freq_atual = 0.0
            return

        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.ultimo_tempo_analise > self.intervalo_analise:
            self.ultimo_tempo_analise = tempo_atual
            
            audio_cru = gravador.obter_array_para_ia()
            if audio_cru is not None:
                if self.corda_selecionada is not None:
                    self.freq_atual = self.extrair_pitch_exato(audio_cru)
                    self.nota_detectada = f"Frequência: {self.freq_atual:.2f} Hz"
                else:
                    nota = self.extrair_nota_dominante(audio_cru)
                    self.nota_detectada = f"Nota no Braço: {nota}"
                    self.freq_atual = 0.0
            else:
                self.nota_detectada = "Aguardando som..."
                self.freq_atual = 0.0

    def tratar_clique(self, pos_mouse, rect_botao, gravador):
        # 1. Botão Principal
        if rect_botao.collidepoint(pos_mouse):
            gravador.alternar_microfone()
            return True
            
        # 2. Seletor de Dispositivos (< ou >)
        if len(self.lista_dispositivos) > 0:
            if self.rect_seta_esq.collidepoint(pos_mouse):
                self.indice_dispositivo = (self.indice_dispositivo - 1) % len(self.lista_dispositivos)
                gravador.mudar_dispositivo(self.lista_dispositivos[self.indice_dispositivo]['id'])
                return True
                
            if self.rect_seta_dir.collidepoint(pos_mouse):
                self.indice_dispositivo = (self.indice_dispositivo + 1) % len(self.lista_dispositivos)
                gravador.mudar_dispositivo(self.lista_dispositivos[self.indice_dispositivo]['id'])
                return True

        # 3. Afinador (Cordas)
        for i, rect in enumerate(self.rects_cordas):
            if rect.collidepoint(pos_mouse):
                self.corda_selecionada = None if self.corda_selecionada == i else i
                return True
        return False

    def desenhar_aba_ia(self, tela, offset_x, y_caixa, rect_botao, gravador, fonte_ui, fonte_titulo):
        # --- INICIALIZAÇÃO DOS DRIVERS NA PRIMEIRA VEZ QUE ABRE A TELA ---
        if not self.carregou_dispositivos:
            self.lista_dispositivos = gravador.obter_lista_entradas()
            for i, disp in enumerate(self.lista_dispositivos):
                if disp['id'] == gravador.device_id:
                    self.indice_dispositivo = i
                    break
            self.carregou_dispositivos = True

        # --- SETOR 1: BOTÃO LIGAR MIC E DETECÇÃO ---
        txt = fonte_titulo.render("Detecção em Tempo Real", True, self.BRANCO)
        tela.blit(txt, (offset_x + 20, y_caixa + 20))

        cor_btn = self.VERMELHO if gravador.gravando else self.AZUL_BOTAO
        pygame.draw.rect(tela, cor_btn, rect_botao, border_radius=8)
        lbl = fonte_ui.render("MIC ABERTO" if gravador.gravando else "LIGAR MIC", True, self.BRANCO)
        tela.blit(lbl, (rect_botao.centerx - lbl.get_width()//2, rect_botao.centery - lbl.get_height()//2))

        cor_res = self.VERDE if gravador.gravando and "Aguardando" not in self.nota_detectada else self.CINZA
        txt_res = fonte_titulo.render(self.nota_detectada, True, cor_res)
        tela.blit(txt_res, (rect_botao.right + 20, rect_botao.y + 8))

        # --- SETOR 1.5: SELETOR DE PLACA DE SOM (A MÁGICA ACONTECE AQUI) ---
        y_seletor = rect_botao.bottom + 15
        tela.blit(fonte_ui.render("Microfone:", True, self.BRANCO), (offset_x + 20, y_seletor + 5))
        
        x_botoes = offset_x + 110
        self.rect_seta_esq.topleft = (x_botoes, y_seletor)
        
        largura_caixa = 320
        pygame.draw.rect(tela, self.FUNDO_ESCURO, (self.rect_seta_esq.right + 5, y_seletor, largura_caixa, 30), border_radius=5)
        
        # Pega o nome do dispositivo e corta se for muito grande
        if len(self.lista_dispositivos) > 0:
            nome_disp = self.lista_dispositivos[self.indice_dispositivo]['nome']
            if len(nome_disp) > 35: nome_disp = nome_disp[:32] + "..."
        else:
            nome_disp = "Nenhum detectado"
            
        txt_disp = fonte_ui.render(nome_disp, True, self.BRANCO)
        tela.blit(txt_disp, (self.rect_seta_esq.right + 15, y_seletor + 5))
        
        self.rect_seta_dir.topleft = (self.rect_seta_esq.right + 5 + largura_caixa + 5, y_seletor)

        # Desenha as setinhas
        pygame.draw.rect(tela, self.CINZA, self.rect_seta_esq, border_radius=5)
        pygame.draw.rect(tela, self.CINZA, self.rect_seta_dir, border_radius=5)
        tela.blit(fonte_ui.render("<", True, self.BRANCO), (self.rect_seta_esq.x + 8, self.rect_seta_esq.y + 4))
        tela.blit(fonte_ui.render(">", True, self.BRANCO), (self.rect_seta_dir.x + 8, self.rect_seta_dir.y + 4))

        # --- SETOR 2: SELEÇÃO DE CORDAS PARA AFINAÇÃO ---
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

        # --- SETOR 3: AGULHA DO AFINADOR ---
        if self.corda_selecionada is not None and gravador.gravando:
            nome_nota = self.ordem_cordas[self.corda_selecionada]
            freq_alvo = self.freqs_referencia[nome_nota]
            
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
            
            tela.blit(fonte_ui.render(f"Alvo: {nome_nota} ({freq_alvo}Hz)", True, self.BRANCO), (x_agulha_base + largura_barra + 30, y_agulha - 10))