# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================
import pygame
import math 
import Modulos.escalas as escalas
from Interface import gerenciador_interface
from Core.constantes_ui import *
from Jogos.Jogos_interativos import GerenciadorJogos
import Modulos.modulos_estudos as modulo_estudos

# Importação dos Novos Componentes Modulares
from Interface.Componentes import (
    desenhar_painel_superior,
    desenhar_guitarra,
    desenhar_acordes_arrastaveis,
    desenhar_controles_playback,
    desenhar_bloco_nota_atual,
    desenhar_painel_cores,
    desenhar_secoes_inferiores_expansiveis
)
from Interface.Componentes.utils import obter_grau, equivalencia_notas

def desenhar_workspace(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico, meu_gerenciador_jogos):
    """Desenha os elementos que pertencem à mesa virtual (podem ser arrastados e zoomados)."""
    # 1. Desenho do Workspace Físico
    desenhar_painel_superior(tela, estado, fontes)
    
    if hasattr(estado, 'lista_guitarras'):
        for guit in estado.lista_guitarras:
            desenhar_guitarra(tela, estado, configs, fontes, meu_processador, meu_campo_harmonico, dragger_obj=guit)
    else:
        desenhar_guitarra(tela, estado, configs, fontes, meu_processador, meu_campo_harmonico)

    desenhar_acordes_arrastaveis(tela, estado, meu_campo_harmonico, fontes)
    desenhar_painel_cores(tela, estado, fontes)
    desenhar_bloco_nota_atual(tela, estado, fontes)
    
    # Novo Componente de Playback (Metrônomo)
    desenhar_controles_playback(tela, estado, meu_metronomo, fontes['ui'])
    
    # Blocos de Tablatura Songsterr
    if hasattr(estado, 'lista_tabs'):
        for tab in estado.lista_tabs:
            tab.desenhar(tela, fontes)
    
    desenhar_secoes_inferiores_expansiveis(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_gerenciador_jogos)

def desenhar_ui_fixa(tela, estado, fontes, meu_gravador, configs, meu_gerenciador_jogos):
    """Desenha os elementos que ficam travados na tela (Menus, Modais, Telas Cheias)."""
    largura_real = tela.get_width()
    altura_real = tela.get_height()

    # 1. Telas Cheias (Estudos/Jogos/Tablatura Full)
    if getattr(estado, 'tab_tela_cheia_ativa', False) and hasattr(estado, 'tab_focada'):
        _desenhar_tela_cheia_tablatura(tela, largura_real, altura_real, estado, fontes)
        return # Trava a UI atrás

    if getattr(estado, 'tela_estudo_ativa', False):
        if not hasattr(estado, 'gerenciador_estudos'):
            estado.gerenciador_estudos = modulo_estudos.GerenciadorEstudos()
        estado.gerenciador_estudos.desenhar_tela_estudo(tela, largura_real, altura_real, estado, fontes)
    elif estado.tela_jogo_ativa: 
        meu_gerenciador_jogos.desenhar_tela_jogo(tela, largura_real, altura_real, estado, meu_gravador, configs)

def _desenhar_tela_cheia_tablatura(tela, largura, altura, estado, fontes):
    tab = estado.tab_focada
    # Fundo Escuro (Padrão do Software)
    tela.fill(FUNDO_ESCURO)
    
    # Cabeçalho da Visualização
    pygame.draw.rect(tela, (30, 30, 35), (0, 0, largura, 80))
    pygame.draw.line(tela, (60, 60, 65), (0, 80), (largura, 80), 2)
    
    txt_t = fontes['titulo'].render(f"{tab.titulo}", True, (240, 240, 240))
    tela.blit(txt_t, (40, 20))
    
    txt_a = fontes['ui'].render(f"Artista: {tab.artista}", True, (160, 160, 160))
    tela.blit(txt_a, (40, 50))
    
    # Botão Voltar
    estado.rect_voltar_tab = pygame.Rect(largura - 180, 20, 140, 40)
    pygame.draw.rect(tela, (0, 120, 215), estado.rect_voltar_tab, border_radius=8)
    txt_v = fontes['ui'].render("<< VOLTAR", True, (255, 255, 255))
    tela.blit(txt_v, (estado.rect_voltar_tab.centerx - txt_v.get_width()//2, estado.rect_voltar_tab.centery - txt_v.get_height()//2))
    
    # Renderização da Tablatura em Toda a Tela (Usando o motor interno do componente)
    # Ajustamos temporariamente as propriedades para o modo escuro full
    original_fundo = tab.COR_FUNDO
    original_linha = tab.COR_LINHA
    tab.COR_FUNDO = FUNDO_ESCURO
    tab.COR_LINHA = (60, 60, 65)
    
    # Área de Desenho (Folha Digital)
    margem_x = 60
    largura_folha = largura - (margem_x * 2)
    tab._desenhar_visualizador_tab(tela, margem_x, 120, largura_folha, altura - 150, fontes)
    
    # Restaura cores originais do componente flutuante
    tab.COR_FUNDO = original_fundo
    tab.COR_LINHA = original_linha

    # 2. Menus Flutuantes e Modais
    if hasattr(estado, 'menu_superior'):
        estado.menu_superior.desenhar(tela, fontes['ui'], estado)
    if hasattr(estado, 'gerenciador_perfil'):
        estado.gerenciador_perfil.desenhar(tela, fontes['titulo'], fontes['ui'], estado) 
    if hasattr(estado, 'menu_contexto'):
        estado.menu_contexto.desenhar(tela, fontes['ui'])

def desenhar_tudo(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico, meu_gerenciador_jogos):
    """Mantido por compatibilidade, mas o ideal é usar as funções separadas."""
    tela.fill(FUNDO_ESCURO)
    desenhar_workspace(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico, meu_gerenciador_jogos)
    desenhar_ui_fixa(tela, estado, fontes, meu_gravador, configs, meu_gerenciador_jogos)

    # 4. Impressão Fotográfica (Roda escondido no final)
    if getattr(estado, 'solicitou_impressao', False):
        import os
        try:
            tela_w, tela_h = tela.get_size()
            x_guit = estado.dragger_guitarra.x if hasattr(estado, 'dragger_guitarra') else 100
            y_guit = estado.dragger_guitarra.y if hasattr(estado, 'dragger_guitarra') else 100
            largura = estado.LARGURA_BRACO
            altura = estado.ALTURA_BRACO
            
            x_captura = max(0, x_guit - 80)
            y_captura = max(0, y_guit - 80)
            largura_captura = min(tela_w - x_captura, largura + 160)
            altura_captura = min(tela_h - y_captura, altura + 160)
            
            rect_captura = pygame.Rect(x_captura, y_captura, largura_captura, altura_captura)
            imagem_recortada = tela.subsurface(rect_captura)
            caminho_imagem = os.path.join(os.getcwd(), "impressao_eiguit.png")
            pygame.image.save(imagem_recortada, caminho_imagem)
            
            if os.name == 'nt':
                os.startfile(caminho_imagem, "print")
                print(f"[IMPRESSÃO] Imagem salva e enviada para o Windows: {caminho_imagem}")
        except Exception as e:
            print(f"[ERRO IMPRESSÃO] Não foi possível gerar a impressão: {e}")
            
        estado.solicitou_impressao = False
