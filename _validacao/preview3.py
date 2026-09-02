# -*- coding: utf-8 -*-
"""
Previews das telas grandes: acordes, estudos, configuracoes e criacao musical.

Gera, nos dois temas, em _preview_design/:
- acordes_caged / acordes_triades / acordes_setimas
- caged                (o painel CAGED sozinho, em tamanho cheio)
- estudos_notas / estudos_padroes / estudos_improvisacao
- configuracoes        (a aba de configuracao do painel inferior)
- criacao_tablatura / criacao_partitura
"""
import os

import pygame

import harness
from harness import Contexto

from config.design_system import ds
from ui.blocks.painel_acordes import PainelAcordes

SAIDA = '_preview_design'
LARGURA, ALTURA = 1600, 900


def salvar(superficie, nome):
    os.makedirs(SAIDA, exist_ok=True)
    pygame.image.save(superficie, os.path.join(SAIDA, nome))
    print('  gerado', os.path.join(SAIDA, nome))


def tela_nova():
    tela = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    ds.fundo_app(tela)
    return tela


def acordes(ctx, familia, nome_arquivo, tema):
    painel = PainelAcordes()
    painel.familia = familia
    tela = tela_nova()
    painel.desenhar(tela, pygame.Rect(40, 40, LARGURA - 80, ALTURA - 80),
                    ctx.fontes, ctx.campo, ctx.estado)
    salvar(tela, f'{nome_arquivo}_{tema}.png')


def estudo(ctx, nome_estudo, nome_arquivo, tema):
    import core.modulos.modulos_estudos as modulo_estudos
    gerenciador = modulo_estudos.GerenciadorEstudos()
    ctx.estado.tela_estudo_ativa = True
    ctx.estado.estudo_ativo = nome_estudo
    tela = tela_nova()
    gerenciador.desenhar_tela_estudo(tela, LARGURA, ALTURA, ctx.estado, ctx.fontes)
    salvar(tela, f'{nome_arquivo}_{tema}.png')


def configuracoes(ctx, tema):
    from ui.components import desenhar_secoes_inferiores_expansiveis
    for secao in ctx.estado.secoes_inferiores:
        secao['expandido'] = secao['conteudo'] == 'configuracao'
    ctx.estado.dragger_painel_inferior.y = 260
    ctx.estado.dragger_painel_inferior.largura = LARGURA - 80
    tela = tela_nova()
    desenhar_secoes_inferiores_expansiveis(
        tela, ctx.estado, ctx.configs, ctx.escalas, ctx.fontes, ctx.metronomo,
        ctx.processador, ctx.gravador, ctx.jogos)
    salvar(tela, f'configuracoes_{tema}.png')
    for secao in ctx.estado.secoes_inferiores:
        secao['expandido'] = False


def criacao(ctx, tema):
    from ui.editor_musical import EditorMusical
    editor = EditorMusical()
    editor.cursor = [0, 0]
    for corda, casa in [(0, 3), (1, 2), (2, 0), (3, 0), (1, 5), (2, 7)]:
        editor.dados.adicionar_nota(corda, casa, corda + casa)
    for visao, nome in ((0, 'criacao_tablatura'), (1, 'criacao_partitura')):
        editor.visao = visao
        tela = tela_nova()
        editor.desenhar_interface_tab(tela, ctx.estado, ctx.fontes, LARGURA,
                                      ALTURA, ctx.configs, ctx.campo)
        salvar(tela, f'{nome}_{tema}.png')


if __name__ == '__main__':
    for tema in harness.TEMAS:
        print(f'[{tema}]')
        harness.definir_tema(tema)
        ctx = Contexto(LARGURA, ALTURA, tema)
        acordes(ctx, 'caged', 'acordes_caged', tema)
        acordes(ctx, 'caged', 'caged', tema)
        acordes(ctx, 'triades_maior', 'acordes_triades', tema)
        acordes(ctx, 'setimas', 'acordes_setimas', tema)
        estudo(ctx, 'Notas', 'estudos_notas', tema)
        estudo(ctx, 'Padrões', 'estudos_padroes', tema)
        estudo(ctx, 'Improvisação', 'estudos_improvisacao', tema)
        configuracoes(ctx, tema)
        criacao(ctx, tema)
    print('preview3 concluido')
