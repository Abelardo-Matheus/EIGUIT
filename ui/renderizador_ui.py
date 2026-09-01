import pygame
import math
import core.modulos.escalas as escalas
from ui import gerenciador_interface
from config.theme import *
from config.ui_metrics import *
from config.app_settings import *
from Jogos.Jogos_interativos import GerenciadorJogos
import core.modulos.modulos_estudos as modulo_estudos
from ui.renderizador_tablatura import RenderizadorTablatura
from ui.components import (
    desenhar_painel_superior, 
    desenhar_controles_instrumento,
    desenhar_acordes_arrastaveis, 
    desenhar_controles_playback, 
    desenhar_bloco_nota_atual, 
    desenhar_painel_cores, 
    desenhar_secoes_inferiores_expansiveis
)
from ui.blocks.guitar_neck import desenhar_guitarra
from ui.components.utils import obter_grau, equivalencia_notas

# Instâncias globais de renderizadores
render_tab_viewer = None
render_tab_maker = None

from DragDrop.gerenciador_snap import desenhar_guias_inteligentes

def desenhar_workspace(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico, meu_gerenciador_jogos):
    """
        Como funciona: Calcula a posição e renderiza os componentes dinâmicos (braço da guitarra, controles, campo harmônico) no espaço virtual.
    """
    # Desenhar Guias Inteligentes (abaixo de tudo no workspace)
    if hasattr(estado, 'guias_x') and (estado.guias_x or estado.guias_y):
        desenhar_guias_inteligentes(tela, estado.guias_x, estado.guias_y, tela.get_width(), tela.get_height())

    if hasattr(estado, 'lista_guitarras'):
        for guit in estado.lista_guitarras:
            desenhar_guitarra(tela, estado, configs, fontes, meu_processador, meu_campo_harmonico, dragger_obj=guit)
    else:
        desenhar_guitarra(tela, estado, configs, fontes, meu_processador, meu_campo_harmonico)
    
    desenhar_controles_instrumento(tela, estado, fontes, configs)
    desenhar_acordes_arrastaveis(tela, estado, meu_campo_harmonico, fontes)
    desenhar_painel_cores(tela, estado, fontes)
    desenhar_bloco_nota_atual(tela, estado, fontes, configs)
    desenhar_controles_playback(tela, estado, meu_metronomo, fontes['ui'], configs)
    
    if hasattr(estado, 'lista_tabs'):
        for tab in estado.lista_tabs:
            tab.desenhar(tela, fontes)
            
    desenhar_secoes_inferiores_expansiveis(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_gerenciador_jogos)

def desenhar_ui_fixa(tela, estado, fontes, meu_gravador, configs, meu_gerenciador_jogos, meu_campo_harmonico=None):
    largura_real = tela.get_width()
    altura_real = tela.get_height()
    
    if getattr(estado, 'tab_tela_cheia_ativa', False) and hasattr(estado, 'tab_focada'):
        _desenhar_tela_cheia_tablatura(tela, largura_real, altura_real, estado, fontes)
    elif getattr(estado, 'tela_criacao_tab_ativa', False):
        _desenhar_tela_criacao_tablatura(tela, largura_real, altura_real, estado, fontes, configs, meu_campo_harmonico)
    elif getattr(estado, 'tela_estudo_ativa', False):
        if not hasattr(estado, 'gerenciador_estudos'):
            estado.gerenciador_estudos = modulo_estudos.GerenciadorEstudos()
        estado.gerenciador_estudos.desenhar_tela_estudo(tela, largura_real, altura_real, estado, fontes)
    elif estado.tela_jogo_ativa:
        meu_gerenciador_jogos.desenhar_tela_jogo(tela, largura_real, altura_real, estado, meu_gravador, configs)

    if hasattr(estado, 'gerenciador_perfil') and estado.gerenciador_perfil.ativo:
        estado.gerenciador_perfil.desenhar(tela, fontes['titulo'], fontes['ui'], estado)
    if hasattr(estado, 'menu_contexto'):
        estado.menu_contexto.desenhar(tela, fontes['ui'])

def _desenhar_tela_cheia_tablatura(tela, largura, altura, estado, fontes):
    tab = estado.tab_focada
    tela.fill(FUNDO_ESCURO)
    pygame.draw.rect(tela, (30, 30, 35), (0, 0, largura, 80))
    pygame.draw.line(tela, (60, 60, 65), (0, 80), (largura, 80), 2)
    txt_t = fontes['titulo'].render(f'{tab.titulo}', True, (240, 240, 240))
    tela.blit(txt_t, (40, 20))
    txt_a = fontes['ui'].render(f'Artista: {tab.artista}', True, (160, 160, 160))
    tela.blit(txt_a, (40, 50))
    
    original_fundo = tab.COR_FUNDO
    original_linha = tab.COR_LINHA
    tab.COR_FUNDO = FUNDO_ESCURO
    tab.COR_LINHA = (60, 60, 65)
    margem_x = 60
    largura_folha = largura - margem_x * 2
    tab._desenhar_visualizador_tab(tela, margem_x, 120, largura_folha, altura - 150, fontes)
    tab.COR_FUNDO = original_fundo
    tab.COR_LINHA = original_linha

def _desenhar_tela_criacao_tablatura(tela, largura, altura, estado, fontes, configs, meu_campo_harmonico=None):
    """
    Renderiza a interface do Criador de Tablaturas seguindo GEMINI.md.
    """
    global render_tab_maker
    if render_tab_maker is None:
        render_tab_maker = RenderizadorTablatura()
        
    render_tab_maker.desenhar_interface_tab(tela, estado, fontes, largura, altura, configs, meu_campo_harmonico)

def desenhar_tudo(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico, meu_gerenciador_jogos):
    largura_tela = tela.get_width()
    altura_tela = tela.get_height()

    # 1. Limpa a tela principal
    tela.fill(FUNDO_ESCURO)

    # 2. ÁREA 2: Conteúdo Dinâmico (Abaixo da Top Bar)
    # Criamos um Viewport para que as telas internas não precisem gerenciar o offset
    altura_conteudo = max(1, altura_tela - ALTURA_TOPBAR)
    rect_viewport = pygame.Rect(0, ALTURA_TOPBAR, largura_tela, altura_conteudo)
    
    try:
        viewport = tela.subsurface(rect_viewport)
        # Todo o resto do programa é renderizado aqui dentro
        desenhar_workspace(viewport, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico, meu_gerenciador_jogos)
        desenhar_ui_fixa(viewport, estado, fontes, meu_gravador, configs, meu_gerenciador_jogos, meu_campo_harmonico)
    except Exception as e:
        # Fallback de segurança caso o subsurface falhe (ex: janela minimizada)
        desenhar_workspace(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico, meu_gerenciador_jogos)
        desenhar_ui_fixa(tela, estado, fontes, meu_gravador, configs, meu_gerenciador_jogos, meu_campo_harmonico)

    # 3. ÁREA 1: Cabeçalho Fixo (Sempre no topo absoluto, z-index alto)
    desenhar_painel_superior(tela, estado, fontes, configs)
    
    pygame.display.flip()
