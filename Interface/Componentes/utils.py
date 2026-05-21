# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Utilitários Musicais para Componentes de UI
# =============================================================================

_NOTAS_IDX = {n: i for i, n in enumerate(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])}

def obter_grau(tonica, nota):
    graus = ['1', 'b2', '2', 'b3', '3', '4', 'b5', '5', 'b6', '6', 'b7', '7']
    try:
        return graus[(_NOTAS_IDX[nota] - _NOTAS_IDX[tonica]) % 12]
    except (KeyError, ValueError): return ""

def equivalencia_notas(nota1, nota2):
    if nota1 == nota2: return True
    enarmonicas = {"C#": "Db", "Db": "C#", "D#": "Eb", "Eb": "D#", "F#": "Gb", "Gb": "F#", "G#": "Ab", "Ab": "G#", "A#": "Bb", "Bb": "A#"}
    return enarmonicas.get(nota1) == nota2 or enarmonicas.get(nota2) == nota1
