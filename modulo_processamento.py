import librosa
import numpy as np
import pygame

class ProcessadorAudio:
    def __init__(self, taxa_amostragem=48000):
        # --- CONFIGURAÇÕES DE ÁUDIO ---
        self.sr = taxa_amostragem
        self.n_fft = 2048
        self.hop_length = 512

        # --- ESTADOS DA INTERFACE (UI) ---
        self.nota_detectada = "Aguardando entrada..."
        self.audio_ja_processado = True
        
        # --- CORES DA INTERFACE ---
        self.BRANCO = (255, 255, 255)
        self.VERDE = (0, 255, 100)
        self.VERMELHO = (255, 50, 50)
        self.AZUL_BOTAO = (0, 120, 215)
        self.CINZA = (150, 150, 150)

    # ==========================================
    # LÓGICA MATEMÁTICA E DE IA
    # ==========================================
    def extrair_nota_dominante(self, audio_array):
        """Usa matemática pura para achar a nota tocada"""
        if audio_array is None or len(audio_array) == 0: return None
        if audio_array.ndim > 1: audio_array = np.mean(audio_array, axis=1)

        chroma = librosa.feature.chroma_stft(y=audio_array, sr=self.sr, n_fft=self.n_fft, hop_length=self.hop_length)
        chroma_mean = np.mean(chroma, axis=1)
        
        notas = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        indice_nota = np.argmax(chroma_mean)
        return notas[indice_nota]

    # ==========================================
    # INTEGRAÇÃO COM O LOOP DO PYGAME
    # ==========================================
    def processar_logica_continua(self, gravador):
        """Verifica frame a frame se a gravação terminou para extrair a nota"""
        if not gravador.gravando and not self.audio_ja_processado:
            audio_cru = gravador.obter_array_para_ia()
            
            if audio_cru is not None:
                nota = self.extrair_nota_dominante(audio_cru)
                self.nota_detectada = f"Nota Detectada: {nota}"
                
            self.audio_ja_processado = True # Evita processar o mesmo áudio duas vezes

    def tratar_clique(self, pos_mouse, rect_botao, gravador):
        """Se o usuário clicar no botão, manda o gravador começar"""
        if rect_botao.collidepoint(pos_mouse):
            if not gravador.gravando:
                gravador.iniciar_gravacao(duracao_segundos=3)
                self.audio_ja_processado = False
                self.nota_detectada = "Ouvindo..."
            return True
        return False

    def desenhar_aba_ia(self, tela, offset_x, y_caixa, rect_botao, gravador, fonte_ui, fonte_titulo, fonte_pequena):
        """Desenha tudo o que pertence à IA dentro da caixa inferior"""
        
        # 1. Título
        txt_sub = fonte_titulo.render("Análise de Frequência em Tempo Real", True, self.BRANCO)
        tela.blit(txt_sub, (offset_x + 20, y_caixa + 60))

        # 2. Botão de Gravar (Muda de cor se estiver gravando)
        cor_btn = self.VERMELHO if gravador.gravando else self.AZUL_BOTAO
        pygame.draw.rect(tela, cor_btn, rect_botao, border_radius=8)
        
        txt_btn = "GRAVANDO..." if gravador.gravando else "OUVIR NOTA"
        lbl_btn = fonte_ui.render(txt_btn, True, self.BRANCO)
        tela.blit(lbl_btn, (rect_botao.centerx - lbl_btn.get_width()//2, rect_botao.centery - lbl_btn.get_height()//2))

        # 3. Resultado da Nota
        cor_res = self.VERMELHO if "Ouvindo" in self.nota_detectada else self.VERDE
        txt_res = fonte_titulo.render(self.nota_detectada, True, cor_res)
        tela.blit(txt_res, (offset_x + 220, y_caixa + 85))
        
        # 4. Instrução
        hint = fonte_pequena.render("Toque uma nota limpa por 3 segundos.", True, self.CINZA)
        tela.blit(hint, (offset_x + 50, y_caixa + 130))