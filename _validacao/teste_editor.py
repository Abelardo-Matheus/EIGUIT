# -*- coding: utf-8 -*-
"""
Suite do editor musical (Criacao Musical).

Escreve uma peca curta pelo teclado, anda com o cursor, troca de visao e de
instrumento e exporta, tudo sem tocar nos arquivos do usuario: o salvar so e
exercitado na estrutura de dados, nao no disco do perfil.
"""
import io

import pygame

import harness
from harness import Contexto, Suite

from ui.editor_musical import EditorMusical, valor_da_celula

s = Suite('teste_editor')


def montar(tema='escuro'):
    ctx = Contexto(tema=tema)
    editor = EditorMusical()
    editor.desenhar_interface_tab(ctx.tela, ctx.estado, ctx.fontes,
                                  ctx.largura, ctx.altura, ctx.configs, ctx.campo)
    return ctx, editor


def tecla(editor, ctx, chave, unicode=''):
    return editor.tratar_evento(pygame.event.Event(
        pygame.KEYDOWN, {'key': chave, 'unicode': unicode, 'mod': 0}), ctx.estado)


def desenha_nas_duas_visoes():
    for tema in harness.TEMAS:
        ctx, editor = montar(tema)
        for visao in range(max(1, len(editor.rects_visao))):
            editor.visao = visao
            editor.desenhar_interface_tab(ctx.tela, ctx.estado, ctx.fontes,
                                          ctx.largura, ctx.altura, ctx.configs,
                                          ctx.campo)


def escrever_notas():
    ctx, editor = montar()
    editor.cursor = [0, 0]
    editor.escrever(5)
    s.checar(valor_da_celula(editor.grade[0][0]) == 5, 'o 5 entrou na celula')
    editor.escrever(7)
    s.checar(valor_da_celula(editor.grade[0][0]) == 57 % 25 or
             valor_da_celula(editor.grade[0][0]) in (7, 57),
             f'segundo digito: {editor.grade[0][0]}')
    editor.apagar()
    s.checar(valor_da_celula(editor.grade[0][0]) is None, 'a celula foi apagada')


def casa_nao_passa_do_braco():
    ctx, editor = montar()
    editor.cursor = [0, 0]
    editor.escrever(9)
    editor.escrever(9)
    valor = valor_da_celula(editor.grade[0][0])
    s.checar(valor is None or valor <= 24, f'casa impossivel: {valor}')


def cursor_anda_e_cresce_a_peca():
    ctx, editor = montar()
    editor.cursor = [0, 0]
    editor.mover(1, 0)
    s.checar(editor.cursor[0] == 1, 'o cursor desceu uma corda')
    editor.mover(-5, 0)
    s.checar(editor.cursor[0] == 0, 'o cursor parou na primeira corda')
    tempos_antes = editor.num_tempos
    for _ in range(tempos_antes + 4):
        editor.mover(0, 1)
    s.checar(editor.num_tempos > tempos_antes,
             'a peca cresce quando o cursor chega ao fim')


def trocar_instrumento_refaz_a_grade():
    ctx, editor = montar()
    for rect, nome in editor.rects_instrumento:
        editor.tratar_evento(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {'pos': rect.center, 'button': 1}), ctx.estado)
        s.checar(editor.instrumento == nome, f'o instrumento nao virou {nome}')
        s.checar(editor.cursor == [0, 0], 'o cursor volta ao inicio')
        s.checar(editor.num_cordas == len(editor.grade), 'grade incoerente')
        editor.desenhar_interface_tab(ctx.tela, ctx.estado, ctx.fontes,
                                      ctx.largura, ctx.altura, ctx.configs, ctx.campo)


def clicar_numa_celula_move_o_cursor():
    ctx, editor = montar()
    s.checar(editor.rects_celulas, 'o editor guardou as celulas clicaveis')
    rect, (corda, tempo) = editor.rects_celulas[len(editor.rects_celulas) // 2]
    editor.tratar_evento(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {'pos': rect.center, 'button': 1}), ctx.estado)
    s.checar(editor.cursor == [corda, tempo],
             f'o cursor foi para {editor.cursor}, esperado {[corda, tempo]}')


def play_sem_som_nao_trava():
    ctx, editor = montar()
    editor.alternar_play(None)
    editor.atualizar_playhead()
    editor.alternar_play(None)
    s.checar(editor.tocando is False, 'o play desligou')


def roda_do_mouse_rola():
    ctx, editor = montar()
    editor.tratar_evento(pygame.event.Event(pygame.MOUSEWHEEL, {'y': -3, 'x': 0}))
    s.checar(editor.scroll >= 0, 'o scroll nao pode ficar negativo')
    editor.tratar_evento(pygame.event.Event(pygame.MOUSEWHEEL, {'y': 30, 'x': 0}))
    s.checar(editor.scroll == 0, 'o scroll voltou ao topo')


def exportar_gera_texto():
    """O arquivo sai numa pasta temporaria, para nao sujar o projeto."""
    import os
    import tempfile
    ctx, editor = montar()
    editor.cursor = [0, 0]
    editor.escrever(3)
    anterior = os.getcwd()
    with tempfile.TemporaryDirectory() as pasta:
        os.chdir(pasta)
        try:
            caminho = editor.exportar()
            s.checar(caminho and os.path.exists(caminho),
                     'exportar escreveu o arquivo de texto')
            conteudo = io.open(caminho, encoding='utf-8').read()
            s.checar('|' in conteudo and str(editor.dados.bpm) in conteudo,
                     'o texto exportado tem as cordas e o andamento')
        finally:
            os.chdir(anterior)


s.teste('desenha nos dois temas e nas duas visoes', desenha_nas_duas_visoes)
s.teste('escrever e apagar notas', escrever_notas)
s.teste('a casa digitada nao passa do braco', casa_nao_passa_do_braco)
s.teste('cursor anda e a peca cresce', cursor_anda_e_cresce_a_peca)
s.teste('trocar instrumento refaz a grade', trocar_instrumento_refaz_a_grade)
s.teste('clicar numa celula move o cursor', clicar_numa_celula_move_o_cursor)
s.teste('play sem som nao trava', play_sem_som_nao_trava)
s.teste('roda do mouse rola dentro do limite', roda_do_mouse_rola)
s.teste('exportar gera arquivo de texto', exportar_gera_texto)
s.encerrar()
