# -*- coding: utf-8 -*-
"""
Analisador IA: compara o perfil de timbre da REFERENCIA (a guitarra da
musica) com o da GRAVACAO (o preset do usuario) e transforma as diferencas
em sugestoes com o vocabulario do estudo de Pedais (Estudos/curriculo_pedais).

Nada aqui olha se as notas estao certas: so o SOM (ganho, EQ, compressao,
modulacao, ambiencia, efeitos de pitch).

Saida de comparar():
    'indice_geral'  0..100 (estimativa!)
    'indices'       {'eq', 'ganho', 'dinamica', 'modulacao', 'ambiencia'}
    'sugestoes'     lista ordenada por impacto; cada uma com
                    tipo ('falta' | 'sobra' | 'ajuste' | 'timbre'), titulo,
                    texto, impacto 0..1, confianca 0..1, possivel (bool),
                    pedal (id do curriculo para abrir em ESTUDOS > Pedais),
                    valores (parametros sugeridos para esse pedal)
    'tabela'        medidas lado a lado (modo avancado)
    'eq_bandas'     diferenca por banda (dB, referencia - voce)
    'avisos'        limites da comparacao (mix, separacao, pouca pausa...)

Os limiares ficam em audio/config_analise/*.json ('sugestoes', 'indices').
"""
import numpy as np

from audio import analise_timbre as at
from audio import detectores_efeitos as det

TIPOS = ('falta', 'sobra', 'ajuste', 'timbre')
NOMES_TIPO = {'falta': 'Falta', 'sobra': 'Sobra', 'ajuste': 'Ajuste', 'timbre': 'Timbre base'}
CATEGORIAS = ('eq', 'ganho', 'dinamica', 'modulacao', 'ambiencia')
NOMES_CATEGORIA = {'eq': 'EQ', 'ganho': 'Ganho', 'dinamica': 'Dinâmica',
                   'modulacao': 'Modulação', 'ambiencia': 'Ambiência'}
# efeitos comparados por presenca (ganho e EQ sao comparados como "timbre base")
EFEITOS_PRESENCA = ('delay', 'reverb', 'tremolo', 'vibrato', 'chorus', 'flanger', 'phaser',
                    'wah', 'autowah', 'octaver', 'ring', 'volume', 'gate', 'compressor')
CATEGORIA_EFEITO = {
    'delay': 'ambiencia', 'reverb': 'ambiencia',
    'tremolo': 'modulacao', 'vibrato': 'modulacao', 'chorus': 'modulacao', 'flanger': 'modulacao',
    'phaser': 'modulacao', 'wah': 'modulacao', 'autowah': 'modulacao', 'octaver': 'modulacao',
    'ring': 'modulacao', 'whammy': 'modulacao',
    'volume': 'dinamica', 'gate': 'dinamica', 'compressor': 'dinamica',
}
# peso do efeito no som (quanto ele muda o resultado quando falta/sobra)
IMPACTO_EFEITO = {
    'delay': 0.8, 'reverb': 0.7, 'tremolo': 0.8, 'vibrato': 0.75, 'chorus': 0.6, 'flanger': 0.7,
    'phaser': 0.65, 'wah': 0.8, 'autowah': 0.7, 'octaver': 0.8, 'ring': 0.9, 'volume': 0.5,
    'gate': 0.3, 'compressor': 0.45,
}
AVISO_REFERENCIA = ('A referência inclui amplificador, gabinete, microfone, mixagem e masterização: '
                    'o objetivo é aproximar o som, não deixá-lo idêntico.')


def _nome_pedal(pid):
    try:
        from Estudos import curriculo_pedais as cur
        return cur.PEDAIS_POR_ID[pid]['nome']
    except Exception:
        return pid


def _valor(perfil, chave):
    m = perfil['medidas'].get(chave)
    return None if m is None else m.get('valor')


def _conf(perfil, chave):
    m = perfil['medidas'].get(chave)
    return 0.0 if m is None else m.get('confianca', 0.0)


def _nota(v):
    """Tempo do delay em figura musical relativa ao BPM."""
    return v


def figura_do_tempo(ms, bpm):
    """'colcheia pontuada' etc. se o tempo cair perto de uma figura (+-6%)."""
    if not bpm or not ms:
        return None
    seminima = 60000.0 / bpm
    figuras = [(4, 'semibreve'), (3, 'mínima pontuada'), (2, 'mínima'), (1.5, 'semínima pontuada'),
               (1, 'semínima'), (2 / 3, 'tercina de semínima'), (0.75, 'colcheia pontuada'),
               (0.5, 'colcheia'), (1 / 3, 'tercina de colcheia'), (0.375, 'semicolcheia pontuada'),
               (0.25, 'semicolcheia')]
    melhor = min(figuras, key=lambda fg: abs(ms / (fg[0] * seminima) - 1))
    if abs(ms / (melhor[0] * seminima) - 1) <= 0.06:
        return melhor[1]
    return None


# ===========================================================================
# INDICES
# ===========================================================================

def diferencas_eq(ref, rec, cfg):
    """dB por banda macro (referencia - voce), com a media tirada (so a forma conta)."""
    bandas = list(cfg['bandas_macro'])
    dif = {}
    for b in bandas:
        a, c = _valor(ref, f'eq_{b}'), _valor(rec, f'eq_{b}')
        if a is not None and c is not None:
            dif[b] = a - c
    if dif:
        media = float(np.mean(list(dif.values())))
        dif = {k: v - media for k, v in dif.items()}
    return dif


def _curva_eq_fina(ref, rec):
    """Diferenca por banda de 1/3 de oitava (para dizer 'em torno de X Hz')."""
    cr, cg = ref['curvas'].get('ltas_db'), rec['curvas'].get('ltas_db')
    hz = ref['curvas'].get('bandas_hz')
    if not cr or not cg or len(cr) != len(cg):
        return None, None
    d = np.array(cr) - np.array(cg)
    return np.array(hz), d - d.mean()


def indice_eq(dif, cfg):
    if not dif:
        return None
    rms = float(np.sqrt(np.mean(np.square(list(dif.values())))))
    tol = cfg['indices']['tolerancia_eq_db']
    esc = cfg['indices']['escala_eq_db']
    return 100.0 * float(np.exp(-0.5 * (max(0.0, rms - tol * 0.3) / esc) ** 2))


def indice_ganho(ref, rec, cfg):
    a, b = _valor(ref, 'indice_ganho'), _valor(rec, 'indice_ganho')
    if a is None or b is None:
        return None
    return 100.0 * float(np.exp(-0.5 * ((a - b) / cfg['indices']['escala_ganho']) ** 2))


def indice_dinamica(ref, rec, cfg):
    partes = []
    a, b = _valor(ref, 'decaimento_nota'), _valor(rec, 'decaimento_nota')
    if a is not None and b is not None:
        razao = np.log2((max(a, 0) + 3.0) / (max(b, 0) + 3.0))
        partes.append((razao / cfg['indices']['escala_sustain_oit']) ** 2)
    a, b = _valor(ref, 'faixa_dinamica'), _valor(rec, 'faixa_dinamica')
    if a is not None and b is not None:
        partes.append(((a - b) / cfg['indices']['escala_faixa_db']) ** 2)
    a, b = _valor(ref, 'tempo_ataque'), _valor(rec, 'tempo_ataque')
    if a is not None and b is not None:
        partes.append(((a - b) / cfg['indices']['escala_ataque_s']) ** 2)
    if not partes:
        return None
    pen = float(np.mean(partes))
    # ecos/cauda so num dos lados mexem no sustain medido: pesa menos
    amb = max(abs(ref['efeitos'].get(k, {}).get('score', 0) - rec['efeitos'].get(k, {}).get('score', 0))
              for k in ('delay', 'reverb'))
    if amb > 0.5:
        pen *= cfg['sugestoes']['fator_ganho_ambiencia'] ** 2
    return 100.0 * float(np.exp(-0.5 * pen))


def _penalidade_efeito(ef, r, g, cfg):
    """0 (igual) .. 1 (um tem e o outro nao, com certeza)."""
    sr, sg = r['score'], g['score']
    if max(sr, sg) < 0.3:
        return 0.0
    pen = abs(sr - sg)
    if sr >= 0.6 and sg >= 0.6:
        pen = max(pen, _diferenca_parametros(ef, r['parametros'], g['parametros'], cfg)[0])
    return float(np.clip(pen, 0, 1))


def _diferenca_parametros(ef, pr, pg, cfg):
    """(penalidade 0..1, lista de (param, ref, voce, texto)) quando os dois tem o efeito."""
    tol = cfg['sugestoes']['tolerancias']
    difs = []
    pen = 0.0

    def rel(chave, limite, nome, unidade, fmt='{:.0f}'):
        nonlocal pen
        a, b = pr.get(chave), pg.get(chave)
        if not a or not b:
            return
        erro = abs(a - b) / max(abs(a), 1e-6)
        if erro > limite:
            pen = max(pen, min(1.0, erro / (3 * limite)))
            difs.append((chave, a, b, f'{nome}: {fmt.format(a)} {unidade} no original, {fmt.format(b)} {unidade} no seu'))

    def absol(chave, limite, nome, fmt='{:.0%}'):
        nonlocal pen
        a, b = pr.get(chave), pg.get(chave)
        if a is None or b is None:
            return
        if abs(a - b) > limite:
            pen = max(pen, min(1.0, abs(a - b) / (3 * limite)))
            difs.append((chave, a, b, f'{nome}: {fmt.format(a)} no original, {fmt.format(b)} no seu'))

    if ef == 'delay':
        rel('time', tol['delay_tempo'], 'tempo', 'ms')
        absol('mix', tol['delay_mix'], 'volume das repetições')
        absol('feedback', tol['delay_feedback'], 'repetições (feedback)')
    elif ef == 'reverb':
        rel('decay', tol['reverb_decay'], 'cauda', 's', '{:.1f}')
        absol('mix', tol['reverb_mix'], 'quantidade de reverb')
    elif ef in ('tremolo', 'vibrato'):
        rel('rate', tol['modulacao_taxa'], 'velocidade', 'Hz', '{:.1f}')
        absol('depth', tol['modulacao_prof'], 'profundidade')
    elif ef in ('chorus', 'phaser', 'flanger', 'wah'):
        rel('rate', tol['modulacao_taxa'] * 2, 'velocidade', 'Hz', '{:.1f}')
    return pen, difs


def indice_categoria_efeitos(ref, rec, cfg, categoria):
    pen = []
    for ef in EFEITOS_PRESENCA:
        if CATEGORIA_EFEITO.get(ef) != categoria:
            continue
        r, g = ref['efeitos'].get(ef), rec['efeitos'].get(ef)
        if not r or not g:
            continue
        pen.append(_penalidade_efeito(ef, r, g, cfg) * IMPACTO_EFEITO.get(ef, 0.5))
    if not pen:
        return 100.0
    return 100.0 * float(np.exp(-1.2 * np.sum(pen)))


# ===========================================================================
# SUGESTOES
# ===========================================================================

def _sug(tipo, titulo, texto, impacto, confianca, pedal=None, valores=None, categoria=None,
         limiar_possivel=0.5):
    return {'tipo': tipo, 'titulo': titulo, 'texto': texto, 'impacto': float(np.clip(impacto, 0, 1)),
            'confianca': float(np.clip(confianca, 0, 1)), 'possivel': confianca < limiar_possivel,
            'pedal': pedal, 'valores': valores or {}, 'categoria': categoria}


def _sugestoes_efeitos(ref, rec, cfg, bpm):
    saida = []
    lp = cfg['sugestoes']['limiar_possivel']
    usados = set()
    ef_r, ef_g = ref['efeitos'], rec['efeitos']
    # phaser e flanger se confundem: compara a "familia varredura" antes
    fam_r = max(ef_r['phaser']['score'], ef_r['flanger']['score'])
    fam_g = max(ef_g['phaser']['score'], ef_g['flanger']['score'])
    if fam_r >= 0.6 and fam_g >= 0.6:
        usados.update(('phaser', 'flanger'))
        tipo_r = 'phaser' if ef_r['phaser']['score'] >= ef_r['flanger']['score'] else 'flanger'
        tipo_g = 'phaser' if ef_g['phaser']['score'] >= ef_g['flanger']['score'] else 'flanger'
        if tipo_r != tipo_g:
            conf = 0.4
            saida.append(_sug('ajuste', f'Talvez {_nome_pedal(tipo_r)} em vez de {_nome_pedal(tipo_g)}',
                              'Os dois têm um efeito de "varredura" no som. O do original parece mais '
                              f'um {_nome_pedal(tipo_r)}; confira se o tipo de modulação é o mesmo.',
                              0.35, conf, tipo_r, ef_r[tipo_r]['parametros'], 'modulacao', lp))
    for ef in EFEITOS_PRESENCA:
        if ef in usados:
            continue
        r, g = ef_r.get(ef), ef_g.get(ef)
        if not r or not g:
            continue
        nome = _nome_pedal(ef)
        cat = CATEGORIA_EFEITO.get(ef, 'modulacao')
        imp = IMPACTO_EFEITO.get(ef, 0.5)
        tem_r = r['presenca'] == 'sim' or (r['presenca'] == 'incerto' and r['score'] >= 0.45)
        tem_g = g['presenca'] == 'sim' or (g['presenca'] == 'incerto' and g['score'] >= 0.45)
        forte_r, forte_g = r['score'] >= 0.6, g['score'] >= 0.6
        if tem_r and not forte_g and r['score'] - g['score'] >= 0.3:
            conf = r['confianca'] * (1 - g['score'] * 0.5)
            texto = _texto_falta(ef, r, bpm)
            saida.append(_sug('falta', f'Falta: {nome}', texto, imp * r['score'], conf, ef,
                              _valores_pedal(ef, r['parametros']), cat, lp))
        elif tem_g and not forte_r and g['score'] - r['score'] >= 0.3:
            conf = g['confianca'] * (1 - r['score'] * 0.5)
            texto = (f'O seu som tem {nome} ({g["motivo"]}) e o original parece não ter. '
                     f'Experimente desligar o {nome} ou diminuir o mix/profundidade.')
            if ef == 'gate':
                texto = ('Seu som corta o fim das notas bem mais seco que o original: o Noise Gate '
                         'pode estar fechando cedo demais (limiar alto). Abaixe o limiar ou aumente o release.')
            saida.append(_sug('sobra', f'Sobra: {nome}', texto, imp * g['score'], conf, ef, {}, cat, lp))
        elif forte_r and forte_g:
            pen, difs = _diferenca_parametros(ef, r['parametros'], g['parametros'], cfg)
            if difs:
                conf = min(r['confianca'], g['confianca']) * 0.9
                texto = f'Os dois têm {nome}, mas ' + '; '.join(d[3] for d in difs) + '.'
                if ef == 'delay' and bpm:
                    fig = figura_do_tempo(r['parametros'].get('time'), bpm)
                    if fig:
                        texto += f' No original, o tempo bate com {fig} a {bpm:.0f} BPM.'
                saida.append(_sug('ajuste', f'Ajuste: {nome}', texto, imp * pen, conf, ef,
                                  _valores_pedal(ef, r['parametros']), cat, lp))
    return saida


def _valores_pedal(ef, par):
    """Parametros estimados -> valores dentro das faixas do curriculo."""
    try:
        from Estudos import curriculo_pedais as cur
        pedal = cur.PEDAIS_POR_ID[ef]
    except Exception:
        return dict(par)
    valores = {}
    for p in pedal['parametros']:
        if p['id'] in par and par[p['id']] is not None:
            valores[p['id']] = float(np.clip(par[p['id']], p['min'], p['max']))
    return valores


def _texto_falta(ef, r, bpm):
    nome = _nome_pedal(ef)
    p = r['parametros']
    if ef == 'delay':
        t = p.get('time', 0)
        fig = figura_do_tempo(t, bpm)
        extra = f' ({fig} a {bpm:.0f} BPM)' if fig else ''
        return (f'A música tem delay de ~{t:.0f} ms{extra}, com repetições em volume de '
                f'~{p.get("mix", 0) * 100:.0f}%, e o seu preset não. Adicione um Delay.')
    if ef == 'reverb':
        return (f'O original tem uma cauda de reverb de ~{p.get("decay", 0):.1f} s depois das notas e o seu '
                'som está mais seco. Adicione um Reverb (ou aumente o mix).')
    if ef == 'tremolo':
        return (f'O volume do original pulsa ~{p.get("rate", 0):.1f} vezes por segundo '
                f'(profundidade ~{p.get("depth", 0) * 100:.0f}%). Isso é um Tremolo.')
    if ef == 'vibrato':
        return f'A afinação do original oscila sozinha ~{p.get("rate", 0):.1f} Hz em todas as notas: Vibrato.'
    if ef == 'chorus':
        return ('Os harmônicos do original estão "espalhados", como se duas guitarras quase iguais '
                'tocassem juntas. Isso é típico de Chorus.')
    if ef in ('phaser', 'flanger'):
        return (f'O timbre do original "varre" devagar (~{p.get("rate", 0):.2f} Hz), como um jato ou '
                f'redemoinho: parece {nome}.')
    if ef == 'wah':
        return 'O brilho do original sobe e desce dentro das notas, como um pedal de Wah sendo mexido.'
    if ef == 'autowah':
        return ('No original o som abre (fica brilhante) na palhetada e fecha enquanto a nota morre: '
                'isso é um Envelope Filter (auto-wah).')
    if ef == 'octaver':
        return 'O original tem uma voz uma oitava abaixo junto das notas: Octaver.'
    if ef == 'ring':
        return 'O original tem notas "metálicas" fora da série harmônica, típicas de Ring Modulator.'
    if ef == 'volume':
        return f'As notas do original entram devagar (~{p.get("ataque", 0) * 1000:.0f} ms), sem o ataque da palhetada: pedal de Volume/Swell.'
    if ef == 'compressor':
        return 'O original sustenta mais e as notas têm volume mais parecido entre si: use um Compressor.'
    if ef == 'gate':
        return 'O original não tem chiado nas pausas: um Noise Gate ajudaria a limpar o seu som.'
    return f'O original parece ter {nome} e o seu preset não.'


def _sugestoes_ganho(ref, rec, cfg):
    saida = []
    lp = cfg['sugestoes']['limiar_possivel']
    a, b = _valor(ref, 'indice_ganho'), _valor(rec, 'indice_ganho')
    if a is None or b is None:
        return saida
    d = a - b
    lim = cfg['sugestoes']['limiar_ganho']
    classe_r = ref['curvas'].get('classe_ganho', 'limpo')
    classe_g = rec['curvas'].get('classe_ganho', 'limpo')
    nomes = {'limpo': 'limpo', 'boost': 'Clean Boost', 'overdrive': 'Overdrive', 'distorcao': 'Distorção'}
    conf = min(_conf(ref, 'indice_ganho'), _conf(rec, 'indice_ganho'))
    imp = min(1.0, abs(d) / 0.4)
    # delay/reverb so num dos lados misturam copias do som e mudam a crista:
    # a medida de ganho fica menos confiavel
    amb = max(abs(ref['efeitos'][k]['score'] - rec['efeitos'][k]['score']) for k in ('delay', 'reverb'))
    if amb > 0.5:
        conf *= cfg['sugestoes']['fator_ganho_ambiencia']
        imp *= cfg['sugestoes']['fator_ganho_ambiencia']
        lim *= 1.5
    if abs(d) < lim:
        return saida
    if d > 0:
        if classe_g == 'limpo':
            pedal = classe_r if classe_r != 'limpo' else 'overdrive'
            texto = (f'O original é saturado (parece {nomes.get(classe_r, classe_r)}) e o seu está limpo. '
                     f'Ligue um {_nome_pedal(pedal)} ou aumente o ganho do amp.')
            saida.append(_sug('falta', f'Falta: saturação ({_nome_pedal(pedal)})', texto, imp, conf, pedal,
                              {}, 'ganho', lp))
        else:
            texto = 'Seu som tem menos ganho que o original: aumente o drive'
            pedal = 'overdrive' if classe_g in ('boost', 'overdrive') else 'distorcao'
            if classe_r == 'distorcao' and classe_g in ('boost', 'overdrive'):
                texto += ' ou use Distorção em vez de Overdrive'
                pedal = 'distorcao'
            saida.append(_sug('timbre', 'Mais ganho', texto + '.', imp, conf, pedal, {}, 'ganho', lp))
    else:
        if classe_r == 'limpo':
            texto = ('O original é limpo e o seu está saturando. Desligue o drive ou abaixe o ganho '
                     '(e toque mais leve, se for o amp que está saturando).')
            saida.append(_sug('sobra', 'Sobra: saturação', texto, imp, conf, 'overdrive', {}, 'ganho', lp))
        else:
            texto = 'Seu som tem mais ganho que o original: abaixe o drive/dist'
            if classe_g == 'distorcao' and classe_r in ('boost', 'overdrive'):
                texto += ' ou troque a Distorção por um Overdrive'
            saida.append(_sug('timbre', 'Menos ganho', texto + '.', imp, conf,
                              'overdrive' if classe_r != 'distorcao' else 'distorcao', {}, 'ganho', lp))
    return saida


FAIXAS_EQ_PEDAL = {
    # banda -> (parametro do Equalizador do motor, frequencia de referencia)
    'graves': 'graves', 'medio_graves': 'medios', 'medios': 'medios',
    'medio_agudos': 'medios', 'agudos': 'agudos', 'presenca': 'agudos',
}


def _sugestoes_eq(ref, rec, cfg, perfil_guitarra=None, captador=None):
    saida = []
    lp = cfg['sugestoes']['limiar_possivel']
    dif = diferencas_eq(ref, rec, cfg)
    if not dif:
        return saida, dif
    hz, fina = _curva_eq_fina(ref, rec)
    lim = cfg['sugestoes']['limiar_banda_db']
    desvio_guitarra = _desvio_guitarra(cfg, perfil_guitarra, captador)
    ordem = sorted(dif.items(), key=lambda kv: -abs(kv[1]))
    for banda, d in ordem[:3]:
        if abs(d) < lim:
            continue
        nome = cfg['nomes_bandas'].get(banda, banda)
        a, b = cfg['bandas_macro'][banda]
        foco = ''
        if hz is not None:
            sel = (hz >= a) & (hz < b)
            if sel.any():
                i = np.argmax(np.abs(fina[sel]) * np.sign(d))
                f_c = hz[sel][i]
                foco = f' (mais perto de {f_c / 1000:.1f} kHz)' if f_c >= 1000 else f' (mais perto de {f_c:.0f} Hz)'
        faixa = f'{a / 1000:.1f} kHz a {b / 1000:.1f} kHz' if a >= 1000 else (
            f'{a:.0f} Hz a {b / 1000:.1f} kHz' if b >= 1000 else f'{a:.0f} a {b:.0f} Hz')
        if d > 0:
            texto = f'O original tem mais {nome.lower()} ({faixa}){foco}: ~{d:.0f} dB a mais que o seu.'
        else:
            texto = f'Seu som tem mais {nome.lower()} ({faixa}){foco}: ~{-d:.0f} dB acima do original.'
        # parte da diferenca vem da guitarra/captador, nao do preset?
        g = desvio_guitarra.get(banda) if desvio_guitarra else None
        if g is not None and abs(g) >= 1.5 and np.sign(g) == np.sign(-d):
            origem = 'do seu captador' if captador and not perfil_guitarra else 'da sua guitarra (calibração)'
            texto += (f' Parte disso (~{min(abs(g), abs(d)):.0f} dB) vem {origem}, não do preset: '
                      'ajuste também o tone/captador.')
        param = FAIXAS_EQ_PEDAL[banda]
        valores = {param: float(np.clip(d, -12, 12))}
        if param == 'medios':
            valores['freq_medios'] = float(np.clip(np.sqrt(a * b), 250, 3000))
        conf = min(_conf(ref, f'eq_{banda}'), _conf(rec, f'eq_{banda}')) * 0.9
        imp = min(1.0, abs(d) / 9.0)
        saida.append(_sug('timbre', f'EQ: {"mais" if d > 0 else "menos"} {nome.lower()}', texto, imp, conf,
                          'eq', valores, 'eq', lp))
    return saida, dif


def _desvio_guitarra(cfg, perfil_guitarra, captador):
    """
        Quanto a guitarra do usuario puxa cada banda para cima/baixo, em dB:
        da calibracao (som limpo gravado) comparado com o modelo de DI do
        config, ou, sem calibracao, do tipo de captador.
    """
    modelo = cfg.get('modelo_di_db')
    if perfil_guitarra and modelo:
        dif = {}
        for b, v in modelo.items():
            g = _valor(perfil_guitarra, f'eq_{b}')
            if g is not None:
                dif[b] = g - v
        if dif:
            m = float(np.mean(list(dif.values())))
            return {k: v - m for k, v in dif.items()}
    if captador and captador in cfg.get('captadores', {}):
        return dict(cfg['captadores'][captador]['offset_db'])
    return {}


def _sugestoes_dinamica(ref, rec, cfg, ja):
    saida = []
    lp = cfg['sugestoes']['limiar_possivel']
    if any(s['pedal'] == 'compressor' for s in ja):
        return saida
    a, b = _valor(ref, 'decaimento_nota'), _valor(rec, 'decaimento_nota')
    if a is None or b is None:
        return saida
    razao = np.log2((max(a, 0) + 3.0) / (max(b, 0) + 3.0))
    lim = cfg['sugestoes']['limiar_sustain_oit']
    conf = min(_conf(ref, 'decaimento_nota'), _conf(rec, 'decaimento_nota'))
    amb = max(abs(ref['efeitos'][k]['score'] - rec['efeitos'][k]['score']) for k in ('delay', 'reverb'))
    if amb > 0.5:
        conf *= cfg['sugestoes']['fator_ganho_ambiencia']
        lim *= 1.5
    if razao < -lim:
        saida.append(_sug('ajuste', 'Mais sustain', f'As notas do original sustentam mais (caem ~{max(a, 0):.0f} '
                          f'dB/s contra ~{max(b, 0):.0f} dB/s no seu). Um Compressor (ou um pouco mais de ganho) '
                          'ajuda.', min(1, -razao / 2), conf, 'compressor', {'sustain': 0.6}, 'dinamica', lp))
    elif razao > lim:
        saida.append(_sug('ajuste', 'Menos sustain', f'Suas notas sustentam mais que as do original (~{max(b, 0):.0f} '
                          f'contra ~{max(a, 0):.0f} dB/s). Tire compressão ou ganho para o som "respirar".',
                          min(1, razao / 2), conf, 'compressor', {'sustain': 0.2}, 'dinamica', lp))
    return saida


def _sugestoes_altura(ref, rec, cfg):
    """Transposicao / oitava diferente: whammy, octaver, afinacao, capotraste."""
    saida = []
    lp = cfg['sugestoes']['limiar_possivel']
    cr, cg = ref['curvas'].get('croma'), rec['curvas'].get('croma')
    ma, mb = _valor(ref, 'altura_mediana'), _valor(rec, 'altura_mediana')
    conf_alt = min(_conf(ref, 'altura_mediana'), _conf(rec, 'altura_mediana'))
    if ma is not None and mb is not None and conf_alt > 0.3:
        d = ma - mb
        if abs(abs(d) - 12) <= 1.5:
            direcao = 'acima' if d > 0 else 'abaixo'
            saida.append(_sug('ajuste', f'Uma oitava {direcao}',
                              f'As notas do original soam uma oitava {direcao} das suas. Pode ser um '
                              f'{"Whammy/Octaver (oitava acima)" if d > 0 else "Octaver"} ou só outra '
                              'região do braço.', 0.6, conf_alt * 0.7,
                              'whammy' if d > 0 else 'octaver',
                              {'intervalo': 12.0} if d > 0 else {'sub': 0.8, 'seco': 0.2}, 'modulacao', lp))
            return saida
    if cr and cg:
        cr, cg = np.array(cr), np.array(cg)
        corr = [float(np.dot(cr - cr.mean(), np.roll(cg, k) - cg.mean())) for k in range(12)]
        k = int(np.argmax(corr))
        norma = np.linalg.norm(cr - cr.mean()) * np.linalg.norm(cg - cg.mean()) + 1e-12
        if k != 0 and corr[k] / norma > 0.75 and corr[k] - corr[0] > 0.25 * norma:
            semis = k if k <= 6 else k - 12
            saida.append(_sug('ajuste', f'Transposto {semis:+d} semitom(ns)',
                              f'As notas do original parecem {abs(semis)} semitom(ns) '
                              f'{"acima" if semis > 0 else "abaixo"} das suas. Confira a afinação '
                              '(meio tom abaixo? drop?), o capotraste ou um Whammy.', 0.5, 0.45,
                              'whammy', {'intervalo': float(semis)}, 'modulacao', lp))
    return saida


# ===========================================================================
# COMPARACAO COMPLETA
# ===========================================================================

def tabela_medidas(ref, rec):
    linhas = []
    for chave in sorted(set(ref['medidas']) | set(rec['medidas'])):
        a, b = ref['medidas'].get(chave, {}), rec['medidas'].get(chave, {})
        va, vb = a.get('valor'), b.get('valor')
        linhas.append({'chave': chave, 'nome': a.get('nome') or b.get('nome') or chave,
                       'familia': a.get('familia') or b.get('familia') or '',
                       'unidade': a.get('unidade') or b.get('unidade') or '',
                       'referencia': va, 'voce': vb,
                       'diferenca': (va - vb) if va is not None and vb is not None else None,
                       'confianca': min(a.get('confianca', 0), b.get('confianca', 0))})
    return linhas


def comparar(ref, rec, cfg=None, bpm=None, perfil_guitarra=None, captador=None, separado=False):
    """
        Como funciona: calcula os indices por categoria, gera as sugestoes
        (efeitos que faltam/sobram, parametros diferentes, ganho, EQ,
        dinamica e altura), ordena pelo impacto x confianca e junta avisos.
        Para que serve: e o resultado que a tela do Analisador mostra.
        Onde e usada: Analisador/analisador_ia.py, testes, relatorio.
    """
    cfg = cfg or at.carregar_config(ref.get('instrumento', 'guitarra'))
    sugestoes = []
    sugestoes += _sugestoes_efeitos(ref, rec, cfg, bpm)
    sugestoes += _sugestoes_ganho(ref, rec, cfg)
    s_eq, dif = _sugestoes_eq(ref, rec, cfg, perfil_guitarra, captador)
    sugestoes += s_eq
    sugestoes += _sugestoes_dinamica(ref, rec, cfg, sugestoes)
    sugestoes += _sugestoes_altura(ref, rec, cfg)
    sugestoes.sort(key=lambda s: -(s['impacto'] * (0.4 + 0.6 * s['confianca'])))

    indices = {
        'eq': indice_eq(dif, cfg),
        'ganho': indice_ganho(ref, rec, cfg),
        'dinamica': indice_dinamica(ref, rec, cfg),
        'modulacao': indice_categoria_efeitos(ref, rec, cfg, 'modulacao'),
        'ambiencia': indice_categoria_efeitos(ref, rec, cfg, 'ambiencia'),
    }
    pesos = cfg['indices']['pesos']
    num = sum(pesos[k] * v for k, v in indices.items() if v is not None)
    den = sum(pesos[k] for k, v in indices.items() if v is not None)
    geral = num / den if den else None

    avisos = [AVISO_REFERENCIA]
    if separado or ref.get('separado'):
        avisos.append('A referência foi separada da mixagem (Demucs): a separação deixa artefatos que '
                      'parecem reverb/chorus, então a confiança dessas medidas foi reduzida.')
    if ref['efeitos'].get('reverb', {}).get('sem_pausas') or rec['efeitos'].get('reverb', {}).get('sem_pausas'):
        avisos.append('O trecho quase não tem pausas: reverb e noise gate foram medidos com pouca certeza. '
                      'Escolha um trecho com notas soltas para medir melhor a ambiência.')
    if ref.get('duracao', 0) < cfg['analise']['duracao_minima_s']:
        avisos.append('Trecho curto: as medidas de modulação e ambiência ficam menos confiáveis.')

    return {
        'indice_geral': None if geral is None else round(float(geral), 1),
        'indices': {k: (None if v is None else round(float(v), 1)) for k, v in indices.items()},
        'sugestoes': sugestoes,
        'tabela': tabela_medidas(ref, rec),
        'eq_bandas': {k: round(float(v), 2) for k, v in dif.items()},
        'avisos': avisos,
        'resumo': resumo(geral, indices, sugestoes),
    }


def resumo(geral, indices, sugestoes):
    """Uma frase para o topo da tela."""
    if geral is None:
        return 'Não foi possível comparar os dois sons.'
    if geral >= 85:
        frase = 'Seu som está bem próximo do original.'
    elif geral >= 65:
        frase = 'Seu som está no caminho: faltam alguns ajustes.'
    elif geral >= 40:
        frase = 'Seu som está diferente do original em pontos importantes.'
    else:
        frase = 'Seu som está bem diferente do original.'
    certas = [s for s in sugestoes if not s['possivel']]
    if certas:
        frase += f' Comece por: {certas[0]["titulo"]}.'
    return frase


def relatorio_markdown(resultado, titulo='Analisador IA', info=None):
    """Relatorio em Markdown (mesmo formato usado pelo Estudo de Tempo para exportar)."""
    info = info or {}
    linhas = [f'# {titulo}', '']
    for k, v in info.items():
        linhas.append(f'- **{k}:** {v}')
    if info:
        linhas.append('')
    g = resultado['indice_geral']
    linhas += [f'## Compatibilidade: {g:.0f}/100 (estimativa)' if g is not None else '## Compatibilidade: -', '',
               resultado['resumo'], '']
    linhas.append('| Categoria | Índice |')
    linhas.append('| --- | --- |')
    for k in CATEGORIAS:
        v = resultado['indices'].get(k)
        linhas.append(f'| {NOMES_CATEGORIA[k]} | {"-" if v is None else f"{v:.0f}"} |')
    linhas.append('')
    for tipo in TIPOS:
        grupo = [s for s in resultado['sugestoes'] if s['tipo'] == tipo]
        if not grupo:
            continue
        linhas.append(f'## {NOMES_TIPO[tipo]}')
        for s in grupo:
            marca = ' _(possível)_' if s['possivel'] else ''
            linhas.append(f'- **{s["titulo"]}**{marca} — {s["texto"]} '
                          f'(confiança {s["confianca"] * 100:.0f}%)')
        linhas.append('')
    linhas.append('## Medidas')
    linhas.append('| Medida | Referência | Você | Unidade | Confiança |')
    linhas.append('| --- | --- | --- | --- | --- |')
    for m in resultado['tabela']:
        fmt = lambda v: '-' if v is None else f'{v:.2f}'
        linhas.append(f'| {m["nome"]} | {fmt(m["referencia"])} | {fmt(m["voce"])} | {m["unidade"]} | '
                      f'{m["confianca"] * 100:.0f}% |')
    linhas.append('')
    for a in resultado['avisos']:
        linhas.append(f'> {a}')
    return '\n'.join(linhas) + '\n'


# ===========================================================================
# ANALISE COMPLETA DE UM PAR (referencia x gravacao) E HISTORICO
# ===========================================================================

def analisar(ref, sr_ref, rec, sr_rec, instrumento='guitarra', bpm=None, deslocamento_s=0.0,
             perfil_guitarra=None, captador=None, separado=False, progresso=None, cancelar=None):
    """
        Como funciona: pre-processa os dois sinais (mono, 32 kHz, sem DC),
        refina o alinhamento (correlacao do envelope de ataques em volta de
        'deslocamento_s', que ja vem com a latencia descontada), recorta o
        mesmo trecho nos dois, calcula os perfis de timbre (loudness
        normalizada) e compara.
        Devolve dict com 'resultado' (comparar), 'perfil_ref', 'perfil_rec',
        'alinhamento' (s, confianca) e os sinais preparados (para graficos/A-B).
        Para que serve: o botao "Analisar" da Etapa 5 (roda numa thread).
    """
    def passo(p, msg):
        if progresso:
            progresso(p, msg)
        if cancelar is not None and cancelar.is_set():
            raise RuntimeError('Análise cancelada.')
    cfg = at.carregar_config(instrumento)
    passo(0.05, 'Preparando os áudios...')
    a = at.preprocessar(ref, sr_ref)
    b = at.preprocessar(rec, sr_rec)
    passo(0.15, 'Alinhando a gravação com a música...')
    desl, conf_al = at.alinhar(a, b, at.SR_ANALISE, deslocamento_s, busca=0.35)
    if conf_al < 0.15:
        desl = deslocamento_s                  # sem ataques parecidos: confia no playback + latencia
    a, b = at.recortar_alinhado(a, b, desl)
    if a.size < at.SR_ANALISE * 1.0:
        raise RuntimeError('O trecho em comum ficou curto demais para analisar.')
    passo(0.3, 'Medindo o timbre da música...')
    pr = at.perfil_timbre(a, at.SR_ANALISE, cfg, separado=separado)
    passo(0.65, 'Medindo o timbre da sua gravação...')
    pg = at.perfil_timbre(b, at.SR_ANALISE, cfg)
    passo(0.9, 'Comparando...')
    res = comparar(pr, pg, cfg, bpm=bpm, perfil_guitarra=perfil_guitarra, captador=captador,
                   separado=separado)
    passo(1.0, 'Pronto')
    return {'resultado': res, 'perfil_ref': pr, 'perfil_rec': pg,
            'alinhamento': {'deslocamento_s': float(desl), 'confianca': float(conf_al)},
            'ref_preparada': a, 'rec_preparada': b, 'sr': at.SR_ANALISE}


def _arquivo_historico(ref_id):
    import os
    from audio import dispositivos as disp
    pasta = os.path.join(disp.pasta_dados(), 'historico')
    os.makedirs(pasta, exist_ok=True)
    return os.path.join(pasta, f'{ref_id or "sem_referencia"}.json')


def salvar_historico(ref_id, resultado, info=None):
    """Acrescenta a analise ao historico da musica (para comparar tentativas de ajuste)."""
    import json
    import time as _time
    caminho = _arquivo_historico(ref_id)
    try:
        with open(caminho, encoding='utf-8') as f:
            lista = json.load(f)
    except (OSError, ValueError):
        lista = []
    lista.append({'quando': _time.time(), 'indice_geral': resultado['indice_geral'],
                  'indices': resultado['indices'],
                  'sugestoes': [s['titulo'] for s in resultado['sugestoes'][:6]],
                  'info': info or {}})
    try:
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(lista[-50:], f, ensure_ascii=False, indent=1)
    except OSError:
        pass
    return lista[-50:]


def listar_historico(ref_id):
    import json
    try:
        with open(_arquivo_historico(ref_id), encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return []
