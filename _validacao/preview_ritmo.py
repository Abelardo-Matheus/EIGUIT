# -*- coding: utf-8 -*-
"""
Previews do jogo de ritmo (Rhythm Hero).

Gera, nos dois temas, em _preview_design/:
- ritmo_ajustes_<tema>.png   : a tela de ajustes, antes de comecar
- ritmo_jogo_<tema>.png      : a pista com as figuras correndo
- ritmo_resultado_<tema>.png : o resumo do fim da rodada
"""
import os
import time

import pygame

import harness
from harness import Contexto

from Jogos.jogo2 import RhythmHero

SAIDA = '_preview_design'
LARGURA, ALTURA = 1600, 900


def salvar(superficie, nome):
    os.makedirs(SAIDA, exist_ok=True)
    caminho = os.path.join(SAIDA, nome)
    pygame.image.save(superficie, caminho)
    print('  gerado', caminho)


def tela_nova():
    return pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)


def ajustes(ctx, jogo):
    tela = tela_nova()
    jogo.jogo_iniciado = False
    jogo.mostrar_resultado = False
    jogo.desenhar(tela, LARGURA, ALTURA, ctx.estado, None, ctx.configs)
    return tela


def jogando(ctx, jogo):
    tela = tela_nova()
    jogo.iniciar_jogo()
    # Recua o inicio para as figuras ja estarem correndo na pista
    jogo.tempo_inicio -= 4.0
    jogo.primeira_valida -= 4.0
    jogo.pontuacao = 1840
    jogo.sequencia = 12
    jogo.melhor_sequencia = 18
    for i, (rotulo, _a, _b) in enumerate(__import__('Jogos.jogo2', fromlist=['GRAUS_ACERTO']).GRAUS_ACERTO):
        jogo.contagem_graus[rotulo] = 9 - i * 2
    jogo.desvios_ms = [-18.0, 12.0, -5.0, 30.0, -22.0, 8.0]
    jogo.desenhar(tela, LARGURA, ALTURA, ctx.estado, None, ctx.configs)
    return tela


def resultado(ctx, jogo):
    tela = tela_nova()
    jogo.parar_jogo()
    jogo.mostrar_resultado = True
    jogo.jogo_iniciado = False
    jogo.desenhar(tela, LARGURA, ALTURA, ctx.estado, None, ctx.configs)
    return tela


if __name__ == '__main__':
    for tema in harness.TEMAS:
        print(f'[{tema}]')
        harness.definir_tema(tema)
        ctx = Contexto(LARGURA, ALTURA, tema)
        jogo = RhythmHero()
        jogo.inicializar(LARGURA, ALTURA)
        salvar(ajustes(ctx, jogo), f'ritmo_ajustes_{tema}.png')
        salvar(jogando(ctx, jogo), f'ritmo_jogo_{tema}.png')
        salvar(resultado(ctx, jogo), f'ritmo_resultado_{tema}.png')
    print('preview_ritmo concluido')
