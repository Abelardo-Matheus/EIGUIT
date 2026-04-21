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