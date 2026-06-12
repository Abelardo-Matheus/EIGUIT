import pygame
import math
import Modulos.escalas as escalas
from Interface import gerenciador_interface
from Core.constantes_ui import *
from Jogos.Jogos_interativos import GerenciadorJogos
import Modulos.modulos_estudos as modulo_estudos
from Interface.renderizador_tablatura import RenderizadorTablatura
from Interface.renderizador_criador_tab import RenderizadorCriadorTablatura
from Interface.Componentes import (
    desenhar_painel_superior, 
    desenhar_controles_instrumento,
    desenhar_guitarra, 
    desenhar_acordes_arrastaveis, 
    desenhar_controles_playback, 
    desenhar_bloco_nota_atual, 
    desenhar_painel_cores, 
    desenhar_secoes_inferiores_expansiveis
)
from Interface.Componentes.utils import obter_grau, equivalencia_notas

# Instâncias globais de renderizadores
render_tab_viewer = None
render_tab_maker = None

def desenhar_workspace(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico, meu_gerenciador_jogos):
    """
        Como funciona: Calcula a posição e renderiza os componentes dinâmicos (braço da guitarra, controles, campo harmônico) no espaço virtual.
    """
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
    
    desenhar_painel_superior(tela, estado, fontes, configs)
    if hasattr(estado, 'menu_superior'):
        estado.menu_superior.desenhar(tela, fontes['ui'], estado)

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
    estado.rect_voltar_tab = pygame.Rect(largura - 180, 20, 140, 40)
    pygame.draw.rect(tela, (0, 120, 215), estado.rect_voltar_tab, border_radius=8)
    txt_v = fontes['ui'].render('<< VOLTAR', True, (255, 255, 255))
    tela.blit(txt_v, (estado.rect_voltar_tab.centerx - txt_v.get_width() // 2, estado.rect_voltar_tab.centery - txt_v.get_height() // 2))
    
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
    Renderiza a interface do Criador de Tablaturas.
    """
    global render_tab_maker
    if render_tab_maker is None:
        render_tab_maker = RenderizadorCriadorTablatura(tela, largura, altura)
        
    render_tab_maker.renderizar()
    
    # Botão voltar (sobreposto para garantir saída)
    estado.rect_voltar_criacao = pygame.Rect(largura - 180, 20, 140, 40)
    pygame.draw.rect(tela, (231, 76, 60), estado.rect_voltar_criacao, border_radius=8)
    txt_v = fontes['ui'].render('<< SAIR', True, BRANCO)
    tela.blit(txt_v, (estado.rect_voltar_criacao.centerx - txt_v.get_width() // 2, estado.rect_voltar_criacao.centery - txt_v.get_height() // 2))

def desenhar_tudo(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico, meu_gerenciador_jogos):
    tela.fill(FUNDO_ESCURO)
    desenhar_workspace(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico, meu_gerenciador_jogos)
    desenhar_ui_fixa(tela, estado, fontes, meu_gravador, configs, meu_gerenciador_jogos, meu_campo_harmonico)
    pygame.display.flip()
