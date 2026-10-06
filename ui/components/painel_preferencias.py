# -*- coding: utf-8 -*-
"""
Sub-abas novas da aba CONFIGURACAO: "Teclas de Atalho" e "Desempenho".

Desenhadas dentro da gaveta do painel inferior (com o recorte e a rolagem que
o bottom_nav ja faz). Cada alvo clicavel fica guardado em PAINEL.alvos com
o retangulo exato do desenho; o controlador so chama tratar_clique().
Tudo que muda aqui marca o perfil para o auto-salvamento.
"""
import pygame

import core.atalhos as atalhos
import core.desempenho as desempenho
from config.design_system import TEMA, ds
from core.i18n import _t

ALTURA_LINHA = 34

_fontes = {}


def _fonte(tamanho, negrito=True):
    chave = (tamanho, negrito)
    if chave not in _fontes:
        _fontes[chave] = pygame.font.SysFont('Arial', tamanho, bold=negrito)
    return _fontes[chave]


class PainelPreferencias:
    def __init__(self):
        self.alvos = []          # [(rect, tipo, dado)]

    # ----------------------------------------------------------- comum ----
    def _alvo(self, rect, tipo, dado=None):
        self.alvos.append((pygame.Rect(rect), tipo, dado))

    def _botao(self, tela, rect, texto, mouse, tipo, dado=None, variante='secundario', ativo=False):
        ds.botao(tela, rect, texto, _fonte(12), variante=variante, ativo=ativo,
                 hover=rect.collidepoint(mouse))
        self._alvo(rect, tipo, dado)

    def _cabecalho(self, tela, x, y, largura, titulo, descricao):
        ds.texto_em(tela, _t(titulo), _fonte(17), (x, y), TEMA.texto)
        ds.texto_em(tela, _t(descricao), _fonte(13, False), (x, y + 24), TEMA.texto_suave,
                    largura_max=largura)
        return y + 52

    def _rodape_perfil(self, tela, x, y, estado):
        import core.acoes_cabecalho as acoes
        nome = acoes.nome_perfil_atual(estado) or _t('Padrão')
        ds.texto_em(tela, f"{_t('Salvo automaticamente no perfil')}: {nome}", _fonte(12, False),
                    (x, y), TEMA.texto_apagado)
        return y + 24

    # --------------------------------------------------------- teclas -----
    def desenhar_teclas(self, tela, x, y, largura, estado, mouse):
        """Devolve a altura total do conteudo (para a rolagem)."""
        self.alvos = []
        y0 = y
        y = self._cabecalho(tela, x, y, largura - 180, 'Teclas de atalho',
                            'Clique em Alterar e aperte a nova combinação. Esc cancela, '
                            'Backspace deixa a função sem tecla.')
        self._botao(tela, pygame.Rect(x + largura - 170, y0 + 4, 160, 30),
                    _t('Restaurar todas'), mouse, 'restaurar_todas', variante='suave')
        tabela = atalhos.obter(estado)
        capturando = getattr(estado, 'capturando_atalho', None)
        colunas = 2 if largura >= 1100 else 1
        largura_col = (largura - (colunas - 1) * 24) // colunas
        # Distribui os grupos nas colunas pela quantidade de linhas
        grupos = [(g, [(a, r) for gg, a, r, _p in atalhos.ACOES if gg == g]) for g in atalhos.GRUPOS]
        alturas = [0] * colunas
        destino = [[] for _ in range(colunas)]
        for grupo in grupos:
            c = alturas.index(min(alturas))
            destino[c].append(grupo)
            alturas[c] += 30 + len(grupo[1]) * ALTURA_LINHA + 12
        y_fim = y
        for c, lista in enumerate(destino):
            cx = x + c * (largura_col + 24)
            cy = y
            for grupo, itens in lista:
                ds.texto_em(tela, _t(grupo).upper(), _fonte(12), (cx, cy + 6), TEMA.acento)
                cy += 30
                for acao, rotulo in itens:
                    self._linha_tecla(tela, pygame.Rect(cx, cy, largura_col, ALTURA_LINHA - 4),
                                      acao, rotulo, tabela.get(acao, []), capturando == acao, mouse)
                    cy += ALTURA_LINHA
                cy += 12
            y_fim = max(y_fim, cy)
        y_fim = self._rodape_perfil(tela, x, y_fim + 4, estado)
        return y_fim - y0 + 12

    def _linha_tecla(self, tela, rect, acao, rotulo, combos, capturando, mouse):
        if capturando:
            ds.superficie_translucida(tela, rect, ds.misturar(TEMA.superficie_alt, TEMA.acento, 0.3),
                                      240, ds.RAIO_MD, TEMA.acento, 1)
        elif rect.collidepoint(mouse):
            ds.superficie_translucida(tela, rect, TEMA.superficie_alt, 200, ds.RAIO_MD)
        larg_botoes = 82 + 6 + 30 + 6 + 30
        x_chips = rect.x + int(rect.width * 0.46)
        ds.texto_em(tela, _t(rotulo), _fonte(13), (rect.x + 10, rect.centery), TEMA.texto,
                    ancora='midleft', largura_max=x_chips - rect.x - 16)
        x = x_chips
        limite = rect.right - larg_botoes - 10
        if capturando:
            ds.texto_em(tela, _t('Aperte a nova tecla...'), _fonte(13), (x, rect.centery),
                        TEMA.acento, ancora='midleft', largura_max=limite - x)
        elif not combos:
            ds.texto_em(tela, _t('sem atalho'), _fonte(12, False), (x, rect.centery),
                        TEMA.texto_apagado, ancora='midleft')
        else:
            for combo in combos:
                txt = atalhos.texto(combo)
                larg = _fonte(12).size(txt)[0] + 16
                if x + larg > limite:
                    break
                chip = pygame.Rect(x, rect.centery - 11, larg, 22)
                ds.superficie_translucida(tela, chip, TEMA.fundo_alt, 255, ds.RAIO_SM, TEMA.borda, 1)
                ds.texto_centralizado(tela, txt, _fonte(12), chip, TEMA.texto)
                x = chip.right + 6
        bx = rect.right - larg_botoes - 4
        self._botao(tela, pygame.Rect(bx, rect.centery - 12, 82, 24),
                    _t('Cancelar') if capturando else _t('Alterar'), mouse,
                    'cancelar_captura' if capturando else 'capturar', acao,
                    variante='primario' if capturando else 'secundario')
        bx += 88
        r = pygame.Rect(bx, rect.centery - 12, 30, 24)
        self._botao(tela, r, '', mouse, 'padrao_tecla', acao)
        _icone_desfazer(tela, r.center, TEMA.texto_suave)
        bx += 36
        r = pygame.Rect(bx, rect.centery - 12, 30, 24)
        self._botao(tela, r, '', mouse, 'limpar_tecla', acao)
        c = ds.rgb(TEMA.texto_suave)
        pygame.draw.line(tela, c, (r.centerx - 4, r.centery - 4), (r.centerx + 4, r.centery + 4), 2)
        pygame.draw.line(tela, c, (r.centerx + 4, r.centery - 4), (r.centerx - 4, r.centery + 4), 2)

    # ------------------------------------------------------ desempenho ----
    def desenhar_desempenho(self, tela, x, y, largura, estado, mouse):
        self.alvos = []
        y0 = y
        cfg = desempenho.obter(estado)
        y = self._cabecalho(tela, x, y, largura,
                            'Desempenho',
                            'Escolha o perfil do seu computador ou ajuste item a item. '
                            'Vale na hora e fica salvo no perfil.')
        # Cartoes dos presets
        n = len(desempenho.ROTULOS_PRESETS)
        larg_cartao = min(300, (largura - (n - 1) * 12) // n)
        for i, (nome, rotulo, desc) in enumerate(desempenho.ROTULOS_PRESETS):
            r = pygame.Rect(x + i * (larg_cartao + 12), y, larg_cartao, 62)
            ativo = cfg.get('preset') == nome
            hover = r.collidepoint(mouse)
            if ativo:
                pygame.draw.rect(tela, ds.rgb(ds.misturar(TEMA.superficie_alt, TEMA.acento, 0.35)), r,
                                 border_radius=ds.RAIO_LG)
                pygame.draw.rect(tela, ds.rgb(TEMA.acento), r, width=2, border_radius=ds.RAIO_LG)
            else:
                ds.superficie_translucida(tela, r, TEMA.superficie_alt, 230 if hover else 190,
                                          ds.RAIO_LG, TEMA.acento if hover else TEMA.borda, 1)
            ds.texto_em(tela, _t(rotulo), _fonte(15), (r.x + 14, r.y + 12), TEMA.texto)
            ds.texto_em(tela, _t(desc), _fonte(12, False), (r.x + 14, r.y + 36), TEMA.texto_suave,
                        largura_max=r.width - 28)
            if ativo:
                pygame.draw.circle(tela, ds.rgb(TEMA.acento), (r.right - 16, r.y + 18), 7)
                pygame.draw.lines(tela, ds.rgb(TEMA.texto_sobre_cor), False,
                                  [(r.right - 19, r.y + 18), (r.right - 17, r.y + 21), (r.right - 12, r.y + 15)], 2)
            self._alvo(r, 'preset', nome)
        y += 62 + 10
        if cfg.get('preset') == 'personalizado':
            ds.texto_em(tela, _t('Personalizado: você ajustou opções à mão.'), _fonte(12, False),
                        (x, y), TEMA.aviso)
        fps = getattr(estado, 'fps_real', 0) or 0
        if fps:
            ds.texto_em(tela, f"{_t('Agora')}: {fps:.0f} FPS", _fonte(12), (x + largura, y),
                        TEMA.texto_suave, ancora='topright')
        y += 26
        # Opcoes
        for chave, rotulo, desc, tipo, rotulos in desempenho.OPCOES:
            r = pygame.Rect(x, y, largura, 48)
            if r.collidepoint(mouse):
                ds.superficie_translucida(tela, r, TEMA.superficie_alt, 160, ds.RAIO_MD)
            ds.texto_em(tela, _t(rotulo), _fonte(14), (r.x + 10, r.y + 7), TEMA.texto)
            ds.texto_em(tela, _t(desc), _fonte(12, False), (r.x + 10, r.y + 27), TEMA.texto_suave,
                        largura_max=int(largura * 0.5))
            if tipo == 'liga':
                chave_rect = pygame.Rect(r.right - 62, r.centery - 12, 48, 24)
                ds.interruptor(tela, chave_rect, bool(cfg.get(chave)))
                self._alvo(r, 'alternar', chave)
            else:
                xx = r.right - 10
                for valor, texto in reversed(list(zip(tipo, rotulos))):
                    larg = _fonte(12).size(_t(texto))[0] + 20
                    chip = pygame.Rect(xx - larg, r.centery - 13, larg, 26)
                    ds.chip(tela, chip, _t(texto), _fonte(12), ativo=cfg.get(chave) == valor)
                    self._alvo(chip, 'valor', (chave, valor))
                    xx = chip.x - 6
            y += 52
        y = self._rodape_perfil(tela, x, y + 6, estado)
        return y - y0 + 12

    # ---------------------------------------------------------- clique ----
    def tratar_clique(self, pos, estado):
        from ui.components.notificacoes import notificar
        for rect, tipo, dado in self.alvos:
            if not rect.collidepoint(pos):
                continue
            if tipo == 'capturar':
                estado.capturando_atalho = dado
            elif tipo == 'cancelar_captura':
                estado.capturando_atalho = None
            elif tipo == 'padrao_tecla':
                atalhos.restaurar(estado, dado)
                estado.capturando_atalho = None
                notificar(estado, f"{_t(atalhos.ROTULOS[dado])}: {_t('tecla padrão')}", 'info', 1.6)
            elif tipo == 'limpar_tecla':
                atalhos.limpar(estado, dado)
                estado.capturando_atalho = None
            elif tipo == 'restaurar_todas':
                atalhos.restaurar(estado)
                estado.capturando_atalho = None
                notificar(estado, _t('Todas as teclas voltaram ao padrão'), 'sucesso')
            elif tipo == 'preset':
                desempenho.aplicar_preset(estado, dado)
                notificar(estado, f"{_t('Desempenho')}: {_t(dado.capitalize())}", 'sucesso', 1.8)
            elif tipo == 'alternar':
                desempenho.definir(estado, dado, not desempenho.obter(estado).get(dado))
            elif tipo == 'valor':
                desempenho.definir(estado, dado[0], dado[1])
            return True
        return False


def _icone_desfazer(tela, centro, cor):
    cx, cy = centro
    cor = ds.rgb(cor)
    pygame.draw.arc(tela, cor, pygame.Rect(cx - 6, cy - 6, 12, 12), 0.3, 4.4, 2)
    pygame.draw.polygon(tela, cor, [(cx + 6, cy - 6), (cx + 6, cy), (cx + 1, cy - 3)])


PAINEL = PainelPreferencias()
