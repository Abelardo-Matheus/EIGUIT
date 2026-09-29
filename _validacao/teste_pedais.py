# -*- coding: utf-8 -*-
"""
Suite do estudo de Pedais de Efeito.

Motor de audio: todo pedal renderiza com qualquer valor de parametro sem NaN
nem estouro, o efeito ligado soa diferente do desligado, e cada parametro,
indo do minimo ao maximo, muda o audio de verdade. Alguns efeitos tambem sao
conferidos pela fisica (o whammy sobe mesmo uma oitava, o delay repete no
tempo certo, o gate silencia o chiado).

Interface: lista e pedal aberto em tres resolucoes e dois temas, clique nos
cartoes, arrasto de slider e de knob, footswitch, audio base, exemplos,
teclado e ESC parando o audio.
"""
import numpy as np
import pygame

import harness
from harness import Contexto, Suite

from audio import efeitos_pedais as motor
from Estudos import curriculo_pedais as cur
import core.modulos.modulos_estudos as modulo_estudos

s = Suite('teste_pedais')


def _rms(a):
    return float(np.sqrt(np.mean(np.asarray(a, dtype=np.float64) ** 2)))


# ------------------------------------------------------------------ motor --
def conteudo_completo():
    ids = [p['id'] for p in cur.PEDAIS]
    s.checar(len(ids) == len(set(ids)), 'ids de pedal repetidos')
    grupos = {g['id'] for g in cur.GRUPOS}
    for p in cur.PEDAIS:
        s.checar(p['id'] in motor.EFEITOS, f"{p['id']} sem efeito no motor")
        s.checar(p['grupo'] in grupos, f"{p['id']} em grupo inexistente")
        s.checar(p['base'] in motor.BASES, f"{p['id']} com base invalida")
        for chave in ('resumo', 'como_funciona', 'quando_usar', 'dica'):
            s.checar(len(p[chave]) > 20, f"{p['id']}: texto '{chave}' vazio")
        ids_par = {par['id'] for par in p['parametros']}
        for par in p['parametros']:
            s.checar(par['min'] <= par['padrao'] <= par['max'],
                     f"{p['id']}.{par['id']}: padrao fora da faixa")
            s.checar(len(par['explicacao']) > 30, f"{p['id']}.{par['id']}: sem explicacao")
            if par['opcoes']:
                s.checar(any(abs(v - par['padrao']) < 1e-9 for v, _ in par['opcoes']),
                         f"{p['id']}.{par['id']}: padrao nao e uma das opcoes")
        for nome, valores in p['exemplos']:
            s.checar(set(valores) <= ids_par, f"{p['id']}: exemplo '{nome}' com parametro errado")


def todos_renderizam_e_mudam_o_som():
    for p in cur.PEDAIS:
        v = cur.valores_padrao(p)
        ligado = motor.renderizar(p['id'], v, p['base'])
        desligado = motor.renderizar(p['id'], v, p['base'], ligado=False)
        s.checar(ligado.shape == desligado.shape and ligado.shape[1] == 2,
                 f"{p['id']}: formato inesperado {ligado.shape}")
        s.checar(np.isfinite(ligado).all(), f"{p['id']}: NaN no audio")
        s.checar(np.abs(ligado).max() <= 1.0, f"{p['id']}: audio estourado")
        s.checar(_rms(ligado) > 0.005, f"{p['id']}: audio mudo com o padrao")
        if p['id'] == 'eq':
            continue                      # EQ comeca plano de proposito: nao muda nada
        diferenca = _rms(ligado - desligado) / _rms(desligado)
        s.checar(diferenca > 0.05, f"{p['id']}: ligado igual a desligado ({diferenca:.3f})")


def cada_parametro_mexe_no_som():
    for p in cur.PEDAIS:
        v = cur.valores_padrao(p)
        if p['id'] == 'eq':
            v['medios'] = 8               # sem ganho nos medios, a frequencia nao importa
        for par in p['parametros']:
            baixo, alto = dict(v), dict(v)
            baixo[par['id']], alto[par['id']] = par['min'], par['max']
            a = motor.renderizar(p['id'], baixo, p['base'])
            b = motor.renderizar(p['id'], alto, p['base'])
            s.checar(np.isfinite(a).all() and np.isfinite(b).all(),
                     f"{p['id']}.{par['id']}: NaN no extremo")
            mudanca = _rms(a - b) / max(_rms(a), _rms(b), 1e-6)
            s.checar(mudanca > 0.02,
                     f"{p['id']}.{par['id']}: min e max soam iguais ({mudanca:.4f})")


def _f0(sinal, sr):
    janela = sinal * np.hanning(sinal.size)
    espectro = np.abs(np.fft.rfft(janela))
    freqs = np.fft.rfftfreq(sinal.size, 1 / sr)
    espectro[freqs < 50] = 0
    return freqs[np.argmax(espectro)]


def whammy_muda_a_afinacao():
    sr = motor.SR_PADRAO
    p = cur.PEDAIS_POR_ID['whammy']
    trecho = slice(sr // 2, sr // 2 + sr)
    seco = motor.renderizar('whammy', cur.valores_padrao(p), 'nota', ligado=False)[trecho, 0]
    base = _f0(seco, sr)
    for semitons in (12, -12, 7):
        v = cur.valores_padrao(p)
        v.update(intervalo=semitons, pedal=1, movimento=0, mix=1)
        f = _f0(motor.renderizar('whammy', v, 'nota')[trecho, 0], sr)
        esperado = base * 2 ** (semitons / 12)
        s.checar(abs(f - esperado) / esperado < 0.03,
                 f'whammy {semitons:+d}: {f:.1f} Hz, esperado {esperado:.1f} Hz')


def delay_repete_no_tempo():
    sr = motor.SR_PADRAO
    x = np.zeros(int(motor.DURACAO_LOOP * sr))
    x[1000] = 1.0
    t = np.arange(x.size) / sr
    y = motor.fx_delay(x, t, sr, {'time': 300, 'feedback': 0.5, 'mix': 1.0, 'tom': 1.0},
                       {'duracao': motor.DURACAO_LOOP})
    eco = 1000 + int(0.3 * sr)
    janela = y[eco - 50:eco + 50]
    s.checar(np.max(np.abs(janela)) > 0.5, 'o primeiro eco nao apareceu em 300 ms')
    s.checar(abs(np.max(np.abs(y[eco + int(0.3 * sr) - 50:eco + int(0.3 * sr) + 50])) - 0.5) < 0.1,
             'o segundo eco nao caiu pela metade com feedback 0.5')


def gate_silencia_o_chiado():
    p = cur.PEDAIS_POR_ID['gate']
    v = cur.valores_padrao(p)
    sr = motor.SR_PADRAO
    janela = sr // 20
    aberto = motor.renderizar('gate', v, 'staccato', ligado=False)[:, 0]
    fechado = motor.renderizar('gate', v, 'staccato')[:, 0]
    minimo = min(_rms(fechado[i:i + janela]) for i in range(0, fechado.size - janela, janela))
    minimo_sem = min(_rms(aberto[i:i + janela]) for i in range(0, aberto.size - janela, janela))
    s.checar(minimo_sem > 0.002, 'o audio do gate precisa ter chiado para cortar')
    s.checar(minimo < 1e-4, 'o gate nao silenciou os intervalos')


def loop_sem_emenda():
    """O fim do loop precisa emendar no comeco sem estalo."""
    for p in cur.PEDAIS:
        y = motor.renderizar(p['id'], cur.valores_padrao(p), p['base'])
        salto = np.abs(y[0] - y[-1]).max()
        passo_tipico = np.percentile(np.abs(np.diff(y[:, 0])), 99.5)
        s.checar(salto <= max(0.02, passo_tipico * 3),
                 f"{p['id']}: estalo na emenda do loop ({salto:.3f})")


# -------------------------------------------------------------- interface --
def _clique(ger, ctx, pos, botao=1):
    ger.tratar_eventos(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': pos, 'button': botao}),
                       pos, ctx.estado)


def _abrir(ctx):
    ger = modulo_estudos.GerenciadorEstudos()
    ctx.estado.tela_estudo_ativa = True
    ctx.estado.estudo_ativo = 'Pedais de Efeito'
    ger.desenhar_tela_estudo(ctx.tela, ctx.largura, ctx.altura, ctx.estado, ctx.fontes)
    return ger, ger.modulo_pedais


def _quadro(ger, ctx):
    ger.desenhar_tela_estudo(ctx.tela, ctx.largura, ctx.altura, ctx.estado, ctx.fontes)


def interface(largura, altura, tema):
    ctx = Contexto(largura, altura, tema)
    ger, m = _abrir(ctx)
    s.checar(m is not None and m.vista == 'lista', 'o estudo nao abriu na lista')
    s.checar(m.rects_pedais, 'a lista nao mostrou nenhum pedal')

    # rolagem da lista nao pode passar do fim
    for _ in range(40):
        ger.tratar_eventos(pygame.event.Event(pygame.MOUSEWHEEL, {'x': 0, 'y': -1}),
                           (0, 0), ctx.estado)
    _quadro(ger, ctx)
    s.checar(m.scroll_lista <= max(0, m.altura_conteudo_lista - m.altura_visivel_lista),
             'a rolagem passou do fim da lista')
    m.scroll_lista = 0
    _quadro(ger, ctx)

    # abrir pelo cartao (coordenadas ja virtuais, como o gerenciador repassa)
    r, pedal = m.rects_pedais[1]
    m.tratar_cliques(r.center, ctx.estado)
    s.checar(m.vista == 'pedal' and m.pedal is pedal, 'o clique no cartao nao abriu o pedal')

    for p in cur.PEDAIS:
        m.abrir_pedal(p)
        m.reprodutor.aguardar()
        _quadro(ger, ctx)
        s.checar(m.reprodutor.audio is not None, f"{p['id']}: nenhum audio renderizado")
        s.checar(len(m.rects_sliders) == len(p['parametros']),
                 f"{p['id']}: faltou slider na tela")
        area = ctx.tela.get_rect()
        for barra, _i in m.rects_sliders:
            s.checar(area.contains(barra), f"{p['id']}: slider fora da tela")
        s.checar(area.contains(m.rect_play) and area.contains(m.rect_bypass),
                 f"{p['id']}: botoes de ouvir/ligar fora da tela")

    # arrastar o primeiro slider ate o fim muda o valor e pede audio novo
    m.abrir_pedal(cur.PEDAIS_POR_ID['delay'])
    m.reprodutor.aguardar()
    _quadro(ger, ctx)
    barra, i = m.rects_sliders[0]
    par = m.parametros[i]
    _clique(ger, ctx, (barra.x + 2, barra.centery))
    ger.tratar_eventos(pygame.event.Event(pygame.MOUSEMOTION,
                                          {'pos': (barra.right + 30, barra.centery),
                                           'rel': (0, 0), 'buttons': (1, 0, 0)}),
                       (barra.right + 30, barra.centery), ctx.estado)
    ger.tratar_eventos(pygame.event.Event(pygame.MOUSEBUTTONUP,
                                          {'pos': (barra.right + 30, barra.centery), 'button': 1}),
                       (barra.right + 30, barra.centery), ctx.estado)
    s.checar(abs(m.valores[par['id']] - par['max']) < 1e-6, 'arrastar o slider nao chegou ao maximo')
    s.checar(m.arrastando is None, 'o arrasto nao terminou no mouse up')
    m.reprodutor.aguardar()

    # knob: arrastar para cima aumenta
    _quadro(ger, ctx)
    rk, ik = m.rects_knobs[1]
    antes = m.valores[m.parametros[ik]['id']]
    _clique(ger, ctx, rk.center)
    ger.tratar_eventos(pygame.event.Event(pygame.MOUSEMOTION,
                                          {'pos': (rk.centerx, rk.centery - 40), 'rel': (0, -40),
                                           'buttons': (1, 0, 0)}),
                       (rk.centerx, rk.centery - 40), ctx.estado)
    ger.tratar_eventos(pygame.event.Event(pygame.MOUSEBUTTONUP,
                                          {'pos': (rk.centerx, rk.centery - 40), 'button': 1}),
                       (rk.centerx, rk.centery - 40), ctx.estado)
    s.checar(m.valores[m.parametros[ik]['id']] > antes, 'arrastar o knob para cima nao aumentou')
    s.checar(m.param_foco == ik, 'o knob nao ficou em foco')

    # footswitch e botao de bypass
    _quadro(ger, ctx)
    m.tratar_cliques(m.rect_footswitch.center, ctx.estado)
    s.checar(m.ligado is False, 'o footswitch nao desligou o efeito')
    _quadro(ger, ctx)
    m.tratar_cliques(m.rect_bypass.center, ctx.estado)
    s.checar(m.ligado is True, 'o botao nao religou o efeito')

    # audio base e exemplos
    _quadro(ger, ctx)
    r, chave = [x for x in m.rects_bases if x[1] != m.base][0]
    m.tratar_cliques(r.center, ctx.estado)
    s.checar(m.base == chave, 'o chip de audio base nao trocou a base')
    _quadro(ger, ctx)
    if m.rects_exemplos:
        r, i = m.rects_exemplos[-1]
        m.tratar_cliques(r.center, ctx.estado)
        nome, valores = m.pedal['exemplos'][i]
        s.checar(all(abs(m.valores[k] - v) < 1e-9 for k, v in valores.items()),
                 f'o exemplo {nome} nao aplicou os valores')
    _quadro(ger, ctx)
    m.tratar_cliques(m.rect_reset.center, ctx.estado)
    s.checar(m.valores == cur.valores_padrao(m.pedal), 'restaurar padrao nao voltou os valores')

    # tocar, teclado, proximo e voltar
    _quadro(ger, ctx)
    m.tratar_cliques(m.rect_play.center, ctx.estado)
    s.checar(m.reprodutor.tocando, 'o botao Ouvir nao comecou a tocar')
    m.param_foco = 0
    for tecla in (pygame.K_DOWN, pygame.K_RIGHT, pygame.K_b, pygame.K_b):
        ger.tratar_eventos(pygame.event.Event(pygame.KEYDOWN, {'key': tecla, 'unicode': '', 'mod': 0}),
                           (0, 0), ctx.estado)
    s.checar(m.param_foco == 1, 'seta para baixo nao trocou o parametro em foco')
    _quadro(ger, ctx)
    atual = m.pedal
    m.tratar_cliques(m.rect_proximo.center, ctx.estado)
    s.checar(m.pedal is not atual, 'Proximo nao trocou de pedal')
    s.checar(m.reprodutor.tocando, 'trocar de pedal nao deveria parar o som')
    m.reprodutor.aguardar()
    _quadro(ger, ctx)

    # ESC sai do estudo e para o audio
    reprodutor = m.reprodutor
    ger.tratar_eventos(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_ESCAPE,
                                                            'unicode': '', 'mod': 0}),
                       (0, 0), ctx.estado)
    s.checar(ger.modulo_pedais is None, 'ESC nao soltou o modulo de pedais')
    s.checar(reprodutor.tocando is False, 'ESC nao parou o audio')


def sub_aba_existe():
    ctx = Contexto()
    secao = [x for x in ctx.estado.secoes_inferiores if x['conteudo'] == 'estudos'][0]
    s.checar('Pedais' in secao['sub_abas'], 'sub-aba Pedais nao esta em ESTUDOS')


s.teste('conteudo didatico completo', conteudo_completo)
s.teste('todos os pedais renderizam e mudam o som', todos_renderizam_e_mudam_o_som)
s.teste('cada parametro mexe no som', cada_parametro_mexe_no_som)
s.teste('whammy muda a afinacao certa', whammy_muda_a_afinacao)
s.teste('delay repete no tempo e cai com o feedback', delay_repete_no_tempo)
s.teste('noise gate silencia o chiado', gate_silencia_o_chiado)
s.teste('loop emenda sem estalo', loop_sem_emenda)
s.teste('sub-aba Pedais em ESTUDOS', sub_aba_existe)
for _tema in harness.TEMAS:
    for _l, _a in ((1920, 1080), (1600, 900), (1280, 720)):
        s.teste(f'[{_tema}] interface {_l}x{_a}', lambda l=_l, a=_a, t=_tema: interface(l, a, t))
s.encerrar()
