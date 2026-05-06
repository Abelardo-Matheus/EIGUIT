# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 [SEU NOME]
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================

# --- TRÍADES MAIORES (CAGED) ---
# Ordem das listas: [7ª, 6ª, 5ª, 4ª, 3ª, 2ª, 1ª]

TRIADE_C_MAIOR = [
    [0, 1, 0, 0], # 7ª B
    [1, 0, 0, 1], # 6ª E
    [0, 0, 0, 2], # 5ª A -> Tônica C (Casa 3)
    [0, 0, 1, 0], # 4ª D
    [1, 0, 0, 0], # 3ª G
    [0, 2, 0, 0], # 2ª B -> Tônica C (Casa 1)
    [1, 0, 0, 1]  # 1ª E
]

TRIADE_A_MAIOR = [
    [0, 0, 1, 0, 0], # 7ª B
    [1, 0, 0, 0, 0], # 6ª E
    [2, 0, 0, 0, 1], # 5ª A -> Tônica A (Casa 0)
    [0, 0, 1, 0, 0], # 4ª D
    [0, 0, 2, 0, 0], # 3ª G -> Tônica A (Casa 2)
    [0, 0, 1, 0, 0], # 2ª B
    [1, 0, 0, 0, 0]  # 1ª E
]

TRIADE_G_MAIOR = [
    [1, 0, 0, 1], # 7ª B
    [0, 0, 0, 2], # 6ª E -> Tônica G (Casa 3)
    [0, 0, 1, 0], # 5ª A
    [1, 0, 0, 0], # 4ª D
    [2, 0, 0, 0], # 3ª G -> Tônica G (Casa 0)
    [1, 0, 0, 1], # 2ª B
    [0, 0, 0, 2]  # 1ª E -> Tônica G (Casa 3)
]

TRIADE_E_MAIOR = [
    [1, 0, 0, 0, 0], # 7ª B
    [2, 0, 0, 0, 1], # 6ª E -> Tônica E (Casa 0)
    [0, 0, 1, 0, 0], # 5ª A
    [0, 0, 2, 0, 0], # 4ª D -> Tônica E (Casa 2)
    [0, 1, 0, 0, 0], # 3ª G
    [1, 0, 0, 0, 0], # 2ª B
    [2, 0, 0, 0, 1]  # 1ª E -> Tônica E (Casa 0)
]

TRIADE_D_MAIOR = [
    [0, 0, 0, 1], # 7ª B
    [0, 0, 1, 0], # 6ª E
    [1, 0, 0, 0], # 5ª A
    [2, 0, 0, 0], # 4ª D -> Tônica D (Casa 0)
    [0, 0, 1, 0], # 3ª G
    [0, 0, 0, 2], # 2ª B -> Tônica D (Casa 3)
    [0, 0, 1, 0]  # 1ª E
]

# --- TRÍADES MENORES (CAGED) ---

TRIADE_C_MENOR = [
    [0, 1, 0, 0, 0], # 7ª B
    [0, 0, 0, 1, 0], # 6ª E
    [0, 0, 0, 2, 0], # 5ª A -> Tônica C (Casa 3)
    [0, 1, 0, 0, 0], # 4ª D
    [1, 0, 0, 0, 0], # 3ª G
    [0, 2, 0, 0, 1], # 2ª B -> Tônica C (Casa 1)
    [0, 0, 0, 1, 0]  # 1ª E
]

TRIADE_A_MENOR = [
    [0, 1, 0, 0], # 7ª B
    [1, 0, 0, 0], # 6ª E
    [2, 0, 0, 1], # 5ª A -> Tônica A (Casa 0)
    [0, 0, 1, 0], # 4ª D
    [0, 0, 2, 0], # 3ª G -> Tônica A (Casa 2)
    [0, 1, 0, 0], # 2ª B
    [1, 0, 0, 0]  # 1ª E
]

TRIADE_G_MENOR = [
    [0, 0, 0, 1], # 7ª B
    [0, 0, 0, 2], # 6ª E -> Tônica G (Casa 3)
    [0, 1, 0, 0], # 5ª A
    [1, 0, 0, 0], # 4ª D
    [2, 0, 0, 1], # 3ª G -> Tônica G (Casa 0)
    [0, 0, 0, 1], # 2ª B
    [0, 0, 0, 2]  # 1ª E -> Tônica G (Casa 3)
]

TRIADE_E_MENOR = [
    [1, 0, 0, 0], # 7ª B
    [2, 0, 0, 1], # 6ª E -> Tônica E (Casa 0)
    [0, 0, 1, 0], # 5ª A
    [0, 0, 2, 0], # 4ª D -> Tônica E (Casa 2)
    [1, 0, 0, 0], # 3ª G
    [1, 0, 0, 0], # 2ª B
    [2, 0, 0, 1]  # 1ª E -> Tônica E (Casa 0)
]

TRIADE_D_MENOR = [
    [0, 0, 0, 1], # 7ª B
    [0, 1, 0, 0], # 6ª E
    [1, 0, 0, 0], # 5ª A
    [2, 0, 0, 1], # 4ª D -> Tônica D (Casa 0)
    [0, 0, 1, 0], # 3ª G
    [0, 0, 0, 2], # 2ª B -> Tônica D (Casa 3)
    [0, 1, 0, 0]  # 1ª E
]

# Organização para o carregador
TODOS_AS_TRIADES_MAIORES = [TRIADE_C_MAIOR, TRIADE_A_MAIOR, TRIADE_G_MAIOR, TRIADE_E_MAIOR, TRIADE_D_MAIOR]
TODOS_AS_TRIADES_MENORES = [TRIADE_C_MENOR, TRIADE_A_MENOR, TRIADE_G_MENOR, TRIADE_E_MENOR, TRIADE_D_MENOR]