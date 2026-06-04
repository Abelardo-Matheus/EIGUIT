"""
Modulo de Teoria Musical - Estúdio CLI
Focado em Campo Harmônico e Progressões.
"""

class TeoricoMusical:
    NOTAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    ESTRUTURA_MAIOR = {
        'intervalos': [0, 2, 4, 5, 7, 9, 11],
        'romanos': ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°'],
        'qualidades': ['', 'm', 'm', '', '', 'm', 'dim'],
        'funcoes': {
            'I': 'Repouso',
            'IV': 'Afastamento',
            'V': 'Tensão',
            'vi': 'Acolhimento'
        }
    }

    @staticmethod
    def obter_campo_harmonico(tonica):
        # Mapeamento de bemóis para sustenidos para compatibilidade com a lista NOTAS
        mapeamento_bemois = {
            'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'
        }
        
        tonica_formatada = tonica[0].upper() + tonica[1:].lower() if len(tonica) > 1 else tonica.upper()
        tonica_busca = mapeamento_bemois.get(tonica_formatada, tonica_formatada)
        
        try:
            idx_raiz = TeoricoMusical.NOTAS.index(tonica_busca)
        except ValueError:
            return None

        campo = []
        est = TeoricoMusical.ESTRUTURA_MAIOR
        
        for i in range(7):
            idx_nota = (idx_raiz + est['intervalos'][i]) % 12
            nota = TeoricoMusical.NOTAS[idx_nota]
            romano = est['romanos'][i]
            qualidade = est['qualidades'][i]
            funcao = est['funcoes'].get(romano, '-')
            
            campo.append({
                'grau': romano,
                'acorde': f"{nota}{qualidade}",
                'funcao': funcao,
                'tipo': 'Maior' if qualidade == '' else ('Menor' if qualidade == 'm' else 'Diminuto')
            })
        return campo

    @staticmethod
    def obter_progressoes(tonica):
        campo = TeoricoMusical.obter_campo_harmonico(tonica)
        if not campo: return []
        
        # Mapeamento para busca rápida
        mapa = {c['grau']: c['acorde'] for c in campo}
        
        return [
            {
                'nome': 'Rock Melódico',
                'graus': 'I - V - IV - I',
                'acordes': f"{mapa['I']} - {mapa['V']} - {mapa['IV']} - {mapa['I']}"
            },
            {
                'nome': 'Balada Rock',
                'graus': 'I - vi - IV - V',
                'acordes': f"{mapa['I']} - {mapa['vi']} - {mapa['IV']} - {mapa['V']}"
            }
        ]
