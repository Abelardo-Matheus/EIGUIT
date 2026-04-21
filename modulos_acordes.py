# --- TRÍADES MAIORES (CAGED) ---
# Ordem das listas: [7ª, 6ª, 5ª, 4ª, 3ª, 2ª, 1ª]

TRIADE_C_MAIOR = [
    [0, 1, 0, 0], # 7ª B
    [1, 0, 0, 1], # 6ª E
    [0, 0, 0, 1], # 5ª A
    [0, 0, 1, 0], # 4ª D
    [1, 0, 0, 0], # 3ª G
    [0, 1, 0, 0], # 2ª B (Tônica)
    [1, 0, 0, 1]  # 1ª E
]

TRIADE_A_MAIOR = [
    [1, 0, 0],    # 7ª B
    [1, 0, 0],    # 6ª E
    [1, 0, 0],    # 5ª A (Tônica)
    [0, 0, 1],    # 4ª D
    [0, 0, 1],    # 3ª G
    [0, 0, 1],    # 2ª B
    [1, 0, 0]     # 1ª E
]

TRIADE_G_MAIOR = [
    [0, 0, 1],    # 7ª B
    [0, 0, 1],    # 6ª E (Tônica)
    [0, 1, 0],    # 5ª A
    [1, 0, 0],    # 4ª D
    [1, 0, 0],    # 3ª G
    [1, 0, 0],    # 2ª B
    [0, 0, 1]     # 1ª E
]

TRIADE_E_MAIOR = [
    [1, 0, 0],    # 7ª B
    [1, 0, 0],    # 6ª E (Tônica)
    [0, 0, 1],    # 5ª A
    [0, 0, 1],    # 4ª D
    [0, 1, 0],    # 3ª G
    [1, 0, 0],    # 2ª B
    [1, 0, 0]     # 1ª E (Tônica)
]

TRIADE_D_MAIOR = [
    [0, 0, 0],    # 7ª B
    [0, 0, 0],    # 6ª E
    [0, 0, 0],    # 5ª A
    [1, 0, 0],    # 4ª D (Tônica)
    [0, 1, 0],    # 3ª G
    [0, 0, 1],    # 2ª B
    [0, 1, 0]     # 1ª E
]

# --- TRÍADES MENORES (CAGED) ---

TRIADE_C_MENOR = [
    [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0], [0, 0, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]
]

TRIADE_A_MENOR = [
    [1, 0, 0],    # 7ª
    [1, 0, 0],    # 6ª
    [1, 0, 0],    # 5ª (Tônica)
    [0, 0, 1],    # 4ª
    [0, 0, 1],    # 3ª
    [0, 1, 0],    # 2ª (Terça menor)
    [1, 0, 0]     # 1ª
]

TRIADE_G_MENOR = [
    [0, 0, 1], [0, 0, 1], [0, 1, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [1, 0, 0]
]

TRIADE_E_MENOR = [
    [1, 0, 0],    # 7ª
    [1, 0, 0],    # 6ª (Tônica)
    [0, 0, 1],    # 5ª
    [0, 0, 1],    # 4ª
    [1, 0, 0],    # 3ª (Terça menor)
    [1, 0, 0],    # 2ª
    [1, 0, 0]     # 1ª (Tônica)
]

TRIADE_D_MENOR = [
    [0, 0, 0], [0, 0, 0], [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 0, 0]
]

TODOS_AS_TRIADES_MAIORES = [TRIADE_C_MAIOR, TRIADE_A_MAIOR, TRIADE_G_MAIOR, TRIADE_E_MAIOR, TRIADE_D_MAIOR]
TODOS_AS_TRIADES_MENORES = [TRIADE_C_MENOR, TRIADE_A_MENOR, TRIADE_G_MENOR, TRIADE_E_MENOR, TRIADE_D_MENOR]