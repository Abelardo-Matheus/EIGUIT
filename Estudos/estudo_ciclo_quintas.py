import pygame
import math
import random
import Modulos.escalas as escalas
from Core.constantes_ui import *
from Core.i18n import _t

class EstudoCicloQuintas:
    """
        Como funciona: Define a estrutura e estado do componente 'EstudoCicloQuintas'.
        Para que serve: Controla a lógica e interação da tela de estudo prático.
        Onde é usada: Chamado a partir do módulo ou classe base de 'estudo_ciclo_quintas'.
    """

    def __init__(self):
        """
            Como funciona: Inicializa os atributos e o estado inicial da instância.
            Para que serve: Prepara o objeto para ser utilizado no ciclo de vida da aplicação.
            Onde é usada: Chamado a partir do módulo ou classe base de 'estudo_ciclo_quintas'.
        """
        self.inicializado = False
        self.modo = 'explorar'
        self.tipo_ciclo = 'quintas'
        self.sub_modo_explorar = 'geral'
        self.modo_tonal = 'maior'
        self.notas_quintas = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'Eb', 'Bb', 'F']
        self.relativas_menores = ['Am', 'Em', 'Bm', 'F#m', 'C#m', 'G#m', 'D#m', 'A#m', 'E#m', 'Cm', 'Gm', 'Dm']
        self.acidentes = ['Natural', '1#', '2#', '3#', '4#', '5#', '6#', '7# / 5b', '4b', '3b', '2b', '1b']
        self.intervalos_maior = [0, 2, 4, 5, 7, 9, 11]
        self.graus_romanos_maior = ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°']
        self.qualidades_maior = ['', 'm', 'm', '', '', 'm', 'dim']
        self.intervalos_menor = [0, 2, 3, 5, 7, 8, 10]
        self.graus_romanos_menor = ['i', 'ii°', 'III', 'iv', 'v', 'VI', 'VII']
        self.qualidades_menor = ['m', 'dim', '', 'm', 'm', '', '']
        
        # Biblioteca Expandida
        self.biblioteca_geral = [
            {'nome': 'Pop Clássico', 'graus': [0, 4, 5, 3]},
            {'nome': 'Rock Melódico', 'graus': [0, 4, 3, 0]},
            {'nome': 'Doo-Wop / 50s', 'graus': [0, 5, 3, 4]},
            {'nome': 'Jazz Standard', 'graus': [1, 4, 0]},
            {'nome': 'Épica / Trilha', 'graus': [5, 3, 0, 4]},
            {'nome': 'Blues Básico', 'graus': [0, 3, 0, 4, 3, 0]},
            {'nome': 'Andaluza (Menor)', 'graus': [0, 6, 5, 4], 'sugestao': 'menor'},
            {'nome': 'Subida Tensa', 'graus': [1, 2, 3, 4]}
        ]
        
        self.sequencias_custom = []
        self.sequencia_atual = [] # Lista de dicionários {'grau': int, 'label': str}
        self.seq_selecionada_idx = -1
        self.nota_selecionada_idx = 0
        
        # Estados de UI e Drag & Drop
        self.rects_notas = []
        self.rects_botoes = {}
        self.rects_sub_modos = {}
        self.rects_biblioteca_rows = []
        self.scroll_y_biblioteca = 0
        self.max_scroll_biblioteca = 0
        self.rect_zona_a = pygame.Rect(0, 0, 0, 0)
        
        # Estados de Drag de Layout
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.bloco_arrastando = None # 'roda', 'info', 'braco', 'header', 'favoritas'
        
        # Posições Customizáveis (Offsets relativos ao layout base)
        self.pos_roda = [209.0, -35.0] 
        self.pos_info = [97.0, -264.0]
        self.pos_braco = [0.0, 320.0]
        self.pos_header = [0.0, 0.0] 
        self.pos_favoritas = [500.0, -35.0] # Offset relativo ao centro (meio_x - offset) 
        
        self.drag_item = None 
        self.drag_pos = (0, 0)
        self.drop_zone_active = False
        
        self.rect_toggle_tonal = pygame.Rect(0, 0, 0, 0)
        self.pergunta_atual = ''
        self.opcoes_desafio = []
        self.resposta_correta = ''
        self.feedback_desafio = ''
        self.cor_feedback = BRANCO
        self.estado_desafio = None
        self.acertos = 0
        
        self._carregar_sequencias_custom()

    def _carregar_sequencias_custom(self):
        try:
            import os, json
            config_global = 'config_eiguit.json'
            if os.path.exists(config_global):
                with open(config_global, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    ultimo = cfg.get('ultimo_perfil', '')
                    if ultimo and os.path.exists(ultimo):
                        with open(ultimo, 'r', encoding='utf-8') as pf:
                            perfil = json.load(pf)
                            self.sequencias_custom = perfil.get('sequencias_custom', [])
        except Exception as e: print(f'[ERRO] Falha ao carregar sequências: {e}')

    def _salvar_sequencias_custom(self):
        try:
            import os, json
            config_global = 'config_eiguit.json'
            if os.path.exists(config_global):
                with open(config_global, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    ultimo = cfg.get('ultimo_perfil', '')
                    if ultimo and os.path.exists(ultimo):
                        with open(ultimo, 'r', encoding='utf-8') as pf: perfil = json.load(pf)
                        perfil['sequencias_custom'] = self.sequencias_custom
                        with open(ultimo, 'w', encoding='utf-8') as pf: json.dump(perfil, pf, indent=4)
        except Exception as e: print(f'[ERRO] Falha ao salvar sequências: {e}')

    def inicializar(self, estado):
        self.inicializado = True
        self.gerar_pergunta()

    def gerar_pergunta(self):
        tipo = random.choice(['relativa', 'acidente', 'quinta', 'quarta'])
        idx = random.randint(0, 11)
        nota = self.notas_quintas[idx]
        if tipo == 'relativa':
            self.pergunta_atual, self.resposta_correta = f'Qual a relativa menor de {nota}?', self.relativas_menores[idx]
            opcoes = [self.resposta_correta]
            while len(opcoes) < 4:
                o = random.choice(self.relativas_menores)
                if o not in opcoes: opcoes.append(o)
        elif tipo == 'acidente':
            self.pergunta_atual, self.resposta_correta = f'Quantos acidentes tem a escala de {nota}?', self.acidentes[idx]
            opcoes = [self.resposta_correta]
            while len(opcoes) < 4:
                o = random.choice(self.acidentes)
                if o not in opcoes: opcoes.append(o)
        elif tipo == 'quinta':
            self.pergunta_atual, self.resposta_correta = f'Qual é a 5ª justa de {nota}?', self.notas_quintas[(idx + 1) % 12]
            opcoes = [self.resposta_correta]
            while len(opcoes) < 4:
                o = random.choice(self.notas_quintas)
                if o not in opcoes: opcoes.append(o)
        else:
            self.pergunta_atual, self.resposta_correta = f'Qual é a 4ª justa de {nota}?', self.notas_quintas[(idx - 1) % 12]
            opcoes = [self.resposta_correta]
            while len(opcoes) < 4:
                o = random.choice(self.notas_quintas)
                if o not in opcoes: opcoes.append(o)
        random.shuffle(opcoes)
        self.opcoes_desafio, self.estado_desafio, self.feedback_desafio = opcoes, None, ''

    def desenhar(self, tela, estado, fontes, meio_x, meio_y, cam_x, cam_y):
        if not self.inicializado: self.inicializar(estado)
        base_y_header, base_x_header = cam_y + 100 + self.pos_header[1], meio_x + self.pos_header[0]
        self.rect_drag_layout_header = pygame.Rect(base_x_header - 230, base_y_header - 10, 460, 100)
        if estado.drag_ativado:
            pygame.draw.rect(tela, (0, 160, 255), self.rect_drag_layout_header, width=2, border_radius=10)
            t_h = fontes['pequena'].render('MOVER MENU', True, (0, 160, 255))
            tela.blit(t_h, (self.rect_drag_layout_header.x + 10, self.rect_drag_layout_header.y - 20))
        self.rects_botoes['explorar'] = pygame.Rect(base_x_header - 220, base_y_header, 140, 40)
        self.rects_botoes['desafio'] = pygame.Rect(base_x_header - 70, base_y_header, 140, 40)
        self.rects_botoes['tipo'] = pygame.Rect(base_x_header + 80, base_y_header, 140, 40)
        c_exp = (0, 160, 255) if self.modo == 'explorar' else (60, 60, 70)
        c_des = (0, 160, 255) if self.modo == 'desafio' else (60, 60, 70)
        pygame.draw.rect(tela, c_exp, self.rects_botoes['explorar'], border_radius=8)
        pygame.draw.rect(tela, c_des, self.rects_botoes['desafio'], border_radius=8)
        pygame.draw.rect(tela, (80, 50, 120), self.rects_botoes['tipo'], border_radius=8)
        tela.blit(fontes['ui'].render('Exploração', True, BRANCO), (self.rects_botoes['explorar'].x+10, self.rects_botoes['explorar'].y+10))
        tela.blit(fontes['ui'].render('Desafio', True, BRANCO), (self.rects_botoes['desafio'].x+10, self.rects_botoes['desafio'].y+10))
        tela.blit(fontes['ui'].render(f'Ciclo: {self.tipo_ciclo.capitalize()}', True, BRANCO), (self.rects_botoes['tipo'].x+10, self.rects_botoes['tipo'].y+10))
        if self.modo == 'explorar':
            sub = [('Geral', 'geral'), ('Escala', 'escala'), ('Campo', 'campo'), ('Sequências', 'sequencias')]
            xs = base_x_header - 220
            for n, k in sub:
                r = pygame.Rect(xs, base_y_header + 50, 105, 30)
                self.rects_sub_modos[k] = r
                c = (0, 120, 215) if self.sub_modo_explorar == k else (40, 40, 50)
                pygame.draw.rect(tela, c, r, border_radius=5)
                t = fontes['pequena'].render(n, True, BRANCO)
                tela.blit(t, (r.centerx - t.get_width() // 2, r.centery - t.get_height() // 2))
                xs += 115
            self.rect_toggle_tonal = pygame.Rect(xs + 10, base_y_header + 50, 120, 30)
            ct = (200, 150, 0) if self.modo_tonal == 'menor' else (0, 150, 200)
            pygame.draw.rect(tela, ct, self.rect_toggle_tonal, border_radius=5)
            tt = fontes['pequena'].render(f'Modo: {self.modo_tonal.capitalize()}', True, BRANCO)
            tela.blit(tt, (self.rect_toggle_tonal.centerx - tt.get_width() // 2, self.rect_toggle_tonal.centery - tt.get_height() // 2))
        re, ri = 180, 120
        centro = (meio_x - self.pos_roda[0], meio_y + self.pos_roda[1])
        self.rect_drag_layout_roda = pygame.Rect(centro[0] - re - 50, centro[1] - re - 50, (re + 50) * 2, (re + 50) * 2)
        if estado.drag_ativado:
            pygame.draw.rect(tela, (0, 160, 255), self.rect_drag_layout_roda, width=2, border_radius=20)
            tela.blit(fontes['pequena'].render('MOVER RODA', True, (0, 160, 255)), (self.rect_drag_layout_roda.x + 10, self.rect_drag_layout_roda.y - 20))
        pygame.draw.circle(tela, (40, 40, 50), centro, re + 40, width=2)
        pygame.draw.circle(tela, (30, 30, 40), centro, re + 10)
        self.rects_notas.clear()
        idx_seq, ints = [], self.intervalos_maior if self.modo_tonal == 'maior' else self.intervalos_menor
        if self.sub_modo_explorar == 'sequencias' and self.seq_selecionada_idx != -1:
            lista = []
            if self.sequencias_custom: lista.extend(self.sequencias_custom)
            lista.extend(self.biblioteca_geral)
            if 0 <= self.seq_selecionada_idx < len(lista):
                seq = lista[self.seq_selecionada_idx]
                bn = self.notas_quintas[self.nota_selecionada_idx] if self.modo_tonal == 'maior' else self.relativas_menores[self.nota_selecionada_idx].replace('m', '')
                for g in seq['graus']:
                    na = escalas.obter_nota_por_intervalo(bn, ints[g])
                    if na in self.notas_quintas: idx_seq.append(self.notas_quintas.index(na))
        for i in range(12):
            ang = math.radians(i * 30 - 90)
            if self.tipo_ciclo == 'quartas': ang = math.radians(-i * 30 - 90)
            nx, ny = centro[0] + math.cos(ang) * re, centro[1] + math.sin(ang) * re
            mx, my = centro[0] + math.cos(ang) * ri, centro[1] + math.sin(ang) * ri
            if i == self.nota_selecionada_idx:
                pygame.draw.circle(tela, (0, 160, 255), (int(nx), int(ny)), 35, width=3)
                pygame.draw.line(tela, (100, 100, 150), centro, (int(nx), int(ny)), 1)
            elif i in idx_seq: pygame.draw.circle(tela, (200, 150, 0), (int(nx), int(ny)), 30, width=2)
            rn = pygame.Rect(nx - 30, ny - 30, 60, 60)
            self.rects_notas.append((i, rn))
            tn = fontes['titulo'].render(self.notas_quintas[i], True, BRANCO)
            tela.blit(tn, (nx - tn.get_width() // 2, ny - tn.get_height() // 2))
            tr = fontes['pequena'].render(self.relativas_menores[i], True, (200, 200, 200))
            tela.blit(tr, (mx - tr.get_width() // 2, my - tr.get_height() // 2))
            ax, ay = centro[0] + math.cos(ang) * (re + 60), centro[1] + math.sin(ang) * (re + 60)
            ta = fontes['pequena'].render(self.acidentes[i], True, (150, 150, 150))
            tela.blit(ta, (ax - ta.get_width() // 2, ay - ta.get_height() // 2))
        xi, yi = meio_x + self.pos_info[0], meio_y + self.pos_info[1]
        if self.modo == 'explorar':
            if self.sub_modo_explorar == 'geral': self._desenhar_painel_explorar(tela, xi, yi, fontes, estado)
            elif self.sub_modo_explorar == 'escala': self._desenhar_painel_escala(tela, xi, yi, fontes)
            elif self.sub_modo_explorar == 'campo': self._desenhar_painel_campo(tela, xi, yi, fontes)
            elif self.sub_modo_explorar == 'sequencias': 
                self._desenhar_painel_sequencias(tela, xi, yi, fontes, centro, re, estado)
                self._desenhar_favoritas(tela, fontes, meio_x, meio_y, estado)
        else: self._desenhar_painel_desafio(tela, xi, yi, fontes)
        self._desenhar_braco_mini(tela, meio_x + self.pos_braco[0], meio_y + self.pos_braco[1], fontes, estado)

    def _desenhar_favoritas(self, tela, fontes, meio_x, meio_y, estado):
        xq, yq = meio_x - self.pos_favoritas[0], meio_y + self.pos_favoritas[1]
        self.rect_drag_layout_favoritas = pygame.Rect(xq - 10, yq - 30, 160, 260)
        
        # Background do painel
        pygame.draw.rect(tela, (30, 30, 40), self.rect_drag_layout_favoritas, border_radius=12)
        pygame.draw.rect(tela, (60, 60, 70), self.rect_drag_layout_favoritas, width=1, border_radius=12)

        if estado.drag_ativado:
            pygame.draw.rect(tela, (0, 160, 255), self.rect_drag_layout_favoritas, width=2, border_radius=12)
            tela.blit(fontes['pequena'].render('MOVER FAVORITAS', True, (0, 160, 255)), (self.rect_drag_layout_favoritas.x, self.rect_drag_layout_favoritas.y - 20))

        tela.blit(fontes['pequena'].render('Favoritas', True, (150, 150, 160)), (xq, yq - 20))
        self.rects_quick_list = []
        for iq in range(min(4, len(self.biblioteca_geral))):
            sq = self.biblioteca_geral[iq]
            rq = pygame.Rect(xq, yq + 10 + iq * 50, 140, 40)
            pygame.draw.rect(tela, (40, 40, 50), rq, border_radius=8)
            pygame.draw.rect(tela, (0, 160, 255), rq, width=1, border_radius=8)
            tsq = fontes['pequena'].render(sq['nome'], True, BRANCO)
            tela.blit(tsq, (rq.centerx - tsq.get_width() // 2, rq.centery - tsq.get_height() // 2))
            self.rects_quick_list.append({'rect': rq, 'data': sq})

    def _desenhar_painel_escala(self, tela, x, y, fontes):
        idx = self.nota_selecionada_idx
        nota = self.notas_quintas[idx] if self.modo_tonal == 'maior' else self.relativas_menores[idx].replace('m', '')
        tela.blit(fontes['titulo'].render(f'Notas da Escala de {nota} {self.modo_tonal.capitalize()}', True, (0, 160, 255)), (x, y))
        y += 50
        ints = self.intervalos_maior if self.modo_tonal == 'maior' else self.intervalos_menor
        gs = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII']
        for i, semitons in enumerate(ints):
            n = escalas.obter_nota_por_intervalo(nota, semitons)
            pygame.draw.rect(tela, (40, 40, 50), (x, y, 350, 35), border_radius=5)
            tela.blit(fontes['ui'].render(gs[i], True, (150, 150, 150)), (x + 10, y + 5))
            tela.blit(fontes['ui'].render(n, True, BRANCO), (x + 80, y + 5))
            y += 40

    def _desenhar_painel_campo(self, tela, x, y, fontes):
        idx = self.nota_selecionada_idx
        nota = self.notas_quintas[idx] if self.modo_tonal == 'maior' else self.relativas_menores[idx].replace('m', '')
        tela.blit(fontes['titulo'].render(f'Campo Harmônico de {nota} {self.modo_tonal.capitalize()}', True, (0, 160, 255)), (x, y))
        y += 50
        pygame.draw.rect(tela, (60, 60, 80), (x, y, 400, 30), border_radius=5)
        tela.blit(fontes['pequena'].render('Grau', True, BRANCO), (x + 10, y + 5))
        tela.blit(fontes['pequena'].render('Acorde', True, BRANCO), (x + 70, y + 5))
        tela.blit(fontes['pequena'].render('Notas (Tríade)', True, BRANCO), (x + 180, y + 5))
        y += 40
        ints, quals, roms = (self.intervalos_maior if self.modo_tonal == 'maior' else self.intervalos_menor), (self.qualidades_maior if self.modo_tonal == 'maior' else self.qualidades_menor), (self.graus_romanos_maior if self.modo_tonal == 'maior' else self.graus_romanos_menor)
        for i in range(7):
            nf = escalas.obter_nota_por_intervalo(nota, ints[i])
            q = quals[i]
            t = escalas.obter_terca(nf, menor=q == 'm' or q == 'dim')
            qu = escalas.obter_quinta(nf) if q != 'dim' else escalas.obter_nota_por_intervalo(nf, 6)
            pygame.draw.rect(tela, (30, 30, 45), (x, y, 400, 35), border_radius=5)
            tela.blit(fontes['ui'].render(roms[i], True, (0, 160, 255)), (x + 10, y + 5))
            tela.blit(fontes['ui'].render(nf + q, True, BRANCO), (x + 70, y + 5))
            tela.blit(fontes['pequena'].render(f'{nf} - {t} - {qu}', True, (200, 200, 200)), (x + 180, y + 8))
            y += 40

    def _desenhar_painel_sequencias(self, tela, x, y, fontes, centro, re, estado):
        lp, at = 420, 480
        aza = int(at * 0.65)
        ra = pygame.Rect(x, y, lp, aza)
        self.rect_zona_a = ra
        rb = pygame.Rect(x, y + aza + 10, lp, at - aza - 10)
        self.rect_drop_zone = rb
        tela.blit(fontes['ui'].render('Biblioteca de Progressões', True, (0, 160, 255)), (x, y - 25))
        clip = tela.get_clip()
        tela.set_clip(ra)
        yi = y + self.scroll_y_biblioteca
        self.rects_biblioteca, self.rects_biblioteca_rows = [], []
        lista = []
        if self.sequencias_custom:
            lista.append({'tipo': 'header', 'nome': 'Minhas Sequências'})
            for s in self.sequencias_custom: lista.append({'tipo': 'item', 'data': s})
        lista.append({'tipo': 'header', 'nome': 'Biblioteca Geral'})
        for s in self.biblioteca_geral: lista.append({'tipo': 'item', 'data': s})
        ints, quals = (self.intervalos_maior if self.modo_tonal == 'maior' else self.intervalos_menor), (self.qualidades_maior if self.modo_tonal == 'maior' else self.qualidades_menor)
        bn = self.notas_quintas[self.nota_selecionada_idx] if self.modo_tonal == 'maior' else self.relativas_menores[self.nota_selecionada_idx].replace('m', '')
        for item in lista:
            if item['tipo'] == 'header':
                th = fontes['pequena'].render(item['nome'].upper(), True, (120, 120, 130))
                tela.blit(th, (x, yi + 10)); yi += 35
            else:
                data = item['data']
                ri = pygame.Rect(x, yi, lp - 15, 60)
                c_bg = (40, 40, 50) if self.seq_selecionada_idx == lista.index(item) else (30, 30, 35)
                pygame.draw.rect(tela, c_bg, ri, border_radius=8)
                self.rects_biblioteca_rows.append({'rect': ri, 'data': data})
                tela.blit(fontes['pequena'].render(data['nome'], True, (200, 200, 200)), (x + 10, yi + 5))
                xb = x + 10
                for g in data['graus']:
                    l = escalas.obter_nota_por_intervalo(bn, ints[g]) + quals[g]
                    rbd = pygame.Rect(xb, yi + 28, 45, 24)
                    pygame.draw.rect(tela, (0, 120, 215), rbd, border_radius=6)
                    tb = fontes['pequena'].render(l, True, BRANCO)
                    tela.blit(tb, (rbd.centerx - tb.get_width() // 2, rbd.centery - tb.get_height() // 2))
                    self.rects_biblioteca.append({'rect': rbd, 'grau': g, 'label': l}); xb += 50
                yi += 70
        self.max_scroll_biblioteca = min(0, aza - (yi - y - self.scroll_y_biblioteca))
        tela.set_clip(clip)
        
        if self.max_scroll_biblioteca < 0:
            por = self.scroll_y_biblioteca / self.max_scroll_biblioteca
            pygame.draw.rect(tela, (60, 60, 65), (x + lp - 8, y + (aza - 40) * por, 4, 40), border_radius=2)
        pygame.draw.rect(tela, (25, 25, 30), rb, border_radius=10)
        if not self.sequencia_atual:
            tp = fontes['pequena'].render('Arraste acordes aqui para criar sua sequência', True, (100, 100, 110))
            tela.blit(tp, (rb.centerx - tp.get_width() // 2, rb.centery - 10))
        else:
            xb_b, yb_b = rb.x + 15, rb.y + 15
            self.rects_builder = []
            for iseq, its in enumerate(self.sequencia_atual):
                if iseq > 0 and xb_b > rb.x + 15:
                    sx, sy = xb_b - 12, yb_b + 17
                    pygame.draw.line(tela, (0, 120, 215), (sx - 5, sy), (sx + 3, sy), 2)
                    pygame.draw.line(tela, (0, 120, 215), (sx + 3, sy), (sx, sy - 3), 2)
                    pygame.draw.line(tela, (0, 120, 215), (sx + 3, sy), (sx, sy + 3), 2)
                rcb = pygame.Rect(xb_b, yb_b, 60, 35)
                pygame.draw.rect(tela, (0, 120, 215), rcb, border_radius=8)
                tbb = fontes['ui'].render(its['label'], True, BRANCO)
                tela.blit(tbb, (rcb.centerx - tbb.get_width() // 2, rcb.centery - tbb.get_height() // 2))
                rx = pygame.Rect(rcb.right - 12, rcb.top - 5, 18, 18)
                pygame.draw.circle(tela, (200, 50, 50), rx.center, 9)
                pygame.draw.line(tela, BRANCO, (rx.x+5, rx.y+5), (rx.right-5, rx.bottom-5), 2)
                pygame.draw.line(tela, BRANCO, (rx.right-5, rx.y+5), (rx.x+5, rx.bottom-5), 2)
                self.rects_builder.append({'rect': rcb, 'rect_x': rx, 'index': iseq})
                xb_b += 78
                if xb_b > rb.right - 70: xb_b, yb_b = rb.x + 15, yb_b + 45
        ya = rb.bottom + 10
        self.rect_btn_salvar, self.rect_btn_limpar = pygame.Rect(x, ya, 200, 40), pygame.Rect(x + 215, ya, 100, 40)
        pygame.draw.rect(tela, (0, 120, 215), self.rect_btn_salvar, border_radius=20)
        ts = fontes['ui'].render('Salvar no Perfil', True, BRANCO)
        tela.blit(ts, (self.rect_btn_salvar.centerx - ts.get_width() // 2, self.rect_btn_salvar.centery - ts.get_height() // 2))
        pygame.draw.rect(tela, (40, 40, 45), self.rect_btn_limpar, border_radius=20)
        pygame.draw.rect(tela, (200, 50, 50), self.rect_btn_limpar, width=1, border_radius=20)
        tl = fontes['pequena'].render('Limpar', True, (200, 50, 50))
        tela.blit(tl, (self.rect_btn_limpar.centerx - tl.get_width() // 2, self.rect_btn_limpar.centery - tl.get_height() // 2))
        if estado.drag_ativado:
            rl = pygame.Rect(x - 5, y - 40, lp + 10, at + 100)
            pygame.draw.rect(tela, (0, 160, 255), rl, width=2, border_radius=10)
            tela.blit(fontes['pequena'].render('MOVER PAINEL', True, (0, 160, 255)), (rl.x + 10, rl.y - 20))
            self.rect_drag_layout_info = rl
        if self.drag_item:
            gs = pygame.Surface((70, 40), pygame.SRCALPHA)
            pygame.draw.rect(gs, (0, 160, 255, 180), (0, 0, 70, 40), border_radius=8)
            tg = fontes['ui'].render(self.drag_item['label'], True, (255, 255, 255, 180))
            gs.blit(tg, (35 - tg.get_width() // 2, 20 - tg.get_height() // 2))
            tela.blit(gs, (self.drag_pos[0] - 35, self.drag_pos[1] - 20))

    def _desenhar_painel_explorar(self, tela, x, y, fontes, estado):
        idx = self.nota_selecionada_idx
        nota = self.notas_quintas[idx]
        tela.blit(fontes['titulo'].render(f'Tonalidade: {nota} Maior', True, (0, 160, 255)), (x, y))
        y += 50
        infos = [('Relativa Menor:', self.relativas_menores[idx]), ('Armadura:', self.acidentes[idx]), ('Subdominante (IV):', self.notas_quintas[(idx - 1) % 12]), ('Dominante (V):', self.notas_quintas[(idx + 1) % 12])]
        for l, v in infos:
            tela.blit(fontes['ui'].render(l, True, (180, 180, 180)), (x, y))
            tela.blit(fontes['ui'].render(v, True, BRANCO), (x + 220, y)); y += 35

    def _desenhar_painel_desafio(self, tela, x, y, fontes):
        tela.blit(fontes['ui'].render(self.pergunta_atual, True, BRANCO), (x, y)); y += 60
        self.rects_opcoes_desafio = []
        for op in self.opcoes_desafio:
            r = pygame.Rect(x, y, 300, 45); self.rects_opcoes_desafio.append((op, r))
            c_bg = (50, 150, 50) if self.estado_desafio == 'respondido' and op == self.resposta_correta else ((150, 50, 50) if self.estado_desafio == 'respondido' and op == self.resposta_usuario else (50, 50, 60))
            pygame.draw.rect(tela, c_bg, r, border_radius=8)
            to = fontes['ui'].render(op, True, BRANCO)
            tela.blit(to, (r.centerx - to.get_width() // 2, r.centery - to.get_height() // 2)); y += 55
        if self.estado_desafio == 'respondido':
            tela.blit(fontes['ui'].render(self.feedback_desafio, True, self.cor_feedback), (x, y + 10))
            self.rect_btn_prox = pygame.Rect(x, y + 50, 120, 40)
            pygame.draw.rect(tela, (0, 120, 215), self.rect_btn_prox, border_radius=5)
            tp = fontes['ui'].render('Próxima', True, BRANCO)
            tela.blit(tp, (self.rect_btn_prox.centerx - tp.get_width() // 2, self.rect_btn_prox.centery - tp.get_height() // 2))

    def _desenhar_braco_mini(self, tela, xc, y, fontes, estado):
        l, h = 1100, 130
        x = xc - l // 2
        self.rect_drag_layout_braco = pygame.Rect(x - 10, y - 10, l + 20, h + 20)
        if estado.drag_ativado:
            pygame.draw.rect(tela, (0, 160, 255), self.rect_drag_layout_braco, width=2, border_radius=10)
            tela.blit(fontes['pequena'].render('MOVER BRAÇO', True, (0, 160, 255)), (x, y - 25))
        pygame.draw.rect(tela, (35, 30, 35), (x, y, l, h), border_radius=5)
        nc, ec, eca = estado.NUM_CORDAS, h / (estado.NUM_CORDAS - 1), l / 18
        for c in range(19): pygame.draw.line(tela, (80, 80, 80), (x + c * eca, y), (x + c * eca, y + h), 1)
        for i in range(nc): pygame.draw.line(tela, (160, 160, 160), (x, y + i * ec), (x + l, y + i * ec), 1)
        bn = self.notas_quintas[self.nota_selecionada_idx] if self.modo_tonal == 'maior' else self.relativas_menores[self.nota_selecionada_idx].replace('m', '')
        nd, ints = {}, (self.intervalos_maior if self.modo_tonal == 'maior' else self.intervalos_menor)
        if self.sub_modo_explorar == 'sequencias' and self.seq_selecionada_idx != -1:
            lista = []
            if self.sequencias_custom: lista.extend(self.sequencias_custom)
            lista.extend(self.biblioteca_geral)
            if 0 <= self.seq_selecionada_idx < len(lista):
                for g in lista[self.seq_selecionada_idx]['graus']: nd[escalas.obter_nota_por_intervalo(bn, ints[g])] = (255, 180, 0)
        else:
            for s in ints: nd[escalas.obter_nota_por_intervalo(bn, s)] = (0, 160, 255) if s == 0 else (150, 150, 150)
        afinacao = ['E', 'A', 'D', 'G', 'B', 'E', 'B']
        for c in range(nc):
            nab = afinacao[c + (1 if nc <= 6 else 0)]
            for casa in range(18):
                nc_calc = escalas.obter_nota(nab, casa)
                if nc_calc in nd:
                    cx, cy = x + casa * eca + (eca // 2 if casa > 0 else -10), y + (nc - 1 - c) * ec
                    pygame.draw.circle(tela, nd[nc_calc], (int(cx), int(cy)), 12)
                    tc = fontes['pequena'].render(nc_calc, True, BRANCO)
                    tela.blit(tc, (cx - tc.get_width() // 2, cy - tc.get_height() // 2))

    def tratar_eventos(self, evento, pos, estado):
        if estado.drag_ativado:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if hasattr(self, 'rect_drag_layout_info') and self.rect_drag_layout_info.collidepoint(pos): self.bloco_arrastando = 'info'
                elif hasattr(self, 'rect_drag_layout_roda') and self.rect_drag_layout_roda.collidepoint(pos): self.bloco_arrastando = 'roda'
                elif hasattr(self, 'rect_drag_layout_braco') and self.rect_drag_layout_braco.collidepoint(pos): self.bloco_arrastando = 'braco'
                elif hasattr(self, 'rect_drag_layout_header') and self.rect_drag_layout_header.collidepoint(pos): self.bloco_arrastando = 'header'
                elif hasattr(self, 'rect_drag_layout_favoritas') and self.rect_drag_layout_favoritas.collidepoint(pos): self.bloco_arrastando = 'favoritas'
                if self.bloco_arrastando:
                    self.drag_offset_x, self.drag_offset_y = pos; return True
            if evento.type == pygame.MOUSEMOTION and self.bloco_arrastando:
                dx, dy = pos[0] - self.drag_offset_x, pos[1] - self.drag_offset_y
                if self.bloco_arrastando == 'info': self.pos_info[0] += dx; self.pos_info[1] += dy
                elif self.bloco_arrastando == 'roda': self.pos_roda[0] -= dx; self.pos_roda[1] += dy
                elif self.bloco_arrastando == 'braco': self.pos_braco[0] += dx; self.pos_braco[1] += dy
                elif self.bloco_arrastando == 'header': self.pos_header[0] += dx; self.pos_header[1] += dy
                elif self.bloco_arrastando == 'favoritas': self.pos_favoritas[0] -= dx; self.pos_favoritas[1] += dy
                self.drag_offset_x, self.drag_offset_y = pos; return True
            if evento.type == pygame.MOUSEBUTTONUP: self.bloco_arrastando = None
        if evento.type == pygame.MOUSEWHEEL and self.sub_modo_explorar == 'sequencias' and hasattr(self, 'rect_zona_a') and self.rect_zona_a.collidepoint(pos):
            self.scroll_y_biblioteca += evento.y * 25
            self.scroll_y_biblioteca = max(self.max_scroll_biblioteca, min(0, self.scroll_y_biblioteca)); return True
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if hasattr(self, 'rect_btn_limpar') and self.rect_btn_limpar.collidepoint(pos): self.sequencia_atual = []; return True
            if hasattr(self, 'rect_btn_salvar') and self.rect_btn_salvar.collidepoint(pos):
                if self.sequencia_atual: self.sequencias_custom.insert(0, {'nome': f'Seq {len(self.sequencias_custom)+1}', 'graus': [i['grau'] for i in self.sequencia_atual]}); self._salvar_sequencias_custom()
                return True
            if self.sub_modo_explorar == 'sequencias':
                dentro_bib = hasattr(self, 'rect_zona_a') and self.rect_zona_a.collidepoint(pos)
                if hasattr(self, 'rects_builder'):
                    for ib in self.rects_builder:
                        if ib['rect_x'].collidepoint(pos): self.sequencia_atual.pop(ib['index']); return True
                        if ib['rect'].collidepoint(pos):
                            val = self.sequencia_atual[ib['index']]
                            self.drag_item = {'tipo': 'badge', 'valor': val, 'origem': 'builder', 'index_origem': ib['index'], 'label': val['label']}
                            self.drag_pos = pos; return True
                if hasattr(self, 'rects_quick_list'):
                    for q in self.rects_quick_list:
                        if q['rect'].collidepoint(pos):
                            ints, quals = (self.intervalos_maior if self.modo_tonal == 'maior' else self.intervalos_menor), (self.qualidades_maior if self.modo_tonal == 'maior' else self.qualidades_menor)
                            bn = self.notas_quintas[self.nota_selecionada_idx] if self.modo_tonal == 'maior' else self.relativas_menores[self.nota_selecionada_idx].replace('m', '')
                            itens = [{'grau': g, 'label': escalas.obter_nota_por_intervalo(bn, ints[g]) + quals[g]} for g in q['data']['graus']]
                            self.drag_item = {'tipo': 'sequencia', 'valor': itens, 'origem': 'quick', 'label': q['data']['nome']}
                            self.drag_pos = pos; return True
                if dentro_bib:
                    if hasattr(self, 'rects_biblioteca'):
                        for b in self.rects_biblioteca:
                            if b['rect'].collidepoint(pos): self.drag_item = {'tipo': 'badge', 'valor': {'grau': b['grau'], 'label': b['label']}, 'origem': 'biblioteca', 'label': b['label']}; self.drag_pos = pos; return True
                    if hasattr(self, 'rects_biblioteca_rows'):
                        for ir, row in enumerate(self.rects_biblioteca_rows):
                            if row['rect'].collidepoint(pos):
                                ints, quals = (self.intervalos_maior if self.modo_tonal == 'maior' else self.intervalos_menor), (self.qualidades_maior if self.modo_tonal == 'maior' else self.qualidades_menor)
                                bn = self.notas_quintas[self.nota_selecionada_idx] if self.modo_tonal == 'maior' else self.relativas_menores[self.nota_selecionada_idx].replace('m', '')
                                itens = [{'grau': g, 'label': escalas.obter_nota_por_intervalo(bn, ints[g]) + quals[g]} for g in row['data']['graus']]
                                self.drag_item = {'tipo': 'sequencia', 'valor': itens, 'origem': 'biblioteca_row', 'label': row['data']['nome']}
                                self.drag_pos, self.seq_selecionada_idx = pos, ir; return True
            for i, r in self.rects_notas:
                if r.collidepoint(pos):
                    self.nota_selecionada_idx = i
                    if self.sub_modo_explorar == 'sequencias' and not estado.drag_ativado:
                        ints, quals = (self.intervalos_maior if self.modo_tonal == 'maior' else self.intervalos_menor), (self.qualidades_maior if self.modo_tonal == 'maior' else self.qualidades_menor)
                        bn = self.notas_quintas[self.nota_selecionada_idx] if self.modo_tonal == 'maior' else self.relativas_menores[self.nota_selecionada_idx].replace('m', '')
                        nota_clicada = self.notas_quintas[i]
                        grau = next((g for g in range(7) if escalas.obter_nota_por_intervalo(bn, ints[g]) == nota_clicada), -1)
                        if grau != -1: self.drag_item = {'tipo': 'badge', 'valor': {'grau': grau, 'label': nota_clicada + quals[grau]}, 'origem': 'ciclo', 'label': nota_clicada + quals[grau]}; self.drag_pos = pos
                    return True
        if evento.type == pygame.MOUSEMOTION and self.drag_item:
            self.drag_pos = pos
            if hasattr(self, 'rect_drop_zone'): self.drop_zone_active = self.rect_drop_zone.collidepoint(pos)
            return True
        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1 and self.drag_item:
            if self.drop_zone_active:
                idx_drop = len(self.sequencia_atual)
                if hasattr(self, 'rects_builder'):
                    for ib, rb in enumerate(self.rects_builder):
                        if pos[0] < rb['rect'].centerx: idx_drop = ib; break
                if self.drag_item.get('tipo') == 'sequencia':
                    for ii, iv in enumerate(self.drag_item['valor']): self.sequencia_atual.insert(idx_drop + ii, iv)
                elif self.drag_item['origem'] == 'builder':
                    it = self.sequencia_atual.pop(self.drag_item['index_origem'])
                    if self.drag_item['index_origem'] < idx_drop: idx_drop -= 1
                    self.sequencia_atual.insert(max(0, idx_drop), it)
                else: self.sequencia_atual.insert(idx_drop, self.drag_item['valor'])
            self.drag_item, self.drop_zone_active = None, False; return True
        if evento.type == pygame.MOUSEBUTTONUP: self.drag_item, self.drop_zone_active, self.bloco_arrastando = None, False, None
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1: return self.tratar_cliques(pos, estado)
        return False

    def tratar_cliques(self, pos, estado):
        if self.rect_toggle_tonal.collidepoint(pos): self.modo_tonal = 'menor' if self.modo_tonal == 'maior' else 'maior'; self.seq_selecionada_idx = -1; return True
        for k, r in self.rects_sub_modos.items():
            if r.collidepoint(pos): self.sub_modo_explorar = k; return True
        for i, r in self.rects_notas:
            if r.collidepoint(pos): self.nota_selecionada_idx = i; return True
        for m, r in self.rects_botoes.items():
            if r.collidepoint(pos):
                if m == 'tipo': self.tipo_ciclo = 'quartas' if self.tipo_ciclo == 'quintas' else 'quintas'
                else: self.modo = m
                return True
        if self.modo == 'desafio':
            if self.estado_desafio != 'respondido':
                for op, r in self.rects_opcoes_desafio:
                    if r.collidepoint(pos):
                        self.resposta_usuario, self.estado_desafio = op, 'respondido'
                        if op == self.resposta_correta: self.acertos += 1; self.feedback_desafio, self.cor_feedback = 'Correto!', (100, 255, 100)
                        else: self.feedback_desafio, self.cor_feedback = f'Resposta: {self.resposta_correta}', (255, 100, 100)
                        return True
            elif hasattr(self, 'rect_btn_prox') and self.rect_btn_prox.collidepoint(pos): self.gerar_pergunta(); return True
        return False
