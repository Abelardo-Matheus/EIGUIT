from core.modulos.escalas import equivalencia_notas
_NOTAS_IDX = {n: i for i, n in enumerate(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])}

def obter_grau(tonica, nota):
    """
        Como funciona: Acessa e formata dados internos ou de configuração.
        Para que serve: Retorna as informações solicitadas sobre 'grau'.
        Onde é usada: Chamado a partir do módulo ou classe base de 'utils'.
    """
    graus = ['1', 'b2', '2', 'b3', '3', '4', 'b5', '5', 'b6', '6', 'b7', '7']
    try:
        return graus[(_NOTAS_IDX[nota] - _NOTAS_IDX[tonica]) % 12]
    except (KeyError, ValueError):
        return ''