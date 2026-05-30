NOTAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
_NOTA_PARA_INDICE = {nota: i for i, nota in enumerate(NOTAS)}

def obter_nota(nota_aberta, casa):
    """
        Como funciona: Calcula o nome da nota musical resultante em uma determinada casa a partir de uma afinação base.
        Para que serve: Identificar notas no braço do instrumento para exibição em escalas e acordes.
        Onde é usada: Amplamente utilizado por módulos de teoria e renderização de braço.
    """
    if nota_aberta not in _NOTA_PARA_INDICE:
        return '?'
    indice_inicial = _NOTA_PARA_INDICE[nota_aberta]
    indice_atual = (indice_inicial + casa) % 12
    return NOTAS[indice_atual]

def obter_nota_por_intervalo(tom_fundamental, semitons):
    """
        Como funciona: Acessa e formata dados internos ou de configuração.
        Para que serve: Retorna as informações solicitadas sobre 'nota por intervalo'.
        Onde é usada: Chamado a partir do módulo ou classe base de 'escalas'.
    """
    if tom_fundamental not in _NOTA_PARA_INDICE:
        return tom_fundamental
    idx_base = _NOTA_PARA_INDICE[tom_fundamental]
    idx_destino = (idx_base + semitons) % 12
    return NOTAS[idx_destino]

def obter_terca(tom_fundamental, menor=False):
    """
        Como funciona: Acessa e formata dados internos ou de configuração.
        Para que serve: Retorna as informações solicitadas sobre 'terca'.
        Onde é usada: Chamado a partir do módulo ou classe base de 'escalas'.
    """
    intervalo = 3 if menor else 4
    return obter_nota_por_intervalo(tom_fundamental, intervalo)

def obter_quinta(tom_fundamental):
    """
        Como funciona: Acessa e formata dados internos ou de configuração.
        Para que serve: Retorna as informações solicitadas sobre 'quinta'.
        Onde é usada: Chamado a partir do módulo ou classe base de 'escalas'.
    """
    return obter_nota_por_intervalo(tom_fundamental, 7)

def equivalencia_notas(nota1, nota2):
    """
        Como funciona: Executa o fluxo lógico necessário para a operação 'equivalencia notas'.
        Para que serve: Realiza as tarefas fundamentais de 'equivalencia notas' dentro do contexto do módulo.
        Onde é usada: Utilizado internamente para gerenciar comportamentos de 'equivalencia notas'.
    """
    if nota1 == nota2:
        return True
    enarmonicas = {'C#': 'Db', 'Db': 'C#', 'D#': 'Eb', 'Eb': 'D#', 'F#': 'Gb', 'Gb': 'F#', 'G#': 'Ab', 'Ab': 'G#', 'A#': 'Bb', 'Bb': 'A#'}
    return enarmonicas.get(nota1) == nota2 or enarmonicas.get(nota2) == nota1