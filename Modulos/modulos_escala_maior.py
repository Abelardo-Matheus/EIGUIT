# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================

# modulos_escala_maior.py

# --- AS MATRIZES DOS 5 SHAPES DA ESCALA MAIOR (SISTEMA CAGED) ---
# Padrões estendidos para 7 cordas. 
# 0 = Vazio | 1 = Nota da Escala | 2 = Tônica (Fundamental)

# Equivalente ao "Modelo de E" da imagem (Inicia na casa 2)
SHAPE_1 = [
    [0, 1, 0, 1, 0], # 7ª Corda (B)
    [1, 2, 0, 1, 0], # 6ª Corda (E)
    [1, 1, 0, 1, 0], # 5ª Corda (A)
    [1, 0, 1, 2, 0], # 4ª Corda (D)
    [1, 0, 1, 1, 0], # 3ª Corda (G)
    [0, 1, 0, 1, 0], # 2ª Corda (B)
    [1, 2, 0, 1, 0], # 1ª Corda (E)
]

# Equivalente ao "Modelo de D" da imagem (Inicia na casa 4)
SHAPE_2 = [
    [0, 1, 0, 1, 2], # 7ª Corda (B)
    [0, 1, 0, 1, 1], # 6ª Corda (E)
    [0, 1, 0, 1, 0], # 5ª Corda (A)
    [1, 2, 0, 1, 0], # 4ª Corda (D)
    [1, 1, 0, 1, 0], # 3ª Corda (G)
    [0, 1, 0, 1, 2], # 2ª Corda (B)
    [0, 1, 0, 1, 1], # 1ª Corda (E)
]

# Equivalente ao "Modelo de C" da imagem (Inicia na casa 7)
SHAPE_3 = [
    [1, 2, 0, 1, 0], # 7ª Corda (B)
    [1, 1, 0, 1, 0], # 6ª Corda (E)
    [1, 0, 1, 2, 0], # 5ª Corda (A)
    [1, 0, 1, 1, 0], # 4ª Corda (D)
    [1, 0, 1, 0, 0], # 3ª Corda (G)
    [1, 2, 0, 1, 0], # 2ª Corda (B)
    [1, 1, 0, 1, 0], # 1ª Corda (E)
]

# Equivalente ao "Modelo de A" da imagem (Inicia na casa 9)
SHAPE_4 = [
    [0, 1, 0, 1, 1], # 7ª Corda (B)
    [0, 1, 0, 1, 0], # 6ª Corda (E)
    [1, 2, 0, 1, 0], # 5ª Corda (A)
    [1, 1, 0, 1, 0], # 4ª Corda (D)
    [1, 0, 1, 2, 0], # 3ª Corda (G)
    [0, 1, 0, 1, 1], # 2ª Corda (B)
    [0, 1, 0, 1, 0], # 1ª Corda (E)
]

# Equivalente ao "Modelo de G" da imagem (Inicia na casa 11)
SHAPE_5 = [
    [0, 1, 1, 0, 1], # 7ª Corda (B)
    [0, 1, 0, 1, 2], # 6ª Corda (E)
    [0, 1, 0, 1, 1], # 5ª Corda (A)
    [0, 1, 0, 1, 0], # 4ª Corda (D)
    [1, 2, 0, 1, 0], # 3ª Corda (G)
    [0, 1, 1, 0, 1], # 2ª Corda (B)
    [0, 1, 0, 1, 2], # 1ª Corda (E)
]

# O Shape Mestre de 12 casas (Uma oitava completa a partir da corda solta)
SHAPE_COMPLETO = [
    [1, 1, 0, 1, 0, 1, 0, 1, 2, 0, 1, 0], # 7ª Corda (B)
    [1, 0, 1, 2, 0, 1, 0, 1, 1, 0, 1, 0], # 6ª Corda (E)
    [1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 2, 0], # 5ª Corda (A)
    [1, 0, 1, 0, 1, 2, 0, 1, 0, 1, 1, 0], # 4ª Corda (D)
    [2, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1], # 3ª Corda (G)
    [1, 1, 0, 1, 0, 1, 0, 1, 2, 0, 1, 0], # 2ª Corda (B)
    [1, 0, 1, 2, 0, 1, 0, 1, 1, 0, 1, 0]  # 1ª Corda (E)
]

# Lista exportável com todos os shapes disponíveis
TODOS_OS_SHAPES = [SHAPE_1, SHAPE_2, SHAPE_3, SHAPE_4, SHAPE_5, SHAPE_COMPLETO]