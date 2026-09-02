# -*- coding: utf-8 -*-
"""Metricas de layout do EIGUIT Studio (espacamentos, raios e alturas)."""
from config.design_system import (  # noqa: F401
    ESPACO_XS, ESPACO_SM, ESPACO_MD, ESPACO_LG, ESPACO_XL,
    RAIO_SM, RAIO_MD, RAIO_LG, RAIO_XL, RAIO_PILULA,
    ALTURA_CONTROLE, ALTURA_CONTROLE_SM, ALTURA_TRILHO,
)

# Nomes legados (mantidos para compatibilidade dos imports existentes)
RADIUS_PADRAO = RAIO_LG
PADDING_PADRAO = ESPACO_MD

# Altura da barra superior fixa. O calculo do viewport em main.py e
# renderizador_ui.py depende deste valor.
ALTURA_TOPBAR = 40

# Tamanhos de toque recomendados
ALVO_CLIQUE_MIN = 30
ALTURA_BOTAO = 32
ALTURA_BOTAO_SM = 26
ALTURA_CHIP = 28
LARGURA_SIDEBAR = 280
