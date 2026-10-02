# -*- coding: utf-8 -*-
"""
Nomes dos modulos, modelos e knobs da MK-300 (firmware v72, M-EFCS).

Tudo aqui foi conferido na tela do M-EFCS e nos arquivos exportados por ele
(_validacao/dados_pedaleiras/mk300). Os modelos de DS, AMP e CAB sao "slots"
da pedaleira: se voce importar outra captura/IR por cima de um slot (Sounds /
Community do M-EFCS), o nome muda la, e da para atualizar a lista aqui.

Tipos de knob (como o valor fica guardado no arquivo, sempre int16):
    pct     0..100
    x10     valor/10 (ex.: Speed 16 = 1.6)
    ms      milissegundos
    hz      hertz
    x100hz  valor*100 Hz (ex.: 180 = 18.0 kHz)
    meio_db valor/2 dB (EQ do preset: 3 = +1.5 dB)
    db      dB com sinal (limiar do gate)
    sync    0 = livre, 1 = sincronizado ao BPM
"""

MODULOS = ['WAH', 'FX', 'GATE', 'DS', 'AMP', 'CAB', 'EQ', 'MOD', 'DLY', 'REV', 'VOL']
WAH, FX, GATE, DS, AMP, CAB, EQ, MOD, DLY, REV, VOL = range(11)

MODELOS = {
    WAH: ['X-Wah', 'Funk-Wah', 'Slide-Wah', 'Cry-Wah', 'Wah-Wah', 'Sense-Wah'],
    FX: ['Wah-Wah', 'Lofi', 'Sense-Wah', 'Boost', 'A Boost', 'E Boost', 'B Boost', 'Boost ED',
         'Compress', 'Compress Pro', 'F Compress', 'Pitch', 'Octave', 'Ring', 'Pitch shifter', 'Whammy'],
    GATE: ['AI Gate', 'Soft Gate', 'Hard Gate', 'Pro Gate', 'Compress', 'Compress Pro', 'F Compress',
           'AI Ms Gate'],
    DS: ['OD-BDTWOOW', 'OD-ONEE', 'OD-THREEE', 'OD-SDONEE', 'OD-AngChar', 'OD-DarkF', 'OD-DarkF+',
         'OD-KlonC', 'OD-MrSug', 'OD-TSTenn', 'OD-X8BP', 'OD-Eight0E', 'OD-Mvave1', 'OD-Mvave2',
         'OD-ProRat', 'DS-ONEE', 'DS-DATWOO', 'DS-MZTWOO', 'DS-HMTWOO', 'DS-MLTWOO', 'DS-MTTWOO',
         'DS-ONEEW', 'DS-DodG69', 'DS-Mvave', 'DS-WalALH', 'FZ-FIVEE', 'FZ-TFourr', 'FZ-BigMff',
         'BT-FBTWOO', 'BT-Mvave', 'BOD-BTK', 'BOD-BTK+', 'BOD-GuyFlip', 'BOD-Ffd2M', 'BOD-DCXX',
         'BFZ-MxrrD', 'BFZ-EhxxGB', 'BFZ-ImppS2', 'BBT-Sat4HA', 'BBT-StuMin'],
    AMP: ['CL-UweTwins', 'CL-UKC30', 'OD-MarVM410', 'OD-MarVicto', 'DS-RandSanat', 'DS-MarsFD100',
          'DS-EagleS', 'DS-DiselHgn', 'DS-EV5150Com', 'CL-FORTIN', 'CL-MessMkt', 'CL-CA-tweed',
          'OD-BogSV20', 'DS-JuiceJIM', 'DS-SurSL68', 'BassADAtube', 'BassAlmbic', 'BassGKmb21',
          'BassTrTrad', 'BassMaT501', 'CL-BogBlue', 'CL-BogSh20', 'DS-BogSh20+', 'DS-BogES20',
          'CL-MesaMk35', 'CL-MesaStar', 'DS-MesaDR', 'DS-MesaDR+', 'CL-FenDvCom', 'CL-Fen65',
          'OD-Fen65p', 'CL-Fen66', 'CL-Fen94', 'CL-FenRed', 'OD-Fenftman', 'CL-FenBM59', 'CL-FenBM67',
          'DS-MarJpCom', 'OD-MarJ900', 'DS-MarJ900+', 'DS-MarJ2000', 'DS-Mar2555', 'DS-Mar59',
          'DS-Mar69', 'OD-MarSV20', 'DS-MarSV20+', 'DS-CusPT50', 'CL-OgTB50,a', 'DS-OgRB100+',
          'OD-TKGemCom', 'DS-LnyG100L', 'OD-SurSL68', 'DS-SurSL68+', 'CL-SurBr35', 'DS-SurBr35+',
          'OD-EngPB2', 'DS-EngPB2+', 'DS-EngMK60', 'CL-Pey6534', 'DS-Pey6505', 'DS-Pey5150',
          'OD-Sold100', 'DS-Sold100+', 'OD-SoldH25', 'DS-SoldH25+', 'CL-DieV4C2', 'DS-DieV4C3',
          'DS-DieV2', 'CL-TwoRB', 'CL-TwoRC', 'OD-Fman100', 'DS-Fman100+', 'CL-GojaX', 'DS-GojaX',
          'DS-RanIIDia', 'DS-RanIISat', 'CL-MatDC30', 'OD-MatLG15', 'CL-Brit1', 'OD-Brit2',
          'DS-Brit3', 'OD-SuperCom', 'CL-Magan50', 'OD-Fen8DVL', 'CL-J120Com', 'OD-DumOD',
          'OD-TimHson', 'DS-SplNito', 'DS-DwodNig', 'DS-Omga', 'AC-Petrucci', 'AC-FenRa',
          'AC-Bens', 'AC-BClassic', 'AC-D45', 'BassSVTCL', 'BassAG751', 'BassAGTH', 'BassT21VT',
          'BassT21VT+', 'BassSan1', 'BassSan2', 'BassSan3', 'BassMaTA', 'BassMaLM4', 'BassMaLMV',
          'BassPJ200', 'BassPJ400', 'BassPJCUB', 'BassMes400', 'BassMes400', 'BassBman10',
          'BassBman70', 'BassFenRum', 'BassDark7k', 'BassDarkVT', 'BassHiwaDR', 'BassHake',
          'BassOgAD', 'BassRIan'],
    CAB: ['EAGLProV30s', 'Sperimental', 'Juice4x12V30', 'Mess Bog', 'FdChamp', 'FdPrJunir',
          'Mar960BV30', 'DizzlV30', 'Elctrovoice', 'MessRectV30', 'TwinJensenC', 'TwedDlx1X12',
          'FendShowman', 'J120Rolnd', 'AC30Silvers', 'BassAgula25', 'BassJensn10', 'BassStdio22',
          'BassAmpg410', 'BassEDN300', 'FenTwed', 'FenChap', 'FenDelu', 'FenBface', 'FenMnTw',
          'FenTwin', 'FenBman', 'FenPrin2', 'FenProJ', 'FenTChap', 'MessOS', 'MessBRO', 'MessIM24',
          'MessREC', 'MessStdio', 'MessStito', 'MessNom', 'Mar60', 'Mar36', 'MarMG15R', 'MarJ2000',
          'MarMfour', 'MarPlx', 'MarVal4', 'MarVal2', 'MarVS412', 'ENG412', 'ENG412+', 'ENG412P',
          'OgP412', 'OgP212', 'OgV30', 'Pey5150', 'PeyDeBlu', 'PeyDeBlu+', 'SoldHor', 'SoldSC412',
          'SoldSC212', 'SoldAng412', 'Alton212', 'BogUX', 'DieV30', 'FimanVt', 'HaBtonV', 'RanII',
          'VHTDeli', 'VxAc15', 'VxAc30', 'CeleAt', 'CeleBlue', 'AC-CeCrm', 'AC-CeVine', 'AC-EmG112',
          'AC-EmG212', 'AC-Se210', 'AC-SeTV20', 'AC-SeGol', 'AC-SeVin', 'AC-CateEx', 'AC-CateFw',
          'BassAm210', 'BassAm410', 'BassAm810', 'BassSR15', 'BassPeyTS', 'BassEbPro', 'BassHake',
          'BassTcBc', 'BassSuns', 'BassMessRR', 'BassCeleV', 'BassSunVin', 'BassEleVoEv',
          'BassOgPPC', 'BassEdn', 'BassMaMM', 'BassAshMag', 'BassGKbx', 'BassRIanMc', 'BassUdio'],
    EQ: ['Guitar EQ 6', 'Bass EQ 7', 'Normal EQ 10'],
    MOD: ['Chorus', 'Tri Chorus', 'Flanger', 'Tri Flanger', 'Tremolo', 'Tri Tremolo', 'Opto Tremolo',
          'Phaser', 'Vibrato', 'Tri Vibrato', 'Opto Vibrato', 'Univibe', 'Tri Univibe', 'Autofilter',
          'Phaser Stereo', 'Flanger Stereo', 'Vibe Stereo', 'Chorus Stereo', 'Tremolo Stereo',
          'Vibrato Stereo'],
    DLY: ['Clean', 'Modern', 'Echo', 'Analog', 'Duck', 'Dtype', 'Tremolo', 'Filter', 'Dual', 'Lofi',
          'Pattern', 'Ice', 'Reverse', 'PingPong Stereo', 'Clean Stereo', 'Modern Stereo',
          'Echo Stereo', 'Analog Stereo', 'Duck Stereo', 'Dtype Stereo', 'Tremolo Stereo',
          'Filter Stereo', 'Dual Stereo', 'Lofi Stereo', 'Pattern Stereo', 'Ice Stereo',
          'Reverse Stereo'],
    REV: ['Room', 'Hall', 'Plate', 'Spring', 'Shimmer', 'Bloom', 'Cloud', 'Lofi', 'Swell',
          'Room stereo', 'Hall stereo', 'Plate stereo', 'Spring stereo', 'Shimmer stereo',
          'Bloom stereo', 'Cloud stereo', 'Lofi stereo', 'Swell stereo'],
    VOL: ['VOL'],
}

_AMP_KNOBS = [(0, 'Gain', 'pct'), (1, 'Level', 'pct'), (2, 'Bass', 'pct'), (3, 'Middle', 'pct'),
              (4, 'Treble', 'pct'), (5, 'Reso', 'pct'), (6, 'Pres', 'pct'), (7, 'Bright', 'pct')]

# knobs por modulo; KNOBS_MODELO sobrepoe para modelos com knobs proprios
KNOBS_MODULO = {
    WAH: [(0, 'Value', 'pct'), (1, 'Gain', 'pct'), (2, 'Level', 'pct')],
    FX: [],
    GATE: [],
    DS: _AMP_KNOBS,
    AMP: _AMP_KNOBS,
    CAB: [(0, 'Level', 'pct'), (1, 'Low Cut', 'hz'), (2, 'High Cut', 'x100hz')],
    EQ: [],
    MOD: [(0, 'Speed', 'x10')],
    DLY: [(0, 'Time', 'ms'), (1, 'Fb', 'pct'), (2, 'Mix', 'pct'), (3, 'Sync', 'sync')],
    REV: [(0, 'Decay', 'pct'), (1, 'Mix', 'pct')],
    VOL: [(0, 'VOL', 'pct')],
}

KNOBS_MODELO = {
    (FX, 0): [(0, 'Speed', 'x10'), (1, 'Q', 'pct'), (2, 'Mix', 'pct'), (3, 'Width', 'pct'),
              (4, 'Level', 'pct')],
    (FX, 8): [(0, 'Sustain', 'pct'), (1, 'Attack', 'pct'), (2, 'Level', 'pct'), (3, 'Blend', 'pct')],
    (GATE, 0): [(0, 'Gate', 'pct'), (1, 'Bias', 'pct')],
    (GATE, 2): [(0, 'Thd', 'db')],
    (EQ, 0): [(0, '100Hz', 'meio_db'), (1, '200Hz', 'meio_db'), (2, '400Hz', 'meio_db'),
              (3, '800Hz', 'meio_db'), (4, '1.6kHz', 'meio_db'), (5, '3.2kHz', 'meio_db')],
    (MOD, 0): [(0, 'Speed', 'x10'), (1, 'Depth', 'pct'), (2, 'Mix', 'pct'), (3, 'Sync', 'sync')],
    (MOD, 7): [(0, 'Speed', 'x10'), (1, 'MidCut', 'pct'), (2, 'Reso', 'pct'), (3, 'Fb', 'pct'),
               (4, 'Sync', 'sync')],
    (REV, 10): [(0, 'Decay', 'pct'), (1, 'Mix', 'pct'), (2, 'High Pass', 'pct'), (3, 'Low Pass', 'pct'),
                (4, 'Mod Depth', 'pct')],
}

# frequencia central de cada banda do "Guitar EQ 6" (modelo 0 do modulo EQ)
BANDAS_EQ_GUITARRA = [100, 200, 400, 800, 1600, 3200]

# divisoes do Speed/Time quando Sync esta ligado (indice no lugar do valor)
DIVISOES_SYNC = ['1/1', '1/2D', '1/1T', '1/2', '1/4D', '1/2T', '1/4', '1/8D', '1/4T', '1/8', '1/16D',
                 '1/8T', '1/16']


def nome_modelo(modulo, indice):
    lista = MODELOS.get(modulo, [])
    if 0 <= indice < len(lista):
        prefixo = '' if modulo not in (DS, AMP, CAB) else f'{indice + 1}'
        return prefixo + lista[indice]
    return f'Modelo {indice + 1}'


def knobs(modulo, modelo):
    return KNOBS_MODELO.get((modulo, modelo), KNOBS_MODULO.get(modulo, []))


def texto_valor(tipo, v):
    if tipo == 'x10':
        return f'{v / 10:.1f}'
    if tipo == 'ms':
        return f'{v / 1000:.3f}s' if v >= 1000 else f'{v} ms'
    if tipo == 'hz':
        return f'{v} Hz'
    if tipo == 'x100hz':
        return f'{v / 10:.1f}K'
    if tipo == 'meio_db':
        return f'{v / 2:+.1f} dB'
    if tipo == 'db':
        return f'{v} dB'
    if tipo == 'sync':
        return 'ligado' if v else 'desligado'
    return str(v)


def categoria_ganho(nome):
    """'limpo', 'overdrive', 'distorcao', 'fuzz', 'boost', 'violao' ou 'baixo' pelo prefixo do slot."""
    n = nome.upper()
    if n.startswith(('BASS', 'BOD', 'BFZ', 'BBT')):
        return 'baixo'
    if n.startswith('AC-'):
        return 'violao'
    if n.startswith('CL'):
        return 'limpo'
    if n.startswith('OD'):
        return 'overdrive'
    if n.startswith('DS'):
        return 'distorcao'
    if n.startswith('FZ'):
        return 'fuzz'
    if n.startswith('BT'):
        return 'boost'
    return 'outro'
