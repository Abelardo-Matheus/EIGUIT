import pygame

def desenhar_controles_playback(tela, estado, meu_metronomo, fonte_ui, configs):
    """
        Como funciona: Utiliza funções de renderização do Pygame para desenhar na tela.
        Para que serve: Apresenta o elemento visual 'controles playback' na interface gráfica.
        Onde é usada: Chamado a partir do módulo ou classe base de 'playback_controls'.
    """
    if hasattr(meu_metronomo, 'desenhar_mini_metronomo'):
        meu_metronomo.desenhar_mini_metronomo(tela, estado, fonte_ui, configs=configs)