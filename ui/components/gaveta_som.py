"""
Gaveta de sons das telas de tablatura: um botao "Som: ..." que abre uma lista
agrupada (guitarra real, realista, sintetico) para escolher o timbre.

Uso:
    self.gaveta = GavetaSom()
    ... no desenho (depois de tudo, para ficar por cima):
    self.gaveta.desenhar(tela, rect_do_botao, fonte, self.synth)
    ... no MOUSEBUTTONDOWN (antes dos outros cliques):
    if self.gaveta.tratar_clique(evento.pos, rect_do_botao, self.synth):
        return True
"""
import pygame

try:
    from config.design_system import TEMA, ds
except Exception:  # noqa: BLE001
    TEMA = ds = None


def _cor(nome, reserva):
    try:
        v = getattr(TEMA, nome)
        v = ds.rgb(v) if ds is not None and hasattr(ds, 'rgb') else v
        return tuple(int(c) for c in v)[:3]
    except Exception:  # noqa: BLE001
        return reserva


class GavetaSom:
    """
        Como funciona: guarda se a gaveta esta aberta e os retangulos de cada opcao.
        Para que serve: trocar o som da tablatura escolhendo numa lista, e nao em ciclo.
        Onde e usada: ui/renderizador_tablatura.py e ui/renderizador_criador_tab.py.
    """

    LARGURA = 280
    ALTURA_ITEM = 28

    def __init__(self):
        self.aberta = False
        self._itens = []
        self.area = None

    @staticmethod
    def grupos(synth):
        reais = [('prof:' + tid, nome.replace('Real: ', '')) for tid, nome in synth.timbres_disponiveis()]
        return [
            ('GUITARRA REAL (SAMPLES + AMP)', reais, synth.profissional_ok),
            ('OUTROS', [('realista', 'Realista (SoundFont)')], synth.motor_realista_ok),
            ('', [('sintetico', 'Sintetico')], True),
        ]

    @staticmethod
    def chave_atual(synth):
        return 'prof:' + synth.timbre if synth.modo == 'profissional' else synth.modo

    def desenhar(self, tela, rect_botao, fonte, synth):
        if not self.aberta:
            return
        fundo, borda = _cor('superficie', (32, 35, 42)), _cor('borda', (70, 76, 90))
        texto, suave = _cor('texto', (235, 237, 242)), _cor('texto_suave', (150, 156, 168))
        acento, sobre = _cor('acento', (50, 150, 255)), _cor('texto_sobre_cor', (255, 255, 255))
        grupos = self.grupos(synth)
        alt = sum((22 if nome else 4) + self.ALTURA_ITEM * len(itens) for nome, itens, _ in grupos) + 10 + 40
        area = pygame.Rect(rect_botao.x, rect_botao.bottom + 4, self.LARGURA, alt)
        tela_r = tela.get_rect()
        if area.bottom > tela_r.bottom - 4:               # sem espaco embaixo: abre para cima
            area.bottom = rect_botao.y - 4
        if area.right > tela_r.right - 4:
            area.right = tela_r.right - 4
        pygame.draw.rect(tela, (0, 0, 0), area.move(0, 3), border_radius=10)
        pygame.draw.rect(tela, fundo, area, border_radius=10)
        pygame.draw.rect(tela, borda, area, 1, border_radius=10)
        self.area = area
        self._itens = []
        atual = self.chave_atual(synth)
        mouse = pygame.mouse.get_pos()
        y = area.y + 6
        for nome, itens, ok in grupos:
            if nome:
                img = fonte.render(nome if ok else nome + ' (indisponivel)', True, suave)
                tela.blit(img, (area.x + 12, y + 4))
                y += 22
            else:
                y += 4
            for chave, rotulo in itens:
                r = pygame.Rect(area.x + 5, y, area.w - 10, self.ALTURA_ITEM - 2)
                if chave == atual:
                    pygame.draw.rect(tela, acento, r, border_radius=6)
                elif ok and r.collidepoint(mouse):
                    pygame.draw.rect(tela, borda, r, border_radius=6)
                cor = sobre if chave == atual else (texto if ok else suave)
                img = fonte.render(rotulo, True, cor)
                tela.blit(img, (r.x + 10, r.centery - img.get_height() // 2))
                if ok:
                    self._itens.append((r, chave))
                y += self.ALTURA_ITEM
        # volume geral (muda na hora; a gaveta continua aberta)
        y += 6
        pygame.draw.line(tela, borda, (area.x + 10, y), (area.right - 10, y))
        y += 6
        tela.blit(fonte.render('VOLUME', True, suave), (area.x + 12, y + 6))
        vol = getattr(synth, 'volume_mestre', 0.9)
        menos = pygame.Rect(area.right - 130, y, 30, 26)
        mais = pygame.Rect(area.right - 40, y, 30, 26)
        for r, t in ((menos, '-'), (mais, '+')):
            pygame.draw.rect(tela, borda, r, border_radius=6)
            img = fonte.render(t, True, texto)
            tela.blit(img, img.get_rect(center=r.center))
        img = fonte.render(f'{vol * 100:.0f}%', True, texto)
        tela.blit(img, img.get_rect(center=((menos.right + mais.x) // 2, menos.centery)))
        self._itens.append((menos, 'vol-'))
        self._itens.append((mais, 'vol+'))

    def tratar_clique(self, pos, rect_botao, synth):
        """True se o clique foi da gaveta (abrir, fechar ou escolher)."""
        if rect_botao is not None and rect_botao.collidepoint(pos):
            self.aberta = not self.aberta
            return True
        if not self.aberta:
            return False
        for r, chave in self._itens:
            if r.collidepoint(pos):
                if chave in ('vol-', 'vol+'):
                    if hasattr(synth, 'definir_volume'):
                        synth.definir_volume(synth.volume_mestre + (0.1 if chave == 'vol+' else -0.1))
                    return True
                if chave.startswith('prof:'):
                    synth.definir_timbre(chave[5:])
                    synth.alternar_modo('profissional')
                else:
                    synth.alternar_modo(chave)
                self.aberta = False
                return True
        dentro = self.area is not None and self.area.collidepoint(pos)
        self.aberta = False
        return dentro
