# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================
import pygame
import sys
import config 
import Modulos.modulo_metronomo as modulo_metronomo
import Modulos.modulo_gravador as modulo_gravador
import Modulos.modulo_processamento as modulo_processamento
from Modulos.modulo_campo_harmonico import CampoHarmonico
import estado_app
import fabrica_escalas
import renderizador_ui
import controlador_eventos
from Jogos.Jogos_interativos import GerenciadorJogos
from Modulos.modulo_perfil import GerenciadorPerfil
import Modulos.modulo_camera as modulo_camera

def main():
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    try: pygame.mixer.Sound(buffer=bytearray(b'\x00' * 4096)).play()
    except: pass
    tela = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Guitar Studio IA")
    meu_gerenciador_jogos = GerenciadorJogos()
    
    # =========================================================================
    # 1. INICIALIZA A MESA GIGANTE 
    # =========================================================================
    
    minha_camera = modulo_camera.CameraWorkspace(tela.get_width(), tela.get_height())
    
    # 2. USA O TAMANHO REAL DA TELA: O layout nasce normal, compacto e centralizado!
    estado = estado_app.EstadoGlobal(tela.get_width(), tela.get_height())
    estado.LARGURA_TELA = tela.get_width()
    estado.ALTURA_TELA = tela.get_height()

    x_base = estado.dragger_guitarra.x
    y_virtual_caixa = estado.dragger_guitarra.y + estado.ALTURA_BRACO + 250
    
    minhas_configs = config.Configuracoes(x_base + 20, y_virtual_caixa + 60)
    meu_metronomo = modulo_metronomo.Metronomo(x_base + 50, y_virtual_caixa + 80)
    meu_campo_harmonico = CampoHarmonico()
    meu_gravador = modulo_gravador.GravadorAudio(device_id=3)
    meu_processador = modulo_processamento.ProcessadorAudio()
    
    estado.gerenciador_perfil = GerenciadorPerfil()
    estado.gerenciador_perfil.carregar_ultimo_perfil(estado, minhas_configs, meu_campo_harmonico, meu_gravador)
    dicionario_escalas = fabrica_escalas.gerar_modulos(estado, minhas_configs)
    
    nome_fonte = minhas_configs.get_fonte()
    fontes = {
        'ui': pygame.font.SysFont(nome_fonte, 18, bold=True),
        'pequena': pygame.font.SysFont(nome_fonte, 15, bold=True),
        'titulo': pygame.font.SysFont(nome_fonte, 22, bold=True),
        'notas': pygame.font.SysFont(nome_fonte, 20, bold=True)
    }

    jogo_aberto_anteriormente = False
    memoria_botao_ia = False

    # Salva a função original do mouse antes de fazer a mágica
    original_get_pos = pygame.mouse.get_pos

    while not estado.solicitou_saida:
        # =====================================================================
        # MÁGICA DA CÂMERA: Captura o mouse real e converte para o virtual
        # =====================================================================
        pos_mouse_real = original_get_pos()
        pos_mouse_virtual = minha_camera.obter_mouse_virtual(pos_mouse_real)
        
        # Engana o Pygame! Todos os outros arquivos agora usam a coordenada da mesa gigante!
        pygame.mouse.get_pos = lambda: pos_mouse_virtual

        eventos_traduzidos = []
        for evento in pygame.event.get():
            # A Câmera tenta agir primeiro (Para o Zoom e Arrasto)
            if minha_camera.tratar_eventos_camera(evento, pos_mouse_real):
                continue # Se for evento da câmera, não passa pras escalas!
                
            # Traduz os cliques para o mundo virtual
            if evento.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                evt_dict = evento.dict.copy()
                evt_dict['pos'] = minha_camera.obter_mouse_virtual(evento.pos)
                if 'rel' in evt_dict:
                    evt_dict['rel'] = (evt_dict['rel'][0] / minha_camera.zoom, evt_dict['rel'][1] / minha_camera.zoom)
                eventos_traduzidos.append(pygame.event.Event(evento.type, evt_dict))
            else:
                eventos_traduzidos.append(evento)
        # =====================================================================
        
        meu_metronomo.processar_logica(pos_mouse_virtual, estado)
        minhas_configs.processar_logica(pos_mouse_virtual)

        if estado.tela_jogo_ativa and not jogo_aberto_anteriormente:
            memoria_botao_ia = getattr(estado, 'analise_ativa', getattr(estado, 'ia_ligada', False))
            estado.analise_ativa = True
            estado.ia_ligada = True
            for func_name in ['iniciar_gravacao', 'start', 'iniciar', 'iniciar_stream']:
                if hasattr(meu_gravador, func_name):
                    try: getattr(meu_gravador, func_name)()
                    except: pass
            jogo_aberto_anteriormente = True

        elif not estado.tela_jogo_ativa and jogo_aberto_anteriormente:
            estado.analise_ativa = memoria_botao_ia
            estado.ia_ligada = memoria_botao_ia
            if not memoria_botao_ia:
                for func_name in ['parar_gravacao', 'stop', 'parar', 'parar_stream']:
                    if hasattr(meu_gravador, func_name):
                        try: getattr(meu_gravador, func_name)()
                        except: pass
            meu_processador.processar_logica_continua(meu_gravador, estado)
            jogo_aberto_anteriormente = False

        meu_processador.processar_logica_continua(meu_gravador, estado)

        if estado.tela_jogo_ativa and meu_gerenciador_jogos.jogo_id_ativo == "acerte_a_nota":
            nota_para_envio = getattr(estado, 'freq_detectada', "") 
            if meu_gerenciador_jogos.jogo_instancia:
                meu_gerenciador_jogos.jogo_instancia.atualizar_audio(nota_para_envio)
        
        if nome_fonte != minhas_configs.get_fonte():
            nome_fonte = minhas_configs.get_fonte()
            fontes = {k: pygame.font.SysFont(nome_fonte, v, bold=True) for k, v in zip(fontes.keys(), [18, 15, 22, 20])}

        controlador_eventos.processar(
            eventos_traduzidos, estado, minhas_configs,
            dicionario_escalas, meu_metronomo, meu_processador, meu_gravador,
            meu_campo_harmonico, meu_gerenciador_jogos
        )

        # =====================================================================
        # NOVO RENDERIZADOR: PINTA NA MESA VIRTUAL E COLA NO MONITOR
        # =====================================================================
        minha_camera.tela_virtual.fill((20, 20, 20)) # Fundo base da mesa
        
        renderizador_ui.desenhar_tudo(
            minha_camera.tela_virtual, estado, minhas_configs, dicionario_escalas, 
            fontes, meu_metronomo, meu_processador, meu_gravador,
            meu_campo_harmonico, meu_gerenciador_jogos
        )
        
        # Agora a câmera processa o que foi pintado e exibe na sua tela
        tela.fill((0, 0, 0)) # Borda preta caso arraste demais
        minha_camera.renderizar(tela)
        pygame.display.flip()

    # Devolve a função original para fechar limpo
    pygame.mouse.get_pos = original_get_pos
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()