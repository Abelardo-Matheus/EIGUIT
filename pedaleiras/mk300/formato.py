# -*- coding: utf-8 -*-
"""
Formato dos arquivos da MK-300 exportados pelo M-EFCS.

Mapeado comparando arquivos exportados do proprio M-EFCS, mudando um knob/
modulo por vez (os arquivos estao em _validacao/dados_pedaleiras/mk300 e a
suite _validacao/teste_pedaleiras.py confere cada campo).

Preset (.dzh, "Share current preset"): 448 bytes, little-endian
    0x000  nome            20 bytes ASCII, preenchido com 0
    0x014  cor             uint32 (0x00RRGGBB) do LED/tela
    0x018  volume          int16 (Preset Vol, 0..100)
    0x01A  bpm             int16
    0x01C  pan             int16 (0 = C, negativo = L, positivo = R)
    0x01E  pedal           2 bytes (estado do pedal de expressao; preservado)
    0x020  cadeia          11 bytes: ids dos modulos na ordem do sinal
    0x02B  ligado          11 bytes: 0/1 por modulo (indice = id do modulo)
    0x036  modelo          11 bytes: modelo escolhido por modulo
    0x042  knobs           11 modulos x 12 int16 (24 bytes por modulo)
    0x14A  resto           118 bytes (atribuicoes de pedal/expressao etc.):
                           preservados sem mudanca
    ids: 0 WAH, 1 FX, 2 GATE, 3 DS, 4 AMP, 5 CAB, 6 EQ, 7 MOD, 8 DLY, 9 REV, 10 VOL

EQ global (.dzheq, aba EQ > "Share EQ"): 22 bytes
    0x00  Q das 4 bandas   uint8 x4 (Q*10: 7 = 0.7)
    0x04  ganho            int8 x4 (dB)
    0x08  frequencia       uint16 x4 (Hz)
    0x10  LC               uint16 (Hz)
    0x12  HC               uint16 (Hz)
    0x14  ligado           uint8
    0x15  (reservado)
"""
import struct

from pedaleiras.base import ErroFormato

TAM_PRESET = 448
TAM_EQ = 22
N_MODULOS = 11
N_KNOBS = 12
OFF_NOME, TAM_NOME = 0x00, 20
OFF_COR = 0x14
OFF_VOLUME = 0x18
OFF_BPM = 0x1A
OFF_PAN = 0x1C
OFF_CADEIA = 0x20
OFF_LIGADO = 0x2B
OFF_MODELO = 0x36
OFF_KNOBS = 0x42
PASSO_MODULO = 0x18
MAX_NOME = 16                       # o M-EFCS mostra/aceita nomes curtos; os 20 bytes ficam com 0


class PresetMK300:
    """Bytes do preset + acesso por campo. O que nao e entendido fica intacto."""

    def __init__(self, dados, caminho=''):
        if len(dados) != TAM_PRESET:
            raise ErroFormato(f'Preset da MK-300 tem {TAM_PRESET} bytes; este arquivo tem {len(dados)}.')
        self.dados = bytearray(dados)
        self.caminho = caminho
        cadeia = list(self.dados[OFF_CADEIA:OFF_CADEIA + N_MODULOS])
        if sorted(cadeia) != list(range(N_MODULOS)):
            raise ErroFormato('A ordem dos módulos no arquivo não é válida: não parece um preset da MK-300.')

    # ---------------------------------------------------------------- campos
    @property
    def nome(self):
        return bytes(self.dados[OFF_NOME:OFF_NOME + TAM_NOME]).split(b'\0')[0].decode('latin-1').rstrip()

    @nome.setter
    def nome(self, texto):
        b = str(texto).encode('ascii', 'replace')[:MAX_NOME]
        self.dados[OFF_NOME:OFF_NOME + TAM_NOME] = b + b'\0' * (TAM_NOME - len(b))

    def _i16(self, off):
        return struct.unpack_from('<h', self.dados, off)[0]

    def _set_i16(self, off, v):
        struct.pack_into('<h', self.dados, off, int(max(-32768, min(32767, round(v)))))

    @property
    def cor(self):
        return struct.unpack_from('<I', self.dados, OFF_COR)[0]

    volume = property(lambda s: s._i16(OFF_VOLUME), lambda s, v: s._set_i16(OFF_VOLUME, v))
    bpm = property(lambda s: s._i16(OFF_BPM), lambda s, v: s._set_i16(OFF_BPM, v))
    pan = property(lambda s: s._i16(OFF_PAN), lambda s, v: s._set_i16(OFF_PAN, v))

    @property
    def cadeia(self):
        return list(self.dados[OFF_CADEIA:OFF_CADEIA + N_MODULOS])

    def ligado(self, m):
        return bool(self.dados[OFF_LIGADO + m])

    def ligar(self, m, sim=True):
        self.dados[OFF_LIGADO + m] = 1 if sim else 0

    def modelo(self, m):
        return self.dados[OFF_MODELO + m]

    def set_modelo(self, m, indice):
        self.dados[OFF_MODELO + m] = int(indice) & 0xFF

    def knob(self, m, i):
        return self._i16(OFF_KNOBS + m * PASSO_MODULO + 2 * i)

    def set_knob(self, m, i, v):
        self._set_i16(OFF_KNOBS + m * PASSO_MODULO + 2 * i, v)

    def knobs(self, m):
        return [self.knob(m, i) for i in range(N_KNOBS)]

    def copia(self):
        return PresetMK300(bytes(self.dados), self.caminho)

    def para_bytes(self):
        return bytes(self.dados)


class EqGlobalMK300:
    def __init__(self, dados, caminho=''):
        if len(dados) != TAM_EQ:
            raise ErroFormato(f'EQ global da MK-300 tem {TAM_EQ} bytes; este arquivo tem {len(dados)}.')
        self.dados = bytearray(dados)
        self.caminho = caminho

    def q(self, b):
        return self.dados[b] / 10.0

    def set_q(self, b, q):
        self.dados[b] = int(max(1, min(255, round(q * 10))))

    def ganho(self, b):
        return struct.unpack_from('<b', self.dados, 4 + b)[0]

    def set_ganho(self, b, db):
        struct.pack_into('<b', self.dados, 4 + b, int(max(-12, min(12, round(db)))))

    def freq(self, b):
        return struct.unpack_from('<H', self.dados, 8 + 2 * b)[0]

    def set_freq(self, b, hz):
        struct.pack_into('<H', self.dados, 8 + 2 * b, int(max(20, min(20000, round(hz)))))

    lc = property(lambda s: struct.unpack_from('<H', s.dados, 16)[0],
                  lambda s, v: struct.pack_into('<H', s.dados, 16, int(max(20, min(20000, round(v))))))
    hc = property(lambda s: struct.unpack_from('<H', s.dados, 18)[0],
                  lambda s, v: struct.pack_into('<H', s.dados, 18, int(max(20, min(20000, round(v))))))

    @property
    def ligado(self):
        return bool(self.dados[20])

    @ligado.setter
    def ligado(self, sim):
        self.dados[20] = 1 if sim else 0

    def copia(self):
        return EqGlobalMK300(bytes(self.dados), self.caminho)

    def para_bytes(self):
        return bytes(self.dados)


def ler_preset(caminho):
    with open(caminho, 'rb') as f:
        dados = f.read()
    # o arquivo de fabrica (160 presets + 'PATCHEND') tambem e aceito: pega o 1o
    if len(dados) == TAM_PRESET * 160 + 8 and dados.endswith(b'PATCHEND'):
        raise ErroFormato('Este arquivo tem todos os 160 presets ("Share all presets"). '
                          'Exporte só o preset atual ("Share current preset").')
    return PresetMK300(dados, caminho)


def ler_eq(caminho):
    with open(caminho, 'rb') as f:
        return EqGlobalMK300(f.read(), caminho)


def gravar(obj, caminho):
    with open(caminho, 'wb') as f:
        f.write(obj.para_bytes())
