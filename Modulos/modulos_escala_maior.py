# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 [SEU NOME]
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================

# modulos_escala_maior.py

# --- AS MATRIZES DOS 5 SHAPES DA ESCALA MAIOR ---
# Padrões estendidos para 7 cordas. 1 = Nota, 0 = Vazio.

SHAPE_1 = [
    [1, 0, 1, 1, 0], # 7ª Corda
    [1, 0, 1, 0, 1], # 6ª Corda
    [1, 0, 1, 0, 1], # 5ª Corda
    [0, 1, 1, 0, 1], # 4ª Corda
    [0, 1, 1, 0, 1], # 3ª Corda
    [1, 0, 1, 0, 1], # 2ª Corda
    [1, 0, 1, 0, 1], # 1ª Corda
]

SHAPE_2 = [
    [1, 0, 1, 0, 1], 
    [1, 0, 1, 0, 1], 
    [0, 1, 1, 0, 1], 
    [0, 1, 1, 0, 1], 
    [1, 0, 1, 0, 1], 
    [1, 0, 1, 1, 0], 
    [1, 0, 1, 0, 1], 
]

SHAPE_3 = [
    [1, 0, 1, 0, 1], 
    [0, 1, 1, 0, 1], 
    [0, 1, 1, 0, 1], 
    [1, 0, 1, 0, 1], 
    [1, 0, 1, 1, 0], 
    [1, 0, 1, 0, 1], 
    [0, 1, 1, 0, 1], 
]

SHAPE_4 = [
    [0, 1, 1, 0, 1], 
    [0, 1, 1, 0, 1], 
    [1, 0, 1, 0, 1], 
    [1, 0, 1, 1, 0], 
    [1, 0, 1, 0, 1], 
    [0, 1, 1, 0, 1], 
    [0, 1, 1, 0, 1], 
]

SHAPE_5 = [
    [0, 1, 1, 0, 1], 
    [1, 0, 1, 0, 1], 
    [1, 0, 1, 1, 0], 
    [1, 0, 1, 0, 1], 
    [0, 1, 1, 0, 1], 
    [0, 1, 1, 0, 1], 
    [1, 0, 1, 0, 1], 
]

# O Shape Mestre de 12 casas (Uma oitava completa)
SHAPE_COMPLETO = [
    [1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1], # 7ª Corda
    [1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1], # 6ª Corda
    [0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1], # 5ª Corda
    [0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1], # 4ª Corda
    [0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1], # 3ª Corda
    [1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1], # 2ª Corda
    [1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1]  # 1ª Corda
]

# Substitua a lista antiga por esta que inclui o completo no final:
TODOS_OS_SHAPES = [SHAPE_1, SHAPE_2, SHAPE_3, SHAPE_4, SHAPE_5, SHAPE_COMPLETO]