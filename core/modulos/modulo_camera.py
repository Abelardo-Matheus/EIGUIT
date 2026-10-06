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

    # Zoom suave (smoothscale) e mais bonito e mais caro; o modo leve usa o rapido
    zoom_suave = False

    def area_visivel(self, largura_monitor, altura_monitor, folga=2):
        """Retangulo da mesa virtual que aparece no monitor agora."""
        largura = int(largura_monitor / self.zoom) + folga
        altura = int(altura_monitor / self.zoom) + folga
        area = pygame.Rect(int(self.offset_x) - 1, int(self.offset_y) - 1, largura, altura)
        return area.clip(self.tela_virtual.get_rect())

    def renderizar(self, tela_monitor):
        """
            Como funciona: Copia para o monitor so o pedaco visivel da mesa.
            Com zoom, escala apenas esse pedaco (antes escalava a mesa inteira
            de 4000x3000 a cada quadro, o que custava dezenas de ms).
        """
        w_mon, h_mon = tela_monitor.get_size()
        if self.zoom == 1.0:
            tela_monitor.blit(self.tela_virtual, (-self.offset_x, -self.offset_y))
            return
        area = self.area_visivel(w_mon, h_mon)
        if area.width <= 0 or area.height <= 0:
            return
        destino = (max(1, int(round(area.width * self.zoom))),
                   max(1, int(round(area.height * self.zoom))))
        pedaco = self.tela_virtual.subsurface(area)
        if self.zoom_suave:
            try:
                escalado = pygame.transform.smoothscale(pedaco, destino)
            except (ValueError, pygame.error):
                escalado = pygame.transform.scale(pedaco, destino)
        else:
            escalado = pygame.transform.scale(pedaco, destino)
        tela_monitor.blit(escalado, ((area.x - self.offset_x) * self.zoom,
                                     (area.y - self.offset_y) * self.zoom))
