# -*- coding: utf-8 -*-
"""
Rastreamento da sessao de estudo.

Acompanha quanto tempo o usuario esta praticando, quantas notas foram tocadas
e qual a proporcao delas que pertence ao contexto harmonico atual (escala ou
acorde selecionado). Alimenta o painel de sessao e a leitura de precisao do
afinador.
"""
import time


class SessaoEstudo:
    """
        Como funciona: Recebe cada nota detectada pelo microfone e classifica
        se ela pertence ao contexto harmonico ativo, mantendo contadores.
        Para que serve: Dar retorno objetivo de pratica ao usuario.
        Onde e usada: Instanciada em main.py e alimentada a cada quadro.
    """

    # Janela usada para a precisao "recente" (ultimas N notas)
    JANELA_RECENTE = 40

    def __init__(self):
        """
            Como funciona: Zera contadores e marca o inicio da sessao.
            Para que serve: Preparar o rastreamento.
            Onde e usada: Chamado por main.py na inicializacao.
        """
        self.inicio = time.time()
        self.notas_tocadas = 0
        self.notas_no_contexto = 0
        self.ultima_nota = '--'
        self.historico_recente = []
        self.pausada = False
        self._acumulado_pausa = 0.0
        self._instante_pausa = None

    # ------------------------------------------------------------- registro
    def registrar(self, nota, notas_validas):
        """
            Como funciona: Conta uma nota apenas na transicao (quando a nota
            detectada muda), evitando inflar o contador enquanto a mesma nota
            soa por varios quadros.
            Para que serve: Contabilizar notas tocadas e acertos.
            Onde e usada: Chamado a cada quadro por main.py.
        """
        if nota == self.ultima_nota:
            return
        self.ultima_nota = nota
        if nota == '--' or not nota:
            return

        self.notas_tocadas += 1
        acertou = bool(notas_validas) and nota in notas_validas
        if acertou:
            self.notas_no_contexto += 1

        self.historico_recente.append(acertou)
        if len(self.historico_recente) > self.JANELA_RECENTE:
            self.historico_recente.pop(0)

    # ------------------------------------------------------------- leituras
    @property
    def precisao(self):
        """Percentual de acerto considerando toda a sessao."""
        if not self.notas_tocadas:
            return 0
        return int(round(self.notas_no_contexto / self.notas_tocadas * 100))

    @property
    def precisao_recente(self):
        """Percentual de acerto nas ultimas notas (responde mais rapido)."""
        if not self.historico_recente:
            return 0
        return int(round(sum(self.historico_recente) / len(self.historico_recente) * 100))

    @property
    def duracao_segundos(self):
        """Tempo de sessao, descontando o periodo em pausa."""
        fim = self._instante_pausa if self.pausada else time.time()
        return max(0.0, fim - self.inicio - self._acumulado_pausa)

    @property
    def duracao_texto(self):
        """Duracao formatada como MM:SS (ou HH:MM:SS acima de uma hora)."""
        total = int(self.duracao_segundos)
        horas, resto = divmod(total, 3600)
        minutos, segundos = divmod(resto, 60)
        if horas:
            return f'{horas}:{minutos:02d}:{segundos:02d}'
        return f'{minutos:02d}:{segundos:02d}'

    # ------------------------------------------------------------- controle
    def alternar_pausa(self):
        """Pausa ou retoma a contagem de tempo da sessao."""
        if self.pausada:
            self._acumulado_pausa += time.time() - self._instante_pausa
            self._instante_pausa = None
            self.pausada = False
        else:
            self._instante_pausa = time.time()
            self.pausada = True
        return self.pausada

    def reiniciar(self):
        """Zera a sessao inteira."""
        self.__init__()
