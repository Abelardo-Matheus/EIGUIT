# -*- coding: utf-8 -*-
"""
Suite das pedaleiras integradas (pedaleiras/).

Usa arquivos REAIS exportados do M-EFCS (dados_pedaleiras/mk300), cada um com
uma mudanca conhecida em relacao ao anterior, e confere que o leitor acha
exatamente o valor que estava na tela do M-EFCS. Depois confere gravar/ler,
o plano de mudancas gerado a partir de sugestoes do Analisador e a comparacao
usada em "Conferir importação".

    python3 _validacao/teste_pedaleiras.py
"""
import os
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from pedaleiras import registro  # noqa: E402
from pedaleiras.base import ErroFormato  # noqa: E402
from pedaleiras.mk300 import formato as fmt  # noqa: E402
from pedaleiras.mk300 import modelos as mdl  # noqa: E402
from pedaleiras.mk300.modelos import AMP, CAB, DLY, DS, EQ, FX, GATE, MOD, REV, VOL, WAH  # noqa: E402

DADOS = os.path.join(RAIZ, '_validacao', 'dados_pedaleiras', 'mk300')
falhas = []


def checar(cond, msg):
    print(('  ok   ' if cond else '  FALHA ') + msg)
    if not cond:
        falhas.append(msg)


def ler(nome):
    return fmt.ler_preset(os.path.join(DADOS, nome + '.dzh'))


def teste_campos():
    print('campos conferidos com a tela do M-EFCS')
    b = ler('p00_base')
    checar(b.nome == 'USER PRESET 160', f'nome {b.nome!r}')
    checar((b.volume, b.bpm, b.pan) == (60, 80, 0), 'Preset Vol 60, BPM 80, Pan C')
    checar(b.cadeia == list(range(11)), 'cadeia padrao')
    checar(b.knobs(AMP)[:8] == [50, 50, 50, 50, 50, 0, 50, 100], 'AMP base')
    checar(mdl.nome_modelo(AMP, b.modelo(AMP)) == '1CL-UweTwins', 'AMP 1CL-UweTwins')
    checar(mdl.nome_modelo(CAB, b.modelo(CAB)) == '1EAGLProV30s', 'CAB 1EAGLProV30s')
    checar(b.knobs(CAB)[:3] == [80, 20, 180], 'CAB Level 80 / Low Cut 20 / High Cut 18.0K')
    checar(b.knob(VOL, 0) == 71, 'VOL 71')

    p = ler('p01_amp')
    checar(p.ligado(AMP) and p.knobs(AMP)[:8] == [56, 66, 58, 38, 69, 4, 32, 96], 'AMP knobs + ligado')
    p = ler('p02_wah')
    checar(p.ligado(WAH) and mdl.MODELOS[WAH][p.modelo(WAH)] == 'Cry-Wah' and p.knobs(WAH)[:3] == [54, 44, 60],
           'WAH Cry-Wah 54/44/60')
    p = ler('p03_fx')
    checar(p.ligado(FX) and mdl.MODELOS[FX][p.modelo(FX)] == 'Compress' and p.knobs(FX)[:4] == [56, 40, 52, 80],
           'FX Compress 56/40/52/80')
    p = ler('p04_gate')
    checar(p.ligado(GATE) and mdl.MODELOS[GATE][p.modelo(GATE)] == 'Hard Gate' and p.knob(GATE, 0) == -57,
           'GATE Hard Gate Thd -57')
    p = ler('p05_ds')
    checar(p.ligado(DS) and mdl.nome_modelo(DS, p.modelo(DS)) == '8OD-KlonC'
           and p.knobs(DS)[:8] == [56, 46, 52, 44, 54, 6, 48, 92], 'DS 8OD-KlonC + knobs')
    p = ler('p06_ampmodel')
    checar(mdl.nome_modelo(AMP, p.modelo(AMP)) == '120BassRIan', 'AMP 120')
    p = ler('p07_cab')
    checar(p.ligado(CAB) and mdl.nome_modelo(CAB, p.modelo(CAB)) == '100BassUdio' and p.knobs(CAB)[:2] == [74, 37],
           'CAB 100BassUdio, Level 74, Low Cut 37')
    p = ler('p08_eq')
    desc = {x['nome']: x['texto'] for x in _modulo(p, EQ)['params']}
    checar(p.ligado(EQ) and [desc[k] for k in ('100Hz', '200Hz', '400Hz', '800Hz', '1.6kHz', '3.2kHz')]
           == ['+1.5 dB', '-1.0 dB', '+1.0 dB', '-1.0 dB', '+2.5 dB', '-2.0 dB'], 'EQ Guitar EQ 6 em meio dB')
    p = ler('p09_mod')
    desc = {x['nome']: x['texto'] for x in _modulo(p, MOD)['params']}
    checar(p.ligado(MOD) and mdl.MODELOS[MOD][p.modelo(MOD)] == 'Phaser'
           and (desc['Speed'], desc['MidCut'], desc['Reso'], desc['Fb']) == ('1.6', '44', '54', '60'),
           'MOD Phaser 1.6/44/54/60')
    p = ler('p10_modsync')
    desc = {x['nome']: x['texto'] for x in _modulo(p, MOD)['params']}
    checar(desc['Sync'] == 'ligado' and desc['Speed'] == '1/4', 'MOD sync ligado -> Speed 1/4')
    p = ler('p11_dly')
    checar(p.ligado(DLY) and mdl.MODELOS[DLY][p.modelo(DLY)] == 'Analog' and p.knobs(DLY)[:3] == [532, 32, 42],
           'DLY Analog 532 ms / 32 / 42')
    p = ler('p12_rev')
    checar(p.ligado(REV) and mdl.MODELOS[REV][p.modelo(REV)] == 'Hall stereo'
           and p.knobs(REV)[:5] == [46, 31, 62, 57, 43], 'REV Hall stereo 46/31/62/57/43')
    p = ler('p13_vol')
    checar((p.volume, p.bpm, p.pan, p.knob(VOL, 0)) == (63, 85, 2, 65), 'Preset Vol 63, BPM 85, Pan R2, VOL 65')
    p = ler('p14_chain')
    checar([mdl.MODULOS[m] for m in p.cadeia] ==
           ['WAH', 'FX', 'GATE', 'DS', 'MOD', 'AMP', 'CAB', 'EQ', 'DLY', 'REV', 'VOL'], 'cadeia com MOD antes do AMP')


def _modulo(p, m):
    d = registro.obter('mk300')
    return next(x for x in d.descrever_preset(p) if x['id'] == m)


def teste_eq_global():
    print('EQ global (.dzheq)')
    e = fmt.ler_eq(os.path.join(DADOS, 'g00_eq_base.dzheq'))
    checar(e.ligado and (e.lc, e.hc) == (93, 7689), 'ligado, LC 93, HC 7.7K')
    checar([e.freq(b) for b in range(4)] == [265, 750, 2421, 6054], 'frequencias')
    checar([e.ganho(b) for b in range(4)] == [-3, 2, 2, -2] and [e.q(b) for b in range(4)] == [0.7] * 4,
           'ganhos e Q')
    m = fmt.ler_eq(os.path.join(DADOS, 'g01_eq_mod.dzheq'))
    checar((m.ligado, m.lc, m.freq(0), m.q(1), m.ganho(2), m.ganho(3)) == (False, 100, 387, 1.3, 1, -1),
           'mudancas da tela: off, LC 100, P1 387, P2 Q1.3, P3 +1, P4 -1')


def teste_gravar_ler():
    print('gravar e ler de novo')
    d = registro.obter('mk300')
    b = ler('p05_ds')
    pasta = tempfile.mkdtemp()
    c = os.path.join(pasta, 'x.dzh')
    d.salvar_preset(b, c)
    checar(open(c, 'rb').read() == b.para_bytes(), 'bytes identicos ao original')
    n = b.copia()
    n.nome = 'EIGUIT TESTE'
    n.set_knob(AMP, 0, 77)
    d.salvar_preset(n, c)
    r = d.ler_preset(c)
    checar(r.nome == 'EIGUIT TESTE' and r.knob(AMP, 0) == 77, 'nome e knob alterados')
    checar(r.dados[0x14A:] == b.dados[0x14A:], 'atribuicoes de pedal preservadas')
    difs = d.comparar(n, r)
    checar(difs == [], 'comparar arquivo igual -> sem diferencas')
    r.set_knob(DLY, 1, 9)
    difs = d.comparar(n, r)
    checar(len(difs) == 1 and difs[0]['campo'] == 'DLY: Fb', f'comparar acha a diferenca ({difs})')
    try:
        fmt.PresetMK300(b'\0' * 10)
        checar(False, 'tamanho errado deveria falhar')
    except ErroFormato:
        checar(True, 'tamanho errado -> ErroFormato')


def _sug(tipo, pedal, valores=None, titulo='', impacto=0.6, confianca=0.8):
    return {'tipo': tipo, 'pedal': pedal, 'valores': valores or {}, 'titulo': titulo or f'{tipo} {pedal}',
            'impacto': impacto, 'confianca': confianca, 'possivel': confianca < 0.5}


def teste_plano():
    print('sugestoes do Analisador -> mudancas no preset')
    d = registro.obter('mk300')
    b = ler('p00_base')
    eq = fmt.ler_eq(os.path.join(DADOS, 'g00_eq_base.dzheq'))
    sugs = [_sug('falta', 'delay', {'time': 420.0, 'feedback': 0.35, 'mix': 0.3}, 'Falta: Delay'),
            _sug('falta', 'reverb', {'decay': 2.5, 'mix': 0.25}, 'Falta: Reverb'),
            _sug('falta', 'overdrive', {}, 'Falta: saturação (Overdrive)'),
            _sug('timbre', 'eq', {'graves': -4.0}, 'EQ: menos graves'),
            _sug('timbre', 'eq', {'medios': 3.0, 'freq_medios': 800.0}, 'EQ: mais médios'),
            _sug('falta', 'chorus', {'rate': 0.8}, 'Falta: Chorus', confianca=0.3)]
    plano = d.planejar(b, sugs, eq, {'destino_eq': 'preset'})
    novo, _ = d.aplicar(b, plano['mudancas'], eq)
    checar(novo.ligado(DLY) and novo.knobs(DLY)[:3] == [420, 35, 30], 'delay ligado com 420 ms / 35 / 30')
    checar(novo.ligado(REV) and novo.knob(REV, 1) == 25, 'reverb ligado, mix 25')
    checar(novo.ligado(DS) and mdl.categoria_ganho(mdl.MODELOS[DS][novo.modelo(DS)]) == 'overdrive' and novo.knob(DS, 0) >= 55,
           'drive ligado (OD) com ganho')
    checar(novo.ligado(EQ) and novo.knob(EQ, 0) == -8 and novo.knob(EQ, 1) == -4 and novo.knob(EQ, 3) == 6,
           'EQ do preset: graves -4 dB (100 Hz) / -2 (200 Hz), médios +3 dB em 800 Hz')
    checar(not novo.ligado(MOD), 'sugestão de baixa confiança fica desmarcada (chorus não entra)')
    marc = [m for m in plano['mudancas'] if m['origem'] == 'Falta: Chorus']
    checar(marc and not any(m['aplicar'] for m in marc), 'mudanças do chorus aparecem desmarcadas')
    for m in marc:
        m['aplicar'] = True
    novo2, _ = d.aplicar(b, plano['mudancas'], eq)
    checar(novo2.ligado(MOD) and novo2.knob(MOD, 0) == 8, 'marcando na tela, o chorus entra (Speed 0.8)')

    plano = d.planejar(b, [_sug('timbre', 'eq', {'agudos': 3.0})], eq, {'destino_eq': 'global'})
    _p, eq2 = d.aplicar(b, plano['mudancas'], eq)
    checar(eq2.ganho(3) == 1 and eq2.ganho(0) == -3, 'EQ global: agudos +3 dB na banda de 6 kHz (-2 -> +1)')

    sobra = ler('p12_rev')
    plano = d.planejar(sobra, [_sug('sobra', 'reverb', {}, 'Sobra: Reverb')], None)
    novo, _ = d.aplicar(sobra, plano['mudancas'])
    checar(not novo.ligado(REV), 'sobra de reverb desliga o REV')


def teste_registro():
    print('registro')
    lista = registro.listar()
    checar(lista[0].id == 'mk300' and lista[0].implementado, 'MK-300 primeiro e implementado')
    checar(len(lista) >= 4 and not any(d.implementado for d in lista[1:]), 'demais listadas como "em breve"')


teste_campos()
teste_eq_global()
teste_gravar_ler()
teste_plano()
teste_registro()
print()
print('TUDO OK' if not falhas else f'{len(falhas)} FALHA(S)')
sys.exit(1 if falhas else 0)
