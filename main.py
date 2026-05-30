import pygame
import sys
from Core import config, i18n
import Modulos.modulo_metronomo as modulo_metronomo
import Modulos.modulo_processamento as modulo_processamento
from Modulos.modulo_campo_harmonico import CampoHarmonico
from Core import estado_app
from Interface import fabrica_escalas
from Interface import renderizador_ui
from Core import controlador_eventos
from Jogos.Jogos_interativos import GerenciadorJogos
from Modulos.modulo_perfil import GerenciadorPerfil
import Modulos.modulo_camera as modulo_camera
from AudioEngine.global_audio import GlobalAudioEngine
from Interface import tela_login

def main():
    """
        Como funciona: Inicializa o ambiente Pygame, carrega as configurações do usuário, autentica o acesso e inicia o loop principal de eventos e renderização.
        Para que serve: Ponto de entrada do sistema que orquestra a inicialização e o ciclo de vida da aplicação.
        Onde é usada: Executado diretamente ao iniciar o software via main.py.
    """
    usuario_logado = tela_login.iniciar_fluxo_autenticacao()
    if not usuario_logado:
        print('Autenticação cancelada. Saindo...')
        sys.exit()
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    try:
        pygame.mixer.Sound(buffer=bytearray(b'\x00' * 4096)).play()
    except:
        pass
    tela = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption('Guitar Studio IA')
    meu_gerenciador_jogos = GerenciadorJogos()
    import Modulos.modulo_camera as modulo_camera
    minha_camera = modulo_camera.CameraWorkspace(tela.get_width(), tela.get_height())
    estado = estado_app.EstadoGlobal(tela.get_width(), tela.get_height())
    estado.usuario_id_logado = usuario_logado['id']
    estado.email_usuario = usuario_logado['email']
    from BD.gerenciador_remoto_db import GerenciadorDB
    db = GerenciadorDB()
    estado.favoritos_songsterr = db.obter_favoritos(estado.usuario_id_logado)
    print(f'[CLOUD] {len(estado.favoritos_songsterr)} favoritos carregados da conta.')
    estado.LARGURA_TELA = tela.get_width()
    estado.ALTURA_TELA = tela.get_height()
    estado.camera = minha_camera
    x_base = estado.dragger_guitarra.x
    y_virtual_caixa = estado.dragger_guitarra.y + estado.ALTURA_BRACO + 250
    minhas_configs = config.Configuracoes(x_base + 20, y_virtual_caixa + 60)
    meu_metronomo = modulo_metronomo.Metronomo(x_base + 50, y_virtual_caixa + 80)
    meu_campo_harmonico = CampoHarmonico()
    from AudioEngine.global_audio import GlobalAudioEngine
    motor_audio = GlobalAudioEngine()
    meu_gravador = motor_audio
    meu_processador = modulo_processamento.ProcessadorAudio()
    estado.gerenciador_perfil = GerenciadorPerfil()
    estado.gerenciador_perfil.carregar_ultimo_perfil(estado, minhas_configs, meu_campo_harmonico, meu_gravador)
    dicionario_escalas = fabrica_escalas.gerar_modulos(estado, minhas_configs)
    nome_fonte = minhas_configs.get_fonte()
    fontes = {'ui': pygame.font.SysFont(nome_fonte, 18, bold=True), 'pequena': pygame.font.SysFont(nome_fonte, 15, bold=True), 'titulo': pygame.font.SysFont(nome_fonte, 22, bold=True), 'notas': pygame.font.SysFont(nome_fonte, 20, bold=True)}
    jogo_aberto_anteriormente = False
    memoria_botao_ia = False
    original_get_pos = pygame.mouse.get_pos
    relogio = pygame.time.Clock()
    while not estado.solicitou_saida:
        relogio.tick(60)
        motor_audio.atualizar_analise_ia(estado.afinador_threshold)
        estado.freq_detectada = motor_audio.freq_detectada
        estado.notas_detectadas_ia = motor_audio.notas_polifonicas
        import math
        agora = pygame.time.get_ticks()
        nota_instante = '--'
        try:
            f = float(estado.freq_detectada)
            if f >= 20.0:
                valor_exato = 12 * math.log2(f / 440.0)
                semitons = round(valor_exato)
                desvio = valor_exato - semitons
                if abs(desvio) <= 0.35:
                    indice_nota = (semitons + 9) % 12
                    nota_instante = estado.notas_base[int(indice_nota)]
        except:
            pass
        if nota_instante != '--':
            estado.nota_atual_detectada = nota_instante
            estado.tempo_ultima_nota = agora
        elif agora - estado.tempo_ultima_nota > estado.afinador_persistencia:
            estado.nota_atual_detectada = '--'
        pos_mouse_real = original_get_pos()
        estado.pos_mouse_real = pos_mouse_real
        pos_mouse_virtual = minha_camera.obter_mouse_virtual(pos_mouse_real)
        pygame.mouse.get_pos = lambda: pos_mouse_virtual
        eventos_traduzidos = []
        for evento in pygame.event.get():
            if minha_camera.tratar_eventos_camera(evento, pos_mouse_real):
                continue
            if evento.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                evt_dict = evento.dict.copy()
                evt_dict['pos'] = minha_camera.obter_mouse_virtual(evento.pos)
                if 'rel' in evt_dict:
                    evt_dict['rel'] = (evt_dict['rel'][0] / minha_camera.zoom, evt_dict['rel'][1] / minha_camera.zoom)
                eventos_traduzidos.append(pygame.event.Event(evento.type, evt_dict))
            else:
                eventos_traduzidos.append(evento)
        meu_metronomo.processar_logica(pos_mouse_virtual, estado)
        minhas_configs.processar_logica(pos_mouse_virtual)
        if nome_fonte != minhas_configs.get_fonte():
            nome_fonte = minhas_configs.get_fonte()
            fontes = {k: pygame.font.SysFont(nome_fonte, v, bold=True) for k, v in zip(fontes.keys(), [18, 15, 22, 20])}
        controlador_eventos.processar(eventos_traduzidos, estado, minhas_configs, dicionario_escalas, meu_metronomo, meu_processador, motor_audio, meu_campo_harmonico, meu_gerenciador_jogos)
        meu_processador.processar_logica_continua(motor_audio, estado)
        if estado.tela_jogo_ativa and meu_gerenciador_jogos.jogo_id_ativo == 'acerte_a_nota':
            pass
        minha_camera.tela_virtual.fill((20, 20, 20))
        renderizador_ui.desenhar_workspace(minha_camera.tela_virtual, estado, minhas_configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico, meu_gerenciador_jogos)
        tela.fill((0, 0, 0))
        minha_camera.renderizar(tela)
        renderizador_ui.desenhar_ui_fixa(tela, estado, fontes, meu_gravador, minhas_configs, meu_gerenciador_jogos)
        pygame.display.flip()
    pygame.mouse.get_pos = original_get_pos
    pygame.quit()
    sys.exit()
if __name__ == '__main__':
    main()