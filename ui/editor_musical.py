# -*- coding: utf-8 -*-
"""
Editor musical: tablatura e partitura da mesma peca.

A fonte de verdade e uma grade [corda][tempo] com o numero da casa. A
partitura nao guarda dados proprios: ela deriva a altura de cada nota a
partir da corda, da casa e da afinacao do instrumento. Por isso as duas
visualizacoes nunca saem de sincronia, e alternar entre elas e imediato.
"""
import json
import time

import pygame

from config.design_system import TEMA, ds
from config.instrumentos import NOTAS, config_instrumento
from core.i18n import _t
from core.modulos.modulo_dados_tab import GerenciadorDadosTablatura

VISOES = ['Tablatura', 'Partitura']

# Afinacao e oitava de cada corda, da mais grave para a mais aguda
AFINACOES = {
    'Guitarra': [('E', 2), ('A', 2), ('D', 3), ('G', 3), ('B', 3), ('E', 4)],
    'Baixo': [('E', 1), ('A', 1), ('D', 2), ('G', 2)],
    'Voz': [('E', 3), ('A', 3), ('D', 4), ('G', 4), ('B', 4), ('E', 5)],
    'Bateria': [('E', 2), ('A', 2), ('D', 3), ('G', 3), ('B', 3), ('E', 4)],
}

# Clave, nota da linha de baixo e oitavas de escrita de cada instrumento.
# Violao, guitarra e baixo soam uma oitava abaixo do que se escreve: por isso
# a partitura sobe a oitava, senao tudo cairia longe da pauta.
CLAVES = {
    'Guitarra': {'simbolo': '&', 'base': ('E', 4), 'oitavas': 1},
    'Baixo':    {'simbolo': '9', 'base': ('G', 2), 'oitavas': 1},
    'Voz':      {'simbolo': '&', 'base': ('E', 4), 'oitavas': 0},
    'Bateria':  {'simbolo': '&', 'base': ('E', 4), 'oitavas': 1},
}

# Passo diatonico de cada nota, para posicionar na pauta
GRAU_DIATONICO = {'C': 0, 'C#': 0, 'D': 1, 'D#': 1, 'E': 2, 'F': 3, 'F#': 3,
                  'G': 4, 'G#': 4, 'A': 5, 'A#': 5, 'B': 6}
TEM_SUSTENIDO = {'C#', 'D#', 'F#', 'G#', 'A#'}

DURACOES = [('Seminima', 4), ('Colcheia', 2), ('Semicolcheia', 1)]
TEMPOS_POR_COMPASSO = 16   # em semicolcheias


def altura_da_casa(instrumento, corda, casa):
    """(nome, oitava) da nota tocada nessa corda e casa."""
    afinacao = AFINACOES.get(instrumento, AFINACOES['Guitarra'])
    if not (0 <= corda < len(afinacao)):
        return None, None
    nome_solta, oitava = afinacao[corda]
    indice = NOTAS.index(nome_solta) + casa
    return NOTAS[indice % 12], oitava + indice // 12


def passo_na_pauta(nome, oitava):
    """
    Posicao diatonica absoluta: quantas linhas e espacos acima de C0.
    Serve para achar a altura da cabeca da nota na pauta.
    """
    if nome is None:
        return None
    return oitava * 7 + GRAU_DIATONICO[nome]


def valor_da_celula(celula):
    """A grade guarda '3v100'; devolve so a casa como inteiro, ou None."""
    if not celula or celula == '-':
        return None
    texto = str(celula).split('v')[0]
    return int(texto) if texto.isdigit() else None


class EditorMusical:
    """
        Como funciona: Uma grade de tablatura editavel que tambem se le como
        partitura. A barra de ferramentas troca instrumento, andamento,
        visualizacao e duracao da figura.
        Para que serve: Criar tablaturas e partituras no proprio estudio.
        Onde e usada: Tela de Criacao Musical.
    """

    ALTURA_TOOLBAR = 96

    def __init__(self):
        self.dados = GerenciadorDadosTablatura()
        self.visao = 0
        self.duracao = 1          # indice em DURACOES
        self.cursor = [0, 0]      # [corda, tempo]
        self.scroll = 0
        self.tocando = False
        self.playhead = 0
        self.inicio_play = 0.0
        self.editando_nome = False
        self.mensagem = ''
        self.mensagem_ate = 0.0

        self.espaco_cordas = 20
        self.espaco_tempos = 22
        self.altura_sistema = 0

        self.rects_visao = []
        self.rects_instrumento = []
        self.rects_duracao = []
        self.rects_celulas = []
        self.rect_nome = pygame.Rect(0, 0, 0, 0)
        self.rect_bpm_menos = pygame.Rect(0, 0, 0, 0)
        self.rect_bpm_mais = pygame.Rect(0, 0, 0, 0)
        self.rect_play = pygame.Rect(0, 0, 0, 0)
        self.rect_salvar = pygame.Rect(0, 0, 0, 0)
        self.rect_exportar = pygame.Rect(0, 0, 0, 0)
        self.rect_add_compasso = pygame.Rect(0, 0, 0, 0)

        self._fontes = {}

    # ------------------------------------------------------------ auxiliares
    def _fonte(self, tamanho, negrito=True):
        chave = (tamanho, negrito)
        if chave not in self._fontes:
            self._fontes[chave] = pygame.font.SysFont('Arial', tamanho, bold=negrito)
        return self._fontes[chave]

    @property
    def instrumento(self):
        return self.dados.instrumento_atual

    @property
    def grade(self):
        return self.dados.grade

    @property
    def num_cordas(self):
        return len(self.grade)

    @property
    def num_tempos(self):
        return len(self.grade[0]) if self.grade else 0

    def _avisar(self, texto):
        self.mensagem = texto
        self.mensagem_ate = time.time() + 2.0

    # ---------------------------------------------------------------- edicao
    def escrever(self, digito):
        """Digita um numero na celula do cursor, acumulando ate dois digitos."""
        corda, tempo = self.cursor
        atual = valor_da_celula(self.grade[corda][tempo])
        if atual is not None and atual < 10 and time.time() - getattr(self, '_ultima_tecla', 0) < 0.8:
            novo = atual * 10 + digito
            if novo > 24:
                novo = digito
        else:
            novo = digito
        self._ultima_tecla = time.time()
        self.dados.adicionar_nota(corda, tempo, novo)

    def apagar(self):
        corda, tempo = self.cursor
        self.grade[corda][tempo] = '-'

    def mover(self, dc, dt):
        """Anda com o cursor pela grade, criando espaco quando chega ao fim."""
        self.cursor[0] = max(0, min(self.num_cordas - 1, self.cursor[0] + dc))
        novo_tempo = self.cursor[1] + dt * DURACOES[self.duracao][1]
        if novo_tempo >= self.num_tempos:
            self.dados.adicionar_colunas(TEMPOS_POR_COMPASSO)
        self.cursor[1] = max(0, min(self.num_tempos - 1, novo_tempo))

    def alternar_play(self, gravador=None):
        """Toca ou para a peca, movendo a cabeca de leitura."""
        if self.tocando:
            self.tocando = False
            self.dados.stop()
            return
        self.tocando = True
        self.playhead = 0
        self.inicio_play = time.time()
        try:
            self.dados.play(lambda *a, **k: None)
        except Exception:
            pass

    def atualizar_playhead(self):
        """A cabeca anda pelo relogio, nao pelo numero de quadros."""
        if not self.tocando:
            return
        pulso = 60.0 / max(1, self.dados.bpm) / 4      # uma semicolcheia
        passo = int((time.time() - self.inicio_play) / pulso)
        if passo >= self.num_tempos:
            self.tocando = False
            self.dados.stop()
            self.playhead = 0
        else:
            self.playhead = passo

    def salvar(self, estado):
        """Grava o projeto no banco, se houver usuario logado."""
        if not (estado and getattr(estado, 'db', None) and getattr(estado, 'usuario_id_logado', None)):
            self._avisar(_t('Entre na sua conta para salvar'))
            return False
        try:
            conteudo = json.dumps({'bpm': self.dados.bpm,
                                   'nome': self.dados.nome_musica,
                                   'trilhas': self.dados.trilhas})
            sucesso = estado.db.salvar_projeto(estado.usuario_id_logado,
                                               self.dados.nome_musica,
                                               'tablatura', conteudo)
            self._avisar(_t('Projeto salvo') if sucesso else _t('Erro ao salvar'))
            return bool(sucesso)
        except Exception as e:
            self._avisar(f"{_t('Erro ao salvar')}: {e}")
            return False

    def exportar(self):
        """Escreve a tablatura em texto, no formato classico de forum."""
        try:
            afinacao = AFINACOES.get(self.instrumento, AFINACOES['Guitarra'])
            linhas = []
            for corda in range(self.num_cordas - 1, -1, -1):
                nome = afinacao[corda][0] if corda < len(afinacao) else '?'
                partes = [f'{nome}|']
                for tempo in range(self.num_tempos):
                    valor = valor_da_celula(self.grade[corda][tempo])
                    partes.append(f'{valor}' if valor is not None else '-')
                    partes.append('-' if valor is None or valor < 10 else '')
                linhas.append(''.join(partes))
            caminho = f'{self.dados.nome_musica.replace(" ", "_")}.txt'
            with open(caminho, 'w', encoding='utf-8') as arq:
                arq.write(f'{self.dados.nome_musica} — {self.dados.bpm} BPM\n\n')
                arq.write('\n'.join(linhas))
            self._avisar(f'{_t("Exportado")}: {caminho}')
            return caminho
        except Exception as e:
            self._avisar(f'{_t("Erro ao exportar")}: {e}')
            return None

    # ------------------------------------------------------------- desenho --
    def _toolbar(self, tela, rect, fontes):
        """Nome, instrumento, andamento, visao, duracao e acoes."""
        pos_mouse = pygame.mouse.get_pos()
        fonte = self._fonte(12)
        y = rect.y

        # Nome da peca
        self.rect_nome = pygame.Rect(rect.x, y, min(300, rect.width * 0.3), 30)
        ds.caixa_texto(tela, self.rect_nome, self.dados.nome_musica, self._fonte(14),
                       focado=self.editando_nome, placeholder=_t('Nome da peca'))

        # Visao: tablatura ou partitura
        self.rects_visao = []
        x = self.rect_nome.right + ds.ESPACO_LG
        for i, nome in enumerate(VISOES):
            larg = fonte.size(_t(nome))[0] + 26
            r = pygame.Rect(x, y + 2, larg, 26)
            self.rects_visao.append(r)
            ds.chip(tela, r, _t(nome), fonte, ativo=i == self.visao)
            x += larg + 5

        # Acoes a direita
        self.rect_exportar = pygame.Rect(rect.right - 96, y, 96, 30)
        self.rect_salvar = pygame.Rect(self.rect_exportar.x - 102, y, 96, 30)
        self.rect_play = pygame.Rect(self.rect_salvar.x - 102, y, 96, 30)
        ds.botao(tela, self.rect_play, _t('Parar') if self.tocando else _t('Tocar'),
                 fonte, variante='perigo' if self.tocando else 'primario',
                 hover=self.rect_play.collidepoint(pos_mouse))
        ds.botao(tela, self.rect_salvar, _t('Salvar'), fonte, variante='suave',
                 hover=self.rect_salvar.collidepoint(pos_mouse))
        ds.botao(tela, self.rect_exportar, _t('Exportar'), fonte, variante='secundario',
                 hover=self.rect_exportar.collidepoint(pos_mouse))

        y += 36
        # Instrumentos
        self.rects_instrumento = []
        x = rect.x
        for nome in self.dados.trilhas:
            larg = fonte.size(_t(nome))[0] + 22
            r = pygame.Rect(x, y, larg, 26)
            self.rects_instrumento.append((r, nome))
            ds.chip(tela, r, _t(nome), fonte, ativo=nome == self.instrumento)
            x += larg + 5

        # Duracao da figura
        self.rects_duracao = []
        x += ds.ESPACO_LG
        for i, (nome, _passos) in enumerate(DURACOES):
            larg = fonte.size(_t(nome))[0] + 20
            r = pygame.Rect(x, y, larg, 26)
            if r.right > rect.right - 230:
                break
            self.rects_duracao.append(r)
            ds.chip(tela, r, _t(nome), self._fonte(11), ativo=i == self.duracao)
            x += larg + 4

        # Andamento
        self.rect_bpm_mais = pygame.Rect(rect.right - 30, y, 30, 26)
        self.rect_bpm_menos = pygame.Rect(rect.right - 130, y, 30, 26)
        ds.botao(tela, self.rect_bpm_menos, '-', fonte, variante='secundario')
        ds.botao(tela, self.rect_bpm_mais, '+', fonte, variante='secundario')
        ds.texto_centralizado(
            tela, f'{self.dados.bpm} BPM', fonte,
            pygame.Rect(self.rect_bpm_menos.right, y,
                        self.rect_bpm_mais.left - self.rect_bpm_menos.right, 26),
            TEMA.texto)

    def _desenhar_tablatura(self, tela, rect, fontes):
        """Grade de cordas e casas, em sistemas que quebram por largura."""
        afinacao = AFINACOES.get(self.instrumento, AFINACOES['Guitarra'])
        margem = 34
        largura_util = rect.width - margem - ds.ESPACO_MD
        por_sistema = max(TEMPOS_POR_COMPASSO,
                          int(largura_util // self.espaco_tempos
                              // TEMPOS_POR_COMPASSO) * TEMPOS_POR_COMPASSO)
        altura_sistema = self.espaco_cordas * (self.num_cordas - 1) + 56
        self.altura_sistema = altura_sistema
        self.rects_celulas = []

        sistemas = max(1, (self.num_tempos + por_sistema - 1) // por_sistema)
        y = rect.y - self.scroll
        for s in range(sistemas):
            if y + altura_sistema < rect.y - 40 or y > rect.bottom + 40:
                y += altura_sistema
                continue
            inicio = s * por_sistema
            base_y = y + 22

            for i in range(self.num_cordas):
                ly = base_y + i * self.espaco_cordas
                pygame.draw.line(tela, ds.rgb(TEMA.corda),
                                 (rect.x + margem, ly),
                                 (rect.x + margem + por_sistema * self.espaco_tempos, ly), 1)
                nome_corda = afinacao[self.num_cordas - 1 - i][0] if self.num_cordas - 1 - i < len(afinacao) else '?'
                ds.texto_em(tela, nome_corda, self._fonte(11),
                            (rect.x + margem - 12, ly), TEMA.texto_apagado, ancora='center')

            # Divisao de compassos
            for c in range(por_sistema // TEMPOS_POR_COMPASSO + 1):
                bx = rect.x + margem + c * TEMPOS_POR_COMPASSO * self.espaco_tempos
                pygame.draw.line(tela, ds.rgb(TEMA.borda), (bx, base_y),
                                 (bx, base_y + (self.num_cordas - 1) * self.espaco_cordas), 2)
                numero = (inicio // TEMPOS_POR_COMPASSO) + c + 1
                if c < por_sistema // TEMPOS_POR_COMPASSO:
                    ds.texto_em(tela, str(numero), self._fonte(10), (bx + 4, base_y - 16),
                                TEMA.texto_apagado)

            # Notas
            for t in range(por_sistema):
                tempo = inicio + t
                if tempo >= self.num_tempos:
                    break
                cx = rect.x + margem + t * self.espaco_tempos + self.espaco_tempos / 2
                for i in range(self.num_cordas):
                    corda = self.num_cordas - 1 - i
                    ly = base_y + i * self.espaco_cordas
                    celula = pygame.Rect(int(cx - self.espaco_tempos / 2),
                                         int(ly - self.espaco_cordas / 2),
                                         int(self.espaco_tempos), int(self.espaco_cordas))
                    self.rects_celulas.append((celula, (corda, tempo)))

                    if [corda, tempo] == self.cursor:
                        ds.superficie_translucida(tela, celula, TEMA.acento, 80,
                                                  ds.RAIO_SM, TEMA.acento, 1)
                    valor = valor_da_celula(self.grade[corda][tempo])
                    if valor is not None:
                        fundo = pygame.Rect(0, 0, 18, 14)
                        fundo.center = (int(cx), int(ly))
                        pygame.draw.rect(tela, ds.rgb(TEMA.fundo), fundo)
                        ds.texto_em(tela, str(valor), self._fonte(12),
                                    (int(cx), int(ly)), TEMA.texto, ancora='center')

                if self.tocando and tempo == self.playhead:
                    pygame.draw.line(tela, ds.rgb(TEMA.aviso), (cx, base_y - 8),
                                     (cx, base_y + (self.num_cordas - 1) * self.espaco_cordas + 8), 2)
            y += altura_sistema

        self.altura_total = sistemas * altura_sistema

    def _desenhar_partitura(self, tela, rect, fontes):
        """A mesma grade lida como pauta de cinco linhas."""
        margem = 44
        espaco = 9                     # metade da distancia entre linhas
        largura_util = rect.width - margem - ds.ESPACO_MD
        por_sistema = max(TEMPOS_POR_COMPASSO,
                          int(largura_util // self.espaco_tempos
                              // TEMPOS_POR_COMPASSO) * TEMPOS_POR_COMPASSO)
        altura_sistema = 150
        self.altura_sistema = altura_sistema
        self.rects_celulas = []

        clave = CLAVES.get(self.instrumento, CLAVES['Guitarra'])
        passo_base = passo_na_pauta(*clave['base'])
        oitavas_escrita = clave['oitavas']

        sistemas = max(1, (self.num_tempos + por_sistema - 1) // por_sistema)
        y = rect.y - self.scroll
        for s in range(sistemas):
            if y + altura_sistema < rect.y - 40 or y > rect.bottom + 40:
                y += altura_sistema
                continue
            inicio = s * por_sistema
            base_y = y + 92          # linha inferior da pauta

            for i in range(5):
                ly = base_y - i * espaco * 2
                pygame.draw.line(tela, ds.rgb(TEMA.corda), (rect.x + margem, ly),
                                 (rect.x + margem + por_sistema * self.espaco_tempos, ly), 1)
            ds.texto_em(tela, clave['simbolo'], self._fonte(34),
                        (rect.x + margem - 24, base_y - 18),
                        TEMA.texto_suave, ancora='center')

            for c in range(por_sistema // TEMPOS_POR_COMPASSO + 1):
                bx = rect.x + margem + c * TEMPOS_POR_COMPASSO * self.espaco_tempos
                pygame.draw.line(tela, ds.rgb(TEMA.borda), (bx, base_y - espaco * 8),
                                 (bx, base_y), 2)

            for t in range(por_sistema):
                tempo = inicio + t
                if tempo >= self.num_tempos:
                    break
                cx = rect.x + margem + t * self.espaco_tempos + self.espaco_tempos / 2
                for corda in range(self.num_cordas):
                    valor = valor_da_celula(self.grade[corda][tempo])
                    if valor is None:
                        continue
                    nome, oitava = altura_da_casa(self.instrumento, corda, valor)
                    passo = passo_na_pauta(nome, oitava + oitavas_escrita)
                    if passo is None:
                        continue
                    ly = base_y - (passo - passo_base) * espaco
                    cor = TEMA.aviso if (self.tocando and tempo == self.playhead) else TEMA.texto

                    # Linhas suplementares acima e abaixo da pauta
                    degrau = passo - passo_base
                    if degrau < 0:
                        for k in range(-1, degrau - 1, -2):
                            ys = base_y - k * espaco
                            pygame.draw.line(tela, ds.rgb(TEMA.corda),
                                             (cx - 9, ys), (cx + 9, ys), 1)
                    elif degrau > 8:
                        for k in range(10, degrau + 2, 2):
                            ys = base_y - k * espaco
                            pygame.draw.line(tela, ds.rgb(TEMA.corda),
                                             (cx - 9, ys), (cx + 9, ys), 1)

                    if nome in TEM_SUSTENIDO:
                        ds.texto_em(tela, '#', self._fonte(11), (cx - 11, ly),
                                    TEMA.texto_suave, ancora='center')
                    cabeca = pygame.Surface((14, 10), pygame.SRCALPHA)
                    pygame.draw.ellipse(cabeca, ds.rgb(cor), (0, 0, 14, 10))
                    cabeca = pygame.transform.rotate(cabeca, 18)
                    tela.blit(cabeca, (int(cx - cabeca.get_width() / 2),
                                       int(ly - cabeca.get_height() / 2)))
                    if degrau > 4:      # acima da linha do meio: haste para baixo
                        pygame.draw.line(tela, ds.rgb(cor), (cx - 6, ly),
                                         (cx - 6, ly + 26), 2)
                    else:
                        pygame.draw.line(tela, ds.rgb(cor), (cx + 6, ly),
                                         (cx + 6, ly - 26), 2)

                if self.tocando and tempo == self.playhead:
                    pygame.draw.line(tela, ds.rgb(TEMA.aviso),
                                     (cx, base_y - espaco * 9), (cx, base_y + 10), 2)
            y += altura_sistema

        self.altura_total = sistemas * altura_sistema

    def desenhar_interface_tab(self, tela, estado, fontes, largura, altura,
                               configs=None, campo=None):
        """
            Como funciona: Desenha a barra de ferramentas e, abaixo, a
            tablatura ou a partitura da mesma peca.
            Para que serve: Tela de Criacao Musical.
            Onde e usada: Chamada por renderizador_ui.
        """
        if configs is not None:
            TEMA.definir_acento(configs.get_cor_tema())
        self.atualizar_playhead()

        area = pygame.Rect(0, 0, largura, altura)
        ds.fundo_app(tela, area)

        toolbar = pygame.Rect(ds.ESPACO_LG, ds.ESPACO_MD,
                              largura - ds.ESPACO_LG * 2, self.ALTURA_TOOLBAR - 20)
        ds.painel(tela, toolbar, None, None, acento=TEMA.acento, alpha=235)
        self._toolbar(tela, toolbar.inflate(-ds.ESPACO_LG * 2, -ds.ESPACO_MD * 2), fontes)

        editor = pygame.Rect(ds.ESPACO_LG, toolbar.bottom + ds.ESPACO_MD,
                             largura - ds.ESPACO_LG * 2,
                             altura - toolbar.bottom - ds.ESPACO_XL - 20)
        ds.painel(tela, editor, None, None, acento=TEMA.borda, alpha=225)
        interno = editor.inflate(-ds.ESPACO_LG * 2, -ds.ESPACO_LG * 2)

        tela.set_clip(interno)
        if VISOES[self.visao] == 'Tablatura':
            self._desenhar_tablatura(tela, interno, fontes)
        else:
            self._desenhar_partitura(tela, interno, fontes)
        tela.set_clip(None)

        # Rodape com ajuda e mensagem
        ajuda = _t('Clique numa casa e digite o numero. Setas movem, Delete apaga.')
        ds.texto_em(tela, ajuda, self._fonte(11),
                    (editor.x + ds.ESPACO_MD, editor.bottom + 4), TEMA.texto_apagado)
        if self.mensagem and time.time() < self.mensagem_ate:
            ds.texto_em(tela, self.mensagem, self._fonte(13),
                        (editor.right - ds.ESPACO_MD, editor.bottom + 2),
                        TEMA.verde, ancora='topright')

    # ------------------------------------------------------------- eventos --
    def tratar_evento(self, evento, estado=None, gravador=None):
        """
            Como funciona: Trata clique, roda do mouse e teclado do editor.
            Para que serve: Toda a edicao da peca.
            Onde e usada: Chamada pelo controlador de eventos.
        """
        if evento.type == pygame.MOUSEWHEEL:
            limite = max(0, getattr(self, 'altura_total', 0) - 200)
            self.scroll = max(0, min(limite, self.scroll - evento.y * 48))
            return True

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            pos = evento.pos
            if self.rect_nome.collidepoint(pos):
                self.editando_nome = True
                return True
            self.editando_nome = False

            for i, r in enumerate(self.rects_visao):
                if r.collidepoint(pos):
                    self.visao = i
                    self.scroll = 0
                    return True
            for r, nome in self.rects_instrumento:
                if r.collidepoint(pos):
                    self.dados.alternar_instrumento(nome)
                    self.cursor = [0, 0]
                    return True
            for i, r in enumerate(self.rects_duracao):
                if r.collidepoint(pos):
                    self.duracao = i
                    return True
            if self.rect_play.collidepoint(pos):
                self.alternar_play(gravador); return True
            if self.rect_salvar.collidepoint(pos):
                self.salvar(estado); return True
            if self.rect_exportar.collidepoint(pos):
                self.exportar(); return True
            if self.rect_bpm_menos.collidepoint(pos):
                self.dados.set_bpm(max(40, self.dados.bpm - 5)); return True
            if self.rect_bpm_mais.collidepoint(pos):
                self.dados.set_bpm(min(300, self.dados.bpm + 5)); return True

            for celula, (corda, tempo) in self.rects_celulas:
                if celula.collidepoint(pos):
                    self.cursor = [corda, tempo]
                    return True
            return False

        if evento.type == pygame.KEYDOWN:
            if self.editando_nome:
                if evento.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    self.editando_nome = False
                elif evento.key == pygame.K_BACKSPACE:
                    self.dados.nome_musica = self.dados.nome_musica[:-1]
                elif evento.unicode and evento.unicode.isprintable():
                    if len(self.dados.nome_musica) < 40:
                        self.dados.nome_musica += evento.unicode
                return True

            if evento.unicode.isdigit():
                self.escrever(int(evento.unicode)); return True
            if evento.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                self.apagar(); return True
            if evento.key == pygame.K_UP:
                self.mover(1, 0); return True
            if evento.key == pygame.K_DOWN:
                self.mover(-1, 0); return True
            if evento.key == pygame.K_LEFT:
                self.mover(0, -1); return True
            if evento.key in (pygame.K_RIGHT, pygame.K_SPACE):
                self.mover(0, 1); return True
            if evento.key == pygame.K_TAB:
                self.visao = (self.visao + 1) % len(VISOES); return True
        return False
