# -*- coding: utf-8 -*-
"""
Configuracoes > Teclas de atalho e Configuracoes > Desempenho.

Teclas: gravar uma combinacao nova pelo clique em "Alterar", conflito tira a
tecla da outra funcao, letra sozinha e recusada, Backspace limpa, Esc cancela
(sem fechar o programa), padrao volta, e a tecla nova dispara a funcao.
Desempenho: presets, opcao avulsa vira "Personalizado", efeitos aplicados.
Perfil: teclas + desempenho + tema vao e voltam do arquivo, auto-salvar grava
sozinho e nao apaga o tema do config_eiguit.json.
Velocidade: zoom so do pedaco visivel e igual ao zoom da mesa inteira.
"""
import json
import os
import tempfile
import time

import pygame

import harness
from harness import Suite
import core.atalhos as atalhos
import core.desempenho as desempenho
from config import design_system as ds
from config.ui_metrics import ALTURA_TOPBAR
from ui.components.painel_preferencias import PAINEL

import teste_cabecalho as tc   # reaproveita montar/clicar/tecla

s = Suite('teste_preferencias')


def evento_tecla(key, ctrl=False, shift=False, alt=False):
    mod = ((pygame.KMOD_LCTRL if ctrl else 0) | (pygame.KMOD_LSHIFT if shift else 0)
           | (pygame.KMOD_LALT if alt else 0))
    return pygame.event.Event(pygame.KEYDOWN, {'key': key, 'mod': mod, 'unicode': '', 'scancode': 0})


def abrir_sub_aba(ctx, sub):
    tc.tecla(ctx, pygame.K_k, ctrl=True) if sub == 2 else \
        ctx.estado.menu_superior.executar_acao('desempenho', ctx.estado, ctx.configs, ctx.campo)
    tc.quadro(ctx)
    secao = next(x for x in ctx.estado.secoes_inferiores if x['conteudo'] == 'configuracao')
    s.checar(secao['expandido'] and secao['memoria_sub_aba'] == sub, f'sub-aba {sub} nao abriu')


def alvo(tipo, dado=None):
    for rect, t, d in PAINEL.alvos:
        if t == tipo and (dado is None or d == dado):
            return rect
    raise AssertionError(f'alvo {tipo}/{dado} nao foi desenhado')


def clicar_painel(ctx, rect):
    # O painel e desenhado no viewport (abaixo da barra)
    tc.clicar(ctx, (rect.centerx, rect.centery + ALTURA_TOPBAR))


def combinacoes():
    s.checar(atalhos.texto('ctrl+shift+s') == 'Ctrl+Shift+S', atalhos.texto('ctrl+shift+s'))
    s.checar(atalhos.texto('f12') == 'F12', 'F12')
    s.checar(atalhos.texto('ctrl+[+]') == 'Ctrl+Num +', atalhos.texto('ctrl+[+]'))
    s.checar(atalhos.combo_do_evento(evento_tecla(pygame.K_s, ctrl=True, shift=True)) == 'ctrl+shift+s',
             'combo do evento')
    s.checar(atalhos.combo_do_evento(evento_tecla(pygame.K_LCTRL, ctrl=True)) is None,
             'Ctrl sozinho virou atalho')
    s.checar(atalhos.precisa_modificador('a') and not atalhos.precisa_modificador('f5'),
             'regra das letras sozinhas')
    for _g, acao, _r, combos in atalhos.ACOES:
        for c in combos:
            s.checar(atalhos.valido(c), f'padrao invalido: {acao} {c}')
    vistos = {}
    for _g, acao, _r, combos in atalhos.ACOES:
        for c in combos:
            s.checar(c not in vistos, f'{c} repetido em {acao} e {vistos.get(c)}')
            vistos[c] = acao


def gravar_tecla_pelo_painel():
    ctx = tc.montar()
    e = ctx.estado
    abrir_sub_aba(ctx, 2)
    clicar_painel(ctx, alvo('capturar', 'salvar_projeto'))
    s.checar(e.capturando_atalho == 'salvar_projeto', 'Alterar nao entrou no modo de gravar')
    # Letra sozinha e recusada, continua esperando
    tc.enviar(ctx, evento_tecla(pygame.K_w))
    s.checar(e.capturando_atalho == 'salvar_projeto', 'letra sozinha foi aceita')
    tc.enviar(ctx, evento_tecla(pygame.K_w, ctrl=True, shift=True))
    s.checar(e.capturando_atalho is None, 'nao saiu do modo de gravar')
    s.checar(atalhos.obter(e)['salvar_projeto'] == ['ctrl+shift+w'], atalhos.obter(e)['salvar_projeto'])
    # A tecla nova dispara a funcao; a antiga nao
    e.notificacoes = []
    tc.enviar(ctx, evento_tecla(pygame.K_w, ctrl=True, shift=True))
    s.checar(any('Nenhum projeto' in a['texto'] for a in e.notificacoes), 'tecla nova nao disparou Salvar')
    s.checar(atalhos.acao_do_combo(e, 'ctrl+s') is None, 'Ctrl+S continuou ligado')
    # Conflito: passar a mesma tecla para outra funcao tira da primeira
    tc.quadro(ctx)
    clicar_painel(ctx, alvo('capturar', 'capturar_tela'))
    tc.enviar(ctx, evento_tecla(pygame.K_w, ctrl=True, shift=True))
    s.checar(atalhos.obter(e)['capturar_tela'] == ['ctrl+shift+w'], 'conflito nao gravou')
    s.checar(atalhos.obter(e)['salvar_projeto'] == [], 'a outra funcao manteve a tecla repetida')
    # Esc cancela sem fechar o programa
    tc.quadro(ctx)
    clicar_painel(ctx, alvo('capturar', 'sair'))
    tc.enviar(ctx, evento_tecla(pygame.K_ESCAPE))
    s.checar(e.capturando_atalho is None and not e.solicitou_saida, 'Esc fechou o programa ou nao cancelou')
    s.checar(atalhos.obter(e)['sair'] == ['ctrl+q'], 'Esc mudou a tecla')
    # Backspace deixa sem tecla; botao padrao devolve
    tc.quadro(ctx)
    clicar_painel(ctx, alvo('capturar', 'sair'))
    tc.enviar(ctx, evento_tecla(pygame.K_BACKSPACE))
    s.checar(atalhos.obter(e)['sair'] == [], 'Backspace nao limpou')
    tc.quadro(ctx)
    clicar_painel(ctx, alvo('padrao_tecla', 'sair'))
    s.checar(atalhos.obter(e)['sair'] == ['ctrl+q'], 'padrao nao voltou')
    clicar_painel(ctx, alvo('restaurar_todas'))
    s.checar(atalhos.obter(e) == atalhos.normalizar(None), 'restaurar todas falhou')
    s.checar(e.perfil_alterado, 'mudanca de tecla nao marcou o perfil')
    # O menu mostra a tecla configurada
    atalhos.definir(e, 'novo_projeto', 'ctrl+alt+n')
    s.checar(e.menu_superior._texto_atalho('novo_projeto', e) == 'Ctrl+Alt+N', 'menu nao mostra a tecla nova')


def atalhos_do_workspace():
    ctx = tc.montar()
    e = ctx.estado
    tc.enviar(ctx, evento_tecla(pygame.K_1, alt=True))
    secao = next(x for x in e.secoes_inferiores if x['conteudo'] == 'escalas')
    s.checar(secao['expandido'], 'Alt+1 nao abriu Escalas')
    tc.enviar(ctx, evento_tecla(pygame.K_1, alt=True))
    s.checar(not secao['expandido'], 'Alt+1 de novo nao fechou')
    bpm = ctx.metronomo.bpm
    tc.enviar(ctx, evento_tecla(pygame.K_UP, ctrl=True))
    s.checar(ctx.metronomo.bpm == bpm + 5, 'Ctrl+cima nao subiu o BPM')
    tc.enviar(ctx, evento_tecla(pygame.K_m, ctrl=True))
    s.checar(ctx.metronomo.tocando, 'Ctrl+M nao ligou o metronomo')
    tc.enviar(ctx, evento_tecla(pygame.K_m, ctrl=True))
    s.checar(not ctx.metronomo.tocando, 'Ctrl+M nao parou o metronomo')


def presets_e_opcoes():
    ctx = tc.montar()
    e = ctx.estado
    abrir_sub_aba(ctx, 3)
    clicar_painel(ctx, alvo('preset', 'leve'))
    cfg = desempenho.obter(e)
    s.checar(cfg['preset'] == 'leve' and e.fps_alvo == 30, f'preset leve: {cfg}')
    s.checar(not ds.EFEITOS['sombras'] and not ds.EFEITOS['transparencias'], 'efeitos nao desligaram')
    s.checar(e.camera.zoom_suave is False, 'zoom suave ficou ligado')
    tc.quadro(ctx)      # desenha tudo sem sombras/transparencias
    clicar_painel(ctx, alvo('valor', ('fps', 60)))
    s.checar(cfg['fps'] == 60 and cfg['preset'] == 'personalizado', 'opcao avulsa nao virou personalizado')
    tc.quadro(ctx)
    clicar_painel(ctx, alvo('alternar', 'mostrar_fps'))
    s.checar(cfg['mostrar_fps'], 'mostrar FPS nao ligou')
    tc.quadro(ctx)
    s.checar(any(a == 'desempenho' for _r, a in e.botoes_cabecalho), 'contador de FPS nao apareceu na barra')
    clicar_painel(ctx, alvo('preset', 'maximo'))
    s.checar(e.fps_alvo == 120 and e.camera.zoom_suave and ds.EFEITOS['sombras'], 'preset maximo')
    desempenho.aplicar_preset(e, 'equilibrado')


def perfil_ida_e_volta():
    ctx = tc.montar()
    e = ctx.estado
    perfil = e.gerenciador_perfil
    atalhos.definir(e, 'capturar_tela', 'ctrl+alt+p')
    desempenho.aplicar_preset(e, 'leve')
    dados = perfil.montar_dados(e, ctx.configs, ctx.campo, None)
    s.checar(dados['atalhos'] == {'capturar_tela': ['ctrl+alt+p']}, dados['atalhos'])
    s.checar(dados['desempenho']['preset'] == 'leve', 'desempenho fora do perfil')
    caminho = os.path.join(tempfile.mkdtemp(), 'p.json')
    json.dump(dados, open(caminho, 'w'))
    ctx2 = tc.montar()
    ctx2.estado.gerenciador_perfil.carregar_perfil(caminho, ctx2.estado, ctx2.configs, ctx2.campo, None)
    s.checar(atalhos.obter(ctx2.estado)['capturar_tela'] == ['ctrl+alt+p'], 'tecla nao voltou do perfil')
    s.checar(ctx2.estado.fps_alvo == 30, 'desempenho nao voltou do perfil')
    # Perfil antigo (sem as chaves novas) carrega com os padroes
    del dados['atalhos'], dados['desempenho'], dados['interface']
    json.dump(dados, open(caminho, 'w'))
    ctx3 = tc.montar()
    ctx3.estado.gerenciador_perfil.carregar_perfil(caminho, ctx3.estado, ctx3.configs, ctx3.campo, None)
    s.checar(atalhos.obter(ctx3.estado) == atalhos.normalizar(None), 'perfil antigo sem teclas padrao')
    desempenho.aplicar_preset(ctx3.estado, 'equilibrado')


def auto_salvar():
    ctx = tc.montar()
    e = ctx.estado
    perfil = e.gerenciador_perfil
    pasta = tempfile.mkdtemp()
    original = (perfil.pasta_padrao, perfil.arquivo_config_global)
    perfil.pasta_padrao = pasta
    perfil.arquivo_config_global = os.path.join(pasta, 'config.json')
    json.dump({'tema_interface': 'claro', 'ultimo_perfil': ''}, open(perfil.arquivo_config_global, 'w'))
    try:
        atalhos.definir(e, 'sobre', 'f9')
        agora = time.time()
        perfil.tick_auto_salvar(e, ctx.configs, ctx.campo, None, agora)
        perfil.tick_auto_salvar(e, ctx.configs, ctx.campo, None, agora + 2)
        arquivo = os.path.join(pasta, 'Padrão.json')
        s.checar(os.path.exists(arquivo), 'auto-salvar nao criou o perfil Padrão')
        s.checar(json.load(open(arquivo, encoding='utf-8'))['atalhos'] == {'sobre': ['f9']},
                 'auto-salvar nao gravou a tecla')
        cfg = json.load(open(perfil.arquivo_config_global))
        s.checar(cfg.get('tema_interface') == 'claro', 'auto-salvar apagou o tema do config')
        s.checar(cfg.get('ultimo_perfil') == arquivo, 'o perfil Padrão nao virou o atual')
        # Sem mudanca, nao regrava
        mtime = os.path.getmtime(arquivo)
        time.sleep(0.02)
        s.checar(not perfil.salvar_automatico(e, ctx.configs, ctx.campo, None), 'regravou sem mudanca')
        s.checar(os.path.getmtime(arquivo) == mtime, 'arquivo mudou sem mudanca')
        # Mudanca de layout (sem marcar nada) entra na conferencia periodica
        e.dragger_metronomo.x += 37
        perfil.tick_auto_salvar(e, ctx.configs, ctx.campo, None, agora + 100)
        dados = json.load(open(arquivo, encoding='utf-8'))
        s.checar(dados['posicoes_draggers']['dragger_metronomo']['x'] == e.dragger_metronomo.x,
                 'mudanca de layout nao foi salva')
    finally:
        perfil.pasta_padrao, perfil.arquivo_config_global = original
        atalhos.restaurar(e)


def zoom_do_pedaco_visivel_igual():
    import core.modulos.modulo_camera as mc
    cam = mc.CameraWorkspace(1280, 720)
    import random
    random.seed(3)
    for _ in range(300):
        cor = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        pygame.draw.rect(cam.tela_virtual, cor, (random.randint(0, 3900), random.randint(0, 2900), 60, 40))
    for zoom, ox, oy in ((1.25, 300, 200), (0.6, 0, 0), (1.8, 1500.5, 900.25), (1.1, -50, -30)):
        cam.zoom, cam.offset_x, cam.offset_y = zoom, ox, oy
        novo = pygame.Surface((1280, 680))
        cam.renderizar(novo)
        antigo = pygame.Surface((1280, 680))
        grande = pygame.transform.scale(cam.tela_virtual, (int(4000 * zoom), int(3000 * zoom)))
        antigo.blit(grande, (-ox * zoom, -oy * zoom))
        a = pygame.surfarray.array3d(novo).astype(int)
        b = pygame.surfarray.array3d(antigo).astype(int)
        diferentes = (abs(a - b).sum(axis=2) > 30).mean()
        s.checar(diferentes < 0.03, f'zoom {zoom}: {diferentes:.1%} dos pixels diferentes')


def quadro_mais_rapido():
    """Mede o quadro do workspace: limpar so o visivel tem de ser bem mais barato."""
    ctx = tc.montar()
    cam = ctx.estado.camera
    area = cam.area_visivel(1920, 1040)
    for _ in range(3):
        ds.fundo_app(cam.tela_virtual, area=area)
    t = time.perf_counter()
    for _ in range(20):
        ds.fundo_app(cam.tela_virtual, area=area)
    parcial = (time.perf_counter() - t) / 20
    t = time.perf_counter()
    for _ in range(5):
        ds.fundo_app(cam.tela_virtual)
    inteiro = (time.perf_counter() - t) / 5
    print(f'          fundo: visivel {parcial * 1000:.1f} ms x mesa inteira {inteiro * 1000:.1f} ms')
    s.checar(parcial < inteiro * 0.6, 'limpar so a area visivel nao ficou mais rapido')


def editor_toca_som():
    """O Tocar do editor manda as notas para o motor (antes o callback era vazio),
    com a corda certa e sem quebrar no baixo de 4 cordas."""
    from ui.editor_musical import EditorMusical

    class MotorFalso:
        instrumento_atual = 'Guitarra'

        def __init__(self):
            self.notas = []

        def alternar_instrumento_synth(self, nome):
            self.instrumento_atual = nome

        def reproduzir_nota(self, corda, casa, tecnica='', duracao=0.3, volume=100):
            self.notas.append((self.instrumento_atual, corda, casa))

    ed = EditorMusical()
    ed._motor = MotorFalso()
    ed.dados.bpm = 1200
    ed.cursor = [0, 0]
    ed.escrever(3)               # corda mais grave da grade
    ed.cursor = [5, 1]
    ed.escrever(7)               # mais aguda
    ed.alternar_play()
    fim = time.time() + 3
    while ed.dados.playing and time.time() < fim:
        time.sleep(0.02)
    s.checar(('Guitarra', 6, 3) in ed._motor.notas and ('Guitarra', 1, 7) in ed._motor.notas,
             f'notas da guitarra: {ed._motor.notas}')
    ed.tocando = False
    ed.dados.alternar_instrumento('Baixo')
    ed._motor.notas.clear()
    ed.cursor = [3, 0]
    ed.escrever(2)
    ed.alternar_play()
    fim = time.time() + 3
    while ed.dados.playing and time.time() < fim:
        time.sleep(0.02)
    s.checar(('Baixo', 3, 2) in ed._motor.notas, f'notas do baixo: {ed._motor.notas}')


for nome, funcao in [
    ('editor: Tocar faz som (guitarra e baixo)', editor_toca_som),
    ('combinacoes: texto, evento, validade, sem repeticao', combinacoes),
    ('gravar tecla pelo painel (conflito, letra, Esc, Backspace, padrao)', gravar_tecla_pelo_painel),
    ('atalhos do workspace (abas e metronomo)', atalhos_do_workspace),
    ('desempenho: presets e opcoes avulsas', presets_e_opcoes),
    ('perfil leva teclas e desempenho (e perfil antigo)', perfil_ida_e_volta),
    ('auto-salvar no perfil', auto_salvar),
    ('zoom do pedaco visivel igual ao da mesa inteira', zoom_do_pedaco_visivel_igual),
    ('fundo so da area visivel e mais rapido', quadro_mais_rapido),
]:
    s.teste(nome, funcao)

s.encerrar()
