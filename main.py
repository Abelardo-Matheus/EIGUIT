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

def main():
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    try: pygame.mixer.Sound(buffer=bytearray(b'\x00' * 4096)).play()
    except: pass
    tela = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Guitar Studio IA")

    estado = estado_app.EstadoGlobal(tela.get_width(), tela.get_height())
    
    # Criamos uma coordenada virtual baseada no dragger_guitarra para substituir as variáveis deletadas
    x_base = estado.dragger_guitarra.x
    y_virtual_caixa = estado.dragger_guitarra.y + estado.ALTURA_BRACO + 250
    
    minhas_configs = config.Configuracoes(x_base + 20, y_virtual_caixa + 60)
    meu_metronomo = modulo_metronomo.Metronomo(x_base + 50, y_virtual_caixa + 80)
    
    meu_campo_harmonico = CampoHarmonico()
    meu_gravador = modulo_gravador.GravadorAudio(device_id=3)
    meu_processador = modulo_processamento.ProcessadorAudio()

    dicionario_escalas = fabrica_escalas.gerar_modulos(estado, minhas_configs)
    
    nome_fonte = minhas_configs.get_fonte()
    fontes = {
        'ui': pygame.font.SysFont(nome_fonte, 18, bold=True),
        'pequena': pygame.font.SysFont(nome_fonte, 15, bold=True),
        'titulo': pygame.font.SysFont(nome_fonte, 22, bold=True),
        'notas': pygame.font.SysFont(nome_fonte, 20, bold=True)
    }

    while not estado.solicitou_saida:
        pos_mouse = pygame.mouse.get_pos()
        
        meu_metronomo.processar_logica(pygame.mouse.get_pos(), estado)
        meu_processador.processar_logica_continua(meu_gravador, estado)
        minhas_configs.processar_logica(pos_mouse)
        
        if nome_fonte != minhas_configs.get_fonte():
            nome_fonte = minhas_configs.get_fonte()
            fontes = {k: pygame.font.SysFont(nome_fonte, v, bold=True) for k, v in zip(fontes.keys(), [18, 15, 22, 20])}

        controlador_eventos.processar(
            pygame.event.get(), estado, minhas_configs,
            dicionario_escalas, meu_metronomo, meu_processador, meu_gravador,
            meu_campo_harmonico 
        )

        renderizador_ui.desenhar_tudo(
            tela, estado, minhas_configs, dicionario_escalas, 
            fontes, meu_metronomo, meu_processador, meu_gravador,
            meu_campo_harmonico 
        )
        
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()