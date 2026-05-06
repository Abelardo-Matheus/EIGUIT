;# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 [SEU NOME]
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================

class MaestroRitmo:
    def __init__(self):
        self.ativo = False
        self.estado = "PARADO" # Agora só tem PARADO e ATIVO
        
        self.bpm = 60
        self.ms_por_batida = 1000.0
        self.ms_por_nota = 1000.0
        
        self.fila_notas = [] 
        self.proxima_batida_esperada = 0
        
        self.janela_perfeito = 60 
        self.janela_bom = 120      
        
        self.acertos_perfeitos = 0
        self.acertos_bons = 0
        self.erros = 0
        self.texto_feedback = ""
        self.cor_feedback = (255, 255, 255)
        self.tempo_ultimo_feedback = 0

    def iniciar_treino(self, bpm, subdivisao, tempo_atual, metronomo):
        self.bpm = bpm
        self.ms_por_batida = 60000.0 / bpm
        self.ms_por_nota = self.ms_por_batida / subdivisao
        self.metronomo = metronomo
        
        # 1. Dá o play no metrônomo imediatamente!
        self.metronomo.bpm = bpm
        self.metronomo.tocando = True 
        self.metronomo.ultimo_tick = tempo_atual
        self.metronomo.tempo_atual = 0
        self.metronomo.tocar_som()
        
        self.estado = "ATIVO"
        self.ativo = True
        
        # 2. A primeira nota nasce no topo e vai chegar no alvo daqui a 4 batidas exatas
        tempo_inicio_real = tempo_atual + (4 * self.ms_por_batida)
        self.fila_notas = [{'tempo': tempo_inicio_real + (i * self.ms_por_nota)} for i in range(30)]
        self.proxima_batida_esperada = self.fila_notas[0]['tempo']
        
        self.acertos_perfeitos = 0
        self.acertos_bons = 0
        self.erros = 0
        self.texto_feedback = ""

    def atualizar(self, tempo_atual):
        if not self.ativo or self.estado != "ATIVO": return

        # Checa se a nota atual passou reto e caiu no chão
        if len(self.fila_notas) > 0:
            nota_atual = self.fila_notas[0]
            
            if tempo_atual > (nota_atual['tempo'] + self.janela_bom):
                self.texto_feedback = "MISS!"
                self.cor_feedback = (150, 150, 150)
                self.tempo_ultimo_feedback = tempo_atual
                self.erros += 1
                self.avancar_batida()

        # Limpa a mensagem depois de 400ms
        if tempo_atual - self.tempo_ultimo_feedback > 400:
            self.texto_feedback = ""

    def registrar_palhetada(self, tempo_atual):
        if self.estado != "ATIVO" or len(self.fila_notas) == 0: return
        
        nota_atual = self.fila_notas[0]
        erro = tempo_atual - nota_atual['tempo']
        erro_abs = abs(erro)

        if erro_abs <= self.janela_perfeito:
            self.texto_feedback = "PERFEITO!"
            self.cor_feedback = (0, 255, 100)
            self.acertos_perfeitos += 1
            self.avancar_batida()
        elif erro_abs <= self.janela_bom:
            self.texto_feedback = "BOM"
            self.cor_feedback = (255, 255, 0)
            self.acertos_bons += 1
            self.avancar_batida()

    def avancar_batida(self):
        if len(self.fila_notas) > 0:
            self.fila_notas.pop(0)
            
        if len(self.fila_notas) > 0:
            ultimo_tempo = self.fila_notas[-1]['tempo']
            self.fila_notas.append({'tempo': ultimo_tempo + self.ms_por_nota})
            self.proxima_batida_esperada = self.fila_notas[0]['tempo']

    def parar_treino(self):
        self.ativo = False
        self.estado = "PARADO"
        if hasattr(self, 'metronomo'):
            self.metronomo.tocando = False