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


def main():
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    try: pygame.mixer.Sound(buffer=bytearray(b'\x00' * 4096)).play()
    except: pass
    tela = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Guitar Studio IA")
    meu_gerenciador_jogos = GerenciadorJogos()
    
    # 1. CRIAMOS TODOS OS COMPONENTES ZERADOS
    estado = estado_app.EstadoGlobal(tela.get_width(), tela.get_height())
    x_base = estado.dragger_guitarra.x
    y_virtual_caixa = estado.dragger_guitarra.y + estado.ALTURA_BRACO + 250
    
    minhas_configs = config.Configuracoes(x_base + 20, y_virtual_caixa + 60)
    meu_metronomo = modulo_metronomo.Metronomo(x_base + 50, y_virtual_caixa + 80)
    meu_campo_harmonico = CampoHarmonico()
    meu_gravador = modulo_gravador.GravadorAudio(device_id=3)
    meu_processador = modulo_processamento.ProcessadorAudio()
    
    # 2. AUTOLOAD DO PERFIL (Injeta as configs do JSON nos objetos recém-criados)
    estado.gerenciador_perfil = GerenciadorPerfil()
    estado.gerenciador_perfil.carregar_ultimo_perfil(estado, minhas_configs, meu_campo_harmonico, meu_gravador)
    
    # 3. GERA OS MÓDULOS (Agora com a num_casas e afinações corretas do Perfil)
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

    while not estado.solicitou_saida:
        pos_mouse = pygame.mouse.get_pos()
        
        meu_metronomo.processar_logica(pygame.mouse.get_pos(), estado)
        minhas_configs.processar_logica(pos_mouse)

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
        
        # O FONT CHANGER QUE ATUALIZA AUTOMÁTICO SE O JSON MUDAR A FONTE!
        if nome_fonte != minhas_configs.get_fonte():
            nome_fonte = minhas_configs.get_fonte()
            fontes = {k: pygame.font.SysFont(nome_fonte, v, bold=True) for k, v in zip(fontes.keys(), [18, 15, 22, 20])}

        controlador_eventos.processar(
            pygame.event.get(), estado, minhas_configs,
            dicionario_escalas, meu_metronomo, meu_processador, meu_gravador,
            meu_campo_harmonico, meu_gerenciador_jogos
        )

        renderizador_ui.desenhar_tudo(
            tela, estado, minhas_configs, dicionario_escalas, 
            fontes, meu_metronomo, meu_processador, meu_gravador,
            meu_campo_harmonico, meu_gerenciador_jogos
        )
        
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()