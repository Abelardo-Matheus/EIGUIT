# -*- coding: utf-8 -*-
"""
Driver da M-VAVE MK-300: le/grava .dzh (preset) e .dzheq (EQ global) do
M-EFCS e traduz as sugestoes do Analisador IA em mudancas nesses arquivos.

Fluxo na pratica:
    M-EFCS > More > Share current preset  ->  arquivo .dzh
    EIGUIT (Analisador > Exportar p/ pedaleira) abre, mostra, ajusta e salva
    M-EFCS > More > Import current preset  <-  arquivo ajustado
    (opcional) exporte de novo e use "Conferir importação" para comparar
"""
from pedaleiras.base import DriverPedaleira, ErroFormato
from pedaleiras.mk300 import formato as fmt
from pedaleiras.mk300 import modelos as mdl
from pedaleiras.mk300.modelos import AMP, CAB, DLY, DS, EQ, FX, GATE, MOD, REV, VOL, WAH

# efeito do Analisador -> modelo do modulo MOD
MOD_POR_EFEITO = {'chorus': 0, 'flanger': 2, 'tremolo': 4, 'phaser': 7, 'vibrato': 8}
FAMILIA_MOD = {'chorus': ('chorus',), 'flanger': ('flanger',), 'tremolo': ('tremolo',),
               'phaser': ('phaser',), 'vibrato': ('vibrato', 'vibe')}
# efeito -> modelo do modulo FX
FX_POR_EFEITO = {'compressor': 8, 'octaver': 12, 'ring': 13, 'whammy': 15}
FX_COMPRESSORES = (8, 9, 10)
# drive desejado -> slot de DS padrao (se o DS atual nao for da mesma familia)
DS_PADRAO = {'overdrive': 'OD-TSTenn', 'distorcao': 'DS-ONEE', 'fuzz': 'FZ-BigMff', 'boost': 'BT-Mvave'}


def _pct(x):
    return int(round(max(0.0, min(1.0, float(x))) * 100))


class DriverMK300(DriverPedaleira):
    id = 'mk300'
    nome = 'MK-300'
    fabricante = 'M-VAVE'
    implementado = True
    software = 'M-EFCS'
    ext_preset = '.dzh'
    ext_eq_global = '.dzheq'
    observacao = ('No M-EFCS: More > "Share current preset" exporta o .dzh e "Import current preset" '
                  'importa (grava no slot atual). EQ global: aba EQ > Share EQ / Import EQ.')

    # ================================================================ arquivos
    def ler_preset(self, caminho):
        return fmt.ler_preset(caminho)

    def salvar_preset(self, preset, caminho):
        fmt.gravar(preset, caminho)

    def ler_eq_global(self, caminho):
        return fmt.ler_eq(caminho)

    def salvar_eq_global(self, eq, caminho):
        fmt.gravar(eq, caminho)

    # ================================================================ leitura
    def _params(self, p, m):
        modelo = p.modelo(m)
        conhecidos = mdl.knobs(m, modelo)
        valores = p.knobs(m)
        saida, usados = [], set()
        sync = any(t == 'sync' and valores[i] for i, _n, t in conhecidos)
        for i, nome, tipo in conhecidos:
            v = valores[i]
            texto = mdl.texto_valor(tipo, v)
            if sync and i == 0 and tipo in ('x10', 'ms') and 0 <= v < len(mdl.DIVISOES_SYNC):
                texto = mdl.DIVISOES_SYNC[v]
            saida.append({'indice': i, 'nome': nome, 'valor': v, 'texto': texto})
            usados.add(i)
        for i, v in enumerate(valores):           # knobs ainda sem nome: so os que tem valor
            if i not in usados and v:
                saida.append({'indice': i, 'nome': f'P{i + 1}', 'valor': v, 'texto': str(v)})
        return saida

    def descrever_preset(self, p):
        modulos = []
        for m in p.cadeia:
            modulos.append({'id': m, 'nome': mdl.MODULOS[m], 'ligado': p.ligado(m), 'modelo': p.modelo(m),
                            'modelo_nome': mdl.nome_modelo(m, p.modelo(m)), 'params': self._params(p, m)})
        return modulos

    def cabecalho(self, p):
        pan = p.pan
        return {'Nome': p.nome, 'Preset Vol': str(p.volume), 'BPM': str(p.bpm),
                'Pan': 'C' if pan == 0 else (f'L{-pan}' if pan < 0 else f'R{pan}'),
                'Cadeia': ' > '.join(mdl.MODULOS[m] for m in p.cadeia)}

    def descrever_eq_global(self, eq):
        linhas = [{'indice': 'on', 'nome': 'EQ', 'valor': int(eq.ligado), 'texto': 'ligado' if eq.ligado else 'desligado'},
                  {'indice': 'lc', 'nome': 'LC', 'valor': eq.lc, 'texto': f'{eq.lc} Hz'},
                  {'indice': 'hc', 'nome': 'HC', 'valor': eq.hc, 'texto': f'{eq.hc / 1000:.1f}K'}]
        for b in range(4):
            f = eq.freq(b)
            linhas.append({'indice': b, 'nome': f'P{b + 1}', 'valor': eq.ganho(b),
                           'texto': f"{f if f < 1000 else f'{f / 1000:.1f}k'} Hz · Q {eq.q(b):.1f} · {eq.ganho(b):+d} dB"})
        return linhas

    # ================================================================ comparar
    def comparar(self, a, b):
        """Diferencas legiveis entre dois presets (a = gerado pelo EIGUIT, b = exportado de novo)."""
        difs = []

        def dif(rotulo, va, vb):
            if va != vb:
                difs.append({'campo': rotulo, 'esperado': va, 'encontrado': vb})
        ca, cb = self.cabecalho(a), self.cabecalho(b)
        for k in ca:
            dif(k, ca[k], cb[k])
        for m in range(fmt.N_MODULOS):
            nome = mdl.MODULOS[m]
            dif(f'{nome}: ligado', 'sim' if a.ligado(m) else 'não', 'sim' if b.ligado(m) else 'não')
            dif(f'{nome}: modelo', mdl.nome_modelo(m, a.modelo(m)), mdl.nome_modelo(m, b.modelo(m)))
            nomes = {i: n for i, n, _t in mdl.knobs(m, a.modelo(m))}
            for i in range(fmt.N_KNOBS):
                dif(f'{nome}: {nomes.get(i, f"P{i + 1}")}', a.knob(m, i), b.knob(m, i))
        resto = sum(1 for i in range(0x14A, fmt.TAM_PRESET) if a.dados[i] != b.dados[i])
        if resto:
            difs.append({'campo': 'Atribuições (pedal/expressão)', 'esperado': '-',
                         'encontrado': f'{resto} byte(s) diferentes'})
        return difs

    def comparar_eq(self, a, b):
        la, lb = self.descrever_eq_global(a), self.descrever_eq_global(b)
        return [{'campo': x['nome'], 'esperado': x['texto'], 'encontrado': y['texto']}
                for x, y in zip(la, lb) if x['texto'] != y['texto']]

    # ================================================================ planejar
    def planejar(self, preset, sugestoes, eq_global=None, opcoes=None):
        """
            Como funciona: aplica as sugestoes numa copia, uma operacao por
            vez, guardando o antes/depois de cada campo tocado. Cada operacao
            vira uma 'mudanca' que a tela mostra (e deixa desmarcar).
            opcoes: {'destino_eq': 'preset'|'global', 'confianca_min': 0.35}
        """
        opcoes = dict(opcoes or {})
        destino_eq = opcoes.get('destino_eq', 'preset')
        conf_min = float(opcoes.get('confianca_min', 0.35))
        plano = _Plano(preset.copia(), eq_global.copia() if eq_global is not None else None)
        notas = []
        ordem = sorted(sugestoes, key=lambda s: -(s.get('impacto', 0) * s.get('confianca', 0)))
        for s in ordem:
            pid = s.get('pedal')
            if not pid:
                continue
            plano.origem = s.get('titulo', pid)
            plano.marcado = (s.get('confianca', 0) >= conf_min) and not s.get('possivel')
            antes = len(plano.mudancas)
            try:
                if pid == 'eq':
                    self._eq(plano, s, destino_eq, notas)
                elif pid in ('overdrive', 'distorcao', 'boost', 'fuzz'):
                    self._ganho(plano, s)
                elif pid == 'delay':
                    self._delay(plano, s)
                elif pid == 'reverb':
                    self._reverb(plano, s)
                elif pid in MOD_POR_EFEITO:
                    self._mod(plano, s, pid)
                elif pid in ('wah', 'autowah'):
                    self._wah(plano, s)
                elif pid == 'compressor':
                    self._compressor(plano, s)
                elif pid == 'gate':
                    self._gate(plano, s)
                elif pid in ('octaver', 'whammy', 'ring'):
                    self._fx_especial(plano, s, pid)
                else:
                    notas.append(f'"{s.get("titulo")}": sem equivalente direto na MK-300 (ajuste à mão).')
            except Exception as erro:              # uma sugestao estranha nao derruba o resto
                notas.append(f'"{s.get("titulo")}": não aplicada ({erro}).')
            if len(plano.mudancas) == antes and pid in ('delay', 'reverb', 'gate', 'compressor', 'wah'):
                notas.append(f'"{s.get("titulo")}": o preset já está assim; nada a mudar.')
        return {'mudancas': plano.mudancas, 'notas': notas + plano._extra}

    # ---- cada tipo de sugestao
    def _ganho(self, pl, s):
        titulo = s.get('titulo', '').lower()
        p = pl.p
        imp = float(s.get('impacto', 0.5))
        if s['tipo'] == 'falta':
            if not p.ligado(DS):
                desejado = s['pedal']
                atual = mdl.categoria_ganho(mdl.MODELOS[DS][p.modelo(DS)] if p.modelo(DS) < len(mdl.MODELOS[DS]) else '')
                if atual != desejado and desejado in DS_PADRAO:
                    pl.modelo(DS, mdl.MODELOS[DS].index(DS_PADRAO[desejado]), 'drive do tipo certo')
                pl.ligar(DS, True, 'liga o drive')
                if p.knob(DS, 0) < 55:
                    pl.knob(DS, 0, 60, 'ganho de partida')
            else:
                pl.knob(AMP, 0, p.knob(AMP, 0) + 15, 'mais saturação no amp')
            return
        if s['tipo'] == 'sobra':
            if p.ligado(DS):
                pl.ligar(DS, False, 'desliga o drive')
            else:
                pl.knob(AMP, 0, p.knob(AMP, 0) - 20, 'amp mais limpo')
            return
        passo = int(round(8 + 20 * imp))
        sinal = -1 if 'menos' in titulo else 1
        alvo = DS if p.ligado(DS) else AMP
        pl.knob(alvo, 0, p.knob(alvo, 0) + sinal * passo, 'ganho')

    def _eq(self, pl, s, destino, notas):
        v = s.get('valores') or {}
        bandas = [(k, float(v[k])) for k in ('graves', 'medios', 'agudos') if k in v]
        if not bandas:
            return
        fm = float(v.get('freq_medios', 800))
        if destino == 'global':
            if pl.eq is None:
                notas.append('EQ: abra também o arquivo de EQ global (.dzheq) ou mande o ajuste para o EQ do preset.')
                return
            alvo = {'graves': 120.0, 'medios': fm, 'agudos': 4000.0}
            if not pl.eq.ligado:
                pl.eq_ligar(True)
            for nome, d in bandas:
                b = min(range(4), key=lambda i: abs(_oit(pl.eq.freq(i), alvo[nome])))
                pl.eq_ganho(b, pl.eq.ganho(b) + d, f'{nome} {d:+.0f} dB')
            return
        p = pl.p
        if p.modelo(EQ) != 0:
            notas.append(f'EQ do preset é "{mdl.nome_modelo(EQ, p.modelo(EQ))}" (bandas não mapeadas): '
                         'use o destino "EQ global" ou troque o EQ do preset para "Guitar EQ 6".')
            return
        if not p.ligado(EQ):
            for i in range(6):
                if p.knob(EQ, i):
                    pl.knob(EQ, i, 0, 'zera o EQ antes de ligar')
            pl.ligar(EQ, True, 'liga o EQ do preset')
        for nome, d in bandas:
            if nome == 'graves':
                alvos = [(0, 1.0), (1, 0.5)]
            elif nome == 'agudos':
                alvos = [(5, 1.0), (4, 0.5)]
            else:
                i = min(range(2, 5), key=lambda j: abs(_oit(mdl.BANDAS_EQ_GUITARRA[j], fm)))
                alvos = [(i, 1.0)]
            for i, peso in alvos:
                pl.knob(EQ, i, max(-24, min(24, p.knob(EQ, i) + round(d * peso * 2))), f'{nome} {d * peso:+.1f} dB')

    def _delay(self, pl, s):
        p, v = pl.p, s.get('valores') or {}
        if s['tipo'] == 'sobra':
            if p.ligado(DLY):
                pl.ligar(DLY, False, 'tira o delay')
            return
        pl.ligar(DLY, True, 'liga o delay')
        if 'time' in v:
            if p.knob(DLY, 3):
                pl.knob(DLY, 3, 0, 'tempo em ms (sem sync)')
            pl.knob(DLY, 0, int(max(20, min(2000, v['time']))), 'tempo das repetições')
        if 'feedback' in v:
            pl.knob(DLY, 1, _pct(v['feedback']), 'número de repetições')
        if 'mix' in v:
            pl.knob(DLY, 2, _pct(v['mix']), 'volume das repetições')

    def _reverb(self, pl, s):
        p, v = pl.p, s.get('valores') or {}
        if s['tipo'] == 'sobra':
            if p.ligado(REV):
                pl.ligar(REV, False, 'tira o reverb')
            return
        pl.ligar(REV, True, 'liga o reverb')
        if 'decay' in v:
            pl.knob(REV, 0, int(round(max(5, min(100, (float(v['decay']) - 0.3) / 7.7 * 100)))), 'tamanho da cauda')
        if 'mix' in v:
            pl.knob(REV, 1, _pct(v['mix']), 'quantidade de reverb')

    def _mod(self, pl, s, ef):
        p, v = pl.p, s.get('valores') or {}
        nome_atual = mdl.nome_modelo(MOD, p.modelo(MOD)).lower()
        mesma = any(f in nome_atual for f in FAMILIA_MOD[ef])
        if s['tipo'] == 'sobra':
            if p.ligado(MOD) and mesma:
                pl.ligar(MOD, False, f'tira o {ef}')
            return
        if not mesma:
            pl.modelo(MOD, MOD_POR_EFEITO[ef], f'troca para {mdl.MODELOS[MOD][MOD_POR_EFEITO[ef]]}')
        pl.ligar(MOD, True, f'liga o {ef}')
        conhecidos = {n: (i, t) for i, n, t in mdl.knobs(MOD, p.modelo(MOD))}
        if 'Sync' in conhecidos and p.knob(MOD, conhecidos['Sync'][0]):
            pl.knob(MOD, conhecidos['Sync'][0], 0, 'velocidade livre')
        if 'rate' in v:
            pl.knob(MOD, 0, int(round(max(1, min(100, float(v['rate']) * 10)))), 'velocidade')
        if 'depth' in v and 'Depth' in conhecidos:
            pl.knob(MOD, conhecidos['Depth'][0], _pct(v['depth']), 'profundidade')
        if 'mix' in v and 'Mix' in conhecidos:
            pl.knob(MOD, conhecidos['Mix'][0], _pct(v['mix']), 'mix')

    def _wah(self, pl, s):
        p = pl.p
        if s['tipo'] == 'sobra':
            if p.ligado(WAH):
                pl.ligar(WAH, False, 'tira o wah')
            if p.ligado(FX) and p.modelo(FX) in (0, 2):
                pl.ligar(FX, False, 'tira o wah do FX')
            return
        pl.ligar(WAH, True, 'liga o wah')

    def _compressor(self, pl, s):
        p, v = pl.p, s.get('valores') or {}
        comp_no_fx = p.modelo(FX) in FX_COMPRESSORES
        if s['tipo'] == 'sobra' or (v.get('sustain', 1) <= 0.25 and s['tipo'] == 'ajuste'):
            if p.ligado(FX) and comp_no_fx:
                if p.modelo(FX) == 8 and p.knob(FX, 0) > 30:
                    pl.knob(FX, 0, max(10, p.knob(FX, 0) - 25), 'menos compressão')
                else:
                    pl.ligar(FX, False, 'tira o compressor')
            return
        if p.ligado(FX) and not comp_no_fx:
            pl.notas_extra(f'FX já está em uso ({mdl.nome_modelo(FX, p.modelo(FX))}); compressor não colocado.')
            return
        if p.modelo(FX) != 8 and not comp_no_fx:
            pl.modelo(FX, 8, 'compressor no FX')
        pl.ligar(FX, True, 'liga o compressor')
        if p.modelo(FX) == 8:
            pl.knob(FX, 0, _pct(v.get('sustain', 0.6)), 'sustain')

    def _gate(self, pl, s):
        p = pl.p
        if s['tipo'] == 'sobra':
            if p.ligado(GATE) and p.modelo(GATE) == 2:
                pl.knob(GATE, 0, max(-90, p.knob(GATE, 0) - 10), 'gate fecha mais tarde')
            elif p.ligado(GATE):
                pl.ligar(GATE, False, 'tira o gate')
            return
        if not p.ligado(GATE):
            pl.ligar(GATE, True, 'liga o noise gate')

    def _fx_especial(self, pl, s, ef):
        p = pl.p
        modelo = FX_POR_EFEITO[ef]
        if s['tipo'] == 'sobra':
            if p.ligado(FX) and p.modelo(FX) == modelo:
                pl.ligar(FX, False, f'tira o {mdl.MODELOS[FX][modelo]}')
            return
        if p.ligado(FX) and p.modelo(FX) != modelo:
            pl.notas_extra(f'FX já está em uso ({mdl.nome_modelo(FX, p.modelo(FX))}); {ef} não colocado.')
            return
        if p.modelo(FX) != modelo:
            pl.modelo(FX, modelo, f'{mdl.MODELOS[FX][modelo]} no FX')
        pl.ligar(FX, True, f'liga o {mdl.MODELOS[FX][modelo]}')

    # ================================================================ aplicar
    def aplicar(self, preset, mudancas, eq_global=None):
        p = preset.copia()
        eq = eq_global.copia() if eq_global is not None else None
        for mu in mudancas:
            if not mu.get('aplicar', True):
                continue
            op = mu['op']
            if op[0] == 'ligar':
                p.ligar(op[1], op[2])
            elif op[0] == 'modelo':
                p.set_modelo(op[1], op[2])
            elif op[0] == 'knob':
                p.set_knob(op[1], op[2], op[3])
            elif op[0] == 'eq_ligar' and eq is not None:
                eq.ligado = op[1]
            elif op[0] == 'eq_ganho' and eq is not None:
                eq.set_ganho(op[1], op[2])
        return p, eq


def _oit(a, b):
    import math
    return math.log2(max(a, 1) / max(b, 1))


class _Plano:
    """Copia de trabalho + lista de mudancas com antes/depois legiveis."""

    def __init__(self, p, eq):
        self.p, self.eq = p, eq
        self.mudancas = []
        self.origem = ''
        self.marcado = True
        self._extra = []

    def _add(self, op, modulo, campo, antes, depois, ta, td, motivo):
        if antes == depois:
            return
        self.mudancas.append({'chave': f'{len(self.mudancas)}', 'op': op, 'modulo': modulo, 'campo': campo,
                              'antes': antes, 'depois': depois, 'texto_antes': ta, 'texto_depois': td,
                              'motivo': motivo, 'origem': self.origem, 'aplicar': self.marcado})

    def ligar(self, m, sim, motivo):
        a = self.p.ligado(m)
        self.p.ligar(m, sim)
        self._add(('ligar', m, sim), mdl.MODULOS[m], 'ligado', a, sim, 'ligado' if a else 'desligado',
                  'ligado' if sim else 'desligado', motivo)

    def modelo(self, m, indice, motivo):
        a = self.p.modelo(m)
        self.p.set_modelo(m, indice)
        self._add(('modelo', m, indice), mdl.MODULOS[m], 'modelo', a, indice, mdl.nome_modelo(m, a),
                  mdl.nome_modelo(m, indice), motivo)

    def knob(self, m, i, valor, motivo):
        nomes = {k: (n, t) for k, n, t in mdl.knobs(m, self.p.modelo(m))}
        nome, tipo = nomes.get(i, (f'P{i + 1}', 'pct'))
        if tipo == 'pct':
            valor = max(0, min(100, int(round(valor))))
        a = self.p.knob(m, i)
        self.p.set_knob(m, i, valor)
        valor = self.p.knob(m, i)
        self._add(('knob', m, i, valor), mdl.MODULOS[m], nome, a, valor, mdl.texto_valor(tipo, a),
                  mdl.texto_valor(tipo, valor), motivo)

    def eq_ligar(self, sim):
        a = self.eq.ligado
        self.eq.ligado = sim
        self._add(('eq_ligar', sim), 'EQ global', 'ligado', a, sim, 'ligado' if a else 'desligado',
                  'ligado' if sim else 'desligado', 'liga o EQ global')

    def eq_ganho(self, b, db, motivo):
        a = self.eq.ganho(b)
        self.eq.set_ganho(b, db)
        d = self.eq.ganho(b)
        f = self.eq.freq(b)
        self._add(('eq_ganho', b, d), 'EQ global', f'P{b + 1} ({f} Hz)', a, d, f'{a:+d} dB', f'{d:+d} dB', motivo)

    def notas_extra(self, texto):
        self._extra.append(texto)
