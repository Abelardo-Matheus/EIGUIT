# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# =============================================================================

import pygame
import random
import Modulos.escalas as escalas
from Core.constantes_ui import lista_afinacoes

# Importa as suas bibliotecas nativas de shape (Para o Modo Desenhar)
import Modulos.modulos_escala_maior as esc_maior
import Modulos.modulos_penta as esc_penta 
import Modulos.modulos_teoria_avancada as esc_avancada
import Modulos.modulos_modos as esc_modos

class EstudoEscalas:
    def __init__(self):
        self.modo_jogo = "desenhar" # "desenhar" ou "adivinhar"
        self.casas_estudo = 12
        self.acertos = 0
        self.total = 0
        self.inicializado = False

        self.x_braco = 0
        self.y_braco = 0
        self.largura_braco = 0
        self.altura_braco = 0
        self.espaco_casas = 0
        self.espaco_cordas = 0
        self.num_cordas = 6

        self.nome_escala_alvo = ""
        self.posicoes_corretas = set() 
        self.posicoes_corretas_relativas = set() 
        
        self.posicoes_desenhadas = set()
        self.estado_resposta = None 
        self.rect_btn_conferir = pygame.Rect(0, 0, 0, 0)
        
        self.opcoes_adivinhar = []
        self.rects_opcoes = []
        self.mostrar_notas = False
        self.rect_btn_mostrar = pygame.Rect(0, 0, 0, 0)

        self.rect_btn_desenhar = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_adivinhar = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_menos = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_mais = pygame.Rect(0, 0, 0, 0)

        # =====================================================================
        # DADOS: MODO DESENHAR (Usa seus arquivos de shape)
        # =====================================================================
        self.catalogo_shapes = {
            "Escala Maior - Shape 1": esc_maior.SHAPE_1,
            "Escala Maior - Shape 2": esc_maior.SHAPE_2,
            "Escala Maior - Shape 3": esc_maior.SHAPE_3,
            "Escala Maior - Shape 4": esc_maior.SHAPE_4,
            "Escala Maior - Shape 5": esc_maior.SHAPE_5,
            
            "Penta Menor - Shape 1": esc_penta.SHAPE_1,
            "Penta Menor - Shape 2": esc_penta.SHAPE_2,
            "Penta Menor - Shape 3": esc_penta.SHAPE_3,
            "Penta Menor - Shape 4": esc_penta.SHAPE_4,
            "Penta Menor - Shape 5": esc_penta.SHAPE_5,
            
            "Blues - Shape 1": esc_avancada.SHAPE_1_BLUES,
            "Modo Dórico": esc_modos.DORICO
        }


        # =====================================================================
        # DADOS: MODO ADIVINHAR (Motor Matemático Dinâmico)
        # =====================================================================
        self.notas_base = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.tipos_escala_adivinhar = {
            "Maior": [0, 2, 4, 5, 7, 9, 11],
            "Menor Natural": [0, 2, 3, 5, 7, 8, 10],
            "Penta Maior": [0, 2, 4, 7, 9],
            "Penta Menor": [0, 3, 5, 7, 10],
            "Blues": [0, 3, 5, 6, 7, 10],
            "Dórico": [0, 2, 3, 5, 7, 9, 10]
        }
        self.msg_adivinhar = ""
        self.cor_msg_adivinhar = (255, 255, 255)

    def inicializar_questao(self, estado):
        self.posicoes_corretas.clear()
        self.posicoes_corretas_relativas.clear()
        self.posicoes_desenhadas.clear()
        self.estado_resposta = None

        try: notas_abertas = lista_afinacoes[estado.indice_afinacao]["notas"]
        except: notas_abertas = ['E', 'A', 'D', 'G', 'B', 'E', 'B']

        instrumento = getattr(estado, 'instrumento', 'guitarra')
        self.num_cordas = 4 if instrumento == 'baixo' else estado.NUM_CORDAS

        # =====================================================================
        # LÓGICA DO MODO DESENHAR (Focado em Shapes do Catálogo)
        # =====================================================================
        if self.modo_jogo == "desenhar":
            nome_sorteado = random.choice(list(self.catalogo_shapes.keys()))
            self.nome_escala_alvo = nome_sorteado
            matriz_shape = self.catalogo_shapes[nome_sorteado]
            
            casa_inicio_offset = random.randint(1, max(1, self.casas_estudo - len(matriz_shape[0])))

            for c_matriz in range(len(matriz_shape)):
                c_real = c_matriz
                if len(matriz_shape) == 7 and self.num_cordas == 6:
                    if c_matriz == 0: continue 
                    c_real = c_matriz - 1
                elif self.num_cordas == 4:
                    if c_matriz < len(matriz_shape) - 4: continue 
                    c_real = c_matriz - (len(matriz_shape) - 4)

                for casa_matriz in range(len(matriz_shape[c_matriz])):
                    valor = matriz_shape[c_matriz][casa_matriz]
                    if valor in [1, 2]: 
                        casa_final = casa_inicio_offset + casa_matriz
                        if casa_final <= self.casas_estudo:
                            self.posicoes_corretas.add((c_real, casa_final))
                        self.posicoes_corretas_relativas.add((c_real, casa_matriz))

            if self.posicoes_corretas_relativas:
                min_casa_esperada = min(casa for corda, casa in self.posicoes_corretas_relativas)
                temp_relativo = set()
                for corda, casa in self.posicoes_corretas_relativas:
                    temp_relativo.add((corda, casa - min_casa_esperada))
                self.posicoes_corretas_relativas = temp_relativo

        # =====================================================================
        # LÓGICA DO MODO ADIVINHAR (Calcula Completas Variando o Tom)
        # =====================================================================
        elif self.modo_jogo == "adivinhar":
            # 1. Sorteia o Tom e o Tipo
            tom_sorteado = random.choice(self.notas_base)
            tipo_sorteado = random.choice(list(self.tipos_escala_adivinhar.keys()))
            self.nome_escala_alvo = f"{tom_sorteado} {tipo_sorteado}"
            
            # 2. Gera a lista de notas dessa escala
            idx_tom = self.notas_base.index(tom_sorteado)
            notas_alvo = [self.notas_base[(idx_tom + i) % 12] for i in self.tipos_escala_adivinhar[tipo_sorteado]]

            # 3. Mapeia no braço inteiro
            # Correção: Se não for 7 cordas, começamos da corda 1 (E) em vez da 0 (B)
            offset_afinacao = 1 if self.num_cordas <= 6 else 0

            for c in range(self.num_cordas):
                nota_aberta = notas_abertas[c + offset_afinacao]
                for casa in range(0, self.casas_estudo + 1):
                    if escalas.obter_nota(nota_aberta, casa) in notas_alvo:
                        self.posicoes_corretas.add((c, casa))

            # 4. Gera as 4 alternativas para os botões
            opcoes = [self.nome_escala_alvo]
            while len(opcoes) < 4:
                t_f = random.choice(self.notas_base)
                tp_f = random.choice(list(self.tipos_escala_adivinhar.keys()))
                n_f = f"{t_f} {tp_f}"
                if n_f not in opcoes:
                    opcoes.append(n_f)
            random.shuffle(opcoes)
            self.opcoes_adivinhar = opcoes

        self.inicializado = True

    def desenhar(self, tela, estado, fontes, meio_x, meio_y, cam_x, cam_y):
        if not self.inicializado:
            self.inicializar_questao(estado)

        try: notas_abertas = lista_afinacoes[estado.indice_afinacao]["notas"]
        except: notas_abertas = ['E', 'A', 'D', 'G', 'B', 'E', 'B']
        instrumento = getattr(estado, 'instrumento', 'guitarra')

        # =====================================================================
        # 1. CONTROLES DE TOPO
        # =====================================================================
        self.rect_btn_desenhar = pygame.Rect(meio_x - 140, cam_y + 90, 130, 35)
        self.rect_btn_adivinhar = pygame.Rect(meio_x + 10, cam_y + 90, 130, 35)

        cor_des = (0, 160, 255) if self.modo_jogo == "desenhar" else (60, 60, 60)
        cor_adiv = (0, 160, 255) if self.modo_jogo == "adivinhar" else (60, 60, 60)

        pygame.draw.rect(tela, cor_des, self.rect_btn_desenhar, border_radius=5)
        pygame.draw.rect(tela, cor_adiv, self.rect_btn_adivinhar, border_radius=5)

        txt_des = fontes['pequena'].render("Desenhar Shape", True, (255, 255, 255))
        txt_adiv = fontes['pequena'].render("Qual a Escala?", True, (255, 255, 255))
        tela.blit(txt_des, (self.rect_btn_desenhar.centerx - txt_des.get_width()//2, self.rect_btn_desenhar.centery - txt_des.get_height()//2))
        tela.blit(txt_adiv, (self.rect_btn_adivinhar.centerx - txt_adiv.get_width()//2, self.rect_btn_adivinhar.centery - txt_adiv.get_height()//2))

        txt_placar = fontes['ui'].render(f"Rodadas Vencidas: {self.acertos}", True, (200, 200, 200))
        tela.blit(txt_placar, (meio_x - txt_placar.get_width()//2, cam_y + 140))

        # =====================================================================
        # 2. DESENHO DO BRAÇO CEGO
        # =====================================================================
        self.largura_braco = max(700, min(1000, 40 * self.casas_estudo)) 
        self.altura_braco = 180
        self.x_braco = meio_x - self.largura_braco // 2
        self.y_braco = meio_y - 90

        self.espaco_cordas = self.altura_braco / (self.num_cordas - 1) if self.num_cordas > 1 else self.altura_braco
        self.espaco_casas = self.largura_braco / self.casas_estudo

        pygame.draw.rect(tela, (45, 40, 45), (self.x_braco, self.y_braco, self.largura_braco, self.altura_braco), border_radius=4)

        for casa in range(self.casas_estudo + 1):
            x_traste = self.x_braco + (casa * self.espaco_casas)
            pygame.draw.line(tela, (160, 160, 160), (x_traste, self.y_braco), (x_traste, self.y_braco + self.altura_braco), 2)
            if casa > 0:
                x_centro = x_traste - (self.espaco_casas / 2)
                if casa in [3, 5, 7, 9, 15, 17, 19, 21]:
                    pygame.draw.circle(tela, (130, 130, 130), (int(x_centro), int(self.y_braco + self.altura_braco / 2)), 6)
                elif casa in [12, 24]:
                    pygame.draw.circle(tela, (130, 130, 130), (int(x_centro), int(self.y_braco + self.altura_braco / 3)), 6)
                    pygame.draw.circle(tela, (130, 130, 130), (int(x_centro), int(self.y_braco + self.altura_braco * 2 / 3)), 6)
                txt_c = fontes['pequena'].render(str(casa), True, (150, 150, 150))
                tela.blit(txt_c, (x_centro - txt_c.get_width()//2, self.y_braco + self.altura_braco + 8))

        for i in range(self.num_cordas):
            y_corda = self.y_braco + self.altura_braco - (i * self.espaco_cordas)
            pygame.draw.line(tela, (220, 220, 220), (self.x_braco, y_corda), (self.x_braco + self.largura_braco, y_corda), 1 + (i // 3))

        # =====================================================================
        # 3. LÓGICA DE BOLINHAS CLICADAS VS MOSTRADAS
        # =====================================================================
        offset_notas = 1 if self.num_cordas <= 6 else 0

        for c in range(self.num_cordas):
            nota_aberta = notas_abertas[c + offset_notas]
            for casa in range(self.casas_estudo + 1):
                x_centro = self.x_braco - 25 if casa == 0 else self.x_braco + (casa * self.espaco_casas) - (self.espaco_casas / 2)
                y_corda = self.y_braco + self.altura_braco - (c * self.espaco_cordas)
                raio = 14
                
                pos = (c, casa)
                cor_fundo = None
                cor_borda = None
                mostrar_txt = False

                if self.modo_jogo == "desenhar":
                    if pos in self.posicoes_desenhadas:
                        cor_fundo = (200, 50, 50) 
                    else:
                        cor_borda = (150, 150, 150) 

                    if self.estado_resposta == "conferido":
                        if pos in self.posicoes_desenhadas and pos in self.posicoes_corretas:
                            cor_borda = (50, 255, 50)
                            mostrar_txt = True
                        elif pos in self.posicoes_desenhadas and pos not in self.posicoes_corretas:
                            cor_fundo = (100, 30, 30) 
                            cor_borda = (255, 0, 0)
                            mostrar_txt = True
                        elif pos not in self.posicoes_desenhadas and pos in self.posicoes_corretas:
                            cor_borda = (255, 255, 0) 
                            mostrar_txt = True

                elif self.modo_jogo == "adivinhar":
                    if pos in self.posicoes_corretas:
                        cor_fundo = (200, 50, 50)
                        if self.mostrar_notas: mostrar_txt = True

                if cor_fundo:
                    pygame.draw.circle(tela, cor_fundo, (int(x_centro), int(y_corda)), raio)
                if cor_borda:
                    pygame.draw.circle(tela, cor_borda, (int(x_centro), int(y_corda)), raio, width=2)

                if mostrar_txt:
                    nota_calc = escalas.obter_nota(nota_aberta, casa)
                    txt_nota = fontes['pequena'].render(nota_calc, True, (255, 255, 255))
                    tela.blit(txt_nota, (x_centro - txt_nota.get_width()//2, y_corda - txt_nota.get_height()//2))

        # =====================================================================
        # 4. PAINÉIS INFERIORES E BOTÕES
        # =====================================================================
        y_inferior = self.y_braco + self.altura_braco + 50

        if self.modo_jogo == "desenhar":
            if not self.estado_resposta:
                txt_alvo = fontes['titulo'].render(f"Desenhe o shape: {self.nome_escala_alvo}", True, (255, 255, 255))
                tela.blit(txt_alvo, (meio_x - txt_alvo.get_width()//2, y_inferior))

                self.rect_btn_conferir = pygame.Rect(meio_x - 75, y_inferior + 40, 150, 45)
                pygame.draw.rect(tela, (50, 200, 50), self.rect_btn_conferir, border_radius=8)
                txt_conf = fontes['ui'].render("Conferir", True, (0, 0, 0))
                tela.blit(txt_conf, (self.rect_btn_conferir.centerx - txt_conf.get_width()//2, self.rect_btn_conferir.centery - txt_conf.get_height()//2))
            
            elif self.estado_resposta == "conferido":
                acertou_tudo = getattr(self, 'resultado_atual', False)
                msg = "Perfeito! O shape está certinho." if acertou_tudo else "Quase lá! Veja no braço os erros apontados em vermelho/amarelo."
                cor_msg = (100, 255, 100) if acertou_tudo else (255, 200, 100)
                
                txt_msg = fontes['titulo'].render(msg, True, cor_msg)
                tela.blit(txt_msg, (meio_x - txt_msg.get_width()//2, y_inferior))

                self.rect_btn_conferir = pygame.Rect(meio_x - 75, y_inferior + 40, 150, 45)
                pygame.draw.rect(tela, (0, 160, 255), self.rect_btn_conferir, border_radius=8)
                txt_prox = fontes['ui'].render("Próxima", True, (255, 255, 255))
                tela.blit(txt_prox, (self.rect_btn_conferir.centerx - txt_prox.get_width()//2, self.rect_btn_conferir.centery - txt_prox.get_height()//2))

        elif self.modo_jogo == "adivinhar":
            self.rect_btn_mostrar = pygame.Rect(meio_x - 85, y_inferior, 170, 35)
            pygame.draw.rect(tela, (80, 80, 80), self.rect_btn_mostrar, border_radius=5)
            txt_most = fontes['pequena'].render("Ocultar Notas" if self.mostrar_notas else "Mostrar Notas", True, (255, 255, 255))
            tela.blit(txt_most, (self.rect_btn_mostrar.centerx - txt_most.get_width()//2, self.rect_btn_mostrar.centery - txt_most.get_height()//2))

            if not self.estado_resposta:
                self.rects_opcoes.clear()
                largura_op = 200
                x_op_start = meio_x - ((len(self.opcoes_adivinhar) * largura_op) + ((len(self.opcoes_adivinhar)-1) * 20)) // 2
                
                for idx, op in enumerate(self.opcoes_adivinhar):
                    rect_op = pygame.Rect(x_op_start + (idx * (largura_op + 20)), y_inferior + 50, largura_op, 50)
                    self.rects_opcoes.append((op, rect_op))
                    
                    pygame.draw.rect(tela, (60, 60, 70), rect_op, border_radius=8)
                    pygame.draw.rect(tela, (150, 150, 150), rect_op, width=2, border_radius=8)
                    
                    txt_op = fontes['ui'].render(op, True, (255, 255, 255))
                    tela.blit(txt_op, (rect_op.centerx - txt_op.get_width()//2, rect_op.centery - txt_op.get_height()//2))
            
            elif self.estado_resposta == "conferido":
                txt_msg = fontes['titulo'].render(self.msg_adivinhar, True, self.cor_msg_adivinhar)
                tela.blit(txt_msg, (meio_x - txt_msg.get_width()//2, y_inferior + 50))

                self.rect_btn_conferir = pygame.Rect(meio_x - 75, y_inferior + 90, 150, 45)
                pygame.draw.rect(tela, (0, 160, 255), self.rect_btn_conferir, border_radius=8)
                txt_prox = fontes['ui'].render("Próxima", True, (255, 255, 255))
                tela.blit(txt_prox, (self.rect_btn_conferir.centerx - txt_prox.get_width()//2, self.rect_btn_conferir.centery - txt_prox.get_height()//2))

        # Controle de Casas Superior Direito
        x_controles = cam_x + getattr(estado, 'LARGURA_TELA', 1280) - 200
        y_controles = cam_y + 20
        txt_casas_info = fontes['pequena'].render(f"Treinando em {self.casas_estudo} casas", True, (150, 150, 150))
        tela.blit(txt_casas_info, (x_controles, y_controles))

        self.rect_btn_menos = pygame.Rect(x_controles, y_controles + 25, 35, 30)
        self.rect_btn_mais = pygame.Rect(x_controles + 125, y_controles + 25, 35, 30)
        
        pygame.draw.rect(tela, (0, 120, 215), self.rect_btn_menos, border_radius=4)
        tela.blit(fontes['titulo'].render("-", True, (255, 255, 255)), (self.rect_btn_menos.centerx - 5, self.rect_btn_menos.centery - 12))
        pygame.draw.rect(tela, (0, 120, 215), self.rect_btn_mais, border_radius=4)
        tela.blit(fontes['titulo'].render("+", True, (255, 255, 255)), (self.rect_btn_mais.centerx - 7, self.rect_btn_mais.centery - 12))

    def tratar_cliques(self, pos_mouse_virtual, estado):
        if self.rect_btn_desenhar.collidepoint(pos_mouse_virtual) and self.modo_jogo != "desenhar":
            self.modo_jogo = "desenhar"
            self.inicializar_questao(estado)
            return True
        if self.rect_btn_adivinhar.collidepoint(pos_mouse_virtual) and self.modo_jogo != "adivinhar":
            self.modo_jogo = "adivinhar"
            self.inicializar_questao(estado)
            return True

        if self.rect_btn_menos.collidepoint(pos_mouse_virtual) and self.casas_estudo > 5:
            self.casas_estudo -= 1
            self.inicializar_questao(estado) 
            return True
        if self.rect_btn_mais.collidepoint(pos_mouse_virtual) and self.casas_estudo < 24:
            self.casas_estudo += 1
            self.inicializar_questao(estado)
            return True

        if self.modo_jogo == "desenhar":
            if not self.estado_resposta:
                rect_braco = pygame.Rect(self.x_braco - 30, self.y_braco, self.largura_braco + 30, self.altura_braco)
                if rect_braco.collidepoint(pos_mouse_virtual):
                    for c in range(self.num_cordas):
                        y_corda = self.y_braco + self.altura_braco - (c * self.espaco_cordas)
                        for casa in range(self.casas_estudo + 1):
                            x_centro = self.x_braco - 25 if casa == 0 else self.x_braco + (casa * self.espaco_casas) - (self.espaco_casas / 2)
                            
                            dist_sq = (pos_mouse_virtual[0] - x_centro)**2 + (pos_mouse_virtual[1] - y_corda)**2
                            if dist_sq <= 15**2:
                                pos = (c, casa)
                                if pos in self.posicoes_desenhadas:
                                    self.posicoes_desenhadas.remove(pos)
                                else:
                                    self.posicoes_desenhadas.add(pos)
                                return True

                if self.rect_btn_conferir.collidepoint(pos_mouse_virtual):
                    self.estado_resposta = "conferido"
                    
                    if not self.posicoes_desenhadas:
                        self.resultado_atual = False
                    else:
                        min_casa_user = min(casa for corda, casa in self.posicoes_desenhadas)
                        user_relativo = set((corda, casa - min_casa_user) for corda, casa in self.posicoes_desenhadas)
                        
                        self.resultado_atual = (user_relativo == self.posicoes_corretas_relativas)
                        
                        self.posicoes_corretas.clear()
                        for corda, casa_rel in self.posicoes_corretas_relativas:
                            self.posicoes_corretas.add((corda, casa_rel + min_casa_user))

                    if self.resultado_atual:
                        self.acertos += 1
                    return True
            else:
                if self.rect_btn_conferir.collidepoint(pos_mouse_virtual):
                    self.inicializar_questao(estado)
                    return True

        elif self.modo_jogo == "adivinhar":
            if self.rect_btn_mostrar.collidepoint(pos_mouse_virtual):
                self.mostrar_notas = not self.mostrar_notas
                return True

            if not self.estado_resposta:
                for op, rect_op in self.rects_opcoes:
                    if rect_op.collidepoint(pos_mouse_virtual):
                        if op == self.nome_escala_alvo:
                            self.msg_adivinhar = "Correto! Visão afiada."
                            self.cor_msg_adivinhar = (100, 255, 100)
                            self.acertos += 1
                        else:
                            self.msg_adivinhar = f"Incorreto. A escala era {self.nome_escala_alvo}."
                            self.cor_msg_adivinhar = (255, 100, 100)
                        self.estado_resposta = "conferido"
                        return True
            else:
                if self.rect_btn_conferir.collidepoint(pos_mouse_virtual):
                    self.inicializar_questao(estado)
                    return True

        return False