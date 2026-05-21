# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Componente: PlaybackControls
# =============================================================================

import pygame

def desenhar_controles_playback(tela, estado, meu_metronomo, fonte_ui):
    """
    Renderiza a área de controles de playback (Metrônomo, Play, BPM).
    Encapsula a chamada do metronomo para manter o padrão de componentes.
    """
    if hasattr(meu_metronomo, 'desenhar_mini_metronomo'):
        meu_metronomo.desenhar_mini_metronomo(tela, estado, fonte_ui)
