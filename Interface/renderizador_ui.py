import pygame
import math
import Modulos.escalas as escalas
from Interface import gerenciador_interface
from Core.constantes_ui import *
from Jogos.Jogos_interativos import GerenciadorJogos
import Modulos.modulos_estudos as modulo_estudos
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

def desenhar_workspace(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico, meu_gerenciador_jogos):
    """
        Como funciona: Calcula a posição e renderiza os componentes dinâmicos (braço da guitarra, controles, campo harmônico) no espaço virtual.
        Para que serve: Renderizar a área de trabalho interativa respeitando o zoom e a posição da câmera.
        Onde é usada: Executado no loop de desenho principal dentro de renderizador_ui.py.
    """
    if hasattr(estado, 'lista_guitarras'):
        for guit in estado.lista_guitarras:
            desenhar_guitarra(tela, estado, configs, fontes, meu_processador, meu_campo_harmonico, dragger_obj=guit)
    else:
        desenhar_guitarra(tela, estado, configs, fontes, meu_processador, meu_campo_harmonico)
    
    # Novos controles de instrumento (Casas, Afinacao, Instrumento) - Seguem a camera
    desenhar_controles_instrumento(tela, estado, fontes, configs)
    
    desenhar_acordes_arrastaveis(tela, estado, meu_campo_harmonico, fontes)
    desenhar_painel_cores(tela, estado, fontes)
    desenhar_bloco_nota_atual(tela, estado, fontes, configs)
    desenhar_controles_playback(tela, estado, meu_metronomo, fontes['ui'], configs)
    if hasattr(estado, 'lista_tabs'):
        for tab in estado.lista_tabs:
            tab.desenhar(tela, fontes)
    desenhar_secoes_inferiores_expansiveis(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_gerenciador_jogos)

def desenhar_ui_fixa(tela, estado, fontes, meu_gravador, configs, meu_gerenciador_jogos):
    """
        Como funciona: Renderiza elementos que não seguem o movimento da câmera, como a topbar, sidebar de notas e painéis de configuração.
        Para que serve: Garantir que os controles de navegação e HUD permaneçam visíveis e acessíveis.
        Onde é usada: Executado após o desenho do workspace para sobrepor a UI ao conteúdo.
    """
    largura_real = tela.get_width()
    altura_real = tela.get_height()
    
    # 2. Telas em destaque (Estudo / Jogo)
    if getattr(estado, 'tab_tela_cheia_ativa', False) and hasattr(estado, 'tab_focada'):
        _desenhar_tela_cheia_tablatura(tela, largura_real, altura_real, estado, fontes)
    elif getattr(estado, 'tela_estudo_ativa', False):
        if not hasattr(estado, 'gerenciador_estudos'):
            estado.gerenciador_estudos = modulo_estudos.GerenciadorEstudos()
        estado.gerenciador_estudos.desenhar_tela_estudo(tela, largura_real, altura_real, estado, fontes)
    elif estado.tela_jogo_ativa:
        meu_gerenciador_jogos.desenhar_tela_jogo(tela, largura_real, altura_real, estado, meu_gravador, configs)
    
    # 3. BARRA SUPERIOR E MENUS (SEMPRE NO TOPO)
    desenhar_painel_superior(tela, estado, fontes, configs)
    if hasattr(estado, 'menu_superior'):
        estado.menu_superior.desenhar(tela, fontes['ui'], estado)

    # 4. Elementos sobrepostos (Perfil / Menus de Contexto)
    if hasattr(estado, 'gerenciador_perfil') and estado.gerenciador_perfil.ativo:
        estado.gerenciador_perfil.desenhar(tela, fontes['titulo'], fontes['ui'], estado)
    if hasattr(estado, 'menu_contexto'):
        estado.menu_contexto.desenhar(tela, fontes['ui'])

def _desenhar_tela_cheia_tablatura(tela, largura, altura, estado, fontes):
    """
        Como funciona: Executa o fluxo lógico necessário para a operação ' desenhar tela cheia tablatura'.
        Para que serve: Realiza as tarefas fundamentais de ' desenhar tela cheia tablatura' dentro do contexto do módulo.
        Onde é usada: Utilizado internamente para gerenciar comportamentos de ' desenhar tela cheia tablatura'.
    """
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
    if hasattr(estado, 'menu_superior'):
        estado.menu_superior.desenhar(tela, fontes['ui'], estado)

def desenhar_tudo(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico, meu_gerenciador_jogos):
    """
        Como funciona: Utiliza funções de renderização do Pygame para desenhar na tela.
        Para que serve: Apresenta o elemento visual 'tudo' na interface gráfica.
        Onde é usada: Chamado a partir do módulo ou classe base de 'renderizador_ui'.
    """
    tela.fill(FUNDO_ESCURO)
    desenhar_workspace(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico, meu_gerenciador_jogos)
    desenhar_ui_fixa(tela, estado, fontes, meu_gravador, configs, meu_gerenciador_jogos)
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
            caminho_imagem = os.path.join(os.getcwd(), 'impressao_eiguit.png')
            pygame.image.save(imagem_recortada, caminho_imagem)
            if os.name == 'nt':
                os.startfile(caminho_imagem, 'print')
                print(f'[IMPRESSÃO] Imagem salva e enviada para o Windows: {caminho_imagem}')
        except Exception as e:
            print(f'[ERRO IMPRESSÃO] Não foi possível gerar a impressão: {e}')
        estado.solicitou_impressao = False