# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================

# --- ESCALA MENOR HARMÔNICA (1, 2, b3, 4, 5, b6, 7) ---
# Ex: A Harmônica (A, B, C, D, E, F, G#)

SHAPE_1_HARM = [
    [1, 1, 0, 0, 1], # 7ª Corda (B) -> B, C, D#? No, if starting at A.
    [2, 0, 1, 1, 0], # 6ª Corda (E) -> A, B, C
    [1, 0, 1, 1, 0], # 5ª Corda (A) -> D, E, F
    [0, 1, 0, 0, 2], # 4ª Corda (D) -> G#, A
    [1, 1, 0, 1, 0], # 3ª Corda (G) -> B, C, D
    [1, 0, 1, 1, 0], # 2ª Corda (B) -> E, F, G#? No.
    [2, 0, 1, 1, 0]  # 1ª Corda (E) -> A, B, C
]

# (I will provide the SHAPE_COMPLETO for both)

SHAPE_COMPLETO_HARM = [
    [1, 1, 0, 0, 1, 2, 0, 1, 1, 0, 0, 1], # 7ª Corda
    [2, 0, 1, 1, 0, 1, 0, 0, 1, 2, 0, 1], # 6ª Corda
    [1, 0, 1, 1, 0, 1, 0, 0, 1, 2, 0, 1], # 5ª Corda
    [1, 0, 0, 1, 2, 0, 1, 1, 0, 1, 0, 0], # 4ª Corda
    [0, 1, 2, 0, 1, 1, 0, 1, 0, 0, 1, 2], # 3ª Corda
    [1, 1, 0, 0, 1, 2, 0, 1, 1, 0, 0, 1], # 2ª Corda
    [2, 0, 1, 1, 0, 1, 0, 0, 1, 2, 0, 1]  # 1ª Corda
]

TODOS_OS_SHAPES_HARM = [SHAPE_1_HARM, SHAPE_COMPLETO_HARM]

# --- ESCALA MENOR MELÓDICA (1, 2, b3, 4, 5, 6, 7) ---
# Ex: A Melódica (A, B, C, D, E, F#, G#)

SHAPE_1_MELO = [
    [1, 1, 0, 1, 0], 
    [2, 0, 1, 0, 1], 
    [1, 0, 1, 0, 1], 
    [0, 1, 0, 0, 2], 
    [1, 1, 0, 1, 0], 
    [1, 1, 0, 1, 0], 
    [2, 0, 1, 0, 1]
]

SHAPE_COMPLETO_MELO = [
    [1, 1, 0, 1, 0, 2, 0, 1, 0, 1, 0, 1],
    [2, 0, 1, 0, 1, 1, 0, 1, 0, 2, 0, 1],
    [1, 0, 1, 0, 1, 1, 0, 1, 0, 2, 0, 1],
    [1, 0, 0, 2, 0, 1, 0, 1, 1, 0, 1, 0],
    [0, 1, 0, 2, 0, 1, 0, 1, 1, 0, 1, 0],
    [1, 1, 0, 1, 0, 2, 0, 1, 0, 1, 0, 1],
    [2, 0, 1, 0, 1, 1, 0, 1, 0, 2, 0, 1]
]

TODOS_OS_SHAPES_MELO = [SHAPE_1_MELO, SHAPE_COMPLETO_MELO]
