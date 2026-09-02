# -*- coding: utf-8 -*-
"""
Deteccao de ataque (palhetada, tecla, batida) a partir do buffer de audio.

Em vez de comparar o volume com um limiar fixo, acompanha dois envelopes da
energia: um rapido, que sobe junto com a nota, e um lento, que representa o
fundo. Um ataque e quando o rapido dispara acima do lento. Isso funciona tanto
com o instrumento baixo quanto alto, e nao dispara com ruido constante.
"""
import time

import numpy as np


class DetectorPalhetadas:
    """
        Como funciona: Mantem envelopes rapido e lento da energia do sinal e
        marca um ataque na subida, respeitando um tempo refratario.
        Para que serve: Disparar eventos de jogo e de estudo ao tocar uma nota.
        Onde e usada: Jogos de ritmo e de percepcao, e o processador de audio.
    """

    def __init__(self, sensibilidade=1.8, refratario=0.09, piso_minimo=0.004):
        # Quanto o envelope rapido precisa superar o lento para contar ataque
        self.sensibilidade = sensibilidade
        # Tempo minimo entre dois ataques, em segundos
        self.refratario = refratario
        # Energia minima absoluta, para nao disparar no silencio
        self.piso_minimo = piso_minimo

        self.volume_atual = 0.0
        self.envelope_rapido = 0.0
        self.envelope_lento = 0.0
        self.ultimo_disparo = 0.0
        self.forca_ultimo_ataque = 0.0
        # Fica desarmado enquanto a nota soa; so rearma quando a energia cai.
        # Sem isso a mesma nota dispara varias vezes enquanto sustenta.
        self.armado = True

        # Compatibilidade com o codigo antigo
        self.limiar_volume = piso_minimo
        self.cooldown = refratario

    def reiniciar(self):
        """Zera os envelopes, para comecar uma rodada limpa."""
        self.envelope_rapido = 0.0
        self.envelope_lento = 0.0
        self.ultimo_disparo = 0.0
        self.forca_ultimo_ataque = 0.0
        self.armado = True

    def processar_buffer(self, buffer_audio, agora=None):
        """
            Como funciona: Calcula o RMS do bloco, atualiza os envelopes e
            devolve True quando reconhece um ataque novo.
            Para que serve: Saber o instante exato em que a pessoa tocou.
            Onde e usada: Chamada a cada quadro pelos jogos.
        """
        if buffer_audio is None or len(buffer_audio) == 0:
            return False

        sinal = np.asarray(buffer_audio, dtype=np.float32)
        pico = float(np.max(np.abs(sinal))) if sinal.size else 0.0
        if pico > 1.5:
            # Buffer veio em inteiros de 16 bits
            sinal = sinal / 32768.0

        # Remove nivel continuo antes de medir energia
        sinal = sinal - float(np.mean(sinal))
        rms = float(np.sqrt(np.mean(sinal ** 2)))
        self.volume_atual = rms

        self.envelope_rapido += (rms - self.envelope_rapido) * 0.55
        self.envelope_lento += (rms - self.envelope_lento) * 0.05

        agora = agora if agora is not None else time.time()
        limiar_disparo = self.envelope_lento * self.sensibilidade + self.piso_minimo
        # Histerese: rearma bem abaixo do limiar de disparo
        limiar_rearme = self.envelope_lento * 1.15 + self.piso_minimo * 0.4

        if not self.armado:
            if self.envelope_rapido < limiar_rearme:
                self.armado = True
            return False

        if (self.envelope_rapido > limiar_disparo
                and (agora - self.ultimo_disparo) > self.refratario):
            self.ultimo_disparo = agora
            self.armado = False
            self.forca_ultimo_ataque = min(1.0, self.envelope_rapido * 8.0)
            return True
        return False
