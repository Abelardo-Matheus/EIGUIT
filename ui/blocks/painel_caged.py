# -*- coding: utf-8 -*-
"""
Compatibilidade: o painel CAGED virou um caso particular de PainelAcordes.

Mantido para que imports antigos continuem funcionando.
"""
from ui.blocks.painel_acordes import (  # noqa: F401
    PainelAcordes, SHAPES, NOTAS, CORDAS_SOLTAS, TIPOS_ACORDE, FAMILIAS,
    notas_do_acorde, nome_do_acorde, semitons as _semitons,
    PAINEIS, painel_da_sub_aba,
)

# Instancia da sub-aba CAGED
painel_caged = PAINEIS[0]
PainelCAGED = PainelAcordes
