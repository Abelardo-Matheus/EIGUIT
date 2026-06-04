import pygame
import os
import subprocess
from Core.i18n import _t
from Modulos.modulos_config import *

class TutorialSuporte:
    """
        Como funciona: Define a estrutura e estado do componente 'TutorialSuporte'.
        Para que serve: Atua como o modelo principal para instâncias de 'TutorialSuporte'.
        Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_suporte'.
    """

    def __init__(self):
        """
            Como funciona: Inicializa os atributos e o estado inicial da instância.
            Para que serve: Prepara o objeto para ser utilizado no ciclo de vida da aplicação.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_suporte'.
        """
        self.aberto = False
        self.aba_ativa = 0
        self.scroll_y = 0
        self.max_scroll = 0
        self.BRANCO = SUPORTE_BRANCO
        self.CINZA = SUPORTE_CINZA
        self.AZUL = SUPORTE_AZUL
        self.AZUL_CLARO = SUPORTE_AZUL_CLARO
        self.abas = ['Escalas', 'Configurações', 'Metrônomo', 'Acordes', 'Vídeos']
        self.conteudo = {
            0: [{'titulo': 'Sistema Drag & Drop', 'texto': "Para utilizar as escalas, ative o ícone do 'Alfinete' (canto superior direito). Com o modo de edição ativado, clique e arraste qualquer escala do painel inferior diretamente para o braço da guitarra."}, {'titulo': 'Sobreposição Dinâmica', 'texto': 'Você pode soltar a escala em qualquer parte do braço. O EIGUIT recalcula automaticamente as notas baseando-se na afinação atual e no tom selecionado.'}, {'titulo': 'Removendo Escalas', 'texto': 'Errou a posição ou quer limpar a tela? Basta clicar com o Botão Direito do mouse sobre o braço da guitarra para devolver todas as escalas de volta ao painel de origem.'}], 
            1: [{'titulo': 'Personalização Visual', 'texto': 'Acesse a aba de configurações para alterar as cores do braço da guitarra e das notas. Use o seletor de cores integrado para encontrar o tom exato que mais agrada sua visão durante os estudos.'}, {'titulo': 'Modos de Visualização', 'texto': "Você pode alternar o texto exibido dentro das bolinhas. Escolha entre 'Notas' (C, D, E), 'Graus' (1, 2, 3) para estudar intervalos, ou oculte o texto para focar apenas nos padrões visuais (shapes)."}, {'titulo': 'Ajuste de Transparência', 'texto': 'Utilize o controle deslizante de Alpha (Transparência) para mesclar a visualização das escalas com a madeira da guitarra, criando uma interface menos agressiva aos olhos.'}], 
            2: [{'titulo': 'Controle de Tempo (BPM)', 'texto': 'O metrônomo é o coração do seu estudo rítmico. Ajuste a velocidade usando os botões de + e - ou clique na barra deslizante. A faixa vai de 40 a 240 Batidas Por Minuto.'}, {'titulo': 'Assinatura de Compasso', 'texto': 'Ajuste os tempos por compasso clicando nos números centrais (ex: 4/4, 3/4). O primeiro tempo (cabeça do compasso) sempre emitirá um som diferenciado para guiá-lo.'}],
            3: [{'titulo': 'Busca de Acordes', 'texto': 'Utilize o painel de acordes para encontrar qualquer variação. Digite o nome da nota e o tipo (Maior, Menor, 7M, etc).'}, {'titulo': 'Visualização no Braço', 'texto': 'Ao clicar em um acorde, ele é desenhado no braço da guitarra, mostrando as casas e dedos recomendados.'}],
            4: [] # Aba de Vídeos
        }
        self.rects_videos = {}
        self._carregar_videos_automacao()

    def _carregar_videos_automacao(self):
        path_videos = "automacao_tutoriais/videos_exportados"
        if os.path.exists(path_videos):
            videos = [f for f in os.listdir(path_videos) if f.endswith('.mp4')]
            self.conteudo[4] = []
            for v in videos:
                nome_formatado = v.replace('.mp4', '').replace('_', ' ').title()
                self.conteudo[4].append({
                    'titulo': nome_formatado,
                    'texto': 'Assista ao tutorial em vídeo para entender melhor como utilizar esta funcionalidade.',
                    'path': os.path.join(path_videos, v),
                    'tipo': 'video'
                })

    def quebrar_texto(self, texto, fonte, max_largura):
        palavras = texto.split(' ')
        linhas = []
        linha_atual = ''
        for palavra in palavras:
            teste_linha = linha_atual + palavra + ' '
            if fonte.size(teste_linha)[0] < max_largura:
                linha_atual = teste_linha
            else:
                linhas.append(linha_atual)
                linha_atual = palavra + ' '
        linhas.append(linha_atual)
        return linhas

    def _reproduzir_video(self, path):
        try:
            if os.name == 'nt':
                os.startfile(path)
            else:
                subprocess.call(['open', path])
        except Exception as e:
            print(f"[ERRO] Falha ao abrir vídeo: {e}")

    def tratar_eventos(self, eventos, pos_mouse):
        if not self.aberto:
            return False
        for evento in eventos:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                self.aberto = False
                return True
            if evento.type == pygame.MOUSEWHEEL:
                velocidade = 30
                self.scroll_y -= evento.y * velocidade
                self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))
                return True
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if hasattr(self, 'rect_fechar') and self.rect_fechar.collidepoint(pos_mouse):
                    self.aberto = False
                    return True
                if hasattr(self, 'rects_abas'):
                    for i, rect in enumerate(self.rects_abas):
                        if rect.collidepoint(pos_mouse):
                            self.aba_ativa = i
                            self.scroll_y = 0
                            if i == 4: self._carregar_videos_automacao()
                            return True
                for path, r_vid in self.rects_videos.items():
                    if r_vid.collidepoint(pos_mouse):
                        self._reproduzir_video(path)
                        return True
            return True
        return False

    def calcular_centro_camera(self, estado, tela, largura_obj, altura_obj):
        largura_real = tela.get_width()
        altura_real = tela.get_height()
        return (largura_real // 2 - largura_obj // 2, altura_real // 2 - altura_obj // 2)

    def desenhar(self, tela, fonte_ui, fonte_titulo, estado=None):
        if not self.aberto:
            return
        overlay = pygame.Surface((tela.get_width(), tela.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        tela.blit(overlay, (0, 0))
        largura_modal, altura_modal = 850, 550
        cx, cy = self.calcular_centro_camera(estado, tela, largura_modal, altura_modal)
        rect_modal = pygame.Rect(cx, cy, largura_modal, altura_modal)
        pygame.draw.rect(tela, (30, 30, 30), rect_modal, border_radius=10)
        pygame.draw.rect(tela, (100, 100, 100), rect_modal, width=2, border_radius=10)
        tit = fonte_titulo.render(_t('Central de Suporte & Tutoriais'), True, self.BRANCO)
        tela.blit(tit, (cx + 20, cy + 20))
        self.rects_abas = []
        largura_aba = (largura_modal - 40) / len(self.abas)
        y_abas = cy + 60
        for i, nome_aba in enumerate(self.abas):
            rect_aba = pygame.Rect(cx + 20 + i * largura_aba, y_abas, largura_aba - 5, 35)
            self.rects_abas.append(rect_aba)
            cor_fundo = self.AZUL_CLARO if self.aba_ativa == i else (60, 60, 60)
            pygame.draw.rect(tela, cor_fundo, rect_aba, border_radius=5)
            txt_aba = fonte_ui.render(_t(nome_aba), True, self.BRANCO)
            tela.blit(txt_aba, (rect_aba.centerx - txt_aba.get_width() // 2, rect_aba.centery - txt_aba.get_height() // 2))
        y_conteudo, altura_conteudo = y_abas + 45, altura_modal - 120
        rect_clipping = pygame.Rect(cx + 20, y_conteudo, largura_modal - 40, altura_conteudo)
        pygame.draw.rect(tela, (20, 20, 20), rect_clipping, border_radius=5)
        tela.set_clip(rect_clipping)
        y_item = y_conteudo + 20 - self.scroll_y
        itens_atuais = self.conteudo.get(self.aba_ativa, [])
        margem_esq, margem_dir, espacamento_meio = (40, 60, 30)
        largura_imagem, altura_imagem = (280, 160)
        largura_texto_max = largura_modal - margem_esq - margem_dir - largura_imagem - espacamento_meio
        self.rects_videos.clear()
        for i, item in enumerate(itens_atuais):
            img_na_esquerda = i % 2 == 0
            if img_na_esquerda:
                x_img = cx + margem_esq
                x_texto = x_img + largura_imagem + espacamento_meio
            else:
                x_texto = cx + margem_esq
                x_img = x_texto + largura_texto_max + espacamento_meio
            rect_img = pygame.Rect(x_img, y_item, largura_imagem, altura_imagem)
            pygame.draw.rect(tela, (40, 40, 45), rect_img, border_radius=8)
            pygame.draw.rect(tela, self.AZUL if item.get('tipo') == 'video' else self.CINZA, rect_img, width=2, border_radius=8)
            if item.get('tipo') == 'video':
                self.rects_videos[item['path']] = rect_img
                # Desenha ícone de Play
                pygame.draw.circle(tela, (255, 255, 255, 100), rect_img.center, 30, width=2)
                p1, p2, p3 = (rect_img.centerx - 10, rect_img.centery - 15), (rect_img.centerx - 10, rect_img.centery + 15), (rect_img.centerx + 15, rect_img.centery)
                pygame.draw.polygon(tela, self.BRANCO, [p1, p2, p3])
                txt_hint = fonte_ui.render(_t('CLIQUE PARA ASSISTIR'), True, self.AZUL_CLARO)
                tela.blit(txt_hint, (rect_img.centerx - txt_hint.get_width() // 2, rect_img.bottom - 25))
            else:
                txt_img = fonte_ui.render(_t('Tutorial'), True, (100, 100, 100))
                tela.blit(txt_img, (rect_img.centerx - txt_img.get_width() // 2, rect_img.centery - txt_img.get_height() // 2))
            txt_titulo = fonte_titulo.render(_t(item['titulo']), True, self.AZUL_CLARO)
            tela.blit(txt_titulo, (x_texto, y_item))
            linhas = self.quebrar_texto(_t(item['texto']), fonte_ui, largura_texto_max)
            y_linha = y_item + 35
            for linha in linhas:
                txt_linha = fonte_ui.render(linha, True, (200, 200, 200))
                tela.blit(txt_linha, (x_texto, y_linha))
                y_linha += 22
            y_item += altura_imagem + 40
        altura_total_renderizada = y_item + self.scroll_y - y_conteudo
        self.max_scroll = max(0, altura_total_renderizada - altura_conteudo)
        tela.set_clip(None)
        if self.max_scroll > 0:
            x_bar = cx + largura_modal - 15
            tamanho_alca = max(40, altura_conteudo * (altura_conteudo / (altura_conteudo + self.max_scroll)))
            y_alca = y_conteudo + self.scroll_y / self.max_scroll * (altura_conteudo - tamanho_alca)
            pygame.draw.rect(tela, (50, 50, 50), (x_bar, y_conteudo, 8, altura_conteudo), border_radius=4)
            pygame.draw.rect(tela, self.CINZA, (x_bar, y_alca, 8, tamanho_alca), border_radius=4)
        self.rect_fechar = pygame.Rect(cx + largura_modal - 140, cy + 20, 120, 30)
        pygame.draw.rect(tela, (200, 50, 50), self.rect_fechar, border_radius=5)
        txt_fechar = fonte_ui.render(_t('Fechar X'), True, self.BRANCO)
        tela.blit(txt_fechar, (self.rect_fechar.centerx - txt_fechar.get_width() // 2, self.rect_fechar.centery - txt_fechar.get_height() // 2))
