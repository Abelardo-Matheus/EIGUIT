# -*- coding: utf-8 -*-
"""
Base comum das suites de teste do EIGUIT.

Sobe o programa sem janela real (drivers dummy de video e audio), monta os
objetos que o main.py monta e oferece utilidades de verificacao. Nenhuma suite
depende de microfone, de placa de som nem do banco de dados.
"""
import atexit
import io
import os
import sys
import traceback

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

RAIZ = None
_AQUI = os.path.dirname(os.path.abspath(__file__))
for _candidato in (os.path.dirname(_AQUI), _AQUI,
                   os.path.join(os.path.expanduser('~'), 'mnt', 'EIGUIT')):
    if os.path.exists(os.path.join(_candidato, 'main.py')) and \
            os.path.isdir(os.path.join(_candidato, 'core')):
        RAIZ = _candidato
        break
if RAIZ is None:
    raise SystemExit('nao encontrei a raiz do projeto EIGUIT')
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1920, 1080))

# As preferencias ficam num arquivo do projeto: guarda e devolve como estava
_PREFS = os.path.join(RAIZ, 'config_eiguit.json')
try:
    _PREFS_ORIGINAL = io.open(_PREFS, encoding='utf-8').read()
except OSError:
    _PREFS_ORIGINAL = None


@atexit.register
def _restaurar_prefs():
    if _PREFS_ORIGINAL is not None:
        try:
            io.open(_PREFS, 'w', encoding='utf-8').write(_PREFS_ORIGINAL)
        except OSError:
            pass


TEMAS = ('escuro', 'claro')


def definir_tema(modo):
    """Troca o tema sem gravar no arquivo de preferencias do usuario."""
    from config.design_system import TEMA, PALETA_CLARA, PALETA_ESCURA
    import config.theme as tema_legado
    TEMA.modo = modo
    TEMA._paleta = PALETA_ESCURA if modo == 'escuro' else PALETA_CLARA
    try:
        tema_legado.sincronizar_tema()
    except Exception:
        pass


def montar_fontes(escala=1.0):
    base = {'ui': 18, 'pequena': 15, 'titulo': 22, 'notas': 20}
    return {k: pygame.font.SysFont('Arial', max(9, int(v * escala)), bold=True)
            for k, v in base.items()}


class Contexto:
    """Os objetos que o main.py cria, prontos para uma suite usar."""

    def __init__(self, largura=1920, altura=1080, tema='escuro'):
        definir_tema(tema)
        import core.config as config
        import core.estado_app as estado_app
        import core.modulos.modulo_camera as modulo_camera
        import core.modulos.modulo_metronomo as modulo_metronomo
        import core.modulos.modulo_processamento as modulo_processamento
        from Jogos.Jogos_interativos import GerenciadorJogos
        from core.modulos.modulo_campo_harmonico import CampoHarmonico
        from core.sessao_estudo import SessaoEstudo
        from ui import fabrica_escalas

        self.largura, self.altura, self.tema = largura, altura, tema
        self.tela = pygame.Surface((largura, altura), pygame.SRCALPHA)
        self.estado = estado_app.EstadoGlobal(largura, altura)
        self.estado.camera = modulo_camera.CameraWorkspace(largura, altura)
        self.configs = config.Configuracoes(40, 400)
        self.metronomo = modulo_metronomo.Metronomo(40, 400)
        self.processador = modulo_processamento.ProcessadorAudio()
        self.campo = CampoHarmonico()
        self.jogos = GerenciadorJogos()
        self.estado.sessao = SessaoEstudo()
        self.gravador = None            # sem motor de audio, de proposito
        self.fontes = montar_fontes()
        self.escalas = fabrica_escalas.gerar_modulos(self.estado, self.configs)

    def redimensionar_bloco(self, nome, largura, altura, x=40, y=40):
        """Coloca um bloco numa posicao e num tamanho exatos."""
        d = getattr(self.estado, f'dragger_{nome}')
        d.x, d.y, d.largura, d.altura = x, y, largura, altura
        if hasattr(d, 'rect_caixa'):
            d.rect_caixa.update(x, y, largura, altura)
        return pygame.Rect(x, y, largura, altura)


class Suite:
    """Contador de testes simples, com relatorio no fim."""

    def __init__(self, nome):
        self.nome = nome
        self.ok = 0
        self.falhas = []

    def teste(self, descricao, funcao):
        try:
            funcao()
        except Exception as erro:
            self.falhas.append((descricao, erro, traceback.format_exc()))
            print(f'  FALHOU  {descricao}: {erro}')
        else:
            self.ok += 1
            print(f'  ok      {descricao}')

    def checar(self, condicao, mensagem):
        if not condicao:
            raise AssertionError(mensagem)

    def encerrar(self):
        total = self.ok + len(self.falhas)
        print(f'\n[{self.nome}] {self.ok}/{total} passaram')
        if self.falhas:
            for descricao, _erro, tb in self.falhas:
                print(f'\n--- {descricao} ---\n{tb}')
            sys.exit(1)
        sys.exit(0)


def pixels_fora(desenhar_conteudo, desenhar_base, tamanho, rect):
    """
        Como funciona: Desenha duas vezes na mesma superficie limpa, uma com o
        conteudo do bloco e outra so com a moldura vazia, e compara tudo o que
        esta fora do retangulo do bloco.
        Para que serve: Provar que nenhum item do conteudo foi pintado fora dos
        limites, tolerando a sombra do painel, que e igual nas duas.
        Onde e usada: teste_blocos.
    """
    fundo = (0, 0, 0, 0)
    a = pygame.Surface(tamanho, pygame.SRCALPHA)
    a.fill(fundo)
    desenhar_conteudo(a)
    b = pygame.Surface(tamanho, pygame.SRCALPHA)
    b.fill(fundo)
    desenhar_base(b)

    diferentes = []
    largura, altura = tamanho
    for y in range(altura):
        for x in range(largura):
            if rect.collidepoint(x, y):
                continue
            if a.get_at((x, y)) != b.get_at((x, y)):
                diferentes.append((x, y))
                if len(diferentes) > 20:
                    return diferentes
    return diferentes
