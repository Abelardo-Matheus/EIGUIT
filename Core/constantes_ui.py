# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================

# constantes_ui.py

# --- CORES MODERNAS ---
FUNDO_ESCURO = (18, 18, 18)        # Cinza quase preto profundo
FUNDO_PAINEL = (28, 28, 28)        # Superfície levemente elevada
COR_CORDA = (160, 160, 160)
COR_TRASTE = (120, 120, 120)
BRANCO = (245, 245, 245)
PRETO = (0, 0, 0)
MADEIRA = (60, 30, 10)             # Madeira mais escura e discreta
AZUL_PRIMARIO = (0, 163, 255)      # Azul Vibrante Moderno
AZUL_HOVER = (0, 130, 200)
VERMELHO_DANGER = (231, 76, 60)    # Coral moderno
VERDE_SUCCESS = (46, 204, 113)     # Verde esmeralda

CORES_TONICA = [
    BRANCO, 
    (231, 76, 60),  # Vermelho
    (46, 204, 113), # Verde
    (241, 196, 15), # Amarelo/Ouro
    (52, 152, 219), # Azul Claro
    (155, 89, 182)  # Roxo
]

COR_PAINEL = FUNDO_PAINEL
COR_ABA_ATIVA = (45, 45, 45)
COR_ABA_INATIVA = (22, 22, 22)
COR_SUB_ATIVA = (80, 80, 80)
COR_SUB_INATIVA = (35, 35, 35)
COR_TEXTO_INATIVO = (100, 100, 100)
COR_BORDA = (60, 60, 60)

# --- GEOMETRIA ---
RADIUS_PADRAO = 8
PADDING_PADRAO = 10

# --- LISTAS DE DADOS ESTÁTICOS ---
lista_afinacoes = [
    {"nome": "Standard B", "notas": ["B", "E", "A", "D", "G", "B", "E"]},
    {"nome": "Drop A",     "notas": ["A", "E", "A", "D", "G", "B", "E"]},
    {"nome": "Standard A", "notas": ["A", "D", "G", "C", "F", "A", "D"]},
    {"nome": "All 4ths",   "notas": ["B", "E", "A", "D", "G", "C", "F"]}
]

nomes_abas = ["Escalas", "Acordes", "Análise de IA", "Configurações"]
nomes_sub_abas = [
    ["Maior", "Menor", "Pentatônica", "Blues", "Modos Gregos"],
    ["Tríades", "Tétrades", "Inversões", "Diminutos", "Suspensos"],
    ["Afinador", "Treino Ritmo", "Gerar Backing", "Timbre", "Chat"],
    ["Cores", "Sons", "MIDI", "Metrônomo", "Exportar Projeto"]
]