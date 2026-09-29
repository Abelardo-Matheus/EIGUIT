# -*- coding: utf-8 -*-
"""
Previews do estudo de Pedais, nos dois temas, em _preview_design/:
- pedais_lista        (todos os pedais agrupados)
- pedais_overdrive / pedais_delay / pedais_whammy / pedais_eq (pedal aberto)
- pedais_720p         (pedal aberto numa tela pequena)
- abas_estudos_pedais (a sub-aba Pedais no painel inferior)
"""
import os
import sys

import pygame

import harness
from harness import Contexto

from config.design_system import ds

SAIDA = sys.argv[1] if len(sys.argv) > 1 else '_preview_design'


def salvar(superficie, nome):
    os.makedirs(SAIDA, exist_ok=True)
    pygame.image.save(superficie, os.path.join(SAIDA, nome))
    print('  gerado', os.path.join(SAIDA, nome))


def pedal(ctx, id_pedal, nome_arquivo, largura, altura):
    import core.modulos.modulos_estudos as modulo_estudos
    from Estudos import curriculo_pedais as cur
    ctx.estado.LARGURA_TELA, ctx.estado.ALTURA_TELA = largura, altura
    gerenciador = modulo_estudos.GerenciadorEstudos()
    ctx.estado.tela_estudo_ativa = True
    ctx.estado.estudo_ativo = 'Pedais de Efeito'
    tela = pygame.Surface((largura, altura), pygame.SRCALPHA)
    ds.fundo_app(tela)
    gerenciador.desenhar_tela_estudo(tela, largura, altura, ctx.estado, ctx.fontes)
    if id_pedal:
        m = gerenciador.modulo_pedais
        m.abrir_pedal(cur.PEDAIS_POR_ID[id_pedal])
        m.reprodutor.aguardar()
        ds.fundo_app(tela)
        gerenciador.desenhar_tela_estudo(tela, largura, altura, ctx.estado, ctx.fontes)
    salvar(tela, nome_arquivo)
    gerenciador._limpar_modulos()


def aba_estudos(ctx, tema):
    from ui.components import desenhar_secoes_inferiores_expansiveis
    for secao in ctx.estado.secoes_inferiores:
        secao['expandido'] = secao['conteudo'] == 'estudos'
        if secao['conteudo'] == 'estudos':
            secao['memoria_sub_aba'] = secao['sub_abas'].index('Pedais')
    ctx.estado.dragger_painel_inferior.y = 260
    ctx.estado.dragger_painel_inferior.largura = 1600 - 80
    tela = pygame.Surface((1600, 900), pygame.SRCALPHA)
    ds.fundo_app(tela)
    desenhar_secoes_inferiores_expansiveis(
        tela, ctx.estado, ctx.configs, ctx.escalas, ctx.fontes, ctx.metronomo,
        ctx.processador, ctx.gravador, ctx.jogos)
    salvar(tela, f'abas_estudos_pedais_{tema}.png')


if __name__ == '__main__':
    for tema in harness.TEMAS:
        print(f'[{tema}]')
        harness.definir_tema(tema)
        ctx = Contexto(1920, 1080, tema)
        pedal(ctx, None, f'pedais_lista_{tema}.png', 1920, 1080)
        for id_pedal in ('overdrive', 'delay', 'whammy', 'eq'):
            pedal(ctx, id_pedal, f'pedais_{id_pedal}_{tema}.png', 1920, 1080)
        pedal(ctx, 'flanger', f'pedais_720p_{tema}.png', 1280, 720)
        pedal(ctx, None, f'pedais_lista_720p_{tema}.png', 1280, 720)
        aba_estudos(Contexto(1600, 900, tema), tema)
    print('preview_pedais concluido')
