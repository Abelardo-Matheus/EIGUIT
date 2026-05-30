class MaestroRitmo:
    """
        Como funciona: Define a estrutura e estado do componente 'MaestroRitmo'.
        Para que serve: Atua como o modelo principal para instâncias de 'MaestroRitmo'.
        Onde é usada: Chamado a partir do módulo ou classe base de 'gerenciador_ritmo'.
    """

    def __init__(self):
        """
            Como funciona: Inicializa os atributos e o estado inicial da instância.
            Para que serve: Prepara o objeto para ser utilizado no ciclo de vida da aplicação.
            Onde é usada: Chamado a partir do módulo ou classe base de 'gerenciador_ritmo'.
        """
        self.ativo = False
        self.estado = 'PARADO'
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
        self.texto_feedback = ''
        self.cor_feedback = (255, 255, 255)
        self.tempo_ultimo_feedback = 0

    def iniciar_treino(self, bpm, subdivisao, tempo_atual, metronomo):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'iniciar treino'.
            Para que serve: Realiza as tarefas fundamentais de 'iniciar treino' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'iniciar treino'.
        """
        self.bpm = bpm
        self.ms_por_batida = 60000.0 / bpm
        self.ms_por_nota = self.ms_por_batida / subdivisao
        self.metronomo = metronomo
        self.metronomo.bpm = bpm
        self.metronomo.tocando = True
        self.metronomo.ultimo_tick = tempo_atual
        self.metronomo.tempo_atual = 0
        if hasattr(self.metronomo, 'som_acento') and self.metronomo.som_acento:
            self.metronomo.som_acento.play()
        elif hasattr(self.metronomo, 'som_tick') and self.metronomo.som_tick:
            self.metronomo.som_tick.play()
        self.estado = 'ATIVO'
        self.ativo = True
        tempo_inicio_real = tempo_atual + 4 * self.ms_por_batida
        self.fila_notas = [{'tempo': tempo_inicio_real + i * self.ms_por_nota} for i in range(30)]
        self.proxima_batida_esperada = self.fila_notas[0]['tempo']
        self.acertos_perfeitos = 0
        self.acertos_bons = 0
        self.erros = 0
        self.texto_feedback = ''

    def atualizar(self, tempo_atual):
        """
            Como funciona: Recalcula dimensões, estados e processa alterações temporais.
            Para que serve: Garante que os dados e a interface reflitam as últimas mudanças.
            Onde é usada: Chamado a partir do módulo ou classe base de 'gerenciador_ritmo'.
        """
        if not self.ativo or self.estado != 'ATIVO':
            return
        if len(self.fila_notas) > 0:
            nota_atual = self.fila_notas[0]
            if tempo_atual > nota_atual['tempo'] + self.janela_bom:
                self.texto_feedback = 'MISS!'
                self.cor_feedback = (150, 150, 150)
                self.tempo_ultimo_feedback = tempo_atual
                self.erros += 1
                self.avancar_batida()
        if tempo_atual - self.tempo_ultimo_feedback > 400:
            self.texto_feedback = ''

    def registrar_palhetada(self, tempo_atual):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'registrar palhetada'.
            Para que serve: Realiza as tarefas fundamentais de 'registrar palhetada' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'registrar palhetada'.
        """
        if self.estado != 'ATIVO' or len(self.fila_notas) == 0:
            return
        nota_atual = self.fila_notas[0]
        erro = tempo_atual - nota_atual['tempo']
        erro_abs = abs(erro)
        if erro_abs <= self.janela_perfeito:
            self.texto_feedback = 'PERFEITO!'
            self.cor_feedback = (0, 255, 100)
            self.acertos_perfeitos += 1
            self.avancar_batida()
        elif erro_abs <= self.janela_bom:
            self.texto_feedback = 'BOM'
            self.cor_feedback = (255, 255, 0)
            self.acertos_bons += 1
            self.avancar_batida()

    def avancar_batida(self):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'avancar batida'.
            Para que serve: Realiza as tarefas fundamentais de 'avancar batida' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'avancar batida'.
        """
        if len(self.fila_notas) > 0:
            self.fila_notas.pop(0)
        if len(self.fila_notas) > 0:
            ultimo_tempo = self.fila_notas[-1]['tempo']
            self.fila_notas.append({'tempo': ultimo_tempo + self.ms_por_nota})
            self.proxima_batida_esperada = self.fila_notas[0]['tempo']

    def parar_treino(self):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'parar treino'.
            Para que serve: Realiza as tarefas fundamentais de 'parar treino' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'parar treino'.
        """
        self.ativo = False
        self.estado = 'PARADO'
        if hasattr(self, 'metronomo'):
            self.metronomo.tocando = False