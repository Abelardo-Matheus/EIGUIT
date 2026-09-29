# -*- coding: utf-8 -*-
"""
Estudo de Pedais de Efeito.

Duas telas no mesmo painel:
    lista -> todos os pedais, agrupados do mais simples ao mais complexo
    pedal -> o pedal desenhado (knobs, LED e footswitch), a explicacao do que
             ele faz, um slider por parametro com a explicacao de cada um e o
             audio de exemplo tocando em loop.

O audio e sintetizado na hora por audio/efeitos_pedais.py. Toda vez que um
parametro muda, o loop e recalculado numa thread e trocado no ar, a partir do
mesmo ponto em que estava tocando, entao da para ficar ouvindo e mexendo nos
botoes como num pedal de verdade. O botao Ligado/Desligado (ou o footswitch
desenhado) compara o som com e sem o efeito.

ESC (tratado pelo gerenciador de estudos) sai do estudo e para o audio.
"""
import math
import threading
import time

import numpy as np
import pygame

from audio import efeitos_pedais as motor
from config.design_system import TEMA, ds
from core.i18n import _t
from Estudos import curriculo_pedais as cur

CANAIS_RESERVADOS = (62, 63)      # dois canais para trocar o loop com fade
FADE_MS = 40


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


def _texto_bloco(tela, texto, fonte, x, y, largura, cor, max_linhas=None, entrelinha=4):
    """Desenha um paragrafo quebrado; devolve o Y logo abaixo dele."""
    linhas = _quebrar(texto, fonte, largura)
    if max_linhas is not None and len(linhas) > max_linhas:
        linhas = linhas[:max(0, max_linhas)]
        if linhas:
            linhas[-1] = ds.truncar(linhas[-1] + ' ...', fonte, largura)
    altura = fonte.get_height() + entrelinha
    for i, linha in enumerate(linhas):
        ds.texto_em(tela, linha, fonte, (x, y + i * altura), cor)
    return y + len(linhas) * altura


# ===========================================================================
# REPRODUTOR: renderiza em thread e troca o loop sem perder a posicao
# ===========================================================================

class ReprodutorLoop:
    """
        Como funciona: guarda o ultimo pedido de renderizacao, calcula numa
        thread (numpy) e, quando fica pronto, cria o Sound na thread principal
        e troca de canal com fade, girando o audio para continuar do ponto
        atual do loop.
        Para que serve: permitir ouvir o efeito mudando enquanto o aluno mexe
        nos parametros, sem travar a interface.
        Onde e usada: EstudoPedais.
    """

    def __init__(self):
        self.tocando = False
        self.sr = motor.SR_PADRAO
        self.canais_mixer = 2
        self.canais = []
        self.canal_ativo = 0
        self.inicio = 0.0
        self.duracao = motor.DURACAO_LOOP
        self.audio = None                 # float32 (N, 2) do loop atual
        self.forma = np.zeros(300)
        self._pedido = None
        self._pedido_id = 0
        self._pronto = None
        self._trabalhando = False
        self._lock = threading.Lock()
        self._cache = {}
        self._iniciar_mixer()
        # sintetiza os audios base em segundo plano: o primeiro pedal ja abre rapido
        threading.Thread(target=self._aquecer_bases, daemon=True).start()

    def _aquecer_bases(self):
        for chave in motor.ORDEM_BASES:
            try:
                motor.gerar_base(chave, self.sr)
            except Exception:
                pass

    def _iniciar_mixer(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 2, 512)
            freq, _tam, canais = pygame.mixer.get_init()
            self.sr, self.canais_mixer = int(freq), int(canais)
            if pygame.mixer.get_num_channels() <= max(CANAIS_RESERVADOS):
                pygame.mixer.set_num_channels(max(CANAIS_RESERVADOS) + 1)
            self.canais = [pygame.mixer.Channel(i) for i in CANAIS_RESERVADOS]
        except Exception:
            self.canais = []

    # ------------------------------------------------------------ pedidos --
    def pedir(self, chave_efeito, params, chave_base, ligado):
        """Registra o que deve tocar agora; so o pedido mais novo vale."""
        chave = (chave_efeito, chave_base, bool(ligado),
                 tuple(sorted((k, round(float(v), 4)) for k, v in params.items())))
        with self._lock:
            if chave in self._cache:
                self._pronto = (chave, self._cache[chave])
                self._pedido = None
                return
            self._pedido_id += 1
            self._pedido = (self._pedido_id, chave, chave_efeito, dict(params),
                            chave_base, bool(ligado))
        self._disparar()

    def _disparar(self):
        with self._lock:
            if self._trabalhando or self._pedido is None:
                return
            pedido = self._pedido
            self._pedido = None
            self._trabalhando = True
        threading.Thread(target=self._trabalhar, args=(pedido,), daemon=True).start()

    def _trabalhar(self, pedido):
        _id, chave, efeito, params, base, ligado = pedido
        try:
            audio = motor.renderizar(efeito, params, base, ligado, self.sr)
        except Exception as erro:          # nunca derruba a interface
            print(f'[PEDAIS] erro ao renderizar {efeito}: {erro}')
            audio = None
        with self._lock:
            self._trabalhando = False
            if audio is not None:
                self._cache[chave] = audio
                if len(self._cache) > 12:
                    self._cache.pop(next(iter(self._cache)))
                self._pronto = (chave, audio)
        self._disparar()                   # se chegou outro pedido no meio

    def ocupado(self):
        with self._lock:
            return self._trabalhando or self._pedido is not None

    def aguardar(self, limite=5.0):
        """Espera a renderizacao pendente (usado pelas suites de teste)."""
        fim = time.time() + limite
        while self.ocupado() and time.time() < fim:
            time.sleep(0.01)
        self.atualizar()

    # ------------------------------------------------------------ quadro ---
    def atualizar(self):
        """Chamado todo quadro: aplica o audio que ficou pronto."""
        with self._lock:
            pronto = self._pronto
            self._pronto = None
        if pronto is None:
            return
        _chave, audio = pronto
        self.audio = audio
        self.duracao = audio.shape[0] / float(self.sr)
        self.forma = motor.forma_de_onda(audio, 300)
        if self.tocando:
            self._tocar_do_ponto_atual()

    def posicao(self):
        """Fracao (0..1) do loop que esta tocando agora."""
        if not self.tocando or self.duracao <= 0:
            return 0.0
        return ((time.time() - self.inicio) % self.duracao) / self.duracao

    def _tocar_do_ponto_atual(self):
        if self.audio is None or not self.canais:
            return
        deslocamento = self.posicao() if self.inicio else 0.0
        amostra = int(deslocamento * self.audio.shape[0])
        girado = np.roll(self.audio, -amostra, axis=0)
        try:
            som = pygame.sndarray.make_sound(motor.para_int16(girado, self.canais_mixer))
        except Exception:
            try:
                som = pygame.mixer.Sound(buffer=motor.para_int16(girado, self.canais_mixer).tobytes())
            except Exception:
                return
        antigo = self.canais[self.canal_ativo]
        self.canal_ativo = 1 - self.canal_ativo
        novo = self.canais[self.canal_ativo]
        try:
            novo.play(som, loops=-1, fade_ms=FADE_MS)
            antigo.fadeout(FADE_MS)
        except Exception:
            pass
        self.inicio = time.time() - deslocamento * self.duracao

    def tocar(self):
        self.tocando = True
        self.inicio = 0.0
        self._tocar_do_ponto_atual()
        self.inicio = time.time()

    def parar(self):
        self.tocando = False
        for canal in self.canais:
            try:
                canal.fadeout(FADE_MS)
            except Exception:
                pass


# ===========================================================================
# ESTUDO
# ===========================================================================

class EstudoPedais:
    """
        Como funciona: tela com duas vistas (lista de pedais e pedal aberto).
        No pedal aberto, cada parametro tem um slider e um knob no desenho do
        pedal; qualquer mudanca pede um novo loop ao ReprodutorLoop.
        Para que serve: ensinar o que cada pedal de efeito faz e o que cada
        botao dele muda, ouvindo o resultado na hora.
        Onde e usada: aba Estudos, secao Pedais.
    """

    def __init__(self):
        self.vista = 'lista'               # 'lista' | 'pedal'
        self.pedal = cur.PEDAIS[0]
        self.valores = cur.valores_padrao(self.pedal)
        self.base = self.pedal['base']
        self.ligado = True
        self.param_foco = 0
        self.exemplo_ativo = None
        self.reprodutor = ReprodutorLoop()

        self.scroll_lista = 0
        self.altura_conteudo_lista = 0
        self.altura_visivel_lista = 0

        self._fontes = {}
        self.rects_pedais = []             # (rect, pedal)
        self.rects_sliders = []            # (rect_barra, indice)
        self.rects_linhas_param = []       # (rect, indice)
        self.rects_knobs = []              # (rect, indice)
        self.rects_bases = []
        self.rects_exemplos = []
        self.rect_voltar = pygame.Rect(0, 0, 0, 0)
        self.rect_play = pygame.Rect(0, 0, 0, 0)
        self.rect_bypass = pygame.Rect(0, 0, 0, 0)
        self.rect_footswitch = pygame.Rect(0, 0, 0, 0)
        self.rect_reset = pygame.Rect(0, 0, 0, 0)
        self.rect_anterior = pygame.Rect(0, 0, 0, 0)
        self.rect_proximo = pygame.Rect(0, 0, 0, 0)
        self.rect_lista = pygame.Rect(0, 0, 0, 0)

        self.arrastando = None             # ('slider', i) | ('knob', i, y0, v0)
        self._ultimo_pedido = 0.0
        self._mudou = False

    # ----------------------------------------------------------- recursos --
    def _fonte(self, tamanho, negrito=True):
        chave = (tamanho, negrito)
        if chave not in self._fontes:
            self._fontes[chave] = pygame.font.SysFont('Arial', tamanho, bold=negrito)
        return self._fontes[chave]

    # ------------------------------------------------------------- valores --
    @property
    def parametros(self):
        return self.pedal['parametros']

    def _pct(self, par, valor):
        """Posicao 0..1 do valor no slider (por indice, se tiver opcoes)."""
        if par.get('opcoes'):
            valores = [v for v, _ in par['opcoes']]
            idx = min(range(len(valores)), key=lambda i: abs(valores[i] - valor))
            return idx / max(1, len(valores) - 1)
        faixa = (par['max'] - par['min']) or 1
        return (valor - par['min']) / faixa

    def _valor_do_pct(self, par, pct):
        pct = max(0.0, min(1.0, pct))
        if par.get('opcoes'):
            valores = [v for v, _ in par['opcoes']]
            return valores[int(round(pct * (len(valores) - 1)))]
        valor = par['min'] + pct * (par['max'] - par['min'])
        if par['unidade'] != '%':
            passo = 10 ** (-par['casas'])
            valor = round(valor / passo) * passo
        return valor

    def definir_valor(self, indice, valor):
        par = self.parametros[indice]
        valor = max(par['min'], min(par['max'], valor))
        if abs(self.valores.get(par['id'], 0) - valor) > 1e-9:
            self.valores[par['id']] = valor
            self.exemplo_ativo = None
            self._mudou = True
        self.param_foco = indice

    def _pedir_audio(self, forcar=False):
        agora = time.time()
        if forcar or agora - self._ultimo_pedido > 0.09:
            self._ultimo_pedido = agora
            self._mudou = False
            self.reprodutor.pedir(self.pedal['id'], self.valores, self.base, self.ligado)

    # ------------------------------------------------------------ acoes ----
    def abrir_pedal(self, pedal):
        self.pedal = pedal
        self.valores = cur.valores_padrao(pedal)
        self.base = pedal['base']
        self.ligado = True
        self.param_foco = 0
        self.exemplo_ativo = None
        self.arrastando = None
        self.vista = 'pedal'
        self._pedir_audio(forcar=True)

    def _vizinho(self, passo):
        i = cur.PEDAIS.index(self.pedal)
        self.abrir_pedal(cur.PEDAIS[(i + passo) % len(cur.PEDAIS)])  # continua tocando

    def aplicar_exemplo(self, indice):
        nome, valores = self.pedal['exemplos'][indice]
        self.valores = cur.valores_padrao(self.pedal)
        self.valores.update(valores)
        self.exemplo_ativo = indice
        self.ligado = True
        self._pedir_audio(forcar=True)

    def alternar_play(self):
        if self.reprodutor.tocando:
            self.reprodutor.parar()
        else:
            self.reprodutor.tocar()

    def alternar_bypass(self):
        self.ligado = not self.ligado
        self._pedir_audio(forcar=True)

    def parar(self):
        """Chamado ao sair do estudo: nada pode continuar tocando."""
        self.reprodutor.parar()

    # =================================================================
    # DESENHO: LISTA
    # =================================================================
    def _desenhar_lista(self, tela, area, fontes):
        ds.painel(tela, area, None, None, acento=TEMA.acento, alpha=235)
        interno = area.inflate(-ds.ESPACO_XL * 2, -ds.ESPACO_XL * 2)
        pos_mouse = pygame.mouse.get_pos()

        ds.texto_em(tela, _t('Pedais de Efeito'), fontes['titulo'],
                    (interno.x, interno.y), TEMA.acento, largura_max=interno.width)
        y = interno.y + fontes['titulo'].get_height() + 6
        y = _texto_bloco(tela, _t(cur.INTRODUCAO), self._fonte(13, False), interno.x, y,
                         interno.width, TEMA.texto_suave, max_linhas=2) + 6

        # cadeia de sinal sugerida
        fonte_chip = self._fonte(11)
        x = interno.x
        ds.texto_em(tela, _t('Ordem comum na pedaleira') + ':', fonte_chip,
                    (x, y + 11), TEMA.texto_apagado, ancora='midleft')
        x += fonte_chip.size(_t('Ordem comum na pedaleira') + ':')[0] + 10
        for i, etapa in enumerate(cur.CADEIA_SUGERIDA):
            w = fonte_chip.size(_t(etapa))[0] + 18
            if x + w > interno.right:
                break
            ds.chip(tela, pygame.Rect(x, y, w, 22), _t(etapa), fonte_chip)
            x += w
            if i < len(cur.CADEIA_SUGERIDA) - 1:
                ds.texto_em(tela, '>', fonte_chip, (x + 7, y + 11), TEMA.texto_apagado,
                            ancora='center')
                x += 14
        y += 34

        # grupos com cartoes, dentro de uma area com rolagem
        self.rect_lista = pygame.Rect(interno.x, y, interno.width, interno.bottom - y)
        self.altura_visivel_lista = self.rect_lista.height
        colunas = 5
        gap = ds.ESPACO_MD
        largura_card = (self.rect_lista.width - gap * (colunas - 1)) // colunas
        altura_card = 78

        clip_antigo = tela.get_clip()
        tela.set_clip(self.rect_lista.clip(clip_antigo) if clip_antigo else self.rect_lista)
        self.rects_pedais = []
        yy = self.rect_lista.y - self.scroll_lista
        for grupo in cur.GRUPOS:
            pedais = cur.pedais_do_grupo(grupo['id'])
            if not pedais:
                continue
            titulo = f"{_t(grupo['nome'])}"
            r_tit = ds.texto_em(tela, titulo, self._fonte(15), (interno.x, yy), TEMA.texto)
            ds.selo(tela, (r_tit.right + 10, yy + 1), _t(grupo['nivel']), self._fonte(10),
                    self._cor_nivel(grupo['nivel']))
            yy += 22
            ds.texto_em(tela, _t(grupo['descricao']), self._fonte(11, False),
                        (interno.x, yy), TEMA.texto_suave, largura_max=interno.width)
            yy += 20
            for i, pedal in enumerate(pedais):
                col = i % colunas
                if col == 0 and i > 0:
                    yy += altura_card + gap
                r = pygame.Rect(interno.x + col * (largura_card + gap), yy,
                                largura_card, altura_card)
                visivel = r.colliderect(self.rect_lista)
                if visivel:
                    self._cartao_pedal(tela, r, pedal, r.collidepoint(pos_mouse)
                                       and self.rect_lista.collidepoint(pos_mouse))
                    self.rects_pedais.append((r.clip(self.rect_lista), pedal))
            yy += altura_card + ds.ESPACO_LG
        tela.set_clip(clip_antigo)

        self.altura_conteudo_lista = (yy + self.scroll_lista) - self.rect_lista.y
        excesso = self.altura_conteudo_lista - self.altura_visivel_lista
        if excesso > 0:
            ds.barra_rolagem(tela, self.rect_lista.right + 8, self.rect_lista.y,
                             self.rect_lista.height,
                             self.altura_visivel_lista / self.altura_conteudo_lista,
                             self.scroll_lista / excesso)

    def _cor_nivel(self, nivel):
        return {'Básico': TEMA.verde, 'Intermediário': TEMA.aviso,
                'Avançado': TEMA.alerta}.get(nivel, TEMA.acento)

    def _cartao_pedal(self, tela, r, pedal, hover):
        cor = pedal['cor']
        fundo = ds.misturar(TEMA.superficie_alt, cor, 0.12 if hover else 0.0)
        ds.superficie_translucida(tela, r, fundo, 230, ds.RAIO_MD,
                                  cor if hover else TEMA.borda, 2 if hover else 1)
        # mini pedal a esquerda
        mini = pygame.Rect(r.x + 10, r.y + 10, 40, r.height - 20)
        pygame.draw.rect(tela, cor, mini, border_radius=6)
        pygame.draw.rect(tela, ds.escurecer(cor, 0.35), mini, width=2, border_radius=6)
        for k in range(min(3, len(pedal['parametros']))):
            cx = mini.x + 9 + k * 11
            pygame.draw.circle(tela, (30, 30, 34), (cx, mini.y + 12), 4)
        pygame.draw.circle(tela, (200, 200, 205), (mini.centerx, mini.bottom - 12), 7)
        pygame.draw.circle(tela, (90, 90, 95), (mini.centerx, mini.bottom - 12), 7, 2)
        # textos
        x = mini.right + 12
        largura = r.right - x - 8
        ds.texto_em(tela, _t(pedal['nome']), self._fonte(14), (x, r.y + 10), TEMA.texto,
                    largura_max=largura)
        _texto_bloco(tela, _t(pedal['resumo']), self._fonte(11, False), x, r.y + 32,
                     largura, TEMA.texto_suave, max_linhas=2, entrelinha=2)

    # =================================================================
    # DESENHO: PEDAL ABERTO
    # =================================================================
    def _desenhar_pedal(self, tela, area, fontes):
        pedal = self.pedal
        cor = pedal['cor']
        ds.painel(tela, area, None, None, acento=cor, alpha=235)
        interno = area.inflate(-ds.ESPACO_XL * 2, -ds.ESPACO_LG * 2)
        pos_mouse = pygame.mouse.get_pos()

        # --- cabecalho --------------------------------------------------
        self.rect_voltar = pygame.Rect(interno.x, interno.y, 96, 28)
        ds.botao(tela, self.rect_voltar, '< ' + _t('Pedais'), self._fonte(12),
                 variante='secundario', hover=self.rect_voltar.collidepoint(pos_mouse))
        r_nome = ds.texto_em(tela, _t(pedal['nome']), fontes['titulo'],
                             (self.rect_voltar.right + 16, self.rect_voltar.centery),
                             cor if not TEMA.escuro or sum(cor) > 200 else TEMA.texto,
                             ancora='midleft')
        grupo = next(g for g in cur.GRUPOS if g['id'] == pedal['grupo'])
        ds.selo(tela, (r_nome.right + 12, self.rect_voltar.centery),
                f"{_t(grupo['nome'])} - {_t(grupo['nivel'])}", self._fonte(10),
                self._cor_nivel(grupo['nivel']), ancora='midleft')
        self.rect_proximo = pygame.Rect(interno.right - 100, interno.y, 100, 28)
        self.rect_anterior = pygame.Rect(self.rect_proximo.x - 108, interno.y, 100, 28)
        ds.botao(tela, self.rect_anterior, '< ' + _t('Anterior'), self._fonte(11),
                 variante='fantasma', hover=self.rect_anterior.collidepoint(pos_mouse))
        ds.botao(tela, self.rect_proximo, _t('Próximo') + ' >', self._fonte(11),
                 variante='fantasma', hover=self.rect_proximo.collidepoint(pos_mouse))

        topo = interno.y + 40
        largura_esq = max(300, min(460, int(interno.width * 0.34)))
        col_esq = pygame.Rect(interno.x, topo, largura_esq, interno.bottom - topo)
        col_dir = pygame.Rect(col_esq.right + ds.ESPACO_XL, topo,
                              interno.right - col_esq.right - ds.ESPACO_XL,
                              interno.bottom - topo)
        self._desenhar_coluna_esquerda(tela, col_esq, pos_mouse)
        self._desenhar_coluna_direita(tela, col_dir, pos_mouse)

    # ------------------------------------------------ desenho do pedal ----
    def _desenhar_caixa_pedal(self, tela, r, pos_mouse):
        pedal = self.pedal
        cor = pedal['cor']
        escuro = ds.escurecer(cor, 0.35)
        pygame.draw.rect(tela, ds.escurecer(cor, 0.55), r.move(0, 4), border_radius=14)
        pygame.draw.rect(tela, cor, r, border_radius=14)
        pygame.draw.rect(tela, escuro, r, width=3, border_radius=14)
        cor_txt = ds.contraste_texto(cor)

        # knobs
        params = self.parametros
        n = len(params)
        por_linha = 3 if n > 4 else n
        linhas = int(math.ceil(n / por_linha))
        esp_x = r.width / (por_linha + 0.0)
        raio = int(min(26 if linhas == 1 else 21, esp_x * 0.3))
        self.rects_knobs = []
        for i, par in enumerate(params):
            lin, col = divmod(i, por_linha)
            itens_linha = min(por_linha, n - lin * por_linha)
            margem = (r.width - itens_linha * esp_x) / 2
            cx = int(r.x + margem + esp_x * (col + 0.5))
            cy = int(r.y + 38 + lin * (raio * 2 + 34))
            foco = i == self.param_foco
            if foco:
                pygame.draw.circle(tela, ds.clarear(cor, 0.5), (cx, cy), raio + 5, 2)
            pygame.draw.circle(tela, (28, 28, 32), (cx, cy), raio)
            pygame.draw.circle(tela, (70, 70, 78), (cx, cy), raio, 2)
            pct = self._pct(par, self.valores[par['id']])
            ang = math.radians(225 - pct * 270)
            px = cx + math.cos(ang) * (raio - 5)
            py = cy - math.sin(ang) * (raio - 5)
            pygame.draw.line(tela, (245, 245, 245), (cx, cy), (px, py), 3)
            rotulo = _t(par['nome']).split(' (')[0]
            ds.texto_em(tela, rotulo.upper(), self._fonte(9), (cx, cy + raio + 4), cor_txt,
                        ancora='midtop', largura_max=int(esp_x) - 4)
            self.rects_knobs.append((pygame.Rect(cx - raio, cy - raio, raio * 2, raio * 2), i))

        # nome e LED
        y_nome = r.y + 38 + linhas * (raio * 2 + 34) - 6
        ds.texto_em(tela, _t(pedal['nome']).upper(), self._fonte(17), (r.centerx, y_nome),
                    cor_txt, ancora='midtop', largura_max=r.width - 20)
        led = (r.centerx, y_nome + 34)
        cor_led = (255, 60, 50) if self.ligado else (70, 30, 30)
        if self.ligado:
            pygame.draw.circle(tela, (255, 150, 140), led, 8)
        pygame.draw.circle(tela, cor_led, led, 6)

        # footswitch
        cfs = (r.centerx, r.bottom - 44)
        self.rect_footswitch = pygame.Rect(cfs[0] - 22, cfs[1] - 22, 44, 44)
        hover = self.rect_footswitch.collidepoint(pos_mouse)
        pygame.draw.circle(tela, (120, 120, 128), cfs, 22)
        pygame.draw.circle(tela, (225, 225, 230) if hover else (200, 200, 206), cfs, 18)
        pygame.draw.circle(tela, (150, 150, 156), cfs, 18, 2)
        ds.texto_em(tela, _t('clique para ligar/desligar'), self._fonte(9, False),
                    (r.centerx, r.bottom - 6), cor_txt, ancora='midbottom',
                    largura_max=r.width - 10)

    def _desenhar_coluna_esquerda(self, tela, col, pos_mouse):
        n = len(self.parametros)
        linhas = int(math.ceil(n / (3 if n > 4 else max(1, n))))
        altura_pedal = min(col.height - 250, 38 + linhas * 80 + 150)
        altura_pedal = max(200, altura_pedal)
        largura_pedal = min(col.width - 40, 320)
        caixa = pygame.Rect(col.centerx - largura_pedal // 2, col.y, largura_pedal, altura_pedal)
        self._desenhar_caixa_pedal(tela, caixa, pos_mouse)

        y = caixa.bottom + 18
        # transporte
        meia = (col.width - ds.ESPACO_SM) // 2
        self.rect_play = pygame.Rect(col.x, y, meia, 36)
        tocando = self.reprodutor.tocando
        ds.botao(tela, self.rect_play, _t('Parar') if tocando else _t('Ouvir'),
                 self._fonte(14), variante='perigo' if tocando else 'primario',
                 hover=self.rect_play.collidepoint(pos_mouse))
        self.rect_bypass = pygame.Rect(self.rect_play.right + ds.ESPACO_SM, y, meia, 36)
        ds.botao(tela, self.rect_bypass,
                 _t('Efeito LIGADO') if self.ligado else _t('Efeito DESLIGADO'),
                 self._fonte(13), variante='sucesso' if self.ligado else 'secundario',
                 hover=self.rect_bypass.collidepoint(pos_mouse))
        y += 46

        # forma de onda do loop, com cursor de reproducao
        onda = pygame.Rect(col.x, y, col.width, 46)
        ds.superficie_translucida(tela, onda, TEMA.superficie_alt, 220, ds.RAIO_SM, TEMA.borda, 1)
        forma = self.reprodutor.forma
        if forma is not None and forma.size:
            topo = max(1e-6, float(forma.max()))
            passo = onda.width / forma.size
            cor_onda = self.pedal['cor'] if self.ligado else TEMA.texto_apagado
            for i in range(0, forma.size, 2):
                h = int(forma[i] / topo * (onda.height / 2 - 4))
                x = int(onda.x + i * passo)
                pygame.draw.line(tela, cor_onda, (x, onda.centery - h), (x, onda.centery + h), 1)
        if tocando:
            xc = int(onda.x + self.reprodutor.posicao() * onda.width)
            pygame.draw.line(tela, TEMA.texto, (xc, onda.y + 2), (xc, onda.bottom - 2), 2)
        if self.reprodutor.ocupado():
            ds.texto_em(tela, _t('atualizando...'), self._fonte(9, False),
                        (onda.right - 6, onda.y + 3), TEMA.texto_apagado, ancora='topright')
        y = onda.bottom + 14

        # audio base
        ds.rotulo_secao(tela, col.x, y, _t('Áudio base'), self._fonte(11))
        y += 18
        self.rects_bases = []
        fonte = self._fonte(11)
        x = col.x
        for chave in motor.ORDEM_BASES:
            rotulo = _t(motor.BASES[chave]['nome'])
            w = fonte.size(rotulo)[0] + 20
            if x + w > col.right:
                x = col.x
                y += 28
            r = pygame.Rect(x, y, w, 24)
            ds.chip(tela, r, rotulo, fonte, ativo=chave == self.base, cor=TEMA.acento)
            self.rects_bases.append((r, chave))
            x += w + 6
        y += 28
        y = _texto_bloco(tela, _t(motor.BASES[self.base]['descricao']), self._fonte(10, False),
                         col.x, y, col.width, TEMA.texto_apagado, max_linhas=2) + 8

        # exemplos prontos
        if y + 60 < col.bottom:
            ds.rotulo_secao(tela, col.x, y, _t('Exemplos prontos'), self._fonte(11))
            y += 18
            self.rects_exemplos = []
            x = col.x
            for i, (nome, _v) in enumerate(self.pedal['exemplos']):
                rotulo = _t(nome)
                w = fonte.size(rotulo)[0] + 20
                if x + w > col.right:
                    x = col.x
                    y += 28
                if y + 24 > col.bottom - 30:
                    break
                r = pygame.Rect(x, y, w, 24)
                ds.chip(tela, r, rotulo, fonte, ativo=i == self.exemplo_ativo, cor=self.pedal['cor'])
                self.rects_exemplos.append((r, i))
                x += w + 6
            y += 32
        else:
            self.rects_exemplos = []
        self.rect_reset = pygame.Rect(col.x, min(y, col.bottom - 26), 150, 26)
        ds.botao(tela, self.rect_reset, _t('Restaurar padrão'), self._fonte(11),
                 variante='fantasma', hover=self.rect_reset.collidepoint(pos_mouse))

    # --------------------------------------------- explicacoes e sliders --
    def _desenhar_coluna_direita(self, tela, col, pos_mouse):
        pedal = self.pedal
        params = self.parametros
        detalhe_min = 90

        # Escolhe o maior tamanho de texto que cabe junto com os parametros
        for tam_txt, altura_param in ((15, 70), (14, 66), (13, 62), (12, 58)):
            fonte_txt = self._fonte(tam_txt, False)
            altura_linha_txt = fonte_txt.get_height() + 4
            altura_params = 26 + len(params) * altura_param
            espaco_texto = col.height - altura_params - detalhe_min - 16
            textos = [_t(pedal['como_funciona']),
                      _t('Quando usar') + ': ' + _t(pedal['quando_usar']),
                      _t('Experimente') + ': ' + _t(pedal['dica'])]
            linhas_total = sum(len(_quebrar(tx, fonte_txt, col.width)) for tx in textos)
            if 30 + linhas_total * altura_linha_txt + 12 <= espaco_texto:
                break

        # --- o que faz / como funciona / quando usar / dica ------------
        y = col.y
        ds.texto_em(tela, _t(pedal['resumo']), self._fonte(tam_txt + 3), (col.x, y), TEMA.texto,
                    largura_max=col.width)
        y += 30
        restante = max(2, (espaco_texto - 30) // altura_linha_txt)
        linhas_como = _quebrar(textos[0], fonte_txt, col.width)
        linhas_uso = _quebrar(textos[1], fonte_txt, col.width)
        linhas_dica = _quebrar(textos[2], fonte_txt, col.width)
        # prioridade: como funciona > dica > quando usar
        n_como = min(len(linhas_como), max(2, restante - 2))
        sobra = restante - n_como
        n_dica = min(len(linhas_dica), max(0, sobra))
        sobra -= n_dica
        n_uso = min(len(linhas_uso), max(0, sobra - 1))
        y = _texto_bloco(tela, textos[0], fonte_txt, col.x, y, col.width,
                         TEMA.texto_suave, max_linhas=n_como)
        if n_uso:
            y = _texto_bloco(tela, textos[1], fonte_txt, col.x, y + 6, col.width, TEMA.texto,
                             max_linhas=n_uso)
        if n_dica:
            y = _texto_bloco(tela, textos[2], fonte_txt, col.x, y + 6, col.width, TEMA.aviso,
                             max_linhas=n_dica)

        # --- parametros --------------------------------------------------
        y = min(y + 16, col.bottom - altura_params - detalhe_min)
        # sobrou espaco: linhas de parametro mais altas (ate um limite)
        livre = col.bottom - y - 26 - 170
        altura_param = int(max(altura_param, min(84, livre / max(1, len(params)))))
        ds.rotulo_secao(tela, col.x, y, _t('Parâmetros (arraste para mudar o som)'),
                        self._fonte(11))
        y += 24
        self.rects_sliders = []
        self.rects_linhas_param = []
        largura_barra = int(col.width * 0.46)
        for i, par in enumerate(params):
            linha = pygame.Rect(col.x, y, col.width, altura_param - 6)
            foco = i == self.param_foco
            ds.superficie_translucida(
                tela, linha,
                ds.misturar(TEMA.superficie_alt, pedal['cor'], 0.14 if foco else 0.0),
                215, ds.RAIO_SM, pedal['cor'] if foco else TEMA.borda, 1)
            self.rects_linhas_param.append((linha, i))
            meio = linha.centery
            ds.texto_em(tela, _t(par['nome']), self._fonte(tam_txt), (linha.x + 12, meio - 2),
                        TEMA.texto, ancora='bottomleft',
                        largura_max=linha.width - largura_barra - 40)
            ds.texto_em(tela, _t(par['curto']), self._fonte(tam_txt - 2, False),
                        (linha.x + 12, meio + 2), TEMA.texto_suave,
                        largura_max=linha.width - largura_barra - 40)
            valor = self.valores[par['id']]
            barra = pygame.Rect(linha.right - largura_barra - 16, meio + 6,
                                largura_barra, ds.ALTURA_TRILHO)
            ds.slider(tela, barra, self._pct(par, valor), cor=pedal['cor'],
                      rotulo=None, valor=cur.formatar_valor(par, valor), fonte=self._fonte(12))
            if par.get('opcoes') and len(par['opcoes']) <= 12:
                for k in range(len(par['opcoes'])):
                    xm = barra.x + int(barra.width * k / max(1, len(par['opcoes']) - 1))
                    pygame.draw.line(tela, TEMA.texto_apagado, (xm, barra.bottom + 4),
                                     (xm, barra.bottom + 7), 1)
            self.rects_sliders.append((barra, i))
            y += altura_param

        # --- detalhe do parametro em foco ----------------------------------
        par = params[self.param_foco % len(params)]
        fonte_det = self._fonte(tam_txt - 1, False)
        n_linhas_det = len(_quebrar(_t(par['explicacao']), fonte_det, col.width - 24))
        altura_det = 44 + n_linhas_det * (fonte_det.get_height() + 3)
        det = pygame.Rect(col.x, y + 4, col.width, max(40, min(altura_det, col.bottom - y - 4)))
        ds.superficie_translucida(tela, det, TEMA.superficie_alt, 225, ds.RAIO_MD,
                                  pedal['cor'], 1)
        ds.texto_em(tela, f"{_t('Sobre')}: {_t(par['nome'])}", self._fonte(tam_txt),
                    (det.x + 12, det.y + 8), pedal['cor'] if sum(pedal['cor']) > 200 else TEMA.texto,
                    largura_max=det.width - 24)
        linhas_max = max(1, (det.height - 36) // (fonte_det.get_height() + 3))
        _texto_bloco(tela, _t(par['explicacao']), fonte_det, det.x + 12,
                     det.y + 32, det.width - 24, TEMA.texto_suave, max_linhas=linhas_max,
                     entrelinha=3)

    # =================================================================
    # API usada pelo gerenciador de estudos
    # =================================================================
    def desenhar(self, tela, estado, fontes, meio_x, meio_y, cam_x, cam_y):
        """
            Como funciona: aplica o audio que ficou pronto, pede um novo se
            algo mudou e desenha a vista atual.
            Para que serve: tela principal do estudo de Pedais.
            Onde e usada: chamada pelo gerenciador de estudos a cada quadro.
        """
        self.reprodutor.atualizar()
        if self._mudou:
            self._pedir_audio()
        largura = getattr(estado, 'LARGURA_TELA', 1280)
        altura = getattr(estado, 'ALTURA_TELA', 720)
        area = pygame.Rect(int(cam_x + 40), int(cam_y + 56),
                           int(largura - 80), int(altura - 130))
        if self.vista == 'lista':
            self._desenhar_lista(tela, area, fontes)
        else:
            self._desenhar_pedal(tela, area, fontes)

    def _limitar_scroll(self):
        excesso = max(0, self.altura_conteudo_lista - self.altura_visivel_lista)
        self.scroll_lista = max(0, min(excesso, self.scroll_lista))

    def _slider_em(self, pos):
        for barra, i in self.rects_sliders:
            if barra.inflate(24, 26).collidepoint(pos):
                return barra, i
        return None

    def _arrastar_para(self, pos):
        if not self.arrastando:
            return
        if self.arrastando[0] == 'slider':
            _tipo, i, barra = self.arrastando
            par = self.parametros[i]
            pct = (pos[0] - barra.x) / max(1, barra.width)
            self.definir_valor(i, self._valor_do_pct(par, pct))
        else:
            _tipo, i, y0, pct0 = self.arrastando
            par = self.parametros[i]
            pct = pct0 + (y0 - pos[1]) / 160.0
            self.definir_valor(i, self._valor_do_pct(par, pct))

    def tratar_cliques(self, pos, estado):
        """Clique simples (mouse down)."""
        if self.vista == 'lista':
            if not self.rect_lista.collidepoint(pos):
                return False
            for r, pedal in self.rects_pedais:
                if r.collidepoint(pos):
                    self.abrir_pedal(pedal)
                    return True
            return False

        if self.rect_voltar.collidepoint(pos):
            self.reprodutor.parar()
            self.vista = 'lista'
            return True
        if self.rect_anterior.collidepoint(pos):
            self._vizinho(-1)
            return True
        if self.rect_proximo.collidepoint(pos):
            self._vizinho(1)
            return True
        if self.rect_play.collidepoint(pos):
            self.alternar_play()
            return True
        if self.rect_bypass.collidepoint(pos) or self.rect_footswitch.collidepoint(pos):
            self.alternar_bypass()
            return True
        if self.rect_reset.collidepoint(pos):
            self.valores = cur.valores_padrao(self.pedal)
            self.exemplo_ativo = None
            self._pedir_audio(forcar=True)
            return True
        for r, chave in self.rects_bases:
            if r.collidepoint(pos):
                if chave != self.base:
                    self.base = chave
                    self._pedir_audio(forcar=True)
                return True
        for r, i in self.rects_exemplos:
            if r.collidepoint(pos):
                self.aplicar_exemplo(i)
                return True
        achado = self._slider_em(pos)
        if achado:
            barra, i = achado
            self.arrastando = ('slider', i, barra)
            self._arrastar_para(pos)
            return True
        for r, i in self.rects_knobs:
            if r.inflate(10, 10).collidepoint(pos):
                par = self.parametros[i]
                self.param_foco = i
                self.arrastando = ('knob', i, pos[1], self._pct(par, self.valores[par['id']]))
                return True
        for r, i in self.rects_linhas_param:
            if r.collidepoint(pos):
                self.param_foco = i
                return True
        return False

    def tratar_eventos(self, evento, pos, estado):
        """Ponto de entrada usado pelo gerenciador de estudos."""
        if evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1:
                return self.tratar_cliques(pos, estado)
            if self.vista == 'lista' and evento.button in (4, 5):
                self.scroll_lista += -60 if evento.button == 4 else 60
                self._limitar_scroll()
                return True
        elif evento.type == pygame.MOUSEWHEEL and self.vista == 'lista':
            self.scroll_lista -= evento.y * 60
            self._limitar_scroll()
            return True
        elif evento.type == pygame.MOUSEMOTION and self.arrastando:
            self._arrastar_para(pos)
            return True
        elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1 and self.arrastando:
            self._arrastar_para(pos)
            self.arrastando = None
            self._pedir_audio(forcar=True)
            return True
        elif evento.type == pygame.KEYDOWN and self.vista == 'pedal':
            if evento.key == pygame.K_SPACE:
                self.alternar_play()
                return True
            if evento.key in (pygame.K_b, pygame.K_RETURN):
                self.alternar_bypass()
                return True
            if evento.key in (pygame.K_UP, pygame.K_DOWN):
                passo = -1 if evento.key == pygame.K_UP else 1
                self.param_foco = (self.param_foco + passo) % len(self.parametros)
                return True
            if evento.key in (pygame.K_LEFT, pygame.K_RIGHT):
                par = self.parametros[self.param_foco]
                n = len(par['opcoes']) - 1 if par.get('opcoes') else 50
                delta = (1 if evento.key == pygame.K_RIGHT else -1) / max(1, n)
                pct = self._pct(par, self.valores[par['id']]) + delta
                self.definir_valor(self.param_foco, self._valor_do_pct(par, pct))
                return True
        return False
