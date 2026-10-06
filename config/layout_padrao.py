# -*- coding: utf-8 -*-
"""
Layout padrao do EIGUIT Studio, derivado do canvas de design.

As posicoes sao guardadas como fracoes da area util (largura da tela x altura
do viewport, ja descontada a barra superior), medidas sobre o artboard de
1920x1080. Assim o mesmo arranjo abre corretamente em qualquer resolucao.

Cada bloco tem tambem um tamanho minimo, para que em telas pequenas os paineis
continuem utilizaveis em vez de colapsar.
"""

# Faixa reservada na esquerda para a coluna do gaveteiro fechada, para
# nenhum bloco abrir por baixo dela
MARGEM_ESQUERDA = 48
MARGEM_DIREITA = 10

# Respiro entre os controles do topo e o braco, e entre o braco e a barra
ESPACO_ENTRE_FIXOS = 16
MARGEM_INFERIOR = 10
# Respiro entre a barra superior e os controles do topo do workspace
MARGEM_TOPO = 10

# Referencia do canvas
LARGURA_REF = 1920
ALTURA_REF = 1040  # 1080 menos a barra superior de 40

# nome -> (x, y, largura, altura) em pixels do canvas de referencia
BLOCOS_REF = {
    'dragger_controles_topo': (40, 20, 700, 64),
    'dragger_guitarra': (40, 96, 1180, 264),
    'dragger_cores': (1560, 20, 320, 150),
    'dragger_nota_atual': (1250, 190, 630, 300),
    'dragger_acordes': (40, 376, 1180, 132),
    # Faixa livre acima do painel inferior, que sobe 280px quando abre
    'dragger_circulo': (40, 508, 214, 168),
    'dragger_historico': (266, 520, 340, 144),
    'dragger_ideias': (618, 520, 232, 144),
    'dragger_graus': (862, 508, 356, 156),
    'dragger_drone': (40, 684, 296, 156),
    'dragger_progressoes': (352, 684, 434, 196),
    'dragger_capo': (862, 684, 356, 120),
    # Logo abaixo do braco: o arrasto ate ele fica curto
    'dragger_paleta_acordes': (400, 372, 620, 196),
    'dragger_metronomo': (1250, 510, 330, 340),
    'dragger_sessao': (1600, 510, 280, 180),
    'dragger_cordas': (1600, 700, 280, 150),
    'dragger_painel_inferior': (40, 960, 1840, 40),
}

# Tamanhos minimos para telas menores (largura, altura)
MINIMOS = {
    'dragger_controles_topo': (420, 56),
    'dragger_guitarra': (520, 160),
    'dragger_cores': (170, 120),
    'dragger_nota_atual': (280, 200),
    'dragger_acordes': (420, 110),
    'dragger_circulo': (150, 120),
    'dragger_historico': (220, 100),
    'dragger_ideias': (170, 96),
    'dragger_graus': (230, 110),
    'dragger_drone': (180, 120),
    'dragger_progressoes': (240, 120),
    'dragger_capo': (190, 96),
    'dragger_paleta_acordes': (260, 130),
    'dragger_metronomo': (240, 104),
    'dragger_sessao': (200, 130),
    'dragger_cordas': (180, 100),
    'dragger_painel_inferior': (600, 38),
}


def calcular(largura_tela, altura_viewport):
    """
        Como funciona: Converte o layout de referencia em pixels da tela atual,
        respeitando os tamanhos minimos e mantendo tudo dentro da area visivel.
        Para que serve: Abrir sempre no arranjo do canvas, em qualquer monitor.
        Onde e usada: EstadoGlobal.__init__ e 'Voltar para o Padrao' do perfil.
    """
    escala_x = largura_tela / LARGURA_REF
    escala_y = max(0.45, altura_viewport / ALTURA_REF)

    layout = {}
    for nome, (x, y, w, h) in BLOCOS_REF.items():
        min_w, min_h = MINIMOS[nome]
        nova_w = max(min_w, int(w * escala_x))
        nova_h = max(min_h, int(h * escala_y))
        nova_x = int(x * escala_x)
        nova_y = int(y * escala_y)

        # Mantem o bloco inteiro dentro da area util, ja descontada a faixa
        # que a coluna do gaveteiro ocupa na esquerda
        nova_w = min(nova_w, max(min_w, largura_tela - MARGEM_ESQUERDA - 10))
        nova_h = min(nova_h, max(min_h, altura_viewport - 20))
        nova_x = max(MARGEM_ESQUERDA, min(nova_x, largura_tela - nova_w - 10))
        nova_y = max(10, min(nova_y, altura_viewport - nova_h - 10))

        layout[nome] = {'x': nova_x, 'y': nova_y, 'w': nova_w, 'h': nova_h}

    _centralizar_fixos(layout, largura_tela, altura_viewport)
    return layout


def _centralizar_fixos(layout, largura_tela, altura_viewport):
    """
        Como funciona: A barra de abas vai para o rodape, ocupando a largura
        toda menos a faixa da coluna. Os controles do topo e o braco ficam
        centrados na horizontal e encostados no topo da area util, um logo
        abaixo do outro.
        Para que serve: A gaveta de baixo abre por cima de mais da metade da
        tela; com o braco no topo ele continua a vista enquanto se escolhe uma
        forma de escala para arrastar ate ele.
        Onde e usada: Fim de calcular(), entao vale na abertura e no 'Voltar
        para o Padrao'.
    """
    esquerda = MARGEM_ESQUERDA
    util = max(120, largura_tela - esquerda - MARGEM_DIREITA)

    barra = layout.get('dragger_painel_inferior')
    if barra is not None:
        barra['x'] = esquerda
        barra['w'] = util
        barra['y'] = max(0, altura_viewport - barra['h'] - MARGEM_INFERIOR)

    topo = layout.get('dragger_controles_topo')
    braco = layout.get('dragger_guitarra')
    if topo is None or braco is None:
        return

    for medidas in (topo, braco):
        medidas['w'] = min(medidas['w'], util)
        medidas['x'] = esquerda + (util - medidas['w']) // 2

    # Encostados no topo, na ordem controles -> braco. Se a tela for tao baixa
    # que o grupo nao caiba acima da barra, os dois encolhem em vez de descer.
    limite = barra['y'] if barra is not None else altura_viewport
    topo['y'] = MARGEM_TOPO
    braco['y'] = topo['y'] + topo['h'] + ESPACO_ENTRE_FIXOS
    sobra = braco['y'] + braco['h'] - (limite - MARGEM_INFERIOR)
    if sobra > 0:
        braco['h'] = max(MINIMOS['dragger_guitarra'][1], braco['h'] - sobra)
    return layout


def aplicar(estado, largura_tela=None, altura_viewport=None):
    """
        Como funciona: Reposiciona e redimensiona os draggers ja existentes em
        estado para o layout padrao.
        Para que serve: Restaurar o arranjo do canvas sem recriar o estado.
        Onde e usada: 'Voltar para o Padrao' e na inicializacao.
    """
    from config.ui_metrics import ALTURA_TOPBAR

    largura_tela = largura_tela or estado.LARGURA_TELA
    if altura_viewport is None:
        altura_viewport = max(600, estado.ALTURA_TELA - ALTURA_TOPBAR)

    layout = calcular(largura_tela, altura_viewport)
    for nome, medidas in layout.items():
        alvo = getattr(estado, nome, None)
        if alvo is None:
            continue
        alvo.x, alvo.y = medidas['x'], medidas['y']
        alvo.largura, alvo.altura = medidas['w'], medidas['h']

    # O braco tem medidas proprias que alimentam o calculo das casas e cordas
    braco = layout['dragger_guitarra']
    estado.LARGURA_BRACO = braco['w']
    estado.ALTURA_BRACO = braco['h']
    estado.ALTURA_ACORDES = layout['dragger_acordes']['h']
    if hasattr(estado, 'atualizar_medidas'):
        estado.atualizar_medidas()
    return layout
