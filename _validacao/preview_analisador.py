# -*- coding: utf-8 -*-
"""
Previews do Analisador IA, nos dois temas, em _preview_design/:
- analisador_1_audio        (dispositivos simulados, medidor, latencia)
- analisador_2_instrumento  (com um timbre base calibrado)
- analisador_3_musica       (referencia carregada, trecho, MIDI)
- analisador_4_gravacao     (tres takes, um com aviso)
- analisador_5_<aba>        (resultado: sugestoes, graficos, medidas,
                             historico, preset sugerido, detector)
- analisador_720p           (resultado numa tela pequena)
- abas_ia_analisador        (a sub-aba Analisador no painel inferior)
Tudo sem placa de som: a gravacao usa o BackendSimulado.

    python3 _validacao/preview_analisador.py [pasta_saida]
"""
import os
import sys
import tempfile

os.environ.setdefault('APPDATA', tempfile.mkdtemp(prefix='eiguit_preview_'))

import numpy as np  # noqa: E402
import pygame  # noqa: E402

import harness  # noqa: E402
from harness import Contexto  # noqa: E402

from config.design_system import ds  # noqa: E402

SAIDA = sys.argv[1] if len(sys.argv) > 1 else '_preview_design'


def salvar(superficie, nome):
    os.makedirs(SAIDA, exist_ok=True)
    pygame.image.save(superficie, os.path.join(SAIDA, nome))
    print('  gerado', os.path.join(SAIDA, nome))


LISTA_FALSA = {
    'entradas': [
        {'id': 3, 'nome': 'Pedaleira USB (4 canais)', 'api': 'WASAPI', 'canais_entrada': 4, 'canais_saida': 2,
         'taxa_padrao': 48000, 'latencia_baixa_ms': 5.0},
        {'id': 1, 'nome': 'Microfone (Realtek)', 'api': 'MME', 'canais_entrada': 2, 'canais_saida': 0,
         'taxa_padrao': 44100, 'latencia_baixa_ms': 10.0}],
    'saidas': [
        {'id': 3, 'nome': 'Pedaleira USB (4 canais)', 'api': 'WASAPI', 'canais_entrada': 4, 'canais_saida': 2,
         'taxa_padrao': 48000, 'latencia_baixa_ms': 5.0},
        {'id': 5, 'nome': 'Alto-falantes (Realtek)', 'api': 'MME', 'canais_entrada': 0, 'canais_saida': 2,
         'taxa_padrao': 44100, 'latencia_baixa_ms': 10.0}],
    'erro': ''}


def montar(largura=1920, altura=1080, tema='escuro'):
    """Analisador com referencia, takes simulados e analise pronta (sincrono)."""
    import core.modulos.modulos_estudos as me
    import sinais_analisador as sa
    from audio import analise_timbre as at
    from audio import dispositivos as disp
    from audio import gravacao_playalong as gp
    ctx = Contexto(largura, altura, tema)
    est = ctx.estado
    est.tela_estudo_ativa, est.estudo_ativo = True, 'Analisador IA'
    g = me.GerenciadorEstudos()
    est.gerenciador_estudos = g
    tela = pygame.Surface((largura, altura), pygame.SRCALPHA)
    g.desenhar_tela_estudo(tela, largura, altura, est, ctx.fontes)
    an = g.modulo_analisador
    # dispositivos de mentira
    disp.disponivel = lambda: (True, '')
    disp.taxas_suportadas = lambda *a, **k: [44100, 48000, 96000]
    an.__dict__.pop('_memo_ui', None)                # esquece o "sem placa de som" do primeiro quadro
    an.lista = LISTA_FALSA
    an.cfg = disp.ConfigAudio(entrada_id=3, entrada_nome=LISTA_FALSA['entradas'][0]['nome'], saida_id=3,
                              saida_nome=LISTA_FALSA['saidas'][0]['nome'], canais_entrada=4, canal_processado=0,
                              canal_di=1, taxa=44100, buffer=256, latencia_ms=23.0)
    an.medidor.iniciar = lambda *a, **k: True
    an.medidor.ativo = True
    an.medidor.niveis = lambda: [(-9.0, -21.0, False, False), (-14.0, -27.0, False, False),
                                 (-80.0, -90.0, False, True), (-0.2, -8.0, True, False)]
    # referencia: overdrive + delay + reverb
    base = sa.com_ruido(sa.base_humana('staccato'))
    ref = sa.cadeia(base, ('overdrive', {'drive': 0.55}), ('eq', {'medios': 6}), ('delay', {'time': 450}),
                    ('reverb', {'decay': 1.8, 'mix': 0.25}))
    caminho = os.path.join(os.environ['APPDATA'], 'ref_preview.wav')
    at.salvar_wav(caminho, ref, sa.SR)
    an.selecionar({'caminho': caminho, 'titulo': 'Riff de referência (exemplo)', 'tipo': 'isolado'})
    an.tarefa[0].aguardar(60)
    an._checar_tarefa()
    an.sel = [0.05, 0.95]
    an.bpm, an.bpm_fonte = 100.0, 'MIDI'
    # tres takes simulados
    tocado = sa.com_ruido(sa.base_humana('staccato', semente=9))
    od = sa.aplicar(tocado, 'overdrive', drive=0.8)
    trecho = an.audio_trecho(44100)
    _, i0, _ = gp.montar_playback(trecho, 44100, an.bpm, 1)

    ini = int(an.trecho()[0] * sa.SR)                # o musico toca o mesmo trecho da musica

    def musico(saida, sr):
        y = np.zeros((saida.shape[0], 2))
        n = min(od.size - ini, y.shape[0] - i0)
        y[i0:i0 + n, 0], y[i0:i0 + n, 1] = od[ini:ini + n], tocado[ini:ini + n]
        return y
    for k, (lat, vaz) in enumerate(((23.0, 0.0), (23.0, 0.6), (23.0, 0.0))):
        take = gp.tocar_e_gravar(trecho, an.cfg, bpm=an.bpm, compassos_contagem=1,
                                 backend=gp.BackendSimulado(lat, musico, vazamento=vaz))
        take['numero'] = k + 1
        an.takes.append(take)
    an.take_sel = 2
    an.perfil_guitarra = at.perfil_timbre(tocado, sa.SR, efeitos=False)
    return ctx, g, an, tela


def desenhar(ctx, g, tela, largura, altura):
    ds.fundo_app(tela)
    g.desenhar_tela_estudo(tela, largura, altura, ctx.estado, ctx.fontes)


def aba_ia(tema, gravar=True):
    from ui.components import desenhar_secoes_inferiores_expansiveis
    ctx = Contexto(1600, 900, tema)
    for secao in ctx.estado.secoes_inferiores:
        secao['expandido'] = secao['conteudo'] == 'analise_ia'
        if secao['conteudo'] == 'analise_ia':
            secao['memoria_sub_aba'] = secao['sub_abas'].index('Analisador')
    ctx.estado.dragger_painel_inferior.y = 260
    ctx.estado.dragger_painel_inferior.largura = 1600 - 80
    tela = pygame.Surface((1600, 900), pygame.SRCALPHA)
    ds.fundo_app(tela)
    desenhar_secoes_inferiores_expansiveis(tela, ctx.estado, ctx.configs, ctx.escalas, ctx.fontes,
                                           ctx.metronomo, ctx.processador, ctx.gravador, ctx.jogos)
    if gravar:
        salvar(tela, f'abas_ia_analisador_{tema}.png')
    return ctx


if __name__ == '__main__':
    for tema in harness.TEMAS:
        print(f'[{tema}]')
        harness.definir_tema(tema)
        ctx, g, an, tela = montar(1920, 1080, tema)
        nomes = ['1_audio', '2_instrumento', '3_musica', '4_gravacao']
        for i, nome in enumerate(nomes):
            an.etapa = i
            desenhar(ctx, g, tela, 1920, 1080)
            salvar(tela, f'analisador_{nome}_{tema}.png')
        an.etapa = 4
        an.analisar()
        an.tarefa[0].aguardar(120)
        an._checar_tarefa()
        an.buscar_preset()
        an.tarefa[0].aguardar(180)
        an._checar_tarefa()
        for aba in ('sugestoes', 'graficos', 'medidas', 'historico', 'preset', 'detector'):
            an.aba = aba
            desenhar(ctx, g, tela, 1920, 1080)
            salvar(tela, f'analisador_5_{aba}_{tema}.png')
        tela720 = pygame.Surface((1280, 720), pygame.SRCALPHA)
        ctx.estado.LARGURA_TELA, ctx.estado.ALTURA_TELA = 1280, 720
        an.aba = 'sugestoes'
        desenhar(ctx, g, tela720, 1280, 720)
        salvar(tela720, f'analisador_720p_{tema}.png')
        g._limpar_modulos()
        aba_ia(tema)
    print('preview_analisador concluido')
