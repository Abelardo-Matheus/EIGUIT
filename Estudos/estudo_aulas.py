# -*- coding: utf-8 -*-
"""
Aulas: trilha guiada de Improvisacao e Padroes Melodicos, do iniciante ao
avancado.

Cada aula abre um dos motores ja existentes (EstudoPadroes ou
EstudoImprovisacao), ja configurado com os presets do curriculo, com uma
faixa no topo explicando o que fazer e um botao para marcar a aula como
concluida. Os motores continuam completos (o aluno pode trocar tonica,
escala, instrumento etc. se quiser explorar); a "simplificacao" da aula
esta em chegar la ja com tudo ajustado e uma explicacao curta, em vez de
um painel vazio com varios controles para decidir sozinho.

Navegacao em tres telas dentro do mesmo painel:
    niveis -> lista de aulas do nivel -> aula em pratica (faixa + motor)
'Voltar' sobe uma tela; ESC (tratado pelo gerenciador de estudos) sai do
estudo por completo, como em qualquer outro modulo.
"""
import json
import os
import time

import pygame

from config.design_system import TEMA, ds
from core.i18n import _t
from Estudos import curriculo_aulas as curriculo
from Estudos.estudo_padroes import EstudoPadroes, DIRECOES
from Estudos.estudo_improvisacao import EstudoImprovisacao


def _caminho_progresso(estado):
    """Onde fica o progresso salvo (um arquivo por usuario logado)."""
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pasta = os.path.join(raiz, 'Perfis')
    try:
        os.makedirs(pasta, exist_ok=True)
    except Exception:
        pass
    usuario = getattr(estado, 'usuario_id_logado', None) or 'local'
    return os.path.join(pasta, f'progresso_aulas_{usuario}.json')


def _quebrar(texto, fonte, largura_max):
    """Quebra o texto em linhas que cabem na largura, palavra a palavra."""
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


class EstudoAulas:
    """
        Como funciona: tela com tres estados (niveis, lista de aulas, aula em
        pratica) que reaproveita EstudoPadroes/EstudoImprovisacao ja
        configurados para cada licao, com uma faixa de explicacao no topo.
        Para que serve: dar uma ordem de estudo (basico a avancado) aos dois
        motores de pratica, com treinos simplificados por preset.
        Onde e usada: aba Estudos, secao Aulas.
    """

    def __init__(self):
        self.vista = 'niveis'          # 'niveis' | 'lista' | 'pratica'
        self.indice_nivel = 0
        self.indice_aula = 0
        self.motor_padroes = EstudoPadroes()
        self.motor_improviso = EstudoImprovisacao()
        self.tempo_praticado = 0.0
        self._ultimo_tick = 0.0
        self.progresso = set()
        self._progresso_carregado_para = None

        self._fontes = {}
        self.rects_niveis = []
        self.rects_aulas = []
        self.rect_voltar = pygame.Rect(0, 0, 0, 0)
        self.rect_concluir = pygame.Rect(0, 0, 0, 0)
        self.rect_iniciar = pygame.Rect(0, 0, 0, 0)

    # ----------------------------------------------------------- recursos --
    def _fonte(self, tamanho, negrito=True):
        chave = (tamanho, negrito)
        if chave not in self._fontes:
            self._fontes[chave] = pygame.font.SysFont('Arial', tamanho, bold=negrito)
        return self._fontes[chave]

    def _garantir_progresso(self, estado):
        caminho = _caminho_progresso(estado)
        if self._progresso_carregado_para == caminho:
            return
        self._progresso_carregado_para = caminho
        self.progresso = set()
        try:
            if os.path.exists(caminho):
                with open(caminho, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                self.progresso = set(dados.get('concluidas', []))
        except Exception:
            self.progresso = set()

    def _salvar_progresso(self, estado):
        caminho = _caminho_progresso(estado)
        try:
            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump({'concluidas': sorted(self.progresso)}, f, indent=2)
        except Exception:
            pass

    # ------------------------------------------------------------ estado --
    @property
    def nivel(self):
        return curriculo.NIVEIS[self.indice_nivel % len(curriculo.NIVEIS)]

    @property
    def aula(self):
        aulas = self.nivel['aulas']
        return aulas[self.indice_aula % len(aulas)]

    def _nivel_concluido(self, nivel):
        return all(a['id'] in self.progresso for a in nivel['aulas'])

    def _nivel_desbloqueado(self, indice):
        """Nivel 0 sempre abre; os seguintes pedem metade do anterior feita."""
        if indice == 0:
            return True
        anterior = curriculo.NIVEIS[indice - 1]
        feitas = sum(1 for a in anterior['aulas'] if a['id'] in self.progresso)
        return feitas >= max(1, len(anterior['aulas']) // 2)

    def _cor(self, nome_cor):
        return {'verde': TEMA.verde, 'ciano': TEMA.ciano,
                'aviso': TEMA.aviso}.get(nome_cor, TEMA.acento)

    def _motor_atual(self):
        return self.motor_padroes if self.aula['tipo'] in ('padrao', 'ritmo') \
            else self.motor_improviso

    def tocando_motor(self):
        return bool(getattr(self._motor_atual(), 'tocando', False))

    # ------------------------------------------------------- configuracao --
    def _abrir_aula(self, estado, indice_nivel, indice_aula):
        """Configura o motor certo com o preset da aula e entra na pratica."""
        self.indice_nivel = indice_nivel
        self.indice_aula = indice_aula
        aula = self.aula
        preset = aula['preset']

        if aula['tipo'] == 'padrao':
            m = self.motor_padroes
            m.modo = 0
            m.tonica = preset['tonica']
            m.chave_escala = preset['escala']
            m.indice_padrao = curriculo.indice_padrao_por_nome(preset['padrao'])
            m.indice_direcao = DIRECOES.index(preset.get('direcao', 'Ascendente'))
            m.instrumento = preset.get('instrumento', 'guitarra')
            m.bpm = preset.get('bpm', 70)
            m.tocando = False
            m.preparar()
        elif aula['tipo'] == 'ritmo':
            m = self.motor_padroes
            m.modo = 1
            m.indice_ritmo = curriculo.indice_ritmo_por_nome(preset['ritmo'])
            m.instrumento = preset.get('instrumento', 'guitarra')
            m.bpm = preset.get('bpm', 80)
            m.tocando = False
        else:  # 'improviso'
            m = self.motor_improviso
            m.tonica = preset['tonica']
            m.indice_progressao = curriculo.indice_progressao_por_nome(preset['progressao'])
            m.indice_modo = curriculo.indice_modo_por_nome(preset['modo'])
            m.instrumento = preset.get('instrumento', 'guitarra')
            m.bpm = preset.get('bpm', 80)
            m.tocando = False

        self.tempo_praticado = 0.0
        self._ultimo_tick = 0.0
        self.vista = 'pratica'

    def _atualizar_tempo_praticado(self):
        agora = time.time()
        if self._ultimo_tick == 0.0:
            self._ultimo_tick = agora
            return
        dt = agora - self._ultimo_tick
        self._ultimo_tick = agora
        if self.tocando_motor() and 0 < dt < 1.0:
            self.tempo_praticado += dt

    # ----------------------------------------------------------- desenho --
    def _desenhar_niveis(self, tela, area, fontes):
        """Tres cartoes de nivel, com barra de progresso e cadeado se travado."""
        ds.texto_em(tela, _t('Aulas: Improvisacao e Padroes Melodicos'),
                    fontes['titulo'], (area.x, area.y), TEMA.acento,
                    largura_max=area.width)
        y = area.y + fontes['titulo'].get_height() + 8
        ds.texto_em(tela, _t('Uma trilha guiada, do iniciante ao avancado. '
                              'Escolha um nivel para ver as aulas.'),
                    self._fonte(13, False), (area.x, y), TEMA.texto_suave,
                    largura_max=area.width)
        y += 30

        self.rects_niveis = []
        altura_card = min(150, max(90, (area.bottom - y - 16) // max(1, len(curriculo.NIVEIS))))
        for i, nivel in enumerate(curriculo.NIVEIS):
            r = pygame.Rect(area.x, y, area.width, altura_card - 14)
            self.rects_niveis.append(r)
            cor = self._cor(nivel['cor'])
            desbloqueado = self._nivel_desbloqueado(i)
            concluidas = sum(1 for a in nivel['aulas'] if a['id'] in self.progresso)
            total = len(nivel['aulas'])

            ds.superficie_translucida(tela, r, TEMA.superficie_alt, 225, ds.RAIO_MD,
                                      cor if desbloqueado else TEMA.borda, 2)
            pad = ds.ESPACO_MD
            cor_titulo = cor if desbloqueado else TEMA.texto_apagado
            rotulo = f"{i + 1}. {_t(nivel['nome'])}"
            if not desbloqueado:
                rotulo = f"[{_t('Bloqueado')}] {rotulo}"
            ds.texto_em(tela, rotulo, self._fonte(18), (r.x + pad, r.y + pad), cor_titulo)
            ds.texto_em(tela, _t(nivel['subtitulo']), self._fonte(12),
                        (r.x + pad, r.y + pad + 25), TEMA.texto)
            ds.texto_em(tela, _t(nivel['descricao']), self._fonte(11, False),
                        (r.x + pad, r.y + pad + 45), TEMA.texto_suave,
                        largura_max=r.width - pad * 2 - 160)

            largura_barra = 150
            rect_barra = pygame.Rect(r.right - largura_barra - pad, r.y + pad + 6,
                                     largura_barra, 10)
            ds.trilho(tela, rect_barra, concluidas / max(1, total), cor)
            ds.texto_centralizado(tela, f'{concluidas}/{total}', self._fonte(11),
                                  pygame.Rect(rect_barra.x, rect_barra.bottom + 4,
                                             rect_barra.width, 16), TEMA.texto_suave)
            if self._nivel_concluido(nivel):
                ds.selo(tela, (r.right - pad, r.bottom - pad), _t('Concluido'),
                       self._fonte(10), TEMA.verde, ancora='bottomright')
            elif not desbloqueado:
                ds.texto_em(tela, _t('Complete metade do nivel anterior para desbloquear'),
                           self._fonte(10, False), (r.x + pad, r.bottom - 20),
                           TEMA.texto_apagado, largura_max=r.width - pad * 2)
            y += altura_card

    def _desenhar_lista(self, tela, area, fontes):
        """Lista de aulas do nivel escolhido, com marca de concluida."""
        nivel = self.nivel
        cor = self._cor(nivel['cor'])
        ds.texto_em(tela, f"{_t(nivel['nome'])}: {_t(nivel['subtitulo'])}",
                    fontes['titulo'], (area.x, area.y), cor, largura_max=area.width - 130)
        y = area.y + fontes['titulo'].get_height() + 16

        self.rects_aulas = []
        n = max(1, len(nivel['aulas']))
        altura_item = min(64, max(46, (area.bottom - y - 8) // n))
        for i, aula in enumerate(nivel['aulas']):
            r = pygame.Rect(area.x, y, area.width, altura_item - 8)
            self.rects_aulas.append(r)
            concluida = aula['id'] in self.progresso
            cor_borda = TEMA.verde if concluida else cor
            ds.superficie_translucida(tela, r, TEMA.superficie_alt, 210, ds.RAIO_SM,
                                      cor_borda, 1)
            marca = 'OK' if concluida else str(i + 1)
            ds.texto_em(tela, marca, self._fonte(14), (r.x + 14, r.centery),
                       TEMA.verde if concluida else TEMA.texto_suave, ancora='midleft')
            ds.texto_em(tela, _t(aula['titulo']), self._fonte(14),
                       (r.x + 46, r.y + 8), TEMA.texto, largura_max=r.width - 60)
            ds.texto_em(tela, _t(aula['objetivo']), self._fonte(11, False),
                       (r.x + 46, r.y + 30), TEMA.texto_suave, largura_max=r.width - 60)
            y += altura_item

    def _desenhar_banner(self, tela, area, fontes):
        """Faixa fixa no topo da pratica: titulo, explicacao curta e acoes."""
        aula = self.aula
        nivel = self.nivel
        cor = self._cor(nivel['cor'])
        pos_mouse = pygame.mouse.get_pos()

        ds.superficie_translucida(tela, area, TEMA.superficie_alt, 235, ds.RAIO_MD, cor, 2)
        pad = ds.ESPACO_MD
        largura_texto = max(120, area.width - 380)
        ds.texto_em(tela, _t(aula['titulo']), self._fonte(16), (area.x + pad, area.y + 8),
                   cor, largura_max=largura_texto)
        linhas = _quebrar(_t(aula['explicacao']), self._fonte(11, False), largura_texto)
        for i, linha in enumerate(linhas[:3]):
            ds.texto_em(tela, linha, self._fonte(11, False),
                       (area.x + pad, area.y + 32 + i * 14), TEMA.texto_suave,
                       largura_max=largura_texto)
        ds.texto_em(tela, f"{_t('Objetivo')}: {_t(aula['objetivo'])}", self._fonte(11),
                   (area.x + pad, area.bottom - 18), TEMA.aviso, largura_max=largura_texto)

        largura_btn = 118
        self.rect_voltar = pygame.Rect(area.right - largura_btn * 3 - 16, area.y + 10,
                                       largura_btn, 26)
        ds.botao(tela, self.rect_voltar, _t('Voltar'), self._fonte(11), variante='secundario',
                hover=self.rect_voltar.collidepoint(pos_mouse))

        concluida = aula['id'] in self.progresso
        self.rect_concluir = pygame.Rect(area.right - largura_btn * 2 - 8, area.y + 10,
                                         largura_btn, 26)
        ds.botao(tela, self.rect_concluir,
                _t('Concluida OK') if concluida else _t('Concluir aula'), self._fonte(11),
                variante='secundario' if concluida else 'sucesso',
                hover=self.rect_concluir.collidepoint(pos_mouse))

        aulas_nivel = self.nivel['aulas']
        proxima_existe = self.indice_aula + 1 < len(aulas_nivel)
        self.rect_iniciar = pygame.Rect(area.right - largura_btn, area.y + 10,
                                        largura_btn, 26)
        ds.botao(tela, self.rect_iniciar,
                _t('Proxima aula') if proxima_existe else _t('Fim do nivel'),
                self._fonte(11), variante='primario' if proxima_existe else 'secundario',
                hover=self.rect_iniciar.collidepoint(pos_mouse))

        if self.tempo_praticado > 0:
            segundos = int(self.tempo_praticado)
            ds.texto_em(tela, f"{_t('Tempo praticado')}: {segundos}s", self._fonte(10, False),
                       (area.right - pad, area.bottom - 8), TEMA.texto_apagado,
                       ancora='bottomright')

    # -------------------------------------------------------------- API ---
    def desenhar(self, tela, estado, fontes, meio_x, meio_y, cam_x, cam_y):
        """
            Como funciona: escolhe a vista atual (niveis, lista ou pratica) e
            desenha; na pratica, sobrepoe uma faixa de explicacao e encolhe a
            area repassada ao motor (Padroes/Improvisacao) para caber abaixo
            dela, restaurando ALTURA_TELA logo em seguida.
            Para que serve: tela principal da trilha de Aulas.
            Onde e usada: chamada pelo gerenciador de estudos.
        """
        self._garantir_progresso(estado)
        largura = getattr(estado, 'LARGURA_TELA', 1280)
        altura = getattr(estado, 'ALTURA_TELA', 720)

        if self.vista == 'niveis':
            area = pygame.Rect(int(cam_x + 40), int(cam_y + 56),
                               int(largura - 80), int(altura - 130))
            ds.painel(tela, area, None, None, acento=TEMA.acento, alpha=235)
            interno = area.inflate(-ds.ESPACO_XL * 2, -ds.ESPACO_XL * 2)
            self._desenhar_niveis(tela, interno, fontes)

        elif self.vista == 'lista':
            area = pygame.Rect(int(cam_x + 40), int(cam_y + 56),
                               int(largura - 80), int(altura - 130))
            ds.painel(tela, area, None, None, acento=self._cor(self.nivel['cor']), alpha=235)
            interno = area.inflate(-ds.ESPACO_XL * 2, -ds.ESPACO_XL * 2)
            self._desenhar_lista(tela, interno, fontes)
            pos_mouse = pygame.mouse.get_pos()
            self.rect_voltar = pygame.Rect(area.right - 118 - ds.ESPACO_XL, area.y + 10, 118, 26)
            ds.botao(tela, self.rect_voltar, _t('Voltar'), self._fonte(11),
                    variante='secundario', hover=self.rect_voltar.collidepoint(pos_mouse))

        else:  # 'pratica'
            self._atualizar_tempo_praticado()
            # A faixa comeca na mesma altura (cam_y + 56) que o painel do
            # modo livre usa, para nao brigar com o titulo que o gerenciador
            # de estudos ja desenha em cam_y + 10.
            banner_h = 114
            folga = 16
            area_banner = pygame.Rect(int(cam_x + 40), int(cam_y + 56),
                                      int(largura - 80), banner_h)
            self._desenhar_banner(tela, area_banner, fontes)

            # Repassa a mesma area de sempre ao motor, so que empurrada para
            # baixo da faixa e com a altura visivel reduzida na mesma medida,
            # para o painel do motor nao ultrapassar o rodape da tela.
            altura_original = getattr(estado, 'ALTURA_TELA', altura)
            deslocamento = banner_h + folga
            try:
                estado.ALTURA_TELA = altura_original - deslocamento
                motor = self._motor_atual()
                motor_audio = getattr(estado, 'motor_audio', None)
                motor.desenhar(tela, estado, fontes, meio_x, meio_y,
                               cam_x, cam_y + deslocamento, motor_audio)
            finally:
                estado.ALTURA_TELA = altura_original

    # ------------------------------------------------------------- clique --
    def tratar_cliques(self, pos, estado):
        """Trata cliques de acordo com a vista atual."""
        if self.vista == 'niveis':
            for i, r in enumerate(self.rects_niveis):
                if r.collidepoint(pos) and self._nivel_desbloqueado(i):
                    self.indice_nivel = i
                    self.vista = 'lista'
                    return True
            return False

        if self.vista == 'lista':
            if self.rect_voltar.collidepoint(pos):
                self.vista = 'niveis'
                return True
            for i, r in enumerate(self.rects_aulas):
                if r.collidepoint(pos):
                    self._abrir_aula(estado, self.indice_nivel, i)
                    return True
            return False

        # vista == 'pratica'
        if self.rect_voltar.collidepoint(pos):
            self._motor_atual().tocando = False
            self.vista = 'lista'
            return True
        if self.rect_concluir.collidepoint(pos):
            self.progresso.add(self.aula['id'])
            self._salvar_progresso(estado)
            return True
        if self.rect_iniciar.collidepoint(pos):
            aulas_nivel = self.nivel['aulas']
            if self.indice_aula + 1 < len(aulas_nivel):
                self._abrir_aula(estado, self.indice_nivel, self.indice_aula + 1)
            else:
                self.vista = 'lista'
            return True
        motor = self._motor_atual()
        if hasattr(motor, 'tratar_cliques'):
            return motor.tratar_cliques(pos, estado)
        return False

    def tratar_eventos(self, evento, pos, estado):
        """Ponto de entrada usado pelo gerenciador de estudos."""
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            return self.tratar_cliques(pos, estado)
        return False
