# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================

# escalas.py

# A matriz principal de notas (Cromática)
NOTAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
_NOTA_PARA_INDICE = {nota: i for i, nota in enumerate(NOTAS)}

def obter_nota(nota_aberta, casa):
    """
    Calcula a nota exata em uma casa específica do braço.
    nota_aberta: A nota da corda solta (ex: 'E')
    casa: O número da casa (0 para corda solta, 1 para primeira casa...)
    """
    if nota_aberta not in _NOTA_PARA_INDICE:
        return "?"

    indice_inicial = _NOTA_PARA_INDICE[nota_aberta]
    indice_atual = (indice_inicial + casa) % 12
    return NOTAS[indice_atual]

def obter_nota_por_intervalo(tom_fundamental, semitons):
    """Função genérica para encontrar qualquer nota a partir de um tom e semitons."""
    if tom_fundamental not in _NOTA_PARA_INDICE:
        return tom_fundamental

    idx_base = _NOTA_PARA_INDICE[tom_fundamental]
    idx_destino = (idx_base + semitons) % 12
    return NOTAS[idx_destino]

def obter_terca(tom_fundamental, menor=False):
    # Terça Maior = 4 semitons | Terça Menor = 3 semitons
    intervalo = 3 if menor else 4
    return obter_nota_por_intervalo(tom_fundamental, intervalo)

def obter_quinta(tom_fundamental):
    # Quinta Justa = 7 semitons
    return obter_nota_por_intervalo(tom_fundamental, 7)