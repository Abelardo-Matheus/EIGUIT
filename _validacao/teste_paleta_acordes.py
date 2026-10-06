# -*- coding: utf-8 -*-
"""
Suite da paleta de acordes (bloco 'Acordes' do gaveteiro).

Cobre:
1. Teoria: a regiao de soltura cai na forma CAGED certa da tonica.
2. Clique: cartao liga/desliga no braco todo; chip tira; Limpar tira tudo.
3. Varios acordes: cores distintas, limite com saida do mais antigo.
4. Arrasto: previa no braco durante o arrasto, soltura vira regiao, soltar
   fora do braco nao faz nada, chip arrastado muda de regiao e mantem a cor.
5. Aba ACORDES: cartao e mini-braco arrastaveis, CAGED leva a propria janela.
6. Limites do bloco em tres tamanhos e dois temas; bloco guardado e modo de
   edicao nao capturam clique.
7. Perfil: acordes ligados vao e voltam pelo JSON; perfil antigo abre com o
   bloco novo guardado.
8. Graus: o acorde do bloco de graus continua no braco nos quadros seguintes.
"""
import json

import pygame

import harness
from harness import Contexto, Suite

import core.controlador_eventos as controlador
from ui import renderizador_ui
from ui.components import gaveteiro as gv
from ui.components import paleta_acordes as pa
from ui.blocks.painel_acordes import painel_da_sub_aba

s = Suite('teste_paleta_acordes')
TOPBAR = 40


def _ctx(tema='escuro', largura=1920, altura=1080):
    ctx = Contexto(largura, altura, tema)
    ctx.estado.drag_ativado = False
    gv.soltar(ctx.estado, 'dragger_paleta_acordes')
    _quadro(ctx)
    return ctx


def _quadro(ctx, vezes=1):
    for _ in range(vezes):
        renderizador_ui.desenhar_workspace(
            ctx.tela, ctx.estado, ctx.configs, ctx.escalas, ctx.fontes,
            ctx.metronomo, ctx.processador, ctx.gravador, ctx.campo, ctx.jogos)


def _evento(ctx, tipo, pos, botoes=(1, 0, 0)):
    """Passa um evento pelo controlador como o main.py passaria."""
    real = (pos[0], pos[1] + TOPBAR)
    ctx.estado.pos_mouse_real = real
    evento = pygame.event.Event(tipo, {'pos': real, 'button': 1, 'rel': (0, 0),
                                       'buttons': botoes})
    controlador.processar([evento], ctx.estado, ctx.configs, ctx.escalas,
                          ctx.metronomo, ctx.processador, ctx.gravador,
                          ctx.campo, ctx.jogos)


def _clicar(ctx, pos):
    _evento(ctx, pygame.MOUSEBUTTONDOWN, pos)
    _evento(ctx, pygame.MOUSEBUTTONUP, pos)
    _quadro(ctx)


def _arrastar(ctx, de, para, soltar=True):
    _evento(ctx, pygame.MOUSEBUTTONDOWN, de)
    _evento(ctx, pygame.MOUSEMOTION, (de[0] + 20, de[1] - 20))
    _evento(ctx, pygame.MOUSEMOTION, para)
    if soltar:
        _evento(ctx, pygame.MOUSEBUTTONUP, para)
    _quadro(ctx)


def _cartao(ctx, tipo):
    return dict((t, r) for r, t in ctx.estado.rects_paleta_tipos)[tipo].center


def _tonica(ctx, nota):
    _clicar(ctx, dict((n, r) for r, n in ctx.estado.rects_paleta_tonicas)[nota].center)


def _ponto_na_casa(ctx, casa):
    rect = pa.rect_do_braco(ctx.estado)
    largura = rect.width / ctx.estado.NUM_CASAS
    return int(rect.x + (casa - 0.5) * largura), rect.centery


def _rotulos(ctx):
    return [a['rotulo'] for a in ctx.estado.acordes_fixados]


# ---------------------------------------------------------------- teoria --
def regioes_caged():
    casos = [('C', 3, 'C'), ('C', 5, 'A'), ('G', 9, 'C'), ('E', 1, 'E'),
             ('A', 7, 'E'), ('A', 4, 'G'), ('D', 12, 'E')]
    for tonica, casa, forma in casos:
        ini, fim, nome = pa.janela_caged(tonica, casa, 18)
        s.checar(nome == forma, f'{tonica} na casa {casa}: forma {nome}, esperava {forma}')
        s.checar(fim - ini == pa.LARGURA_JANELA, 'janela com largura errada')
        s.checar(ini <= casa <= fim, f'{tonica}: casa {casa} fora da janela {ini}-{fim}')
    for tonica in pa._acordes().NOTAS:
        for casa in range(0, 25):
            ini, fim, _ = pa.janela_caged(tonica, casa, 24)
            s.checar(0 <= ini <= 23, 'janela comeca fora do braco')


s.teste('soltura cai na forma CAGED mais perto', regioes_caged)


def regiao_tem_as_notas_do_acorde():
    """A janela da forma contem a tonica na corda da forma."""
    acordes = pa._acordes()
    for tonica in acordes.NOTAS:
        for casa in (2, 7, 12):
            ini, fim, nome = pa.janela_caged(tonica, casa, 18)
            shape = next(x for x in acordes.SHAPES if x['nome'] == nome)
            casa_r = ini + shape['casa_tonica']
            solta = acordes.CORDAS_SOLTAS[shape['corda_tonica']]
            nota = acordes.NOTAS[(acordes.NOTAS.index(solta) + casa_r) % 12]
            s.checar(nota == tonica, f'{tonica} forma {nome}: casa {casa_r} da {nota}')


s.teste('a regiao tem a tonica onde a forma manda', regiao_tem_as_notas_do_acorde)


# ---------------------------------------------------------------- clique --
def clique_liga_e_desliga():
    ctx = _ctx()
    _tonica(ctx, 'A')
    _clicar(ctx, _cartao(ctx, 'm7'))
    s.checar(_rotulos(ctx) == ['Am7'], f'esperava Am7 no braco: {_rotulos(ctx)}')
    s.checar(ctx.estado.acordes_fixados[0]['janela'] is None, 'clique e braco todo')
    s.checar([a['rotulo'] for a in ctx.estado.acordes_no_braco] == ['Am7'],
             'o braco nao recebeu o acorde')
    _clicar(ctx, _cartao(ctx, 'm7'))
    s.checar(_rotulos(ctx) == [], 'segundo clique deveria tirar')


s.teste('clique no cartao liga e desliga no braco todo', clique_liga_e_desliga)


def varios_com_cores_distintas():
    ctx = _ctx()
    for tipo in ('maior', 'menor', '7', 'maj7'):
        _clicar(ctx, _cartao(ctx, tipo))
    s.checar(_rotulos(ctx) == ['C', 'Cm', 'C7', 'Cmaj7'], f'{_rotulos(ctx)}')
    cores = [a['cor'] for a in ctx.estado.acordes_fixados]
    s.checar(len(set(cores)) == 4, 'cores repetidas entre acordes')
    for tipo in ('m7', 'power', 'sus2'):
        _clicar(ctx, _cartao(ctx, tipo))
    s.checar(len(ctx.estado.acordes_fixados) == pa.MAX_NO_BRACO, 'passou do limite')
    s.checar('C' not in _rotulos(ctx), 'o mais antigo deveria ter saido')
    cores = [a['cor'] for a in ctx.estado.acordes_fixados]
    s.checar(len(set(cores)) == pa.MAX_NO_BRACO, 'cor repetida no limite')


s.teste('varios acordes ao mesmo tempo, cada um com sua cor', varios_com_cores_distintas)


def chip_e_limpar():
    ctx = _ctx()
    for tipo in ('maior', 'menor', '7'):
        _clicar(ctx, _cartao(ctx, tipo))
    chips = ctx.estado.rects_paleta_ativos
    s.checar(len(chips) == 3, f'esperava 3 chips: {len(chips)}')
    _clicar(ctx, chips[1][0].center)
    s.checar(_rotulos(ctx) == ['C', 'C7'], f'chip do meio devia sair: {_rotulos(ctx)}')
    _clicar(ctx, ctx.estado.rect_paleta_limpar.center)
    s.checar(_rotulos(ctx) == [], 'Limpar devia tirar tudo')


s.teste('clique no chip tira, Limpar tira tudo', chip_e_limpar)


# ---------------------------------------------------------------- arrasto --
def arrasto_com_previa_e_soltura():
    ctx = _ctx()
    destino = _ponto_na_casa(ctx, 5)
    _arrastar(ctx, _cartao(ctx, 'maior'), destino, soltar=False)
    lista, foco = pa.acordes_para_desenhar(ctx.estado)
    s.checar(len(lista) == 1 and lista[0].get('previa'), 'sem previa durante o arrasto')
    s.checar(foco == {lista[0]['rotulo']}, 'a previa devia ficar em foco')
    s.checar(_rotulos(ctx) == [], 'nada deveria estar fixado antes de soltar')
    _evento(ctx, pygame.MOUSEBUTTONUP, destino)
    _quadro(ctx)
    s.checar(_rotulos(ctx) == ['C (A)'], f'esperava C (A): {_rotulos(ctx)}')
    s.checar(ctx.estado.acordes_fixados[0]['janela'] == (3, 7), 'janela errada')
    s.checar(ctx.estado.arrasto_acorde is None, 'arrasto nao terminou')


s.teste('arrastar mostra previa e soltar fixa a regiao', arrasto_com_previa_e_soltura)


def soltar_fora_nao_faz_nada():
    ctx = _ctx()
    _arrastar(ctx, _cartao(ctx, 'maior'), (1700, 900))
    s.checar(_rotulos(ctx) == [], 'soltar longe do braco nao devia ligar nada')


s.teste('soltar fora do braco nao liga nada', soltar_fora_nao_faz_nada)


def mesma_cifra_em_duas_regioes():
    ctx = _ctx()
    _arrastar(ctx, _cartao(ctx, 'maior'), _ponto_na_casa(ctx, 5))
    _arrastar(ctx, _cartao(ctx, 'maior'), _ponto_na_casa(ctx, 10))
    s.checar(_rotulos(ctx) == ['C (A)', 'C (E)'], f'{_rotulos(ctx)}')
    _arrastar(ctx, _cartao(ctx, 'maior'), _ponto_na_casa(ctx, 5))
    s.checar(len(_rotulos(ctx)) == 2, 'mesma regiao nao entra duas vezes')
    # Clique no cartao tira todas as regioes daquela cifra
    _clicar(ctx, _cartao(ctx, 'maior'))
    s.checar(_rotulos(ctx) == [], 'clique devia tirar as duas regioes')


s.teste('a mesma cifra em duas formas, e o clique tira as duas', mesma_cifra_em_duas_regioes)


def braco_todo_vira_regiao():
    ctx = _ctx()
    _clicar(ctx, _cartao(ctx, '7'))
    cor = ctx.estado.acordes_fixados[0]['cor']
    _arrastar(ctx, _cartao(ctx, '7'), _ponto_na_casa(ctx, 8))
    s.checar(len(ctx.estado.acordes_fixados) == 1, 'devia substituir, nao duplicar')
    s.checar(ctx.estado.acordes_fixados[0]['janela'] is not None, 'devia virar regiao')
    s.checar(ctx.estado.acordes_fixados[0]['cor'] == cor, 'devia manter a cor')


s.teste('acorde do braco todo solto numa regiao vira regiao', braco_todo_vira_regiao)


def chip_arrastado_muda_regiao():
    ctx = _ctx()
    _tonica(ctx, 'G')
    _arrastar(ctx, _cartao(ctx, '7'), _ponto_na_casa(ctx, 4))
    cor = ctx.estado.acordes_fixados[0]['cor']
    janela_antes = ctx.estado.acordes_fixados[0]['janela']
    chip = ctx.estado.rects_paleta_ativos[0][0]
    _arrastar(ctx, chip.center, _ponto_na_casa(ctx, 13), soltar=False)
    s.checar(ctx.estado.acorde_em_foco == {ctx.estado.acordes_fixados[0]['rotulo']},
             'acorde arrastado devia ficar em foco')
    _evento(ctx, pygame.MOUSEBUTTONUP, _ponto_na_casa(ctx, 13))
    _quadro(ctx)
    item = ctx.estado.acordes_fixados[0]
    s.checar(len(ctx.estado.acordes_fixados) == 1, 'chip arrastado nao pode duplicar')
    s.checar(item['janela'] != janela_antes, 'a regiao nao mudou')
    s.checar(item['janela'][0] <= 13 <= item['janela'][1], f'regiao {item["janela"]}')
    s.checar(item['cor'] == cor, 'a cor mudou ao mover')
    s.checar(item['rotulo'].startswith('G7 ('), f'rotulo {item["rotulo"]}')


s.teste('arrastar o chip leva o acorde para outra regiao', chip_arrastado_muda_regiao)


def chip_de_outra_origem_tambem_move():
    """Acorde fixado pela aba ou pelas progressoes (sem tonica salva) tambem move."""
    ctx = _ctx()
    from ui.components.blocos_extras import aplicar_progressao
    aplicar_progressao(ctx.estado, 'C', [0, 4, 5, 3])
    _quadro(ctx)
    chip = ctx.estado.rects_paleta_ativos[1][0]          # G
    _arrastar(ctx, chip.center, _ponto_na_casa(ctx, 5))
    item = ctx.estado.acordes_fixados[1]
    s.checar(item['rotulo'] == 'G (E)', f'esperava G (E): {item["rotulo"]}')


s.teste('chip vindo das progressoes tambem muda de regiao', chip_de_outra_origem_tambem_move)


def foco_ao_passar_o_mouse():
    ctx = _ctx()
    for tipo in ('maior', 'menor'):
        _clicar(ctx, _cartao(ctx, tipo))
    chip = ctx.estado.rects_paleta_ativos[1][0]
    _evento(ctx, pygame.MOUSEMOTION, chip.center, botoes=(0, 0, 0))
    _quadro(ctx)
    _lista, foco = pa.acordes_para_desenhar(ctx.estado)
    s.checar(foco == {'Cm'}, f'foco errado: {foco}')
    _evento(ctx, pygame.MOUSEMOTION, (1700, 900), botoes=(0, 0, 0))
    _quadro(ctx)
    s.checar(not pa.acordes_para_desenhar(ctx.estado)[1], 'foco devia sair')


s.teste('mouse sobre o chip deixa so aquele acorde em evidencia', foco_ao_passar_o_mouse)


# ------------------------------------------------------------ aba ACORDES --
def arrasto_da_aba():
    ctx = _ctx()
    gv.guardar(ctx.estado, 'dragger_paleta_acordes')
    secao = ctx.estado.secoes_inferiores[1]
    secao['expandido'] = True
    secao['memoria_sub_aba'] = 0              # CAGED
    _quadro(ctx)
    painel = painel_da_sub_aba(0)
    cartao_a = painel.rects_itens[1]           # forma A
    braco = pa.rect_do_braco(ctx.estado)
    _arrastar(ctx, cartao_a.center, (braco.right - 40, braco.y + 30))
    s.checar(_rotulos(ctx) == ['C (A)'], f'CAGED leva a propria forma: {_rotulos(ctx)}')
    s.checar(ctx.estado.acordes_fixados[0]['janela'] == (3, 7), 'janela da forma A')

    secao['memoria_sub_aba'] = 3              # setimas
    _quadro(ctx)
    painel = painel_da_sub_aba(3)
    s.checar(painel.rect_mini_braco.width > 0, 'mini-braco sem alvo')
    _arrastar(ctx, painel.rect_mini_braco.center, _ponto_na_casa(ctx, 12)[:1] + (braco.y + 30,))
    s.checar(len(ctx.estado.acordes_fixados) == 2, f'mini-braco nao fixou: {_rotulos(ctx)}')
    s.checar(_rotulos(ctx)[1].startswith('C7 ('), f'{_rotulos(ctx)}')
    secao['expandido'] = False


s.teste('cartao e mini-braco da aba arrastam para o braco', arrasto_da_aba)


def clique_simples_na_aba_continua_igual():
    ctx = _ctx()
    gv.guardar(ctx.estado, 'dragger_paleta_acordes')
    secao = ctx.estado.secoes_inferiores[1]
    secao['expandido'] = True
    secao['memoria_sub_aba'] = 3
    _quadro(ctx)
    painel = painel_da_sub_aba(3)
    _clicar(ctx, painel.rects_itens[2].center)
    s.checar(painel.indice_tipo == 2, 'clique devia selecionar o tipo')
    s.checar(_rotulos(ctx) == [], 'clique sem arrasto nao fixa')
    s.checar(ctx.estado.arrasto_acorde is None, 'arrasto ficou pendurado')
    secao['expandido'] = False


s.teste('clique simples na aba seleciona sem fixar', clique_simples_na_aba_continua_igual)


# ----------------------------------------------------------------- limites --
def limites_do_bloco():
    from harness import pixels_fora
    from ui.components.blocos_extras import _moldura
    for tema in harness.TEMAS:
        for largura, altura in ((200, 110), (300, 160), (620, 196)):
            ctx = Contexto(800, 500, tema)
            ctx.estado.blocos_guardados = set()
            rect = ctx.redimensionar_bloco('paleta_acordes', largura, altura)
            ctx.estado.acordes_fixados = []
            pa.adicionar(ctx.estado, pa.descrever('C', 'maior'))
            pa.adicionar(ctx.estado, pa.descrever('A', 'm7', (5, 9), 'E'))

            def conteudo(sup, c=ctx):
                pa.desenhar_bloco_paleta(sup, c.estado, c.fontes, c.configs)

            def base(sup, c=ctx):
                with _moldura(sup, c.estado, 'paleta_acordes', 'x', c.fontes, c.configs):
                    pass

            fora = pixels_fora(conteudo, base, (800, 500), rect)
            s.checar(not fora, f'[{tema}] {largura}x{altura} pintou fora: {fora[:3]}')
            alvos = ([r for r, _ in ctx.estado.rects_paleta_tonicas]
                     + [r for r, _ in ctx.estado.rects_paleta_tipos]
                     + [r for r, _ in ctx.estado.rects_paleta_ativos])
            s.checar(alvos, f'{largura}x{altura} sem nenhum alvo')
            for r in alvos:
                s.checar(rect.contains(r), f'{largura}x{altura}: alvo {r} fora do bloco')


s.teste('nada pintado nem clicavel fora do bloco (3 tamanhos, 2 temas)', limites_do_bloco)


def guardado_e_edicao_nao_capturam():
    ctx = _ctx()
    pos = _cartao(ctx, 'maior')
    gv.guardar(ctx.estado, 'dragger_paleta_acordes')
    _quadro(ctx)
    s.checar(not ctx.estado.rects_paleta_tipos, 'bloco guardado deixou alvo')
    _clicar(ctx, pos)
    s.checar(_rotulos(ctx) == [], 'bloco guardado respondeu ao clique')

    gv.soltar(ctx.estado, 'dragger_paleta_acordes')
    _quadro(ctx)
    ctx.estado.drag_ativado = True
    _evento(ctx, pygame.MOUSEBUTTONDOWN, _cartao(ctx, 'maior'))
    s.checar(ctx.estado.arrasto_acorde is None, 'modo de edicao deve mover o bloco')
    _evento(ctx, pygame.MOUSEBUTTONUP, _cartao(ctx, 'maior'))
    ctx.estado.drag_ativado = False


s.teste('bloco guardado e modo de edicao nao capturam clique', guardado_e_edicao_nao_capturam)


def gaveta_existe():
    s.checar('dragger_paleta_acordes' in gv.NOMES, 'paleta fora do gaveteiro')
    ctx = Contexto()
    s.checar('dragger_paleta_acordes' in ctx.estado.blocos_guardados,
             'paleta devia nascer guardada como os outros blocos')
    nomes = [d for d in controlador.obter_draggers_ativos(ctx.estado)]
    s.checar(ctx.estado.dragger_paleta_acordes not in nomes, 'guardada nao arrasta')


s.teste('a paleta mora no gaveteiro e nasce guardada', gaveta_existe)


# ------------------------------------------------------------------ perfil --
def perfil_ida_e_volta():
    ctx = _ctx()
    pa.adicionar(ctx.estado, pa.descrever('C', 'maior'))
    pa.adicionar(ctx.estado, pa.descrever('A', 'm7', (5, 9), 'E'))
    texto = json.dumps(pa.exportar(ctx.estado))
    outro = Contexto()
    pa.importar(outro.estado, json.loads(texto))
    s.checar([a['rotulo'] for a in outro.estado.acordes_fixados] == ['C', 'Am7 (E)'],
             'rotulos nao voltaram')
    s.checar(outro.estado.acordes_fixados[1]['janela'] == (5, 9), 'janela nao voltou como tupla')
    s.checar(isinstance(outro.estado.acordes_fixados[0]['cor'], tuple), 'cor nao voltou como tupla')
    pa.importar(outro.estado, [{'lixo': 1}, None, 'x'])
    s.checar(outro.estado.acordes_fixados == [], 'dados tortos deviam ser ignorados')


s.teste('acordes ligados vao e voltam pelo perfil', perfil_ida_e_volta)


def perfil_salvo_e_carregado(tmp=None):
    import os
    import tempfile
    from core.modulos.modulo_perfil import GerenciadorPerfil
    ctx = _ctx()
    pa.adicionar(ctx.estado, pa.descrever('E', 'menor', (0, 4), 'E'))
    perfil = GerenciadorPerfil()
    pasta = tempfile.mkdtemp()
    perfil.pasta_padrao = pasta
    perfil.texto_input = 'teste_paleta'
    perfil.salvar_ultimo_perfil_config = lambda caminho: None
    ctx.estado.usuario_id_logado = None
    perfil.salvar_perfil(ctx.estado, ctx.configs, ctx.campo, ctx.gravador)
    caminho = os.path.join(pasta, 'teste_paleta.json')
    dados = json.load(open(caminho, encoding='utf-8'))
    s.checar('dragger_paleta_acordes' in dados['posicoes_draggers'], 'posicao nao salva')

    novo = Contexto()
    perfil.carregar_perfil(caminho, novo.estado, novo.configs, novo.campo, novo.gravador)
    s.checar([a['rotulo'] for a in novo.estado.acordes_fixados] == ['Em (E)'],
             f'acordes nao voltaram: {novo.estado.acordes_fixados}')
    s.checar('dragger_paleta_acordes' not in novo.estado.blocos_guardados,
             'a paleta estava na tela e devia voltar na tela')

    # Perfil antigo: nao conhece o bloco novo, que entao nasce guardado
    del dados['posicoes_draggers']['dragger_paleta_acordes']
    dados['estado']['blocos_guardados'] = []
    json.dump(dados, open(caminho, 'w', encoding='utf-8'))
    velho = Contexto()
    perfil.carregar_perfil(caminho, velho.estado, velho.configs, velho.campo, velho.gravador)
    s.checar('dragger_paleta_acordes' in velho.estado.blocos_guardados,
             'perfil antigo abriu com a paleta na tela')


s.teste('perfil salva posicao e acordes; perfil antigo nao estranha', perfil_salvo_e_carregado)


# ------------------------------------------------------------------- graus --
def grau_continua_no_braco():
    ctx = _ctx()
    gv.soltar(ctx.estado, 'dragger_graus')
    _quadro(ctx)
    _clicar(ctx, ctx.estado.rects_graus[0][0].center)
    _quadro(ctx, 3)
    s.checar([a['rotulo'] for a in ctx.estado.acordes_no_braco] == ['C'],
             f'grau sumiu do braco: {ctx.estado.acordes_no_braco}')


s.teste('acorde do bloco de graus continua no braco', grau_continua_no_braco)


# ------------------------------------------------------------------ quadro --
def quadros_completos():
    for tema in harness.TEMAS:
        for largura, altura in ((1280, 720), (1920, 1080), (2560, 1440)):
            ctx = _ctx(tema, largura, altura)
            for tipo in ('maior', '7'):
                _clicar(ctx, _cartao(ctx, tipo))
            _arrastar(ctx, _cartao(ctx, 'm7'), _ponto_na_casa(ctx, 7), soltar=False)
            _quadro(ctx, 2)
            _evento(ctx, pygame.MOUSEBUTTONUP, _ponto_na_casa(ctx, 7))
            ctx.estado.instrumento = 'baixo'
            _quadro(ctx)


s.teste('workspace desenha com acordes e arrasto (3 resolucoes, 2 temas, baixo)',
        quadros_completos)

s.encerrar()
