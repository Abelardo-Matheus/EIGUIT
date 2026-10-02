# -*- coding: utf-8 -*-
"""
Registro das pedaleiras que aparecem na area "Exportar p/ pedaleira".

Para integrar uma nova:
    1. crie pedaleiras/<id>/driver.py com uma subclasse de base.DriverPedaleira
       (implementado = True);
    2. acrescente-a em _carregar() abaixo (no lugar da PedaleiraPlanejada, se ja existir);
    3. coloque arquivos de exemplo em _validacao/dados_pedaleiras/<id>/ e um caso
       em _validacao/teste_pedaleiras.py.
"""
from pedaleiras.base import PedaleiraPlanejada

_DRIVERS = None


def _carregar():
    from pedaleiras.mk300.driver import DriverMK300
    return [
        DriverMK300(),
        PedaleiraPlanejada('tank_g', 'Tank-G', 'M-VAVE', 'M-EFCS', '.tkg'),
        PedaleiraPlanejada('tank_b', 'Tank-B', 'M-VAVE', 'M-EFCS', '.tkb'),
        PedaleiraPlanejada('blackbox', 'Blackbox', 'M-VAVE', 'M-EFCS', '.bkx'),
        PedaleiraPlanejada('mooer_ge150', 'GE150', 'Mooer', 'Mooer Studio'),
        PedaleiraPlanejada('valeton_gp200', 'GP-200', 'Valeton', 'Valeton GP-200 Editor'),
        PedaleiraPlanejada('boss_gt1', 'GT-1', 'Boss', 'BOSS TONE STUDIO'),
        PedaleiraPlanejada('line6_podgo', 'POD Go', 'Line 6', 'POD Go Edit'),
    ]


def listar():
    global _DRIVERS
    if _DRIVERS is None:
        _DRIVERS = _carregar()
    return list(_DRIVERS)


def obter(id_):
    for d in listar():
        if d.id == id_:
            return d
    return None


def padrao():
    for d in listar():
        if d.implementado:
            return d
    return listar()[0]
