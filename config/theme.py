# -*- coding: utf-8 -*-
"""
Paleta legada do EIGUIT, agora derivada do design system.

Este modulo existe para compatibilidade: dezenas de arquivos fazem
`from config.theme import *`. Os nomes continuam identicos, mas os valores
vem de config/design_system.py, entao toda a interface herda o novo visual.

Para codigo novo prefira:

    from config.design_system import TEMA, ds

porque TEMA responde a troca de tema claro/escuro em tempo real, enquanto as
constantes abaixo sao capturadas no momento do import.
"""
from config.design_system import (  # noqa: F401  (reexportado de proposito)
    TEMA,
    PALETA_ESCURA,
    PALETA_CLARA,
    ds,
    misturar,
    clarear,
    escurecer,
    rgb,
)

# --- Superficies -----------------------------------------------------------
FUNDO_ESCURO = TEMA.fundo
FUNDO_PAINEL = TEMA.superficie
COR_PAINEL = TEMA.superficie
COR_SUPERFICIE_ALT = TEMA.superficie_alt
COR_TOPBAR = TEMA.superficie_topo

# --- Instrumento -----------------------------------------------------------
COR_CORDA = TEMA.corda
COR_TRASTE = TEMA.traste
MADEIRA = TEMA.madeira

# --- Texto -----------------------------------------------------------------
BRANCO = TEMA.texto
PRETO = (0, 0, 0)
COR_TEXTO = TEMA.texto
COR_TEXTO_SUAVE = TEMA.texto_suave
COR_TEXTO_INATIVO = TEMA.texto_apagado

# --- Acentos ---------------------------------------------------------------
AZUL_PRIMARIO = TEMA.primaria
AZUL_HOVER = TEMA.primaria_clara
CIANO = TEMA.ciano
VERDE_SUCCESS = TEMA.verde
VERMELHO_DANGER = TEMA.alerta
AMARELO_AVISO = TEMA.aviso
ROXO = TEMA.roxo

# --- Abas e bordas ---------------------------------------------------------
COR_ABA_ATIVA = TEMA.superficie_alt
COR_ABA_INATIVA = TEMA.superficie
COR_SUB_ATIVA = misturar(TEMA.superficie_alt, TEMA.primaria, 0.25)
COR_SUB_INATIVA = TEMA.superficie
COR_BORDA = TEMA.borda
COR_TRILHO = TEMA.trilho

# --- Cores dos graus (tonica / terca / quinta) -----------------------------
# Mantidas como tuplas RGB simples: varios modulos fazem (*cor, alpha).
CORES_TONICA = [
    (255, 255, 255),
    (255, 107, 107),
    (78, 205, 196),
    (255, 217, 61),
    (0, 212, 255),
    (155, 122, 255),
]


def sincronizar_tema():
    """
    Reescreve as constantes deste modulo a partir do TEMA atual.

    Uso: apos TEMA.alternar(), chamar sincronizar_tema() atualiza os modulos que
    importarem config.theme DEPOIS da troca. Modulos ja carregados via
    `import *` mantem os valores antigos por design do Python, por isso os
    componentes principais leem TEMA diretamente.
    """
    g = globals()
    g['FUNDO_ESCURO'] = TEMA.fundo
    g['FUNDO_PAINEL'] = TEMA.superficie
    g['COR_PAINEL'] = TEMA.superficie
    g['COR_SUPERFICIE_ALT'] = TEMA.superficie_alt
    g['COR_TOPBAR'] = TEMA.superficie_topo
    g['COR_CORDA'] = TEMA.corda
    g['COR_TRASTE'] = TEMA.traste
    g['MADEIRA'] = TEMA.madeira
    g['BRANCO'] = TEMA.texto
    g['COR_TEXTO'] = TEMA.texto
    g['COR_TEXTO_SUAVE'] = TEMA.texto_suave
    g['COR_TEXTO_INATIVO'] = TEMA.texto_apagado
    g['AZUL_PRIMARIO'] = TEMA.primaria
    g['AZUL_HOVER'] = TEMA.primaria_clara
    g['CIANO'] = TEMA.ciano
    g['VERDE_SUCCESS'] = TEMA.verde
    g['VERMELHO_DANGER'] = TEMA.alerta
    g['AMARELO_AVISO'] = TEMA.aviso
    g['ROXO'] = TEMA.roxo
    g['COR_ABA_ATIVA'] = TEMA.superficie_alt
    g['COR_ABA_INATIVA'] = TEMA.superficie
    g['COR_SUB_ATIVA'] = misturar(TEMA.superficie_alt, TEMA.primaria, 0.25)
    g['COR_SUB_INATIVA'] = TEMA.superficie
    g['COR_BORDA'] = TEMA.borda
    g['COR_TRILHO'] = TEMA.trilho
