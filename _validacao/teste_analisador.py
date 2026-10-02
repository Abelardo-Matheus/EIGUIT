# -*- coding: utf-8 -*-
"""
Suite do Analisador IA (ANALISE DE IA > Analisador).

Tudo sem placa de som e sem rede: os sinais sao guitarras do proprio projeto
(sinais_analisador.py: sintetizada "humana" e o sampler de DI real) passando
por efeitos conhecidos do motor de pedais, e a gravacao usa o
BackendSimulado (latencia e "musico" de mentira).

Cobre:
  motor      aplicar_efeito / renderizar_cadeia em audio linear, sem mudar o loop do estudo
  config     cada instrumento carrega; cada detector tem os limiares no JSON
  detectores efeito conhecido -> detectado, com parametro dentro da tolerancia
             (delay +-10%, tremolo/vibrato +-15%); audio limpo -> nada com
             confianca alta; ganho em ordem (limpo < overdrive < distorcao)
  comparacao Overdrive+Delay x Overdrive -> "Falta: Delay" em primeiro;
             mesmo audio em volumes diferentes -> compatibilidade ~100
  gravacao   alinhamento com latencia simulada, calibracao, validacao do take
             (silencio, clipping, curto, musica vazando na entrada)
  referencia importar/buscar sem acento, BPM, compassos do MIDI
  fase 2     o preset sugerido aproxima o som (indice sobe) e traz o delay
  fase 3     treino local (se houver scikit-learn) e o reforco das regras
  interface  as cinco etapas e as abas do resultado em tres resolucoes e dois
             temas, cartao na sub-aba, cliques, link para o pedal e ESC

    python3 _validacao/teste_analisador.py
"""
import os
import sys
import tempfile

os.environ['APPDATA'] = tempfile.mkdtemp(prefix='eiguit_teste_analisador_')

import numpy as np  # noqa: E402
import pygame  # noqa: E402

import harness  # noqa: E402
from harness import Contexto, Suite  # noqa: E402

import sinais_analisador as sa  # noqa: E402
from audio import analise_timbre as at  # noqa: E402
from audio import detectores_efeitos as det  # noqa: E402
from audio import dispositivos as disp  # noqa: E402
from audio import efeitos_pedais as motor  # noqa: E402
from audio import gravacao_playalong as gp  # noqa: E402
from audio import referencia as refm  # noqa: E402
from audio import sugestoes_timbre as st  # noqa: E402
from audio import treinar_detector as td  # noqa: E402
from Estudos import curriculo_pedais as cur  # noqa: E402

import warnings  # noqa: E402
warnings.filterwarnings('ignore')

# as regras sao testadas sozinhas (um modelo treinado no projeto mudaria os scores)
td._desligar_reforco = True
s = Suite('teste_analisador')
FONTES = (('humana', sa.base_humana), ('DI', sa.base_di))


def _perfil(x):
    return at.perfil_timbre(x, sa.SR)


def _sinal(fonte, base, efeito=None, **params):
    x = sa.com_ruido(fonte(base))
    if efeito == 'gate':
        x = motor._preparar_entrada('gate', x, sa.SR)
    return sa.aplicar(x, efeito, **params) if efeito else x


# ------------------------------------------------------------------ motor --
def motor_linear():
    x = np.zeros(sa.SR * 2)
    x[1000] = 1.0
    y = motor.aplicar_efeito(x, sa.SR, 'delay', {'time': 300, 'feedback': 0.5, 'mix': 1.0, 'tom': 1.0})
    eco = 1000 + int(0.3 * sa.SR)
    s.checar(np.max(np.abs(y[eco - 40:eco + 40])) > 0.5, 'eco linear fora do lugar')
    s.checar(np.max(np.abs(y[:900])) < 1e-6, 'convolucao linear nao pode dobrar a cauda para o comeco')
    cadeia = motor.renderizar_cadeia(sa.base_humana('riff', 1), sa.SR,
                                     [('overdrive', cur.valores_padrao(cur.PEDAIS_POR_ID['overdrive'])),
                                      {'id': 'chorus', 'params': cur.valores_padrao(cur.PEDAIS_POR_ID['chorus'])},
                                      {'id': 'delay', 'params': {'time': 300}, 'ligado': False}])
    s.checar(cadeia.ndim == 2 and np.isfinite(cadeia).all() and np.max(np.abs(cadeia)) <= 0.96,
             'cadeia (com pedal estereo e um desligado) invalida')
    for p in cur.PEDAIS:
        y = motor.aplicar_efeito(sa.base_humana('riff', 1)[:sa.SR * 2], sa.SR, p['id'], cur.valores_padrao(p))
        s.checar(np.isfinite(y).all(), f"{p['id']}: NaN no audio linear")
    loop = motor.renderizar('delay', cur.valores_padrao(cur.PEDAIS_POR_ID['delay']), 'staccato')
    s.checar(np.max(np.abs(loop[:200])) > 0, 'o loop do estudo de Pedais continua circular (cauda no comeco)')


def config_completa():
    ids = [i for i, _ in at.listar_instrumentos()]
    s.checar(set(ids) >= {'guitarra', 'violao', 'baixo'}, f'instrumentos faltando: {ids}')
    for i in ids:
        cfg = at.carregar_config(i)
        s.checar(cfg['instrumento'] == i, f'{i}: config nao carregou')
        for k in ('interacoes', 'ganho', 'delay', 'reverb', 'tremolo', 'vibrato', 'chorus', 'phaser', 'flanger',
                  'wah', 'autowah', 'octaver', 'ring', 'compressor', 'volume', 'gate'):
            s.checar(k in cfg['detectores'], f'{i}: limiares de {k} faltando no config')
    s.checar(at.carregar_config('baixo')['bandas_macro']['graves'][0] == 40, 'bandas do baixo devem comecar em 40 Hz')
    perfil = _perfil(_sinal(sa.base_humana, 'riff'))
    s.checar(set(p['id'] for p in cur.PEDAIS) <= set(perfil['efeitos']), 'algum pedal do motor ficou sem detector')
    for chave, m in perfil['medidas'].items():
        s.checar({'valor', 'unidade', 'confianca', 'familia', 'nome'} <= set(m), f'medida {chave} incompleta')


def lufs_e_alinhamento():
    x = _sinal(sa.base_humana, 'riff')
    s.checar(abs(at.lufs(x, sa.SR) - at.lufs(x * 0.1, sa.SR) - 20) < 0.2, 'LUFS nao escala com o ganho')
    a = at.preprocessar(x, sa.SR)
    atraso = int(0.087 * at.SR_ANALISE)
    b = np.concatenate([np.zeros(atraso), a])[:a.size]
    d, conf = at.alinhar(a, b, at.SR_ANALISE, 0.0, 0.3)
    s.checar(abs(d - 0.087) < 0.008 and conf > 0.4, f'alinhamento: {d * 1000:.1f} ms (esperado 87), conf {conf:.2f}')


# -------------------------------------------------------------- detectores --
CASOS = [
    # (efeito, base, params, fontes que precisam dar "sim", checagem de parametro)
    ('delay', 'staccato', {'time': 300}, ('humana', 'DI'), ('time', 300, 0.10)),
    ('delay', 'riff', {'time': 450}, ('humana', 'DI'), ('time', 450, 0.10)),
    ('delay', 'power', {'time': 620, 'mix': 0.3}, ('DI',), ('time', 620, 0.10)),
    ('tremolo', 'acorde', {'rate': 7.0}, ('humana', 'DI'), ('rate', 7.0, 0.15)),
    ('tremolo', 'nota', {'rate': 3.5}, ('humana', 'DI'), ('rate', 3.5, 0.15)),
    ('vibrato', 'nota', {'rate': 6.0}, ('humana', 'DI'), ('rate', 6.0, 0.15)),
    ('chorus', 'acorde', {}, ('humana', 'DI'), None),
    ('chorus', 'power', {}, ('humana', 'DI'), None),
    ('phaser', 'nota', {}, ('DI',), ('rate', 0.625, 0.15)),
    ('flanger', 'nota', {}, ('DI',), None),
    ('wah', 'riff', {}, ('humana', 'DI'), None),
    ('autowah', 'riff', {}, ('DI',), None),
    ('octaver', 'riff', {}, ('humana', 'DI'), None),
    ('ring', 'riff', {'freq': 150}, ('humana', 'DI'), None),
    ('ring', 'nota', {'freq': 150}, ('humana', 'DI'), None),
    ('gate', 'staccato', {}, ('humana', 'DI'), None),
    ('compressor', 'nota', {}, ('humana',), None),
    ('volume', 'nota', {'ataque': 0.5}, ('humana', 'DI'), None),
    ('reverb', 'staccato', {'decay': 1.0}, ('humana', 'DI'), None),
    ('reverb', 'staccato', {'decay': 3.0}, ('humana', 'DI'), None),
]


def detecta_efeitos_conhecidos():
    for efeito, base, params, precisa, checa in CASOS:
        for nome, fonte in FONTES:
            if nome not in precisa:
                continue
            r = _perfil(_sinal(fonte, base, efeito, **params))['efeitos'][efeito]
            s.checar(r['presenca'] == 'sim',
                     f'{efeito} em {base} ({nome}): {r["presenca"]} (score {r["score"]:.2f}) - {r["motivo"]}')
            if checa:
                chave, esperado, tol = checa
                v = r['parametros'].get(chave)
                s.checar(v is not None and abs(v - esperado) <= tol * esperado,
                         f'{efeito} em {base} ({nome}): {chave} {v} (esperado {esperado} +-{tol * 100:.0f}%)')


def phaser_flanger_familia():
    """Phaser e flanger se confundem: pelo menos a "varredura" tem que aparecer."""
    for efeito, base in (('phaser', 'acorde'), ('flanger', 'acorde'), ('phaser', 'nota'), ('flanger', 'nota')):
        for nome, fonte in FONTES:
            e = _perfil(_sinal(fonte, base, efeito))['efeitos']
            fam = max(e['phaser']['score'], e['flanger']['score'])
            s.checar(fam >= 0.3, f'{efeito} em {base} ({nome}): varredura nao apareceu ({fam:.2f})')


def reverb_curto_x_longo():
    """Cauda longa tem que medir "mais reverb": RT60 maior ou cauda mais alta (a pausa pode ser curta demais para o RT)."""
    for nome, fonte in FONTES:
        m_c = _perfil(_sinal(fonte, 'staccato', 'reverb', decay=0.8, mix=0.35))['medidas']
        m_l = _perfil(_sinal(fonte, 'staccato', 'reverb', decay=3.0, mix=0.35))['medidas']
        rt_c, rt_l = m_c['reverb_rt60']['valor'], m_l['reverb_rt60']['valor']
        cd_c, cd_l = m_c['reverb_cauda']['valor'], m_l['reverb_cauda']['valor']
        s.checar(None not in (rt_c, rt_l, cd_c, cd_l), f'reverb ({nome}): cauda nao medida')
        s.checar(rt_l > rt_c * 1.4 or cd_l > cd_c + 3,
                 f'reverb ({nome}): longo (RT {rt_l:.2f} s, cauda {cd_l:.0f} dB) nao mediu mais que o curto '
                 f'(RT {rt_c:.2f} s, cauda {cd_c:.0f} dB)')


def limpo_sem_falso_positivo():
    for base in motor.ORDEM_BASES:
        for nome, fonte in FONTES:
            ef = _perfil(_sinal(fonte, base))['efeitos']
            fortes = [f"{k} ({v['score']:.2f})" for k, v in ef.items()
                      if v['presenca'] == 'sim' and v['confianca'] > 0.7]
            s.checar(not fortes, f'audio limpo ({base}, {nome}) detectou: {", ".join(fortes)}')


def ganho_em_ordem():
    for base in ('riff', 'power', 'acorde'):
        for nome, fonte in FONTES:
            g = [_perfil(_sinal(fonte, base, e))['medidas']['indice_ganho']['valor']
                 for e in (None, 'overdrive', 'distorcao')]
            s.checar(g[0] < g[1] < g[2] and g[2] - g[0] > 0.4,
                     f'ganho fora de ordem em {base} ({nome}): limpo {g[0]:.2f}, od {g[1]:.2f}, dist {g[2]:.2f}')


# -------------------------------------------------------------- comparacao --
def falta_delay_em_primeiro():
    for base in ('riff', 'staccato'):
        for nome, fonte in FONTES:
            x = sa.com_ruido(fonte(base))
            tocado = sa.com_ruido(fonte(base, semente=21) if fonte is sa.base_di else fonte(base, semente=21))
            ref = sa.cadeia(x, ('overdrive', {}), ('delay', {'time': 450}))
            rec = sa.aplicar(tocado, 'overdrive')
            r = st.comparar(_perfil(ref), _perfil(rec), bpm=100)
            primeira = r['sugestoes'][0] if r['sugestoes'] else None
            s.checar(primeira is not None and primeira['titulo'] == 'Falta: Delay' and primeira['pedal'] == 'delay',
                     f'{base} ({nome}): primeira sugestao foi {primeira and primeira["titulo"]}')
            s.checar('colcheia pontuada' in primeira['texto'], 'o tempo do delay deveria virar figura (100 BPM)')
            s.checar(r['indices']['ambiencia'] < 70, f'{base} ({nome}): indice de ambiencia alto demais')


def invariancia_volume():
    for base in ('riff', 'acorde', 'staccato'):
        for nome, fonte in FONTES:
            x = sa.aplicar(sa.com_ruido(fonte(base)), 'overdrive')
            r = st.comparar(_perfil(x), _perfil(x * 0.12))
            s.checar(r['indice_geral'] >= 97, f'{base} ({nome}): mesmo som em outro volume deu {r["indice_geral"]}')
            s.checar(not [q for q in r['sugestoes'] if q['confianca'] > 0.5],
                     f'{base} ({nome}): sugestoes para o mesmo som: {[q["titulo"] for q in r["sugestoes"]]}')


def sobra_e_ajuste():
    x = sa.com_ruido(sa.base_humana('acorde'))
    r = st.comparar(_perfil(x), _perfil(sa.aplicar(x, 'tremolo')))
    s.checar(any(q['titulo'] == 'Sobra: Tremolo' for q in r['sugestoes']), 'tremolo so no usuario deveria sobrar')
    y = sa.com_ruido(sa.base_humana('staccato'))
    r = st.comparar(_perfil(sa.aplicar(y, 'delay', time=450)), _perfil(sa.aplicar(y, 'delay', time=300)), bpm=100)
    s.checar(any(q['titulo'] == 'Ajuste: Delay' and q['valores'].get('time') == 450 for q in r['sugestoes']),
             'delay com tempo diferente deveria virar "Ajuste: Delay" com o tempo do original')
    md = st.relatorio_markdown(r, 'teste', {'Música': 'x'})
    s.checar('## Ajuste' in md and '| Categoria |' in md and 'Medidas' in md, 'relatorio markdown incompleto')


# --------------------------------------------------------------- gravacao --
def _cfg(latencia=0.0):
    return disp.ConfigAudio(taxa=44100, latencia_ms=latencia, canais_entrada=2, canal_processado=0, canal_di=1,
                            entrada_id=0, saida_id=0, entrada_nome='sim', saida_nome='sim')


def _musico(od, limpo, ref):
    _, i0, _ = gp.montar_playback(ref, 44100, 100, 1)

    def tocar(saida, sr):
        y = np.zeros((saida.shape[0], 2))
        n = min(od.size, y.shape[0] - i0)
        y[i0:i0 + n, 0], y[i0:i0 + n, 1] = od[:n], limpo[:n]
        return y
    return tocar


def gravacao_com_latencia():
    limpo = sa.com_ruido(sa.base_humana('riff', 2, semente=13))
    od = sa.aplicar(limpo, 'overdrive')
    ref = sa.cadeia(sa.com_ruido(sa.base_humana('riff', 2)), ('overdrive', {}), ('delay', {'time': 450}))
    musico = _musico(od, limpo, ref)
    # latencia conhecida e compensada: fica alinhado
    take = gp.tocar_e_gravar(ref, _cfg(31.0), bpm=100, compassos_contagem=1,
                             backend=gp.BackendSimulado(31.0, musico))
    s.checar(take['audio'].shape[1] == 2, 'deveria gravar o canal processado e o DI')
    s.checar(not [p for p in take['problemas'] if p[0] == 'erro'], f'take valido marcado com erro: {take["problemas"]}')
    s.checar(take.get('vazamento', 1) < 0.35, f'nao ha musica na entrada, mas vazamento {take.get("vazamento"):.2f}')
    r = st.analisar(take['referencia'], 44100, take['audio'][:, 0], 44100, bpm=100)
    s.checar(abs(r['alinhamento']['deslocamento_s']) < 0.012, f'alinhado: {r["alinhamento"]}')
    s.checar(r['resultado']['sugestoes'][0]['titulo'] == 'Falta: Delay', 'take simulado: faltou o delay')
    # latencia NAO compensada (70 ms): o refino por correlacao acha
    take = gp.tocar_e_gravar(ref, _cfg(0.0), bpm=100, compassos_contagem=1,
                             backend=gp.BackendSimulado(70.0, musico))
    r = st.analisar(take['referencia'], 44100, take['audio'][:, 0], 44100, bpm=100)
    s.checar(abs(r['alinhamento']['deslocamento_s'] - 0.070) < 0.012, f'latencia simulada: {r["alinhamento"]}')
    # streams separados: deslocamento entre relogios somado
    take = gp.tocar_e_gravar(ref, _cfg(31.0), bpm=100, compassos_contagem=0,
                             backend=gp.BackendSimulado(31.0, _musico(od, limpo, ref), deslocamento=441))
    r = st.analisar(take['referencia'], 44100, take['audio'][:, 0], 44100, bpm=100)
    s.checar(abs(r['alinhamento']['deslocamento_s']) < 0.03, f'deslocamento entre streams: {r["alinhamento"]}')


def validacao_do_take():
    ref = sa.base_humana('riff', 1)
    silencio = gp.tocar_e_gravar(ref, _cfg(), backend=gp.BackendSimulado(0, None, ruido_db=-90))
    s.checar(any(p[0] == 'erro' and 'silêncio' in p[1] for p in silencio['problemas']), 'silencio nao detectado')
    alto = gp.tocar_e_gravar(ref, _cfg(), backend=gp.BackendSimulado(
        0, lambda saida, sr: np.clip(saida[:, 0] * 8, -1, 1)))
    s.checar(any('saturou' in p[1] for p in alto['problemas']), 'clipping nao detectado')
    s.checar(any('entrando na gravação' in p[1] for p in alto['problemas']),
             'a "gravacao" e a propria musica: deveria avisar vazamento')
    curto = gp.tocar_e_gravar(ref[:sa.SR], _cfg(), compassos_contagem=0,
                              backend=gp.BackendSimulado(0, lambda saida, sr: saida[:, 0] * 0.3))
    s.checar(any(p[0] == 'erro' and 'curta' in p[1] for p in curto['problemas']), 'take curto nao detectado')
    vaz = gp.tocar_e_gravar(ref, _cfg(), backend=gp.BackendSimulado(
        0, lambda saida, sr: sa.com_ruido(sa.base_humana('riff', 1, semente=4))[:saida.shape[0]] * 0.3,
        vazamento=0.5))
    s.checar(vaz['vazamento'] > 0.35, f'vazamento da musica nao detectado ({vaz["vazamento"]:.2f})')
    caminho = gp.salvar_take(vaz, 'teste', 1)
    s.checar(os.path.exists(caminho) and gp.listar_takes('teste'), 'take nao foi salvo')


def calibracao_latencia():
    cliques, tempos = disp.sinal_cliques(44100)
    gravado = np.zeros(cliques.shape[0] + 44100)
    d = int(0.047 * 44100)
    gravado[d:d + cliques.shape[0]] = cliques[:, 0] * 0.3
    ms, conf, _ = disp.medir_latencia(gravado, 44100, tempos, 'loopback')
    s.checar(ms is not None and abs(ms - 47) < 1.5 and conf > 0.5, f'loopback: {ms} ms, conf {conf}')
    # tocar junto: palhetadas ~60 ms depois de cada clique
    cliques, tempos = disp.sinal_cliques(44100, n=10, intervalo=0.75)
    x = np.zeros(cliques.shape[0] + 44100)
    nota = sa.base_humana('staccato', 1)[:int(0.3 * 44100)]
    rng = np.random.default_rng(2)
    for t in tempos:
        i = int((t + 0.060 + rng.normal(0, 0.006)) * 44100)
        x[i:i + nota.size] += nota
    ms, conf, _ = disp.medir_latencia(x, 44100, tempos, 'tocar')
    s.checar(ms is not None and abs(ms - 60) < 15, f'tocar junto: {ms} ms')
    s.checar(disp.medir_latencia(np.zeros(1000), 44100, tempos)[0] is None, 'silencio deveria falhar a calibracao')
    cfg = disp.ConfigAudio(entrada_nome='A', saida_nome='B')
    cfg.definir_latencia(33)
    disp.salvar_config(cfg)
    lido = disp.carregar_config()
    lido.latencia_ms = 0
    lido.restaurar_latencia()
    s.checar(lido.latencia_ms == 33, 'latencia por dispositivo nao foi salva/restaurada')


# ------------------------------------------------------------- referencia --
def biblioteca_e_bpm():
    pasta = tempfile.mkdtemp()
    cam = os.path.join(pasta, 'Canção Teste - Àrtista.wav')
    at.salvar_wav(cam, sa.base_humana('riff', 1), sa.SR)
    reg = refm.importar_arquivo(cam, tipo='isolado', titulo='Canção Teste', artista='Àrtista')
    s.checar(any(i['id'] == reg['id'] for i in refm.listar_biblioteca('cancao artista', incluir_partituras=False)),
             'busca sem acento nao achou a referencia')
    refm.adicionar_pasta(pasta)
    s.checar(refm.listar_biblioteca('teste', incluir_partituras=False), 'pasta de referencias nao listada')
    try:
        refm.importar_arquivo(os.path.join(pasta, 'x.txt'))
        s.checar(False, 'formato invalido deveria falhar')
    except ValueError:
        pass
    # BPM de um clique a 120
    sr = 44100
    x = np.zeros(sr * 12)
    for k in range(24):
        c = gp.clique(sr, k % 4 == 0)
        i = int(k * 0.5 * sr)
        x[i:i + c.size] += c
    bpm, conf = refm.detectar_bpm(x, sr)
    s.checar(bpm is not None and abs(bpm - 120) < 3, f'BPM {bpm}')
    forma = refm.forma_de_onda(x, 300)
    s.checar(forma.size == 300 and abs(forma.max() - 1) < 1e-9, 'forma de onda')
    ok, msg = refm.yt_dlp_disponivel()
    s.checar(ok or len(msg) > 20, 'sem yt-dlp tem que haver mensagem explicando')
    ok, msg = refm.demucs_disponivel()
    s.checar(ok or len(msg) > 20, 'sem demucs tem que haver mensagem explicando')


def compassos_midi():
    pasta = os.path.join(harness.RAIZ, 'assets', 'audio', 'Midis')
    midis = []
    for f in (sorted(os.listdir(pasta)) if os.path.isdir(pasta) else []):
        caminho = os.path.join(pasta, f)
        if f.endswith('.mid') and open(caminho, 'rb').read(4) == b'MThd':   # alguns .mid sao XML
            midis.append(caminho)
    if not midis:
        return
    compassos, bpm = refm.compassos_do_midi(midis[0], deslocamento_s=1.5)
    s.checar(compassos and bpm > 0, 'MIDI sem compassos')
    s.checar(abs(compassos[0]['inicio_s'] - 1.5) < 1e-6, 'deslocamento do compasso 1')
    s.checar(all(b['inicio_s'] >= a['inicio_s'] and b['fim_s'] > b['inicio_s'] for a, b in zip(compassos, compassos[1:])),
             'compassos fora de ordem')


# ----------------------------------------------------------------- fases 2/3
def preset_sugerido():
    from audio import cadeia_pedais as cp
    alvo = sa.cadeia(sa.com_ruido(sa.base_di('riff')), ('distorcao', {'dist': 0.5}),
                     ('eq', {'medios': 6, 'freq_medios': 800}), ('delay', {'time': 375, 'mix': 0.35}))
    pr = _perfil(alvo)
    limpo = sa.com_ruido(sa.base_di('riff', semente=5))
    antes = st.comparar(pr, _perfil(limpo))['indice_geral']
    r = cp.buscar_preset(pr, limpo, sa.SR)
    depois = st.comparar(pr, r['perfil'])['indice_geral']
    ids = [it['id'] for it in r['cadeia']]
    s.checar(depois >= antes + 10, f'o preset deveria aproximar o som: {antes} -> {depois}')
    s.checar('delay' in ids, f'a referencia tem delay e o preset nao: {ids}')
    d = next(it for it in r['cadeia'] if it['id'] == 'delay')
    s.checar(abs(d['params']['time'] - 375) < 40, f'delay do preset {d["params"]["time"]}')
    s.checar(any(i in ids for i in cp.GANHO), f'a referencia e distorcida e o preset nao tem ganho: {ids}')
    s.checar(ids == [it['id'] for it in cp.ordenar(r['cadeia'])], 'ordem da cadeia')
    s.checar(len(cp.descrever(r['cadeia'])) > 20, 'descricao do preset')


def detector_treinado():
    ok, _msg = td.sklearn_disponivel()
    if not ok:
        return
    original = td.ARQUIVO_MODELO
    td.ARQUIVO_MODELO = os.path.join(tempfile.mkdtemp(), 'modelo.pkl')
    try:
        m = td.treinar(amostras=70, semente=3)
        s.checar(os.path.exists(td.ARQUIVO_MODELO) and 0 <= m['media_modelo'] <= 1, 'modelo nao salvo')
        td._desligar_reforco = False
        td._cache.clear()
        ef = _perfil(_sinal(sa.base_humana, 'staccato', 'delay'))['efeitos']
        s.checar('modelo' in ef['delay'], 'o modelo nao reforcou os detectores')
        s.checar(ef['delay']['presenca'] == 'sim', 'reforco derrubou um delay obvio')
    finally:
        td._desligar_reforco = True
        td._cache.clear()
        td.ARQUIVO_MODELO = original


# -------------------------------------------------------------- interface --
def _montar_interface(largura, altura, tema):
    import preview_analisador as pv
    return pv.montar(largura, altura, tema)


def interface():
    import core.modulos.modulos_estudos as me
    s.checar('Analisador IA' in me.NOMES_ANALISADOR, 'nome do cartao nao abre o Analisador')
    for tema in harness.TEMAS:
        harness.definir_tema(tema)
        ctx, g, an, _ = _montar_interface(1920, 1080, tema)
        for largura, altura in ((1920, 1080), (1600, 900), (1280, 720)):
            ctx.estado.LARGURA_TELA, ctx.estado.ALTURA_TELA = largura, altura
            tela = pygame.Surface((largura, altura), pygame.SRCALPHA)
            for etapa in range(4):
                an.etapa = etapa
                g.desenhar_tela_estudo(tela, largura, altura, ctx.estado, ctx.fontes)
                s.checar(an._alvos, f'etapa {etapa + 1} sem alvos clicaveis ({largura}x{altura}, {tema})')
                for r, _acao, _d in an._alvos:
                    s.checar(an.area.contains(r) or an.area.colliderect(r),
                             f'alvo fora da area na etapa {etapa + 1} ({largura}x{altura}, {tema})')
            if an.analise is None:
                an.etapa = 4
                an.analisar()
                an.tarefa[0].aguardar(120)
                an._checar_tarefa()
            s.checar(an.analise is not None, 'analise da interface nao terminou')
            an.etapa = 4
            for aba, _n in __import__('Analisador.analisador_ia', fromlist=['x']).ABAS_RESULTADO:
                an.aba = aba
                g.desenhar_tela_estudo(tela, largura, altura, ctx.estado, ctx.fontes)
        # clique na barra de etapas volta para a Musica
        alvo = next(r for r, a, d in an._alvos if a == 'etapa' and d == 2)
        an.clicar(alvo.center)
        s.checar(an.etapa == 2, 'clique na barra de etapas')
        # "Abrir pedal" leva para ESTUDOS > Pedais com os valores sugeridos
        an.abrir_pedal('delay', {'time': 375.0, 'mix': 0.3})
        s.checar(ctx.estado.estudo_ativo == 'Pedais de Efeito', 'abrir pedal nao trocou de estudo')
        tela = pygame.Surface((1920, 1080), pygame.SRCALPHA)
        ctx.estado.LARGURA_TELA, ctx.estado.ALTURA_TELA = 1920, 1080
        g.desenhar_tela_estudo(tela, 1920, 1080, ctx.estado, ctx.fontes)
        ped = g.modulo_pedais
        s.checar(ped.pedal['id'] == 'delay' and abs(ped.valores['time'] - 375) < 1e-6, 'pedal aberto sem os valores')
        ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode='')
        g.tratar_eventos(ev, (0, 0), ctx.estado)
        s.checar(ctx.estado.estudo_ativo == 'Analisador IA' and ctx.estado.tela_estudo_ativa,
                 'ESC no pedal deveria voltar ao Analisador')
        g.tratar_eventos(ev, (0, 0), ctx.estado)
        s.checar(not ctx.estado.tela_estudo_ativa and g.modulo_analisador is None, 'ESC nao saiu do Analisador')
        s.checar(not an.player.tocando and an.gravador.estado != 'gravando', 'audio continuou depois de sair')


def cartao_na_sub_aba():
    import preview_analisador as pv
    for tema in harness.TEMAS:
        ctx = pv.aba_ia(tema, gravar=False)
        secao = next(sc for sc in ctx.estado.secoes_inferiores if sc['conteudo'] == 'analise_ia')
        s.checar('Analisador' in secao['sub_abas'], 'sub-aba Analisador nao esta em ANALISE DE IA')
        s.checar(getattr(ctx.estado, 'rect_cartao_analisador', None) is not None, 'cartao do Analisador nao desenhado')


def texto_e_teclado():
    ctx, g, an, _ = _montar_interface(1600, 900, 'escuro')
    an.etapa = 2
    tela = pygame.Surface((1600, 900), pygame.SRCALPHA)
    g.desenhar_tela_estudo(tela, 1600, 900, ctx.estado, ctx.fontes)
    caixa = next(r for r, a, d in an._alvos if a == 'foco_busca')
    an.clicar(caixa.center)
    for ch in 'riff':
        an.tratar_eventos(pygame.event.Event(pygame.KEYDOWN, key=0, mod=0, unicode=ch), (0, 0), ctx.estado)
    an.tratar_eventos(pygame.event.Event(pygame.TEXTINPUT, text='ç'), (0, 0), ctx.estado)
    s.checar(an.busca == 'riffç', f'digitacao: {an.busca!r}')
    esc = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode='')
    g.tratar_eventos(esc, (0, 0), ctx.estado)
    s.checar(not an.busca_foco and ctx.estado.tela_estudo_ativa, 'ESC no campo de busca so tira o foco')
    onda = next(r for r, a, d in an._alvos if a == 'onda')
    an.clicar((onda.x + onda.width // 4, onda.centery))
    an.tratar_eventos(pygame.event.Event(pygame.MOUSEMOTION, pos=(onda.x + onda.width // 2, onda.centery),
                                         rel=(1, 0), buttons=(1, 0, 0)), (onda.x + onda.width // 2, onda.centery),
                      ctx.estado)
    an.tratar_eventos(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=(onda.x + onda.width // 2, onda.centery),
                                         button=1), (onda.x + onda.width // 2, onda.centery), ctx.estado)
    a, b = sorted(an.sel)
    s.checar(abs(a - 0.25) < 0.02 and abs(b - 0.5) < 0.02, f'selecao do trecho {an.sel}')
    g._limpar_modulos()


s.teste('motor em audio linear e cadeia de pedais', motor_linear)
s.teste('configuracao por instrumento e perfil completo', config_completa)
s.teste('LUFS e alinhamento', lufs_e_alinhamento)
s.teste('efeitos conhecidos sao detectados (e os parametros batem)', detecta_efeitos_conhecidos)
s.teste('phaser/flanger: a varredura aparece', phaser_flanger_familia)
s.teste('reverb curto x longo', reverb_curto_x_longo)
s.teste('audio limpo nao gera deteccao com confianca alta', limpo_sem_falso_positivo)
s.teste('indice de ganho em ordem', ganho_em_ordem)
s.teste('Overdrive+Delay x Overdrive -> "Falta: Delay"', falta_delay_em_primeiro)
s.teste('mesmo som em outro volume -> ~100', invariancia_volume)
s.teste('sobra e ajuste de parametro', sobra_e_ajuste)
s.teste('gravacao: latencia simulada e alinhamento', gravacao_com_latencia)
s.teste('validacao do take', validacao_do_take)
s.teste('calibracao de latencia', calibracao_latencia)
s.teste('biblioteca, busca e BPM', biblioteca_e_bpm)
s.teste('compassos do MIDI', compassos_midi)
s.teste('fase 2: preset sugerido', preset_sugerido)
s.teste('fase 3: detector treinado localmente', detector_treinado)
s.teste('interface: etapas, abas, resolucoes e temas', interface)
s.teste('cartao na sub-aba ANALISE DE IA', cartao_na_sub_aba)
s.teste('interface: busca, ESC e selecao do trecho', texto_e_teclado)
s.encerrar()
