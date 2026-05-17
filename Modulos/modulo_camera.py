# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# =============================================================================

import pygame

class CameraWorkspace:
    def __init__(self, largura_monitor, altura_monitor):
        self.zoom = 1.0
        
        # O tamanho infinito da sua mesa (Workspace Gigante)
        self.largura_mesa = 4000
        self.altura_mesa = 3000
        
        # Cria o "Quadro Branco" gigante na memória
        self.tela_virtual = pygame.Surface((self.largura_mesa, self.altura_mesa))
        
        # Câmera inicia focada no canto superior esquerdo (onde o layout original nasce!)
        self.offset_x = 0
        self.offset_y = 0
        
        self.arrastando = False
        self.mouse_inicio = (0, 0)
        self.camera_inicio = (0, 0)

    def obter_mouse_virtual(self, pos_real):
        mx = (pos_real[0] / self.zoom) + self.offset_x
        my = (pos_real[1] / self.zoom) + self.offset_y
        return (int(mx), int(my))

    def tratar_eventos_camera(self, evento, pos_real):
        teclas = pygame.key.get_pressed()
        
        # --- ATALHO 1: ZOOM (CTRL + Scroll do Mouse) ---
        if evento.type == pygame.MOUSEWHEEL and (teclas[pygame.K_LCTRL] or teclas[pygame.K_RCTRL]):
            self.zoom += evento.y * 0.05 
            self.zoom = max(0.4, min(self.zoom, 2.5)) 
            
            mx_virt, my_virt = self.obter_mouse_virtual(pos_real)
            self.offset_x = mx_virt - (pos_real[0] / self.zoom)
            self.offset_y = my_virt - (pos_real[1] / self.zoom)
            return True
            
        # --- ATALHO 2: ARRASTAR A MESA (Botão do Meio ou ALT + Clique Esquerdo) ---
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
        if self.zoom != 1.0:
            w_zoom = int(self.largura_mesa * self.zoom)
            h_zoom = int(self.altura_mesa * self.zoom)
            tela_escala = pygame.transform.scale(self.tela_virtual, (w_zoom, h_zoom))
            tela_monitor.blit(tela_escala, (-self.offset_x * self.zoom, -self.offset_y * self.zoom))
        else:
            tela_monitor.blit(self.tela_virtual, (-self.offset_x, -self.offset_y))