# -*- coding: utf-8 -*-
"""
ANALISE DE IA > Analisador > aba "Pedaleira"

Leva o resultado do Analisador para o arquivo de preset da pedaleira:
    1. escolha a pedaleira (por enquanto so a MK-300 esta implementada);
    2. abra o preset exportado pelo software dela (MK-300: M-EFCS > More >
       "Share current preset" -> .dzh) e, se quiser, o EQ global (.dzheq);
    3. veja as mudancas sugeridas (cada uma pode ser desmarcada), os pedais e
       todos os parametros antes -> depois;
    4. salve o preset ajustado e importe no software da pedaleira;
    5. "Conferir importação": exporte de novo do software e abra aqui para
       comparar campo a campo com o que o EIGUIT gerou.

A parte de arquivo fica em pedaleiras/ (um driver por pedaleira); esta tela
so desenha e chama o driver. Usa os helpers do AnalisadorIA (botoes, alvos,
rolagem), por isso recebe a instancia dele.
"""
import os

import pygame

from config.design_system import TEMA, ds
from core.i18n import _t
from pedaleiras import registro
from pedaleiras.base import ErroFormato


def _janela_arquivo(salvar, titulo, extensao, descricao, inicial='', pasta=''):
    try:
        import tkinter as tk
        from tkinter import filedialog
        janela = tk.Tk()
        janela.withdraw()
        janela.attributes('-topmost', True)
        tipos = [(descricao, '*' + extensao), ('Todos', '*.*')]
        if salvar:
            caminho = filedialog.asksaveasfilename(title=titulo, filetypes=tipos, defaultextension=extensao,
                                                   initialfile=inicial, initialdir=pasta or None)
        else:
            caminho = filedialog.askopenfilename(title=titulo, filetypes=tipos, initialdir=pasta or None)
        janela.destroy()
        return caminho or ''
    except Exception:
        return ''


class PainelPedaleira:
    def __init__(self, analisador):
        self.an = analisador
        self.driver = registro.padrao()
        self.preset = None
        self.eq = None
        self.plano = None
        self._plano_de = None
        self.destino_eq = 'preset'
        self.salvo = None              # (preset, eq) do ultimo "Salvar", para conferir
        self.conferencia = None        # {'arquivo', 'difs', 'tipo'}
        self.pasta = ''

    # ================================================================ dados
    def _sugestoes(self):
        a = self.an.analise
        return a['resultado']['sugestoes'] if a else []

    def _replanejar(self, forcar=False):
        if self.preset is None:
            self.plano = None
            return
        chave = (id(self.an.analise), id(self.preset), id(self.eq), self.destino_eq)
        if not forcar and chave == self._plano_de:
            return
        self._plano_de = chave
        self.plano = self.driver.planejar(self.preset, self._sugestoes(), self.eq,
                                          {'destino_eq': self.destino_eq})

    def ajustados(self):
        if self.preset is None:
            return None, self.eq
        if not self.plano:
            return self.preset, self.eq
        return self.driver.aplicar(self.preset, self.plano['mudancas'], self.eq)

    def abrir_preset(self):
        d = self.driver
        caminho = _janela_arquivo(False, f'Preset da {d.nome} ({d.ext_preset})', d.ext_preset,
                                  f'Preset {d.nome}', pasta=self.pasta)
        if not caminho:
            return
        try:
            self.preset = d.ler_preset(caminho)
        except (ErroFormato, OSError) as erro:
            self.an.avisar(str(erro), 'erro', 10)
            return
        self.pasta = os.path.dirname(caminho)
        self.conferencia = None
        self._replanejar(True)
        self.an.avisar(f'Preset "{self.preset.nome}" aberto.', 'ok')

    def abrir_eq(self):
        d = self.driver
        caminho = _janela_arquivo(False, f'EQ global da {d.nome} ({d.ext_eq_global})', d.ext_eq_global,
                                  'EQ global', pasta=self.pasta)
        if not caminho:
            return
        try:
            self.eq = d.ler_eq_global(caminho)
        except (ErroFormato, OSError) as erro:
            self.an.avisar(str(erro), 'erro', 10)
            return
        self.pasta = os.path.dirname(caminho)
        self._replanejar(True)
        self.an.avisar('EQ global aberto.', 'ok')

    def salvar(self, qual):
        d = self.driver
        p, eq = self.ajustados()
        obj, ext = (p, d.ext_preset) if qual == 'preset' else (eq, d.ext_eq_global)
        if obj is None:
            return
        base = os.path.splitext(os.path.basename(getattr(obj, 'caminho', '') or 'preset'))[0]
        caminho = _janela_arquivo(True, 'Salvar arquivo ajustado', ext, d.nome, inicial=f'{base}_EIGUIT{ext}',
                                  pasta=self.pasta)
        if not caminho:
            return
        try:
            (d.salvar_preset if qual == 'preset' else d.salvar_eq_global)(obj, caminho)
        except OSError as erro:
            self.an.avisar(f'Não consegui salvar: {erro}', 'erro', 10)
            return
        anterior = self.salvo or (None, None)
        self.salvo = (obj, anterior[1]) if qual == 'preset' else (anterior[0], obj)
        self.an.avisar(f'Salvo em {caminho}. Importe no {d.software} e depois use "Conferir importação".',
                       'ok', 14)

    def conferir(self, qual):
        d = self.driver
        p, eq = self.ajustados()
        esperado = (self.salvo or (None, None))[0 if qual == 'preset' else 1] or (p if qual == 'preset' else eq)
        if esperado is None:
            self.an.avisar('Abra (e ajuste) um arquivo primeiro.', 'aviso')
            return
        ext = d.ext_preset if qual == 'preset' else d.ext_eq_global
        caminho = _janela_arquivo(False, f'Arquivo exportado de novo pelo {d.software}', ext, d.nome,
                                  pasta=self.pasta)
        if not caminho:
            return
        try:
            if qual == 'preset':
                difs = d.comparar(esperado, d.ler_preset(caminho))
            else:
                difs = d.comparar_eq(esperado, d.ler_eq_global(caminho))
        except (ErroFormato, OSError) as erro:
            self.an.avisar(str(erro), 'erro', 10)
            return
        self.conferencia = {'arquivo': os.path.basename(caminho), 'difs': difs, 'tipo': qual}

    # ================================================================ acoes
    def acao(self, dado):
        tipo, valor = dado
        if tipo == 'driver':
            novo = registro.obter(valor)
            if novo is None or not novo.implementado:
                self.an.avisar(f'{novo.fabricante} {novo.nome}: integração ainda não implementada. '
                               'Por enquanto só a MK-300.', 'aviso', 8)
                return
            if novo is not self.driver:
                self.driver, self.preset, self.eq, self.plano, self.conferencia = novo, None, None, None, None
        elif tipo == 'abrir':
            self.abrir_preset()
        elif tipo == 'abrir_eq':
            self.abrir_eq()
        elif tipo == 'destino':
            self.destino_eq = valor
            self._replanejar(True)
        elif tipo == 'marcar' and self.plano:
            for m in self.plano['mudancas']:
                if m['chave'] == valor:
                    m['aplicar'] = not m['aplicar']
        elif tipo == 'marcar_todas' and self.plano:
            for m in self.plano['mudancas']:
                m['aplicar'] = valor
        elif tipo == 'salvar':
            self.salvar(valor)
        elif tipo == 'conferir':
            self.conferir(valor)
        elif tipo == 'fechar_conf':
            self.conferencia = None

    # ================================================================ desenho
    def desenhar(self, tela, r):
        an = self.an
        self._replanejar()
        f11, f10, f12 = an._fonte(11, False), an._fonte(10, False), an._fonte(12)
        maximo_ant = an.scroll.get('pedaleira', 0)
        clip = tela.get_clip()
        tela.set_clip(r.clip(clip) if clip else r)
        self._area = r
        y = r.y - maximo_ant
        x, w = r.x, r.width - 14

        # --- pedaleira
        ds.texto_em(tela, _t('Pedaleira'), an._fonte(11), (x, y + 6), TEMA.texto_suave)
        cx = x + 80
        for d in registro.listar():
            rot = f'{d.fabricante} {d.nome}' + ('' if d.implementado else f" ({_t('em breve')})")
            larg = f10.size(rot)[0] + 22
            if cx + larg > x + w:
                cx, y = x + 80, y + 30
            rr = pygame.Rect(cx, y, larg, 26)
            ds.chip(tela, rr, rot, an._fonte(10), ativo=d is self.driver,
                    cor=None if d.implementado else TEMA.texto_apagado)
            self._alvo(rr, ('driver', d.id))
            cx += larg + 6
        y += 36
        d = self.driver
        y = self._paragrafo(tela, _t(d.observacao), f10, x, y, w, TEMA.texto_apagado) + 6

        # --- arquivos
        b = pygame.Rect(x, y, 200, 30)
        self._botao(tela, b, f'Abrir preset ({d.ext_preset})', ('abrir', None), 'primario' if not self.preset else 'secundario')
        if d.ext_eq_global:
            self._botao(tela, b.move(208, 0), f'Abrir EQ global ({d.ext_eq_global})', ('abrir_eq', None))
            ds.texto_em(tela, _t('EQ sugerido vai para:'), f10, (b.x + 424, b.y + 8), TEMA.texto_suave)
            cx = b.x + 424 + f10.size(_t('EQ sugerido vai para:'))[0] + 8
            for valor, rot in (('preset', 'EQ do preset'), ('global', 'EQ global')):
                larg = f10.size(_t(rot))[0] + 20
                rr = pygame.Rect(cx, b.y + 2, larg, 26)
                ds.chip(tela, rr, _t(rot), an._fonte(10), ativo=self.destino_eq == valor)
                self._alvo(rr, ('destino', valor))
                cx += larg + 6
        y += 40
        if self.preset is None:
            ds.cartao_vazio(tela, pygame.Rect(x, y, w, 70),
                            _t(f'Exporte o preset no {d.software} e abra aqui para ver e ajustar.'), an._fonte(12))
            y += 80
            self._fim(tela, r, y, maximo_ant, clip)
            return

        p_novo, eq_novo = self.ajustados()
        cab = d.cabecalho(p_novo)
        linha = '   ·   '.join(f'{_t(k)}: {v}' for k, v in cab.items() if k != 'Cadeia')
        ds.texto_em(tela, f'{os.path.basename(self.preset.caminho)}   ·   {linha}', f12, (x, y), TEMA.texto,
                    largura_max=w)
        y += 20
        ds.texto_em(tela, f"{_t('Cadeia')}: {cab['Cadeia']}", f10, (x, y), TEMA.texto_apagado, largura_max=w)
        y += 22

        # --- mudancas
        y = self._mudancas(tela, x, y, w)

        # --- salvar / conferir
        meia = (w - 12) // 4
        self._botao(tela, pygame.Rect(x, y, meia, 30), 'Salvar preset ajustado', ('salvar', 'preset'), 'primario')
        self._botao(tela, pygame.Rect(x + meia + 4, y, meia, 30), 'Conferir importação', ('conferir', 'preset'))
        if self.eq is not None:
            self._botao(tela, pygame.Rect(x + 2 * (meia + 4), y, meia, 30), 'Salvar EQ global', ('salvar', 'eq'))
            self._botao(tela, pygame.Rect(x + 3 * (meia + 4), y, meia, 30), 'Conferir EQ global', ('conferir', 'eq'))
        y += 38
        if self.conferencia:
            y = self._conferencia(tela, x, y, w)

        # --- pedais e parametros
        ds.rotulo_secao(tela, x, y, _t('Pedais e parâmetros (como vai ficar)'), an._fonte(11))
        y += 22
        antes = {m['id']: m for m in d.descrever_preset(self.preset)}
        cols = 3 if w > 900 else 2
        larg = (w - (cols - 1) * 8) // cols
        alturas = []
        modulos = d.descrever_preset(p_novo)
        for i, mod in enumerate(modulos):
            col = i % cols
            if col == 0 and i:
                y += max(alturas) + 8
                alturas = []
            alturas.append(self._cartao_modulo(tela, x + col * (larg + 8), y, larg, mod, antes[mod['id']]))
        y += (max(alturas) if alturas else 0) + 12

        if eq_novo is not None:
            ds.rotulo_secao(tela, x, y, _t('EQ global'), an._fonte(11))
            y += 22
            antes_eq = {l['nome']: l['texto'] for l in d.descrever_eq_global(self.eq)}
            for l in d.descrever_eq_global(eq_novo):
                mudou = antes_eq.get(l['nome']) != l['texto']
                txt = f"{l['nome']}: " + (f"{antes_eq.get(l['nome'])}  →  {l['texto']}" if mudou else l['texto'])
                ds.texto_em(tela, txt, an._fonte(11, mudou), (x + 8, y), TEMA.aviso if mudou else TEMA.texto_suave,
                            largura_max=w - 8)
                y += 18
            y += 8
        self._fim(tela, r, y, maximo_ant, clip)

    def _mudancas(self, tela, x, y, w):
        an = self.an
        mud = self.plano['mudancas'] if self.plano else []
        if an.analise is None:
            ds.texto_em(tela, _t('Sem análise ainda: só dá para ver o preset e conferir arquivos.'), an._fonte(11, False),
                        (x, y), TEMA.texto_apagado)
            return y + 26
        marcadas = sum(1 for m in mud if m['aplicar'])
        ds.rotulo_secao(tela, x, y, f"{_t('Mudanças a partir da análise')} ({marcadas}/{len(mud)})", an._fonte(11))
        if mud:
            self._botao(tela, pygame.Rect(x + w - 200, y - 4, 96, 24), 'Marcar todas', ('marcar_todas', True), tamanho=10)
            self._botao(tela, pygame.Rect(x + w - 100, y - 4, 96, 24), 'Desmarcar', ('marcar_todas', False), tamanho=10)
        y += 24
        if not mud:
            ds.texto_em(tela, _t('Nenhuma mudança: as sugestões não têm equivalente direto ou o preset já está assim.'),
                        an._fonte(11, False), (x, y), TEMA.texto_apagado, largura_max=w)
            y += 22
        origem_ant = None
        for m in mud:
            if m['origem'] != origem_ant:
                ds.texto_em(tela, m['origem'], an._fonte(10), (x, y + 2), TEMA.acento, largura_max=w)
                y += 18
                origem_ant = m['origem']
            caixa = pygame.Rect(x + 4, y + 2, 16, 16)
            ds.caixa_selecao(tela, caixa, m['aplicar'])
            linha = pygame.Rect(x, y, w, 20)
            self._alvo(linha, ('marcar', m['chave']))
            txt = f"{m['modulo']} · {m['campo']}: {m['texto_antes']}  →  {m['texto_depois']}"
            cor = TEMA.texto if m['aplicar'] else TEMA.texto_apagado
            ds.texto_em(tela, txt, an._fonte(11), (x + 28, y + 2), cor, largura_max=w * 0.62)
            ds.texto_em(tela, m['motivo'], an._fonte(10, False), (x + w, y + 4), TEMA.texto_apagado, ancora='topright',
                        largura_max=w * 0.35)
            y += 22
        for nota in (self.plano or {}).get('notas', []):
            y = self._paragrafo(tela, '• ' + nota, an._fonte(10, False), x, y, w, TEMA.aviso) + 2
        return y + 10

    def _cartao_modulo(self, tela, x, y, w, mod, antes):
        an = self.an
        mudou_mod = (mod['ligado'] != antes['ligado']) or (mod['modelo'] != antes['modelo'])
        params_antes = {(p['indice']): p['texto'] for p in antes['params']} if antes['modelo'] == mod['modelo'] else {}
        n = len(mod['params'])
        h = 46 + ((n + 1) // 2) * 16
        rr = pygame.Rect(x, y, w, h)
        cor = TEMA.verde if mod['ligado'] else TEMA.borda
        ds.superficie_translucida(tela, rr, ds.misturar(TEMA.superficie_alt, cor, 0.1), 225, ds.RAIO_MD,
                                  TEMA.aviso if mudou_mod else cor, 2 if mudou_mod else 1)
        ds.texto_em(tela, mod['nome'], an._fonte(13), (x + 10, y + 6), TEMA.texto)
        ds.interruptor(tela, pygame.Rect(x + w - 44, y + 7, 34, 18), mod['ligado'], cor=TEMA.verde)
        modelo = mod['modelo_nome']
        if antes['modelo'] != mod['modelo']:
            modelo = f"{antes['modelo_nome']} → {modelo}"
        ds.texto_em(tela, modelo, an._fonte(10, False), (x + 10, y + 25), TEMA.aviso if antes['modelo'] != mod['modelo']
                    else TEMA.texto_suave, largura_max=w - 60)
        meia = (w - 20) // 2
        for i, p in enumerate(mod['params']):
            px = x + 10 + (i % 2) * meia
            py = y + 44 + (i // 2) * 16
            ant = params_antes.get(p['indice'])
            mudou = ant is not None and ant != p['texto']
            txt = f"{p['nome']}: " + (f"{ant} → {p['texto']}" if mudou else p['texto'])
            ds.texto_em(tela, txt, an._fonte(10, mudou), (px, py), TEMA.aviso if mudou else TEMA.texto_suave,
                        largura_max=meia - 6)
        return h

    def _conferencia(self, tela, x, y, w):
        an = self.an
        c = self.conferencia
        ok = not c['difs']
        cor = TEMA.verde if ok else TEMA.alerta
        titulo = (f"{_t('Conferência')} ({c['arquivo']}): " +
                  (_t('tudo igual ao que o EIGUIT gerou ✓') if ok else f"{len(c['difs'])} {_t('diferença(s)')}"))
        ds.texto_em(tela, titulo, an._fonte(12), (x, y), cor, largura_max=w - 90)
        self._botao(tela, pygame.Rect(x + w - 80, y - 4, 80, 24), 'Fechar', ('fechar_conf', None), tamanho=10)
        y += 22
        for dif in c['difs'][:30]:
            ds.texto_em(tela, f"{dif['campo']}: {_t('esperado')} {dif['esperado']}, {_t('no arquivo')} {dif['encontrado']}",
                        an._fonte(10, False), (x + 10, y), TEMA.texto_suave, largura_max=w - 10)
            y += 16
        return y + 10

    # ================================================================ util
    def _alvo(self, rect, dado):
        vis = pygame.Rect(rect).clip(self._area)
        if vis.width > 0 and vis.height > 0:
            self.an._alvo(vis, 'ped', dado)

    def _botao(self, tela, rect, texto, dado, variante='secundario', tamanho=11):
        an = self.an
        rect = pygame.Rect(rect)
        ds.botao(tela, rect, _t(texto), an._fonte(tamanho), variante=variante, hover=an._hover(rect.clip(self._area)))
        self._alvo(rect, dado)

    def _paragrafo(self, tela, texto, fonte, x, y, largura, cor):
        palavras, linha = str(texto).split(' '), ''
        for p in palavras:
            teste = (linha + ' ' + p).strip()
            if fonte.size(teste)[0] > largura and linha:
                ds.texto_em(tela, linha, fonte, (x, y), cor)
                y += fonte.get_height() + 2
                linha = p
            else:
                linha = teste
        if linha:
            ds.texto_em(tela, linha, fonte, (x, y), cor)
            y += fonte.get_height() + 2
        return y

    def _fim(self, tela, r, y, rolagem, clip):
        tela.set_clip(clip)
        total = y + rolagem - r.y
        maximo = max(0, total - r.height + 10)
        self.an.scroll['pedaleira'] = max(0, min(rolagem, maximo))
        self.an._areas_rolagem.append((r, 'pedaleira', maximo))
        if maximo > 0:
            ds.barra_rolagem(tela, r.right - 6, r.y, r.height, r.height / max(1, total), rolagem / maximo, largura=6)
