# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 [SEU NOME]
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================

# constantes_ui.py

# --- CORES ---
FUNDO_ESCURO = (30, 30, 30)
COR_CORDA = (180, 180, 180)
COR_TRASTE = (140, 140, 140)
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
MADEIRA = (80, 40, 15)
AZUL_BOTAO = (0, 120, 215)

CORES_TONICA = [
    BRANCO, (255, 80, 80), (80, 255, 80), 
    (255, 200, 50), (50, 200, 255), (200, 100, 255)
]

COR_PAINEL = (45, 45, 45)
COR_ABA_ATIVA = (65, 65, 65)
COR_ABA_INATIVA = (35, 35, 35)
COR_SUB_ATIVA = (100, 100, 100)
COR_SUB_INATIVA = (55, 55, 55)
COR_TEXTO_INATIVO = (150, 150, 150)

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