# -*- coding: utf-8 -*-
"""
Estudo do ciclo de quintas e de quartas.

Tres abas:

- Roda: o circulo com as doze tonalidades. Cada posicao mostra a maior, a
  relativa menor e a armadura de clave. Escolher uma tonalidade abre o campo
  harmonico completo e as tonalidades vizinhas.
- Sequencias: monta progressoes clicando nos graus, ouve, salva no perfil e
  reaproveita a biblioteca de progressoes classicas.
- Desafio: perguntas de relativa, armadura, quinta e quarta.

Quintas e quartas sao o mesmo circulo lido em sentidos opostos, entao o botao
de sentido inverte a leitura em vez de trocar de tela.
"""
import json
import math
import os
import random

import pygame

from config.design_system import TEMA, ds
from core.i18n import _t

# Ordem do ciclo de quintas, a partir de Do
NOTAS_CICLO = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#', 'F']
RELATIVAS = ['Am', 'Em', 'Bm', 'F#m', 'C#m', 'G#m', 'D#m', 'A#m', 'Fm', 'Cm', 'Gm', 'Dm']
ARMADURAS = ['—', '1♯', '2♯', '3♯', '4♯', '5♯', '6♯', '5♭', '4♭', '3♭', '2♭', '1♭']

CROMATICA = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

CAMPO_MAIOR = {
    'intervalos': [0, 2, 4, 5, 7, 9, 11],
    'romanos': ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°'],
    'qualidades': ['', 'm', 'm', '', '', 'm', 'dim'],
    'funcoes': ['Tonica', 'Subdominante', 'Tonica', 'Subdominante',
                'Dominante', 'Tonica', 'Dominante'],
}
CAMPO_MENOR = {
    'intervalos': [0, 2, 3, 5, 7, 8, 10],
    'romanos': ['i', 'ii°', 'III', 'iv', 'v', 'VI', 'VII'],
    'qualidades': ['m', 'dim', '', 'm', 'm', '', ''],
    'funcoes': ['Tonica', 'Subdominante', 'Tonica', 'Subdominante',
                'Dominante', 'Subdominante', 'Dominante'],
}

BIBLIOTECA = [
    {'nome': 'Pop classico', 'graus': [0, 4, 5, 3], 'cifra': 'I - V - vi - IV'},
    {'nome': 'Rock melodico', 'graus': [0, 4, 3, 0], 'cifra': 'I - V - IV - I'},
    {'nome': 'Doo-wop anos 50', 'graus': [0, 5, 3, 4], 'cifra': 'I - vi - IV - V'},
    {'nome': 'ii - V - I', 'graus': [1, 4, 0], 'cifra': 'ii - V - I'},
    {'nome': 'Epica', 'graus': [5, 3, 0, 4], 'cifra': 'vi - IV - I - V'},
    {'nome': 'Blues basico', 'graus': [0, 3, 0, 4, 3, 0], 'cifra': 'I - IV - I - V - IV - I'},
    {'nome': 'Andaluza', 'graus': [0, 6, 5, 4], 'cifra': 'i - VII - VI - V', 'tonal': 'menor'},
    {'nome': 'Subida', 'graus': [0, 1, 2, 3], 'cifra': 'I - ii - iii - IV'},
    {'nome': 'Circulo completo', 'graus': [5, 1, 4, 0], 'cifra': 'vi - ii - V - I'},
]

ABAS = ['Roda', 'Sequencias', 'Desafio']


def transpor(tonica, semitons):
    """Nota a tantos semitons acima da tonica."""
    base = CROMATICA.index(tonica) if tonica in CROMATICA else 0
    return CROMATICA[(base + semitons) % 12]


def campo_harmonico(tonica, tonal='maior'):
    """Os sete acordes do campo harmonico, com romano, cifra e funcao."""
    campo = CAMPO_MAIOR if tonal == 'maior' else CAMPO_MENOR
    graus = []
    for i in range(7):
        nota = transpor(tonica, campo['intervalos'][i])
        graus.append({
            'romano': campo['romanos'][i],
            'cifra': nota + campo['qualidades'][i],
            'nota': nota,
            'funcao': campo['funcoes'][i],
        })
    return graus


class EstudoCicloQuintas:
    """
        Como funciona: Uma roda de doze posicoes que serve as tres abas. A
        tonalidade escolhida alimenta o campo harmonico, o construtor de
        sequencias e o desafio.
        Para que serve: Entender por que as tonalidades vizinhas soam bem
        juntas e usar isso para criar progressoes.
        Onde e usada: Aba Estudos, secao Ciclo de Quintas.
    """

    def __init__(self):
        self.inicializado = False
        self.aba = 0
        self.sentido = 'quintas'      # ou 'quartas'
        self.tonal = 'maior'
        self.indice_tonalidade = 0    # posicao na roda

        self.sequencia_atual = []     # lista de indices de grau (0..6)
        self.sequencias_custom = []
        self.seq_selecionada = -1
        self.tocando = False
        self.passo_sequencia = 0
        self.ultimo_passo = 0.0
        self.bpm = 80

        # desafio
        self.pergunta = ''
        self.resposta_correta = ''
        self.opcoes = []
        self.feedback = ''
        self.cor_feedback = None
        self.acertos = 0
        self.total = 0

        self.rects_aba = []
        self.rects_roda = []
        self.rects_graus = []
        self.rects_biblioteca = []
        self.rects_salvas = []
        self.rects_opcoes = []
        self.rect_sentido = pygame.Rect(0, 0, 0, 0)
        self.rect_tonal = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_salvar = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_limpar = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_tocar = pygame.Rect(0, 0, 0, 0)

        self.som_nota = None
        self._fontes = {}
        self._carregar_sequencias()

    # ----------------------------------------------------------- persistencia
    def _caminho_perfil(self):
        """Perfil ativo, onde as sequencias ficam guardadas."""
        try:
            if os.path.exists('config_eiguit.json'):
                with open('config_eiguit.json', 'r', encoding='utf-8') as arq:
                    ultimo = json.load(arq).get('ultimo_perfil', '')
                if ultimo and os.path.exists(ultimo):
                    return ultimo
        except Exception:
            pass
        return None

    def _carregar_sequencias(self):
        """Le as sequencias salvas no perfil do usuario."""
        caminho = self._caminho_perfil()
        if not caminho:
            return
        try:
            with open(caminho, 'r', encoding='utf-8') as arq:
                self.sequencias_custom = json.load(arq).get('sequencias_custom', [])
        except Exception as e:
            print(f'[CICLO] Falha ao carregar sequencias: {e}')

    def _salvar_sequencias(self):
        """Grava as sequencias no perfil, preservando o resto do arquivo."""
        caminho = self._caminho_perfil()
        if not caminho:
            print('[CICLO] Nenhum perfil ativo: as sequencias so valem nesta sessao.')
            return False
        try:
            with open(caminho, 'r', encoding='utf-8') as arq:
                perfil = json.load(arq)
            perfil['sequencias_custom'] = self.sequencias_custom
            with open(caminho, 'w', encoding='utf-8') as arq:
                json.dump(perfil, arq, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f'[CICLO] Falha ao salvar sequencias: {e}')
            return False

    # ---------------------------------------------------------------- estado
    def _fonte(self, tamanho):
        if tamanho not in self._fontes:
            self._fontes[tamanho] = pygame.font.SysFont('Arial', tamanho, bold=True)
        return self._fontes[tamanho]

    @property
    def tonalidade(self):
        return NOTAS_CICLO[self.indice_tonalidade % 12]

    @property
    def relativa(self):
        return RELATIVAS[self.indice_tonalidade % 12]

    @property
    def armadura(self):
        return ARMADURAS[self.indice_tonalidade % 12]

    def campo(self):
        base = self.tonalidade if self.tonal == 'maior' else self.relativa[:-1]
        return campo_harmonico(base, self.tonal)

    def vizinhas(self):
        """As duas tonalidades ao lado na roda, que compartilham quase tudo."""
        anterior = NOTAS_CICLO[(self.indice_tonalidade - 1) % 12]
        seguinte = NOTAS_CICLO[(self.indice_tonalidade + 1) % 12]
        if self.sentido == 'quintas':
            return [(seguinte, _t('uma quinta acima')), (anterior, _t('uma quarta acima'))]
        return [(anterior, _t('uma quarta acima')), (seguinte, _t('uma quinta acima'))]

    def inicializar(self, estado=None):
        self.inicializado = True
        self.gerar_pergunta()

    # --------------------------------------------------------------- desafio
    def gerar_pergunta(self):
        """Sorteia uma pergunta sobre a roda."""
        tipo = random.choice(['relativa', 'armadura', 'quinta', 'quarta'])
        idx = random.randrange(12)
        nota = NOTAS_CICLO[idx]

        if tipo == 'relativa':
            self.pergunta = f"{_t('Qual a relativa menor de')} {nota}?"
            self.resposta_correta = RELATIVAS[idx]
            universo = RELATIVAS
        elif tipo == 'armadura':
            self.pergunta = f"{_t('Qual a armadura de')} {nota} {_t('maior')}?"
            self.resposta_correta = ARMADURAS[idx]
            universo = ARMADURAS
        elif tipo == 'quinta':
            self.pergunta = f"{_t('Qual a quinta justa de')} {nota}?"
            self.resposta_correta = NOTAS_CICLO[(idx + 1) % 12]
            universo = NOTAS_CICLO
        else:
            self.pergunta = f"{_t('Qual a quarta justa de')} {nota}?"
            self.resposta_correta = NOTAS_CICLO[(idx - 1) % 12]
            universo = NOTAS_CICLO

        opcoes = [self.resposta_correta]
        while len(opcoes) < 4:
            candidato = random.choice(universo)
            if candidato not in opcoes:
                opcoes.append(candidato)
        random.shuffle(opcoes)
        self.opcoes = opcoes
        self.feedback = ''

    def responder(self, escolha):
        """Confere a resposta do desafio."""
        self.total += 1
        if escolha == self.resposta_correta:
            self.acertos += 1
            self.feedback = _t('Acertou!')
            self.cor_feedback = TEMA.verde
            self.gerar_pergunta()
        else:
            self.feedback = f"{_t('Era')} {self.resposta_correta}"
            self.cor_feedback = TEMA.alerta

    # ------------------------------------------------------------ sequencias
    def salvar_sequencia_atual(self):
        """Guarda a progressao montada como uma sequencia nomeada."""
        if not self.sequencia_atual:
            return False
        nome = f"{self.tonalidade} · {' - '.join(self.campo()[g]['romano'] for g in self.sequencia_atual)}"
        self.sequencias_custom.insert(0, {
            'nome': nome,
            'graus': list(self.sequencia_atual),
            'tonalidade': self.tonalidade,
            'tonal': self.tonal,
        })
        del self.sequencias_custom[12:]
        return self._salvar_sequencias()

    def carregar_sequencia(self, indice):
        """Traz uma sequencia salva de volta para o construtor."""
        if 0 <= indice < len(self.sequencias_custom):
            item = self.sequencias_custom[indice]
            self.sequencia_atual = list(item.get('graus', []))
            self.tonal = item.get('tonal', self.tonal)
            tonalidade = item.get('tonalidade')
            if tonalidade in NOTAS_CICLO:
                self.indice_tonalidade = NOTAS_CICLO.index(tonalidade)
            self.seq_selecionada = indice

    def avancar_sequencia(self, agora):
        """Anda um acorde da progressao no andamento escolhido."""
        if not (self.tocando and self.sequencia_atual):
            return
        intervalo = 60.0 / max(1, self.bpm) * 2   # dois tempos por acorde
        if agora - self.ultimo_passo >= intervalo:
            self.ultimo_passo = agora
            self.passo_sequencia = (self.passo_sequencia + 1) % len(self.sequencia_atual)

    # ------------------------------------------------------------- desenho --
    def _desenhar_roda(self, tela, centro, raio, fontes):
        """As doze tonalidades em circulo, maiores fora e menores dentro."""
        self.rects_roda = []
        raio_menor = raio * 0.62
        tam = max(24, int(raio * 0.19))

        # Arco indicando o sentido de leitura
        pygame.draw.circle(tela, ds.rgb(ds.misturar(TEMA.borda, TEMA.fundo, 0.4)),
                           centro, int(raio), 1)
        pygame.draw.circle(tela, ds.rgb(ds.misturar(TEMA.borda, TEMA.fundo, 0.5)),
                           centro, int(raio_menor), 1)

        for i in range(12):
            angulo = -math.pi / 2 + i * math.tau / 12
            cx = centro[0] + math.cos(angulo) * raio
            cy = centro[1] + math.sin(angulo) * raio
            rect = pygame.Rect(0, 0, tam * 2, tam * 2)
            rect.center = (int(cx), int(cy))
            self.rects_roda.append(rect)

            selecionada = i == self.indice_tonalidade % 12
            vizinha = abs((i - self.indice_tonalidade) % 12) in (1, 11)

            if selecionada:
                ds.gradiente_vertical(tela, rect, ds.clarear(TEMA.acento, 0.2),
                                      TEMA.acento, tam)
                cor_txt = TEMA.texto_sobre_cor
            elif vizinha:
                ds.superficie_translucida(tela, rect,
                                          ds.misturar(TEMA.superficie_alt, TEMA.ciano, 0.3),
                                          230, tam, TEMA.ciano, 1)
                cor_txt = TEMA.texto
            else:
                ds.superficie_translucida(tela, rect, TEMA.superficie_alt, 215,
                                          tam, TEMA.borda, 1)
                cor_txt = TEMA.texto_suave

            ds.texto_em(tela, NOTAS_CICLO[i], self._fonte(max(12, tam // 2)),
                        (rect.centerx, rect.centery - 5), cor_txt, ancora='center')
            ds.texto_em(tela, ARMADURAS[i], self._fonte(max(9, tam // 3)),
                        (rect.centerx, rect.centery + 9),
                        cor_txt if selecionada else TEMA.texto_apagado, ancora='center')

            # Relativa menor, no anel interno
            mx = centro[0] + math.cos(angulo) * raio_menor
            my = centro[1] + math.sin(angulo) * raio_menor
            ds.texto_em(tela, RELATIVAS[i], self._fonte(max(10, tam // 3)),
                        (int(mx), int(my)),
                        TEMA.acento if selecionada else TEMA.texto_apagado,
                        ancora='center')

        # Miolo: tonalidade escolhida
        miolo = pygame.Rect(0, 0, int(raio_menor * 1.05), int(raio_menor * 0.8))
        miolo.center = centro
        ds.superficie_translucida(tela, miolo, TEMA.superficie, 235, ds.RAIO_LG,
                                  TEMA.acento, 2)
        ds.texto_em(tela, self.tonalidade, self._fonte(30),
                    (miolo.centerx, miolo.y + 8), TEMA.acento, ancora='midtop')
        ds.texto_em(tela, f"{_t('relativa')} {self.relativa}", self._fonte(12),
                    (miolo.centerx, miolo.y + 46), TEMA.texto_suave, ancora='midtop')
        ds.texto_em(tela, f"{_t('armadura')} {self.armadura}", self._fonte(12),
                    (miolo.centerx, miolo.y + 64), TEMA.texto_apagado, ancora='midtop')

    def _desenhar_campo(self, tela, rect, fontes, clicavel=False):
        """Os sete graus da tonalidade, com romano, cifra e funcao."""
        graus = self.campo()
        self.rects_graus = []
        gap = ds.ESPACO_SM
        largura = (rect.width - gap * 6) / 7
        for i, grau in enumerate(graus):
            celula = pygame.Rect(int(rect.x + i * (largura + gap)), rect.y,
                                 int(largura), rect.height)
            self.rects_graus.append(celula)
            no_passo = (self.tocando and self.sequencia_atual
                        and self.sequencia_atual[self.passo_sequencia % len(self.sequencia_atual)] == i)
            if no_passo:
                ds.gradiente_vertical(tela, celula, ds.clarear(TEMA.aviso, 0.2),
                                      TEMA.aviso, ds.RAIO_MD)
                cor_txt = ds.contraste_texto(TEMA.aviso)
            else:
                cor_funcao = {'Tonica': TEMA.acento, 'Dominante': TEMA.alerta,
                              'Subdominante': TEMA.ciano}.get(grau['funcao'], TEMA.borda)
                ds.superficie_translucida(tela, celula,
                                          ds.misturar(TEMA.superficie_alt, cor_funcao, 0.22),
                                          225, ds.RAIO_MD, cor_funcao, 1)
                cor_txt = TEMA.texto
            ds.texto_em(tela, grau['romano'], self._fonte(12),
                        (celula.centerx, celula.y + 5), TEMA.texto_apagado, ancora='midtop')
            ds.texto_em(tela, grau['cifra'], self._fonte(17),
                        (celula.centerx, celula.centery + 2), cor_txt, ancora='center')
            if celula.height >= 60:
                ds.texto_em(tela, _t(grau['funcao'])[:12], self._fonte(10),
                            (celula.centerx, celula.bottom - 5), TEMA.texto_apagado,
                            ancora='midbottom')

    def _aba_roda(self, tela, rect, fontes):
        """Roda a esquerda, campo harmonico e vizinhas a direita."""
        largura_roda = min(rect.width * 0.44, rect.height * 1.05)
        raio = min(largura_roda, rect.height) * 0.40
        centro = (int(rect.x + largura_roda / 2), int(rect.y + rect.height / 2))
        self._desenhar_roda(tela, centro, raio, fontes)

        col = pygame.Rect(int(rect.x + largura_roda + ds.ESPACO_LG), rect.y,
                          int(rect.width - largura_roda - ds.ESPACO_LG), rect.height)
        y = col.y
        ds.rotulo_secao(tela, col.x, y, _t('Campo harmonico'), fontes['pequena'],
                        TEMA.acento, largura_max=col.width)
        y += fontes['pequena'].get_height() + ds.ESPACO_SM
        self._desenhar_campo(tela, pygame.Rect(col.x, y, col.width, 74), fontes)
        y += 74 + ds.ESPACO_LG

        ds.rotulo_secao(tela, col.x, y, _t('Tonalidades vizinhas'), fontes['pequena'],
                        TEMA.acento, largura_max=col.width)
        y += fontes['pequena'].get_height() + ds.ESPACO_SM
        for nota, explicacao in self.vizinhas():
            ds.texto_em(tela, nota, self._fonte(16), (col.x, y), TEMA.ciano)
            ds.texto_em(tela, explicacao, self._fonte(12), (col.x + 46, y + 3),
                        TEMA.texto_suave, largura_max=col.width - 50)
            y += 24
        y += ds.ESPACO_SM
        for linha in _quebrar(
                _t('Tonalidades vizinhas na roda diferem por uma nota so. E por isso '
                   'que modular para elas soa natural.'), self._fonte(11), col.width):
            ds.texto_em(tela, linha, self._fonte(11), (col.x, y), TEMA.texto_apagado)
            y += 14

    def _aba_sequencias(self, tela, rect, fontes):
        """Construtor de progressoes, biblioteca e sequencias salvas."""
        pos_mouse = pygame.mouse.get_pos()
        y = rect.y

        ds.rotulo_secao(tela, rect.x, y, _t('Clique nos graus para montar'),
                        fontes['pequena'], TEMA.acento, largura_max=rect.width)
        y += fontes['pequena'].get_height() + ds.ESPACO_SM
        self._desenhar_campo(tela, pygame.Rect(rect.x, y, rect.width, 74), fontes,
                             clicavel=True)
        y += 74 + ds.ESPACO_MD

        # Progressao montada
        faixa = pygame.Rect(rect.x, y, rect.width, 46)
        ds.superficie_translucida(tela, faixa, TEMA.superficie_alt, 215, ds.RAIO_MD,
                                  TEMA.borda, 1)
        if self.sequencia_atual:
            graus = self.campo()
            largura = min(78, faixa.width / max(1, len(self.sequencia_atual)))
            for i, indice in enumerate(self.sequencia_atual):
                celula = pygame.Rect(int(faixa.x + 6 + i * largura), faixa.y + 6,
                                     int(largura) - 4, faixa.height - 12)
                ativo = self.tocando and i == self.passo_sequencia % len(self.sequencia_atual)
                ds.superficie_translucida(tela, celula,
                                          TEMA.aviso if ativo else TEMA.superficie,
                                          230, ds.RAIO_SM,
                                          TEMA.aviso if ativo else TEMA.borda, 1)
                ds.texto_centralizado(tela, graus[indice]['cifra'], self._fonte(14),
                                      celula,
                                      ds.contraste_texto(TEMA.aviso) if ativo else TEMA.texto)
        else:
            ds.texto_centralizado(tela, _t('Nenhum acorde ainda'), self._fonte(12),
                                  faixa, TEMA.texto_apagado)
        y += 46 + ds.ESPACO_SM

        # Acoes
        self.rect_btn_tocar = pygame.Rect(rect.x, y, 96, 30)
        self.rect_btn_salvar = pygame.Rect(rect.x + 102, y, 96, 30)
        self.rect_btn_limpar = pygame.Rect(rect.x + 204, y, 96, 30)
        ds.botao(tela, self.rect_btn_tocar,
                 _t('Parar') if self.tocando else _t('Tocar'), self._fonte(12),
                 variante='perigo' if self.tocando else 'primario',
                 hover=self.rect_btn_tocar.collidepoint(pos_mouse))
        ds.botao(tela, self.rect_btn_salvar, _t('Salvar'), self._fonte(12),
                 variante='suave', habilitado=bool(self.sequencia_atual),
                 hover=self.rect_btn_salvar.collidepoint(pos_mouse))
        ds.botao(tela, self.rect_btn_limpar, _t('Limpar'), self._fonte(12),
                 variante='secundario', habilitado=bool(self.sequencia_atual),
                 hover=self.rect_btn_limpar.collidepoint(pos_mouse))
        y += 30 + ds.ESPACO_LG

        # Biblioteca e salvas, lado a lado
        meio = rect.width // 2 - ds.ESPACO_SM
        col_bib = pygame.Rect(rect.x, y, meio, rect.bottom - y)
        col_salvas = pygame.Rect(rect.x + meio + ds.ESPACO_LG, y,
                                 rect.width - meio - ds.ESPACO_LG, rect.bottom - y)

        ds.rotulo_secao(tela, col_bib.x, col_bib.y, _t('Progressoes classicas'),
                        fontes['pequena'], TEMA.acento, largura_max=col_bib.width)
        yb = col_bib.y + fontes['pequena'].get_height() + 4
        self.rects_biblioteca = []
        for item in BIBLIOTECA:
            if yb + 24 > col_bib.bottom:
                break
            r = pygame.Rect(col_bib.x, yb, col_bib.width, 22)
            self.rects_biblioteca.append(r)
            ds.texto_em(tela, _t(item['nome']), self._fonte(12),
                        (r.x, r.y), TEMA.texto_suave, largura_max=r.width * 0.55)
            ds.texto_em(tela, item['cifra'], self._fonte(11),
                        (r.right, r.y + 1), TEMA.ciano, ancora='topright',
                        largura_max=r.width * 0.45)
            yb += 24

        ds.rotulo_secao(tela, col_salvas.x, col_salvas.y, _t('Minhas sequencias'),
                        fontes['pequena'], TEMA.acento, largura_max=col_salvas.width)
        ys = col_salvas.y + fontes['pequena'].get_height() + 4
        self.rects_salvas = []
        if not self.sequencias_custom:
            ds.texto_em(tela, _t('Monte uma progressao e clique em Salvar'),
                        self._fonte(11), (col_salvas.x, ys), TEMA.texto_apagado,
                        largura_max=col_salvas.width)
        for item in self.sequencias_custom:
            if ys + 24 > col_salvas.bottom:
                break
            r = pygame.Rect(col_salvas.x, ys, col_salvas.width, 22)
            self.rects_salvas.append(r)
            ds.texto_em(tela, item.get('nome', '—'), self._fonte(12),
                        (r.x, r.y), TEMA.texto_suave, largura_max=r.width)
            ys += 24

    def _aba_desafio(self, tela, rect, fontes):
        """Pergunta, alternativas e placar."""
        pos_mouse = pygame.mouse.get_pos()
        ds.texto_em(tela, self.pergunta, self._fonte(22),
                    (rect.centerx, rect.y + 20), TEMA.texto, ancora='midtop',
                    largura_max=rect.width)

        self.rects_opcoes = []
        largura = min(220, (rect.width - ds.ESPACO_LG * 3) / 4)
        y = rect.y + 90
        for i, opcao in enumerate(self.opcoes):
            r = pygame.Rect(int(rect.centerx - (largura * 2 + ds.ESPACO_LG * 1.5)
                                + i * (largura + ds.ESPACO_LG)), y, int(largura), 52)
            self.rects_opcoes.append(r)
            ds.botao(tela, r, opcao, self._fonte(18), variante='secundario',
                     hover=r.collidepoint(pos_mouse))

        if self.feedback:
            ds.texto_em(tela, self.feedback, self._fonte(18),
                        (rect.centerx, y + 70), self.cor_feedback or TEMA.texto,
                        ancora='midtop')

        precisao = int(self.acertos / self.total * 100) if self.total else 0
        ds.texto_em(tela, f'{self.acertos}/{self.total}  ·  {precisao}%',
                    self._fonte(15), (rect.centerx, rect.bottom - 30),
                    TEMA.verde if precisao >= 70 else TEMA.texto_suave, ancora='midtop')

    def desenhar(self, tela, estado, fontes, meio_x, meio_y, cam_x, cam_y,
                 motor_audio=None):
        """
            Como funciona: Barra com abas, sentido e modo tonal, e o conteudo
            da aba escolhida.
            Para que serve: Tela do estudo do ciclo.
            Onde e usada: Chamada pelo gerenciador de estudos.
        """
        if not self.inicializado:
            self.inicializar(estado)
        import time
        self.avancar_sequencia(time.time())

        largura = getattr(estado, 'LARGURA_TELA', 1280)
        altura = getattr(estado, 'ALTURA_TELA', 720)
        area = pygame.Rect(int(cam_x + 40), int(cam_y + 56),
                           int(largura - 80), int(altura - 130))
        ds.painel(tela, area, None, None, acento=TEMA.acento, alpha=235)
        interno = area.inflate(-ds.ESPACO_XL * 2, -ds.ESPACO_XL * 2)
        pos_mouse = pygame.mouse.get_pos()

        # Barra superior
        self.rects_aba = []
        x = interno.x
        for i, nome in enumerate(ABAS):
            larg = self._fonte(13).size(_t(nome))[0] + 26
            r = pygame.Rect(x, interno.y, larg, 28)
            self.rects_aba.append(r)
            ds.chip(tela, r, _t(nome), self._fonte(13), ativo=i == self.aba)
            x += larg + 6

        self.rect_sentido = pygame.Rect(interno.right - 116, interno.y, 116, 28)
        ds.botao(tela, self.rect_sentido,
                 _t('Quintas') if self.sentido == 'quintas' else _t('Quartas'),
                 self._fonte(12), variante='suave',
                 hover=self.rect_sentido.collidepoint(pos_mouse))
        self.rect_tonal = pygame.Rect(self.rect_sentido.x - 106, interno.y, 100, 28)
        ds.botao(tela, self.rect_tonal,
                 _t('Maior') if self.tonal == 'maior' else _t('Menor'),
                 self._fonte(12), variante='secundario',
                 hover=self.rect_tonal.collidepoint(pos_mouse))

        conteudo = pygame.Rect(interno.x, interno.y + 40, interno.width,
                               interno.height - 40)
        if self.aba == 0:
            self._aba_roda(tela, conteudo, fontes)
        elif self.aba == 1:
            self._aba_sequencias(tela, conteudo, fontes)
        else:
            self._aba_desafio(tela, conteudo, fontes)

    # ------------------------------------------------------------- cliques --
    def tratar_cliques(self, pos, estado=None):
        """Trata abas, roda, graus, biblioteca, salvas e desafio."""
        for i, r in enumerate(self.rects_aba):
            if r.collidepoint(pos):
                self.aba = i
                return True
        if self.rect_sentido.collidepoint(pos):
            self.sentido = 'quartas' if self.sentido == 'quintas' else 'quintas'
            return True
        if self.rect_tonal.collidepoint(pos):
            self.tonal = 'menor' if self.tonal == 'maior' else 'maior'
            return True

        if self.aba == 0:
            for i, r in enumerate(self.rects_roda):
                if r.collidepoint(pos):
                    self.indice_tonalidade = i
                    return True

        elif self.aba == 1:
            for i, r in enumerate(self.rects_graus):
                if r.collidepoint(pos):
                    self.sequencia_atual.append(i)
                    del self.sequencia_atual[16:]
                    return True
            if self.rect_btn_tocar.collidepoint(pos):
                self.tocando = not self.tocando
                self.passo_sequencia = 0
                import time
                self.ultimo_passo = time.time()
                return True
            if self.rect_btn_salvar.collidepoint(pos):
                self.salvar_sequencia_atual()
                return True
            if self.rect_btn_limpar.collidepoint(pos):
                self.sequencia_atual.clear()
                self.tocando = False
                return True
            for i, r in enumerate(self.rects_biblioteca):
                if r.collidepoint(pos):
                    item = BIBLIOTECA[i]
                    self.sequencia_atual = list(item['graus'])
                    if item.get('tonal'):
                        self.tonal = item['tonal']
                    return True
            for i, r in enumerate(self.rects_salvas):
                if r.collidepoint(pos):
                    self.carregar_sequencia(i)
                    return True

        else:
            for i, r in enumerate(self.rects_opcoes):
                if r.collidepoint(pos):
                    self.responder(self.opcoes[i])
                    return True
        return False

    def tratar_eventos(self, evento, pos, estado=None):
        """Compatibilidade com o gerenciador de estudos."""
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            return self.tratar_cliques(pos, estado)
        return False


def _quebrar(texto, fonte, largura_max):
    """Quebra o texto em linhas que cabem na largura."""
    palavras, linhas, atual = texto.split(' '), [], ''
    for palavra in palavras:
        teste = f'{atual} {palavra}'.strip()
        if fonte.size(teste)[0] <= largura_max:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas
