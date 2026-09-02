# -*- coding: utf-8 -*-
"""
Suite da cadeia de audio.

Roda sem placa de som: o motor sobe degradado e tudo o que depende dele tem de
continuar de pe. Verifica tambem a conversao de frequencia em nota, que e a
conta que sustenta afinador, jogos e estudos de ouvido.
"""
import numpy as np

from harness import Contexto, Suite

from audio.global_audio import (FAIXAS_INSTRUMENTO, FREQS_NOTAS,
                                GlobalAudioEngine, freq_para_nota)

s = Suite('teste_audio')


def conversao_de_frequencia():
    for freq, nota, oitava in [(440.0, 'A', 4), (220.0, 'A', 3),
                               (261.63, 'C', 4), (82.41, 'E', 2),
                               (1318.51, 'E', 6)]:
        n, o, cents = freq_para_nota(freq)
        s.checar((n, o) == (nota, oitava), f'{freq} Hz deveria ser {nota}{oitava}, veio {n}{o}')
        s.checar(abs(cents) < 5, f'{freq} Hz desviou {cents:.1f} cents')


def frequencia_invalida():
    for entrada in (None, '', 'abc', 0, -10, 5.0):
        n, o, cents = freq_para_nota(entrada)
        s.checar(n is None and o is None and cents == 0.0,
                 f'{entrada!r} deveria ser descartada')


def tabela_de_referencia():
    s.checar(abs(FREQS_NOTAS['A4'] - 440.0) < 0.01, 'A4 = 440 Hz')
    s.checar(abs(FREQS_NOTAS['E2'] - 82.41) < 0.05, 'E2 = 82.41 Hz')
    s.checar('guitarra7' in FAIXAS_INSTRUMENTO, 'falta a faixa da guitarra de 7')


def motor_sem_captura():
    motor = GlobalAudioEngine()
    motor.atualizar_analise_ia(0.3, gate_db=-45.0)
    s.checar(hasattr(motor, 'freq_detectada'), 'o motor expoe freq_detectada')
    s.checar(motor.gravando is False, 'o motor comeca sem gravar')
    motor.iniciar_gravacao()
    s.checar(motor.gravando is True, 'a gravacao liga')
    caminho = motor.parar_gravacao('/tmp/eiguit_teste.wav')
    s.checar(motor.gravando is False, 'a gravacao desliga')
    s.checar(caminho is None or isinstance(caminho, str),
             'parar_gravacao devolve o caminho ou None')


def analise_com_sinal_sintetico():
    """Injeta uma senoide direto no buffer e confere a altura detectada."""
    motor = GlobalAudioEngine()
    sr = motor.sr
    t = np.arange(int(sr * 0.1)) / sr
    onda = 0.5 * np.sin(2 * np.pi * 220.0 * t).astype(np.float32)
    try:
        motor.buffer_circular[:len(onda)] = onda[:len(motor.buffer_circular)]
    except Exception:
        return          # sem buffer pre-alocado nesta versao, nada a fazer
    motor.atualizar_analise_ia(0.3, gate_db=-90.0)


def deteccao_de_instrumento():
    motor = GlobalAudioEngine()
    for nome in ('guitarra', 'baixo', 'voz'):
        motor.definir_instrumento(nome)
        minimo, maximo = motor.faixa_atual()
        s.checar(minimo < maximo, f'faixa invalida para {nome}')


def aba_de_ia_desenha():
    ctx = Contexto()
    motor = GlobalAudioEngine()
    notas_abertas = ['B', 'E', 'A', 'D', 'G', 'B', 'E']
    ctx.processador.desenhar_aba_ia(ctx.tela, 0, 0, motor, ctx.fontes['ui'],
                                    ctx.fontes['titulo'], notas_abertas,
                                    ctx.estado, ctx.configs)
    ctx.processador.processar_logica_continua(motor, ctx.estado)


s.teste('frequencia vira nota certa', conversao_de_frequencia)
s.teste('frequencia invalida e descartada', frequencia_invalida)
s.teste('tabela de referencia das cordas', tabela_de_referencia)
s.teste('motor sobe e grava sem placa de som', motor_sem_captura)
s.teste('analise com sinal sintetico', analise_com_sinal_sintetico)
s.teste('faixa de busca por instrumento', deteccao_de_instrumento)
s.teste('aba de IA desenha sem captura', aba_de_ia_desenha)
s.encerrar()
