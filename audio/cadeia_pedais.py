# -*- coding: utf-8 -*-
"""
Analisador IA - Fase 2: analise por sintese.

Pega o som LIMPO do usuario (canal DI da pedaleira, ou a gravacao de
calibracao do instrumento), passa por cadeias de pedais do motor
(audio/efeitos_pedais.py) e procura a cadeia e os knobs cujo perfil de
timbre mais se aproxima da referencia. O resultado e um "preset sugerido":
pedais, ordem e valores, que o usuario ouve aplicado ao proprio som limpo e
abre na aba ESTUDOS > Pedais.

Busca (tudo local, numpy/scipy):
    1. estagio de ganho: grade (nenhum, boost, overdrive, distorcao, fuzz)
       e depois scipy.optimize (Nelder-Mead) no drive/tone do melhor;
    2. equalizador: calculado pela diferenca de bandas e refinado uma vez;
    3. compressor, se a referencia sustenta mais;
    4. filtros, modulacao, pitch, delay e reverb: vem dos detectores da
       referencia (tipo e parametros estimados), com um ajuste fino do mix.
A ordem segue a cadeia comum do curriculo (Estudos/curriculo_pedais.py).
"""
import numpy as np

from audio import analise_timbre as at
from audio import efeitos_pedais as motor

# ordem na pedaleira (mesma ideia de curriculo_pedais.CADEIA_SUGERIDA)
ORDEM = ['wah', 'autowah', 'compressor', 'octaver', 'whammy', 'boost', 'overdrive', 'distorcao',
         'fuzz', 'eq', 'ring', 'tremolo', 'vibrato', 'chorus', 'phaser', 'flanger', 'volume', 'delay',
         'reverb', 'gate']
GANHO = ('boost', 'overdrive', 'distorcao', 'fuzz')
DURACAO_MAX_S = 12.0


def _valores(pid, **extra):
    """Valores padrao do curriculo com os pedidos por cima (dentro da faixa)."""
    from Estudos import curriculo_pedais as cur
    pedal = cur.PEDAIS_POR_ID[pid]
    v = cur.valores_padrao(pedal)
    for p in pedal['parametros']:
        if p['id'] in extra and extra[p['id']] is not None:
            v[p['id']] = float(np.clip(extra[p['id']], p['min'], p['max']))
    return v


def ordenar(cadeia):
    return sorted(cadeia, key=lambda it: ORDEM.index(it['id']) if it['id'] in ORDEM else 99)


def aplicar(di, sr, cadeia):
    """Renderiza a cadeia (lista de {'id','params'}) em mono."""
    y = motor.renderizar_cadeia(di, sr, [(it['id'], it['params']) for it in ordenar(cadeia)])
    return y.mean(axis=1) if y.ndim == 2 else y


def _perfil_rapido(y, sr, cfg):
    return at.perfil_timbre(y, sr, cfg, efeitos=False)


def distancia(p_ref, p, cfg, pesos=None):
    """
        Distancia de timbre (quanto menor, mais parecido): EQ por banda (dB,
        so a forma), indice de ganho e sustain. Mesmas medidas da comparacao.
    """
    pesos = pesos or {'eq': 1.0, 'ganho': 1.0, 'sustain': 0.4}
    d_eq = []
    for b in cfg['bandas_macro']:
        a, c = p_ref['medidas'].get(f'eq_{b}', {}).get('valor'), p['medidas'].get(f'eq_{b}', {}).get('valor')
        if a is not None and c is not None:
            d_eq.append(a - c)
    eq = float(np.sqrt(np.mean((np.array(d_eq) - np.mean(d_eq)) ** 2))) / 4.0 if d_eq else 0.0
    ga = p_ref['medidas']['indice_ganho']['valor'] or 0.0
    gb = p['medidas']['indice_ganho']['valor'] or 0.0
    ganho = abs(ga - gb) / 0.2
    sa, sb = p_ref['medidas']['decaimento_nota']['valor'], p['medidas']['decaimento_nota']['valor']
    sust = abs(np.log2((max(sa or 0, 0) + 3) / (max(sb or 0, 0) + 3))) if sa is not None and sb is not None else 0.0
    return float(pesos['eq'] * eq ** 2 + pesos['ganho'] * ganho ** 2 + pesos['sustain'] * sust ** 2)


def _eq_pela_diferenca(p_ref, p, cfg, atual=None):
    """Knobs do Equalizador do motor a partir da diferenca de bandas (ref - atual)."""
    dif = {}
    for b in cfg['bandas_macro']:
        a, c = p_ref['medidas'][f'eq_{b}']['valor'], p['medidas'][f'eq_{b}']['valor']
        if a is not None and c is not None:
            dif[b] = a - c
    if not dif:
        return None
    m = np.mean(list(dif.values()))
    dif = {k: v - m for k, v in dif.items()}
    atual = atual or {'graves': 0.0, 'medios': 0.0, 'agudos': 0.0, 'freq_medios': 800.0, 'level': 0.0}
    medios = {k: dif.get(k, 0.0) for k in ('medio_graves', 'medios', 'medio_agudos')}
    chave_m = max(medios, key=lambda k: abs(medios[k]))
    a, b = cfg['bandas_macro'][chave_m]
    novo = {
        'graves': atual['graves'] + 0.8 * dif.get('graves', 0.0),
        'medios': atual['medios'] + 0.8 * medios[chave_m],
        'freq_medios': float(np.clip(np.sqrt(a * b), 250, 3000)),
        'agudos': atual['agudos'] + 0.8 * np.mean([dif.get('agudos', 0.0), dif.get('presenca', 0.0)]),
        'level': 0.0,
    }
    return {k: float(np.clip(v, -12, 12)) if k != 'freq_medios' else v for k, v in novo.items()}


def buscar_preset(perfil_ref, di, sr_di, instrumento='guitarra', progresso=None, cancelar=None,
                  avaliacoes_max=60):
    """
        Como funciona: ver o comentario do modulo. 'perfil_ref' e o perfil
        completo da referencia (com 'efeitos'); 'di' o som limpo do usuario.
        Devolve {'cadeia': [{'id','nome','params'}], 'audio': mono no sr
        de analise, 'sr', 'perfil': perfil final, 'distancia', 'passos'}.
        Para que serve: o botao "Preset sugerido" da tela de resultado.
    """
    from Estudos import curriculo_pedais as cur
    cfg = at.carregar_config(instrumento)
    sr = at.SR_ANALISE
    x = at.preprocessar(di, sr_di)
    x = x[:int(DURACAO_MAX_S * sr)]
    x = x / (np.max(np.abs(x)) or 1.0) * 0.5
    passos = []
    contagem = {'n': 0}

    def avaliar(cadeia):
        if cancelar is not None and cancelar.is_set():
            raise RuntimeError('Busca cancelada.')
        contagem['n'] += 1
        if progresso:
            progresso(min(0.95, contagem['n'] / float(avaliacoes_max)), 'Testando pedais no seu som limpo...')
        y = aplicar(x, sr, cadeia)
        p = _perfil_rapido(y, sr, cfg)
        return distancia(perfil_ref, p, cfg), p

    # 1. estagio de ganho (grade)
    candidatos = [[]]
    candidatos += [[{'id': 'boost', 'params': _valores('boost', ganho=g, amp=0.5)}] for g in (8, 16)]
    candidatos += [[{'id': 'overdrive', 'params': _valores('overdrive', drive=d, tone=0.55)}] for d in (0.25, 0.55, 0.85)]
    candidatos += [[{'id': 'distorcao', 'params': _valores('distorcao', dist=d, tone=0.5)}] for d in (0.35, 0.75)]
    candidatos += [[{'id': 'fuzz', 'params': _valores('fuzz', fuzz=0.8)}]]
    resultados = []
    for cand in candidatos:
        d, p = avaliar(cand)
        resultados.append((d, cand, p))
    resultados.sort(key=lambda r: r[0])
    d_melhor, cadeia, p_melhor = resultados[0]
    passos.append(f'estágio de ganho: {cadeia[0]["id"] if cadeia else "nenhum"} (distância {d_melhor:.2f})')

    # refino continuo do drive/tone do estagio escolhido
    if cadeia and cadeia[0]['id'] in ('overdrive', 'distorcao', 'fuzz'):
        pid = cadeia[0]['id']
        chave = {'overdrive': 'drive', 'distorcao': 'dist', 'fuzz': 'fuzz'}[pid]
        inicio = np.array([cadeia[0]['params'][chave], cadeia[0]['params']['tone']])
        from scipy.optimize import minimize

        def objetivo(v):
            v = np.clip(v, 0.02, 1.0)
            c = [{'id': pid, 'params': _valores(pid, **{chave: v[0], 'tone': v[1]})}]
            return avaliar(c)[0]
        try:
            r = minimize(objetivo, inicio, method='Nelder-Mead',
                         options={'maxfev': 14, 'xatol': 0.04, 'fatol': 0.01, 'initial_simplex':
                                  [inicio, inicio + [0.15, 0], inicio + [0, 0.2]]})
            v = np.clip(r.x, 0.02, 1.0)
            if r.fun < d_melhor:
                cadeia = [{'id': pid, 'params': _valores(pid, **{chave: v[0], 'tone': v[1]})}]
                d_melhor, p_melhor = avaliar(cadeia)
                passos.append(f'{pid}: {chave} {v[0]:.2f}, tone {v[1]:.2f} (distância {d_melhor:.2f})')
        except RuntimeError:
            raise
        except Exception:
            pass

    # 2. equalizador
    eq = _eq_pela_diferenca(perfil_ref, p_melhor, cfg)
    if eq and max(abs(eq['graves']), abs(eq['medios']), abs(eq['agudos'])) > 1.5:
        tentativa = cadeia + [{'id': 'eq', 'params': _valores('eq', **eq)}]
        d, p = avaliar(tentativa)
        eq2 = _eq_pela_diferenca(perfil_ref, p, cfg, eq)
        tentativa2 = cadeia + [{'id': 'eq', 'params': _valores('eq', **eq2)}]
        d2, p2 = avaliar(tentativa2)
        if min(d, d2) < d_melhor:
            if d2 < d:
                d, p, tentativa = d2, p2, tentativa2
            cadeia, d_melhor, p_melhor = tentativa, d, p
            passos.append(f'EQ ajustado (distância {d_melhor:.2f})')

    # 3. compressor (se a referencia sustenta bem mais e o ganho nao explica)
    sa = perfil_ref['medidas']['decaimento_nota']['valor']
    sb = p_melhor['medidas']['decaimento_nota']['valor']
    if sa is not None and sb is not None and sa + 3 < 0.6 * (sb + 3):
        melhor_c = None
        for sust in (0.4, 0.7, 0.95):
            c = cadeia + [{'id': 'compressor', 'params': _valores('compressor', sustain=sust)}]
            d, p = avaliar(c)
            if d < d_melhor and (melhor_c is None or d < melhor_c[0]):
                melhor_c = (d, c, p)
        if melhor_c:
            d_melhor, cadeia, p_melhor = melhor_c
            passos.append(f'compressor (distância {d_melhor:.2f})')

    # 4. efeitos detectados na referencia
    ef = perfil_ref.get('efeitos', {})
    presentes = [k for k, r in ef.items() if k not in GANHO and k not in ('eq', 'whammy')
                 and r.get('score', 0) >= 0.6]
    # familias que se confundem: fica so o mais forte
    for a, b in (('phaser', 'flanger'), ('wah', 'autowah'), ('chorus', 'vibrato')):
        if a in presentes and b in presentes:
            presentes.remove(a if ef[a]['score'] < ef[b]['score'] else b)
    for pid in presentes:
        par = dict(ef[pid].get('parametros', {}))
        if pid in ('gate',) or any(it['id'] == pid for it in cadeia):
            continue
        cadeia.append({'id': pid, 'params': _valores(pid, **par)})
        passos.append(f'{cur.PEDAIS_POR_ID[pid]["nome"]} com os valores medidos na música')
    # ajuste fino do mix do delay e do reverb pela cauda/volume medidos
    for pid, medida, chave in (('delay', 'delay_mix', 'mix'), ('reverb', 'reverb_cauda', 'mix')):
        item = next((it for it in cadeia if it['id'] == pid), None)
        if item is None or cancelar is not None and cancelar.is_set():
            continue
        alvo = perfil_ref['medidas'].get(medida, {}).get('valor')
        if alvo is None:
            continue
        melhor = None
        for mix in (0.2, 0.35, 0.5, 0.7):
            item['params'][chave] = mix
            y = aplicar(x, sr, cadeia)
            p = at.perfil_timbre(y, sr, cfg, efeitos=True)
            contagem['n'] += 1
            v = p['medidas'].get(medida, {}).get('valor')
            if v is None:
                continue
            erro = abs(v - alvo)
            if melhor is None or erro < melhor[0]:
                melhor = (erro, mix)
        if melhor:
            item['params'][chave] = melhor[1]
            passos.append(f'{pid}: mix {melhor[1]:.2f}')

    cadeia = ordenar(cadeia)
    y = aplicar(x, sr, cadeia)
    if progresso:
        progresso(0.97, 'Medindo o resultado...')
    perfil_final = at.perfil_timbre(y, sr, cfg, efeitos=True)
    for it in cadeia:
        it['nome'] = cur.PEDAIS_POR_ID[it['id']]['nome']
        it['params'] = {k: float(v) for k, v in it['params'].items()}
    if progresso:
        progresso(1.0, 'Pronto')
    return {'cadeia': cadeia, 'audio': y, 'sr': sr, 'perfil': perfil_final,
            'distancia': distancia(perfil_ref, perfil_final, cfg), 'passos': passos,
            'di': x, 'avaliacoes': contagem['n']}


def descrever(cadeia):
    """Texto curto do preset: 'Overdrive (drive 60%, tone 50%) > EQ (...) > Delay (...)'."""
    from Estudos import curriculo_pedais as cur
    partes = []
    for it in ordenar(cadeia):
        pedal = cur.PEDAIS_POR_ID[it['id']]
        knobs = []
        for p in pedal['parametros']:
            if p['id'] in it['params']:
                knobs.append(f"{p['nome'].split(' (')[0].lower()} {cur.formatar_valor(p, it['params'][p['id']])}")
        partes.append(f"{pedal['nome']} ({', '.join(knobs[:4])})")
    return '  >  '.join(partes)
