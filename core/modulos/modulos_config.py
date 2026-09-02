# -*- coding: utf-8 -*-
"""
Constantes visuais dos modulos (menus, perfil, suporte, campo harmonico).

As cores derivam do design system para manter tudo coerente. Os nomes foram
preservados porque varios modulos fazem `from core.modulos.modulos_config import *`.
"""
from config.design_system import TEMA, misturar

# --- Menu superior ---------------------------------------------------------
MENU_SUPERIOR_ALTURA_BARRA = 40
MENU_SUPERIOR_COR_BARRA = TEMA.superficie_topo
MENU_SUPERIOR_COR_TEXTO = TEMA.texto_suave
MENU_SUPERIOR_COR_HOVER = TEMA.primaria
MENU_SUPERIOR_COR_DROPDOWN = TEMA.superficie_alt
MENU_SUPERIOR_COR_BORDA = TEMA.borda
MENU_SUPERIOR_BRANCO = TEMA.texto
MENU_SUPERIOR_LARGURA_DROPDOWN = 230
MENU_SUPERIOR_MODAL_IDEIAS_LARGURA = 680
MENU_SUPERIOR_MODAL_IDEIAS_ALTURA = 360
MENU_SUPERIOR_MODAL_PATROCINE_LARGURA = 800
MENU_SUPERIOR_MODAL_PATROCINE_ALTURA = 360
MENU_SUPERIOR_MODAL_MOTIVACAO_LARGURA = 850
MENU_SUPERIOR_MODAL_MOTIVACAO_ALTURA = 400

# --- Menu de contexto ------------------------------------------------------
MENU_CONTEXTO_LARGURA = 210
MENU_CONTEXTO_ALTURA_ITEM = 34
MENU_CONTEXTO_COR_FUNDO = TEMA.superficie_alt
MENU_CONTEXTO_COR_BORDA = TEMA.borda
MENU_CONTEXTO_COR_HOVER = TEMA.primaria
MENU_CONTEXTO_COR_TEXTO = TEMA.texto

# --- Campo harmonico -------------------------------------------------------
CAMPO_HARM_COR_FUNDO = TEMA.superficie_alt
CAMPO_HARM_COR_BORDA = TEMA.borda
CAMPO_HARM_COR_TEXTO = TEMA.texto
CAMPO_HARM_AZUL_BOTAO = TEMA.primaria
CAMPO_HARM_LARGURA_BLOCO = 80
CAMPO_HARM_ALTURA_BLOCO = 58
CAMPO_HARM_ESPACAMENTO = 12

# --- Metronomo -------------------------------------------------------------
METRONOMO_BRANCO = TEMA.texto
METRONOMO_CINZA = TEMA.texto_apagado
METRONOMO_FUNDO_INPUT = TEMA.superficie_alt
METRONOMO_SLIDER_LARGURA = 150

# --- Perfil ----------------------------------------------------------------
PERFIL_BRANCO = TEMA.texto
PERFIL_FUNDO = TEMA.superficie
PERFIL_AZUL_BOTAO = TEMA.primaria
PERFIL_CINZA = TEMA.texto_apagado
PERFIL_VERMELHO = TEMA.alerta
PERFIL_VERMELHO_DARK = misturar(TEMA.alerta, (0, 0, 0), 0.3)
PERFIL_MODAL_LARGURA = 450
PERFIL_MODAL_ALTURA_CONTA = 300
PERFIL_MODAL_ALTURA_PADRAO = 250

# --- Suporte ---------------------------------------------------------------
SUPORTE_BRANCO = TEMA.texto
SUPORTE_CINZA = TEMA.texto_suave
SUPORTE_AZUL = TEMA.primaria
SUPORTE_AZUL_CLARO = TEMA.primaria_clara
SUPORTE_MODAL_LARGURA = 850
SUPORTE_MODAL_ALTURA = 550
SUPORTE_MARGEM_ESQ = 40
SUPORTE_MARGEM_DIR = 60
SUPORTE_ESPACAMENTO_MEIO = 30
SUPORTE_LARGURA_IMAGEM = 280
SUPORTE_ALTURA_IMAGEM = 160

# --- Estudos de acordes ----------------------------------------------------
ESTUDOS_ACORDES_NUM_CORDAS = 7
ESTUDOS_ACORDES_ESPACO_CORDAS = 30
ESTUDOS_ACORDES_ESPACO_CASAS = 45
