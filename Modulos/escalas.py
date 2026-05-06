# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 [SEU NOME]
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================

# escalas.py

# A matriz principal de notas (Cromática)
NOTAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def obter_nota(nota_aberta, casa):
    """
    Calcula a nota exata em uma casa específica do braço.
    nota_aberta: A nota da corda solta (ex: 'E')
    casa: O número da casa (0 para corda solta, 1 para primeira casa...)
    """
    # Se por acaso vier uma nota inválida, retorna vazio para não quebrar o programa
    if nota_aberta not in NOTAS:
        return "?"

    # Encontra onde a nota solta está no array (ex: 'C' é 0, 'D' é 2)
    indice_inicial = NOTAS.index(nota_aberta)
    
    # Soma as casas (cada casa é um semitom). 
    # O "% 12" faz o array dar a volta (depois do B, volta pro C)
    indice_atual = (indice_inicial + casa) % 12
    
    return NOTAS[indice_atual]

NOTAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def obter_nota_por_intervalo(tom_fundamental, semitons):
    """Função genérica para encontrar qualquer nota a partir de um tom e semitons."""
    try:
        idx_base = NOTAS.index(tom_fundamental)
        idx_destino = (idx_base + semitons) % 12
        return NOTAS[idx_destino]
    except ValueError:
        return tom_fundamental

def obter_terca(tom_fundamental, menor=False):
    # Terça Maior = 4 semitons | Terça Menor = 3 semitons
    intervalo = 3 if menor else 4
    return obter_nota_por_intervalo(tom_fundamental, intervalo)

def obter_quinta(tom_fundamental):
    # Quinta Justa = 7 semitons
    return obter_nota_por_intervalo(tom_fundamental, 7)