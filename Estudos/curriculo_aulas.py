# -*- coding: utf-8 -*-
"""
Curriculo da trilha de Aulas: Improvisacao e Padroes Melodicos.

Uma trilha guiada, do iniciante ao avancado, que costura os dois motores
ja existentes (Estudos/estudo_padroes.py e Estudos/estudo_improvisacao.py)
em aulas curtas: uma explicacao simples, um objetivo claro e um treino
interativo ja configurado (tonica, escala/progressao, padrao, andamento).

Cada aula aponta para um dos motores por 'tipo' ('padrao', 'ritmo' ou
'improviso') e guarda um 'preset' com os NOMES (nao indices) das opcoes a
selecionar, resolvidos em tempo de execucao por indice_padrao_por_nome /
indice_ritmo_por_nome / indice_progressao_por_nome / indice_modo_por_nome.
Isso evita quebrar a trilha se a ordem das listas mudar nos motores.
"""
import Estudos.estudo_padroes as estudo_padroes
import Estudos.estudo_improvisacao as estudo_improvisacao


def indice_padrao_por_nome(nome):
    for i, p in enumerate(estudo_padroes.PADROES_MELODICOS):
        if p['nome'] == nome:
            return i
    return 0


def indice_ritmo_por_nome(nome):
    for i, p in enumerate(estudo_padroes.PADROES_RITMICOS):
        if p['nome'] == nome:
            return i
    return 0


def indice_progressao_por_nome(nome):
    for i, p in enumerate(estudo_improvisacao.PROGRESSOES):
        if p['nome'] == nome:
            return i
    return 0


def indice_modo_por_nome(nome):
    for i, m in enumerate(estudo_improvisacao.MODOS_PRATICA):
        if m['nome'] == nome:
            return i
    return 0


# --- niveis da trilha --------------------------------------------------------
NIVEIS = [
    {
        'id': 'iniciante',
        'nome': 'Iniciante',
        'subtitulo': 'Uma nota de cada vez',
        'descricao': 'O pulso, a primeira escala e o conceito de "para onde a nota vai".',
        'cor': 'verde',
        'aulas': [
            {
                'id': 'ini_pulso',
                'titulo': 'O pulso antes da nota',
                'tipo': 'improviso',
                'explicacao': (
                    'Antes de pensar em escalas, sinta o tempo. Aqui voce toca uma '
                    'unica nota (a tonica) e varia so o ritmo em cima da progressao. '
                    'Improviso comeca no ritmo, nao na altura da nota.'
                ),
                'objetivo': 'Toque so a tonica, mudando o ritmo a cada compasso.',
                'preset': {'tonica': 'A', 'progressao': 'I - V - vi - IV',
                           'modo': 'So ritmo', 'instrumento': 'guitarra', 'bpm': 70},
            },
            {
                'id': 'ini_escala',
                'titulo': 'Primeira escala: pentatonica menor',
                'tipo': 'padrao',
                'explicacao': (
                    'A pentatonica menor tem so 5 notas por oitava e serve sobre a '
                    'maioria das musicas. Suba e desca devagar, no tempo do metronomo, '
                    'ate decorar a ordem sem olhar.'
                ),
                'objetivo': 'Suba e desca a escala inteira sem perder o tempo.',
                'preset': {'tonica': 'A', 'escala': 'penta_menor', 'padrao': 'Escala direta',
                           'direcao': 'Ascendente', 'instrumento': 'guitarra', 'bpm': 60},
            },
            {
                'id': 'ini_alvo',
                'titulo': 'Notas alvo: para onde a nota vai',
                'tipo': 'improviso',
                'explicacao': (
                    'Improvisar bem e menos sobre decorar escala e mais sobre saber '
                    'em qual nota voce chega quando o acorde muda. Aqui o diagrama '
                    'marca em verde as notas do acorde atual: mire nelas no tempo forte.'
                ),
                'objetivo': 'A cada troca de acorde, toque uma nota alvo (verde) no tempo 1.',
                'preset': {'tonica': 'C', 'progressao': 'I - V - vi - IV',
                           'modo': 'Notas alvo', 'instrumento': 'guitarra', 'bpm': 75},
            },
            {
                'id': 'ini_grupos3',
                'titulo': 'Grupos de 3: fluencia',
                'tipo': 'padrao',
                'explicacao': (
                    'Em vez de subir grau a grau, toque tres notas a partir de cada '
                    'grau da escala antes de avancar. Isso quebra o automatismo e '
                    'comeca a soar como frase, nao como exercicio.'
                ),
                'objetivo': 'Toque o padrao de grupos de 3 sem travar entre um grupo e outro.',
                'preset': {'tonica': 'A', 'escala': 'penta_menor', 'padrao': 'Grupos de 3',
                           'direcao': 'Ascendente', 'instrumento': 'guitarra', 'bpm': 65},
            },
            {
                'id': 'ini_pentamaior',
                'titulo': 'Pentatonica maior: outra cor',
                'tipo': 'padrao',
                'explicacao': (
                    'Mesma forma da pentatonica menor, som bem diferente: mais aberto, '
                    'menos "triste". Troque so a escala e compare o efeito na mesma '
                    'tonica.'
                ),
                'objetivo': 'Suba e desca comparando o som com a pentatonica menor.',
                'preset': {'tonica': 'A', 'escala': 'penta_maior', 'padrao': 'Escala direta',
                           'direcao': 'Ascendente', 'instrumento': 'guitarra', 'bpm': 65},
            },
        ],
    },
    {
        'id': 'intermediario',
        'nome': 'Intermediario',
        'subtitulo': 'Frases com direcao',
        'descricao': 'Intervalos, arpejos, a cadencia do jazz e o inicio do fraseado.',
        'cor': 'ciano',
        'aulas': [
            {
                'id': 'int_tercas',
                'titulo': 'Tercas: o ouvido pra harmonia',
                'tipo': 'padrao',
                'explicacao': (
                    'Tocar em intervalos de terca (pular uma nota da escala) e a base '
                    'de quase todo solo melodico. Comece devagar: o salto exige mais '
                    'precisao que a escala direta.'
                ),
                'objetivo': 'Toque o padrao de tercas mantendo o tempo constante.',
                'preset': {'tonica': 'C', 'escala': 'maior', 'padrao': 'Tercas',
                           'direcao': 'Ascendente', 'instrumento': 'guitarra', 'bpm': 70},
            },
            {
                'id': 'int_grupos4',
                'titulo': 'Grupos de 4: o classico do estudo tecnico',
                'tipo': 'padrao',
                'explicacao': (
                    'O padrao 1-2-3-4, 2-3-4-5... aparece em praticamente todo metodo '
                    'de tecnica. Serve tanto para velocidade quanto para memorizar a '
                    'escala em blocos.'
                ),
                'objetivo': 'Toque os grupos de 4 sem parar entre cada bloco.',
                'preset': {'tonica': 'E', 'escala': 'menor_nat', 'padrao': 'Grupos de 4',
                           'direcao': 'Ascendente', 'instrumento': 'guitarra', 'bpm': 75},
            },
            {
                'id': 'int_blues',
                'titulo': 'Blues: a escala e a forma',
                'tipo': 'improviso',
                'explicacao': (
                    'O blues de 12 compassos e a forma mais tocada da musica popular. '
                    'Aqui a escala inteira do acorde fica disponivel: percorra ela sem '
                    'parar nas notas marcadas para evitar.'
                ),
                'objetivo': 'Siga a forma de 12 compassos usando a escala do acorde atual.',
                'preset': {'tonica': 'A', 'progressao': 'Blues em 12 compassos',
                           'modo': 'Escala', 'instrumento': 'guitarra', 'bpm': 85},
            },
            {
                'id': 'int_arpejo135',
                'titulo': 'Arpejo 1-3-5: deixando claro o acorde',
                'tipo': 'padrao',
                'explicacao': (
                    'Tocar a triade (1-3-5) sobre cada grau da escala mostra a '
                    'harmonia com clareza. E o jeito mais direto de "dizer" qual '
                    'acorde esta soando so com a melodia.'
                ),
                'objetivo': 'Toque o arpejo de cada grau antes de passar para o proximo.',
                'preset': {'tonica': 'G', 'escala': 'maior', 'padrao': 'Arpejo 1-3-5',
                           'direcao': 'Ascendente', 'instrumento': 'guitarra', 'bpm': 70},
            },
            {
                'id': 'int_iiVI',
                'titulo': 'ii-V-I: a cadencia do jazz',
                'tipo': 'improviso',
                'explicacao': (
                    'ii-V-I e a celula harmonica mais comum do jazz. Treine chegar '
                    'na nota alvo do acorde I bem no momento da resolucao: e ali que '
                    'a frase "fecha".'
                ),
                'objetivo': 'Resolva claramente no acorde I a cada volta da progressao.',
                'preset': {'tonica': 'C', 'progressao': 'ii - V - I',
                           'modo': 'Notas alvo', 'instrumento': 'guitarra', 'bpm': 80},
            },
            {
                'id': 'int_pergresp',
                'titulo': 'Pergunta e resposta',
                'tipo': 'improviso',
                'explicacao': (
                    'Toque uma frase curta de dois compassos (a "pergunta") e depois '
                    'responda com uma frase parecida, mas que termine diferente. E o '
                    'primeiro passo para improvisar com estrutura, nao so notas soltas.'
                ),
                'objetivo': 'Toque uma frase de 2 compassos e responda com outra diferente no final.',
                'preset': {'tonica': 'A', 'progressao': 'i - VI - III - VII',
                           'modo': 'Pergunta e resposta', 'instrumento': 'guitarra', 'bpm': 75},
            },
        ],
    },
    {
        'id': 'avancado',
        'nome': 'Avancado',
        'subtitulo': 'Cor, tensao e vocabulario',
        'descricao': 'Cromatismo, modos, harmonia mais tensa e ritmo irregular.',
        'cor': 'aviso',
        'aulas': [
            {
                'id': 'av_cromatismo',
                'titulo': 'Cromatismo: aproximando por fora',
                'tipo': 'improviso',
                'explicacao': (
                    'Em vez de cair direto na nota alvo, aproxime por um semitom '
                    'abaixo (ou acima) antes de resolver. E o principal tempero do '
                    'vocabulario de jazz e blues avancado.'
                ),
                'objetivo': 'Aproxime cada nota alvo por semitom antes de resolver nela.',
                'preset': {'tonica': 'D', 'progressao': 'ii - V - I',
                           'modo': 'Cromatismo', 'instrumento': 'guitarra', 'bpm': 85},
            },
            {
                'id': 'av_arpejo1357',
                'titulo': 'Arpejo 1-3-5-7: vocabulario de jazz',
                'tipo': 'padrao',
                'explicacao': (
                    'Adicionar a setima ao arpejo muda completamente a cor: agora '
                    'cada grau soa como um acorde de quatro notas. Base do vocabulario '
                    'de jazz e de harmonia mais sofisticada.'
                ),
                'objetivo': 'Toque o arpejo de quatro notas sobre cada grau da escala.',
                'preset': {'tonica': 'D', 'escala': 'menor_harm', 'padrao': 'Arpejo 1-3-5-7',
                           'direcao': 'Ascendente', 'instrumento': 'guitarra', 'bpm': 75},
            },
            {
                'id': 'av_dorico',
                'titulo': 'Vamp dorico: som modal',
                'tipo': 'improviso',
                'explicacao': (
                    'Com so dois acordes tocando em loop, sobra espaco para explorar '
                    'o modo dorico com calma. Sem a pressa de trocar de escala a cada '
                    'compasso, o foco vai para o fraseado.'
                ),
                'objetivo': 'Explore o modo dorico livremente sobre os dois acordes.',
                'preset': {'tonica': 'E', 'progressao': 'Vamp dorico i - IV',
                           'modo': 'Escala', 'instrumento': 'guitarra', 'bpm': 90},
            },
            {
                'id': 'av_iiVmenor',
                'titulo': 'ii-V menor: a nota a evitar',
                'tipo': 'improviso',
                'explicacao': (
                    'A cadencia menor tem um acorde meio-diminuto (m7b5) que exige '
                    'cuidado: uma das notas da escala pesa demais se parada em tempo '
                    'forte. Aprenda a reconhecer e contornar essa nota.'
                ),
                'objetivo': 'Resolva a cadencia evitando parar na nota marcada em vermelho.',
                'preset': {'tonica': 'B', 'progressao': 'ii - V menor',
                           'modo': 'Escala', 'instrumento': 'guitarra', 'bpm': 80},
            },
            {
                'id': 'av_ziguezague',
                'titulo': 'Zigue-zague e escada: quebrando a linearidade',
                'tipo': 'padrao',
                'explicacao': (
                    'Depois de dominar os padroes lineares, misture a ordem dentro '
                    'de cada grupo. O ouvido para de prever a proxima nota e a frase '
                    'soa mais "composta" do que "estudada".'
                ),
                'objetivo': 'Toque o padrao completo mantendo o tempo, mesmo com a ordem quebrada.',
                'preset': {'tonica': 'A', 'escala': 'dorico', 'padrao': 'Zigue-zague',
                           'direcao': 'Ascendente', 'instrumento': 'guitarra', 'bpm': 75},
            },
            {
                'id': 'av_ritmo',
                'titulo': 'Ritmo avancado: sincope',
                'tipo': 'ritmo',
                'explicacao': (
                    'Improviso avancado nao e so sobre notas dificeis: e sobre ritmo '
                    'que sai do obvio. A sincope acentua fora do tempo forte; treine '
                    'ate o contratempo soar natural, nao contado.'
                ),
                'objetivo': 'Toque a celula ritmica no tempo, conferida pelo microfone.',
                'preset': {'ritmo': 'Sincope', 'instrumento': 'guitarra', 'bpm': 80},
            },
            {
                'id': 'av_pedal',
                'titulo': 'Pedal na tonica: criando tensao',
                'tipo': 'padrao',
                'explicacao': (
                    'Alternar cada grau da escala com a tonica cria um efeito de '
                    'pedal: a tonica funciona como ancora enquanto a outra nota '
                    'passeia por cima, criando e resolvendo tensao a cada par.'
                ),
                'objetivo': 'Toque o padrao de pedal ouvindo a tensao e resolucao em cada par.',
                'preset': {'tonica': 'E', 'escala': 'blues', 'padrao': 'Pedal na tonica',
                           'direcao': 'Ascendente', 'instrumento': 'guitarra', 'bpm': 70},
            },
        ],
    },
]


def todas_aulas():
    """Lista achatada de (nivel, aula) para busca por id."""
    for nivel in NIVEIS:
        for aula in nivel['aulas']:
            yield nivel, aula


def total_aulas():
    return sum(len(n['aulas']) for n in NIVEIS)
