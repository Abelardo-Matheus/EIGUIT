# -*- coding: utf-8 -*-
"""
Conteudo didatico do estudo de Pedais de Efeito.

Cada pedal tem: o que ele faz em uma frase, como funciona por dentro (sem
matematica), quando usar, uma dica pratica, o audio base que melhor mostra o
efeito, os parametros (com explicacao curta e longa) e exemplos prontos.

Os 'id' dos parametros sao os mesmos nomes usados em audio/efeitos_pedais.py.
Os grupos vao do mais simples (ganho) ao mais complexo (pitch e sintese).
"""

# ---------------------------------------------------------------------------
# Parametros: fabrica curta para nao repetir chaves
# ---------------------------------------------------------------------------

def _p(id_, nome, minimo, maximo, padrao, curto, explicacao, unidade='%',
       casas=0, opcoes=None):
    return {'id': id_, 'nome': nome, 'min': minimo, 'max': maximo,
            'padrao': padrao, 'unidade': unidade, 'casas': casas,
            'opcoes': opcoes, 'curto': curto, 'explicacao': explicacao}


def formatar_valor(param, valor):
    """Texto do valor para a interface (porcentagem, dB, ms, Hz, opcao)."""
    if param.get('opcoes'):
        for v, rotulo in param['opcoes']:
            if abs(v - valor) < 1e-6:
                return rotulo
        return str(valor)
    u = param['unidade']
    if u == '%' and param['min'] >= 0 and param['max'] <= 1:
        return f"{int(round(valor * 100))}%"
    if u == '%':
        faixa = param['max'] - param['min'] or 1
        return f"{int(round((valor - param['min']) / faixa * 100))}%"
    if param['casas'] == 0:
        texto = f'{int(round(valor))}'
    else:
        texto = f"{valor:.{param['casas']}f}"
    if u == 'dB' and valor > 0:
        texto = '+' + texto
    return f'{texto} {u}'.strip()


# ---------------------------------------------------------------------------
# Grupos (do simples ao complexo)
# ---------------------------------------------------------------------------

GRUPOS = [
    {'id': 'ganho', 'nome': 'Ganho e saturação', 'nivel': 'Básico',
     'descricao': 'Pedais que aumentam o sinal e "sujam" o som. É por onde quase todo mundo começa.'},
    {'id': 'dinamica', 'nome': 'Dinâmica e volume', 'nivel': 'Básico',
     'descricao': 'Controlam o quão forte ou fraco o som fica ao longo do tempo.'},
    {'id': 'filtros', 'nome': 'Filtros e equalização', 'nivel': 'Intermediário',
     'descricao': 'Mudam o timbre escolhendo quais frequências (graves, médios, agudos) aparecem.'},
    {'id': 'modulacao', 'nome': 'Modulação', 'nivel': 'Intermediário',
     'descricao': 'Um oscilador lento (LFO) mexe sozinho em volume, afinação ou fase, criando movimento.'},
    {'id': 'ambiencia', 'nome': 'Tempo e ambiência', 'nivel': 'Intermediário',
     'descricao': 'Repetem o som ou simulam o espaço de uma sala: dão profundidade e tamanho.'},
    {'id': 'pitch', 'nome': 'Pitch e especiais', 'nivel': 'Avançado',
     'descricao': 'Mexem na altura das notas ou criam sons que a guitarra sozinha não faz.'},
]

PCT = '%'

PEDAIS = [
    # ===================================================================
    # GANHO E SATURACAO
    # ===================================================================
    {
        'id': 'boost', 'grupo': 'ganho', 'nome': 'Clean Boost', 'cor': (225, 190, 60),
        'resumo': 'Deixa o som mais alto, sem mudar muito o timbre.',
        'como_funciona': 'É um amplificador pequeno dentro de uma caixinha: pega o sinal da '
                         'guitarra e aumenta o volume dele. Sozinho quase não muda o som, mas '
                         'quando esse sinal mais forte chega no amplificador, o amp começa a '
                         'saturar. Por isso o boost também é usado para "empurrar" o amp. Aqui a '
                         'gente simula um amp logo depois do pedal para você ouvir isso.',
        'quando_usar': 'Solos que precisam aparecer mais que a base, ou para dar um pouco mais de '
                       'drive ao amplificador sem usar um pedal de distorção.',
        'dica': 'Compare "Ligado" e "Desligado" com o Amp em zero: a diferença é quase só volume. '
                'Depois suba o Amp e repita: agora o boost também muda a saturação.',
        'base': 'riff',
        'parametros': [
            _p('ganho', 'Ganho', 0, 20, 8, 'Quanto o volume sobe.',
               'É o único controle de muitos boosts. Em decibéis: +6 dB é mais ou menos o dobro '
               'da força do sinal, +20 dB é um empurrão enorme. Quanto mais alto, mais o amp '
               'depois dele satura.', 'dB'),
            _p('brilho', 'Brilho', -1, 1, 0, 'Mais ou menos agudo.',
               'Alguns boosts têm um controle de agudos (treble booster). Para a direita o som fica '
               'mais brilhante e cortante, para a esquerda mais escuro.', PCT),
            _p('amp', 'Amp (simulado)', 0, 1, 0.35, 'Quanto o amplificador já está saturando.',
               'Não é um botão do pedal: representa o quanto o seu amplificador já está no limite. '
               'Com o amp limpo (0%) o boost só aumenta o volume. Com o amp perto de saturar, o '
               'boost empurra ele para o drive.', PCT),
        ],
        'exemplos': [('Só volume', {'ganho': 6, 'brilho': 0, 'amp': 0}),
                     ('Empurrando o amp', {'ganho': 16, 'brilho': 0.2, 'amp': 0.8}),
                     ('Treble booster', {'ganho': 12, 'brilho': 1, 'amp': 0.5})],
    },
    {
        'id': 'overdrive', 'grupo': 'ganho', 'nome': 'Overdrive', 'cor': (70, 185, 90),
        'resumo': 'Saturação suave, parecida com um amp valvulado no talo.',
        'como_funciona': 'O pedal aumenta muito o sinal e depois "arredonda" os picos da onda '
                         '(clipping suave). Uma onda arredondada ganha harmônicos novos, e é isso '
                         'que a gente ouve como "sujeira". Muitos overdrives cortam um pouco dos '
                         'graves antes de saturar, o que dá aquele som com mais médios, que se '
                         'destaca na banda.',
        'quando_usar': 'Blues, rock clássico, country, bases com um pouco de "crocância". Responde '
                       'bem à dinâmica: tocando mais leve ele limpa.',
        'dica': 'Com o Drive baixo, as notas mais fracas do riff soam quase limpas e as mais fortes '
                'saturam: isso é a "dinâmica" que o pessoal fala tanto.',
        'base': 'riff',
        'parametros': [
            _p('drive', 'Drive', 0, 1, 0.45, 'Quanto de saturação.',
               'Aumenta o sinal antes do circuito que arredonda a onda. Pouco drive: o som só '
               'fica "gordinho". Muito drive: sustenta mais, comprime e fica mais sujo.'),
            _p('tone', 'Tone', 0, 1, 0.55, 'Mais escuro ou mais brilhante.',
               'Um filtro de agudos depois da saturação. Para a esquerda o som fica mais '
               'aveludado, para a direita mais aberto e cortante. Agudo demais pode ficar áspero.'),
            _p('level', 'Level', 0, 1, 0.7, 'Volume de saída do pedal.',
               'Só o volume final. Serve para deixar o pedal ligado no mesmo volume de desligado '
               '(ou mais alto, para solos). Não muda a quantidade de saturação.'),
        ],
        'exemplos': [('Blues leve', {'drive': 0.25, 'tone': 0.5, 'level': 0.8}),
                     ('Rock clássico', {'drive': 0.6, 'tone': 0.6, 'level': 0.7}),
                     ('Escuro e gordo', {'drive': 0.5, 'tone': 0.15, 'level': 0.8})],
    },
    {
        'id': 'distorcao', 'grupo': 'ganho', 'nome': 'Distorção', 'cor': (230, 120, 40),
        'resumo': 'Saturação pesada e agressiva, típica do rock pesado e do metal.',
        'como_funciona': 'Mesma ideia do overdrive, só que muito mais extrema: o sinal é '
                         'aumentado centenas de vezes e os picos são cortados de forma quase reta '
                         '(clipping duro). A onda fica parecida com uma onda quadrada, cheia de '
                         'harmônicos, e as notas sustentam por muito mais tempo.',
        'quando_usar': 'Riffs de rock pesado e metal, power chords, solos com muito sustain.',
        'dica': 'Troque o audio base para "Acordes": acordes cheios com muita distorção viram uma '
                'massa confusa. É por isso que no metal se usa tanto power chord (só 2 ou 3 notas).',
        'base': 'power',
        'parametros': [
            _p('dist', 'Distortion', 0, 1, 0.6, 'Quanto de ganho e corte.',
               'Aumenta o sinal antes do corte. Pouco: rock com pegada. Muito: metal, sustain '
               'longo e mais ruído junto (em um pedal de verdade o chiado também sobe).'),
            _p('tone', 'Tone', 0, 1, 0.5, 'Brilho do som.',
               'Filtro depois da distorção. Mais escuro soa grosso e "fechado"; mais aberto soa '
               'agressivo. Distorção pesada com agudo no máximo tende a ficar estridente.'),
            _p('level', 'Level', 0, 1, 0.7, 'Volume de saída.',
               'Volume final do pedal, para igualar com o som limpo.'),
        ],
        'exemplos': [('Hard rock', {'dist': 0.35, 'tone': 0.55, 'level': 0.75}),
                     ('Metal', {'dist': 0.95, 'tone': 0.45, 'level': 0.65}),
                     ('Grunge escuro', {'dist': 0.7, 'tone': 0.2, 'level': 0.8})],
    },
    {
        'id': 'fuzz', 'grupo': 'ganho', 'nome': 'Fuzz', 'cor': (170, 60, 170),
        'resumo': 'A saturação mais antiga e mais "rasgada": som felpudo, quase de sintetizador.',
        'como_funciona': 'Os primeiros pedais de efeito eram fuzz: dois ou três transistores '
                         'levados ao extremo. A onda fica praticamente quadrada e assimétrica. '
                         'O som é grosso, "felpudo" e as notas terminam de forma estranha, '
                         'picotando quando o sinal fica fraco (isso é característica, não defeito).',
        'quando_usar': 'Rock dos anos 60 e 70, stoner, psicodélico, solos com timbre bem marcante.',
        'dica': 'Suba o Bias e ouça o fim das notas: o som começa a "engasgar" (sputter). Muitos '
                'fuzz antigos com bateria fraca soam assim, e tem gente que busca isso.',
        'base': 'riff',
        'parametros': [
            _p('fuzz', 'Fuzz', 0, 1, 0.7, 'Quantidade de saturação.',
               'O ganho dos transistores. Mesmo no mínimo um fuzz já é bem saturado; no máximo '
               'vira uma parede de som.'),
            _p('tone', 'Tone', 0, 1, 0.5, 'Escuro ou brilhante.',
               'Filtro de agudos. Fuzz escuro lembra um violoncelo distorcido; aberto fica '
               'áspero e agressivo.'),
            _p('volume', 'Volume', 0, 1, 0.7, 'Volume de saída.',
               'Volume final do pedal. Fuzz costuma ter muito mais volume disponível do que '
               'você precisa: ajuste para ficar parecido com o som desligado.'),
            _p('bias', 'Bias / Gate', 0, 1, 0, 'Deixa o som picotado.',
               'Muda o ponto de trabalho do transistor (como uma bateria fraca). Com o valor '
               'alto, as partes mais fracas do som somem e a nota "engasga" ao morrer.'),
        ],
        'exemplos': [('Clássico anos 60', {'fuzz': 0.5, 'tone': 0.6, 'volume': 0.7, 'bias': 0}),
                     ('Parede de fuzz', {'fuzz': 1, 'tone': 0.35, 'volume': 0.65, 'bias': 0}),
                     ('Bateria fraca', {'fuzz': 0.8, 'tone': 0.5, 'volume': 0.8, 'bias': 0.8})],
    },

    # ===================================================================
    # DINAMICA E VOLUME
    # ===================================================================
    {
        'id': 'volume', 'grupo': 'dinamica', 'nome': 'Volume / Swell', 'cor': (120, 130, 150),
        'resumo': 'Controla o volume com o pé e cria o efeito de "violino" (swell).',
        'como_funciona': 'Um pedal de volume é só um potenciômetro de volume controlado com o pé. '
                         'Quando você toca a nota com o volume fechado e abre devagar, o ataque '
                         'da palheta some e a nota "nasce" do nada, parecendo um violino. Pedais '
                         'como o Slow Gear fazem esse movimento sozinhos a cada nota.',
        'quando_usar': 'Entradas suaves, ambientes, fazer swells em baladas, controlar o volume '
                       'da guitarra sem mexer no amplificador.',
        'dica': 'Compare Ataque em zero com Ataque perto de 0,8 s: o som da palheta desaparece e '
                'cada acorde parece surgir do nada.',
        'base': 'acorde',
        'parametros': [
            _p('pedal', 'Pedal (posição)', 0, 1, 1, 'Posição do pé: fechado a aberto.',
               'Onde o seu pé está no pedal. 0% é mudo, 100% é o volume total. A curva é '
               'logarítmica, como nos pedais de verdade, para a variação soar natural.'),
            _p('ataque', 'Ataque (swell)', 0, 1.2, 0.5, 'Tempo para cada nota aparecer.',
               'Tempo que o volume leva para subir depois de cada nota. Zero é o som normal. '
               'Valores altos apagam o ataque da palheta e fazem a nota crescer devagar.', 's', 2),
        ],
        'exemplos': [('Normal', {'pedal': 1, 'ataque': 0}),
                     ('Violino', {'pedal': 1, 'ataque': 0.45}),
                     ('Swell lento', {'pedal': 1, 'ataque': 0.9})],
    },
    {
        'id': 'compressor', 'grupo': 'dinamica', 'nome': 'Compressor', 'cor': (60, 130, 220),
        'resumo': 'Iguala o volume das notas: as fortes ficam mais baixas, as fracas mais altas.',
        'como_funciona': 'O compressor "escuta" o volume o tempo todo. Quando o som passa de um '
                         'limite, ele abaixa o volume automaticamente; depois compensa tudo para '
                         'cima. Resultado: notas mais uniformes e que duram mais (sustain), porque '
                         'o fim da nota, que era fraco, fica mais alto.',
        'quando_usar': 'Funk e country (palhetada limpa bem regular), sustain em solos limpos, '
                       'deixar o som mais "polido" e estável.',
        'dica': 'Use "Nota longa" e compare ligado/desligado: sem o compressor a nota vai sumindo, '
                'com ele o volume fica quase parado. No Attack alto o "tapa" da palheta volta.',
        'base': 'nota',
        'parametros': [
            _p('sustain', 'Sustain', 0, 1, 0.6, 'Quanto comprimir.',
               'Junta dois ajustes: o limite a partir do qual o compressor age e a força com que '
               'ele abaixa o volume. Mais sustain = notas mais iguais e mais longas, mas também '
               'mais "achatadas" e com mais ruído aparecendo.'),
            _p('attack', 'Attack', 1, 100, 10, 'Velocidade da reação.',
               'Quanto tempo o compressor demora para abaixar o volume depois que a nota começa. '
               'Rápido (1 ms) segura até o ataque da palheta; lento (50 ms ou mais) deixa o ataque '
               'passar e só comprime o resto da nota, soando mais percussivo.', 'ms'),
            _p('level', 'Level', 0, 1, 0.6, 'Volume de saída.',
               'Compensação de volume depois da compressão.'),
        ],
        'exemplos': [('Leve', {'sustain': 0.3, 'attack': 20, 'level': 0.6}),
                     ('Country / funk', {'sustain': 0.7, 'attack': 3, 'level': 0.55}),
                     ('Ataque percussivo', {'sustain': 0.8, 'attack': 80, 'level': 0.5})],
    },
    {
        'id': 'gate', 'grupo': 'dinamica', 'nome': 'Noise Gate', 'cor': (90, 95, 105),
        'resumo': 'Corta o chiado quando você não está tocando.',
        'como_funciona': 'Funciona como uma porta: se o volume está acima de um limite, a porta '
                         'fica aberta e o som passa; se cai abaixo (entre as notas, só chiado), '
                         'a porta fecha e fica mudo. Neste exemplo o audio base já vem com '
                         'distorção alta e chiado, que é justamente quando um gate faz falta.',
        'quando_usar': 'Distorções com muito ganho, metal com paradas secas, pedaleiras '
                       'barulhentas.',
        'dica': 'Desligue o pedal e ouça o chiado nos intervalos. Ligue e vá subindo o Limiar: '
                'se passar do ponto, o gate começa a cortar o fim das notas também.',
        'base': 'staccato',
        'parametros': [
            _p('limiar', 'Threshold (limiar)', -70, -15, -34, 'A partir de qual volume a porta abre.',
               'Sinal abaixo desse volume é cortado. Muito baixo: o chiado ainda passa. Muito '
               'alto: o gate come o sustain e o fim das notas.', 'dB'),
            _p('release', 'Release', 10, 500, 80, 'Quanto tempo a porta demora para fechar.',
               'Depois que o som cai abaixo do limiar, a porta ainda fica aberta esse tempo e fecha '
               'suave. Curto: paradas bem secas (metal). Longo: fim de nota mais natural.', 'ms'),
        ],
        'exemplos': [('Suave', {'limiar': -37, 'release': 300}),
                     ('Metal seco', {'limiar': -30, 'release': 25}),
                     ('Exagerado', {'limiar': -17, 'release': 40})],
    },

    # ===================================================================
    # FILTROS E EQ
    # ===================================================================
    {
        'id': 'eq', 'grupo': 'filtros', 'nome': 'Equalizador', 'cor': (200, 200, 205),
        'resumo': 'Aumenta ou diminui graves, médios e agudos.',
        'como_funciona': 'Todo som é uma mistura de frequências: graves (encorpado), médios '
                         '(presença, "voz" da guitarra) e agudos (brilho, ataque). O equalizador '
                         'tem filtros que reforçam ou cortam cada faixa. Não adiciona nada novo, '
                         'só muda o equilíbrio do que já existe.',
        'quando_usar': 'Ajustar o timbre para a sala ou para a banda, dar um reforço de médios no '
                       'solo, corrigir um som embolado ou estridente.',
        'dica': 'Zere tudo e mexa uma banda por vez até o extremo. Depois tente o clássico '
                '"V" (graves e agudos para cima, médios para baixo) e compare com médios para cima.',
        'base': 'acorde',
        'parametros': [
            _p('graves', 'Graves', -12, 12, 0, 'Corpo e peso.',
               'Faixa abaixo de ~180 Hz. Mais graves: som encorpado (em excesso, embola). Menos: '
               'som magro, que sobra espaço para o baixo.', 'dB'),
            _p('medios', 'Médios', -12, 12, 0, 'Presença e "voz".',
               'É onde a guitarra se destaca na mistura. Cortar médios dá um som mais "moderno" '
               'e escavado, mas que some quando a banda toca junto.', 'dB'),
            _p('freq_medios', 'Freq. dos médios', 250, 3000, 800, 'Qual médio você está mexendo.',
               'Escolhe o centro da banda de médios. Perto de 400 Hz é a região "caixa" e '
               'abafada; perto de 1 a 2 kHz é a região de ataque e "nasal".', 'Hz'),
            _p('agudos', 'Agudos', -12, 12, 0, 'Brilho e definição.',
               'Faixa acima de ~3 kHz. Mais agudos: som claro e cortante. Menos: som escuro e '
               'macio.', 'dB'),
            _p('level', 'Level', -12, 12, 0, 'Volume geral.',
               'Volume de saída do equalizador (em muitos modelos é um fader a mais).', 'dB'),
        ],
        'exemplos': [('Som em V', {'graves': 8, 'medios': -9, 'freq_medios': 700, 'agudos': 7, 'level': 0}),
                     ('Reforço para solo', {'graves': -2, 'medios': 8, 'freq_medios': 900, 'agudos': 2, 'level': 3}),
                     ('Telefone', {'graves': -12, 'medios': 10, 'freq_medios': 1500, 'agudos': -12, 'level': 0})],
    },
    {
        'id': 'wah', 'grupo': 'filtros', 'nome': 'Wah-Wah', 'cor': (40, 40, 45),
        'resumo': 'Um filtro que você move com o pé: o som "fala" uá-uá.',
        'como_funciona': 'Dentro do wah há um filtro que deixa passar só uma faixa estreita de '
                         'frequências, com um pico forte. O pedal move essa faixa: calcanhar '
                         'embaixo = pico nos graves (som fechado, "u"); ponta do pé = pico nos '
                         'agudos (som aberto, "á"). Mexendo o pé você ouve "uá-uá", como uma voz.',
        'quando_usar': 'Funk (palhetada abafada com wah), rock dos anos 70, solos expressivos. '
                       'Também "parado" numa posição, como um filtro fixo.',
        'dica': 'Deixe Auto em 0 e vá mudando a posição do Pedal: você ouve cada "vogal" parada. '
                'Depois ligue o Auto para simular o pé indo e voltando.',
        'base': 'riff',
        'parametros': [
            _p('pedal', 'Pedal (posição)', 0, 1, 0.5, 'Onde está o seu pé.',
               'Posição do pedal. 0% é o calcanhar (grave, fechado), 100% é a ponta do pé '
               '(agudo, aberto). Com o Auto ligado, é o ponto em volta do qual o pé balança: '
               'mais para trás o wah fica mais fechado e grave.'),
            _p('q', 'Ressonância (Q)', 1, 12, 5, 'Quão acentuado é o pico.',
               'Largura do filtro. Baixo: efeito suave, mais natural. Alto: pico estreito e bem '
               'marcado, o wah "grita" mais.', '', 1),
            _p('auto', 'Auto (movimento)', 0, 6, 1.5, 'Velocidade do pé automático.',
               'Aqui simulamos o pé indo e voltando. 0 deixa o pedal parado na posição escolhida; '
               'valores altos parecem um wah frenético de funk.', 'Hz', 1),
        ],
        'exemplos': [('Pedal parado (meio)', {'pedal': 0.5, 'q': 5, 'auto': 0}),
                     ('Solo lento', {'pedal': 0.5, 'q': 6, 'auto': 0.8}),
                     ('Funk rápido', {'pedal': 0.5, 'q': 8, 'auto': 4})],
    },
    {
        'id': 'autowah', 'grupo': 'filtros', 'nome': 'Envelope Filter', 'cor': (240, 140, 180),
        'resumo': 'Um wah que se mexe sozinho conforme a força com que você toca.',
        'como_funciona': 'É o mesmo tipo de filtro do wah, mas em vez do pé, quem move o filtro é '
                         'o volume da sua palhetada (o "envelope"). Nota forte: o filtro abre. '
                         'Enquanto a nota perde força, o filtro fecha. Cada nota faz um "uóu".',
        'quando_usar': 'Funk, fusion, baixo slap, sons "borrachudos" tipo sintetizador.',
        'dica': 'Troque para "Notas soltas" para ouvir cada nota abrindo e fechando. Mude a Direção '
                'para o filtro descer em vez de subir.',
        'base': 'riff',
        'parametros': [
            _p('sens', 'Sensibilidade', 0, 1, 0.6, 'Quanto a palhetada move o filtro.',
               'Pouca: só as notas fortes mexem o filtro. Muita: qualquer nota abre o filtro todo.'),
            _p('q', 'Ressonância (Q)', 1, 12, 6, 'Intensidade do pico.',
               'Igual ao wah: mais alto deixa o efeito mais "cantado" e marcante.', '', 1),
            _p('resposta', 'Resposta (decay)', 5, 300, 60, 'Velocidade do filtro seguir a nota.',
               'Tempo que o filtro leva para acompanhar o volume. Curto: reação rápida e nervosa. '
               'Longo: movimento lento e "preguiçoso".', 'ms'),
            _p('direcao', 'Direção', 0, 1, 0, 'Filtro sobe ou desce com a nota.',
               'Para cima (normal): nota forte abre o filtro. Para baixo: nota forte fecha o '
               'filtro, dando um som mais estranho e "de sintetizador".', '', 0,
               [(0, 'Para cima'), (1, 'Para baixo')]),
        ],
        'exemplos': [('Funk clássico', {'sens': 0.6, 'q': 7, 'resposta': 40, 'direcao': 0}),
                     ('Borrachudo', {'sens': 0.9, 'q': 10, 'resposta': 150, 'direcao': 0}),
                     ('Invertido', {'sens': 0.7, 'q': 7, 'resposta': 60, 'direcao': 1})],
    },

    # ===================================================================
    # MODULACAO
    # ===================================================================
    {
        'id': 'tremolo', 'grupo': 'modulacao', 'nome': 'Tremolo', 'cor': (60, 190, 190),
        'resumo': 'O volume sobe e desce sozinho, num ritmo constante.',
        'como_funciona': 'É o efeito de modulação mais simples: um oscilador lento (LFO) aumenta '
                         'e diminui o volume sem parar, como se alguém girasse o botão de volume. '
                         'Existe em amplificadores antigos (Fender) desde os anos 50.',
        'quando_usar': 'Surf music, country, rockabilly, baladas atmosféricas, e o picotado '
                       '"helicóptero" quando a onda é quadrada.',
        'dica': 'Use "Nota longa": a nota parada deixa o movimento de volume bem claro. Leve a '
                'Forma para 100% e o Rate alto para o som picotado.',
        'base': 'acorde',
        'parametros': [
            _p('rate', 'Rate (velocidade)', 0.5, 12, 5, 'Quantas vezes por segundo o volume oscila.',
               'Velocidade do LFO. Lento (1 a 3 Hz): ondas suaves. Rápido (8 Hz ou mais): '
               'pulsação intensa, quase um trêmulo de bandolim.', 'Hz', 1),
            _p('depth', 'Depth (profundidade)', 0, 1, 0.7, 'Quanto o volume cai.',
               'Distância entre o volume mais alto e o mais baixo. Pouco: só um balanço sutil. '
               'Máximo: o som some por completo a cada ciclo.'),
            _p('forma', 'Forma da onda', 0, 1, 0.1, 'Suave (senoide) ou picotado (quadrada).',
               'Formato da oscilação. Senoide: sobe e desce suave. Quadrada: liga e desliga '
               'seco, como alguém batendo no botão de mudo.'),
        ],
        'exemplos': [('Surf', {'rate': 6, 'depth': 0.6, 'forma': 0.1}),
                     ('Ondas lentas', {'rate': 1.5, 'depth': 0.8, 'forma': 0}),
                     ('Helicóptero', {'rate': 9, 'depth': 1, 'forma': 1})],
    },
    {
        'id': 'chorus', 'grupo': 'modulacao', 'nome': 'Chorus', 'cor': (100, 170, 250),
        'resumo': 'Parece que duas guitarras tocam juntas, levemente desafinadas.',
        'como_funciona': 'O pedal faz uma cópia do seu som com um atraso muito curto (uns 15 ms, '
                         'curto demais para ouvir como eco) e esse atraso fica variando devagar. '
                         'Isso desafina a cópia um tiquinho para cima e para baixo. Misturada '
                         'com o original, soa como um coro (daí o nome) e fica largo e brilhante.',
        'quando_usar': 'Limpos dos anos 80, baladas, arpejos, pop, deixar acordes mais "abertos". '
                       'Use fone: aqui o chorus é estéreo.',
        'dica': 'Com Depth alto e Rate alto o som fica "enjoado", quase desafinado: é o limite '
                'entre chorus e vibrato.',
        'base': 'acorde',
        'parametros': [
            _p('rate', 'Rate', 0.1, 4, 0.8, 'Velocidade do balanço.',
               'Quão rápido o atraso varia. Lento: movimento amplo e suave. Rápido: '
               'ondulação mais nervosa.', 'Hz', 1),
            _p('depth', 'Depth', 0, 1, 0.5, 'Quanto a cópia desafina.',
               'Tamanho da variação do atraso. Pouco: só um brilho a mais. Muito: '
               'desafinação evidente, som "aquático".'),
            _p('mix', 'Mix', 0, 1, 0.6, 'Quanto da cópia entra.',
               'Proporção entre o som original e a cópia modulada. É a quantidade de efeito.'),
        ],
        'exemplos': [('Sutil', {'rate': 0.5, 'depth': 0.3, 'mix': 0.4}),
                     ('Anos 80', {'rate': 0.9, 'depth': 0.65, 'mix': 0.7}),
                     ('Aquático', {'rate': 2.5, 'depth': 0.9, 'mix': 0.7})],
    },
    {
        'id': 'flanger', 'grupo': 'modulacao', 'nome': 'Flanger', 'cor': (150, 90, 230),
        'resumo': 'Um "avião a jato" passando pelo som.',
        'como_funciona': 'Parecido com o chorus, só que o atraso é ainda menor (1 a 5 ms) e parte '
                         'da saída volta para a entrada (realimentação). Somar o som com uma cópia '
                         'quase sem atraso cancela algumas frequências em série (filtro "pente"). '
                         'Como o atraso varia, esses cancelamentos sobem e descem: é o "vuuush".',
        'quando_usar': 'Rock dos anos 70 e 80, efeitos de transição, riffs com movimento.',
        'dica': 'Suba a Realimentação (Feedback): o efeito fica metálico e ressonante. Com o '
                'Rate bem lento você ouve o "avião" subir e descer claramente.',
        'base': 'power',
        'parametros': [
            _p('rate', 'Rate', 0.05, 2, 0.25, 'Velocidade da varredura.',
               'Quão rápido o "vuuush" sobe e desce. Flanger costuma ficar bem lento.', 'Hz', 2),
            _p('depth', 'Depth', 0, 1, 0.8, 'Tamanho da varredura.',
               'Quanto o atraso varia. Maior profundidade = o "avião" percorre mais frequências.'),
            _p('manual', 'Manual (atraso)', 0.5, 6, 2.5, 'Centro do atraso.',
               'Ponto de partida do atraso. Valores menores deixam os cancelamentos nos agudos; '
               'maiores levam o efeito para os médios e graves.', 'ms', 1),
            _p('feedback', 'Feedback (regen)', 0, 0.9, 0.6, 'Quanto a saída volta para a entrada.',
               'Mais realimentação = picos e vales mais fortes, som metálico e "robótico". '
               'Zero = flanger suave.'),
        ],
        'exemplos': [('Jato clássico', {'rate': 0.2, 'depth': 0.9, 'manual': 2.5, 'feedback': 0.6}),
                     ('Suave', {'rate': 0.4, 'depth': 0.6, 'manual': 3, 'feedback': 0.1}),
                     ('Metálico', {'rate': 0.15, 'depth': 0.8, 'manual': 1.2, 'feedback': 0.88})],
    },
    {
        'id': 'phaser', 'grupo': 'modulacao', 'nome': 'Phaser', 'cor': (240, 150, 50),
        'resumo': 'Um redemoinho suave que gira dentro do som.',
        'como_funciona': 'Em vez de atrasar o som inteiro, o phaser atrasa cada frequência um '
                         'pouco diferente (muda a "fase") com filtros chamados passa-tudo. Somado '
                         'ao original, isso cria alguns vales no timbre. O LFO move esses vales '
                         'para cima e para baixo, dando um movimento mais suave e musical que o '
                         'flanger.',
        'quando_usar': 'Funk, rock dos anos 70 (Van Halen), limpos com movimento, teclados.',
        'dica': 'Aumente os Estágios: 2 estágios dá um efeito leve; 8 estágios cria mais vales e '
                'um redemoinho mais intenso.',
        'base': 'acorde',
        'parametros': [
            _p('rate', 'Rate (speed)', 0.1, 6, 0.6, 'Velocidade do giro.',
               'Muitos phasers clássicos têm só esse botão. Lento: redemoinho largo. Rápido: '
               'quase um vibrato.', 'Hz', 1),
            _p('depth', 'Depth', 0, 1, 0.8, 'Quanto os vales se movem.',
               'Faixa de frequências percorrida pelo efeito.'),
            _p('estagios', 'Estágios', 2, 8, 4, 'Quantos filtros em série.',
               'Cada par de estágios cria um vale no timbre. Mais estágios = efeito mais '
               'denso e evidente.', '', 0, [(2, '2'), (4, '4'), (6, '6'), (8, '8')]),
            _p('mix', 'Mix', 0, 1, 1, 'Quantidade de efeito.',
               'Proporção do som processado. O efeito nasce da soma com o original, então no '
               'zero ele some por completo.'),
        ],
        'exemplos': [('Phase 90', {'rate': 0.5, 'depth': 0.8, 'estagios': 4, 'mix': 1}),
                     ('Leve', {'rate': 0.3, 'depth': 0.5, 'estagios': 2, 'mix': 0.7}),
                     ('Redemoinho', {'rate': 1.8, 'depth': 1, 'estagios': 8, 'mix': 1})],
    },
    {
        'id': 'vibrato', 'grupo': 'modulacao', 'nome': 'Vibrato', 'cor': (80, 200, 140),
        'resumo': 'A afinação oscila para cima e para baixo, como a mão de um violinista.',
        'como_funciona': 'Mesmo circuito do chorus, mas você ouve só a cópia com atraso variando, '
                         'sem o som original. Sem a referência do original, o ouvido percebe a '
                         'variação como mudança de afinação: a nota ondula.',
        'quando_usar': 'Sons antigos e "de fita", psicodelia, lo-fi, dar vida a notas longas.',
        'dica': 'Compare com o chorus: é o mesmo truque, só que 100% efeito. Depth alto soa como '
                'uma fita cassete gasta.',
        'base': 'nota',
        'parametros': [
            _p('rate', 'Rate', 0.5, 10, 5, 'Velocidade da oscilação.',
               'Quantas vezes por segundo a nota sobe e desce. Perto de 5 a 6 Hz lembra o vibrato '
               'de um cantor.', 'Hz', 1),
            _p('depth', 'Depth', 0, 1, 0.4, 'Quanto a afinação varia.',
               'Tamanho da oscilação de afinação. Pouco: vibrato sutil. Muito: som enjoado, '
               'de fita esticada.'),
        ],
        'exemplos': [('Cantor', {'rate': 5.5, 'depth': 0.3}),
                     ('Fita gasta', {'rate': 1.2, 'depth': 0.8}),
                     ('Nervoso', {'rate': 9, 'depth': 0.5})],
    },

    # ===================================================================
    # TEMPO E AMBIENCIA
    # ===================================================================
    {
        'id': 'delay', 'grupo': 'ambiencia', 'nome': 'Delay', 'cor': (60, 200, 110),
        'resumo': 'Repete o que você tocou, como um eco.',
        'como_funciona': 'O pedal grava o seu som e toca de volta depois de um tempo (Time). Parte '
                         'dessa repetição volta para a entrada e é repetida de novo (Feedback), '
                         'gerando vários ecos que vão sumindo. Em delays analógicos e de fita, '
                         'cada repetição fica mais escura que a anterior.',
        'quando_usar': 'Solos (dá tamanho), slapback do rockabilly, texturas no estilo U2 com '
                       'repetições no ritmo da música, ambientes.',
        'dica': 'Use "Notas soltas" e escute cada repetição. O loop está a 100 BPM: Time de 600 ms '
                'cai em cima de cada tempo e 450 ms é a colcheia pontuada.',
        'base': 'staccato',
        'parametros': [
            _p('time', 'Time', 50, 1200, 450, 'Tempo entre o som e a repetição.',
               'Curto (80 a 150 ms): slapback, uma "dobra" rápida. Médio (300 a 500 ms): o eco '
               'clássico de solo. Longo (700 ms ou mais): ecos bem separados, ambiente.', 'ms'),
            _p('feedback', 'Feedback (repeats)', 0, 0.9, 0.4, 'Quantas repetições.',
               'Quanto de cada repetição volta para ser repetida de novo. Zero: um eco só. Alto: '
               'muitos ecos, que se acumulam e demoram a sumir.'),
            _p('mix', 'Mix (level)', 0, 1, 0.45, 'Volume das repetições.',
               'Quão alto os ecos soam em relação ao som original. Baixo: só um "fundo". Alto: '
               'os ecos competem com a nota.'),
            _p('tom', 'Tone', 0, 1, 0.5, 'Digital (claro) ou analógico (escuro).',
               'Quanto cada repetição perde de agudo. No máximo, as repetições são idênticas '
               '(digital). Mais para baixo, cada eco fica mais escuro, como em fita e analógico.'),
        ],
        'exemplos': [('Slapback', {'time': 110, 'feedback': 0, 'mix': 0.5, 'tom': 0.6}),
                     ('Solo', {'time': 450, 'feedback': 0.35, 'mix': 0.4, 'tom': 0.5}),
                     ('Colcheia pontuada', {'time': 450, 'feedback': 0.55, 'mix': 0.55, 'tom': 0.9}),
                     ('Ambiente', {'time': 900, 'feedback': 0.75, 'mix': 0.6, 'tom': 0.2})],
    },
    {
        'id': 'reverb', 'grupo': 'ambiencia', 'nome': 'Reverb', 'cor': (130, 150, 255),
        'resumo': 'Coloca a guitarra dentro de uma sala, igreja ou caverna.',
        'como_funciona': 'Numa sala de verdade o som bate nas paredes milhares de vezes e chega '
                         'ao ouvido de todos os lados, formando uma "cauda" que vai sumindo. O '
                         'reverb simula isso: primeiro algumas reflexões rápidas e depois uma '
                         'nuvem densa de reflexões que decai. É diferente do delay porque você '
                         'não ouve ecos separados.',
        'quando_usar': 'Quase sempre um pouco: deixa o som menos "seco". Muito: ambientes, '
                       'post-rock, surf (reverb de mola).',
        'dica': 'Use "Notas soltas" e suba o Decay: a cauda enche o silêncio. O Pre-delay separa a '
                'nota da cauda e deixa a guitarra mais nítida mesmo com muito reverb.',
        'base': 'staccato',
        'parametros': [
            _p('decay', 'Decay', 0.3, 8, 2.5, 'Tamanho da sala.',
               'Tempo que a cauda leva para sumir. 0,5 s é um quarto; 2 s um salão; 6 s ou mais '
               'uma catedral.', 's', 1),
            _p('predelay', 'Pre-delay', 0, 150, 20, 'Espera antes da cauda.',
               'Tempo entre a nota e o começo do reverb. Salas grandes têm pre-delay maior porque '
               'as paredes estão mais longe. Ajuda a nota original a não se perder.', 'ms'),
            _p('tom', 'Tone', 0, 1, 0.5, 'Cauda escura ou brilhante.',
               'Paredes macias (cortinas) absorvem agudos: cauda escura. Paredes duras (pedra, '
               'azulejo): cauda brilhante.'),
            _p('mix', 'Mix', 0, 1, 0.35, 'Quanto de sala.',
               'Proporção entre o som direto e o reverb. Pouco: guitarra perto de você. Muito: '
               'guitarra longe, lá no fundo da sala.'),
        ],
        'exemplos': [('Quarto', {'decay': 0.6, 'predelay': 5, 'tom': 0.5, 'mix': 0.3}),
                     ('Salão', {'decay': 2.5, 'predelay': 25, 'tom': 0.5, 'mix': 0.4}),
                     ('Catedral', {'decay': 7, 'predelay': 60, 'tom': 0.35, 'mix': 0.6}),
                     ('Ambiente infinito', {'decay': 8, 'predelay': 100, 'tom': 0.7, 'mix': 0.85})],
    },

    # ===================================================================
    # PITCH E ESPECIAIS
    # ===================================================================
    {
        'id': 'octaver', 'grupo': 'pitch', 'nome': 'Octaver', 'cor': (200, 80, 70),
        'resumo': 'Acrescenta a mesma nota uma oitava abaixo e/ou acima.',
        'como_funciona': 'Oitava abaixo: o circuito conta os ciclos da nota e cria uma onda que '
                         'vira a cada dois ciclos, ou seja, com metade da frequência. Oitava '
                         'acima: "dobra" a onda (retificação), o que dobra a frequência. Por '
                         'isso os octavers analógicos funcionam bem com uma nota por vez e se '
                         'confundem com acordes.',
        'quando_usar': 'Engrossar riffs (parece baixo e guitarra juntos), solos com timbre de '
                       'órgão, e a oitava acima com fuzz no estilo Hendrix.',
        'dica': 'Troque para "Acordes" e ouça o octaver se perder: é o comportamento real dos '
                'pedais analógicos (os digitais modernos já lidam com acordes).',
        'base': 'riff',
        'parametros': [
            _p('sub', 'Oitava abaixo', 0, 1, 0.7, 'Volume da nota uma oitava mais grave.',
               'Mistura a voz grave gerada. Alto: parece que um baixista dobra a sua linha.'),
            _p('cima', 'Oitava acima', 0, 1, 0, 'Volume da nota uma oitava mais aguda.',
               'Mistura a voz aguda. Soa meio metálico e "de sino", ainda mais com distorção.'),
            _p('seco', 'Direto (dry)', 0, 1, 0.8, 'Volume do som original.',
               'Quanto do som sem efeito continua. No zero, você ouve só as oitavas geradas.'),
        ],
        'exemplos': [('Guitarra + baixo', {'sub': 0.8, 'cima': 0, 'seco': 0.8}),
                     ('Órgão', {'sub': 0.5, 'cima': 0.5, 'seco': 0.6}),
                     ('Só o sub', {'sub': 1, 'cima': 0, 'seco': 0})],
    },
    {
        'id': 'whammy', 'grupo': 'pitch', 'nome': 'Whammy', 'cor': (220, 40, 50),
        'resumo': 'Muda a afinação do som com o pé: sobe ou desce oitavas em tempo real.',
        'como_funciona': 'Um pitch shifter digital: o som é gravado em pedacinhos de poucos '
                         'milissegundos, que são lidos mais rápido (afinação sobe) ou mais '
                         'devagar (afinação desce) e emendados com fade. O pedal de expressão '
                         'escolhe quanto do intervalo é aplicado: calcanhar = afinação normal, '
                         'ponta do pé = intervalo completo. Por isso dá para "arrastar" a nota.',
        'quando_usar': 'Efeitos de "sirene" e subidas de oitava (Tom Morello, Jack White), '
                       'harmonias com a própria guitarra, afinar mais grave sem trocar as cordas.',
        'dica': 'Coloque Mix em 50% para ouvir o original junto com a nota deslocada (modo '
                'harmonia). Com Mix em 100% e o Movimento ligado, é o clássico "grito" do Whammy.',
        'base': 'riff',
        'parametros': [
            _p('intervalo', 'Intervalo', -24, 24, 12, 'Até onde a nota vai com o pé no fim.',
               'O quanto a afinação muda com o pedal todo à frente. +12 é uma oitava acima, '
               '-12 uma oitava abaixo, +7 é uma quinta (harmonia), -24 duas oitavas abaixo.', '', 0,
               [(-24, '-2 oitavas'), (-12, '-1 oitava'), (-7, '-5ª'), (-5, '-4ª'), (-2, '-1 tom'),
                (3, '+3ª menor'), (4, '+3ª maior'), (5, '+4ª'), (7, '+5ª'), (12, '+1 oitava'),
                (24, '+2 oitavas')]),
            _p('pedal', 'Pedal (posição)', 0, 1, 1, 'Onde está o seu pé.',
               'Com o Movimento em zero, é a posição fixa do pedal: 0% não muda nada, 50% aplica '
               'metade do intervalo, 100% o intervalo inteiro. Com o Movimento ligado, vira o '
               'limite até onde o pé automático vai.'),
            _p('movimento', 'Movimento (auto)', 0, 2, 0, 'Pé automático indo e voltando.',
               'Simula o pé varrendo o pedal. 0 = parado. Valores baixos fazem uma subida e '
               'descida lenta, como uma sirene.', 'Hz', 2),
            _p('mix', 'Mix', 0, 1, 1, 'Só efeito ou efeito + original.',
               '100% é o modo "Whammy" (só a nota deslocada). Em 50% você ouve as duas: é o '
               'modo "Harmony", que faz uma segunda voz.'),
        ],
        'exemplos': [('Oitava acima', {'intervalo': 12, 'pedal': 1, 'movimento': 0, 'mix': 1}),
                     ('Sirene', {'intervalo': 12, 'pedal': 1, 'movimento': 0.5, 'mix': 1}),
                     ('Harmonia em quinta', {'intervalo': 7, 'pedal': 1, 'movimento': 0, 'mix': 0.5}),
                     ('Drop grave', {'intervalo': -12, 'pedal': 1, 'movimento': 0, 'mix': 1})],
    },
    {
        'id': 'ring', 'grupo': 'pitch', 'nome': 'Ring Modulator', 'cor': (160, 170, 60),
        'resumo': 'Som metálico de sino ou robô, fora de qualquer afinação.',
        'como_funciona': 'Multiplica o som da guitarra por uma onda gerada pelo pedal (portadora). '
                         'O resultado não tem mais as notas originais, e sim a soma e a diferença '
                         'entre elas e a portadora. Essas frequências não seguem a escala, por '
                         'isso o som fica metálico, de sino ou de voz robótica.',
        'quando_usar': 'Efeitos especiais, rock experimental, sons de ficção científica. Em '
                       'frequências bem baixas lembra um tremolo.',
        'dica': 'Leve a Frequência para perto de 20 a 30 Hz: vira um tremolo esquisito. Acima de '
                '300 Hz o som vira um sino desafinado.',
        'base': 'riff',
        'parametros': [
            _p('freq', 'Frequência', 20, 2000, 440, 'Frequência da portadora.',
               'A "nota" da onda interna do pedal. Baixa: pulsação. Média: timbre de sino. Alta: '
               'agudos metálicos e ásperos.', 'Hz'),
            _p('mix', 'Mix', 0, 1, 0.8, 'Quantidade de efeito.',
               'Proporção entre o som original e o som modulado.'),
        ],
        'exemplos': [('Sino', {'freq': 420, 'mix': 0.8}),
                     ('Robô', {'freq': 110, 'mix': 1}),
                     ('Tremolo estranho', {'freq': 25, 'mix': 1})],
    },
]

PEDAIS_POR_ID = {p['id']: p for p in PEDAIS}


def pedais_do_grupo(id_grupo):
    return [p for p in PEDAIS if p['grupo'] == id_grupo]


def valores_padrao(pedal):
    return {par['id']: par['padrao'] for par in pedal['parametros']}


INTRODUCAO = ('Um pedal recebe o sinal da guitarra, transforma e manda adiante para o próximo '
              'pedal ou para o amplificador. Escolha um pedal para ouvir o antes e o depois, '
              'mexer em cada botão e entender o que ele faz. A ordem vai do mais simples ao '
              'mais complexo.')

CADEIA_SUGERIDA = ['Afinador', 'Wah / Filtro', 'Compressor', 'Overdrive / Distorção', 'EQ',
                   'Modulação', 'Delay', 'Reverb']
