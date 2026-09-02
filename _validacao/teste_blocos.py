# -*- coding: utf-8 -*-
"""
Suite dos blocos extras do workspace.

Cobre tres coisas, para cada bloco e em tres tamanhos (150x120, 230x150 e
360x200), nos dois temas:

1. Valores: o que o bloco calcula bate com a teoria musical.
2. Limites: nada e pintado fora do retangulo do bloco. A prova e desenhar duas
   vezes, uma com o conteudo e outra so com a moldura, e comparar tudo o que
   esta fora do bloco; a sombra do painel e igual nas duas e nao acusa.
3. Cliques: todo retangulo guardado no desenho cai dentro do bloco e responde
   ao clique com a acao esperada, e um bloco pequeno demais nao deixa
   retangulo nenhum para tras.
"""
import pygame

import harness
from harness import Contexto, Suite

import config.design_system as design
from config.design_system import TEMA
import ui.components.blocos_extras as bx

TAMANHOS = [(150, 120), (230, 150), (360, 200)]
POSICAO = (40, 40)
SUPERFICIE = (600, 400)

# nome do bloco -> acao que tratar_clique_blocos devolve ao clicar nele
ACOES = {'circulo': 'tonalidade', 'historico': 'historico', 'ideias': 'ideia',
         'graus': 'grau', 'drone': 'drone', 'cordas': 'corda',
         'capo': 'capo', 'progressoes': 'progressao'}

LISTAS_DE_RECTS = {
    'circulo': ['rects_circulo'],
    'historico': ['rect_btn_limpar_historico'],
    'ideias': ['rect_btn_gravar_ideia'],
    'graus': ['rects_graus'],
    'drone': ['rects_drone', 'rect_btn_drone'],
    'cordas': ['rects_cordas'],
    'capo': ['rects_capo'],
    'progressoes': ['rects_progressoes'],
}

s = Suite('teste_blocos')


def _preparar(ctx):
    """Estado com conteudo em todos os blocos, para nada desenhar vazio."""
    # Os blocos nascem guardados no gaveteiro; aqui eles precisam estar na tela
    ctx.estado.blocos_guardados = set()
    ctx.estado.historico_notas = ['C', 'D', 'F#', 'A', 'C', 'E', 'G', 'A#']
    ctx.estado.ideias_recentes = ['Ideias/ideia_2026-09-01_10-00-00.wav',
                                  'Ideias/ideia_2026-09-01_09-00-00.wav']
    ctx.estado.drag_ativado = False
    return ctx


def _zerar_rects(estado):
    """Apaga os alvos de todos os blocos, como acontece a cada quadro real."""
    for atributos in LISTAS_DE_RECTS.values():
        for atributo in atributos:
            valor = getattr(estado, atributo, None)
            if isinstance(valor, pygame.Rect):
                setattr(estado, atributo, pygame.Rect(0, 0, 0, 0))
            else:
                setattr(estado, atributo, [])


def _desenhar(ctx, nome, tamanho, tela):
    """Desenha um bloco no tamanho pedido e devolve (rect, argumentos_do_painel)."""
    _zerar_rects(ctx.estado)
    rect = ctx.redimensionar_bloco(nome, tamanho[0], tamanho[1], *POSICAO)
    desenhar = dict(bx.BLOCOS_EXTRAS)[nome]
    capturado = []
    original = design.painel

    def espiao(tela_alvo, rect_p, titulo=None, fonte=None, **kw):
        capturado.append((pygame.Rect(rect_p), titulo, fonte, kw))
        return original(tela_alvo, rect_p, titulo, fonte, **kw)

    design.painel = espiao
    try:
        if nome == 'ideias':
            desenhar(tela, ctx.estado, ctx.fontes, ctx.configs, None)
        else:
            desenhar(tela, ctx.estado, ctx.fontes, ctx.configs, ctx.campo)
    finally:
        design.painel = original
    return rect, capturado


def _rects_do_bloco(estado, nome):
    """Os retangulos clicaveis que o bloco guardou, como lista de (rect, valor)."""
    saida = []
    for atributo in LISTAS_DE_RECTS[nome]:
        valor = getattr(estado, atributo, None)
        if isinstance(valor, pygame.Rect):
            if valor.width > 0 and valor.height > 0:
                saida.append((valor, None))
        else:
            saida.extend(valor or [])
    return saida


# ---------------------------------------------------------------------------
# 1. VALORES
# ---------------------------------------------------------------------------

def valores_do_ciclo():
    s.checar(bx.vizinhas_da_tonalidade('C') == ('F', 'G'), 'IV e V de C')
    s.checar(bx.vizinhas_da_tonalidade('F') == ('A#', 'C'), 'IV e V de F')
    s.checar(bx.relativa_de('C') == 'Am' and bx.relativa_de('G') == 'Em',
             'relativas menores')
    s.checar(bx.armadura_de('C') == '-' and bx.armadura_de('D') == '2#'
             and bx.armadura_de('F') == '1b', 'armaduras')
    s.checar(len(set(bx.CICLO)) == 12 and len(bx.RELATIVAS) == 12
             and len(bx.ARMADURAS) == 12, 'ciclo com doze tonalidades')


def valores_de_intervalo():
    s.checar(bx.intervalo_entre('C', 'E') == '3M', 'C -> E e terca maior')
    s.checar(bx.intervalo_entre('C', 'G') == '5J', 'C -> G e quinta justa')
    s.checar(bx.intervalo_entre('E', 'C') == '6m', 'E -> C e sexta menor')
    s.checar(bx.direcao_entre('C', 'E') == '^', 'C -> E sobe')
    s.checar(bx.direcao_entre('C', 'A') == 'v', 'C -> A desce')
    s.checar(bx.direcao_entre('C', 'C') == '', 'mesma nota nao tem direcao')


def valores_de_tonalidade():
    s.checar(bx.notas_da_tonalidade('C') == ['C', 'D', 'E', 'F', 'G', 'A', 'B'],
             'escala de C')
    s.checar(bx.notas_da_tonalidade('G')[-1] == 'F#', 'G maior tem F#')
    total, fora = bx.resumo_historico(['C', 'F#', 'D'], 'C')
    s.checar((total, fora) == (3, 1), 'F# esta fora de C')


def valores_do_campo():
    cifras = [c for _a, c, _n, _t in bx.campo_da_tonalidade('C')]
    s.checar(cifras == ['C', 'Dm', 'Em', 'F', 'G', 'Am', 'Bdim'],
             f'campo de C maior: {cifras}')
    giro = [c for _a, c, _n, _t in bx.acordes_da_progressao('C', [0, 4, 5, 3])]
    s.checar(giro == ['C', 'G', 'Am', 'F'], f'giro pop em C: {giro}')


def valores_do_capo():
    s.checar(bx.forma_com_capo('C', 0) == 'C', 'sem capo a forma e a tonalidade')
    s.checar(bx.forma_com_capo('F', 1) == 'E', 'F com capo na 1a e forma de E')
    s.checar(bx.forma_com_capo('D', 2) == 'C', 'D com capo na 2a e forma de C')


def valores_de_frequencia():
    s.checar(abs(bx.frequencia_da_nota('A', 4) - 440.0) < 0.01, 'La 4 = 440 Hz')
    s.checar(abs(bx.frequencia_da_nota('A', 3) - 220.0) < 0.01, 'La 3 = 220 Hz')


def valores_das_cordas():
    ctx = Contexto()
    ctx.estado.indice_afinacao = 0
    ctx.estado.instrumento = 'guitarra'
    nome, cordas = bx.afinacao_atual(ctx.estado)
    s.checar(len(cordas) == ctx.estado.NUM_CORDAS,
             f'{len(cordas)} cordas para NUM_CORDAS={ctx.estado.NUM_CORDAS}')
    ctx.estado.instrumento = 'baixo'
    _nome, cordas_baixo = bx.afinacao_atual(ctx.estado)
    s.checar(len(cordas_baixo) == 4, 'o baixo mostra quatro cordas')


def historico_ignora_repeticao():
    ctx = Contexto()
    ctx.estado.historico_notas = []
    for nota in ['C', 'C', 'C', '--', 'C', 'D']:
        bx.registrar_nota_historico(ctx.estado, nota)
    s.checar(ctx.estado.historico_notas == ['C', 'C', 'D'],
             f'silencio separa repeticoes: {ctx.estado.historico_notas}')
    for _ in range(30):
        bx.registrar_nota_historico(ctx.estado, 'E')
        bx.registrar_nota_historico(ctx.estado, 'G')
    s.checar(len(ctx.estado.historico_notas) == bx.MAX_HISTORICO,
             'o historico para nas ultimas doze')


s.teste('ciclo das quintas: IV, V, relativa e armadura', valores_do_ciclo)
s.teste('intervalos e direcao entre notas', valores_de_intervalo)
s.teste('notas da tonalidade e contagem de notas de fora', valores_de_tonalidade)
s.teste('campo harmonico e giros', valores_do_campo)
s.teste('capotraste: forma que se toca', valores_do_capo)
s.teste('frequencias do drone', valores_de_frequencia)
s.teste('cordas soltas seguem a afinacao e o instrumento', valores_das_cordas)
s.teste('historico de notas', historico_ignora_repeticao)


# ---------------------------------------------------------------------------
# 2. LIMITES E 3. CLIQUES, POR BLOCO / TAMANHO / TEMA
# ---------------------------------------------------------------------------

for tema in harness.TEMAS:
    ctx = _preparar(Contexto(tema=tema))
    for nome, _fn in bx.BLOCOS_EXTRAS:
        for tamanho in TAMANHOS:

            def limites(nome=nome, tamanho=tamanho, ctx=ctx):
                tela = pygame.Surface(SUPERFICIE, pygame.SRCALPHA)
                tela.fill((0, 0, 0, 0))
                rect, capturado = _desenhar(ctx, nome, tamanho, tela)
                s.checar(capturado, 'o bloco desenhou a moldura')

                base = pygame.Surface(SUPERFICIE, pygame.SRCALPHA)
                base.fill((0, 0, 0, 0))
                for rect_p, titulo, fonte, kw in capturado:
                    design.painel(base, rect_p, titulo, fonte, **kw)

                fora = []
                for y in range(SUPERFICIE[1]):
                    for x in range(SUPERFICIE[0]):
                        if rect.collidepoint(x, y):
                            continue
                        if tela.get_at((x, y)) != base.get_at((x, y)):
                            fora.append((x, y))
                            if len(fora) > 5:
                                break
                    if len(fora) > 5:
                        break
                s.checar(not fora,
                         f'conteudo pintado fora do bloco em {fora[:5]}')

            def cliques(nome=nome, tamanho=tamanho, ctx=ctx):
                tela = pygame.Surface(SUPERFICIE, pygame.SRCALPHA)
                rect, _cap = _desenhar(ctx, nome, tamanho, tela)
                guardados = _rects_do_bloco(ctx.estado, nome)
                for r, _valor in guardados:
                    s.checar(rect.contains(r),
                             f'retangulo clicavel {r} fora do bloco {rect}')
                    acao = bx.tratar_clique_blocos(ctx.estado, r.center,
                                                  ctx.campo, None)
                    s.checar(acao == ACOES[nome],
                             f'clique em {r.center} devolveu {acao}')
                    # redesenha: a acao pode ter mudado o conteudo do bloco
                    _desenhar(ctx, nome, tamanho, tela)

            s.teste(f'[{tema}] {nome} {tamanho[0]}x{tamanho[1]}: nada fora dos limites',
                    limites)
            s.teste(f'[{tema}] {nome} {tamanho[0]}x{tamanho[1]}: rects clicaveis',
                    cliques)


# ---------------------------------------------------------------------------
# 3b. NENHUM BLOCO FICA VAZIO NOS TAMANHOS DE TESTE
# ---------------------------------------------------------------------------

# quantos alvos cada bloco tem de oferecer nos tres tamanhos, do menor ao maior
MINIMO_DE_ALVOS = {
    'circulo': (12, 12, 12),     # as doze tonalidades, em qualquer tamanho
    'historico': (1, 1, 1),      # o botao de limpar
    'ideias': (1, 1, 1),         # o botao de gravar
    'graus': (7, 7, 7),          # os sete graus do campo
    'drone': (2, 12, 12),        # no menor, o seletor com as duas setas
    'cordas': (6, 6, 6),         # as cordas da afinacao
    'capo': (8, 8, 8),           # as casas 0 a 7
    'progressoes': (2, 4, 4),    # os giros que couberem
}


def nao_fica_vazio(nome, indice, tamanho, ctx):
    tela = pygame.Surface(SUPERFICIE, pygame.SRCALPHA)
    _desenhar(ctx, nome, tamanho, tela)
    alvos = len(_rects_do_bloco(ctx.estado, nome))
    esperado = MINIMO_DE_ALVOS[nome][indice]
    s.checar(alvos >= esperado,
             f'{nome} em {tamanho[0]}x{tamanho[1]}: {alvos} alvos, '
             f'esperado ao menos {esperado}')


for _tema in harness.TEMAS:
    ctx = _preparar(Contexto(tema=_tema))
    for nome, _fn in bx.BLOCOS_EXTRAS:
        for _i, _tamanho in enumerate(TAMANHOS):
            s.teste(f'[{_tema}] {nome} {_tamanho[0]}x{_tamanho[1]}: nao fica vazio',
                    lambda n=nome, i=_i, t=_tamanho, c=ctx: nao_fica_vazio(n, i, t, c))


# ---------------------------------------------------------------------------
# 4. EFEITOS DOS CLIQUES
# ---------------------------------------------------------------------------

def clique_no_ciclo_troca_tonalidade():
    ctx = _preparar(Contexto())
    tela = pygame.Surface(SUPERFICIE, pygame.SRCALPHA)
    _desenhar(ctx, 'circulo', (360, 200), tela)
    alvo = [(r, n) for r, n in ctx.estado.rects_circulo if n == 'G'][0]
    s.checar(bx.tratar_clique_blocos(ctx.estado, alvo[0].center, ctx.campo, None)
             == 'tonalidade', 'clique no ciclo')
    s.checar(ctx.estado.tom_atual == 'G' and ctx.campo.tonica_campo == 'G',
             'a tonalidade virou G no estado e no campo harmonico')


def clique_no_grau_poe_acorde_no_braco():
    ctx = _preparar(Contexto())
    ctx.campo.tonica_campo = 'C'
    tela = pygame.Surface(SUPERFICIE, pygame.SRCALPHA)
    _desenhar(ctx, 'graus', (360, 200), tela)
    rect, indice = ctx.estado.rects_graus[4]        # o quinto grau, G
    bx.tratar_clique_blocos(ctx.estado, rect.center, ctx.campo, None)
    s.checar(ctx.estado.acordes_no_braco, 'o acorde entrou no braco')
    s.checar(ctx.estado.acordes_no_braco[-1]['rotulo'] == 'G',
             f"o quinto grau de C e G, veio {ctx.estado.acordes_no_braco[-1]['rotulo']}")
    bx.tratar_clique_blocos(ctx.estado, rect.center, ctx.campo, None)
    s.checar(not ctx.estado.acordes_no_braco, 'o mesmo clique tira o acorde')


def clique_na_progressao_fixa_o_giro():
    ctx = _preparar(Contexto())
    ctx.campo.tonica_campo = 'C'
    tela = pygame.Surface(SUPERFICIE, pygame.SRCALPHA)
    _desenhar(ctx, 'progressoes', (360, 200), tela)
    rect, _i = ctx.estado.rects_progressoes[0]
    bx.tratar_clique_blocos(ctx.estado, rect.center, ctx.campo, None)
    rotulos = [a['rotulo'] for a in ctx.estado.acordes_no_braco]
    s.checar(rotulos == ['C', 'G', 'Am', 'F'], f'giro pop no braco: {rotulos}')
    bx.tratar_clique_blocos(ctx.estado, rect.center, ctx.campo, None)
    s.checar(not ctx.estado.acordes_no_braco, 'o mesmo clique limpa o giro')


def clique_no_capo_e_nas_cordas():
    ctx = _preparar(Contexto())
    tela = pygame.Surface(SUPERFICIE, pygame.SRCALPHA)
    _desenhar(ctx, 'capo', (360, 200), tela)
    rect, casa = ctx.estado.rects_capo[2]
    bx.tratar_clique_blocos(ctx.estado, rect.center, ctx.campo, None)
    s.checar(ctx.estado.capo_casa == casa, 'a casa do capo mudou')
    bx.tratar_clique_blocos(ctx.estado, rect.center, ctx.campo, None)
    s.checar(ctx.estado.capo_casa == 0, 'clicar de novo tira o capo')

    _desenhar(ctx, 'cordas', (360, 200), tela)
    rect, nota = ctx.estado.rects_cordas[0]
    bx.tratar_clique_blocos(ctx.estado, rect.center, ctx.campo, None)
    s.checar(ctx.estado.drone_nota == nota,
             'a corda escolheu a nota de referencia')


def limpar_historico_pelo_botao():
    ctx = _preparar(Contexto())
    tela = pygame.Surface(SUPERFICIE, pygame.SRCALPHA)
    _desenhar(ctx, 'historico', (360, 200), tela)
    botao = ctx.estado.rect_btn_limpar_historico
    s.checar(botao.width > 0, 'o botao de limpar aparece quando ha notas')
    bx.tratar_clique_blocos(ctx.estado, botao.center, ctx.campo, None)
    s.checar(ctx.estado.historico_notas == [], 'o historico foi limpo')


def bloco_minusculo_nao_deixa_alvo():
    ctx = _preparar(Contexto())
    tela = pygame.Surface(SUPERFICIE, pygame.SRCALPHA)
    for nome, _fn in bx.BLOCOS_EXTRAS:
        _desenhar(ctx, nome, (50, 34), tela)
        for r, _v in _rects_do_bloco(ctx.estado, nome):
            raise AssertionError(f'{nome} guardou alvo {r} num bloco de 50x34')


def sem_motor_de_audio_nao_quebra():
    ctx = _preparar(Contexto())
    tela = pygame.Surface(SUPERFICIE, pygame.SRCALPHA)
    _desenhar(ctx, 'ideias', (360, 200), tela)
    botao = ctx.estado.rect_btn_gravar_ideia
    s.checar(bx.tratar_clique_blocos(ctx.estado, botao.center, ctx.campo, None)
             == 'ideia', 'o botao de gravar responde sem motor de audio')
    # Sem mixer (maquina sem placa de som) o drone avisa em vez de quebrar
    pygame.mixer.quit()
    bx._cache_drone.clear()
    try:
        s.checar(bx.alternar_drone(ctx.estado, 'E') is False,
                 'o drone avisa que nao conseguiu soar, em vez de quebrar')
        s.checar(ctx.estado.drone_ativo is False, 'e nao fica ligado no vazio')
        s.checar(ctx.estado.drone_nota == 'E', 'mas a nota escolhida fica guardada')
        _desenhar(ctx, 'drone', (230, 150), tela)
    finally:
        try:
            pygame.mixer.init()
        except pygame.error:
            pass


s.teste('clique no ciclo troca a tonalidade', clique_no_ciclo_troca_tonalidade)
s.teste('clique no grau poe o acorde no braco', clique_no_grau_poe_acorde_no_braco)
s.teste('clique na progressao fixa o giro', clique_na_progressao_fixa_o_giro)
s.teste('cliques no capotraste e nas cordas', clique_no_capo_e_nas_cordas)
s.teste('botao de limpar o historico', limpar_historico_pelo_botao)
s.teste('bloco pequeno demais nao deixa alvo clicavel', bloco_minusculo_nao_deixa_alvo)
s.teste('blocos funcionam sem motor de audio', sem_motor_de_audio_nao_quebra)

# ---------------------------------------------------------------------------
# 5. GAVETEIRO LATERAL
# ---------------------------------------------------------------------------

from ui.components import gaveteiro as gv          # noqa: E402
from ui import renderizador_ui                     # noqa: E402

TELA_CHEIA = (1920, 1040)


def _workspace(ctx):
    """Desenha um quadro inteiro do workspace e devolve a superficie."""
    tela = pygame.Surface(TELA_CHEIA, pygame.SRCALPHA)
    renderizador_ui.desenhar_workspace(
        tela, ctx.estado, ctx.configs, ctx.escalas, ctx.fontes, ctx.metronomo,
        ctx.processador, ctx.gravador, ctx.campo, ctx.jogos)
    return tela


def _abrir_coluna(ctx):
    """Deixa a coluna aberta, como depois de o mouse parar em cima dela."""
    ctx.estado.mouse_workspace = (8, 300)
    for _ in range(40):
        gv.atualizar(ctx.estado, TELA_CHEIA[1])
    return _workspace(ctx)


def tudo_comeca_guardado():
    ctx = Contexto()
    s.checar(set(ctx.estado.blocos_guardados) == set(gv.NOMES),
             'todo bloco do gaveteiro comeca guardado')
    for nome in gv.NOMES:
        s.checar(not gv.visivel(ctx.estado, nome), f'{nome} deveria estar guardado')
    s.checar(gv.visivel(ctx.estado, 'dragger_guitarra'),
             'o braco nao entra no gaveteiro')
    s.checar(gv.visivel(ctx.estado, 'dragger_painel_inferior'),
             'a barra de abas nao entra no gaveteiro')
    s.checar(gv.visivel(ctx.estado, 'dragger_controles_topo'),
             'os controles do topo nao entram no gaveteiro')


def bloco_guardado_nao_deixa_alvo():
    ctx = Contexto()
    _workspace(ctx)
    for nome, _fn in bx.BLOCOS_EXTRAS:
        alvos = _rects_do_bloco(ctx.estado, nome)
        s.checar(not alvos, f'{nome} guardado ainda deixou alvo {alvos[:1]}')


def coluna_abre_no_hover_e_fecha():
    ctx = Contexto()
    _workspace(ctx)
    s.checar(gv.largura_atual(ctx.estado) == gv.LARGURA_FECHADO,
             'a coluna comeca fechada')
    _abrir_coluna(ctx)
    s.checar(gv.largura_atual(ctx.estado) == gv.LARGURA_ABERTO,
             'a coluna abre com o mouse em cima')
    ctx.estado.mouse_workspace = (900, 500)
    for _ in range(40):
        gv.atualizar(ctx.estado, TELA_CHEIA[1])
    s.checar(gv.largura_atual(ctx.estado) == gv.LARGURA_FECHADO,
             'a coluna fecha quando o mouse sai')


def gavetas_dentro_da_coluna():
    ctx = Contexto()
    _abrir_coluna(ctx)
    s.checar(len(ctx.estado.rects_gavetas) == len(gv.GAVETAS),
             f'{len(ctx.estado.rects_gavetas)} gavetas desenhadas')
    coluna = pygame.Rect(0, 0, gv.largura_atual(ctx.estado), TELA_CHEIA[1])
    vistos = []
    for rect, nome in ctx.estado.rects_gavetas:
        s.checar(coluna.contains(rect), f'gaveta {nome} fora da coluna: {rect}')
        for outro in vistos:
            s.checar(not rect.colliderect(outro), f'gavetas sobrepostas em {nome}')
        vistos.append(rect)


def clique_tira_e_guarda():
    ctx = Contexto()
    _abrir_coluna(ctx)
    for rect, nome in list(ctx.estado.rects_gavetas):
        clique = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                    {'pos': rect.center, 'button': 1})
        s.checar(gv.tratar_evento(ctx.estado, clique), f'clique na gaveta {nome}')
        s.checar(gv.visivel(ctx.estado, nome), f'{nome} deveria ter saido')
        bloco = getattr(ctx.estado, nome)
        s.checar(bloco.x >= gv.LARGURA_FECHADO,
                 f'{nome} saiu por baixo da coluna (x={bloco.x})')
        gv.tratar_evento(ctx.estado, pygame.event.Event(
            pygame.MOUSEBUTTONUP, {'pos': rect.center, 'button': 1}))
        s.checar(gv.visivel(ctx.estado, nome), f'{nome} sumiu ao soltar o clique')
        gv.tratar_evento(ctx.estado, clique)
        s.checar(not gv.visivel(ctx.estado, nome), f'{nome} deveria ter voltado')


def arrastar_tira_o_bloco_e_largar_na_coluna_guarda():
    ctx = Contexto()
    _abrir_coluna(ctx)
    rect, nome = ctx.estado.rects_gavetas[0]
    bloco = getattr(ctx.estado, nome)

    gv.tratar_evento(ctx.estado, pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {'pos': rect.center, 'button': 1}))
    destino = (900, 420)
    gv.tratar_evento(ctx.estado, pygame.event.Event(
        pygame.MOUSEMOTION, {'pos': destino, 'rel': (0, 0), 'buttons': (1, 0, 0)}))
    s.checar(bloco.arrastando, 'o bloco saiu preso ao mouse')
    centro_x = bloco.x + bloco.largura // 2
    s.checar(abs(centro_x - destino[0]) < 40,
             f'o bloco nao acompanhou o mouse (centro em {centro_x})')
    gv.tratar_evento(ctx.estado, pygame.event.Event(
        pygame.MOUSEBUTTONUP, {'pos': destino, 'button': 1}))
    s.checar(gv.visivel(ctx.estado, nome), 'largado na tela, o bloco fica')
    s.checar(not bloco.arrastando, 'o arrasto terminou')

    # Agora arrasta de volta para cima da coluna
    bloco.arrastando = True
    bloco.x, bloco.y = 4, 300
    gv.tratar_evento(ctx.estado, pygame.event.Event(
        pygame.MOUSEBUTTONUP, {'pos': (10, 300), 'button': 1}))
    s.checar(not gv.visivel(ctx.estado, nome),
             'largado na coluna, o bloco volta para a gaveta')


def coluna_nao_pinta_fora_de_si():
    """A coluna e desenhada com recorte: nada dela cai sobre o workspace."""
    for tema in harness.TEMAS:
        ctx = Contexto(tema=tema)
        _abrir_coluna(ctx)
        tela = pygame.Surface(TELA_CHEIA, pygame.SRCALPHA)
        tela.fill((0, 0, 0, 0))
        gv.desenhar(tela, ctx.estado, ctx.fontes, ctx.configs)
        limite = gv.largura_atual(ctx.estado) + 16     # tolera a sombra
        fora = []
        for y in range(0, TELA_CHEIA[1], 2):
            for x in range(limite, TELA_CHEIA[0], 2):
                if tela.get_at((x, y))[3] != 0:
                    fora.append((x, y))
                    break
            if fora:
                break
        s.checar(not fora, f'[{tema}] a coluna pintou em {fora[:3]}')


def coluna_encolhida_continua_utilizavel():
    """Em tela baixa as gavetas encolhem, mas continuam todas na coluna."""
    ctx = Contexto(1280, 720)
    ctx.estado.mouse_workspace = (8, 200)
    for _ in range(40):
        gv.atualizar(ctx.estado, 680)
    tela = pygame.Surface((1280, 680), pygame.SRCALPHA)
    gv.desenhar(tela, ctx.estado, ctx.fontes, ctx.configs)
    s.checar(len(ctx.estado.rects_gavetas) == len(gv.GAVETAS),
             f'so {len(ctx.estado.rects_gavetas)} gavetas couberam em 720p')
    coluna = pygame.Rect(0, 0, gv.largura_atual(ctx.estado), 680)
    for rect, nome in ctx.estado.rects_gavetas:
        s.checar(coluna.contains(rect), f'{nome} fora da coluna em 720p')
        s.checar(rect.height >= 20, f'{nome} virou uma gaveta clicavel demais fina')


def gaveteiro_calado_com_tela_cheia():
    """Com um estudo aberto, o clique nao pode cair numa gaveta antiga."""
    ctx = Contexto()
    _abrir_coluna(ctx)
    rect, nome = ctx.estado.rects_gavetas[0]
    ctx.estado.tela_estudo_ativa = True
    clique = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                {'pos': rect.center, 'button': 1})
    s.checar(gv.tratar_evento(ctx.estado, clique) is False,
             'o gaveteiro nao deveria responder com a tela de estudo aberta')
    s.checar(not gv.visivel(ctx.estado, nome), f'{nome} saiu sem querer')
    ctx.estado.tela_estudo_ativa = False
    s.checar(gv.tratar_evento(ctx.estado, clique), 'volta a responder depois')


s.teste('todo bloco comeca guardado na coluna', tudo_comeca_guardado)
s.teste('gaveteiro fica calado com a tela cheia aberta',
        gaveteiro_calado_com_tela_cheia)
s.teste('bloco guardado nao deixa alvo clicavel', bloco_guardado_nao_deixa_alvo)
s.teste('a coluna abre no hover e fecha ao sair', coluna_abre_no_hover_e_fecha)
s.teste('as gavetas ficam dentro da coluna, sem sobrepor', gavetas_dentro_da_coluna)
s.teste('clique tira o bloco e clique de novo guarda', clique_tira_e_guarda)
s.teste('arrastar tira, largar na coluna guarda',
        arrastar_tira_o_bloco_e_largar_na_coluna_guarda)
s.teste('a coluna nao pinta fora de si', coluna_nao_pinta_fora_de_si)
s.teste('as gavetas cabem em tela baixa', coluna_encolhida_continua_utilizavel)

s.encerrar()
