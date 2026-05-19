# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================
# modulos_teoria_avancada.py

# --- PENTATÔNICA BLUES (Penta Menor + 4# / 5b) ---
SHAPE_1_BLUES = [
    [1, 0, 0, 1, 0], # 7ª Corda
    [2, 0, 0, 1, 1], # 6ª Corda (A, C, Eb)
    [1, 0, 1, 0, 0], # 5ª Corda
    [1, 1, 2, 0, 0], # 4ª Corda
    [1, 0, 1, 0, 0], # 3ª Corda
    [1, 0, 0, 1, 1], # 2ª Corda
    [2, 0, 0, 1, 1]  # 1ª Corda
]

SHAPE_2_BLUES = [
    [0, 1, 0, 2, 0], 
    [0, 1, 1, 1, 0], 
    [1, 0, 0, 1, 0], 
    [2, 0, 1, 0, 0], 
    [1, 1, 1, 0, 0], 
    [0, 2, 0, 1, 1], 
    [0, 1, 1, 1, 0]
]

# Shape Completo Blues (12 casas)
SHAPE_COMPLETO_BLUES = [
    [1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0], 
    [1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0], 
    [1, 0, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0], 
    [1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 0, 0], 
    [1, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1], 
    [1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0], 
    [1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0]  
]

TODOS_OS_SHAPES_BLUES = [SHAPE_1_BLUES, SHAPE_2_BLUES, SHAPE_COMPLETO_BLUES]