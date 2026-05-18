# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# =============================================================================

import pygame
import Estudos.estudo_notas as estudo_notas
import Estudos.estudo_escalas as estudo_escalas # <--- NOVO IMPORT

class GerenciadorEstudos:
    def __init__(self):
        self.rect_voltar = pygame.Rect(0, 0, 0, 0)
        self.modulo_notas = None
        self.modulo_escalas = None # <--- NOVA INSTÂNCIA

    def desenhar_tela_estudo(self, tela, largura, altura, estado, fontes):
        tela.fill((20, 20, 25))

        cam_x = estado.camera.offset_x if hasattr(estado, 'camera') else 0
        cam_y = estado.camera.offset_y if hasattr(estado, 'camera') else 0
        w_monitor = getattr(estado, 'LARGURA_TELA', 1280)
        h_monitor = getattr(estado, 'ALTURA_TELA', 720)
        zoom = estado.camera.zoom if hasattr(estado, 'camera') else 1.0
        
        meio_x = cam_x + (w_monitor / 2) / zoom
        meio_y = cam_y + (h_monitor / 2) / zoom

        self.rect_voltar = pygame.Rect(cam_x + 20, cam_y + 20, 120, 40)
        pygame.draw.rect(tela, (200, 50, 50), self.rect_voltar, border_radius=5)
        txt_voltar = fontes['ui'].render("<< Voltar (ESC)", True, (255, 255, 255))
        tela.blit(txt_voltar, (self.rect_voltar.centerx - txt_voltar.get_width()//2, self.rect_voltar.centery - txt_voltar.get_height()//2))

        titulo = f"Estudo: {estado.estudo_ativo}"
        txt_titulo = fontes['titulo'].render(titulo, True, (0, 160, 255))
        tela.blit(txt_titulo, (meio_x - txt_titulo.get_width() // 2, cam_y + 40))

        # =====================================================================
        # ROTEAMENTO DOS MÓDULOS DE ESTUDO
        # =====================================================================
        if estado.estudo_ativo == "Acerte a Nota":
            if self.modulo_notas is None: self.modulo_notas = estudo_notas.AcerteANota()
            self.modulo_notas.desenhar(tela, estado, fontes, meio_x, meio_y, cam_x, cam_y)
            
        elif estado.estudo_ativo == "Acerte a Escala": # <--- NOVA ROTA
            if self.modulo_escalas is None: self.modulo_escalas = estudo_escalas.EstudoEscalas()
            self.modulo_escalas.desenhar(tela, estado, fontes, meio_x, meio_y, cam_x, cam_y)
            
        else:
            txt_info = fontes['ui'].render("Módulo em desenvolvimento...", True, (150, 150, 150))
            tela.blit(txt_info, (meio_x - txt_info.get_width() // 2, meio_y))

    def tratar_eventos(self, evento, pos_mouse, estado):
        cam_x = estado.camera.offset_x if hasattr(estado, 'camera') else 0
        cam_y = estado.camera.offset_y if hasattr(estado, 'camera') else 0
        zoom = estado.camera.zoom if hasattr(estado, 'camera') else 1.0
        pos_mouse_virtual = (cam_x + pos_mouse[0] / zoom, cam_y + pos_mouse[1] / zoom)

        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            estado.tela_estudo_ativa = False
            estado.estudo_ativo = ""
            self.modulo_notas = None
            self.modulo_escalas = None # <--- LIMPA AO SAIR
            return True

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.rect_voltar.collidepoint(pos_mouse_virtual):
                estado.tela_estudo_ativa = False
                estado.estudo_ativo = ""
                self.modulo_notas = None 
                self.modulo_escalas = None # <--- LIMPA AO SAIR
                return True

            # Repassa os cliques
            if estado.estudo_ativo == "Acerte a Nota" and self.modulo_notas:
                if self.modulo_notas.tratar_cliques(pos_mouse_virtual, estado): return True
                
            elif estado.estudo_ativo == "Acerte a Escala" and self.modulo_escalas: # <--- NOVA ROTA
                if self.modulo_escalas.tratar_cliques(pos_mouse_virtual, estado): return True
                        
        return False