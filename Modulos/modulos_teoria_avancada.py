# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================
# modulos_teoria_avancada.py

# --- PENTATÔNICA BLUES (Penta Menor + 4# / 5b) ---
SHAPE_1_BLUES = [
    [1, 0, 0, 1, 0], # 7ª Corda
    [1, 0, 0, 1, 0], # 6ª Corda
    [1, 0, 1, 1, 0], # 5ª Corda (Blue note na 3ª casa do desenho)
    [1, 0, 1, 0, 0], # 4ª Corda
    [1, 1, 1, 0, 0], # 3ª Corda (Blue note na 2ª casa do desenho)
    [1, 0, 0, 1, 0], # 2ª Corda
    [1, 0, 0, 1, 0]  # 1ª Corda
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

TODOS_OS_SHAPES_BLUES = [SHAPE_1_BLUES, SHAPE_COMPLETO_BLUES]

# --- MODOS GREGOS ---
# Modo Dórico (Escala Maior começando da 2ª nota)
DORICO = [
    [0, 1, 1, 0, 1], # 7ª
    [0, 1, 0, 1, 1], # 6ª
    [1, 0, 1, 1, 0], # 5ª
    [1, 0, 1, 0, 1], # 4ª
    [1, 0, 1, 0, 1], # 3ª
    [0, 1, 1, 0, 1], # 2ª
    [0, 1, 0, 1, 1]  # 1ª
]

TODOS_OS_MODOS = [DORICO]