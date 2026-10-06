# -*- coding: utf-8 -*-
"""
Configuracoes de desempenho (Configuracoes > Desempenho).

Cada opcao troca qualidade visual por velocidade. Os presets cobrem os tipos
de PC mais comuns e o usuario pode ajustar item a item (vira "Personalizado").
Tudo e guardado no perfil (core/modulos/modulo_perfil.py).
"""
import threading

from config import design_system as ds

# id, rotulo, descricao, tipo ('liga' ou lista de valores), rotulos dos valores
OPCOES = [
    ('fps', 'Limite de quadros (FPS)',
     'Menos quadros por segundo = menos uso de processador.',
     [30, 45, 60, 90, 120], ['30', '45', '60', '90', '120']),
    ('sombras', 'Sombras', 'Sombra suave sob painéis, menus e janelas.', 'liga', None),
    ('transparencias', 'Transparências', 'Painéis translúcidos. Desligado: cores sólidas.', 'liga', None),
    ('animacoes', 'Animações', 'Avisos deslizando e indicadores pulsando.', 'liga', None),
    ('zoom_suave', 'Zoom com suavização', 'Imagem mais lisa ao aproximar a mesa (mais pesado).', 'liga', None),
    ('intervalo_audio', 'Análise do áudio', 'De quanto em quanto tempo a nota tocada é analisada.',
     [30, 50, 80, 120], ['30 ms (precisa)', '50 ms', '80 ms', '120 ms (leve)']),
    ('pre_carregar', 'Pré-carregar análise de áudio',
     'Carrega o detector de notas ao abrir, sem engasgo na 1ª nota.', 'liga', None),
    ('mostrar_fps', 'Mostrar FPS na barra', 'Mostra quantos quadros por segundo estão saindo.', 'liga', None),
]

PRESETS = {
    'leve': {'fps': 30, 'sombras': False, 'transparencias': False, 'animacoes': False,
             'zoom_suave': False, 'intervalo_audio': 80, 'pre_carregar': False},
    'equilibrado': {'fps': 60, 'sombras': True, 'transparencias': True, 'animacoes': True,
                    'zoom_suave': False, 'intervalo_audio': 30, 'pre_carregar': True},
    'maximo': {'fps': 120, 'sombras': True, 'transparencias': True, 'animacoes': True,
               'zoom_suave': True, 'intervalo_audio': 30, 'pre_carregar': True},
}
ROTULOS_PRESETS = [
    ('leve', 'Leve', 'PC antigo, notebook simples ou integrado fraco'),
    ('equilibrado', 'Equilibrado', 'A maioria dos computadores'),
    ('maximo', 'Máximo', 'PC forte: tudo ligado, 120 FPS'),
]

PADRAO = dict(PRESETS['equilibrado'], preset='equilibrado', mostrar_fps=False)


def normalizar(dados):
    """Completa e valida um dicionario vindo do perfil (ou de um perfil antigo)."""
    final = dict(PADRAO)
    if isinstance(dados, dict):
        for chave, _rotulo, _desc, tipo, _rotulos in OPCOES:
            if chave not in dados:
                continue
            valor = dados[chave]
            if tipo == 'liga':
                final[chave] = bool(valor)
            elif valor in tipo:
                final[chave] = valor
    final['preset'] = detectar_preset(final)
    return final


def detectar_preset(cfg):
    for nome, valores in PRESETS.items():
        if all(cfg.get(k) == v for k, v in valores.items()):
            return nome
    return 'personalizado'


def obter(estado):
    cfg = getattr(estado, 'desempenho', None)
    if not isinstance(cfg, dict):
        cfg = dict(PADRAO)
        estado.desempenho = cfg
    return cfg


def aplicar(estado):
    """Leva as opcoes para quem as usa: design system, camera, audio e laco."""
    cfg = obter(estado)
    mudou_visual = (ds.EFEITOS['sombras'] != cfg['sombras']
                    or ds.EFEITOS['transparencias'] != cfg['transparencias'])
    ds.EFEITOS['sombras'] = cfg['sombras']
    ds.EFEITOS['transparencias'] = cfg['transparencias']
    ds.EFEITOS['animacoes'] = cfg['animacoes']
    if mudou_visual:
        ds.limpar_caches()
    camera = getattr(estado, 'camera', None)
    if camera is not None:
        camera.zoom_suave = cfg['zoom_suave']
    motor = getattr(estado, 'motor_audio', None)
    if motor is not None and hasattr(motor, 'INTERVALO_ANALISE_MS'):
        motor.INTERVALO_ANALISE_MS = cfg['intervalo_audio']
    estado.fps_alvo = cfg['fps']


def definir(estado, chave, valor):
    cfg = obter(estado)
    cfg[chave] = valor
    cfg['preset'] = detectar_preset(cfg)
    aplicar(estado)
    _avisar_mudanca(estado)


def aplicar_preset(estado, nome):
    if nome not in PRESETS:
        return
    cfg = obter(estado)
    cfg.update(PRESETS[nome])
    cfg['preset'] = nome
    aplicar(estado)
    _avisar_mudanca(estado)


def _avisar_mudanca(estado):
    """Marca o perfil para ser gravado (o auto-salvamento cuida do resto)."""
    estado.perfil_alterado = True


def pre_carregar_audio(estado):
    """Importa o librosa em segundo plano: a primeira nota nao engasga a tela."""
    if not obter(estado).get('pre_carregar'):
        return

    def _carregar():
        try:
            import librosa  # noqa: F401
            motor = getattr(estado, 'motor_audio', None)
            if motor is not None and getattr(motor, '_librosa', None) is None:
                motor._librosa = librosa
        except Exception:
            pass

    threading.Thread(target=_carregar, daemon=True).start()


class MedidorFPS:
    """FPS real medido por uma media movel simples."""

    def __init__(self):
        self.valor = 0.0

    def registrar(self, ms_quadro):
        if ms_quadro <= 0:
            return
        instantaneo = 1000.0 / ms_quadro
        self.valor = instantaneo if not self.valor else self.valor * 0.9 + instantaneo * 0.1
