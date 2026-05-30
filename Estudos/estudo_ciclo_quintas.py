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
        self.sequencias_maior = [{'nome': 'II - V - I', 'graus': [1, 4, 0]}, {'nome': 'I - VI - IV - V', 'graus': [0, 5, 3, 4]}, {'nome': 'IV - V - I', 'graus': [3, 4, 0]}, {'nome': 'I - V - VI - IV', 'graus': [0, 4, 5, 3]}]
        self.sequencias_menor = [{'nome': 'ii° - V - i', 'graus': [1, 4, 0]}, {'nome': 'i - VI - VII', 'graus': [0, 5, 6]}, {'nome': 'iv - V - i', 'graus': [3, 4, 0]}]
        self.seq_selecionada_idx = -1
        self.nota_selecionada_idx = 0
        self.rects_notas = []
        self.rects_botoes = {}
        self.rects_sub_modos = {}
        self.rect_toggle_tonal = pygame.Rect(0, 0, 0, 0)
        self.pergunta_atual = ''
        self.opcoes_desafio = []
        self.resposta_correta = ''
        self.feedback_desafio = ''
        self.cor_feedback = BRANCO
        self.estado_desafio = None
        self.acertos = 0

    def inicializar(self, estado):
        """
            Como funciona: Prepara variáveis e limpa dados de sessões anteriores.
            Para que serve: Configura o ambiente necessário para início de uma nova tarefa.
            Onde é usada: Chamado a partir do módulo ou classe base de 'estudo_ciclo_quintas'.
        """
        self.inicializado = True
        self.gerar_pergunta()

    def gerar_pergunta(self):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'gerar pergunta'.
            Para que serve: Realiza as tarefas fundamentais de 'gerar pergunta' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'gerar pergunta'.
        """
        tipo_pergunta = random.choice(['relativa', 'acidente', 'quinta', 'quarta'])
        idx = random.randint(0, 11)
        nota = self.notas_quintas[idx]
        if tipo_pergunta == 'relativa':
            self.pergunta_atual = f'Qual a relativa menor de {nota}?'
            self.resposta_correta = self.relativas_menores[idx]
            opcoes = [self.resposta_correta]
            while len(opcoes) < 4:
                outra = random.choice(self.relativas_menores)
                if outra not in opcoes:
                    opcoes.append(outra)
        elif tipo_pergunta == 'acidente':
            self.pergunta_atual = f'Quantos acidentes tem a escala de {nota}?'
            self.resposta_correta = self.acidentes[idx]
            opcoes = [self.resposta_correta]
            while len(opcoes) < 4:
                outra = random.choice(self.acidentes)
                if outra not in opcoes:
                    opcoes.append(outra)
        elif tipo_pergunta == 'quinta':
            self.pergunta_atual = f'Qual é a 5ª justa de {nota}?'
            prox_idx = (idx + 1) % 12
            self.resposta_correta = self.notas_quintas[prox_idx]
            opcoes = [self.resposta_correta]
            while len(opcoes) < 4:
                outra = random.choice(self.notas_quintas)
                if outra not in opcoes:
                    opcoes.append(outra)
        else:
            self.pergunta_atual = f'Qual é a 4ª justa de {nota}?'
            prox_idx = (idx - 1) % 12
            self.resposta_correta = self.notas_quintas[prox_idx]
            opcoes = [self.resposta_correta]
            while len(opcoes) < 4:
                outra = random.choice(self.notas_quintas)
                if outra not in opcoes:
                    opcoes.append(outra)
        random.shuffle(opcoes)
        self.opcoes_desafio = opcoes
        self.estado_desafio = None
        self.feedback_desafio = ''

    def desenhar(self, tela, estado, fontes, meio_x, meio_y, cam_x, cam_y):
        """
            Como funciona: Utiliza funções de renderização do Pygame para desenhar na tela.
            Para que serve: Apresenta o elemento visual 'desenhar' na interface gráfica.
            Onde é usada: Chamado a partir do módulo ou classe base de 'estudo_ciclo_quintas'.
        """
        if not self.inicializado:
            self.inicializar(estado)
        self.rects_botoes['explorar'] = pygame.Rect(meio_x - 220, cam_y + 100, 140, 40)
        self.rects_botoes['desafio'] = pygame.Rect(meio_x - 70, cam_y + 100, 140, 40)
        self.rects_botoes['tipo'] = pygame.Rect(meio_x + 80, cam_y + 100, 140, 40)
        cor_exp = (0, 160, 255) if self.modo == 'explorar' else (60, 60, 70)
        cor_des = (0, 160, 255) if self.modo == 'desafio' else (60, 60, 70)
        pygame.draw.rect(tela, cor_exp, self.rects_botoes['explorar'], border_radius=8)
        pygame.draw.rect(tela, cor_des, self.rects_botoes['desafio'], border_radius=8)
        pygame.draw.rect(tela, (80, 50, 120), self.rects_botoes['tipo'], border_radius=8)
        txt_exp = fontes['ui'].render('Exploração', True, BRANCO)
        txt_des = fontes['ui'].render('Desafio', True, BRANCO)
        txt_tipo = fontes['ui'].render(f'Ciclo: {self.tipo_ciclo.capitalize()}', True, BRANCO)
        tela.blit(txt_exp, (self.rects_botoes['explorar'].centerx - txt_exp.get_width() // 2, self.rects_botoes['explorar'].centery - txt_exp.get_height() // 2))
        tela.blit(txt_des, (self.rects_botoes['desafio'].centerx - txt_des.get_width() // 2, self.rects_botoes['desafio'].centery - txt_des.get_height() // 2))
        tela.blit(txt_tipo, (self.rects_botoes['tipo'].centerx - txt_tipo.get_width() // 2, self.rects_botoes['tipo'].centery - txt_tipo.get_height() // 2))
        if self.modo == 'explorar':
            sub_modos = [('Geral', 'geral'), ('Escala', 'escala'), ('Campo', 'campo'), ('Sequências', 'sequencias')]
            x_sub = meio_x - 220
            for nome, chave in sub_modos:
                rect = pygame.Rect(x_sub, cam_y + 150, 105, 30)
                self.rects_sub_modos[chave] = rect
                cor = (0, 120, 215) if self.sub_modo_explorar == chave else (40, 40, 50)
                pygame.draw.rect(tela, cor, rect, border_radius=5)
                txt = fontes['pequena'].render(nome, True, BRANCO)
                tela.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))
                x_sub += 115
            self.rect_toggle_tonal = pygame.Rect(x_sub + 10, cam_y + 150, 120, 30)
            cor_toggle = (200, 150, 0) if self.modo_tonal == 'menor' else (0, 150, 200)
            pygame.draw.rect(tela, cor_toggle, self.rect_toggle_tonal, border_radius=5)
            txt_t = fontes['pequena'].render(f'Modo: {self.modo_tonal.capitalize()}', True, BRANCO)
            tela.blit(txt_t, (self.rect_toggle_tonal.centerx - txt_t.get_width() // 2, self.rect_toggle_tonal.centery - txt_t.get_height() // 2))
        raio_externo = 180
        raio_interno = 120
        centro_ciclo = (meio_x - 220, meio_y + 30)
        pygame.draw.circle(tela, (40, 40, 50), centro_ciclo, raio_externo + 40, width=2)
        pygame.draw.circle(tela, (30, 30, 40), centro_ciclo, raio_externo + 10)
        self.rects_notas.clear()
        indices_seq = []
        intervalos = self.intervalos_maior if self.modo_tonal == 'maior' else self.intervalos_menor
        if self.sub_modo_explorar == 'sequencias' and self.seq_selecionada_idx != -1:
            sequencias = self.sequencias_maior if self.modo_tonal == 'maior' else self.sequencias_menor
            seq = sequencias[self.seq_selecionada_idx]
            base_nota = self.notas_quintas[self.nota_selecionada_idx] if self.modo_tonal == 'maior' else self.relativas_menores[self.nota_selecionada_idx].replace('m', '')
            for grau in seq['graus']:
                semitons = intervalos[grau]
                nota_alvo = escalas.obter_nota_por_intervalo(base_nota, semitons)
                if nota_alvo in self.notas_quintas:
                    indices_seq.append(self.notas_quintas.index(nota_alvo))
        for i in range(12):
            angulo = math.radians(i * 30 - 90)
            if self.tipo_ciclo == 'quartas':
                angulo = math.radians(-i * 30 - 90)
            nx = centro_ciclo[0] + math.cos(angulo) * raio_externo
            ny = centro_ciclo[1] + math.sin(angulo) * raio_externo
            mx = centro_ciclo[0] + math.cos(angulo) * raio_interno
            my = centro_ciclo[1] + math.sin(angulo) * raio_interno
            if i == self.nota_selecionada_idx:
                pygame.draw.circle(tela, (0, 160, 255), (int(nx), int(ny)), 35, width=3)
                pygame.draw.line(tela, (100, 100, 150), centro_ciclo, (int(nx), int(ny)), 1)
            elif i in indices_seq:
                pygame.draw.circle(tela, (200, 150, 0), (int(nx), int(ny)), 30, width=2)
            rect_nota = pygame.Rect(nx - 30, ny - 30, 60, 60)
            self.rects_notas.append((i, rect_nota))
            txt_nota = fontes['titulo'].render(self.notas_quintas[i], True, BRANCO)
            tela.blit(txt_nota, (nx - txt_nota.get_width() // 2, ny - txt_nota.get_height() // 2))
            txt_rel = fontes['pequena'].render(self.relativas_menores[i], True, (200, 200, 200))
            tela.blit(txt_rel, (mx - txt_rel.get_width() // 2, my - txt_rel.get_height() // 2))
            ax = centro_ciclo[0] + math.cos(angulo) * (raio_externo + 60)
            ay = centro_ciclo[1] + math.sin(angulo) * (raio_externo + 60)
            txt_acid = fontes['pequena'].render(self.acidentes[i], True, (150, 150, 150))
            tela.blit(txt_acid, (ax - txt_acid.get_width() // 2, ay - txt_acid.get_height() // 2))
        x_info = meio_x + 100
        y_info = meio_y - 120
        if self.modo == 'explorar':
            if self.sub_modo_explorar == 'geral':
                self._desenhar_painel_explorar(tela, x_info, y_info, fontes, estado)
            elif self.sub_modo_explorar == 'escala':
                self._desenhar_painel_escala(tela, x_info, y_info, fontes)
            elif self.sub_modo_explorar == 'campo':
                self._desenhar_painel_campo(tela, x_info, y_info, fontes)
            elif self.sub_modo_explorar == 'sequencias':
                self._desenhar_painel_sequencias(tela, x_info, y_info, fontes)
        else:
            self._desenhar_painel_desafio(tela, x_info, y_info, fontes)
        self._desenhar_braco_mini(tela, meio_x, meio_y + 320, fontes, estado)

    def _desenhar_painel_escala(self, tela, x, y, fontes):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação ' desenhar painel escala'.
            Para que serve: Realiza as tarefas fundamentais de ' desenhar painel escala' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de ' desenhar painel escala'.
        """
        idx = self.nota_selecionada_idx
        nota = self.notas_quintas[idx] if self.modo_tonal == 'maior' else self.relativas_menores[idx].replace('m', '')
        txt_tit = fontes['titulo'].render(f'Notas da Escala de {nota} {self.modo_tonal.capitalize()}', True, (0, 160, 255))
        tela.blit(txt_tit, (x, y))
        y += 50
        intervalos = self.intervalos_maior if self.modo_tonal == 'maior' else self.intervalos_menor
        notas_escala = [escalas.obter_nota_por_intervalo(nota, semitons) for semitons in intervalos]
        graus = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII']
        for i, n in enumerate(notas_escala):
            pygame.draw.rect(tela, (40, 40, 50), (x, y, 350, 35), border_radius=5)
            t_grau = fontes['ui'].render(graus[i], True, (150, 150, 150))
            t_nota = fontes['ui'].render(n, True, BRANCO)
            tela.blit(t_grau, (x + 10, y + 5))
            tela.blit(t_nota, (x + 80, y + 5))
            y += 40

    def _desenhar_painel_campo(self, tela, x, y, fontes):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação ' desenhar painel campo'.
            Para que serve: Realiza as tarefas fundamentais de ' desenhar painel campo' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de ' desenhar painel campo'.
        """
        idx = self.nota_selecionada_idx
        nota = self.notas_quintas[idx] if self.modo_tonal == 'maior' else self.relativas_menores[idx].replace('m', '')
        txt_tit = fontes['titulo'].render(f'Campo Harmônico de {nota} {self.modo_tonal.capitalize()}', True, (0, 160, 255))
        tela.blit(txt_tit, (x, y))
        y += 50
        pygame.draw.rect(tela, (60, 60, 80), (x, y, 400, 30), border_radius=5)
        tela.blit(fontes['pequena'].render('Grau', True, BRANCO), (x + 10, y + 5))
        tela.blit(fontes['pequena'].render('Acorde', True, BRANCO), (x + 70, y + 5))
        tela.blit(fontes['pequena'].render('Notas (Tríade)', True, BRANCO), (x + 180, y + 5))
        y += 40
        intervalos = self.intervalos_maior if self.modo_tonal == 'maior' else self.intervalos_menor
        qualidades = self.qualidades_maior if self.modo_tonal == 'maior' else self.qualidades_menor
        romanos = self.graus_romanos_maior if self.modo_tonal == 'maior' else self.graus_romanos_menor
        for i in range(7):
            semitons = intervalos[i]
            nota_fund = escalas.obter_nota_por_intervalo(nota, semitons)
            qualidade = qualidades[i]
            nome_acorde = nota_fund + qualidade
            romano = romanos[i]
            terca = escalas.obter_terca(nota_fund, menor=qualidade == 'm' or qualidade == 'dim')
            quinta = escalas.obter_quinta(nota_fund)
            if qualidade == 'dim':
                quinta = escalas.obter_nota_por_intervalo(nota_fund, 6)
            notas_triade = f'{nota_fund} - {terca} - {quinta}'
            pygame.draw.rect(tela, (30, 30, 45), (x, y, 400, 35), border_radius=5)
            t_rom = fontes['ui'].render(romano, True, (0, 160, 255))
            t_acorde = fontes['ui'].render(nome_acorde, True, BRANCO)
            t_notas = fontes['pequena'].render(notas_triade, True, (200, 200, 200))
            tela.blit(t_rom, (x + 10, y + 5))
            tela.blit(t_acorde, (x + 70, y + 5))
            tela.blit(t_notas, (x + 180, y + 8))
            y += 40

    def _desenhar_painel_sequencias(self, tela, x, y, fontes):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação ' desenhar painel sequencias'.
            Para que serve: Realiza as tarefas fundamentais de ' desenhar painel sequencias' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de ' desenhar painel sequencias'.
        """
        txt_tit = fontes['titulo'].render(f'Sequências: {self.modo_tonal.capitalize()}', True, (0, 160, 255))
        tela.blit(txt_tit, (x, y))
        y += 40
        msg = 'Dica: Pratique estas sequências no instrumento para dominar o som da tonalidade.'
        tela.blit(fontes['pequena'].render(msg, True, (150, 150, 150)), (x, y))
        y += 30
        sequencias = self.sequencias_maior if self.modo_tonal == 'maior' else self.sequencias_menor
        intervalos = self.intervalos_maior if self.modo_tonal == 'maior' else self.intervalos_menor
        qualidades = self.qualidades_maior if self.modo_tonal == 'maior' else self.qualidades_menor
        self.rects_seq_btns = []
        for i, seq in enumerate(sequencias):
            rect = pygame.Rect(x, y, 400, 45)
            self.rects_seq_btns.append((i, rect))
            cor = (0, 100, 200) if self.seq_selecionada_idx == i else (45, 45, 55)
            pygame.draw.rect(tela, cor, rect, border_radius=8)
            base_nota = self.notas_quintas[self.nota_selecionada_idx] if self.modo_tonal == 'maior' else self.relativas_menores[self.nota_selecionada_idx].replace('m', '')
            notas_seq = []
            for grau in seq['graus']:
                n = escalas.obter_nota_por_intervalo(base_nota, intervalos[grau])
                notas_seq.append(n + qualidades[grau])
            txt_n = fontes['ui'].render(seq['nome'], True, BRANCO)
            txt_prog = fontes['ui'].render(' > '.join(notas_seq), True, BRANCO)
            tela.blit(txt_n, (x + 10, y + 10))
            tela.blit(txt_prog, (x + 130, y + 10))
            y += 55

    def _desenhar_painel_explorar(self, tela, x, y, fontes, estado):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação ' desenhar painel explorar'.
            Para que serve: Realiza as tarefas fundamentais de ' desenhar painel explorar' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de ' desenhar painel explorar'.
        """
        idx = self.nota_selecionada_idx
        nota = self.notas_quintas[idx]
        relativa = self.relativas_menores[idx]
        acid = self.acidentes[self.nota_selecionada_idx]
        txt_tit = fontes['titulo'].render(f'Tonalidade: {nota} Maior', True, (0, 160, 255))
        tela.blit(txt_tit, (x, y))
        y += 50
        infos = [(f'Relativa Menor:', relativa), (f'Armadura de Clave:', acid), (f'Subdominante (IV):', self.notas_quintas[(idx - 1) % 12]), (f'Dominante (V):', self.notas_quintas[(idx + 1) % 12])]
        for label, val in infos:
            t_label = fontes['ui'].render(label, True, (180, 180, 180))
            t_val = fontes['ui'].render(val, True, BRANCO)
            tela.blit(t_label, (x, y))
            tela.blit(t_val, (x + 220, y))
            y += 35
        y += 20
        dica = 'Dica: No sentido horário (Quintas), adicionamos um sustenido (#) ou removemos um bemol (b). No sentido anti-horário (Quartas), adicionamos um bemol ou removemos um sustenido.'
        palavras = dica.split(' ')
        linha = ''
        for p in palavras:
            if fontes['pequena'].size(linha + p)[0] < 400:
                linha += p + ' '
            else:
                t_l = fontes['pequena'].render(linha, True, (130, 130, 130))
                tela.blit(t_l, (x, y))
                y += 18
                linha = p + ' '
        tela.blit(fontes['pequena'].render(linha, True, (130, 130, 130)), (x, y))

    def _desenhar_painel_desafio(self, tela, x, y, fontes):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação ' desenhar painel desafio'.
            Para que serve: Realiza as tarefas fundamentais de ' desenhar painel desafio' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de ' desenhar painel desafio'.
        """
        txt_pergunta = fontes['ui'].render(self.pergunta_atual, True, BRANCO)
        tela.blit(txt_pergunta, (x, y))
        y += 60
        self.rects_opcoes_desafio = []
        for i, op in enumerate(self.opcoes_desafio):
            rect = pygame.Rect(x, y, 300, 45)
            self.rects_opcoes_desafio.append((op, rect))
            cor_bg = (50, 50, 60)
            if self.estado_desafio == 'respondido':
                if op == self.resposta_correta:
                    cor_bg = (50, 150, 50)
                elif op == self.resposta_usuario:
                    cor_bg = (150, 50, 50)
            pygame.draw.rect(tela, cor_bg, rect, border_radius=8)
            pygame.draw.rect(tela, (100, 100, 100), rect, width=1, border_radius=8)
            txt_op = fontes['ui'].render(op, True, BRANCO)
            tela.blit(txt_op, (rect.centerx - txt_op.get_width() // 2, rect.centery - txt_op.get_height() // 2))
            y += 55
        if self.estado_desafio == 'respondido':
            txt_f = fontes['ui'].render(self.feedback_desafio, True, self.cor_feedback)
            tela.blit(txt_f, (x, y + 10))
            self.rect_btn_prox = pygame.Rect(x, y + 50, 120, 40)
            pygame.draw.rect(tela, (0, 120, 215), self.rect_btn_prox, border_radius=5)
            txt_p = fontes['ui'].render('Próxima', True, BRANCO)
            tela.blit(txt_p, (self.rect_btn_prox.centerx - txt_p.get_width() // 2, self.rect_btn_prox.centery - txt_p.get_height() // 2))

    def _desenhar_braco_mini(self, tela, x_centro, y, fontes, estado):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação ' desenhar braco mini'.
            Para que serve: Realiza as tarefas fundamentais de ' desenhar braco mini' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de ' desenhar braco mini'.
        """
        largura = 1100
        altura = 130
        x = x_centro - largura // 2
        pygame.draw.rect(tela, (35, 30, 35), (x, y, largura, altura), border_radius=5)
        num_cordas = estado.NUM_CORDAS
        espaco_cordas = altura / (num_cordas - 1)
        espaco_casas = largura / 18
        for c in range(19):
            pygame.draw.line(tela, (80, 80, 80), (x + c * espaco_casas, y), (x + c * espaco_casas, y + altura), 1)
        for i in range(num_cordas):
            pygame.draw.line(tela, (160, 160, 160), (x, y + i * espaco_cordas), (x + largura, y + i * espaco_cordas), 1)
        base_nota = self.notas_quintas[self.nota_selecionada_idx] if self.modo_tonal == 'maior' else self.relativas_menores[self.nota_selecionada_idx].replace('m', '')
        notas_destaque = {}
        intervalos = self.intervalos_maior if self.modo_tonal == 'maior' else self.intervalos_menor
        if self.sub_modo_explorar == 'geral':
            notas_destaque = {base_nota: (0, 160, 255), escalas.obter_nota_por_intervalo(base_nota, 5): (0, 200, 100), escalas.obter_nota_por_intervalo(base_nota, 7): (200, 50, 50), self.relativas_menores[self.nota_selecionada_idx].replace('m', ''): (150, 100, 255)}
        elif self.sub_modo_explorar == 'escala' or self.sub_modo_explorar == 'campo':
            for semitons in intervalos:
                n = escalas.obter_nota_por_intervalo(base_nota, semitons)
                notas_destaque[n] = (0, 160, 255) if n == base_nota else (150, 150, 150)
        elif self.sub_modo_explorar == 'sequencias' and self.seq_selecionada_idx != -1:
            sequencias = self.sequencias_maior if self.modo_tonal == 'maior' else self.sequencias_menor
            seq = sequencias[self.seq_selecionada_idx]
            for grau in seq['graus']:
                n = escalas.obter_nota_por_intervalo(base_nota, intervalos[grau])
                notas_destaque[n] = (255, 180, 0)
        try:
            afinacao = lista_afinacoes[estado.indice_afinacao]['notas']
        except:
            afinacao = ['E', 'A', 'D', 'G', 'B', 'E', 'B']
        for c in range(num_cordas):
            nota_aberta = afinacao[c + (1 if num_cordas <= 6 else 0)]
            for casa in range(18):
                nota_calc = escalas.obter_nota(nota_aberta, casa)
                if nota_calc in notas_destaque:
                    cx = x + casa * espaco_casas + (espaco_casas // 2 if casa > 0 else -10)
                    cy = y + (num_cordas - 1 - c) * espaco_cordas
                    pygame.draw.circle(tela, notas_destaque[nota_calc], (int(cx), int(cy)), 12)
                    txt = fontes['pequena'].render(nota_calc, True, BRANCO)
                    tela.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))

    def tratar_cliques(self, pos, estado):
        """
            Como funciona: Verifica colisões e processa inputs do mouse/teclado.
            Para que serve: Mapeia ações do usuário para atualizações de estado.
            Onde é usada: Chamado a partir do módulo ou classe base de 'estudo_ciclo_quintas'.
        """
        if self.rect_toggle_tonal.collidepoint(pos):
            self.modo_tonal = 'menor' if self.modo_tonal == 'maior' else 'maior'
            self.seq_selecionada_idx = -1
            return True
        for chave, rect in self.rects_sub_modos.items():
            if rect.collidepoint(pos):
                self.sub_modo_explorar = chave
                return True
        if self.sub_modo_explorar == 'sequencias':
            for idx, rect in self.rects_seq_btns:
                if rect.collidepoint(pos):
                    self.seq_selecionada_idx = idx
                    return True
        for i, rect in self.rects_notas:
            if rect.collidepoint(pos):
                self.nota_selecionada_idx = i
                return True
        for modo, rect in self.rects_botoes.items():
            if rect.collidepoint(pos):
                if modo == 'tipo':
                    self.tipo_ciclo = 'quartas' if self.tipo_ciclo == 'quintas' else 'quintas'
                else:
                    self.modo = modo
                return True
        if self.modo == 'desafio':
            if self.estado_desafio != 'respondido':
                for op, rect in self.rects_opcoes_desafio:
                    if rect.collidepoint(pos):
                        self.resposta_usuario = op
                        self.estado_desafio = 'respondido'
                        if op == self.resposta_correta:
                            self.acertos += 1
                            self.feedback_desafio = 'Correto! Excelente conhecimento teórico.'
                            self.cor_feedback = (100, 255, 100)
                        else:
                            self.feedback_desafio = f'Ops! A resposta era {self.resposta_correta}.'
                            self.cor_feedback = (255, 100, 100)
                        return True
            elif hasattr(self, 'rect_btn_prox') and self.rect_btn_prox.collidepoint(pos):
                self.gerar_pergunta()
                return True
        return False