# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================

# modulos_escala_menor.py

# --- AS MATRIZES DOS 5 SHAPES DA ESCALA MENOR NATURAL (EÓLIA) ---
# Padrões estendidos para 7 cordas. 
# 0 = Vazio | 1 = Nota da Escala | 2 = Tônica (Fundamental)

# Shape 1 (Equivalente ao formato de Em)
SHAPE_1 = [
    [1, 1, 0, 1, 0], # 7ª Corda
    [2, 0, 1, 1, 0], # 6ª Corda
    [1, 0, 1, 1, 0], # 5ª Corda
    [1, 0, 2, 0, 1], # 4ª Corda
    [1, 0, 1, 0, 1], # 3ª Corda
    [1, 1, 0, 1, 0], # 2ª Corda
    [2, 0, 1, 1, 0]  # 1ª Corda
]

# Shape 2 (Equivalente ao formato de Dm)
SHAPE_2 = [
    [0, 1, 0, 2, 0], # 7ª Corda
    [0, 1, 1, 0, 1], # 6ª Corda
    [0, 1, 1, 0, 1], # 5ª Corda
    [2, 0, 1, 0, 1], # 4ª Corda
    [1, 0, 1, 0, 1], # 3ª Corda
    [0, 2, 0, 1, 1], # 2ª Corda
    [0, 1, 1, 0, 1]  # 1ª Corda
]

# Shape 3 (Equivalente ao formato de Cm)
SHAPE_3 = [
    [1, 0, 1, 0, 2], # 7ª Corda
    [1, 1, 0, 1, 0], # 6ª Corda
    [1, 1, 0, 2, 0], # 5ª Corda
    [1, 0, 1, 1, 0], # 4ª Corda
    [1, 0, 1, 1, 0], # 3ª Corda
    [1, 0, 2, 0, 1], # 2ª Corda
    [1, 1, 0, 1, 0]  # 1ª Corda
]

# Shape 4 (Equivalente ao formato de Am)
SHAPE_4 = [
    [1, 0, 1, 1, 0], # 7ª Corda
    [1, 0, 1, 0, 1], # 6ª Corda
    [2, 0, 1, 0, 1], # 5ª Corda
    [1, 1, 0, 1, 0], # 4ª Corda
    [1, 1, 0, 2, 0], # 3ª Corda
    [1, 0, 1, 1, 0], # 2ª Corda
    [1, 0, 1, 0, 1]  # 1ª Corda
]

# Shape 5 (Equivalente ao formato de Gm)
SHAPE_5 = [
    [1, 0, 1, 0, 1], # 7ª Corda
    [1, 0, 1, 2, 0], # 6ª Corda
    [1, 0, 1, 1, 0], # 5ª Corda
    [0, 1, 0, 1, 0], # 4ª Corda
    [0, 2, 0, 1, 0], # 3ª Corda
    [1, 0, 1, 0, 1], # 2ª Corda
    [1, 0, 1, 2, 0]  # 1ª Corda
]

# O Shape Mestre de 12 casas (Uma oitava completa a partir da corda solta)
SHAPE_COMPLETO = [
    [1, 1, 0, 1, 0, 2, 0, 1, 1, 0, 1, 0], # 7ª Corda
    [2, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0], # 6ª Corda
    [1, 0, 1, 1, 0, 1, 0, 2, 0, 1, 1, 0], # 5ª Corda
    [1, 0, 2, 0, 1, 1, 0, 1, 0, 1, 1, 0], # 4ª Corda
    [1, 0, 1, 0, 1, 1, 0, 1, 0, 2, 0, 1], # 3ª Corda
    [1, 1, 0, 1, 0, 2, 0, 1, 1, 0, 1, 0], # 2ª Corda
    [2, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0]  # 1ª Corda
]
TODOS_OS_SHAPES = [SHAPE_1, SHAPE_2, SHAPE_3, SHAPE_4, SHAPE_5, SHAPE_COMPLETO]