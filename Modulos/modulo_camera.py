import pygame

class CameraWorkspace:
    """
        Como funciona: Define a estrutura e estado do componente 'CameraWorkspace'.
        Para que serve: Atua como o modelo principal para instâncias de 'CameraWorkspace'.
        Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_camera'.
    """

    def __init__(self, largura_monitor, altura_monitor):
        """
            Como funciona: Inicializa os atributos e o estado inicial da instância.
            Para que serve: Prepara o objeto para ser utilizado no ciclo de vida da aplicação.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_camera'.
        """
        self.zoom = 1.0
        self.largura_mesa = 4000
        self.altura_mesa = 3000
        self.tela_virtual = pygame.Surface((self.largura_mesa, self.altura_mesa))
        self.offset_x = 0
        self.offset_y = 0
        self.arrastando = False
        self.mouse_inicio = (0, 0)
        self.camera_inicio = (0, 0)

    def obter_mouse_virtual(self, pos_real):
        """
            Como funciona: Acessa e formata dados internos ou de configuração.
            Para que serve: Retorna as informações solicitadas sobre 'mouse virtual'.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_camera'.
        """
        mx = pos_real[0] / self.zoom + self.offset_x
        my = pos_real[1] / self.zoom + self.offset_y
        return (int(mx), int(my))

    def tratar_eventos_camera(self, evento, pos_real):
        """
            Como funciona: Verifica colisões e processa inputs do mouse/teclado.
            Para que serve: Mapeia ações do usuário para atualizações de estado.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_camera'.
        """
        teclas = pygame.key.get_pressed()
        if evento.type == pygame.MOUSEWHEEL and (teclas[pygame.K_LCTRL] or teclas[pygame.K_RCTRL]):
            self.zoom += evento.y * 0.05
            self.zoom = max(0.4, min(self.zoom, 2.5))
            mx_virt, my_virt = self.obter_mouse_virtual(pos_real)
            self.offset_x = mx_virt - pos_real[0] / self.zoom
            self.offset_y = my_virt - pos_real[1] / self.zoom
            return True
        if evento.type == pygame.MOUSEBUTTONDOWN and (evento.button == 2 or (evento.button == 1 and teclas[pygame.K_LALT])):
            self.arrastando = True
            self.mouse_inicio = pos_real
            self.camera_inicio = (self.offset_x, self.offset_y)
            return True
        if evento.type == pygame.MOUSEBUTTONUP and (evento.button == 2 or evento.button == 1):
            self.arrastando = False
        if evento.type == pygame.MOUSEMOTION and self.arrastando:
            dx = (pos_real[0] - self.mouse_inicio[0]) / self.zoom
            dy = (pos_real[1] - self.mouse_inicio[1]) / self.zoom
            self.offset_x = self.camera_inicio[0] - dx
            self.offset_y = self.camera_inicio[1] - dy
            return True
        return False

    def renderizar(self, tela_monitor):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'renderizar'.
            Para que serve: Realiza as tarefas fundamentais de 'renderizar' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'renderizar'.
        """
        if self.zoom != 1.0:
            w_zoom = int(self.largura_mesa * self.zoom)
            h_zoom = int(self.altura_mesa * self.zoom)
            tela_escala = pygame.transform.scale(self.tela_virtual, (w_zoom, h_zoom))
            tela_monitor.blit(tela_escala, (-self.offset_x * self.zoom, -self.offset_y * self.zoom))
        else:
            tela_monitor.blit(self.tela_virtual, (-self.offset_x, -self.offset_y))