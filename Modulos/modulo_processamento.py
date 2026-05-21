# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================

import numpy as np
import pygame
from Modulos.detector_palhetadas import DetectorPalhetadas
from Modulos.gerenciador_ritmo import MaestroRitmo
from Core.i18n import _t

class ProcessadorAudio:
    """
    Controlador de lógica de interface para o áudio.
    Agora consome dados do GlobalAudioEngine.
    """
    def __init__(self, taxa_amostragem=48000):
        self.sr = taxa_amostragem
        self.nomes_exibicao = []
        self.ordem_cordas = []
        self.freqs_referencia = []
        self.detector_ritmo = DetectorPalhetadas()
        self.maestro = MaestroRitmo()
        
        self.nota_detectada = "Ouvindo..."
        self.freq_atual = 0.0
        self.corda_selecionada = None 
        
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
        if self.nomes_exibicao == notas_abertas: return
        self.nomes_exibicao = notas_abertas
        self.ordem_cordas = []
        self.freqs_referencia = []
        
        notas_escala = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        oitava_atual = 1
        
        if len(notas_abertas) > 0:
            ultimo_idx = notas_escala.index(notas_abertas[0])
            for nota in notas_abertas:
                idx = notas_escala.index(nota)
                if idx < ultimo_idx: oitava_atual += 1
                ultimo_idx = idx
                nome_completo = f"{nota}{oitava_atual}"
                self.ordem_cordas.append(nome_completo)
                
                # Frequências aproximadas para referência visual
                from AudioEngine.global_audio import FREQS_NOTAS
                self.freqs_referencia.append(FREQS_NOTAS.get(nome_completo, 440.0))
        
        self.corda_selecionada = None 

    def processar_logica_continua(self, motor_audio, estado):
        # Apenas sincroniza para exibição na UI da aba IA
        self.freq_atual = motor_audio.freq_detectada
        
        if self.corda_selecionada is not None:
            self.nota_detectada = f"{_t('Frequência')}: {self.freq_atual:.2f} Hz"
        else:
            if self.freq_atual > 0:
                self.nota_detectada = f"{_t('Nota no Braço')}: {estado.nota_atual_detectada}"
            else:
                self.nota_detectada = _t("Ouvindo...")

        # Maestro e Ritmo (Opcional se for usar)
        if motor_audio.volume_atual > 0.05:
            if self.detector_ritmo.processar_buffer(motor_audio.buffer):
                self.maestro.registrar_palhetada(pygame.time.get_ticks())
        self.maestro.atualizar(pygame.time.get_ticks())

    def tratar_clique(self, pos_mouse, motor_audio):
        # Gerencia troca de dispositivos
        if len(self.lista_dispositivos) > 0:
            if self.rect_seta_esq.collidepoint(pos_mouse):
                self.indice_dispositivo = (self.indice_dispositivo - 1) % len(self.lista_dispositivos)
                motor_audio.mudar_dispositivo(self.lista_dispositivos[self.indice_dispositivo]['id'])
                return True
            if self.rect_seta_dir.collidepoint(pos_mouse):
                self.indice_dispositivo = (self.indice_dispositivo + 1) % len(self.lista_dispositivos)
                motor_audio.mudar_dispositivo(self.lista_dispositivos[self.indice_dispositivo]['id'])
                return True

        for i, rect in enumerate(self.rects_cordas):
            if rect.collidepoint(pos_mouse):
                self.corda_selecionada = None if self.corda_selecionada == i else i
                return True
        return False

    def desenhar_aba_ia(self, tela, offset_x, y_caixa, motor_audio, fonte_ui, fonte_titulo, notas_abertas, estado):
        self.atualizar_afinacao(notas_abertas)

        if not self.carregou_dispositivos:
            self.lista_dispositivos = motor_audio.obter_lista_entradas()
            for i, disp in enumerate(self.lista_dispositivos):
                if disp['id'] == motor_audio.device_id:
                    self.indice_dispositivo = i
                    break
            self.carregou_dispositivos = True

        # Título da Sessão
        txt = fonte_titulo.render(_t("Detecção Real-Time (IA Sempre ON)"), True, self.BRANCO)
        tela.blit(txt, (offset_x + 20, y_caixa + 20))

        # Status e Nota
        cor_res = self.VERDE if self.freq_atual > 0 else self.CINZA
        txt_res = fonte_titulo.render(self.nota_detectada, True, cor_res)
        tela.blit(txt_res, (offset_x + 20, y_caixa + 70))

        # --- SELETOR DE MICROFONE ---
        y_seletor = y_caixa + 120
        tela.blit(fonte_ui.render(_t("Entrada de Áudio:"), True, self.BRANCO), (offset_x + 20, y_seletor + 5))
        
        x_botoes = offset_x + 180
        self.rect_seta_esq.topleft = (x_botoes, y_seletor)
        largura_caixa = 250
        pygame.draw.rect(tela, self.FUNDO_ESCURO, (self.rect_seta_esq.right + 5, y_seletor, largura_caixa, 30), border_radius=5)
        
        if len(self.lista_dispositivos) > 0:
            nome_disp = self.lista_dispositivos[self.indice_dispositivo]['nome']
            if len(nome_disp) > 25: nome_disp = nome_disp[:22] + "..."
        else: nome_disp = _t("Nenhum detectado")
            
        txt_disp = fonte_ui.render(nome_disp, True, self.BRANCO)
        tela.blit(txt_disp, (self.rect_seta_esq.right + 15, y_seletor + 5))
        
        self.rect_seta_dir.topleft = (self.rect_seta_esq.right + 5 + largura_caixa + 5, y_seletor)
        pygame.draw.rect(tela, self.CINZA, self.rect_seta_esq, border_radius=5)
        pygame.draw.rect(tela, self.CINZA, self.rect_seta_dir, border_radius=5)
        tela.blit(fonte_ui.render("<", True, self.BRANCO), (self.rect_seta_esq.x + 8, self.rect_seta_esq.y + 4))
        tela.blit(fonte_ui.render(">", True, self.BRANCO), (self.rect_seta_dir.x + 8, self.rect_seta_dir.y + 4))

        # --- BOLINHAS DO AFINADOR ---
        y_afinador_base = y_seletor + 50
        tela.blit(fonte_ui.render(_t("Afinador (Escolha uma corda para foco):"), True, self.BRANCO), (offset_x + 20, y_afinador_base))
        
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

        # --- AGULHA DO AFINADOR ---
        if self.corda_selecionada is not None:
            nome_nota = self.ordem_cordas[self.corda_selecionada]
            freq_alvo = self.freqs_referencia[self.corda_selecionada]
            x_agulha_base = offset_x + 20
            y_agulha = y_cordas + 65
            largura_barra = 350
            
            pygame.draw.line(tela, (100, 100, 100), (x_agulha_base, y_agulha), (x_agulha_base + largura_barra, y_agulha), 4)
            pygame.draw.circle(tela, self.VERDE, (x_agulha_base + largura_barra//2, y_agulha), 6) 

            if self.freq_atual > 0:
                cents = 1200 * np.log2(self.freq_atual / freq_alvo)
                desvio_x = (cents / 50) * (largura_barra // 2)
                desvio_x = max(-largura_barra//2, min(largura_barra//2, desvio_x)) 
                cor_agulha = self.VERDE if abs(cents) < 5 else self.VERMELHO
                pos_agulha = x_agulha_base + largura_barra//2 + desvio_x
                pygame.draw.line(tela, cor_agulha, (pos_agulha, y_agulha - 30), (pos_agulha, y_agulha + 30), 4)
                txt_status = _t("AFINADO!") if abs(cents) < 5 else (_t("APERTAR") if cents < 0 else _t("FROUXAR"))
                lbl_st = fonte_ui.render(f"{txt_status} ({cents:.1f} cents)", True, cor_agulha)
                tela.blit(lbl_st, (x_agulha_base + largura_barra//2 - lbl_st.get_width()//2, y_agulha - 45))
            
            tela.blit(fonte_ui.render(f"{_t('Alvo')}: {nome_nota} ({freq_alvo:.2f}Hz)", True, self.BRANCO), (x_agulha_base + largura_barra + 30, y_agulha - 10))
