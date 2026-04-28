
import asyncio
import sys



print("1. O código Python começou a rodar!")

NO_NAVEGADOR = sys.platform in ["emscripten", "wasm32"]
print(f"2. Estamos no navegador? {NO_NAVEGADOR}")

import pygame
print("3. Pygame importado com sucesso!")


# Importações dos seus módulos
import config 
import Modulos.modulo_metronomo as modulo_metronomo
import Modulos.modulo_gravador as modulo_gravador
print("4. Gravador importado (Escudo funcionou)!")

import Modulos.modulo_processamento as modulo_processamento
print("5. Processador importado (Escudo funcionou)!")

import estado_app
import fabrica_escalas
import renderizador_ui
import controlador_eventos
print("6. Todos os módulos importados! Indo iniciar o jogo...")


async def main():
    print("7. Entrou na função main async!")
    pygame.mixer.pre_init(44100, -16, 2, 1024)
    pygame.init()
    print("8. Pygame inicializado!")
    # Aumentando um pouco o buffer para o navegador não "engasgar" o áudio
    pygame.mixer.pre_init(44100, -16, 2, 1024)
    pygame.init()
    
    try: 
        pygame.mixer.Sound(buffer=bytearray(b'\x00' * 4096)).play()
    except: 
        pass

    # CORREÇÃO 1: Tela
    # Se estiver na Web, usa uma resolução fixa padrão (1280x720). Se for PC, usa FullScreen.
    if NO_NAVEGADOR:
        tela = pygame.display.set_mode((1280, 720))
    else:
        tela = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        
    pygame.display.set_caption("EIGUIT")

    estado = estado_app.EstadoGlobal(tela.get_width(), tela.get_height())
    minhas_configs = config.Configuracoes(estado.OFFSET_X + 20, estado.Y_CAIXA + 60)
    
    meu_metronomo = modulo_metronomo.Metronomo(estado.OFFSET_X + 50, estado.Y_CAIXA + 80)
    
    # CORREÇÃO 2: Gravador
    # Não força o device_id=3 se estiver no navegador
    if NO_NAVEGADOR:
        meu_gravador = modulo_gravador.GravadorAudio() 
    else:
        meu_gravador = modulo_gravador.GravadorAudio(device_id=3)
        
    meu_processador = modulo_processamento.ProcessadorAudio()

    dicionario_escalas = fabrica_escalas.gerar_modulos(estado, minhas_configs)
    
    nome_fonte = minhas_configs.get_fonte()
    
    # CORREÇÃO 3: Fontes Seguras
    # O navegador carrega a fonte padrão do Pygame (Font=None) para não travar
    if NO_NAVEGADOR:
        fontes = {
            'ui': pygame.font.Font(None, 24),
            'pequena': pygame.font.Font(None, 20),
            'titulo': pygame.font.Font(None, 30),
            'notas': pygame.font.Font(None, 26)
        }
    else:
        fontes = {
            'ui': pygame.font.SysFont(nome_fonte, 18, bold=True),
            'pequena': pygame.font.SysFont(nome_fonte, 15, bold=True),
            'titulo': pygame.font.SysFont(nome_fonte, 22, bold=True),
            'notas': pygame.font.SysFont(nome_fonte, 20, bold=True)
        }

    while not estado.solicitou_saida:
        pos_mouse = pygame.mouse.get_pos()
        
        meu_metronomo.processar_logica(pos_mouse)
        meu_processador.processar_logica_continua(meu_gravador, estado)
        minhas_configs.processar_logica(pos_mouse)
        
        if nome_fonte != minhas_configs.get_fonte():
            nome_fonte = minhas_configs.get_fonte()
            if not NO_NAVEGADOR:
                fontes = {k: pygame.font.SysFont(nome_fonte, v, bold=True) for k, v in zip(fontes.keys(), [18, 15, 22, 20])}

        controlador_eventos.processar(
            pygame.event.get(), estado, minhas_configs, 
            dicionario_escalas, meu_metronomo, meu_processador, meu_gravador
        )

        renderizador_ui.desenhar_tudo(
            tela, estado, minhas_configs, dicionario_escalas, 
            fontes, meu_metronomo, meu_processador, meu_gravador
        )
        
        pygame.display.flip()

        await asyncio.sleep(0)
        

    pygame.quit()
    # No navegador, o sys.exit() pode quebrar o loop do WebAssembly, então evitamos.
    if not NO_NAVEGADOR:
        sys.exit()

if __name__ == "__main__":
    asyncio.run(main())